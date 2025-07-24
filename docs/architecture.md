# 系統架構設計

## 🏗️ 整體架構圖

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   前端控制台     │    │    NetStack API   │    │  PostgreSQL DB  │
│                │    │                  │    │                │
│ ⏰ 時間軸控制    │◄──►│ 🛰️ 衛星位置查詢   │◄──►│ 📊 預計算數據    │
│ 🌟 星座選擇     │    │ 📡 handover事件   │    │ 🗃️ TLE 數據庫    │
│ 📊 3D 可視化    │    │ ⚡ 高效能 API     │    │ 🔄 時間序列優化  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌────────▼────────┐              │
         │              │  背景更新服務    │              │
         │              │ 🔄 TLE 自動更新  │              │
         │              │ 📈 增量預計算    │              │
         └──────────────┤ 🛡️ 智能回退機制  │──────────────┘
                        └─────────────────┘
```

## 🗃️ PostgreSQL 統一數據架構

### **核心設計原則**
- **時間序列優化**：針對衛星軌道數據的時間查詢優化
- **多星座支援**：constellation 欄位區分不同衛星系統
- **RL 系統整合**：與現有強化學習系統共享數據架構
- **高效查詢**：複合索引支援複雜時空查詢

### **主要數據表**

#### `satellite_tle_data` - TLE 數據主表
```sql
CREATE TABLE satellite_tle_data (
    id BIGSERIAL PRIMARY KEY,
    satellite_id VARCHAR(50) NOT NULL,
    norad_id INTEGER UNIQUE NOT NULL,
    satellite_name VARCHAR(100) NOT NULL,
    constellation VARCHAR(20) NOT NULL, -- 'starlink', 'oneweb', 'gps'
    line1 TEXT NOT NULL,               -- TLE 第一行
    line2 TEXT NOT NULL,               -- TLE 第二行
    epoch TIMESTAMP WITH TIME ZONE NOT NULL,
    -- 軌道參數
    mean_motion FLOAT,                 -- 平均運動
    eccentricity FLOAT,                -- 偏心率
    inclination FLOAT,                 -- 傾斜角
    orbital_period FLOAT,              -- 軌道週期 (分鐘)
    apogee_altitude FLOAT,             -- 遠地點高度
    perigee_altitude FLOAT,            -- 近地點高度
    is_active BOOLEAN DEFAULT TRUE,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

#### `satellite_orbital_cache` - 軌道位置緩存
```sql
CREATE TABLE satellite_orbital_cache (
    id BIGSERIAL PRIMARY KEY,
    satellite_id VARCHAR(50) NOT NULL,
    constellation VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    -- ECI 座標系位置 (km)
    position_x FLOAT NOT NULL,
    position_y FLOAT NOT NULL,
    position_z FLOAT NOT NULL,
    -- 地理座標
    latitude FLOAT NOT NULL,
    longitude FLOAT NOT NULL,
    altitude FLOAT NOT NULL,
    -- 觀測者視角 (台灣位置)
    elevation_angle FLOAT,             -- 仰角
    azimuth_angle FLOAT,               -- 方位角
    range_distance FLOAT,              -- 距離 (km)
    -- 計算品質
    calculation_method VARCHAR(20) DEFAULT 'SGP4',
    data_quality FLOAT DEFAULT 1.0,   -- 0-1 品質評分
    UNIQUE(satellite_id, timestamp)
);
```

#### `d2_measurement_cache` - D2 測量事件
```sql
CREATE TABLE d2_measurement_cache (
    id BIGSERIAL PRIMARY KEY,
    scenario_name VARCHAR(100) NOT NULL,
    satellite_id VARCHAR(50) NOT NULL,
    constellation VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    -- UE 和參考位置
    ue_latitude FLOAT NOT NULL,
    ue_longitude FLOAT NOT NULL,
    fixed_ref_latitude FLOAT NOT NULL,
    fixed_ref_longitude FLOAT NOT NULL,
    moving_ref_latitude FLOAT,         -- 衛星位置
    moving_ref_longitude FLOAT,
    -- D2 測量值
    satellite_distance FLOAT NOT NULL, -- UE 到衛星距離
    ground_distance FLOAT NOT NULL,    -- UE 到固定參考點距離
    -- D2 事件參數
    thresh1 FLOAT NOT NULL,
    thresh2 FLOAT NOT NULL,
    hysteresis FLOAT NOT NULL,
    -- 事件狀態
    trigger_condition_met BOOLEAN DEFAULT FALSE,
    event_type VARCHAR(20),            -- 'entering', 'leaving', 'none'
    -- 信號品質
    signal_strength FLOAT,             -- dBm
    snr FLOAT                          -- 信噪比
);
```

### **索引策略**
```sql
-- 時間序列查詢優化
CREATE INDEX idx_orbital_time_constellation ON satellite_orbital_cache 
    (constellation, timestamp, elevation_angle);

-- 空間查詢優化  
CREATE INDEX idx_orbital_position ON satellite_orbital_cache 
    (latitude, longitude, timestamp);

-- D2 事件查詢
CREATE INDEX idx_d2_events ON d2_measurement_cache 
    (constellation, timestamp, trigger_condition_met);
```

## 🔄 數據流設計

### **數據獲取與預處理**
```
TLE 數據源 → SGP4 軌道計算 → PostgreSQL 存儲 → API 查詢服務
     ↓              ↓              ↓              ↓
  Celestrak      Skyfield     時間序列表      FastAPI
Space-Track      精確計算     複合索引      JSON 響應
```

### **預計算流程**
1. **TLE 下載** → 從官方來源獲取最新軌道數據
2. **軌道傳播** → SGP4 算法計算指定時間範圍的位置
3. **觀測計算** → 轉換為台灣觀測者視角的天球座標
4. **批量存儲** → 高效插入 PostgreSQL 時間序列表
5. **品質驗證** → 數據完整性和準確性檢查

### **API 服務層**
```python
# 高效能查詢示例
@router.get("/satellites/positions")
async def get_satellite_positions(
    timestamp: datetime,
    constellation: str = "starlink",
    min_elevation: float = 10.0
):
    # 利用索引快速查詢
    query = """
    SELECT satellite_id, latitude, longitude, altitude, 
           elevation_angle, azimuth_angle, range_distance
    FROM satellite_orbital_cache 
    WHERE constellation = $1 
      AND timestamp = $2 
      AND elevation_angle >= $3
    ORDER BY elevation_angle DESC
    """
    return await database.fetch_all(query, constellation, timestamp, min_elevation)
```

## 🚀 性能優化策略

### **數據庫層面**
- **分區表**：按月份或星座分區大型表
- **物化視圖**：預聚合常用統計查詢
- **連接池**：asyncpg 連接池管理
- **批量操作**：COPY 指令高效插入

### **應用層面**
- **異步處理**：FastAPI + asyncio 非阻塞 I/O
- **快取策略**：Redis 快取熱點查詢結果
- **資料壓縮**：二進制格式減少傳輸量
- **增量更新**：只更新變更的衛星數據

### **前端層面**
- **虛擬滾動**：大量衛星數據的高效渲染
- **時間分片**：動畫播放的幀率控制
- **狀態管理**：React Context 統一狀態
- **懶加載**：按需載入時間段數據

## 🔧 智能更新機制

### **三層回退策略**
1. **即時更新** → 正常情況下的增量更新
2. **預載數據** → 網路異常時的本地回退
3. **內建數據** → 極端情況下的基礎功能

### **更新觸發條件**
- **定期檢查**：每週檢查 TLE 數據新鮮度
- **手動觸發**：開發者或管理員手動更新
- **自動偵測**：軌道預測誤差超過閾值時更新

### **更新流程**
```
檢查更新 → 下載 TLE → 增量計算 → 數據庫更新 → 快取清理 → 服務重啟
```

## 📊 監控與維護

### **健康檢查端點**
- `/health` - 整體服務狀態
- `/health/database` - 數據庫連接狀態  
- `/health/data` - 數據新鮮度檢查
- `/health/performance` - 性能指標

### **關鍵指標監控**
- **API 響應時間** < 100ms
- **數據庫查詢時間** < 50ms
- **內存使用率** < 80%
- **數據新鮮度** < 7 天

---

**下一步**: 查看各階段實施文檔 [phase1-database.md](./phase1-database.md)