# Macro System 快速开始指南

## 🚀 5 分钟快速部署

### 1. 安装依赖
```bash
cd /root/.openclaw/workspace/macro_system
pip install -r requirements.txt
```

### 2. 配置环境变量
创建 `~/.macro.env` 文件：
```bash
FRED_API_KEY=your_fred_key_here
ZHIPU_API_KEY=your_zhipu_key_here
MACRO_DB_PATH=/opt/macro-push/data/macro.db
```

### 3. 运行健康检查
```bash
python -m macro_system check
```

### 4. 首次运行
```bash
# 空跑测试
python -m macro_system run --dry-run

# 正式运行
python -m macro_system run
```

## 📋 常用命令

| 命令 | 说明 |
|------|------|
| `python -m macro_system run` | 运行主流程 |
| `python -m macro_system run --dry-run` | 空跑测试 |
| `python -m macro_system check` | 健康检查 |
| `python -m macro_system vacuum` | 清理数据库 |
| `python -m macro_system status` | 查看状态 |

## 🔧 故障排查

### 问题 1: 配置校验失败
```bash
# 检查环境变量
echo $FRED_API_KEY

# 检查 .env 文件
cat ~/.macro.env
```

### 问题 2: 数据库锁定
```bash
# 清理锁文件
rm /opt/macro-push/data/macro.db.lock

# 整理数据库
python -m macro_system vacuum
```

## 📚 更多文档
- [生产部署指南](./README-PRODUCTION.md)
- [架构说明](./ARCHITECTURE.md)
- [配置说明](./config/settings.py)
