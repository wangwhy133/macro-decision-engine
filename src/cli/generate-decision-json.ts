#!/usr/bin/env tsx
/**
 * 生成机器可读的决策报告 (JSON 格式)
 * 用于对接交易系统或前端看板
 */

import { initDatabase } from '../db/init-db';
import { DataCredibilityService } from '../services/DataCredibilityService';
import { RuleEvaluator } from '../engine/RuleEvaluator';
import { parseRule } from '../parser/parser';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const DB_PATH = path.join(__dirname, '../../macro-decision.db');
const OUTPUT_PATH = path.join(__dirname, '../../reports/decision-latest.json');

// 猪周期经典策略
const STRATEGIES = [
  parseRule(`
RULE low_inventory_buy: "低水位买入"
DESCRIPTION "当能繁母猪存栏量低于 4300 万头时，视为周期底部区域，触发买入信号"
TYPE threshold
CATEGORY pig_cycle
PRIORITY 1
CONDITION pig_inventory_value < 4300
THEN CONCLUSION "低水位买入" CONFIDENCE 0.85 IMPACT positive HORIZON long
METADATA SOURCE expert VALIDATED true
END
`),
  parseRule(`
RULE rapid_decline_buy: "加速去化"
DESCRIPTION "当 3 个月存栏变化率低于 -3% 时，说明行业正在加速去产能，周期拐点临近"
TYPE trend
CATEGORY pig_cycle
PRIORITY 2
CONDITION pig_inventory_change_3m < -3
THEN CONCLUSION "加速去化买入" CONFIDENCE 0.80 IMPACT positive HORIZON medium
METADATA SOURCE expert VALIDATED true
END
`),
  parseRule(`
RULE peak_warning: "周期顶部预警"
DESCRIPTION "当存栏量高于 5000 万头时，周期可能见顶，应警惕下行风险"
TYPE threshold
CATEGORY pig_cycle
PRIORITY 3
CONDITION pig_inventory_value > 5000
THEN CONCLUSION "周期顶部风险" CONFIDENCE 0.75 IMPACT negative HORIZON medium
METADATA SOURCE expert VALIDATED false
END
`)
];

async function generateDecisionJson() {
  console.log('🤖 生成决策报告 (JSON)...\n');
  
  const db = await initDatabase(DB_PATH);
  const dataService = new DataCredibilityService(db);
  const evaluator = new RuleEvaluator();

  // 加载所有必需指标
  const inventoryData = await dataService.loadDataForEvaluation('pig_inventory', 12);
  const change3mData = await dataService.loadDataForEvaluation('pig_inventory_change_3m', 12);
  
  if (inventoryData.length === 0) {
    console.error('❌ 无数据');
    process.exit(1);
  }

  // 合并数据上下文
  const allData = [...inventoryData, ...change3mData];
  evaluator.setDataContext(allData);

  // 扫描所有策略
  const triggeredStrategies: any[] = [];
  const allStrategies = STRATEGIES.map(s => s.name);
  
  for (const strategy of STRATEGIES) {
    const result = evaluator.evaluate(strategy);
    if (result.triggered) {
      triggeredStrategies.push({
        ruleId: strategy.id,
        name: strategy.name,
        conclusion: strategy.inference.conclusion,
        confidence: strategy.inference.confidence,
        impact: strategy.inference.impact,
        horizon: strategy.inference.horizon
      });
    }
  }

  // 提取最新数据
  const latestInv = inventoryData[0]?.normalized.value as number || 0;
  const latestChange3m = change3mData[0]?.normalized.value as number || 0;
  const timestamp = new Date().toISOString();

  // 生成决策建议
  let action = 'HOLD';
  let reasoning = '市场运行平稳，无明确信号';
  
  if (triggeredStrategies.some(s => s.impact === 'positive')) {
    action = 'BUY';
    reasoning = `触发 ${triggeredStrategies.length} 个买入信号`;
  } else if (triggeredStrategies.some(s => s.impact === 'negative')) {
    action = 'SELL';
    reasoning = `触发 ${triggeredStrategies.length} 个风险信号`;
  }

  const report = {
    version: '1.0',
    timestamp,
    market: {
      pig_inventory: {
        value: latestInv,
        unit: '万头',
        change_3m: latestChange3m
      }
    },
    strategies: {
      total: allStrategies.length,
      triggered: triggeredStrategies.map(s => s.name)
    },
    decision: {
      action, // BUY | SELL | HOLD
      confidence: triggeredStrategies.length > 0 ? Math.max(...triggeredStrategies.map(s => s.confidence)) : 0,
      reasoning
    },
    signals: triggeredStrategies
  };

  // 写入文件
  fs.writeFileSync(OUTPUT_PATH, JSON.stringify(report, null, 2));
  
  console.log(`✅ 决策报告已生成：${OUTPUT_PATH}`);
  console.log(`📊 决策建议：${action}`);
  console.log(`💡 理由：${reasoning}`);
  console.log(`🔔 触发策略：${triggeredStrategies.length}/${allStrategies.length}`);
  
  if (triggeredStrategies.length > 0) {
    console.log('\n详细信号:');
    triggeredStrategies.forEach(s => {
      console.log(`  - ${s.name}: ${s.conclusion} (置信度: ${s.confidence})`);
    });
  }
}

generateDecisionJson().catch(console.error);
