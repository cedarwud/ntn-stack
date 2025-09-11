# 階段5：Stage1TLEProcessor架構設計

## 課程目標與學習重點

### 完成本階段後您將能夠：
- 理解完整的Stage1TLEProcessor系統架構
- 設計模組化的軌道計算處理器
- 實現批量TLE數據處理能力
- 建立完善的錯誤處理機制
- 整合所有前四階段的核心技術

### 職業發展價值：
- 具備大型衛星系統架構設計能力
- 掌握高性能批量數據處理技術
- 理解生產級軌道計算系統設計原則

## Stage1TLEProcessor系統架構概述

### 系統定位與功能：
Stage1TLEProcessor是衛星處理系統的第一階段處理器，負責：
- 接收和解析TLE數據
- 執行SGP4軌道計算
- 進行座標系統轉換
- 輸出標準化的軌道數據

### 核心設計原則：
1. **模組化設計** - 每個組件職責單一且可重複使用
2. **批量處理** - 支援8000+顆衛星的並行計算
3. **錯誤處理** - 完善的異常捕獲和錯誤恢復
4. **性能優化** - 記憶體效率和計算速度平衡
5. **標準輸出** - 統一的數據格式和介面

## 系統架構組件設計

### 1. 核心處理器架構

```
Stage1TLEProcessor
├── TLEDataLoader          # TLE數據載入器
├── TLEParser              # TLE解析器
├── SGP4Calculator         # SGP4計算引擎
├── CoordinateConverter    # 座標轉換器
├── OutputFormatter        # 輸出格式化器
├── ErrorHandler           # 錯誤處理器
└── MetadataManager        # 元數據管理器
```

### 2. 數據流向設計

```
[TLE檔案] → [TLEDataLoader] → [TLEParser] → [SGP4Calculator] 
    ↓
[CoordinateConverter] → [OutputFormatter] → [標準化輸出JSON]
    ↓
[MetadataManager] → [處理報告和統計]
```

### 3. 關鍵介面定義

**主要處理介面：**
```python
class Stage1TLEProcessor:
    def process_satellite_data(self, 
                             tle_data_source: str,
                             observer_coords: dict,
                             time_range: dict) -> dict:
        """
        主要處理函數
        
        Args:
            tle_data_source: TLE數據來源路徑
            observer_coords: 觀測者座標 {lat, lon, altitude}
            time_range: 時間範圍 {start_time, end_time, interval}
            
        Returns:
            dict: 處理結果包含軌道數據、統計資訊、錯誤報告
        """
```

## 關鍵組件詳細設計

### TLEDataLoader - 數據載入器

**功能職責：**
- 讀取不同格式的TLE數據檔案
- 驗證TLE數據完整性
- 支援本地檔案和遠程數據源
- 實現數據快取機制

**核心方法設計：**
```python
class TLEDataLoader:
    def load_tle_file(self, file_path: str) -> List[str]:
        """載入TLE檔案並返回TLE行列表"""
        
    def validate_tle_data(self, tle_lines: List[str]) -> bool:
        """驗證TLE數據格式和完整性"""
        
    def get_satellite_count(self) -> int:
        """獲取載入的衛星數量"""
```

**實際應用考量：**
- 支援Starlink 8,370顆衛星的大文件載入
- 記憶體效率：使用生成器避免一次載入所有數據
- 錯誤恢復：跳過損壞的TLE記錄，記錄錯誤統計

### TLEParser - TLE解析器

**功能職責：**
- 解析三行TLE格式數據
- 提取軌道要素參數
- 驗證檢查碼正確性
- 轉換數據類型和單位

**解析流程設計：**
1. 分離衛星名稱行和兩行TLE數據
2. 驗證行號和衛星編號一致性
3. 提取並驗證檢查碼
4. 解析軌道要素到結構化對象
5. 單位轉換和數值驗證

**核心數據結構：**
```python
@dataclass
class TLEData:
    satellite_number: int
    satellite_name: str
    epoch_year: int
    epoch_day: float
    mean_motion: float
    eccentricity: float
    inclination: float
    raan: float           # 升交點赤經
    argument_of_perigee: float
    mean_anomaly: float
    mean_motion_derivative: float
    mean_motion_second_derivative: float
    bstar: float          # BSTAR拖曳係數
    element_number: int
    revolution_number: int
```

### SGP4Calculator - SGP4計算引擎

**功能職責：**
- 實現完整的SGP4/SDP4算法
- 處理近地和深空軌道
- 時間基準轉換和管理
- 軌道位置和速度計算

**關鍵實現要點：**

**時間基準處理（極其重要）：**
```python
def calculate_satellite_position(self, tle_data: TLEData, 
                               calculation_time: datetime) -> dict:
    """
    計算衛星在指定時間的位置
    
    重要：必須使用TLE epoch時間作為計算基準，不能使用當前時間！
    """
    # 1. 取得TLE epoch時間
    tle_epoch = self._convert_tle_epoch_to_datetime(tle_data)
    
    # 2. 計算時間差（分鐘）
    time_diff = (calculation_time - tle_epoch).total_seconds() / 60.0
    
    # 3. 執行SGP4計算
    position, velocity = self._sgp4_algorithm(tle_data, time_diff)
    
    return {
        'position_eci': position,      # ECI座標系位置
        'velocity_eci': velocity,      # ECI座標系速度
        'calculation_time': calculation_time,
        'tle_epoch': tle_epoch,
        'time_since_epoch_minutes': time_diff
    }
```

**批量處理優化：**
- 預先計算常數項
- 向量化數值計算
- 記憶體池管理大量對象
- 並行處理多顆衛星

### CoordinateConverter - 座標轉換器

**功能職責：**
- ECI到ECEF座標轉換
- ECEF到地理座標轉換
- 觀測者相對座標計算
- 仰角、方位角、距離計算

**轉換鏈設計：**
```
衛星ECI位置 → 地球固定座標ECEF → 地理座標(lat,lon,alt)
      ↓
觀測者座標系 → 仰角/方位角/距離 → 可見性判斷
```

**關鍵轉換算法：**
```python
def eci_to_geographic(self, eci_position: np.array, 
                     calculation_time: datetime) -> dict:
    """ECI座標轉換為地理座標"""
    # 1. 計算格林威治恆星時
    gmst = self._calculate_gmst(calculation_time)
    
    # 2. ECI轉ECEF（考慮地球自轉）
    ecef_pos = self._eci_to_ecef(eci_position, gmst)
    
    # 3. ECEF轉地理座標
    geographic = self._ecef_to_geographic(ecef_pos)
    
    return geographic

def calculate_observer_view(self, satellite_pos: dict, 
                          observer_coords: dict) -> dict:
    """計算觀測者視角的衛星位置"""
    # 計算仰角、方位角、距離
    elevation, azimuth, distance = self._topocentric_calculation(
        satellite_pos, observer_coords)
    
    return {
        'elevation_deg': elevation,
        'azimuth_deg': azimuth, 
        'distance_km': distance,
        'is_visible': elevation > 0  # 地平線以上為可見
    }
```

## 批量處理架構設計

### 多線程處理策略

**處理8000+顆衛星的挑戰：**
- 計算密集度高：每顆衛星需要SGP4+座標轉換
- 記憶體需求大：位置數據、中間計算結果
- I/O操作：TLE數據讀取、結果輸出

**並行處理方案：**
```python
class BatchProcessor:
    def __init__(self, num_threads: int = 4):
        self.thread_pool = ThreadPoolExecutor(max_workers=num_threads)
        self.result_queue = Queue()
    
    def process_satellites_batch(self, tle_data_list: List[TLEData],
                               observer_coords: dict,
                               time_range: dict) -> List[dict]:
        """批量處理衛星數據"""
        # 分批處理減少記憶體壓力
        batch_size = 100
        results = []
        
        for i in range(0, len(tle_data_list), batch_size):
            batch = tle_data_list[i:i + batch_size]
            batch_futures = []
            
            for tle_data in batch:
                future = self.thread_pool.submit(
                    self._process_single_satellite,
                    tle_data, observer_coords, time_range)
                batch_futures.append(future)
            
            # 收集批次結果
            for future in batch_futures:
                try:
                    result = future.result(timeout=30)
                    results.append(result)
                except Exception as e:
                    self._handle_processing_error(e, tle_data)
        
        return results
```

### 記憶體管理策略

**優化方案：**
1. **流式處理** - 避免一次載入所有TLE數據
2. **結果快取** - 重複計算的結果進行快取
3. **對象池** - 重複使用計算對象減少GC壓力
4. **分批輸出** - 避免大量結果數據積累

## 錯誤處理與品質控制

### 錯誤分級系統

**Level 1: 致命錯誤（停止處理）**
- TLE檔案不存在或無法讀取
- 觀測者座標格式錯誤
- SGP4算法初始化失敗

**Level 2: 嚴重錯誤（跳過當前衛星）**
- TLE數據格式錯誤或檢查碼不符
- SGP4計算發生數值異常
- 座標轉換計算失敗

**Level 3: 警告（記錄但繼續處理）**
- TLE數據時間過舊（>30天）
- 軌道參數異常值
- 計算結果超出合理範圍

### 品質驗證檢查

**數據有效性檢查：**
```python
class QualityValidator:
    def validate_tle_data(self, tle_data: TLEData) -> ValidationResult:
        """驗證TLE數據品質"""
        issues = []
        
        # 檢查軌道高度合理性
        if not (200 < self._calculate_altitude(tle_data) < 2000):
            issues.append('軌道高度異常')
        
        # 檢查離心率範圍
        if not (0 <= tle_data.eccentricity < 1):
            issues.append('離心率超出有效範圍')
        
        # 檢查時間新鮮度
        age_days = (datetime.now() - self._get_tle_epoch(tle_data)).days
        if age_days > 30:
            issues.append(f'TLE數據過舊：{age_days}天')
        
        return ValidationResult(is_valid=len(issues)==0, issues=issues)
    
    def validate_calculation_result(self, result: dict) -> bool:
        """驗證計算結果合理性"""
        # 檢查位置是否在地球附近
        distance_from_earth = np.linalg.norm(result['position_eci'])
        if distance_from_earth > 50000:  # 50,000 km
            return False
        
        # 檢查速度是否合理
        speed = np.linalg.norm(result['velocity_eci'])
        if not (1 < speed < 15):  # km/s
            return False
        
        return True
```

## 輸出格式與元數據

### 標準化輸出格式

**主要輸出JSON結構：**
```json
{
  "processing_metadata": {
    "processor_version": "1.0.0",
    "processing_time": "2025-09-11T10:30:00Z",
    "input_tle_file": "/data/starlink_tle.txt",
    "observer_coordinates": {
      "latitude": 25.0330,
      "longitude": 121.5654,
      "altitude_m": 10
    },
    "time_range": {
      "start_time": "2025-09-11T10:00:00Z",
      "end_time": "2025-09-11T11:00:00Z",
      "interval_seconds": 300
    },
    "processing_statistics": {
      "total_satellites": 8370,
      "successfully_processed": 8365,
      "errors_encountered": 5,
      "processing_duration_seconds": 45.7
    }
  },
  "satellite_data": [
    {
      "satellite_info": {
        "satellite_number": 44713,
        "satellite_name": "STARLINK-1007",
        "tle_epoch": "2025-09-02T14:25:33.123Z"
      },
      "orbital_positions": [
        {
          "calculation_time": "2025-09-11T10:00:00Z",
          "position_eci_km": [4567.8, -1234.5, 5678.9],
          "velocity_eci_kmps": [2.34, 7.12, -1.45],
          "geographic_coordinates": {
            "latitude_deg": 34.567,
            "longitude_deg": -118.234,
            "altitude_km": 550.2
          },
          "observer_view": {
            "elevation_deg": 45.7,
            "azimuth_deg": 123.4,
            "distance_km": 1234.5,
            "is_visible": true
          }
        }
      ]
    }
  ],
  "error_reports": [
    {
      "satellite_number": 44714,
      "error_type": "TLE_PARSE_ERROR",
      "error_message": "檢查碼驗證失敗",
      "timestamp": "2025-09-11T10:30:15Z"
    }
  ]
}
```

### 性能指標和統計資訊

**關鍵性能指標：**
- 每秒處理衛星數量（satellites/second）
- 記憶體峰值使用量（MB）
- 計算精確度評估（與參考值比較）
- 錯誤率統計（errors/total）

## 整合測試與驗證

### 端到端測試流程

**測試數據準備：**
1. 小規模測試：10顆已知衛星的TLE數據
2. 中規模測試：100顆衛星，包含不同軌道類型
3. 大規模測試：完整Starlink星座 8,370顆衛星

**驗證基準：**
- 與skyfield庫計算結果比較（誤差<1km）
- 與已知衛星過境時間比較
- 物理合理性檢查（速度、高度範圍）

**測試場景設計：**
```python
def test_stage1_processor_integration():
    """完整的Stage1處理器整合測試"""
    processor = Stage1TLEProcessor()
    
    # 測試配置
    test_config = {
        'tle_file': 'test_data/starlink_sample.tle',
        'observer_coords': {
            'latitude': 25.0330,
            'longitude': 121.5654,
            'altitude_m': 10
        },
        'time_range': {
            'start_time': '2025-09-11T10:00:00Z',
            'end_time': '2025-09-11T11:00:00Z',
            'interval_seconds': 300
        }
    }
    
    # 執行處理
    result = processor.process_satellite_data(**test_config)
    
    # 驗證結果
    assert result['processing_metadata']['successfully_processed'] > 0
    assert len(result['satellite_data']) > 0
    assert result['processing_metadata']['errors_encountered'] == 0
    
    # 驗證數據品質
    for satellite in result['satellite_data']:
        for position in satellite['orbital_positions']:
            # 檢查位置合理性
            assert_position_is_reasonable(position['position_eci_km'])
            # 檢查速度合理性  
            assert_velocity_is_reasonable(position['velocity_eci_kmps'])
```

## 階段總結

### 階段5學習成果確認：

**掌握的核心技術：**
- 模組化系統架構設計原則
- 批量處理8000+顆衛星的並行策略
- 完整的錯誤處理和品質控制體系
- 標準化輸出格式和元數據管理
- 端到端整合測試方法論

**完成的設計工作：**
- Stage1TLEProcessor完整架構定義
- 7個核心組件的詳細設計
- 數據流向和介面規範
- 性能優化和記憶體管理策略
- 品質驗證和錯誤處理機制

**實際應用能力：**
- 能夠設計大規模衛星數據處理系統
- 具備生產級軌道計算系統開發能力
- 掌握並行處理和性能優化技術
- 理解完整的軟體品質保證流程

**下一步行動計畫：**
- 進入階段6：完整程式實作 Step by Step
- 將架構設計轉化為可執行的Python代碼
- 實現每個組件的具體功能
- 進行模組化開發和單元測試

**重要提醒：確保完全理解系統架構再開始實作！**

## 關鍵技術提醒

### 時間基準處理（再次強調）
- 軌道計算必須使用TLE epoch時間，絕不使用當前時間
- 實際案例：8000+顆衛星→0顆可見 = 時間基準錯誤
- 時間差>3天會導致軌道預測嚴重偏離

### 資料真實性原則
- 所有衛星數據使用真實來源（Space-Track.org）
- 禁止使用模擬或假設的軌道參數
- 物理計算必須基於標準算法（SGP4/SDP4）
- 座標轉換使用精確的天文學公式

### 性能考量
- 記憶體效率：避免一次載入8000+顆衛星數據
- 計算優化：預先計算常數項，向量化運算
- 並行處理：合理的線程數量和批次大小
- 錯誤處理：快速失敗，避免無效計算資源消耗