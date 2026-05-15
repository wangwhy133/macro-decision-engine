"""
MDE 事件链聚合
将相关新闻聚合成事件链，追踪事件演化
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta
from .sources import NewsItem
import hashlib

class EventChain:
    """事件链"""
    
    def __init__(self, event_id: str, seed_news: NewsItem):
        self.event_id = event_id
        self.seed_news = seed_news
        self.news_list: List[NewsItem] = [seed_news]
        self.last_update = seed_news.publish_time
        self.related_stocks: set = set()
        self.sentiment_trend: List[float] = [seed_news.sentiment]
    
    def add_news(self, news: NewsItem) -> bool:
        """添加相关新闻"""
        # 简单相似度检查 (标题包含关键词)
        if self._is_related(news):
            self.news_list.append(news)
            self.last_update = news.publish_time
            self.sentiment_trend.append(news.sentiment)
            return True
        return False
    
    def _is_related(self, news: NewsItem) -> bool:
        """判断是否相关"""
        # 1. 标题包含种子新闻关键词
        seed_words = set(self.seed_news.title[:10])  # 前 10 字
        news_words = set(news.title[:10])
        if len(seed_words & news_words) >= 2:
            return True
        
        # 2. 标签重合
        if set(self.seed_news.tags) & set(news.tags):
            return True
        
        return False
    
    def get_sentiment_trend(self) -> float:
        """获取情感趋势 (最新 - 最早)"""
        if len(self.sentiment_trend) < 2:
            return self.sentiment_trend[0] if self.sentiment_trend else 0.0
        return self.sentiment_trend[-1] - self.sentiment_trend[0]
    
    def get_summary(self) -> Dict:
        return {
            'event_id': self.event_id,
            'seed_title': self.seed_news.title,
            'news_count': len(self.news_list),
            'sentiment_trend': self.get_sentiment_trend(),
            'last_update': self.last_update.isoformat(),
            'related_stocks': list(self.related_stocks)
        }

class EventAggregator:
    """事件聚合器"""
    
    def __init__(self, max_chains: int = 50, ttl_hours: int = 24):
        self.max_chains = max_chains
        self.ttl_hours = ttl_hours
        self.chains: Dict[str, EventChain] = {}
    
    def process_news(self, news_list: List[NewsItem]) -> List[EventChain]:
        """处理一批新闻，返回更新的事件链"""
        updated_chains = []
        
        for news in news_list:
            matched = False
            
            # 尝试匹配现有事件链
            for chain in list(self.chains.values()):
                if chain.add_news(news):
                    chain.related_stocks.update(news.tags)
                    matched = True
                    updated_chains.append(chain)
                    break
            
            # 创建新事件链
            if not matched:
                event_id = hashlib.md5(news.title.encode()).hexdigest()[:8]
                if len(self.chains) < self.max_chains:
                    chain = EventChain(event_id, news)
                    self.chains[event_id] = chain
                    updated_chains.append(chain)
        
        # 清理过期事件
        self._cleanup()
        
        return updated_chains
    
    def _cleanup(self):
        """清理过期事件"""
        now = datetime.now()
        expired = []
        for event_id, chain in self.chains.items():
            if now - chain.last_update > timedelta(hours=self.ttl_hours):
                expired.append(event_id)
        
        for event_id in expired:
            del self.chains[event_id]

# 全局实例
aggregator = EventAggregator()

__all__ = ['EventChain', 'EventAggregator', 'aggregator']
