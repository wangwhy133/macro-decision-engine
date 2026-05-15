"""
MDE 影子回测与实盘一致性校验
实时对比回测与实盘差异，防止"回测幻觉"
"""

from typing import Dict, List, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class TradeRecord:
    symbol: str
    side: str
    price: float
    quantity: float
    timestamp: datetime
    mode: str  # 'backtest' or 'live'

class ShadowBacktest:
    """影子回测校验器"""
    
    def __init__(self, tolerance: float = 0.05):
        self.tolerance = tolerance  # 允许偏差 5%
        self.live_trades: List[TradeRecord] = []
        self.backtest_trades: List[TradeRecord] = []
        self.deviation_alert = False
    
    def record_live_trade(self, trade: TradeRecord):
        self.live_trades.append(trade)
        self._check_deviation()
    
    def record_backtest_trade(self, trade: TradeRecord):
        self.backtest_trades.append(trade)
    
    def _check_deviation(self):
        """检查实盘与回测的偏差"""
        if not self.backtest_trades:
            return
        
        # 简单对比：最近一笔实盘 vs 最近一笔回测
        if self.live_trades and self.backtest_trades:
            live = self.live_trades[-1]
            backtest = self.backtest_trades[-1]
            
            # 价格偏差
            price_diff = abs(live.price - backtest.price) / backtest.price
            if price_diff > self.tolerance:
                self.deviation_alert = True
                print(f"⚠️  价格偏差过大！实盘:{live.price} vs 回测:{backtest.price} (偏差:{price_diff:.2%})")
            
            # 数量偏差
            qty_diff = abs(live.quantity - backtest.quantity) / backtest.quantity
            if qty_diff > self.tolerance:
                self.deviation_alert = True
                print(f"⚠️  数量偏差过大！实盘:{live.quantity} vs 回测:{backtest.quantity}")

class ParameterOptimizer:
    """滚动窗口参数优化器"""
    
    def __init__(self, window_days: int = 30, step_days: int = 5):
        self.window_days = window_days
        self.step_days = step_days
        self.best_params: Dict[str, Any] = {}
    
    def optimize(self, strategy, data: Any) -> Dict[str, Any]:
        """
        在滚动窗口上优化策略参数
        (简化版：实际需接入回测引擎)
        """
        # 模拟优化过程
        # 1. 切分时间窗口
        # 2. 网格搜索参数
        # 3. 选择夏普比率最高的参数
        print(f"🔄 正在优化参数 (窗口:{self.window_days}天)...")
        
        # 模拟返回
        self.best_params = {'threshold': 0.35, 'position': 0.2}
        return self.best_params
    
    def should_reoptimize(self, last_optimize_time: datetime) -> bool:
        """判断是否需要重新优化"""
        from datetime import timedelta
        return (datetime.now() - last_optimize_time).days >= self.step_days

# 全局实例
shadow_checker = ShadowBacktest()
param_optimizer = ParameterOptimizer()

__all__ = ['ShadowBacktest', 'ParameterOptimizer', 'shadow_checker', 'param_optimizer']
