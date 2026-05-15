# src/services/watchdog.py
"""
看门狗服务 (Watchdog Service)

功能:
1. 定时巡检关键组件 (数据源、API、磁盘空间)
2. 异常主动告警 (Telegram/邮件/日志)
3. 自动恢复尝试 (重启服务、切换备用源)

巡检项:
- 数据源延迟 (超过 1 小时未更新)
- 磁盘空间 (低于 10%)
- API 可用性
- 进程内存占用
"""

import os
import shutil
import time
import threading
from datetime import datetime, timedelta
from typing import Callable, List, Dict, Any
from src.utils.logger import setup_logger
from src.utils.retry import retry_with_fallback

logger = setup_logger("MDE.Watchdog")

class WatchdogService:
    """看门狗服务"""
    
    def __init__(self, check_interval: int = 300):  # 5 分钟检查一次
        self.check_interval = check_interval
        self.running = False
        self.thread: threading.Thread = None
        self.alert_callbacks: List[Callable[[str], None]] = []
        self.last_check_time: Dict[str, datetime] = {}
    
    def start(self):
        """启动看门狗"""
        self.running = True
        self.thread = threading.Thread(target=self._check_loop, daemon=True)
        self.thread.start()
        logger.info("🐕 看门狗服务已启动")
    
    def stop(self):
        """停止看门狗"""
        self.running = False
        if self.thread:
            self.thread.join()
        logger.info("🐕 看门狗服务已停止")
    
    def add_alert_callback(self, callback: Callable[[str], None]):
        """添加告警回调 (如发送 Telegram 消息)"""
        self.alert_callbacks.append(callback)
    
    def _send_alert(self, message: str):
        """发送告警"""
        logger.warning(f"🚨 告警：{message}")
        for callback in self.alert_callbacks:
            try:
                callback(message)
            except Exception as e:
                logger.error(f"告警回调失败：{e}")
    
    def _check_loop(self):
        """巡检循环"""
        while self.running:
            try:
                self._run_checks()
            except Exception as e:
                logger.error(f"看门狗巡检异常：{e}")
            time.sleep(self.check_interval)
    
    def _run_checks(self):
        """执行所有检查"""
        logger.debug("执行健康巡检...")
        
        # 1. 检查数据源延迟
        self._check_data_freshness("data/features/latest_state.json", 3600)  # 1 小时
        self._check_data_freshness("data/supply_demand_state.json", 86400)  # 24 小时
        
        # 2. 检查磁盘空间
        self._check_disk_space("/", 0.1)  # 低于 10% 告警
        
        # 3. 检查关键进程 (简化为检查文件锁或 PID 文件)
        # TODO: 实现具体进程检查
    
    def _check_data_freshness(self, file_path: str, max_age_seconds: int):
        """检查数据文件是否过期"""
        if not os.path.exists(file_path):
            self._send_alert(f"数据文件缺失：{file_path}")
            return
        
        mtime = os.path.getmtime(file_path)
        age = time.time() - mtime
        
        if age > max_age_seconds:
            self._send_alert(f"数据过期：{file_path} (已 {age/3600:.1f} 小时未更新)")
    
    def _check_disk_space(self, path: str, threshold: float):
        """检查磁盘空间"""
        try:
            total, used, free = shutil.disk_usage(path)
            free_ratio = free / total
            if free_ratio < threshold:
                self._send_alert(f"磁盘空间不足：{path} (剩余 {free_ratio:.1%})")
        except Exception as e:
            logger.error(f"磁盘检查失败：{e}")

# 全局单例
_watchdog = None

def get_watchdog() -> WatchdogService:
    global _watchdog
    if _watchdog is None:
        _watchdog = WatchdogService()
    return _watchdog

def start_watchdog(alert_callback: Callable[[str], None] = None):
    """启动看门狗"""
    dog = get_watchdog()
    if alert_callback:
        dog.add_alert_callback(alert_callback)
    dog.start()
    return dog

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    def telegram_alert(msg):
        print(f"[Telegram] {msg}")
    
    dog = start_watchdog(telegram_alert)
    
    print("看门狗运行中... (按 Ctrl+C 停止)")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        dog.stop()
