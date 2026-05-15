"""
MDE 策略基类
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import numpy as np

class StrategyContext:
    """策略上下文"""
    def __init__(self, data_provider=None, executor=None, logger=None, config=None):
        self.data = data_provider
        self.executor = executor
        self.logger = logger
        self.config = config or {}

class BaseStrategy(ABC):
    """策略基类"""
    
    name = "BaseStrategy"
    version = "1.0.0"
    author = "Unknown"
    
    def __init__(self, context: StrategyContext):
        self.ctx = context
        self.position = 0
        self._initialized = False
    
    @abstractmethod
    def on_init(self):
        pass
    
    @abstractmethod
    def on_bar(self, bar: Dict[str, Any]) -> Optional[int]:
        pass
    
    def on_trade(self, trade_info: Dict[str, Any]):
        pass
    
    def calculate_health_score(self, returns: List[float]) -> float:
        """计算策略健康度评分 (0-100)"""
        if len(returns) < 2:
            return 100.0
        returns = np.array(returns)
        sharpe = np.mean(returns) / (np.std(returns) + 1e-9) * np.sqrt(252)
        win_rate = np.sum(returns > 0) / len(returns)
        score = (sharpe * 20 + win_rate * 80)
        return max(0, min(100, score))

def register_strategy(cls):
    """策略注册装饰器"""
    return cls

__all__ = ['BaseStrategy', 'StrategyContext', 'register_strategy']
