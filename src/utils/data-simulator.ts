/**
 * 高保真宏观数据模拟器
 * 模拟真实的猪周期：包含长期趋势、季节性波动、随机噪声和突发冲击
 */

export interface SimulatedDataPoint {
  timestamp: number;
  inventory: number; // 存栏量
  price: number;     // 猪价
  profit: number;    // 养殖利润
  feedCost: number;  // 饲料成本
}

/**
 * 生成过去 N 个月的模拟数据
 * @param months 月数
 * @param includeShock 是否包含突发冲击 (如猪瘟)
 */
export function generateRealisticData(months: number = 60, includeShock: boolean = true): SimulatedDataPoint[] {
  const data: SimulatedDataPoint[] = [];
  const now = Date.now();
  const oneMonth = 30 * 24 * 60 * 60 * 1000;
  
  // 猪周期参数 (约 40 个月一轮)
  const cycleLength = 40;
  const baseInventory = 4500;
  const amplitude = 400;
  
  // 价格与存栏的反向关系系数
  const priceSensitivity = 0.015;
  const basePrice = 18.0;
  
  // 饲料成本趋势 (缓慢上涨)
  const baseFeedCost = 3.5;
  
  for (let i = months; i >= 0; i--) {
    const timestamp = now - i * oneMonth;
    
    // 1. 长期趋势 (正弦波模拟周期)
    const cyclePhase = (i * 2 * Math.PI) / cycleLength;
    const trendInv = baseInventory + amplitude * Math.sin(cyclePhase);
    
    // 2. 季节性波动 (春节前后需求大，夏季淡季)
    const monthOfYear = (new Date(timestamp).getMonth() + 1);
    const seasonalFactor = 1.0 + 0.05 * Math.sin((monthOfYear - 3) * Math.PI / 6); // 峰值在春节前后
    
    // 3. 随机噪声
    const noiseInv = (Math.random() - 0.5) * 50;
    const noisePrice = (Math.random() - 0.5) * 2;
    
    // 4. 突发冲击 (如 2019 猪瘟，2020 疫情)
    let shockInv = 0;
    let shockPrice = 0;
    if (includeShock) {
      // 模拟第 10 个月发生猪瘟 (存栏大减，价格大涨)
      if (i >= 10 && i <= 15) {
        shockInv = -300; 
        shockPrice = 5.0;
      }
      // 模拟第 45 个月发生饲料危机
      if (i >= 45 && i <= 48) {
        shockInv = -100;
        shockPrice = 2.0;
      }
    }

    const inventory = trendInv * seasonalFactor + noiseInv + shockInv;
    
    // 价格由供需决定：存栏越少价格越高，叠加冲击
    const price = basePrice - (inventory - baseInventory) * priceSensitivity + noisePrice + shockPrice;
    
    // 养殖利润 = 价格 - 成本 (简化)
    const feedCost = baseFeedCost + (i * 0.01); // 成本缓慢上升
    const profit = price - feedCost * 10; // 简化公式

    data.push({
      timestamp,
      inventory,
      price,
      profit,
      feedCost
    });
  }
  
  return data;
}

/**
 * 将模拟数据转换为数据库可接受的格式
 */
export function toDataPoints(simData: SimulatedDataPoint[]) {
  return simData.map((d, idx) => {
    const prevInv = idx < simData.length - 1 ? simData[idx + 1].inventory : d.inventory;
    const change = d.inventory - prevInv;
    const changePct = prevInv !== 0 ? change / prevInv : 0;

    return {
      id: `sim_inv_${d.timestamp}`,
      source_id: 'simulator',
      category: 'pig_cycle',
      metric: 'pig_inventory',
      value: d.inventory, // 确保这是数字
      unit: '万头',
      change_value: change,
      change_pct: changePct,
      period: '月度',
      timestamp: Math.floor(d.timestamp / 1000),
      tags: JSON.stringify(['模拟数据', '猪周期']),
      raw_data: JSON.stringify(d), // 包含完整信息
      credibility_score: 0.95
    };
  });
}
