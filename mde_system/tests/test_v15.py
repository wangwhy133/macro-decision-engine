"""
MDE v15.0 测试
"""

import pytest
from mde_core import (
    attribution_engine, portfolio_risk_manager,
    hot_config, init_hot_config
)

class TestAttribution:
    def test_analyze(self):
        returns = [0.01, -0.02, 0.03]
        benchmarks = [0.01, 0.01, 0.01]
        costs = [0.001, 0.001, 0.001]
        
        result = attribution_engine.analyze(returns, benchmarks, costs)
        assert result is not None
        assert "结论" in str(result.conclusion) or "策略" in str(result.conclusion)

class TestPortfolioRisk:
    def test_update_and_check(self):
        pr = portfolio_risk_manager
        pr.update_position("s1", "stock1", 100, 10.0, "Tech")
        pr.update_position("s1", "stock2", 100, 10.0, "Finance")
        
        metrics = pr.get_metrics()
        assert metrics.total_exposure == 2000.0
        assert len(metrics.sector_concentration) == 2

class TestHotConfig:
    def test_load_and_get(self):
        # 创建临时配置
        import tempfile, json, os
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"test": {"key": 123}}, f)
            temp_path = f.name
        
        hc = init_hot_config(temp_path)
        assert hc.get('test.key') == 123
        
        os.unlink(temp_path)

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
