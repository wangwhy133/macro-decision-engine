"""
MDE 执行器抽象 (模拟/实盘/影子)
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from datetime import datetime

class BaseExecutor(ABC):
    """执行器基类"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._balance = config.get('initial_cash', 100000.0)
        self._positions: Dict[str, float] = {}
    
    @abstractmethod
    def submit_order(self, symbol: str, side: str, quantity: float, price: float) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        pass
    
    def get_position(self, symbol: str) -> float:
        return self._positions.get(symbol, 0.0)
    
    def get_balance(self) -> float:
        return self._balance

class PaperExecutor(BaseExecutor):
    """模拟盘执行器"""
    
    def submit_order(self, symbol: str, side: str, quantity: float, price: float) -> Dict[str, Any]:
        cost = quantity * price
        if side == 'buy':
            if cost > self._balance:
                return {"status": "rejected", "reason": "insufficient_balance"}
            self._balance -= cost
            self._positions[symbol] = self._positions.get(symbol, 0) + quantity
        else:
            if self._positions.get(symbol, 0) < quantity:
                return {"status": "rejected", "reason": "insufficient_position"}
            self._balance += cost
            self._positions[symbol] = self._positions.get(symbol, 0) - quantity
        
        return {
            "status": "filled",
            "order_id": f"paper_{datetime.now().timestamp()}",
            "symbol": symbol, "side": side,
            "quantity": quantity, "price": price,
            "mode": "paper"
        }
    
    def cancel_order(self, order_id: str) -> bool:
        return True

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
