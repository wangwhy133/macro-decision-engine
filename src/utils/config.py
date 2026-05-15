# src/utils/config.py
"""
配置管理与验证模块

功能:
1. 环境变量验证
2. API Key 检查
3. 配置文件完整性
4. 启动前健康检查
"""

import os
import sys
import logging
from typing import Optional, List
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class ConfigurationError(Exception):
    """配置错误"""
    pass


class ConfigValidator:
    """配置验证器"""
    
    def __init__(self, env_file: str = ".env"):
        self.env_file = env_file
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def load_env(self) -> bool:
        """加载环境变量文件"""
        if not os.path.exists(self.env_file):
            self.errors.append(f"配置文件不存在：{self.env_file}")
            return False
        
        try:
            load_dotenv(dotenv_path=self.env_file, encoding='utf-8')
            logger.info(f"环境变量已加载：{self.env_file}")
            return True
        except Exception as e:
            self.errors.append(f"加载环境变量失败：{e}")
            return False
    
    def validate_api_key(self, key_name: str = "MINIMAX_API_KEY") -> bool:
        """验证 API Key"""
        api_key = os.getenv(key_name, "")
        
        if not api_key:
            self.errors.append(f"API Key 未配置：{key_name}")
            return False
        
        if len(api_key) < 10:
            self.errors.append(f"API Key 格式错误 (过短): {key_name}")
            return False
        
        # 脱敏记录
        masked_key = f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) > 8 else "****"
        logger.info(f"API Key 验证通过：{key_name} = {masked_key}")
        return True
    
    def validate_required_vars(self, required_vars: List[str]) -> bool:
        """验证必需的环境变量"""
        all_present = True
        for var in required_vars:
            if not os.getenv(var):
                self.errors.append(f"必需的环境变量缺失：{var}")
                all_present = False
        return all_present
    
    def validate_directories(self, directories: List[str]) -> bool:
        """验证并创建必要目录"""
        all_ok = True
        for dir_path in directories:
            try:
                Path(dir_path).mkdir(parents=True, exist_ok=True)
                logger.info(f"目录已准备：{dir_path}")
            except Exception as e:
                self.errors.append(f"创建目录失败 {dir_path}: {e}")
                all_ok = False
        return all_ok
    
    def validate_python_version(self, min_version: tuple = (3, 8)) -> bool:
        """验证 Python 版本"""
        current = sys.version_info[:2]
        if current < min_version:
            self.errors.append(f"Python 版本过低：{current[0]}.{current[1]}, 需要 {'.'.join(map(str, min_version))}+")
            return False
        
        logger.info(f"Python 版本验证通过：{'.'.join(map(str, current))}")
        return True
    
    def run_all_checks(self) -> bool:
        """运行所有检查"""
        logger.info("开始配置验证...")
        
        # 1. Python 版本
        self.validate_python_version()
        
        # 2. 加载环境变量
        env_loaded = self.load_env()
        
        # 3. 验证 API Key
        if env_loaded:
            self.validate_api_key("MINIMAX_API_KEY")
        
        # 4. 验证目录
        required_dirs = ["logs", "data/raw", "data/features"]
        self.validate_directories(required_dirs)
        
        # 输出结果
        if self.errors:
            logger.error("配置验证失败:")
            for error in self.errors:
                logger.error(f"  - {error}")
            return False
        
        if self.warnings:
            logger.warning("配置验证警告:")
            for warning in self.warnings:
                logger.warning(f"  - {warning}")
        
        logger.info("✅ 配置验证通过")
        return True


def validate_and_init() -> bool:
    """
    验证配置并初始化
    
    Returns:
        bool: 验证是否通过
    """
    validator = ConfigValidator()
    return validator.run_all_checks()


def get_api_key(key_name: str = "MINIMAX_API_KEY") -> str:
    """
    获取 API Key (带验证)
    
    Raises:
        ConfigurationError: 如果 API Key 无效
    """
    api_key = os.getenv(key_name)
    
    if not api_key:
        raise ConfigurationError(f"API Key 未配置：{key_name}")
    
    if len(api_key) < 10:
        raise ConfigurationError(f"API Key 格式错误：{key_name}")
    
    return api_key


# 快捷方式
def check_config() -> bool:
    """快速检查配置"""
    return validate_and_init()


if __name__ == "__main__":
    # 测试配置验证
    import logging
    logging.basicConfig(level=logging.INFO)
    
    print("测试配置验证...")
    success = validate_and_init()
    
    if success:
        print("✅ 配置验证通过")
    else:
        print("❌ 配置验证失败")
        sys.exit(1)
