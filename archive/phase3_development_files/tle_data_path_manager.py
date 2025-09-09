#!/usr/bin/env python3
"""
TLE Data Path Manager - Phase 3.5 Task 4b
標準化TLE數據路徑配置管理系統

提供統一的TLE數據路徑管理，支援多環境配置和路徑標準化
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class TLEDataEnvironment(Enum):
    """TLE數據環境類型"""
    CONTAINER = "container"    # Docker容器環境
    HOST = "host"             # 主機環境
    DEVELOPMENT = "development"  # 開發環境
    PRODUCTION = "production"    # 生產環境


class ConstellationType(Enum):
    """支援的衛星星座類型"""
    STARLINK = "starlink"
    ONEWEB = "oneweb"


@dataclass
class TLEPathConfig:
    """TLE路徑配置結構"""
    base_path: str
    constellation_paths: Dict[str, str]
    backup_path: str
    environment: TLEDataEnvironment
    version: str = "1.0"
    last_updated: Optional[str] = None
    
    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.utcnow().isoformat()


@dataclass
class TLEFileInfo:
    """TLE文件信息結構"""
    constellation: str
    date: str
    file_path: Path
    file_size: int
    creation_time: datetime
    is_valid: bool = True


class TLEDataPathManager:
    """
    TLE數據路徑標準化管理器
    
    提供功能：
    - 多環境路徑配置管理
    - 自動路徑解析和標準化
    - TLE文件發現和驗證
    - 路徑健康檢查
    - 配置序列化和持久化
    """
    
    # 預定義路徑模板
    PATH_TEMPLATES = {
        TLEDataEnvironment.CONTAINER: {
            "base": "/app/tle_data",
            "starlink": "/app/tle_data/starlink",
            "oneweb": "/app/tle_data/oneweb",
            "backup": "/app/tle_data/backups"
        },
        TLEDataEnvironment.HOST: {
            "base": "/home/sat/ntn-stack/netstack/tle_data",
            "starlink": "/home/sat/ntn-stack/netstack/tle_data/starlink",
            "oneweb": "/home/sat/ntn-stack/netstack/tle_data/oneweb",
            "backup": "/home/sat/ntn-stack/netstack/tle_data/backups"
        },
        TLEDataEnvironment.DEVELOPMENT: {
            "base": "./netstack/tle_data",
            "starlink": "./netstack/tle_data/starlink",
            "oneweb": "./netstack/tle_data/oneweb",
            "backup": "./netstack/tle_data/backups"
        },
        TLEDataEnvironment.PRODUCTION: {
            "base": "/data/tle_data",
            "starlink": "/data/tle_data/starlink",
            "oneweb": "/data/tle_data/oneweb",
            "backup": "/data/tle_data/backups"
        }
    }
    
    def __init__(self, environment: Optional[TLEDataEnvironment] = None, config_file: Optional[str] = None):
        """
        初始化TLE數據路徑管理器
        
        Args:
            environment: 目標環境，自動檢測如果未指定
            config_file: 自定義配置文件路徑
        """
        self.environment = environment or self._detect_environment()
        self.config_file = Path(config_file or "/tmp/tle_path_config.json")
        self.config = self._load_or_create_config()
        
        logger.info(f"🗂️  TLE Data Path Manager 初始化 - 環境: {self.environment.value}")
        logger.info(f"   基礎路徑: {self.config.base_path}")
    
    def _detect_environment(self) -> TLEDataEnvironment:
        """自動檢測運行環境"""
        if os.path.exists("/.dockerenv"):
            return TLEDataEnvironment.CONTAINER
        elif os.environ.get("DOCKER_CONTAINER", "").lower() == "true":
            return TLEDataEnvironment.CONTAINER
        elif os.environ.get("ENVIRONMENT", "").lower() == "production":
            return TLEDataEnvironment.PRODUCTION
        elif os.path.exists("/home/sat/ntn-stack"):
            return TLEDataEnvironment.HOST
        else:
            return TLEDataEnvironment.DEVELOPMENT
    
    def _load_or_create_config(self) -> TLEPathConfig:
        """載入或創建配置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    # 轉換環境枚舉
                    config_data['environment'] = TLEDataEnvironment(config_data['environment'])
                    return TLEPathConfig(**config_data)
            except Exception as e:
                logger.warning(f"配置文件載入失敗，使用預設配置: {e}")
        
        return self._create_default_config()
    
    def _create_default_config(self) -> TLEPathConfig:
        """創建預設配置"""
        template = self.PATH_TEMPLATES[self.environment]
        
        constellation_paths = {}
        for constellation in ConstellationType:
            constellation_paths[constellation.value] = template[constellation.value]
        
        return TLEPathConfig(
            base_path=template["base"],
            constellation_paths=constellation_paths,
            backup_path=template["backup"],
            environment=self.environment
        )
    
    def save_config(self) -> bool:
        """保存配置到文件"""
        try:
            self.config.last_updated = datetime.utcnow().isoformat()
            config_dict = asdict(self.config)
            config_dict['environment'] = self.config.environment.value
            
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ 配置已保存至: {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"❌ 配置保存失敗: {e}")
            return False
    
    def get_constellation_path(self, constellation: Union[str, ConstellationType], subdir: str = "tle") -> Path:
        """
        獲取指定星座的路徑
        
        Args:
            constellation: 星座名稱或類型
            subdir: 子目錄 (tle, json)
            
        Returns:
            Path: 標準化的路徑
        """
        if isinstance(constellation, ConstellationType):
            constellation = constellation.value
        
        constellation_lower = constellation.lower()
        if constellation_lower not in self.config.constellation_paths:
            raise ValueError(f"不支援的星座類型: {constellation}")
        
        base_path = Path(self.config.constellation_paths[constellation_lower])
        return base_path / subdir
    
    def get_tle_file_path(self, constellation: Union[str, ConstellationType], date: Union[str, datetime]) -> Path:
        """
        獲取指定日期的TLE文件路徑
        
        Args:
            constellation: 星座名稱
            date: 日期字串或datetime物件
            
        Returns:
            Path: TLE文件完整路徑
        """
        if isinstance(date, datetime):
            date_str = date.strftime("%Y%m%d")
        else:
            date_str = str(date).replace("-", "")
        
        constellation_str = constellation.value if isinstance(constellation, ConstellationType) else constellation
        tle_dir = self.get_constellation_path(constellation, "tle")
        
        return tle_dir / f"{constellation_str.lower()}_{date_str}.tle"
    
    def discover_tle_files(self, constellation: Optional[Union[str, ConstellationType]] = None) -> List[TLEFileInfo]:
        """
        發現可用的TLE文件
        
        Args:
            constellation: 指定星座，None表示所有星座
            
        Returns:
            List[TLEFileInfo]: TLE文件信息列表
        """
        tle_files = []
        
        constellations_to_check = []
        if constellation:
            constellation_name = constellation.value if isinstance(constellation, ConstellationType) else constellation
            constellations_to_check = [constellation_name]
        else:
            constellations_to_check = [c.value for c in ConstellationType]
        
        for const_name in constellations_to_check:
            try:
                tle_dir = self.get_constellation_path(const_name, "tle")
                if not tle_dir.exists():
                    logger.warning(f"TLE目錄不存在: {tle_dir}")
                    continue
                
                for tle_file in tle_dir.glob("*.tle"):
                    try:
                        stat = tle_file.stat()
                        tle_info = TLEFileInfo(
                            constellation=const_name,
                            date=self._extract_date_from_filename(tle_file.name),
                            file_path=tle_file,
                            file_size=stat.st_size,
                            creation_time=datetime.fromtimestamp(stat.st_mtime),
                            is_valid=self._validate_tle_file(tle_file)
                        )
                        tle_files.append(tle_info)
                    except Exception as e:
                        logger.error(f"處理TLE文件失敗 {tle_file}: {e}")
            except Exception as e:
                logger.error(f"檢查星座 {const_name} 失敗: {e}")
        
        return sorted(tle_files, key=lambda x: (x.constellation, x.date), reverse=True)
    
    def get_latest_tle_file(self, constellation: Union[str, ConstellationType]) -> Optional[TLEFileInfo]:
        """獲取指定星座的最新TLE文件"""
        files = self.discover_tle_files(constellation)
        valid_files = [f for f in files if f.is_valid]
        
        if valid_files:
            return valid_files[0]  # 已按日期排序，第一個是最新的
        return None
    
    def _extract_date_from_filename(self, filename: str) -> str:
        """從文件名提取日期"""
        # 假設格式: starlink_20250902.tle -> 20250902
        parts = filename.replace('.tle', '').split('_')
        if len(parts) >= 2:
            return parts[-1]
        return ""
    
    def _validate_tle_file(self, file_path: Path) -> bool:
        """簡單的TLE文件驗證"""
        try:
            if not file_path.exists() or file_path.stat().st_size == 0:
                return False
            
            # 檢查文件前幾行是否符合TLE格式
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()[:6]  # 檢查前6行
                
                if len(lines) < 3:
                    return False
                
                # 簡單檢查：每3行為一組，第2、3行應該以'1 '和'2 '開頭
                for i in range(0, len(lines), 3):
                    if i + 2 < len(lines):
                        line2 = lines[i + 1].strip()
                        line3 = lines[i + 2].strip()
                        if not (line2.startswith('1 ') and line3.startswith('2 ')):
                            return False
                
                return True
        except Exception:
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """執行路徑健康檢查"""
        health_status = {
            "timestamp": datetime.utcnow().isoformat(),
            "environment": self.environment.value,
            "base_path_exists": Path(self.config.base_path).exists(),
            "constellations": {},
            "total_tle_files": 0,
            "latest_files": {},
            "issues": []
        }
        
        # 檢查每個星座
        for constellation in ConstellationType:
            const_name = constellation.value
            try:
                tle_dir = self.get_constellation_path(constellation, "tle")
                json_dir = self.get_constellation_path(constellation, "json")
                
                files = self.discover_tle_files(constellation)
                valid_files = [f for f in files if f.is_valid]
                latest = self.get_latest_tle_file(constellation)
                
                health_status["constellations"][const_name] = {
                    "tle_dir_exists": tle_dir.exists(),
                    "json_dir_exists": json_dir.exists(),
                    "total_files": len(files),
                    "valid_files": len(valid_files),
                    "latest_date": latest.date if latest else None,
                    "latest_size_mb": round(latest.file_size / 1024 / 1024, 2) if latest else 0
                }
                
                health_status["total_tle_files"] += len(valid_files)
                if latest:
                    health_status["latest_files"][const_name] = latest.date
                
                # 檢查問題
                if not tle_dir.exists():
                    health_status["issues"].append(f"{const_name} TLE目錄不存在: {tle_dir}")
                if len(valid_files) == 0:
                    health_status["issues"].append(f"{const_name} 沒有有效的TLE文件")
                elif latest and (datetime.now() - latest.creation_time).days > 7:
                    health_status["issues"].append(f"{const_name} 最新TLE文件超過7天: {latest.date}")
                    
            except Exception as e:
                health_status["issues"].append(f"{const_name} 健康檢查失敗: {str(e)}")
        
        # 檢查備份目錄
        backup_path = Path(self.config.backup_path)
        health_status["backup_path_exists"] = backup_path.exists()
        if not backup_path.exists():
            health_status["issues"].append(f"備份目錄不存在: {backup_path}")
        
        health_status["overall_healthy"] = len(health_status["issues"]) == 0
        
        return health_status
    
    def get_path_for_processor(self, processor_type: str = "stage1") -> str:
        """為處理器獲取適當的TLE數據路徑"""
        # 根據處理器類型和環境返回合適的路徑
        if processor_type == "stage1":
            return self.config.base_path
        else:
            # 其他處理器可能有不同的路徑需求
            return self.config.base_path
    
    def create_path_migration_plan(self, target_environment: TLEDataEnvironment) -> Dict[str, Any]:
        """創建路徑遷移計劃"""
        current_config = self.config
        target_template = self.PATH_TEMPLATES[target_environment]
        
        migration_plan = {
            "source_environment": current_config.environment.value,
            "target_environment": target_environment.value,
            "migrations": [],
            "estimated_size_mb": 0
        }
        
        # 計算需要遷移的文件
        for constellation in ConstellationType:
            files = self.discover_tle_files(constellation)
            total_size = sum(f.file_size for f in files)
            
            source_path = self.get_constellation_path(constellation)
            target_path = Path(target_template[constellation.value])
            
            migration_plan["migrations"].append({
                "constellation": constellation.value,
                "source_path": str(source_path),
                "target_path": str(target_path),
                "file_count": len(files),
                "size_mb": round(total_size / 1024 / 1024, 2)
            })
            
            migration_plan["estimated_size_mb"] += total_size / 1024 / 1024
        
        return migration_plan


def create_tle_path_manager(environment: Optional[str] = None, config_file: Optional[str] = None) -> TLEDataPathManager:
    """
    工廠函數：創建TLE路徑管理器實例
    
    Args:
        environment: 環境字串 (container, host, development, production)
        config_file: 配置文件路徑
        
    Returns:
        TLEDataPathManager: 配置好的管理器實例
    """
    env = None
    if environment:
        try:
            env = TLEDataEnvironment(environment.lower())
        except ValueError:
            logger.warning(f"無效的環境類型: {environment}，將自動檢測")
    
    return TLEDataPathManager(environment=env, config_file=config_file)


if __name__ == "__main__":
    # 示例用法
    logging.basicConfig(level=logging.INFO)
    
    # 創建管理器
    manager = create_tle_path_manager()
    
    # 執行健康檢查
    health = manager.health_check()
    print("=== TLE數據路徑健康檢查 ===")
    print(f"整體健康狀態: {'✅ 正常' if health['overall_healthy'] else '❌ 有問題'}")
    print(f"環境: {health['environment']}")
    print(f"總TLE文件數: {health['total_tle_files']}")
    
    if health['issues']:
        print("\n發現的問題:")
        for issue in health['issues']:
            print(f"  - {issue}")
    
    # 顯示最新文件
    print(f"\n最新TLE文件:")
    for const, date in health['latest_files'].items():
        print(f"  {const}: {date}")
    
    # 保存配置
    manager.save_config()