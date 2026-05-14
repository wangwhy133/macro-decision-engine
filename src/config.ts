/**
 * 系统配置
 * 支持环境变量覆盖
 */

export interface AppConfig {
  // 数据库
  dbPath: string;
  
  // 数据源
  dataSource: 'simulator' | 'tushare' | 'akshare';
  tushareToken: string;
  
  // AI 配置
  aiProvider: 'minimax' | 'openai' | 'mock';
  aiApiKey: string;
  aiModel: string;
  
  // 规则配置
  defaultRulePriority: number;
  
  // 调试
  debug: boolean;
}

// 从环境变量读取配置，如果没有则使用默认值
export const config: AppConfig = {
  dbPath: process.env.MDE_DB_PATH || './macro-decision.db',
  
  dataSource: (process.env.MDE_DATA_SOURCE as any) || 'simulator',
  tushareToken: process.env.TUSHARE_TOKEN || 'your_tushare_token_here',
  
  aiProvider: (process.env.MDE_AI_PROVIDER as any) || 'mock',
  aiApiKey: process.env.MDE_AI_API_KEY || '',
  aiModel: process.env.MDE_AI_MODEL || 'MiniMax-M2.7',
  
  defaultRulePriority: 5,
  
  debug: process.env.MDE_DEBUG === 'true',
};

export function validateConfig(): void {
  if (config.dataSource === 'tushare' && config.tushareToken === 'your_tushare_token_here') {
    console.warn('⚠️  警告：数据源配置为 Tushare 但未设置 Token。请设置环境变量 TUSHARE_TOKEN。');
  }
  if (config.aiProvider === 'minimax' && !config.aiApiKey) {
    console.warn('⚠️  警告：AI 提供商配置为 MiniMax 但未设置 API Key。将降级为 Mock 模式。');
  }
}
