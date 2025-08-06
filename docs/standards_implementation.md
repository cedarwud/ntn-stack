# 📐 LEO 衛星切換標準與實現指南

**版本**: 1.0.0  
**建立日期**: 2025-08-06  
**適用於**: LEO 衛星切換研究系統 - 標準合規與實現

## 📋 概述

本指南整合了 LEO 衛星切換系統的**所有技術標準規範與實現細節**，確保系統完全符合國際標準並提供學術研究所需的規範基礎。

## 🎯 技術參考標準

### 國際通訊標準
- **3GPP TS 38.331**: NTN 無線資源控制 - 信令程序和狀態管理
- **3GPP TR 38.811**: NTN 研究報告 - 技術需求和架構指導
- **ITU-R P.618-14**: 衛星鏈路大氣衰減模型 - 傳播損耗計算
- **47 CFR § 25.205**: 美國 FCC 最低天線仰角規範 - 法規合規

### 學術研究標準
- **IEEE 802.11**: 無線網路標準 - 換手程序參考
- **ETSI TS 103 154**: 衛星地面綜合網路 - 系統架構
- **ISO/IEC 23270**: 網路安全標準 - 衛星通訊安全

## 🛰️ 3GPP NTN 標準實現

### Event A4/A5 觸發條件實現

#### 3GPP TS 38.331 標準定義
```python
# Event A4: 鄰近小區變得優於門檻
def event_a4_trigger_condition(measurement_results):
    """
    進入條件: Mn + Ofn + Ocn – Hys > Thresh
    離開條件: Mn + Ofn + Ocn + Hys < Thresh
    """
    Mn = measurement_results.neighbor_cell_rsrp        # 鄰近小區 RSRP (dBm)
    Ofn = measurement_results.frequency_offset          # 頻率特定偏移 (dB)
    Ocn = measurement_results.cell_specific_offset      # 小區特定偏移 (dB)
    Hys = measurement_results.hysteresis               # 遲滯參數 (dB)
    Thresh = measurement_results.a4_threshold           # A4 門檻 (dBm)
    
    enter_condition = (Mn + Ofn + Ocn - Hys) > Thresh
    leave_condition = (Mn + Ofn + Ocn + Hys) < Thresh
    
    return enter_condition, leave_condition

# Event A5: 服務小區低於門檻1且鄰近小區高於門檻2
def event_a5_trigger_condition(measurement_results):
    """
    進入條件: Mp + Hys < Thresh1 且 Mn + Ofn + Ocn – Hys > Thresh2
    離開條件: Mp – Hys > Thresh1 或 Mn + Ofn + Ocn + Hys < Thresh2
    """
    Mp = measurement_results.serving_cell_rsrp         # 服務小區 RSRP (dBm)
    Mn = measurement_results.neighbor_cell_rsrp        # 鄰近小區 RSRP (dBm)
    Hys = measurement_results.hysteresis               # 遲滯參數 (dB)
    Thresh1 = measurement_results.a5_threshold_1       # A5 門檻1 (dBm)
    Thresh2 = measurement_results.a5_threshold_2       # A5 門檻2 (dBm)
    
    enter_condition = ((Mp + Hys) < Thresh1) and ((Mn + Ofn + Ocn - Hys) > Thresh2)
    leave_condition = ((Mp - Hys) > Thresh1) or ((Mn + Ofn + Ocn + Hys) < Thresh2)
    
    return enter_condition, leave_condition
```

### 測量參數標準定義
```python
measurement_parameters = {
    # RSRP 測量 (Reference Signal Received Power)
    "rsrp_range": (-156, -31),              # dBm, 3GPP 規範範圍
    "rsrp_resolution": 1,                   # dB, 測量解析度
    "rsrp_accuracy": "±6 dB",               # 測量準確度
    
    # RSRQ 測量 (Reference Signal Received Quality)  
    "rsrq_range": (-43, 20),                # dB, 3GPP 規範範圍
    "rsrq_resolution": 0.5,                 # dB, 測量解析度
    "rsrq_accuracy": "±3 dB",               # 測量準確度
    
    # RS-SINR 測量 (Reference Signal Signal-to-Interference-plus-Noise Ratio)
    "rs_sinr_range": (-23, 40),             # dB, 3GPP 規範範圍
    "rs_sinr_resolution": 0.5,              # dB, 測量解析度
    "rs_sinr_accuracy": "±3 dB"             # 測量準確度
}
```

### SIB19 衛星位置廣播實現
```python
sib19_information_elements = {
    "satellite_position_and_velocity": {
        "position_x": "int32",              # km, ECEF 座標
        "position_y": "int32",              # km, ECEF 座標  
        "position_z": "int32",              # km, ECEF 座標
        "velocity_x": "int16",              # km/s, ECEF 速度
        "velocity_y": "int16",              # km/s, ECEF 速度
        "velocity_z": "int16"               # km/s, ECEF 速度
    },
    "ephemeris_data": {
        "reference_time": "uint64",         # GPS 時間
        "satellite_id": "uint16",           # 衛星標識符
        "orbital_elements": {
            "semi_major_axis": "uint32",     # km
            "eccentricity": "uint32",        # 無單位
            "inclination": "uint32",         # 度
            "longitude_ascending_node": "uint32",  # 度
            "argument_of_perigee": "uint32", # 度
            "mean_anomaly": "uint32"         # 度
        }
    },
    "candidate_beam_list": {
        "max_candidates": 8,                # 3GPP NTN 標準限制
        "beam_info": [
            {
                "beam_id": "uint8",          # 波束標識符
                "coverage_area": "polygon",   # 覆蓋區域
                "eirp_max": "uint8",         # dBm, 最大 EIRP
                "elevation_min": "uint8"     # 度, 最小仰角
            }
        ]
    }
}
```

## 📐 分層仰角門檻標準

### 標準分層架構
```python
elevation_threshold_standards = {
    "ideal_service": {
        "elevation_deg": 15.0,
        "success_rate": "≥ 99.9%",
        "use_case": "最佳服務品質",
        "standard_compliance": "超越 3GPP NTN 標準"
    },
    "standard_service": {
        "elevation_deg": 10.0, 
        "success_rate": "≥ 99.5%",
        "use_case": "正常換手操作",
        "standard_compliance": "完全符合 3GPP NTN"
    },
    "minimum_service": {
        "elevation_deg": 5.0,
        "success_rate": "≥ 98.0%", 
        "use_case": "邊緣區域覆蓋保障",
        "standard_compliance": "符合 FCC Part 25"
    },
    "emergency_only": {
        "elevation_deg": 3.0,
        "success_rate": "≥ 95.0%",
        "use_case": "特殊情況下保留通訊",
        "standard_compliance": "需特殊授權"
    }
}
```

### ITU-R P.618 大氣衰減模型實現
```python
def calculate_atmospheric_attenuation(elevation_deg, frequency_ghz, rain_rate_mm_h=0):
    """
    基於 ITU-R P.618-14 標準的大氣衰減計算
    
    Args:
        elevation_deg: 衛星仰角 (度)
        frequency_ghz: 載波頻率 (GHz)  
        rain_rate_mm_h: 降雨強度 (mm/h)
    
    Returns:
        total_attenuation_db: 總大氣衰減 (dB)
    """
    # 氣體吸收衰減 (ITU-R P.676)
    oxygen_attenuation = calculate_oxygen_attenuation(frequency_ghz, elevation_deg)
    water_vapor_attenuation = calculate_water_vapor_attenuation(frequency_ghz, elevation_deg)
    
    # 雨衰減 (ITU-R P.838)  
    rain_attenuation = 0
    if rain_rate_mm_h > 0:
        rain_specific_attenuation = calculate_rain_specific_attenuation(frequency_ghz, rain_rate_mm_h)
        path_length = calculate_effective_path_length(elevation_deg, rain_rate_mm_h)
        rain_attenuation = rain_specific_attenuation * path_length
    
    # 雲霧衰減 (ITU-R P.840)
    cloud_attenuation = calculate_cloud_attenuation(frequency_ghz, elevation_deg)
    
    # 閃爍衰減 (ITU-R P.618)
    scintillation_attenuation = calculate_scintillation_attenuation(frequency_ghz, elevation_deg)
    
    total_attenuation = (
        oxygen_attenuation + 
        water_vapor_attenuation + 
        rain_attenuation + 
        cloud_attenuation + 
        scintillation_attenuation
    )
    
    return total_attenuation
```

### 環境調整係數標準
```python
environmental_adjustment_factors = {
    "open_areas": {
        "factor": 0.9,
        "actual_threshold_example": "9.0° (for 10° standard)",
        "environments": ["海洋", "平原", "沙漠", "極地"],
        "rationale": "無地形遮蔽，信號傳播理想"
    },
    "standard_terrain": {
        "factor": 1.0, 
        "actual_threshold_example": "10.0° (baseline)",
        "environments": ["一般陸地", "丘陵", "郊區"],
        "rationale": "標準地形，符合模型假設"
    },
    "urban_environment": {
        "factor": 1.2,
        "actual_threshold_example": "12.0° (for 10° standard)", 
        "environments": ["市區", "建築密集區", "工業區"],
        "rationale": "建築物遮蔽和多路徑效應"
    },
    "complex_terrain": {
        "factor": 1.5,
        "actual_threshold_example": "15.0° (for 10° standard)",
        "environments": ["山區", "峽谷", "高樓林立"],
        "rationale": "嚴重地形遮蔽和信號反射"
    },
    "severe_weather": {
        "factor": 1.8,
        "actual_threshold_example": "18.0° (for 10° standard)",
        "environments": ["暴雨區", "雪災", "沙塵暴"],
        "rationale": "極端天氣造成額外衰減"
    }
}
```

## 🔄 分層換手策略實現

### 階段化換手決策邏輯
```python
class LayeredHandoverDecision:
    def __init__(self, config):
        self.thresholds = config.elevation_thresholds
        self.environmental_factor = config.environmental_factor
        
    def evaluate_handover_trigger(self, satellite_elevation, signal_quality):
        """分層換手觸發評估"""
        
        # 應用環境調整
        adjusted_elevation = satellite_elevation / self.environmental_factor
        
        # 階段 1: 預備觸發 (15° → 12°)
        if adjusted_elevation <= self.thresholds.preparation_trigger:
            return HandoverPhase.PREPARATION, self._start_preparation_phase()
            
        # 階段 2: 標準執行 (12° → 8°)  
        elif adjusted_elevation <= self.thresholds.execution_trigger:
            return HandoverPhase.EXECUTION, self._execute_handover()
            
        # 階段 3: 邊緣保障 (8° → 5°)
        elif adjusted_elevation <= self.thresholds.critical_trigger:
            return HandoverPhase.CRITICAL, self._critical_handover()
            
        # 階段 4: 緊急中斷 (< 5°)
        else:
            return HandoverPhase.EMERGENCY, self._emergency_disconnection()
    
    def _start_preparation_phase(self):
        """預備階段：爭取 10-20 秒準備時間"""
        actions = [
            "scan_candidate_satellites",
            "reserve_channel_resources", 
            "preconfig_routing_table",
            "calculate_handover_timing"
        ]
        return HandoverAction(phase="preparation", actions=actions, target_delay="10-20s")
    
    def _execute_handover(self):
        """標準執行：符合 3GPP NTN 標準的穩定切換"""
        actions = [
            "execute_handover_decision",
            "maintain_signal_quality",
            "prevent_call_drop",
            "update_network_topology"
        ]
        return HandoverAction(phase="execution", actions=actions, target_delay="<100ms")
    
    def _critical_handover(self):  
        """邊緣保障：延長邊緣區域服務"""
        actions = [
            "activate_degraded_service_mode",
            "execute_emergency_handover",
            "prepare_forced_disconnection",
            "notify_network_management"
        ]
        return HandoverAction(phase="critical", actions=actions, target_delay="<200ms")
```

## 📊 標準合規驗證

### 自動化合規檢查
```python
def validate_standards_compliance(system_config, measurement_data):
    """標準合規性驗證"""
    
    compliance_report = {
        "3gpp_ntn": validate_3gpp_ntn_compliance(system_config),
        "itu_r_p618": validate_itu_atmospheric_model(measurement_data),
        "fcc_part25": validate_fcc_elevation_requirements(system_config),
        "ieee_802_11": validate_handover_procedures(system_config)
    }
    
    overall_compliance = all(compliance_report.values())
    
    return ComplianceReport(
        overall_status=overall_compliance,
        individual_standards=compliance_report,
        recommendations=generate_compliance_recommendations(compliance_report)
    )

def validate_3gpp_ntn_compliance(config):
    """3GPP NTN 標準合規檢查"""
    checks = {
        "max_candidates": config.max_candidate_satellites <= 8,
        "measurement_accuracy": config.rsrp_accuracy <= 6.0,  # ±6 dB
        "handover_latency": config.handover_latency <= 100,    # ms
        "sib19_broadcast": config.sib19_enabled,
        "event_triggers": all([
            hasattr(config, 'event_a4_threshold'),
            hasattr(config, 'event_a5_threshold_1'),  
            hasattr(config, 'event_a5_threshold_2')
        ])
    }
    
    return all(checks.values()), checks
```

### 效能基準與驗證
```python
performance_standards = {
    "handover_success_rate": {
        "threshold_15deg": {"target": "≥ 99.9%", "measured": None},
        "threshold_10deg": {"target": "≥ 99.5%", "measured": None},
        "threshold_5deg": {"target": "≥ 98.0%", "measured": None}
    },
    "handover_latency": {
        "preparation_phase": {"target": "< 50ms", "measured": None},
        "execution_phase": {"target": "< 100ms", "measured": None},
        "critical_phase": {"target": "< 200ms", "measured": None}
    },
    "signal_quality": {
        "rsrp_accuracy": {"target": "±6 dB", "measured": None},
        "rsrq_accuracy": {"target": "±3 dB", "measured": None},
        "measurement_frequency": {"target": "≤ 200ms", "measured": None}
    }
}
```

## 🌐 API 標準接口規範

### 標準化 API 設計原則
```python
api_design_standards = {
    "rest_compliance": "完全符合 REST API 設計原則",
    "http_methods": {
        "GET": "資源查詢和狀態獲取",
        "POST": "資源創建和操作觸發", 
        "PUT": "資源完整更新",
        "DELETE": "資源刪除"
    },
    "response_format": "統一 JSON 格式響應",
    "error_handling": "標準 HTTP 狀態碼 + 詳細錯誤信息",
    "authentication": "支援 API Key 和 OAuth 2.0",
    "rate_limiting": "防止 API 濫用的速率限制"
}

# 標準 API 響應格式
standard_api_response = {
    "success": bool,                    # 操作成功狀態
    "data": object,                     # 響應數據  
    "message": str,                     # 操作結果描述
    "timestamp": "ISO 8601 format",     # 響應時間戳
    "api_version": str,                 # API 版本號
    "request_id": str                   # 請求唯一標識符
}
```

## 🔧 配置標準化

### 統一配置架構
```python
@dataclass
class StandardsConfiguration:
    """標準化配置類別"""
    
    # 3GPP NTN 標準參數
    max_candidate_satellites: int = 8
    measurement_accuracy_rsrp: float = 6.0      # ±dB
    measurement_accuracy_rsrq: float = 3.0      # ±dB
    handover_latency_target: int = 100          # ms
    
    # ITU-R P.618 大氣模型參數  
    atmospheric_model_enabled: bool = True
    rain_rate_default: float = 10.0             # mm/h
    scintillation_model: str = "ITU-R P.618"
    
    # FCC Part 25 合規參數
    minimum_elevation_deg: float = 5.0
    interference_protection: bool = True
    coordination_required: bool = True
    
    # 環境調整參數
    environmental_factors: Dict[str, float] = field(default_factory=lambda: {
        "open_area": 0.9,
        "standard": 1.0,
        "urban": 1.2, 
        "complex_terrain": 1.5,
        "severe_weather": 1.8
    })
    
    def validate_configuration(self) -> bool:
        """配置驗證"""
        return all([
            self.max_candidate_satellites <= 8,
            self.measurement_accuracy_rsrp <= 6.0,
            self.handover_latency_target <= 100,
            self.minimum_elevation_deg >= 5.0
        ])
```

## ⚠️ 重要合規注意事項

### 強制性要求
1. **3GPP NTN 合規**：最大候選衛星數不得超過 8 顆
2. **ITU-R 大氣模型**：必須使用標準大氣衰減計算
3. **FCC 仰角規範**：最低服務仰角不得低於 5°
4. **測量準確度**：RSRP ±6dB，RSRQ ±3dB 範圍內

### 建議性最佳實踐
1. **標準服務門檻**：建議使用 10° 作為正常換手仰角
2. **環境調整**：根據實際部署環境調整仰角門檻
3. **性能監控**：持續監控切換成功率和延遲指標
4. **合規驗證**：定期執行自動化標準合規檢查

---

**本標準實現指南確保 LEO 衛星切換系統完全符合國際標準，為學術研究和實際部署提供可靠的規範基礎。**