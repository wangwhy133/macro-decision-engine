"""
MDE 状态持久化管理
解决进程重启后状态丢失问题
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

class StateManager:
    """状态管理器"""
    
    def __init__(self, state_file: str = "state.json"):
        self.state_file = Path(state_file)
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
    
    def save(self, state: Dict[str, Any]) -> bool:
        """保存状态"""
        try:
            state['_timestamp'] = datetime.now().isoformat()
            temp_file = self.state_file.with_suffix('.tmp')
            
            # 原子写入 (先写临时文件，再重命名)
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
            
            temp_file.replace(self.state_file)
            return True
        except Exception as e:
            print(f"保存状态失败：{e}")
            return False
    
    def load(self) -> Optional[Dict[str, Any]]:
        """加载状态"""
        if not self.state_file.exists():
            return None
        
        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
            return state
        except Exception as e:
            print(f"加载状态失败：{e}")
            return None
    
    def clear(self):
        """清除状态"""
        if self.state_file.exists():
            self.state_file.unlink()

__all__ = ['StateManager']
