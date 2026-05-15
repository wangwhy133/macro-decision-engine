"""
MDE v16.0 测试
"""

import pytest
from mde_core import (
    hard_stop_engine, HardStopConfig,
    decision_logger, DecisionLog,
    config_auditor
)
from datetime import datetime

class TestHardStop:
    def test_trigger_on_drawdown(self):
        engine = hard_stop_engine
        engine.initial_capital = 100000
        engine.current_capital = 70000  # 30% 亏损
        assert engine.check(10.0, 10.0, 0.0)
    
    def test_trigger_on_volatility(self):
        config = HardStopConfig(max_volatility_trigger=0.05)
        engine = HardStopEngine(config)
        engine.initial_capital = 100000
        engine.current_capital = 100000
        assert engine.check(10.0, 10.0, volatility=0.10)

class TestDecisionLogger:
    def test_log_and_retrieve(self):
        log = DecisionLog(
            timestamp=datetime.now().isoformat(),
            strategy_name="test",
            symbol="TEST",
            action="BUY",
            reason="test reason",
            data_context={},
            confidence=0.9,
            trace_id="test-trace"
        )
        decision_logger.log(log)
        # 验证文件存在
        logs = decision_logger.get_today_logs()
        assert len(logs) > 0

class TestConfigAuditor:
    def test_backup_and_rollback(self):
        import tempfile, json, os
        # 创建临时配置
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"test": 1}, f)
            temp_path = f.name
        
        auditor = config_auditor
        auditor.config_path = temp_path
        auditor.backup_dir = tempfile.mkdtemp()
        
        # 备份
        auditor.save_snapshot(operator="test", comment="test backup")
        assert len(auditor.history) > 0
        
        # 清理
        os.unlink(temp_path)

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
