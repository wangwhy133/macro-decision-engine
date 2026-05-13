"""
配置管理中心 (增强版)
- 支持 .env 文件自动加载
- 支持环境变量覆盖
- 支持配置文件 (~/.macro_config.json)
"""
import os
import json
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# 尝试加载 .env 文件 (当前目录或上级目录)
load_dotenv(dotenv_path='.env')
load_dotenv(dotenv_path='../.env')
load_dotenv(dotenv_path=os.path.expanduser('~/.macro.env'))

class Settings:
    def __init__(self):
        self.data_dir = os.getenv("MACRO_DATA_DIR", "/opt/macro-push/data")
        self.db_path = os.getenv("MACRO_DB_PATH", f"{self.data_dir}/macro.db")
        self.cache_db_path = os.getenv("MACRO_CACHE_PATH", f"{self.data_dir}/cache.db")
        self.timezone = os.getenv("MACRO_TIMEZONE", "Asia/Shanghai")
        self.fred_api_key = os.getenv("FRED_API_KEY", "")
        self.zhipu_key = os.getenv("ZHIPU_API_KEY", "")
        self.zhipu_base = os.getenv("ZHIPU_BASE_URL", "https://open.bigmodel.cn/api/paas/v4/")
        self.log_level = os.getenv("MACRO_LOG_LEVEL", "INFO")
        
        # 尝试从配置文件加载补充信息
        self._load_config_file()

    def _load_config_file(self):
        config_paths = [
            os.path.expanduser("~/.macro_config.json"),
            "/etc/macro_push/config.json",
            "config.json"
        ]
        for path in config_paths:
            if os.path.exists(path):
                try:
                    with open(path) as f:
                        cfg = json.load(f)
                        # 仅当环境变量未设置时才用配置文件覆盖
                        if not self.fred_api_key:
                            self.fred_api_key = cfg.get("fred_api_key", "")
                        if not self.zhipu_key:
                            self.zhipu_key = cfg.get("zhipu_key", "")
                        self.data_dir = cfg.get("data_dir") or self.data_dir
                        self.db_path = cfg.get("db_path") or self.db_path
                        break
                except Exception as e:
                    print(f"[Config] 加载 {path} 失败：{e}")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "data_dir": self.data_dir,
            "db_path": self.db_path,
            "cache_db_path": self.cache_db_path,
            "timezone": self.timezone,
            "fred_api_key": "***" if self.fred_api_key else "",
            "zhipu_key": "***" if self.zhipu_key else "",
            "log_level": self.log_level,
        }

_settings: Optional[Settings] = None

def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

if __name__ == "__main__":
    s = get_settings()
    print("当前配置:")
    print(json.dumps(s.to_dict(), indent=2))
