"""
MDE 多源数据策略示例
演示如何融合使用财联社新闻、个股新闻、同花顺热点数据
"""

from mde_core import BaseStrategy, StrategyContext, register_strategy
from mde_core.data import fusion_engine, NewsItem
from typing import Dict, Any, Optional

@register_strategy
class MultiSourceNewsStrategy(BaseStrategy):
    """
    多源新闻融合策略
    - 监控财联社快讯
    - 监控个股新闻
    - 结合同花顺热点
    - 情感分析打分
    """
    
    name = "multi_source_news"
    version = "1.0.0"
    author = "MDE Team"
    
    def on_init(self):
        self.ctx.logger.info("初始化多源数据策略")
        self.news_threshold = self.ctx.config.get('news_threshold', 0.3)
        self.last_news_time = None
    
    def on_bar(self, bar: Dict[str, Any]) -> Optional[int]:
        """
        K 线回调
        逻辑:
        1. 获取最新新闻 (自动融合多源)
        2. 计算情感分数
        3. 结合热点板块判断
        4. 生成交易信号
        """
        symbol = bar.get('symbol', '000629.SZ')
        
        # 1. 获取融合新闻
        news_list = fusion_engine.get_news(symbol=symbol, limit=5)
        
        # 2. 计算综合情感分
        if news_list:
            avg_sentiment = sum(n.sentiment for n in news_list) / len(news_list)
        else:
            avg_sentiment = 0.0
        
        # 3. 获取热点
        hot_topics = fusion_engine.get_hot_topics()
        is_hot = any(symbol in (t.related_stocks or []) for t in hot_topics[:5])
        
        # 4. 生成信号
        if avg_sentiment > self.news_threshold:
            # 利好 + 热点 = 强力买入
            if is_hot:
                self.ctx.logger.info(f"【强力买入】{symbol} 情感:{avg_sentiment:.2f} 热点:是")
                return 1
            else:
                self.ctx.logger.info(f"【买入】{symbol} 情感:{avg_sentiment:.2f}")
                return 1
        elif avg_sentiment < -self.news_threshold:
            # 利空卖出
            self.ctx.logger.info(f"【卖出】{symbol} 情感:{avg_sentiment:.2f}")
            return -1
        
        return 0
    
    def on_trade(self, trade_info: Dict[str, Any]):
        self.ctx.logger.info(f"交易完成：{trade_info}")

# 简化版：仅监控财联社快讯
@register_strategy
class ClsFastNewsStrategy(BaseStrategy):
    """
    财联社快讯策略
    只监控财联社 7x24 快讯，适合超短线
    """
    
    name = "cls_fast_news"
    version = "1.0.0"
    
    def on_init(self):
        self.ctx.logger.info("初始化财联社快讯策略")
    
    def on_bar(self, bar: Dict[str, Any]) -> Optional[int]:
        # 获取快讯
        news_list = fusion_engine.get_news(symbol=None, limit=3)
        
        # 简单逻辑：最新一条快讯情感
        if news_list:
            latest = news_list[0]
            if latest.sentiment > 0.2:
                return 1
            elif latest.sentiment < -0.2:
                return -1
        return 0

__all__ = ['MultiSourceNewsStrategy', 'ClsFastNewsStrategy']
