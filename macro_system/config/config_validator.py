"""
配置校验器 (Fail Fast) - 增强版
在启动时检查关键配置，包括 API Key 格式预检查
"""
import os
import sys
from typing import List, Tuple
from .settings import get_settings
from macro_system.utils.logger import get_logger

logger = get_logger("macro_system.config_validator")

def check_env_vars() -> Tuple[bool, List[str]]:
    errors = []
    recommended = {
        "FRED_API_KEY": "美国宏观数据 (FRED) 需要",
        "ZHIPU_API_KEY": "AI 分析需要",
        "MACRO_DB_PATH": "数据库路径",
    }
    missing = [f"{var} ({desc})" for var, desc in recommended.items() if var not in os.environ]
    if missing:
        logger.warning(f"以下环境变量未配置：{', '.join(missing)}")
    return True, []

def check_dependencies() -> Tuple[bool, List[str]]:
    errors = []
    core_deps = ["akshare", "pandas", "sqlite3"]
    for dep in core_deps:
        try:
            if dep == "sqlite3":
                import sqlite3
            else:
                __import__(dep)
        except ImportError:
            errors.append(f"缺少核心依赖：{dep}")
    
    optional_deps = {"fredapi": "FRED 数据源"}
    for dep, desc in optional_deps.items():
        try:
            __import__(dep)
        except ImportError:
            logger.info(f"可选依赖 {dep} 未安装：{desc}")
    
    return len(errors) == 0, errors

def check_database_path(db_path: str) -> Tuple[bool, List[str]]:
    errors = []
    db_dir = os.path.dirname(db_path)
    if not os.path.exists(db_dir):
        try:
            os.makedirs(db_dir, exist_ok=True)
            logger.info(f"创建数据库目录：{db_dir}")
        except Exception as e:
            errors.append(f"无法创建数据库目录 {db_dir}: {e}")
    elif not os.access(db_dir, os.W_OK):
        errors.append(f"数据库目录 {db_dir} 无写权限")
    return len(errors) == 0, errors

def check_api_keys() -> Tuple[bool, List[str], List[str]]:
    """检查 API Key 格式"""
    errors = []
    warnings = []
    
    fred_key = os.getenv("FRED_API_KEY", "")
    if fred_key and len(fred_key) != 32:
        warnings.append(f"FRED_API_KEY 长度异常 (应为 32): {len(fred_key)}")
    
    zhipu_key = os.getenv("ZHIPU_API_KEY", "")
    if zhipu_key and not zhipu_key.startswith("."):
        warnings.append("ZHIPU_API_KEY 格式疑似错误")
    
    return len(errors) == 0, errors, warnings

def validate_config() -> bool:
    logger.info("开始配置校验...")
    all_passed = True
    
    # 1. 环境变量
    ok, errors = check_env_vars()
    logger.info("✓ 环境变量检查通过")
    
    # 2. 依赖检查
    ok, errors = check_dependencies()
    if errors:
        for err in errors:
            logger.error(f"依赖错误：{err}")
        all_passed = False
    else:
        logger.info("✓ 依赖检查通过")
    
    # 3. 数据库路径
    settings = get_settings()
    ok, errors = check_database_path(settings.db_path)
    if errors:
        for err in errors:
            logger.error(f"数据库路径错误：{err}")
        all_passed = False
    else:
        logger.info(f"✓ 数据库路径检查通过：{settings.db_path}")
    
    # 4. API Key 预检查
    ok, errors, warnings = check_api_keys()
    for w in warnings:
        logger.warning(f"API Key 警告：{w}")
    if errors:
        for err in errors:
            logger.error(f"API Key 错误：{err}")
        all_passed = False
    else:
        logger.info("✓ API Key 格式检查通过")
    
    if all_passed:
        logger.info("✓ 所有配置校验通过")
    else:
        logger.error("✗ 配置校验失败")
    
    return all_passed

if __name__ == "__main__":
    ok = validate_config()
    sys.exit(0 if ok else 1)
