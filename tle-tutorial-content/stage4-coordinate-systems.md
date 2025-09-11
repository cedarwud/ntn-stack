# 階段4：座標系統和轉換實作

## 座標系統概論

### 為什麼需要多種座標系統？

**不同應用需求：**
- **SGP4計算**：使用ECI座標系統
- **地面追蹤**：需要地理座標系統
- **觀測計算**：使用地平座標系統
- **GPS定位**：採用ECEF座標系統

**物理考量：**
- 地球自轉效應
- 觀測者位置影響
- 計算效率需求
- 精度要求差異

### 座標系統分類：

1. **慣性座標系** - 相對恆星固定
2. **地固座標系** - 隨地球旋轉
3. **地理座標系** - 人類直觀理解
4. **觀測座標系** - 觀測者視角

## ECI座標系統詳解

### ECI (Earth-Centered Inertial) 基本概念

**定義：**
- 原點：地球質心
- Z軸：指向地球北極
- X軸：指向春分點方向
- Y軸：完成右手座標系

**特性：**
- 慣性座標系（相對恆星固定）
- SGP4計算的標準輸出
- 不隨地球自轉變化
- 天文計算的基準

### ECI座標系的物理意義：

```python
def eci_coordinates_explanation():
    """ECI座標系統說明"""
    
    print("ECI座標系統特性：")
    print("• 原點：地球質心")
    print("• X軸：指向J2000.0春分點")
    print("• Y軸：在赤道面內，垂直於X軸") 
    print("• Z軸：指向地球北極")
    print("• 單位：通常使用公里(km)")
    
    # 典型的ECI座標範例
    starlink_eci = {
        'x': -2194.36,  # km
        'y': -4581.12,  # km  
        'z': 4525.89    # km
    }
    
    # 計算距離地心距離
    distance = np.sqrt(starlink_eci['x']**2 + 
                      starlink_eci['y']**2 + 
                      starlink_eci['z']**2)
    
    print(f"\n範例Starlink衛星ECI位置：")
    print(f"X: {starlink_eci['x']:.2f} km")
    print(f"Y: {starlink_eci['y']:.2f} km") 
    print(f"Z: {starlink_eci['z']:.2f} km")
    print(f"距地心距離: {distance:.2f} km")
    print(f"軌道高度: ~{distance-6371:.0f} km")
```

### ECI座標系統的時間考量：

**歲差效應：**
- 地球自轉軸緩慢進動
- 周期約26,000年
- 春分點位置變化
- 需要歷元校正

**常用歷元：**
- **J2000.0** - 2000年1月1日12:00 TT
- **當前歷元** - 觀測時刻
- **TLE歷元** - TLE數據的參考時刻

## ECEF座標系統原理

### ECEF (Earth-Centered, Earth-Fixed) 基本概念

**定義：**
- 原點：地球質心
- Z軸：指向地球北極（與ECI相同）
- X軸：指向0°經線與赤道交點
- Y軸：指向90°E經線與赤道交點

**特性：**
- 地固座標系（隨地球旋轉）
- GPS系統使用標準
- 方便地面應用
- 與ECI通過旋轉矩陣轉換

### ECEF座標系統實際應用：

```python
import numpy as np
from datetime import datetime

def eci_to_ecef(eci_position, julian_date):
    """ECI到ECEF座標轉換"""
    
    # 計算格林威治恆星時
    gst = calculate_greenwich_sidereal_time(julian_date)
    
    # 旋轉矩陣 (繞Z軸旋轉)
    cos_gst = np.cos(gst)
    sin_gst = np.sin(gst)
    
    rotation_matrix = np.array([
        [ cos_gst, sin_gst, 0],
        [-sin_gst, cos_gst, 0], 
        [       0,       0, 1]
    ])
    
    # 矩陣乘法轉換
    eci_vec = np.array([eci_position['x'], eci_position['y'], eci_position['z']])
    ecef_vec = rotation_matrix @ eci_vec
    
    return {
        'x': ecef_vec[0],
        'y': ecef_vec[1], 
        'z': ecef_vec[2]
    }

def calculate_greenwich_sidereal_time(julian_date):
    """計算格林威治恆星時"""
    
    # 從J2000.0開始的儒略世紀數
    T = (julian_date - 2451545.0) / 36525.0
    
    # 格林威治平恆星時 (度)
    gst_degrees = 280.46061837 + 360.98564736629 * (julian_date - 2451545.0) + \
                  0.000387933 * T**2 - T**3 / 38710000.0
    
    # 轉換為弧度
    gst_radians = np.radians(gst_degrees % 360)
    
    return gst_radians
```

### 地球自轉效應考慮：

```python
def earth_rotation_effect_demo():
    """展示地球自轉對座標轉換的影響"""
    
    # 固定的ECI位置
    eci_pos = {'x': 6700.0, 'y': 0.0, 'z': 0.0}  # 赤道上空
    
    print("地球自轉對ECEF座標的影響：")
    print("ECI位置固定在 (6700, 0, 0) km\n")
    
    # 不同時間的ECEF座標
    base_jd = 2459945.0  # 某個基準日期
    
    for hours in [0, 6, 12, 18]:
        jd = base_jd + hours / 24.0
        ecef_pos = eci_to_ecef(eci_pos, jd)
        
        print(f"時間: +{hours:2d}小時")
        print(f"ECEF: ({ecef_pos['x']:7.1f}, {ecef_pos['y']:7.1f}, {ecef_pos['z']:7.1f})")
        
        # 計算地理位置
        lat, lon = ecef_to_geographic(ecef_pos)
        print(f"地理: ({lat:.1f}°N, {lon:.1f}°E)\n")
```

## 地理座標系統 (WGS84)

### WGS84橢球體參數

**標準參數：**
```python
class WGS84Constants:
    """WGS84橢球體常數"""
    
    # 長半軸
    A = 6378137.0  # 公尺
    
    # 扁率
    F = 1.0 / 298.257223563
    
    # 第一偏心率平方
    E2 = F * (2 - F)
    
    # 短半軸  
    B = A * (1 - F)
    
    # 重力參數
    GM = 3.986004418e14  # m³/s²
```

### ECEF到地理座標轉換

**Bowring算法實作：**
```python
def ecef_to_geographic(ecef_pos):
    """ECEF座標轉換為地理座標 (WGS84)"""
    
    x, y, z = ecef_pos['x'] * 1000, ecef_pos['y'] * 1000, ecef_pos['z'] * 1000  # 轉換為公尺
    
    # 計算經度 (簡單)
    longitude = np.arctan2(y, x)
    
    # 計算緯度和高度 (迭代法)
    p = np.sqrt(x**2 + y**2)
    
    # 初始猜測
    lat = np.arctan2(z, p * (1 - WGS84Constants.E2))
    
    # 迭代計算緯度
    for _ in range(5):  # 通常5次迭代足夠
        N = WGS84Constants.A / np.sqrt(1 - WGS84Constants.E2 * np.sin(lat)**2)
        h = p / np.cos(lat) - N
        lat = np.arctan2(z, p * (1 - WGS84Constants.E2 * N / (N + h)))
    
    # 最終高度計算
    N = WGS84Constants.A / np.sqrt(1 - WGS84Constants.E2 * np.sin(lat)**2)
    altitude = p / np.cos(lat) - N
    
    return {
        'latitude_deg': np.degrees(lat),
        'longitude_deg': np.degrees(longitude),
        'altitude_m': altitude
    }
```

### 地理座標到ECEF轉換

```python
def geographic_to_ecef(lat_deg, lon_deg, alt_m):
    """地理座標轉換為ECEF座標"""
    
    lat = np.radians(lat_deg)
    lon = np.radians(lon_deg)
    
    # 主曲率半徑
    N = WGS84Constants.A / np.sqrt(1 - WGS84Constants.E2 * np.sin(lat)**2)
    
    # ECEF座標計算
    x = (N + alt_m) * np.cos(lat) * np.cos(lon)
    y = (N + alt_m) * np.cos(lat) * np.sin(lon)
    z = (N * (1 - WGS84Constants.E2) + alt_m) * np.sin(lat)
    
    return {
        'x': x / 1000,  # 轉換為公里
        'y': y / 1000,
        'z': z / 1000
    }
```

## 座標轉換數學公式推導

### ECI到地理座標完整轉換

```python
def eci_to_geographic_complete(eci_pos, julian_date):
    """ECI直接轉換為地理座標的完整實作"""
    
    # 步驟1: ECI → ECEF
    ecef_pos = eci_to_ecef(eci_pos, julian_date)
    
    # 步驟2: ECEF → 地理座標
    geo_pos = ecef_to_geographic(ecef_pos)
    
    return geo_pos

def validate_coordinate_conversion():
    """驗證座標轉換的正確性"""
    
    # 測試已知位置 (台北101)
    taipei_101 = {
        'latitude_deg': 25.0340,
        'longitude_deg': 121.5645, 
        'altitude_m': 500
    }
    
    # 地理 → ECEF → 地理 (往返測試)
    ecef = geographic_to_ecef(**taipei_101)
    geo_back = ecef_to_geographic(ecef)
    
    # 計算誤差
    lat_error = abs(taipei_101['latitude_deg'] - geo_back['latitude_deg'])
    lon_error = abs(taipei_101['longitude_deg'] - geo_back['longitude_deg'])
    alt_error = abs(taipei_101['altitude_m'] - geo_back['altitude_m'])
    
    print("座標轉換精度驗證：")
    print(f"緯度誤差: {lat_error:.8f}°")
    print(f"經度誤差: {lon_error:.8f}°")  
    print(f"高度誤差: {alt_error:.2f}m")
    
    if lat_error < 1e-6 and lon_error < 1e-6 and alt_error < 0.1:
        print("✅ 座標轉換精度符合要求")
    else:
        print("❌ 座標轉換精度不足")
```

## 觀測者位置和地平座標系統

### 地平座標系統定義

**地平座標系統：**
- **原點**：觀測者位置
- **水平面**：觀測者所在地的切平面
- **方位角**：從北方順時針測量的角度
- **仰角**：從水平面向上測量的角度

### 觀測者位置設定

```python
class Observer:
    """觀測者類別"""
    
    def __init__(self, latitude_deg, longitude_deg, altitude_m=0):
        self.latitude_deg = latitude_deg
        self.longitude_deg = longitude_deg
        self.altitude_m = altitude_m
        
        # 轉換為弧度
        self.latitude_rad = np.radians(latitude_deg)
        self.longitude_rad = np.radians(longitude_deg)
        
        # 計算ECEF位置
        self.ecef_position = geographic_to_ecef(latitude_deg, longitude_deg, altitude_m)
        
        print(f"觀測者位置: ({latitude_deg:.6f}°N, {longitude_deg:.6f}°E, {altitude_m}m)")
        
    def get_local_frame_matrix(self):
        """獲取當地座標系轉換矩陣"""
        
        lat = self.latitude_rad
        lon = self.longitude_rad
        
        # 當地座標系轉換矩陣 (ECEF → ENU)
        # E: East, N: North, U: Up
        
        transform_matrix = np.array([
            [-np.sin(lon),                np.cos(lon),               0],
            [-np.cos(lon)*np.sin(lat), -np.sin(lon)*np.sin(lat), np.cos(lat)],
            [ np.cos(lon)*np.cos(lat),  np.sin(lon)*np.cos(lat), np.sin(lat)]
        ])
        
        return transform_matrix

# 設定觀測者 (NTPU)
ntpu_observer = Observer(24.9441667, 121.3713889, 50)
```

### 衛星相對觀測者位置計算

```python
def calculate_satellite_relative_position(satellite_ecef, observer):
    """計算衛星相對於觀測者的位置"""
    
    # 相對位置向量 (ECEF座標)
    relative_ecef = {
        'x': satellite_ecef['x'] - observer.ecef_position['x'],
        'y': satellite_ecef['y'] - observer.ecef_position['y'],
        'z': satellite_ecef['z'] - observer.ecef_position['z']
    }
    
    # 轉換為當地座標系 (ENU)
    transform_matrix = observer.get_local_frame_matrix()
    relative_vector = np.array([relative_ecef['x'], relative_ecef['y'], relative_ecef['z']])
    enu_vector = transform_matrix @ relative_vector
    
    return {
        'east_km': enu_vector[0],
        'north_km': enu_vector[1], 
        'up_km': enu_vector[2]
    }
```

## 仰角和方位角計算

### 地平座標計算實作

```python
def calculate_azimuth_elevation(satellite_ecef, observer, julian_date):
    """計算衛星的方位角和仰角"""
    
    # 計算相對位置
    relative_pos = calculate_satellite_relative_position(satellite_ecef, observer)
    
    # 提取ENU分量
    east = relative_pos['east_km']
    north = relative_pos['north_km']
    up = relative_pos['up_km']
    
    # 距離計算
    range_km = np.sqrt(east**2 + north**2 + up**2)
    horizontal_distance = np.sqrt(east**2 + north**2)
    
    # 方位角計算 (從北方順時針)
    azimuth_rad = np.arctan2(east, north)
    azimuth_deg = np.degrees(azimuth_rad)
    if azimuth_deg < 0:
        azimuth_deg += 360  # 確保0-360度範圍
    
    # 仰角計算
    elevation_rad = np.arctan2(up, horizontal_distance)
    elevation_deg = np.degrees(elevation_rad)
    
    return {
        'azimuth_deg': azimuth_deg,
        'elevation_deg': elevation_deg,
        'range_km': range_km
    }
```

### 實際計算範例

```python
def satellite_observation_example():
    """衛星觀測計算完整範例"""
    
    # 設定觀測者 (NTPU)
    observer = Observer(24.9441667, 121.3713889, 50)
    
    # 模擬Starlink衛星位置 (ECI)
    starlink_eci = {
        'x': -2194.36,
        'y': -4581.12, 
        'z': 4525.89
    }
    
    # 當前時間 (儒略日)
    jd_now = 2459945.5  # 範例日期
    
    print("🛰️ 衛星觀測計算範例\n")
    
    # 步驟1: ECI → ECEF
    satellite_ecef = eci_to_ecef(starlink_eci, jd_now)
    print("步驟1 - ECEF座標:")
    print(f"  X: {satellite_ecef['x']:.2f} km")
    print(f"  Y: {satellite_ecef['y']:.2f} km")
    print(f"  Z: {satellite_ecef['z']:.2f} km\n")
    
    # 步驟2: ECEF → 地理座標
    satellite_geo = ecef_to_geographic(satellite_ecef)
    print("步驟2 - 地理座標:")
    print(f"  緯度: {satellite_geo['latitude_deg']:.4f}°")
    print(f"  經度: {satellite_geo['longitude_deg']:.4f}°")
    print(f"  高度: {satellite_geo['altitude_m']/1000:.1f} km\n")
    
    # 步驟3: 計算觀測參數
    observation = calculate_azimuth_elevation(satellite_ecef, observer, jd_now)
    print("步驟3 - 觀測參數:")
    print(f"  方位角: {observation['azimuth_deg']:.1f}°")
    print(f"  仰角: {observation['elevation_deg']:.1f}°")
    print(f"  距離: {observation['range_km']:.1f} km\n")
    
    # 可見性判斷
    is_visible = observation['elevation_deg'] > 0
    print(f"可見性: {'✅ 可見' if is_visible else '❌ 不可見'}")
    
    if is_visible:
        print(f"觀測建議: 朝{get_direction_name(observation['azimuth_deg'])}方向")
        print(f"仰角: {observation['elevation_deg']:.1f}度")

def get_direction_name(azimuth_deg):
    """將方位角轉換為方向名稱"""
    directions = [
        (0, 22.5, "北"), (22.5, 67.5, "東北"), (67.5, 112.5, "東"),
        (112.5, 157.5, "東南"), (157.5, 202.5, "南"), (202.5, 247.5, "西南"),
        (247.5, 292.5, "西"), (292.5, 337.5, "西北"), (337.5, 360, "北")
    ]
    
    for start, end, name in directions:
        if start <= azimuth_deg < end:
            return name
    return "北"
```

## 可見性判斷算法

### 基本可見性判斷

```python
def basic_visibility_check(elevation_deg, min_elevation=0):
    """基本可見性判斷"""
    return elevation_deg > min_elevation

def advanced_visibility_check(satellite_ecef, observer, julian_date, 
                            min_elevation=0, check_eclipse=True):
    """進階可見性判斷"""
    
    # 基本幾何可見性
    observation = calculate_azimuth_elevation(satellite_ecef, observer, julian_date)
    is_above_horizon = observation['elevation_deg'] > min_elevation
    
    if not is_above_horizon:
        return {
            'is_visible': False,
            'reason': 'below_horizon',
            'elevation_deg': observation['elevation_deg']
        }
    
    # 地球陰影檢查
    if check_eclipse:
        is_in_eclipse = check_earth_shadow(satellite_ecef, julian_date)
        if is_in_eclipse:
            return {
                'is_visible': False,
                'reason': 'earth_shadow',
                'elevation_deg': observation['elevation_deg']
            }
    
    return {
        'is_visible': True,
        'elevation_deg': observation['elevation_deg'],
        'azimuth_deg': observation['azimuth_deg'],
        'range_km': observation['range_km']
    }
```

### 地球陰影計算

```python
def check_earth_shadow(satellite_ecef, julian_date):
    """檢查衛星是否在地球陰影中"""
    
    # 太陽位置計算 (簡化)
    sun_position = calculate_sun_position(julian_date)
    
    # 衛星位置向量
    sat_vector = np.array([satellite_ecef['x'], satellite_ecef['y'], satellite_ecef['z']])
    sat_distance = np.linalg.norm(sat_vector)
    
    # 太陽方向向量 (假設太陽在無限遠)
    sun_direction = np.array([sun_position['x'], sun_position['y'], sun_position['z']])
    sun_direction = sun_direction / np.linalg.norm(sun_direction)
    
    # 衛星到地心的投影
    projection_length = np.dot(sat_vector, -sun_direction)
    
    if projection_length <= 0:
        return False  # 衛星在日照面
    
    # 計算陰影半徑
    earth_radius = 6371.0  # km
    shadow_radius = earth_radius * projection_length / sat_distance
    
    # 計算衛星到陰影軸的距離
    shadow_axis_vector = -sun_direction * projection_length
    lateral_vector = sat_vector - shadow_axis_vector
    lateral_distance = np.linalg.norm(lateral_vector)
    
    # 判斷是否在陰影中
    return lateral_distance < shadow_radius

def calculate_sun_position(julian_date):
    """計算太陽位置 (簡化模型)"""
    
    # 從J2000.0開始的日數
    n = julian_date - 2451545.0
    
    # 太陽平經度
    L = np.radians(280.460 + 0.9856474 * n)
    
    # 近日點平近點角
    g = np.radians(357.528 + 0.9856003 * n)
    
    # 黃道經度
    lambda_sun = L + np.radians(1.915) * np.sin(g) + np.radians(0.020) * np.sin(2*g)
    
    # 轉換為直角座標 (天文單位)
    AU = 149597870.7  # km
    x = AU * np.cos(lambda_sun)
    y = AU * np.sin(lambda_sun) * np.cos(np.radians(23.44))  # 黃道傾角
    z = AU * np.sin(lambda_sun) * np.sin(np.radians(23.44))
    
    return {'x': x, 'y': y, 'z': z}
```

## 座標轉換完整Python程式碼

### 完整的座標轉換類別

```python
class CoordinateTransformer:
    """完整的座標轉換工具類別"""
    
    def __init__(self):
        self.wgs84 = WGS84Constants()
        
    def eci_to_geographic(self, eci_pos, julian_date):
        """ECI → 地理座標的完整轉換"""
        ecef_pos = self.eci_to_ecef(eci_pos, julian_date)
        return self.ecef_to_geographic(ecef_pos)
    
    def eci_to_ecef(self, eci_pos, julian_date):
        """ECI → ECEF座標轉換"""
        gst = self._calculate_gst(julian_date)
        cos_gst, sin_gst = np.cos(gst), np.sin(gst)
        
        rotation_matrix = np.array([
            [ cos_gst, sin_gst, 0],
            [-sin_gst, cos_gst, 0],
            [       0,       0, 1]
        ])
        
        eci_vector = np.array([eci_pos['x'], eci_pos['y'], eci_pos['z']])
        ecef_vector = rotation_matrix @ eci_vector
        
        return {'x': ecef_vector[0], 'y': ecef_vector[1], 'z': ecef_vector[2]}
    
    def ecef_to_geographic(self, ecef_pos):
        """ECEF → 地理座標轉換 (高精度Bowring算法)"""
        x, y, z = ecef_pos['x'] * 1000, ecef_pos['y'] * 1000, ecef_pos['z'] * 1000
        
        longitude = np.arctan2(y, x)
        p = np.sqrt(x**2 + y**2)
        
        # 迭代求解緯度
        latitude = np.arctan2(z, p * (1 - self.wgs84.E2))
        
        for _ in range(5):
            N = self.wgs84.A / np.sqrt(1 - self.wgs84.E2 * np.sin(latitude)**2)
            altitude = p / np.cos(latitude) - N
            latitude = np.arctan2(z, p * (1 - self.wgs84.E2 * N / (N + altitude)))
        
        N = self.wgs84.A / np.sqrt(1 - self.wgs84.E2 * np.sin(latitude)**2)
        altitude = p / np.cos(latitude) - N
        
        return {
            'latitude_deg': np.degrees(latitude),
            'longitude_deg': np.degrees(longitude),
            'altitude_m': altitude
        }
    
    def calculate_observation_parameters(self, satellite_eci, observer, julian_date):
        """計算完整的觀測參數"""
        
        # 座標轉換
        satellite_ecef = self.eci_to_ecef(satellite_eci, julian_date)
        satellite_geo = self.ecef_to_geographic(satellite_ecef)
        
        # 觀測參數計算
        observation = calculate_azimuth_elevation(satellite_ecef, observer, julian_date)
        
        # 可見性判斷
        visibility = advanced_visibility_check(satellite_ecef, observer, julian_date)
        
        return {
            'satellite_position': {
                'eci': satellite_eci,
                'ecef': satellite_ecef,
                'geographic': satellite_geo
            },
            'observation': observation,
            'visibility': visibility
        }
    
    def _calculate_gst(self, julian_date):
        """計算格林威治恆星時"""
        T = (julian_date - 2451545.0) / 36525.0
        gst_degrees = 280.46061837 + 360.98564736629 * (julian_date - 2451545.0) + \
                     0.000387933 * T**2 - T**3 / 38710000.0
        return np.radians(gst_degrees % 360)
    
    def batch_coordinate_conversion(self, satellites_eci, julian_date, observer):
        """批量座標轉換"""
        results = []
        
        for satellite_eci in satellites_eci:
            result = self.calculate_observation_parameters(satellite_eci, observer, julian_date)
            results.append(result)
        
        return results

# 使用範例
def coordinate_system_demo():
    """座標系統轉換完整演示"""
    
    print("🌍 座標系統轉換完整演示\n")
    
    # 初始化轉換器和觀測者
    transformer = CoordinateTransformer()
    observer = Observer(24.9441667, 121.3713889, 50)  # NTPU
    
    # 模擬衛星位置
    satellites_eci = [
        {'x': -2194.36, 'y': -4581.12, 'z': 4525.89, 'name': 'STARLINK-1008'},
        {'x': 3194.56, 'y': 2581.34, 'z': -5525.67, 'name': 'STARLINK-2045'}
    ]
    
    julian_date = 2459945.5
    
    # 批量轉換
    results = transformer.batch_coordinate_conversion(satellites_eci, julian_date, observer)
    
    # 輸出結果
    for i, result in enumerate(results):
        sat_name = satellites_eci[i]['name']
        print(f"📡 {sat_name}")
        print(f"地理位置: {result['satellite_position']['geographic']['latitude_deg']:.2f}°N, "
              f"{result['satellite_position']['geographic']['longitude_deg']:.2f}°E, "
              f"{result['satellite_position']['geographic']['altitude_m']/1000:.1f}km")
        print(f"觀測參數: 方位{result['observation']['azimuth_deg']:.1f}°, "
              f"仰角{result['observation']['elevation_deg']:.1f}°")
        print(f"可見性: {'✅ 可見' if result['visibility']['is_visible'] else '❌ 不可見'}\n")
```

## 座標轉換精度和數值穩定性

### 精度測試和驗證

```python
def coordinate_precision_test():
    """座標轉換精度測試"""
    
    transformer = CoordinateTransformer()
    
    # 測試案例：已知精確位置
    test_cases = [
        {'lat': 0.0, 'lon': 0.0, 'alt': 0, 'name': '赤道-本初子午線'},
        {'lat': 90.0, 'lon': 0.0, 'alt': 0, 'name': '北極'},
        {'lat': -90.0, 'lon': 0.0, 'alt': 0, 'name': '南極'},
        {'lat': 25.0340, 'lon': 121.5645, 'alt': 500, 'name': '台北101'},
        {'lat': 40.7589, 'lon': -73.9851, 'alt': 100, 'name': '時代廣場'}
    ]
    
    print("座標轉換精度測試：\n")
    
    for test_case in test_cases:
        original_geo = {
            'latitude_deg': test_case['lat'],
            'longitude_deg': test_case['lon'], 
            'altitude_m': test_case['alt']
        }
        
        # 地理 → ECEF → 地理 (往返測試)
        ecef = geographic_to_ecef(test_case['lat'], test_case['lon'], test_case['alt'])
        recovered_geo = transformer.ecef_to_geographic(ecef)
        
        # 計算誤差
        lat_error = abs(original_geo['latitude_deg'] - recovered_geo['latitude_deg'])
        lon_error = abs(original_geo['longitude_deg'] - recovered_geo['longitude_deg'])
        alt_error = abs(original_geo['altitude_m'] - recovered_geo['altitude_m'])
        
        print(f"測試點: {test_case['name']}")
        print(f"緯度誤差: {lat_error:.10f}° ({lat_error*111319:.6f}m)")
        print(f"經度誤差: {lon_error:.10f}° ({lon_error*111319*np.cos(np.radians(test_case['lat'])):.6f}m)")
        print(f"高度誤差: {alt_error:.6f}m")
        
        # 精度判斷
        position_error_m = max(lat_error*111319, 
                              lon_error*111319*np.cos(np.radians(test_case['lat'])),
                              alt_error)
        
        if position_error_m < 0.001:  # 1mm
            print("✅ 精度優秀 (<1mm)")
        elif position_error_m < 0.01:  # 1cm  
            print("✅ 精度良好 (<1cm)")
        elif position_error_m < 0.1:   # 10cm
            print("⚠️ 精度尚可 (<10cm)")
        else:
            print("❌ 精度不足 (>10cm)")
        print()
```

### 數值穩定性考量

```python
def numerical_stability_analysis():
    """數值穩定性分析"""
    
    print("數值穩定性分析：\n")
    
    # 測試極端情況
    extreme_cases = [
        {'x': 1e-10, 'y': 1e-10, 'z': 6371, 'case': '極小水平分量'},
        {'x': 6371, 'y': 1e-10, 'z': 1e-10, 'case': '極小垂直分量'},  
        {'x': 42164, 'y': 0, 'z': 0, 'case': '地球同步高度'},
        {'x': 100000, 'y': 100000, 'z': 100000, 'case': '極高軌道'}
    ]
    
    transformer = CoordinateTransformer()
    
    for case in extreme_cases:
        ecef_pos = {'x': case['x'], 'y': case['y'], 'z': case['z']}
        
        try:
            geo_pos = transformer.ecef_to_geographic(ecef_pos)
            distance = np.sqrt(case['x']**2 + case['y']**2 + case['z']**2)
            
            print(f"測試案例: {case['case']}")
            print(f"ECEF: ({case['x']:.1f}, {case['y']:.1f}, {case['z']:.1f}) km")
            print(f"地心距離: {distance:.1f} km")
            print(f"地理座標: ({geo_pos['latitude_deg']:.6f}°, {geo_pos['longitude_deg']:.6f}°, {geo_pos['altitude_m']/1000:.1f}km)")
            print("✅ 計算成功\n")
            
        except Exception as e:
            print(f"測試案例: {case['case']}")
            print(f"❌ 計算失敗: {e}\n")
```

## 階段總結

### 階段4學習成果確認：

**座標系統理論掌握：**
- ECI/ECEF/地理座標系統的定義和特性
- 不同座標系統的適用場景和轉換原理
- 地球自轉對座標轉換的影響
- WGS84橢球體模型和參數

**數學轉換技能：**
- ECI到ECEF的旋轉矩陣轉換
- ECEF到地理座標的Bowring算法
- 格林威治恆星時的精確計算
- 觀測者當地座標系的建立

**觀測計算實作：**
- 方位角和仰角的精確計算
- 衛星可見性判斷算法
- 地球陰影效應的考慮
- 批量觀測參數計算

**工程實踐技能：**
- 完整的座標轉換類別設計
- 數值穩定性和精度控制
- 極端情況的錯誤處理
- 批量處理和性能優化

**品質控制能力：**
- 座標轉換精度驗證方法
- 往返轉換一致性檢查
- 物理合理性驗證
- 數值穩定性分析

**下一步行動計劃：**
- 進入階段5：Stage1TLEProcessor架構設計
- 整合TLE解析、SGP4計算、座標轉換
- 設計完整的數據處理流水線
- 實作生產級的錯誤處理和監控

**實用成果：**
- 可處理任意衛星的觀測參數計算
- 支援任意觀測者位置設定
- 具備毫米級的座標轉換精度
- 完整的可見性判斷功能

**重要提醒：**
座標轉換是衛星追蹤系統的基礎，必須確保每個轉換步驟的精度和數值穩定性！