"""
MDE 策略灰度发布管理
支持 Canary Release (金丝雀发布)
"""

from typing import Dict, Any, Optional, List
from enum import Enum
from datetime import datetime

class ReleaseStage(Enum):
    CANARY = "canary"  # 灰度阶段 (1% 资金)
    PARTIAL = "partial" # 部分发布 (10% 资金)
    FULL = "full"       # 全量发布 (100% 资金)

class StrategyRelease:
    """策略发布实例"""
    
    def __init__(self, strategy_name: str, version: str):
        self.strategy_name = strategy_name
        self.version = version
        self.stage = ReleaseStage.CANARY
        self.start_time = datetime.now()
        self.error_count = 0
        self.success_count = 0
        self.is_active = True
    
    def record_trade(self, success: bool):
        if success:
            self.success_count += 1
        else:
            self.error_count += 1
    
    def promote(self):
        """提升发布阶段"""
        if self.stage == ReleaseStage.CANARY:
            if self.error_count == 0 and self.success_count >= 10:
                self.stage = ReleaseStage.PARTIAL
                print(f"✅ {self.strategy_name} 提升至部分发布")
        elif self.stage == ReleaseStage.PARTIAL:
            if self.error_count == 0 and self.success_count >= 50:
                self.stage = ReleaseStage.FULL
                print(f"✅ {self.strategy_name} 提升至全量发布")
    
    def rollback(self):
        """回滚"""
        self.is_active = False
        print(f"❌ {self.strategy_name} 已回滚")
    
    def get_position_scale(self) -> float:
        """获取当前资金比例"""
        if self.stage == ReleaseStage.CANARY:
            return 0.01
        elif self.stage == ReleaseStage.PARTIAL:
            return 0.10
        return 1.0
    
    def should_rollback(self) -> bool:
        """判断是否应该回滚"""
        # 错误率超过 10% 回滚
        total = self.success_count + self.error_count
        if total > 0 and (self.error_count / total) > 0.1:
            return True
        return False

class ReleaseManager:
    """发布管理器"""
    
    def __init__(self):
        self.releases: Dict[str, StrategyRelease] = {}
    
    def deploy(self, strategy_name: str, version: str) -> StrategyRelease:
        """部署新版本"""
        release = StrategyRelease(strategy_name, version)
        self.releases[strategy_name] = release
        print(f"🚀 部署 {strategy_name} v{version} (灰度阶段)")
        return release
    
    def get_release(self, strategy_name: str) -> Optional[StrategyRelease]:
        return self.releases.get(strategy_name)

# 全局实例
release_manager = ReleaseManager()

__all__ = ['StrategyRelease', 'ReleaseStage', 'ReleaseManager', 'release_manager']
