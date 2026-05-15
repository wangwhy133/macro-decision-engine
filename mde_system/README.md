# MDE System v10.0.0

[![Version](https://img.shields.io/badge/version-10.0.0-blue.svg)](https://github.com/wangwhy133/macro-system)
[![Python](https://img.shields.io/badge/python-3.10+-green.svg)](https://python.org)
[![Production Ready](https://img.shields.io/badge/production--ready-brightgreen.svg)](https://github.com/wangwhy133/macro-system)

## 🏆 特性

- **配置防呆**: Pydantic 强校验
- **执行抽象**: 模拟/实盘/影子切换
- **策略插件**: 动态加载
- **指标收集**: 系统监控
- **事务管理**: 数据原子性

## 🚀 安装

```bash
pip install -r requirements.txt
python -c "from mde_core import get_version; print(get_version())"
```

## 📊 核心模块

- `exceptions`: 异常体系
- `config_model`: 配置校验
- `executor`: 执行器抽象
- `strategy`: 策略基类
- `metrics`: 指标收集

## 📄 文档

- [部署说明](DEPLOY.md)
- [反思报告](REFLECTION_REPORT_v10.md)

---

**MDE System - 让普通人享受专业级量化交易能力**
