/**
 * 规则 DSL 语法分析器 (重构版)
 * 采用算符优先 + 递归下降混合模式，解决死循环问题
 */

import { Token, TokenType, tokenize as lexerTokenize } from './tokens';
import {
  RuleAST,
  ConditionBlock,
  InferenceBlock,
  MetadataBlock,
  Expression,
  RuleType,
  ImpactType,
  TimeHorizon,
  SourceType,
  TimeReference,
  numberLiteral,
  stringLiteral,
  booleanLiteral,
  variableRef,
  functionCall,
  comparison,
  logical,
  unary,
  between as betweenExpr,
  parseRuleType,
  parseImpactType,
  parseTimeHorizon,
  parseSourceType,
  parseTimeRef,
} from './ast';

/**
 * 解析超时错误
 */
class ParseTimeoutError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'ParseTimeoutError';
  }
}

/**
 * 语法分析器类 (带超时保护)
 */
export class Parser {
  private tokens: Token[];
  private position: number = 0;
  private startTime: number = 0;
  private timeoutMs: number = 5000; // 5 秒超时

  constructor(tokens: Token[], timeoutMs: number = 5000) {
    this.tokens = tokens;
    this.timeoutMs = timeoutMs;
  }

  private currentToken(): Token {
    return this.tokens[this.position] || { type: TokenType.EOF, value: '', line: 0, column: 0 };
  }

  private peekToken(offset: number = 1): Token {
    return this.tokens[this.position + offset] || { type: TokenType.EOF, value: '', line: 0, column: 0 };
  }

  private advance(): Token {
    this.checkTimeout();
    const token = this.currentToken();
    if (this.position < this.tokens.length - 1) {
      this.position++;
    }
    return token;
  }

  private checkTimeout(): void {
    if (Date.now() - this.startTime > this.timeoutMs) {
      throw new ParseTimeoutError(
        `解析超时 (>${this.timeoutMs}ms). 规则可能过于复杂或存在语法错误。当前位置：Line ${this.currentToken().line}, Col ${this.currentToken().column}`
      );
    }
  }

  private match(...types: TokenType[]): boolean {
    return types.includes(this.currentToken().type);
  }

  private expect(type: TokenType, context: string): Token {
    if (this.currentToken().type !== type) {
      throw new Error(
        `期望 ${type}, 实际得到 ${this.currentToken().type} (${this.currentToken().value}) ` +
        `at line ${this.currentToken().line}, column ${this.currentToken().column} (上下文：${context})`
      );
    }
    return this.currentToken();
  }

  private consume(): Token {
    return this.advance();
  }

  private skipOptional(...types: TokenType[]): boolean {
    if (this.match(...types)) {
      this.advance();
      return true;
    }
    return false;
  }

  /**
   * 解析规则入口
   */
  parseRule(): RuleAST {
    this.startTime = Date.now();
    this.checkTimeout();

    // RULE rule_id: "规则名称"
    this.expect(TokenType.RULE, '规则开始');
    this.advance();

    const idToken = this.expect(TokenType.IDENTIFIER, '规则 ID');
    const ruleId = idToken.value;
    this.advance();

    this.skipOptional(TokenType.COLON);

    this.expect(TokenType.STRING, '规则名称');
    const nameToken = this.consume();
    const name = nameToken.value;

    const description = this.parseDescription();
    const ruleType = this.parseRuleType();
    const category = this.parseCategory();
    const priority = this.parsePriority();
    const condition = this.parseConditionBlock();
    const inference = this.parseInferenceBlock();
    const metadata = this.parseMetadataBlock();

    this.expect(TokenType.END, '规则结束');
    this.advance();

    return {
      type: 'rule',
      id: ruleId,
      name,
      description,
      ruleType,
      category,
      priority,
      condition,
      inference,
      metadata,
    };
  }

  private parseDescription(): string {
    this.expect(TokenType.DESCRIPTION, 'DESCRIPTION 关键字');
    this.advance();
    this.expect(TokenType.STRING, '描述字符串');
    const descToken = this.consume();
    return descToken.value;
  }

  private parseRuleType(): RuleType {
    this.expect(TokenType.TYPE, 'TYPE 关键字');
    this.advance();
    const typeToken = this.currentToken();
    this.advance();
    return parseRuleType(typeToken.value);
  }

  private parseCategory(): string {
    this.expect(TokenType.CATEGORY, 'CATEGORY 关键字');
    this.advance();
    const categoryToken = this.currentToken();
    this.advance();
    return categoryToken.value;
  }

  private parsePriority(): number {
    this.expect(TokenType.PRIORITY, 'PRIORITY 关键字');
    this.advance();
    const priorityToken = this.expect(TokenType.NUMBER, '优先级数字');
    this.advance();
    return parseInt(priorityToken.value, 10);
  }

  private parseConditionBlock(): ConditionBlock {
    this.expect(TokenType.CONDITION, 'CONDITION 关键字');
    this.advance();
    const expression = this.parseExpression();
    return { type: 'condition', expression };
  }

  private parseInferenceBlock(): InferenceBlock {
    this.expect(TokenType.THEN, 'THEN 关键字');
    this.advance();

    this.expect(TokenType.CONCLUSION, 'CONCLUSION 关键字');
    this.advance();
    this.expect(TokenType.STRING, '结论文本');
    const conclusionToken = this.consume();
    const conclusion = conclusionToken.value;

    this.expect(TokenType.CONFIDENCE, 'CONFIDENCE 关键字');
    this.advance();
    const confidenceToken = this.expect(TokenType.NUMBER, '置信度');
    this.advance();
    const confidence = parseFloat(confidenceToken.value);

    this.expect(TokenType.IMPACT, 'IMPACT 关键字');
    this.advance();
    const impactToken = this.currentToken();
    this.advance();
    const impact = parseImpactType(impactToken.value);

    this.expect(TokenType.HORIZON, 'HORIZON 关键字');
    this.advance();
    const horizonToken = this.currentToken();
    this.advance();
    const horizon = parseTimeHorizon(horizonToken.value);

    return {
      type: 'inference',
      conclusion,
      confidence,
      impact,
      horizon,
    };
  }

  private parseMetadataBlock(): MetadataBlock {
    this.expect(TokenType.METADATA, 'METADATA 关键字');
    this.advance();

    let source: SourceType = 'expert';
    let validated = false;
    let successRate: number | undefined;
    let validationCount: number | undefined;

    while (!this.match(TokenType.END, TokenType.EOF)) {
      this.checkTimeout();
      const keyToken = this.currentToken();

      if (keyToken.type === TokenType.SOURCE) {
        this.advance();
        const valueToken = this.currentToken();
        this.advance();
        source = parseSourceType(valueToken.value);
      } else if (keyToken.type === TokenType.VALIDATED) {
        this.advance();
        const valueToken = this.currentToken();
        this.advance();
        validated = valueToken.type === TokenType.TRUE;
      } else if (keyToken.type === TokenType.SUCCESS_RATE) {
        this.advance();
        const valueToken = this.expect(TokenType.NUMBER, '成功率');
        this.advance();
        successRate = parseFloat(valueToken.value);
      } else if (keyToken.type === TokenType.VALIDATION_COUNT) {
        this.advance();
        const valueToken = this.expect(TokenType.NUMBER, '验证次数');
        this.advance();
        validationCount = parseInt(valueToken.value, 10);
      } else {
        // 跳过未知字段
        this.advance();
      }
      this.skipOptional(TokenType.NEWLINE);
    }

    return {
      type: 'metadata',
      source,
      validated,
      successRate,
      validationCount,
    };
  }

  // ==================== 表达式解析 (算符优先) ====================

  /**
   * 解析表达式 (最低优先级：OR)
   */
  parseExpression(): Expression {
    return this.parseOrExpression();
  }

  /**
   * 解析 OR 表达式
   */
  private parseOrExpression(): Expression {
    this.checkTimeout();
    let left = this.parseAndExpression();

    while (this.match(TokenType.OR)) {
      this.advance();
      const right = this.parseAndExpression();
      left = logical('OR', left, right);
    }

    return left;
  }

  /**
   * 解析 AND 表达式
   */
  private parseAndExpression(): Expression {
    this.checkTimeout();
    let left = this.parseNotExpression();

    while (this.match(TokenType.AND)) {
      this.advance();
      const right = this.parseNotExpression();
      left = logical('AND', left, right);
    }

    return left;
  }

  /**
   * 解析 NOT 表达式
   */
  private parseNotExpression(): Expression {
    this.checkTimeout();
    if (this.match(TokenType.NOT)) {
      this.advance();
      const operand = this.parseNotExpression();
      return unary('NOT', operand);
    }
    return this.parseComparison();
  }

  /**
   * 解析比较表达式
   */
  private parseComparison(): Expression {
    this.checkTimeout();
    let left = this.parsePrimary();

    // 处理 BETWEEN
    if (this.match(TokenType.BETWEEN)) {
      this.advance();
      const low = this.parsePrimary();
      this.expect(TokenType.AND, 'BETWEEN 的 AND');
      this.advance();
      const high = this.parsePrimary();
      return betweenExpr(left, low, high);
    }

    // 处理比较运算符
    if (this.match(TokenType.GT, TokenType.LT, TokenType.GTE, TokenType.LTE, TokenType.EQ, TokenType.NEQ)) {
      const opToken = this.advance();
      const operator = opToken.value as '>' | '<' | '>=' | '<=' | '=' | '!=';
      const right = this.parsePrimary();
      return comparison(operator, left, right);
    }

    return left;
  }

  /**
   * 解析主要单元 (函数、变量、字面量、括号)
   */
  private parsePrimary(): Expression {
    this.checkTimeout();

    // 括号
    if (this.match(TokenType.LPAREN)) {
      this.advance();
      const expr = this.parseExpression();
      this.expect(TokenType.RPAREN, '右括号');
      this.advance();
      return expr;
    }

    // 数字
    if (this.match(TokenType.NUMBER)) {
      const token = this.advance();
      return numberLiteral(parseFloat(token.value));
    }

    // 字符串
    if (this.match(TokenType.STRING)) {
      const token = this.advance();
      return stringLiteral(token.value);
    }

    // 布尔值
    if (this.match(TokenType.TRUE, TokenType.FALSE)) {
      const token = this.advance();
      return booleanLiteral(token.type === TokenType.TRUE);
    }

    // 函数调用或变量引用
    if (
      this.match(
        TokenType.IDENTIFIER,
        TokenType.TREND_UP, TokenType.TREND_DOWN,
        TokenType.ACCELERATING_UP, TokenType.ACCELERATING_DOWN,
        TokenType.BREAKS_ABOVE, TokenType.BREAKS_BELOW,
        TokenType.CORRELATION_FUNC, TokenType.LEADS,
        TokenType.MATCHES_PATTERN, TokenType.IS_ANOMALY,
        TokenType.IS_SEASONAL_PERIOD, TokenType.CYCLE_POSITION,
        TokenType.AVG, TokenType.STD, TokenType.MIN,
        TokenType.MAX, TokenType.SUM, TokenType.PERCENTILE,
        TokenType.NOW, TokenType.YEAR, TokenType.MONTH,
        TokenType.QUARTER, TokenType.DAY_OF_WEEK
      )
    ) {
      const nameToken = this.advance();
      const name = nameToken.value;

      // 函数调用
      if (this.match(TokenType.LPAREN)) {
        this.advance();
        const args: Expression[] = [];
        if (!this.match(TokenType.RPAREN)) {
          args.push(this.parseExpression());
          while (this.match(TokenType.COMMA)) {
            this.advance();
            args.push(this.parseExpression());
          }
        }
        this.expect(TokenType.RPAREN, '函数参数结束');
        this.advance();
        return functionCall(name, args);
      }

      // 变量引用 (可能带时间下标)
      let timeRef: TimeReference | undefined;
      if (this.match(TokenType.LBRACKET)) {
        this.advance();
        const timeToken = this.currentToken();
        if (timeToken.type === TokenType.IDENTIFIER || timeToken.type === TokenType.NUMBER || timeToken.type === TokenType.STRING) {
          this.advance();
          try {
            if (timeToken.value.startsWith('T')) {
              timeRef = parseTimeRef(timeToken.value);
            } else if (timeToken.type === TokenType.NUMBER) {
              timeRef = { type: 'relative', offset: parseInt(timeToken.value, 10) };
            } else {
              timeRef = { type: 'absolute', value: timeToken.value };
            }
          } catch (e) {
            // 忽略解析错误
          }
        }
        this.expect(TokenType.RBRACKET, '时间引用结束');
        this.advance();
      }

      return variableRef(name, timeRef);
    }

    throw new Error(
      `意外的 Token: ${this.currentToken().type} (${this.currentToken().value}) ` +
      `at line ${this.currentToken().line}, column ${this.currentToken().column}. ` +
      `期望：数字、字符串、布尔值、函数或变量.`
    );
  }

  parseRules(): RuleAST[] {
    this.startTime = Date.now();
    const rules: RuleAST[] = [];
    while (!this.match(TokenType.EOF)) {
      this.checkTimeout();
      while (this.match(TokenType.NEWLINE)) this.advance();
      if (this.match(TokenType.RULE)) {
        rules.push(this.parseRule());
      } else if (!this.match(TokenType.EOF)) {
        this.advance();
      }
    }
    return rules;
  }
}

/**
 * 便捷函数：解析单条规则
 */
export function parseRule(input: string, timeoutMs?: number): RuleAST {
  const tokens = lexerTokenize(input);
  const parser = new Parser(tokens, timeoutMs);
  return parser.parseRule();
}

/**
 * 便捷函数：解析多条规则
 */
export function parseRules(input: string, timeoutMs?: number): RuleAST[] {
  const tokens = lexerTokenize(input);
  const parser = new Parser(tokens, timeoutMs);
  return parser.parseRules();
}
