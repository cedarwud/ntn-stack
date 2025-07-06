"""
NetStack API 統一配置管理器
負責集中管理所有配置和環境設定
"""

import os
import structlog
from typing import Dict, Any, List

logger = structlog.get_logger(__name__)


class ConfigManager:
    """
    統一配置管理器
    集中管理所有環境變數、配置項目和系統設定
    """
    
    def __init__(self):
        """初始化配置管理器"""
        self.config = {}
        self._load_all_configs()
    
    def _load_all_configs(self) -> None:
        """載入所有配置項目"""
        logger.info("📋 載入系統配置...")
        
        self.config = {
            # 資料庫配置
            "database": {
                "mongo_url": os.getenv("DATABASE_URL", "mongodb://mongo:27017/open5gs"),
                "mongo_host": os.getenv("MONGO_HOST", "mongo"),
                "mongo_port": int(os.getenv("MONGO_PORT", "27017")),
            },
            
            # Redis 配置
            "redis": {
                "redis_url": os.getenv("REDIS_URL", "redis://redis:6379"),
                "redis_host": os.getenv("REDIS_HOST", "redis"),
                "redis_port": int(os.getenv("REDIS_PORT", "6379")),
            },
            
            # 應用配置
            "app": {
                "title": "NetStack API",
                "description": "Open5GS + UERANSIM 雙 Slice 核心網管理 API",
                "version": "2.0.0",
                "environment": os.getenv("ENVIRONMENT", "development"),
                "debug": os.getenv("DEBUG", "false").lower() == "true",
            },
            
            # 服務器配置
            "server": {
                "host": os.getenv("HOST", "0.0.0.0"),
                "port": int(os.getenv("PORT", "8080")),
                "reload": os.getenv("RELOAD", "true").lower() == "true",
                "log_level": os.getenv("LOG_LEVEL", "info"),
            },
            
            # CORS 配置
            "cors": {
                "allowed_origins": self._parse_list(os.getenv("CORS_ORIGINS", "*")),
                "allow_credentials": os.getenv("CORS_CREDENTIALS", "true").lower() == "true",
                "allowed_methods": self._parse_list(os.getenv("CORS_METHODS", "*")),
                "allowed_headers": self._parse_list(os.getenv("CORS_HEADERS", "*")),
            },
            
            # 安全配置
            "security": {
                "max_request_size": int(os.getenv("MAX_REQUEST_SIZE", str(16 * 1024 * 1024))),
                "rate_limit": int(os.getenv("RATE_LIMIT", "100")),
                "security_headers": os.getenv("SECURITY_HEADERS", "true").lower() == "true",
            }
        }
        
        logger.info("✅ 配置載入完成", 
                   environment=self.config["app"]["environment"],
                   debug=self.config["app"]["debug"])
    
    def _parse_list(self, value: str) -> List[str]:
        """解析逗號分隔的字符串為列表"""
        if value == "*":
            return ["*"]
        return [item.strip() for item in value.split(",") if item.strip()]
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        獲取配置值
        
        Args:
            key_path: 配置路徑，例如 "database.mongo_url" 或 "app.debug"
            default: 預設值
            
        Returns:
            配置值
        """
        keys = key_path.split(".")
        value = self.config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def get_database_config(self) -> Dict[str, Any]:
        """獲取資料庫配置"""
        return self.config["database"]
    
    def get_redis_config(self) -> Dict[str, Any]:
        """獲取 Redis 配置"""
        return self.config["redis"]
    
    def get_app_config(self) -> Dict[str, Any]:
        """獲取應用配置"""
        return self.config["app"]
    
    def get_server_config(self) -> Dict[str, Any]:
        """獲取服務器配置"""
        return self.config["server"]
    
    def get_cors_config(self) -> Dict[str, Any]:
        """獲取 CORS 配置"""
        return self.config["cors"]
    
    def get_security_config(self) -> Dict[str, Any]:
        """獲取安全配置"""
        return self.config["security"]
    
    def is_production(self) -> bool:
        """檢查是否為生產環境"""
        return self.config["app"]["environment"] == "production"
    
    def is_development(self) -> bool:
        """檢查是否為開發環境"""
        return self.config["app"]["environment"] == "development"
    
    def get_config_summary(self) -> Dict[str, Any]:
        """獲取配置摘要（隱藏敏感信息）"""
        return {
            "app": self.config["app"],
            "server": {
                "host": self.config["server"]["host"],
                "port": self.config["server"]["port"],
            },
            "database": {
                "host": self.config["database"]["mongo_host"],
                "port": self.config["database"]["mongo_port"],
            },
            "redis": {
                "host": self.config["redis"]["redis_host"],
                "port": self.config["redis"]["redis_port"],
            },
            "security": {
                "max_request_size_mb": self.config["security"]["max_request_size"] / 1024 / 1024,
                "security_headers": self.config["security"]["security_headers"],
            }
        }


# 全域配置實例
config = ConfigManager()