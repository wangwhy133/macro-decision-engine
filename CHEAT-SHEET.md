# 🚀 宏观经济数据监控系统 - 快速上手速查表

> 打印此页或保存在桌面，以便随时查阅。

---

## ⚡ 一、常用命令速查

| 目的 | 命令 |
|:-----|:-----|
| **启动系统** | `bash start.sh` |
| **健康检查** | `./venv/bin/python -m macro_system check` |
| **运行采集** | `./venv/bin/python -m macro_system run` |
| **启动看板** | `./venv/bin/streamlit run macro_system/dashboard.py` |
| **清理数据** | `./venv/bin/python -m macro_system vacuum` |
| **查看日志** | `tail -f logs/daily.log` |

---

## 🔑 二、API Key 获取链接

| 名称 | 用途 | 获取链接 | 必需性 |
|:----:|:----:|:--------:|:------:|
| **FRED** | 美国数据 | [点击获取](https://fred.stlouisfed.org/docs/api/api_key.html) | ⭐⭐⭐ 必需 |
| **智谱 AI** | 智能分析 | [点击获取](https://open.bigmodel.cn/) | ⭐⭐ 推荐 |
| **Telegram** | 消息推送 | [点击获取](https://t.me/BotFather) | ⭐ 可选 |

---

## 🛠️ 三、故障排查速查

| 现象 | 可能原因 | 解决方法 |
|:-----|:---------|:---------|
| 报错 `No module` | 虚拟环境未激活 | 使用 `./venv/bin/python` 前缀执行 |
| 报错 `API Key 无效` | Key 填错或未填 | 检查 `.env` 文件，确保无空格 |
| 看板打不开 | 端口被占用 | 检查防火墙或更换端口 `--server.port 8502` |
| 采集无数据 | 网络不通 | 检查服务器 `ping www.google.com` |

---

## 📂 四、关键文件路径

| 文件 | 路径 | 说明 |
|:-----|:-----|:-----|
| **配置文件** | `.env` | 存放 API Keys |
| **运行日志** | `logs/daily.log` | 查看采集历史 |
| **数据库** | `/opt/macro-push/data/macro.db` | 数据存储位置 |
| **依赖列表** | `requirements.txt` | Python 包列表 |

---

## 📅 五、日常运维清单

- [ ] **每日**: 查看 Dashboard 数据是否更新
- [ ] **每周**: 检查 `logs/daily.log` 有无报错
- [ ] **每月**: 运行一次 `vacuum` 清理数据库
- [ ] **每季**: 检查 API Key 是否过期

---

## 🆘 六、紧急求助

如果遇到无法解决的问题：
1. 查看 [SYSTEM-SUMMARY.md](./SYSTEM-SUMMARY.md) 获取详细日志
2. 检查 `.env` 配置是否正确
3. 尝试重启系统：`bash start.sh`

---

<div align="center">

**🎉 系统已就绪，祝您使用愉快！**

</div>
