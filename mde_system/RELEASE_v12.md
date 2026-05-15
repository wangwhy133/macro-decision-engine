# MDE v12.0 数据融合层发布说明

## 🎯 版本信息
- **版本**: v12.0.0
- **日期**: 2026-05-15
- **主题**: 多源数据融合 (财联社/个股新闻/同花顺热点)

## ✨ 新增数据源

### 1. AkShare 数据源
- **财联社 7x24 快讯**: 实时财经新闻
- **个股新闻**: 东方财富/同花顺个股公告与新闻
- **板块热点**: 同花顺/东方财富行业板块

### 2. Mootdx 数据源
- **腾讯/同花顺底层协议**: 高速行情数据
- **支持**: 沪深股票、基金、期货

### 3. iWenCai (问财) 数据源
- **同花顺热点主题**: 概念板块、热点排行
- **智能选股**: 自然语言选股结果

## 🔧 核心功能

### 1. 统一数据模型
```python
from mde_core.data import NewsItem, HotTopic

# 新闻
news = NewsItem(
    title="某公司中标大单",
    content="详细内容...",
    source="财联社",
    publish_time=datetime.now(),
    sentiment=0.8  # 利好
)

# 热点
topic = HotTopic(
    name="人工智能",
    rank=1,
    change_rate=3.5,
    related_stocks=['000xxx', '600xxx']
)
```

### 2. 智能融合引擎
```python
from mde_core.data import fusion_engine

# 获取融合新闻 (自动去重+情感分析)
news_list = fusion_engine.get_news(symbol='000629.SZ', limit=10)

# 获取热点排行
topics = fusion_engine.get_hot_topics()

# 获取行情 (带缓存)
quote = fusion_engine.get_quote('000629.SZ')
```

### 3. 情感分析
- **内置词典**: 利好/利空关键词匹配
- **自动打分**: -1.0 (大利空) ~ 1.0 (大利好)
- **可扩展**: 支持集成 NLP 模型

## 📊 策略示例

### 多源新闻策略
```python
from mde_core import BaseStrategy, register_strategy
from mde_core.data import fusion_engine

@register_strategy
class MultiSourceNewsStrategy(BaseStrategy):
    def on_bar(self, bar):
        # 获取新闻 + 情感分析
        news_list = fusion_engine.get_news(symbol='000629.SZ')
        avg_sentiment = sum(n.sentiment for n in news_list) / len(news_list)
        
        if avg_sentiment > 0.3:
            return 1  # 买入
        elif avg_sentiment < -0.3:
            return -1  # 卖出
        return 0
```

### 财联社快讯策略
```python
# 仅监控财联社 7x24 快讯
news = fusion_engine.get_news(symbol=None, limit=1)
if news and news[0].sentiment > 0.2:
    # 快速反应
    pass
```

## 📦 依赖安装

```bash
# 核心依赖
pip install akshare>=1.10.0

# 可选 (腾讯源)
pip install mootdx>=0.10.0
```

## ⚠️ 注意事项

1. **网络依赖**: 数据获取需联网，建议增加重试机制
2. **缓存策略**: 默认 60 秒缓存，避免频繁请求
3. **情感准确性**: 内置简单词典，实盘建议接入专业 NLP
4. **合规使用**: 遵守各数据源 API 使用条款

## 🔗 相关文档

- [数据源接口定义](mde_core/data/sources.py)
- [融合引擎实现](mde_core/data/fusion.py)
- [策略示例](strategies/news_strategy.py)

---

**MDE v12.0 - 数据驱动决策！**
