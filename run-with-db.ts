/**
 * 综合运行脚本：初始化 DB -> 导入数据 -> 运行回测
 */

import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';
import { initDatabase, saveDatabase } from './src/db/init-db';
import { seedDatabase } from './src/db/seed-data';
import { DataCredibilityService } from './src/services/DataCredibilityService';
import { RuleEvaluator } from './src/engine/RuleEvaluator';
import { parseRule } from './src/parser/parser';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const DB_PATH = path.join(__dirname, 'macro-decision.db');

async function run() {
  console.log('🚀 宏观决策支持引擎 - 持久化与回测演示\n');
  
  // 1. 初始化数据库
  console.log('【步骤 1】初始化数据库...');
  const db = await initDatabase(DB_PATH);
  
  // 2. 导入种子数据
  console.log('\n【步骤 2】导入历史数据...');
  seedDatabase(db);
  saveDatabase(db, DB_PATH); // 保存
  
  // 3. 创建服务实例
  const dataService = new DataCredibilityService(db);
  const evaluator = new RuleEvaluator();
  
  // 4. 加载数据
  console.log('\n【步骤 3】加载数据...');
  const inventoryData = await dataService.loadDataForEvaluation('pig_inventory', 50);
  const priceData = await dataService.loadDataForEvaluation('pig_price', 50);
  console.log(`  - 加载存栏量数据：${inventoryData.length} 条`);
  console.log(`  - 加载猪价数据：${priceData.length} 条`);
  
  // 5. 构建回测上下文
  const allData = [...inventoryData, ...priceData];
  evaluator.setDataContext(allData);
  
  // 6. 定义并测试规则
  console.log('\n【步骤 4】运行回测规则...');
  
  const rules = [
    parseRule(`
RULE backtest_low_inventory: "低存栏量信号"
DESCRIPTION "当存栏量低于 4500 时触发"
TYPE threshold
CATEGORY pig_cycle
PRIORITY 8
CONDITION
  pig_inventory_value < 4500
THEN
  CONCLUSION "存栏量低位，供给收缩预期"
  CONFIDENCE 0.75
  IMPACT positive
  HORIZON medium
METADATA
  SOURCE expert
  VALIDATED true
END
`),
    parseRule(`
RULE backtest_trend: "存栏量下降趋势"
DESCRIPTION "当存栏量变化为负时触发"
TYPE trend
CATEGORY pig_cycle
PRIORITY 7
CONDITION
  pig_inventory_change_value < 0
THEN
  CONCLUSION "存栏量下降中"
  CONFIDENCE 0.65
  IMPACT positive
  HORIZON short
METADATA
  SOURCE expert
  VALIDATED true
END
`)
  ];
  
  let triggerCount = 0;
  for (const rule of rules) {
    const result = evaluator.evaluate(rule);
    if (result.triggered) {
      console.log(`  ✅ [${rule.name}] 触发！结论：${rule.inference.conclusion}`);
      triggerCount++;
    } else {
      console.log(`  ℹ️  [${rule.name}] 未触发`);
    }
  }
  
  console.log(`\n📊 回测总结：${triggerCount}/${rules.length} 条规则触发`);
  console.log('✅ 演示完成！数据库文件位于:', DB_PATH);
  
  // 保存最终状态
  saveDatabase(db, DB_PATH);
}

run().catch(console.error);
