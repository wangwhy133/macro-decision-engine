// 快速测试词法分析器
import { tokenize, TokenType } from './src/parser/tokens.js';

console.log('='.repeat(60));
console.log('宏观决策支持引擎 - 快速测试');
console.log('='.repeat(60));

// 测试 1: 简单规则文本分词
console.log('\n【测试 1】简单规则分词');
const ruleText = `
RULE test_rule: "测试规则"
DESCRIPTION "测试描述"
TYPE trend
CATEGORY pig_cycle
PRIORITY 8
CONDITION
  pig_inventory.change < -0.10
THEN
  CONCLUSION "结论"
  CONFIDENCE 0.75
  IMPACT positive
  HORIZON medium
METADATA
  SOURCE expert
  VALIDATED true
END
`;

try {
  const tokens = tokenize(ruleText);
  console.log(`成功分词：${tokens.length} 个 tokens`);
  console.log('前 10 个 tokens:');
  tokens.slice(0, 10).forEach((t, i) => {
    console.log(`  ${i + 1}. ${t.type}: "${t.value}"`);
  });
} catch (error) {
  console.error('分词失败:', error.message);
}

// 测试 2: 解析完整规则
console.log('\n【测试 2】解析完整规则');
import { parseRule } from './src/parser/parser.js';

try {
  const rule = parseRule(ruleText);
  console.log('规则解析成功:');
  console.log(`  ID: ${rule.id}`);
  console.log(`  名称：${rule.name}`);
  console.log(`  类型：${rule.ruleType}`);
  console.log(`  类别：${rule.category}`);
  console.log(`  优先级：${rule.priority}`);
  console.log(`  结论：${rule.inference.conclusion}`);
  console.log(`  置信度：${rule.inference.confidence}`);
} catch (error) {
  console.error('规则解析失败:', error.message);
}

console.log('\n' + '='.repeat(60));
console.log('测试完成');
console.log('='.repeat(60));
