#!/usr/bin/env tsx
/**
 * MDE 实时监控守护进程
 * 功能：定期轮询数据，发现异常信号时自动报警（日志/声音/推送）
 * 用法：npx tsx src/monitor/index.ts
 */

import { initDatabase } from '../db/init-db';
import { DataCredibilityService } from '../services/DataCredibilityService';
import { RuleEvaluator } from '../engine/RuleEvaluator';
import { parseRule } from '../parser/parser';

const CHECK_INTERVAL = parseInt(process.env.MDE_CHECK_INTERVAL || '3600000'); // 默认 1 小时
const DB_PATH = new URL('../../macro-decision.db', import.meta.url).pathname.replace(/^file:\/\//, '');

// 规则定义
const RULES = [
  {
    id: 'low_inventory',
    name: '低水位买入',
    rule: parseRule(`
RULE low_inventory: "低水位买入"
DESCRIPTION "当存栏量低于 4300 万头"
TYPE threshold
CATEGORY pig_cycle
PRIORITY 1
CONDITION pig_inventory_value < 4300
THEN CONCLUSION "低水位买入" CONFIDENCE 0.85 IMPACT positive HORIZON long
METADATA SOURCE expert VALIDATED true
END
`)
  },
  {
    id: 'rapid_decline',
    name: '加速去化',
    rule: parseRule(`
RULE rapid_decline: "加速去化"
DESCRIPTION "当 3 月变化率低于 -3%"
TYPE trend
CATEGORY pig_cycle
PRIORITY 2
CONDITION pig_inventory_change_3m < -3
THEN CONCLUSION "加速去化买入" CONFIDENCE 0.80 IMPACT positive HORIZON medium
METADATA SOURCE expert VALIDATED true
END
`)
  },
  {
    id: 'peak_warning',
    name: '周期顶部预警',
    rule: parseRule(`
RULE peak_warning: "周期顶部预警"
DESCRIPTION "当存栏量高于 5000 万头"
TYPE threshold
CATEGORY pig_cycle
PRIORITY 3
CONDITION pig_inventory_value > 5000
THEN CONCLUSION "周期顶部风险" CONFIDENCE 0.75 IMPACT negative HORIZON medium
METADATA SOURCE expert VALIDATED false
END
`)
  }
];

let lastCheckTime: number | null = null;

async function runCheck() {
  console.log(`\n🔍 [${new Date().toLocaleString()}] 开始例行检查...`);
  
  try {
    const db = await initDatabase(DB_PATH);
    const dataService = new DataCredibilityService(db);
    const evaluator = new RuleEvaluator();

    // 加载数据
    const inventoryData = await dataService.loadDataForEvaluation('pig_inventory', 12);
    const change3mData = await dataService.loadDataForEvaluation('pig_inventory_change_3m', 12);
    
    if (inventoryData.length === 0) {
      console.log('❌ 无可用数据');
      return;
    }

    const allData = [...inventoryData, ...change3mData];
    evaluator.setDataContext(allData);

    // 扫描规则
    const triggered: any[] = [];
    
    for (const { id, name, rule } of RULES) {
      const result = evaluator.evaluate(rule);
      if (result.triggered) {
        triggered.push({ id, name, ...result });
      }
    }

    // 输出结果
    const latestInv = inventoryData[0]?.normalized.value as number;
    const latestChange3m = change3mData[0]?.normalized.value as number;
    
    console.log(`📊 最新数据：存栏量 ${latestInv.toFixed(1)} 万头 | 3 月变化率 ${latestChange3m.toFixed(2)}%`);
    
    if (triggered.length > 0) {
      console.log('🚨 发现重要信号:');
      triggered.forEach(t => {
        console.log(`   🔔 [${t.name}] 已触发！`);
        // 这里可以扩展推送逻辑 (Telegram/邮件/声音)
        playAlertSound();
      });
      
      // 如果是新信号，可以记录日志或发送通知
      if (lastCheckTime) {
        console.log('💡 建议：查看决策报告或执行回测');
      }
    } else {
      console.log('✅ 无异常信号，市场平稳');
    }
    
    lastCheckTime = Date.now();
    
  } catch (error: any) {
    console.error('❌ 检查失败:', error.message);
  }
}

/**
 * 播放提示音 (终端 Bell)
 */
function playAlertSound() {
  // ASCII Bell character
  process.stdout.write('\x07');
}

// 立即执行一次
runCheck();

// 定时执行
setInterval(() => {
  runCheck();
}, CHECK_INTERVAL);

console.log(`⏰ 监控守护进程已启动，每 ${CHECK_INTERVAL / 1000} 秒检查一次`);
console.log('按 Ctrl+C 停止');
