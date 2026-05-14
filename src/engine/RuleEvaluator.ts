/**
 * 规则求值引擎 (重构版 - 安全 AST 求值)
 */

import {
  RuleAST,
  Expression,
  LogicalExpression,
  ComparisonExpression,
  UnaryExpression,
  BetweenExpression,
  FunctionCall,
  VariableRef,
  Literal,
  RuleType,
} from '../parser/ast';
import { DataPoint, Rule, RuleEvaluationResult, RuleExecution, Conclusion } from '../types';

export interface VariableContext { [key: string]: any; }
export type FunctionRegistry = { [name: string]: (...args: any[]) => any; };

export class RuleEvaluator {
  private dataContext: Map<string, DataPoint[]> = new Map();
  private functions: FunctionRegistry = {};

  constructor(functions?: FunctionRegistry) {
    if (functions) this.functions = functions;
    this.registerBuiltinFunctions();
  }

  private registerBuiltinFunctions(): void {
    this.functions['TREND_UP'] = (series: any[], n: number) => {
      if (!Array.isArray(series) || series.length < n) return false;
      const recent = series.slice(-n);
      for (let i = 1; i < recent.length; i++) if (Number(recent[i]) <= Number(recent[i - 1])) return false;
      return true;
    };
    this.functions['TREND_DOWN'] = (series: any[], n: number) => {
      if (!Array.isArray(series) || series.length < n) return false;
      const recent = series.slice(-n);
      for (let i = 1; i < recent.length; i++) if (Number(recent[i]) >= Number(recent[i - 1])) return false;
      return true;
    };
    this.functions['AVG'] = (series: any[], n?: number) => {
      if (!Array.isArray(series) || series.length === 0) return 0;
      const data = n ? series.slice(-n) : series;
      return data.reduce((acc, val) => acc + Number(val), 0) / data.length;
    };
    this.functions['SUM'] = (series: any[], n?: number) => {
      if (!Array.isArray(series) || series.length === 0) return 0;
      const data = n ? series.slice(-n) : series;
      return data.reduce((acc, val) => acc + Number(val), 0);
    };
    this.functions['MAX'] = (series: any[], n?: number) => {
      if (!Array.isArray(series) || series.length === 0) return 0;
      const data = n ? series.slice(-n) : series;
      return Math.max(...data.map(Number));
    };
    this.functions['MIN'] = (series: any[], n?: number) => {
      if (!Array.isArray(series) || series.length === 0) return 0;
      const data = n ? series.slice(-n) : series;
      return Math.min(...data.map(Number));
    };
    this.functions['NOW'] = () => Date.now();
    this.functions['MONTH'] = () => new Date().getMonth() + 1;
    this.functions['YEAR'] = () => new Date().getFullYear();
  }

  setDataContext(dataPoints: DataPoint[]): void {
    this.dataContext.clear();
    const grouped = new Map<string, DataPoint[]>();
    dataPoints.forEach(dp => {
      const rawMetric = dp.normalized.metric || 'unknown';
      const metric = rawMetric.replace(/[^a-zA-Z0-9_]/g, '_');
      if (!grouped.has(metric)) grouped.set(metric, []);
      grouped.get(metric)!.push(dp);
    });
    grouped.forEach((points, _) => {
      points.sort((a, b) => b.timestamp - a.timestamp);
    });
    this.dataContext = grouped;
  }

  evaluate(rule: Rule): RuleExecution {
    const variables: Record<string, any> = {};
    let triggered = false;
    let conditionResult = false;
    try {
      const context = this.buildVariableContext();
      conditionResult = this.evaluateExpression(rule.condition.expression, context, variables);
      triggered = conditionResult;
    } catch (error: any) {
      console.error(`规则 ${rule.id} 评估失败:`, error.message);
    }
    return { ruleId: rule.id, ruleName: rule.name, triggered, conditionResult, variables };
  }

  evaluateBatch(rules: Rule[]): RuleEvaluationResult {
    const executions: RuleExecution[] = [];
    const conclusions: Conclusion[] = [];
    for (const rule of rules) {
      const execution = this.evaluate(rule);
      executions.push(execution);
      if (execution.triggered) {
        conclusions.push({
          ruleId: rule.id, conclusion: rule.inference.conclusion,
          confidence: rule.inference.confidence, impact: rule.inference.impact,
          timeHorizon: rule.inference.timeHorizon,
        });
      }
    }
    const overallConfidence = conclusions.length > 0 ? conclusions.reduce((sum, c) => sum + c.confidence, 0) / conclusions.length : 0;
    return { triggeredRules: executions.filter(e => e.triggered), conclusions, overallConfidence };
  }

  private evaluateExpression(expr: any, ctx: VariableContext, vars: Record<string, any>): any {
    if (!expr || !expr.type) return false;
    switch (expr.type) {
      case 'logical': return this.evalLogical(expr as LogicalExpression, ctx, vars);
      case 'comparison': return this.evalComparison(expr as ComparisonExpression, ctx, vars);
      case 'unary': return this.evalUnary(expr as UnaryExpression, ctx, vars);
      case 'between': return this.evalBetween(expr as BetweenExpression, ctx, vars);
      case 'function_call': return this.evalFunctionCall(expr as FunctionCall, ctx, vars);
      case 'variable_ref': return this.evalVariableRef(expr as VariableRef, ctx, vars);
      case 'number': case 'string': case 'boolean': return (expr as Literal).value;
      default: throw new Error(`未知的表达式类型：${expr.type}`);
    }
  }

  private evalLogical(expr: LogicalExpression, ctx: VariableContext, vars: Record<string, any>): boolean {
    const left = this.evaluateExpression(expr.left, ctx, vars);
    if (expr.operator === 'AND') return Boolean(left) && Boolean(this.evaluateExpression(expr.right, ctx, vars));
    if (expr.operator === 'OR') return Boolean(left) || Boolean(this.evaluateExpression(expr.right, ctx, vars));
    return false;
  }

  private evalComparison(expr: ComparisonExpression, ctx: VariableContext, vars: Record<string, any>): boolean {
    const left = this.evaluateExpression(expr.left, ctx, vars);
    const right = this.evaluateExpression(expr.right, ctx, vars);
    const l = Number(left), r = Number(right);
    switch (expr.operator) {
      case '>': return l > r; case '<': return l < r;
      case '>=': return l >= r; case '<=': return l <= r;
      case '=': return l === r; case '!=': return l !== r;
      default: return false;
    }
  }

  private evalUnary(expr: UnaryExpression, ctx: VariableContext, vars: Record<string, any>): boolean {
    const val = this.evaluateExpression(expr.operand, ctx, vars);
    if (expr.operator === 'NOT') return !val;
    return false;
  }

  private evalBetween(expr: BetweenExpression, ctx: VariableContext, vars: Record<string, any>): boolean {
    const val = Number(this.evaluateExpression(expr.variable, ctx, vars));
    const low = Number(this.evaluateExpression(expr.low, ctx, vars));
    const high = Number(this.evaluateExpression(expr.high, ctx, vars));
    return val >= low && val <= high;
  }

  private evalFunctionCall(expr: FunctionCall, ctx: VariableContext, vars: Record<string, any>): any {
    const func = this.functions[expr.name];
    if (!func) { console.warn(`未定义的函数：${expr.name}`); return 0; }
    const args = expr.args.map(arg => this.evaluateExpression(arg, ctx, vars));
    return func(...args);
  }

  private evalVariableRef(expr: VariableRef, ctx: VariableContext, vars: Record<string, any>): any {
    const name = (expr.name || '').replace(/[^a-zA-Z0-9_]/g, '_');
    if (expr.timeRef && expr.timeRef.type === 'relative') {
      const offset = expr.timeRef.offset || 0;
      const series = ctx[expr.name] || [];
      if (Array.isArray(series) && series.length > Math.abs(offset)) {
        const index = offset < 0 ? Math.abs(offset) : 0;
        if (series[index]) return series[index].normalized.value;
      }
    }
    if (ctx[expr.name]) {
      if (Array.isArray(ctx[expr.name])) {
        const dp = ctx[expr.name][0];
        return dp ? dp.normalized.value : 0;
      }
      return ctx[expr.name];
    }
    return 0;
  }

  private buildVariableContext(): VariableContext {
    const context: VariableContext = {};
    this.dataContext.forEach((points, metric) => {
      context[metric] = points;
      if (points.length > 0) {
        const latest = points[0];
        context[`${metric}_value`] = latest.normalized.value;
        if (latest.normalized.change) {
          context[`${metric}_change`] = latest.normalized.change.absolute;
          context[`${metric}_change_pct`] = latest.normalized.change.percentage;
        }
        if (latest.normalized.change !== undefined) {
           context[`${metric}_change_value`] = latest.normalized.change?.absolute;
        }
      }
    });
    return context;
  }
}

export const ruleEvaluator = new RuleEvaluator();
