#!/usr/bin/env python3
# tests/test_all.py
"""
MDE 综合测试套件

运行所有测试:
    python -m pytest tests/ -v

运行单个测试:
    python -m pytest tests/test_risk_control.py -v
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def test_imports():
    """测试所有模块能否正常导入"""
    print("测试模块导入...")
    
    try:
        from src.risk.risk_control import RiskControlSystem, init_risk_control
        print("✅ 风控模块导入成功")
    except Exception as e:
        print(f"❌ 风控模块导入失败：{e}")
        return False
    
    try:
        from src.utils.logger import setup_logger
        print("✅ 日志模块导入成功")
    except Exception as e:
        print(f"❌ 日志模块导入失败：{e}")
        return False
    
    try:
        from src.utils.config import ConfigValidator
        print("✅ 配置模块导入成功")
    except Exception as e:
        print(f"❌ 配置模块导入失败：{e}")
        return False
    
    try:
        from src.utils.filelock import FileLock
        print("✅ 文件锁模块导入成功")
    except Exception as e:
        print(f"❌ 文件锁模块导入失败：{e}")
        return False
    
    try:
        from src.services.healthcheck import HealthCheckService
        print("✅ 健康检查模块导入成功")
    except Exception as e:
        print(f"❌ 健康检查模块导入失败：{e}")
        return False
    
    print("\n✅ 所有模块导入成功")
    return True


def test_risk_control():
    """测试风控系统"""
    print("\n测试风控系统...")
    
    from src.risk.risk_control import RiskControlSystem, TradeAction, init_risk_control
    import pandas as pd
    
    rc = init_risk_control()
    
    # 测试 1: 模拟数据标记
    df = pd.DataFrame({'A': [1, 2, 3]})
    rc.mark_as_simulation(df)
    print("✅ 模拟数据标记成功")
    
    # 测试 2: 数据源检查
    risk_level, reason = rc.check_data_source_risk("simulation")
    assert risk_level.name == "BLOCKED"
    print("✅ 模拟数据源检查通过")
    
    # 测试 3: 交易权限检查
    action, reason = rc.check_trade_permission(
        data_source="simulation",
        features={"is_simulated": True},
        decision={"action": "BUY"}
    )
    assert action == TradeAction.BLOCK
    print("✅ 交易阻断检查通过")
    
    # 测试 4: 熔断器
    rc.record_failure()
    rc.record_failure()
    rc.record_failure()
    assert rc.circuit_breaker == True
    print("✅ 熔断器触发检查通过")
    
    print("\n✅ 风控系统测试全部通过")
    return True


def test_filelock():
    """测试文件锁"""
    print("\n测试文件锁...")
    
    from src.utils.filelock import FileLock, locked_write
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "test.json")
        
        # 测试加锁写入
        success = locked_write(test_file, '{"test": 1}', timeout=5)
        assert success
        
        # 验证内容
        with open(test_file, 'r') as f:
            content = f.read()
        assert content == '{"test": 1}'
        
        print("✅ 文件锁测试通过")
    
    return True


def test_healthcheck():
    """测试健康检查"""
    print("\n测试健康检查...")
    
    from src.services.healthcheck import HealthCheckService
    
    hc = HealthCheckService()
    status = hc.get_status()
    
    # 验证返回结构
    assert 'status' in status
    assert 'checks' in status
    assert 'issues' in status
    
    print(f"系统状态：{status['status']}")
    print(f"健康度：{status['health_percentage']:.0%}")
    
    if status['issues']:
        print(f"问题：{', '.join(status['issues'])}")
    
    print("✅ 健康检查测试通过")
    return True


def test_config():
    """测试配置验证"""
    print("\n测试配置验证...")
    
    from src.utils.config import ConfigValidator
    
    validator = ConfigValidator()
    
    # 测试环境变量加载
    env_loaded = validator.load_env()
    print(f"环境变量加载：{'成功' if env_loaded else '失败'}")
    
    # 测试目录验证
    dirs_ok = validator.validate_directories(['logs', 'data/test'])
    print(f"目录验证：{'通过' if dirs_ok else '失败'}")
    
    print("✅ 配置验证测试通过")
    return True


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("MDE 综合测试套件")
    print("=" * 60)
    
    tests = [
        ("模块导入", test_imports),
        ("风控系统", test_risk_control),
        ("文件锁", test_filelock),
        ("健康检查", test_healthcheck),
        ("配置验证", test_config),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                print(f"\n❌ {name} 测试失败")
        except Exception as e:
            failed += 1
            print(f"\n❌ {name} 测试异常：{e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print(f"测试结果：{passed} 通过，{failed} 失败")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    success = run_all_tests()
    sys.exit(0 if success else 1)
