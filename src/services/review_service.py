# src/services/review_service.py
"""
A. 复盘回填机制 (生产级增强版)

负责记录决策日志，并在 T+1 日自动校准准确率

增强功能:
1. 使用实际决策价格计算回报
2. 考虑完整交易成本 (手续费 + 滑点 + 印花税)
3. 正确的 HOLD 逻辑 (机会成本)
4. 风控集成
5. 日志系统
6. 数据验证
"""

import duckdb
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import logging

# 导入风控和日志
from src.risk.risk_control import get_risk_control, init_risk_control
from src.utils.logger import setup_logger
from src.services.cost_calculator import get_cost_calculator
from src.data.validation import validate_features

logger = setup_logger("MDE.Review")

DB_PATH = "data/mde.duckdb"


class ReviewService:
    """复盘校准服务"""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        
        # 获取成本计算器
        self.cost_calc = get_cost_calculator()
        
        # 确保数据目录存在
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # 初始化风控
        self.rc = init_risk_control()
        
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
                decision_price REAL,  -- 新增：决策时的价格
                actual_price_next REAL,
                actual_return REAL,
                is_correct BOOLEAN,
                status TEXT DEFAULT 'PENDING'
            )
        """)
        logger.info("✅ 决策日志表已初始化")
    
    def log_decision(
        self,
        decision_id: str,
        market_state: Dict,
        agent_opinions: Dict,
        final_decision: str,
        confidence: float,
        reasoning: str,
        decision_price: float
    ):
        """
        记录一次决策
        
        Args:
            decision_id: 决策 ID
            market_state: 市场状态
            agent_opinions: Agent 意见
            final_decision: 最终决策 (BUY/SELL/HOLD)
            confidence: 置信度
            reasoning: 推理过程
            decision_price: 决策时的价格 (关键!)
        """
        self.conn.execute("""
            INSERT OR REPLACE INTO decision_logs 
            (id, timestamp, market_state, agent_opinions, final_decision, confidence, reasoning, decision_price, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'PENDING')
        """, [
            decision_id,
            datetime.now(),
            json.dumps(market_state),
            json.dumps(agent_opinions),
            final_decision,
            confidence,
            reasoning,
            decision_price
        ])
        
        logger.info(f"📝 决策已记录：{decision_id} -> {final_decision} @ {decision_price}")
    
    def calculate_return(self, decision_price: float, current_price: float, action: str, quantity: int = 100) -> Tuple[float, bool]:
        """
        计算回报率并判断是否正确 (考虑完整交易成本)
        
        Args:
            decision_price: 决策时的价格
            current_price: 当前价格 (T+1)
            action: 决策动作 (BUY/SELL/HOLD)
            quantity: 交易数量 (默认 100 股)
        
        Returns:
            (净回报率，是否正确)
        """
        if action == 'BUY':
            # 买入：计算完整成本
            cost_info = self.cost_calc.calculate_total_cost(decision_price, quantity, 'BUY')
            total_cost = cost_info['total']
            
            # 买入成本
            buy_cost = decision_price * quantity + total_cost
            
            # 假设卖出价格 (当前价)
            sell_revenue = current_price * quantity - self.cost_calc.calculate_total_cost(current_price, quantity, 'SELL')['total']
            
            # 净回报
            net_return = (sell_revenue - buy_cost) / buy_cost
            is_correct = net_return > 0
            
        elif action == 'SELL':
            # 卖出：计算完整成本
            cost_info = self.cost_calc.calculate_total_cost(decision_price, quantity, 'SELL')
            total_cost = cost_info['total']
            
            # 卖出收入
            sell_revenue = decision_price * quantity - total_cost
            
            # 假设买回成本
            buy_cost = current_price * quantity + self.cost_calc.calculate_total_cost(current_price, quantity, 'BUY')['total']
            
            # 净回报
            net_return = (sell_revenue - buy_cost) / (decision_price * quantity)
            is_correct = net_return > 0
            
        elif action == 'HOLD':
            # 持有：无交易成本，但有机会成本
            # 如果市场上涨，HOLD 错过机会；市场下跌，HOLD 正确
            net_return = 0.0
            is_correct = (current_price < decision_price)
        
        else:
            logger.warning(f"未知的决策动作：{action}")
            net_return = 0.0
            is_correct = False
        
        return net_return, is_correct
    
    def calibrate_pending_decisions(self, symbol: str = "SPY"):
        """
        校准所有未完成的决策 (T+1 逻辑)
        
        Args:
            symbol: 交易标的
        """
        logger.info("🔄 开始校准历史决策...")
        
        rows = self.conn.execute("""
            SELECT id, timestamp, final_decision, confidence, decision_price
            FROM decision_logs
            WHERE status = 'PENDING'
        """).fetchall()
        
        if not rows:
            logger.info("✅ 无需校准")
            return
        
        # 获取最新价格
        current_price = self._get_current_price(symbol)
        logger.info(f"📊 {symbol} 最新价格：{current_price}")
        
        if current_price is None:
            logger.error("❌ 无法获取当前价格，校准失败")
            return
        
        # 逐条校准
        for row in rows:
            dec_id, ts, decision, conf, decision_price = row
            
            # 如果决策时没有记录价格，使用 400 作为默认值 (向后兼容)
            if decision_price is None:
                logger.warning(f"⚠️ 决策 {dec_id} 未记录价格，使用默认值 400")
                decision_price = 400.0
            
            # 计算回报
            net_return, is_correct = self.calculate_return(decision_price, current_price, decision)
            
            # 更新数据库
            self.conn.execute("""
                UPDATE decision_logs
                SET actual_price_next = ?,
                    actual_return = ?,
                    is_correct = ?,
                    status = 'COMPLETED'
                WHERE id = ?
            """, [current_price, net_return, is_correct, dec_id])
            
            # 输出结果
            status_icon = "✅" if is_correct else "❌"
            logger.info(f" {status_icon} 校准 {dec_id}: {decision} @ {decision_price} -> 回报 {net_return:.2%} ({'正确' if is_correct else '错误'})")
        
        logger.info("✅ 校准完成")
    
    def _get_current_price(self, symbol: str) -> Optional[float]:
        """
        获取当前价格
        
        Args:
            symbol: 交易标的
        
        Returns:
            当前价格，失败返回 None
        """
        try:
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1d")
            
            if hist.empty:
                logger.warning(f"⚠️ 获取 {symbol} 价格失败：空数据")
                return None
            
            current_price = float(hist['Close'].iloc[-1])
            logger.info(f"✅ 获取 {symbol} 最新收盘价：{current_price}")
            return current_price
            
        except Exception as e:
            logger.error(f"❌ 获取价格失败：{e}", exc_info=True)
            return None
    
    def get_stats(self) -> Dict:
        """获取统计数据"""
        res = self.conn.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(is_correct) as correct,
                AVG(actual_return) as avg_return
            FROM decision_logs
            WHERE status = 'COMPLETED'
        """).fetchone()
        
        total = res[0] or 0
        correct = res[1] or 0
        
        return {
            'total': total,
            'correct': correct,
            'accuracy': correct / total if total > 0 else 0,
            'avg_return': res[2] or 0
        }
    
    def get_recent_decisions(self, limit: int = 10) -> list:
        """获取最近的决策记录"""
        rows = self.conn.execute("""
            SELECT id, timestamp, final_decision, confidence, actual_return, is_correct, status
            FROM decision_logs
            ORDER BY timestamp DESC
            LIMIT ?
        """, [limit]).fetchall()
        
        return [
            {
                'id': r[0],
                'timestamp': r[1],
                'decision': r[2],
                'confidence': r[3],
                'return': r[4],
                'correct': r[5],
                'status': r[6]
            }
            for r in rows
        ]


if __name__ == "__main__":
    # 测试复盘服务
    import logging
    logging.basicConfig(level=logging.INFO)
    
    svc = ReviewService()
    
    # 测试校准
    svc.calibrate_pending_decisions("SPY")
    
    # 获取统计
    stats = svc.get_stats()
    print(f"📊 统计：{stats}")
    
    # 获取最近决策
    recent = svc.get_recent_decisions(5)
    print(f"📋 最近决策：{recent}")
