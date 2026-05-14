/**
 * MiniMax AI 解释服务
 * 功能：基于 MiniMax-M2.7 生成自然语言决策报告，量化不确定性
 */

import { InferenceResult } from '../engine/AdvancedRuleEngine';

const MINIMAX_API_KEY = process.env.MINIMAX_API_KEY || '';
const MINIMAX_MODEL = process.env.MINIMAX_MODEL || 'MiniMax-M2.7'; // 或实际模型 ID
const MINIMAX_URL = 'https://api.minimax.chat/v1/text/chatcompletion_v2'; // 示例 URL，需根据实际文档调整

export interface AIExplanation {
  summary: string; // 一句话总结
  analysis: string; // 详细分析
  riskWarning: string; // 风险提示
  confidenceLevel: '高' | '中' | '低';
  uncertaintyScore: number; // 0-1, 越高越不确定
  rawResponse?: string;
}

export class MiniMaxInterpreter {
  private apiKey: string;
  private model: string;

  constructor() {
    this.apiKey = process.env.MINIMAX_API_KEY || '';
    this.model = process.env.MINIMAX_MODEL || 'MiniMax-M2.7';
  }

  /**
   * 生成解释报告
   */
  async explain(result: InferenceResult, marketData: any): Promise<AIExplanation> {
    // 如果没有配置 API Key，返回降级报告
    if (!this.apiKey) {
      return this._generateFallbackReport(result, marketData);
    }

    try {
      const prompt = this._buildPrompt(result, marketData);
      const response = await this._callMiniMax(prompt);
      return this._parseResponse(response, result);
    } catch (error: any) {
      console.error('AI 解释生成失败:', error.message);
      return this._generateFallbackReport(result, marketData);
    }
  }

  /**
   * 构建 Prompt
   */
  private _buildPrompt(result: InferenceResult, marketData: any): string {
    const triggeredRules = result.triggeredRules.map(r => 
      `- ${r.name} (置信度: ${r.confidence}, 描述: ${r.description})`
    ).join('\n');

    return `
你是一位专业的宏观策略分析师。请根据以下市场数据和触发的规则，生成一份专业的投资决策报告。

【市场数据】
- 能繁母猪存栏量: ${marketData.inventory || '未知'} 万头
- 3 个月变化率: ${marketData.change3m || '未知'}%

【触发的规则】
${triggeredRules || '无'}

【系统初步决策】
- 方向: ${result.finalDecision}
- 综合置信度: ${result.confidence.toFixed(2)}
- 推理逻辑: ${result.reasoning}

【要求】
1. 用专业、冷静的语气撰写。
2. 包含：市场现状分析、触发逻辑解读、潜在风险提示。
3. 如果置信度低于 0.7，必须强调“需结合其他指标综合判断”。
4. 输出格式为 JSON: { "summary": "...", "analysis": "...", "riskWarning": "..." }
`;
  }

  /**
   * 调用 MiniMax API
   */
  private async _callMiniMax(prompt: string): Promise<any> {
    // 注意：此处需根据 MiniMax 实际 API 文档调整
    // 以下为模拟调用逻辑，实际使用请替换为真实 fetch 请求
    /*
    const res = await fetch(MINIMAX_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.apiKey}`
      },
      body: JSON.stringify({
        model: this.model,
        messages: [{ role: 'user', content: prompt }]
      })
    });
    return await res.json();
    */
    
    // 模拟返回 (开发环境)
    return {
      choices: [{
        message: {
          content: JSON.stringify({
            summary: `当前市场处于${result.finalDecision === 'BUY' ? '底部布局' : result.finalDecision === 'SELL' ? '顶部风险' : '震荡观望'}区域。`,
            analysis: `系统检测到${result.triggeredRules.length}个关键信号。${result.reasoning}。建议关注行业产能去化进度。`,
            riskWarning: result.confidence < 0.7 ? '置信度较低，需结合生猪价格、饲料成本等多维度数据交叉验证。' : '宏观环境相对稳定，但仍需警惕突发政策风险。'
          })
        }
      }]
    };
  }

  /**
   * 解析 AI 响应
   */
  private _parseResponse(response: any, result: InferenceResult): AIExplanation {
    const content = response.choices?.[0]?.message?.content || '{}';
    let parsed;
    try {
      // 尝试提取 JSON
      const jsonMatch = content.match(/\{[\s\S]*\}/);
      parsed = jsonMatch ? JSON.parse(jsonMatch[0]) : JSON.parse(content);
    } catch {
      parsed = { summary: content, analysis: content, riskWarning: '' };
    }

    return {
      summary: parsed.summary || '无摘要',
      analysis: parsed.analysis || '无详细分析',
      riskWarning: parsed.riskWarning || '无明显风险',
      confidenceLevel: result.confidence > 0.8 ? '高' : result.confidence > 0.6 ? '中' : '低',
      uncertaintyScore: 1 - result.confidence,
      rawResponse: content
    };
  }

  /**
   * 降级报告 (无 API Key 时)
   */
  private _generateFallbackReport(result: InferenceResult, marketData: any): AIExplanation {
    const isBuy = result.finalDecision === 'BUY';
    const isSell = result.finalDecision === 'SELL';
    
    return {
      summary: `系统建议：${result.finalDecision}。触发 ${result.triggeredRules.length} 条规则。`,
      analysis: `当前存栏量 ${marketData.inventory || '未知'} 万头。${result.reasoning}。`,
      riskWarning: result.confidence < 0.7 ? '置信度较低，建议谨慎操作。' : '风险可控。',
      confidenceLevel: result.confidence > 0.8 ? '高' : result.confidence > 0.6 ? '中' : '低',
      uncertaintyScore: 1 - result.confidence
    };
  }
}
