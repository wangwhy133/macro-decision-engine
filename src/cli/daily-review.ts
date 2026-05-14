#!/usr/bin/env tsx
/**
 * 每日复盘 CLI - 扫描规则并生成 AI 解读
 */

import { initDatabase } from '../db/init-db';
import { DataCredibilityService } from '../services/DataCredibilityService';
import { RuleEvaluator } from '../engine/RuleEvaluator';
import { parseRule } from '../parser/parser';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const DB_PATH = path.join(__dirname, '../../macro-decision.db');

async function dailyReview() {
  console.log('🔍 开始每日复盘扫描...\n');

  const db = await initDatabase(DB_PATH);
  const dataService = new DataCredibilityService(db);
  const evaluator = new RuleEvaluator();

  // 加载能繁母猪存栏数据 (最近 12 个月)
  const inventoryData = await dataService.loadDataForEvaluation('pig_inventory', 12);
  if (inventoryData.length === 0) {
    console.log('❌ 未找到数据，请先加载数据');
    return;
  }

  console.log(`📊 已加载 ${inventoryData.length} 条存栏数据`);
  const latest = inventoryData[0];
  const latestVal = typeof latest.normalized.value === 'number' ? latest.normalized.value : 0;
  console.log(`📈 最新存栏量：${latestVal.toFixed(2)} (标准化值)\n`);

  // 设置数据上下文
  evaluator.setDataContext(inventoryData);

  // 规则扫描
  const rules = [
    parseRule(`
RULE low_inventory: "低存栏量"
DESCRIPTION "当存栏量低于 4300 万头时触发"
TYPE threshold
CATEGORY pig_cycle
PRIORITY 1
CONDITION pig_inventory_value < 4300
THEN CONCLUSION "低水位" CONFIDENCE 0.8 IMPACT positive HORIZON long
METADATA SOURCE expert VALIDATED true
END
`),
    parseRule(`
RULE rapid_decline: "加速去化"
DESCRIPTION "当 3 个月变化率低于 -5% 时触发"
TYPE trend
CATEGORY pig_cycle
PRIORITY 2
CONDITION pig_inventory_change_3m < -5
THEN CONCLUSION "加速去化" CONFIDENCE 0.85 IMPACT positive HORIZON medium
METADATA SOURCE expert VALIDATED true
END
`)
  ];

  console.log('🔔 规则扫描结果:');
  let triggeredCount = 0;
  
  for (const rule of rules) {
    const result = evaluator.evaluate(rule);
    if (result.triggered) {
      triggeredCount++;
      console.log(`  ✅ [${rule.name}] ${rule.conclusion} (置信度：${result.confidence})`);
    } else {
      console.log(`  ❌ [${rule.name}] 未触发`);
    }
  }

  console.log(`\n📝 总结：共触发 ${triggeredCount}/${rules.length} 条规则`);
  
  if (triggeredCount > 0) {
    console.log('\n💡 建议运行 `npm run report` 生成详细报告');
  }
}

dailyReview().catch(console.error);
