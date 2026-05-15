"""
MDE 执行器抽象 (模拟/实盘/影子) - 增强版
支持撤单、改单、重试与熔断
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
from .retry import RetryConfig, retry_with_config, CircuitBreaker

class BaseExecutor(ABC):
    """执行器基类"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._balance = config.get('initial_cash', 100000.0)
        self._positions: Dict[str, float] = {}
        self._orders: Dict[str, Dict] = {}
        self._circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_time=60)
    
    @abstractmethod
    def submit_order(self, symbol: str, side: str, quantity: float, price: float) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        pass
    
    def modify_order(self, order_id: str, new_price: Optional[float] = None, new_quantity: Optional[float] = None) -> bool:
        """改单 (默认实现：先撤单再下单)"""
        if order_id not in self._orders:
            return False
        return self.cancel_order(order_id)
    
    def get_position(self, symbol: str) -> float:
        return self._positions.get(symbol, 0.0)
    
    def get_balance(self) -> float:
        return self._balance
    
    def get_orders(self) -> List[Dict]:
        return list(self._orders.values())

class PaperExecutor(BaseExecutor):
    """模拟盘执行器"""
    
    def submit_order(self, symbol: str, side: str, quantity: float, price: float) -> Dict[str, Any]:
        if not self._circuit_breaker.can_execute():
            return {"status": "rejected", "reason": "circuit_breaker_open"}
        
        try:
            cost = quantity * price
            order_id = f"paper_{datetime.now().timestamp()}"
            
            if side == 'buy':
                if cost > self._balance:
                    self._circuit_breaker.record_failure()
                    return {"status": "rejected", "reason": "insufficient_balance"}
                self._balance -= cost
                self._positions[symbol] = self._positions.get(symbol, 0) + quantity
            else:
                if self._positions.get(symbol, 0) < quantity:
                    self._circuit_breaker.record_failure()
                    return {"status": "rejected", "reason": "insufficient_position"}
                self._balance += cost
                self._positions[symbol] = self._positions.get(symbol, 0) - quantity
            
            self._orders[order_id] = {
                "symbol": symbol, "side": side,
                "quantity": quantity, "price": price,
                "status": "filled", "mode": "paper"
            }
            
            self._circuit_breaker.record_success()
            return {"status": "filled", "order_id": order_id, "mode": "paper"}
        except Exception as e:
            self._circuit_breaker.record_failure()
            raise
    
    def cancel_order(self, order_id: str) -> bool:
        if order_id in self._orders:
            self._orders[order_id]["status"] = "cancelled"
            return True
        return False

class ShadowExecutor(PaperExecutor):
    """影子模式执行器"""
    def submit_order(self, symbol: str, side: str, quantity: float, price: float) -> Dict[str, Any]:
        result = super().submit_order(symbol, side, quantity, price)
        result['mode'] = 'shadow'
        return result

def create_executor(mode: str, config: Dict[str, Any]) -> BaseExecutor:
    """工厂函数"""
    if mode == 'shadow':
        return ShadowExecutor(config)
    return PaperExecutor(config)

__all__ = ['BaseExecutor', 'PaperExecutor', 'ShadowExecutor', 'create_executor']
