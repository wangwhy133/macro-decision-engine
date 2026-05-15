# MDE v12.0 数据融合层 - 完整发布说明

## 🎯 版本信息
- **版本**: v12.0.0 (完善版)
- **日期**: 2026-05-15
- **主题**: 多源数据融合 + 情感分析 + 事件链追踪

## ✨ 核心功能矩阵

| 模块 | 功能 | 状态 |
|------|------|------|
| **数据源** | AkShare (财联社/个股新闻) | ✅ |
| | Mootdx (腾讯/同花顺底层) | ✅ |
| | WenCai (同花顺热点) | ✅ |
| **情感分析** | 金融词典打分 | ✅ |
| | 情感趋势追踪 | ✅ |
| **健康监控** | 数据源健康检查 | ✅ |
| | 自动熔断切换 | ✅ |
| **事件聚合** | 新闻去重 | ✅ |
| | 事件链追踪 | ✅ |
| **策略集成** | 多源新闻策略 | ✅ |
| | 事件链策略 | ✅ |
| | 情感趋势策略 | ✅ |

## 🔧 新增组件详解

### 1. 情感分析增强 (`sentiment.py`)
```python
from mde_core.data import analyzer

# 分析新闻情感
score = analyzer.analyze("公司中标大单，业绩预增")
print(f"情感分：{score:.2f}")  # 输出：0.75

# 批量分析
scores = analyzer.analyze_batch(["利好", "利空", "中性"])
```

**特性**:
- 内置金融情感词典 (涨停/跌停/中标/诉讼等)
- 自动归一化到 [-1.0, 1.0]
- 可扩展至专业 NLP 模型

### 2. 健康检查 (`health.py`)
```python
from mde_core.data import health_checker

# 注册数据源
health_checker.register('AkShare')
health_checker.register('WenCai')

# 记录请求结果
health_checker.record('AkShare', success=True, latency_ms=120)

# 获取最健康源
best = health_checker.get_best_source()
print(f"最佳数据源：{best}")
```

**特性**:
- 实时监控成功率/延迟
- 自动熔断不健康源
- 智能切换备用源

### 3. 事件链聚合 (`events.py`)
```python
from mde_core.data import aggregator, NewsItem

# 处理新闻流
news_list = [...]  # 一批新闻
chains = aggregator.process_news(news_list)

# 查看事件链
for chain in chains:
    summary = chain.get_summary()
    print(f"事件：{summary['seed_title']}")
    print(f"新闻数：{summary['news_count']}")
    print(f"情感趋势：{summary['sentiment_trend']:.2f}")
```

**特性**:
- 自动聚合同一事件相关新闻
- 追踪情感演化趋势
- TTL 自动清理过期事件

## 📊 策略示例

### 事件链追踪策略
```python
from mde_core import register_strategy
from mde_core.data import aggregator, fusion_engine

@register_strategy
class EventChainStrategy(BaseStrategy):
    def on_bar(self, bar):
        # 获取新闻
        news = fusion_engine.get_news(symbol='000629.SZ')
        
        # 聚合事件
        chains = aggregator.process_news(news)
        
        # 寻找机会：新闻数>=3 且情感趋势向上
        for chain in chains:
            if chain.get_summary()['news_count'] >= 3:
                if chain.get_sentiment_trend() > 0.2:
                    return 1  # 买入
        return 0
```

### 情感趋势策略
```python
# 监控单只股票情感变化
history = []
current = sum(n.sentiment for n in news) / len(news)
history.append(current)

# 情感拐点：连续上升且突破阈值
if len(history) >= 3 and history[-1] > history[-2] and history[-1] > 0.3:
    return 1  # 买入
```

### 健康感知策略
```python
from mde_core.data import health_checker

# 自动选择最健康数据源
best = health_checker.get_best_source()
if not best:
    return 0  # 所有源不可用，暂停交易

# 基于最佳源获取数据
```

## 🧪 测试验证

```bash
# 运行 v12.0 测试
pytest tests/test_v12.py -v

# 测试覆盖
- [x] 情感分析准确性
- [x] 健康检查逻辑
- [x] 事件链聚合
- [x] 策略集成
```

## 📦 依赖更新

```txt
# requirements.txt
akshare>=1.10.0      # 核心数据源
mootdx>=0.10.0       # 可选，腾讯源
```

## ⚠️ 注意事项

1. **情感准确性**: 内置词典适用于一般场景，专业交易建议接入金融 NLP 模型
2. **网络依赖**: 数据获取需联网，建议配置重试和熔断
3. **缓存策略**: 默认 60 秒缓存，高频交易需调整
4. **合规使用**: 遵守各数据源 API 条款

## 🔗 相关文件

- [数据源接口](mde_core/data/sources.py)
- [融合引擎](mde_core/data/fusion.py)
- [情感分析](mde_core/data/sentiment.py)
- [健康检查](mde_core/data/health.py)
- [事件链](mde_core/data/events.py)
- [策略示例](strategies/advanced_news.py)

---

**MDE v12.0 - 让数据驱动交易，让决策更智能！**
