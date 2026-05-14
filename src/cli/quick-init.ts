#!/usr/bin/env tsx
/**
 * 快速初始化数据库 - 直接插入模拟数据
 */

import initSqlJs from 'sql.js';
import { generateRealisticData } from '../utils/data-simulator';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const DB_PATH = path.join(__dirname, '../../macro-decision.db');

async function quickInit() {
  console.log('🗄️  初始化数据库...');
  
  // 删除旧数据库，创建新的
  if (fs.existsSync(DB_PATH)) {
    fs.unlinkSync(DB_PATH);
  }
  
  const SQL = await initSqlJs();
  const db = new SQL.Database();
  
  console.log('📋 创建数据表...');
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
  
  console.log('📊 生成模拟数据...');
  const rawData = generateRealisticData(60);
  
  console.log('💾 直接插入数据...');
  
  // 直接插入原始数据到 data_points 表
  const stmt = db.prepare(`
    INSERT OR REPLACE INTO data_points 
    (id, source_id, category, metric, value, unit, change_value, change_pct, period, timestamp, tags, raw_data, credibility_score)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `);
  
  const now = Date.now();
  const oneMonth = 30 * 24 * 60 * 60 * 1000;
  
  // 预计算所有派生指标
  for (let i = 0; i < rawData.length; i++) {
    const d = rawData[i];
    const monthsAgo = rawData.length - i;
    const timestamp = Math.floor((now - monthsAgo * oneMonth) / 1000);
    
    // 计算变化率
    const prevInv = i < rawData.length - 1 ? rawData[i + 1].inventory : d.inventory;
    const change = d.inventory - prevInv;
    const changePct = prevInv !== 0 ? (change / prevInv) * 100 : 0;
    
    // 计算 3 个月变化率 (派生指标)
    let change3m = 0;
    if (i + 3 < rawData.length) {
      const inv3m = rawData[i + 3].inventory;
      change3m = ((d.inventory - inv3m) / inv3m) * 100;
    }

    // 1. 插入主指标 pig_inventory
    stmt.run([
      `sim_${i}_inv`,
      'simulator',
      'pig_cycle',
      'pig_inventory',
      d.inventory,
      '万头',
      change,
      changePct,
      '月度',
      timestamp,
      JSON.stringify(['模拟数据', '猪周期']),
      JSON.stringify({ ...d, change_3m: change3m }),
      0.95
    ]);

    // 2. 插入派生指标 pig_inventory_change_3m
    stmt.run([
      `sim_${i}_chg3m`,
      'simulator',
      'pig_cycle',
      'pig_inventory_change_3m',
      change3m,
      '%',
      0,
      0,
      '月度',
      timestamp,
      JSON.stringify(['派生指标', '3 月变化']),
      JSON.stringify({ value: change3m }),
      0.95
    ]);
  }
  
  stmt.free();
  
  console.log(`✅ 成功插入 ${rawData.length} 条数据`);
  
  // 验证
  const result = db.exec('SELECT COUNT(*) as count FROM data_points');
  if (result.length > 0 && result[0].values.length > 0) {
    console.log(`📊 数据库统计：${result[0].values[0][0]} 条记录`);
  }
  
  // 保存数据库
  console.log('💾 保存数据库到磁盘...');
  const data = db.export();
  const buffer = Buffer.from(data);
  fs.writeFileSync(DB_PATH, buffer);
  
  console.log(`📍 数据库已保存：${DB_PATH}`);
  
  db.close();
}

quickInit().catch(console.error);
