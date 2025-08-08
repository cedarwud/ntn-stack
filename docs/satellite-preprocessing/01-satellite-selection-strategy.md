# 🎯 衛星選擇策略設計

**文檔編號**: 01  
**主題**: 從大規模星座中篩選研究級衛星子集

## 1. 選星核心原則

### 1.1 數量需求計算
基於 duty cycle 分析，確保 8-12 顆同時可見：

```python
# Duty Cycle 基礎公式
duty_cycle = visible_time / orbital_period
required_satellites = target_visible / duty_cycle * safety_factor

# Starlink 計算
starlink_duty = 10 / 96  # 約 10.4%
starlink_needed = 10 / 0.104 * 1.5  # ≈ 144顆（含安全係數）

# OneWeb 計算  
oneweb_duty = 20 / 109  # 約 18.3%
oneweb_needed = 10 / 0.183 * 1.3  # ≈ 71顆（含安全係數）
```

### 1.2 相位分散要求
避免衛星同時出現/消失，確保換手機會連續：

- **軌道平面分組**: 每個軌道平面選 15-20% 衛星
- **相位均勻採樣**: Mean Anomaly 間隔 > 15°
- **時間錯開**: 升起時間間隔 15-30 秒

## 2. 三階段篩選流程

### 第一階段：軌道平面分群
```python
def orbital_plane_grouping(satellites):
    """按軌道平面分群，確保多樣性"""
    planes = {}
    for sat in satellites:
        # 使用 RAAN (升交點赤經) 和 inclination 分群
        plane_id = f"{sat.inclination:.1f}_{sat.raan:.1f}"
        if plane_id not in planes:
            planes[plane_id] = []
        planes[plane_id].append(sat)
    
    # Starlink: 72個軌道平面，每平面選2-3顆
    # OneWeb: 18個軌道平面，每平面選4-5顆
    return planes
```

### 第二階段：可見性評分
```python
def visibility_scoring(satellite, observer_location):
    """計算衛星的可見性評分"""
    score_components = {
        "peak_elevation": 0.30,      # 最高仰角
        "visible_duration": 0.25,     # 可見時長
        "pass_frequency": 0.20,       # 過境頻率
        "signal_quality": 0.15,       # 預估信號品質
        "orbital_stability": 0.10     # 軌道穩定性
    }
    
    # 計算各項分數
    peak_elev_score = min(satellite.max_elevation / 90, 1.0)
    duration_score = min(satellite.visible_minutes / 15, 1.0)
    frequency_score = satellite.daily_passes / 15
    signal_score = estimate_signal_strength(satellite)
    stability_score = 1.0 - satellite.tle_age_days / 30
    
    # 加權總分
    total_score = (
        peak_elev_score * score_components["peak_elevation"] +
        duration_score * score_components["visible_duration"] +
        frequency_score * score_components["pass_frequency"] +
        signal_score * score_components["signal_quality"] +
        stability_score * score_components["orbital_stability"]
    )
    
    return total_score
```

### 第三階段：相位分散優化
```python
def phase_distribution_optimization(selected_satellites):
    """優化相位分佈，避免叢聚"""
    
    # 計算每顆衛星的升起時間
    rise_times = []
    for sat in selected_satellites:
        rise_time = calculate_next_rise_time(sat, observer_location)
        rise_times.append((sat, rise_time))
    
    # 按升起時間排序
    rise_times.sort(key=lambda x: x[1])
    
    # 檢查時間間隔
    optimized = []
    last_rise = None
    MIN_INTERVAL = 20  # 最小間隔20秒
    
    for sat, rise_time in rise_times:
        if last_rise is None or (rise_time - last_rise).seconds >= MIN_INTERVAL:
            optimized.append(sat)
            last_rise = rise_time
        else:
            # 調整相位或選擇替代衛星
            alternative = find_alternative_satellite(sat, rise_time + timedelta(seconds=MIN_INTERVAL))
            if alternative:
                optimized.append(alternative)
    
    return optimized
```

## 3. A4/A5/D2 事件整合

### 3.1 事件觸發條件
整合 3GPP NTN 標準事件到選星策略：

```python
class HandoverEventCriteria:
    """換手事件判定條件"""
    
    # Event A4: 鄰近小區變優
    A4_THRESHOLD = -95  # dBm
    A4_HYSTERESIS = 3   # dB
    
    # Event A5: 服務小區變差且鄰近變優  
    A5_THRESH1 = -100   # 服務小區門檻
    A5_THRESH2 = -95    # 鄰近小區門檻
    
    # Event D2: 仰角觸發（NTN特有）
    D2_LOW_ELEVATION = 15     # 低仰角門檻
    D2_HIGH_ELEVATION = 25    # 高仰角門檻
    
    def should_include_satellite(self, sat_metrics):
        """判斷衛星是否適合觸發換手事件"""
        
        # 檢查是否能觸發 A4
        can_trigger_a4 = sat_metrics.rsrp > self.A4_THRESHOLD + self.A4_HYSTERESIS
        
        # 檢查是否能觸發 A5
        can_trigger_a5 = sat_metrics.rsrp > self.A5_THRESH2
        
        # 檢查是否能觸發 D2
        can_trigger_d2 = (
            sat_metrics.elevation > self.D2_LOW_ELEVATION and
            sat_metrics.elevation < 75  # 避免天頂衛星
        )
        
        # 至少能觸發一種事件
        return can_trigger_a4 or can_trigger_a5 or can_trigger_d2
```

### 3.2 候選衛星配對
確保有足夠的換手候選對：

```python
def ensure_handover_pairs(satellites):
    """確保有適合的換手候選對"""
    
    pairs = []
    for i, sat1 in enumerate(satellites):
        for sat2 in satellites[i+1:]:
            # 檢查重疊可見時間
            overlap = calculate_visibility_overlap(sat1, sat2)
            
            if overlap > timedelta(minutes=2):  # 至少2分鐘重疊
                # 檢查信號強度差異
                signal_diff = abs(sat1.estimated_rsrp - sat2.estimated_rsrp)
                
                if 5 <= signal_diff <= 15:  # 適中的信號差異
                    pairs.append((sat1, sat2, overlap))
    
    # 確保有足夠的換手對
    if len(pairs) < 20:
        # 添加更多衛星或調整選擇標準
        return adjust_selection_criteria(satellites)
    
    return satellites
```

## 4. 動態調整機制

### 4.1 實時監控
```python
class SatellitePoolMonitor:
    """監控衛星池品質"""
    
    def __init__(self):
        self.min_visible = 8
        self.max_visible = 12
        self.target_visible = 10
        
    def check_coverage_quality(self, timestamp, satellite_pool):
        """檢查特定時間的覆蓋品質"""
        
        visible_sats = []
        for sat in satellite_pool:
            elevation = calculate_elevation(sat, timestamp, NTPU_LOCATION)
            if elevation >= 10:  # 10度仰角門檻
                visible_sats.append(sat)
        
        quality_metrics = {
            "visible_count": len(visible_sats),
            "coverage_gap": max(0, self.min_visible - len(visible_sats)),
            "excess_coverage": max(0, len(visible_sats) - self.max_visible),
            "handover_candidates": self.count_handover_pairs(visible_sats),
            "event_triggers": self.check_event_triggers(visible_sats)
        }
        
        return quality_metrics
    
    def adjust_pool_if_needed(self, quality_metrics, satellite_pool):
        """根據品質指標調整衛星池"""
        
        if quality_metrics["coverage_gap"] > 0:
            # 添加更多衛星
            return self.add_satellites(satellite_pool, quality_metrics["coverage_gap"])
        
        elif quality_metrics["excess_coverage"] > 3:
            # 移除多餘衛星
            return self.remove_satellites(satellite_pool, quality_metrics["excess_coverage"])
        
        return satellite_pool
```

### 4.2 時間窗口驗證
```python
def validate_time_window(satellite_pool, duration_hours=24):
    """驗證時間窗口內的覆蓋品質"""
    
    start_time = datetime.now(timezone.utc)
    end_time = start_time + timedelta(hours=duration_hours)
    
    # 每30秒採樣一次
    sample_interval = 30
    timestamps = []
    current = start_time
    
    while current <= end_time:
        timestamps.append(current)
        current += timedelta(seconds=sample_interval)
    
    # 統計各時間點的可見衛星數
    visibility_stats = []
    for ts in timestamps:
        visible_count = count_visible_satellites(satellite_pool, ts, NTPU_LOCATION)
        visibility_stats.append(visible_count)
    
    # 計算統計指標
    stats = {
        "mean_visible": np.mean(visibility_stats),
        "std_visible": np.std(visibility_stats),
        "min_visible": np.min(visibility_stats),
        "max_visible": np.max(visibility_stats),
        "below_target_ratio": sum(1 for v in visibility_stats if v < 8) / len(visibility_stats),
        "optimal_ratio": sum(1 for v in visibility_stats if 8 <= v <= 12) / len(visibility_stats)
    }
    
    return stats
```

## 5. 實施建議

### 5.1 初始配置
- **Starlink**: 從 120 顆開始，驗證覆蓋品質
- **OneWeb**: 從 70 顆開始，確保極地軌道多樣性

### 5.2 迭代優化
1. 運行 24 小時模擬
2. 分析覆蓋缺口和過度覆蓋
3. 調整衛星數量和選擇標準
4. 重複直到達到 >95% 時間的 8-12 顆可見

### 5.3 性能考量
- 預計算可見性窗口，避免實時計算
- 使用空間索引加速衛星查找
- 批量處理 SGP4 計算

---

**下一步**: 查看 [時間序列規劃](./02-timeseries-planning.md) 了解連續運行設計