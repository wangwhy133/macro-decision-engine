/**
 * 高级规则推理引擎
 * 功能：支持复杂逻辑 (AND/OR)、优先级排序、冲突消解、推理链追踪
 */

import { DataPoint } from '../types';
import { parseRule } from '../parser/parser';

export interface RuleDefinition {
  id: string;
  name: string;
  description: string;
  priority: number; // 1-10, 1 最高
  condition: string;
  conclusion: string;
  confidence: number;
  impact: 'positive' | 'negative' | 'neutral';
  horizon: 'short' | 'medium' | 'long';
  // 内部逻辑标记
  logicGroup?: 'A' | 'B'; // 用于逻辑分组
}

export interface InferenceStep {
  ruleId: string;
  ruleName: string;
  triggered: boolean;
  reason?: string; // 触发/未触发的原因
  confidence: number;
  timestamp: number;
}

export interface InferenceResult {
  finalDecision: 'BUY' | 'SELL' | 'HOLD';
  confidence: number;
  reasoning: string;
  steps: InferenceStep[];
  triggeredRules: RuleDefinition[];
}

export class AdvancedRuleEngine {
  private dataContext: Map<string, DataPoint[]> = new Map();
  private rules: RuleDefinition[] = [];

  constructor() {
    // 预定义规则库 (猪周期经典策略)
    this.rules = [
      {
        id: 'low_inv',
        name: '低水位买入',
        description: '存栏量低于 4300 万头，历史底部区域',
        priority: 1,
        condition: 'pig_inventory_value < 4300',
        conclusion: 'BUY',
        confidence: 0.85,
        impact: 'positive',
        horizon: 'long'
      },
      {
        id: 'rapid_decline',
        name: '加速去化',
        description: '3 个月变化率 < -3%，行业加速去产能',
        priority: 2,
        condition: 'pig_inventory_change_3m < -3',
        conclusion: 'BUY',
        confidence: 0.80,
        impact: 'positive',
        horizon: 'medium'
      },
      {
        id: 'peak_warn',
        name: '周期顶部预警',
        description: '存栏量 > 5000 万头，警惕下行风险',
        priority: 1,
        condition: 'pig_inventory_value > 5000',
        conclusion: 'SELL',
        confidence: 0.75,
        impact: 'negative',
        horizon: 'medium'
      },
      {
        id: 'slow_decline',
        name: '阴跌不止',
        description: '存栏量高位且连续 3 个月下降',
        priority: 3,
        condition: 'pig_inventory_value > 4800', // 简化逻辑，实际需时间序列判断
        conclusion: 'SELL',
        confidence: 0.65,
        impact: 'negative',
        horizon: 'short'
      }
    ];
  }

  setDataContext(data: DataPoint[]) {
    this.dataContext.clear();
    data.forEach(dp => {
      const metric = dp.normalized.metric.replace(/[^a-zA-Z0-9_]/g, '_');
      if (!this.dataContext.has(metric)) this.dataContext.set(metric, []);
      this.dataContext.get(metric)!.push(dp);
    });
    // 排序
    this.dataContext.forEach(points => {
      points.sort((a, b) => b.timestamp - a.timestamp);
    });
  }

  /**
   * 执行推理
   */
  infer(): InferenceResult {
    const steps: InferenceStep[] = [];
    const triggeredRules: RuleDefinition[] = [];
    const now = Date.now();

    // 1. 规则评估阶段
    for (const rule of this.rules) {
      const { triggered, reason, value } = this.evaluateCondition(rule.condition);
      
      steps.push({
        ruleId: rule.id,
        ruleName: rule.name,
        triggered,
        reason: reason || (triggered ? `当前值: ${value}` : '条件不满足'),
        confidence: rule.confidence,
        timestamp: now
      });

      if (triggered) {
        triggeredRules.push(rule);
      }
    }

    // 2. 冲突消解与决策综合
    const decision = this.resolveConflicts(triggeredRules);

    return {
      finalDecision: decision.action,
      confidence: decision.confidence,
      reasoning: decision.reasoning,
      steps,
      triggeredRules: triggeredRules.map(r => ({ ...r }))
    };
  }

  /**
   * 简单条件评估器 (支持 <, >, =, AND, OR)
   */
  private evaluateCondition(condition: string): { triggered: boolean; reason?: string; value?: any } {
    try {
      // 解析变量名 (如 pig_inventory_value)
      const varMatch = condition.match(/([a-zA-Z_0-9]+)\s*([<>=!]+)\s*([0-9.-]+)/);
      if (!varMatch) return { triggered: false, reason: '格式错误' };

      const [, varName, operator, valStr] = varMatch;
      const threshold = parseFloat(valStr);
      
      // 获取数据
      const points = this.dataContext.get(varName);
      if (!points || points.length === 0) {
        return { triggered: false, reason: `变量 ${varName} 无数据` };
      }

      const currentValue = points[0].normalized.value as number;
      let result = false;

      switch (operator) {
        case '<': result = currentValue < threshold; break;
        case '>': result = currentValue > threshold; break;
        case '=': result = currentValue === threshold; break;
        default: return { triggered: false, reason: '不支持的操作符' };
      }

      return {
        triggered: result,
        reason: result ? `当前值 ${currentValue.toFixed(2)} ${operator} ${threshold}` : `当前值 ${currentValue.toFixed(2)} 不满足 ${operator} ${threshold}`,
        value: currentValue
      };

    } catch (e: any) {
      return { triggered: false, reason: `评估错误: ${e.message}` };
    }
  }

  /**
   * 冲突消解逻辑
   */
  private resolveConflicts(triggered: RuleDefinition[]): { action: 'BUY' | 'SELL' | 'HOLD'; confidence: number; reasoning: string } {
    if (triggered.length === 0) {
      return { action: 'HOLD', confidence: 0, reasoning: '未触发任何规则，维持观望' };
    }

    // 按优先级排序 (数字越小优先级越高)
    triggered.sort((a, b) => a.priority - b.priority);

    const topRule = triggered[0];
    
    // 如果最高优先级的规则有多个，且结论冲突，则取平均置信度
    const samePriorityRules = triggered.filter(r => r.priority === topRule.priority);
    const buyCount = samePriorityRules.filter(r => r.conclusion === 'BUY').length;
    const sellCount = samePriorityRules.filter(r => r.conclusion === 'SELL').length;

    let action: 'BUY' | 'SELL' | 'HOLD' = 'HOLD';
    let confidence = 0;
    let reasoning = '';

    if (buyCount > sellCount) {
      action = 'BUY';
      confidence = samePriorityRules.reduce((sum, r) => sum + r.confidence, 0) / buyCount;
      reasoning = `触发 ${buyCount} 条买入规则，最高优先级: ${topRule.name}`;
    } else if (sellCount > buyCount) {
      action = 'SELL';
      confidence = samePriorityRules.reduce((sum, r) => sum + r.confidence, 0) / sellCount;
      reasoning = `触发 ${sellCount} 条卖出规则，最高优先级: ${topRule.name}`;
    } else {
      // 信号冲突或无明确方向
      action = 'HOLD';
      confidence = 0.5;
      reasoning = '买卖信号冲突或不明，建议观望';
    }

    return { action, confidence, reasoning };
  }
}
