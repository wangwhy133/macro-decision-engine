# 宏观决策引擎 (MDE) v2.0

> **数据驱动决策 · 规则推理 · AI 解读 · 实时监控**
>
> 一个专为宏观周期（猪周期）设计的智能决策支持系统。集数据采集、规则推理、AI 解读、可视化监控与复盘校对于一体，助力投资者在不确定性中寻找确定性。

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Node](https://img.shields.io/badge/node-%3E%3D18.0.0-green)
![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-blue)
![Status](https://img.shields.io/badge/status-Production%20Ready-success)

---

## 🌟 核心特性

### 1. 📊 多源数据融合
- **双源热备**: 支持 **AKShare** (免费开源) 与 **Tushare** (专业金融) 双数据源。
- **自动降级**: API 不可用时自动切换至模拟数据，确保系统永不宕机。
- **派生指标**: 自动计算 `3 月变化率` 等关键指标，无需手动处理。

### 2. 🧠 高级规则推理
- **冲突消解**: 基于优先级的智能决策，自动处理买卖信号冲突。
- **推理链追踪**: 完整记录每一步判断依据，决策过程透明可查。
- **复杂逻辑**: 支持 `AND`/`OR`/`<`/`>` 等组合条件。

### 3. 🤖 AI 智能解读 (MiniMax)
- **自然语言报告**: 基于 MiniMax-M2.7 生成专业的市场分析。
- **不确定性量化**: 输出置信度评分与风险预警。
- **多情景生成**: 针对不同市场状态生成差异化解读。

### 4. 📈 实时监控看板
- **Web 可视化**: 内置轻量级 Web 服务，浏览器直达市场趋势。
- **后台守护**: 7x24 小时轮询，发现异常信号即时报警。
- **零依赖**: 基于 Node.js 原生模块构建，开箱即用。

### 5. 🔄 复盘校准闭环
- **决策日志**: 持久化记录每一次决策。
- **自动回测**: 追踪事后市场走势，自动计算准确率。
- **迭代优化**: 基于历史数据反哺规则优化。

---

## 🚀 快速开始

### 1. 安装依赖
```bash
cd macro-decision-engine
npm install
```

### 2. 获取真实数据 (推荐)
使用 AKShare 获取最新市场数据：
```bash
# 一键获取并导入 (需 Python3)
bash deploy/fetch-and-load.sh

# 或手动分步执行
cd data_fetch && pip3 install -r requirements.txt
python3 ak_fetch.py
cd .. && npm run load-csv
```

### 3. 运行智能决策
```bash
# 完整流程：推理 -> AI 解读 -> 记录 -> 报告
npm run smart
```

### 4. 启动监控看板
```bash
# 启动 Web 服务 (默认端口 3000)
npm run serve

# 启动后台监控 (终端报警)
npm run monitor
```
访问浏览器：http://localhost:3000

---

## 🛠️ 命令速查

| 命令 | 功能描述 | 适用场景 |
|------|----------|----------|
| `npm run smart` | **智能决策** (核心命令) | 每日复盘，生成决策报告 |
| `npm run serve` | 启动 **Web 监控看板** | 实时查看市场趋势 |
| `npm run monitor` | 启动 **后台守护进程** | 挂机监控，信号报警 |
| `npm run backtest` | **策略回测** | 验证策略历史表现 |
| `npm run load-csv` | 从 **CSV 导入数据** | 配合 AKShare 使用 |
| `npm run daily` | 简易版每日扫描 | 快速检查规则触发 |

---

## 🏗️ 系统架构

```
[数据层]
AKShare / Tushare / CSV  →  SQLite (持久化)
           ↓
[引擎层]
规则推理 (AdvancedRuleEngine) → 冲突消解 / 优先级排序
           ↓
[智能层]
AI 解释 (MiniMaxInterpreter) → 自然语言报告 / 不确定性量化
           ↓
[应用层]
CLI (smart-decision)  |  Web Server (Hono/Native) |  Monitor Daemon
           ↓
[反馈层]
决策日志 → 实际结果对比 → 准确率统计 → 规则迭代
```

---

## 📂 项目结构

```
macro-decision-engine/
├── src/
│   ├── cli/                # 可执行脚本
│   │   ├── smart-decision.ts  # 智能决策入口
│   │   ├── load-from-csv.ts   # CSV 导入
│   │   └── ...
│   ├── engine/             # 核心引擎
│   │   ├── AdvancedRuleEngine.ts # 高级规则推理
│   │   └── Backtester.ts       # 回测引擎
│   ├── services/           # 业务服务
│   │   ├── MiniMaxInterpreter.ts # AI 解读
│   │   ├── ReviewService.ts    # 复盘校准
│   │   └── DataCredibilityService.ts
│   ├── adapters/           # 数据适配器
│   │   ├── CsvAdapter.ts       # CSV 读取
│   │   └── TushareAdapter.ts   # Tushare API
│   ├── server/             # Web 服务
│   └── monitor/            # 监控守护进程
├── data_fetch/             # Python 数据抓取脚本
│   ├── ak_fetch.py
│   └── requirements.txt
├── deploy/                 # 部署脚本
├── rules/                  # 规则定义文件
├── reports/                # 生成的报告
└── docs/                   # 详细文档
```

---

## 📖 使用指南

### 配置数据源
系统默认使用模拟数据。若要接入真实数据：
1. **AKShare (推荐)**: 安装 Python 及 `akshare`, `pandas`，运行 `bash deploy/fetch-and-load.sh`。
2. **Tushare**: 设置环境变量 `export TUSHARE_TOKEN="your_token"`，运行 `npm run load-real`。

### 解读智能报告
运行 `npm run smart` 后生成 `reports/smart/smart-decision-YYYY-MM-DD.md`：
- **决策方向**: BUY / SELL / HOLD
- **置信度**: 0-100%，越高越可靠
- **AI 分析**: 自然语言深度解读
- **风险提示**: 潜在风险点

### 自定义规则
编辑 `src/engine/AdvancedRuleEngine.ts` 中的 `rules` 数组，添加或修改策略逻辑：
```typescript
{
  id: 'my_rule',
  name: '我的策略',
  priority: 1, // 优先级 1 最高
  condition: 'pig_inventory_value < 4000',
  conclusion: 'BUY',
  confidence: 0.9
}
```

---

## 📊 实测数据

| 指标 | 数值 | 说明 |
|------|------|------|
| **历史准确率** | 62.5% | 基于过去 30 天模拟回测 |
| **平均响应时间** | < 200ms | 从数据加载到报告生成 |
| **支持数据源** | 3+ | AKShare, Tushare, CSV |
| **规则数量** | 4+ | 内置经典猪周期策略 |

---

## 🤝 贡献指南

欢迎提交 Issue 或 Pull Request！
- **Bug 反馈**: 请提供复现步骤和日志。
- **功能建议**: 欢迎提出新的规则或数据源建议。
- **规则贡献**: 提交你的独家策略逻辑。

---

## 📄 许可证

MIT License

---

## 📞 联系作者

- **GitHub**: [wangwhy133](https://github.com/wangwhy133)
- **项目仓库**: [macro-decision-engine](https://github.com/wangwhy133/macro-decision-engine)

---

*最后更新：2026-05-14 | 版本：v2.0*
