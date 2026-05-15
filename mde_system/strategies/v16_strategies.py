"""
MDE v16.0 逃生与透明化策略示例
"""

from mde_core import BaseStrategy, register_strategy
from mde_core.data import fusion_engine
from mde_core import (
    hard_stop_engine, decision_logger, config_auditor,
    DecisionLog, get_trace_id, TraceContext
)
from typing import Dict, Any, Optional
from datetime import datetime

@register_strategy
class HardStopStrategy(BaseStrategy):
    """
    硬止损策略
    极端行情下无条件清仓
    """
    
    name = "hard_stop_demo"
    version = "1.0.0"
    
    def on_init(self):
        self.ctx.logger.info("初始化硬止损策略")
        self.entry_price = 0.0
    
    def on_bar(self, bar: Dict[str, Any]) -> Optional[int]:
        current_price = bar.get('price', 10.0)
        volatility = bar.get('volatility', 0.0)
        
        # 检查硬止损
        if hard_stop_engine.check(current_price, self.entry_price, volatility):
            self.ctx.logger.error(f"🚨 硬止损触发！暂停交易。原因：{hard_stop_engine.trigger_reason}")
            return 0  # 停止交易
        
        # 模拟建仓
        if self.entry_price == 0:
            self.entry_price = current_price
        
        # 正常逻辑
        return 1

@register_strategy
class TransparentStrategy(BaseStrategy):
    """
    透明化策略
    每一笔交易都记录详细决策理由
    """
    
    name = "transparent_demo"
    version = "1.0.0"
    
    def on_bar(self, bar: Dict[str, Any]) -> Optional[int]:
        symbol = bar.get('symbol', 'UNKNOWN')
        price = bar.get('price', 10.0)
        sentiment = 0.6  # 模拟情感
        
        # 决策理由
        reason = f"情感分 {sentiment:.2f} > 阈值 0.5"
        confidence = 0.85
        
        # 记录决策日志
        log = DecisionLog(
            timestamp=datetime.now().isoformat(),
            strategy_name=self.name,
            symbol=symbol,
            action="BUY",
            reason=reason,
            data_context={"sentiment": sentiment, "price": price},
            confidence=confidence,
            trace_id=get_trace_id() or "unknown"
        )
        decision_logger.log(log)
        
        self.ctx.logger.info(f"[{get_trace_id()}] 买入 {symbol}，理由：{reason}")
        return 1

@register_strategy
class AuditAwareStrategy(BaseStrategy):
    """
    配置审计感知策略
    关键操作前自动备份配置
    """
    
    name = "audit_aware"
    version = "1.0.0"
    
    def on_init(self):
        self.ctx.logger.info("初始化配置审计策略")
        # 初始化时备份
        config_auditor.save_snapshot(operator="strategy_init", comment="策略初始化备份")
    
    def on_bar(self, bar: Dict[str, Any]) -> Optional[int]:
        # 模拟参数调整
        # 调整前自动备份
        config_auditor.save_snapshot(operator="auto", comment="参数调整前备份")
        return 1

__all__ = ['HardStopStrategy', 'TransparentStrategy', 'AuditAwareStrategy']
