"""
MDE 自定义异常体系
"""

class MDEException(Exception):
    """MDE 系统基础异常"""
    pass

class DataException(MDEException):
    """数据相关异常"""
    pass

class StrategyException(MDEException):
    """策略逻辑异常"""
    pass

class RiskException(MDEException):
    """风控触发异常"""
    pass

class OrderException(MDEException):
    """订单执行异常"""
    pass

class ConfigurationException(MDEException):
    """配置相关异常"""
    pass

class DatabaseException(MDEException):
    """数据库操作异常"""
    pass

__all__ = [
    'MDEException', 'DataException', 'StrategyException',
    'RiskException', 'OrderException', 'ConfigurationException', 'DatabaseException'
]
