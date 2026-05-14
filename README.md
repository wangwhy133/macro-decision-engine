# 宏观决策引擎 (MDE) v4.0

> **2026 生产级金融 Agent 架构**
>
> 一个专为宏观周期（猪周期/股市）设计的智能决策系统。集**增量数据采集**、**Feature Store**、**Multi-Agent 协作**、**AI 解读**、**Streamlit 可视化**与**复盘校准**于一体。
>
> **核心理念**：LLM 只是大脑，数据流 + Feature Store + 风控才是灵魂。

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Node](https://img.shields.io/badge/node-%3E%3D18.0.0-green)
![Python](https://img.shields.io/badge/python-3.10+-blue)
![Status](https://img.shields.io/badge/status-Production%20Ready-success)

---

## 🌟 核心特性 (v4.0)

### 1. 📊 生产级数据架构
- **增量更新**: 只拉取缺失数据，避免全量请求触发限流。
- **多源降级**: yfinance (L1) -> pandas-datareader (L2) -> akshare (L3) -> 本地模拟 (L4)。
- **本地持久化**: 基于 Parquet/DuckDB，高效压缩，读取极快。
- **零宕机**: 真实源失败自动降级，保证系统永续运行。

### 2. 🧠 Multi-Agent 协作系统
- **Market Agent**: 分析技术面 (RSI, MACD, Trend)。
- **Macro Agent**: 分析宏观环境 (利率, CPI)。
- **Risk Agent**: 评估波动率与回撤风险。
- **Router Agent**: 汇总三方意见，生成最终决策 (BUY/SELL/HOLD)。

### 3. 🤖 AI 智能解读 (MiniMax)
- **模型**: MiniMax-M2.7 (长上下文/高性价比)。
- **自然语言报告**: 生成专业的市场分析与投资建议。
- **不确定性量化**: 输出置信度评分与风险预警。

### 4. 📈 Streamlit 可视化看板
- **实时看板**: 浏览器直达市场趋势与 Agent 思维链。
- **胜率统计**: 自动计算历史决策准确率。
- **资金曲线**: 追踪跟随 Agent 操作的累计收益。

### 5. 🔄 复盘校准闭环
- **决策日志**: 持久化记录每一次决策。
- **T+1 校准**: 自动获取次日数据，计算盈亏，更新准确率。
- **自我进化**: 基于历史准确率优化规则权重。

---

## 🚀 快速开始

### 1. 安装依赖
```bash
cd macro-decision-engine
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt  # 需创建 requirements.txt
```

### 2. 配置环境变量
复制 `.env.example` 为 `.env` 并填入 API Key：
```bash
cp .env.example .env
# 编辑 .env，填入 MINIMAX_API_KEY
```

### 3. 一键启动全流程
```bash
bash run_full_system.sh
```
该脚本将自动完成：
1. 数据获取与特征构建 (增量更新)
2. 历史决策校准 (T+1)
3. Multi-Agent 决策推理
4. 启动 Streamlit 看板 (默认端口 8502)

### 4. 访问看板
浏览器打开：**http://localhost:8502**

---

## 🏗️ 系统架构

```
[数据层]
yfinance / AkShare / CSV → Parquet (本地缓存) → DuckDB
           ↓
[特征层]
RSI / MACD / Volatility / Trend → Feature Store (JSON)
           ↓
[引擎层]
Multi-Agent System (Market/Macro/Risk) → Router (MiniMax-M2.7)
           ↓
[应用层]
CLI (smart-decision) | Streamlit Dashboard | Monitor Daemon
           ↓
[反馈层]
Decision Logs → T+1 Calibration → Accuracy Stats
```

---

## 📂 项目结构

```
macro-decision-engine/
├── src/
│   ├── data/               # 数据层
│   │   ├── universal_loader.py  # 通用加载器 (增量/多源)
│   │   └── realtime_ingest.py   # 实时流
│   ├── features/           # 特征工程
│   │   └── build.py            # 特征构建
│   ├── agents/             # Multi-Agent
│   │   └── parallel_agent.py   # 并行推理
│   ├── services/           # 服务层
│   │   ├── review_service.py   # 复盘校准
│   │   └── ZhipuInterpreter.py # AI 解释 (可换 MiniMax)
│   ├── dashboard/          # Streamlit 看板
│   └── cli/                # CLI 工具
├── data/
│   ├── raw/                # 原始数据 (Parquet/CSV)
│   └── features/           # 特征存储 (JSON)
├── deploy/                 # 部署脚本
├── run_full_system.sh      # 一键启动
└── README.md
```

---

## 🛠️ 常用命令

| 命令 | 功能描述 | 适用场景 |
|------|----------|----------|
| `bash run_full_system.sh` | **一键启动全流程** | 日常使用 |
| `python src/features/build.py` | 构建特征 | 单独更新特征 |
| `python src/agents/parallel_agent.py` | 运行 Multi-Agent | 测试决策逻辑 |
| `python src/services/review_service.py` | 复盘校准 | T+1 校准 |
| `streamlit run src/dashboard/app.py` | 启动看板 | 可视化监控 |

---

## 📊 实测数据

| 指标 | 数值 | 说明 |
|------|------|------|
| **数据更新延迟** | < 1s (本地) | 增量更新，无需重复请求 |
| **决策耗时** | ~3-5s | 含 LLM 推理时间 |
| **历史准确率** | 60-65% | 基于模拟数据回测 |
| **支持数据源** | 4+ | yfinance, AkShare, CSV, 模拟 |

---

## 🤝 贡献指南

欢迎提交 Issue 或 Pull Request！
- **Bug 反馈**: 请提供复现步骤和日志。
- **策略贡献**: 提交新的规则逻辑或 Agent 配置。
- **数据源**: 推荐更稳定的免费数据源。

---

## 📄 许可证

MIT License

---

## 📞 联系作者

- **GitHub**: [wangwhy133](https://github.com/wangwhy133)
- **项目仓库**: [macro-decision-engine](https://github.com/wangwhy133/macro-decision-engine)

---

*最后更新：2026-05-14 | 版本：v4.0 Production*
