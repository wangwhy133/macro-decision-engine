/**
 * 规则 DSL 词法分析器 (最终修复版 - 状态机模式)
 * 修复重点：彻底根除死循环，完美支持负数，增强鲁棒性
 */

export enum TokenType {
  // 关键字
  RULE = 'RULE', DESCRIPTION = 'DESCRIPTION', TYPE = 'TYPE', CATEGORY = 'CATEGORY',
  PRIORITY = 'PRIORITY', CONDITION = 'CONDITION', THEN = 'THEN', CONCLUSION = 'CONCLUSION',
  CONFIDENCE = 'CONFIDENCE', IMPACT = 'IMPACT', HORIZON = 'HORIZON', METADATA = 'METADATA',
  SOURCE = 'SOURCE', CREATED_AT = 'CREATED_AT', VALIDATED = 'VALIDATED',
  SUCCESS_RATE = 'SUCCESS_RATE', VALIDATION_COUNT = 'VALIDATION_COUNT', END = 'END',
  // 类型值
  THRESHOLD = 'THRESHOLD', TREND = 'TREND', CORRELATION = 'CORRELATION',
  PATTERN = 'PATTERN', COMPOSITE = 'COMPOSITE',
  POSITIVE = 'POSITIVE', NEGATIVE = 'NEGATIVE', NEUTRAL = 'NEUTRAL',
  SHORT = 'SHORT', MEDIUM = 'MEDIUM', LONG = 'LONG',
  EXPERT = 'EXPERT', MINED = 'MINED', LEARNED = 'LEARNED',
  TRUE = 'TRUE', FALSE = 'FALSE',
  // 运算符
  AND = 'AND', OR = 'OR', NOT = 'NOT', BETWEEN = 'BETWEEN',
  GT = 'GT', LT = 'LT', GTE = 'GTE', LTE = 'LTE', EQ = 'EQ', NEQ = 'NEQ',
  // 符号
  COMMA = 'COMMA', COLON = 'COLON', LPAREN = 'LPAREN', RPAREN = 'RPAREN',
  LBRACKET = 'LBRACKET', RBRACKET = 'RBRACKET', LBRACE = 'LBRACE', RBRACE = 'RBRACE',
  // 函数
  TREND_UP = 'TREND_UP', TREND_DOWN = 'TREND_DOWN', ACCELERATING_UP = 'ACCELERATING_UP',
  ACCELERATING_DOWN = 'ACCELERATING_DOWN', BREAKS_ABOVE = 'BREAKS_ABOVE',
  BREAKS_BELOW = 'BREAKS_BELOW', CORRELATION_FUNC = 'CORRELATION_FUNC',
  LEADS = 'LEADS', MATCHES_PATTERN = 'MATCHES_PATTERN', IS_ANOMALY = 'IS_ANOMALY',
  IS_SEASONAL_PERIOD = 'IS_SEASONAL_PERIOD', CYCLE_POSITION = 'CYCLE_POSITION',
  AVG = 'AVG', STD = 'STD', MIN = 'MIN', MAX = 'MAX', SUM = 'SUM', PERCENTILE = 'PERCENTILE',
  NOW = 'NOW', YEAR = 'YEAR', MONTH = 'MONTH', QUARTER = 'QUARTER', DAY_OF_WEEK = 'DAY_OF_WEEK',
  // 基础类型
  IDENTIFIER = 'IDENTIFIER', NUMBER = 'NUMBER', STRING = 'STRING', TIME_REF = 'TIME_REF',
  NEWLINE = 'NEWLINE', EOF = 'EOF',
}

export interface Token {
  type: TokenType;
  value: string;
  line: number;
  column: number;
}

const KEYWORDS: Record<string, TokenType> = {
  'RULE': TokenType.RULE, 'DESCRIPTION': TokenType.DESCRIPTION, 'TYPE': TokenType.TYPE,
  'CATEGORY': TokenType.CATEGORY, 'PRIORITY': TokenType.PRIORITY, 'CONDITION': TokenType.CONDITION,
  'THEN': TokenType.THEN, 'CONCLUSION': TokenType.CONCLUSION, 'CONFIDENCE': TokenType.CONFIDENCE,
  'IMPACT': TokenType.IMPACT, 'HORIZON': TokenType.HORIZON, 'METADATA': TokenType.METADATA,
  'SOURCE': TokenType.SOURCE, 'CREATED_AT': TokenType.CREATED_AT, 'VALIDATED': TokenType.VALIDATED,
  'SUCCESS_RATE': TokenType.SUCCESS_RATE, 'VALIDATION_COUNT': TokenType.VALIDATION_COUNT,
  'END': TokenType.END, 'threshold': TokenType.THRESHOLD, 'trend': TokenType.TREND,
  'correlation': TokenType.CORRELATION, 'pattern': TokenType.PATTERN, 'composite': TokenType.COMPOSITE,
  'positive': TokenType.POSITIVE, 'negative': TokenType.NEGATIVE, 'neutral': TokenType.NEUTRAL,
  'short': TokenType.SHORT, 'medium': TokenType.MEDIUM, 'long': TokenType.LONG,
  'expert': TokenType.EXPERT, 'mined': TokenType.MINED, 'learned': TokenType.LEARNED,
  'true': TokenType.TRUE, 'false': TokenType.FALSE, 'AND': TokenType.AND, 'OR': TokenType.OR,
  'NOT': TokenType.NOT, 'BETWEEN': TokenType.BETWEEN, 'TREND_UP': TokenType.TREND_UP,
  'TREND_DOWN': TokenType.TREND_DOWN, 'ACCELERATING_UP': TokenType.ACCELERATING_UP,
  'ACCELERATING_DOWN': TokenType.ACCELERATING_DOWN, 'BREAKS_ABOVE': TokenType.BREAKS_ABOVE,
  'BREAKS_BELOW': TokenType.BREAKS_BELOW, 'CORRELATION': TokenType.CORRELATION_FUNC,
  'LEADS': TokenType.LEADS, 'MATCHES_PATTERN': TokenType.MATCHES_PATTERN,
  'IS_ANOMALY': TokenType.IS_ANOMALY, 'IS_SEASONAL_PERIOD': TokenType.IS_SEASONAL_PERIOD,
  'CYCLE_POSITION': TokenType.CYCLE_POSITION, 'AVG': TokenType.AVG, 'STD': TokenType.STD,
  'MIN': TokenType.MIN, 'MAX': TokenType.MAX, 'SUM': TokenType.SUM, 'PERCENTILE': TokenType.PERCENTILE,
  'NOW': TokenType.NOW, 'YEAR': TokenType.YEAR, 'MONTH': TokenType.MONTH,
  'QUARTER': TokenType.QUARTER, 'DAY_OF_WEEK': TokenType.DAY_OF_WEEK,
};

const OPERATORS: Record<string, TokenType> = {
  '>': TokenType.GT, '<': TokenType.LT, '>=': TokenType.GTE, '<=': TokenType.LTE,
  '=': TokenType.EQ, '!=': TokenType.NEQ,
};

export class Lexer {
  private input: string;
  private pos: number = 0;
  private line: number = 1;
  private col: number = 1;
  private lastTokenType: TokenType | null = null;
  private maxIterations: number = 0; // 防止死循环的安全阀

  constructor(input: string) {
    this.input = input;
    this.maxIterations = input.length * 2 + 1000; // 安全阈值
  }

  private curr(): string { return this.input[this.pos] || ''; }
  private peek(): string { return this.input[this.pos + 1] || ''; }
  
  private advance(): void {
    if (this.curr() === '\n') { this.line++; this.col = 1; }
    else { this.col++; }
    this.pos++;
    // 安全阀：防止死循环
    if (this.pos > this.input.length + 10) {
      throw new Error(`词法分析死循环保护触发 at line ${this.line}`);
    }
  }

  private skipWhitespace(): void {
    while (this.curr() !== '' && /\s/.test(this.curr())) {
      this.advance();
    }
  }

  private skipComment(): void {
    if (this.curr() === '#') {
      while (this.curr() !== '\n' && this.curr() !== '') this.advance();
    }
  }

  private readIdentifier(): Token {
    const startLine = this.line;
    const startCol = this.col;
    let value = '';
    while (this.curr() !== '' && /[a-zA-Z0-9_\.]/.test(this.curr())) {
      value += this.curr();
      this.advance();
    }
    const type = KEYWORDS[value] || TokenType.IDENTIFIER;
    const token = { type, value, line: startLine, column: startCol };
    this.lastTokenType = type;
    return token;
  }

  private readNumber(): Token {
    const startLine = this.line;
    const startCol = this.col;
    let value = '';
    // 整数部分
    while (this.curr() !== '' && /[0-9]/.test(this.curr())) {
      value += this.curr();
      this.advance();
    }
    // 小数部分
    if (this.curr() === '.' && /[0-9]/.test(this.peek())) {
      value += this.curr();
      this.advance();
      while (this.curr() !== '' && /[0-9]/.test(this.curr())) {
        value += this.curr();
        this.advance();
      }
    }
    const token = { type: TokenType.NUMBER, value, line: startLine, column: startCol };
    this.lastTokenType = TokenType.NUMBER;
    return token;
  }

  private readString(): Token {
    const startLine = this.line;
    const startCol = this.col;
    const quote = this.curr();
    this.advance(); // skip opening quote
    let value = '';
    while (this.curr() !== '' && this.curr() !== quote) {
      if (this.curr() === '\\' && this.peek() !== '') {
        this.advance(); // skip backslash
        const esc = this.curr();
        if (esc === 'n') value += '\n';
        else if (esc === 't') value += '\t';
        else if (esc === 'r') value += '\r';
        else value += esc;
      } else {
        value += this.curr();
      }
      this.advance();
    }
    if (this.curr() === quote) this.advance(); // skip closing quote
    const token = { type: TokenType.STRING, value, line: startLine, column: startCol };
    this.lastTokenType = TokenType.STRING;
    return token;
  }

  private readTimeRef(): Token {
    const startLine = this.line;
    const startCol = this.col;
    let value = 'T';
    this.advance(); // skip 'T'
    while (this.curr() !== '' && /[\-\d]/.test(this.curr())) {
      value += this.curr();
      this.advance();
    }
    const token = { type: TokenType.TIME_REF, value, line: startLine, column: startCol };
    this.lastTokenType = TokenType.TIME_REF;
    return token;
  }

  // 核心修复：判断是否需要解析为负数
  private isNegativeNumberContext(): boolean {
    if (this.lastTokenType === null) return true;
    const t = this.lastTokenType;
    return (
      t === TokenType.GT || t === TokenType.LT || t === TokenType.GTE || t === TokenType.LTE ||
      t === TokenType.EQ || t === TokenType.NEQ || t === TokenType.AND || t === TokenType.OR ||
      t === TokenType.NOT || t === TokenType.LPAREN || t === TokenType.COMMA || t === TokenType.COLON
    );
  }

  private nextToken(): Token {
    while (this.curr() !== '') {
      // 1. 空白与注释
      if (/\s/.test(this.curr())) { this.skipWhitespace(); continue; }
      if (this.curr() === '#') { this.skipComment(); continue; }

      const startLine = this.line;
      const startCol = this.col;

      // 2. 字符串
      if (this.curr() === '"' || this.curr() === "'") {
        return this.readString();
      }

      // 3. 时间引用 (T-1)
      if (this.curr() === 'T' && (this.peek() === '-' || this.peek() === '+' || this.peek() === '[')) {
        return this.readTimeRef();
      }

      // 4. 标识符
      if (/[a-zA-Z_]/.test(this.curr())) {
        return this.readIdentifier();
      }

      // 5. 数字 (直接数字)
      if (/[0-9]/.test(this.curr())) {
        return this.readNumber();
      }

      // 6. 负数 (上下文感知)
      if (this.curr() === '-' && this.isNegativeNumberContext() && /[0-9]/.test(this.peek())) {
        this.advance(); // skip '-'
        // 直接调用 readNumber 的核心逻辑，但加上负号
        const numToken = this.readNumber();
        numToken.value = '-' + numToken.value;
        return numToken;
      }

      // 7. 多字符运算符
      const twoChar = this.curr() + this.peek();
      if (OPERATORS[twoChar]) {
        this.advance(); this.advance();
        const token = { type: OPERATORS[twoChar], value: twoChar, line: startLine, column: startCol };
        this.lastTokenType = OPERATORS[twoChar];
        return token;
      }

      // 8. 单字符运算符
      if (OPERATORS[this.curr()]) {
        const type = OPERATORS[this.curr()];
        const token = { type, value: this.curr(), line: startLine, column: startCol };
        this.advance();
        this.lastTokenType = type;
        return token;
      }

      // 9. 特殊符号
      const char = this.curr();
      this.advance();
      let type: TokenType = TokenType.EOF;
      if (char === ',') type = TokenType.COMMA;
      else if (char === ':') type = TokenType.COLON;
      else if (char === '(') type = TokenType.LPAREN;
      else if (char === ')') type = TokenType.RPAREN;
      else if (char === '[') type = TokenType.LBRACKET;
      else if (char === ']') type = TokenType.RBRACKET;
      else if (char === '{') type = TokenType.LBRACE;
      else if (char === '}') type = TokenType.RBRACE;
      
      if (type !== TokenType.EOF) {
        this.lastTokenType = type;
        return { type, value: char, line: startLine, column: startCol };
      }

      // 10. 未知字符
      throw new Error(`未知字符：'${char}' at line ${startLine}, column ${startCol}`);
    }

    const token = { type: TokenType.EOF, value: '', line: this.line, column: this.col };
    this.lastTokenType = TokenType.EOF;
    return token;
  }

  tokenize(): Token[] {
    const tokens: Token[] = [];
    this.pos = 0;
    this.line = 1;
    this.col = 1;
    this.lastTokenType = null;
    
    let count = 0;
    while (true) {
      count++;
      if (count > this.maxIterations) {
        throw new Error('词法分析死循环保护触发');
      }
      const token = this.nextToken();
      tokens.push(token);
      if (token.type === TokenType.EOF) break;
    }
    return tokens;
  }
}

export function tokenize(input: string): Token[] {
  const lexer = new Lexer(input);
  return lexer.tokenize();
}
