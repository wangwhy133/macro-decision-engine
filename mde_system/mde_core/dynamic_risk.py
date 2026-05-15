"""
MDE 动态风控引擎
基于实时波动率调整仓位和止损
"""

import math
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime

@dataclass
class RiskMetrics:
    """实时风险指标"""
    volatility: float  # 波动率
    max_drawdown: float  # 最大回撤
    var_95: float  # 95% VaR
    liquidity_score: float  # 流动性评分 (0-1)

class DynamicRiskEngine:
    """动态风控引擎"""
    
    def __init__(self, base_position_limit: float = 0.2):
        self.base_position_limit = base_position_limit
        self.current_position_limit = base_position_limit
        self.volatility_window: List[float] = []
        self.alert_threshold = 0.05  # 波动率超过 5% 触发
        
    def update_metrics(self, returns: List[float], liquidity_score: float = 1.0):
        """更新风险指标"""
        if len(returns) < 2:
            return
        
        # 1. 计算波动率 (年化)
        import statistics
        vol = statistics.stdev(returns) * math.sqrt(252)
        self.volatility_window.append(vol)
        
        # 2. 计算最大回撤 (简化)
        cum_returns = [1.0]
        for r in returns:
            cum_returns.append(cum_returns[-1] * (1 + r))
        peak = max(cum_returns)
        trough = min(cum_returns)
        max_dd = (peak - trough) / peak if peak > 0 else 0
        
        # 3. 计算 VaR (简化：正态分布假设)
        var_95 = vol * 1.65
        
        # 4. 动态调整仓位上限
        self._adjust_position_limit(vol, max_dd, var_95, liquidity_score)
    
    def _adjust_position_limit(self, vol: float, max_dd: float, var_95: float, liquidity: float):
        """根据风险指标动态调整仓位上限"""
        # 波动率飙升 -> 降仓
        if vol > self.alert_threshold:
            factor = self.alert_threshold / vol
            self.current_position_limit = self.base_position_limit * factor * liquidity
        else:
            self.current_position_limit = self.base_position_limit
        
        # 最大回撤过大 -> 强制降仓
        if max_dd > 0.1:
            self.current_position_limit *= 0.5
        
        # 确保不为负
        self.current_position_limit = max(0.01, self.current_position_limit)
    
    def get_position_limit(self) -> float:
        """获取当前允许的仓位上限"""
        return self.current_position_limit
    
    def should_halt(self) -> bool:
        """判断是否应该停止交易"""
        if len(self.volatility_window) == 0:
            return False
        # 波动率极高时停止
        return self.volatility_window[-1] > 0.2  # 年化波动率>20%

# 全局实例
risk_engine = DynamicRiskEngine()

__all__ = ['DynamicRiskEngine', 'RiskMetrics', 'risk_engine']
