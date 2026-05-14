/**
 * 宏观决策支持引擎 - 服务接口定义
 * 定义各层核心服务的契约
 */

import {
  DataPoint,
  RawDataPoint,
  CredibilityContext,
  CredibilityMetrics,
  DataFilters,
  AnomalyReport,
  ValidationResult,
  Rule,
  RuleFilters,
  RuleEvaluationResult,
  ConditionAST,
  ReasoningChain,
  AIInterpretation,
  InterpretationContext,
  UncertaintyQuantification,
  Scenario,
  ReviewRecord,
  OutcomeData,
  ErrorAnalysis,
  CalibrationConfig,
  CalibrationResult,
  ReviewReport,
  RuleChangeSuggestion,
} from '../types';

// ==================== 数据可信度系统 ====================

/**
 * 数据可信度服务接口
 * 负责数据接入、可信度评分、交叉验证、异常检测
 */
export interface DataCredibilityService {
  /**
   * 接入单个数据点
   * @param data 原始数据
   * @returns 处理后的数据点 (含可信度评分)
   */
  ingest(data: RawDataPoint): Promise<DataPoint>;

  /**
   * 批量接入数据
   * @param data 原始数据数组
   * @returns 处理后的数据点数组
   */
  ingestBatch(data: RawDataPoint[]): Promise<DataPoint[]>;

  /**
   * 计算可信度分数
   * @param dataPoint 数据点
   * @param context 计算上下文
   * @returns 可信度指标
   */
  calculateCredibility(
    dataPoint: DataPoint,
    context: CredibilityContext
  ): Promise<CredibilityMetrics>;

  /**
   * 交叉验证
   * @param dataPoints 数据点数组
   * @param metric 要验证的指标
   * @returns 验证结果
   */
  crossValidate(
    dataPoints: DataPoint[],
    metric: string
  ): Promise<ValidationResult>;

  /**
   * 异常检测
   * @param dataPoints 数据点数组
   * @param threshold 异常阈值 (可选)
   * @returns 异常报告
   */
  detectAnomalies(
    dataPoints: DataPoint[],
    threshold?: number
  ): Promise<AnomalyReport>;

  /**
   * 查询数据
   * @param filters 过滤条件
   * @returns 数据点数组
   */
  query(filters: DataFilters): Promise<DataPoint[]>;

  /**
   * 按标签查询
   * @param tags 标签数组
   * @returns 数据点数组
   */
  getByTags(tags: string[]): Promise<DataPoint[]>;

  /**
   * 按ID获取数据点
   * @param id 数据点ID
   * @returns 数据点或null
   */
  getById(id: string): Promise<DataPoint | null>;

  /**
   * 更新可信度指标
   * @param id 数据点ID
   * @param credibility 新的可信度指标
   */
  updateCredibility(id: string, credibility: CredibilityMetrics): Promise<void>;
}

// ==================== 规则推理系统 ====================

/**
 * 规则引擎接口
 * 负责规则管理、条件评估、推理执行
 */
export interface RuleEngine {
  /**
   * 添加规则
   * @param rule 规则定义
   */
  addRule(rule: Rule): Promise<void>;

  /**
   * 删除规则
   * @param ruleId 规则ID
   */
  removeRule(ruleId: string): Promise<void>;

  /**
   * 更新规则
   * @param ruleId 规则ID
   * @param updates 更新内容
   */
  updateRule(ruleId: string, updates: Partial<Rule>): Promise<void>;

  /**
   * 获取规则
   * @param filters 过滤条件
   * @returns 规则数组
   */
  getRules(filters?: RuleFilters): Promise<Rule[]>;

  /**
   * 按ID获取规则
   * @param ruleId 规则ID
   * @returns 规则或null
   */
  getRuleById(ruleId: string): Promise<Rule | null>;

  /**
   * 评估规则
   * @param data 数据点数组
   * @param ruleIds 规则ID列表 (可选，为空则评估所有激活规则)
   * @returns 评估结果
   */
  evaluate(
    data: DataPoint[],
    ruleIds?: string[]
  ): Promise<RuleEvaluationResult>;

  /**
   * 验证规则
   * @param rule 规则定义
   * @returns 验证结果
   */
  validateRule(rule: Rule): Promise<any>;

  /**
   * 解析条件表达式
   * @param expression DSL表达式
   * @returns 条件AST
   */
  parseCondition(expression: string): Promise<ConditionAST>;

  /**
   * 评估条件
   * @param ast 条件AST
   * @param context 变量上下文
   * @returns 条件真假
   */
  evaluateCondition(
    ast: ConditionAST,
    context: Record<string, any>
  ): Promise<boolean>;

  /**
   * 激活规则
   * @param ruleId 规则ID
   */
  activateRule(ruleId: string): Promise<void>;

  /**
   * 停用规则
   * @param ruleId 规则ID
   */
  deactivateRule(ruleId: string): Promise<void>;

  /**
   * 导入规则 (从JSON或DSL文件)
   * @param content 规则内容
   * @param format 格式 ('json' | 'dsl')
   */
  importRules(content: string, format: 'json' | 'dsl'): Promise<Rule[]>;

  /**
   * 导出规则
   * @param ruleIds 规则ID列表
   * @param format 导出格式
   * @returns 导出的内容
   */
  exportRules(ruleIds: string[], format: 'json' | 'dsl'): Promise<string>;
}

// ==================== AI解释层 ====================

/**
 * AI解释服务接口
 * 负责语义理解、情景生成、可解释性输出
 */
export interface AIInterpretationService {
  /**
   * 解释推理链
   * @param chain 推理链
   * @param context 解释上下文
   * @returns AI解释结果
   */
  interpret(
    chain: ReasoningChain,
    context: InterpretationContext
  ): Promise<AIInterpretation>;

  /**
   * 生成多种情景
   * @param data 数据点
   * @param rules 触发的规则
   * @returns 情景数组
   */
  generateScenarios(
    data: DataPoint[],
    rules: Rule[]
  ): Promise<Scenario[]>;

  /**
   * 生成可解释性输出
   * @param chain 推理链
   * @param audience 目标受众
   * @returns 解释文本
   */
  generateExplanation(
    chain: ReasoningChain,
    audience: 'expert' | 'layman' | 'executive'
  ): Promise<string>;

  /**
   * 量化不确定性
   * @param chain 推理链
   * @returns 不确定性量化结果
   */
  quantifyUncertainty(
    chain: ReasoningChain
  ): Promise<UncertaintyQuantification>;

  /**
   * 生成决策建议
   * @param chain 推理链
   * @param scenarios 情景数组
   * @returns 决策建议文本
   */
  generateRecommendation(
    chain: ReasoningChain,
    scenarios: Scenario[]
  ): Promise<string>;

  /**
   * 识别关键因素
   * @param data 数据点
   * @param rules 规则
   * @returns 关键因素列表
   */
  identifyKeyFactors(
    data: DataPoint[],
    rules: Rule[]
  ): Promise<string[]>;

  /**
   * 生成摘要
   * @param chain 推理链
   * @param maxLength 最大长度
   * @returns 摘要文本
   */
  summarize(chain: ReasoningChain, maxLength?: number): Promise<string>;
}

// ==================== 复盘校准系统 ====================

/**
 * 复盘校准服务接口
 * 负责记录、分析、校准
 */
export interface ReviewCalibrationService {
  /**
   * 记录预测
   * @param chain 推理链
   */
  recordPrediction(chain: ReasoningChain): Promise<void>;

  /**
   * 记录结果
   * @param predictionId 预测ID
   * @param outcome 实际结果数据
   */
  recordOutcome(
    predictionId: string,
    outcome: OutcomeData
  ): Promise<void>;

  /**
   * 分析误差
   * @param predictionId 预测ID
   * @returns 误差分析
   */
  analyzeError(predictionId: string): Promise<ErrorAnalysis>;

  /**
   * 自动校准
   * @param reviewRecords 复盘记录
   * @param config 校准配置
   * @returns 校准结果
   */
  autoCalibrate(
    reviewRecords: ReviewRecord[],
    config: CalibrationConfig
  ): Promise<CalibrationResult>;

  /**
   * 生成报告
   * @param period 时间范围
   * @param format 报告格式
   * @returns 复盘报告
   */
  generateReport(
    period: { start: number; end: number },
    format: 'summary' | 'detailed'
  ): Promise<ReviewReport>;

  /**
   * 建议规则变更
   * @param reviewRecords 复盘记录
   * @returns 规则变更建议
   */
  suggestRuleChanges(
    reviewRecords: ReviewRecord[]
  ): Promise<RuleChangeSuggestion[]>;

  /**
   * 获取复盘记录
   * @param predictionId 预测ID
   * @returns 复盘记录或null
   */
  getReviewRecord(predictionId: string): Promise<ReviewRecord | null>;

  /**
   * 查询复盘记录
   * @param filters 过滤条件
   * @returns 复盘记录数组
   */
  queryRecords(filters: {
    timeRange?: { start: number; end: number };
    errorType?: string;
    severity?: string;
  }): Promise<ReviewRecord[]>;

  /**
   * 标记为已校准
   * @param predictionId 预测ID
   * @param calibration 校准动作
   */
  markCalibrated(
    predictionId: string,
    calibration: any
  ): Promise<void>;
}

// ==================== 编排服务 ====================

/**
 * 决策编排服务接口
 * 负责协调四层系统完成完整决策流程
 */
export interface DecisionOrchestrator {
  /**
   * 执行完整决策流程
   * @param query 用户查询
   * @param options 选项
   * @returns 推理链
   */
  execute(
    query: string,
    options?: DecisionOptions
  ): Promise<ReasoningChain>;

  /**
   * 刷新数据
   * @param sources 数据源列表
   */
  refreshData(sources?: string[]): Promise<void>;

  /**
   * 获取系统状态
   */
  getStatus(): Promise<SystemStatus>;
}

/**
 * 决策选项
 */
export interface DecisionOptions {
  includeScenarios?: boolean;
  audience?: 'expert' | 'layman' | 'executive';
  maxDataAge?: number;  // 最大数据年龄 (小时)
  minCredibility?: number;
}

/**
 * 系统状态
 */
export interface SystemStatus {
  data: {
    totalPoints: number;
    lastUpdate: number;
    sources: string[];
  };
  rules: {
    total: number;
    active: number;
    deprecated: number;
  };
  predictions: {
    total: number;
    pending: number;
    accuracy: number;
  };
}

// ==================== 辅助类型 ====================

/**
 * 实际结果数据
 */
export interface OutcomeData {
  outcome: string;
  occurred: boolean;
  deviation: number;
  timestamp: number;
  source?: string;
}
