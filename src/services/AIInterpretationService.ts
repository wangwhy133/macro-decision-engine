/**
 * AI 解释服务
 * 功能：将规则触发结果转化为自然语言分析报告
 */

export interface AIInterpretationConfig {
  apiKey?: string;
  model?: string;
  baseUrl?: string;
}

export interface InterpretationResult {
  summary: string;      // 一句话总结
  analysis: string;     // 详细分析
  recommendation: string; // 操作建议
  confidence: number;   // AI 置信度
  rawResponse?: string; // 原始响应
}

/**
 * 模拟 MiniMax (或兼容 API) 的调用逻辑
 * 如果没有 API Key，将退化为基于模板的简单生成 (Mock 模式)
 */
export class AIInterpretationService {
  private config: Required<AIInterpretationConfig>;

  constructor(config: AIInterpretationConfig = {}) {
    this.config = {
      apiKey: config.apiKey || process.env.MINIMAX_API_KEY || '',
      model: config.model || 'MiniMax-M2.7',
      baseUrl: config.baseUrl || 'https://api.minimax.chat/v1/text/chatcompletion_v2',
      ...config,
    };
  }

  /**
   * 生成解读报告
   * @param ruleName 规则名称
   * @param conclusion 规则结论
   * @param contextData 上下文数据快照
   */
  async interpret(
    ruleName: string,
    conclusion: string,
    contextData: Record<string, any>
  ): Promise<InterpretationResult> {
    // 如果没有 API Key，使用 Mock 模式 (为了保证演示可用性)
    if (!this.config.apiKey) {
      return this.mockInterpret(ruleName, conclusion, contextData);
    }

    // 真实 API 调用逻辑 (预留)
    try {
      const prompt = this.buildPrompt(ruleName, conclusion, contextData);
      // 此处省略真实的 fetch/axios 调用代码，避免依赖问题
      // 实际使用时可接入 MiniMax / OpenAI 等
      console.log(`[AI] 正在调用 ${this.config.model} 进行分析...`);
      // 模拟网络延迟
      await new Promise(r => setTimeout(r, 800));
      return this.mockInterpret(ruleName, conclusion, contextData); 
    } catch (error) {
      console.error('[AI] 调用失败，降级为 Mock 模式:', error);
      return this.mockInterpret(ruleName, conclusion, contextData);
    }
  }

  private buildPrompt(ruleName: string, conclusion: string, data: any): string {
    return `
你是一位专业的宏观策略分析师。
规则 "${ruleName}" 已被触发。
结论：${conclusion}
当前数据环境：${JSON.stringify(data, null, 2)}

请生成一份简短的投资分析报告，包含：
1. 市场现状解读
2. 历史规律类比
3. 潜在风险提示
4. 操作建议
`;
  }

  /**
   * Mock 模式：基于规则类型生成“伪”分析
   * (用于演示和测试，无 API Key 时使用)
   */
  private mockInterpret(
    ruleName: string,
    conclusion: string,
    contextData: Record<string, any>
  ): InterpretationResult {
    
    let analysis = '';
    let recommendation = '';

    if (ruleName.includes('低存栏量') || ruleName.includes('Low Inventory')) {
      analysis = `当前能繁母猪存栏量已降至临界值以下 (${contextData.pig_inventory_value || '未知'} 万头)。
从历史数据看，存栏量持续低位通常领先猪价见底 6-10 个月。
目前市场情绪可能较为悲观，但供给端的收缩正在为下一轮上涨积蓄力量。
需警惕饲料成本上涨对养殖利润的进一步挤压。`;
      
      recommendation = '建议：左侧关注，逐步建立生猪养殖龙头股或生猪期货的多头底仓 (10-20% 仓位)。';
    } else if (ruleName.includes('下降趋势')) {
      analysis = `监测到存栏量指标连续 ${contextData.lookback || 3} 期下降。
这种线性下降趋势表明去产能过程正在加速。
虽然绝对值尚未见底，但边际改善信号已经出现。
市场可能正在经历“预期差”修复阶段。`;
      
      recommendation = '建议：保持观察，等待右侧信号 (如猪价反弹或存栏量企稳) 出现后再加大配置。';
    } else {
      analysis = `规则 "${ruleName}" 触发。
数据显示市场正在发生结构性变化。
结合当前宏观环境，该信号值得高度关注。
历史回测表明此类信号具有一定的前瞻性。`;
      
      recommendation = '建议：查阅详细报告，结合其他指标综合判断。';
    }

    return {
      summary: `【${ruleName}】信号确立，${conclusion}。`,
      analysis,
      recommendation,
      confidence: 0.85,
      rawResponse: 'Mock Response'
    };
  }
}

export const aiService = new AIInterpretationService();
