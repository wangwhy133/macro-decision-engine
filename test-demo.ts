/**
 * 宏观决策支持引擎 - 演示脚本
 * 测试数据可信度系统和规则解析器
 */

import { DataCredibilityService } from './src/services/DataCredibilityService';
import { RuleEvaluator } from './src/engine/RuleEvaluator';
import { parseRule, parseRules, tokenize } from './src/parser/parser';
import { TokenType } from './src/parser/tokens';

async function runDemo() {
  console.log('='.repeat(60));
  console.log('宏观决策支持引擎 v1.0 - 演示');
  console.log('='.repeat(60));
  console.log('');

  // ========== 1. 测试数据可信度系统 ==========
  console.log('【测试 1】数据可信度系统');
  console.log('-'.repeat(40));

  const dataService = new DataCredibilityService();

  // 模拟能繁母猪存栏数据
  const rawData = {
    source: 'eastmoney',
    sourceType: 'financial' as const,
    timestamp: Date.now(),
    category: 'pig_cycle',
    data: {
      metric: '能繁母猪存栏量',
      value: 4500,
      unit: '万头',
      change: {
        absolute: -100,
        percentage: -0.022,
        period: '月环比'
      }
    },
    tags: ['猪周期', '供给端']
  };

  const dataPoint = await dataService.ingest(rawData);
  console.log('数据点 ID:', dataPoint.id);
  console.log('来源:', dataPoint.source);
  console.log('指标:', dataPoint.normalized.metric);
  console.log('数值:', dataPoint.normalized.value, dataPoint.normalized.unit);
  console.log('变化:', dataPoint.normalized.change?.percentage * 100, '%');
  console.log('可信度评分:', dataPoint.credibility.score.toFixed(3));
  console.log('  - 来源可靠性:', dataPoint.credibility.sourceReliability.toFixed(3));
  console.log('  - 时效性:', dataPoint.credibility.timeliness.toFixed(3));
  console.log('  - 一致性:', dataPoint.credibility.crossValidation.consistencyScore.toFixed(3));
  console.log('  - 异常标记:', dataPoint.credibility.anomalyFlags.length > 0 ? dataPoint.credibility.anomalyFlags.join(', ') : '无');
  console.log('');

  // ========== 2. 测试规则解析器 ==========
  console.log('【测试 2】规则 DSL 解析器');
  console.log('-'.repeat(40));

  const ruleText = `
RULE test_rule: "测试规则"
DESCRIPTION "用于测试的规则"
TYPE trend
CATEGORY pig_cycle
PRIORITY 8

CONDITION
  pig_inventory.change < -0.10 AND
  pig_grain_ratio.value < 5.5

THEN
  CONCLUSION "测试结论"
  CONFIDENCE 0.75
  IMPACT positive
  HORIZON medium

METADATA
  SOURCE expert
  VALIDATED true
  SUCCESS_RATE 0.72
  VALIDATION_COUNT 15
END
`;

  try {
    const rule = parseRule(ruleText);
    console.log('规则 ID:', rule.id);
    console.log('规则名称:', rule.name);
    console.log('描述:', rule.description);
    console.log('类型:', rule.ruleType);
    console.log('类别:', rule.category);
    console.log('优先级:', rule.priority);
    console.log('结论:', rule.inference.conclusion);
    console.log('置信度:', rule.inference.confidence);
    console.log('影响:', rule.inference.impact);
    console.log('时间范围:', rule.inference.horizon);
    console.log('来源:', rule.metadata.source);
    console.log('已验证:', rule.metadata.validated);
    console.log('成功率:', rule.metadata.successRate);
    console.log('');
  } catch (error) {
    console.error('规则解析失败:', error);
  }

  // ========== 3. 测试 pig_cycle 规则文件 ==========
  console.log('【测试 3】解析 pig_cycle.rules 文件');
  console.log('-'.repeat(40));

  const fs = require('fs');
  const path = require('path');
  
  try {
    const rulesPath = path.join(__dirname, 'rules/pig_cycle.rules');
    const rulesContent = fs.readFileSync(rulesPath, 'utf-8');
    const rules = parseRules(rulesContent);
    
    console.log(`成功解析 ${rules.length} 条规则:`);
    rules.forEach((rule, i) => {
      console.log(`  ${i + 1}. ${rule.name} (${rule.ruleType})`);
      console.log(`     优先级：${rule.priority}`);
      console.log(`     置信度：${rule.inference.confidence}`);
      console.log(`     结论：${rule.inference.conclusion.substring(0, 40)}...`);
    });
    console.log('');
  } catch (error) {
    console.error('规则文件解析失败:', error);
  }

  // ========== 4. 测试规则求值 ==========
  console.log('【测试 4】规则求值引擎');
  console.log('-'.repeat(40));

  const evaluator = new RuleEvaluator();
  
  // 准备测试数据
  const testData = [
    {
      id: 'test-1',
      source: 'test',
      sourceType: 'financial' as const,
      timestamp: Date.now(),
      receivedAt: Date.now(),
      category: 'pig_cycle',
      tags: [],
      raw: {},
      credibility: { score: 0.8, sourceReliability: 0.85, timeliness: 0.9, crossValidation: { verified: true, conflictingSources: [], consistencyScore: 0.95 }, anomalyFlags: [] },
      normalized: {
        metric: 'pig_inventory',
        value: 4500,
        unit: '万头',
        change: {
          absolute: -100,
          percentage: -0.05,
          period: '月环比'
        }
      }
    } as any
  ];

  evaluator.setDataContext(testData);
  
  // 创建简单规则进行测试
  const testRules = [
    {
      id: 'test_1',
      name: '测试规则 1',
      condition: 'pig_inventory.change < 0',
      inference: {
        conclusion: '测试结论 1',
        confidence: 0.7,
        impact: 'positive' as const,
        timeHorizon: 'short' as const
      }
    } as any
  ];

  const result = evaluator.evaluateBatch(testRules);
  console.log('触发规则数:', result.triggeredRules.length);
  console.log('结论数:', result.conclusions.length);
  console.log('整体置信度:', result.overallConfidence.toFixed(3));
  
  if (result.triggeredRules.length > 0) {
    console.log('触发的规则:');
    result.triggeredRules.forEach(rule => {
      console.log(`  - ${rule.ruleName}`);
    });
  }
  console.log('');

  // ========== 完成 ==========
  console.log('='.repeat(60));
  console.log('演示完成');
  console.log('='.repeat(60));
}

// 运行演示
runDemo().catch(console.error);
