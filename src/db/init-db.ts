/**
 * 数据库初始化脚本 (sql.js 版本)
 */

import initSqlJs, { Database } from 'sql.js';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const DB_PATH = path.join(__dirname, '../../macro-decision.db');

export async function initDatabase(dbPath: string = DB_PATH): Promise<Database> {
  const SQL = await initSqlJs();
  let db: Database;

  if (fs.existsSync(dbPath)) {
    const buffer = fs.readFileSync(dbPath);
    db = new SQL.Database(buffer);
  } else {
    db = new SQL.Database();
    
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

    db.run(`
      CREATE TABLE IF NOT EXISTS rules (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        rule_type TEXT,
        category TEXT,
        priority INTEGER,
        condition_expr TEXT NOT NULL,
        conclusion TEXT,
        confidence REAL,
        impact TEXT,
        horizon TEXT,
        source_type TEXT,
        validated INTEGER DEFAULT 0,
        success_rate REAL,
        validation_count INTEGER,
        status TEXT DEFAULT 'active'
      )
    `);

    db.run(`
      CREATE TABLE IF NOT EXISTS decision_logs (
        id TEXT PRIMARY KEY,
        rule_id TEXT NOT NULL,
        triggered INTEGER,
        context_snapshot TEXT,
        conclusion TEXT,
        confidence REAL,
        eval_time INTEGER
      )
    `);

    db.run(`CREATE INDEX IF NOT EXISTS idx_data_metric ON data_points(metric)`);
    db.run(`CREATE INDEX IF NOT EXISTS idx_data_time ON data_points(timestamp DESC)`);
  }

  return db;
}

export function saveDatabase(db: Database, dbPath: string = DB_PATH): void {
  const data = db.export();
  const buffer = Buffer.from(data);
  fs.writeFileSync(dbPath, buffer);
}
