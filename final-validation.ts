/**
 * 最终验证 - 完整规则解析测试
 */

import { parseRule } from './src/parser/parser';
import { DataCredibilityService } from './src/services/DataCredibilityService';

async function finalValidation() {
  console.log('🚀 宏观决策支持引擎 - 最终验证\n');
  
  let passed = 0;
  let failed = 0;

  // 测试 1: 简单阈值规则 (含负数)
  console.log('【测试 1】简单阈值规则 (含负数)');
  try {
    const rule1 = parseRule(`
RULE test_neg: "负数测试"
DESCRIPTION "测试负数字面量"
TYPE threshold
CATEGORY pig_cycle
PRIORITY 8
CONDITION
  pig_inventory.change < -0.10
THEN
  CONCLUSION "负数测试通过"
  CONFIDENCE 0.75
  IMPACT positive
  HORIZON medium
METADATA
  SOURCE expert
  VALIDATED true
END
`);
    console.log(`✅ 规则解析成功：${rule1.name}`);
    console.log(`   条件：${rule1.condition.expression}`);
    passed++;
  } catch (e: any) {
    console.log(`❌ 解析失败：${e.message}`);
    failed++;
  }

  // 测试 2: 复合逻辑规则
  console.log('\n【测试 2】复合逻辑规则');
  try {
    const rule2 = parseRule(`
RULE test_and: "AND 逻辑测试"
DESCRIPTION "测试 AND 逻辑"
TYPE composite
CATEGORY pig_cycle
PRIORITY 7
CONDITION
  pig_inventory.change < 0 AND pig_grain_ratio.value < 5.5
THEN
  CONCLUSION "AND 逻辑测试通过"
  CONFIDENCE 0.70
  IMPACT negative
  HORIZON short
METADATA
  SOURCE expert
  VALIDATED true
END
`);
    console.log(`✅ 规则解析成功：${rule2.name}`);
    passed++;
  } catch (e: any) {
    console.log(`❌ 解析失败：${e.message}`);
    failed++;
  }

  // 测试 3: 函数调用规则
  console.log('\n【测试 3】函数调用规则');
  try {
    const rule3 = parseRule(`
RULE test_func: "函数测试"
DESCRIPTION "测试 AVG 函数"
TYPE trend
CATEGORY pig_cycle
PRIORITY 6
CONDITION
  AVG(pig_inventory.value, 3) < 4000
THEN
  CONCLUSION "函数测试通过"
  CONFIDENCE 0.65
  IMPACT neutral
  HORIZON long
METADATA
  SOURCE mined
  VALIDATED false
END
`);
    console.log(`✅ 规则解析成功：${rule3.name}`);
    passed++;
  } catch (e: any) {
    console.log(`❌ 解析失败：${e.message}`);
    failed++;
  }

  // 测试 4: 数据验证
  console.log('\n【测试 4】数据验证系统');
  const service = new DataCredibilityService();
  
  // 正常数据
  const data = await service.ingest({
    source: 'eastmoney',
    sourceType: 'financial',
    timestamp: Date.now(),
    category: 'pig_cycle',
    data: { metric: '存栏量', value: 4500, change: { percentage: -0.05 } },
    tags: []
  });
  console.log(`✅ 数据接入：可信度 ${data.credibility.score.toFixed(3)}`);
  passed++;

  // 负数拦截
  try {
    await service.ingest({
      source: 'test',
      sourceType: 'financial',
      timestamp: Date.now(),
      category: 'pig_cycle',
      data: { metric: '存栏量', value: -100 },
      tags: []
    });
    console.log('❌ 负数数据未拦截');
    failed++;
  } catch (e: any) {
    console.log(`✅ 负数数据已拦截`);
    passed++;
  }

  // 总结
  console.log('\n' + '='.repeat(60));
  console.log(`验证完成：通过 ${passed} 项，失败 ${failed} 项`);
  if (failed === 0) {
    console.log('🎉 所有测试通过！系统已准备好进行实战。');
  } else {
    console.log('⚠️  存在失败项，请检查。');
  }
  console.log('='.repeat(60));
}

finalValidation().catch(console.error);
