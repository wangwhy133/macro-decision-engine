# 宏观决策支持引擎 - 实现进度报告

**版本**: v1.0.0  
**日期**: 2026-05-14  
**状态**: 核心框架完成，规则引擎原型可用

## 已完成组件

### ✅ 1. 数据可信度系统 (100%)

**文件**: `src/services/DataCredibilityService.ts`

**功能**:
- [x] 多源数据接入 (官方/财经/新闻/社交)
- [x] 可信度评分算法
  - 来源可靠性 (基于来源类型和历史准确性)
  - 时效性 (指数衰减，可配置半衰期)
  - 交叉验证一致性
  - 异常修正
- [x] 交叉验证机制 (多源数据一致性检验)
- [x] 异常检测 (统计学离群值 + 领域规则)
- [x] 来源可靠性配置系统

**核心算法**:
```typescript
score = sourceReliability × timeliness × consistency × anomalyModifier
```

**测试结果**:
- 单个数据点接入：✅
- 批量数据接入：✅
- 交叉验证：✅
- 异常检测：✅

---

### ✅ 2. 规则 DSL 解析器 (90%)

**文件**: 
- `src/parser/tokens.ts` - 词法分析器
- `src/parser/ast.ts` - AST 定义
- `src/parser/parser.ts` - 语法分析器

**功能**:
- [x] 完整词法分析器
  - 关键字识别 (RULE, DESCRIPTION, TYPE 等)
  - 操作符识别 (>, <, AND, OR 等)
  - 函数识别 (TREND_UP, AVG, SUM 等)
  - 字符串、数字、标识符
- [x] 递归下降语法分析器
  - 规则结构解析
  - 条件表达式解析
  - 逻辑运算符优先级
  - 函数调用解析
- [x] AST 构建
- [x] 错误处理

**支持的语法**:
```
RULE rule_id: "名称"
DESCRIPTION "描述"
TYPE threshold|trend|correlation|pattern|composite
CATEGORY category_name
PRIORITY 1-10

CONDITION
  <表达式>

THEN
  CONCLUSION "结论"
  CONFIDENCE 0.0-1.0
  IMPACT positive|negative|neutral
  HORIZON short|medium|long

METADATA
  SOURCE expert|mined|learned
  VALIDATED true|false
  ...
END
```

**表达式支持**:
- 比较运算：`>`, `<`, `>=`, `<=`, `=`, `!=`
- 逻辑运算：`AND`, `OR`, `NOT`
- 区间判断：`BETWEEN x AND y`
- 函数调用：`AVG()`, `SUM()`, `TREND_UP()`, 等
- 时间引用：`T-1`, `T-12`, `[2024-01]`
- 变量属性：`pig_inventory.change`, `pig_inventory.change.pct`

---

### ✅ 3. 规则求值引擎 (70%)

**文件**: `src/engine/RuleEvaluator.ts`

**功能**:
- [x] 变量上下文管理
- [x] 内置函数库
  - 趋势函数：`TREND_UP`, `TREND_DOWN`
  - 聚合函数：`AVG`, `SUM`, `MAX`, `MIN`
  - 时间函数：`NOW`, `MONTH`, `YEAR`
- [x] 条件表达式求值
- [x] 批量规则评估
- [ ] 复杂函数完整实现 (CORRELATION, LEADS 等)
- [ ] 时间引用完整支持

---

### ✅ 4. 示例规则库

**文件**: `rules/pig_cycle.rules`

**已编写 5 条猪周期核心规则**:
1. `pig_supply_shortage` - 能繁母猪存栏大幅下降 (优先级 9)
2. `pig_grain_ratio_low` - 猪粮比价跌破盈亏平衡点 (优先级 8)
3. `pig_inventory_low` - 能繁母猪存栏处于历史低位 (优先级 7)
4. `pig_demand_seasonal` - 猪肉消费旺季来临 (优先级 6)
5. `pig_disease_outbreak` - 猪瘟等疫情爆发 (优先级 10)

---

## 项目结构

```
macro-decision-engine/
├── src/
│   ├── types/
│   │   └── index.ts              # 核心类型定义
│   ├── services/
│   │   ├── interfaces.ts         # 服务接口定义
│   │   └── DataCredibilityService.ts  # 数据可信度服务
│   ├── parser/
│   │   ├── tokens.ts             # 词法分析器
│   │   ├── ast.ts                # AST 定义
│   │   └── parser.ts             # 语法分析器
│   ├── engine/
│   │   └── RuleEvaluator.ts      # 规则求值引擎
│   └── index.ts                  # 主入口
├── rules/
│   └── pig_cycle.rules           # 猪周期规则集
├── docs/
│   └── RULE_DSL.md               # DSL 设计文档
├── test-demo.ts                  # 演示脚本
├── package.json
├── tsconfig.json
├── ARCHITECTURE.md               # 架构文档
├── README.md                     # 使用说明
├── TASKS.md                      # 任务清单
└── IMPLEMENTATION.md             # 本文件
```

---

## 下一步工作

### 立即可做 (Phase 2)

1. **完善规则求值引擎**
   - [ ] 实现剩余内置函数 (CORRELATION, LEADS, BREAKS_ABOVE 等)
   - [ ] 完善时间引用支持 (T-1, T-12 等)
   - [ ] 添加更完善的错误处理

2. **编写更多规则**
   - [ ] 通胀规则集 (3 条)
   - [ ] 政策规则集 (3 条)
   - [ ] 跨市场规则集 (3 条)

3. **测试与验证**
   - [ ] 单元测试
   - [ ] 集成测试
   - [ ] 历史数据回测

### 后续阶段

**Phase 3: AI 解释层** (3-4 周)
- MiniMax-M2.7 集成
- 语义理解
- 情景生成
- 可解释性输出

**Phase 4: 复盘校准系统** (2-3 周)
- 决策日志
- 误差分析
- 自动校准

**Phase 5: 编排与集成** (2 周)
- 决策编排服务
- eastmoney-data-api 集成
- API 接口

---

## 技术亮点

1. **可信度评分算法**: 多维度评分，考虑来源、时效、一致性、异常
2. **领域特定 DSL**: 专为宏观决策设计，支持趋势、相关性、模式等概念
3. **可解释性优先**: 每条规则、每个推理链都可追溯
4. **分层架构**: 四层独立，可单独测试和迭代

---

## 已知问题

1. 词法分析器对中文引号支持不完善
2. 复杂函数 (如 CORRELATION) 需要更多数据支持
3. 规则冲突检测机制尚未实现
4. 缺少持久化存储层

---

## 运行测试

```bash
cd macro-decision-engine

# 安装依赖
pnpm install

# 运行演示
npx tsx test-demo.ts

# 或构建后运行
pnpm build
node dist/index.js --parse rules/pig_cycle.rules
```

---

*最后更新：2026-05-14*
