# tests/test_risk_control.py
"""
风控系统测试套件

测试范围:
1. 数据源验证
2. 特征层风控
3. 交易权限检查
4. 熔断机制
5. 安全事件日志
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from src.risk.risk_control import (
    RiskControlSystem,
    RiskLevel,
    TradeAction,
    init_risk_control,
    get_risk_control
)


class TestDataSignature:
    """测试数据签名"""
    
    def test_generate_signature(self):
        """测试生成数据签名"""
        rc = RiskControlSystem()
        import pandas as pd
        
        df = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
        sig1 = rc.generate_data_signature(df)
        sig2 = rc.generate_data_signature(df)
        
        assert sig1 == sig2  # 相同数据应生成相同签名
        assert len(sig1) == 64  # SHA256 长度为 64
    
    def test_signature_changes_with_data(self):
        """测试数据变化时签名也变化"""
        rc = RiskControlSystem()
        import pandas as pd
        
        df1 = pd.DataFrame({'A': [1, 2, 3]})
        df2 = pd.DataFrame({'A': [1, 2, 4]})  # 最后一个值不同
        
        sig1 = rc.generate_data_signature(df1)
        sig2 = rc.generate_data_signature(df2)
        
        assert sig1 != sig2


class TestDataSourceRisk:
    """测试数据源风险检查"""
    
    def test_simulation_blocked(self):
        """测试模拟数据被阻断"""
        rc = RiskControlSystem()
        
        # 标记为模拟
        import pandas as pd
        df = pd.DataFrame({'A': [1, 2, 3]})
        rc.mark_as_simulation(df)
        signature = rc.generate_data_signature(df)
        
        # 检查应被阻断
        risk_level, reason = rc.check_data_source_risk("simulation", signature)
        assert risk_level == RiskLevel.BLOCKED
    
    def test_real_data_allowed(self):
        """测试真实数据允许"""
        rc = RiskControlSystem()
        
        risk_level, reason = rc.check_data_source_risk("yfinance")
        assert risk_level == RiskLevel.SAFE


class TestFeatureRisk:
    """测试特征层风控"""
    
    def test_simulated_feature_blocked(self):
        """测试模拟特征被阻断"""
        rc = RiskControlSystem()
        
        features = {
            "is_simulated": True,
            "is_safe_to_trade": False
        }
        
        risk_level, reason = rc.check_feature_risk(features)
        assert risk_level == RiskLevel.BLOCKED
    
    def test_safe_feature_allowed(self):
        """测试安全特征允许"""
        rc = RiskControlSystem()
        
        features = {
            "is_simulated": False,
            "is_safe_to_trade": True
        }
        
        risk_level, reason = rc.check_feature_risk(features)
        assert risk_level == RiskLevel.SAFE


class TestTradePermission:
    """测试交易权限检查"""
    
    def test_simulation_trade_blocked(self):
        """测试模拟数据交易被阻断"""
        rc = init_risk_control()
        
        import pandas as pd
        df = pd.DataFrame({'A': [1, 2, 3]})
        rc.mark_as_simulation(df)
        signature = rc.generate_data_signature(df)
        
        action, reason = rc.check_trade_permission(
            data_source="simulation",
            features={"is_simulated": True},
            decision={"action": "BUY"},
            data_signature=signature
        )
        
        assert action == TradeAction.BLOCK
        assert "阻断" in reason or "BLOCK" in reason
    
    def test_real_trade_allowed(self):
        """测试真实数据交易允许"""
        rc = RiskControlSystem(safe_mode=False)
        
        action, reason = rc.check_trade_permission(
            data_source="yfinance",
            features={"is_simulated": False, "is_safe_to_trade": True},
            decision={"action": "BUY"}
        )
        
        assert action == TradeAction.ALLOW


class TestCircuitBreaker:
    """测试熔断机制"""
    
    def test_circuit_breaker_triggers(self):
        """测试熔断器触发"""
        rc = RiskControlSystem()
        rc.max_failures = 3
        
        # 连续失败 3 次应触发熔断
        for i in range(3):
            rc.record_failure()
        
        assert rc.circuit_breaker == True
    
    def test_circuit_breaker_resets(self):
        """测试熔断器重置"""
        rc = RiskControlSystem()
        
        rc.trigger_circuit_breaker("测试")
        assert rc.circuit_breaker == True
        
        rc.reset_circuit_breaker()
        assert rc.circuit_breaker == False
        assert rc.consecutive_failures == 0


class TestSecurityLogging:
    """测试安全事件日志"""
    
    def test_security_event_logged(self):
        """测试安全事件被记录"""
        import tempfile
        import json
        
        with tempfile.TemporaryDirectory() as tmpdir:
            rc = RiskControlSystem()
            rc.security_log_file = os.path.join(tmpdir, "security.log")
            
            rc._log_security_event("TEST_EVENT", test_data="test")
            
            # 检查日志文件
            assert os.path.exists(rc.security_log_file)
            
            with open(rc.security_log_file, 'r') as f:
                content = f.read()
                assert "TEST_EVENT" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
