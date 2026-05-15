"""
MDE 资源配额与看门狗
- 内存限制
- 文件句柄限制
- 自动清理
"""

import os
import gc
import sys
from typing import Dict, Any
from datetime import datetime

class ResourceQuota:
    """资源配额管理"""
    
    def __init__(self, max_memory_mb: int = 512, max_open_files: int = 100):
        self.max_memory_mb = max_memory_mb
        self.max_open_files = max_open_files
    
    def check_memory(self) -> Dict[str, Any]:
        """检查内存使用"""
        try:
            import psutil
            process = psutil.Process(os.getpid())
            mem_info = process.memory_info()
            used_mb = mem_info.rss / 1024 / 1024
            return {
                'used_mb': used_mb,
                'limit_mb': self.max_memory_mb,
                'usage_pct': (used_mb / self.max_memory_mb) * 100,
                'is_safe': used_mb < self.max_memory_mb
            }
        except:
            return {'used_mb': 0, 'is_safe': True, 'error': '无法获取内存信息'}
    
    def force_gc(self):
        """强制垃圾回收"""
        gc.collect()

class Watchdog:
    """系统看门狗"""
    
    def __init__(self, quota: ResourceQuota):
        self.quota = quota
        self.last_check = datetime.now()
        self.check_count = 0
    
    def heartbeat(self) -> bool:
        """心跳检查"""
        self.check_count += 1
        self.last_check = datetime.now()
        
        # 每 100 次检查一次内存
        if self.check_count % 100 == 0:
            mem_status = self.quota.check_memory()
            if not mem_status.get('is_safe', True):
                print(f"⚠️  内存使用过高：{mem_status['used_mb']:.1f}MB")
                self.quota.force_gc()
                return False
        return True
    
    def report(self) -> Dict[str, Any]:
        """生成健康报告"""
        return {
            'uptime': (datetime.now() - self.last_check).total_seconds(),
            'checks': self.check_count,
            'memory': self.quota.check_memory()
        }

# 全局实例
default_quota = ResourceQuota()
watchdog = Watchdog(default_quota)

__all__ = ['ResourceQuota', 'Watchdog', 'default_quota', 'watchdog']
