"""
MDE v14.0 测试
"""

import pytest
from mde_core import (
    risk_engine, release_manager,
    generate_trace_id, TraceContext, get_trace_id
)

class TestDynamicRisk:
    def test_adjust_position(self):
        # 模拟高波动率
        returns = [0.01, -0.02, 0.05, -0.03, 0.02]
        risk_engine.update_metrics(returns, liquidity_score=0.8)
        
        limit = risk_engine.get_position_limit()
        assert 0 < limit <= 0.2
    
    def test_halt(self):
        # 模拟极端波动
        extreme_returns = [0.1] * 10
        risk_engine.update_metrics(extreme_returns)
        # 可能触发停止

class TestReleaseManager:
    def test_deploy_promote(self):
        rm = release_manager
        release = rm.deploy("test_strategy", "1.0.0")
        
        assert release.stage.name == "CANARY"
        assert release.get_position_scale() == 0.01
        
        # 模拟成功交易
        for _ in range(15):
            release.record_trade(True)
        release.promote()
        
        assert release.stage.name == "PARTIAL"
        assert release.get_position_scale() == 0.10
    
    def test_rollback(self):
        rm = release_manager
        release = rm.deploy("test_rollback", "1.0.0")
        
        # 模拟大量失败
        for _ in range(5):
            release.record_trade(False)
        
        assert release.should_rollback()

class TestTrace:
    def test_trace_context(self):
        tid = generate_trace_id()
        assert len(tid) > 0
        
        with TraceContext() as ctx:
            ctx.set('key', 'value')
            assert ctx.get('key') == 'value'

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
