# LEO 衛星換手管理演算法說明文檔

## 概述

本文檔詳細說明 LEO 衛星換手管理系統中的演算法實現，包括如何解讀側邊欄中"換手管理">"LEO 衛星換手管理系統"所呈現的各種資料及計算結果。系統基於 IEEE INFOCOM 2024 論文實現 Fine-Grained Synchronized Algorithm（細粒度同步演算法）。

## 核心演算法架構

### 1. Fine-Grained Synchronized Algorithm（細粒度同步演算法）

**論文來源**: IEEE INFOCOM 2024  
**實現位置**: 
- `/simworld/backend/app/domains/handover/services/fine_grained_sync_service.py`
- `/netstack/netstack_api/services/fine_grained_sync_service.py`

#### 1.1 演算法核心理念

細粒度同步演算法的核心創新在於無需 access network 與 core network 間的控制信令交互即可維持嚴格同步。演算法採用二點預測方法來預測 UE 接入衛星變化。

#### 1.2 二點預測方法 (Two-Point Prediction Method)

**演算法流程**:
```
1. 在時間點 T 預測最佳接入衛星 AT
2. 在時間點 T+Δt 預測最佳接入衛星 AT+Δt  
3. 判斷換手必要性: AT ≠ AT+Δt
4. 使用 Binary Search Refinement 精確計算換手時間 Tp
```

**資料結構對應**:
```python
class TwoPointPredictionResult:
    current_satellite: str      # AT (當前最佳衛星)
    predicted_satellite: str    # AT+Δt (預測最佳衛星)
    current_time: float         # 時間點 T
    future_time: float          # 時間點 T+Δt
    handover_needed: bool       # 是否需要換手 (AT ≠ AT+Δt)
    confidence: float           # 預測置信度
```

**前端呈現解讀**:
- **當前接入衛星**: 對應 `current_satellite` (AT)
- **預測接入衛星**: 對應 `predicted_satellite` (AT+Δt)
- **換手建議**: 對應 `handover_needed` 布林值
- **預測置信度**: 對應 `confidence` 數值 (0-1)

### 2. Binary Search Refinement（二進制搜索精化）

#### 2.1 演算法目標

將預測誤差迭代減半至低於 RAN 層換手程序時間，實現 10ms 精度的換手時間預測。

#### 2.2 實現邏輯

```python
async def binary_search_refinement(
    self, ue_id: str, ue_position: Tuple[float, float, float],
    t_start: float, t_end: float
) -> Tuple[float, List[BinarySearchIteration]]:
    """
    使用 Binary Search Refinement 精確計算換手觸發時間 Tp
    """
    while (t_end - t_start) > precision_threshold:
        t_mid = (t_start + t_end) / 2
        mid_satellite = await self.calculate_best_satellite(ue_position, t_mid)
        
        if mid_satellite.satellite_id != start_satellite_id:
            t_end = t_mid    # 換手點在前半段
        else:
            t_start = t_mid  # 換手點在後半段
```

**資料結構對應**:
```python
class BinarySearchIteration:
    iteration: int              # 迭代次數
    start_time: float          # 搜索區間開始時間
    end_time: float            # 搜索區間結束時間
    mid_time: float            # 中點時間
    precision: float           # 當前精度 (秒)
    completed: bool            # 是否完成收斂
```

**前端呈現解讀**:
- **迭代次數**: 顯示 Binary Search 執行的迭代回合數
- **精度收斂**: 顯示當前搜索精度，目標 < 0.1 秒
- **換手時間 Tp**: 最終計算出的精確換手觸發時間

### 3. 衛星選擇演算法

#### 3.1 約束式衛星接入 (Constrained Satellite Access)

**實現位置**: `/simworld/backend/app/domains/handover/services/constrained_satellite_access_service.py`

#### 3.2 評分機制

**衛星評分計算**:
```python
async def calculate_satellite_score(self, satellite, ue_position, timestamp):
    elevation_score = min(satellite.elevation_deg / 90.0, 1.0) * 40     # 仰角分數 (40%)
    distance_score = max(0, (2000 - satellite.distance_km) / 2000) * 30  # 距離分數 (30%)
    signal_score = max(0, (signal_strength + 60) / 40) * 20             # 信號分數 (20%)
    load_score = load_factor * 10                                       # 負載分數 (10%)
    
    return elevation_score + distance_score + signal_score + load_score
```

**前端呈現解讀**:
- **衛星評分**: 總分 0-100，數值越高表示衛星越適合作為接入目標
- **仰角**: 衛星相對於 UE 的仰角，越高信號品質越好
- **距離**: UE 與衛星的距離，越近延遲越低
- **信號強度**: 估算的接收信號強度 (dBm)
- **負載因子**: 衛星當前負載程度，影響服務品質

### 4. 信號品質估算

#### 4.1 自由空間路徑損耗模型

```python
def estimate_signal_strength(self, satellite, ue_position):
    frequency_ghz = 20.0        # 20 GHz 頻率
    tx_power_dbm = 40.0         # 40 dBm 發射功率
    
    # 自由空間路徑損耗計算
    distance_km = satellite.distance_km
    fspl_db = 32.45 + 20 * log10(distance_km) + 20 * log10(frequency_ghz)
    
    # 接收信號強度
    rx_power_dbm = tx_power_dbm - fspl_db
    
    return rx_power_dbm
```

**前端呈現解讀**:
- **信號強度 (dBm)**: 負值，絕對值越小信號越強
  - \> -70 dBm: 極佳信號
  - -70 ~ -85 dBm: 良好信號  
  - -85 ~ -100 dBm: 可用信號
  - < -100 dBm: 弱信號

### 5. 換手決策演算法

#### 5.1 觸發條件分析

**實現位置**: `/simworld/backend/app/domains/handover/services/handover_decision_service.py`

```python
class HandoverTrigger:
    SIGNAL_DEGRADATION = "signal_degradation"  # 信號品質下降
    BETTER_SATELLITE = "better_satellite"      # 發現更佳衛星
    PREDICTED_OUTAGE = "predicted_outage"      # 預測服務中斷
    LOAD_BALANCING = "load_balancing"          # 負載平衡
    EMERGENCY_HANDOVER = "emergency_handover"  # 緊急換手
```

#### 5.2 換手成本計算

```python
async def estimate_handover_cost(self, source_sat_id, target_sat_id, triggers):
    latency_cost = 15.0 + (satellite_distance_factor * 15.0)      # 延遲成本 (10-30)
    signaling_cost = 10.0 + (satellite_distance_factor * 10.0)    # 信令成本 (8-20)
    resource_cost = 8.0 + (satellite_distance_factor * 7.0)       # 資源成本 (5-15)
    disruption_cost = 20.0 + (satellite_distance_factor * 15.0)   # 中斷成本 (15-35)
    
    total_cost = (latency_cost * 0.4 + signaling_cost * 0.2 + 
                 resource_cost * 0.2 + disruption_cost * 0.2)
```

**前端呈現解讀**:
- **換手成本**: 總成本 0-100，數值越低表示換手影響越小
- **延遲成本**: 換手過程中的延遲增加
- **信令成本**: 控制信令的資源消耗
- **資源成本**: 系統資源重配置成本
- **中斷成本**: 服務中斷時間成本

### 6. 預測準確率優化

#### 6.1 自適應參數調整

```python
class PredictionAccuracyOptimizer:
    def get_recommended_delta_t(self):
        """基於歷史準確率動態調整 Δt"""
        if self.current_accuracy > 0.9:
            return max(5, self.base_delta_t - 2)   # 高準確率時縮短間隔
        elif self.current_accuracy < 0.7:
            return min(30, self.base_delta_t + 5)  # 低準確率時延長間隔
        return self.base_delta_t
```

**前端呈現解讀**:
- **預測準確率**: 歷史預測與實際結果的吻合度
- **Delta-T 優化**: 系統自動調整的預測時間間隔
- **準確率趨勢**: 顯示準確率的變化趨勢

## 前端資料解讀指南

### 1. 換手管理儀表板資料對應

#### 1.1 即時狀態區域
- **當前接入衛星**: 來自 `UESatelliteMapping.current_satellite_id`
- **連接品質**: 來自 `UESatelliteMapping.signal_quality` (dBm)
- **仰角/方位角**: 來自 `elevation_angle` / `azimuth_angle`
- **距離**: 來自 `distance_km`

#### 1.2 預測資訊區域
- **預測換手時間**: 來自 `HandoverPrediction.predicted_handover_time`
- **目標衛星**: 來自 `HandoverPrediction.target_satellite_id`
- **換手原因**: 來自 `HandoverPrediction.handover_reason`
- **置信度**: 來自 `HandoverPrediction.confidence_score`

#### 1.3 演算法指標區域
- **Binary Search 迭代**: 來自 `BinarySearchIteration.iteration`
- **收斂精度**: 來自 `BinarySearchIteration.precision`
- **同步狀態**: 來自 `SynchronizationPoint.sync_state`
- **預測誤差**: 來自 `error_bound_ms`

### 2. 性能指標解讀

#### 2.1 演算法性能
- **平均預測精度**: 目標 < 50ms，優異 < 10ms
- **收斂率**: Binary Search 成功收斂的比例，目標 > 90%
- **同步精度**: access/core network 同步精度，目標 < 10ms

#### 2.2 系統指標
- **換手成功率**: 執行換手的成功比例
- **服務中斷時間**: 換手過程中的服務中斷時長
- **吞吐量變化**: 換手前後的數據吞吐量比較

### 3. 天氣整合預測

#### 3.1 天氣因子影響
```python
class WeatherIntegratedPredictionService:
    async def predict_with_weather_integration(self, ue_id, ue_position, satellite_candidates):
        """整合天氣因子的衛星選擇預測"""
        # 考慮降雨衰減、大氣折射等天氣因素
```

**前端呈現解讀**:
- **天氣影響係數**: 0-1，數值越高表示天氣對信號影響越大
- **降雨衰減**: Ka/Ku 頻段受降雨影響的信號衰減程度
- **大氣條件**: 大氣折射對信號傳播路徑的影響

## 演算法調優建議

### 1. 參數調整指導

#### 1.1 Binary Search 參數
- `precision_threshold`: 調整收斂精度，預設 0.1 秒
- `max_iterations`: 調整最大迭代次數，預設 15 次
- `delta_t`: 調整預測時間間隔，預設 10 秒

#### 1.2 信號品質門檻
- `signal_threshold_dbm`: 調整信號品質門檻，預設 -85 dBm
- `elevation_threshold_deg`: 調整最低仰角門檻，預設 10 度

### 2. 性能優化策略

#### 2.1 精度 vs 效率平衡
- 高精度需求: 降低 `precision_threshold` 至 0.05 秒
- 高效率需求: 提高 `precision_threshold` 至 0.2 秒

#### 2.2 網路負載最佳化
- 繁忙時段: 提高換手成本權重，減少不必要換手
- 閒置時段: 降低換手成本權重，優化連接品質

## 故障診斷

### 1. 常見問題及解決方案

#### 1.1 Binary Search 不收斂
**症狀**: `convergence_achieved = false`
**可能原因**: 
- 衛星軌道數據不準確
- UE 位置變化過快
- 干擾環境影響信號估算

**解決方案**:
- 更新 TLE 軌道數據
- 調整 `max_iterations` 參數
- 檢查信號估算模型參數

#### 1.2 預測準確率低
**症狀**: `prediction_accuracy < 0.7`
**可能原因**:
- `delta_t` 設定不當
- 環境因子變化劇烈
- 演算法參數需要校準

**解決方案**:
- 啟用自適應 `delta_t` 調整
- 整合更多環境感知因子
- 使用機器學習優化參數

#### 1.3 換手延遲過高
**症狀**: 實際換手時間與預測時間差異 > 100ms
**可能原因**:
- 系統處理延遲
- 網路信令延遲
- 演算法計算複雜度過高

**解決方案**:
- 優化演算法執行效率
- 實現預測結果快取
- 並行處理多個 UE 預測

這份文檔提供了完整的演算法理解框架，幫助開發者和操作者正確解讀系統中的各種資料和計算結果，並基於論文演算法進行系統調優和故障診斷。