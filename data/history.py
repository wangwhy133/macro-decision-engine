"""
历史数据归档模块
负责将每日运行结果持久化到 SQLite，并提供查询接口
"""
import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from macro_system.utils.logger import get_logger

logger = get_logger("macro_system.history")

class HistoryManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """初始化历史数据表"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_date TEXT NOT NULL UNIQUE,
                    run_timestamp TEXT NOT NULL,
                    regime TEXT,
                    risk_level INTEGER,
                    data_quality TEXT,
                    cpi REAL,
                    ppi REAL,
                    pmi_mfg REAL,
                    us_cpi REAL,
                    us_unemployment REAL,
                    raw_data_snapshot TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
    
    def save_run(self, data: Dict[str, Any]) -> bool:
        """
        保存一次运行记录
        :param data: 包含 run_timestamp, regime, risk_level, data_quality 及宏观数据的字典
        """
        try:
            run_date = data.get("run_timestamp", datetime.now().isoformat())[:10]  # YYYY-MM-DD
            
            # 提取关键指标
            macro = data.get("macro", {})
            us_macro = data.get("us_macro", {})
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO daily_runs 
                    (run_date, run_timestamp, regime, risk_level, data_quality, cpi, ppi, pmi_mfg, us_cpi, us_unemployment, raw_data_snapshot)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    run_date,
                    data.get("run_timestamp"),
                    data.get("regime"),
                    data.get("risk_level"),
                    data.get("data_quality"),
                    macro.get("cpi"),
                    macro.get("ppi"),
                    macro.get("pmi_mfg"),
                    us_macro.get("cpi"),
                    us_macro.get("unemployment_rate"),
                    json.dumps(data, ensure_ascii=False)
                ))
                conn.commit()
            
            logger.info(f"历史数据已归档：{run_date}")
            return True
        except Exception as e:
            logger.error(f"归档失败：{e}")
            return False
    
    def get_history(self, limit: int = 30) -> List[Dict[str, Any]]:
        """获取最近 N 条历史记录"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT run_date, run_timestamp, regime, risk_level, data_quality, cpi, ppi, pmi_mfg
                FROM daily_runs
                ORDER BY run_date DESC
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_trend(self, field: str, limit: int = 30) -> List[Dict[str, Any]]:
        """获取特定字段的趋势数据"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT run_date, {field}
                FROM daily_runs
                ORDER BY run_date DESC
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            return [{"date": row["run_date"], "value": row[field]} for row in rows]

# 全局单例
_history_mgr = None

def get_history_manager(db_path: Optional[str] = None) -> HistoryManager:
    global _history_mgr
    if _history_mgr is None:
        if db_path is None:
            db_path = os.getenv("MACRO_DB_PATH", "/opt/macro-push/data/macro.db")
        _history_mgr = HistoryManager(db_path)
    return _history_mgr

if __name__ == "__main__":
    mgr = get_history_manager()
    print("历史数据表初始化完成")
    print("最近记录:", mgr.get_history(1))
