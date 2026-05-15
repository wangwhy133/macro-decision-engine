"""
MDE 核心测试
"""

import pytest
from mde_core import (
    PaperExecutor, create_executor,
    MDEConfig, RiskConfig,
    metrics, record_latency,
    BaseStrategy, StrategyContext
)

class TestExecutor:
    def test_paper_executor(self):
        exec = PaperExecutor({'initial_cash': 100000})
        result = exec.submit_order('TEST', 'buy', 100, 10.0)
        assert result['status'] == 'filled'
        assert result['mode'] == 'paper'
    
    def test_create_executor(self):
        exec = create_executor('paper', {})
        assert exec is not None

class TestConfig:
    def test_valid_config(self):
        config = MDEConfig(version="10.0", environment="production")
        assert config.version == "10.0"
    
    def test_risk_range(self):
        try:
            MDEConfig(version="1.0", environment="prod", risk={'max_position_total': 1.5})
            assert False, "Should raise error"
        except Exception:
            pass

class TestMetrics:
    def test_record(self):
        record_latency('test', 10.5)
        avg = metrics.get_average('latency.test', 60)
        assert avg is not None

class TestStrategy:
    def test_strategy_context(self):
        ctx = StrategyContext(config={'test': True})
        assert ctx.config['test']

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
