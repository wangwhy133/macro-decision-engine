# MDE v7.0 快速入门指南

## 🚀 一键部署 (推荐)

### 方式一：Docker (生产环境)

```bash
# 1. 克隆项目
git clone https://github.com/wangwhy133/macro-decision-engine.git
cd macro-decision-engine

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，填入 MINIMAX_API_KEY

# 3. 一键启动
docker-compose up -d

# 4. 访问看板
# 浏览器打开：http://localhost:8501
# API 文档：http://localhost:8000/docs
```

### 方式二：本地开发

```bash
# 1. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境
cp .env.example .env
# 编辑 .env

# 4. 启动服务
# 启动 API
python -m src.api.main

# 启动看板
streamlit run src/dashboard/app.py
```

## 📱 使用指南

### 1. 查看信号

访问 `http://localhost:8501`，在"最新信号"面板查看：
- **买入信号 (BUY)**: 绿色，强度>7 可重点关注
- **卖出信号 (SELL)**: 红色，注意风险
- **持有 (HOLD)**: 观望

### 2. 一键下单

在"快速交易"区域：
1. 选择标的 (如 PIG)
2. 选择操作 (BUY/SELL)
3. 输入数量
4. 点击"立即下单"

### 3. 查看 API 文档

访问 `http://localhost:8000/docs` 查看完整 Swagger 文档。

示例 (curl):
```bash
# 获取组合状态
curl http://localhost:8000/portfolio

# 获取信号
curl http://localhost:8000/signals

# 下单
curl -X POST http://localhost:8000/trade \
  -H "Content-Type: application/json" \
  -d '{"symbol":"PIG","action":"BUY","shares":1000}'
```

## 🔧 常见问题

### Q: 如何修改策略参数？
A: 编辑 `.env` 文件中的配置，重启服务即可。

### Q: 数据不更新怎么办？
A: 检查爬虫容器日志：`docker logs mde-crawler`

### Q: 如何备份数据？
A: 数据卷挂载在 `./data` 目录，定期备份该目录即可。

## 📚 更多文档

- [用户手册](USER_GUIDE.md)
- [API 文档](http://localhost:8000/docs)
- [策略开发指南](STRATEGY_DEV.md)

---

**版本**: v7.0.0  
**最后更新**: 2026-05-15
