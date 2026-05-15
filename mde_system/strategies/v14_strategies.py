"""
MDE v14.0 金融级风控与灰度发布策略示例
"""

from mde_core import BaseStrategy, register_strategy
from mde_core.data import fusion_engine
from mde_core import (
    risk_engine, release_manager,
    TraceContext, get_trace_id
)
from typing import Dict, Any, Optional

@register_strategy
class DynamicRiskStrategy(BaseStrategy):
    """
    动态风控策略
    根据波动率自动调整仓位
    """
    
    name = "dynamic_risk"
    version = "1.0.0"
    
    def on_init(self):
        self.ctx.logger.info("初始化动态风控策略")
    
    def on_bar(self, bar: Dict[str, Any]) -> Optional[int]:
        # 1. 获取动态仓位上限
        position_limit = risk_engine.get_position_limit()
        
        # 2. 检查是否应该停止交易
        if risk_engine.should_halt():
            self.ctx.logger.warning("⚠️  波动率过高，停止交易")
            return 0
        
        # 3. 正常逻辑
        news = fusion_engine.get_news(limit=1)
        if news and news[0].sentiment > 0.3:
            # 根据动态仓位下单
            quantity = int(position_limit * 1000)  # 示例
            self.ctx.logger.info(f"买入 {quantity} 股 (仓位上限:{position_limit:.2%})")
            return 1
        
        return 0

@register_strategy
class CanaryReleaseStrategy(BaseStrategy):
    """
    灰度发布策略示例
    """
    
    name = "canary_demo"
    version = "1.0.0"
    
    def on_init(self):
        # 部署新版本
        self.release = release_manager.deploy(self.name, self.version)
        self.ctx.logger.info(f"策略 {self.name} 灰度发布")
    
    def on_bar(self, bar: Dict[str, Any]) -> Optional[int]:
        # 检查是否应该回滚
        if self.release.should_rollback():
            self.release.rollback()
            return 0
        
        # 获取当前资金比例
        scale = self.release.get_position_scale()
        
        # 模拟交易
        success = True  # 实际应为下单结果
        self.release.record_trade(success)
        
        # 尝试提升阶段
        self.release.promote()
        
        with TraceContext() as ctx:
            ctx.set('stage', self.release.stage.name)
            self.ctx.logger.info(f"[{get_trace_id()}] 灰度阶段: {self.release.stage.name}, 资金比例: {scale:.2%}")
        
        return 1 if success else 0

__all__ = ['DynamicRiskStrategy', 'CanaryReleaseStrategy']
