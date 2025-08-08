# ⏱️ 時間序列規劃

**文檔編號**: 02  
**主題**: 連續運行的時間段設計與循環策略

## 1. 時間段需求分析

### 1.1 展示需求
立體圖需要**無限循環運行**，展示連續的衛星運動和換手：

- **最小展示週期**: 2-3 個完整軌道週期（3-5 小時）
- **理想展示週期**: 24 小時（展現日變化）
- **循環策略**: 無縫銜接，避免突然重置

### 1.2 數據量估算
```python
data_volume_estimation = {
    "starlink": {
        "satellites": 120,
        "time_points": 24 * 60 * 2,  # 24小時，30秒間隔
        "data_per_point": 64,  # bytes (位置、速度、信號)
        "total_size_mb": 120 * 2880 * 64 / 1024 / 1024  # ≈ 21 MB
    },
    "oneweb": {
        "satellites": 80,
        "time_points": 24 * 60 * 2,
        "data_per_point": 64,
        "total_size_mb": 80 * 2880 * 64 / 1024 / 1024  # ≈ 14 MB
    }
}
```

## 2. 循環時間窗口設計

### 2.1 基礎週期計算
```python
class OrbitPeriodAnalyzer:
    """分析軌道週期，設計最佳循環窗口"""
    
    def calculate_optimal_window(self, constellation):
        if constellation == "starlink":
            orbit_period = 96  # 分鐘
            # 找最小公倍數，確保完整週期
            # 15個軌道 = 1440分鐘 = 24小時
            return {
                "window_hours": 24,
                "complete_orbits": 15,
                "seamless_loop": True
            }
        
        elif constellation == "oneweb":
            orbit_period = 109  # 分鐘
            # 13個軌道 ≈ 1417分鐘 ≈ 23.6小時
            # 取24小時，會有小偏移但可接受
            return {
                "window_hours": 24,
                "complete_orbits": 13.2,
                "seamless_loop": True,  # 需要相位調整
                "phase_adjustment": 23  # 分鐘偏移
            }
```

### 2.2 無縫循環策略
```python
def create_seamless_loop(timeseries_data, window_hours=24):
    """創建無縫循環的時間序列"""
    
    # 1. 確保首尾銜接
    first_frame = timeseries_data[0]
    last_frame = timeseries_data[-1]
    
    # 2. 計算位置差異
    position_diff = calculate_position_difference(first_frame, last_frame)
    
    if position_diff > POSITION_THRESHOLD:
        # 3. 添加過渡段
        transition_duration = 60  # 60秒過渡
        transition_frames = interpolate_transition(
            last_frame, 
            first_frame, 
            transition_duration
        )
        
        # 4. 插入過渡段
        timeseries_data = timeseries_data + transition_frames
    
    # 5. 標記循環點
    timeseries_data.metadata["loop_point"] = len(timeseries_data) - len(transition_frames)
    
    return timeseries_data
```

## 3. 時間戳策略優化

### 3.1 動態時間窗口選擇
```python
class DynamicTimeWindowSelector:
    """選擇最佳觀測時間窗口"""
    
    def find_optimal_window(self, date, constellation):
        """找到指定日期的最佳24小時窗口"""
        
        candidates = []
        
        # 測試不同起始時間
        for hour in range(0, 24, 6):  # 每6小時測試一次
            start_time = datetime(date.year, date.month, date.day, hour, 0, 0, tzinfo=timezone.utc)
            end_time = start_time + timedelta(hours=24)
            
            # 評估這個時間窗口
            quality = self.evaluate_window_quality(
                start_time, 
                end_time, 
                constellation
            )
            
            candidates.append({
                "start": start_time,
                "end": end_time,
                "quality_score": quality
            })
        
        # 選擇最佳窗口
        best_window = max(candidates, key=lambda x: x["quality_score"])
        return best_window
    
    def evaluate_window_quality(self, start_time, end_time, constellation):
        """評估時間窗口品質"""
        
        # 採樣評估
        sample_times = []
        current = start_time
        while current <= end_time:
            sample_times.append(current)
            current += timedelta(minutes=10)
        
        # 計算各指標
        metrics = []
        for ts in sample_times:
            visible_sats = self.count_visible_satellites(ts, constellation)
            handover_candidates = self.count_handover_candidates(ts, constellation)
            
            metrics.append({
                "visible": visible_sats,
                "candidates": handover_candidates
            })
        
        # 綜合評分
        score = 0
        score += sum(1 for m in metrics if 8 <= m["visible"] <= 12) * 10  # 理想可見數
        score += sum(1 for m in metrics if m["candidates"] >= 3) * 5      # 充足候選
        score -= sum(1 for m in metrics if m["visible"] < 6) * 20         # 懲罰過少
        score -= sum(1 for m in metrics if m["visible"] > 15) * 5         # 懲罰過多
        
        return score
```

### 3.2 歷史數據對齊
```python
def align_with_historical_tle(target_date, tle_archive):
    """對齊歷史 TLE 數據"""
    
    # 找最接近的 TLE epoch
    best_tle_set = None
    min_time_diff = float('inf')
    
    for tle_date, tle_data in tle_archive.items():
        time_diff = abs((target_date - tle_date).total_seconds())
        
        if time_diff < min_time_diff:
            min_time_diff = time_diff
            best_tle_set = tle_data
    
    # 檢查 TLE 年齡
    tle_age_days = min_time_diff / 86400
    
    if tle_age_days > 7:
        print(f"警告: TLE 數據年齡 {tle_age_days:.1f} 天，可能影響精度")
    
    return best_tle_set, tle_age_days
```

## 4. 數據預計算策略

### 4.1 批量計算框架
```python
class BatchTrajectoryCalculator:
    """批量計算衛星軌跡"""
    
    def __init__(self):
        self.sgp4_calculator = SGP4Calculator()
        self.cache = {}
        
    def calculate_batch(self, satellites, time_window, interval_seconds=30):
        """批量計算所有衛星的時間序列"""
        
        results = {}
        
        # 生成時間點
        timestamps = []
        current = time_window["start"]
        while current <= time_window["end"]:
            timestamps.append(current)
            current += timedelta(seconds=interval_seconds)
        
        # 並行計算每顆衛星
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = {}
            
            for sat in satellites:
                future = executor.submit(
                    self.calculate_satellite_trajectory,
                    sat,
                    timestamps
                )
                futures[sat.id] = future
            
            # 收集結果
            for sat_id, future in futures.items():
                results[sat_id] = future.result()
        
        return results
    
    def calculate_satellite_trajectory(self, satellite, timestamps):
        """計算單顆衛星的完整軌跡"""
        
        trajectory = []
        
        for ts in timestamps:
            # SGP4 計算
            position, velocity = self.sgp4_calculator.propagate(
                satellite.tle,
                ts
            )
            
            # 轉換到地理座標
            lat, lon, alt = eci_to_geographic(position, ts)
            
            # 計算相對觀測者的參數
            elevation, azimuth, distance = calculate_relative_position(
                lat, lon, alt,
                NTPU_LAT, NTPU_LON, NTPU_ALT
            )
            
            # 估算信號參數
            rsrp = estimate_rsrp(distance, elevation, satellite.tx_power)
            doppler = calculate_doppler_shift(velocity, position, NTPU_POSITION)
            
            trajectory.append({
                "timestamp": ts.isoformat(),
                "position": {
                    "lat": lat,
                    "lon": lon,
                    "alt": alt
                },
                "relative": {
                    "elevation": elevation,
                    "azimuth": azimuth,
                    "distance": distance
                },
                "signal": {
                    "rsrp": rsrp,
                    "doppler": doppler
                }
            })
        
        return trajectory
```

### 4.2 增量更新機制
```python
class IncrementalUpdater:
    """增量更新時間序列數據"""
    
    def update_timeseries(self, existing_data, new_tle, update_window):
        """使用新 TLE 更新部分時間序列"""
        
        # 識別需要更新的衛星
        updated_satellites = self.identify_changed_satellites(
            existing_data.tle_version,
            new_tle
        )
        
        if not updated_satellites:
            print("無需更新，TLE 無顯著變化")
            return existing_data
        
        # 只重算變更的衛星
        print(f"更新 {len(updated_satellites)} 顆衛星的軌跡")
        
        updated_trajectories = self.calculator.calculate_batch(
            updated_satellites,
            update_window
        )
        
        # 合併到現有數據
        for sat_id, trajectory in updated_trajectories.items():
            existing_data.trajectories[sat_id] = trajectory
        
        # 更新元數據
        existing_data.tle_version = new_tle.version
        existing_data.last_updated = datetime.now(timezone.utc)
        
        return existing_data
```

## 5. 循環播放實現

### 5.1 前端播放控制
```javascript
class TimeSeriesPlayer {
    constructor(timeseriesData) {
        this.data = timeseriesData
        this.currentIndex = 0
        this.loopPoint = timeseriesData.metadata.loop_point
        this.isPlaying = false
        this.playbackSpeed = 1
    }
    
    play() {
        this.isPlaying = true
        this.animationLoop()
    }
    
    animationLoop() {
        if (!this.isPlaying) return
        
        // 更新當前幀
        this.updateFrame(this.currentIndex)
        
        // 計算下一幀
        this.currentIndex += this.playbackSpeed
        
        // 檢查循環點
        if (this.currentIndex >= this.loopPoint) {
            this.currentIndex = 0  // 無縫循環
            this.onLoopComplete()
        }
        
        // 繼續動畫
        requestAnimationFrame(() => this.animationLoop())
    }
    
    updateFrame(index) {
        const frameData = this.data.frames[index]
        
        // 更新衛星位置
        frameData.satellites.forEach(sat => {
            this.updateSatellitePosition(sat)
        })
        
        // 檢查換手事件
        this.checkHandoverEvents(frameData.timestamp)
        
        // 更新時間顯示
        this.updateTimeDisplay(frameData.timestamp)
    }
}
```

### 5.2 記憶體管理
```python
def optimize_memory_usage(timeseries_data):
    """優化記憶體使用"""
    
    # 1. 壓縮重複數據
    compressed = compress_redundant_data(timeseries_data)
    
    # 2. 使用差分編碼
    delta_encoded = delta_encode_positions(compressed)
    
    # 3. 只保留可見衛星的詳細數據
    visible_only = filter_visible_satellites(delta_encoded)
    
    # 4. 分段載入策略
    segments = split_into_segments(visible_only, segment_minutes=60)
    
    return {
        "segments": segments,
        "total_size_mb": calculate_size(segments),
        "compression_ratio": len(timeseries_data) / len(segments)
    }
```

## 6. 性能優化建議

### 6.1 預載入策略
- 初始載入：前 5 分鐘數據
- 背景載入：接下來 30 分鐘
- 循環預載：接近循環點時預載首段

### 6.2 資料結構優化
- 使用 TypedArray 存儲數值數據
- 位置使用相對編碼減少精度需求
- 時間戳使用相對秒數而非完整 ISO 字串

### 6.3 渲染優化
- 只渲染視野內的衛星
- LOD (Level of Detail) 根據距離調整
- 批量更新減少 draw call

---

**下一步**: 查看 [換手事件整合](./03-handover-events-integration.md) 了解 A4/A5/D2 事件處理