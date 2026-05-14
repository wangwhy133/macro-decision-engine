/**
 * 宏观决策支持引擎 - 核心类型定义
 * Version: v1.0.0
 */

// ==================== 基础类型 ====================

/** 数据源类型 */
export type DataSourceType = 'official' | 'financial' | 'news' | 'social';

/** 影响方向 */
export type ImpactType = 'positive' | 'negative' | 'neutral';

/** 时间范围 */
export type TimeHorizon = 'short' | 'medium' | 'long';

/** 规则状态 */
export type RuleStatus = 'active' | 'deprecated' | 'testing';

/** 规则来源 */
export type RuleSource = 'expert' | 'mined' | 'learned';

/** 误差类型 */
export type ErrorType = 'data_error' | 'rule_flaw' | 'ai_misjudgment' | 'black_swan';

/** 误差严重程度 */
export type ErrorSeverity = 'low' | 'medium' | 'high';

// ==================== 数据可信度系统类型 ====================

/** 原始数据点 */
export interface RawDataPoint {
  source: string;
  sourceType: DataSourceType;
  timestamp: number;
  category: string;
  data: Record<string, any>;
  tags?: string[];
}

/** 标准化后的数据点 */
export interface DataPoint {
  id: string;
  source: string;
  sourceType: DataSourceType;
  timestamp: number;
  receivedAt: number;
  category: string;
  tags: string[];
  
  // 原始数据
  raw: Record<string, any>;
  
  // 可信度指标
  credibility: CredibilityMetrics;
  
  // 标准化后的值
  normalized: NormalizedValue;
}

/** 可信度指标 */
export interface CredibilityMetrics {
  score: number;               // 0-1 综合可信度
  sourceReliability: number;   // 来源可靠性 (静态配置)
  timeliness: number;          // 时效性 (0-1, 时间衰减计算)
  crossValidation: CrossValidationResult;
  anomalyFlags: string[];      // 异常标记
}

/** 交叉验证结果 */
export interface CrossValidationResult {
  verified: boolean;
  conflictingSources: string[];
  consistencyScore: number;    // 0-1
}

/** 标准化值 */
export interface NormalizedValue {
  metric: string;              // 指标名称
  value: number | string;
  unit: string;
  change?: {
    absolute: number;
    percentage: number;
    period: string;
  };
}

/** 可信度计算上下文 */
export interface CredibilityContext {
  currentTime: number;
  knownSources: Map<string, SourceReliability>;
  timeDecayHalfLife: number;   // 时间衰减半衰期 (小时)
}

/** 来源可靠性配置 */
export interface SourceReliability {
  baseScore: number;
  category: DataSourceType;
  historicalAccuracy?: number;
}

// ==================== 规则推理系统类型 ====================

/** 规则类型 */
export type RuleType = 'threshold' | 'trend' | 'correlation' | 'pattern' | 'composite';

/** 规则定义 */
export interface Rule {
  id: string;
  name: string;
  description: string;
  type: RuleType;
  condition: string;           // DSL表达式
  inference: Inference;
  metadata: RuleMetadata;
  status: RuleStatus;
}

/** 规则推理结果 */
export interface Inference {
  conclusion: string;
  confidence: number;          // 0-1
  impact: ImpactType;
  timeHorizon: TimeHorizon;
}

/** 规则元数据 */
export interface RuleMetadata {
  createdAt: number;
  updatedAt: number;
  source: RuleSource;
  validationCount: number;
  successRate: number;
  priority: number;
}

/** 规则执行结果 */
export interface RuleExecution {
  ruleId: string;
  ruleName: string;
  triggered: boolean;
  conditionResult: boolean;
  variables: Record<string, any>;
}

/** 规则评估结果 */
export interface RuleEvaluationResult {
  triggeredRules: RuleExecution[];
  conclusions: Conclusion[];
  overallConfidence: number;
}

/** 结论 */
export interface Conclusion {
  ruleId: string;
  conclusion: string;
  confidence: number;
  impact: ImpactType;
  timeHorizon: TimeHorizon;
}

// ==================== 推理链类型 ====================

/** 完整推理链 */
export interface ReasoningChain {
  id: string;
  timestamp: number;
  query: string;
  inputData: InputData;
  ruleExecutions: RuleExecution[];
  aiInterpretation: AIInterpretation;
  conclusion: FinalConclusion;
  trace: TraceInfo;
}

/** 输入数据 */
export interface InputData {
  dataPoints: DataPoint[];
  filters: Record<string, any>;
}

/** AI解释 */
export interface AIInterpretation {
  summary: string;
  scenarios: Scenario[];
  confidence: number;
  uncertaintyFactors: string[];
}

/** 情景 */
export interface Scenario {
  name: string;
  probability: number;
  description: string;
  keyFactors: string[];
}

/** 最终结论 */
export interface FinalConclusion {
  recommendation: string;
  confidence: number;
  reasoning: string;
  supportingData: string[];    // 数据点ID列表
  conflictingData: string[];   // 数据点ID列表
}

/** 追踪信息 */
export interface TraceInfo {
  dataVersion: string;
  ruleVersion: string;
  modelVersion: string;
}

// ==================== 复盘校准类型 ====================

/** 复盘记录 */
export interface ReviewRecord {
  id: string;
  reasoningChainId: string;
  prediction: PredictionInfo;
  actual: ActualOutcome;
  errorAnalysis?: ErrorAnalysis;
  calibration?: CalibrationAction;
}

/** 预测信息 */
export interface PredictionInfo {
  conclusion: string;
  confidence: number;
  timeHorizon: string;
}

/** 实际结果 */
export interface ActualOutcome {
  outcome: string;
  occurred: boolean;
  deviation: number;
  timestamp: number;
}

/** 误差分析 */
export interface ErrorAnalysis {
  errorType: ErrorType;
  rootCause: string;
  severity: ErrorSeverity;
  suggestedFix?: string;
}

/** 校准动作 */
export interface CalibrationAction {
  action: CalibrationActionType;
  targetId?: string;
  parameters: Record<string, any>;
  executed: boolean;
}

/** 校准动作类型 */
export type CalibrationActionType = 
  | 'adjust_weight'
  | 'modify_rule'
  | 'add_rule'
  | 'remove_rule'
  | 'retrain_model';

// ==================== 服务接口类型 ====================

/** 数据过滤器 */
export interface DataFilters {
  category?: string;
  source?: string;
  tags?: string[];
  timeRange?: {
    start: number;
    end: number;
  };
  minCredibility?: number;
}

/** 规则过滤器 */
export interface RuleFilters {
  status?: RuleStatus;
  type?: RuleType;
  category?: string;
  minPriority?: number;
}

/** AI解释上下文 */
export interface InterpretationContext {
  audience: 'expert' | 'layman' | 'executive';
  includeUncertainty: boolean;
  maxScenarios: number;
}

/** 不确定性量化 */
export interface UncertaintyQuantification {
  epistemic: number;    // 认知不确定性 (模型/知识不足)
  aleatoric: number;    // 偶然不确定性 (数据固有噪声)
  total: number;
  factors: string[];
}

// ==================== 配置类型 ====================

/** 数据源配置 */
export interface SourceConfig {
  id: string;
  name: string;
  type: DataSourceType;
  baseReliability: number;
  updateFrequency: {
    interval: number;    // 分钟
    priority: 'high' | 'medium' | 'low';
  };
  connection: {
    type: 'api' | 'scrape' | 'manual';
    endpoint?: string;
    auth?: string;
  };
  fieldMapping: Record<string, string>;
}

/** 校准配置 */
export interface CalibrationConfig {
  autoExecute: boolean;
  confidenceThreshold: number;
  minReviewCount: number;
  maxAdjustment: number;
}

/** 时间范围 */
export interface TimePeriod {
  start: number;
  end: number;
}

/** 复盘报告 */
export interface ReviewReport {
  period: TimePeriod;
  totalPredictions: number;
  accuratePredictions: number;
  accuracy: number;
  errorDistribution: Record<ErrorType, number>;
  topRules: Array<{
    ruleId: string;
    successRate: number;
    usageCount: number;
  }>;
  recommendations: string[];
}

/** 规则变更建议 */
export interface RuleChangeSuggestion {
  type: 'add' | 'modify' | 'remove';
  ruleId?: string;
  reason: string;
  confidence: number;
  suggestedChange?: Partial<Rule>;
}

// ==================== 结果类型 ====================

/** 异常报告 */
export interface AnomalyReport {
  anomalies: Array<{
    dataPointId: string;
    anomalyType: string;
    severity: number;
    description: string;
  }>;
  summary: {
    total: number;
    byType: Record<string, number>;
  };
}

/** 验证结果 */
export interface ValidationResult {
  metric: string;
  dataPoints: string[];
  consensus: number | string;
  deviations: Array<{
    dataPointId: string;
    deviation: number;
  }>;
  consistencyScore: number;
}

/** 规则验证 */
export interface RuleValidation {
  valid: boolean;
  errors: string[];
  warnings: string[];
  suggestions: string[];
}

/** 条件AST */
export interface ConditionAST {
  type: string;
  expression: string;
  variables: string[];
}

/** 校准结果 */
export interface CalibrationResult {
  adjustedRules: string[];
  adjustedParameters: Record<string, any>;
  accuracyImprovement: number;
  suggestions: string[];
}
