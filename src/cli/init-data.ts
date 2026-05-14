#!/usr/bin/env tsx
/**
 * 初始化数据库并加载模拟数据
 */

import { initDatabase } from '../db/init-db';
import { DataCredibilityService } from '../services/DataCredibilityService';
import { generateRealisticData, toDataPoints } from '../utils/data-simulator';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const DB_PATH = path.join(__dirname, '../../macro-decision.db');

async function initData() {
  console.log('🗄️  初始化数据库...');
  
  const db = await initDatabase(DB_PATH);
  const dataService = new DataCredibilityService(db);

  console.log('📊 生成模拟数据...');
  const simulatedRaw = generateRealisticData(60); // 生成 60 个月原始数据
  const simulatedData = toDataPoints(simulatedRaw); // 转换为标准格式

  console.log('💾 保存数据到数据库...');
  
  // 批量插入数据
  for (const point of simulatedData) {
    await dataService.ingest({
      source: 'simulator',
      sourceType: 'simulated',
      timestamp: point.timestamp * 1000,
      category: 'pig_cycle',
      data: {
        metric: 'pig_inventory',
        value: point.value,
        unit: point.unit,
        change: { absolute: point.change_value, percentage: point.change_pct }
      },
      tags: JSON.parse(point.tags || '[]')
    });
  }

  console.log(`✅ 成功加载 ${simulatedData.length} 条数据`);
  console.log(`📍 数据库位置：${DB_PATH}`);
  
  // 显示最新数据 - 从数据库读取
  const latestData = await dataService.loadDataForEvaluation('pig_inventory', 1);
  if (latestData.length > 0) {
    const latest = latestData[0];
    console.log(`📈 最新存栏量：${(latest.normalized.value as number).toFixed(1)} 万头`);
  }
}

initData().catch(console.error);
