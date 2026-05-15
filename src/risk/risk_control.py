# src/risk/risk_control.py
"""
风控熔断系统 (生产级)

核心功能:
1. 数据源签名验证 (防篡改)
2. 三级熔断机制 (数据层/特征层/交易层)
3. 安全事件审计日志
4. 交易权限动态控制
"""

import hashlib
import json
import os
import logging
from datetime import datetime
from typing import Dict, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)

class RiskLevel(Enum):
    """风险等级"""
    SAFE = "SAFE"
    WARNING = "WARNING"
    HIGH_RISK = "HIGH_RISK"
    BLOCKED = "BLOCKED"

class TradeAction(Enum):
    """交易动作"""
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"
    REVIEW = "REVIEW"

class RiskControlSystem:
    """风控熔断系统"""
    
    def __init__(self, safe_mode: bool = False):
        self.safe_mode = safe_mode or os.getenv("MDE_SAFE_MODE", "false").lower() == "true"
        self.security_log_file = "logs/security_events.log"
        self.simulation_signatures = set()
        self.consecutive_failures = 0
        self.max_failures = 3
        self.circuit_breaker = False
        self.circuit_breaker_time = None
        
        # 加载已知的模拟数据签名
        self._load_simulation_signatures()
        
        os.makedirs("logs", exist_ok=True)
    
    def _load_simulation_signatures(self):
        """加载模拟数据签名白名单"""
        # 从配置或数据库加载已知的模拟数据签名
        # 这里简化为内存存储
        pass
    
    def generate_data_signature(self, data) -> str:
        """生成数据签名 (防篡改)"""
        try:
            import pandas as pd
            if isinstance(data, pd.DataFrame):
                # DataFrame 签名
                data_str = data.to_csv(index=False).encode('utf-8')
            else:
                # 其他类型转为字符串
                data_str = str(data).encode('utf-8')
            
            signature = hashlib.sha256(data_str).hexdigest()
            return signature
        except Exception as e:
            logger.error(f"生成数据签名失败：{e}")
            return ""
    
    def verify_data_signature(self, data, expected_signature: str) -> bool:
        """验证数据签名"""
        if not expected_signature:
            return False
        
        current_signature = self.generate_data_signature(data)
        return current_signature == expected_signature
    
    def mark_as_simulation(self, data) -> str:
        """标记数据为模拟数据并记录签名"""
        signature = self.generate_data_signature(data)
        self.simulation_signatures.add(signature)
        self._log_security_event(
            event_type="SIMULATION_MARKED",
            data_signature=signature,
            action="MARKED_AS_SIMULATION"
        )
        return signature
    
    def check_data_source_risk(self, data_source: str, data_signature: str = None) -> Tuple[RiskLevel, str]:
        """
        检查数据源风险
        
        Args:
            data_source: 数据源 (simulation/yfinance/akshare 等)
            data_signature: 数据签名
        
        Returns:
            (风险等级，原因)
        """
        # 检查是否为模拟数据
        if data_source == "simulation" or data_signature in self.simulation_signatures:
            self._log_security_event(
                event_type="SIMULATED_DATA_DETECTED",
                data_source=data_source,
                data_signature=data_signature,
                action="RISK_IDENTIFIED"
            )
            return RiskLevel.BLOCKED, "数据源为模拟数据"
        
        # 检查安全模式
        if self.safe_mode:
            return RiskLevel.WARNING, "系统处于安全模式"
        
        # 检查熔断器
        if self.circuit_breaker:
            return RiskLevel.BLOCKED, "系统熔断中"
        
        return RiskLevel.SAFE, "数据源可信"
    
    def check_feature_risk(self, features: Dict) -> Tuple[RiskLevel, str]:
        """
        检查特征风险
        
        Args:
            features: 特征字典
        
        Returns:
            (风险等级，原因)
        """
        is_simulated = features.get("is_simulated", False)
        is_safe_to_trade = features.get("is_safe_to_trade", True)
        
        if is_simulated:
            return RiskLevel.BLOCKED, "特征标记为模拟数据"
        
        if not is_safe_to_trade:
            return RiskLevel.BLOCKED, "特征标记为不安全"
        
        return RiskLevel.SAFE, "特征可信"
    
    def check_trade_permission(
        self,
        data_source: str,
        features: Dict,
        decision: Dict,
        data_signature: str = None
    ) -> Tuple[TradeAction, str]:
        """
        最终交易权限检查 (三级熔断)
        
        Args:
            data_source: 数据源
            features: 特征数据
            decision: 交易决策
            data_signature: 数据签名
        
        Returns:
            (交易动作，原因)
        """
        # 第一级：数据源检查
        risk_level, reason = self.check_data_source_risk(data_source, data_signature)
        if risk_level == RiskLevel.BLOCKED:
            self._log_security_event(
                event_type="TRADE_BLOCKED_LEVEL_1",
                data_source=data_source,
                decision=decision,
                action="BLOCKED_AT_DATA_LAYER"
            )
            return TradeAction.BLOCK, f"数据层阻断：{reason}"
        
        # 第二级：特征检查
        risk_level, reason = self.check_feature_risk(features)
        if risk_level == RiskLevel.BLOCKED:
            self._log_security_event(
                event_type="TRADE_BLOCKED_LEVEL_2",
                features=features,
                decision=decision,
                action="BLOCKED_AT_FEATURE_LAYER"
            )
            return TradeAction.BLOCK, f"特征层阻断：{reason}"
        
        # 第三级：安全模式检查
        if self.safe_mode and data_source == "simulation":
            self._log_security_event(
                event_type="TRADE_BLOCKED_LEVEL_3",
                safe_mode=self.safe_mode,
                decision=decision,
                action="BLOCKED_AT_SAFE_MODE"
            )
            return TradeAction.BLOCK, "安全模式阻断"
        
        # 检查通过
        return TradeAction.ALLOW, "交易权限验证通过"
    
    def trigger_circuit_breaker(self, reason: str = "系统异常"):
        """触发熔断器"""
        self.circuit_breaker = True
        self.circuit_breaker_time = datetime.now()
        
        self._log_security_event(
            event_type="CIRCUIT_BREAKER_TRIGGERED",
            reason=reason,
            action="CIRCUIT_BREAKER_ON"
        )
        
        logger.warning(f"🚨 熔断器已触发：{reason}")
    
    def reset_circuit_breaker(self):
        """重置熔断器"""
        self.circuit_breaker = False
        self.circuit_breaker_time = None
        self.consecutive_failures = 0
        
        self._log_security_event(
            event_type="CIRCUIT_BREAKER_RESET",
            action="CIRCUIT_BREAKER_OFF"
        )
        
        logger.info("✅ 熔断器已重置")
    
    def record_failure(self):
        """记录失败次数"""
        self.consecutive_failures += 1
        
        if self.consecutive_failures >= self.max_failures:
            self.trigger_circuit_breaker(f"连续失败{self.consecutive_failures}次")
        
        logger.warning(f"⚠️ 记录失败次数：{self.consecutive_failures}/{self.max_failures}")
    
    def record_success(self):
        """记录成功"""
        self.consecutive_failures = 0
    
    def _log_security_event(self, event_type: str, **kwargs):
        """记录安全事件日志"""
        try:
            event = {
                "timestamp": datetime.now().isoformat(),
                "event_type": event_type,
                **kwargs
            }
            
            with open(self.security_log_file, 'a') as f:
                f.write(json.dumps(event) + "\n")
        except Exception as e:
            logger.error(f"记录安全事件失败：{e}")
    
    def get_security_report(self) -> Dict:
        """获取安全报告"""
        return {
            "safe_mode": self.safe_mode,
            "circuit_breaker": self.circuit_breaker,
            "consecutive_failures": self.consecutive_failures,
            "simulation_signatures_count": len(self.simulation_signatures)
        }


# 全局风控实例
_global_risk_control = None

def get_risk_control() -> RiskControlSystem:
    """获取全局风控实例"""
    global _global_risk_control
    if _global_risk_control is None:
        _global_risk_control = RiskControlSystem()
    return _global_risk_control


def init_risk_control(safe_mode: bool = False) -> RiskControlSystem:
    """初始化风控系统"""
    global _global_risk_control
    _global_risk_control = RiskControlSystem(safe_mode=safe_mode)
    return _global_risk_control


if __name__ == "__main__":
    # 测试风控系统
    import logging
    logging.basicConfig(level=logging.INFO)
    
    rc = init_risk_control(safe_mode=True)
    
    # 测试数据源检查
    risk_level, reason = rc.check_data_source_risk("simulation")
    print(f"模拟数据源检查：{risk_level.value} - {reason}")
    
    # 测试特征检查
    features = {"is_simulated": True, "is_safe_to_trade": False}
    risk_level, reason = rc.check_feature_risk(features)
    print(f"模拟特征检查：{risk_level.value} - {reason}")
    
    # 测试交易权限
    action, reason = rc.check_trade_permission(
        data_source="simulation",
        features=features,
        decision={"action": "BUY", "confidence": 0.95}
    )
    print(f"交易权限检查：{action.value} - {reason}")
    
    # 获取安全报告
    report = rc.get_security_report()
    print(f"安全报告：{report}")
