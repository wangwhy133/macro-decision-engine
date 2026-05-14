#!/usr/bin/env tsx
/**
 * 生成每日复盘报告 (Markdown 格式)
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { initDatabase } from '../db/init-db';
import { DataCredibilityService } from '../services/DataCredibilityService';
import { RuleEvaluator } from '../engine/RuleEvaluator';
import { parseRule } from '../parser/parser';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const DB_PATH = path.join(__dirname, '../../macro-decision.db');
const REPORTS_DIR = path.join(__dirname, '../../reports');

async function generateReport() {
  console.log('📝 生成每日复盘报告...');
  
  // 确保 reports 目录存在
  if (!fs.existsSync(REPORTS_DIR)) {
    fs.mkdirSync(REPORTS_DIR, { recursive: true });
  }

  const db = await initDatabase(DB_PATH);
  const dataService = new DataCredibilityService(db);
  const evaluator = new RuleEvaluator();

  // 获取数据
  const inventoryData = await dataService.loadDataForEvaluation('pig_inventory', 12);
  if (inventoryData.length === 0) {
    console.log('❌ 无数据');
    return;
  }

  const latest = inventoryData[0];
  const prev = inventoryData[1];
  const latestVal = typeof latest.normalized.value === 'number' ? latest.normalized.value : 0;
  const prevVal = prev && typeof prev.normalized.value === 'number' ? prev.normalized.value : 0;
  const changePct = prevVal ? ((latestVal - prevVal) / prevVal) * 100 : 0;

  // 规则扫描
  evaluator.setDataContext(inventoryData);
  const rules = [
    parseRule(`
RULE report_rule: "低存栏量"
DESCRIPTION "当存栏量低于 4300 万头时触发"
TYPE threshold
CATEGORY pig_cycle
PRIORITY 1
CONDITION pig_inventory_value < 4300
THEN CONCLUSION "低水位" CONFIDENCE 0.8 IMPACT positive HORIZON long
METADATA SOURCE expert VALIDATED true
END
`)
  ];
  
  const triggeredRules: string[] = [];
  for (const rule of rules) {
    if (evaluator.evaluate(rule).triggered) {
      triggeredRules.push(rule.name);
    }
  }

  // 生成 Markdown
  const dateStr = new Date().toISOString().split('T')[0];
  const md = `# 宏观决策日报 ${dateStr}

## 📊 市场概览
| 指标 | 数值 | 环比变化 |
|------|------|----------|
| 能繁母猪存栏量 | ${latestVal.toFixed(1)} 万头 | ${changePct > 0 ? '+' : ''}${changePct.toFixed(2)}% |

## 🔔 触发规则
${triggeredRules.length > 0 ? triggeredRules.map(r => `- ✅ ${r}`).join('\n') : '- 无重要规则触发'}

## 💡 操作建议
${triggeredRules.length > 0 
  ? '市场处于特殊状态，建议关注相关板块异动。'
  : '市场运行平稳，维持现有策略观察。'}

---
*生成时间：${new Date().toLocaleString('zh-CN')} | 宏观决策支持引擎 v1.0*
`;

  // 写入文件
  const fileName = `daily-report-${dateStr}.md`;
  const filePath = path.join(REPORTS_DIR, fileName);
  fs.writeFileSync(filePath, md);
  
  console.log(`✅ 报告已生成：${filePath}`);
  console.log('\n' + md);
}

generateReport().catch(console.error);
