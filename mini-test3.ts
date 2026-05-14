import { Lexer } from './src/parser/tokens';

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

console.log('开始分词...');
const start = Date.now();
try {
  const lexer = new Lexer(ruleText);
  const tokens = lexer.tokenize();
  const end = Date.now();
  console.log(`✅ 分词成功！耗时：${end - start}ms`);
  console.log(`Token 数量：${tokens.length}`);
  console.log('Tokens:', tokens.map(t => `${t.type}(${t.value.substring(0, 20)})`));
} catch (e: any) {
  console.error('❌ 错误:', e.message);
  if (e.stack) console.error(e.stack);
}
