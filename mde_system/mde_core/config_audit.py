"""
MDE 配置审计与回滚
记录配置变更历史，支持一键回滚
"""

import json
import shutil
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

class ConfigAuditor:
    """配置审计器"""
    
    def __init__(self, config_path: str, backup_dir: str = "config_backups"):
        self.config_path = Path(config_path)
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.history: List[Dict[str, Any]] = []
        self._load_history()
    
    def _load_history(self):
        """加载历史记录"""
        history_file = self.backup_dir / "history.json"
        if history_file.exists():
            with open(history_file, 'r') as f:
                self.history = json.load(f)
    
    def save_snapshot(self, operator: str = "system", comment: str = ""):
        """保存当前配置快照"""
        if not self.config_path.exists():
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = self.backup_dir / f"config_{timestamp}.json"
        
        # 备份文件
        shutil.copy(self.config_path, backup_file)
        
        # 记录历史
        record = {
            "timestamp": timestamp,
            "file": str(backup_file),
            "operator": operator,
            "comment": comment
        }
        self.history.append(record)
        self._save_history()
        
        print(f"✅ 配置已备份：{backup_file}")
        return backup_file
    
    def rollback(self, version_index: int = -1) -> bool:
        """
        回滚到指定版本
        :param version_index: 版本号索引 (-1 表示上一个版本)
        """
        if version_index >= len(self.history) or version_index < -len(self.history):
            print("❌ 版本号越界")
            return False
        
        record = self.history[version_index]
        backup_file = record['file']
        
        if not Path(backup_file).exists():
            print(f"❌ 备份文件不存在：{backup_file}")
            return False
        
        # 先备份当前状态
        self.save_snapshot(operator="rollback_auto", comment=f"回滚前备份，目标版本：{record['timestamp']}")
        
        # 恢复文件
        shutil.copy(backup_file, self.config_path)
        print(f"✅ 已回滚到版本：{record['timestamp']} (操作者：{record['operator']})")
        return True
    
    def list_history(self) -> List[Dict[str, Any]]:
        """列出历史版本"""
        return self.history
    
    def _save_history(self):
        history_file = self.backup_dir / "history.json"
        with open(history_file, 'w') as f:
            json.dump(self.history, f, indent=2)

# 全局实例
config_auditor = ConfigAuditor("config.json")

__all__ = ['ConfigAuditor', 'config_auditor']
