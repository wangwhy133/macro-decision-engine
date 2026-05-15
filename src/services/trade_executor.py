# src/services/trade_executor.py
"""
交易执行器 (Trade Executor)

功能:
1. 接收 MDE 信号 (BUY/SELL/HOLD + 仓位)
2. 调用券商 API 下单 (模拟/实盘)
3. 记录交易日志
4. 风控二次校验

支持模式:
- Paper Trading (模拟盘)
- Live Trading (实盘，需对接券商 API)
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum

from src.utils.logger import setup_logger
from src.risk.position_sizer import get_position_sizer
from src.risk.risk_control import get_risk_control, TradeAction

logger = setup_logger("MDE.TradeExecutor")

class TradingMode(Enum):
    PAPER = "paper"
    LIVE = "live"

class TradeExecutor:
    """交易执行器"""
    
    def __init__(self, mode: TradingMode = TradingMode.PAPER, capital: float = 100000):
        self.mode = mode
        self.capital = capital
        self.position_sizer = get_position_sizer(capital)
        self.risk_control = get_risk_control()
        self.log_file = "logs/trade_logs.json"
        
        os.makedirs("logs", exist_ok=True)
    
    def execute_signal(
        self,
        symbol: str,
        signal: str,  # BUY/SELL/HOLD
        signal_strength: float,  # 0-10
        price: float,
        win_rate: float = 0.55,
        profit_loss_ratio: float = 2.0,
        volatility: float = 0.02
    ) -> Dict[str, Any]:
        """
        执行交易信号
        
        Args:
            symbol: 交易标的
            signal: 信号类型
            signal_strength: 信号强度
            price: 当前价格
            win_rate: 胜率
            profit_loss_ratio: 盈亏比
            volatility: 波动率
        
        Returns:
            执行结果
        """
        # 1. 风控二次校验
        risk_action, risk_reason = self.risk_control.check_trade_permission(
            data_source="real",  # 实盘数据
            features={"is_simulated": False},
            decision={"action": signal}
        )
        
        if risk_action == TradeAction.BLOCK:
            logger.warning(f"🚫 风控阻断：{risk_reason}")
            return {"status": "blocked", "reason": risk_reason}
        
        # 2. 计算仓位
        if signal in ["BUY", "SELL"]:
            position_info = self.position_sizer.calculate_position(
                price=price,
                signal_strength=signal_strength,
                win_rate=win_rate,
                profit_loss_ratio=profit_loss_ratio,
                volatility=volatility
            )
        else:
            position_info = {"action": "HOLD", "shares": 0, "amount": 0}
        
        # 3. 执行交易
        if position_info["action"] == "HOLD" or signal == "HOLD":
            logger.info(f"⚪ {symbol}: 持有观望")
            result = {"status": "hold", "symbol": symbol}
        elif position_info["shares"] > 0:
            # 下单
            order_result = self._place_order(
                symbol=symbol,
                side=signal.lower(),
                shares=position_info["shares"],
                price=price
            )
            result = {**position_info, **order_result}
        else:
            result = {"status": "no_position", "reason": "信号强度不足"}
        
        # 4. 记录日志
        self._log_trade(result)
        
        return result
    
    def _place_order(
        self,
        symbol: str,
        side: str,
        shares: int,
        price: float
    ) -> Dict[str, Any]:
        """下单 (模拟或实盘)"""
        timestamp = datetime.now().isoformat()
        
        if self.mode == TradingMode.PAPER:
            # 模拟盘
            logger.info(f"📝 [模拟] {side.upper()} {symbol} {shares}股 @ {price}")
            return {
                "status": "executed",
                "mode": "paper",
                "symbol": symbol,
                "side": side,
                "shares": shares,
                "price": price,
                "timestamp": timestamp,
                "message": f"模拟单已下：{side} {shares}股"
            }
        else:
            # 实盘 (需对接真实 API)
            # TODO: 接入富途/盈透/IBKR API
            logger.warning(f"⚠️ [实盘] 实盘接口未接入，转为模拟单：{side} {symbol} {shares}股")
            return {
                "status": "simulated_live",
                "mode": "live_simulated",
                "symbol": symbol,
                "side": side,
                "shares": shares,
                "price": price,
                "timestamp": timestamp,
                "message": "实盘接口待开发，已转为模拟"
            }
    
    def _log_trade(self, result: Dict[str, Any]):
        """记录交易日志"""
        logs = []
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r') as f:
                    logs = json.load(f)
            except:
                logs = []
        
        logs.append(result)
        
        # 保留最近 1000 条
        logs = logs[-1000:]
        
        with open(self.log_file, 'w') as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)
    
    def get_trade_history(self, limit: int = 10) -> list:
        """获取交易历史"""
        if not os.path.exists(self.log_file):
            return []
        
        with open(self.log_file, 'r') as f:
            logs = json.load(f)
        
        return logs[-limit:]

# 全局单例
_executor = None

def get_executor(mode: str = "paper", capital: float = 100000) -> TradeExecutor:
    """获取执行器"""
    global _executor
    if _executor is None:
        _executor = TradeExecutor(
            mode=TradingMode(mode),
            capital=capital
        )
    return _executor

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    executor = get_executor(mode="paper", capital=100000)
    
    # 测试：强买入信号
    result = executor.execute_signal(
        symbol="002714.SZ",  # 牧原股份
        signal="BUY",
        signal_strength=9.0,
        price=40.5,
        win_rate=0.65,
        profit_loss_ratio=3.0,
        volatility=0.02
    )
    
    print(f"执行结果：{result}")
