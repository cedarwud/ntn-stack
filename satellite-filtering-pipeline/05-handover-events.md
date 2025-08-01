# 多種換手事件檢測設計

**狀態**: 🔬 詳細設計  
**參考標準**: 3GPP TS 38.331, TS 38.821  
**相關文件**: `/docs/ts.md`, `/docs/sib19.md`

## 📋 設計目標

詳細定義並實現四種換手事件類型的檢測算法：
- **準確性** - 符合 3GPP 標準定義
- **即時性** - 低延遲事件檢測
- **可擴展性** - 易於添加新事件類型
- **可配置性** - 參數可調整優化

## 🎯 3GPP 換手事件詳解

### D2 事件：MRL 距離觸發換手 ✅
```python
class D2EventDetector:
    """
    Event D2: MRL-based handover trigger
    服務衛星 MRL 距離增加，目標衛星 MRL 距離減少
    """
    def __init__(self):
        self.thresh1 = 1000  # km - 服務衛星距離門檻
        self.thresh2 = 800   # km - 目標衛星距離門檻
        self.hysteresis = 50 # km - 遲滯值防止乒乓效應
        
    def detect(self, serving_mrl, target_mrl, time_series):
        events = []
        for i, t in enumerate(time_series):
            if (serving_mrl[i] > self.thresh1 + self.hysteresis and
                target_mrl[i] < self.thresh2 - self.hysteresis):
                events.append({
                    'type': 'D2',
                    'timestamp': t,
                    'serving_mrl': serving_mrl[i],
                    'target_mrl': target_mrl[i],
                    'condition': 'mrl_distance_criteria_met'
                })
        return events
```

### D1 事件：信號品質觸發換手 🆕
```python
class D1EventDetector:
    """
    Event D1: Signal quality-based handover
    服務衛星信號弱化，目標衛星信號增強
    """
    def __init__(self):
        self.rsrp_thresh1 = -110  # dBm - 服務衛星最低門檻
        self.rsrp_thresh2 = -105  # dBm - 目標衛星最低門檻
        self.rsrp_offset = 3      # dB - 目標必須優於服務
        self.time_to_trigger = 100 # ms - 持續時間要求
        
    def detect(self, serving_rsrp, target_rsrp, time_series):
        events = []
        trigger_start = None
        
        for i, t in enumerate(time_series):
            # 檢查觸發條件
            if (serving_rsrp[i] < self.rsrp_thresh1 and
                target_rsrp[i] > self.rsrp_thresh2 and
                target_rsrp[i] > serving_rsrp[i] + self.rsrp_offset):
                
                if trigger_start is None:
                    trigger_start = i
                elif (i - trigger_start) * 10 >= self.time_to_trigger:
                    # 滿足持續時間要求
                    events.append({
                        'type': 'D1',
                        'timestamp': t,
                        'serving_rsrp': serving_rsrp[i],
                        'target_rsrp': target_rsrp[i],
                        'condition': 'signal_quality_handover',
                        'duration_ms': (i - trigger_start) * 10
                    })
                    trigger_start = None
            else:
                trigger_start = None
                
        return events
```

### A4 事件：鄰近衛星測量報告 🆕
```python
class A4EventDetector:
    """
    Event A4: Neighbour becomes better than threshold
    鄰近衛星信號超過配置門檻，觸發測量報告
    """
    def __init__(self):
        self.rsrp_thresh = -100   # dBm - 觸發門檻
        self.hysteresis = 2       # dB - 遲滯值
        self.time_to_trigger = 50 # ms - 持續時間
        self.max_neighbors = 8    # 最大鄰近衛星數
        
    def detect(self, neighbor_measurements, time_series):
        events = []
        trigger_states = {}  # 追蹤每個鄰近衛星的觸發狀態
        
        for i, t in enumerate(time_series):
            for sat_id, rsrp in neighbor_measurements[i].items():
                # 進入條件
                if rsrp > self.rsrp_thresh + self.hysteresis:
                    if sat_id not in trigger_states:
                        trigger_states[sat_id] = i
                    elif (i - trigger_states[sat_id]) * 10 >= self.time_to_trigger:
                        events.append({
                            'type': 'A4',
                            'timestamp': t,
                            'neighbor_id': sat_id,
                            'rsrp': rsrp,
                            'condition': 'neighbor_above_threshold',
                            'measurement_type': 'periodic'
                        })
                        # 避免重複觸發
                        trigger_states[sat_id] = i
                        
                # 離開條件
                elif rsrp < self.rsrp_thresh - self.hysteresis:
                    if sat_id in trigger_states:
                        del trigger_states[sat_id]
                        
        return events
```

### T1 事件：衛星即將不可見 🆕
```python
class T1EventDetector:
    """
    Event T1: Satellite becoming non-visible
    NTN 特定事件 - 預測衛星即將離開覆蓋範圍
    """
    def __init__(self):
        self.min_elevation = 10    # degrees - 最低仰角
        self.prediction_window = 30 # seconds - 預測時間窗
        self.critical_window = 10   # seconds - 緊急換手窗
        
    def detect(self, satellite_positions, ue_position, time_series):
        events = []
        
        for i, t in enumerate(time_series[:-3]):  # 預留預測空間
            current_elevation = calculate_elevation(
                satellite_positions[i], ue_position
            )
            
            # 預測未來位置
            future_idx = min(i + self.prediction_window // 10, 
                           len(time_series) - 1)
            future_elevation = calculate_elevation(
                satellite_positions[future_idx], ue_position
            )
            
            # 檢查是否即將不可見
            if (current_elevation > self.min_elevation and
                future_elevation < self.min_elevation):
                
                # 計算精確的不可見時間
                loss_time = self._interpolate_loss_time(
                    satellite_positions[i:future_idx+1],
                    ue_position,
                    time_series[i:future_idx+1]
                )
                
                time_to_loss = (loss_time - t).total_seconds()
                
                events.append({
                    'type': 'T1',
                    'timestamp': t,
                    'current_elevation': current_elevation,
                    'predicted_loss_time': loss_time,
                    'time_to_loss_seconds': time_to_loss,
                    'urgency': 'critical' if time_to_loss < self.critical_window else 'normal',
                    'condition': 'satellite_leaving_coverage'
                })
                
        return events
```

## 🔧 綜合事件檢測框架

### 事件優先級與協調
```python
class HandoverEventCoordinator:
    """協調多種事件類型，避免衝突"""
    
    EVENT_PRIORITIES = {
        'T1': 1,  # 最高優先級 - 衛星即將消失
        'D1': 2,  # 信號品質急劇下降
        'D2': 3,  # MRL 距離增加
        'A4': 4   # 測量報告（最低優先級）
    }
    
    def coordinate_events(self, all_events):
        """處理事件衝突和優先級"""
        # 按時間戳和優先級排序
        sorted_events = sorted(
            all_events,
            key=lambda e: (e['timestamp'], self.EVENT_PRIORITIES[e['type']])
        )
        
        # 移除衝突事件
        coordinated = []
        last_handover_time = None
        min_interval = timedelta(seconds=5)  # 最小換手間隔
        
        for event in sorted_events:
            if event['type'] in ['D1', 'D2', 'T1']:  # 換手事件
                if (last_handover_time is None or 
                    event['timestamp'] - last_handover_time > min_interval):
                    coordinated.append(event)
                    last_handover_time = event['timestamp']
            else:  # A4 測量報告
                coordinated.append(event)
                
        return coordinated
```

## 📊 事件參數配置

### 可調參數系統
```yaml
# handover_config.yaml
event_parameters:
  d2:
    thresh1_km: 1000
    thresh2_km: 800
    hysteresis_km: 50
    
  d1:
    rsrp_thresh1_dbm: -110
    rsrp_thresh2_dbm: -105
    rsrp_offset_db: 3
    time_to_trigger_ms: 100
    
  a4:
    rsrp_thresh_dbm: -100
    hysteresis_db: 2
    time_to_trigger_ms: 50
    max_neighbors: 8
    reporting_interval_ms: 1000
    
  t1:
    min_elevation_deg: 10
    prediction_window_s: 30
    critical_window_s: 10
    
coordination:
  min_handover_interval_s: 5
  event_buffer_size: 100
  priority_mode: "strict"  # strict, weighted, adaptive
```

## 💡 特殊考量

### 1. LEO 衛星高速移動
- 事件檢測需要考慮快速變化的幾何關係
- 預測算法必須準確且低延遲
- 時間同步要求嚴格

### 2. 多衛星可見性
- 同時可能有多個衛星滿足換手條件
- 需要智能選擇最佳目標衛星
- 考慮負載平衡

### 3. 乒乓效應防止
```python
class PingPongPrevention:
    def __init__(self):
        self.handover_history = deque(maxlen=10)
        self.penalty_duration = 30  # seconds
        
    def is_pingpong_risk(self, source_id, target_id, timestamp):
        """檢查是否有乒乓換手風險"""
        for prev_ho in self.handover_history:
            if (prev_ho['source'] == target_id and 
                prev_ho['target'] == source_id and
                timestamp - prev_ho['time'] < self.penalty_duration):
                return True
        return False
```

## 🚀 測試場景

### 典型換手場景
1. **正常通過**: 衛星從地平線升起到落下
2. **快速切換**: 多衛星同時可見的城市環境
3. **邊緣情況**: 極地區域的特殊軌道
4. **高負載**: 密集用戶區域的資源競爭

## ✅ 驗證標準

- [ ] 事件檢測準確率 > 99%
- [ ] 誤報率 < 0.1%
- [ ] 檢測延遲 < 100ms
- [ ] 支援 1000+ 並發用戶
- [ ] 完整的單元測試覆蓋

## 📚 參考資料

- 3GPP TS 38.331 - RRC Protocol
- 3GPP TS 38.821 - NTN Solutions
- ITU-R M.2410 - Satellite Handover
- 實測數據：Starlink/OneWeb 軌跡
