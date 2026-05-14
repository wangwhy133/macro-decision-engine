import { Lexer } from './src/parser/tokens';

console.log('测试负数...');
try {
  const input = 'pig_inventory.change < -0.10';
  console.log('Input:', input);
  const lexer = new Lexer(input);
  const tokens = lexer.tokenize();
  console.log('Tokens:', tokens.map(t => `${t.type}(${t.value})`));
} catch (e: any) {
  console.error('Error:', e.message);
}

console.log('\n测试复杂规则...');
try {
  const input = `RULE test: "test"
DESCRIPTION "desc"
TYPE threshold
CATEGORY pig
PRIORITY 5
CONDITION
  x < -0.10
THEN
  CONCLUSION "c"
  CONFIDENCE 0.5
  IMPACT positive
  HORIZON short
METADATA
  SOURCE expert
  VALIDATED true
END
`;
  console.log('Input length:', input.length);
  const lexer = new Lexer(input);
  const tokens = lexer.tokenize();
  console.log('Token count:', tokens.length);
  console.log('First 10:', tokens.slice(0, 10).map(t => `${t.type}(${t.value})`));
} catch (e: any) {
  console.error('Error:', e.message);
  console.error('Stack:', e.stack);
}
