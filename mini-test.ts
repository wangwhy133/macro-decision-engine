import { Lexer } from './src/parser/tokens';

console.log('极简测试...');
try {
  const lexer = new Lexer('RULE test: "test"');
  const tokens = lexer.tokenize();
  console.log('Tokens:', tokens.map(t => t.type));
} catch (e: any) {
  console.error('Error:', e.message);
  console.error('Stack:', e.stack);
}
