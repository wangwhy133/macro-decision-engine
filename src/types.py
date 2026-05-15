# src/types.py
"""
类型定义模块

提供统一的类型注解，增强代码可读性和 IDE 支持
"""

from typing import Dict, List, Optional, Union, Any, Literal
from dataclasses import dataclass
from enum import Enum


# 决策动作类型
DecisionAction = Literal['BUY', 'SELL', 'HOLD']

# 风险等级
RiskLevelType = Literal['SAFE', 'WARNING', 'HIGH_RISK', 'BLOCKED']

# 数据源类型
DataSourceType = Literal['yfinance', 'akshare', 'simulation', 'real']

# 市场状态
MarketRegimeType = Literal['risk_on', 'risk_off', 'overbought', 'oversold']

# 趋势类型
TrendType = Literal['bullish', 'bearish', 'neutral']


@dataclass
class FeatureData:
    """特征数据"""
    timestamp: str
    symbol: str
    price: float
    rsi: float
    macd: float
    volatility: float
    trend: TrendType
    market_regime: MarketRegimeType
    is_simulated: bool
    is_safe_to_trade: bool
    data_source: DataSourceType


@dataclass
class DecisionResult:
    """决策结果"""
    action: DecisionAction
    confidence: float
    summary: str
    market_opinion: str
    macro_opinion: str
    risk_opinion: str


@dataclass
class RiskReport:
    """风险报告"""
    safe_mode: bool
    circuit_breaker: bool
    consecutive_failures: int
    simulation_signatures_count: int


@dataclass
class HealthStatus:
    """健康状态"""
    status: Literal['healthy', 'degraded', 'unhealthy']
    timestamp: str
    uptime_seconds: float
    health_percentage: float
    issues: List[str]
    checks: Dict[str, Any]


# 通用类型别名
JSONDict = Dict[str, Any]
JSONList = List[Any]
FeatureDict = Dict[str, Any]
DecisionDict = Dict[str, Any]
