#!/usr/bin/env python3
"""P0→P1 修复验证测试套件"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def test_imports():
    """测试 1: 关键模块导入"""
    print("[1/7] 测试模块导入...")
    try:
        from macro_system.config.settings import get_settings
        from macro_system.utils.cache_manager import get_cache
        from macro_system.utils.healthcheck import run_healthcheck
        from macro_system.core.orchestrator import MacroOrchestrator
        print("  ✓ 所有模块导入成功")
        return True
    except Exception as e:
        print(f"  ✗ 导入失败：{e}")
        return False

def test_config():
    """测试 2: 配置加载"""
    print("[2/7] 测试配置加载...")
    try:
        from macro_system.config.settings import get_settings
        s = get_settings()
        assert s.data_dir, "data_dir 为空"
        print(f"  ✓ 配置正常：data_dir={s.data_dir}")
        return True
    except Exception as e:
        print(f"  ✗ 配置失败：{e}")
        return False

def test_cache():
    """测试 3: 缓存管理器"""
    print("[3/7] 测试缓存管理器...")
    try:
        from macro_system.utils.cache_manager import get_cache
        cache = get_cache()
        stats = cache.get_stats()
        print(f"  ✓ 缓存正常：{stats['total_entries']} 条目")
        return True
    except Exception as e:
        print(f"  ✗ 缓存失败：{e}")
        return False

def test_healthcheck():
    """测试 4: 健康检查工具"""
    print("[4/7] 测试健康检查...")
    try:
        from macro_system.utils.healthcheck import run_healthcheck
        report = run_healthcheck()
        print(f"  ✓ 健康检查完成：{report['overall_status']}")
        return report['overall_status'] != 'error'
    except Exception as e:
        print(f"  ✗ 健康检查失败：{e}")
        return False

def test_akshare_import():
    """测试 5: AkShare 导入"""
    print("[5/7] 测试 AkShare 可用性...")
    try:
        import akshare as ak
        print(f"  ✓ AkShare 已安装：{ak.__version__ if hasattr(ak, '__version__') else 'unknown'}")
        return True
    except ImportError:
        print(f"  ⚠ AkShare 未安装 (pip install akshare)")
        return False
    except Exception as e:
        print(f"  ✗ AkShare 错误：{e}")
        return False

def test_prompts_export():
    """测试 6: Prompts 导出"""
    print("[6/7] 测试 Prompts 导出...")
    try:
        from macro_system.engines.prompts import build_opportunity_points
        result = build_opportunity_points({"standard_payload": {}})
        print(f"  ✓ build_opportunity_points 正常：{len(result)} 条")
        return True
    except Exception as e:
        print(f"  ✗ Prompts 导出失败：{e}")
        return False

def test_orchestrator_creation():
    """测试 7: Orchestrator 创建"""
    print("[7/7] 测试 Orchestrator 创建...")
    try:
        from macro_system.core.orchestrator import MacroOrchestrator
        from macro_system.config.settings import get_settings
        s = get_settings()
        orch = MacroOrchestrator(
            config={"data_dir": s.data_dir},
            dry_run=True
        )
        print(f"  ✓ Orchestrator 创建成功")
        return True
    except Exception as e:
        print(f"  ✗ Orchestrator 创建失败：{e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("P0→P1 修复验证测试套件")
    print("=" * 60)
    
    results = []
    results.append(test_imports())
    results.append(test_config())
    results.append(test_cache())
    results.append(test_healthcheck())
    results.append(test_akshare_import())
    results.append(test_prompts_export())
    results.append(test_orchestrator_creation())
    
    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"测试结果：{passed}/{total} 通过")
    
    if passed == total:
        print("✓ 所有 P0→P1 修复已验证")
        sys.exit(0)
    else:
        print(f"⚠ {total - passed} 项失败")
        sys.exit(1)
