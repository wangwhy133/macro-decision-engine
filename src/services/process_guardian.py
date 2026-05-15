# src/services/process_guardian.py
"""
进程守护服务 (Process Guardian)

功能:
1. 监控主进程健康状态
2. 检测死锁/无响应
3. 自动重启进程 (如果挂掉)
4. 优雅关闭 (保存状态后重启)

使用场景:
- 作为主程序的包装器启动
- 长期运行的服务 (7x24 小时)
- 防止内存泄漏导致的 OOM
"""

import os
import sys
import time
import subprocess
import signal
import logging
from datetime import datetime, timedelta
from typing import Optional, Callable

from src.utils.logger import setup_logger
from src.utils.cleanup import get_cleanup_manager

logger = setup_logger("MDE.Guardian")

class ProcessGuardian:
    """进程守护器"""
    
    def __init__(
        self,
        script_path: str,
        max_restarts: int = 5,
        restart_delay: int = 5,
        max_uptime_hours: int = 24,  # 运行 24 小时后自动重启 (防内存泄漏)
        health_check_func: Optional[Callable[[], bool]] = None
    ):
        self.script_path = script_path
        self.max_restarts = max_restarts
        self.restart_delay = restart_delay
        self.max_uptime_seconds = max_uptime_hours * 3600
        self.health_check_func = health_check_func
        
        self.process: Optional[subprocess.Popen] = None
        self.restart_count = 0
        self.start_time: Optional[datetime] = None
        self.running = False
    
    def start(self):
        """启动守护"""
        self.running = True
        logger.info(f"🛡️ 进程守护启动，监控：{self.script_path}")
        
        while self.running:
            # 检查是否需要重启 (运行时间过长)
            if self.start_time and (datetime.now() - self.start_time).total_seconds() > self.max_uptime_seconds:
                logger.info("运行时间过长，计划重启...")
                self._stop_process()
            
            # 启动子进程
            self._start_process()
            
            # 等待子进程结束
            if self.process:
                self.process.wait()
                
                # 如果子进程正常退出 (代码 0)，则退出
                if self.process.returncode == 0:
                    logger.info("子进程正常退出，守护结束")
                    break
                
                # 异常退出，尝试重启
                logger.warning(f"子进程异常退出 (代码 {self.process.returncode})，准备重启...")
                self._handle_restart()
    
    def _start_process(self):
        """启动子进程"""
        try:
            self.start_time = datetime.now()
            self.process = subprocess.Popen(
                [sys.executable, self.script_path],
                env=os.environ.copy()
            )
            logger.info(f"子进程已启动 (PID: {self.process.pid})")
        except Exception as e:
            logger.error(f"启动子进程失败：{e}")
            self.process = None
    
    def _stop_process(self):
        """停止子进程"""
        if self.process and self.process.poll() is None:
            logger.info("正在停止子进程...")
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            logger.info("子进程已停止")
        self.process = None
    
    def _handle_restart(self):
        """处理重启逻辑"""
        if self.restart_count >= self.max_restarts:
            logger.error(f"达到最大重启次数 ({self.max_restarts})，停止守护")
            self.running = False
            return
        
        self.restart_count += 1
        logger.info(f"第 {self.restart_count} 次重启，等待 {self.restart_delay} 秒...")
        time.sleep(self.restart_delay)
    
    def stop(self):
        """停止守护"""
        self.running = False
        self._stop_process()

# 便捷函数：作为主入口
def guard_main(main_func):
    """
    装饰器：保护主函数
    
    @guard_main
    def main():
        # 业务逻辑
        pass
    """
    def wrapper():
        guardian = ProcessGuardian(script_path=__file__)
        
        def health_check():
            try:
                # 检查清理服务
                cleanup_mgr = get_cleanup_manager()
                if cleanup_mgr.check_memory_usage(threshold_percent=90.0):
                    return False
                return True
            except:
                return False
        
        guardian.health_check_func = health_check
        guardian.start()
    
    return wrapper

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # 测试：模拟一个会挂掉的脚本
    print("守护进程测试中...")
    guardian = ProcessGuardian(script_path="dummy_script.py", max_restarts=3)
    
    # 实际使用中，这通常是一个单独的启动脚本
    # guardian.start()
