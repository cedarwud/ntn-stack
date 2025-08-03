#!/usr/bin/env python3
"""
LEO 衛星系統統一配置
實現改進路線圖 Phase 1 的配置統一要求

此文件是衛星數量、計算精度、智能篩選的中央配置點，
取代分散在多個模組中的硬編碼數值。

遵循 CLAUDE.md 的真實性原則：所有參數基於 3GPP NTN 標準和 ITU-R 建議書。
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum
import threading

class ProcessingStage(Enum):
    """處理階段枚舉"""
    SIB19_RUNTIME = "sib19_runtime"        # SIB19 運行時：最嚴格限制
    PREPROCESS = "preprocess"              # 預處理階段：智能篩選
    BATCH_COMPUTE = "batch_compute"        # 批次計算：最大化覆蓋
    ALGORITHM_TEST = "algorithm_test"      # 算法測試：受控環境

class ConstellationType(Enum):
    """星座類型枚舉"""
    STARLINK = "starlink"
    ONEWEB = "oneweb"
    KUIPER = "kuiper"
    ALL = "all"

@dataclass
class ElevationThresholds:
    """仰角門檻配置 - 基於 ITU-R P.618 標準"""
    
    # 分層仰角門檻 (度)
    PREPARATION_TRIGGER: float = 15.0    # 預備觸發：準備換手
    EXECUTION_THRESHOLD: float = 10.0    # 執行門檻：標準門檻
    CRITICAL_THRESHOLD: float = 5.0      # 臨界門檻：最低可用
    
    # 環境調整係數 (基於地理和氣象條件)
    ENVIRONMENT_FACTORS: Dict[str, float] = None
    
    def __post_init__(self):
        if self.ENVIRONMENT_FACTORS is None:
            self.ENVIRONMENT_FACTORS = {
                "open_area": 1.0,        # 開闊地區：無調整
                "urban": 1.1,            # 城市環境：+10%
                "mountainous": 1.3,      # 山區：+30%
                "heavy_rain": 1.4        # 強降雨：+40%
            }

@dataclass
class IntelligentSelection:
    """智能篩選配置"""
    
    enabled: bool = True
    geographic_filter: bool = True
    handover_suitability_scoring: bool = True
    
    # 目標觀測位置 (NTPU 為主要研究點)
    target_location: Dict[str, float] = None
    
    # 地理相關性篩選參數
    orbital_inclination_match: bool = True
    raan_longitude_match: bool = True
    
    # 換手適用性評分權重
    scoring_weights: Dict[str, float] = None
    
    def __post_init__(self):
        if self.target_location is None:
            self.target_location = {
                "lat": 24.9441667,      # NTPU 緯度
                "lon": 121.3713889      # NTPU 經度
            }
        
        if self.scoring_weights is None:
            self.scoring_weights = {
                "altitude_factor": 0.3,      # 高度因子
                "orbit_shape": 0.25,         # 軌道形狀
                "pass_frequency": 0.25,      # 通過頻率
                "constellation_diversity": 0.2  # 星座多樣性
            }

@dataclass
class ComputationPrecision:
    """計算精度配置"""
    
    # 軌道計算方法
    USE_SGP4_IN_PREPROCESSING: bool = True      # 預處理階段使用 SGP4
    USE_SGP4_IN_RUNTIME: bool = True            # 運行時使用 SGP4
    
    # 計算參數
    TIME_STEP_SECONDS: int = 30                 # 時間步長 (秒)
    POSITION_ACCURACY_METERS: float = 100.0     # 位置精度要求 (米)
    
    # 性能優化
    ENABLE_PARALLEL_COMPUTATION: bool = True    # 啟用並行計算
    MAX_COMPUTATION_THREADS: int = 4            # 最大計算線程

@dataclass 
class SatelliteConfig:
    """衛星系統統一配置類
    
    根據改進路線圖設計，整合所有分散的衛星數量配置，
    確保符合 3GPP NTN 標準和系統設計要求。
    """
    
    # === 核心衛星數量配置 ===
    
    # SIB19 合規：3GPP NTN 標準要求最多 8 顆候選衛星
    MAX_CANDIDATE_SATELLITES: int = 8
    
    # 預處理階段優化數量：基於智能篩選結果的經驗值
    PREPROCESS_SATELLITES: Dict[str, int] = None
    
    # 批次計算最大數量：確保覆蓋完整性的最大值
    BATCH_COMPUTE_MAX_SATELLITES: int = 50
    
    # 算法測試環境數量：受控測試環境的平衡值
    ALGORITHM_TEST_MAX_SATELLITES: int = 10
    
    # === 子系統配置 ===
    
    elevation_thresholds: ElevationThresholds = None
    intelligent_selection: IntelligentSelection = None
    computation_precision: ComputationPrecision = None
    
    def __post_init__(self):
        """初始化預設值"""
        if self.PREPROCESS_SATELLITES is None:
            self.PREPROCESS_SATELLITES = {
                "starlink": 40,     # Starlink：較大星座，需更多候選
                "oneweb": 30,       # OneWeb：中等星座，適中候選
                "kuiper": 35,       # Kuiper：預估值 (未來)
                "all": 50           # 所有星座：最大覆蓋
            }
        
        if self.elevation_thresholds is None:
            self.elevation_thresholds = ElevationThresholds()
            
        if self.intelligent_selection is None:
            self.intelligent_selection = IntelligentSelection()
            
        if self.computation_precision is None:
            self.computation_precision = ComputationPrecision()
    
    def get_max_satellites_for_stage(self, stage: str, constellation: str = None) -> int:
        """根據處理階段和星座獲取最大衛星數量
        
        Args:
            stage: ProcessingStage 枚舉值或字符串
            constellation: ConstellationType 枚舉值或字符串 (可選)
            
        Returns:
            該階段和星座的最大衛星數量
        """
        
        # 轉換字符串為枚舉
        if isinstance(stage, str):
            try:
                stage_enum = ProcessingStage(stage)
            except ValueError:
                raise ValueError(f"不支援的處理階段: {stage}")
        else:
            stage_enum = stage
        
        # 根據階段返回對應的數量
        if stage_enum == ProcessingStage.SIB19_RUNTIME:
            return self.MAX_CANDIDATE_SATELLITES
        
        elif stage_enum == ProcessingStage.PREPROCESS:
            if constellation:
                return self.PREPROCESS_SATELLITES.get(constellation, 30)
            return self.PREPROCESS_SATELLITES.get("all", 50)
        
        elif stage_enum == ProcessingStage.BATCH_COMPUTE:
            return self.BATCH_COMPUTE_MAX_SATELLITES
        
        elif stage_enum == ProcessingStage.ALGORITHM_TEST:
            return self.ALGORITHM_TEST_MAX_SATELLITES
        
        else:
            raise ValueError(f"未知的處理階段: {stage_enum}")
    
    def validate_configuration(self) -> List[str]:
        """驗證配置的合理性
        
        Returns:
            配置問題列表，空列表表示無問題
        """
        issues = []
        
        try:
            # 檢查 SIB19 合規性
            if self.MAX_CANDIDATE_SATELLITES > 8:
                issues.append(f"MAX_CANDIDATE_SATELLITES ({self.MAX_CANDIDATE_SATELLITES}) 超過 SIB19 標準限制 (8)")
            elif self.MAX_CANDIDATE_SATELLITES <= 0:
                issues.append(f"MAX_CANDIDATE_SATELLITES ({self.MAX_CANDIDATE_SATELLITES}) 必須為正數")
            
            # 檢查預處理數量合理性
            if self.PREPROCESS_SATELLITES:
                for constellation, count in self.PREPROCESS_SATELLITES.items():
                    if not isinstance(count, int) or count <= 0:
                        issues.append(f"預處理 {constellation} 數量 ({count}) 必須為正整數")
                    elif count < self.MAX_CANDIDATE_SATELLITES:
                        issues.append(f"預處理 {constellation} 數量 ({count}) 小於 SIB19 最大值 ({self.MAX_CANDIDATE_SATELLITES})")
            
            # 檢查批次計算數量
            if self.BATCH_COMPUTE_MAX_SATELLITES <= 0:
                issues.append(f"BATCH_COMPUTE_MAX_SATELLITES ({self.BATCH_COMPUTE_MAX_SATELLITES}) 必須為正數")
            elif self.PREPROCESS_SATELLITES and self.BATCH_COMPUTE_MAX_SATELLITES < max(self.PREPROCESS_SATELLITES.values()):
                issues.append("BATCH_COMPUTE_MAX_SATELLITES 小於預處理階段的最大值")
            
            # 檢查算法測試數量
            if self.ALGORITHM_TEST_MAX_SATELLITES <= 0:
                issues.append(f"ALGORITHM_TEST_MAX_SATELLITES ({self.ALGORITHM_TEST_MAX_SATELLITES}) 必須為正數")
            
            # 檢查仰角門檻邏輯
            if self.elevation_thresholds:
                prep = self.elevation_thresholds.PREPARATION_TRIGGER
                exec_ = self.elevation_thresholds.EXECUTION_THRESHOLD  
                crit = self.elevation_thresholds.CRITICAL_THRESHOLD
                
                if not (prep > exec_ > crit > 0):
                    issues.append(f"仰角門檻必須遞減且為正數: 預備({prep}) > 執行({exec_}) > 臨界({crit}) > 0")
            
            # 檢查計算精度參數
            if self.computation_precision:
                if self.computation_precision.TIME_STEP_SECONDS <= 0:
                    issues.append(f"TIME_STEP_SECONDS ({self.computation_precision.TIME_STEP_SECONDS}) 必須為正數")
                
                if self.computation_precision.POSITION_ACCURACY_METERS <= 0:
                    issues.append(f"POSITION_ACCURACY_METERS ({self.computation_precision.POSITION_ACCURACY_METERS}) 必須為正數")
                
                if self.computation_precision.MAX_COMPUTATION_THREADS <= 0:
                    issues.append(f"MAX_COMPUTATION_THREADS ({self.computation_precision.MAX_COMPUTATION_THREADS}) 必須為正數")
            
        except Exception as e:
            issues.append(f"配置驗證過程中發生異常: {str(e)}")
        
        return issues


# === 全域配置實例 ===

# 線程安全的配置鎖
_config_lock = threading.RLock()

# 建立全域配置實例，供所有模組使用
SATELLITE_CONFIG = SatelliteConfig()

def get_config_safely():
    """線程安全地獲取配置實例"""
    with _config_lock:
        return SATELLITE_CONFIG

# 驗證配置合理性
_config_issues = SATELLITE_CONFIG.validate_configuration()
if _config_issues:
    import warnings
    for issue in _config_issues:
        warnings.warn(f"衛星配置問題: {issue}", UserWarning)

# === 便利函數 ===

def get_max_satellites(stage: str, constellation: str = None) -> int:
    """便利函數：獲取指定階段的最大衛星數量"""
    return SATELLITE_CONFIG.get_max_satellites_for_stage(stage, constellation)

def get_elevation_threshold(threshold_type: str, environment: str = "open_area") -> float:
    """便利函數：獲取調整後的仰角門檻"""
    thresholds = SATELLITE_CONFIG.elevation_thresholds
    
    base_threshold = {
        "preparation": thresholds.PREPARATION_TRIGGER,
        "execution": thresholds.EXECUTION_THRESHOLD,
        "critical": thresholds.CRITICAL_THRESHOLD
    }.get(threshold_type)
    
    if base_threshold is None:
        raise ValueError(f"不支援的門檻類型: {threshold_type}")
    
    factor = thresholds.ENVIRONMENT_FACTORS.get(environment, 1.0)
    return base_threshold * factor

def is_sgp4_enabled(stage: str) -> bool:
    """便利函數：檢查指定階段是否啟用 SGP4"""
    precision = SATELLITE_CONFIG.computation_precision
    
    if stage == "preprocessing":
        return precision.USE_SGP4_IN_PREPROCESSING
    elif stage == "runtime":
        return precision.USE_SGP4_IN_RUNTIME
    else:
        return True  # 預設啟用

# === 配置匯出 ===

# 為了與現有代碼的向後兼容，匯出常用的配置值
MAX_TRACKED_SATELLITES = SATELLITE_CONFIG.MAX_CANDIDATE_SATELLITES
STARLINK_PREPROCESS_COUNT = SATELLITE_CONFIG.PREPROCESS_SATELLITES["starlink"]
ONEWEB_PREPROCESS_COUNT = SATELLITE_CONFIG.PREPROCESS_SATELLITES["oneweb"]
BATCH_MAX_SATELLITES = SATELLITE_CONFIG.BATCH_COMPUTE_MAX_SATELLITES

# 匯出計算配置
SGP4_ENABLED_PREPROCESSING = SATELLITE_CONFIG.computation_precision.USE_SGP4_IN_PREPROCESSING
SGP4_ENABLED_RUNTIME = SATELLITE_CONFIG.computation_precision.USE_SGP4_IN_RUNTIME
TIME_STEP_SECONDS = SATELLITE_CONFIG.computation_precision.TIME_STEP_SECONDS

if __name__ == "__main__":
    """配置測試和驗證"""
    print("=== LEO 衛星系統統一配置 ===")
    print(f"SIB19 最大候選衛星: {SATELLITE_CONFIG.MAX_CANDIDATE_SATELLITES}")
    print(f"預處理階段配置: {SATELLITE_CONFIG.PREPROCESS_SATELLITES}")
    print(f"批次計算最大衛星: {SATELLITE_CONFIG.BATCH_COMPUTE_MAX_SATELLITES}")
    print(f"算法測試最大衛星: {SATELLITE_CONFIG.ALGORITHM_TEST_MAX_SATELLITES}")
    
    print("\n=== 仰角門檻配置 ===")
    thresholds = SATELLITE_CONFIG.elevation_thresholds
    print(f"預備觸發: {thresholds.PREPARATION_TRIGGER}°")
    print(f"執行門檻: {thresholds.EXECUTION_THRESHOLD}°")
    print(f"臨界門檻: {thresholds.CRITICAL_THRESHOLD}°")
    
    print("\n=== 計算精度配置 ===")
    precision = SATELLITE_CONFIG.computation_precision
    print(f"預處理使用 SGP4: {precision.USE_SGP4_IN_PREPROCESSING}")
    print(f"運行時使用 SGP4: {precision.USE_SGP4_IN_RUNTIME}")
    print(f"時間步長: {precision.TIME_STEP_SECONDS} 秒")
    
    print("\n=== 配置驗證 ===")
    issues = SATELLITE_CONFIG.validate_configuration()
    if issues:
        print("發現配置問題:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("✅ 配置驗證通過")