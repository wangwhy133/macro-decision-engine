"""
MDE v13.0 高可用策略示例
- 自适应参数策略
- 影子校验策略
- 资源感知策略
"""

from mde_core import BaseStrategy, register_strategy
from mde_core.data import fusion_engine, aggregator
from mde_core import (
    watchdog, shadow_checker, param_optimizer,
    TradeRecord, datetime
)
from typing import Dict, Any, Optional

@register_strategy
class AdaptiveParamStrategy(BaseStrategy):
    """
    自适应参数策略
    定期滚动优化策略参数
    """
    
    name = "adaptive_param"
    version = "1.0.0"
    
    def on_init(self):
        self.ctx.logger.info("初始化自适应参数策略")
        self.last_optimize = datetime.now()
        self.params = param_optimizer.best_params or {'threshold': 0.3}
    
    def on_bar(self, bar: Dict[str, Any]) -> Optional[int]:
        # 检查是否需要重新优化
        if param_optimizer.should_reoptimize(self.last_optimize):
            self.ctx.logger.info("🔄 开始重新优化参数...")
            # 模拟优化 (实际需传入历史数据)
            self.params = param_optimizer.optimize(None, None)
            self.last_optimize = datetime.now()
        
        # 使用最新参数
        threshold = self.params.get('threshold', 0.3)
        
        # 简单逻辑
        news = fusion_engine.get_news(limit=1)
        if news and news[0].sentiment > threshold:
            return 1
        return 0

@register_strategy
class ShadowValidateStrategy(BaseStrategy):
    """
    影子校验策略
    对比实盘与回测差异，偏差过大自动熔断
    """
    
    name = "shadow_validate"
    version = "1.0.0"
    
    def on_init(self):
        self.ctx.logger.info("初始化影子校验策略")
    
    def on_trade(self, trade_info: Dict[str, Any]):
        # 记录实盘交易
        trade = TradeRecord(
            symbol=trade_info.get('symbol', ''),
            side=trade_info.get('side', ''),
            price=trade_info.get('price', 0),
            quantity=trade_info.get('quantity', 0),
            timestamp=datetime.now(),
            mode='live'
        )
        shadow_checker.record_live_trade(trade)
        
        # 如果偏差过大，触发熔断
        if shadow_checker.deviation_alert:
            self.ctx.logger.error("⚠️  实盘与回测偏差过大，建议检查策略！")
            # 可在此处触发紧急制动

@register_strategy
class ResourceAwareStrategy(BaseStrategy):
    """
    资源感知策略
    在资源紧张时降低交易频率或暂停
    """
    
    name = "resource_aware"
    version = "1.0.0"
    
    def on_init(self):
        self.ctx.logger.info("初始化资源感知策略")
        self.check_count = 0
    
    def on_bar(self, bar: Dict[str, Any]) -> Optional[int]:
        self.check_count += 1
        
        # 每 10 次检查一次资源
        if self.check_count % 10 == 0:
            if not watchdog.heartbeat():
                self.ctx.logger.warning("⚠️  资源紧张，暂停交易")
                return 0
        
        # 正常逻辑
        news = fusion_engine.get_news(limit=1)
        if news and news[0].sentiment > 0.3:
            return 1
        return 0

__all__ = ['AdaptiveParamStrategy', 'ShadowValidateStrategy', 'ResourceAwareStrategy']
