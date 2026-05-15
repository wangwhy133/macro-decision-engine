"""
MDE v13.0 高可用测试
"""

import pytest
from mde_core import (
    watchdog, default_quota,
    shadow_checker, param_optimizer,
    TradeRecord, datetime
)

class TestWatchdog:
    def test_heartbeat(self):
        assert watchdog.heartbeat()
    
    def test_memory_check(self):
        status = default_quota.check_memory()
        assert 'is_safe' in status

class TestShadowBacktest:
    def test_deviation_alert(self):
        sb = shadow_checker
        # 记录回测交易
        sb.record_backtest_trade(TradeRecord('TEST', 'buy', 10.0, 100, datetime.now(), 'backtest'))
        # 记录偏差过大的实盘交易
        sb.record_live_trade(TradeRecord('TEST', 'buy', 15.0, 100, datetime.now(), 'live'))
        assert sb.deviation_alert

class TestParamOptimizer:
    def test_optimize(self):
        opt = param_optimizer
        params = opt.optimize(None, None)
        assert 'threshold' in params

class TestResourceQuota:
    def test_gc(self):
        default_quota.force_gc()
        assert True

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
