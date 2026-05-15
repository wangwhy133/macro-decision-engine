# src/strategy/optimizer.py
"""
滚动窗口参数优化器 (Rolling Window Optimizer)

核心理念:
1. 市场风格在变，参数必须动态调整
2. 用过去的表现指导未来，但避免过拟合
3. 如果所有参数都失效，自动停止交易

逻辑:
- 每周回顾过去 N 笔交易
- 模拟不同参数组合下的收益
- 选择夏普比率/总收益 最高的参数组合作为下周参数
- 如果最佳组合仍亏损，触发“策略熔断”，暂停交易
"""

import json
import os
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import numpy as np
from src.utils.logger import setup_logger

logger = setup_logger("MDE.Optimizer")

@dataclass
class TradeRecord:
    """交易记录"""
    entry_price: float
    exit_price: float
    shares: int
    pnl: float  # 盈亏金额
    pnl_pct: float  # 盈亏比例
    params: Dict  # 当时的参数

class StrategyOptimizer:
    """策略优化器"""
    
    def __init__(
        self,
        window_size: int = 20,  # 回顾最近 20 笔交易
        min_trades_for_opt: int = 5,  # 至少 5 笔交易才优化
        stop_loss_threshold: float = -0.10  # 最大回撤 10% 停止策略
    ):
        self.window_size = window_size
        self.min_trades_for_opt = min_trades_for_opt
        self.stop_loss_threshold = stop_loss_threshold
        self.trade_history: List[TradeRecord] = []
        
        # 默认参数范围
        self.param_grid = {
            'open_threshold': [6.0, 6.5, 7.0, 7.5, 8.0],
            'add_threshold': [7.5, 8.0, 8.5, 9.0],
            'reduce_threshold': [3.0, 3.5, 4.0, 4.5],
            'stop_loss_pct': [0.03, 0.05, 0.07, 0.10]
        }
    
    def add_trade(self, record: TradeRecord):
        """添加交易记录"""
        self.trade_history.append(record)
        # 保持窗口大小
        if len(self.trade_history) > self.window_size + 10:
            self.trade_history = self.trade_history[-(self.window_size + 10):]
    
    def optimize(self) -> Tuple[Dict[str, float], bool]:
        """
        执行参数优化
        
        Returns:
            (最佳参数字典, 是否暂停交易)
        """
        if len(self.trade_history) < self.min_trades_for_opt:
            logger.info(f"交易记录不足 ({len(self.trade_history)})，使用默认参数")
            return self._get_default_params(), False
        
        # 取最近 N 笔交易
        recent_trades = self.trade_history[-self.window_size:]
        
        best_params = None
        best_score = -999999.0
        pause_trading = True
        
        # 网格搜索最佳参数
        for open_t in self.param_grid['open_threshold']:
            for add_t in self.param_grid['add_threshold']:
                for red_t in self.param_grid['reduce_threshold']:
                    for stop_t in self.param_grid['stop_loss_pct']:
                        
                        # 模拟该参数下的表现
                        score, total_pnl = self._simulate_params(
                            recent_trades, 
                            open_t, add_t, red_t, stop_t
                        )
                        
                        # 更新最优
                        if score > best_score:
                            best_score = score
                            best_params = {
                                'open_threshold': open_t,
                                'add_threshold': add_t,
                                'reduce_threshold': red_t,
                                'stop_loss_pct': stop_t
                            }
        
        # 检查是否所有参数都亏损 (策略失效)
        if best_score < 0:
            logger.warning("⚠️ 所有参数组合均亏损，触发策略熔断，暂停交易")
            return self._get_default_params(), True  # 暂停
        
        logger.info(f"✅ 优化完成：最佳参数 {best_params}, 模拟得分 {best_score:.2f}")
        return best_params, False
    
    def _simulate_params(
        self, 
        trades: List[TradeRecord], 
        open_t: float, add_t: float, red_t: float, stop_t: float
    ) -> Tuple[float, float]:
        """
        模拟特定参数下的表现
        简化逻辑：只计算符合该参数的交易盈亏
        """
        total_pnl = 0.0
        count = 0
        
        for t in trades:
            # 简化回测：假设参数能过滤掉部分亏损单
            # 实际逻辑应重新跑一遍状态机，这里简化为加权
            if t.pnl > 0:
                total_pnl += t.pnl_pct
                count += 1
            else:
                # 如果止损更严格，可能少亏
                if t.pnl_pct > -stop_t: 
                    total_pnl += t.pnl_pct
                    count += 1
        
        if count == 0:
            return 0.0, 0.0
        
        # 评分 = 总收益 * 胜率 (简化版夏普)
        win_rate = count / len(trades)
        score = total_pnl * win_rate
        
        return score, total_pnl
    
    def _get_default_params(self) -> Dict[str, float]:
        return {
            'open_threshold': 7.0,
            'add_threshold': 8.5,
            'reduce_threshold': 4.0,
            'stop_loss_pct': 0.05
        }

# 全局单例
_optimizer = None

def get_optimizer() -> StrategyOptimizer:
    global _optimizer
    if _optimizer is None:
        _optimizer = StrategyOptimizer()
    return _optimizer

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    opt = get_optimizer()
    
    # 模拟添加一些交易记录
    for i in range(10):
        pnl = 0.05 if i % 2 == 0 else -0.03
        opt.add_trade(TradeRecord(
            entry_price=100, exit_price=100, shares=100,
            pnl=pnl*100, pnl_pct=pnl, params={}
        ))
    
    best_params, pause = opt.optimize()
    print(f"最佳参数：{best_params}")
    print(f"是否暂停：{pause}")
