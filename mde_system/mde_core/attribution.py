"""
MDE 策略归因引擎
分析策略盈亏来源：市场/参数/数据/运气
"""

from typing import Dict, List, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class AttributionResult:
    """归因结果"""
    strategy_name: str
    total_return: float
    market_beta: float      # 市场贡献 (大盘涨跌)
    alpha: float            # 超额收益 (策略能力)
    timing: float           # 择时贡献
    selection: float        # 选股贡献
    cost_drag: float        # 成本拖累 (手续费/滑点)
    conclusion: str         # 结论建议

class AttributionEngine:
    """归因引擎"""
    
    def __init__(self):
        pass
    
    def analyze(self, 
                strategy_returns: List[float], 
                benchmark_returns: List[float],
                costs: List[float]) -> AttributionResult:
        """
        简单归因分析
        Alpha = 策略收益 - Beta * 市场收益
        """
        if not strategy_returns or not benchmark_returns:
            return None
        
        total_ret = sum(strategy_returns)
        market_ret = sum(benchmark_returns)
        cost_drag = sum(costs) if costs else 0.0
        
        # 简化 Beta 假设为 1 (实际需回归计算)
        beta = 1.0
        alpha = total_ret - beta * market_ret
        
        # 归因结论
        conclusion = "策略表现正常"
        if alpha < -0.05:
            conclusion = "策略失效，建议检查参数或暂停"
        elif cost_drag > abs(total_ret) * 0.5:
            conclusion = "成本过高，建议优化交易频率或滑点控制"
        elif market_ret > 0 and total_ret < 0:
            conclusion = "严重跑输市场，建议检查选股逻辑"
        
        return AttributionResult(
            strategy_name="unknown",
            total_return=total_ret,
            market_beta=market_ret,
            alpha=alpha,
            timing=0.0,  # 需更复杂计算
            selection=alpha,
            cost_drag=cost_drag,
            conclusion=conclusion
        )

# 全局实例
attribution_engine = AttributionEngine()

__all__ = ['AttributionEngine', 'AttributionResult', 'attribution_engine']
