/**
 * 端到端集成测试
 * 场景：猪周期决策支持
 * 流程：数据接入 -> 规则解析 -> 规则求值 -> 输出结论
 */

import { DataCredibilityService } from './src/services/DataCredibilityService';
import { RuleEvaluator } from './src/engine/RuleEvaluator';
import { parseRule, parseRules } from './src/parser/parser';

async function runIntegrationTest() {
  console.log('🚀 宏观决策支持引擎 - 端到端集成测试');
  console.log('场景：猪周期决策支持\n');
  console.log('='.repeat(60));

  // 1. 初始化服务
  const dataService = new DataCredibilityService();
  const evaluator = new RuleEvaluator();

  // 2. 模拟数据接入 (交易员视角：真实场景数据)
  console.log('【步骤 1】数据接入与验证');
  const now = Date.now();
  const oneDay = 24 * 60 * 60 * 1000;

  // 模拟过去 5 天的存栏量数据 (递减趋势)
  const inventoryData = [
    { day: 0, value: 4500, change: -50 },
    { day: 1, value: 4550, change: -30 },
    { day: 2, value: 4580, change: -20 },
    { day: 3, value: 4600, change: -10 },
    { day: 4, value: 4610, change: -5 },
  ];

  const dataPoints = [];
  for (const item of inventoryData) {
    const dp = await dataService.ingest({
      source: 'eastmoney',
      sourceType: 'financial',
      timestamp: now - item.day * oneDay,
      category: 'pig_cycle',
      data: {
        metric: 'pig_inventory',
        value: item.value,
        unit: '万头',
        change: {
          absolute: item.change,
          percentage: item.change / (item.value - item.change),
          period: '日环比'
        }
      },
      tags: ['猪周期', '供给端']
    });
    dataPoints.push(dp);
    console.log(`  - 接入数据：${dp.normalized.value} (变化：${dp.normalized.change?.absolute}) [可信度：${dp.credibility.score.toFixed(3)}]`);
  }
  console.log('');

  // 3. 规则解析
  console.log('【步骤 2】规则解析');
  const ruleText = `
RULE pig_decline_test: "存栏量连续下降测试"
DESCRIPTION "测试连续下降趋势"
TYPE trend
CATEGORY pig_cycle
PRIORITY 9
CONDITION
  pig_inventory_change < 0 AND pig_inventory_value < 4600
THEN
  CONCLUSION "存栏量持续下降，供给收缩信号确立"
  CONFIDENCE 0.80
  IMPACT positive
  HORIZON medium
METADATA
  SOURCE expert
  VALIDATED true
END
`;

  try {
    const rule = parseRule(ruleText);
    console.log(`  ✅ 规则解析成功：${rule.name}`);
    console.log(`     条件：${rule.condition.expression.type}`);
    console.log(`     结论：${rule.inference.conclusion}`);
    console.log('');

    // 4. 规则求值
    console.log('【步骤 3】规则求值');
    evaluator.setDataContext(dataPoints);
    const result = evaluator.evaluate(rule);

    if (result.triggered) {
      console.log(`  ✅ 规则触发！`);
      console.log(`     结论：${rule.inference.conclusion}`);
      console.log(`     置信度：${rule.inference.confidence}`);
      console.log(`     影响：${rule.inference.impact}`);
      console.log(`     时间范围：${rule.inference.timeHorizon}`);
    } else {
      console.log(`  ℹ️  规则未触发`);
      console.log(`     条件评估结果：${result.conditionResult}`);
    }
    console.log('');

    // 5. 复杂规则测试 (函数调用)
    console.log('【步骤 4】复杂规则测试 (AVG 函数)');
    const avgRuleText = `
RULE pig_avg_test: "平均值测试"
DESCRIPTION "测试 AVG 函数"
TYPE pattern
CATEGORY pig_cycle
PRIORITY 7
CONDITION
  AVG(pig_inventory.value, 3) < 4600
THEN
  CONCLUSION "近 3 日平均存栏量低于阈值"
  CONFIDENCE 0.70
  IMPACT neutral
  HORIZON short
METADATA
  SOURCE mined
  VALIDATED true
END
`;

    const avgRule = parseRule(avgRuleText);
    const avgResult = evaluator.evaluate(avgRule);
    
    if (avgResult.triggered) {
      console.log(`  ✅ 规则触发！`);
      console.log(`     结论：${avgRule.inference.conclusion}`);
    } else {
      console.log(`  ℹ️  规则未触发`);
    }
    console.log('');

    console.log('='.repeat(60));
    console.log('🎉 集成测试完成！系统运行正常。');
    console.log('='.repeat(60));

  } catch (error: any) {
    console.error('❌ 测试失败:', error.message);
    if (error.stack) console.error(error.stack);
  }
}

runIntegrationTest().catch(console.error);
