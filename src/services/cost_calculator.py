# src/services/cost_calculator.py
"""
交易成本计算器 (生产级)

功能:
1. 手续费计算
2. 滑点成本计算
3. 印花税计算
4. 市场冲击成本
5. 完整成本汇总

使用示例:
    from src.services.cost_calculator import CostCalculator
    
    calc = CostCalculator()
    total_cost = calc.calculate_total_cost(price=400, quantity=100, side='BUY')
    print(f"交易成本：{total_cost}")
"""

from typing import Dict, Any
from src.utils.logger import setup_logger

logger = setup_logger("MDE.CostCalculator")


class CostCalculator:
    """交易成本计算器"""
    
    def __init__(
        self,
        commission_rate: float = 0.001,      # 手续费率 0.1%
        slippage_rate: float = 0.0005,       # 滑点 0.05%
        stamp_duty_rate: float = 0.001,      # 印花税 0.1% (卖出时收取)
        market_impact_rate: float = 0.0002   # 市场冲击 0.02%
    ):
        """
        初始化成本计算器
        
        Args:
            commission_rate: 手续费率
            slippage_rate: 滑点率
            stamp_duty_rate: 印花税率
            market_impact_rate: 市场冲击率
        """
        self.commission_rate = commission_rate
        self.slippage_rate = slippage_rate
        self.stamp_duty_rate = stamp_duty_rate
        self.market_impact_rate = market_impact_rate
    
    def calculate_commission(self, price: float, quantity: int) -> float:
        """
        计算手续费
        
        Args:
            price: 成交价格
            quantity: 成交数量
        
        Returns:
            手续费金额
        """
        return price * quantity * self.commission_rate
    
    def calculate_slippage(self, price: float, quantity: int, side: str) -> float:
        """
        计算滑点成本
        
        Args:
            price: 预期价格
            quantity: 成交数量
            side: 买卖方向 ('BUY' 或 'SELL')
        
        Returns:
            滑点成本
        """
        # 滑点总是成本，无论买卖
        return price * quantity * self.slippage_rate
    
    def calculate_stamp_duty(self, price: float, quantity: int, side: str) -> float:
        """
        计算印花税
        
        Args:
            price: 成交价格
            quantity: 成交数量
            side: 买卖方向
        
        Returns:
            印花税金额 (仅卖出时收取)
        """
        if side.upper() == 'SELL':
            return price * quantity * self.stamp_duty_rate
        return 0.0
    
    def calculate_market_impact(self, price: float, quantity: int) -> float:
        """
        计算市场冲击成本
        
        Args:
            price: 成交价格
            quantity: 成交数量
        
        Returns:
            市场冲击成本
        """
        return price * quantity * self.market_impact_rate
    
    def calculate_total_cost(
        self,
        price: float,
        quantity: int,
        side: str
    ) -> Dict[str, float]:
        """
        计算完整交易成本
        
        Args:
            price: 成交价格
            quantity: 成交数量
            side: 买卖方向 ('BUY' 或 'SELL')
        
        Returns:
            成本明细和总计
        """
        commission = self.calculate_commission(price, quantity)
        slippage = self.calculate_slippage(price, quantity, side)
        stamp_duty = self.calculate_stamp_duty(price, quantity, side)
        market_impact = self.calculate_market_impact(price, quantity)
        
        total = commission + slippage + stamp_duty + market_impact
        
        return {
            'commission': commission,
            'slippage': slippage,
            'stamp_duty': stamp_duty,
            'market_impact': market_impact,
            'total': total,
            'price': price,
            'quantity': quantity,
            'side': side
        }
    
    def calculate_break_even_return(
        self,
        price: float,
        quantity: int,
        side: str
    ) -> float:
        """
        计算盈亏平衡所需的回报率
        
        Args:
            price: 成交价格
            quantity: 成交数量
            side: 买卖方向
        
        Returns:
            盈亏平衡所需回报率 (小数)
        """
        cost_info = self.calculate_total_cost(price, quantity, side)
        total_cost = cost_info['total']
        principal = price * quantity
        
        # 盈亏平衡需要覆盖成本
        return total_cost / principal
    
    def get_cost_percentage(self) -> Dict[str, float]:
        """
        获取各项成本占比
        
        Returns:
            成本占比字典
        """
        total_rate = (
            self.commission_rate +
            self.slippage_rate +
            self.stamp_duty_rate +
            self.market_impact_rate
        )
        
        return {
            'commission_rate': self.commission_rate,
            'slippage_rate': self.slippage_rate,
            'stamp_duty_rate': self.stamp_duty_rate,
            'market_impact_rate': self.market_impact_rate,
            'total_rate': total_rate
        }


# 全局成本计算器实例
_global_calculator = None


def get_cost_calculator() -> CostCalculator:
    """获取全局成本计算器"""
    global _global_calculator
    if _global_calculator is None:
        _global_calculator = CostCalculator()
    return _global_calculator


if __name__ == "__main__":
    # 测试成本计算
    import logging
    logging.basicConfig(level=logging.INFO)
    
    calc = CostCalculator()
    
    # 测试买入
    print("=== 买入成本 ===")
    buy_cost = calc.calculate_total_cost(price=400, quantity=100, side='BUY')
    for k, v in buy_cost.items():
        print(f"{k}: {v:.4f}")
    
    print("\n=== 卖出成本 ===")
    sell_cost = calc.calculate_total_cost(price=400, quantity=100, side='SELL')
    for k, v in sell_cost.items():
        print(f"{k}: {v:.4f}")
    
    print("\n=== 盈亏平衡点 ===")
    be_return = calc.calculate_break_even_return(price=400, quantity=100, side='BUY')
    print(f"买入后需要上涨 {be_return:.2%} 才能盈亏平衡")
    
    print("\n=== 成本占比 ===")
    percentages = calc.get_cost_percentage()
    for k, v in percentages.items():
        print(f"{k}: {v:.4%}")
