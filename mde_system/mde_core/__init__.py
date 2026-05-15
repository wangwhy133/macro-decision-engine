"""
MDE Core - 完整核心模块导出 (v10.0.0)
"""

from .exceptions import (
    MDEException, DataException, StrategyException,
    RiskException, OrderException, ConfigurationException, DatabaseException
)
from .config_model import MDEConfig, RiskConfig, ExecutionConfig
from .executor import BaseExecutor, PaperExecutor, ShadowExecutor, create_executor
from .metrics import MetricCollector, metrics, record_latency, record_system
from .state import StateManager
from .retry import RetryConfig, CircuitBreaker, retry_with_config
from .data import (
    fusion_engine, NewsItem, HotTopic,
    SentimentAnalyzer, analyzer,
    HealthChecker, health_checker,
    EventChain, EventAggregator, aggregator
)
from .async_support import io_executor, run_in_thread, async_wrap
from .watchdog import ResourceQuota, Watchdog, default_quota, watchdog
from .validation import ShadowBacktest, ParameterOptimizer, shadow_checker, param_optimizer
from .dynamic_risk import DynamicRiskEngine, RiskMetrics, risk_engine
from .release import StrategyRelease, ReleaseStage, ReleaseManager, release_manager
from .trace import generate_trace_id, get_trace_id, set_trace_id, clear_trace_id, TraceContext
from .attribution import AttributionEngine, AttributionResult, attribution_engine
from .portfolio_risk import PortfolioRiskManager, PortfolioRiskMetrics, portfolio_risk_manager
from .hot_config import HotConfig, hot_config, init_hot_config

__version__ = "10.0.0"
__all__ = [
    # 异常
    'MDEException', 'DataException', 'StrategyException',
    'RiskException', 'OrderException', 'ConfigurationException', 'DatabaseException',
    # 配置
    'MDEConfig', 'RiskConfig', 'ExecutionConfig',
    # 执行器
    'BaseExecutor', 'PaperExecutor', 'ShadowExecutor', 'create_executor',
    # 指标
    'MetricCollector', 'metrics', 'record_latency', 'record_system',
    # v11.0 新增
    'StateManager',
    'RetryConfig', 'CircuitBreaker', 'retry_with_config',
    # v12.0 数据融合
    'fusion_engine', 'NewsItem', 'HotTopic',
    'SentimentAnalyzer', 'analyzer',
    'HealthChecker', 'health_checker',
    'EventChain', 'EventAggregator', 'aggregator',
    # v13.0 高可用
    'io_executor', 'run_in_thread', 'async_wrap',
    'ResourceQuota', 'Watchdog', 'default_quota', 'watchdog',
    'ShadowBacktest', 'ParameterOptimizer', 'shadow_checker', 'param_optimizer',
    # v14.0 金融级风控
    'DynamicRiskEngine', 'RiskMetrics', 'risk_engine',
    'StrategyRelease', 'ReleaseStage', 'ReleaseManager', 'release_manager',
    'generate_trace_id', 'get_trace_id', 'set_trace_id', 'clear_trace_id', 'TraceContext',
    # v15.0 长期主义
    'AttributionEngine', 'AttributionResult', 'attribution_engine',
    'PortfolioRiskManager', 'PortfolioRiskMetrics', 'portfolio_risk_manager',
    'HotConfig', 'hot_config', 'init_hot_config',
]

def get_version():
    return __version__
