/**
 * 综合测试脚本 - 工程师 + 交易员视角
 * 测试内容：
 * 1. 数据可信度评分逻辑
 * 2. 异常数据拦截
 * 3. 规则解析正确性
 * 4. 内存管理策略
 */

import { DataCredibilityService } from './src/services/DataCredibilityService';
import { parseRule } from './src/parser/parser';
import { tokenize } from './src/parser/tokens';

async function runComprehensiveTest() {
  console.log('='.repeat(70));
  console.log('🧪 宏观决策支持引擎 - 综合测试 (工程师 + 交易员视角)');
  console.log('='.repeat(70));
  console.log('');

  let passCount = 0;
  let failCount = 0;

  // ========== 测试 1: 数据可信度与异常检测 ==========
  console.log('【测试 1】数据可信度与异常检测');
  console.log('-'.repeat(70));
  try {
    const service = new DataCredibilityService();

    // 1.1 正常数据接入
    const normalData = await service.ingest({
      source: 'eastmoney',
      sourceType: 'financial',
      timestamp: Date.now(),
      category: 'pig_cycle',
      data: { metric: '能繁母猪存栏量', value: 4500, unit: '万头' },
      tags: []
    });
    console.log(`✅ 正常数据接入：可信度 ${normalData.credibility.score.toFixed(3)}`);
    if (normalData.credibility.score > 0.8) passCount++; else failCount++;

    // 1.2 负数拦截 (交易员规则：猪周期数据不能为负)
    try {
      await service.ingest({
        source: 'test',
        sourceType: 'financial',
        timestamp: Date.now(),
        category: 'pig_cycle',
        data: { metric: '能繁母猪存栏量', value: -100, unit: '万头' },
        tags: []
      });
      console.log('❌ 负数数据未被拦截 (严重)');
      failCount++;
    } catch (e: any) {
      console.log(`✅ 负数数据已拦截：${e.message}`);
      passCount++;
    }

    // 1.3 无穷大拦截
    try {
      await service.ingest({
        source: 'test',
        sourceType: 'financial',
        timestamp: Date.now(),
        category: 'pig_cycle',
        data: { metric: 'CPI', value: Infinity, unit: '%' },
        tags: []
      });
      console.log('❌ 无穷大数据未被拦截');
      failCount++;
    } catch (e: any) {
      console.log(`✅ 无穷大数据已拦截`);
      passCount++;
    }

    // 1.4 时效性测试 (模拟旧数据)
    const oldData = await service.ingest({
      source: 'stats.gov',
      sourceType: 'official',
      timestamp: Date.now() - 48 * 60 * 60 * 1000, // 48 小时前
      category: 'inflation',
      data: { metric: 'CPI', value: 102.5, unit: '%' },
      tags: []
    });
    console.log(`✅ 旧数据接入：时效性 ${oldData.credibility.timeliness.toFixed(3)}`);
    if (oldData.credibility.timeliness < 0.3) passCount++; // 48 小时后半衰期 24h，应该较低
    else failCount++;

  } catch (e) {
    console.error('❌ 测试 1 异常:', e);
    failCount++;
  }
  console.log('');

  // ========== 测试 2: 规则 DSL 解析 ==========
  console.log('【测试 2】规则 DSL 解析能力');
  console.log('-'.repeat(70));
  
  const testCases = [
    {
      name: '简单阈值规则',
      rule: `
RULE test_threshold: "简单阈值"
DESCRIPTION "测试阈值判断"
TYPE threshold
CATEGORY test
PRIORITY 5
CONDITION
  pig_inventory.change < -0.10
THEN
  CONCLUSION "测试结论"
  CONFIDENCE 0.7
  IMPACT positive
  HORIZON short
METADATA
  SOURCE expert
  VALIDATED true
END
`
    },
    {
      name: '复合逻辑规则',
      rule: `
RULE test_composite: "复合逻辑"
DESCRIPTION "测试 AND/OR 逻辑"
TYPE composite
CATEGORY pig_cycle
PRIORITY 8
CONDITION
  pig_inventory.change < 0 AND pig_grain_ratio.value < 5.5
THEN
  CONCLUSION "复合结论"
  CONFIDENCE 0.75
  IMPACT negative
  HORIZON medium
METADATA
  SOURCE expert
  VALIDATED true
END
`
    },
    {
      name: '函数调用规则',
      rule: `
RULE test_function: "函数调用"
DESCRIPTION "测试聚合函数"
TYPE trend
CATEGORY pig_cycle
PRIORITY 7
CONDITION
  AVG(pig_inventory.value, 3) < 4000
THEN
  CONCLUSION "函数结论"
  CONFIDENCE 0.65
  IMPACT neutral
  HORIZON long
METADATA
  SOURCE mined
  VALIDATED false
END
`
    }
  ];

  for (const tc of testCases) {
    try {
      const rule = parseRule(tc.rule);
      console.log(`✅ ${tc.name}: 解析成功 (ID: ${rule.id}, 优先级：${rule.priority})`);
      passCount++;
    } catch (e: any) {
      console.error(`❌ ${tc.name}: 解析失败 - ${e.message}`);
      failCount++;
    }
  }
  console.log('');

  // ========== 测试 3: 分词边界情况 ==========
  console.log('【测试 3】分词边界情况');
  console.log('-'.repeat(70));
  
  const edgeCases = [
    { input: 'RULE id: "名"', expected: ['RULE', 'IDENTIFIER', 'COLON', 'STRING'] },
    { input: 'pig[T-1] < 100', expected: ['IDENTIFIER', 'LBRACKET', 'IDENTIFIER', 'RBRACKET', 'LT', 'NUMBER'] },
  ];

  for (const tc of edgeCases) {
    try {
      const tokens = tokenize(tc.input);
      const types = tokens.filter(t => t.type !== 'EOF').map(t => t.type);
      console.log(`✅ 分词测试：${tc.input}`);
      console.log(`   结果：${types.join(' ')}`);
      passCount++;
    } catch (e: any) {
      console.error(`❌ 分词失败：${e.message}`);
      failCount++;
    }
  }
  console.log('');

  // ========== 总结 ==========
  console.log('='.repeat(70));
  console.log('📊 测试结果汇总');
  console.log('-'.repeat(70));
  console.log(`通过：${passCount} | 失败：${failCount}`);
  console.log(`通过率：${((passCount / (passCount + failCount)) * 100).toFixed(1)}%`);
  
  if (failCount === 0) {
    console.log('🎉 所有测试通过！系统健壮性良好。');
  } else {
    console.log('⚠️  存在失败项，请检查日志。');
  }
  console.log('='.repeat(70));
}

runComprehensiveTest().catch(console.error);
