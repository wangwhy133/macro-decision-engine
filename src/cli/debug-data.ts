#!/usr/bin/env tsx
/**
 * 调试脚本：检查数据分布
 */

import { initDatabase } from '../db/init-db';
import { DataCredibilityService } from '../services/DataCredibilityService';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const DB_PATH = path.join(__dirname, '../../macro-decision.db');

async function debugData() {
  console.log('🔍 检查数据分布...\n');
  
  const db = await initDatabase(DB_PATH);
  const dataService = new DataCredibilityService(db);
  
  // 获取所有 3 月变化率数据
  const data = await dataService.loadDataForEvaluation('pig_inventory_change_3m', 100);
  
  console.log(`📊 共加载 ${data.length} 条 pig_inventory_change_3m 数据`);
  
  let triggerCount = 0;
  console.log('\n前 10 条数据详情:');
  data.slice(0, 10).forEach((dp, idx) => {
    const val = dp.normalized.value as number;
    const triggered = val < -3;
    if (triggered) triggerCount++;
    
    console.log(`  ${idx+1}. 值=${val.toFixed(2)}% | 触发条件 (< -3): ${triggered ? '✅' : '❌'}`);
  });
  
  // 统计触发次数
  const allTriggered = data.filter(dp => (dp.normalized.value as number) < -3);
  console.log(`\n📉 总触发次数：${allTriggered.length}/${data.length}`);
  
  if (allTriggered.length > 0) {
    console.log('✅ 数据中存在满足条件的记录，规则引擎应能触发');
  } else {
    console.log('⚠️  数据中无满足条件的记录，需调整阈值或检查数据生成逻辑');
  }
}

debugData().catch(console.error);
