# src/data/cycle_indicators.py
"""
周期指标计算模块 (Cycle Indicators)

核心逻辑:
1. 痛苦指数 (Misery Index): 衡量行业亏损程度 (用于判断底部)
2. 疯狂指数 (Mania Index): 衡量扩产狂热程度 (用于判断顶部)
3. 库存周期: 库存销售比的变动
4. 剪刀差: 价格与成本的背离

目标: 在"将发还未发"之际察觉信号
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from src.utils.logger import setup_logger

logger = setup_logger("MDE.CycleIndicators")


def calculate_pain_index(
    current_price: float,
    cost_line: float,
    duration_months: int,
    industry_loss_ratio: float
) -> float:
    """
    计算痛苦指数 (用于判断底部)
    
    逻辑: 价格低于成本线的时间越长、幅度越深、亏损面越大，痛苦指数越高，反转越近。
    
    Args:
        current_price: 当前价格
        cost_line: 行业平均成本线
        duration_months: 低于成本线持续的月数
        industry_loss_ratio: 行业亏损面比例 (0-1)
    
    Returns:
        痛苦指数 (0-100), >80 表示极度痛苦，即将反转
    """
    if current_price >= cost_line:
        return 0.0
    
    # 价格偏离度 (越深越痛苦)
    price_gap = (cost_line - current_price) / cost_line
    
    # 时间维度 (越久越痛苦)
    time_factor = min(duration_months / 12.0, 1.0)  # 最多算 1 年
    
    # 亏损面
    loss_factor = industry_loss_ratio
    
    # 综合计算 (权重可调)
    pain = (price_gap * 0.4 + time_factor * 0.3 + loss_factor * 0.3) * 100
    
    return min(pain, 100.0)


def calculate_mania_index(
    capex_growth: float,
    price_momentum: float,
    new_entrants: int,
    media_sentiment: float
) -> float:
    """
    计算疯狂指数 (用于判断顶部)
    
    逻辑: 资本开支增速越快、价格动量越强、新进入者越多、媒体越乐观，疯狂指数越高，崩盘越近。
    
    Args:
        capex_growth: 资本开支同比增速 (%)
        price_momentum: 价格动量 (同比涨幅 %)
        new_entrants: 新进入行业的企业数量 (归一化)
        media_sentiment: 媒体情绪 (0-1, 1 为极度乐观)
    
    Returns:
        疯狂指数 (0-100), >80 表示极度疯狂，即将崩盘
    """
    # 资本开支 (过热信号)
    capex_factor = min(capex_growth / 50.0, 1.0)  # 假设 50% 增长为极值
    
    # 价格动量 (逼空信号)
    momentum_factor = min(price_momentum / 100.0, 1.0)
    
    # 新进入者
    entrant_factor = min(new_entrants / 10.0, 1.0)
    
    # 情绪
    sentiment_factor = media_sentiment
    
    mania = (capex_factor * 0.4 + momentum_factor * 0.2 + entrant_factor * 0.2 + sentiment_factor * 0.2) * 100
    
    return min(mania, 100.0)


def detect_inflection_point(
    series: pd.Series,
    window: int = 6,
    threshold: float = 0.05
) -> Tuple[bool, str]:
    """
    检测拐点 (将发还未发的关键时刻)
    
    逻辑: 当指标在底部/顶部盘整后，首次突破阈值，或出现底背离/顶背离。
    
    Args:
        series: 时间序列数据 (如存栏量、库存)
        window: 观察窗口
        threshold: 变化阈值
    
    Returns:
        (是否拐点, 信号类型)
    """
    if len(series) < window * 2:
        return False, "数据不足"
    
    # 最近 window 期的平均值 vs 再之前 window 期
    recent_avg = series.iloc[-window:].mean()
    prev_avg = series.iloc[-window*2:-window].mean()
    
    # 变化率
    change_rate = (recent_avg - prev_avg) / (prev_avg + 1e-9)
    
    # 判断趋势反转
    if change_rate > threshold:
        return True, "向上拐点 (供给收缩/需求启动)"
    elif change_rate < -threshold:
        return True, "向下拐点 (供给扩张/需求萎缩)"
    
    return False, "无显著拐点"


def analyze_cycle_stage(
    pain_index: float,
    mania_index: float,
    inventory_trend: str
) -> Dict[str, any]:
    """
    综合判断周期阶段
    
    Returns:
        包含阶段名称、操作建议、置信度的字典
    """
    stage = "Unknown"
    action = "HOLD"
    confidence = 0.0
    
    if pain_index > 70:
        stage = "萧条末期 (痛苦期)"
        action = "BUY (左侧布局)"
        confidence = pain_index / 100.0
    elif pain_index > 40 and pain_index <= 70:
        stage = "萧条中期 (磨底期)"
        action = "WATCH (等待信号)"
        confidence = 0.5
    elif mania_index > 70:
        stage = "繁荣末期 (疯狂期)"
        action = "SELL (左侧离场)"
        confidence = mania_index / 100.0
    elif mania_index > 40 and mania_index <= 70:
        stage = "繁荣中期 (扩张期)"
        action = "HOLD (持有享受泡沫)"
        confidence = 0.6
    else:
        # 结合库存趋势
        if inventory_trend == "decreasing":
            stage = "复苏早期"
            action = "BUY (右侧跟随)"
            confidence = 0.7
        elif inventory_trend == "increasing":
            stage = "衰退早期"
            action = "SELL (右侧避险)"
            confidence = 0.7
        else:
            stage = "震荡期"
            action = "HOLD"
            confidence = 0.4
    
    return {
        "stage": stage,
        "action": action,
        "confidence": confidence,
        "pain_index": pain_index,
        "mania_index": mania_index
    }


if __name__ == "__main__":
    # 测试
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # 模拟生猪行业数据
    # 假设当前猪粮比 4.5 (成本线 6.0), 已亏损 10 个月，亏损面 80%
    pain = calculate_pain_index(4.5, 6.0, 10, 0.8)
    print(f"痛苦指数：{pain:.2f}")
    
    # 模拟半导体行业数据
    # 资本开支 +40%, 价格 +60%, 新进入者多，情绪乐观 0.9
    mania = calculate_mania_index(40.0, 60.0, 5, 0.9)
    print(f"疯狂指数：{mania:.2f}")
    
    # 判断阶段
    stage_info = analyze_cycle_stage(pain, mania, "decreasing")
    print(f"周期阶段：{stage_info['stage']}")
    print(f"建议操作：{stage_info['action']}")
