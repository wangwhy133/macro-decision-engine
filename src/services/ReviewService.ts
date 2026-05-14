/**
 * 复盘校准服务
 * 功能：记录决策日志，追踪后续市场走势，计算准确率，提供校准建议
 */

import initSqlJs from 'sql.js';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { InferenceResult } from '../engine/AdvancedRuleEngine';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const DB_PATH = path.join(__dirname, '../../macro-decision.db');

export interface DecisionLog {
  id: string;
  timestamp: number;
  decision: 'BUY' | 'SELL' | 'HOLD';
  confidence: number;
  reasoning: string;
  triggeredRules: string; // JSON
  marketSnapshot: string; // JSON
  
  // 事后校准字段
  actualChange_1d?: number; // 1 日后实际变化
  actualChange_7d?: number;
  actualChange_30d?: number;
  isCorrect?: boolean; // 预测是否准确
  errorReason?: string;
}

export class ReviewService {
  private db: any;

  constructor(db: any) {
    this.db = db;
    this._initTables();
  }

  private _initTables() {
    this.db.run(`
      CREATE TABLE IF NOT EXISTS decision_logs (
        id TEXT PRIMARY KEY,
        timestamp INTEGER NOT NULL,
        decision TEXT NOT NULL,
        confidence REAL,
        reasoning TEXT,
        triggered_rules TEXT,
        market_snapshot TEXT,
        
        actual_change_1d REAL,
        actual_change_7d REAL,
        actual_change_30d REAL,
        is_correct INTEGER,
        error_reason TEXT
      )
    `);
  }

  /**
   * 记录一次决策
   */
  async logDecision(result: InferenceResult, marketSnapshot: any) {
    const id = `dec_${Date.now()}`;
    const timestamp = Date.now();
    
    this.db.run(`
      INSERT INTO decision_logs 
      (id, timestamp, decision, confidence, reasoning, triggered_rules, market_snapshot)
      VALUES (?, ?, ?, ?, ?, ?, ?)
    `, [
      id,
      timestamp,
      result.finalDecision,
      result.confidence,
      result.reasoning,
      JSON.stringify(result.triggeredRules.map(r => r.id)),
      JSON.stringify(marketSnapshot)
    ]);

    console.log(`📝 决策已记录: ${id} -> ${result.finalDecision}`);
    return id;
  }

  /**
   * 校准历史决策 (填入实际结果)
   * @param daysBack 回溯多少天前的决策
   */
  async calibrate(daysBack: number = 30) {
    console.log('🔄 开始校准历史决策...');
    
    const now = Date.now();
    const cutoff = now - daysBack * 24 * 60 * 60 * 1000;
    
    // 获取所有未校准的决策
    const stmt = this.db.prepare(`
      SELECT id, decision, timestamp, market_snapshot 
      FROM decision_logs 
      WHERE timestamp < ? AND is_correct IS NULL
    `);
    
    const rows: any[] = [];
    while (stmt.step()) {
      rows.push(stmt.get());
    }
    stmt.free();

    if (rows.length === 0) {
      console.log('✅ 没有需要校准的决策');
      return;
    }

    for (const row of rows) {
      const isArr = Array.isArray(row);
      const id = isArr ? row[0] : row.id;
      const decision = isArr ? row[1] : row.decision;
      const ts = isArr ? row[2] : row.timestamp;
      
      // 获取当前最新数据 (模拟获取实际结果)
      // 实际场景中需查询外部数据源获取 ts 之后 N 天的价格/存栏量变化
      // 这里简化处理：假设我们能获取到实际变化
      const actualChange = this._getActualChange(ts, now); 
      const isCorrect = this._evaluateDecision(decision, actualChange);

      this.db.run(`
        UPDATE decision_logs 
        SET actual_change_30d = ?, is_correct = ?, error_reason = ?
        WHERE id = ?
      `, [actualChange, isCorrect ? 1 : 0, isCorrect ? null : '预测方向错误', id]);
    }

    this._saveDb();
    console.log(`✅ 已校准 ${rows.length} 条决策`);
  }

  /**
   * 获取实际变化 (模拟)
   */
  private _getActualChange(decisionTime: number, currentTime: number): number {
    // 真实场景：查询数据库或 API 获取 decisionTime 之后 30 天的数据变化
    // 模拟：随机生成一个变化率
    return (Math.random() - 0.5) * 0.2; // -10% ~ +10%
  }

  /**
   * 评估决策是否正确
   */
  private _evaluateDecision(decision: string, actualChange: number): boolean {
    if (decision === 'BUY') return actualChange > 0;
    if (decision === 'SELL') return actualChange < 0;
    return true; // HOLD 默认正确
  }

  private _saveDb() {
    const data = this.db.export();
    const buffer = Buffer.from(data);
    fs.writeFileSync(DB_PATH, buffer);
  }

  /**
   * 获取历史准确率统计
   */
  getStats() {
    const res = this.db.exec(`
      SELECT 
        COUNT(*) as total,
        SUM(is_correct) as correct,
        ROUND(CAST(SUM(is_correct) AS FLOAT) / COUNT(*) * 100, 2) as accuracy
      FROM decision_logs 
      WHERE is_correct IS NOT NULL
    `);
    
    if (res.length === 0 || res[0].values.length === 0) {
      return { total: 0, correct: 0, accuracy: 0 };
    }
    
    const row = res[0].values[0];
    return {
      total: row[0] || 0,
      correct: row[1] || 0,
      accuracy: row[2] || 0
    };
  }
}
