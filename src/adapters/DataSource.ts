/**
 * 数据源适配器接口
 * 用于接入真实世界数据 (如 Tushare, AkShare, Wind 等)
 */

export interface MacroDataPoint {
  timestamp: number;
  metric: string;
  value: number;
  unit: string;
  change?: number;
  changePct?: number;
  raw?: any;
}

export interface DataSource {
  name: string;
  connect(): Promise<void>;
  fetchData(metric: string, startDate: number, endDate: number): Promise<MacroDataPoint[]>;
}

/**
 * 模拟 Tushare 适配器
 * 实际使用时，替换为真实的 API 调用逻辑
 */
export class MockTushareAdapter implements DataSource {
  name = 'Tushare (Mock)';
  private token: string;

  constructor(token: string) {
    this.token = token;
  }

  async connect(): Promise<void> {
    console.log(`[Tushare] 正在连接 (Token: ${this.token.substring(0, 4)}...)`);
    // 真实场景：验证 Token 有效性
    await new Promise(r => setTimeout(r, 500));
    console.log('[Tushare] 连接成功');
  }

  async fetchData(metric: string, startDate: number, endDate: number): Promise<MacroDataPoint[]> {
    console.log(`[Tushare] 获取数据：${metric} (${new Date(startDate).toLocaleDateString()} - ${new Date(endDate).toLocaleDateString()})`);
    
    // 模拟返回过去 12 个月的数据
    const result: MacroDataPoint[] = [];
    const now = Date.now();
    const oneMonth = 30 * 24 * 60 * 60 * 1000;
    
    for (let i = 12; i >= 0; i--) {
      const ts = now - i * oneMonth;
      // 模拟数据：基础值 + 周期波动
      const base = metric === 'pig_inventory' ? 4500 : 18.0;
      const cycle = Math.sin((12 - i) * 0.5) * (metric === 'pig_inventory' ? 200 : 3);
      const noise = (Math.random() - 0.5) * 50;
      
      result.push({
        timestamp: ts,
        metric,
        value: base + cycle + noise,
        unit: metric === 'pig_inventory' ? '万头' : '元/公斤',
        raw: { source: 'tushare_mock' }
      });
    }
    
    // 计算变化率
    for (let i = 1; i < result.length; i++) {
      const prev = result[i-1].value;
      const curr = result[i].value;
      result[i].change = curr - prev;
      result[i].changePct = (curr - prev) / prev;
    }

    return result;
  }
}
