"""
MDE 配置模型 (Pydantic 强校验)
"""

from pydantic import BaseModel, Field
from typing import Literal, Optional, Dict
import json

class RiskConfig(BaseModel):
    """风控配置"""
    max_position_total: float = Field(ge=0, le=1.0, default=0.8)
    max_drawdown_daily: float = Field(ge=0, le=0.5, default=0.05)
    max_drawdown_total: float = Field(ge=0, le=1.0, default=0.15)

class ExecutionConfig(BaseModel):
    """执行配置"""
    mode: Literal['paper', 'live', 'shadow'] = Field(default='paper')
    default_slippage: float = Field(ge=0, le=0.1, default=0.002)
    timeout_seconds: int = Field(gt=0, default=30)

class MDEConfig(BaseModel):
    """MDE 根配置模型"""
    version: str
    environment: Literal['development', 'production', 'testing'] = Field(default='production')
    strategies: Dict = Field(default_factory=dict)
    risk: Optional[RiskConfig] = None
    execution: Optional[ExecutionConfig] = None
    
    @classmethod
    def from_json_file(cls, path: str) -> 'MDEConfig':
        """从 JSON 文件加载并校验"""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls(**data)

__all__ = ['MDEConfig', 'RiskConfig', 'ExecutionConfig']
