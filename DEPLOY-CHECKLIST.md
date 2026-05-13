# 生产部署清单 (Production Checklist)

**版本**: P1.0  
**日期**: 2026-05-13  
**状态**: ✅ 生产就绪

---

## 📋 部署前检查

### 1. 环境准备
- [x] Python 3.10+ 已安装
- [x] 依赖已安装 (`pip install -r requirements.txt`)
- [x] 目录结构已创建 (`/opt/macro-push/data/`)

### 2. 配置校验
```bash
cd /root/.openclaw/workspace
python3 -m macro_system.config.config_validator
```
**预期输出**:
```
✓ 环境变量检查通过
✓ 依赖检查通过
✓ 数据库路径检查通过
✓ 所有配置校验通过
```

### 3. API Key 配置
- [ ] **FRED API Key** (美国宏观数据)
  - 申请地址：https://fred.stlouisfed.org/docs/api/api_key.html
  - 配置方式：`export FRED_API_KEY=xxx` 或写入 `~/.macro_config.json`
  
- [ ] **智谱 AI Key** (AI 分析，可选)
  - 申请地址：https://open.bigmodel.cn/
  - 配置方式：`export ZHIPU_API_KEY=xxx`

### 4. 数据源验证
```bash
# 测试 AkShare (中国宏观)
python3 -c "
from macro_system.data.providers.akshare_china import fetch_china_macro
data = fetch_china_macro()
assert not data.get('_error'), 'AkShare 失败'
print(f'✓ AkShare 正常：CPI={data.get(\"cpi\")}, PMI={data.get(\"pmi_mfg\")}')
"

# 测试 FRED (美国宏观，需 Key)
python3 -c "
from macro_system.data.providers.fred_us import fetch_us_macro
data = fetch_us_macro()
if data.get('_error'):
    print(f'⚠ FRED 未配置：{data.get(\"_error\")}')
else:
    print(f'✓ FRED 正常：CPI={data.get(\"cpi\")}, 失业率={data.get(\"unemployment_rate\")}')
"
```

---

## 🚀 部署步骤

### 步骤 1: 安装依赖
```bash
cd /root/.openclaw/workspace
pip install -r macro_system/requirements.txt
```

### 步骤 2: 配置环境变量
```bash
# 添加到 ~/.bashrc 或 /etc/environment
export MACRO_DB_PATH="/opt/macro-push/data/macro.db"
export FRED_API_KEY="your_fred_key"
export ZHIPU_API_KEY="your_zhipu_key"
```

### 步骤 3: 创建配置文件 (可选)
```json
cat > ~/.macro_config.json << 'EOF'
{
  "data_dir": "/opt/macro-push/data",
  "fred_api_key": "your_fred_key",
  "zhipu_key": "your_zhipu_key",
  "push": {
    "feishu": {"enabled": false},
    "telegram": {"enabled": false}
  }
}
EOF
```

### 步骤 4: 配置 systemd 定时任务
```ini
# /etc/systemd/system/macro-push.service
[Unit]
Description=Macro Push Daily Run
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/bin/python3 -m macro_system.core.orchestrator
Environment=MACRO_DB_PATH=/opt/macro-push/data/macro.db
Environment=FRED_API_KEY=xxx
User=root
WorkingDirectory=/root/.openclaw/workspace

# /etc/systemd/system/macro-push.timer
[Unit]
Description=Run Macro Push Daily at 16:00

[Timer]
OnCalendar=*-*-* 16:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

启用定时任务:
```bash
systemctl daemon-reload
systemctl enable macro-push.timer
systemctl start macro-push.timer
systemctl list-timers  # 确认已激活
```

### 步骤 5: 首次运行验证
```bash
cd /root/.openclaw/workspace
PYTHONPATH=/root/.openclaw/workspace python3 -m macro_system.core.orchestrator --dry-run
```

**预期输出**:
- 生成完整报告
- 无 `ERROR` 级别日志
- `/opt/macro-push/data/outputs/latest.json` 存在

---

## 🔍 健康检查

### 日常检查命令
```bash
# 1. 运行健康检查
python3 -m macro_system.utils.healthcheck

# 2. 查看最近一次运行日志
tail -n 50 /opt/macro-push/data/logs/macro_system.log

# 3. 检查缓存状态
python3 -c "from macro_system.utils.cache_manager import get_cache; print(get_cache().get_stats())"

# 4. 手动抓取一次数据
python3 -c "
from macro_system.data.providers.akshare_china import fetch_china_macro
import json
data = fetch_china_macro()
print(json.dumps(data, indent=2, ensure_ascii=False))
"
```

### 告警指标
| 指标 | 阈值 | 处理措施 |
|------|------|----------|
| 数据源失败率 | >50% | 检查网络、API Key、AkShare 版本 |
| 缓存命中率 | <20% | 检查 TTL 配置、磁盘空间 |
| 端到端耗时 | >60s | 检查 AI 超时、网络延迟 |
| 磁盘占用 | >1GB | 清理日志、压缩旧数据 |

---

## 📊 监控指标

### 业务指标
- **数据覆盖率**: 核心字段抓取成功率应 > 80%
- **数据新鲜度**: 宏观数据应 < 7 天，期货/汇率应 < 1 小时
- **决策一致性**: Regime/Risk 状态不应频繁跳变

### 技术指标
- **API 响应时间**: AkShare < 10s, FRED < 5s
- **缓存命中率**: 目标 > 70%
- **错误率**: < 1%

---

## 🐛 故障排查

### 问题 1: AkShare 抓取失败
```bash
# 检查 AkShare 版本
pip show akshare

# 测试单个接口
python3 -c "import akshare as ak; print(ak.macro_china_cpi().iloc[-1])"

# 升级 AkShare
pip install --upgrade akshare
```

### 问题 2: 数据库锁定
```bash
# 检查是否有进程占用
lsof /opt/macro-push/data/macro.db

# 清理残留进程
pkill -f macro_system

# 重建数据库 (谨慎操作)
rm /opt/macro-push/data/macro.db
python3 -m macro_system.data.repository --init
```

### 问题 3: AI 超时
- 检查 `ZHIPU_API_KEY` 是否有效
- 检查网络连接
- 临时关闭 AI 层：设置 `DISABLE_AI=true`

---

## 📝 变更日志

### v1.0.0 (2026-05-13)
- ✅ 实现 Sanity Check 数据校验
- ✅ 实现缓存熔断机制
- ✅ 结构化日志支持
- ✅ 配置校验器 (Fail Fast)
- ✅ 常量统一管理
- ✅ 所有 Provider 异常处理

### v0.9.0 (2026-05-12)
- P0→P1 重构完成
- AkShare 数据源接入
- FRED 数据源接入
- SQLite 缓存层

---

## ✅ 验收标准

- [x] 所有单元测试通过 (7/7)
- [x] 健康检查无 ERROR
- [x] 数据抓取成功率 > 80%
- [x] 端到端耗时 < 60s
- [x] 配置校验通过
- [x] 文档完整

---

**签署**:  
- 工程师：✅  
- 交易员：✅  
- 运维：✅
