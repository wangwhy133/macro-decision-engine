# P0 → P1 修复与优化总结

## ✅ 已完成的修复（2026-05-13）

### 1. 导出缺失修复
**问题**: `macro_push.py` 导入 `macro_system.engines.prompts.build_opportunity_points` 失败

**修复**:
- 在 `/root/.openclaw/workspace/macro_system/engines/prompts.py` 中添加 `build_opportunity_points()` 函数
- 作为 `_structured_opportunity_points()` 的兼容层包装器
- 保持向后兼容，支持 legacy 测试

### 2. 导入错误清理
**问题**: `macro_push.py` 导入了不存在的符号

**修复**:
- 删除 `from macro_system.core.standard_output import get_macro`（未使用）
- 删除 `from macro_system.output.result_builder import PushDeliveryError`（未使用）

### 3. 兼容层完善
**问题**: subprocess 调用的 `get_*` 系列函数缺失

**修复**: 在 `macro_push.py` 中添加完整的 legacy 兼容层：
```python
def get_macro(): ...        # China macro data
def get_pe(): ...           # Valuation data
def get_futures(): ...      # Global futures
def get_zt_emotion(): ...   # Limit-up emotion
def get_us_macro(): ...     # US macro
def get_us_bond(): ...      # US bond yields
def get_north_flow(): ...   # Northbound capital flow
```

当前实现返回 fallback 数据，等待真实数据源接入。

### 4. subprocess 错误处理增强
**修复**:
- 添加 try/except 捕获 ImportError
- 添加函数存在性检查 `hasattr(macro_push, function_name)`
- 改进错误日志输出，区分 timeout 和其他错误

---

## 📊 当前状态

### 运行验证
```bash
cd /root/.openclaw/workspace
PYTHONPATH=/root/.openclaw/workspace python3 -c "
from macro_system.core.orchestrator import create_orchestrator
o = create_orchestrator(dry_run=True)
o.run()
"
```

**结果**: ✅ 完整流程通过
- [x] 数据收集（fallback 模式）
- [x] 叙事构建
- [x] 标准输出生成
- [x] AI 分析（超时但已优雅处理）
- [x] 报告格式化
- [x] 每日运行持久化

### 测试验证
```bash
cd /root/.openclaw/workspace
python3 -m pytest macro_system/tests/ -v
```

**结果**: ✅ 130/130 测试通过

---

## 🔧 架构改进

### 修复前
```
macro_push.py (CLI)
  ├─ 直接导入所有函数
  ├─ 循环依赖风险
  └─ 错误处理弱

collector.py
  └─ subprocess 导入整个 macro_push
       └─ 任一导入失败 → 全挂
```

### 修复后
```
macro_push.py (CLI + Legacy 兼容层)
  ├─ 显式导出所有 get_* 函数
  ├─ 完善的错误处理
  └─ 清晰的职责边界

collector.py
  └─ subprocess 导入 macro_push
       ├─ try/except 捕获导入错误
       ├─ hasattr 检查函数存在
       └─ 优雅 fallback 机制
```

---

## 🎯 遗留问题（P2+）

### 1. 数据源未接入
**现状**: 所有数据源返回 fallback 数据（None/空字典）

**下一步**:
- 实现真实的 API 调用（AkShare, FRED, FxPro 等）
- 配置 API Keys
- 添加数据缓存和刷新策略

### 2. AI 分析超时
**现状**: AI 层调用超时（60 秒）

**原因**: 
- 可能是 API Key 未配置
- 或网络问题

**下一步**:
- 检查 `ZHIPU_KEY` 配置
- 验证 AI 服务连通性
- 考虑异步调用或缩短 prompt

### 3. 硬编码路径
**现状**: 多处使用硬编码路径
- `/opt/macro-push/data/macro.db`
- `/opt/macro-push/data/outputs/`

**下一步**:
- 统一从配置加载
- 支持环境变量覆盖

---

## 📝 工程建议

###  交易员视角
1. **数据质量优先**: 宁可输出 N/A 也不编造数据 ✅ 已实现
2. **风险第一**: 数据不足时暂停机会输出 ✅ 已实现
3. **可解释性**: 所有判断必须有数据支持 ✅ 已实现

### 程序员视角
1. **测试覆盖**: 保持 130+ 测试用例 ✅
2. **错误处理**: 所有外部调用都有 fallback ✅
3. **日志记录**: 关键步骤有日志 ✅

### 工程师视角
1. **渐进式重构**: 保持向后兼容 ✅
2. **职责分离**: CLI 与业务逻辑分离 ✅
3. **配置驱动**: 避免硬编码（待改进）

---

## 🚀 下一步行动项

### P1.5（本周）
- [ ] 配置真实数据源 API Keys
- [ ] 验证 AkShare 数据抓取
- [ ] 修复 AI 分析超时问题

### P2（下周）
- [ ] 实现 Feishu/Telegram 推送
- [ ] 添加数据缓存层（SQLite）
- [ ] 配置定时任务（cron/systemd）

### P3（下月）
- [ ] 复盘数据库（记录每日决策与实际走势）
- [ ] 回测框架验证
- [ ] Dashboard 可视化

---

## 📚 参考文档

- [ARCHITECTURE.md](./ARCHITECTURE.md) - 架构说明
- [data/source_registry.py](./data/source_registry.py) - 数据源注册表
- [core/orchestrator.py](./core/orchestrator.py) - 编排器实现

---

*最后更新：2026-05-13*
*状态：P0→P1 完成，准备接入真实数据源*
