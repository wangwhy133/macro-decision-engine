"""
SQLite 数据缓存管理器 (增强版 - 防泄漏)
- 使用上下文管理器防止连接泄漏
- 支持差异化 TTL
- 支持失败缓存 (Cache Failure)
"""
import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from macro_system.utils.json_utils import safe_json_dumps, safe_json_loads
from macro_system.utils.file_lock import db_lock

class CacheManager:
    def __init__(self, db_path: str = "/opt/macro-push/data/cache.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """初始化数据库表结构"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS data_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    data_type TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    fetched_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    is_error INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_source_type ON data_cache(source, data_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_expires ON data_cache(expires_at)")
            conn.commit()
    
    def get(self, source: str, data_type: str, max_age_hours: int = 24) -> Optional[Dict[str, Any]]:
        """读取缓存"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT payload, fetched_at, is_error FROM data_cache
                WHERE source = ? AND data_type = ?
                ORDER BY fetched_at DESC LIMIT 1
            """, (source, data_type))
            row = cursor.fetchone()
        
        if not row:
            return None
        
        try:
            payload = safe_json_loads(row[0])  # 使用安全反序列化
            fetched_at = datetime.fromisoformat(row[1])
            is_error = row[2]
            
            # 错误缓存逻辑
            if is_error:
                if datetime.now() - fetched_at < timedelta(hours=1):
                    return None  # 冷却中
                else:
                    return None  # 冷却结束，应重抓
            
            # 正常 TTL 检查
            if datetime.now() - fetched_at > timedelta(hours=max_age_hours):
                return None
            
            return payload
        except:
            return None
    
    def set(self, source: str, data_type: str, payload: Dict[str, Any], 
            ttl_hours: int = 24, is_error: bool = False) -> bool:
        """写入缓存（带文件锁保护）"""
        try:
            with db_lock(self.db_path, timeout=5.0):
                with sqlite3.connect(self.db_path) as conn:
                    fetched_at = datetime.now()
                    actual_ttl = 1 if is_error else ttl_hours
                    expires_at = fetched_at + timedelta(hours=actual_ttl)
                    
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO data_cache (source, data_type, payload, fetched_at, expires_at, is_error)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        source, data_type, 
                        safe_json_dumps(payload),
                        fetched_at.isoformat(),
                        expires_at.isoformat(),
                        1 if is_error else 0
                    ))
                    conn.commit()
            return True
        except TimeoutError:
            print(f"[Cache] 获取锁超时：{self.db_path}")
            return False
        except Exception as e:
            print(f"[Cache] 写入失败：{e}")
            return False
    
    def clear_expired(self) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM data_cache WHERE expires_at < datetime('now')")
            deleted = cursor.rowcount
            conn.commit()
        return deleted
    
    def get_stats(self) -> Dict[str, Any]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM data_cache")
            total = cursor.fetchone()[0]
            cursor.execute("SELECT source, COUNT(*) as cnt FROM data_cache GROUP BY source")
            by_source = {row[0]: row[1] for row in cursor.fetchall()}
        return {"total_entries": total, "by_source": by_source, "db_path": self.db_path}

# 移除全局单例，改为工厂函数
def get_cache(db_path: str = "/opt/macro-push/data/cache.db") -> CacheManager:
    return CacheManager(db_path)

if __name__ == "__main__":
    cache = get_cache()
    print("缓存统计:", cache.get_stats())