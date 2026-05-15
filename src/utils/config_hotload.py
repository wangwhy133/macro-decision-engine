# src/utils/config_hotload.py
"""
配置热加载模块 (Hot Reload Config)

功能:
1. 监听配置文件变化 (.env, config.yaml)
2. 自动重新加载配置，无需重启服务
3. 配置变更通知回调

使用示例:
    from src.utils.config_hotload import watch_config
    
    def on_change():
        print("配置已更新!")
    
    watch_config('config.yaml', on_change)
"""

import os
import time
import threading
import logging
from typing import Callable, Optional
from dotenv import load_dotenv
from src.utils.logger import setup_logger

logger = setup_logger("MDE.HotLoad")

class ConfigWatcher:
    """配置文件监听器"""
    
    def __init__(self, file_path: str, callback: Callable, interval: int = 5):
        self.file_path = file_path
        self.callback = callback
        self.interval = interval
        self.last_mtime = None
        self.running = False
        self.thread: Optional[threading.Thread] = None
    
    def start(self):
        """启动监听"""
        if os.path.exists(self.file_path):
            self.last_mtime = os.path.getmtime(self.file_path)
        
        self.running = True
        self.thread = threading.Thread(target=self._watch_loop, daemon=True)
        self.thread.start()
        logger.info(f"配置监听已启动：{self.file_path}")
    
    def stop(self):
        """停止监听"""
        self.running = False
        if self.thread:
            self.thread.join()
        logger.info(f"配置监听已停止：{self.file_path}")
    
    def _watch_loop(self):
        """监听循环"""
        while self.running:
            if os.path.exists(self.file_path):
                current_mtime = os.path.getmtime(self.file_path)
                if self.last_mtime != current_mtime:
                    logger.info(f"检测到配置变化：{self.file_path}")
                    self.last_mtime = current_mtime
                    # 重新加载配置
                    load_dotenv(dotenv_path=self.file_path, override=True)
                    # 回调通知
                    try:
                        self.callback()
                    except Exception as e:
                        logger.error(f"配置更新回调失败：{e}")
            time.sleep(self.interval)

_watchers = []

def watch_config(file_path: str, callback: Callable = None):
    """
    便捷函数：启动配置监听
    
    Args:
        file_path: 配置文件路径
        callback: 配置变化时的回调函数
    """
    def default_callback():
        logger.info("配置已自动重新加载")
    
    watcher = ConfigWatcher(
        file_path=file_path,
        callback=callback or default_callback
    )
    watcher.start()
    _watchers.append(watcher)
    return watcher

def stop_all_watchers():
    """停止所有监听"""
    for w in _watchers:
        w.stop()

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # 测试
    def my_callback():
        print(">>> 配置更新了！")
    
    # 创建测试文件
    test_file = "test_config.env"
    with open(test_file, 'w') as f:
        f.write("TEST_VAR=initial\n")
    
    watcher = watch_config(test_file, my_callback)
    
    print("监听中... (修改 test_config.env 测试)")
    try:
        time.sleep(30)
    except KeyboardInterrupt:
        stop_all_watchers()
