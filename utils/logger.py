"""
结构化日志配置 (增强版 - 异步非阻塞)
- 支持控制台彩色输出
- 支持生产环境 JSON 格式
- 异步队列写入，防止阻塞主线程
"""
import logging
import sys
import json
import threading
import queue
from typing import Optional
from datetime import datetime
from logging.handlers import QueueHandler, QueueListener

class JsonFormatter(logging.Formatter):
    """JSON 格式化器"""
    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj, ensure_ascii=False)

def setup_logger(
    name: str, 
    level: int = logging.INFO, 
    json_format: bool = False,
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    配置异步日志记录器
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # 避免重复添加
    
    logger.setLevel(level)
    
    # 创建日志队列 (容量 1000，防止内存溢出)
    log_queue = queue.Queue(maxsize=1000)
    
    # 处理器工厂
    def create_handler():
        if json_format:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(JsonFormatter())
        else:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
        return handler
    
    # 队列处理器 (异步写入)
    queue_handler = QueueHandler(log_queue)
    
    # 队列监听器 (后台线程消费)
    handler = create_handler()
    listener = QueueListener(log_queue, handler, respect_handler_level=True)
    listener.start()
    
    # 添加文件处理器 (可选)
    if log_file:
        try:
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(JsonFormatter() if json_format else handler.formatter)
            listener.handlers = (*listener.handlers, file_handler)
        except Exception as e:
            logger.warning(f"无法写入日志文件 {log_file}: {e}")
    
    logger.addHandler(queue_handler)
    
    # 清理钩子 (进程退出时停止监听器)
    import atexit
    atexit.register(listener.stop)
    
    return logger

# 全局默认 Logger
default_logger = setup_logger("macro_system", level=logging.INFO)

def get_logger(name: str = "macro_system") -> logging.Logger:
    if name == "macro_system":
        return default_logger
    return setup_logger(name)

if __name__ == "__main__":
    logger = get_logger("test")
    logger.info("测试异步日志")
    logger.warning("测试警告")
    logger.error("测试错误")
