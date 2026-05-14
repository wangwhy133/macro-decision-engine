#!/usr/bin/env tsx
/**
 * 从 CSV 文件加载真实数据 (AKShare 生成)
 * 用法：npx tsx src/cli/load-from-csv.ts
 */

import initSqlJs from 'sql.js';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';
import { CsvAdapter } from '../adapters/CsvAdapter';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const DB_PATH = path.join(__dirname, '../../macro-decision.db');

async function loadFromCsv() {
  console.log('🗄️  从 CSV 加载真实数据...\n');
  
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
  
  // 3. 从 CSV 加载数据
  const adapter = new CsvAdapter();
  const rawData = await adapter.loadDataAll();
  
  if (rawData.length === 0) {
    console.error('❌ 未从 CSV 加载到任何数据，请检查 data/raw/ 目录');
    return;
  }
  
  console.log(`\n💾 开始插入 ${rawData.length} 条数据...\n`);
  
  // 4. 插入数据
  const stmt = db.prepare(`
    INSERT OR REPLACE INTO data_points 
    (id, source_id, category, metric, value, unit, change_value, change_pct, period, timestamp, tags, raw_data, credibility_score)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `);
  
  // 按指标分组处理
  const groupedData = new Map<string, any[]>();
  rawData.forEach(d => {
    const key = d.normalized.metric;
    if (!groupedData.has(key)) groupedData.set(key, []);
    groupedData.get(key)!.push(d);
  });
  
  for (const [metric, metricsData] of groupedData) {
    // 按时间排序
    const sorted = metricsData.sort((a, b) => a.timestamp - b.timestamp);
    
    for (let i = 0; i < sorted.length; i++) {
      const d = sorted[i];
      const prev = i > 0 ? sorted[i - 1] : null;
      
      // 计算变化率
      const change = prev ? (d.normalized.value as number) - (prev.normalized.value as number) : 0;
      const changePct = prev && prev.normalized.value !== 0 
        ? (change / (prev.normalized.value as number)) * 100 
        : 0;
      
      // 计算 3 个月变化率 (派生指标)
      let change3m = 0;
      if (i >= 3) {
        const prev3 = sorted[i - 3];
        change3m = ((d.normalized.value as number) - (prev3.normalized.value as number)) / (prev3.normalized.value as number) * 100;
      }
      
      // 1. 插入主指标
      stmt.run([
        `${d.id}_main`,
        d.source,
        d.category,
        d.normalized.metric,
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
      
      // 2. 如果是存栏量，插入派生指标
      if (d.normalized.metric === 'pig_inventory') {
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
    }
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
  const result = verifyDbInstance.exec('SELECT metric, COUNT(*) FROM data_points GROUP BY metric');
  
  console.log(`\n✅ 完成！`);
  console.log('📊 数据统计:');
  result.forEach(row => {
    console.log(`   - ${row[0]}: ${row[1]} 条`);
  });
  console.log(`📍 数据库位置：${DB_PATH}`);
  
  verifyDbInstance.close();
}

loadFromCsv().catch(console.error);
