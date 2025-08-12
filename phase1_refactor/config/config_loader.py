#!/usr/bin/env python3
"""
Phase 1 統一配置載入器

功能:
1. 整合 NetStack 配置管理器
2. 提供統一的路徑配置
3. 支援容器和本機環境自動切換
4. 解決所有硬編碼路徑問題

符合 CLAUDE.md 原則:
- 統一的配置管理確保系統一致性
- 自動路徑解析支援不同部署環境
- 完整的錯誤處理和日誌記錄
"""

import os
import sys
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class Phase1Config:
    """Phase 1 統一配置類"""
    # 數據路徑
    tle_data_dir: str
    output_dir: str
    backup_dir: str
    
    # 計算參數
    time_step_seconds: int = 30
    trajectory_duration_minutes: int = 120
    
    # 觀測點配置 (NTPU)
    observer_latitude: float = 24.9441667
    observer_longitude: float = 121.3713889
    observer_altitude_m: float = 50.0
    
    # 支援星座
    supported_constellations: list = None
    
    def __post_init__(self):
        if self.supported_constellations is None:
            self.supported_constellations = ["starlink", "oneweb"]


class Phase1ConfigLoader:
    """Phase 1 配置載入器"""
    
    def __init__(self):
        """初始化配置載入器"""
        self.phase1_root = Path(__file__).parent.parent
        self.project_root = self._find_project_root()
        self.netstack_config = None
        
        # 嘗試載入 NetStack 配置管理器
        self._load_netstack_config()
        
        logger.info("✅ Phase 1 配置載入器初始化完成")
    
    def _find_project_root(self) -> Path:
        """跨平台自動找到專案根目錄"""
        current_dir = Path(__file__).parent.absolute()
        
        # 跨平台根目錄偵測
        if os.name == 'nt':  # Windows
            root_check = lambda d: d.parent == d  # C:\ 的 parent 等於自身
        else:  # Linux/Unix/macOS  
            root_check = lambda d: str(d) == "/"
        
        # 向上搜尋專案根目錄
        while not root_check(current_dir):
            # 檢查專案標識目錄或檔案
            if ((current_dir / "netstack").exists() or 
                (current_dir / "ntn-stack").exists() or
                current_dir.name == "ntn-stack" or
                (current_dir / "phase1_refactor").exists() or
                (current_dir / "simworld").exists() or
                (current_dir / ".git").exists()):
                return current_dir
            current_dir = current_dir.parent
        
        # 跨平台預設路徑
        if os.name == 'nt':  # Windows
            default_path = Path.home() / "ntn-stack"
        elif sys.platform == 'darwin':  # macOS
            default_path = Path.home() / "ntn-stack" 
        else:  # Linux/Unix
            default_path = Path("/home/sat/ntn-stack")
        
        # 如果預設路徑不存在，嘗試其他常見位置
        if not default_path.exists():
            alternative_paths = [
                Path.cwd(),  # 當前工作目錄
                Path(__file__).parent.parent.parent,  # 相對於當前檔案的上三層
                Path.home() / "Documents" / "ntn-stack",  # 用戶文檔目錄 (跨平台)
                Path.home() / "Desktop" / "ntn-stack"     # 桌面目錄 (跨平台)
            ]
            
            for alt_path in alternative_paths:
                if alt_path.exists() and (
                    (alt_path / "netstack").exists() or 
                    (alt_path / "phase1_refactor").exists()
                ):
                    return alt_path
        
        return default_path
    
    def _load_netstack_config(self):
        """載入 NetStack 配置管理器"""
        try:
            # 添加 NetStack API 路徑
            netstack_api_path = self.project_root / "netstack" / "netstack_api"
            if netstack_api_path.exists():
                sys.path.insert(0, str(netstack_api_path))
                
            from app.core.config_manager import ConfigManager
            self.netstack_config = ConfigManager()
            logger.info("✅ NetStack 配置管理器載入成功")
            
        except Exception as e:
            logger.warning(f"⚠️ 無法載入 NetStack 配置管理器: {e}")
            self.netstack_config = None
    
    def _resolve_path(self, path: str) -> str:
        """
        跨平台路徑解析，支援 Windows、macOS 和 Linux
        與 NetStack ConfigManager 保持一致的路徑解析邏輯
        
        Args:
            path: 原始路徑 (容器路徑、絕對路徑或相對路徑)
            
        Returns:
            解析後的實際路徑
        """
        if self.netstack_config:
            # 優先使用 NetStack ConfigManager 的路徑解析
            if path == "/netstack/tle_data":
                return self.netstack_config.get_tle_data_path()
            elif path == "/app/data":
                return self.netstack_config.get_output_data_path()
            elif path == "/app/backup":
                return self.netstack_config.get_backup_data_path()
        
        # 手動跨平台路徑解析 (與 NetStack ConfigManager 一致的邏輯)
        project_root = str(self._find_project_root())
        
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
    
    def load_yaml_config(self) -> Dict[str, Any]:
        """載入 YAML 配置文件"""
        config_file = self.phase1_root / "config" / "phase1_config.yaml"
        
        if not config_file.exists():
            logger.warning(f"⚠️ 配置文件不存在: {config_file}")
            return {}
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            logger.info("✅ YAML 配置載入成功")
            return config_data
        
        except Exception as e:
            logger.error(f"❌ YAML 配置載入失敗: {e}")
            return {}
    
    def create_phase1_config(self) -> Phase1Config:
        """創建 Phase 1 配置對象"""
        
        # 載入 YAML 配置
        yaml_config = self.load_yaml_config()
        
        # 從 YAML 或預設值獲取配置
        data_sources = yaml_config.get("data_sources", {})
        computation = yaml_config.get("computation", {})
        observer = computation.get("observer", {})
        constellations = yaml_config.get("supported_constellations", [])
        
        # 解析路徑
        tle_data_dir = self._resolve_path(
            data_sources.get("tle_data_dir", "/netstack/tle_data")
        )
        
        output_dir = self._resolve_path(
            data_sources.get("output_dir", "/app/data")
        )
        
        backup_dir = self._resolve_path(
            data_sources.get("backup_dir", "/app/backup")
        )
        
        # 處理星座配置
        if isinstance(constellations, list) and len(constellations) > 0:
            constellation_names = []
            for constellation in constellations:
                if isinstance(constellation, dict):
                    constellation_names.append(constellation.get("name", ""))
                else:
                    constellation_names.append(str(constellation))
            supported_constellations = [name for name in constellation_names if name]
        else:
            supported_constellations = ["starlink", "oneweb"]
        
        config = Phase1Config(
            tle_data_dir=tle_data_dir,
            output_dir=output_dir,
            backup_dir=backup_dir,
            time_step_seconds=computation.get("time_step_seconds", 30),
            trajectory_duration_minutes=computation.get("trajectory_duration_minutes", 120),
            observer_latitude=observer.get("latitude", 24.9441667),
            observer_longitude=observer.get("longitude", 121.3713889),
            observer_altitude_m=observer.get("altitude_m", 50.0),
            supported_constellations=supported_constellations
        )
        
        logger.info("✅ Phase 1 配置創建完成:")
        logger.info(f"   TLE 數據目錄: {config.tle_data_dir}")
        logger.info(f"   輸出目錄: {config.output_dir}")
        logger.info(f"   支援星座: {config.supported_constellations}")
        
        return config
    
    def get_tle_data_path(self) -> str:
        """獲取 TLE 數據路徑 (便利方法)"""
        return self._resolve_path("/netstack/tle_data")
    
    def get_output_data_path(self) -> str:
        """獲取輸出數據路徑 (便利方法)"""
        return self._resolve_path("/app/data")
    
    def get_backup_data_path(self) -> str:
        """獲取備份數據路徑 (便利方法)"""
        return self._resolve_path("/app/backup")
    
    def validate_paths(self) -> Dict[str, bool]:
        """驗證所有路徑是否可用"""
        config = self.create_phase1_config()
        
        validation_result = {
            "tle_data_dir": os.path.exists(config.tle_data_dir),
            "output_dir": os.path.exists(config.output_dir),
            "backup_dir": os.path.exists(config.backup_dir),
        }
        
        # 嘗試創建不存在的目錄
        for path_name, exists in validation_result.items():
            if not exists:
                try:
                    path_value = getattr(config, path_name)
                    os.makedirs(path_value, exist_ok=True)
                    validation_result[path_name] = True
                    logger.info(f"✅ 創建目錄: {path_value}")
                except Exception as e:
                    logger.error(f"❌ 無法創建目錄 {path_name}: {e}")
        
        return validation_result


# 全域配置載入器實例
_global_config_loader = None

def get_config_loader() -> Phase1ConfigLoader:
    """獲取全域配置載入器實例 (單例模式)"""
    global _global_config_loader
    if _global_config_loader is None:
        _global_config_loader = Phase1ConfigLoader()
    return _global_config_loader

def get_phase1_config() -> Phase1Config:
    """獲取 Phase 1 配置 (便利函數)"""
    return get_config_loader().create_phase1_config()

def get_tle_data_path() -> str:
    """獲取 TLE 數據路徑 (便利函數)"""
    return get_config_loader().get_tle_data_path()

def get_output_data_path() -> str:
    """獲取輸出數據路徑 (便利函數)"""
    return get_config_loader().get_output_data_path()

def get_backup_data_path() -> str:
    """獲取備份數據路徑 (便利函數)"""
    return get_config_loader().get_backup_data_path()


if __name__ == "__main__":
    # 測試配置載入器
    logging.basicConfig(level=logging.INFO)
    
    try:
        print("🔧 測試 Phase 1 配置載入器...")
        
        # 載入配置
        loader = get_config_loader()
        config = get_phase1_config()
        
        print("\n✅ 配置載入成功:")
        print(f"   TLE 數據目錄: {config.tle_data_dir}")
        print(f"   輸出目錄: {config.output_dir}")
        print(f"   備份目錄: {config.backup_dir}")
        print(f"   觀測點: ({config.observer_latitude}, {config.observer_longitude})")
        print(f"   支援星座: {config.supported_constellations}")
        
        # 驗證路徑
        validation = loader.validate_paths()
        print(f"\n🔍 路徑驗證結果: {validation}")
        
        # 測試便利函數
        print(f"\n🛠️ 便利函數測試:")
        print(f"   get_tle_data_path(): {get_tle_data_path()}")
        print(f"   get_output_data_path(): {get_output_data_path()}")
        print(f"   get_backup_data_path(): {get_backup_data_path()}")
        
        print("\n🎉 Phase 1 配置載入器測試完成！")
        
    except Exception as e:
        print(f"❌ 配置載入器測試失敗: {e}")
        import traceback
        traceback.print_exc()