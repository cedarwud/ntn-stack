# 📡 換手事件整合 (A4/A5/D2)

**文檔編號**: 03  
**主題**: 3GPP NTN 換手事件觸發邏輯與資料預處理整合

## 1. 事件定義與觸發條件

### 1.1 Event A4 - 鄰近小區變優
**3GPP TS 38.331 定義**：鄰近小區測量結果優於門檻值

```python
class EventA4:
    """Event A4: Neighbour becomes better than threshold"""
    
    def __init__(self):
        self.threshold = -95  # dBm (RSRP)
        self.hysteresis = 3   # dB
        self.time_to_trigger = 320  # ms
        
    def check_entering_condition(self, neighbour_rsrp, offsets):
        """進入條件: Mn + Ofn + Ocn - Hys > Thresh"""
        mn = neighbour_rsrp
        ofn = offsets.get('frequency_offset', 0)
        ocn = offsets.get('cell_offset', 0)
        
        return (mn + ofn + ocn - self.hysteresis) > self.threshold
    
    def check_leaving_condition(self, neighbour_rsrp, offsets):
        """離開條件: Mn + Ofn + Ocn + Hys < Thresh"""
        mn = neighbour_rsrp
        ofn = offsets.get('frequency_offset', 0)
        ocn = offsets.get('cell_offset', 0)
        
        return (mn + ofn + ocn + self.hysteresis) < self.threshold
```

### 1.2 Event A5 - 服務小區變差且鄰近變優
**3GPP TS 38.331 定義**：雙門檻觸發

```python
class EventA5:
    """Event A5: Serving becomes worse than threshold1 and neighbour better than threshold2"""
    
    def __init__(self):
        self.threshold1 = -100  # dBm (服務小區門檻)
        self.threshold2 = -95   # dBm (鄰近小區門檻)
        self.hysteresis = 3     # dB
        self.time_to_trigger = 640  # ms
        
    def check_entering_condition(self, serving_rsrp, neighbour_rsrp, offsets):
        """進入條件: Mp + Hys < Thresh1 AND Mn + Ofn + Ocn - Hys > Thresh2"""
        mp = serving_rsrp
        mn = neighbour_rsrp
        ofn = offsets.get('frequency_offset', 0)
        ocn = offsets.get('cell_offset', 0)
        
        serving_condition = (mp + self.hysteresis) < self.threshold1
        neighbour_condition = (mn + ofn + ocn - self.hysteresis) > self.threshold2
        
        return serving_condition and neighbour_condition
```

### 1.3 Event D2 - NTN 仰角觸發
**NTN 特定事件**：基於衛星仰角的換手觸發

```python
class EventD2:
    """Event D2: Satellite elevation-based handover trigger (NTN specific)"""
    
    def __init__(self):
        self.low_elevation_threshold = 15   # 度
        self.high_elevation_threshold = 25  # 度
        self.time_to_trigger = 1000  # ms
        
    def check_trigger_conditions(self, serving_sat, candidate_sats):
        """檢查 D2 觸發條件"""
        
        triggers = []
        
        # D2-1: 服務衛星仰角過低
        if serving_sat.elevation < self.low_elevation_threshold:
            for candidate in candidate_sats:
                if candidate.elevation > self.high_elevation_threshold:
                    triggers.append({
                        "type": "D2-1",
                        "reason": "serving_low_elevation",
                        "serving": serving_sat,
                        "target": candidate,
                        "urgency": "high"
                    })
        
        # D2-2: 候選衛星仰角顯著更優
        elevation_improvement_threshold = 20  # 度
        for candidate in candidate_sats:
            elevation_diff = candidate.elevation - serving_sat.elevation
            if elevation_diff > elevation_improvement_threshold:
                triggers.append({
                    "type": "D2-2",
                    "reason": "significant_elevation_improvement",
                    "serving": serving_sat,
                    "target": candidate,
                    "urgency": "medium"
                })
        
        # D2-3: 預測性換手（衛星即將消失）
        if serving_sat.time_to_los < 60:  # 60秒內失去視線
            best_candidate = max(candidate_sats, key=lambda s: s.elevation, default=None)
            if best_candidate and best_candidate.time_to_los > 180:
                triggers.append({
                    "type": "D2-3",
                    "reason": "predictive_handover",
                    "serving": serving_sat,
                    "target": best_candidate,
                    "urgency": "critical"
                })
        
        return triggers
```

## 2. 衛星選擇與事件觸發整合

### 2.1 事件感知的衛星篩選
```python
class EventAwareSatelliteSelector:
    """整合換手事件的衛星選擇器"""
    
    def __init__(self):
        self.event_a4 = EventA4()
        self.event_a5 = EventA5()
        self.event_d2 = EventD2()
        
    def score_satellite_for_events(self, satellite, timestamp):
        """評估衛星觸發各種事件的潛力"""
        
        score = 0
        event_potential = {}
        
        # 預測該時間點的衛星參數
        sat_state = self.predict_satellite_state(satellite, timestamp)
        
        # A4 事件潛力
        if sat_state.rsrp > self.event_a4.threshold - 10:
            event_potential['A4'] = True
            score += 20
        
        # A5 事件潛力（作為候選）
        if sat_state.rsrp > self.event_a5.threshold2 - 5:
            event_potential['A5_candidate'] = True
            score += 15
        
        # D2 事件潛力
        if 20 <= sat_state.elevation <= 70:  # 理想仰角範圍
            event_potential['D2_optimal'] = True
            score += 25
        elif sat_state.elevation < 15:  # 可觸發 D2-1
            event_potential['D2_trigger'] = True
            score += 10
        
        # 時間多樣性加分
        if sat_state.time_in_view > 300:  # 可見時間 > 5分鐘
            score += 10
        
        return score, event_potential
    
    def select_satellites_with_event_coverage(self, candidate_pool, target_count):
        """選擇能觸發多樣化事件的衛星子集"""
        
        selected = []
        event_coverage = {
            'A4': 0,
            'A5': 0,
            'D2': 0
        }
        
        # 按事件潛力評分排序
        scored_candidates = []
        for sat in candidate_pool:
            score, events = self.score_satellite_for_events(sat, self.reference_time)
            scored_candidates.append((sat, score, events))
        
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        
        # 選擇衛星，確保事件覆蓋
        for sat, score, events in scored_candidates:
            if len(selected) >= target_count:
                break
            
            # 優先選擇能增加事件多樣性的衛星
            adds_diversity = False
            if events.get('A4') and event_coverage['A4'] < 5:
                adds_diversity = True
                event_coverage['A4'] += 1
            if events.get('A5_candidate') and event_coverage['A5'] < 5:
                adds_diversity = True
                event_coverage['A5'] += 1
            if events.get('D2_optimal') and event_coverage['D2'] < 5:
                adds_diversity = True
                event_coverage['D2'] += 1
            
            if adds_diversity or len(selected) < target_count * 0.6:
                selected.append(sat)
        
        return selected, event_coverage
```

### 2.2 換手對生成
```python
class HandoverPairGenerator:
    """生成適合展示各種換手事件的衛星對"""
    
    def generate_event_pairs(self, satellites, time_window):
        """生成事件觸發對"""
        
        pairs = {
            'A4_pairs': [],
            'A5_pairs': [],
            'D2_pairs': []
        }
        
        # 遍歷時間窗口
        for timestamp in time_window:
            visible_sats = self.get_visible_satellites(satellites, timestamp)
            
            if len(visible_sats) < 2:
                continue
            
            # 按信號強度排序
            visible_sats.sort(key=lambda s: s.rsrp, reverse=True)
            
            # 生成 A4 事件對
            for i, sat in enumerate(visible_sats[1:], 1):  # 跳過最強的
                if self.event_a4.check_entering_condition(sat.rsrp, {}):
                    pairs['A4_pairs'].append({
                        'timestamp': timestamp,
                        'candidate': sat,
                        'current_best': visible_sats[0],
                        'event_data': {
                            'rsrp_diff': sat.rsrp - visible_sats[0].rsrp,
                            'elevation_diff': sat.elevation - visible_sats[0].elevation
                        }
                    })
            
            # 生成 A5 事件對
            weakest = visible_sats[-1]
            if weakest.rsrp < self.event_a5.threshold1:
                for candidate in visible_sats[:-1]:
                    if candidate.rsrp > self.event_a5.threshold2:
                        pairs['A5_pairs'].append({
                            'timestamp': timestamp,
                            'serving': weakest,
                            'candidate': candidate,
                            'event_data': {
                                'serving_rsrp': weakest.rsrp,
                                'candidate_rsrp': candidate.rsrp
                            }
                        })
            
            # 生成 D2 事件對
            for serving in visible_sats:
                d2_triggers = self.event_d2.check_trigger_conditions(
                    serving, 
                    [s for s in visible_sats if s != serving]
                )
                for trigger in d2_triggers:
                    pairs['D2_pairs'].append({
                        'timestamp': timestamp,
                        'trigger': trigger,
                        'serving': trigger['serving'],
                        'target': trigger['target']
                    })
        
        return pairs
```

## 3. 時間序列中的事件標記

### 3.1 事件時間線生成
```python
class EventTimeline:
    """生成換手事件時間線"""
    
    def __init__(self):
        self.events = []
        
    def generate_timeline(self, satellite_trajectories, time_window):
        """生成完整的事件時間線"""
        
        timeline = []
        
        # 初始化事件檢測器
        detectors = {
            'A4': EventA4Detector(),
            'A5': EventA5Detector(),
            'D2': EventD2Detector()
        }
        
        # 逐時間點檢測
        for timestamp in time_window:
            frame_events = []
            
            # 獲取當前可見衛星狀態
            visible_states = self.get_satellite_states(
                satellite_trajectories, 
                timestamp
            )
            
            # 檢測各類事件
            for event_type, detector in detectors.items():
                detected = detector.detect(visible_states, timestamp)
                for event in detected:
                    frame_events.append({
                        'type': event_type,
                        'timestamp': timestamp,
                        'details': event
                    })
            
            if frame_events:
                timeline.append({
                    'timestamp': timestamp,
                    'events': frame_events
                })
        
        return timeline
    
    def mark_critical_moments(self, timeline):
        """標記關鍵時刻用於展示"""
        
        critical_moments = []
        
        for entry in timeline:
            # 多事件同時觸發
            if len(entry['events']) >= 2:
                critical_moments.append({
                    'timestamp': entry['timestamp'],
                    'type': 'multi_event',
                    'events': entry['events']
                })
            
            # D2-3 緊急換手
            for event in entry['events']:
                if event['type'] == 'D2' and event['details'].get('urgency') == 'critical':
                    critical_moments.append({
                        'timestamp': entry['timestamp'],
                        'type': 'urgent_handover',
                        'event': event
                    })
        
        return critical_moments
```

### 3.2 事件驅動的數據結構
```python
def create_event_aware_timeseries(satellites, time_window):
    """創建包含事件信息的時間序列數據"""
    
    timeseries = {
        'metadata': {
            'start_time': time_window['start'],
            'end_time': time_window['end'],
            'interval_seconds': 30,
            'event_types': ['A4', 'A5', 'D2']
        },
        'frames': [],
        'events': [],
        'statistics': {}
    }
    
    # 生成基礎軌跡
    trajectories = calculate_trajectories(satellites, time_window)
    
    # 生成事件時間線
    event_timeline = EventTimeline().generate_timeline(trajectories, time_window)
    
    # 合併數據
    for timestamp in time_window:
        frame = {
            'timestamp': timestamp,
            'satellites': [],
            'active_events': [],
            'handover_candidates': []
        }
        
        # 添加衛星狀態
        for sat_id, trajectory in trajectories.items():
            state = trajectory.get_state_at(timestamp)
            if state.elevation >= 10:  # 只包含可見衛星
                frame['satellites'].append(state)
        
        # 添加事件
        events_at_time = [e for e in event_timeline if e['timestamp'] == timestamp]
        frame['active_events'] = events_at_time
        
        # 識別換手候選
        if frame['satellites']:
            serving = max(frame['satellites'], key=lambda s: s.rsrp)
            candidates = identify_handover_candidates(serving, frame['satellites'])
            frame['handover_candidates'] = candidates
        
        timeseries['frames'].append(frame)
    
    # 計算統計
    timeseries['statistics'] = calculate_event_statistics(timeseries['frames'])
    
    return timeseries
```

## 4. 信號強度模型

### 4.1 RSRP 估算
```python
def estimate_rsrp(distance_km, elevation_deg, tx_power_dbm=23):
    """估算參考信號接收功率 (RSRP)"""
    
    # 自由空間路徑損耗 (FSPL)
    frequency_ghz = 2.0  # S-band
    fspl = 20 * np.log10(distance_km) + 20 * np.log10(frequency_ghz) + 92.45
    
    # 大氣衰減
    atmospheric_loss = calculate_atmospheric_loss(elevation_deg, frequency_ghz)
    
    # 天線增益 (仰角相關)
    antenna_gain = calculate_antenna_gain(elevation_deg)
    
    # 計算 RSRP
    rsrp = tx_power_dbm - fspl - atmospheric_loss + antenna_gain
    
    # 添加陰影衰落
    shadow_fading = np.random.normal(0, 3)  # 3 dB 標準差
    
    return rsrp + shadow_fading

def calculate_atmospheric_loss(elevation_deg, frequency_ghz):
    """計算大氣衰減 (ITU-R P.618)"""
    
    if elevation_deg < 5:
        return 20  # 高衰減
    elif elevation_deg < 10:
        return 10
    elif elevation_deg < 20:
        return 5
    elif elevation_deg < 30:
        return 3
    else:
        return 2  # 低衰減

def calculate_antenna_gain(elevation_deg):
    """計算天線增益模式"""
    
    # 簡化的餘弦模式
    optimal_elevation = 45
    gain_pattern = np.cos(np.radians(abs(elevation_deg - optimal_elevation)))
    max_gain = 15  # dBi
    
    return max_gain * gain_pattern
```

### 4.2 都卜勒頻移計算
```python
def calculate_doppler_shift(velocity_vector, position_vector, observer_position):
    """計算都卜勒頻移"""
    
    # 計算徑向速度
    los_vector = position_vector - observer_position
    los_unit = los_vector / np.linalg.norm(los_vector)
    radial_velocity = np.dot(velocity_vector, los_unit)  # km/s
    
    # 計算都卜勒頻移
    c = 299792.458  # 光速 km/s
    frequency = 2e9  # 2 GHz
    doppler_shift = frequency * (radial_velocity / c)
    
    return doppler_shift  # Hz
```

## 5. 事件視覺化準備

### 5.1 事件標記數據
```python
def prepare_visualization_data(timeseries_with_events):
    """準備用於視覺化的事件數據"""
    
    viz_data = {
        'event_markers': [],
        'handover_arrows': [],
        'signal_charts': [],
        'elevation_plots': []
    }
    
    for frame in timeseries_with_events['frames']:
        # 事件標記
        for event in frame['active_events']:
            viz_data['event_markers'].append({
                'timestamp': frame['timestamp'],
                'type': event['type'],
                'position': calculate_event_position(event),
                'color': get_event_color(event['type']),
                'label': format_event_label(event)
            })
        
        # 換手箭頭
        for candidate in frame['handover_candidates']:
            if candidate['probability'] > 0.5:
                viz_data['handover_arrows'].append({
                    'timestamp': frame['timestamp'],
                    'from': frame['serving_satellite'],
                    'to': candidate['satellite'],
                    'probability': candidate['probability'],
                    'event_type': candidate['triggering_event']
                })
        
        # 信號圖表數據
        viz_data['signal_charts'].append({
            'timestamp': frame['timestamp'],
            'satellites': [
                {
                    'id': sat['id'],
                    'rsrp': sat['rsrp'],
                    'elevation': sat['elevation']
                }
                for sat in frame['satellites']
            ]
        })
    
    return viz_data
```

## 6. 實施檢查清單

### 6.1 數據完整性檢查
- [ ] 每個時間點有 8-12 顆可見衛星
- [ ] A4 事件觸發機會 > 10次/小時
- [ ] A5 事件觸發機會 > 5次/小時
- [ ] D2 事件觸發機會 > 15次/小時
- [ ] 換手候選對重疊時間 > 2分鐘

### 6.2 事件多樣性檢查
- [ ] 包含高/低仰角觸發場景
- [ ] 包含信號強度逆轉場景
- [ ] 包含緊急換手場景
- [ ] 包含多衛星競爭場景

### 6.3 時間連續性檢查
- [ ] 事件分佈均勻，無長時間空白
- [ ] 衛星出現時間錯開
- [ ] 換手機會連續可用

---

**下一步**: 查看 [數據流架構](./04-data-flow-architecture.md) 了解系統整合