# src/risk/position_sizer.py
"""
动态仓位管理模块 (Position Sizing)

核心理念:
1. 永不 All-in: 根据信号强度和风险动态调整仓位
2. 凯利公式优化: 避免过度下注导致破产
3. 风险平价: 波动率高的资产仓位低

使用示例:
    sizer = PositionSizer(capital=100000)
    position = sizer.calculate_position(
        signal_strength=8,  # 信号强度 0-10
        win_rate=0.65,      # 历史胜率
        profit_loss_ratio=2.5, # 盈亏比
        volatility=0.02     # 当前波动率
    )
    print(f"建议仓位：{position['recommended_size']} 股")
"""

import math
from typing import Dict, Optional
from src.utils.logger import setup_logger

logger = setup_logger("MDE.PositionSizer")


class PositionSizer:
    """动态仓位计算器"""
    
    def __init__(
        self,
        capital: float,
        max_position_ratio: float = 0.3,  # 单标的最大仓位 30%
        risk_per_trade: float = 0.02,     # 单笔风险 2%
        kelly_leverage: float = 0.25      # 凯利系数折扣 (0.25 表示使用 1/4 凯利)
    ):
        """
        Args:
            capital: 总资金
            max_position_ratio: 单标的最大仓位比例 (防黑天鹅)
            risk_per_trade: 单笔交易愿意承担的总资金风险比例
            kelly_leverage: 凯利系数折扣 (防过拟合)
        """
        self.capital = capital
        self.max_position_ratio = max_position_ratio
        self.risk_per_trade = risk_per_trade
        self.kelly_leverage = kelly_leverage
    
    def calculate_kelly_fraction(
        self,
        win_rate: float,
        profit_loss_ratio: float
    ) -> float:
        """
        计算凯利最优下注比例
        
        公式: f* = (p * b - q) / b
        p: 胜率
        b: 盈亏比 (平均盈利/平均亏损)
        q: 败率 (1-p)
        
        Returns:
            凯利比例 (0-1), 负数表示不下注
        """
        if win_rate <= 0 or win_rate >= 1:
            return 0.0
        
        if profit_loss_ratio <= 0:
            return 0.0
        
        loss_rate = 1 - win_rate
        
        # 凯利公式
        kelly = (win_rate * profit_loss_ratio - loss_rate) / profit_loss_ratio
        
        # 应用折扣 (防过拟合) 和 截断
        discounted_kelly = kelly * self.kelly_leverage
        return max(0.0, min(discounted_kelly, 1.0))
    
    def calculate_signal_strength_weight(self, strength: float) -> float:
        """
        将信号强度 (0-10) 映射为仓位权重 (0-1)
        
        逻辑:
        - 强度 < 4: 观望 (0)
        - 强度 4-6: 轻仓 (0.2-0.4)
        - 强度 6-8: 中仓 (0.4-0.7)
        - 强度 8-10: 重仓 (0.7-1.0)
        
        Returns:
            仓位权重
        """
        if strength < 4:
            return 0.0
        elif strength < 6:
            return 0.2 + (strength - 4) * 0.1  # 0.2 -> 0.4
        elif strength < 8:
            return 0.4 + (strength - 6) * 0.15 # 0.4 -> 0.7
        else:
            return 0.7 + (strength - 8) * 0.15 # 0.7 -> 1.0
    
    def calculate_position(
        self,
        price: float,
        signal_strength: float,  # 0-10
        win_rate: float = 0.55,
        profit_loss_ratio: float = 2.0,
        volatility: Optional[float] = None,
        stop_loss_pct: Optional[float] = None
    ) -> Dict:
        """
        综合计算建议仓位
        
        Args:
            price: 当前价格
            signal_strength: 信号强度 (0-10)
            win_rate: 预估胜率
            profit_loss_ratio: 预估盈亏比
            volatility: 波动率 (可选，用于波动率调整)
            stop_loss_pct: 止损百分比 (可选)
        
        Returns:
            包含建议股数、金额、风险敞口的字典
        """
        # 1. 基于信号强度的基础权重
        signal_weight = self.calculate_signal_strength_weight(signal_strength)
        
        if signal_weight == 0:
            return {
                "action": "HOLD",
                "shares": 0,
                "amount": 0,
                "reason": "信号强度不足 (<4)"
            }
        
        # 2. 基于凯利公式的理论仓位
        kelly_fraction = self.calculate_kelly_fraction(win_rate, profit_loss_ratio)
        
        # 3. 取两者较小值 (保守策略)
        # 信号强但凯利低 -> 听凯利的 (可能是陷阱)
        # 凯利高但信号弱 -> 听信号的 (时机未到)
        target_ratio = min(kelly_fraction, signal_weight)
        
        # 4. 应用最大仓位限制
        target_ratio = min(target_ratio, self.max_position_ratio)
        
        # 5. 波动率调整 (波动大则仓位小)
        if volatility and volatility > 0:
            vol_adjustment = min(1.0, 0.02 / (volatility + 1e-9)) # 基准波动率 2%
            target_ratio *= vol_adjustment
        
        # 6. 计算具体数值
        risk_amount = self.capital * self.risk_per_trade
        max_amount = self.capital * target_ratio
        
        # 如果有止损，根据止损距离调整仓位
        if stop_loss_pct and stop_loss_pct > 0:
            stop_loss_amount = risk_amount / stop_loss_pct
            max_amount = min(max_amount, stop_loss_amount)
        
        shares = int(max_amount / price)
        total_amount = shares * price
        
        # 风险敞口
        exposure = total_amount / self.capital
        
        return {
            "action": "BUY" if shares > 0 else "HOLD",
            "shares": shares,
            "price": price,
            "amount": total_amount,
            "exposure": exposure,
            "signal_strength": signal_strength,
            "kelly_fraction": kelly_fraction,
            "target_ratio": target_ratio,
            "reason": f"信号强度 {signal_strength}/10, 凯利 {kelly_fraction:.1%}"
        }
    
    def update_capital(self, new_capital: float):
        """更新资金量"""
        self.capital = new_capital
        logger.info(f"更新资金量：{new_capital}")


# 全局单例
_sizer = None

def get_position_sizer(capital: float = 100000) -> PositionSizer:
    """获取仓位计算器"""
    global _sizer
    if _sizer is None:
        _sizer = PositionSizer(capital)
    return _sizer


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    sizer = get_position_sizer(capital=100000)
    
    # 场景 1: 强信号 (痛苦指数高，强度 9)
    print("=== 场景 1: 强买入信号 ===")
    pos1 = sizer.calculate_position(
        price=14.0,
        signal_strength=9.0,
        win_rate=0.65,
        profit_loss_ratio=3.0,
        volatility=0.015
    )
    print(f"建议：{pos1['action']} {pos1['shares']} 股")
    print(f"金额：{pos1['amount']:.2f} (仓位 {pos1['exposure']:.1%})")
    print(f"理由：{pos1['reason']}")
    
    # 场景 2: 弱信号 (强度 5)
    print("\n=== 场景 2: 弱买入信号 ===")
    pos2 = sizer.calculate_position(
        price=14.0,
        signal_strength=5.0,
        win_rate=0.55,
        profit_loss_ratio=2.0
    )
    print(f"建议：{pos2['action']} {pos2['shares']} 股")
    print(f"金额：{pos2['amount']:.2f} (仓位 {pos2['exposure']:.1%})")
    
    # 场景 3: 无信号
    print("\n=== 场景 3: 无信号 ===")
    pos3 = sizer.calculate_position(
        price=14.0,
        signal_strength=3.0
    )
    print(f"建议：{pos3['action']} - {pos3['reason']}")
