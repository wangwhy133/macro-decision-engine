"""
MDE 数据融合引擎
- 智能路由
- 数据去重
- 情感分析
- 缓存管理
"""

import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from .sources import DataSource, NewsItem, HotTopic
from .providers import AkShareSource, MootdxSource, WenCaiSource

class DataFusionEngine:
    """数据融合引擎"""
    
    def __init__(self, sources: List[DataSource] = None):
        self.sources = sources or [AkShareSource(), MootdxSource(), WenCaiSource()]
        self._cache: Dict[str, tuple] = {}  # key: (data, timestamp)
        self._cache_ttl = 60  # 缓存 60 秒
    
    def get_news(self, symbol: Optional[str] = None, limit: int = 20) -> List[NewsItem]:
        """
        获取融合后的新闻
        策略：优先财联社 (快讯) + 个股新闻
        """
        all_news: List[NewsItem] = []
        
        # 1. 优先获取财联社/快讯
        for source in self.sources:
            if source.name == 'AkShare':
                all_news.extend(source.get_news(symbol=symbol, limit=limit))
        
        # 2. 去重 (基于 title + time)
        seen = set()
        unique_news = []
        for news in all_news:
            key = f"{news.title}_{news.publish_time.strftime('%Y%m%d%H')}"
            if key not in seen:
                seen.add(key)
                unique_news.append(news)
        
        # 3. 简单情感分析 (基于关键词)
        for news in unique_news:
            score = self._simple_sentiment(news.title + news.content)
            news.sentiment = score
        
        return unique_news[:limit]
    
    def get_hot_topics(self) -> List[HotTopic]:
        """获取融合后的热点"""
        all_topics: List[HotTopic] = []
        
        for source in self.sources:
            all_topics.extend(source.get_hot_topics())
        
        # 按热度排序
        all_topics.sort(key=lambda x: x.rank)
        return all_topics[:20]
    
    def get_quote(self, symbol: str) -> Dict[str, Any]:
        """获取行情 (带缓存)"""
        cache_key = f"quote_{symbol}"
        now = time.time()
        
        if cache_key in self._cache:
            data, ts = self._cache[cache_key]
            if now - ts < self._cache_ttl:
                return data
        
        # 多源获取
        for source in self.sources:
            data = source.get_quote(symbol)
            if data and data.get('price', 0) > 0:
                self._cache[cache_key] = (data, now)
                return data
        
        return {}
    
    def _simple_sentiment(self, text: str) -> float:
        """简单情感打分"""
        positive_words = ['利好', '上涨', '突破', '增长', '盈利', '重组', '中标']
        negative_words = ['利空', '下跌', '暴跌', '亏损', '处罚', '诉讼', '减持']
        
        score = 0.0
        for word in positive_words:
            if word in text:
                score += 0.2
        for word in negative_words:
            if word in text:
                score -= 0.2
        
        return max(-1.0, min(1.0, score))

# 全局实例
fusion_engine = DataFusionEngine()

__all__ = ['DataFusionEngine', 'fusion_engine']
