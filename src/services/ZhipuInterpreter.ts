/**
 * 智谱 AI (Zhipu AI / BigModel) 解释服务
 * 模型：glm-4.7-flash
 * 功能：生成专业的宏观决策报告，量化不确定性
 */

import { InferenceResult } from '../engine/AdvancedRuleEngine';

const ZHIPU_API_KEY = process.env.ZHIPU_API_KEY || '';
const ZHIPU_MODEL = process.env.ZHIPU_MODEL || 'glm-4.7-flash';
const ZHIPU_BASE_URL = process.env.ZHIPU_BASE_URL || 'https://open.bigmodel.cn/api/paas/v4/chat/completions';

export interface AIExplanation {
  summary: string;
  analysis: string;
  riskWarning: string;
  confidenceLevel: '高' | '中' | '低';
  uncertaintyScore: number;
  rawResponse?: string;
}

export class ZhipuInterpreter {
  private apiKey: string;
  private model: string;
  private baseUrl: string;

  constructor() {
    this.apiKey = process.env.ZHIPU_API_KEY || '';
    this.model = process.env.ZHIPU_MODEL || 'glm-4.7-flash';
    this.baseUrl = process.env.ZHIPU_BASE_URL || ZHIPU_BASE_URL;
  }

  /**
   * 生成解释报告
   */
  async explain(result: InferenceResult, marketData: any): Promise<AIExplanation> {
    if (!this.apiKey || this.apiKey.includes('your_key')) {
      console.warn('⚠️  未配置有效的 Zhipu API Key，使用降级报告模式');
      return this._generateFallbackReport(result, marketData);
    }

    try {
      const prompt = this._buildPrompt(result, marketData);
      const response = await this._callZhipu(prompt);
      return this._parseResponse(response, result);
    } catch (error: any) {
      console.error('❌ 智谱 AI 调用失败:', error.message);
      return this._generateFallbackReport(result, marketData);
    }
  }

  /**
   * 构建 Prompt
   */
  private _buildPrompt(result: InferenceResult, marketData: any): string {
    const triggeredRules = result.triggeredRules.map(r => 
      `- **${r.name}**: ${r.description} (置信度: ${r.confidence})`
    ).join('\n') || '- 无特定规则触发';

    return `你是一位拥有 20 年经验的宏观策略分析师，擅长猪周期研究。请根据以下数据生成一份专业、客观的投资决策报告。

## 市场数据
- **能繁母猪存栏量**: ${marketData.inventory ? marketData.inventory.toFixed(1) : '未知'} 万头
- **3 个月变化率**: ${marketData.change3m ? marketData.change3m.toFixed(2) : '未知'}%

## 系统触发的规则信号
${triggeredRules}

## 系统初步结论
- **决策方向**: ${result.finalDecision}
- **综合置信度**: ${(result.confidence * 100).toFixed(1)}%
- **推理逻辑**: ${result.reasoning}

## 输出要求
1. **语气**: 专业、冷静、客观，像券商首席分析师。
2. **结构**: 
   - 【核心观点】一句话总结（30 字内）。
   - 【深度分析】结合存栏量位置和变化率趋势分析（100 字左右）。
   - 【风险提示】指出潜在风险（如政策、疫情、饲料成本）。
3. **JSON 格式**: 必须严格返回 JSON 格式：
   {
     "summary": "核心观点",
     "analysis": "深度分析内容",
     "riskWarning": "风险提示内容"
   }
`;
  }

  /**
   * 调用智谱 API
   */
  private async _callZhipu(prompt: string): Promise<any> {
    const response = await fetch(this.baseUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.apiKey}`
      },
      body: JSON.stringify({
        model: this.model,
        messages: [
          {
            role: 'system',
            content: '你是一位专业的宏观策略分析师，擅长猪周期和大宗商品研究。请根据提供的数据生成客观、专业的分析报告。输出必须为合法的 JSON 格式。'
          },
          {
            role: 'user',
            content: prompt
          }
        ],
        temperature: 0.3, // 低温度，保持客观
        top_p: 0.8
      })
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`API Error: ${response.status} ${response.statusText} - ${errorText}`);
    }

    return await response.json();
  }

  /**
   * 解析响应
   */
  private _parseResponse(response: any, result: InferenceResult): AIExplanation {
    const content = response.choices?.[0]?.message?.content || '';
    
    // 尝试提取 JSON
    let parsed;
    try {
      const jsonMatch = content.match(/\{[\s\S]*\}/);
      const jsonStr = jsonMatch ? jsonMatch[0] : content;
      parsed = JSON.parse(jsonStr);
    } catch {
      // 解析失败则使用原始内容
      parsed = { summary: content, analysis: content, riskWarning: '' };
    }

    return {
      summary: parsed.summary || '暂无核心观点',
      analysis: parsed.analysis || content,
      riskWarning: parsed.riskWarning || '暂无特别风险提示',
      confidenceLevel: result.confidence > 0.8 ? '高' : result.confidence > 0.6 ? '中' : '低',
      uncertaintyScore: parseFloat((1 - result.confidence).toFixed(2)),
      rawResponse: content
    };
  }

  /**
   * 降级报告
   */
  private _generateFallbackReport(result: InferenceResult, marketData: any): AIExplanation {
    const isBuy = result.finalDecision === 'BUY';
    const isSell = result.finalDecision === 'SELL';
    
    return {
      summary: `系统建议：**${result.finalDecision}**。当前触发了 ${result.triggeredRules.length} 条规则信号。`,
      analysis: `当前存栏量 ${marketData.inventory ? marketData.inventory.toFixed(1) : '未知'} 万头。${result.reasoning}。`,
      riskWarning: result.confidence < 0.7 ? '⚠️ 置信度较低，建议结合多方信息综合判断。' : '宏观环境相对稳定，关注突发政策变化。',
      confidenceLevel: result.confidence > 0.8 ? '高' : result.confidence > 0.6 ? '中' : '低',
      uncertaintyScore: 1 - result.confidence
    };
  }
}
