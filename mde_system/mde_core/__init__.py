"""
MDE Core - 核心模块导出 (v10.0.0)
"""

__version__ = "10.0.0"
__all__ = [
    "MDEException", "DataException", "StrategyException",
    "RiskException", "OrderException", "ConfigurationException",
]

class MDEException(Exception):
    """MDE 基础异常"""
    pass

class RiskException(MDEException):
    """风控异常"""
    pass

class ConfigurationException(MDEException):
    """配置异常"""
    pass

# 简化版导出
def get_version():
    return "10.0.0"
