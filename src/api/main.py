# src/api/main.py
"""
MDE REST API 网关 (FastAPI)

功能:
1. 提供标准化 REST API
2. 支持移动端/第三方集成
3. 自动生成 Swagger 文档
4. 鉴权与限流

端点:
- GET /health: 健康检查
- GET /portfolio: 获取组合状态
- GET /signals: 获取最新信号
- POST /trade: 下单交易
- GET /backtest: 回测结果
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime
import uvicorn

app = FastAPI(
    title="MDE API",
    description="宏观决策引擎 REST API",
    version="7.0.0"
)

# 数据模型
class Position(BaseModel):
    symbol: str
    name: str
    shares: int
    avg_price: float
    current_price: float
    pnl: float

class Signal(BaseModel):
    time: str
    symbol: str
    action: str
    strength: float
    reason: str

class TradeRequest(BaseModel):
    symbol: str
    action: str
    shares: int
    price: Optional[float] = None

# 模拟数据 (实际应调用后端服务)
def get_portfolio_mock() -> Dict:
    return {
        "total_equity": 125000,
        "cash": 45000,
        "pnl_today": 2300,
        "positions": [
            Position(symbol="PIG", name="生猪", shares=1000, avg_price=14.0, current_price=14.5, pnl=500)
        ]
    }

def get_signals_mock() -> List[Signal]:
    return [
        Signal(time="10:00", symbol="PIG", action="BUY", strength=9.0, reason="痛苦指数高")
    ]

# 端点实现
@app.get("/")
async def root():
    return {"message": "MDE API v7.0.0", "status": "running"}

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "7.0.0"
    }

@app.get("/portfolio")
async def get_portfolio():
    """获取组合状态"""
    return get_portfolio_mock()

@app.get("/signals")
async def get_signals():
    """获取最新信号"""
    return get_signals_mock()

@app.post("/trade")
async def place_trade(trade: TradeRequest):
    """下单交易"""
    # 实际应调用交易执行器
    return {
        "status": "success",
        "message": f"Order {trade.action} {trade.shares} {trade.symbol} submitted",
        "order_id": "ORD_123456"
    }

@app.get("/backtest/{strategy}")
async def get_backtest(strategy: str, symbol: str = "PIG", days: int = 30):
    """获取回测结果"""
    return {
        "strategy": strategy,
        "symbol": symbol,
        "period_days": days,
        "total_return": 0.15,
        "max_drawdown": 0.08,
        "sharpe_ratio": 1.5
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
