# src/portfolio/manager.py
"""
多资产组合管理器 (Multi-Asset Portfolio Manager)

核心理念:
1. 策略与资产解耦: 同一套策略逻辑，可应用于猪、玉米、标普等多个标的
2. 统一风控: 全局总仓位控制，防止多资产相关性导致的系统性风险
3. 资金动态分配: 根据各资产波动率和相关性，动态分配资金权重
4. 并发执行: 多线程/异步并发监控和执行多个标的

架构:
PortfolioManager (总控)
  ├── AssetContext (资产上下文：猪)
  ├── AssetContext (资产上下文：玉米)
  └── AssetContext (资产上下文：标普)
"""

import threading
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.utils.logger import setup_logger
from src.strategy.state_machine import get_strategy_engine, PositionInfo, Action
from src.risk.position_sizer import get_position_sizer

logger = setup_logger("MDE.Portfolio")

@dataclass
class AssetContext:
    """资产上下文"""
    symbol: str
    name: str
    capital_allocation: float  # 分配资金
    current_price: float
    position: PositionInfo
    last_signal: Optional[Dict] = None
    is_active: bool = True

class PortfolioManager:
    """组合管理器"""
    
    def __init__(
        self,
        total_capital: float,
        max_total_exposure: float = 0.8,  # 总仓位上限 80%
        max_single_exposure: float = 0.2   # 单资产上限 20%
    ):
        self.total_capital = total_capital
        self.max_total_exposure = max_total_exposure
        self.max_single_exposure = max_single_exposure
        
        self.assets: Dict[str, AssetContext] = {}
        self.strategy_engine = get_strategy_engine()
        self.position_sizer = get_position_sizer(total_capital)
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.running = False
    
    def add_asset(self, context: AssetContext):
        """添加资产"""
        self.assets[context.symbol] = context
        logger.info(f"添加资产：{context.name} ({context.symbol})")
    
    def remove_asset(self, symbol: str):
        """移除资产"""
        if symbol in self.assets:
            del self.assets[symbol]
            logger.info(f"移除资产：{symbol}")
    
    def run_cycle(self):
        """
        执行一轮全资产扫描与决策
        流程: 获取信号 -> 生成指令 -> 全局风控 -> 执行
        """
        if not self.assets:
            logger.warning("组合中无资产")
            return
        
        logger.info(f"开始组合扫描，共 {len(self.assets)} 个资产")
        
        # 并发处理每个资产
        futures = {}
        for symbol, ctx in self.assets.items():
            if ctx.is_active:
                future = self.executor.submit(self._process_asset, symbol, ctx)
                futures[future] = symbol
        
        # 等待所有任务完成
        for future in as_completed(futures):
            symbol = futures[future]
            try:
                result = future.result()
                logger.debug(f"资产 {symbol} 处理完成：{result}")
            except Exception as e:
                logger.error(f"资产 {symbol} 处理失败：{e}")
    
    def _process_asset(self, symbol: str, ctx: AssetContext) -> Dict:
        """处理单个资产"""
        # 1. 获取信号 (调用爬虫或数据源)
        # 简化：假设已有 signal_strength
        signal_strength = self._get_signal_strength(symbol)
        
        if signal_strength < 2:
            return {"symbol": symbol, "action": "WAIT", "reason": "无显著信号"}
        
        # 2. 状态机决策
        decision = self.strategy_engine.decide(
            symbol=symbol,
            signal_strength=signal_strength,
            current_price=ctx.current_price,
            position=ctx.position,
            target_position_size=int((self.total_capital * self.max_single_exposure) / ctx.current_price)
        )
        
        # 3. 全局风控检查 (简化：检查总仓位)
        total_exposure = self._calculate_total_exposure()
        action = decision.get('action', 'WAIT')
        if total_exposure > self.max_total_exposure and action in ['OPEN', 'ADD']:
            logger.warning(f"总仓位超限 ({total_exposure:.1%} > {self.max_total_exposure:.1%}), 拒绝开仓/加仓")
            return {"symbol": symbol, "action": "REJECTED", "reason": "总仓位超限"}
        
        # 4. 执行 (模拟或实盘)
        # self._execute_trade(decision)
        
        return decision
    
    def _get_signal_strength(self, symbol: str) -> float:
        """获取信号强度 (模拟，实际应调用爬虫或监控器)"""
        # 简化：随机生成或调用外部接口
        # 实际应调用：supply_demand_monitor.get_signal(symbol)
        import random
        return random.uniform(0, 10)
    
    def _calculate_total_exposure(self) -> float:
        """计算总风险敞口"""
        total = 0.0
        for ctx in self.assets.values():
            state_str = str(ctx.position.state)
            if 'HOLD' in state_str.upper():
                total += (ctx.position.shares * ctx.current_price) / self.total_capital
        return total
    
    def start(self):
        """启动组合管理循环"""
        self.running = True
        logger.info("🚀 组合管理器已启动")
        while self.running:
            self.run_cycle()
            time.sleep(60)  # 每分钟扫描一次
    
    def stop(self):
        """停止"""
        self.running = False
        self.executor.shutdown(wait=True)
        logger.info("组合管理器已停止")

# 全局单例
_portfolio_mgr = None

def get_portfolio_manager(capital: float = 100000) -> PortfolioManager:
    global _portfolio_mgr
    if _portfolio_mgr is None:
        _portfolio_mgr = PortfolioManager(capital)
    return _portfolio_mgr

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    pm = get_portfolio_manager(100000)
    
    # 添加资产
    pm.add_asset(AssetContext("PIG", "生猪", 30000, 14.0, PositionInfo(state="EMPTY")))
    pm.add_asset(AssetContext("CORN", "玉米", 30000, 2.5, PositionInfo(state="EMPTY")))
    pm.add_asset(AssetContext("SPX", "标普 500", 40000, 4500, PositionInfo(state="EMPTY")))
    
    # 运行一轮
    pm.run_cycle()
    
    pm.stop()
