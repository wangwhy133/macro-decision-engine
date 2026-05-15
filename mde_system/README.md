# MDE System - 宏观决策引擎

[![Version](https://img.shields.io/badge/version-10.0.0-blue.svg)](https://github.com/wangwhy133/macro-system)
[![Python](https://img.shields.io/badge/python-3.10+-green.svg)](https://python.org)
[![Production Ready](https://img.shields.io/badge/production-ready-brightgreen.svg)](https://github.com/wangwhy133/macro-system)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](https://opensource.org/licenses/MIT)

## 🏆 系统特性

MDE (Macro Decision Engine) 是一个**生产级量化交易决策系统**，具备完整的策略插件化、执行抽象、事务管理、指标收集能力。

### 核心能力

- **策略插件化**: 动态加载/卸载，热切换
- **执行抽象**: 模拟盘/实盘/影子模式一键切换
- **配置防呆**: Pydantic 强校验，拒绝错误配置
- **事务管理**: 确保数据原子性
- **指标收集**: 系统可观测性，监控无死角
- **日志轮转**: 自动轮转，防止磁盘撑爆

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置系统

编辑 `config.json`，Pydantic 会自动校验配置有效性。

### 3. 运行测试

```bash
pytest tests/ -v
```

### 4. 启动 Web 界面

```bash
python web_enhanced.py
# 访问 http://localhost:8001
```

## 📊 版本演进

- **v10.0.0**: 实盘就绪 (配置防呆/执行抽象/指标收集)
- **v9.0.0**: 架构级重构 (策略插件化/存储接口)
- **v8.0.0**: 生产级就绪 (Bar 级回测/进程守护)
- **v7.1.0**: 金融级加固 (滑点/压力测试/紧急制动)

## 📄 文档

- [第十轮反思报告](REFLECTION_REPORT_v10.md) - 实盘就绪
- [第十一轮反思报告](REFLECTION_REPORT_v9.md) - 架构重构
- [API 文档](http://localhost:8001/docs) - Swagger 自动生成

---

**MDE System - 让普通人享受专业级量化交易能力**

*实盘就绪 · 静待花开*
