"""
磁盘工具类
检查磁盘空间，清理数据库碎片
"""
import os
import sqlite3
import shutil
from typing import Tuple

def get_disk_usage(path: str) -> Tuple[float, float, float]:
    """
    获取磁盘使用情况
    :return: (总空间 GB, 已用 GB, 使用率 %)
    """
    stat = shutil.disk_usage(path)
    total_gb = stat.total / (1024 ** 3)
    used_gb = stat.used / (1024 ** 3)
    percent = (stat.used / stat.total) * 100
    return total_gb, used_gb, percent

def check_disk_space(path: str, min_free_gb: float = 1.0) -> bool:
    """
    检查剩余空间
    :param path: 检查路径
    :param min_free_gb: 最小可用空间 (GB)
    :return: 是否满足要求
    """
    stat = shutil.disk_usage(path)
    free_gb = stat.free / (1024 ** 3)
    return free_gb >= min_free_gb

def vacuum_database(db_path: str) -> bool:
    """
    清理 SQLite 数据库碎片，回收空间
    :param db_path: 数据库路径
    :return: 是否成功
    """
    if not os.path.exists(db_path):
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("VACUUM")
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"[Disk] 数据库整理失败：{e}")
        return False

def get_db_size(db_path: str) -> float:
    """获取数据库文件大小 (MB)"""
    if not os.path.exists(db_path):
        return 0.0
    return os.path.getsize(db_path) / (1024 ** 2)

if __name__ == "__main__":
    total, used, percent = get_disk_usage("/")
    print(f"磁盘：总计 {total:.2f}GB, 已用 {used:.2f}GB ({percent:.1f}%)")
    
    db_path = "/opt/macro-push/data/macro.db"
    if os.path.exists(db_path):
        size = get_db_size(db_path)
        print(f"数据库大小：{size:.2f}MB")
