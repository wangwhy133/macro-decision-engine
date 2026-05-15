# MDE v14.0 金融级风控版 - 发布说明

## 🎯 版本信息
- **版本**: v14.0.0
- **日期**: 2026-05-15
- **主题**: 金融级动态风控与灰度发布

## 🛑 解决的核心痛点

### 1. 静态风控滞后 (Static Risk Lag)
- **问题**: 市场已暴跌，风控阈值还是 5%，反应太慢。
- **v14 方案**: **动态风控引擎**，基于实时波动率自动调整仓位和止损。
- **效果**: 波动率飙升时自动降仓，黑天鹅事件中保住本金。

### 2. 策略上线即全仓 (All-in Risk)
- **问题**: 新策略直接全量上线，有 Bug 则全盘皆输。
- **v14 方案**: **灰度发布机制** (Canary Release)，1% -> 10% -> 100% 逐步放量。
- **效果**: 即使有 Bug，损失控制在 1% 以内。

### 3. 故障排查无头绪 (No Traceability)
- **问题**: 日志分散，无法串联一次交易的全链路。
- **v14 方案**: **TraceID 链路追踪**，贯穿数据->策略->下单->成交。
- **效果**: 一次请求，一个 ID，全程可追溯。

## ✨ 核心特性

### 1. 动态风控引擎 (`dynamic_risk`)
```python
from mde_core import risk_engine

# 更新风险指标 (收益率序列 + 流动性评分)
returns = [0.01, -0.02, 0.05, ...]
risk_engine.update_metrics(returns, liquidity_score=0.8)

# 获取动态仓位上限
limit = risk_engine.get_position_limit()
if risk_engine.should_halt():
    print("波动率过高，停止交易")
```

**特性**:
- 基于波动率动态调整仓位
- 流动性枯竭时强制降仓
- 极端行情自动熔断

### 2. 灰度发布管理 (`release`)
```python
from mde_core import release_manager

# 部署新版本
release = release_manager.deploy("my_strategy", "1.0.0")

# 在策略中
def on_bar(self, bar):
    # 自动判断当前阶段
    scale = release.get_position_scale()  # 0.01 / 0.10 / 1.0
    
    # 记录交易结果
    release.record_trade(success=True)
    
    # 自动晋升阶段
    release.promote()
    
    # 异常自动回滚
    if release.should_rollback():
        release.rollback()
```

**发布阶段**:
1. **Canary (灰度)**: 1% 资金，跑 10 次无错 -> 晋升
2. **Partial (部分)**: 10% 资金，跑 50 次无错 -> 晋升
3. **Full (全量)**: 100% 资金

### 3. 链路追踪 (`trace`)
```python
from mde_core import TraceContext, get_trace_id

with TraceContext() as ctx:
    ctx.set('strategy', 'pig_cycle')
    logger.info(f"[{get_trace_id()}] 开始执行")
    # 输出：[a1b2c3d4] 开始执行 (strategy=pig_cycle)
```

## 📊 策略示例

### 动态风控策略
```python
@register_strategy
class DynamicRiskStrategy(BaseStrategy):
    def on_bar(self, bar):
        # 获取动态仓位
        limit = risk_engine.get_position_limit()
        
        # 检查熔断
        if risk_engine.should_halt():
            return 0
        
        # 按动态仓位下单
        quantity = int(limit * total_capital)
        return 1 if signal else 0
```

### 灰度发布策略
```python
@register_strategy
class CanaryStrategy(BaseStrategy):
    def on_init(self):
        self.release = release_manager.deploy(self.name, "1.0")
    
    def on_bar(self, bar):
        # 自动管理阶段
        if self.release.should_rollback():
            self.release.rollback()
            return 0
        
        self.release.promote()
        # 使用对应比例资金
        scale = self.release.get_position_scale()
```

## 🧪 测试验证

```bash
# 运行 v14.0 测试
pytest tests/test_v14.py -v

# 测试覆盖
- [x] 动态风控仓位调整
- [x] 灰度发布阶段晋升
- [x] 异常自动回滚
- [x] TraceID 生成与上下文
```

## ⚠️ 注意事项

1. **波动率计算**: 需至少 2 个收益率数据点才能计算
2. **灰度策略**: 需配合真实交易记录才能正确晋升
3. **TraceID**: 异步环境下需手动传递上下文

## 🔗 相关文件

- [动态风控](mde_core/dynamic_risk.py)
- [灰度发布](mde_core/release.py)
- [链路追踪](mde_core/trace.py)
- [策略示例](strategies/v14_strategies.py)

---

**MDE v14.0 - 金融级风控，为资金安全保驾护航！**
