/**
 * 回测引擎
 * 功能：在历史数据上重放规则，统计胜率、盈亏比和最大回撤
 */

import { Rule } from '../parser/parser'; // 假设 Rule 类型已导出
import { DataPoint } from '../types';
import { RuleEvaluator } from './RuleEvaluator';

export interface BacktestResult {
  ruleId: string;
  ruleName: string;
  totalSignals: number;      // 总信号数
  winCount: number;           // 盈利次数
  lossCount: number;          // 亏损次数
  winRate: number;            // 胜率
  avgProfit: number;          // 平均盈利幅度
  avgLoss: number;            // 平均亏损幅度
  profitLossRatio: number;    // 盈亏比
  maxDrawdown: number;        // 最大回撤 (模拟)
  totalReturn: number;        // 总回报 (模拟累加)
  signals: BacktestSignal[];  // 详细信号记录
}

export interface BacktestSignal {
  timestamp: number;
  triggered: boolean;
  prediction: string;         // 规则结论
  actualChange?: number;      // 实际后续变化 (用于计算盈亏)
  isWin?: boolean;            // 是否盈利
}

/**
 * 回测配置
 */
export interface BacktestConfig {
  lookforwardPeriods: number; // 向前看多少期来验证结果 (例如：触发后看 3 期)
  threshold: number;          // 盈利/亏损阈值 (例如：变化超过 1% 算赢)
}

const DEFAULT_CONFIG: BacktestConfig = {
  lookforwardPeriods: 3,
  threshold: 0.01, // 1%
};

export class Backtester {
  private evaluator: RuleEvaluator;
  private config: BacktestConfig;

  constructor(config?: Partial<BacktestConfig>) {
    this.evaluator = new RuleEvaluator();
    this.config = { ...DEFAULT_CONFIG, ...config };
  }

  /**
   * 对单条规则进行回测
   * @param rule 规则
   * @param dataPoints 历史数据 (按时间倒序排列)
   */
  runBacktest(rule: Rule, dataPoints: DataPoint[]): BacktestResult {
    const signals: BacktestSignal[] = [];
    let winCount = 0;
    let lossCount = 0;
    let totalProfit = 0;
    let totalLoss = 0;
    let currentCapital = 10000; // 初始资金
    let maxCapital = currentCapital;
    let minCapital = currentCapital;

    // 数据必须是时间倒序 (最新在前)，但回测需要从旧到新，所以需要反转
    // 注意：dataPoints 传入时通常是最新在前，这里我们需要反转它来模拟时间流逝
    const reversedData = [...dataPoints].reverse(); 

    for (let i = 0; i < reversedData.length - this.config.lookforwardPeriods; i++) {
      // 1. 构建当前时刻的数据快照 (只包含 i 之前的数据，防止未来函数)
      // 注意：为了模拟真实场景，我们只能用“当时”已有的数据
      // 这里简化处理：假设规则只依赖当前值，不依赖未来
      const currentSnapshot = [reversedData[i]]; 
      
      // 2. 设置上下文并评估规则
      this.evaluator.setDataContext(currentSnapshot);
      const result = this.evaluator.evaluate(rule);

      const signal: BacktestSignal = {
        timestamp: reversedData[i].timestamp,
        triggered: result.triggered,
        prediction: result.triggered ? rule.inference.conclusion : 'No Signal',
      };

      // 3. 如果触发信号，计算 N 期后的结果
      if (result.triggered) {
        const futureValue = reversedData[i + this.config.lookforwardPeriods].normalized.value as number;
        const currentValue = reversedData[i].normalized.value as number;
        const actualChange = (futureValue - currentValue) / currentValue;
        
        signal.actualChange = actualChange;

        // 判断盈亏 (简化逻辑：假设规则结论是"positive"则希望上涨)
        const isPositive = rule.inference.impact === 'positive';
        const isWin = isPositive ? (actualChange > this.config.threshold) : (actualChange < -this.config.threshold);
        
        signal.isWin = isWin;

        if (isWin) {
          winCount++;
          totalProfit += Math.abs(actualChange);
          currentCapital *= (1 + Math.abs(actualChange));
        } else {
          lossCount++;
          totalLoss += Math.abs(actualChange);
          currentCapital *= (1 - Math.abs(actualChange));
        }

        if (currentCapital > maxCapital) maxCapital = currentCapital;
        if (currentCapital < minCapital) minCapital = currentCapital;
      }

      signals.push(signal);
    }

    const totalSignals = signals.filter(s => s.triggered).length;
    const winRate = totalSignals > 0 ? winCount / totalSignals : 0;
    const avgProfit = winCount > 0 ? totalProfit / winCount : 0;
    const avgLoss = lossCount > 0 ? totalLoss / lossCount : 0;
    const profitLossRatio = avgLoss > 0 ? avgProfit / avgLoss : 0;
    const maxDrawdown = maxCapital > 0 ? (maxCapital - minCapital) / maxCapital : 0;
    const totalReturn = (currentCapital - 10000) / 10000;

    return {
      ruleId: rule.id,
      ruleName: rule.name,
      totalSignals,
      winCount,
      lossCount,
      winRate,
      avgProfit,
      avgLoss,
      profitLossRatio,
      maxDrawdown,
      totalReturn,
      signals,
    };
  }

  /**
   * 批量回测
   */
  runBatchBacktest(rules: Rule[], dataPoints: DataPoint[]): BacktestResult[] {
    return rules.map(rule => this.runBacktest(rule, dataPoints));
  }
}
