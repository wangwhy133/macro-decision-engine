# MDE System - 宏观决策引擎

[![Version](https://img.shields.io/badge/version-10.0.0-blue.svg)](https://github.com/wangwhy133/macro-system)
[![Python](https://img.shields.io/badge/python-3.10+-green.svg)](https://python.org)
[![Production Ready](https://img.shields.io/badge/production--ready-brightgreen.svg)](https://github.com/wangwhy133/macro-system)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](https://opensource.org/licenses/MIT)

---

## 📖 简介

**MDE (Macro Decision Engine)** 是一个**生产级量化交易决策系统**，专为宏观策略交易设计。系统具备完整的策略插件化、执行抽象、配置防呆、事务管理和指标收集能力，支持模拟盘、实盘和影子模式无缝切换。

> **核心理念**: 让普通人享受专业级量化交易能力

---

## ✨ 核心特性

### 🛡️ 安全稳健
- **配置防呆**: Pydantic 强类型校验，拒绝错误配置
- **事务管理**: 确保交易数据原子性和一致性
- **日志轮转**: 自动轮转防止磁盘撑爆
- **紧急制动**: 全局 Kill Switch，人工干预通道

### 🚀 灵活扩展
- **策略插件化**: 动态加载/卸载，热切换
- **执行器抽象**: 模拟盘/实盘/影子模式一键切换
- **存储接口**: 解耦具体实现，支持 SQLite/Redis/InfluxDB
- **依赖倒置**: 符合 SOLID 原则，易于维护

### 📊 专业交易
- **Bar 级回测**: 严格时序，杜绝未来函数
- **完整手续费**: 佣金 + 印花税 + 过户费全支持
- **滑点模型**: 基于订单规模和市场流动性
- **压力测试**: 黑天鹅事件回测验证

### 🔍 可观测性
- **指标收集**: 延迟、错误、系统资源全监控
- **结构化日志**: JSON 格式，ELK 友好
- **健康度评分**: 策略 Alpha 衰减自动预警

---

## 📦 安装部署

### 1. 克隆仓库
```bash
git clone https://github.com/wangwhy133/macro-system.git
cd macro-system/mde_system
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 验证安装
```bash
python -c "from mde_core import get_version; print(f'MDE v{get_version()}')"
# 输出：MDE v10.0.0
```

### 4. 运行测试
```bash
pytest tests/ -v
```

---

## 🚀 快速开始

### 基础使用

```python
from mde_core import (
    MDEConfig, 
    PaperExecutor, 
    metrics, 
    record_latency
)

# 1. 配置校验
config = MDEConfig.from_json_file("config.json")

# 2. 创建执行器 (模拟盘)
executor = PaperExecutor({'initial_cash': 100000})

# 3. 下单交易
result = executor.submit_order('000629.SZ', 'buy', 1000, 10.5)
print(f"订单状态：{result['status']}")

# 4. 记录指标
record_latency('order_submit', 15.5)
```

### 策略开发

```python
from mde_core import BaseStrategy, register_strategy

@register_strategy
class MyStrategy(BaseStrategy):
    name = "my_strategy"
    
    def on_init(self):
        self.threshold = 0.85
    
    def on_bar(self, bar):
        if bar.get('pain_index', 0) > self.threshold:
            return 1  # 买入信号
        return 0  # 持有
```

### 模式切换

```python
from mde_core import create_executor

# 模拟盘
paper = create_executor('paper', {'initial_cash': 100000})

# 影子模式 (实盘数据，模拟下单)
shadow = create_executor('shadow', {})

# 实盘 (需配置券商 API)
# live = create_executor('live', config)
```

---

## 📁 项目结构

```
mde_system/
├── mde_core/              # 核心模块
│   ├── __init__.py        # 导出
│   ├── exceptions.py      # 异常体系
│   ├── config_model.py    # Pydantic 配置
│   ├── executor.py        # 执行器抽象
│   ├── strategy.py        # 策略基类
│   └── metrics.py         # 指标收集
├── strategies/            # 策略插件
│   ├── __init__.py
│   └── pig_cycle.py       # 猪周期示例
├── tests/                 # 单元测试
│   ├── test_core.py
│   └── test_boundaries.py
├── requirements.txt       # 依赖清单
├── config.json           # 配置示例
├── README.md             # 本文档
└── DEPLOY.md             # 部署说明
```

---

## 📊 版本演进

| 版本 | 日期 | 核心能力 | 状态 |
|------|------|----------|------|
| **v10.0.0** | 2026-05-15 | 实盘就绪 (配置防呆/执行抽象) | ✅ 已发布 |
| v9.0.0 | 2026-05-15 | 架构级重构 (策略插件化) | ✅ |
| v8.0.0 | 2026-05-15 | 生产级就绪 (Bar 级回测) | ✅ |
| v7.1.0 | 2026-05-15 | 金融级加固 (滑点/压力测试) | ✅ |

---

## 🧪 测试覆盖

```bash
# 运行所有测试
pytest tests/ -v

# 边界测试
pytest tests/test_boundaries.py -v

# 覆盖率报告
pytest tests/ --cov=mde_core --cov-report=html
```

---

## 📄 相关文档

- [部署说明](DEPLOY.md) - 详细部署步骤
- [反思报告](REFLECTION_REPORT_v10.md) - v10.0.0 设计思路
- [API 文档](http://localhost:8001/docs) - Swagger 自动生成

---

## 🤝 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 📝 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

## 🙏 致谢

感谢所有贡献者和用户！

---

**MDE System - 让普通人享受专业级量化交易能力**

*实盘就绪 · 静待花开*
