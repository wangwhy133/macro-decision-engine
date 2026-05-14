/**
 * 快速验证修复效果
 * 重点测试：数据验证 + 基础分词
 */

import { DataCredibilityService } from './src/services/DataCredibilityService';
import { tokenize } from './src/parser/tokens';

async function validate() {
  console.log('🔍 验证修复效果...\n');

  // 1. 数据验证
  console.log('【1】数据验证系统');
  const service = new DataCredibilityService();
  
  // 正常数据
  const normal = await service.ingest({
    source: 'eastmoney',
    sourceType: 'financial',
    timestamp: Date.now(),
    category: 'pig_cycle',
    data: { metric: '存栏量', value: 4500 },
    tags: []
  });
  console.log(`✅ 正常数据：可信度 ${normal.credibility.score.toFixed(3)}`);

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
    console.log('❌ 负数未拦截');
  } catch (e) {
    console.log(`✅ 负数拦截：${(e as Error).message}`);
  }

  // 无穷大拦截
  try {
    await service.ingest({
      source: 'test',
      sourceType: 'financial',
      timestamp: Date.now(),
      category: 'test',
      data: { metric: 'CPI', value: Infinity },
      tags: []
    });
    console.log('❌ 无穷大未拦截');
  } catch (e) {
    console.log(`✅ 无穷大拦截成功`);
  }

  // 2. 分词测试
  console.log('\n【2】分词功能');
  const testCases = [
    'RULE test: "测试"',
    'pig_inventory.change < -0.10',
    'AVG(value, 3)'
  ];

  for (const input of testCases) {
    try {
      const tokens = tokenize(input);
      console.log(`✅ "${input}" -> ${tokens.length} tokens`);
    } catch (e: any) {
      console.log(`❌ "${input}" 失败：${e.message}`);
    }
  }

  console.log('\n✅ 核心功能验证完成');
}

validate().catch(console.error);
