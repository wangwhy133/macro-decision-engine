# 宏观决策支持引擎 - 从这里开始

**快速开始指南 | 版本 v1.0.0 | 更新时间 2026-05-14**

---

## 这是什么？

宏观决策支持引擎是一个四层架构的决策支持系统：

```
数据可信度系统 → 规则推理系统 → AI 解释层 → 复盘校准系统
```

**核心价值**:
- 数据可信度评分 - 多源数据交叉验证，识别虚假信息
- 规则推理 - 基于领域专家知识自动推导结论
- AI 解释 - 生成可理解的情景分析和决策建议
- 复盘校准 - 持续优化，提高准确性

---

## 快速开始

### 1. 安装依赖

```bash
cd macro-decision-engine
pnpm install
```

### 2. 运行测试

```bash
npx tsx simple-test.ts
```

### 3. 查看示例规则

```bash
cat rules/pig_cycle.rules
```

---

## 项目结构

```
macro-decision-engine/
├── src/
│   ├── types/              # 类型定义
│   ├── services/           # 数据可信度服务
│   ├── parser/             # 规则 DSL 解析器
│   └── engine/             # 规则求值引擎
├── rules/                  # 规则文件
├── docs/                   # 文档
└── test-*.ts              # 测试脚本
```

---

## 核心功能

### 1. 数据可信度系统 ✅

```typescript
import { DataCredibilityService } from './src/services/DataCredibilityService';

const service = new DataCredibilityService();
const dataPoint = await service.ingest({
  source: 'eastmoney',
  sourceType: 'financial',
  timestamp: Date.now(),
  category: 'pig_cycle',
  data: { metric: '能繁母猪存栏量', value: 4500, unit: '万头' }
});

console.log(dataPoint.credibility.score); // 0.85
```

### 2. 规则 DSL

```
RULE pig_supply_shortage: "能繁母猪存栏大幅下降"
DESCRIPTION "连续 3 个月下降且累计降幅超过 10%"
TYPE trend
CATEGORY pig_cycle
PRIORITY 9

CONDITION
  pig_inventory.change[T] < 0 AND
  pig_inventory.change[T-1] < 0 AND
  pig_inventory.change[T-2] < 0 AND
  SUM(pig_inventory.change, 3) < -0.10

THEN
  CONCLUSION "生猪供给将在未来 6-12 个月收缩"
  CONFIDENCE 0.75
  IMPACT positive
  HORIZON medium

METADATA
  SOURCE expert
  VALIDATED true
END
```

### 3. 规则求值

```typescript
import { RuleEvaluator } from './src/engine/RuleEvaluator';

const evaluator = new RuleEvaluator();
evaluator.setDataContext(dataPoints);
const result = evaluator.evaluateBatch(rules);

console.log(result.triggeredRules);
console.log(result.conclusions);
```

---

## 文档导航

| 文档 | 说明 |
|------|------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | 完整架构设计 |
| [README.md](README.md) | 使用说明 |
| [PROGRESS.md](PROGRESS.md) | 实现进度 |
| [TASKS.md](TASKS.md) | 任务清单 |
| [docs/RULE_DSL.md](docs/RULE_DSL.md) | DSL 语法文档 |

---

## 下一步

### 本周任务

1. [ ] 修复解析器死循环问题
2. [ ] 完善规则求值引擎
3. [ ] 编写通胀规则集

### 长期目标

- [ ] AI 解释层集成 (MiniMax-M2.7)
- [ ] 复盘校准系统
- [ ] 历史数据回测

---

## 联系方式

- 项目发起人：王力
- Telegram: @MichaelDavid128

---

**开始编码吧！🚀**
