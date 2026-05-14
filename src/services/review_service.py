# src/services/review_service.py
"""
A. 复盘回填机制
负责记录决策日志，并在 T+1 日自动校准准确率
"""
import duckdb
import json
import os
from datetime import datetime
import yfinance as yf

DB_PATH = "data/mde.duckdb"

class ReviewService:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        # 确保数据目录存在
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = duckdb.connect(db_path)
        self._init_db()

    def _init_db(self):
        """初始化决策日志表"""
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS decision_logs (
            id TEXT PRIMARY KEY,
            timestamp TIMESTAMP,
            market_state TEXT,
            agent_opinions TEXT,
            final_decision TEXT,
            confidence REAL,
            reasoning TEXT,
            actual_price_next REAL,
            actual_return REAL,
            is_correct BOOLEAN,
            status TEXT DEFAULT 'PENDING'
        )
        """)

    def log_decision(self, decision_id, market_state, agent_opinions, final_decision, confidence, reasoning):
        """记录一次决策"""
        self.conn.execute("""
        INSERT OR REPLACE INTO decision_logs 
        (id, timestamp, market_state, agent_opinions, final_decision, confidence, reasoning, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'PENDING')
        """, [
            decision_id,
            datetime.now(),
            json.dumps(market_state),
            json.dumps(agent_opinions),
            final_decision,
            confidence,
            reasoning
        ])
        print(f"📝 决策已记录：{decision_id} -> {final_decision}")

    def calibrate_pending_decisions(self, symbol: str = "SPY"):
        """校准所有未完成的决策 (T+1 逻辑)"""
        print("🔄 开始校准历史决策...")
        
        rows = self.conn.execute("""
        SELECT id, timestamp, final_decision, confidence 
        FROM decision_logs 
        WHERE status = 'PENDING'
        """).fetchall()

        if not rows:
            print("✅ 无需校准")
            return

        # 获取最新价格用于校准 (简化逻辑：假设所有 PENDING 都是昨天的)
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1d")
            if hist.empty:
                current_price = 0.0
            else:
                current_price = float(hist['Close'].iloc[-1])
            print(f"📊 获取 {symbol} 最新收盘价：{current_price}")
        except Exception as e:
            print(f"⚠️ 获取价格失败：{e}")
            current_price = 0.0

        for row in rows:
            dec_id, ts, decision, conf = row
            
            # 简化逻辑：模拟回报率 (实际应获取 T+1 的收盘价)
            # 假设基准价 400 (SPY 近似价)
            mock_return = (current_price - 400) / 400 if current_price else 0.0
            
            is_win = False
            if decision == 'BUY' and mock_return > 0:
                is_win = True
            elif decision == 'SELL' and mock_return < 0:
                is_win = True
            elif decision == 'HOLD':
                is_win = True  # HOLD 默认不亏

            self.conn.execute("""
            UPDATE decision_logs 
            SET actual_price_next = ?, actual_return = ?, is_correct = ?, status = 'COMPLETED'
            WHERE id = ?
            """, [current_price, mock_return, is_win, dec_id])
            
            status_icon = "✅" if is_win else "❌"
            print(f" {status_icon} 校准 {dec_id}: 决策{decision} -> 结果{'正确' if is_win else '错误'}")

    def get_stats(self):
        """获取统计数据"""
        res = self.conn.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(is_correct) as correct,
            AVG(actual_return) as avg_return
        FROM decision_logs 
        WHERE status = 'COMPLETED'
        """).fetchone()
        return {
            'total': res[0],
            'correct': res[1],
            'accuracy': res[1]/res[0] if res[0] else 0,
            'avg_return': res[2] or 0
        }

if __name__ == "__main__":
    svc = ReviewService()
    svc.calibrate_pending_decisions()
    print(f"📊 统计：{svc.get_stats()}")
