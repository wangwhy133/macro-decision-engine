#!/usr/bin/env tsx
/**
 * 策略回测 CLI
 */

import { initDatabase } from '../db/init-db';
import { DataCredibilityService } from '../services/DataCredibilityService';
import { Backtester } from '../engine/Backtester';
import { parseRule } from '../parser/parser';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const DB_PATH = path.join(__dirname, '../../macro-decision.db');

async function runBacktest() {
  console.log('📈 开始策略回测...\n');

  const db = await initDatabase(DB_PATH);
  const dataService = new DataCredibilityService(db);

  // 加载主指标
  const inventoryData = await dataService.loadDataForEvaluation('pig_inventory', 60);
  // 加载派生指标
  const change3mData = await dataService.loadDataForEvaluation('pig_inventory_change_3m', 60);
  
  if (inventoryData.length === 0) {
    console.log('❌ 未找到数据');
    return;
  }

  console.log(`📊 回测数据：${inventoryData.length} 个月`);
  console.log(`📊 派生指标：${change3mData.length} 条`);
  
  // 合并数据上下文 (RuleEvaluator 需要能访问所有指标)
  const allData = [...inventoryData, ...change3mData];

  // 定义策略规则 - 使用 3 月变化率
  const rule = parseRule(`
RULE backtest_strategy: "加速去化策略"
DESCRIPTION "当 3 个月变化率低于 -3% 时买入"
TYPE trend
CATEGORY pig_cycle
PRIORITY 1
CONDITION pig_inventory_change_3m < -3
THEN CONCLUSION "买入信号" CONFIDENCE 0.8 IMPACT positive HORIZON medium
METADATA SOURCE expert VALIDATED false
END
`);

  // 运行回测 - 传入合并后的数据
  const engine = new Backtester();
  // 注意：Backtester 目前只接受单一指标数据，需要修改为接受多指标
  // 临时方案：只使用 pig_inventory_change_3m 数据进行回测
  const results = engine.runBacktest(rule, change3mData);

  console.log('\n📊 回测结果:');
  console.log(`  总信号数：${results.totalSignals}`);
  console.log(`  胜率：${results.winRate.toFixed(1)}%`);
  console.log(`  盈亏比：${results.profitLossRatio.toFixed(2)}`);
  console.log(`  最大回撤：${results.maxDrawdown.toFixed(1)}%`);
  console.log(`  总回报：${results.totalReturn.toFixed(1)}%`);
  
  if (results.winRate > 50 && results.profitLossRatio > 1) {
    console.log('\n✅ 策略有效，可考虑实盘');
  } else {
    console.log('\n⚠️  策略需优化');
  }
}

runBacktest().catch(console.error);
