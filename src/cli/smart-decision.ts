#!/usr/bin/env tsx
/**
 * 智能决策 CLI (整合版)
 * 功能：规则推理 -> AI 解释 -> 记录日志 -> 输出报告
 */

import { initDatabase } from '../db/init-db';
import { DataCredibilityService } from '../services/DataCredibilityService';
import { AdvancedRuleEngine } from '../engine/AdvancedRuleEngine';
import { ZhipuInterpreter } from '../services/ZhipuInterpreter';
import { ReviewService } from '../services/ReviewService';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const DB_PATH = path.join(__dirname, '../../macro-decision.db');

async function smartDecision() {
  console.log('🧠 启动智能决策引擎...\n');

  const db = await initDatabase(DB_PATH);
  const dataService = new DataCredibilityService(db);
  const ruleEngine = new AdvancedRuleEngine();
  const aiInterpreter = new ZhipuInterpreter();
  const reviewService = new ReviewService(db);

  // 1. 加载数据
  const inventoryData = await dataService.loadDataForEvaluation('pig_inventory', 12);
  const change3mData = await dataService.loadDataForEvaluation('pig_inventory_change_3m', 12);
  
  if (inventoryData.length === 0) {
    console.error('❌ 无数据');
    return;
  }

  const allData = [...inventoryData, ...change3mData];
  ruleEngine.setDataContext(allData);

  // 2. 规则推理
  console.log('🔍 执行规则推理...');
  const inference = ruleEngine.infer();
  
  const marketSnapshot = {
    inventory: inventoryData[0]?.normalized.value || 0,
    change3m: change3mData[0]?.normalized.value || 0
  };

  console.log(`   决策方向：${inference.finalDecision}`);
  console.log(`   置信度：${(inference.confidence * 100).toFixed(1)}%`);
  console.log(`   触发规则：${inference.triggeredRules.length} 条`);

  // 3. AI 解释生成
  console.log('\n🤖 生成 AI 解读 (智谱 glm-4.7-flash)...');
  const explanation = await aiInterpreter.explain(inference, marketSnapshot);
  
  console.log(`   [摘要] ${explanation.summary}`);
  console.log(`   [置信度等级] ${explanation.confidenceLevel}`);
  console.log(`   [不确定性评分] ${(explanation.uncertaintyScore * 100).toFixed(1)}%`);

  // 4. 记录日志
  console.log('\n📝 记录决策日志...');
  await reviewService.logDecision(inference, marketSnapshot);

  // 5. 生成完整报告 (Markdown)
  const reportDir = path.join(__dirname, '../../reports/smart');
  if (!fs.existsSync(reportDir)) fs.mkdirSync(reportDir, { recursive: true });
  
  const dateStr = new Date().toISOString().split('T')[0];
  const reportPath = path.join(reportDir, `smart-decision-${dateStr}.md`);
  
  const report = `
# 智能决策报告

**生成时间**: ${new Date().toLocaleString('zh-CN')}
**决策方向**: ${inference.finalDecision}
**置信度**: ${(inference.confidence * 100).toFixed(1)}%

## 📊 市场快照
| 指标 | 数值 |
|------|------|
| 存栏量 | ${marketSnapshot.inventory.toFixed(1)} 万头 |
| 3 月变化率 | ${marketSnapshot.change3m.toFixed(2)}% |

## 🤖 AI 分析 (智谱)
> ${explanation.summary}

${explanation.analysis}

## ⚠️ 风险提示
${explanation.riskWarning}

## 🔍 推理过程
${inference.steps.map(s => `- [${s.triggered ? '✅' : '❌'}] ${s.ruleName}: ${s.reason}`).join('\n')}

---
*本报告由 MDE 智能决策引擎生成 (模型：glm-4.7-flash)*
`;

  fs.writeFileSync(reportPath, report);
  console.log(`\n✅ 完整报告已保存：${reportPath}`);
  
  // 6. 尝试校准旧决策 (可选)
  console.log('\n🔄 检查历史决策校准...');
  reviewService.calibrate(30);
  const stats = reviewService.getStats();
  console.log(`   历史准确率：${stats.accuracy}% (${stats.correct}/${stats.total})`);
}

smartDecision().catch(console.error);
