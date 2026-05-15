"""
MDE 配置热加载 2.0
支持动态注入策略参数，无需重启
"""

import json
import os
from typing import Dict, Any, Optional
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class HotConfig:
    """热配置管理器"""
    
    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self._config: Dict[str, Any] = {}
        self._callbacks: list = []
        self._observer: Optional[Observer] = None
        self.load()
        self.start_watch()
    
    def load(self):
        """加载配置"""
        if not self.config_path.exists():
            return
        with open(self.config_path, 'r') as f:
            self._config = json.load(f)
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项"""
        keys = key.split('.')
        val = self._config
        for k in keys:
            if isinstance(val, dict) and k in val:
                val = val[k]
            else:
                return default
        return val
    
    def set(self, key: str, value: Any):
        """设置配置项 (并触发回调)"""
        keys = key.split('.')
        config = self._config
        for k in keys[:-1]:
            config = config.setdefault(k, {})
        config[keys[-1]] = value
        self._notify_callbacks()
    
    def register_callback(self, callback):
        """注册配置变更回调"""
        self._callbacks.append(callback)
    
    def _notify_callbacks(self):
        """通知所有回调"""
        for cb in self._callbacks:
            try:
                cb(self._config)
            except Exception as e:
                print(f"回调执行失败：{e}")
    
    def start_watch(self):
        """启动文件监控"""
        class ConfigChangeHandler(FileSystemEventHandler):
            def __init__(self, loader):
                self.loader = loader
            
            def on_modified(self, event):
                if event.src_path == str(self.loader.config_path):
                    self.loader.load()
                    self.loader._notify_callbacks()
                    print(f"✅ 配置热更新：{self.loader.config_path}")
        
        self._observer = Observer()
        self._observer.schedule(ConfigChangeHandler(self), str(self.config_path.parent), recursive=False)
        self._observer.start()

# 全局实例 (延迟加载)
hot_config: Optional[HotConfig] = None

def init_hot_config(path: str = "config.json"):
    global hot_config
    hot_config = HotConfig(path)
    return hot_config

__all__ = ['HotConfig', 'hot_config', 'init_hot_config']
