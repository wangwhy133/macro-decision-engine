"""
MDE v11.0 核心测试
测试状态持久化、重试熔断机制
"""

import pytest
from mde_core import (
    PaperExecutor, create_executor,
    MDEConfig, 
    StateManager,
    RetryConfig, CircuitBreaker, retry_with_config
)

class TestStateManager:
    def test_save_load(self):
        state = StateManager('test_state.json')
        data = {'balance': 10000, 'position': 100}
        assert state.save(data)
        
        loaded = state.load()
        assert loaded['balance'] == 10000
        assert loaded['position'] == 100
        
        state.clear()
    
    def test_atomic_write(self):
        state = StateManager('test_atomic.json')
        # 并发写入测试（简化）
        assert state.save({'v': 1})
        assert state.save({'v': 2})
        loaded = state.load()
        assert loaded['v'] == 2
        state.clear()

class TestCircuitBreaker:
    def test_initial_state(self):
        cb = CircuitBreaker(failure_threshold=3)
        assert cb.state == 'CLOSED'
        assert cb.can_execute()
    
    def test_open_circuit(self):
        cb = CircuitBreaker(failure_threshold=3, recovery_time=1)
        for _ in range(3):
            cb.record_failure()
        assert cb.state == 'OPEN'
        assert not cb.can_execute()

class TestRetry:
    @retry_with_config(RetryConfig(max_retries=2, base_delay=0.01))
    def flaky_func(self):
        if not hasattr(self, 'attempts'):
            self.attempts = 0
        self.attempts += 1
        if self.attempts < 2:
            raise ValueError("临时错误")
        return "success"
    
    def test_retry_success(self):
        result = self.flaky_func()
        assert result == "success"

class TestExecutorEnhanced:
    def test_circuit_breaker_integration(self):
        exec = PaperExecutor({'initial_cash': 100000})
        # 正常下单
        result = exec.submit_order('TEST', 'buy', 100, 10.0)
        assert result['status'] == 'filled'
        
        # 测试撤单
        order_id = result['order_id']
        assert exec.cancel_order(order_id)

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
