/**
 * 宏观决策支持引擎
 * 
 * 数据可信度系统 + 规则推理系统 + AI 解释层 + 复盘校准系统
 */

import { DataCredibilityService } from './services/DataCredibilityService';
import { RuleEvaluator } from './engine/RuleEvaluator';
import { parseRule, parseRules } from './parser/parser';
import { tokenize } from './parser/tokens';

// 导出核心服务
export { DataCredibilityService } from './services/DataCredibilityService';
export { RuleEvaluator } from './engine/RuleEvaluator';

// 导出解析器
export { parseRule, parseRules, tokenize } from './parser/parser';

// 导出类型
export * from './types';
export * from './parser/ast';

/**
 * 版本信息
 */
export const VERSION = '1.0.0';

/**
 * 创建引擎实例
 */
export function createEngine() {
  const dataService = new DataCredibilityService();
  const ruleEvaluator = new RuleEvaluator();

  return {
    dataService,
    ruleEvaluator,
    
    /**
     * 接入数据并评估规则
     */
    async ingestAndEvaluate(rawData: any[], rules: any[]) {
      // 1. 接入数据
      const dataPoints = await dataService.ingestBatch(rawData);
      
      // 2. 设置数据上下文
      ruleEvaluator.setDataContext(dataPoints);
      
      // 3. 评估规则
      const result = ruleEvaluator.evaluateBatch(rules);
      
      return {
        dataPoints,
        ...result,
      };
    },
  };
}

// CLI 入口
if (typeof process !== 'undefined' && process.argv) {
  const args = process.argv.slice(2);
  
  if (args[0] === '--version' || args[0] === '-v') {
    console.log(`宏观决策支持引擎 v${VERSION}`);
    process.exit(0);
  }

  if (args[0] === '--help' || args[0] === '-h') {
    console.log(`
宏观决策支持引擎 v${VERSION}

用法:
  macro-decision-engine [选项]

选项:
  -v, --version     显示版本号
  -h, --help        显示帮助信息
  --parse <file>    解析规则文件
  --test            运行测试

示例:
  macro-decision-engine --parse rules/pig_cycle.rules
`);
    process.exit(0);
  }

  if (args[0] === '--parse' && args[1]) {
    const fs = require('fs');
    const path = require('path');
    
    try {
      const filePath = path.resolve(args[1]);
      const content = fs.readFileSync(filePath, 'utf-8');
      const rules = parseRules(content);
      
      console.log(`成功解析 ${rules.length} 条规则:`);
      rules.forEach((rule, i) => {
        console.log(`  ${i + 1}. ${rule.name} (${rule.id})`);
        console.log(`     类型：${rule.ruleType}`);
        console.log(`     类别：${rule.category}`);
        console.log(`     优先级：${rule.priority}`);
        console.log(`     结论：${rule.inference.conclusion}`);
        console.log(`     置信度：${rule.inference.confidence}`);
        console.log('');
      });
    } catch (error) {
      console.error('解析失败:', error);
      process.exit(1);
    }
  }
}

export default createEngine;
