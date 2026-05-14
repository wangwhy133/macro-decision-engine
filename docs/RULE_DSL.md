# 规则 DSL 设计文档

## 目标

设计一套简洁、可读、可扩展的规则描述语言，用于宏观决策领域的规则表达。

## 设计原则

1. **人类可读**: 规则应该像自然语言一样易于理解
2. **领域特定**: 针对宏观经济、投资领域优化
3. **类型安全**: 编译时/运行时类型检查
4. **可组合**: 支持规则组合和复用
5. **可解释**: 规则执行过程可追溯

## 语法规则

### 基本结构

```
RULE rule_id: "规则名称"
DESCRIPTION "规则描述"
TYPE threshold | trend | correlation | pattern | composite
CATEGORY pig_cycle | inflation | policy | ...
PRIORITY 1-10

CONDITION
  <条件表达式>

THEN
  CONCLUSION "结论描述"
  CONFIDENCE 0.0-1.0
  IMPACT positive | negative | neutral
  HORIZON short | medium | long

METADATA
  SOURCE expert | mined | learned
  CREATED_AT timestamp
  VALIDATED true | false
END
```

### 条件表达式

#### 1. 阈值比较

```
# 简单阈值
pig_inventory.change < -0.10

# 区间判断
cpi.value BETWEEN 0.02 AND 0.05

# 多条件组合
pig_inventory.change < -0.10 AND feed_cost.change > 0.05
```

#### 2. 趋势判断

```
# 连续下降
TREND_DOWN(pig_inventory.value, 3)  # 连续 3 期下降

# 加速上涨
ACCELERATING_UP(producer_price.index, 2)

# 突破均线
BREAKS_ABOVE(price.value, MA(price.value, 20))
```

#### 3. 相关性

```
# 负相关
CORRELATION(pig_inventory.value, pork_price.value, -0.7)

# 领先滞后关系
LEADS(pig_inventory.change, pork_price.change, 6)  # 领先 6 期
```

#### 4. 模式匹配

```
# 历史模式匹配
MATCHES_PATTERN(price.series, "head_and_shoulders")

# 异常模式
IS_ANOMALY(value, method="zscore", threshold=3.0)
```

#### 5. 时间相关

```
# 季节性
IS_SEASONAL_PERIOD(month(), "Q1")

# 周期位置
CYCLE_POSITION(pig_cycle, "trough")
```

### 变量引用

```
# 直接引用数据点
pig_inventory.value          # 能繁母猪存栏量
pig_inventory.change         # 变化量
pig_inventory.change.pct     # 变化百分比

# 时间修饰
pig_inventory.value[T-1]     # 上期值
pig_inventory.value[T-12]    # 去年同期值
pig_inventory.value[2024-01] # 指定时间

# 聚合函数
AVG(pig_inventory.value, 3)  # 近 3 期平均
MAX(pig_inventory.value, 12) # 近 12 期最大值
MIN(pig_inventory.value, 12) # 近 12 期最小值
```

### 函数库

#### 数学函数

```
ABS(x)           # 绝对值
SIGN(x)          # 符号函数
ROUND(x, n)      # 四舍五入
LOG(x)           # 对数
EXP(x)           # 指数
```

#### 统计函数

```
AVG(series, n)   # n 期平均
STD(series, n)   # n 期标准差
MIN(series, n)   # n 期最小值
MAX(series, n)   # n 期最大值
PERCENTILE(series, p)  # 分位数
```

#### 时间函数

```
NOW()            # 当前时间
YEAR()           # 年份
MONTH()          # 月份
QUARTER()        # 季度
DAY_OF_WEEK()    # 星期几
```

#### 逻辑函数

```
AND(a, b, ...)   # 与
OR(a, b, ...)    # 或
NOT(a)           # 非
IF(cond, a, b)   # 条件
```

## 示例规则

### 示例 1: 猪周期 - 供给收缩

```
RULE pig_supply_shortage: "能繁母猪存栏大幅下降"
DESCRIPTION "当能繁母猪存栏量连续 3 个月下降且累计降幅超过 10%，预示未来 6-12 个月生猪供给收缩"
TYPE trend
CATEGORY pig_cycle
PRIORITY 8

CONDITION
  pig_inventory.change[T] < 0 AND
  pig_inventory.change[T-1] < 0 AND
  pig_inventory.change[T-2] < 0 AND
  SUM(pig_inventory.change, 3) < -0.10

THEN
  CONCLUSION "生猪供给将在未来 6-12 个月收缩，猪价上涨概率>70%"
  CONFIDENCE 0.75
  IMPACT positive
  HORIZON medium

METADATA
  SOURCE expert
  VALIDATED true
  SUCCESS_RATE 0.72
  VALIDATION_COUNT 15
END
```

### 示例 2: 通胀预警

```
RULE inflation_warning: "CPI 突破警戒线"
DESCRIPTION "当 CPI 同比涨幅超过 3% 且 PPI 连续上涨，触发通胀预警"
TYPE composite
CATEGORY inflation
PRIORITY 9

CONDITION
  cpi.yoy > 0.03 AND
  TREND_UP(ppi.value, 3) AND
  core_cpi.yoy > 0.02

THEN
  CONCLUSION "通胀压力显著上升，建议增加抗通胀资产配置"
  CONFIDENCE 0.68
  IMPACT positive
  HORIZON short

METADATA
  SOURCE expert
  VALIDATED true
END
```

### 示例 3: 政策响应

```
RULE policy_response: "货币政策响应"
DESCRIPTION "当经济数据走弱且通胀温和时，央行可能采取宽松政策"
TYPE pattern
CATEGORY policy
PRIORITY 7

CONDITION
  gdp.growth < 0.05 AND
  unemployment.rate > 0.05 AND
  cpi.yoy < 0.02 AND
  IS_SEASONAL_PERIOD(MONTH(), "Q1|Q4")

THEN
  CONCLUSION "货币政策可能边际宽松，关注降准降息窗口"
  CONFIDENCE 0.60
  IMPACT positive
  HORIZON medium

METADATA
  SOURCE mined
  VALIDATED true
END
```

### 示例 4: 跨市场联动

```
RULE cross_market_linkage: "猪粮比价失衡"
DESCRIPTION "当猪粮比价低于盈亏平衡点且持续恶化，预示产能出清加速"
TYPE correlation
CATEGORY pig_cycle
PRIORITY 8

CONDITION
  pig_grain_ratio.value < 5.5 AND
  pig_grain_ratio.change < 0 AND
  TREND_DOWN(pig_grain_ratio.value, 2)

THEN
  CONCLUSION "养殖户亏损加剧，产能加速出清，周期底部特征明显"
  CONFIDENCE 0.70
  IMPACT neutral
  HORIZON medium

METADATA
  SOURCE expert
  VALIDATED true
END
```

## 解析器设计

### AST 结构

```typescript
interface RuleAST {
  type: 'rule';
  id: string;
  name: string;
  description: string;
  ruleType: RuleType;
  category: string;
  priority: number;
  condition: ConditionAST;
  inference: InferenceAST;
  metadata: MetadataAST;
}

interface ConditionAST {
  type: 'condition';
  expression: LogicalExpression;
}

interface LogicalExpression {
  type: 'logical_op';
  operator: 'AND' | 'OR' | 'NOT';
  operands: Expression[];
}

interface ComparisonExpression {
  type: 'comparison';
  operator: '>' | '<' | '=' | '>=' | '<=' | '!=';
  left: VariableRef | FunctionCall | Literal;
  right: VariableRef | FunctionCall | Literal;
}
```

## 执行流程

```
规则文本 → 词法分析 → 语法分析 → AST → 语义检查 → 可执行代码
                                      ↓
                                  错误报告

执行时:
数据上下文 + AST → 变量求值 → 条件评估 → 触发判断 → 结论输出
```

## 下一步

1. **实现词法分析器**: 将规则文本转换为 token 流
2. **实现语法分析器**: 构建 AST
3. **实现求值引擎**: 执行条件表达式
4. **构建规则库**: 基于 DSL 编写 10-20 条初始规则
5. **测试验证**: 用历史数据回测规则有效性

## 参考

- Drools 规则引擎
- Prometheus Alerting Rules
- OpenPolicyAgent Rego
- SQL 条件表达式
