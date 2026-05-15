"""
MDE 情感分析增强模块
- 中文金融情感词典
- 简单 NLP 打分
- 可扩展至专业模型
"""

from typing import List, Dict
from collections import defaultdict

# 简易金融情感词典 (可扩展)
FINANCE_POSITIVE = {
    '涨停': 0.9, '利好': 0.8, '增长': 0.6, '盈利': 0.7, '重组': 0.8,
    '中标': 0.7, '突破': 0.6, '上涨': 0.5, '净利': 0.6, '预增': 0.7,
    '回购': 0.5, '增持': 0.6, '创新高': 0.8, '放量': 0.4
}

FINANCE_NEGATIVE = {
    '跌停': -0.9, '利空': -0.8, '下滑': -0.6, '亏损': -0.8, '处罚': -0.7,
    '诉讼': -0.6, '下跌': -0.5, '减持': -0.6, '暴跌': -0.8, '违约': -0.9,
    '立案': -0.7, '退市': -0.9, '造假': -0.9, '减持': -0.6
}

class SentimentAnalyzer:
    """情感分析器"""
    
    def __init__(self):
        self.positive = FINANCE_POSITIVE
        self.negative = FINANCE_NEGATIVE
    
    def analyze(self, text: str) -> float:
        """
        分析文本情感
        :return: -1.0 (极利空) ~ 1.0 (极利好)
        """
        score = 0.0
        count = 0
        
        # 匹配正向词
        for word, val in self.positive.items():
            if word in text:
                score += val
                count += 1
        
        # 匹配负向词
        for word, val in self.negative.items():
            if word in text:
                score += val
                count += 1
        
        if count == 0:
            return 0.0
        
        # 归一化到 [-1, 1]
        normalized = score / max(count, 1)
        return max(-1.0, min(1.0, normalized))
    
    def analyze_batch(self, texts: List[str]) -> List[float]:
        return [self.analyze(t) for t in texts]

# 全局实例
analyzer = SentimentAnalyzer()

__all__ = ['SentimentAnalyzer', 'analyzer']
