"""
MDE 硬止损与逃生通道
极端行情下的最后防线
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime

@dataclass
class HardStopConfig:
    """硬止损配置"""
    max_drawdown_total: float = 0.20      # 总资金最大回撤 20%
    max_drawdown_daily: float = 0.05      # 单日最大回撤 5%
    max_loss_per_trade: float = 0.02      # 单笔最大亏损 2%
    max_volatility_trigger: float = 0.10  # 波动率触发阈值 10%

class HardStopEngine:
    """硬止损引擎"""
    
    def __init__(self, config: HardStopConfig = None):
        self.config = config or HardStopConfig()
        self.initial_capital = 100000.0
        self.current_capital = self.initial_capital
        self.daily_start_capital = self.initial_capital
        self.is_triggered = False
        self.trigger_reason: Optional[str] = None
        self.trigger_time: Optional[datetime] = None
    
    def update_capital(self, current: float):
        """更新当前资金"""
        self.current_capital = current
    
    def reset_daily(self):
        """每日重置"""
        self.daily_start_capital = self.current_capital
    
    def check(self, current_price: float, entry_price: float, volatility: float = 0.0) -> bool:
        """
        检查是否触发硬止损
        :return: True 表示触发，需立即清仓并暂停
        """
        if self.is_triggered:
            return True
        
        # 1. 总资金回撤检查
        total_dd = (self.initial_capital - self.current_capital) / self.initial_capital
        if total_dd > self.config.max_drawdown_total:
            self._trigger(f"总资金回撤超限：{total_dd:.2%}")
            return True
        
        # 2. 单日回撤检查
        daily_dd = (self.daily_start_capital - self.current_capital) / self.daily_start_capital
        if daily_dd > self.config.max_drawdown_daily:
            self._trigger(f"单日回撤超限：{daily_dd:.2%}")
            return True
        
        # 3. 单笔交易亏损检查 (需传入当前交易信息)
        if entry_price > 0:
            trade_loss = (entry_price - current_price) / entry_price
            if trade_loss > self.config.max_loss_per_trade:
                self._trigger(f"单笔亏损超限：{trade_loss:.2%}")
                return True
        
        # 4. 波动率触发 (极端行情)
        if volatility > self.config.max_volatility_trigger:
            self._trigger(f"波动率过高：{volatility:.2%}")
            return True
        
        return False
    
    def _trigger(self, reason: str):
        self.is_triggered = True
        self.trigger_reason = reason
        self.trigger_time = datetime.now()
        print(f"🚨 硬止损触发！原因：{reason}")
    
    def reset(self):
        """重置状态 (需人工确认)"""
        self.is_triggered = False
        self.trigger_reason = None
        self.trigger_time = None
        print("✅ 硬止损已重置")

# 全局实例
hard_stop_engine = HardStopEngine()

__all__ = ['HardStopConfig', 'HardStopEngine', 'hard_stop_engine']
