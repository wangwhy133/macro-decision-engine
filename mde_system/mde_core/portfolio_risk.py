"""
MDE 组合级风控
监控多策略整体敞口、相关性和集中度
"""

from typing import Dict, List, Any
from dataclasses import dataclass
import math

@dataclass
class PortfolioRiskMetrics:
    """组合风险指标"""
    total_exposure: float       # 总敞口
    sector_concentration: Dict[str, float]  # 行业集中度
    max_single_position: float  # 最大单一持仓占比
    correlation_risk: float     # 相关性风险 (简化)
    is_diversified: bool        # 是否分散

class PortfolioRiskManager:
    """组合风控管理器"""
    
    def __init__(self, max_total_exposure: float = 0.8, max_single_ratio: float = 0.2):
        self.max_total_exposure = max_total_exposure
        self.max_single_ratio = max_single_ratio
        self.positions: Dict[str, Dict[str, Any]] = {}  # strategy -> position
    
    def update_position(self, strategy: str, symbol: str, quantity: float, price: float, sector: str = "unknown"):
        """更新持仓"""
        if strategy not in self.positions:
            self.positions[strategy] = {}
        self.positions[strategy][symbol] = {
            'quantity': quantity,
            'price': price,
            'value': quantity * price,
            'sector': sector
        }
    
    def get_metrics(self) -> PortfolioRiskMetrics:
        """计算组合风险指标"""
        total_value = 0.0
        sector_map: Dict[str, float] = {}
        max_single = 0.0
        
        # 汇总
        for strategy, pos_map in self.positions.items():
            for symbol, data in pos_map.items():
                val = data['value']
                total_value += val
                sector = data.get('sector', 'unknown')
                sector_map[sector] = sector_map.get(sector, 0.0) + val
                if val > max_single:
                    max_single = val
        
        # 集中度
        concentration = {k: v/total_value if total_value > 0 else 0 for k, v in sector_map.items()} if total_value > 0 else {}
        
        # 单一最大占比
        max_single_ratio = max_single / total_value if total_value > 0 else 0
        
        # 简化相关性风险 (假设所有持仓同涨同跌则风险高)
        correlation_risk = 1.0 if len(concentration) == 1 else 0.5
        
        is_diversified = (max_single_ratio < self.max_single_ratio and 
                          len(concentration) >= 3)
        
        return PortfolioRiskMetrics(
            total_exposure=total_value,
            sector_concentration=concentration,
            max_single_position=max_single_ratio,
            correlation_risk=correlation_risk,
            is_diversified=is_diversified
        )
    
    def should_reduce_position(self) -> bool:
        """判断是否应该减仓"""
        metrics = self.get_metrics()
        # 总敞口超限 或 未分散
        return (metrics.total_exposure > self.max_total_exposure * 1000000 or 
                not metrics.is_diversified)

# 全局实例
portfolio_risk_manager = PortfolioRiskManager()

__all__ = ['PortfolioRiskManager', 'PortfolioRiskMetrics', 'portfolio_risk_manager']
