/**
 * CSV 数据适配器
 * 功能：读取由 Python 脚本 (AKShare) 生成的原始 CSV 数据，并转换为标准 DataPoint 格式
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { DataPoint } from '../types';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const DATA_DIR = path.join(__dirname, '../../data/raw');

export interface CsvConfig {
  inventoryFile?: string;
  feedRatioFile?: string;
}

export class CsvAdapter {
  private config: CsvConfig;

  constructor(config: CsvConfig = {}) {
    this.config = {
      inventoryFile: 'pig_inventory.csv',
      feedRatioFile: 'pig_feed_ratio.csv',
      ...config
    };
  }

  /**
   * 加载所有可用数据
   */
  async loadDataAll(): Promise<DataPoint[]> {
    const allData: DataPoint[] = [];

    // 1. 加载存栏数据
    if (this.config.inventoryFile) {
      const invData = await this._loadInventory(path.join(DATA_DIR, this.config.inventoryFile));
      allData.push(...invData);
    }

    // 2. 加载猪粮比数据
    if (this.config.feedRatioFile) {
      const ratioData = await this._loadFeedRatio(path.join(DATA_DIR, this.config.feedRatioFile));
      allData.push(...ratioData);
    }

    return allData;
  }

  /**
   * 加载存栏数据
   */
  private async _loadInventory(filePath: string): Promise<DataPoint[]> {
    if (!fs.existsSync(filePath)) {
      console.warn(`⚠️  文件不存在: ${filePath}`);
      return [];
    }

    console.log(`📂 读取存栏数据: ${filePath}`);
    const content = fs.readFileSync(filePath, 'utf-8');
    const lines = content.trim().split('\n');
    
    if (lines.length < 2) return [];

    const data: DataPoint[] = [];
    // 跳过表头
    for (let i = 1; i < lines.length; i++) {
      const [dateStr, inventoryStr, changeStr] = lines[i].split(',');
      const value = parseFloat(inventoryStr);
      const date = new Date(dateStr);
      
      if (isNaN(value)) continue;

      data.push({
        id: `csv_inv_${dateStr}`,
        source: 'akshare_csv',
        sourceType: 'file',
        timestamp: date.getTime(),
        receivedAt: Date.now(),
        category: 'pig_cycle',
        tags: ['真实数据', 'AKShare', '存栏量'],
        raw: { date: dateStr, inventory: value },
        credibility: { 
          score: 0.95, 
          sourceReliability: 0.95, 
          timeliness: 1.0, 
          crossValidation: { verified: true, conflictingSources: [], consistencyScore: 1.0 }, 
          anomalyFlags: [] 
        },
        normalized: {
          metric: 'pig_inventory',
          value,
          unit: '万头',
          change: { absolute: parseFloat(changeStr) || 0, percentage: 0 }
        }
      });
    }

    console.log(`✅ 加载 ${data.length} 条存栏数据`);
    return data;
  }

  /**
   * 加载猪粮比数据
   */
  private async _loadFeedRatio(filePath: string): Promise<DataPoint[]> {
    if (!fs.existsSync(filePath)) {
      console.warn(`⚠️  文件不存在: ${filePath}`);
      return [];
    }

    console.log(`📂 读取猪粮比数据: ${filePath}`);
    const content = fs.readFileSync(filePath, 'utf-8');
    const lines = content.trim().split('\n');
    
    if (lines.length < 2) return [];

    const data: DataPoint[] = [];
    for (let i = 1; i < lines.length; i++) {
      const [dateStr, ratioStr] = lines[i].split(',');
      const value = parseFloat(ratioStr);
      const date = new Date(dateStr);
      
      if (isNaN(value)) continue;

      data.push({
        id: `csv_ratio_${dateStr}`,
        source: 'akshare_csv',
        sourceType: 'file',
        timestamp: date.getTime(),
        receivedAt: Date.now(),
        category: 'pig_cycle',
        tags: ['真实数据', 'AKShare', '猪粮比'],
        raw: { date: dateStr, ratio: value },
        credibility: { 
          score: 0.95, 
          sourceReliability: 0.95, 
          timeliness: 1.0, 
          crossValidation: { verified: true, conflictingSources: [], consistencyScore: 1.0 }, 
          anomalyFlags: [] 
        },
        normalized: {
          metric: 'pig_feed_ratio',
          value,
          unit: '比值',
          change: { absolute: 0, percentage: 0 }
        }
      });
    }

    console.log(`✅ 加载 ${data.length} 条猪粮比数据`);
    return data;
  }
}
