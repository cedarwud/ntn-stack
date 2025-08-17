#!/usr/bin/env python3
"""
統一仰角門檻配置系統
解決 Phase 0 中不同模組使用不同仰角標準的問題
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class StandardElevationConfig:
    """標準仰角配置"""
    
    # 基礎門檻 (ITU-R P.618 建議)
    minimum_visibility_threshold: float = 5.0      # 最低可見門檻
    itu_compliant_threshold: float = 10.0          # ITU 合規門檻
    preferred_handover_threshold: float = 12.0     # 推薦換手門檻
    optimal_service_threshold: float = 15.0        # 最佳服務門檻
    
    # 分層換手門檻 (根據 NASA 衛星激光測距系統建議調整)
    pre_handover_trigger: float = 12.0             # 預備觸發
    handover_execution: float = 10.0               # 執行門檻
    critical_handover: float = 5.0                 # 臨界換手
    
    # 環境調整係數
    environment_adjustments: Dict[str, float] = None
    
    def __post_init__(self):
        if self.environment_adjustments is None:
            self.environment_adjustments = {
                "open_area": 1.0,       # 開闊地區
                "urban": 1.125,         # 城市環境 (1.1-1.15 中值)
                "suburban": 1.05,       # 郊區
                "mountain": 1.3,        # 山區 (1.2-1.4 中值)
                "heavy_rain": 1.45,     # 強降雨區 (1.4-1.5 中值)
                "coastal": 1.1,         # 海岸地區
                "indoor": 1.5           # 室內環境
            }
    
    def get_adjusted_threshold(self, base_threshold: float, 
                             environment: str = "open_area") -> float:
        """根據環境調整門檻"""
        adjustment = self.environment_adjustments.get(environment, 1.0)
        return base_threshold * adjustment
    
    def get_system_defaults(self) -> Dict[str, float]:
        """獲取系統預設配置"""
        return {
            "coordinate_engine_default": self.minimum_visibility_threshold,
            "ntpu_filter_default": self.minimum_visibility_threshold,
            "handover_analysis_default": self.itu_compliant_threshold,
            "research_analysis_default": self.itu_compliant_threshold,
            "production_service_default": self.preferred_handover_threshold
        }
    
    def export_config(self, config_path: Path) -> bool:
        """匯出配置到 JSON 文件"""
        try:
            config_data = {
                "standard_elevation_config": asdict(self),
                "generated_at": "2025-07-29",
                "version": "1.0.0",
                "description": "統一仰角門檻配置 - 解決 Phase 0 標準不一致問題",
                "references": [
                    "ITU-R P.618-14: Propagation data and prediction methods",
                    "3GPP TS 38.331: NTN Radio Resource Control",
                    "Phase 0 實際測試結果分析"
                ]
            }
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"配置已匯出至: {config_path}")
            return True
            
        except Exception as e:
            logger.error(f"配置匯出失敗: {e}")
            return False

class ElevationConfigManager:
    """仰角配置管理器"""
    
    def __init__(self, config_file: Optional[Path] = None):
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件路徑，None 則使用預設配置
        """
        self.config_file = config_file
        self.config = self._load_config()
        
        logger.info("ElevationConfigManager 初始化完成")
        logger.info(f"ITU 合規門檻: {self.config.itu_compliant_threshold}°")
        logger.info(f"推薦換手門檻: {self.config.preferred_handover_threshold}°")
    
    def _load_config(self) -> StandardElevationConfig:
        """載入配置"""
        if self.config_file and self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    config_data = data.get('standard_elevation_config', {})
                    return StandardElevationConfig(**config_data)
            except Exception as e:
                logger.warning(f"配置載入失敗，使用預設值: {e}")
        
        return StandardElevationConfig()
    
    def get_threshold_for_use_case(self, use_case: str, 
                                 environment: str = "open_area") -> float:
        """
        根據使用場景獲取適當的仰角門檻
        
        Args:
            use_case: 使用場景 (visibility/handover/research/production)
            environment: 環境類型
            
        Returns:
            float: 調整後的仰角門檻
        """
        base_thresholds = {
            "visibility": self.config.minimum_visibility_threshold,
            "handover": self.config.itu_compliant_threshold,
            "research": self.config.itu_compliant_threshold,
            "production": self.config.preferred_handover_threshold,
            "optimal": self.config.optimal_service_threshold
        }
        
        base_threshold = base_thresholds.get(use_case, 
                                           self.config.itu_compliant_threshold)
        
        return self.config.get_adjusted_threshold(base_threshold, environment)
    
    def get_layered_thresholds(self, environment: str = "open_area") -> Dict[str, float]:
        """獲取分層換手門檻"""
        return {
            "pre_handover": self.config.get_adjusted_threshold(
                self.config.pre_handover_trigger, environment
            ),
            "execution": self.config.get_adjusted_threshold(
                self.config.handover_execution, environment
            ),
            "critical": self.config.critical_handover,  # 臨界門檻不調整
            "environment": environment
        }
    
    def get_dynamic_adjustment(self, threshold: float, snr: float = None, rssi: float = None) -> Dict[str, Any]:
        """
        基於信號品質動態調整門檻
        
        Args:
            threshold: 基礎門檻值
            snr: 信噪比 (dB)
            rssi: 接收信號強度指示器 (dBm)
            
        Returns:
            Dict: 動態調整結果
        """
        adjusted_threshold = threshold
        adjustment_reason = []
        
        # 基於 SNR 調整
        if snr is not None:
            if snr < 10:  # 低信噪比
                snr_adjustment = 2.0
                adjustment_reason.append(f"低 SNR ({snr} dB) +2°")
            elif snr < 15:  # 中等信噪比  
                snr_adjustment = 1.0
                adjustment_reason.append(f"中等 SNR ({snr} dB) +1°")
            else:  # 高信噪比
                snr_adjustment = 0.0
                adjustment_reason.append(f"良好 SNR ({snr} dB) 無調整")
            
            adjusted_threshold += snr_adjustment
        
        # 基於 RSSI 調整
        if rssi is not None:
            if rssi < -100:  # 弱信號
                rssi_adjustment = 1.5
                adjustment_reason.append(f"弱 RSSI ({rssi} dBm) +1.5°")
            elif rssi < -90:  # 中等信號
                rssi_adjustment = 0.5  
                adjustment_reason.append(f"中等 RSSI ({rssi} dBm) +0.5°")
            else:  # 強信號
                rssi_adjustment = 0.0
                adjustment_reason.append(f"強 RSSI ({rssi} dBm) 無調整")
            
            adjusted_threshold += rssi_adjustment
        
        return {
            "original_threshold": threshold,
            "adjusted_threshold": round(adjusted_threshold, 1),
            "total_adjustment": round(adjusted_threshold - threshold, 1),
            "adjustment_factors": adjustment_reason,
            "recommendation": "使用調整後門檻" if adjusted_threshold != threshold else "使用原始門檻"
        }
    
    def generate_migration_plan(self) -> Dict[str, Any]:
        """生成現有系統的遷移計劃"""
        migration_plan = {
            "current_issues": [
                "CoordinateSpecificOrbitEngine 預設使用 5° 門檻",
                "研究分析使用 10° 門檻", 
                "早期報告數據不一致",
                "不同模組間標準不統一"
            ],
            "recommended_actions": [
                {
                    "component": "CoordinateSpecificOrbitEngine",
                    "current_default": 5.0,
                    "recommended_default": self.config.itu_compliant_threshold,
                    "rationale": "符合 ITU-R P.618 標準，確保信號品質"
                },
                {
                    "component": "NTPUVisibilityFilter", 
                    "current_default": 5.0,
                    "recommended_default": self.config.itu_compliant_threshold,
                    "rationale": "與軌道引擎保持一致"
                },
                {
                    "component": "LayeredElevationEngine",
                    "implementation": "new",
                    "thresholds": self.get_layered_thresholds(),
                    "rationale": "實現您建議的分層換手策略"
                }
            ],
            "migration_steps": [
                "1. 更新 CoordinateSpecificOrbitEngine 預設門檻為 10°",
                "2. 更新 NTPUVisibilityFilter 預設門檻為 10°", 
                "3. 整合 LayeredElevationEngine 到主要換手流程",
                "4. 更新所有相關文檔和報告",
                "5. 重新生成 Phase 0 預計算數據"
            ],
            "backward_compatibility": {
                "maintain_5deg_option": True,
                "config_file_override": True,
                "api_parameter_support": True
            }
        }
        
        return migration_plan
    
    def validate_system_consistency(self) -> Dict[str, Any]:
        """驗證系統一致性"""
        validation_results = {
            "timestamp": "2025-07-29",
            "checks": {
                "itu_compliance": self.config.itu_compliant_threshold >= 10.0,
                "layered_logic": (
                    self.config.pre_handover_trigger > 
                    self.config.handover_execution > 
                    self.config.critical_handover
                ),
                "environment_factors": all(
                    factor >= 1.0 for factor in 
                    self.config.environment_adjustments.values()
                )
            },
            "recommendations": []
        }
        
        if not validation_results["checks"]["itu_compliance"]:
            validation_results["recommendations"].append(
                "ITU 合規門檻應 ≥ 10° 以符合 ITU-R P.618 標準"
            )
        
        if not validation_results["checks"]["layered_logic"]:
            validation_results["recommendations"].append(
                "分層門檻邏輯錯誤：預備觸發 > 執行門檻 > 臨界門檻"
            )
        
        return validation_results

# 全域配置實例
_global_config_manager = None

def get_elevation_config(config_file: Optional[Path] = None) -> ElevationConfigManager:
    """獲取全域配置管理器實例"""
    global _global_config_manager
    if _global_config_manager is None:
        _global_config_manager = ElevationConfigManager(config_file)
    return _global_config_manager

def get_standard_threshold(use_case: str = "handover", 
                         environment: str = "open_area") -> float:
    """快速獲取標準門檻值"""
    return get_elevation_config().get_threshold_for_use_case(use_case, environment)

if __name__ == "__main__":
    # 示例使用和測試
    print("🎯 統一仰角門檻配置系統")
    print()
    
    # 創建配置管理器
    config_manager = ElevationConfigManager()
    
    # 顯示不同使用場景的門檻
    use_cases = ["visibility", "handover", "research", "production", "optimal"]
    environments = ["open_area", "urban", "mountain"]
    
    print("📊 不同場景的仰角門檻:")
    for use_case in use_cases:
        print(f"\n{use_case.upper()}:")
        for env in environments:
            threshold = config_manager.get_threshold_for_use_case(use_case, env)
            print(f"  {env}: {threshold:.1f}°")
    
    # 顯示分層門檻
    print("\n🔄 分層換手門檻 (開闊地區):")
    layered = config_manager.get_layered_thresholds("open_area")
    for name, value in layered.items():
        if name != "environment":
            print(f"  {name}: {value:.1f}°")
    
    # 生成遷移計劃
    print("\n📋 系統遷移計劃:")
    migration = config_manager.generate_migration_plan()
    for i, step in enumerate(migration["migration_steps"], 1):
        print(f"  {step}")
    
    # 驗證一致性
    print("\n✅ 系統一致性驗證:")
    validation = config_manager.validate_system_consistency()
    for check, result in validation["checks"].items():
        status = "✅" if result else "❌"
        print(f"  {status} {check}: {result}")
    
    if validation["recommendations"]:
        print("\n⚠️  建議:")
        for rec in validation["recommendations"]:
            print(f"  - {rec}")