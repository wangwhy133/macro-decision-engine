"""
MDE v12.0 数据层测试
"""

import pytest
from mde_core.data import (
    SentimentAnalyzer, analyzer,
    SourceHealth, HealthChecker,
    EventChain, EventAggregator,
    NewsItem
)
from datetime import datetime

class TestSentimentAnalyzer:
    def test_positive(self):
        score = analyzer.analyze("公司中标大单，业绩增长")
        assert score > 0
    
    def test_negative(self):
        score = analyzer.analyze("公司亏损，面临诉讼")
        assert score < 0
    
    def test_neutral(self):
        score = analyzer.analyze("公司发布公告")
        assert score == 0.0

class TestHealthChecker:
    def test_record(self):
        hc = HealthChecker()
        hc.register('TestSource')
        hc.record('TestSource', True, 100)
        assert hc.sources['TestSource'].is_healthy
    
    def test_best_source(self):
        hc = HealthChecker()
        hc.register('A')
        hc.register('B')
        hc.record('A', False)
        hc.record('B', True, 50)
        assert hc.get_best_source() == 'B'

class TestEventChain:
    def test_create_chain(self):
        news = NewsItem(
            title="测试新闻",
            content="内容",
            source="Test",
            publish_time=datetime.now()
        )
        chain = EventChain("e1", news)
        assert chain.event_id == "e1"
    
    def test_add_related(self):
        seed = NewsItem(title="公司 A 中标", content="", source="T", publish_time=datetime.now())
        chain = EventChain("e1", seed)
        
        related = NewsItem(title="公司 A 中标金额增长", content="", source="T", publish_time=datetime.now())
        assert chain.add_news(related) is True

class TestAggregator:
    def test_process(self):
        agg = EventAggregator()
        news = [
            NewsItem(title="事件 A 发生", content="", source="T", publish_time=datetime.now()),
            NewsItem(title="事件 A 进展", content="", source="T", publish_time=datetime.now())
        ]
        chains = agg.process_news(news)
        # 应该聚合
        assert len(chains) >= 1

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
