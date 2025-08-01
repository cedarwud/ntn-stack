# Phase 2: D2/A4/A5 換手事件檢測實現

## 目標
基於現有的分層門檻架構，實現 3GPP 38.331 標準的 D2/A4/A5 事件檢測邏輯，為 NTPU 場景提供精確的換手決策支援。

## 3GPP NTN 換手事件詳解

### D2 事件：服務衛星即將不可見
**定義**：當服務衛星的仰角接近臨界門檻，預示即將失去連線。

**觸發條件**：
```python
# 基於現有分層門檻
if serving_satellite.elevation <= critical_threshold + margin:  # 5.0° + 2.0° = 7.0°
    trigger_d2_event()
```

**應用場景**：
- LEO 衛星快速移動導致的週期性不可見
- 建築物或地形遮擋導致的突發性不可見

### A4 事件：鄰近衛星測量值超過門檻
**定義**：當鄰近衛星的信號品質超過預設門檻，成為潛在換手目標。

**觸發條件**：
```python
# 使用執行門檻作為基準
if neighbor_satellite.elevation >= execution_threshold:  # 11.25°
    if neighbor_satellite.rsrp > rsrp_threshold:       # 例如 -110 dBm
        trigger_a4_event()
```

**特徵參數**：
- 仰角 (Elevation)
- 接收信號功率 (RSRP)
- 都卜勒頻移 (Doppler Shift)
- 預期可見時長

### A5 事件：服務變差且鄰近變好
**定義**：複合條件事件，同時滿足服務衛星品質下降和鄰近衛星品質提升。

**觸發條件**：
```python
# 雙重門檻判定
if (serving_satellite.elevation < execution_threshold and      # < 11.25°
    neighbor_satellite.elevation > pre_handover_threshold):    # > 13.5°
    trigger_a5_event()
```

## 基於現有架構的實現方案

### 2.1 擴展現有預處理流程

在 `build_with_phase0_data.py` 中新增事件檢測模組：

```python
class HandoverEventDetector:
    def __init__(self):
        # 使用現有的分層門檻
        self.pre_handover_threshold = 13.5
        self.execution_threshold = 11.25  
        self.critical_threshold = 5.0
        
        # RSRP 門檻 (基於 ITU-R 建議)
        self.rsrp_good_threshold = -110  # dBm
        self.rsrp_poor_threshold = -120  # dBm
    
    def process_visibility_windows(self, satellites_data):
        """處理可見性窗口，生成換手事件"""
        events = {
            'd2_events': [],
            'a4_events': [],
            'a5_events': [],
            'statistics': {}
        }
        
        # 時間軸掃描
        for timestamp in self.timeline:
            visible_sats = self.get_visible_satellites(timestamp)
            serving_sat = self.get_serving_satellite(visible_sats)
            
            # D2 事件檢測
            if serving_sat and serving_sat.elevation <= self.critical_threshold + 2.0:
                events['d2_events'].append({
                    'timestamp': timestamp,
                    'satellite_id': serving_sat.id,
                    'elevation': serving_sat.elevation,
                    'time_to_los': self.calculate_time_to_los(serving_sat),
                    'recommended_target': self.find_best_target(visible_sats)
                })
            
            # A4 事件檢測
            for sat in visible_sats:
                if (sat.id != serving_sat.id and 
                    sat.elevation >= self.execution_threshold and
                    sat.rsrp > self.rsrp_good_threshold):
                    events['a4_events'].append({
                        'timestamp': timestamp,
                        'candidate_id': sat.id,
                        'elevation': sat.elevation,
                        'rsrp': sat.rsrp,
                        'visibility_duration': sat.remaining_visible_time
                    })
            
            # A5 事件檢測
            if serving_sat and serving_sat.elevation < self.execution_threshold:
                for candidate in visible_sats:
                    if (candidate.id != serving_sat.id and
                        candidate.elevation > self.pre_handover_threshold):
                        events['a5_events'].append({
                            'timestamp': timestamp,
                            'serving_id': serving_sat.id,
                            'serving_elevation': serving_sat.elevation,
                            'candidate_id': candidate.id,
                            'candidate_elevation': candidate.elevation,
                            'urgency': 'high' if serving_sat.elevation < 8.0 else 'normal'
                        })
        
        return events
```

### 2.2 事件資料結構設計

```json
// ntpu_handover_events.json
{
  "generated_at": "2025-01-01T00:00:00Z",
  "scene": "ntpu",
  "analysis_period": {
    "start": "2025-01-01T00:00:00Z",
    "duration_minutes": 96
  },
  "events": {
    "d2_events": [
      {
        "timestamp": "2025-01-01T00:15:30Z",
        "satellite_id": "48273",
        "elevation": 7.0,
        "time_to_los": 120,  // 秒
        "recommended_target": "48274",
        "severity": "warning"
      }
    ],
    "a4_events": [
      {
        "timestamp": "2025-01-01T00:10:00Z",
        "candidate_id": "48274",
        "elevation": 12.5,
        "rsrp": -108.5,
        "visibility_duration": 450,
        "quality_score": 0.85
      }
    ],
    "a5_events": [
      {
        "timestamp": "2025-01-01T00:14:00Z",
        "serving_id": "48273",
        "serving_elevation": 10.5,
        "candidate_id": "48274", 
        "candidate_elevation": 15.2,
        "urgency": "normal",
        "handover_gain": 4.7  // dB
      }
    ]
  },
  "statistics": {
    "total_d2_events": 15,
    "total_a4_events": 42,
    "total_a5_events": 18,
    "avg_warning_time": 95.5,  // 秒
    "handover_opportunities": 75,
    "potential_service_gaps": 2
  }
}
```

### 2.3 與現有系統整合

1. **資料流程**：
   ```
   TLE Data → SGP4 計算 → 可見性窗口 → 事件檢測 → 事件儲存
                                ↓
                          3D 視覺化資料
   ```

2. **儲存分離**：
   - 軌道資料：供 SimWorld 3D 渲染使用
   - 事件資料：供 NetStack 決策分析使用

3. **即時更新**：
   - 每日更新 TLE 時觸發重新計算
   - 增量式事件檢測，避免重複計算

## 實現優先順序

1. **Phase 2.1**：在現有 `build_with_phase0_data.py` 中加入基本 D2 事件檢測
2. **Phase 2.2**：實現 A4/A5 事件檢測邏輯
3. **Phase 2.3**：建立獨立的事件資料儲存結構
4. **Phase 2.4**：開發事件視覺化 API 端點

## 預期成果

- **事件檢測準確率**：> 95%
- **預警時間**：D2 事件平均 90-120 秒前預警
- **處理延遲**：< 50ms (基於預計算資料)
- **資料大小**：事件資料約 10-20MB/天