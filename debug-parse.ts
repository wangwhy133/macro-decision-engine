/**
 * 最小化调试测试
 */

import { tokenize } from './src/parser/tokens';
import { Parser } from './src/parser/parser';

console.log('🔍 最小化调试测试\n');

const ruleText = `
RULE test_neg: "负数测试"
DESCRIPTION "测试负数字面量"
TYPE threshold
CATEGORY pig_cycle
PRIORITY 8
CONDITION
  pig_inventory.change < -0.10
THEN
  CONCLUSION "负数测试通过"
  CONFIDENCE 0.75
  IMPACT positive
  HORIZON medium
METADATA
  SOURCE expert
  VALIDATED true
END
`;

console.log('步骤 1: 分词...');
try {
  const tokens = tokenize(ruleText);
  console.log(`✅ 分词成功：${tokens.length} 个 tokens`);
  console.log('前 15 个 tokens:');
  tokens.slice(0, 15).forEach((t, i) => {
    console.log(`  ${i + 1}. ${t.type}: "${t.value}"`);
  });
  
  console.log('\n步骤 2: 解析...');
  const parser = new Parser(tokens, 2000); // 2 秒超时
  
  console.log('开始解析规则...');
  const startTime = Date.now();
  const rule = parser.parseRule();
  const endTime = Date.now();
  
  console.log(`✅ 解析成功！耗时：${endTime - startTime}ms`);
  console.log(`规则 ID: ${rule.id}`);
  console.log(`规则名称：${rule.name}`);
  console.log(`条件类型：${rule.condition.expression.type}`);
  
} catch (e: any) {
  console.error(`❌ 错误：${e.message}`);
  if (e.stack) {
    console.error('堆栈:', e.stack.split('\n').slice(0, 10).join('\n'));
  }
}
