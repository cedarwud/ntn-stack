"""統一配置管理模組"""
import os
from typing import Optional, List


class Settings:
    """應用程式設定類"""
    
    def __init__(self):
        # 應用程式基本配置
        self.app_name: str = "NTN Stack NetStack API"
        self.app_version: str = "1.0.0"
        self.debug: bool = os.getenv("DEBUG", "false").lower() == "true"
        
        # API 配置
        self.api_host: str = os.getenv("API_HOST", "0.0.0.0")
        self.api_port: int = int(os.getenv("API_PORT", "8080"))
        self.api_prefix: str = os.getenv("API_PREFIX", "/api/v1")
        
        # 數據庫配置
        self.mongodb_url: str = os.getenv("MONGODB_URL", "mongodb://mongo:27017/open5gs")
        self.redis_url: str = os.getenv("REDIS_URL", "redis://redis:6379")
        
        # 日誌配置
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")
        
        # CORS 配置
        self.cors_origins: List[str] = ["*"]
        self.cors_allow_credentials: bool = True
        self.cors_allow_methods: List[str] = ["*"]
        self.cors_allow_headers: List[str] = ["*"]
        
        # 效能配置
        self.max_workers: int = int(os.getenv("MAX_WORKERS", "4"))


# 全域設定實例
settings = Settings()