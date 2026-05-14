/**
 * 简单测试 - 仅测试核心功能
 */

import { tokenize } from './src/parser/tokens';
import { parseRule } from './src/parser/parser';

console.log('宏观决策支持引擎 - 简单测试\n');

// 测试 1: 分词
console.log('【测试 1】分词功能');
const testText = 'RULE test: "测试"';
const tokens = tokenize(testText);
console.log(`输入：${testText}`);
console.log(`Tokens: ${tokens.length} 个`);
tokens.forEach(t => console.log(`  - ${t.type}: "${t.value}"`));

// 测试 2: 解析规则
console.log('\n【测试 2】解析规则');
const ruleText = `
RULE pig_test: "测试规则"
DESCRIPTION "测试描述"
TYPE trend
CATEGORY pig_cycle
PRIORITY 8
CONDITION
  pig_inventory.change < -0.10
THEN
  CONCLUSION "测试结论"
  CONFIDENCE 0.75
  IMPACT positive
  HORIZON medium
METADATA
  SOURCE expert
  VALIDATED true
END
`;

try {
  const rule = parseRule(ruleText);
  console.log(`规则 ID: ${rule.id}`);
  console.log(`规则名称：${rule.name}`);
  console.log(`类型：${rule.ruleType}`);
  console.log(`类别：${rule.category}`);
  console.log(`优先级：${rule.priority}`);
  console.log(`结论：${rule.inference.conclusion}`);
  console.log(`置信度：${rule.inference.confidence}`);
  console.log('解析成功!');
} catch (error: any) {
  console.error('解析失败:', error.message);
}

console.log('\n测试完成');
