# src/utils/logger.py
"""
日志配置模块 (生产级)

功能:
1. 统一日志格式
2. 日志级别控制
3. 日志轮转
4. 安全日志脱敏
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from datetime import datetime

def setup_logger(
    name: str = "MDE",
    level: int = logging.INFO,
    log_dir: str = "logs",
    max_bytes: int = 10*1024*1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """
    配置并返回日志记录器
    
    Args:
        name: 日志名称
        level: 日志级别
        log_dir: 日志目录
        max_bytes: 单个日志文件最大大小
        backup_count: 保留的日志文件数量
    
    Returns:
        配置好的 Logger 实例
    """
    # 创建日志目录
    os.makedirs(log_dir, exist_ok=True)
    
    # 获取或创建 logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 避免重复添加 handler
    if logger.handlers:
        return logger
    
    # 日志格式
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件处理器 (带轮转)
    log_file = os.path.join(log_dir, f"{name.lower()}.log")
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # 错误日志单独记录
    error_log_file = os.path.join(log_dir, f"{name.lower()}_error.log")
    error_handler = RotatingFileHandler(
        error_log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)
    
    logger.info(f"日志系统已初始化：{log_dir}")
    
    return logger


class SensitiveDataFilter(logging.Filter):
    """敏感数据过滤器 (脱敏)"""
    
    def __init__(self, patterns=None):
        super().__init__()
        self.patterns = patterns or ['api_key', 'password', 'token', 'secret']
    
    def filter(self, record):
        msg = str(record.msg)
        for pattern in self.patterns:
            if pattern in msg.lower():
                record.msg = msg.replace(pattern, '*' * len(pattern))
        return True


def get_logger(name: str = "MDE") -> logging.Logger:
    """获取已配置的 logger"""
    return logging.getLogger(name)


# 快捷方式
def log_info(message: str, **kwargs):
    """记录 INFO 日志"""
    logger = get_logger()
    if kwargs:
        logger.info(f"{message} | {kwargs}")
    else:
        logger.info(message)


def log_warning(message: str, **kwargs):
    """记录 WARNING 日志"""
    logger = get_logger()
    if kwargs:
        logger.warning(f"{message} | {kwargs}")
    else:
        logger.warning(message)


def log_error(message: str, exc_info: bool = False, **kwargs):
    """记录 ERROR 日志"""
    logger = get_logger()
    if kwargs:
        logger.error(f"{message} | {kwargs}", exc_info=exc_info)
    else:
        logger.error(message, exc_info=exc_info)


def log_critical(message: str, exc_info: bool = False, **kwargs):
    """记录 CRITICAL 日志"""
    logger = get_logger()
    if kwargs:
        logger.critical(f"{message} | {kwargs}", exc_info=exc_info)
    else:
        logger.critical(message, exc_info=exc_info)


# 初始化默认 logger
default_logger = setup_logger()

if __name__ == "__main__":
    # 测试日志系统
    logger = setup_logger("TestLogger", level=logging.DEBUG)
    
    logger.info("这是一条 INFO 日志")
    logger.warning("这是一条 WARNING 日志")
    logger.error("这是一条 ERROR 日志")
    
    try:
        1 / 0
    except Exception as e:
        logger.error("发生异常", exc_info=True)
    
    print("日志测试完成")
