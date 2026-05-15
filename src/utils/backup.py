# src/utils/backup.py
"""
自动化备份与恢复模块 (Backup & Restore)

功能:
1. 定时备份关键数据 (代码、配置、数据库、日志)
2. 压缩加密 (可选)
3. 上传到远程存储 (S3/OSS/FTP) 或 本地备份目录
4. 清理旧备份 (保留最近 N 天)
5. 一键恢复

使用场景:
- 每日凌晨自动备份
- 部署新版本前自动备份
- 灾难后快速恢复
"""

import os
import shutil
import tarfile
import datetime
import glob
import logging
from typing import List, Optional

from src.utils.logger import setup_logger

logger = setup_logger("MDE.Backup")

class BackupManager:
    """备份管理器"""
    
    def __init__(
        self,
        root_dir: str = ".",
        backup_dir: str = "backups",
        keep_days: int = 7,
        include_paths: List[str] = None
    ):
        self.root_dir = os.path.abspath(root_dir)
        self.backup_dir = os.path.join(self.root_dir, backup_dir)
        self.keep_days = keep_days
        self.include_paths = include_paths or [
            'src', 'data', 'logs', '.env', 'requirements.txt', 'config.yaml'
        ]
        
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def run_backup(self, prefix: str = "mde_backup") -> Optional[str]:
        """
        执行备份
        
        Returns:
            备份文件路径，失败返回 None
        """
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{prefix}_{timestamp}.tar.gz"
        backup_path = os.path.join(self.backup_dir, backup_filename)
        
        try:
            logger.info(f"开始备份到 {backup_path}...")
            
            with tarfile.open(backup_path, "w:gz") as tar:
                for path in self.include_paths:
                    full_path = os.path.join(self.root_dir, path)
                    if os.path.exists(full_path):
                        # 添加到压缩包
                        tar.add(full_path, arcname=os.path.basename(full_path))
                        logger.debug(f"已添加：{path}")
                    else:
                        logger.warning(f"路径不存在，跳过：{path}")
            
            logger.info(f"备份完成：{backup_path}")
            
            # 清理旧备份
            self._cleanup_old_backups()
            
            # TODO: 上传到远程存储 (S3/OSS)
            # self._upload_to_remote(backup_path)
            
            return backup_path
            
        except Exception as e:
            logger.error(f"备份失败：{e}")
            return None
    
    def _cleanup_old_backups(self):
        """清理超过保留天数的旧备份"""
        cutoff_time = datetime.datetime.now().timestamp() - (self.keep_days * 86400)
        
        for f in glob.glob(os.path.join(self.backup_dir, "mde_backup_*.tar.gz")):
            if os.path.getmtime(f) < cutoff_time:
                try:
                    os.remove(f)
                    logger.info(f"清理旧备份：{f}")
                except Exception as e:
                    logger.error(f"清理备份失败 {f}: {e}")
    
    def restore(self, backup_path: str, target_dir: str = None):
        """
        从备份恢复
        
        Args:
            backup_path: 备份文件路径
            target_dir: 恢复目标目录 (默认原目录)
        """
        if target_dir is None:
            target_dir = self.root_dir
            logger.warning("⚠️ 将恢复到原目录，请确保已停止服务！")
        
        try:
            logger.info(f"开始从 {backup_path} 恢复...")
            
            with tarfile.open(backup_path, "r:gz") as tar:
                tar.extractall(path=target_dir)
            
            logger.info(f"恢复完成到：{target_dir}")
            return True
            
        except Exception as e:
            logger.error(f"恢复失败：{e}")
            return False

# 全局单例
_backup_manager = None

def get_backup_manager() -> BackupManager:
    global _backup_manager
    if _backup_manager is None:
        _backup_manager = BackupManager()
    return _backup_manager

def run_daily_backup():
    """便捷函数：执行每日备份"""
    manager = get_backup_manager()
    return manager.run_backup()

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # 测试备份
    path = run_daily_backup()
    if path:
        print(f"备份成功：{path}")
        
        # 测试恢复 (谨慎使用)
        # manager = get_backup_manager()
        # manager.restore(path, target_dir="./restore_test")
