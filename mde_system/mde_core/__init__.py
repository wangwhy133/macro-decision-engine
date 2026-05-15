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
]

def get_version():
    return __version__
