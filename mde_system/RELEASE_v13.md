# MDE v13.0 高可用版 - 发布说明

## 🎯 版本信息
- **版本**: v13.0.0
- **日期**: 2026-05-15
- **主题**: 工业级高可用与自适应优化

## 🛑 解决的问题

### 1. 回测幻觉 (Backtest Illusion)
- **问题**: 回测赚钱，实盘亏钱。
- **原因**: 回测未考虑滑点、冲击成本、成交延迟。
- **v13 方案**: **影子回测校验**，实时对比实盘与回测偏差，偏差过大自动熔断。

### 2. 策略过拟合 (Overfitting)
- **问题**: 参数静态，市场风格变化后策略失效。
- **v13 方案**: **滚动窗口参数优化**，定期自动重算最优参数。

### 3. 资源泄露 (Resource Leak)
- **问题**: 长期运行后内存溢出、文件句柄耗尽。
- **v13 方案**: **资源配额管理** + **看门狗**，自动监控并回收资源。

### 4. 单线程阻塞
- **问题**: 网络卡顿导致整个系统假死。
- **v13 方案**: **异步并发架构** (AsyncIO + 线程池)，IO 与计算分离。

## ✨ 核心特性

### 1. 异步并发支持 (`async_support`)
```python
from mde_core import async_wrap, io_executor

# 将同步函数包装为异步
async_get_news = async_wrap(fusion_engine.get_news)

# 异步执行，不阻塞主线程
news = await async_get_news(symbol='000629.SZ')
```

### 2. 资源看门狗 (`watchdog`)
```python
from mde_core import watchdog, default_quota

# 心跳检查
if not watchdog.heartbeat():
    print("资源紧张，暂停交易")

# 查看报告
report = watchdog.report()
print(f"内存使用：{report['memory']['used_mb']:.1f}MB")
```

### 3. 影子回测校验 (`validation`)
```python
from mde_core import shadow_checker, TradeRecord

# 记录实盘交易
shadow_checker.record_live_trade(trade)

# 记录回测交易
shadow_checker.record_backtest_trade(trade)

# 自动检测偏差，偏差过大自动报警
if shadow_checker.deviation_alert:
    print("⚠️ 实盘与回测偏差过大！")
```

### 4. 参数自优化 (`validation`)
```python
from mde_core import param_optimizer

# 检查是否需要重新优化
if param_optimizer.should_reoptimize(last_time):
    new_params = param_optimizer.optimize(strategy, data)
    strategy.update_params(new_params)
```

## 📊 策略示例

### 自适应参数策略
```python
@register_strategy
class AdaptiveParamStrategy(BaseStrategy):
    def on_bar(self, bar):
        # 定期重新优化参数
        if param_optimizer.should_reoptimize(self.last_optimize):
            self.params = param_optimizer.optimize(...)
        
        # 使用最新参数交易
        if sentiment > self.params['threshold']:
            return 1
```

### 影子校验策略
```python
@register_strategy
class ShadowValidateStrategy(BaseStrategy):
    def on_trade(self, trade_info):
        # 记录实盘
        shadow_checker.record_live_trade(trade)
        
        # 偏差过大自动熔断
        if shadow_checker.deviation_alert:
            kill_switch.activate("实盘回测偏差过大")
```

### 资源感知策略
```python
@register_strategy
class ResourceAwareStrategy(BaseStrategy):
    def on_bar(self, bar):
        # 资源紧张时暂停
        if not watchdog.heartbeat():
            return 0
        # 正常交易逻辑
        ...
```

## 🧪 测试验证

```bash
# 运行 v13.0 测试
pytest tests/test_v13.py -v

# 测试覆盖
- [x] 看门狗心跳检查
- [x] 影子回测偏差检测
- [x] 参数优化器
- [x] 资源配额管理
```

## 📦 依赖更新

无需额外依赖 (psutil 为可选，用于内存监控)

```bash
pip install psutil  # 可选，增强版资源监控
```

## ⚠️ 注意事项

1. **异步适配**: 原有同步策略无需修改，但建议使用 `@async_wrap` 包装耗时操作
2. **参数优化**: 需接入真实回测引擎才能发挥最大效用
3. **影子校验**: 首次运行时需积累一定实盘数据才能生效

## 🔗 相关文件

- [异步支持](mde_core/async_support.py)
- [看门狗](mde_core/watchdog.py)
- [影子校验](mde_core/validation.py)
- [策略示例](strategies/v13_strategies.py)

---

**MDE v13.0 - 迈向工业级高可用交易系统！**
