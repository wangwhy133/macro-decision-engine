"""
MDE v12.0 高级策略示例
- 事件链追踪策略
- 情感趋势策略
- 健康源切换策略
"""

from mde_core import BaseStrategy, register_strategy
from mde_core.data import (
    fusion_engine, analyzer, health_checker,
    aggregator, EventChain
)
from typing import Dict, Any, Optional

@register_strategy
class EventChainStrategy(BaseStrategy):
    """
    事件链追踪策略
    监控事件演化，在情感趋势向上时介入
    """
    
    name = "event_chain_tracker"
    version = "1.0.0"
    author = "MDE Team"
    
    def on_init(self):
        self.ctx.logger.info("初始化事件链追踪策略")
        self.min_chain_length = 3  # 至少 3 条新闻才触发
        self.sentiment_threshold = 0.2
    
    def on_bar(self, bar: Dict[str, Any]) -> Optional[int]:
        symbol = bar.get('symbol', '')
        
        # 1. 获取新闻
        news_list = fusion_engine.get_news(symbol=symbol, limit=10)
        if not news_list:
            return 0
        
        # 2. 聚合事件链
        chains = aggregator.process_news(news_list)
        
        # 3. 寻找有潜力的事件链
        for chain in chains:
            summary = chain.get_summary()
            
            # 条件：新闻数量足够 + 情感趋势向上
            if (summary['news_count'] >= self.min_chain_length and 
                summary['sentiment_trend'] > self.sentiment_threshold):
                
                self.ctx.logger.info(
                    f"【事件链机会】{summary['seed_title'][:20]}... "
                    f"新闻数:{summary['news_count']} "
                    f"趋势:{summary['sentiment_trend']:.2f}"
                )
                return 1
        
        return 0

@register_strategy
class SentimentTrendStrategy(BaseStrategy):
    """
    情感趋势策略
    监控单只股票情感变化，捕捉拐点
    """
    
    name = "sentiment_trend"
    version = "1.0.0"
    
    def on_init(self):
        self.ctx.logger.info("初始化情感趋势策略")
        self.history: Dict[str, list] = {}  # symbol -> [sentiments]
    
    def on_bar(self, bar: Dict[str, Any]) -> Optional[int]:
        symbol = bar.get('symbol', '')
        
        # 1. 获取最新情感
        news_list = fusion_engine.get_news(symbol=symbol, limit=5)
        if not news_list:
            return 0
        
        current_sentiment = sum(n.sentiment for n in news_list) / len(news_list)
        
        # 2. 记录历史
        if symbol not in self.history:
            self.history[symbol] = []
        
        self.history[symbol].append(current_sentiment)
        if len(self.history[symbol]) > 10:
            self.history[symbol].pop(0)
        
        # 3. 判断趋势
        if len(self.history[symbol]) < 3:
            return 0
        
        # 最近一次情感上升
        if self.history[symbol][-1] > self.history[symbol][-2] and \
           self.history[symbol][-1] > 0.3:
            self.ctx.logger.info(f"【情感拐点】{symbol} 情感:{current_sentiment:.2f}")
            return 1
        
        return 0

@register_strategy
class HealthAwareStrategy(BaseStrategy):
    """
    健康感知策略
    根据数据源健康状态自动切换
    """
    
    name = "health_aware"
    version = "1.0.0"
    
    def on_init(self):
        self.ctx.logger.info("初始化健康感知策略")
        # 注册数据源
        health_checker.register('AkShare')
        health_checker.register('WenCai')
    
    def on_bar(self, bar: Dict[str, Any]) -> Optional[int]:
        # 获取最健康的数据源
        best_source = health_checker.get_best_source()
        
        if not best_source:
            self.ctx.logger.warning("所有数据源不健康，暂停交易")
            return 0
        
        self.ctx.logger.info(f"使用健康数据源：{best_source}")
        
        # 基于该源获取数据
        # ... (具体逻辑)
        
        return 0

__all__ = ['EventChainStrategy', 'SentimentTrendStrategy', 'HealthAwareStrategy']
