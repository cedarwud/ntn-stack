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
                "version": "2.0.0-final",
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
            },
            
            # 數據路徑配置 (統一路徑管理)
            "data_paths": {
                # TLE 數據路徑 (支援容器和本機環境)
                "tle_data_dir": self._resolve_data_path(
                    os.getenv("TLE_DATA_PATH", "/netstack/tle_data")
                ),
                
                # 應用數據輸出路徑
                "output_dir": self._resolve_data_path(
                    os.getenv("OUTPUT_DATA_PATH", "/app/data")
                ),
                
                # 備份數據路徑
                "backup_dir": self._resolve_data_path(
                    os.getenv("BACKUP_DATA_PATH", "/app/backup")
                ),
                
                # Phase 0 預計算數據路徑
                "phase0_data_dir": self._resolve_data_path(
                    os.getenv("PHASE0_DATA_PATH", "/app/data")
                ),
                
                # 專案根目錄 (自動偵測)
                "project_root": self._get_project_root(),
            },
            
            # 衛星數據配置
            "satellite_data": {
                "supported_constellations": ["starlink", "oneweb"],
                "default_constellation": os.getenv("DEFAULT_CONSTELLATION", "starlink"),
                "update_interval_hours": int(os.getenv("TLE_UPDATE_INTERVAL", "24")),
                "enable_auto_update": os.getenv("TLE_AUTO_UPDATE", "true").lower() == "true",
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
    
    def _get_project_root(self) -> str:
        """跨平台自動偵測專案根目錄"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.splitdrive(current_dir)[0] + os.sep if os.name == 'nt' else "/"
        
        while current_dir != root_dir:
            # 檢查專案標識文件或目錄
            if (os.path.exists(os.path.join(current_dir, "ntn-stack")) or 
                os.path.exists(os.path.join(current_dir, "netstack")) or 
                os.path.basename(current_dir) == "ntn-stack" or
                os.path.exists(os.path.join(current_dir, "phase1_refactor")) or
                os.path.exists(os.path.join(current_dir, "simworld"))):
                return current_dir
            current_dir = os.path.dirname(current_dir)
        
        # 跨平台的預設路徑
        if os.name == 'nt':  # Windows
            return os.path.join(os.path.expanduser("~"), "ntn-stack")
        else:  # Linux/Unix/macOS
            return "/home/sat/ntn-stack"
    
    def _resolve_data_path(self, path: str) -> str:
        """
        跨平台數據路徑解析，支援 Windows、macOS 和 Linux
        
        Args:
            path: 原始路徑 (容器路徑、絕對路徑或相對路徑)
            
        Returns:
            解析後的實際路徑
        """
        project_root = self._get_project_root()
        
        # 如果已經是絕對路徑且存在，直接使用
        if os.path.isabs(path) and os.path.exists(path):
            return path
        
        # 跨平台容器路徑轉換邏輯
        relative_path = None
        
        # Unix 容器路徑轉換
        if path.startswith("/netstack/"):
            # /netstack/tle_data -> netstack/tle_data
            relative_path = path[1:]  # 移除開頭的 "/"
            
        elif path.startswith("/app/"):
            # /app/data -> data
            relative_path = path[5:]  # 移除 "/app/"
            
        elif path.startswith("/") and not os.name == 'nt':
            # Unix 其他絕對路徑轉為相對路徑 (非 Windows)
            relative_path = path[1:]
            
        # Windows 絕對路徑處理
        elif os.name == 'nt' and len(path) >= 3 and path[1:3] == ':\\':
            # Windows 絕對路徑 (C:\path) 直接使用，但可能需要轉換
            # 如果是標準 Windows 路徑且存在，直接返回
            if os.path.exists(path):
                return path
            # 否則嘗試轉換為相對路徑
            relative_path = os.path.basename(path)
            
        else:
            # 已經是相對路徑或其他格式
            relative_path = path
        
        # 如果沒有成功轉換為相對路徑，使用原始路徑
        if relative_path is None:
            relative_path = path
        
        # 使用 os.path.join 進行跨平台路徑拼接
        resolved_path = os.path.join(project_root, relative_path)
        
        # 如果路徑存在，直接返回
        if os.path.exists(resolved_path):
            return resolved_path
            
        # 如果不存在，嘗試一些常見的替代位置
        alternative_paths = []
        
        if "tle_data" in relative_path:
            alternative_paths.extend([
                os.path.join(project_root, "netstack", "tle_data"),
                os.path.join(project_root, "tle_data")
            ])
            
        if relative_path in ["data", "backup"] or relative_path.endswith("data"):
            alternative_paths.extend([
                os.path.join(project_root, "data"),
                os.path.join(project_root, "netstack", "data"),
                os.path.join(project_root, "phase1_refactor", "data")
            ])
        
        # 檢查替代路徑
        for alt_path in alternative_paths:
            if os.path.exists(alt_path):
                return alt_path
        
        # 如果都不存在，創建原始解析的路徑
        try:
            os.makedirs(resolved_path, exist_ok=True)
            return resolved_path
        except (OSError, PermissionError):
            # 如果無法創建，使用第一個替代路徑
            if alternative_paths:
                fallback_path = alternative_paths[0]
                try:
                    os.makedirs(fallback_path, exist_ok=True)
                    return fallback_path
                except (OSError, PermissionError):
                    pass
            
            # 最後回退：返回原路徑
            return path
    
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
    
    def get_data_paths_config(self) -> Dict[str, str]:
        """獲取數據路徑配置"""
        return self.config["data_paths"]
    
    def get_tle_data_path(self) -> str:
        """獲取 TLE 數據路徑"""
        return self.config["data_paths"]["tle_data_dir"]
    
    def get_output_data_path(self) -> str:
        """獲取輸出數據路徑"""
        return self.config["data_paths"]["output_dir"]
    
    def get_backup_data_path(self) -> str:
        """獲取備份數據路徑"""
        return self.config["data_paths"]["backup_dir"]
    
    def get_project_root_path(self) -> str:
        """獲取專案根目錄路徑"""
        return self.config["data_paths"]["project_root"]
    
    def get_satellite_data_config(self) -> Dict[str, Any]:
        """獲取衛星數據配置"""
        return self.config["satellite_data"]
    
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