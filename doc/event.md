# 3GPP 測量事件與 LEO 衛星換手開發參考文件

> **基於**: 3GPP TS 38.331 version 18.5.1 Release 18 (2025-04)  
> **用途**: LEO 衛星換手決策系統開發參考  
> **更新**: 2025-01-27

## 📋 概述

本文件整理了 3GPP 標準中與 LEO 衛星換手相關的六個核心測量事件，提供完整的技術定義、應用場景和實現指導。

## 🚀 核心測量事件

### 1️⃣ Event A3 - 鄰居小區變得比 SpCell 好

#### **標準定義**
```
觸發條件 (A3-1): Mn + Ofn + Ocn – Hys > Mp + Ofp + Ocp + Off
離開條件 (A3-2): Mn + Ofn + Ocn + Hys < Mp + Ofp + Ocp + Off
```

#### **變數說明**
- `Mn`: 鄰居小區測量結果 (RSRP: dBm, RSRQ/RS-SINR: dB)
- `Mp`: SpCell 測量結果 (RSRP: dBm, RSRQ/RS-SINR: dB)
- `Ofn/Ofp`: 測量對象特定偏移量 (dB)
- `Ocn/Ocp`: 小區特定偏移量 (dB)
- `Hys`: 滯後參數 (dB)
- `Off`: 事件偏移參數 (dB)

#### **🛰️ LEO 衛星應用場景**
- **衛星間換手**: 當鄰居衛星信號品質明顯優於當前服務衛星
- **軌道切換**: 衛星軌道平面間的最佳換手時機選擇
- **動態偏移調整**: 根據衛星運動速度調整 `Off` 參數
- **多波束管理**: 同一衛星不同波束間的切換決策

#### **🔧 實現考慮**
```python
class A3EventProcessor:
    def evaluate_a3_condition(self, neighbor_rsrp, serving_rsrp, 
                             offsets, hysteresis, a3_offset):
        entering = (neighbor_rsrp + offsets['neighbor'] - hysteresis > 
                   serving_rsrp + offsets['serving'] + a3_offset)
        leaving = (neighbor_rsrp + offsets['neighbor'] + hysteresis < 
                  serving_rsrp + offsets['serving'] + a3_offset)
        return {'entering': entering, 'leaving': leaving}
```

---

### 2️⃣ Event A4 - 鄰居小區變得比閾值好

#### **標準定義**
```
觸發條件 (A4-1): Mn + Ofn + Ocn – Hys > Thresh
離開條件 (A4-2): Mn + Ofn + Ocn + Hys < Thresh
```

#### **🛰️ LEO 衛星應用場景**
- **候選衛星篩選**: 設定最低信號品質門檻篩選可用衛星
- **服務品質保證**: 確保換手目標滿足最低 QoS 要求
- **負載平衡觸發**: 結合負載狀況設定動態閾值
- **緊急換手**: 快速識別可用的備用衛星

#### **🔧 動態閾值設計**
```python
def calculate_dynamic_a4_threshold(satellite_type, user_service_class, 
                                 current_load):
    base_threshold = {
        'GEO': -100,      # dBm for RSRP
        'MEO': -105,
        'LEO': -110
    }
    
    # 根據服務等級調整
    service_adjustment = {
        'emergency': 5,    # 降低要求
        'premium': -10,    # 提高要求
        'standard': 0
    }
    
    # 根據負載動態調整
    load_adjustment = current_load * -0.1  # 負載越高要求越低
    
    return (base_threshold[satellite_type] + 
            service_adjustment[user_service_class] + 
            load_adjustment)
```

---

### 3️⃣ Event A5 - SpCell 變差且鄰居小區變好

#### **標準定義**
```
觸發條件1 (A5-1): Mp + Hys < Thresh1 (服務小區變差)
觸發條件2 (A5-2): Mn + Ofn + Ocn – Hys > Thresh2 (鄰居小區變好)
```

#### **🛰️ LEO 衛星應用場景**
- **預測性換手**: 服務衛星信號劣化前的主動換手
- **軌道邊界處理**: 衛星離開最佳服務角度時的切換
- **遮蔽恢復**: 地形或建築物遮蔽恢復時的快速切換
- **雙重驗證換手**: 同時驗證必要性和可行性

#### **🔧 LEO 特定實現**
```python
class A5EventProcessor:
    def __init__(self):
        self.elevation_threshold = 10  # 最低仰角度數
        self.snr_threshold = 5         # 最低 SNR 要求
        
    def evaluate_leo_a5(self, serving_satellite, candidate_satellites, 
                       ue_position):
        # 檢查服務衛星是否劣化 (結合仰角)
        serving_elevation = calculate_elevation(serving_satellite, ue_position)
        serving_degraded = (serving_satellite.rsrp < self.thresh1 or 
                          serving_elevation < self.elevation_threshold)
        
        # 檢查候選衛星是否滿足條件
        for candidate in candidate_satellites:
            if (candidate.rsrp > self.thresh2 and 
                calculate_elevation(candidate, ue_position) > serving_elevation + 5):
                return {'trigger': True, 'target': candidate}
        
        return {'trigger': False}
```

---

### 4️⃣ Event D1 - 雙重距離閾值事件

#### **標準定義**
```
觸發條件1 (D1-1): Ml1 – Hys > Thresh1 (距離參考位置1超過閾值)
觸發條件2 (D1-2): Ml2 + Hys < Thresh2 (距離參考位置2低於閾值)
```

#### **🛰️ LEO 衛星應用場景**
- **波束邊界管理**: 離開當前波束覆蓋範圍的距離觸發
- **服務區域優化**: 進入更優服務區域的距離觸發
- **地理負載均衡**: 基於地理位置的負載分配
- **覆蓋空隙填補**: 多衛星協同覆蓋區域的無縫切換

#### **🔧 波束邊界實現**
```python
class D1EventProcessor:
    def calculate_beam_boundary_event(self, ue_position, 
                                    current_beam_center, 
                                    target_beam_center):
        # 距離當前波束中心的距離
        distance_from_current = haversine_distance(ue_position, 
                                                  current_beam_center)
        
        # 距離目標波束中心的距離
        distance_to_target = haversine_distance(ue_position, 
                                               target_beam_center)
        
        # D1 事件評估
        leaving_current = distance_from_current > self.current_beam_radius
        approaching_target = distance_to_target < self.target_beam_radius
        
        return {
            'trigger': leaving_current and approaching_target,
            'distances': {
                'current': distance_from_current,
                'target': distance_to_target
            }
        }
```

---

### 5️⃣ Event D2 - 移動參考位置距離事件 🌟

#### **標準定義**
```
觸發條件1 (D2-1): Ml1 – Hys > Thresh1 (距離服務小區移動參考位置)
觸發條件2 (D2-2): Ml2 + Hys < Thresh2 (距離移動參考位置)
```

#### **🌟 LEO 衛星專用特性**
- **衛星星曆整合**: 基於 `satellite ephemeris` 和 `SIB19` 的精確軌道計算
- **動態參考位置**: 移動參考位置隨衛星軌道實時更新
- **epoch time**: 基於精確時間戳的軌道預測

#### **🛰️ LEO 衛星應用場景**
- **軌道預測換手**: 基於衛星軌道預測的主動換手決策
- **星座管理**: 多衛星星座間的智能路由選擇
- **時間窗口優化**: 利用衛星可見性時間窗口的最佳化
- **動態覆蓋管理**: 衛星運動導致的覆蓋區域動態調整

#### **🔧 衛星星曆整合實現**
```python
class D2EventProcessor:
    def __init__(self, tle_service):
        self.tle_service = tle_service
        
    def calculate_moving_reference_event(self, ue_position, serving_sat_id, 
                                       candidate_sat_id, epoch_time):
        # 獲取服務衛星的移動參考位置
        serving_sat_position = self.tle_service.get_satellite_position(
            serving_sat_id, epoch_time)
        
        # 獲取候選衛星的移動參考位置
        candidate_sat_position = self.tle_service.get_satellite_position(
            candidate_sat_id, epoch_time)
        
        # 計算距離 (3D 空間距離)
        distance_to_serving = calculate_3d_distance(
            ue_position, serving_sat_position)
        distance_to_candidate = calculate_3d_distance(
            ue_position, candidate_sat_position)
        
        # D2 事件評估
        leaving_serving = (distance_to_serving - self.hysteresis > 
                          self.serving_threshold)
        approaching_candidate = (distance_to_candidate + self.hysteresis < 
                               self.candidate_threshold)
        
        return {
            'trigger': leaving_serving and approaching_candidate,
            'satellite_positions': {
                'serving': serving_sat_position,
                'candidate': candidate_sat_position
            },
            'distances': {
                'serving': distance_to_serving,
                'candidate': distance_to_candidate
            }
        }
```

---

### 6️⃣ CondEvent T1 - 時間窗口條件事件

#### **標準定義**
```
觸發條件 (T1-1): Mt > Thresh1
離開條件 (T1-2): Mt > Thresh1 + Duration
```

#### **🛰️ LEO 衛星應用場景**
- **預配置換手**: 基於衛星軌道可預測性的時間窗口換手
- **服務連續性**: 確保換手在最佳時間窗口內完成
- **避免頻繁切換**: 通過時間滯後避免乒乓效應
- **軌道同步換手**: 多衛星協調的同步換手時機

#### **🔧 軌道預測時間窗口**
```python
class T1EventProcessor:
    def calculate_optimal_handover_window(self, serving_satellite, 
                                        candidate_satellites, 
                                        ue_position):
        current_time = time.time()
        
        # 計算服務衛星的最佳服務結束時間
        serving_end_time = self.calculate_satellite_service_end(
            serving_satellite, ue_position)
        
        # 計算候選衛星的最佳服務開始時間
        candidate_start_times = []
        for candidate in candidate_satellites:
            start_time = self.calculate_satellite_service_start(
                candidate, ue_position)
            candidate_start_times.append({
                'satellite': candidate,
                'start_time': start_time
            })
        
        # T1 事件時間窗口
        time_until_handover = serving_end_time - current_time
        handover_duration = 5000  # 5 seconds in ms
        
        return {
            'trigger': time_until_handover > self.t1_threshold,
            'handover_window': {
                'start': serving_end_time,
                'duration': handover_duration,
                'candidates': candidate_start_times
            }
        }
```

## 🔄 事件整合策略

### **多事件聯合觸發**
```python
class LEOHandoverDecisionEngine:
    def __init__(self):
        self.event_processors = {
            'A3': A3EventProcessor(),
            'A4': A4EventProcessor(),
            'A5': A5EventProcessor(),
            'D1': D1EventProcessor(),
            'D2': D2EventProcessor(),
            'T1': T1EventProcessor()
        }
        
    def evaluate_handover_decision(self, context):
        results = {}
        for event_type, processor in self.event_processors.items():
            results[event_type] = processor.evaluate(context)
        
        # 聯合決策邏輯
        return self.make_joint_decision(results, context)
    
    def make_joint_decision(self, event_results, context):
        # 優先級: 服務品質 > 預測性 > 負載均衡
        
        # 緊急換手 (A5 + D1)
        if (event_results['A5']['trigger'] and 
            event_results['D1']['trigger']):
            return {'decision': 'immediate_handover', 
                   'reason': 'emergency_quality_degradation'}
        
        # 預測性換手 (D2 + T1)
        if (event_results['D2']['trigger'] and 
            event_results['T1']['trigger']):
            return {'decision': 'predictive_handover', 
                   'reason': 'orbital_prediction'}
        
        # 機會性換手 (A3 + A4)
        if (event_results['A3']['trigger'] and 
            event_results['A4']['trigger']):
            return {'decision': 'opportunistic_handover', 
                   'reason': 'better_alternative'}
        
        return {'decision': 'maintain_connection', 
               'reason': 'no_trigger_conditions'}
```

## 📊 性能參數建議

### **LEO 衛星特定參數**
```python
LEO_SATELLITE_PARAMETERS = {
    'A3': {
        'hysteresis': 3.0,      # dB
        'a3_offset': 2.0,       # dB
        'time_to_trigger': 160  # ms
    },
    'A4': {
        'threshold': -110,      # dBm for RSRP
        'hysteresis': 2.0,      # dB
        'time_to_trigger': 160  # ms
    },
    'A5': {
        'threshold1': -108,     # dBm (serving degradation)
        'threshold2': -106,     # dBm (neighbor improvement)
        'hysteresis': 2.0,      # dB
        'time_to_trigger': 160  # ms
    },
    'D1': {
        'distance_threshold1': 50000,  # meters (beam radius)
        'distance_threshold2': 30000,  # meters (target approach)
        'hysteresis_location': 1000,   # meters
        'time_to_trigger': 320         # ms
    },
    'D2': {
        'distance_threshold1': 800000,  # meters (satellite distance)
        'distance_threshold2': 600000,  # meters (closer satellite)
        'hysteresis_location': 10000,   # meters
        'time_to_trigger': 640          # ms
    },
    'T1': {
        't1_threshold': 10000,  # ms (10 seconds before optimal handover)
        'duration': 5000,       # ms (5 seconds handover window)
        'time_to_trigger': 0    # immediate
    }
}
```

## 🛠️ 實現檢查清單

### **開發階段**
- [ ] **A3 事件處理器**: 實現基於 RSRP/RSRQ 的比較邏輯
- [ ] **A4 事件處理器**: 實現動態閾值和候選篩選
- [ ] **A5 事件處理器**: 實現雙重條件驗證機制
- [ ] **D1 事件處理器**: 實現波束邊界距離計算
- [ ] **D2 事件處理器**: 實現衛星星曆整合和動態位置計算
- [ ] **T1 事件處理器**: 實現軌道預測和時間窗口管理
- [ ] **聯合決策引擎**: 實現多事件優先級和聯合觸發邏輯

### **測試驗證**
- [ ] **單元測試**: 每個事件處理器的獨立功能測試
- [ ] **整合測試**: 多事件聯合觸發場景測試
- [ ] **性能測試**: 實時處理延遲和準確性驗證
- [ ] **真實場景測試**: 基於真實 TLE 數據的端到端測試

### **生產部署**
- [ ] **參數調優**: 基於實際衛星星座的參數最佳化
- [ ] **監控整合**: 事件觸發統計和性能監控
- [ ] **故障處理**: 異常事件和錯誤恢復機制
- [ ] **文檔更新**: API 文檔和操作手冊

---

**📝 註**: 本文件基於 3GPP TS 38.331 v18.5.1 Release 18，專門針對 LEO 衛星換手場景進行技術分析和實現指導。
