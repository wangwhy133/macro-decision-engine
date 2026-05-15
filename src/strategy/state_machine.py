# src/strategy/state_machine.py
"""
状态机策略引擎 (State Machine Strategy Engine)

核心理念:
1. 状态驱动: 根据当前持仓状态 (Empty/Holding) 决定动作
2. 规则明确: 杜绝“看着办”，一切量化
3. 动态调仓: 信号强弱变化时自动加减仓

状态流转:
- Empty (空仓) 
  -> 信号强 (Strength > 7): Open (开仓)
  -> 信号中 (4 < Strength <= 7): Watch (观望，防止假突破)
  -> 信号弱: Wait

- Holding (持仓)
  -> 信号增强 (Strength 上升): Add (加仓)
  -> 信号减弱但仍强 (Strength 下降但 > 6): Hold (持有)
  -> 信号转弱 (Strength < 4): Reduce (减仓)
  -> 信号消失 (Strength < 2) 或 触发止损: Close (清仓)
"""

from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass
from src.utils.logger import setup_logger

logger = setup_logger("MDE.Strategy")

class PositionState(Enum):
    EMPTY = "empty"
    HOLDING = "holding"

class Action(Enum):
    WAIT = "WAIT"       # 观望
    OPEN = "OPEN"       # 开仓
    ADD = "ADD"         # 加仓
    HOLD = "HOLD"       # 持有 (不操作)
    REDUCE = "REDUCE"   # 减仓
    CLOSE = "CLOSE"     # 清仓

@dataclass
class PositionInfo:
    """持仓信息"""
    state: PositionState
    shares: int = 0
    avg_price: float = 0.0
    unrealized_pnl: float = 0.0

class StrategyEngine:
    """策略状态机引擎"""
    
    def __init__(
        self,
        open_threshold: float = 7.0,      # 开仓阈值
        add_threshold: float = 8.5,       # 加仓阈值
        reduce_threshold: float = 4.0,    # 减仓阈值
        close_threshold: float = 2.0,     # 清仓阈值
        stop_loss_pct: float = 0.05       # 止损比例 5%
    ):
        self.open_threshold = open_threshold
        self.add_threshold = add_threshold
        self.reduce_threshold = reduce_threshold
        self.close_threshold = close_threshold
        self.stop_loss_pct = stop_loss_pct
    
    def decide(
        self,
        symbol: str,
        signal_strength: float,  # 0-10
        current_price: float,
        position: PositionInfo,
        target_position_size: int  # 目标总仓位 (由仓位管理器计算)
    ) -> Dict[str, Any]:
        """
        根据信号和当前状态生成操作指令
        
        Returns:
            包含 action, shares, reason 的字典
        """
        action = Action.WAIT
        shares = 0
        reason = ""
        
        # 1. 检查止损 (最高优先级)
        if position.state == PositionState.HOLDING:
            pnl_ratio = (current_price - position.avg_price) / position.avg_price
            if pnl_ratio < -self.stop_loss_pct:
                action = Action.CLOSE
                shares = position.shares
                reason = f"触发止损 (亏损 {pnl_ratio:.2%} < -{self.stop_loss_pct:.2%})"
                return self._build_result(symbol, action, shares, reason)
        
        # 2. 状态机逻辑
        if position.state == PositionState.EMPTY:
            # 空仓逻辑
            if signal_strength >= self.open_threshold:
                action = Action.OPEN
                shares = target_position_size
                reason = f"信号强度 {signal_strength} >= {self.open_threshold}, 开仓"
            elif signal_strength >= self.open_threshold - 1.5:
                action = Action.WAIT
                reason = f"信号强度 {signal_strength} 中等，观望"
            else:
                reason = f"信号强度 {signal_strength} 不足，等待"
        
        elif position.state == PositionState.HOLDING:
            # 持仓逻辑
            current_value = position.shares * current_price
            target_value = target_position_size * current_price
            
            if signal_strength >= self.add_threshold and position.shares < target_position_size:
                # 加仓: 信号极强且未达目标仓位
                action = Action.ADD
                shares = target_position_size - position.shares
                reason = f"信号增强 ({signal_strength}), 加仓 {shares} 股"
            
            elif signal_strength < self.reduce_threshold:
                # 减仓/清仓: 信号转弱
                if signal_strength < self.close_threshold:
                    action = Action.CLOSE
                    shares = position.shares
                    reason = f"信号消失 ({signal_strength}), 清仓"
                else:
                    # 减仓一半
                    action = Action.REDUCE
                    shares = int(position.shares * 0.5)
                    reason = f"信号减弱 ({signal_strength}), 减仓 {shares} 股"
            
            else:
                action = Action.HOLD
                reason = f"信号稳定 ({signal_strength}), 持有"
        
        return self._build_result(symbol, action, shares, reason)
    
    def _build_result(self, symbol: str, action: Action, shares: int, reason: str) -> Dict:
        return {
            "symbol": symbol,
            "action": action.value,
            "shares": shares,
            "reason": reason,
            "timestamp": __import__('datetime').datetime.now().isoformat()
        }

# 全局单例
_strategy_engine = None

def get_strategy_engine() -> StrategyEngine:
    global _strategy_engine
    if _strategy_engine is None:
        _strategy_engine = StrategyEngine()
    return _strategy_engine

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    engine = get_strategy_engine()
    
    # 场景 1: 空仓，强信号 -> 开仓
    pos1 = PositionInfo(state=PositionState.EMPTY)
    res1 = engine.decide("PIG", 9.0, 14.0, pos1, target_position_size=1000)
    print(f"场景 1: {res1}")
    
    # 场景 2: 持仓，信号减弱 -> 减仓
    pos2 = PositionInfo(state=PositionState.HOLDING, shares=1000, avg_price=14.0)
    res2 = engine.decide("PIG", 3.5, 14.5, pos2, target_position_size=1000)
    print(f"场景 2: {res2}")
    
    # 场景 3: 持仓，触发止损 -> 清仓
    pos3 = PositionInfo(state=PositionState.HOLDING, shares=1000, avg_price=14.0)
    res3 = engine.decide("PIG", 5.0, 13.2, pos3, target_position_size=1000) # 跌 5.7%
    print(f"场景 3: {res3}")
