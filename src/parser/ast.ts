/**
 * 规则 DSL 抽象语法树 (AST) 节点定义
 */

/**
 * 规则 AST 根节点
 */
export interface RuleAST {
  type: 'rule';
  id: string;
  name: string;
  description: string;
  ruleType: RuleType;
  category: string;
  priority: number;
  condition: ConditionBlock;
  inference: InferenceBlock;
  metadata: MetadataBlock;
}

/**
 * 规则类型
 */
export type RuleType = 'threshold' | 'trend' | 'correlation' | 'pattern' | 'composite';

/**
 * 条件块
 */
export interface ConditionBlock {
  type: 'condition';
  expression: Expression;
}

/**
 * 推理块
 */
export interface InferenceBlock {
  type: 'inference';
  conclusion: string;
  confidence: number;
  impact: ImpactType;
  horizon: TimeHorizon;
}

/**
 * 元数据块
 */
export interface MetadataBlock {
  type: 'metadata';
  source: SourceType;
  createdAt?: number;
  validated: boolean;
  successRate?: number;
  validationCount?: number;
}

/**
 * 影响类型
 */
export type ImpactType = 'positive' | 'negative' | 'neutral';

/**
 * 时间范围
 */
export type TimeHorizon = 'short' | 'medium' | 'long';

/**
 * 来源类型
 */
export type SourceType = 'expert' | 'mined' | 'learned';

/**
 * 表达式类型
 */
export type Expression =
  | LogicalExpression
  | ComparisonExpression
  | FunctionCall
  | VariableRef
  | Literal
  | BetweenExpression
  | UnaryExpression;

/**
 * 逻辑表达式 (AND, OR)
 */
export interface LogicalExpression {
  type: 'logical';
  operator: 'AND' | 'OR';
  left: Expression;
  right: Expression;
}

/**
 * 比较表达式 (>, <, =, etc.)
 */
export interface ComparisonExpression {
  type: 'comparison';
  operator: '>' | '<' | '>=' | '<=' | '=' | '!=';
  left: Expression;
  right: Expression;
}

/**
 * 一元表达式 (NOT)
 */
export interface UnaryExpression {
  type: 'unary';
  operator: 'NOT';
  operand: Expression;
}

/**
 * Between 表达式
 */
export interface BetweenExpression {
  type: 'between';
  variable: Expression;
  low: Expression;
  high: Expression;
}

/**
 * 函数调用
 */
export interface FunctionCall {
  type: 'function_call';
  name: string;
  args: Expression[];
}

/**
 * 变量引用
 */
export interface VariableRef {
  type: 'variable_ref';
  name: string;
  timeRef?: TimeReference;
}

/**
 * 时间引用
 */
export interface TimeReference {
  type: 'relative' | 'absolute';
  offset?: number;  // T-1, T-12 等
  value?: string;   // "2024-01" 等
}

/**
 * 字面量
 */
export type Literal = NumberLiteral | StringLiteral | BooleanLiteral;

/**
 * 数字字面量
 */
export interface NumberLiteral {
  type: 'number';
  value: number;
}

/**
 * 字符串字面量
 */
export interface StringLiteral {
  type: 'string';
  value: string;
}

/**
 * 布尔字面量
 */
export interface BooleanLiteral {
  type: 'boolean';
  value: boolean;
}

/**
 * AST 辅助函数
 */

/**
 * 创建数字字面量
 */
export function numberLiteral(value: number): NumberLiteral {
  return { type: 'number', value };
}

/**
 * 创建字符串字面量
 */
export function stringLiteral(value: string): StringLiteral {
  return { type: 'string', value };
}

/**
 * 创建布尔字面量
 */
export function booleanLiteral(value: boolean): BooleanLiteral {
  return { type: 'boolean', value };
}

/**
 * 创建变量引用
 */
export function variableRef(name: string, timeRef?: TimeReference): VariableRef {
  return { type: 'variable_ref', name, timeRef };
}

/**
 * 创建函数调用
 */
export function functionCall(name: string, args: Expression[]): FunctionCall {
  return { type: 'function_call', name, args };
}

/**
 * 创建比较表达式
 */
export function comparison(
  operator: '>' | '<' | '>=' | '<=' | '=' | '!=',
  left: Expression,
  right: Expression
): ComparisonExpression {
  return { type: 'comparison', operator, left, right };
}

/**
 * 创建逻辑表达式
 */
export function logical(
  operator: 'AND' | 'OR',
  left: Expression,
  right: Expression
): LogicalExpression {
  return { type: 'logical', operator, left, right };
}

/**
 * 创建一元表达式
 */
export function unary(operator: 'NOT', operand: Expression): UnaryExpression {
  return { type: 'unary', operator, operand };
}

/**
 * 创建 Between 表达式
 */
export function between(
  variable: Expression,
  low: Expression,
  high: Expression
): BetweenExpression {
  return { type: 'between', variable, low, high };
}

/**
 * 解析规则类型字符串
 */
export function parseRuleType(type: string): RuleType {
  const validTypes: RuleType[] = ['threshold', 'trend', 'correlation', 'pattern', 'composite'];
  const lower = type.toLowerCase();
  if (!validTypes.includes(lower as RuleType)) {
    throw new Error(`无效的规则类型: ${type}. 有效值: ${validTypes.join(', ')}`);
  }
  return lower as RuleType;
}

/**
 * 解析影响类型
 */
export function parseImpactType(impact: string): ImpactType {
  const validTypes: ImpactType[] = ['positive', 'negative', 'neutral'];
  const lower = impact.toLowerCase();
  if (!validTypes.includes(lower as ImpactType)) {
    throw new Error(`无效的影响类型: ${impact}. 有效值: ${validTypes.join(', ')}`);
  }
  return lower as ImpactType;
}

/**
 * 解析时间范围
 */
export function parseTimeHorizon(horizon: string): TimeHorizon {
  const validTypes: TimeHorizon[] = ['short', 'medium', 'long'];
  const lower = horizon.toLowerCase();
  if (!validTypes.includes(lower as TimeHorizon)) {
    throw new Error(`无效的时间范围: ${horizon}. 有效值: ${validTypes.join(', ')}`);
  }
  return lower as TimeHorizon;
}

/**
 * 解析来源类型
 */
export function parseSourceType(source: string): SourceType {
  const validTypes: SourceType[] = ['expert', 'mined', 'learned'];
  const lower = source.toLowerCase();
  if (!validTypes.includes(lower as SourceType)) {
    throw new Error(`无效的来源类型: ${source}. 有效值: ${validTypes.join(', ')}`);
  }
  return lower as SourceType;
}

/**
 * 解析时间引用
 */
export function parseTimeRef(value: string): TimeReference {
  // T-1, T-12 等
  const relativeMatch = value.match(/^T([+-]?\d+)$/);
  if (relativeMatch) {
    return {
      type: 'relative',
      offset: parseInt(relativeMatch[1], 10),
    };
  }

  // T[2024-01] 等
  const absoluteMatch = value.match(/^T\[(.+)\]$/);
  if (absoluteMatch) {
    return {
      type: 'absolute',
      value: absoluteMatch[1],
    };
  }

  throw new Error(`无效的时间引用格式: ${value}`);
}
