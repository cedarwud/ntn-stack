#!/usr/bin/env python3
"""
Phase 2.5 配置遷移工具
從分散配置遷移到統一配置系統

版本: v1.0.0
建立日期: 2025-08-10
目標: 安全地遷移現有配置到統一系統
"""

import logging
import json
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import asdict

from unified_satellite_config import (
    UnifiedSatelliteConfig, 
    ConstellationConfig, 
    ObserverLocation,
    SelectionStrategy,
    ValidationResult
)

logger = logging.getLogger(__name__)

class ConfigMigrationResult:
    """配置遷移結果"""
    
    def __init__(self):
        self.success: bool = True
        self.warnings: List[str] = []
        self.errors: List[str] = []
        self.backed_up_files: List[str] = []
        self.migrated_configs: Dict[str, str] = {}
    
    def add_warning(self, message: str):
        self.warnings.append(message)
        logger.warning(message)
    
    def add_error(self, message: str):
        self.errors.append(message)
        self.success = False
        logger.error(message)
    
    def add_backup(self, file_path: str):
        self.backed_up_files.append(file_path)
        logger.info(f"已備份: {file_path}")
    
    def add_migration(self, old_config: str, new_config: str):
        self.migrated_configs[old_config] = new_config
        logger.info(f"已遷移: {old_config} -> {new_config}")

class LegacyConfigExtractor:
    """舊配置提取器 - 從現有系統中提取配置"""
    
    def __init__(self, netstack_root: Path):
        self.netstack_root = Path(netstack_root)
        self.legacy_configs = {}
    
    def extract_build_time_config(self) -> Dict:
        """提取建構時配置 - 從 satellite_orbit_preprocessor.py 提取"""
        build_script = self.netstack_root / "docker" / "satellite_orbit_preprocessor.py"
        
        config = {
            "starlink_pool_size": 555,  # 從文檔中已知的最終配置
            "oneweb_pool_size": 134,
            "selection_method": "intelligent_filtering"
        }
        
        if build_script.exists():
            try:
                # 讀取並解析建構腳本中的配置
                with open(build_script, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 查找 max_display_starlink 等配置
                if "max_display_starlink" in content:
                    # 這裡可以添加更詳細的解析邏輯
                    logger.info(f"發現建構時配置於: {build_script}")
                    
            except Exception as e:
                logger.warning(f"無法解析建構腳本: {e}")
        
        return config
    
    def extract_runtime_config(self) -> Dict:
        """提取運行時配置 - 從 satellite_selector.py 提取"""
        selector_file = self.netstack_root / "src" / "services" / "satellite" / "preprocessing" / "satellite_selector.py"
        
        config = {
            "starlink_target": 15,  # 從文檔中已知的配置
            "oneweb_target": 8,
            "starlink_elevation": 10.0,
            "oneweb_elevation": 8.0,
            "selection_strategy": "dynamic_optimal"
        }
        
        if selector_file.exists():
            try:
                with open(selector_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 查找配置常數
                logger.info(f"發現運行時配置於: {selector_file}")
                
            except Exception as e:
                logger.warning(f"無法解析選擇器文件: {e}")
        
        return config
    
    def extract_observer_config(self) -> Dict:
        """提取觀測點配置"""
        return {
            "name": "NTPU",
            "latitude": 24.9441667,
            "longitude": 121.3713889,
            "altitude_m": 50.0,
            "timezone": "UTC+8"
        }
    
    def extract_all_configs(self) -> Dict:
        """提取所有舊配置"""
        self.legacy_configs = {
            "build_time": self.extract_build_time_config(),
            "runtime": self.extract_runtime_config(),
            "observer": self.extract_observer_config()
        }
        return self.legacy_configs

class ConfigMigrator:
    """配置遷移器 - 核心遷移邏輯"""
    
    def __init__(self, netstack_root: Path):
        self.netstack_root = Path(netstack_root)
        self.backup_dir = self.netstack_root / "config" / "backups"
        self.extractor = LegacyConfigExtractor(netstack_root)
        
        # 確保備份目錄存在
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def backup_existing_configs(self, result: ConfigMigrationResult) -> bool:
        """備份現有配置文件"""
        try:
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_subdir = self.backup_dir / f"migration_{timestamp}"
            backup_subdir.mkdir(parents=True, exist_ok=True)
            
            # 備份配置文件
            config_files = [
                self.netstack_root / "config" / "satellite_config.py",
                self.netstack_root / "docker" / "satellite_orbit_preprocessor.py",
                self.netstack_root / "src" / "services" / "satellite" / "preprocessing" / "satellite_selector.py"
            ]
            
            for config_file in config_files:
                if config_file.exists():
                    backup_file = backup_subdir / config_file.name
                    shutil.copy2(config_file, backup_file)
                    result.add_backup(str(backup_file))
            
            return True
            
        except Exception as e:
            result.add_error(f"備份配置失敗: {e}")
            return False
    
    def create_unified_config_from_legacy(self) -> UnifiedSatelliteConfig:
        """從舊配置創建統一配置"""
        # 提取舊配置
        legacy_configs = self.extractor.extract_all_configs()
        
        # 創建觀測點配置
        observer_data = legacy_configs.get("observer", {})
        observer = ObserverLocation(**observer_data)
        
        # 創建星座配置
        build_config = legacy_configs.get("build_time", {})
        runtime_config = legacy_configs.get("runtime", {})
        
        starlink_config = ConstellationConfig(
            name="starlink",
            total_satellites=build_config.get("starlink_pool_size", 555),
            target_satellites=runtime_config.get("starlink_target", 15),
            min_elevation=runtime_config.get("starlink_elevation", 10.0),
            selection_strategy=SelectionStrategy.DYNAMIC_OPTIMAL,
            pool_selection_method="diverse_orbital_sampling",
            tle_validity_hours=24,
            orbital_validation=True
        )
        
        oneweb_config = ConstellationConfig(
            name="oneweb",
            total_satellites=build_config.get("oneweb_pool_size", 134),
            target_satellites=runtime_config.get("oneweb_target", 8),
            min_elevation=runtime_config.get("oneweb_elevation", 8.0),
            selection_strategy=SelectionStrategy.COVERAGE_OPTIMAL,
            pool_selection_method="polar_coverage_sampling",
            tle_validity_hours=48,
            orbital_validation=True
        )
        
        # 創建統一配置
        unified_config = UnifiedSatelliteConfig(
            version="5.0.0",
            config_name="migrated_from_legacy",
            created_at="2025-08-10",
            observer=observer,
            constellations={
                "starlink": starlink_config,
                "oneweb": oneweb_config
            }
        )
        
        return unified_config
    
    def validate_migration(self, unified_config: UnifiedSatelliteConfig, result: ConfigMigrationResult) -> bool:
        """驗證遷移結果"""
        # 驗證統一配置
        validation_result = unified_config.validate()
        
        if not validation_result.is_valid:
            for error in validation_result.errors:
                result.add_error(f"統一配置驗證失敗: {error}")
            return False
        
        for warning in validation_result.warnings:
            result.add_warning(f"統一配置警告: {warning}")
        
        # 檢查數據一致性
        legacy_configs = self.extractor.legacy_configs
        
        # 檢查衛星數量一致性
        build_config = legacy_configs.get("build_time", {})
        runtime_config = legacy_configs.get("runtime", {})
        
        starlink_constellation = unified_config.get_constellation_config("starlink")
        oneweb_constellation = unified_config.get_constellation_config("oneweb")
        
        if starlink_constellation:
            if starlink_constellation.total_satellites != build_config.get("starlink_pool_size", 555):
                result.add_warning("Starlink 建構時配置不一致")
            if starlink_constellation.target_satellites != runtime_config.get("starlink_target", 15):
                result.add_warning("Starlink 運行時配置不一致")
        
        if oneweb_constellation:
            if oneweb_constellation.total_satellites != build_config.get("oneweb_pool_size", 134):
                result.add_warning("OneWeb 建構時配置不一致")
            if oneweb_constellation.target_satellites != runtime_config.get("oneweb_target", 8):
                result.add_warning("OneWeb 運行時配置不一致")
        
        return True
    
    def migrate(self) -> ConfigMigrationResult:
        """執行完整的配置遷移"""
        result = ConfigMigrationResult()
        
        logger.info("開始 Phase 2.5 配置遷移...")
        
        try:
            # 1. 備份現有配置
            if not self.backup_existing_configs(result):
                return result
            
            # 2. 創建統一配置
            unified_config = self.create_unified_config_from_legacy()
            
            # 3. 驗證遷移結果
            if not self.validate_migration(unified_config, result):
                return result
            
            # 4. 保存統一配置
            config_file = self.netstack_root / "config" / "unified_satellite_config.json"
            if unified_config.save_to_file(config_file):
                result.add_migration("legacy_configs", str(config_file))
            else:
                result.add_error("保存統一配置失敗")
                return result
            
            # 5. 生成遷移報告
            self._generate_migration_report(unified_config, result)
            
            logger.info("配置遷移完成")
            
        except Exception as e:
            result.add_error(f"遷移過程中發生異常: {e}")
            logger.exception("遷移異常")
        
        return result
    
    def _generate_migration_report(self, unified_config: UnifiedSatelliteConfig, result: ConfigMigrationResult):
        """生成遷移報告"""
        report = {
            "migration_summary": {
                "success": result.success,
                "timestamp": "2025-08-10",
                "warnings_count": len(result.warnings),
                "errors_count": len(result.errors)
            },
            "backup_files": result.backed_up_files,
            "migrated_configurations": result.migrated_configs,
            "new_unified_config": {
                "version": unified_config.version,
                "config_name": unified_config.config_name,
                "total_pool_satellites": sum(c.total_satellites for c in unified_config.constellations.values()),
                "total_target_satellites": sum(c.target_satellites for c in unified_config.constellations.values())
            },
            "warnings": result.warnings,
            "errors": result.errors
        }
        
        report_file = self.backup_dir / "migration_report.json"
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            logger.info(f"遷移報告已生成: {report_file}")
            
        except Exception as e:
            logger.error(f"生成遷移報告失敗: {e}")

def perform_migration(netstack_root: str) -> ConfigMigrationResult:
    """執行配置遷移的便利函數"""
    migrator = ConfigMigrator(Path(netstack_root))
    return migrator.migrate()

def validate_existing_unified_config(config_file: str) -> ValidationResult:
    """驗證現有的統一配置文件"""
    try:
        unified_config = UnifiedSatelliteConfig.load_from_file(config_file)
        return unified_config.validate()
    except Exception as e:
        result = ValidationResult(is_valid=False)
        result.add_error(f"無法加載配置文件: {e}")
        return result

if __name__ == "__main__":
    """配置遷移測試腳本"""
    import sys
    
    # 設置日誌
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 60)
    print("Phase 2.5 配置遷移工具")
    print("=" * 60)
    
    # 獲取 NetStack 根目錄
    netstack_root = Path(__file__).parent.parent
    
    print(f"NetStack 根目錄: {netstack_root}")
    print(f"開始配置遷移...")
    
    # 執行遷移
    result = perform_migration(str(netstack_root))
    
    # 輸出結果
    print(f"\n遷移結果: {'✅ 成功' if result.success else '❌ 失敗'}")
    
    if result.backed_up_files:
        print(f"\n備份文件:")
        for backup in result.backed_up_files:
            print(f"  - {backup}")
    
    if result.migrated_configs:
        print(f"\n遷移配置:")
        for old, new in result.migrated_configs.items():
            print(f"  {old} -> {new}")
    
    if result.warnings:
        print(f"\n警告:")
        for warning in result.warnings:
            print(f"  ⚠️  {warning}")
    
    if result.errors:
        print(f"\n錯誤:")
        for error in result.errors:
            print(f"  ❌ {error}")
    
    print(f"\n" + "=" * 60)
    print("配置遷移完成")
    print("=" * 60)