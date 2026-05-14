# 宏观决策支持引擎 v1.0 - 发布说明

**发布日期**: 2026-05-14  
**版本**: v1.0.0  
**状态**: 核心功能可用，部分优化中

---

## 🎉 本次更新亮点

### 1. ✅ 词法分析器负数修复
**问题**: 之前版本无法识别 `-0.10` 这样的负数字面量，导致规则解析失败。  
**修复**: 实现上下文感知的负数解析逻辑，在操作符后、左括号后、行首等位置自动将 `-` 和后续数字合并为负数。  
**验证**:
```typescript
// ✅ 现在可以正常解析
pig_inventory.change < -0.10
```

### 2. ✅ 数据验证增强
**新增功能**:
- 猪周期数据负值拦截
- 无穷大数值拦截
- 自动过期清理 (30 天)
- 单指标数据量限制 (1000 条)

**交易员收益**: 防止错误数据污染模型，确保决策质量。

### 3. ✅ 内存管理优化
**新增配置**:
```typescript
maxDataPointsPerMetric: 1000,  // 防止内存泄漏
maxAgeHours: 720,              // 30 天自动过期
```

---

## 📊 测试验证结果

### 通过项目 (6/6)
```
✅ 正常数据接入：可信度 0.850
✅ 负数数据拦截：猪周期数据不能为负
✅ 无穷大数据拦截
✅ 分词功能：负数字面量解析
✅ 简单规则解析
✅ 函数调用解析
```

### 待优化项目
- ⚠️  复杂嵌套规则解析超时 (Phase 2 优化)
- ⚠️  BETWEEN 语法糖暂时移除 (保持核心稳定)

---

## 🚀 使用示例

### 数据可信度评分
```typescript
import { DataCredibilityService } from './src/services/DataCredibilityService';

const service = new DataCredibilityService();

// 接入数据 (自动验证)
const data = await service.ingest({
  source: 'eastmoney',
  sourceType: 'financial',
  timestamp: Date.now(),
  category: 'pig_cycle',
  data: { metric: '能繁母猪存栏量', value: 4500, unit: '万头' },
  tags: ['猪周期']
});

console.log(`可信度评分：${data.credibility.score.toFixed(3)}`);
// 输出：可信度评分：0.850
```

### 规则解析 (含负数)
```typescript
import { parseRule } from './src/parser/parser';

const rule = parseRule(`
RULE pig_test: "负数测试规则"
DESCRIPTION "测试负数字面量解析"
TYPE threshold
CATEGORY pig_cycle
PRIORITY 8
CONDITION
  pig_inventory.change < -0.10
THEN
  CONCLUSION "存栏量下降超过 10%，供给收缩信号"
  CONFIDENCE 0.75
  IMPACT positive
  HORIZON medium
METADATA
  SOURCE expert
  VALIDATED true
END
`);

console.log(`规则解析成功：${rule.name}`);
```

---

## 📁 文件清单

| 文件 | 状态 | 说明 |
|------|------|------|
| `src/parser/tokens.ts` | ✅ 已修复 | 支持负数字面量 |
| `src/services/DataCredibilityService.ts` | ✅ 已增强 | 数据验证 + 内存管理 |
| `src/parser/parser.ts` | ⚠️ 部分优化 | 简单规则可用 |
| `validate-fix.ts` | ✅ 新增 | 快速验证脚本 |
| `final-validation.ts` | ✅ 新增 | 完整功能验证 |
| `RELEASE_NOTES_v1.0.md` | ✅ 本文件 | 发布说明 |

---

## 🛠️ 技术细节

### 负数解析原理
```typescript
// 上下文感知：在以下场景将 '-' 识别为负号而非减号
if (this.currentChar() === '-' && this.isNegativeNumberContext() && this.peekChar().match(/[0-9]/)) {
  this.advance(); // 跳过 '-'
  let value = '-' + this.readNumberValue(); // 读取数字并加负号
  return { type: TokenType.NUMBER, value };
}

// 判断上下文的逻辑
private isNegativeNumberContext(): boolean {
  if (this.lastTokenType === null) return true; // 行首
  const t = this.lastTokenType;
  return (
    t === TokenType.GT || t === TokenType.LT ||  // 比较运算符后
    t === TokenType.AND || t === TokenType.OR || // 逻辑运算符后
    t === TokenType.LPAREN || t === TokenType.COMMA // 左括号/逗号后
  );
}
```

---

## ⚠️ 已知限制

### 1. 复杂规则解析
**现象**: 多层嵌套或包含多个 AND/OR 的规则可能超时。  
**临时方案**: 拆分规则，使用简单逻辑组合。  
**计划**: Phase 2 重构解析器性能。

### 2. 时间引用格式
**现象**: `T-1` 格式支持有限。  
**临时方案**: 使用绝对时间戳或简单偏移。  
**计划**: Phase 2 完善时间引用解析。

---

## 📅 后续计划

### Phase 2 (本周): 性能优化
- [ ] 解析器性能优化
- [ ] 完善时间引用
- [ ] 恢复 BETWEEN 语法糖

### Phase 3 (下周): AI 解释层
- [ ] MiniMax 集成
- [ ] 情景生成
- [ ] 可解释性输出

### Phase 4 (两周后): 持久化
- [ ] SQLite 存储
- [ ] 历史数据查询

---

## 🎯 推荐使用场景

**✅ 适合**:
- 数据可信度评分
- 简单规则解析和求值
- 原型验证和技术演示
- 学习和研究

**⚠️ 暂不适合**:
- 高并发生产环境
- 复杂嵌套规则
- 长时间无维护运行

---

## 📞 联系方式

- 项目发起人：王力
- Telegram: @MichaelDavid128
- 项目路径：`/root/.openclaw/workspace/macro-decision-engine/`

---

*发布完成 | 2026-05-14*
