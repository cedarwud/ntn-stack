#!/usr/bin/env python3
"""
Phase 2.5 統一衛星配置管理系統
解決配置分散化和雙重篩選邏輯矛盾

版本: v5.0.0
建立日期: 2025-08-10
目標: 統一配置源，清晰的建構/運行時職責分離

遵循 CLAUDE.md 真實性原則：絕不使用簡化算法或模擬數據
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union
from enum import Enum
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class SelectionStrategy(Enum):
    """衛星選擇策略枚舉"""
    DYNAMIC_OPTIMAL = "dynamic_optimal"      # 動態最優選擇 (適用於 Starlink)
    COVERAGE_OPTIMAL = "coverage_optimal"    # 覆蓋最優選擇 (適用於 OneWeb)
    DIVERSITY_BALANCED = "diversity_balanced" # 多樣性平衡選擇
    HANDOVER_FOCUSED = "handover_focused"    # 換手專注選擇

@dataclass
class ObserverLocation:
    """觀測點配置 - 基於真實 NTPU 座標"""
    name: str = "NTPU"
    latitude: float = 24.9441667  # NTPU 緯度 (真實座標)
    longitude: float = 121.3713889  # NTPU 經度 (真實座標)
    altitude_m: float = 50.0  # 海拔高度 (米)
    timezone: str = "UTC+8"  # 時區

    def __post_init__(self):
        """驗證觀測點座標的合理性"""
        if not (-90 <= self.latitude <= 90):
            raise ValueError(f"緯度必須在 -90° 到 90° 之間: {self.latitude}")
        if not (-180 <= self.longitude <= 180):
            raise ValueError(f"經度必須在 -180° 到 180° 之間: {self.longitude}")
        if self.altitude_m < 0:
            raise ValueError(f"海拔高度不能為負數: {self.altitude_m}")

@dataclass
class ConstellationConfig:
    """單個星座配置 - 明確分離建構時和運行時職責"""
    name: str
    total_satellites: int      # 建構時準備的衛星池大小
    target_satellites: int     # 運行時選擇的目標數量
    min_elevation: float       # 最小仰角門檻 (度)
    
    # 可選參數 (帶默認值)
    pool_selection_method: str = "diverse_sampling"  # 衛星池選擇方法
    selection_strategy: SelectionStrategy = SelectionStrategy.DYNAMIC_OPTIMAL
    tle_validity_hours: int = 48  # TLE 數據有效期 (小時)
    orbital_validation: bool = True  # 是否進行軌道驗證
    
    def __post_init__(self):
        """驗證星座配置合理性"""
        if self.total_satellites <= 0:
            raise ValueError(f"{self.name}: 衛星池大小必須為正數: {self.total_satellites}")
        if self.target_satellites <= 0:
            raise ValueError(f"{self.name}: 目標衛星數量必須為正數: {self.target_satellites}")
        if self.target_satellites > self.total_satellites:
            raise ValueError(f"{self.name}: 目標衛星數量不能超過衛星池大小: {self.target_satellites} > {self.total_satellites}")
        if not (0 <= self.min_elevation <= 90):
            raise ValueError(f"{self.name}: 仰角門檻必須在 0° 到 90° 之間: {self.min_elevation}")
        if self.tle_validity_hours <= 0:
            raise ValueError(f"{self.name}: TLE 有效期必須為正數: {self.tle_validity_hours}")
        
        # 確保 selection_strategy 是 SelectionStrategy 枚舉
        if isinstance(self.selection_strategy, str):
            try:
                self.selection_strategy = SelectionStrategy(self.selection_strategy)
            except ValueError:
                raise ValueError(f"{self.name}: 無效的選擇策略: {self.selection_strategy}")

@dataclass
class ValidationResult:
    """配置驗證結果"""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def add_error(self, error: str):
        """添加錯誤"""
        self.errors.append(error)
        self.is_valid = False
    
    def add_warning(self, warning: str):
        """添加警告"""
        self.warnings.append(warning)

@dataclass
class BuildTimeConfig:
    """建構時配置 - 專門用於數據池準備階段"""
    constellations: Dict[str, Dict[str, Union[int, str]]]
    observer: ObserverLocation
    
    def get_pool_size(self, constellation: str) -> int:
        """獲取指定星座的衛星池大小"""
        return self.constellations.get(constellation, {}).get("total_satellites", 0)

@dataclass
class RuntimeConfig:
    """運行時配置 - 專門用於智能選擇階段"""
    constellations: Dict[str, Dict[str, Union[int, float, str]]]
    observer: ObserverLocation
    
    def get_target_count(self, constellation: str) -> int:
        """獲取指定星座的目標衛星數量"""
        return self.constellations.get(constellation, {}).get("target_satellites", 0)
    
    def get_min_elevation(self, constellation: str) -> float:
        """獲取指定星座的最小仰角門檻"""
        return self.constellations.get(constellation, {}).get("min_elevation", 0.0)

@dataclass
class UnifiedSatelliteConfig:
    """統一衛星配置管理系統 v5.0.0
    
    解決 Phase 2.5 架構問題：
    1. 配置分散化 -> 統一配置源
    2. 雙重篩選矛盾 -> 清晰職責分離  
    3. 邏輯重複 -> 單一真實源
    
    設計原則：
    - 建構時：準備充足的衛星池 (555/134 配置)
    - 運行時：智能選擇最佳衛星 (15/8 目標)
    - 配置統一：單一配置源，消除重複
    """
    
    # 版本資訊
    version: str = "5.0.0"
    config_name: str = "unified_555_134_standard"
    created_at: str = "2025-08-10"
    
    # 觀測點配置
    observer: ObserverLocation = field(default_factory=ObserverLocation)
    
    # 星座配置 - 555/134 統一標準 (基於完整軌道週期分析結果)
    constellations: Dict[str, ConstellationConfig] = field(default_factory=lambda: {
        "starlink": ConstellationConfig(
            name="starlink",
            total_satellites=555,      # 建構時衛星池：基於 SGP4 分析結果
            target_satellites=15,      # 運行時目標：3GPP NTN 標準換手候選
            min_elevation=10.0,        # 商業服務標準仰角門檻
            selection_strategy=SelectionStrategy.DYNAMIC_OPTIMAL,
            pool_selection_method="diverse_orbital_sampling",
            tle_validity_hours=24,     # Starlink TLE 更新頻繁
            orbital_validation=True
        ),
        "oneweb": ConstellationConfig(
            name="oneweb",
            total_satellites=134,      # 建構時衛星池：基於 SGP4 分析結果
            target_satellites=8,       # 運行時目標：OneWeb 極地軌道特性
            min_elevation=8.0,         # 略低於 Starlink，適應極地軌道
            selection_strategy=SelectionStrategy.COVERAGE_OPTIMAL,
            pool_selection_method="polar_coverage_sampling",
            tle_validity_hours=48,     # OneWeb TLE 更新較慢
            orbital_validation=True
        )
    })
    
    # 系統級配置
    enable_sgp4: bool = True           # 強制使用 SGP4 (符合 CLAUDE.md 真實性原則)
    enable_parallel_processing: bool = True
    max_processing_threads: int = 4
    
    # 數據品質要求
    position_accuracy_meters: float = 100.0  # 位置精度要求
    time_step_seconds: int = 30              # 計算時間步長
    
    def validate(self) -> ValidationResult:
        """配置驗證 - 確保所有配置的一致性和合理性"""
        result = ValidationResult(is_valid=True)
        
        try:
            # 驗證版本資訊
            if not self.version or not self.config_name:
                result.add_error("版本資訊和配置名稱不能為空")
            
            # 驗證觀測點
            try:
                # ObserverLocation 的 __post_init__ 會自動驗證
                pass
            except ValueError as e:
                result.add_error(f"觀測點配置錯誤: {e}")
            
            # 驗證星座配置
            if not self.constellations:
                result.add_error("至少需要配置一個星座")
            else:
                for constellation_name, config in self.constellations.items():
                    try:
                        # ConstellationConfig 的 __post_init__ 會自動驗證
                        pass
                    except ValueError as e:
                        result.add_error(f"星座 {constellation_name} 配置錯誤: {e}")
                    
                    # 檢查建構時/運行時配置一致性
                    if config.target_satellites > config.total_satellites:
                        result.add_error(f"{constellation_name}: 運行時目標 ({config.target_satellites}) 超過建構時衛星池 ({config.total_satellites})")
                    
                    # 檢查是否符合 3GPP NTN 標準
                    if config.target_satellites > 8:
                        result.add_warning(f"{constellation_name}: 目標衛星數 ({config.target_satellites}) 超過 3GPP NTN 建議的 8 顆上限")
            
            # 驗證系統級配置
            if self.max_processing_threads <= 0:
                result.add_error(f"處理線程數必須為正數: {self.max_processing_threads}")
            
            if self.position_accuracy_meters <= 0:
                result.add_error(f"位置精度要求必須為正數: {self.position_accuracy_meters}")
            
            if self.time_step_seconds <= 0:
                result.add_error(f"時間步長必須為正數: {self.time_step_seconds}")
            
            # 檢查 SGP4 要求 (符合 CLAUDE.md 原則)
            if not self.enable_sgp4:
                result.add_error("根據 CLAUDE.md 原則，必須啟用 SGP4 真實軌道計算")
            
            # 統計總衛星數
            total_pool_satellites = sum(config.total_satellites for config in self.constellations.values())
            total_target_satellites = sum(config.target_satellites for config in self.constellations.values())
            
            logger.info(f"配置統計: 衛星池總數 {total_pool_satellites}, 運行時目標總數 {total_target_satellites}")
            
            # 合理性檢查
            if total_pool_satellites > 1000:
                result.add_warning(f"衛星池總數過大 ({total_pool_satellites})，可能影響建構性能")
            
            if total_target_satellites < 8:
                result.add_warning(f"運行時目標總數過少 ({total_target_satellites})，可能影響換手性能")
                
        except Exception as e:
            result.add_error(f"配置驗證過程中發生異常: {str(e)}")
            logger.exception("配置驗證異常")
        
        return result
    
    def get_build_config(self) -> BuildTimeConfig:
        """獲取建構時配置 - 專門用於數據池準備階段"""
        build_constellations = {}
        
        for name, config in self.constellations.items():
            build_constellations[name] = {
                "total_satellites": config.total_satellites,
                "pool_selection_method": config.pool_selection_method,
                "tle_validity_hours": config.tle_validity_hours,
                "orbital_validation": config.orbital_validation
            }
        
        return BuildTimeConfig(
            constellations=build_constellations,
            observer=self.observer
        )
    
    def get_runtime_config(self) -> RuntimeConfig:
        """獲取運行時配置 - 專門用於智能選擇階段"""
        runtime_constellations = {}
        
        for name, config in self.constellations.items():
            runtime_constellations[name] = {
                "target_satellites": config.target_satellites,
                "min_elevation": config.min_elevation,
                "selection_strategy": config.selection_strategy.value,
                "tle_validity_hours": config.tle_validity_hours
            }
        
        return RuntimeConfig(
            constellations=runtime_constellations,
            observer=self.observer
        )
    
    def get_constellation_config(self, constellation_name: str) -> Optional[ConstellationConfig]:
        """獲取指定星座的配置"""
        return self.constellations.get(constellation_name)
    
    def save_to_file(self, file_path: Union[str, Path]) -> bool:
        """保存配置到文件"""
        try:
            config_dict = {
                "version": self.version,
                "config_name": self.config_name,
                "created_at": self.created_at,
                "observer": {
                    "name": self.observer.name,
                    "latitude": self.observer.latitude,
                    "longitude": self.observer.longitude,
                    "altitude_m": self.observer.altitude_m,
                    "timezone": self.observer.timezone
                },
                "constellations": {},
                "system": {
                    "enable_sgp4": self.enable_sgp4,
                    "enable_parallel_processing": self.enable_parallel_processing,
                    "max_processing_threads": self.max_processing_threads,
                    "position_accuracy_meters": self.position_accuracy_meters,
                    "time_step_seconds": self.time_step_seconds
                }
            }
            
            for name, config in self.constellations.items():
                config_dict["constellations"][name] = {
                    "name": config.name,
                    "total_satellites": config.total_satellites,
                    "target_satellites": config.target_satellites,
                    "min_elevation": config.min_elevation,
                    "selection_strategy": config.selection_strategy.value,
                    "pool_selection_method": config.pool_selection_method,
                    "tle_validity_hours": config.tle_validity_hours,
                    "orbital_validation": config.orbital_validation
                }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
            
            logger.info(f"配置已保存到: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"保存配置失敗: {e}")
            return False
    
    @classmethod
    def load_from_file(cls, file_path: Union[str, Path]) -> 'UnifiedSatelliteConfig':
        """從文件加載配置"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config_dict = json.load(f)
            
            # 創建觀測點
            observer_data = config_dict.get("observer", {})
            observer = ObserverLocation(**observer_data)
            
            # 創建星座配置
            constellations = {}
            for name, constellation_data in config_dict.get("constellations", {}).items():
                # 確保 selection_strategy 是正確的枚舉值
                strategy_value = constellation_data.get("selection_strategy", "dynamic_optimal")
                constellation_data["selection_strategy"] = SelectionStrategy(strategy_value)
                constellations[name] = ConstellationConfig(**constellation_data)
            
            # 創建系統配置
            system_config = config_dict.get("system", {})
            
            # 創建配置實例
            config = cls(
                version=config_dict.get("version", "5.0.0"),
                config_name=config_dict.get("config_name", "loaded_config"),
                created_at=config_dict.get("created_at", "unknown"),
                observer=observer,
                constellations=constellations,
                enable_sgp4=system_config.get("enable_sgp4", True),
                enable_parallel_processing=system_config.get("enable_parallel_processing", True),
                max_processing_threads=system_config.get("max_processing_threads", 4),
                position_accuracy_meters=system_config.get("position_accuracy_meters", 100.0),
                time_step_seconds=system_config.get("time_step_seconds", 30)
            )
            
            logger.info(f"配置已從 {file_path} 加載")
            return config
            
        except Exception as e:
            logger.error(f"加載配置失敗: {e}")
            raise


# === 全局配置實例 ===

# 創建默認的統一配置實例
DEFAULT_UNIFIED_CONFIG = UnifiedSatelliteConfig()

def get_unified_config() -> UnifiedSatelliteConfig:
    """獲取統一配置實例"""
    return DEFAULT_UNIFIED_CONFIG

def validate_unified_config() -> ValidationResult:
    """驗證統一配置"""
    return DEFAULT_UNIFIED_CONFIG.validate()

# === 向後兼容性接口 ===

def get_build_time_satellite_count(constellation: str) -> int:
    """獲取建構時衛星數量 (向後兼容)"""
    config = get_unified_config()
    constellation_config = config.get_constellation_config(constellation)
    return constellation_config.total_satellites if constellation_config else 0

def get_runtime_satellite_count(constellation: str) -> int:
    """獲取運行時目標衛星數量 (向後兼容)"""
    config = get_unified_config()
    constellation_config = config.get_constellation_config(constellation)
    return constellation_config.target_satellites if constellation_config else 0

def get_min_elevation_degrees(constellation: str) -> float:
    """獲取最小仰角門檻 (向後兼容)"""
    config = get_unified_config()
    constellation_config = config.get_constellation_config(constellation)
    return constellation_config.min_elevation if constellation_config else 0.0


if __name__ == "__main__":
    """配置測試和驗證腳本"""
    print("=" * 60)
    print("Phase 2.5 統一衛星配置管理系統")
    print("=" * 60)
    
    # 創建和驗證配置
    config = UnifiedSatelliteConfig()
    validation_result = config.validate()
    
    print(f"配置版本: {config.version}")
    print(f"配置名稱: {config.config_name}")
    print(f"建立日期: {config.created_at}")
    
    print(f"\n觀測點: {config.observer.name}")
    print(f"座標: {config.observer.latitude:.6f}°N, {config.observer.longitude:.6f}°E")
    print(f"海拔: {config.observer.altitude_m:.1f}m")
    
    print(f"\n星座配置:")
    for name, constellation_config in config.constellations.items():
        print(f"  {name.upper()}:")
        print(f"    建構時衛星池: {constellation_config.total_satellites} 顆")
        print(f"    運行時目標: {constellation_config.target_satellites} 顆")
        print(f"    仰角門檻: {constellation_config.min_elevation}°")
        print(f"    選擇策略: {constellation_config.selection_strategy.value}")
    
    print(f"\n系統配置:")
    print(f"  SGP4 啟用: {config.enable_sgp4}")
    print(f"  並行處理: {config.enable_parallel_processing}")
    print(f"  處理線程: {config.max_processing_threads}")
    print(f"  位置精度: {config.position_accuracy_meters}m")
    print(f"  時間步長: {config.time_step_seconds}s")
    
    print(f"\n配置驗證結果:")
    if validation_result.is_valid:
        print("✅ 配置驗證通過")
    else:
        print("❌ 配置驗證失敗")
        for error in validation_result.errors:
            print(f"  錯誤: {error}")
    
    if validation_result.warnings:
        print("⚠️  配置警告:")
        for warning in validation_result.warnings:
            print(f"  警告: {warning}")
    
    # 測試建構時和運行時配置分離
    print(f"\n建構時配置測試:")
    build_config = config.get_build_config()
    for name in ["starlink", "oneweb"]:
        pool_size = build_config.get_pool_size(name)
        print(f"  {name}: 準備 {pool_size} 顆衛星池")
    
    print(f"\n運行時配置測試:")
    runtime_config = config.get_runtime_config()
    for name in ["starlink", "oneweb"]:
        target_count = runtime_config.get_target_count(name)
        min_elevation = runtime_config.get_min_elevation(name)
        print(f"  {name}: 選擇 {target_count} 顆衛星 (≥{min_elevation}°)")
    
    # 測試配置文件保存
    config_file = Path("/tmp/unified_satellite_config_test.json")
    if config.save_to_file(config_file):
        print(f"\n✅ 配置已保存到: {config_file}")
        
        # 測試加載配置
        try:
            loaded_config = UnifiedSatelliteConfig.load_from_file(config_file)
            print(f"✅ 配置已從文件加載: {loaded_config.config_name}")
        except Exception as e:
            print(f"❌ 配置加載失敗: {e}")
    else:
        print(f"\n❌ 配置保存失敗")
    
    print(f"\n" + "=" * 60)
    print("Phase 2.5 統一配置系統測試完成")
    print("=" * 60)