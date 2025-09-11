# 階段3：SGP4軌道計算算法

## SGP4算法數學原理和物理背景

### SGP4算法基礎概念

**SGP4 (Simplified General Perturbations 4)** 是專門為TLE數據設計的軌道預測算法。

### 算法發展歷史：
- **1960年代**：初代SGP算法開發
- **1970年代**：SGP4版本成為標準
- **1980年代**：民用開放
- **2000年代**：開源實作普及

### 核心設計理念：
- **簡化攝動理論**：平衡精度與計算速度
- **針對TLE優化**：專門處理TLE格式參數
- **批量計算**：高效處理大量衛星

### 物理背景：
- 基於開普勒軌道理論
- 考慮地球非球形效應
- 包含大氣阻力影響
- 處理太陽月球攝動

## 簡化攝動理論基礎

### 攝動力來源分析：

**主要攝動力：**
1. **地球非球形效應 (J2項)**
   - 地球扁率引起的攝動
   - 影響軌道面方向
   - 主導性攝動力

2. **大氣阻力**
   - 低軌道衛星主要衰減原因
   - 高度越低影響越大
   - 導致軌道能量損失

3. **太陽輻射壓力**
   - 影響高軌道衛星
   - 與衛星面積質量比相關
   - 週期性變化

4. **第三體引力**
   - 太陽和月球引力
   - 長週期影響
   - 高軌道更明顯

### 簡化處理策略：
- 解析解法優於數值積分
- 平均化處理短週期項
- 保留主要長週期項
- 特殊處理臨界軌道

## SGP4 vs SDP4差異分析

### 軌道分類標準：

**深空軌道判定：**
```
如果 period >= 225分鐘：使用SDP4
如果 period < 225分鐘：使用SGP4
```

### SGP4 (近地軌道)特性：
- **適用範圍**：高度 < 2000km
- **週期範圍**：85-225分鐘
- **主要攝動**：地球扁率、大氣阻力
- **計算速度**：快速
- **典型衛星**：Starlink, ISS, OneWeb

### SDP4 (深空軌道)特性：
- **適用範圍**：高度 > 2000km
- **週期範圍**：> 225分鐘
- **主要攝動**：第三體引力、共振效應
- **計算複雜**：包含長週期項
- **典型衛星**：GPS, GEO通訊衛星

### 實際應用考量：
```python
def choose_propagator(mean_motion):
    period_minutes = 1440.0 / mean_motion
    if period_minutes >= 225:
        return "SDP4"  # Deep space
    else:
        return "SGP4"  # Near earth
```

## 時間系統：Julian Day詳解

### 時間系統概念：

**為什麼需要Julian Day？**
- 天文計算標準時間
- 避免曆法轉換複雜性
- 便於時間差計算
- SGP4算法標準格式

### Julian Day定義：
- 從西元前4713年1月1日開始的連續日數
- 當前約為245xxxx天
- 包含小數部分表示一天內的時間

### TLE Epoch轉Julian Day：
```python
def tle_epoch_to_jd(epoch_year, epoch_day):
    # 處理兩位年份
    if epoch_year < 57:
        full_year = 2000 + epoch_year
    else:
        full_year = 1900 + epoch_year
    
    # 計算該年1月1日的Julian Day
    jan1_jd = julian_day(full_year, 1, 1)
    
    # 加上年中日數
    return jan1_jd + epoch_day - 1.0
```

### 時間差計算：
```python
def time_since_epoch(current_jd, epoch_jd):
    return current_jd - epoch_jd  # 單位：天
```

## 地球模型和重力場

### WGS84地球模型參數：

**基本參數：**
- **長半軸 (a)**：6378137.0 m
- **扁率 (f)**：1/298.257223563
- **重力參數 (μ)**：3.986004418 × 10¹⁴ m³/s²

### J2項攝動係數：
- **J2值**：1.08262668 × 10⁻³
- **物理意義**：地球赤道凸出效應
- **影響**：軌道面進動

### J2攝動效應計算：
```python
def j2_effects(a, ecc, inc, mean_motion):
    # J2常數
    J2 = 1.08262668e-3
    RE = 6378.137  # 地球半徑 (km)
    
    # 半長軸計算
    n = mean_motion * 2 * pi / 1440  # rad/min
    a = (mu / (n**2))**(1/3)  # km
    
    # J2效應計算
    factor = -3/2 * J2 * (RE/a)**2 * n / (1-ecc**2)**2
    
    # 升交點赤經進動率
    raan_dot = factor * cos(inc)  # rad/min
    
    # 近地點幅角進動率  
    arg_perigee_dot = factor * (2 - 2.5 * sin(inc)**2)  # rad/min
    
    return raan_dot, arg_perigee_dot
```

## 大氣阻力攝動效應

### 大氣密度模型：

**簡化指數大氣：**
```python
def atmospheric_density(altitude_km):
    # 簡化模型（實際SGP4使用更複雜的模型）
    if altitude_km > 1000:
        return 0  # 忽略高軌道大氣阻力
    
    # 參考高度密度
    h0 = [0, 25, 30, 40, 50, 60, 70, 80, 90, 100, 
          110, 120, 130, 140, 150, 180, 200, 250, 
          300, 350, 400, 450, 500, 600, 700, 800, 900, 1000]
    
    rho0 = [1.225e0, 3.899e-2, 1.774e-2, 3.972e-3, 1.057e-3,
            3.206e-4, 8.770e-5, 1.905e-5, 3.396e-6, 5.297e-7,
            9.661e-8, 2.438e-8, 8.484e-9, 3.845e-9, 2.070e-9,
            5.464e-10, 2.789e-10, 7.248e-11, 2.418e-11, 9.518e-12,
            3.725e-12, 1.585e-12, 6.967e-13, 1.454e-13, 3.614e-14,
            1.170e-14, 5.245e-15, 3.019e-15]
    
    # 線性插值
    return interpolate_density(altitude_km, h0, rho0)
```

### 拖拽力計算：
```python
def drag_acceleration(velocity, density, drag_coeff, area_mass_ratio):
    # 拖拽加速度 = -0.5 * ρ * v² * CD * (A/m)
    drag_acc = -0.5 * density * velocity**2 * drag_coeff * area_mass_ratio
    return drag_acc
```

### TLE中的B*係數：
- **定義**：B* = CD × A/m / (2 × ρ0)
- **單位**：earth radii⁻¹
- **用途**：簡化大氣阻力計算

## 地球扁率攝動修正

### J2攝動的軌道元素變化：

**長期效應（世俗項）：**
```python
def secular_effects(a, ecc, inc, raan, arg_perigee, mean_motion, t_since_epoch):
    # 計算J2係數影響
    J2 = 1.08262668e-3
    RE = 6378.137
    
    n = mean_motion * 2 * pi / 1440  # 轉換為rad/min
    factor = -3/2 * J2 * (RE/a)**2 * n / (1-ecc**2)**2
    
    # 升交點赤經變化（世俗項）
    raan_sec = factor * cos(inc) * t_since_epoch
    
    # 近地點幅角變化（世俗項）
    arg_perigee_sec = factor * (2 - 2.5 * sin(inc)**2) * t_since_epoch
    
    # 平均近點角變化
    mean_anomaly_sec = factor * sqrt(1 - ecc**2) * (1.5 * sin(inc)**2 - 1) * t_since_epoch
    
    return raan_sec, arg_perigee_sec, mean_anomaly_sec
```

**週期效應（短週期項）：**
```python
def periodic_effects(ecc, inc, u, r):
    # u = 真近點角 + 近地點幅角
    # r = 向徑
    
    # J2短週期項修正
    cos2u = cos(2 * u)
    sin2u = sin(2 * u)
    
    # 向徑修正
    delta_r = -J2 * (RE**2 / r**2) * (1 - 1.5 * sin(inc)**2) * cos2u
    
    # 緯幅修正
    delta_u = J2 * (RE**2 / r**2) * (1 - 1.5 * sin(inc)**2) * sin2u
    
    return delta_r, delta_u
```

## ⚠️ 時間基準關鍵原則

### 🚨 絕對禁止使用當前時間

**錯誤做法：**
```python
# ❌ 這是錯誤的！
current_time = datetime.now()
jd_now = datetime_to_julian(current_time)
position = sgp4(satellite, jd_now)  # 錯誤！
```

**正確做法：**
```python
# ✅ 這是正確的！
epoch_time = satellite.epoch  # 使用TLE epoch時間
time_since_epoch = 0.0  # 從epoch開始
jd_epoch = epoch_time
position = sgp4(satellite, jd_epoch)  # 正確！

# 如果要預測未來位置
minutes_ahead = 30  # 30分鐘後
jd_future = jd_epoch + minutes_ahead / 1440.0  # 轉換為天
position_future = sgp4(satellite, jd_future)
```

### 時間基準錯誤的後果：

1. **軌道偏移**：時間差每天導致軌道偏移數百公里
2. **預測失效**：無法正確預測衛星位置
3. **可見性錯誤**：地面站無法正確追蹤衛星
4. **系統故障**：整個衛星追蹤系統失效

## 🚨 8000→0顆可見案例分析

### 問題描述：
- **輸入**：8,370顆Starlink衛星TLE數據
- **期望**：計算當前可見的衛星
- **結果**：0顆衛星可見
- **狀態**：程式運行正常，無錯誤訊息

### 根本原因分析：

**錯誤時間使用：**
```python
# ❌ 錯誤的實作
def calculate_satellite_positions():
    current_time = datetime.now()  # 2025-09-11
    for satellite in satellites:
        # TLE epoch是 2025-09-05 (6天前)
        position = sgp4_propagate(satellite, current_time)
        # 結果：位置完全錯誤
```

**6天時間差的影響：**
- Starlink衛星軌道週期：~95分鐘
- 6天 = 8640分鐘
- 軌道圈數：8640 ÷ 95 ≈ 91圈
- 每圈軌道面進動：~1度
- 總偏差：91度 → 位置完全錯誤

### 正確的修復方案：

```python
# ✅ 正確的實作
def calculate_satellite_positions():
    for satellite in satellites:
        epoch_time = satellite.epoch  # 使用TLE epoch時間
        
        # 如果需要當前位置，從epoch時間推算
        now = datetime.now()
        time_diff = (now - epoch_time).total_seconds() / 60.0  # 分鐘
        
        # 使用epoch + 時間差
        jd_now = satellite.jd_epoch + time_diff / 1440.0
        position = sgp4_propagate(satellite, jd_now)
```

### 檢測機制：
```python
def validate_time_basis(tle_epoch, calculation_time):
    time_diff = abs((calculation_time - tle_epoch).days)
    if time_diff > 7:
        print(f"⚠️ 警告：時間差 {time_diff} 天，可能影響精度")
    if time_diff > 14:
        print(f"🚨 錯誤：時間差 {time_diff} 天，結果不可信")
        return False
    return True
```

## skyfield庫SGP4實作分析

### skyfield庫特色：

**專業級實作：**
- 完整的SGP4/SDP4實作
- 符合AIAA-2006-6753標準
- 高精度時間系統
- 優化的數值計算

**使用便利性：**
- 直接支援TLE格式
- 自動處理時間轉換
- 批量計算優化
- 豐富的座標系統

### 基本使用模式：

```python
from skyfield.api import load, EarthSatellite

# 載入時間尺度
ts = load.timescale()

# 創建衛星對象
satellite = EarthSatellite(line1, line2, name, ts=ts)

# 關鍵：使用epoch時間
epoch_time = satellite.epoch
times = ts.tt_jd(satellite.model.jdsatepoch)

# 計算位置
geocentric = satellite.at(times)
```

### 時間處理最佳實踐：

```python
def safe_sgp4_calculation(tle_data, prediction_minutes=0):
    """安全的SGP4計算，確保時間基準正確"""
    
    # 解析TLE數據
    satellite = EarthSatellite(
        tle_data['line1'], 
        tle_data['line2'], 
        tle_data['name'],
        ts=ts
    )
    
    # 使用TLE epoch作為基準時間
    epoch_jd = satellite.model.jdsatepoch
    
    # 生成時間序列（從epoch開始）
    time_points = []
    for i in range(prediction_minutes + 1):
        jd = epoch_jd + i / 1440.0  # 轉換分鐘為天
        time_points.append(ts.tt_jd(jd))
    
    # 批量計算位置
    positions = satellite.at(time_points)
    
    return positions
```

## EarthSatellite類別使用詳解

### EarthSatellite初始化：

```python
from skyfield.api import load, EarthSatellite

ts = load.timescale()

# 標準初始化
satellite = EarthSatellite(
    line1="1 25544U 98067A   25245.83...",
    line2="2 25544  51.6461 123.4567...",
    name="ISS",
    ts=ts
)
```

### 衛星對象屬性：

```python
# 軌道參數訪問
print(f"NORAD ID: {satellite.model.satnum}")
print(f"Inclination: {satellite.model.inclo * 180/pi:.4f}°")
print(f"Eccentricity: {satellite.model.ecco:.6f}")
print(f"Mean Motion: {satellite.model.no_kozai * 1440/(2*pi):.8f} rev/day")

# Epoch時間
print(f"Epoch: {satellite.epoch.utc_iso()}")
print(f"Julian Day: {satellite.model.jdsatepoch}")
```

### 位置計算方法：

```python
# 單點計算
time = ts.now()
geocentric = satellite.at(time)
lat, lon = geocentric.subpoint().latitude, geocentric.subpoint().longitude

# 批量計算
times = ts.linspace(satellite.epoch, satellite.epoch + 1, 96)  # 1天，15分鐘間隔
positions = satellite.at(times)
```

### 觀測者相關計算：

```python
from skyfield.api import wgs84

# 設定觀測者位置 (NTPU)
observer = wgs84.latlon(24.9441667, 121.3713889, elevation_m=50)

# 計算相對位置
difference = satellite - observer
topocentric = difference.at(times)

# 地平座標
alt, az, distance = topocentric.altaz()
```

## 批量SGP4計算優化技巧

### 向量化計算：

```python
def batch_sgp4_calculation(satellites_data, time_points):
    """批量計算多顆衛星在多個時間點的位置"""
    
    results = {}
    
    for sat_data in satellites_data:
        satellite = EarthSatellite(
            sat_data['line1'], 
            sat_data['line2'],
            sat_data['name'], 
            ts=ts
        )
        
        # 向量化時間計算
        times = ts.tt_jd([satellite.model.jdsatepoch + t/1440.0 
                         for t in time_points])
        
        # 批量位置計算
        geocentric = satellite.at(times)
        
        results[sat_data['norad_id']] = {
            'positions': geocentric.position.km,
            'velocities': geocentric.velocity.km_per_s
        }
    
    return results
```

### 記憶體優化：

```python
def memory_efficient_calculation(satellites_data, chunk_size=100):
    """記憶體高效的批量計算"""
    
    results = []
    
    # 分塊處理
    for i in range(0, len(satellites_data), chunk_size):
        chunk = satellites_data[i:i+chunk_size]
        
        chunk_results = []
        for sat_data in chunk:
            # 只計算必要的資料
            satellite = EarthSatellite(sat_data['line1'], sat_data['line2'])
            position = satellite.at(ts.tt_jd(satellite.model.jdsatepoch))
            
            # 只保存關鍵資料
            chunk_results.append({
                'norad_id': sat_data['norad_id'],
                'position': position.position.km.tolist(),
                'epoch': satellite.model.jdsatepoch
            })
        
        results.extend(chunk_results)
        
        # 清理記憶體
        del chunk_results
    
    return results
```

### 並行計算：

```python
from concurrent.futures import ThreadPoolExecutor
import multiprocessing as mp

def parallel_sgp4_calculation(satellites_data, num_workers=None):
    """並行SGP4計算"""
    
    if num_workers is None:
        num_workers = min(mp.cpu_count(), len(satellites_data))
    
    def calculate_single_satellite(sat_data):
        try:
            satellite = EarthSatellite(sat_data['line1'], sat_data['line2'])
            position = satellite.at(ts.tt_jd(satellite.model.jdsatepoch))
            return {
                'norad_id': sat_data['norad_id'],
                'success': True,
                'position': position.position.km
            }
        except Exception as e:
            return {
                'norad_id': sat_data['norad_id'],
                'success': False,
                'error': str(e)
            }
    
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        results = list(executor.map(calculate_single_satellite, satellites_data))
    
    return results
```

## 計算結果驗證方法

### 物理合理性檢查：

```python
def validate_orbital_parameters(satellite_data):
    """驗證軌道參數的物理合理性"""
    
    errors = []
    
    # 檢查軌道高度
    mean_motion = satellite_data['mean_motion']
    period_minutes = 1440.0 / mean_motion
    
    # 根據週期估算高度 (簡化公式)
    estimated_altitude = ((period_minutes / 90.0) - 1) * 420 + 420
    
    if estimated_altitude < 200:
        errors.append("軌道高度過低，可能已再入大氣層")
    elif estimated_altitude > 2000:
        errors.append("高度超出LEO範圍")
    
    # 檢查偏心率
    if satellite_data['eccentricity'] > 0.9:
        errors.append("偏心率過高，軌道可能不穩定")
    
    # 檢查軌道傾角
    inclination = satellite_data['inclination']
    if inclination > 180:
        errors.append("軌道傾角無效")
    
    return errors
```

### 數值穩定性檢查：

```python
def check_numerical_stability(positions, velocities):
    """檢查數值計算的穩定性"""
    
    # 檢查位置向量長度
    distances = [np.linalg.norm(pos) for pos in positions]
    
    if any(d < 6000 or d > 8000 for d in distances):  # km
        print("⚠️ 警告：軌道半徑異常")
    
    # 檢查速度大小
    speeds = [np.linalg.norm(vel) for vel in velocities]
    
    if any(s < 6 or s > 9 for s in speeds):  # km/s
        print("⚠️ 警告：軌道速度異常")
    
    # 檢查角動量守恆
    angular_momenta = [np.cross(pos, vel) for pos, vel in zip(positions, velocities)]
    h_magnitudes = [np.linalg.norm(h) for h in angular_momenta]
    
    h_variation = (max(h_magnitudes) - min(h_magnitudes)) / np.mean(h_magnitudes)
    if h_variation > 0.01:  # 1%
        print("⚠️ 警告：角動量不守恆，可能數值誤差過大")
```

### 與參考數據比較：

```python
def compare_with_reference(calculated_position, reference_position, tolerance_km=10):
    """與參考數據比較驗證"""
    
    distance_error = np.linalg.norm(
        np.array(calculated_position) - np.array(reference_position)
    )
    
    if distance_error > tolerance_km:
        print(f"⚠️ 位置誤差 {distance_error:.2f} km 超出容許範圍")
        return False
    else:
        print(f"✅ 位置誤差 {distance_error:.2f} km 在容許範圍內")
        return True
```

## SGP4計算異常處理和錯誤恢復

### 常見異常類型：

```python
def robust_sgp4_calculation(satellite_data):
    """穩健的SGP4計算，包含完整錯誤處理"""
    
    try:
        satellite = EarthSatellite(
            satellite_data['line1'],
            satellite_data['line2'],
            satellite_data['name']
        )
        
        # 檢查TLE時效性
        days_old = (datetime.now() - satellite.epoch.utc_datetime()).days
        if days_old > 14:
            print(f"⚠️ TLE數據已 {days_old} 天，精度可能降低")
        
        # 計算位置
        position = satellite.at(ts.tt_jd(satellite.model.jdsatepoch))
        
        return {
            'success': True,
            'position': position.position.km,
            'velocity': position.velocity.km_per_s,
            'epoch': satellite.epoch.utc_iso()
        }
        
    except ValueError as e:
        if "checksum" in str(e).lower():
            return {'success': False, 'error': 'TLE校驗和錯誤'}
        elif "format" in str(e).lower():
            return {'success': False, 'error': 'TLE格式錯誤'}
        else:
            return {'success': False, 'error': f'數值錯誤: {e}'}
    
    except Exception as e:
        return {'success': False, 'error': f'未知錯誤: {e}'}
```

### 錯誤恢復策略：

```python
def calculate_with_fallback(satellite_data, max_retries=3):
    """帶降級策略的SGP4計算"""
    
    for attempt in range(max_retries):
        try:
            result = robust_sgp4_calculation(satellite_data)
            if result['success']:
                return result
        except Exception as e:
            print(f"嘗試 {attempt + 1} 失敗: {e}")
            
            if attempt < max_retries - 1:
                # 嘗試修復策略
                if "checksum" in str(e):
                    # 嘗試修復校驗和
                    satellite_data = fix_checksum(satellite_data)
                elif "format" in str(e):
                    # 嘗試格式修復
                    satellite_data = fix_format(satellite_data)
    
    # 所有嘗試失敗
    return {'success': False, 'error': '無法完成計算'}
```

## 完整SGP4計算函數實作

### 生產級SGP4計算器：

```python
class ProductionSGP4Calculator:
    """生產級SGP4軌道計算器"""
    
    def __init__(self, observer_lat=24.9441667, observer_lon=121.3713889):
        self.observer_lat = observer_lat
        self.observer_lon = observer_lon
        self.ts = load.timescale()
        self.observer = wgs84.latlon(observer_lat, observer_lon)
        
        # 統計資料
        self.stats = {
            'total_calculations': 0,
            'successful_calculations': 0,
            'failed_calculations': 0,
            'average_calculation_time': 0.0
        }
    
    def calculate_satellite_orbit(self, tle_data, time_points=192, interval_minutes=30):
        """計算完整的衛星軌道"""
        
        start_time = time.time()
        
        try:
            # 創建衛星對象
            satellite = EarthSatellite(
                tle_data['line1'],
                tle_data['line2'], 
                tle_data['name'],
                ts=self.ts
            )
            
            # 🚨 關鍵：使用TLE epoch時間作為基準
            epoch_jd = satellite.model.jdsatepoch
            
            # 生成時間序列
            time_offsets = [i * interval_minutes / 1440.0 for i in range(time_points)]
            times = self.ts.tt_jd([epoch_jd + offset for offset in time_offsets])
            
            # 批量計算位置
            geocentric = satellite.at(times)
            
            # 計算觀測參數
            difference = satellite - self.observer
            topocentric = difference.at(times)
            alt, az, distance = topocentric.altaz()
            
            # 格式化結果
            result = self._format_orbit_data(
                satellite, times, geocentric, alt, az, distance, tle_data
            )
            
            # 更新統計
            calculation_time = time.time() - start_time
            self.stats['successful_calculations'] += 1
            self.stats['average_calculation_time'] = (
                (self.stats['average_calculation_time'] * (self.stats['successful_calculations'] - 1) +
                 calculation_time) / self.stats['successful_calculations']
            )
            
            return result
            
        except Exception as e:
            self.stats['failed_calculations'] += 1
            return {
                'success': False,
                'error': str(e),
                'satellite_name': tle_data.get('name', 'Unknown')
            }
        finally:
            self.stats['total_calculations'] += 1
    
    def _format_orbit_data(self, satellite, times, geocentric, alt, az, distance, tle_data):
        """格式化軌道計算結果"""
        
        positions = geocentric.position.km
        velocities = geocentric.velocity.km_per_s
        
        # 計算地理座標
        subpoints = geocentric.subpoint()
        
        orbit_data = {
            'success': True,
            'satellite_info': {
                'name': tle_data['name'],
                'norad_id': satellite.model.satnum,
                'epoch': satellite.epoch.utc_iso()
            },
            'orbital_elements': {
                'inclination_deg': satellite.model.inclo * 180 / pi,
                'eccentricity': satellite.model.ecco,
                'mean_motion_rev_day': satellite.model.no_kozai * 1440 / (2*pi),
                'period_minutes': 1440 / (satellite.model.no_kozai * 1440 / (2*pi))
            },
            'positions': []
        }
        
        # 格式化每個時間點的數據
        for i in range(len(times)):
            point_data = {
                'time_utc': times[i].utc_iso(),
                'position_eci_km': {
                    'x': float(positions[0][i]),
                    'y': float(positions[1][i]), 
                    'z': float(positions[2][i])
                },
                'velocity_eci_km_s': {
                    'vx': float(velocities[0][i]),
                    'vy': float(velocities[1][i]),
                    'vz': float(velocities[2][i])
                },
                'geographic': {
                    'latitude_deg': float(subpoints.latitude.degrees[i]),
                    'longitude_deg': float(subpoints.longitude.degrees[i]),
                    'altitude_km': float(subpoints.elevation.km[i])
                },
                'observer_view': {
                    'elevation_deg': float(alt.degrees[i]),
                    'azimuth_deg': float(az.degrees[i]),
                    'range_km': float(distance.km[i]),
                    'is_visible': float(alt.degrees[i]) > 0
                }
            }
            orbit_data['positions'].append(point_data)
        
        return orbit_data
    
    def get_statistics(self):
        """獲取計算統計資料"""
        if self.stats['total_calculations'] > 0:
            success_rate = (self.stats['successful_calculations'] / 
                          self.stats['total_calculations']) * 100
            return {
                **self.stats,
                'success_rate_percent': success_rate
            }
        return self.stats
```

## 階段總結

### 階段3學習成果確認：

**核心理論掌握：**
- SGP4算法的數學原理和物理背景
- 簡化攝動理論的基本概念
- 時間系統和Julian Day處理
- 地球模型和J2攝動效應
- 大氣阻力模型和拖拽計算

**關鍵原則理解：**
- ⚠️ **時間基準絕對原則**：必須使用TLE epoch時間
- 🚨 **8000→0顆案例教訓**：時間基準錯誤的嚴重後果
- ✅ **正確時間處理**：從epoch開始計算的方法

**實作技能獲得：**
- skyfield庫的專業使用方法
- EarthSatellite類別的完整操作
- 批量SGP4計算優化技巧
- 並行計算和記憶體優化
- 完整的錯誤處理和驗證機制

**生產級技能：**
- 數值穩定性檢查方法
- 物理合理性驗證算法
- 異常處理和錯誤恢復策略
- 完整的統計和監控機制

**下一步行動計劃：**
- 進入階段4：座標系統和轉換實作
- 學習ECI/ECEF/地理座標轉換
- 實作觀測者相關計算
- 掌握可見性判斷算法

**⚠️ 絕對重要提醒：**
**永遠記住時間基準原則：SGP4計算必須使用TLE epoch時間作為基準，絕對不能使用當前系統時間！**