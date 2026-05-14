#!/usr/bin/env tsx
/**
 * 危机模拟脚本：注入极端数据，测试系统反应
 * 场景：模拟某地爆发猪瘟，存栏量单月暴跌 15%
 */

import initSqlJs from 'sql.js';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const DB_PATH = path.join(__dirname, '../../macro-decision.db');

async function simulateCrisis() {
  console.log('🚨 开始危机模拟...\n');
  console.log('🦠 场景：模拟爆发猪瘟，存栏量单月暴跌 15%');

  // 1. 读取当前数据库
  if (!fs.existsSync(DB_PATH)) {
    console.error('❌ 数据库不存在，请先运行 npm run quick-init');
    return;
  }

  const SQL = await initSqlJs();
  const db = new SQL.Database(fs.readFileSync(DB_PATH));

  // 2. 获取最新数据
  const latestRes = db.exec('SELECT * FROM data_points WHERE metric="pig_inventory" ORDER BY timestamp DESC LIMIT 1');
  if (latestRes.length === 0 || latestRes[0].values.length === 0) {
    console.error('❌ 无数据');
    return;
  }

  const latestRow = latestRes[0].values[0];
  // sql.js 返回的是数组，按顺序对应字段
  // id, source_id, category, metric, value, unit, change_value, change_pct, period, timestamp, tags, raw_data, credibility_score
  const currentInv = latestRow[4] as number;
  const currentTs = latestRow[9] as number;
  
  console.log(`📊 当前存栏量：${currentInv.toFixed(1)} 万头`);

  // 3. 注入危机数据 (时间设为当前时间 + 1 个月，模拟最新数据)
  const crisisInv = currentInv * 0.85; // 暴跌 15%
  const crisisTs = currentTs + 30 * 24 * 3600; // +30 天
  const crisisId = `crisis_${crisisTs}`;

  console.log(`📉 注入危机数据：${crisisInv.toFixed(1)} 万头 (-15%)`);

  db.run(`
    INSERT OR REPLACE INTO data_points 
    (id, source_id, category, metric, value, unit, change_value, change_pct, period, timestamp, tags, raw_data, credibility_score)
    VALUES (?, 'crisis_sim', 'pig_cycle', 'pig_inventory', ?, '万头', ?, ?, '月度', ?, ?, ?, 0.95)
  `, [crisisId, crisisInv, crisisInv - currentInv, ((crisisInv - currentInv) / currentInv) * 100, crisisTs, '["危机模拟", "猪瘟"]', JSON.stringify({ event: 'swine_fever' })]);

  // 同时注入派生指标 (3 月变化率)
  const crisisChange3m = -12.5; // 模拟 3 月变化率 -12.5%
  db.run(`
    INSERT OR REPLACE INTO data_points 
    (id, source_id, category, metric, value, unit, change_value, change_pct, period, timestamp, tags, raw_data, credibility_score)
    VALUES (?, 'crisis_sim', 'pig_cycle', 'pig_inventory_change_3m', ?, '%', 0, 0, '月度', ?, ?, ?, 0.95)
  `, [`${crisisId}_chg3m`, crisisChange3m, crisisTs, '["危机模拟", "3 月变化"]', JSON.stringify({ value: crisisChange3m })]);

  // 4. 保存数据库
  const data = db.export();
  const buffer = Buffer.from(data);
  fs.writeFileSync(DB_PATH, buffer);
  db.close();

  console.log('✅ 危机数据已注入\n');

  // 5. 自动运行决策脚本，观察反应
  console.log('🤖 运行决策引擎检测警报...');
  const { exec } = await import('child_process');
  const { promisify } = await import('util');
  const execAsync = promisify(exec);
  
  try {
    const { stdout } = await execAsync('npm run decision', { cwd: __dirname + '/../..' });
    console.log('\n' + stdout);
    
    // 检查结果中是否有 "BUY" 信号
    const reportPath = path.join(__dirname, '../../reports/decision-latest.json');
    if (fs.existsSync(reportPath)) {
      const report = JSON.parse(fs.readFileSync(reportPath, 'utf-8'));
      if (report.decision.action === 'BUY') {
        console.log('🎯 系统成功识别危机，发出买入信号！');
      } else {
        console.log('⚠️  系统未发出预期信号，请检查规则阈值');
      }
    }
  } catch (e: any) {
    console.error('执行出错:', e.message);
  }
}

simulateCrisis().catch(console.error);
