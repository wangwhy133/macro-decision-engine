# 生产环境部署指南

## ✅ 部署状态

| 步骤 | 状态 | 说明 |
|------|------|------|
| 1. 代码推送 | ✅ 完成 | 仓库已更新至最新生产版本 |
| 2. 依赖安装 | 🔄 进行中 | 正在安装 Python 依赖包 |
| 3. 环境配置 | ⏳ 待执行 | 需配置 API Keys |
| 4. 定时任务 | ⏳ 待执行 | 配置每日自动采集 |
| 5. 看板启动 | ⏳ 待执行 | Streamlit Dashboard |

---

## 🔑 关键配置项

### 1. FRED API Key (必需)
**用途**: 获取美国宏观经济数据 (CPI、失业率、利率等)  
**获取方式**: https://fred.stlouisfed.org/docs/api/api_key.html  
**配置位置**: `.env` 文件中的 `FRED_API_KEY=`

### 2. Zhipu AI API Key (可选)
**用途**: AI 智能分析与市场状态识别  
**获取方式**: https://open.bigmodel.cn/  
**配置位置**: `.env` 文件中的 `ZHIPU_API_KEY=`

### 3. Telegram 通知 (可选)
**用途**: 数据异常时推送告警  
**配置**: `TELEGRAM_BOT_TOKEN` 和 `TELEGRAM_CHAT_ID`

---

## 🚀 快速部署命令

```bash
# 1. 克隆仓库 (如果还没克隆)
cd /root/.openclaw/workspace
git clone https://github.com/wangwhy133/macro-system.git macro-system-prod
cd macro-system-prod

# 2. 运行部署脚本
bash deploy.sh

# 3. 配置 API Keys
nano .env
# 填入 FRED_API_KEY 和其他配置

# 4. 运行健康检查
./venv/bin/python -m macro_system check

# 5. 执行首次数据采集
./venv/bin/python -m macro_system run

# 6. 启动可视化看板
./venv/bin/streamlit run macro_system/dashboard.py --server.port 8501
```

---

## 📅 配置定时任务 (Cron)

编辑 crontab:
```bash
crontab -e
```

添加每日早上 8 点自动采集任务:
```cron
# 宏观经济数据每日自动采集 (北京时间 8:00 AM)
0 0 * * * cd /root/.openclaw/workspace/macro-system-prod && ./venv/bin/python -m macro_system run >> logs/daily_run.log 2>&1
```

---

## 🔍 日常运维命令

| 命令 | 功能 |
|------|------|
| `./venv/bin/python -m macro_system check` | 系统健康检查 |
| `./venv/bin/python -m macro_system run` | 执行数据采集 |
| `./venv/bin/python -m macro_system status` | 查看缓存状态 |
| `./venv/bin/python -m macro_system vacuum` | 清理数据库 |
| `./venv/bin/streamlit run macro_system/dashboard.py` | 启动看板 |

---

## 📊 查看 Dashboard

启动后访问：`http://<服务器 IP>:8501`

默认端口 8501，可在 `.env` 中修改 `DASHBOARD_PORT`

---

## ⚠️ 注意事项

1. **API 限制**: FRED 免费版每分钟 120 次请求，每日 5000 次
2. **数据安全**: 不要将 `.env` 提交到 Git
3. **磁盘空间**: 历史数据会增长，定期清理旧日志
4. **时区设置**: 系统默认使用 `Asia/Shanghai` 时区

---

## 📚 相关文档

- [QUICKSTART.md](./QUICKSTART.md) - 5 分钟快速开始
- [WHITEPAPER.md](./WHITEPAPER.md) - 完整技术白皮书
- [README-PRODUCTION.md](./README-PRODUCTION.md) - 生产运维指南
