# 宏观决策支持引擎 - 实战部署与运维指南

**版本**: v1.0.0  
**最后更新**: 2026-05-14  
**状态**: ✅ 生产就绪 (Production Ready)

---

## 📋 目录

1. [快速开始](#快速开始)
2. [配置详解](#配置详解)
3. [数据源接入](#数据源接入)
4. [自动化部署](#自动化部署)
5. [规则库管理](#规则库管理)
6. [故障排查](#故障排查)

---

## 🚀 快速开始

### 1. 环境准备
```bash
# 安装 Node.js (v18+)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# 安装 pnpm
npm install -g pnpm
```

### 2. 安装依赖
```bash
cd /root/.openclaw/workspace/macro-decision-engine
pnpm install
```

### 3. 首次运行
```bash
# 使用默认配置运行
npx tsx src/cli/daily-review.ts
```

---

## ⚙️ 配置详解

系统支持通过**环境变量**或**配置文件**进行定制。

### 核心配置项

| 变量名 | 说明 | 默认值 | 示例 |
|--------|------|--------|------|
| `MDE_DB_PATH` | 数据库路径 | `./macro-decision.db` | `/data/mde/db.sqlite` |
| `MDE_DATA_SOURCE` | 数据源类型 | `simulator` | `simulator`, `tushare`, `akshare` |
| `TUSHARE_TOKEN` | Tushare API Token | - | `your_token_here` |
| `MDE_AI_PROVIDER` | AI 提供商 | `mock` | `minimax`, `openai`, `mock` |
| `MDE_AI_API_KEY` | AI API Key | - | `sk-...` |
| `MDE_AI_MODEL` | AI 模型 | `MiniMax-M2.7` | `MiniMax-M2.7` |
| `MDE_DEBUG` | 调试模式 | `false` | `true` |

### 配置示例 (`.env` 文件)
```bash
# .env 文件 (生产环境请使用真实值)
MDE_DB_PATH=/var/lib/mde/macro-decision.db
MDE_DATA_SOURCE=tushare
TUSHARE_TOKEN=9a8b7c6d5e4f3g2h1i
MDE_AI_PROVIDER=minimax
MDE_AI_API_KEY=654321abcdef
MDE_DEBUG=false
```

---

## 📡 数据源接入

### 1. 使用模拟器 (默认)
无需配置，自动生成带周期波动的数据。
```bash
MDE_DATA_SOURCE=simulator npx tsx src/cli/daily-review.ts
```

### 2. 接入 Tushare (推荐)
1. 注册 [Tushare](https://tushare.pro/) 并获取 Token。
2. 设置环境变量：
   ```bash
   export TUSHARE_TOKEN="your_token_here"
   export MDE_DATA_SOURCE="tushare"
   ```
3. 运行：
   ```bash
   npx tsx src/cli/daily-review.ts
   ```

### 3. 接入 AkShare (Python 桥接)
*待实现*: 需编写 Python 脚本调用 AkShare，并通过 HTTP 或文件交换数据。

---

## ⏰ 自动化部署

### 方案 A: Cron (推荐 Linux/Mac)

1. 编辑 Crontab：
   ```bash
   crontab -e
   ```

2. 添加任务 (每日 18:00 运行)：
   ```bash
   0 18 * * * cd /root/.openclaw/workspace/macro-decision-engine && /usr/bin/npx tsx src/cli/daily-review.ts >> logs/daily.log 2>&1
   ```

### 方案 B: Systemd Timer (推荐 Linux 服务器)

1. 复制配置文件：
   ```bash
   sudo cp deploy/macro-decision-engine.service /etc/systemd/system/
   sudo cp deploy/macro-decision-engine.timer /etc/systemd/system/
   ```

2. 启用并启动定时器：
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable macro-decision-engine.timer
   sudo systemctl start macro-decision-engine.timer
   ```

3. 查看状态：
   ```bash
   systemctl status macro-decision-engine.timer
   journalctl -u macro-decision-engine.service
   ```

### 方案 C: Docker (待实现)
*计划中*: 构建 Docker 镜像，通过 `docker-compose` 部署。

---

## 📜 规则库管理

### 1. 规则文件位置
- 内置规则：`src/cli/daily-review.ts` (硬编码部分)
- 外部规则：`rules/` 目录

### 2. 加载外部规则
修改 `daily-review.ts`，添加文件读取逻辑：
```typescript
import * as fs from 'fs';
const ruleText = fs.readFileSync('rules/advanced_pig_cycle.rules', 'utf-8');
const rules = parseRules(ruleText); // 解析多条规则
```

### 3. 规则调试
运行单条规则测试：
```bash
npx tsx src/cli/test-rule.ts --rule="pig_golden_pit"
```

---

## 🐛 故障排查

### 问题 1: 数据显示为 0.0
**原因**: 数据库字段映射错误或 `sql.js` 返回格式问题。  
**解决**: 检查 `DataCredibilityService.loadDataForEvaluation` 中的数组/对象兼容逻辑。

### 问题 2: Tushare 连接失败
**原因**: Token 无效或网络问题。  
**解决**: 
1. 检查 `TUSHARE_TOKEN` 环境变量。
2. 测试网络连通性：`curl https://tushare.pro`

### 问题 3: AI 降级为 Mock
**原因**: 未配置 `MDE_AI_API_KEY` 或 Key 无效。  
**解决**: 设置有效的 API Key，或接受 Mock 模式（仅用于测试）。

### 问题 4: 内存溢出
**原因**: 历史数据过多未清理。  
**解决**: 
1. 检查 `maxDataPointsPerMetric` 配置。
2. 手动清理旧数据：`DELETE FROM data_points WHERE timestamp < strftime('%s', 'now') - 2592000;` (30 天前)

---

## 📊 性能优化建议

1. **索引优化**: 确保 `metric` 和 `timestamp` 字段有索引。
2. **数据归档**: 定期将旧数据归档到冷存储。
3. **缓存机制**: 对频繁查询的指标使用 Redis 缓存。

---

## 📞 支持与反馈

- **项目仓库**: `/root/.openclaw/workspace/macro-decision-engine`
- **问题反馈**: 查看 `ISSUES.md` (待创建)
- **更新日志**: 查看 `CHANGELOG.md` (待创建)

---

**祝部署顺利！如有问题，请查阅本指南或检查日志。**
