# Macro System 生产环境部署清单 (v1.2.0)

**生成时间**: 2026-05-13  
**版本**: v1.2.0 (Final)  
**状态**: ✅ 就绪

---

## 📦 1. 核心文件清单
确保以下文件存在于代码库中：

### 核心代码
- [x] `macro_system/__main__.py` (CLI 入口)
- [x] `macro_system/cli.py` (命令行工具)
- [x] `macro_system/core/orchestrator.py` (主流程编排)
- [x] `macro_system/data/collector.py` (数据收集)
- [x] `macro_system/data/providers/akshare_china.py` (AkShare 源)
- [x] `macro_system/data/providers/fred_us.py` (FRED 源)

### 工具模块
- [x] `macro_system/utils/cache_manager.py` (缓存管理)
- [x] `macro_system/utils/file_lock.py` (文件锁)
- [x] `macro_system/utils/json_utils.py` (JSON 序列化)
- [x] `macro_system/utils/anomaly_detector.py` (突变检测)
- [x] `macro_system/utils/heartbeat.py` (心跳机制)
- [x] `macro_system/utils/disk_utils.py` (磁盘工具)
- [x] `macro_system/utils/logger.py` (日志系统)
- [x] `macro_system/utils/retry.py` (重试机制)

### 配置模块
- [x] `macro_system/config/settings.py` (配置加载)
- [x] `macro_system/config/config_validator.py` (配置校验)
- [x] `macro_system/config/constants.py` (常量定义)

### 依赖与文档
- [x] `requirements.txt`
- [x] `QUICKSTART.md`
- [x] `README-PRODUCTION.md`
- [x] `DEPLOY-MANIFEST.md` (本文件)

---

## 🛠️ 2. 环境准备 (目标服务器)

### 前置条件
- [ ] Python 3.10+
- [ ] pip3
- [ ] 网络连接 (访问 AkShare/FRED)
- [ ] 磁盘空间 > 1GB

### 安装步骤
```bash
# 1. 克隆代码 (假设已上传到 Git)
git clone <repo_url> /opt/macro-system
cd /opt/macro-system/macro_system

# 2. 安装依赖
pip install -r requirements.txt

# 3. 创建数据目录
mkdir -p /opt/macro-push/data
chown -R $(whoami):$(whoami) /opt/macro-push
```

---

## ⚙️ 3. 配置步骤

### 方式 A: 使用 .env 文件 (推荐)
创建 `~/.macro.env`:
```bash
cat > ~/.macro.env << EOF
FRED_API_KEY=your_fred_key_here
ZHIPU_API_KEY=your_zhipu_key_here
MACRO_DB_PATH=/opt/macro-push/data/macro.db
MACRO_LOG_LEVEL=INFO
EOF
```

### 方式 B: 使用配置文件
创建 `~/.macro_config.json`:
```json
{
  "fred_api_key": "your_fred_key",
  "zhipu_key": "your_zhipu_key",
  "data_dir": "/opt/macro-push/data"
}
```

---

## 🧪 4. 验证步骤

### 4.1 健康检查
```bash
cd /opt/macro-system/macro_system
python -m macro_system check
```
**预期输出**:
- ✅ 环境变量检查通过
- ✅ 依赖检查通过
- ✅ 数据库路径检查通过
- ✅ API Key 格式检查通过

### 4.2 空跑测试
```bash
python -m macro_system run --dry-run
```
**预期输出**:
- 生成完整报告
- 无 ERROR 级别日志
- 状态文件更新为 SUCCESS

### 4.3 正式运行
```bash
python -m macro_system run
```

---

## 📅 5. 定时任务配置 (Systemd)

### 服务文件 `/etc/systemd/system/macro-push.service`
```ini
[Unit]
Description=Macro Push Daily Run
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/bin/python3 -m macro_system run
WorkingDirectory=/opt/macro-system/macro_system
Environment=PATH=/usr/bin:/usr/local/bin
User=root
```

### 定时器文件 `/etc/systemd/system/macro-push.timer`
```ini
[Unit]
Description=Run Macro Push Daily at 16:00

[Timer]
OnCalendar=*-*-* 16:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

### 启用定时任务
```bash
systemctl daemon-reload
systemctl enable macro-push.timer
systemctl start macro-push.timer
systemctl list-timers | grep macro
```

---

## 📊 6. 监控与维护

### 日常检查
```bash
# 查看状态
python -m macro_system status

# 查看最近一次运行日志
tail -n 50 /opt/macro-push/data/logs/macro_system.log

# 检查缓存
python -c "from macro_system.utils.cache_manager import get_cache; print(get_cache().get_stats())"
```

### 定期维护
```bash
# 每月清理一次数据库碎片
python -m macro_system vacuum

# 检查磁盘空间
df -h /opt/macro-push/data
```

---

## ✅ 7. 验收标准

- [ ] 健康检查无 ERROR
- [ ] 空跑测试生成完整报告
- [ ] 定时任务正常触发
- [ ] 状态文件正常更新
- [ ] 日志文件正常写入
- [ ] 数据抓取成功率 > 90%

---

**签署**:
- 部署工程师: _______________ 日期: ___________
- 系统负责人: _______________ 日期: ___________
