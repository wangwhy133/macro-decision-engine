# MDE v16.0 逃生与透明化版 - 发布说明

## 🎯 版本信息
- **版本**: v16.0.0
- **日期**: 2026-05-15
- **主题**: 极端逃生与完全透明化

## 🛑 解决的核心痛点

### 1. 极端行情无逃生 (No Escape)
- **问题**: 软约束在暴跌 20% 时反应太慢，导致穿仓。
- **v16 方案**: **硬止损机制**，一旦触发立即清仓并暂停所有策略。
- **效果**: 极端行情下保住本金，留得青山在。

### 2. 策略黑盒不透明 (Black Box)
- **问题**: 为什么买？为什么卖？逻辑不透明，不敢全仓信。
- **v16 方案**: **决策日志**，每一笔交易都记录详细理由、数据上下文、置信度。
- **效果**: 每一笔交易都可追溯，策略逻辑透明化。

### 3. 配置误操作无追溯 (No Audit)
- **问题**: 配置改错了不知道谁改的，无法回滚。
- **v16 方案**: **配置审计与回滚**，自动备份历史版本，支持一键回滚。
- **效果**: 误操作可恢复，责任可追溯。

## ✨ 核心特性

### 1. 硬止损引擎 (`hard_stop`)
```python
from mde_core import hard_stop_engine, HardStopConfig

# 配置硬止损
config = HardStopConfig(
    max_drawdown_total=0.20,   # 总资金回撤 20% 熔断
    max_drawdown_daily=0.05,   # 单日回撤 5% 熔断
    max_loss_per_trade=0.02,   # 单笔亏损 2% 熔断
    max_volatility_trigger=0.10 # 波动率 10% 熔断
)
hard_stop_engine.config = config

# 在策略中检查
if hard_stop_engine.check(current_price, entry_price, volatility):
    return 0  # 停止交易
```

### 2. 决策日志 (`decision_log`)
```python
from mde_core import decision_logger, DecisionLog

# 记录决策
log = DecisionLog(
    timestamp=datetime.now().isoformat(),
    strategy_name="my_strategy",
    symbol="000629.SZ",
    action="BUY",
    reason="情感分 0.8 > 阈值 0.5",
    data_context={"sentiment": 0.8, "news": "中标大单"},
    confidence=0.9,
    trace_id="abc123"
)
decision_logger.log(log)

# 查看今日决策
logs = decision_logger.get_today_logs()
print(decision_logger.visualize(logs))
```

### 3. 配置审计与回滚 (`config_audit`)
```python
from mde_core import config_auditor

# 保存快照
config_auditor.save_snapshot(operator="admin", comment="调整阈值前备份")

# 查看历史
history = config_auditor.list_history()

# 回滚到上一版本
config_auditor.rollback(version_index=-1)
```

## 📊 策略示例

### 硬止损策略
```python
@register_strategy
class HardStopStrategy(BaseStrategy):
    def on_bar(self, bar):
        if hard_stop_engine.check(bar['price'], self.entry_price, bar['volatility']):
            self.ctx.logger.error("硬止损触发，暂停交易")
            return 0
        return 1
```

### 透明化策略
```python
@register_strategy
class TransparentStrategy(BaseStrategy):
    def on_bar(self, bar):
        # 记录决策
        log = DecisionLog(...reason="情感分高于阈值"...)
        decision_logger.log(log)
        return 1
```

## 🧪 测试验证

```bash
# 运行 v16.0 测试
pytest tests/test_v16.py -v

# 测试覆盖
- [x] 硬止损触发逻辑
- [x] 决策日志记录与检索
- [x] 配置备份与回滚
```

## ⚠️ 注意事项

1. **硬止损重置**: 触发后需人工确认并调用 `reset()` 才能恢复
2. **日志存储**: 决策日志按天存储，注意定期清理旧日志
3. **配置备份**: 确保备份目录有足够空间

## 🔗 相关文件

- [硬止损](mde_core/hard_stop.py)
- [决策日志](mde_core/decision_log.py)
- [配置审计](mde_core/config_audit.py)
- [策略示例](strategies/v16_strategies.py)

---

**MDE v16.0 - 极端行情能逃生，策略逻辑全透明！**
