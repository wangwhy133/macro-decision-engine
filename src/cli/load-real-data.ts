#!/usr/bin/env tsx
/**
 * 加载真实数据 (或模拟数据) 并初始化数据库
 * 
 * 使用步骤:
 * 1. 设置环境变量: export TUSHARE_TOKEN="your_token"
 * 2. 运行脚本: npx tsx src/cli/load-real-data.ts
 */

import initSqlJs from 'sql.js';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';
import { TushareAdapter } from '../adapters/TushareAdapter';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const DB_PATH = path.join(__dirname, '../../macro-decision.db');

async function loadRealData() {
  console.log('🗄️  初始化数据库并加载数据...\n');
  
  // 1. 删除旧数据库
  if (fs.existsSync(DB_PATH)) {
    fs.unlinkSync(DB_PATH);
    console.log('🗑️  已删除旧数据库');
  }
  
  const SQL = await initSqlJs();
  const db = new SQL.Database();
  
  // 2. 创建数据表
  console.log('📋 创建数据表结构...');
  db.run(`
    CREATE TABLE IF NOT EXISTS data_points (
      id TEXT PRIMARY KEY,
      source_id TEXT NOT NULL,
      category TEXT NOT NULL,
      metric TEXT NOT NULL,
      value REAL NOT NULL,
      unit TEXT,
      change_value REAL,
      change_pct REAL,
      period TEXT,
      timestamp INTEGER NOT NULL,
      tags TEXT,
      raw_data TEXT,
      credibility_score REAL
    )
  `);
  
  // 3. 加载数据
  const adapter = new TushareAdapter();
  const rawData = await adapter.loadData(60); // 获取 60 个月数据
  
  if (rawData.length === 0) {
    console.error('❌ 未获取到任何数据');
    return;
  }
  
  console.log(`\n💾 开始插入 ${rawData.length} 条数据...\n`);
  
  // 4. 插入数据
  const stmt = db.prepare(`
    INSERT OR REPLACE INTO data_points 
    (id, source_id, category, metric, value, unit, change_value, change_pct, period, timestamp, tags, raw_data, credibility_score)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `);
  
  const dataMap = new Map<string, any>();
  rawData.forEach(d => {
    dataMap.set(`${d.normalized.metric}_${d.timestamp}`, d);
  });
  
  // 排序以确保时间顺序正确
  const sortedData = [...rawData].sort((a, b) => a.timestamp - b.timestamp);
  
  for (let i = 0; i < sortedData.length; i++) {
    const d = sortedData[i];
    const prev = i > 0 ? sortedData[i - 1] : null;
    
    // 计算变化率
    const change = prev ? (d.normalized.value as number) - (prev.normalized.value as number) : 0;
    const changePct = prev && prev.normalized.value !== 0 
      ? (change / (prev.normalized.value as number)) * 100 
      : 0;
    
    // 计算 3 个月变化率 (派生指标)
    let change3m = 0;
    if (i >= 3) {
      const prev3 = sortedData[i - 3];
      change3m = ((d.normalized.value as number) - (prev3.normalized.value as number)) / (prev3.normalized.value as number) * 100;
    }
    
    // 1. 插入主指标
    stmt.run([
      `${d.id}_inv`,
      d.source,
      d.category,
      'pig_inventory',
      d.normalized.value,
      d.normalized.unit,
      change,
      changePct,
      '月度',
      Math.floor(d.timestamp / 1000),
      JSON.stringify(d.tags),
      JSON.stringify(d.raw),
      d.credibility.score
    ]);
    
    // 2. 插入派生指标 (3 月变化率)
    stmt.run([
      `${d.id}_chg3m`,
      d.source,
      d.category,
      'pig_inventory_change_3m',
      change3m,
      '%',
      0,
      0,
      '月度',
      Math.floor(d.timestamp / 1000),
      JSON.stringify(['派生指标', '3 月变化']),
      JSON.stringify({ value: change3m }),
      d.credibility.score
    ]);
  }
  
  stmt.free();
  
  // 5. 保存数据库
  console.log('\n💾 保存数据库到磁盘...');
  const data = db.export();
  const buffer = Buffer.from(data);
  fs.writeFileSync(DB_PATH, buffer);
  db.close();
  
  // 6. 验证
  const verifyDb = await initSqlJs();
  const verifyDbInstance = new verifyDb.Database(buffer);
  const result = verifyDbInstance.exec('SELECT COUNT(*) FROM data_points');
  const count = result[0].values[0][0];
  
  console.log(`\n✅ 完成！`);
  console.log(`📊 数据库统计：${count} 条记录`);
  console.log(`📍 数据库位置：${DB_PATH}`);
  
  // 显示最新数据
  const latest = verifyDbInstance.exec('SELECT value FROM data_points WHERE metric="pig_inventory" ORDER BY timestamp DESC LIMIT 1');
  if (latest.length > 0 && latest[0].values.length > 0) {
    console.log(`📈 最新存栏量：${latest[0].values[0][0].toFixed(1)} 万头`);
  }
  
  verifyDbInstance.close();
}

loadRealData().catch(console.error);
