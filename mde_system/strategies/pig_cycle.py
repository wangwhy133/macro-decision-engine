"""
MDE 猪周期策略示例
"""

from .strategy import BaseStrategy, StrategyContext, register_strategy
from typing import Dict, Any, Optional

@register_strategy
class PigCycleStrategy(BaseStrategy):
    """猪周期策略"""
    
    name = "pig_cycle"
    version = "1.0.0"
    author = "MDE Team"
    
    def on_init(self):
        self.threshold = self.ctx.config.get('pain_threshold', 0.85)
        self._initialized = True
    
    def on_bar(self, bar: Dict[str, Any]) -> Optional[int]:
        if not self._initialized:
            return 0
        
        pain_index = bar.get('pain_index', 0)
        
        if pain_index > self.threshold:
            return 1  # 买入
        elif pain_index < self.threshold * 0.5:
            return -1  # 卖出
        
        return 0  # 持有

__all__ = ['PigCycleStrategy']
