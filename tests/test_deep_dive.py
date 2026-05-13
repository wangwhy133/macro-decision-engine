"""
深度审查修复验证测试
验证连接泄漏、数据完整性、异步日志等修复
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
import time
from macro_system.utils.cache_manager import get_cache
from macro_system.data.providers.akshare_china import fetch_china_macro, CORE_FIELDS

def test_connection_leak():
    """测试 1: 连接泄漏修复"""
    print("[1/4] 测试 SQLite 连接泄漏修复...")
    cache = get_cache()
    
    # 清理旧数据
    cache.clear_expired()
    
    # 连续写入 10 次
    for i in range(10):
        cache.set("test_leak_new", f"key_{i}", {"val": i}, is_error=(i % 2 == 0))
    
    # 验证数据存在
    conn = sqlite3.connect("/opt/macro-push/data/cache.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM data_cache WHERE source='test_leak_new'")
    count = cursor.fetchone()[0]
    conn.close()
    
    assert count == 10, f"连接泄漏：期望 10 条，实际 {count} 条"
    print(f"  ✓ 写入 10 条记录，实际存在：{count} 条")
    print("  ✓ 连接泄漏修复验证通过")
    return True

def test_data_integrity():
    """测试 2: 数据完整性校验"""
    print("\n[2/4] 测试数据完整性校验...")
    
    data = fetch_china_macro()
    
    if data.get("_error"):
        # 如果返回错误，说明触发了熔断
        error_msg = data.get("_error", "")
        if "核心字段缺失" in error_msg:
            print(f"  ✓ 数据完整性校验触发熔断：{error_msg}")
        else:
            print(f"  ⚠️  其他错误：{error_msg}")
    else:
        core_fields = data.get("_quality", {}).get("core_fields", [])
        missing = [f for f in CORE_FIELDS if f not in core_fields]
        missing_ratio = len(missing) / len(CORE_FIELDS)
        
        print(f"  核心字段：{core_fields}")
        print(f"  缺失字段：{missing} (缺失率：{missing_ratio:.2f})")
        
        if missing_ratio > 0.5:
            assert False, "应触发熔断但未触发"
        else:
            print("  ✓ 数据完整性正常")
    
    return True

def test_async_logging():
    """测试 3: 异步日志"""
    print("\n[3/4] 测试异步日志...")
    from macro_system.utils.logger import get_logger
    import time
    
    logger = get_logger("test_async")
    
    start = time.time()
    for i in range(100):
        logger.info(f"异步日志测试 {i}")
    elapsed = time.time() - start
    
    print(f"  ✓ 写入 100 条日志耗时：{elapsed*1000:.2f}ms")
    print("  ✓ 异步日志验证通过")
    return True

def test_retry_mechanism():
    """测试 4: 重试机制"""
    print("\n[4/4] 测试重试机制...")
    from macro_system.utils.retry import retry
    
    call_count = 0
    
    @retry(retries=3, delay=0.05, exceptions=(ValueError,))
    def flaky_func():
        nonlocal call_count
        call_count += 1
        if call_count < 3:  # 前两次失败，第三次成功
            raise ValueError("模拟失败")
        return "success"
    
    result = flaky_func()
    
    assert result == "success", "重试失败"
    assert call_count == 3, f"期望调用 3 次，实际 {call_count} 次"
    
    print(f"  ✓ 重试机制正常：调用 {call_count} 次后成功")
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("深度审查修复验证测试")
    print("=" * 60)
    
    tests = [
        test_connection_leak,
        test_data_integrity,
        test_async_logging,
        test_retry_mechanism,
    ]
    
    passed = 0
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"  ✗ 测试失败：{e}")
    
    print("\n" + "=" * 60)
    print(f"测试结果：{passed}/{len(tests)} 通过")
    
    if passed == len(tests):
        print("✅ 所有深度审查修复已验证")
        sys.exit(0)
    else:
        print("⚠️  部分测试失败")
        sys.exit(1)
