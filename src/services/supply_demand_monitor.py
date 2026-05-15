# src/services/supply_demand_monitor.py
"""
供需监控器 (Supply-Demand Monitor)

功能:
1. 监控关键行业 (猪/半导体/存储) 的供需指标
2. 计算痛苦指数和疯狂指数
3. 生成早期预警信号
4. 与 MDE Agent 集成

核心逻辑:
- 供过于求 -> 痛苦指数高 -> 关注反转 (买入)
- 供不应求 -> 疯狂指数高 -> 关注崩盘 (卖出)
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from src.utils.logger import setup_logger
from src.data.cycle_indicators import (
    calculate_pain_index,
    calculate_mania_index,
    detect_inflection_point,
    analyze_cycle_stage
)

logger = setup_logger("MDE.SupplyDemandMonitor")


class SupplyDemandMonitor:
    """供需监控器"""
    
    def __init__(self):
        # 行业配置
        self.industries = {
            "pig": {
                "name": "生猪养殖",
                "cost_line": 15.0,  # 元/公斤 (假设成本线)
                "data_source": "manual",  # 目前手动输入，后续接 API
            },
            "memory": {
                "name": "存储芯片",
                "capex_benchmark": 20.0,  # 资本开支基准
            },
            "shipping": {
                "name": "集运",
                "cost_line": 1000.0,  # 假想成本
            }
        }
        
        self.monitor_file = "data/supply_demand_state.json"
        os.makedirs("data", exist_ok=True)
    
    def update_industry_data(
        self,
        industry: str,
        current_price: float,
        duration_months: int = 0,
        loss_ratio: float = 0.0,
        capex_growth: float = 0.0,
        price_momentum: float = 0.0,
        inventory_trend: str = "stable"
    ):
        """
        更新行业数据 (可手动调用，或从 API 获取)
        
        Args:
            industry: 行业代码 (pig/memory/shipping)
            current_price: 当前价格
            duration_months: 低于成本线持续月数
            loss_ratio: 行业亏损面
            capex_growth: 资本开支增速
            price_momentum: 价格动量
            inventory_trend: 库存趋势
        """
        if industry not in self.industries:
            logger.warning(f"未知行业：{industry}")
            return
        
        config = self.industries[industry]
        cost_line = config.get("cost_line", current_price * 0.9)
        
        # 计算指数
        pain = calculate_pain_index(
            current_price, cost_line, duration_months, loss_ratio
        )
        
        mania = calculate_mania_index(
            capex_growth, price_momentum, 0, 0.0
        )
        
        # 判断阶段
        stage_info = analyze_cycle_stage(pain, mania, inventory_trend)
        
        # 生成信号
        signal = "NEUTRAL"
        if stage_info["confidence"] > 0.7:
            signal = stage_info["action"].split()[0]  # BUY/SELL/HOLD
        
        result = {
            "industry": industry,
            "industry_name": config["name"],
            "timestamp": datetime.now().isoformat(),
            "current_price": current_price,
            "cost_line": cost_line,
            "pain_index": pain,
            "mania_index": mania,
            "stage": stage_info["stage"],
            "action": stage_info["action"],
            "signal": signal,
            "confidence": stage_info["confidence"],
            "inventory_trend": inventory_trend
        }
        
        # 保存状态
        self._save_state(result)
        
        # 输出日志
        self._log_signal(result)
        
        return result
    
    def _save_state(self, result: Dict):
        """保存最新状态"""
        history = []
        if os.path.exists(self.monitor_file):
            try:
                with open(self.monitor_file, 'r') as f:
                    history = json.load(f)
            except:
                history = []
        
        # 只保留最近 100 条
        history = [h for h in history if h.get('industry') != result['industry']]
        history.append(result)
        history = history[-100:]
        
        with open(self.monitor_file, 'w') as f:
            json.dump(history, f, indent=2)
    
    def _log_signal(self, result: Dict):
        """记录信号日志"""
        industry_name = result['industry_name']
        stage = result['stage']
        signal = result['signal']
        confidence = result['confidence']
        
        if signal != "NEUTRAL" and confidence > 0.6:
            emoji = "🟢" if "BUY" in signal else "🔴"
            logger.warning(f"{emoji} [{industry_name}] 周期信号：{stage} -> {signal} (置信度：{confidence:.0%})")
        else:
            logger.info(f"⚪ [{industry_name}] 当前状态：{stage}")
    
    def get_all_signals(self) -> List[Dict]:
        """获取所有行业信号"""
        if not os.path.exists(self.monitor_file):
            return []
        
        with open(self.monitor_file, 'r') as f:
            return json.load(f)
    
    def get_opportunities(self) -> List[Dict]:
        """获取高置信度机会 (痛苦或疯狂)"""
        signals = self.get_all_signals()
        opportunities = []
        
        for s in signals:
            if s['pain_index'] > 70:
                opportunities.append({
                    **s,
                    "type": "BOTTOM_FISHING",  # 抄底机会
                    "reason": f"痛苦指数 {s['pain_index']:.1f} (行业极度亏损)"
                })
            elif s['mania_index'] > 70:
                opportunities.append({
                    **s,
                    "type": "TOP_AVOIDING",  # 逃顶机会
                    "reason": f"疯狂指数 {s['mania_index']:.1f} (行业极度狂热)"
                })
        
        return sorted(opportunities, key=lambda x: x.get('confidence', 0), reverse=True)


# 全局单例
_monitor = None

def get_monitor() -> SupplyDemandMonitor:
    """获取监控器实例"""
    global _monitor
    if _monitor is None:
        _monitor = SupplyDemandMonitor()
    return _monitor


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    monitor = get_monitor()
    
    # 模拟更新生猪数据 (假设全行业亏损，痛苦指数高)
    print("=== 更新生猪行业数据 ===")
    pig_signal = monitor.update_industry_data(
        industry="pig",
        current_price=14.0,  # 低于成本 15
        duration_months=10,  # 已亏损 10 个月
        loss_ratio=0.85,     # 85% 亏损面
        inventory_trend="decreasing"  # 库存开始下降 (信号!)
    )
    print(f"生猪信号：{pig_signal}")
    
    # 模拟更新存储芯片数据 (假设疯狂扩产)
    print("\n=== 更新存储芯片行业数据 ===")
    mem_signal = monitor.update_industry_data(
        industry="memory",
        current_price=100.0,
        capex_growth=55.0,    # 资本开支 +55%
        price_momentum=80.0,  # 价格 +80%
        inventory_trend="increasing"  # 库存开始累积
    )
    print(f"存储信号：{mem_signal}")
    
    # 获取机会
    print("\n=== 周期机会 ===")
    opps = monitor.get_opportunities()
    for opp in opps:
        print(f"{opp['industry_name']}: {opp['type']} - {opp['reason']}")
