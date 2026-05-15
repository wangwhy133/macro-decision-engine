# MDE v11.0 实盘加固版 - 发布说明

## 🎯 版本信息
- **版本**: v11.0.0
- **日期**: 2026-05-15
- **主题**: 实盘深水区加固

## ✨ 新增特性

### 1. 状态持久化 (StateManager)
- **问题**: 进程重启后内存数据丢失，导致"账实不符"
- **方案**: 原子写入磁盘，启动时自动恢复
- **使用**:
```python
from mde_core import StateManager
state = StateManager('state.json')
state.save({'balance': 100000, 'position': 1000})
# 重启后
data = state.load()
```

### 2. 熔断器 (CircuitBreaker)
- **问题**: 网络抖动导致连续失败，系统雪崩
- **方案**: 失败次数超限后自动熔断，进入恢复期
- **使用**:
```python
from mde_core import CircuitBreaker
cb = CircuitBreaker(failure_threshold=5, recovery_time=60)
if cb.can_execute():
    # 执行操作
```

### 3. 重试机制 (RetryConfig)
- **问题**: 临时网络错误导致交易失败
- **方案**: 指数退避重试，自动恢复
- **使用**:
```python
from mde_core import retry_with_config, RetryConfig

@retry_with_config(RetryConfig(max_retries=3, base_delay=1.0))
def submit_order(...):
    # 可能失败的操作
```

### 4. 执行器增强
- **完善撤单**: `cancel_order()` 真正模拟撤单逻辑
- **新增改单**: `modify_order()` 支持改价改量
- **熔断集成**: 执行器内置熔断保护

## 📊 核心改进对比

| 维度 | v10.0 | v11.0 | 改进 |
|------|-------|-------|------|
| 状态恢复 | ❌ | ✅ 自动恢复 | 防止数据丢失 |
| 网络容错 | ❌ | ✅ 重试+熔断 | 提升稳定性 |
| 撤单功能 | 基础 | ✅ 完整实现 | 实盘必备 |
| 改单功能 | ❌ | ✅ 支持 | 灵活调整 |

## 🚀 升级建议

### 必改项
1. **状态持久化**: 实盘必须开启，防止重启丢数据
2. **熔断配置**: 根据网络环境调整阈值

### 选改项
1. **重试策略**: 高频交易需调小延迟
2. **日志增强**: 建议配合上下文日志

## 📝 使用示例

### 完整交易流程 (含重试+持久化)
```python
from mde_core import (
    PaperExecutor, StateManager, 
    retry_with_config, RetryConfig
)

# 初始化
state = StateManager('trade_state.json')
executor = PaperExecutor({'initial_cash': 100000})

# 带重试的下单
@retry_with_config(RetryConfig(max_retries=3))
def safe_submit(symbol, side, qty, price):
    return executor.submit_order(symbol, side, qty, price)

# 下单
result = safe_submit('000629.SZ', 'buy', 1000, 10.5)

# 保存状态
state.save({
    'balance': executor.get_balance(),
    'position': executor.get_position('000629.SZ'),
    'last_order': result
})
```

## 🔧 配置示例

```json
{
  "retry": {
    "max_retries": 3,
    "base_delay": 1.0,
    "max_delay": 60.0
  },
  "circuit_breaker": {
    "failure_threshold": 5,
    "recovery_time": 60
  },
  "state": {
    "file": "state.json",
    "auto_save_interval": 60
  }
}
```

## ⚠️ 注意事项

1. **原子写入**: 状态文件采用临时文件+重命名，确保写入原子性
2. **熔断恢复**: 熔断后需等待恢复期，不可强行操作
3. **重试延迟**: 实盘环境建议设置合理延迟，避免雪崩

---

**MDE v11.0 - 让实盘更稳健！**
