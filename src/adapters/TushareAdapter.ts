/**
 * Tushare 数据适配器 - 获取真实能繁母猪存栏量数据
 * 
 * 使用步骤:
 * 1. 注册 Tushare (tushare.pro) 获取 Token
 * 2. 将 Token 填入环境变量 TUSHARE_TOKEN 或 .env 文件
 * 3. 调用 loadData() 即可获取真实数据
 * 
 * 注意：目前 Tushare 免费接口可能不包含直接的猪存栏数据，
 * 此适配器实现了标准的 Tushare 调用流程，并提供了模拟数据作为降级方案。
 * 如果未来获取到真实的猪周期数据接口，只需修改 api_name 和 params。
 */

import { DataPoint } from '../types';

const TUSHARE_TOKEN = process.env.TUSHARE_TOKEN || '';
const TUSHARE_URL = 'http://api.tushare.pro';

// 定义 Tushare API 请求结构
interface TushareRequest {
  api_name: string;
  token: string;
  params: Record<string, any>;
  fields?: string;
}

// 定义 Tushare API 响应结构
interface TushareResponse {
  ret_code: number;
  ret_msg: string;
  data?: {
    fields: string[];
    values: any[][];
  };
}

export class TushareAdapter {
  private token: string;

  constructor(token?: string) {
    this.token = token || TUSHARE_TOKEN;
  }

  /**
   * 加载真实数据
   * @param months 需要获取的历史月份数量
   */
  async loadData(months: number = 60): Promise<DataPoint[]> {
    if (!this.token) {
      console.warn('⚠️  未配置 TUSHARE_TOKEN，返回模拟数据');
      return this._getMockData(months);
    }

    try {
      console.log('📡 正在从 Tushare 获取真实数据...');
      
      // 尝试获取猪周期相关数据
      // 注意：Tushare 免费接口可能不直接提供猪存栏数据，这里演示标准调用流程
      // 实际使用时需确认具体接口名，如 "pig_inventory", "livestock_pig" 等
      const data = await this._fetchFromTushare('pig_inventory', {
        start_date: new Date(Date.now() - months * 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        end_date: new Date().toISOString().split('T')[0]
      });

      if (data && data.values && data.values.length > 0) {
        console.log(`✅ 成功获取 ${data.values.length} 条真实数据`);
        return this._transformData(data);
      } else {
        console.warn('⚠️  Tushare 未返回有效数据，切换至模拟数据模式');
        return this._getMockData(months);
      }
    } catch (error: any) {
      console.error('❌ Tushare 调用失败:', error.message);
      console.warn('⚠️  切换至模拟数据模式');
      return this._getMockData(months);
    }
  }

  /**
   * 从 Tushare 获取数据
   */
  private async _fetchFromTushare(apiName: string, params: Record<string, any>): Promise<any> {
    if (!this.token) {
      throw new Error('缺少 TUSHARE_TOKEN');
    }

    const requestBody: TushareRequest = {
      api_name: apiName,
      token: this.token,
      params: params,
      fields: 'trade_date,inventory' // 假设接口返回这些字段
    };

    const response = await fetch(TUSHARE_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody)
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const result: TushareResponse = await response.json();
    
    if (result.ret_code !== 0) {
      throw new Error(`Tushare API error: ${result.ret_msg}`);
    }

    return result.data;
  }

  /**
   * 将 Tushare 原始数据转换为标准 DataPoint 格式
   */
  private _transformData(rawData: any): DataPoint[] {
    // 假设 fields 为 ['trade_date', 'inventory']
    return rawData.values.map((item: any[], index: number) => {
      const dateStr = item[0]; // 假设第一列是日期
      const inventory = parseFloat(item[1]); // 假设第二列是存栏量
      
      // 解析日期
      const dateMatch = dateStr.toString().match(/(\d{4})(\d{2})(\d{2})/);
      const year = dateMatch ? parseInt(dateMatch[1]) : 2020;
      const month = dateMatch ? parseInt(dateMatch[2]) : 1;
      const day = dateMatch ? parseInt(dateMatch[3]) : 1;
      
      const timestamp = new Date(year, month - 1, day).getTime();

      return {
        id: `tushare_${index}`,
        source: 'tushare',
        sourceType: 'api',
        timestamp: timestamp,
        receivedAt: Date.now(),
        category: 'pig_cycle',
        tags: ['真实数据', 'Tushare'],
        raw: { trade_date: dateStr, inventory },
        credibility: { 
          score: 0.95, 
          sourceReliability: 0.95, 
          timeliness: 1.0, 
          crossValidation: { verified: true, conflictingSources: [], consistencyScore: 1.0 }, 
          anomalyFlags: [] 
        },
        normalized: {
          metric: 'pig_inventory',
          value: inventory,
          unit: '万头',
          change: { absolute: 0, percentage: 0 }
        }
      };
    });
  }

  /**
   * 模拟数据 (用于开发测试或 API 不可用时降级)
   */
  private _getMockData(months: number): DataPoint[] {
    const data: DataPoint[] = [];
    const now = Date.now();
    const oneMonth = 30 * 24 * 60 * 60 * 1000;
    let baseValue = 4500;

    console.log(`📊 生成 ${months} 个月的模拟数据...`);

    for (let i = months; i >= 0; i--) {
      const trend = Math.sin(i * 0.15) * 200; // 周期波动
      const noise = (Math.random() - 0.5) * 50;
      const value = baseValue + trend + noise;
      
      // 计算变化率
      const prevValue = i < months ? data[data.length - 1].normalized.value as number : value;
      const change = value - prevValue;
      const changePct = prevValue !== 0 ? (change / prevValue) * 100 : 0;

      data.push({
        id: `mock_${i}`,
        source: 'mock',
        sourceType: 'simulated',
        timestamp: now - i * oneMonth,
        receivedAt: Date.now(),
        category: 'pig_cycle',
        tags: ['模拟数据'],
        raw: { value, trend, noise },
        credibility: { 
          score: 0.8, 
          sourceReliability: 0.8, 
          timeliness: 1.0, 
          crossValidation: { verified: false, conflictingSources: [], consistencyScore: 1.0 }, 
          anomalyFlags: [] 
        },
        normalized: {
          metric: 'pig_inventory',
          value,
          unit: '万头',
          change: { absolute: change, percentage: changePct }
        }
      });
    }
    return data;
  }
}
