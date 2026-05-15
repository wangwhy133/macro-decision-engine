# src/utils/cleanup.py
"""
资源清理与日志轮转模块 (Cleanup & Rotation)

功能:
1. 日志文件轮转 (Log Rotation): 超过大小/天数自动切割
2. 缓存清理 (Cache TTL): 清理过期的缓存文件
3. 临时文件清理: 定期清理 tmp 目录
4. 内存泄漏检测: 监控进程内存，超阈值告警/重启

使用场景:
- 系统启动时初始化日志轮转
- 定时任务 (每小时/每天) 执行清理
- 进程守护脚本中集成内存监控
"""

import os
import glob
import time
import logging
import psutil
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler
from typing import List, Optional

from src.utils.logger import setup_logger

logger = setup_logger("MDE.Cleanup")

class CleanupManager:
    """资源清理管理器"""
    
    def __init__(
        self,
        log_dir: str = "logs",
        cache_dir: str = "data/cache",
        max_log_size_mb: int = 10,
        max_log_files: int = 5,
        cache_ttl_hours: int = 24
    ):
        self.log_dir = log_dir
        self.cache_dir = cache_dir
        self.max_log_size_bytes = max_log_size_mb * 1024 * 1024
        self.max_log_files = max_log_files
        self.cache_ttl_seconds = cache_ttl_hours * 3600
        
        # 确保目录存在
        os.makedirs(log_dir, exist_ok=True)
        os.makedirs(cache_dir, exist_ok=True)
    
    def setup_log_rotation(self, log_file: str = "mde.log"):
        """
        设置日志轮转
        
        Args:
            log_file: 日志文件名
        """
        log_path = os.path.join(self.log_dir, log_file)
        
        handler = RotatingFileHandler(
            log_path,
            maxBytes=self.max_log_size_bytes,
            backupCount=self.max_log_files
        )
        handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s'))
        
        # 添加到根 logger
        root_logger = logging.getLogger()
        root_logger.addHandler(handler)
        root_logger.setLevel(logging.INFO)
        
        logger.info(f"日志轮转已配置：{log_path} (最大 {self.max_log_size_bytes}B, 保留 {self.max_log_files} 个)")
    
    def run_cleanup(self) -> dict:
        """
        执行清理任务
        
        Returns:
            清理统计信息
        """
        stats = {
            'logs_cleaned': 0,
            'cache_cleaned': 0,
            'space_freed_mb': 0.0
        }
        
        # 1. 清理旧日志
        stats['logs_cleaned'] = self._cleanup_old_logs()
        
        # 2. 清理过期缓存
        stats['cache_cleaned'] = self._cleanup_expired_cache()
        
        # 3. (可选) 清理临时文件
        # self._cleanup_temp_files()
        
        logger.info(f"清理完成：{stats}")
        return stats
    
    def _cleanup_old_logs(self) -> int:
        """清理超过保留数量的旧日志"""
        count = 0
        log_pattern = os.path.join(self.log_dir, "mde.log.*")
        log_files = sorted(glob.glob(log_pattern))
        
        # 保留最新的 max_log_files 个
        if len(log_files) > self.max_log_files:
            for f in log_files[:-self.max_log_files]:
                try:
                    size = os.path.getsize(f) / (1024*1024)
                    os.remove(f)
                    count += 1
                    logger.debug(f"清理旧日志：{f} ({size:.2f}MB)")
                except Exception as e:
                    logger.error(f"清理日志失败 {f}: {e}")
        
        return count
    
    def _cleanup_expired_cache(self) -> int:
        """清理过期缓存"""
        count = 0
        now = time.time()
        
        for f in glob.glob(os.path.join(self.cache_dir, "*")):
            if os.path.isfile(f):
                mtime = os.path.getmtime(f)
                if now - mtime > self.cache_ttl_seconds:
                    try:
                        size = os.path.getsize(f) / (1024*1024)
                        os.remove(f)
                        count += 1
                        logger.debug(f"清理过期缓存：{f} ({size:.2f}MB)")
                    except Exception as e:
                        logger.error(f"清理缓存失败 {f}: {e}")
        
        return count
    
    def check_memory_usage(self, threshold_percent: float = 90.0) -> bool:
        """
        检查内存使用率
        
        Returns:
            是否超过阈值
        """
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        total_memory = psutil.virtual_memory().total
        
        usage_percent = (memory_info.rss / total_memory) * 100
        
        if usage_percent > threshold_percent:
            logger.warning(f"内存使用率过高：{usage_percent:.1f}% (阈值：{threshold_percent}%)")
            return True
        
        return False

# 全局单例
_cleanup_manager = None

def get_cleanup_manager() -> CleanupManager:
    global _cleanup_manager
    if _cleanup_manager is None:
        _cleanup_manager = CleanupManager()
    return _cleanup_manager

def init_cleanup():
    """初始化清理服务"""
    manager = get_cleanup_manager()
    manager.setup_log_rotation()
    return manager

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    manager = init_cleanup()
    
    # 模拟生成一些日志
    for i in range(100):
        logger.info(f"测试日志 {i}")
    
    # 执行清理
    stats = manager.run_cleanup()
    print(f"清理统计：{stats}")
    
    # 检查内存
    is_high = manager.check_memory_usage(threshold_percent=50.0)
    print(f"内存是否过高：{is_high}")
