# MDE v15.0 长期主义版 - 发布说明

## 🎯 版本信息
- **版本**: v15.0.0
- **日期**: 2026-05-15
- **主题**: 架构熵减与长期主义

## 🛑 解决的深层问题

### 1. 策略黑盒 (Black Box)
- **问题**: 亏损了不知道是市场原因还是策略失效。
- **v15 方案**: **策略归因引擎**，自动拆解盈亏来源 (Alpha/Beta/成本)。
- **效果**: 拒绝盲目调参，科学归因。

### 2. 伪分散 (Fake Diversification)
- **问题**: 10 个策略都在做多同一板块，风险未分散。
- **v15 方案**: **组合级风控**，监控整体敞口、行业集中度、相关性。
- **效果**: 真分散，抗风险。

### 3. 配置僵化 (Rigid Config)
- **问题**: 修改参数需改代码重启。
- **v15 方案**: **配置热加载 2.0**，动态注入参数，秒级生效。
- **效果**: 快速响应市场变化。

### 4. 架构熵增 (Entropy)
- **问题**: 核心逻辑与第三方库耦合，升级困难。
- **v15 方案**: **强化防腐层**，核心只依赖抽象接口。
- **效果**: 易于维护，升级无忧。

## ✨ 核心特性

### 1. 策略归因引擎 (`attribution`)
```python
from mde_core import attribution_engine

# 分析盈亏来源
result = attribution_engine.analyze(
    strategy_returns=[0.01, -0.02, ...],
    benchmark_returns=[0.01, 0.01, ...],
    costs=[0.001, ...]
)

print(result.conclusion) 
# 输出："策略失效，建议检查参数" 或 "成本过高，建议优化"
```

### 2. 组合风控 (`portfolio_risk`)
```python
from mde_core import portfolio_risk_manager

# 更新持仓
portfolio_risk_manager.update_position(
    "strategy_1", "000629.SZ", 
    quantity=1000, price=10.5, sector="Steel"
)

# 检查风险
metrics = portfolio_risk_manager.get_metrics()
if not metrics.is_diversified:
    print("警告：组合未分散！")
if portfolio_risk_manager.should_reduce_position():
    print("警告：总敞口过高，建议减仓！")
```

### 3. 配置热加载 2.0 (`hot_config`)
```python
from mde_core import init_hot_config

# 初始化
hot_config = init_hot_config("config.json")

# 策略中动态读取
threshold = hot_config.get('strategies.my_strategy.threshold', 0.3)

# 修改 config.json 后，自动生效，无需重启
```

## 📊 策略示例

### 归因感知策略
```python
@register_strategy
class AttributionAwareStrategy(BaseStrategy):
    def on_bar(self, bar):
        # 定期归因
        if len(self.returns) % 10 == 0:
            result = attribution_engine.analyze(...)
            if "失效" in result.conclusion:
                return 0  # 暂停
```

### 组合安全策略
```python
@register_strategy
class PortfolioSafeStrategy(BaseStrategy):
    def on_bar(self, bar):
        # 更新持仓
        portfolio_risk_manager.update_position(...)
        
        # 受组合约束
        if portfolio_risk_manager.should_reduce_position():
            return 0  # 停止开仓
```

## 🧪 测试验证

```bash
# 运行 v15.0 测试
pytest tests/test_v15.py -v

# 测试覆盖
- [x] 归因分析准确性
- [x] 组合风险指标计算
- [x] 配置热加载
```

## ⚠️ 注意事项

1. **归因数据**: 需至少 10 个周期数据才能进行有效归因
2. **组合更新**: 需在每次交易后更新持仓，否则指标不准
3. **配置文件**: 确保 JSON 格式正确，否则热加载失败

## 🔗 相关文件

- [归因引擎](mde_core/attribution.py)
- [组合风控](mde_core/portfolio_risk.py)
- [热配置](mde_core/hot_config.py)
- [策略示例](strategies/v15_strategies.py)

---

**MDE v15.0 - 做时间的朋友，构建长期主义架构！**
