"""
MDE v15.0 长期主义策略示例
- 归因分析策略
- 组合风控策略
- 热配置策略
"""

from mde_core import BaseStrategy, register_strategy
from mde_core.data import fusion_engine
from mde_core import (
    attribution_engine, portfolio_risk_manager,
    hot_config, get_trace_id, TraceContext
)
from typing import Dict, Any, Optional

@register_strategy
class AttributionAwareStrategy(BaseStrategy):
    """
    归因感知策略
    定期分析盈亏来源，自动调整
    """
    
    name = "attribution_aware"
    version = "1.0.0"
    
    def on_init(self):
        self.ctx.logger.info("初始化归因感知策略")
        self.returns = []
        self.benchmarks = [0.01, 0.02, -0.01]  # 模拟大盘
        self.costs = []
    
    def on_bar(self, bar: Dict[str, Any]) -> Optional[int]:
        # 模拟收益
        ret = bar.get('change', 0.0)
        self.returns.append(ret)
        
        # 每 10 次分析一次
        if len(self.returns) % 10 == 0:
            result = attribution_engine.analyze(self.returns, self.benchmarks, self.costs)
            if result:
                self.ctx.logger.info(f"归因分析：{result.conclusion}")
                if "失效" in result.conclusion:
                    self.ctx.logger.warning("策略可能失效，建议暂停")
                    return 0
        
        # 正常逻辑
        news = fusion_engine.get_news(limit=1)
        if news and news[0].sentiment > 0.3:
            return 1
        return 0

@register_strategy
class PortfolioSafeStrategy(BaseStrategy):
    """
    组合安全策略
    受组合风控约束
    """
    
    name = "portfolio_safe"
    version = "1.0.0"
    
    def on_init(self):
        self.ctx.logger.info("初始化组合安全策略")
    
    def on_bar(self, bar: Dict[str, Any]) -> Optional[int]:
        symbol = bar.get('symbol', 'UNKNOWN')
        
        # 更新持仓
        portfolio_risk_manager.update_position(
            self.name, symbol, 
            quantity=100, price=bar.get('price', 10.0),
            sector="Tech"
        )
        
        # 检查组合风险
        if portfolio_risk_manager.should_reduce_position():
            self.ctx.logger.warning("组合风险过高，暂停开仓")
            return 0
        
        # 正常逻辑
        return 1

@register_strategy
class HotConfigStrategy(BaseStrategy):
    """
    热配置策略
    参数动态调整
    """
    
    name = "hot_config_demo"
    version = "1.0.0"
    
    def on_init(self):
        self.ctx.logger.info("初始化热配置策略")
        # 从热配置读取参数
        self.threshold = hot_config.get('strategies.my_strategy.threshold', 0.3) if hot_config else 0.3
    
    def on_bar(self, bar: Dict[str, Any]) -> Optional[int]:
        # 使用动态阈值
        sentiment = 0.5  # 模拟
        if sentiment > self.threshold:
            with TraceContext() as ctx:
                ctx.set('action', 'buy')
                ctx.set('threshold', self.threshold)
                self.ctx.logger.info(f"[{get_trace_id()}] 买入 (threshold={self.threshold})")
            return 1
        return 0

__all__ = ['AttributionAwareStrategy', 'PortfolioSafeStrategy', 'HotConfigStrategy']
