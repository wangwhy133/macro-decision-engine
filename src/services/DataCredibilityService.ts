/**
 * 数据可信度服务 (sql.js 版本 - 修复数组取值)
 */

import { Database } from 'sql.js';
import { v4 as uuidv4 } from 'uuid';
import {
  DataPoint,
  RawDataPoint,
  CredibilityContext,
  CredibilityMetrics,
  DataFilters,
} from '../types';

const DEFAULT_CONFIG = {
  timeDecayHalfLife: 24,
  minCredibilityThreshold: 0.3,
  anomalyDetectionSensitivity: 2.0,
  maxDataPointsPerMetric: 1000,
  maxAgeHours: 720,
};

const SOURCE_BASE_SCORES: Record<string, number> = {
  'stats.gov': 0.95, 'pbc.gov': 0.95, 'gov.cn': 0.95,
  'eastmoney': 0.85, 'wind': 0.85, 'caixin': 0.80,
  'xinhua': 0.75, 'people_daily': 0.75, 'reuters': 0.70,
  'bloomberg': 0.70, 'default': 0.50,
};

export class DataCredibilityService {
  private db: Database;
  private config = DEFAULT_CONFIG;

  constructor(db: Database, config?: Partial<typeof DEFAULT_CONFIG>) {
    this.db = db;
    if (config) this.config = { ...this.config, ...config };
  }

  async ingest(data: RawDataPoint): Promise<DataPoint> {
    const value = data.data.value;
    if (typeof value === 'number') {
      if (!isFinite(value)) throw new Error(`无效数值：${value}`);
      if (data.category === 'pig_cycle' && value < 0) throw new Error('猪周期数据不能为负');
    }

    const dataPoint: DataPoint = {
      id: uuidv4(),
      source: data.source,
      sourceType: data.sourceType,
      timestamp: data.timestamp,
      receivedAt: Date.now(),
      category: data.category,
      tags: data.tags || [],
      raw: data.data,
      credibility: { score: 0, sourceReliability: 0, timeliness: 0, crossValidation: { verified: false, conflictingSources: [], consistencyScore: 0 }, anomalyFlags: [] },
      normalized: { metric: data.data.metric || 'unknown', value: data.data.value ?? 0, unit: data.data.unit || '', change: data.data.change },
    };

    const context: CredibilityContext = { currentTime: Date.now(), knownSources: this.getSourceReliabilities(), timeDecayHalfLife: this.config.timeDecayHalfLife };
    dataPoint.credibility = await this.calculateCredibility(dataPoint, context);

    this.saveToDb(dataPoint);
    return dataPoint;
  }

  private saveToDb(dp: DataPoint): void {
    this.db.run(`
      INSERT OR REPLACE INTO data_points 
      (id, source_id, category, metric, value, unit, change_value, change_pct, period, timestamp, tags, raw_data, credibility_score)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `, [
      dp.id, dp.source, dp.category, dp.normalized.metric,
      typeof dp.normalized.value === 'number' ? dp.normalized.value : 0,
      dp.normalized.unit,
      dp.normalized.change?.absolute || 0,
      dp.normalized.change?.percentage || 0,
      'unknown',
      Math.floor(dp.timestamp / 1000),
      JSON.stringify(dp.tags),
      JSON.stringify(dp.raw),
      dp.credibility.score
    ]);
  }

  async calculateCredibility(dataPoint: DataPoint, context: CredibilityContext): Promise<CredibilityMetrics> {
    const sourceReliability = this.getSourceReliability(dataPoint.source, context.knownSources);
    const age = (context.currentTime - dataPoint.timestamp) / (1000 * 60 * 60);
    const timeliness = Math.pow(0.5, age / context.timeDecayHalfLife);
    const crossValidation = await this.crossValidateSingle(dataPoint);
    const anomalyFlags = await this.detectAnomaliesSingle(dataPoint);
    let score = sourceReliability * timeliness * crossValidation.consistencyScore;
    if (anomalyFlags.length > 0) score *= Math.pow(0.7, anomalyFlags.length);
    return { score: Math.max(0, Math.min(1, score)), sourceReliability, timeliness, crossValidation, anomalyFlags };
  }

  private getSourceReliability(source: string, knownSources: any): number {
    return SOURCE_BASE_SCORES[source] || SOURCE_BASE_SCORES.default;
  }

  private getSourceReliabilities(): any {
    return new Map(Object.entries(SOURCE_BASE_SCORES).map(([k, v]) => [k, { baseScore: v }]));
  }

  private async crossValidateSingle(dp: DataPoint): Promise<any> {
    const stmt = this.db.prepare('SELECT value FROM data_points WHERE metric = ? AND timestamp > ?');
    stmt.bind([dp.normalized.metric, (dp.timestamp - 86400000) / 1000]);
    const rows: any[] = [];
    while (stmt.step()) rows.push(stmt.get() as any);
    stmt.free();

    if (rows.length === 0) return { verified: false, conflictingSources: [], consistencyScore: 1.0 };
    
    const values = rows.map((r: any) => Array.isArray(r) ? r[4] : r.value).filter((v: any) => typeof v === 'number');
    if (values.length === 0) return { verified: false, conflictingSources: [], consistencyScore: 1.0 };

    const avg = values.reduce((a: number, b: number) => a + b, 0) / values.length;
    const deviation = Math.abs((dp.normalized.value as number) - avg) / (avg || 1);
    const consistent = deviation <= 0.2;

    return {
      verified: consistent,
      conflictingSources: consistent ? [] : ['db_check'],
      consistencyScore: consistent ? 1.0 : Math.max(0.3, 1 - deviation)
    };
  }

  private async detectAnomaliesSingle(dp: DataPoint): Promise<string[]> {
    const flags: string[] = [];
    const value = dp.normalized.value as number;
    if (typeof value !== 'number') return flags;
    if (value < 0) flags.push('invalid_negative_value');
    return flags;
  }

  async loadDataForEvaluation(metric: string, limit: number = 100): Promise<DataPoint[]> {
    const stmt = this.db.prepare(`
      SELECT id, source_id, category, metric, value, unit, change_value, change_pct, timestamp, tags, raw_data, credibility_score
      FROM data_points 
      WHERE metric = ? 
      ORDER BY timestamp DESC 
      LIMIT ?
    `);
    stmt.bind([metric, limit]);
    
    const rows: any[] = [];
    while (stmt.step()) {
      rows.push(stmt.get() as any);
    }
    stmt.free();

    return rows.map((row: any) => {
      // sql.js get() 返回的是数组 [id, source_id, category, metric, value, unit, change_value, change_pct, timestamp, tags, raw_data, credibility_score]
      const isArr = Array.isArray(row);
      
      const id = isArr ? row[0] : row.id;
      const source = isArr ? row[1] : row.source_id;
      const category = isArr ? row[2] : row.category;
      const m = isArr ? row[3] : row.metric;
      const val = isArr ? row[4] : (row.value ?? 0);
      const unit = isArr ? row[5] : (row.unit ?? '');
      const changeVal = isArr ? row[6] : (row.change_value ?? 0);
      const changePct = isArr ? row[7] : (row.change_pct ?? 0);
      const ts = isArr ? row[8] : row.timestamp;
      const tags = isArr ? row[9] : row.tags;
      const rawData = isArr ? row[10] : row.raw_data;
      const cred = isArr ? row[11] : row.credibility_score;

      return {
        id,
        source,
        sourceType: 'financial' as any,
        timestamp: ts * 1000,
        receivedAt: Date.now(),
        category,
        tags: JSON.parse(tags || '[]'),
        raw: JSON.parse(rawData || '{}'),
        credibility: { score: cred, sourceReliability: 0, timeliness: 0, crossValidation: { verified: false, conflictingSources: [], consistencyScore: 0 }, anomalyFlags: [] },
        normalized: { metric: m, value: val, unit: unit, change: { absolute: changeVal, percentage: changePct, period: 'unknown' } }
      };
    });
  }

  async query(filters: DataFilters): Promise<DataPoint[]> { return []; }
  async getByTags(tags: string[]): Promise<DataPoint[]> { return []; }
  async getById(id: string): Promise<DataPoint | null> { return null; }
  async updateCredibility(id: string, credibility: CredibilityMetrics): Promise<void> {}
}
