# 宏观决策支持引擎 v1.0

## 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    宏观决策支持引擎                               │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │ 数据可信度系统   │  │ 规则推理系统     │  │ AI解释层         │  │
│  │                 │  │                 │  │                 │  │
│  │ - 多源数据接入   │  │ - 规则DSL引擎    │  │ - 语义理解      │  │
│  │ - 可信度评分     │  │ - 冲突消解       │  │ - 情境适配      │  │
│  │ - 交叉验证       │  │ - 推理链追踪     │  │ - 多假设生成    │  │
│  │ - 异常检测       │  │ - 置信度计算     │  │ - 可解释输出    │  │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘  │
│           │                   │                   │           │
│           └───────────────────┼───────────────────┘           │
│                               │                               │
│  ┌────────────────────────────▼────────────────────────────┐  │
│  │                  复盘校准系统                            │  │
│  │  - 决策日志  - 误差归因  - 参数优化  - 规则迭代          │  │
│  └─────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## 一、数据结构定义

### 1.1 核心数据模型

#### DataPoint (数据点)
```typescript
interface DataPoint {
  id: string;                    // 唯一标识
  source: string;                // 数据源 (eastmoney, stats.gov, news, etc.)
  sourceType: 'official' | 'financial' | 'news' | 'social';
  timestamp: number;             // 数据时间戳
  receivedAt: number;            // 接收时间
  category: string;              // 分类 (pig_cycle, inflation, policy, etc.)
  tags: string[];                // 标签数组
  
  // 原始数据
  raw: Record<string, any>;
  
  // 可信度指标
  credibility: {
    score: number;               // 0-1 综合可信度
    sourceReliability: number;   // 来源可靠性 (静态配置)
    timeliness: number;          // 时效性 (时间衰减计算)
    crossValidation: {           // 交叉验证结果
      verified: boolean;
      conflictingSources: string[];
      consistencyScore: number;  // 0-1
    };
    anomalyFlags: string[];      // 异常标记
  };
  
  // 标准化后的值
  normalized: {
    metric: string;              // 指标名称
    value: number | string;
    unit: string;
    change?: {
      absolute: number;
      percentage: number;
      period: string;
    };
  };
}
```

#### Rule (规则)
```typescript
interface Rule {
  id: string;
  name: string;
  description: string;
  
  // 规则类型
  type: 'threshold' | 'trend' | 'correlation' | 'pattern' | 'composite';
  
  // 触发条件 (DSL表达式)
  condition: string;             // e.g., "pig_inventory.change < -0.10"
  
  // 推理结果
  inference: {
    conclusion: string;          // 结论描述
    confidence: number;          // 基础置信度 (0-1)
    impact: 'positive' | 'negative' | 'neutral';
    timeHorizon: 'short' | 'medium' | 'long';
  };
  
  // 元数据
  metadata: {
    createdAt: number;
    updatedAt: number;
    source: 'expert' | 'mined' | 'learned';
    validationCount: number;     // 验证次数
    successRate: number;         // 历史准确率
    priority: number;            // 优先级 (高优先级先执行)
  };
  
  // 状态
  status: 'active' | 'deprecated' | 'testing';
}
```

#### ReasoningChain (推理链)
```typescript
interface ReasoningChain {
  id: string;
  timestamp: number;
  query: string;                 // 原始问题/查询
  
  // 输入数据
  inputData: {
    dataPoints: DataPoint[];
    filters: Record<string, any>;
  };
  
  // 规则执行
  ruleExecutions: Array<{
    ruleId: string;
    ruleName: string;
    triggered: boolean;
    conditionResult: boolean;
    variables: Record<string, any>;
  }>;
  
  // AI解释
  aiInterpretation: {
    summary: string;
    scenarios: Array<{
      name: string;
      probability: number;
      description: string;
      keyFactors: string[];
    }>;
    confidence: number;
    uncertaintyFactors: string[];
  };
  
  // 最终输出
  conclusion: {
    recommendation: string;
    confidence: number;
    reasoning: string;
    supportingData: string[];    // 支持的数据点ID
    conflictingData: string[];   // 矛盾的数据点ID
  };
  
  // 可追溯性
  trace: {
    dataVersion: string;
    ruleVersion: string;
    modelVersion: string;
  };
}
```

#### ReviewRecord (复盘记录)
```typescript
interface ReviewRecord {
  id: string;
  reasoningChainId: string;
  
  // 预测 vs 实际
  prediction: {
    conclusion: string;
    confidence: number;
    timeHorizon: string;
  };
  
  actual: {
    outcome: string;
    occurred: boolean;
    deviation: number;           // 偏差程度
    timestamp: number;
  };
  
  // 误差分析
  errorAnalysis: {
    errorType: 'data_error' | 'rule_flaw' | 'ai_misjudgment' | 'black_swan';
    rootCause: string;
    severity: 'low' | 'medium' | 'high';
    suggestedFix?: string;
  };
  
  // 校准动作
  calibration: {
    action: 'adjust_weight' | 'modify_rule' | 'add_rule' | 'remove_rule' | 'retrain_model';
    targetId?: string;           // 规则ID或模型ID
    parameters: Record<string, any>;
    executed: boolean;
  };
}
```

### 1.2 配置数据

#### SourceConfig (数据源配置)
```typescript
interface SourceConfig {
  id: string;
  name: string;
  type: 'official' | 'financial' | 'news' | 'social';
  
  // 可信度基准
  baseReliability: number;       // 0-1 基础可靠性
  
  // 更新频率
  updateFrequency: {
    interval: number;            // 分钟
    priority: 'high' | 'medium' | 'low';
  };
  
  // 连接信息
  connection: {
    type: 'api' | 'scrape' | 'manual';
    endpoint?: string;
    auth?: string;
  };
  
  // 字段映射
  fieldMapping: Record<string, string>;
}
```

## 二、接口定义

### 2.1 数据可信度系统接口

```typescript
interface DataCredibilityService {
  // 数据接入
  ingest(data: RawDataPoint): Promise<DataPoint>;
  ingestBatch(data: RawDataPoint[]): Promise<DataPoint[]>;
  
  // 可信度计算
  calculateCredibility(
    dataPoint: DataPoint,
    context: CredibilityContext
  ): Promise<CredibilityScore>;
  
  // 交叉验证
  crossValidate(
    dataPoints: DataPoint[],
    metric: string
  ): Promise<ValidationResult>;
  
  // 异常检测
  detectAnomalies(
    dataPoints: DataPoint[],
    threshold?: number
  ): Promise<AnomalyReport>;
  
  // 数据查询
  query(filters: DataFilters): Promise<DataPoint[]>;
  getByTags(tags: string[]): Promise<DataPoint[]>;
}
```

### 2.2 规则推理系统接口

```typescript
interface RuleEngine {
  // 规则管理
  addRule(rule: Rule): Promise<void>;
  removeRule(ruleId: string): Promise<void>;
  updateRule(ruleId: string, updates: Partial<Rule>): Promise<void>;
  getRules(filters?: RuleFilters): Promise<Rule[]>;
  
  // 推理执行
  evaluate(
    data: DataPoint[],
    ruleIds?: string[]
  ): Promise<RuleEvaluationResult>;
  
  // 规则验证
  validateRule(rule: Rule): Promise<RuleValidation>;
  
  // DSL解析
  parseCondition(expression: string): Promise<ConditionAST>;
  evaluateCondition(
    ast: ConditionAST,
    context: Record<string, any>
  ): Promise<boolean>;
}
```

### 2.3 AI解释层接口

```typescript
interface AIInterpretationService {
  // 语义理解
  interpret(
    reasoningChain: ReasoningChain,
    context: InterpretationContext
  ): Promise<AIInterpretation>;
  
  // 多假设生成
  generateScenarios(
    data: DataPoint[],
    rules: Rule[]
  ): Promise<Scenario[]>;
  
  // 可解释性输出
  generateExplanation(
    chain: ReasoningChain,
    audience: 'expert' | 'layman' | 'executive'
  ): Promise<string>;
  
  // 不确定性量化
  quantifyUncertainty(
    chain: ReasoningChain
  ): Promise<UertaintyQuantification>;
}
```

### 2.4 复盘校准系统接口

```typescript
interface ReviewCalibrationService {
  // 记录保存
  recordPrediction(chain: ReasoningChain): Promise<void>;
  recordOutcome(
    predictionId: string,
    outcome: OutcomeData
  ): Promise<void>;
  
  // 误差分析
  analyzeError(
    predictionId: string
  ): Promise<ErrorAnalysis>;
  
  // 自动校准
  autoCalibrate(
    reviewRecords: ReviewRecord[],
    config: CalibrationConfig
  ): Promise<CalibrationResult>;
  
  // 报告生成
  generateReport(
    period: TimePeriod,
    format: 'summary' | 'detailed'
  ): Promise<ReviewReport>;
  
  // 规则建议
  suggestRuleChanges(
    reviewRecords: ReviewRecord[]
  ): Promise<RuleChangeSuggestion[]>;
}
```

## 三、工作流程

### 3.1 数据处理流程
```
原始数据 → 标准化 → 可信度评分 → 交叉验证 → 异常标记 → 存储
           ↓
       元数据更新
           ↓
       触发规则评估
```

### 3.2 决策推理流程
```
用户查询 → 数据检索 → 规则评估 → AI解释 → 多情景生成 → 输出
                                    ↓
                              记录推理链
                                    ↓
                              等待复盘
```

### 3.3 复盘校准流程
```
结果发生 → 对比预测 → 误差分析 → 归因 → 校准建议 → 人工确认 → 执行
                                                          ↓
                                                  更新规则/参数
```

## 四、技术选型建议

| 组件 | 推荐方案 | 理由 |
|------|---------|------|
| 数据存储 | PostgreSQL + TimescaleDB | 时序数据 + 关系型查询 |
| 规则引擎 | 自研轻量DSL | 投资领域特定需求，灵活性优先 |
| AI模型 | MiniMax-M2.7 | 已有集成，中文理解优秀 |
| 缓存 | Redis | 高频查询缓存 |
| 消息队列 | Redis Streams | 异步处理、解耦 |
| 监控 | Prometheus + Grafana | 成熟方案 |

## 五、下一步

1. **Phase 1**: 实现数据可信度系统核心
   - [ ] 设计数据库schema
   - [ ] 实现DataPoint模型
   - [ ] 集成eastmoney-data-api
   - [ ] 可信度评分算法

2. **Phase 2**: 构建规则推理引擎原型
   - [ ] 设计规则DSL语法
   - [ ] 实现条件解析器
   - [ ] 构建初始规则库(10-20条)

3. **Phase 3**: AI解释层集成
   - [ ] 设计prompt模板
   - [ ] 实现场景生成逻辑
   - [ ] 可解释性输出格式化

4. **Phase 4**: 复盘系统
   - [ ] 决策日志持久化
   - [ ] 误差分析算法
   - [ ] 校准建议生成

---
*文档版本: v1.0 | 创建时间: 2026-05-14*
