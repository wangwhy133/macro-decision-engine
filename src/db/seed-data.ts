/**
 * 数据种子脚本 (sql.js 版本)
 * 功能：导入历史宏观数据 (猪周期示例)
 */

import { Database } from 'sql.js';
import { v4 as uuidv4 } from 'uuid';

// 模拟过去 36 个月的月度猪周期数据
export function generatePigCycleData(): any[] {
  const data: any[] = [];
  const now = Date.now();
  const oneMonth = 30 * 24 * 60 * 60 * 1000;
  
  let inventory = 4800; 
  let price = 15.0;

  for (let i = 36; i >= 0; i--) {
    const timestamp = now - i * oneMonth;
    
    // 模拟周期性波动 (正弦波 + 随机噪声)
    const cycle = Math.sin((36 - i) * 0.17); 
    const noise = (Math.random() - 0.5) * 50;
    
    inventory = 4500 + cycle * 200 + noise;
    price = 18 - cycle * 5 + (Math.random() - 0.5) * 2;

    const prevInventory = data.find(d => d.metric === 'pig_inventory')?.value || inventory;
    const change = prevInventory ? (inventory - prevInventory) : 0;
    const changePct = prevInventory ? (change / prevInventory) : 0;

    data.push({
      id: uuidv4(),
      source_id: 'eastmoney',
      category: 'pig_cycle',
      metric: 'pig_inventory',
      value: inventory,
      unit: '万头',
      change_value: change,
      change_pct: changePct,
      period: '月度',
      timestamp: Math.floor(timestamp / 1000),
      tags: JSON.stringify(['猪周期', '供给端']),
      raw_data: JSON.stringify({ source: 'simulated' }),
      credibility_score: 0.85
    });

    const prevPrice = data.find(d => d.metric === 'pig_price')?.value || price;
    const priceChange = prevPrice ? (price - prevPrice) : 0;
    const priceChangePct = prevPrice ? (priceChange / prevPrice) : 0;

    data.push({
      id: uuidv4(),
      source_id: 'eastmoney',
      category: 'pig_cycle',
      metric: 'pig_price',
      value: price,
      unit: '元/公斤',
      change_value: priceChange,
      change_pct: priceChangePct,
      period: '月度',
      timestamp: Math.floor(timestamp / 1000),
      tags: JSON.stringify(['猪周期', '价格']),
      raw_data: JSON.stringify({ source: 'simulated' }),
      credibility_score: 0.90
    });
  }
  
  return data;
}

export function seedDatabase(db: Database): void {
  console.log('🌱 开始导入种子数据...');
  const data = generatePigCycleData();
  const insert = db.prepare(`
    INSERT OR REPLACE INTO data_points 
    (id, source_id, category, metric, value, unit, change_value, change_pct, period, timestamp, tags, raw_data, credibility_score)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `);
  db.run('BEGIN TRANSACTION');
  try {
    for (const item of data) {
      insert.run([item.id, item.source_id, item.category, item.metric, item.value, item.unit, item.change_value, item.change_pct, item.period, item.timestamp, item.tags, item.raw_data, item.credibility_score]);
    }
    db.run('COMMIT');
  } catch (e) {
    db.run('ROLLBACK');
    throw e;
  }
  console.log(`✅ 成功导入 ${data.length} 条历史数据`);
}
