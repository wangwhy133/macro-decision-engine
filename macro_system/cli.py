#!/usr/bin/env python3
"""
Macro System 命令行工具
用法:
  python -m macro_system.cli run              # 正常运行
  python -m macro_system.cli run --dry-run    # 空跑测试
  python -m macro_system.cli check            # 健康检查
  python -m macro_system.cli vacuum           # 清理数据库
  python -m macro_system.cli status           # 查看状态
"""
import sys
import argparse
import os

# 设置 PYTHONPATH
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(script_dir))

def cmd_run(args):
    """运行主流程"""
    from macro_system.core.orchestrator import create_orchestrator
    from macro_system.utils.heartbeat import update_status
    
    print("🚀 启动宏观决策系统...")
    
    if args.dry_run:
        print("🧪 模式：Dry Run (空跑)")
        orchestrator = create_orchestrator(dry_run=True)
    else:
        orchestrator = create_orchestrator(dry_run=False)
    
    try:
        orchestrator.run()
        print("✅ 运行完成")
    except Exception as e:
        print(f"❌ 运行失败：{e}")
        update_status("FAILED", str(e))
        sys.exit(1)

def cmd_check(args):
    """健康检查"""
    from macro_system.config.config_validator import validate_config
    from macro_system.utils.disk_utils import get_disk_usage, get_db_size
    from macro_system.utils.cache_manager import get_cache
    
    print("🔍 健康检查...")
    
    # 1. 配置校验
    if not validate_config():
        print("❌ 配置校验失败")
        return
    
    # 2. 磁盘检查
    disk_info = get_disk_usage("/opt/macro-push/data")
    total = disk_info.get("total", 0)
    used = disk_info.get("used", 0)
    percent = disk_info.get("percent", 0)
    print(f"💾 磁盘使用：{used:.2f}GB / {total:.2f}GB ({percent:.1f}%)")
    
    # 3. 数据库大小
    db_size = get_db_size("/opt/macro-push/data/macro.db")
    print(f"🗄️  数据库大小：{db_size:.2f}MB")
    
    # 4. 缓存统计
    cache = get_cache()
    stats = cache.get_stats()
    print(f"📦 缓存条目：{stats.get('count', 0)}")
    
    print("✅ 健康检查通过")

def cmd_vacuum(args):
    """清理数据库"""
    from macro_system.utils.disk_utils import vacuum_database, get_db_size
    
    db_path = "/opt/macro-push/data/macro.db"
    if not os.path.exists(db_path):
        print("数据库不存在")
        return
    
    size_before = get_db_size(db_path)
    print(f"🧹 整理前大小：{size_before:.2f}MB")
    
    if vacuum_database(db_path):
        size_after = get_db_size(db_path)
        saved = size_before - size_after
        print(f"✅ 整理完成，节省空间：{saved:.2f}MB")
    else:
        print("❌ 整理失败")

def cmd_status(args):
    """查看状态"""
    from macro_system.utils.heartbeat import get_status
    from datetime import datetime
    
    status = get_status()
    print("📊 系统状态")
    print(f"  状态：{status.get('status')}")
    print(f"  消息：{status.get('message')}")
    print(f"  时间：{status.get('timestamp')}")
    print(f"  PID: {status.get('pid')}")

def main():
    parser = argparse.ArgumentParser(description="Macro System CLI")
    subparsers = parser.add_subparsers(dest='command', help='命令')
    
    # run 命令
    p_run = subparsers.add_parser('run', help='运行主流程')
    p_run.add_argument('--dry-run', action='store_true', help='空跑测试')
    p_run.set_defaults(func=cmd_run)
    
    # check 命令
    p_check = subparsers.add_parser('check', help='健康检查')
    p_check.set_defaults(func=cmd_check)
    
    # vacuum 命令
    p_vacuum = subparsers.add_parser('vacuum', help='清理数据库')
    p_vacuum.set_defaults(func=cmd_vacuum)
    
    # status 命令
    p_status = subparsers.add_parser('status', help='查看状态')
    p_status.set_defaults(func=cmd_status)
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        sys.exit(0)
    
    args.func(args)

if __name__ == "__main__":
    main()
