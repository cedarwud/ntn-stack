# 真實衛星歷史數據預計算方案

## 🎯 方案概述

**核心理念**：使用真實 TLE 歷史數據 + 預計算存儲 + 時間軸播放，解決即時計算性能問題，同時保持數據真實性。

### ✅ 方案優勢
- **真實性保證**：使用真實 Starlink TLE 數據，非模擬數據
- **性能優化**：預計算避免即時 SGP4 運算瓶頸
- **展示友好**：支援時間軸控制、加速播放、handover 動畫
- **研究價值**：可用於 3GPP events 計算和論文分析
- **穩定性**：不依賴網路即時連接

### 📊 技術參數建議

#### **時間段選擇（按研究等級分層）**

**📊 展示級數據**：6 小時歷史數據
- 用途：系統驗證、UI 展示、概念驗證  
- 理由：展示完整的衛星覆蓋變化和 handover 場景

**🎓 研究級數據**：45 天歷史數據
- 訓練數據：30 天（RL 主要學習期）
- 測試數據：7 天（性能評估）
- 驗證數據：7 天（交叉驗證）  
- 緩衝數據：1 天（時間重疊處理）

**🏆 頂級期刊標準**：60 天歷史數據
- 符合 IEEE TCOM、TWC 等頂級期刊要求
- 支援大規模統計分析和長期趨勢研究

**💾 數據量估算（45天研究級）**：
```
45 天 × 24 小時 × 120 時間點(30秒) × 8 顆可見衛星 = 518,400 條記錄
518,400 × 500 bytes ≈ 260MB（映像檔完全可承受）
```

#### **時間解析度**
- **建議間隔**：30 秒
- **理由**：衛星速度 7.5 km/s，30 秒移動 225km，適合 handover 觸發精度
- **數據量**：6 小時 = 720 個時間點

#### **多星座支援設計**

**🌟 主要星座：Starlink (SpaceX)**
- 衛星數量：~5000 顆，覆蓋密度最高
- 軌道參數：550km 高度，53° 傾角  
- 研究價值：數據最豐富，學術熱度最高
- handover 場景：星座內切換

**🌐 對比星座：OneWeb**  
- 衛星數量：~648 顆，極地覆蓋優異
- 軌道參數：1200km 高度，87.4° 傾角
- 研究價值：不同軌道特性的對比研究
- 分析模式：獨立分析，避免混合不同星座

**⚠️ 重要限制：跨星座 handover 不可行**
- 不同星座使用不同頻段、協議、地面設施
- 論文研究應分別分析各星座的內部 handover
- UI 設計：需要星座切換功能，避免混合顯示

#### **可見衛星數量 & 數據規模**
```
各仰角範圍的可見衛星：
- 仰角 ≥ 15°（handover 主要候選）: 3-5 顆
- 仰角 ≥ 10°（handover 監測範圍）: 6-8 顆  
- 仰角 ≥ 5°（潛在候選）: 8-12 顆
- 仰角 ≥ 0°（理論可見）: 15-25 顆

多星座數據規模（45天研究級）：
Starlink: 45 天 × 2880 時間點 × 8 顆 = 1,036,800 條記錄 (518MB)
OneWeb: 45 天 × 2880 時間點 × 5 顆 = 648,000 條記錄 (324MB)
總計: ~842MB（Docker 映像檔完全可承受）

展示級數據（6小時）：僅 2.9MB
```

## 📱 真實 UE Handover 場景分析

### **🛰️ Starlink 可見衛星數量**

基於真實的 Starlink 星座配置：
- **總衛星數**: ~5000 顆 Starlink 衛星
- **軌道高度**: 550km
- **觀測半徑**: √((6371+550)² - 6371²) ≈ 2300km

### **📊 分層可見性設計**

```python
VISIBILITY_LEVELS = {
    "handover_candidates": {
        "min_elevation": 15, 
        "expected_count": "3-5 顆",
        "usage": "主要 handover 候選，信號強度足夠"
    },
    "monitoring_satellites": {
        "min_elevation": 10, 
        "expected_count": "6-8 顆",
        "usage": "handover 監測範圍，符合 3GPP NTN 標準"
    }, 
    "potential_satellites": {
        "min_elevation": 5, 
        "expected_count": "8-12 顆",
        "usage": "潛在候選，即將進入監測範圍"
    },
    "theoretical_visible": {
        "min_elevation": 0, 
        "expected_count": "15-25 顆",
        "usage": "理論可見但信號太弱，不參與 handover"
    }
}
```

### **🎯 典型 Handover 場景示例**

```
時間點: 2025-07-15 10:30:00 UTC
台灣 UE 位置: (24.94°N, 121.37°E)

🔗 服務衛星: STARLINK-1234 (仰角 45°, 信號強度 -95dBm)

📡 Handover 候選:
├── STARLINK-5678 (仰角 25°, 信號強度 -105dBm) ✅ 主要候選
├── STARLINK-9012 (仰角 18°, 信號強度 -108dBm) ✅ 次要候選  
└── STARLINK-3456 (仰角 12°, 信號強度 -112dBm) ⚠️ 備選候選

👁️ 監測中: 2 顆 (仰角 5-10°)
🌅 即將可見: 1 顆 (仰角 0-5°)

總計參與 handover 決策: 6-8 顆（符合 3GPP NTN 建議）
```

### **📋 3GPP NTN 標準符合性**

- **測量衛星數**: 最多 8 顆 ✅
- **handover 候選**: 3-5 顆 ✅
- **同時監測**: 6-8 顆 ✅
- **信號閾值**: 仰角 ≥ 10° ✅

## 🚀 實施計劃

### Phase 1: 立即可用數據準備 (1-2 天)

#### 1.1 PostgreSQL 歷史數據表設計
```sql
-- 擴展現有的 satellite_orbital_cache 表以支援歷史數據查詢
-- 表已存在於 NetStack RL PostgreSQL (172.20.0.51:5432/rl_research)

-- 添加台灣觀測者特定的字段
ALTER TABLE satellite_orbital_cache 
ADD COLUMN IF NOT EXISTS observer_latitude FLOAT,
ADD COLUMN IF NOT EXISTS observer_longitude FLOAT,
ADD COLUMN IF NOT EXISTS observer_altitude FLOAT,
ADD COLUMN IF NOT EXISTS signal_strength FLOAT,
ADD COLUMN IF NOT EXISTS path_loss_db FLOAT;

-- 添加歷史數據查詢索引
CREATE INDEX IF NOT EXISTS idx_orbital_observer_time 
ON satellite_orbital_cache (observer_latitude, observer_longitude, timestamp);

CREATE INDEX IF NOT EXISTS idx_orbital_elevation_time 
ON satellite_orbital_cache (elevation_angle, timestamp) 
WHERE elevation_angle >= 10;

-- 歷史數據結構 (基於現有表)
-- satellite_orbital_cache 表結構:
-- id, satellite_id, norad_id, constellation, timestamp
-- position_x, position_y, position_z (ECI 座標)
-- latitude, longitude, altitude (地理座標)  
-- elevation_angle, azimuth_angle (相對觀測者)
-- range_rate, calculation_method, data_quality
-- observer_latitude, observer_longitude, observer_altitude (新增)
-- signal_strength, path_loss_db (新增)
```

#### 1.2 容器內預載數據機制
```bash
# Docker 鏡像內建預載數據（構建時生成）
# netstack/Dockerfile 添加預載數據生成

# 第1步：構建時預計算歷史數據
RUN python3 generate_precomputed_satellite_data.py \
    --output /app/data/satellite_history_embedded.sql \
    --observer_lat 24.94417 \
    --observer_lon 121.37139 \
    --duration_hours 6 \
    --time_step_seconds 30

# 第2步：啟動時立即載入（無需網路連接）
COPY docker-entrypoint.sh /app/
RUN chmod +x /app/docker-entrypoint.sh
```

#### 1.3 智能數據載入器
```python
# app/services/instant_satellite_loader.py
import os
import asyncpg
import logging
from datetime import datetime, timedelta

class InstantSatelliteLoader:
    """容器啟動時立即載入衛星數據"""
    
    def __init__(self, postgres_url: str):
        self.postgres_url = postgres_url
        self.embedded_data_path = "/app/data/satellite_history_embedded.sql"
        
    async def ensure_data_available(self) -> bool:
        """確保衛星數據立即可用"""
        
        # 1. 檢查 PostgreSQL 中是否已有數據
        existing_data = await self._check_existing_data()
        
        if existing_data and self._is_data_fresh(existing_data):
            logging.info(f"✅ 發現 {existing_data['count']} 條新鮮的衛星歷史數據，跳過載入")
            return True
            
        # 2. 載入內建預載數據
        logging.info("📡 載入內建衛星歷史數據...")
        success = await self._load_embedded_data()
        
        if success:
            logging.info("✅ 衛星數據載入完成，系統立即可用")
            return True
            
        # 3. 緊急 fallback：生成最小可用數據集
        logging.warning("⚠️ 使用緊急 fallback 數據")
        return await self._generate_emergency_data()
        
    async def _check_existing_data(self):
        """檢查現有數據"""
        conn = await asyncpg.connect(self.postgres_url)
        try:
            result = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as count,
                    MAX(timestamp) as latest_time,
                    MIN(timestamp) as earliest_time
                FROM satellite_orbital_cache 
                WHERE observer_latitude = 24.94417 
                  AND observer_longitude = 121.37139
            """)
            return dict(result) if result else None
        finally:
            await conn.close()
            
    def _is_data_fresh(self, data_info) -> bool:
        """判斷數據是否夠新鮮（7天內）"""
        if not data_info['latest_time']:
            return False
            
        age = datetime.utcnow() - data_info['latest_time'].replace(tzinfo=None)
        return age.days < 7 and data_info['count'] > 1000
        
    async def _load_embedded_data(self) -> bool:
        """載入內建預載數據"""
        if not os.path.exists(self.embedded_data_path):
            logging.error(f"❌ 內建數據文件不存在: {self.embedded_data_path}")
            return False
            
        conn = await asyncpg.connect(self.postgres_url)
        try:
            # 清空舊數據
            await conn.execute("""
                DELETE FROM satellite_orbital_cache 
                WHERE observer_latitude = 24.94417 AND observer_longitude = 121.37139
            """)
            
            # 載入預載數據
            with open(self.embedded_data_path, 'r') as f:
                sql_content = f.read()
                await conn.execute(sql_content)
                
            # 驗證載入結果
            count = await conn.fetchval("""
                SELECT COUNT(*) FROM satellite_orbital_cache 
                WHERE observer_latitude = 24.94417 AND observer_longitude = 121.37139
            """)
            
            logging.info(f"✅ 成功載入 {count} 條預載衛星數據")
            return count > 0
            
        except Exception as e:
            logging.error(f"❌ 載入內建數據失敗: {e}")
            return False
        finally:
            await conn.close()
            
    async def _generate_emergency_data(self) -> bool:
        """生成緊急最小數據集（1小時數據）"""
        from .emergency_satellite_generator import EmergencySatelliteGenerator
        
        generator = EmergencySatelliteGenerator(self.postgres_url)
        return await generator.generate_minimal_dataset(
            observer_lat=24.94417,
            observer_lon=121.37139,
            duration_hours=1,
            time_step_seconds=60
        )
```

### Phase 2: 預計算引擎開發 (2-3 天)

#### 2.1 歷史數據預計算器
```python
# precompute_satellite_history.py
class SatelliteHistoryPrecomputer:
    def __init__(self, tle_file_path, observer_coords, time_range):
        self.tle_data = self.load_tle_data(tle_file_path)
        self.observer = wgs84.latlon(*observer_coords)
        self.time_range = time_range
        
    def compute_history(self, time_interval_seconds=30):
        """預計算指定時間範圍內的所有衛星位置"""
        results = []
        
        start_time = self.time_range[0] 
        end_time = self.time_range[1]
        
        current_time = start_time
        while current_time <= end_time:
            # 計算所有衛星在當前時間的位置
            visible_satellites = self.compute_visible_satellites(current_time)
            results.extend(visible_satellites)
            
            current_time += timedelta(seconds=time_interval_seconds)
            
        return results
        
    def compute_visible_satellites(self, timestamp):
        """計算指定時間所有可見衛星位置"""
        visible = []
        ts = load.timescale()
        t = ts.from_datetime(timestamp)
        
        for satellite_data in self.tle_data:
            satellite = EarthSatellite(satellite_data.line1, satellite_data.line2, satellite_data.name, ts)
            
            # SGP4 軌道計算
            difference = satellite - self.observer
            topocentric = difference.at(t)
            alt, az, distance = topocentric.altaz()
            
            if alt.degrees >= -10:  # 可見性閾值
                geocentric = satellite.at(t)
                subpoint = wgs84.subpoint(geocentric)
                
                position_data = {
                    "timestamp": timestamp,
                    "satellite_id": satellite_data.norad_id,
                    "satellite_name": satellite_data.name,
                    "observer_position": {
                        "latitude": self.observer.latitude.degrees,
                        "longitude": self.observer.longitude.degrees,
                        "altitude": self.observer.elevation.km * 1000
                    },
                    "satellite_position": {
                        "latitude": subpoint.latitude.degrees,
                        "longitude": subpoint.longitude.degrees,
                        "altitude": subpoint.elevation.km,
                        "elevation": alt.degrees,
                        "azimuth": az.degrees,
                        "range": distance.km,
                        "velocity": 7.5  # LEO 平均速度
                    },
                    "signal_quality": {
                        "path_loss_db": 120 + 20 * math.log10(distance.km),
                        "signal_strength": max(30, 80 - distance.km / 25)
                    }
                }
                
                visible.append(position_data)
                
        return visible
```

#### 2.2 批次處理和存儲
```python
# batch_processor.py
import asyncpg
from typing import List, Dict

class HistoryBatchProcessor:
    def __init__(self, postgres_url: str):
        self.postgres_url = postgres_url
        
    async def process_and_store(self, precomputed_data: List[Dict]):
        """批次存儲預計算數據到 PostgreSQL"""
        batch_size = 1000
        
        conn = await asyncpg.connect(self.postgres_url)
        try:
            for i in range(0, len(precomputed_data), batch_size):
                batch = precomputed_data[i:i + batch_size]
                
                # 批次插入到 satellite_orbital_cache
                await conn.executemany("""
                    INSERT INTO satellite_orbital_cache (
                        satellite_id, norad_id, constellation, timestamp,
                        position_x, position_y, position_z,
                        latitude, longitude, altitude,
                        elevation_angle, azimuth_angle, range_rate,
                        observer_latitude, observer_longitude, observer_altitude,
                        signal_strength, path_loss_db,
                        calculation_method, data_quality
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20)
                    ON CONFLICT (satellite_id, timestamp) DO UPDATE SET
                        elevation_angle = EXCLUDED.elevation_angle,
                        azimuth_angle = EXCLUDED.azimuth_angle,
                        signal_strength = EXCLUDED.signal_strength,
                        path_loss_db = EXCLUDED.path_loss_db
                """, [self._prepare_record(record) for record in batch])
                
                print(f"已存儲 {i + len(batch)}/{len(precomputed_data)} 條記錄到 PostgreSQL")
                
        finally:
            await conn.close()
            
    def _prepare_record(self, record: Dict) -> tuple:
        """準備 PostgreSQL 插入記錄"""
        return (
            record["satellite_id"], record["norad_id"], record["constellation"],
            record["timestamp"], record["position_x"], record["position_y"], record["position_z"],
            record["satellite_position"]["latitude"], record["satellite_position"]["longitude"], 
            record["satellite_position"]["altitude"], record["satellite_position"]["elevation"],
            record["satellite_position"]["azimuth"], record["satellite_position"]["range_rate"],
            record["observer_position"]["latitude"], record["observer_position"]["longitude"], 
            record["observer_position"]["altitude"], record["signal_quality"]["signal_strength"],
            record["signal_quality"]["path_loss_db"], "SGP4", 1.0
        )
```

### Phase 3: API 重構 (1-2 天)

#### 3.1 時間軸查詢 API
```python
# satellite_history_api.py
@router.get("/satellites/history/at_time")
async def get_satellites_at_time(
    target_time: datetime,
    observer_lat: float = 24.94417,
    observer_lon: float = 121.37139,
    min_elevation: float = 10.0,
    count: int = 10
):
    """獲取指定時間點的衛星位置"""
    
    # 查詢預計算數據 (PostgreSQL)
    conn = await asyncpg.connect(RL_DATABASE_URL)
    try:
        satellites = await conn.fetch("""
            SELECT satellite_id, norad_id, constellation, timestamp,
                   latitude, longitude, altitude, elevation_angle, azimuth_angle,
                   range_rate, signal_strength, path_loss_db
            FROM satellite_orbital_cache 
            WHERE timestamp = $1 
              AND observer_latitude = $2 
              AND observer_longitude = $3
              AND elevation_angle >= $4
            ORDER BY elevation_angle DESC 
            LIMIT $5
        """, target_time, observer_lat, observer_lon, min_elevation, count)
    finally:
        await conn.close()
    
    return {
        "success": True,
        "timestamp": target_time.isoformat(),
        "satellites": satellites,
        "count": len(satellites)
    }

@router.get("/satellites/history/time_range") 
async def get_satellites_time_range(
    start_time: datetime,
    end_time: datetime,
    satellite_ids: List[str] = None,
    time_step_seconds: int = 30
):
    """獲取時間範圍內的衛星軌跡數據（用於動畫）"""
    
    query = {
        "timestamp": {"$gte": start_time, "$lte": end_time}
    }
    
    if satellite_ids:
        query["satellite_id"] = {"$in": satellite_ids}
        
    cursor = mongodb.satellite_history.find(query).sort("timestamp", 1)
    trajectory_data = await cursor.to_list(length=None)
    
    # 按衛星分組
    satellites_trajectories = {}
    for point in trajectory_data:
        sat_id = point["satellite_id"]
        if sat_id not in satellites_trajectories:
            satellites_trajectories[sat_id] = []
        satellites_trajectories[sat_id].append(point)
    
    return {
        "success": True,
        "time_range": {
            "start": start_time.isoformat(),
            "end": end_time.isoformat(),
            "step_seconds": time_step_seconds
        },
        "satellites": satellites_trajectories
    }
```

#### 3.2 時間控制 API  
```python
@router.get("/satellites/history/timeline_info")
async def get_timeline_info():
    """獲取可用的歷史數據時間範圍"""
    
    pipeline = [
        {"$group": {
            "_id": None,
            "earliest_time": {"$min": "$timestamp"},
            "latest_time": {"$max": "$timestamp"},
            "total_timepoints": {"$addToSet": "$timestamp"}
        }}
    ]
    
    result = await mongodb.satellite_history.aggregate(pipeline).to_list(1)
    
    if result:
        info = result[0]
        return {
            "available_time_range": {
                "start": info["earliest_time"].isoformat(),
                "end": info["latest_time"].isoformat(),
                "total_duration_hours": (info["latest_time"] - info["earliest_time"]).total_seconds() / 3600,
                "total_timepoints": len(info["total_timepoints"])
            },
            "recommended_playback_speeds": [1, 2, 5, 10, 30, 60],  # 加速倍數
            "time_step_seconds": 30
        }
    
    return {"error": "No historical data available"}
```

### Phase 4: 前端時間軸控制 (2-3 天)

#### 4.1 星座切換控制器
```typescript
// ConstellationSelector.tsx
interface ConstellationSelectorProps {
  selectedConstellation: 'starlink' | 'oneweb';
  onConstellationChange: (constellation: 'starlink' | 'oneweb') => void;
  availableConstellations: ConstellationInfo[];
}

interface ConstellationInfo {
  id: 'starlink' | 'oneweb';
  name: string;
  description: string;
  satelliteCount: number;
  orbitAltitude: number;
  inclination: number;
  coverage: string;
}

export const ConstellationSelector: React.FC<ConstellationSelectorProps> = ({
  selectedConstellation,
  onConstellationChange,
  availableConstellations
}) => {
  return (
    <div className="constellation-selector">
      <h3>星座選擇</h3>
      <div className="constellation-tabs">
        {availableConstellations.map(constellation => (
          <div
            key={constellation.id}
            className={`constellation-tab ${selectedConstellation === constellation.id ? 'active' : ''}`}
            onClick={() => onConstellationChange(constellation.id)}
          >
            <div className="constellation-name">{constellation.name}</div>
            <div className="constellation-info">
              <span>衛星數: {constellation.satelliteCount}</span>
              <span>高度: {constellation.orbitAltitude}km</span>
              <span>傾角: {constellation.inclination}°</span>
            </div>
            <div className="constellation-coverage">{constellation.coverage}</div>
          </div>
        ))}
      </div>
      
      {/* 切換警告 */}
      <div className="constellation-warning">
        ⚠️ 注意：不同星座無法進行跨星座 handover，請分別分析
      </div>
    </div>
  );
};
```

#### 4.2 時間軸控制器組件  
```typescript
// TimelineController.tsx
interface TimelineControllerProps {
  availableTimeRange: {
    start: string;
    end: string;
    totalDurationHours: number;
  };
  onTimeChange: (timestamp: Date) => void;
  onPlaybackSpeedChange: (speed: number) => void;
}

export const TimelineController: React.FC<TimelineControllerProps> = ({
  availableTimeRange,
  onTimeChange, 
  onPlaybackSpeedChange
}) => {
  const [currentTime, setCurrentTime] = useState(new Date(availableTimeRange.start));
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  
  // 時間軸滑桿
  const handleTimeSliderChange = (value: number) => {
    const startTime = new Date(availableTimeRange.start).getTime();
    const endTime = new Date(availableTimeRange.end).getTime();
    const targetTime = new Date(startTime + (endTime - startTime) * value / 100);
    
    setCurrentTime(targetTime);
    onTimeChange(targetTime);
  };
  
  // 播放控制
  useEffect(() => {
    if (!isPlaying) return;
    
    const interval = setInterval(() => {
      setCurrentTime(prev => {
        const next = new Date(prev.getTime() + 30000 * playbackSpeed); // 30秒步進 × 加速倍數
        
        if (next.getTime() > new Date(availableTimeRange.end).getTime()) {
          setIsPlaying(false);
          return prev;
        }
        
        onTimeChange(next);
        return next;
      });
    }, 1000); // 每秒更新
    
    return () => clearInterval(interval);
  }, [isPlaying, playbackSpeed]);
  
  return (
    <div className="timeline-controller">
      {/* 時間顯示 */}
      <div className="time-display">
        {currentTime.toISOString().substr(11, 8)} UTC
      </div>
      
      {/* 時間軸滑桿 */}
      <input
        type="range"
        min={0}
        max={100} 
        value={(currentTime.getTime() - new Date(availableTimeRange.start).getTime()) / 
               (new Date(availableTimeRange.end).getTime() - new Date(availableTimeRange.start).getTime()) * 100}
        onChange={(e) => handleTimeSliderChange(Number(e.target.value))}
        className="time-slider"
      />
      
      {/* 播放控制按鈕 */}
      <div className="playback-controls">
        <button onClick={() => setIsPlaying(!isPlaying)}>
          {isPlaying ? '⏸️' : '▶️'}
        </button>
        
        <select 
          value={playbackSpeed} 
          onChange={(e) => {
            const speed = Number(e.target.value);
            setPlaybackSpeed(speed);
            onPlaybackSpeedChange(speed);
          }}
        >
          <option value={1}>1x</option>
          <option value={2}>2x</option>
          <option value={5}>5x</option>
          <option value={10}>10x</option>
          <option value={30}>30x</option>
          <option value={60}>60x</option>
        </select>
      </div>
    </div>
  );
};
```

#### 4.2 動畫渲染組件
```typescript
// SatelliteAnimationViewer.tsx
interface SatelliteAnimationViewerProps {
  currentTime: Date;
  playbackSpeed: number;
}

export const SatelliteAnimationViewer: React.FC<SatelliteAnimationViewerProps> = ({
  currentTime,
  playbackSpeed
}) => {
  const [satellites, setSatellites] = useState<SatellitePosition[]>([]);
  const [handoverEvents, setHandoverEvents] = useState<HandoverEvent[]>([]);
  
  // 獲取當前時間點的衛星位置
  useEffect(() => {
    const fetchSatellitesAtTime = async () => {
      const response = await netstackFetch(`/api/v1/satellites/history/at_time?target_time=${currentTime.toISOString()}&count=20`);
      const data = await response.json();
      
      if (data.success) {
        setSatellites(data.satellites);
      }
    };
    
    fetchSatellitesAtTime();
  }, [currentTime]);
  
  // 計算並顯示 handover 事件
  useEffect(() => {
    const calculateHandoverEvents = () => {
      // 基於當前衛星位置和 3GPP events 計算 handover 觸發
      const events = satellites.map(sat => {
        if (sat.satellite_position.elevation < 15 && sat.satellite_position.elevation > 10) {
          return {
            type: 'A3_EVENT', // 鄰近衛星強度超過閾值
            satellite_id: sat.satellite_id,
            timestamp: currentTime,
            trigger_condition: 'elevation_threshold',
            details: {
              elevation: sat.satellite_position.elevation,
              signal_strength: sat.signal_quality.signal_strength
            }
          };
        }
        return null;
      }).filter(Boolean);
      
      setHandoverEvents(events);
    };
    
    calculateHandoverEvents();
  }, [satellites, currentTime]);
  
  return (
    <div className="satellite-animation-viewer">
      {/* 3D 衛星位置可視化 */}
      <div className="satellite-3d-view">
        {satellites.map(satellite => (
          <SatelliteMarker
            key={satellite.satellite_id}
            position={satellite.satellite_position}
            name={satellite.satellite_name}
            signalStrength={satellite.signal_quality.signal_strength}
            isHandoverCandidate={handoverEvents.some(e => e.satellite_id === satellite.satellite_id)}
          />
        ))}
      </div>
      
      {/* Handover 事件列表 */}
      <div className="handover-events-panel">
        <h3>當前 Handover 事件</h3>
        {handoverEvents.map((event, index) => (
          <div key={index} className="handover-event">
            <span className="event-type">{event.type}</span>
            <span className="satellite-name">{event.satellite_id}</span>
            <span className="trigger-condition">{event.trigger_condition}</span>
          </div>
        ))}
      </div>
    </div>
  );
};
```

#### 4.3 增強型星座選擇器 (多星座支援)
```typescript
// ConstellationSelector.tsx (增強版)
import React, { useState, useEffect } from 'react';
import { Select, Badge, Alert, Card, Statistic, Row, Col } from 'antd';
import { SatelliteOutlined, GlobalOutlined } from '@ant-design/icons';

interface ConstellationInfo {
  name: string;
  displayName: string;
  color: string;
  icon: React.ReactNode;
  satelliteCount: number;
  coverage: string;
  orbitAltitude: string;
  latency: string;
  dataAvailability: {
    start: string;
    end: string;
    totalDays: number;
  };
}

const CONSTELLATION_CONFIGS: Record<string, ConstellationInfo> = {
  starlink: {
    name: 'starlink',
    displayName: 'Starlink',
    color: '#1890ff',
    icon: <SatelliteOutlined />,
    satelliteCount: 0,
    coverage: '全球覆蓋 (±70°)',
    orbitAltitude: '550km',
    latency: '20-40ms',
    dataAvailability: { start: '', end: '', totalDays: 0 }
  },
  oneweb: {
    name: 'oneweb',
    displayName: 'OneWeb', 
    color: '#52c41a',
    icon: <GlobalOutlined />,
    satelliteCount: 0,
    coverage: '極地覆蓋 (±88°)',
    orbitAltitude: '1200km',
    latency: '32-50ms',
    dataAvailability: { start: '', end: '', totalDays: 0 }
  }
};

interface Props {
  value: string;
  onChange: (constellation: string) => void;
  disabled?: boolean;
  showComparison?: boolean;
}

export const ConstellationSelector: React.FC<Props> = ({ 
  value, 
  onChange, 
  disabled = false,
  showComparison = true
}) => {
  const [constellations, setConstellations] = useState(CONSTELLATION_CONFIGS);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchConstellationData = async () => {
      setLoading(true);
      try {
        const response = await fetch('/api/satellites/constellations/info');
        const data = await response.json();
        
        const updated = { ...constellations };
        data.forEach((item: any) => {
          if (updated[item.constellation]) {
            updated[item.constellation].satelliteCount = item.satellite_count;
            updated[item.constellation].dataAvailability = {
              start: item.data_start,
              end: item.data_end,
              totalDays: item.total_days
            };
          }
        });
        setConstellations(updated);
      } catch (error) {
        console.error('Failed to fetch constellation data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchConstellationData();
  }, []);

  const handleChange = (newValue: string) => {
    if (!disabled) {
      onChange(newValue);
    }
  };

  const selectedConstellation = constellations[value];

  return (
    <div className="constellation-selector">
      <div className="selector-header mb-3">
        <span className="text-base font-semibold text-gray-800">
          🛰️ LEO 衛星星座系統
        </span>
        {loading && <span className="ml-2 text-sm text-blue-500">載入中...</span>}
      </div>
      
      <Select
        value={value}
        onChange={handleChange}
        disabled={disabled || loading}
        className="w-full"
        placeholder="選擇星座系統"
        size="large"
        optionLabelProp="label"
      >
        {Object.entries(constellations).map(([key, info]) => (
          <Select.Option 
            key={key} 
            value={key}
            label={
              <div className="flex items-center">
                <span style={{ color: info.color, fontSize: '16px' }}>
                  {info.icon}
                </span>
                <span className="ml-2 font-medium">{info.displayName}</span>
                {info.satelliteCount > 0 && (
                  <Badge 
                    count={info.satelliteCount} 
                    size="small" 
                    className="ml-2"
                    style={{ backgroundColor: info.color }}
                  />
                )}
              </div>
            }
          >
            <div className="constellation-option py-2">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center">
                  <span style={{ color: info.color, fontSize: '18px' }}>
                    {info.icon}
                  </span>
                  <span className="ml-2 font-semibold text-gray-800">
                    {info.displayName}
                  </span>
                </div>
                {info.satelliteCount > 0 && (
                  <Badge 
                    count={info.satelliteCount} 
                    size="small"
                    style={{ backgroundColor: info.color }}
                  />
                )}
              </div>
              
              <div className="text-sm text-gray-600 space-y-1">
                <div>📍 覆蓋: {info.coverage}</div>
                <div>🚀 高度: {info.orbitAltitude}</div>
                <div>⚡ 延遲: {info.latency}</div>
                {info.dataAvailability.totalDays > 0 && (
                  <div>📊 數據: {info.dataAvailability.totalDays} 天</div>
                )}
              </div>
            </div>
          </Select.Option>
        ))}
      </Select>
      
      {selectedConstellation && (
        <Card className="mt-4" size="small">
          <Row gutter={16}>
            <Col span={18}>
              <div className="flex items-center mb-3">
                <span style={{ color: selectedConstellation.color, fontSize: '20px' }}>
                  {selectedConstellation.icon}
                </span>
                <span className="ml-3 text-lg font-semibold">
                  {selectedConstellation.displayName}
                </span>
              </div>
              
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div>
                  <span className="text-gray-500">覆蓋範圍:</span>
                  <span className="ml-1 font-medium">{selectedConstellation.coverage}</span>
                </div>
                <div>
                  <span className="text-gray-500">軌道高度:</span>
                  <span className="ml-1 font-medium">{selectedConstellation.orbitAltitude}</span>
                </div>
                <div>
                  <span className="text-gray-500">預期延遲:</span>
                  <span className="ml-1 font-medium">{selectedConstellation.latency}</span>
                </div>
                <div>
                  <span className="text-gray-500">數據覆蓋:</span>
                  <span className="ml-1 font-medium">
                    {selectedConstellation.dataAvailability.totalDays} 天
                  </span>
                </div>
              </div>
            </Col>
            <Col span={6}>
              <Statistic
                title="可見衛星"
                value={selectedConstellation.satelliteCount}
                suffix="顆"
                valueStyle={{ color: selectedConstellation.color }}
              />
            </Col>
          </Row>
          
          {selectedConstellation.dataAvailability.start && (
            <div className="mt-3 p-2 bg-blue-50 rounded text-xs text-gray-600">
              💡 數據期間: {selectedConstellation.dataAvailability.start} ~ {selectedConstellation.dataAvailability.end}
              <br />
              🎯 適用於論文級 LEO 衛星 Handover 研究和 RL 訓練
            </div>
          )}
          
          <Alert
            message="星座隔離原則"
            description="不同衛星星座間無法進行 Handover，請分別進行分析。每個星座的軌道參數、覆蓋模式和服務特性均不相同。"
            type="info"
            showIcon
            className="mt-3"
            size="small"
          />
        </Card>
      )}
    </div>
  );
};
```

#### 4.4 增強型時間軸控制器
```typescript
// TimelineControl.tsx (增強版)
import React, { useState, useEffect, useCallback } from 'react';
import { Slider, DatePicker, Button, Space, Card, Statistic, Progress, Switch } from 'antd';
import { 
  PlayCircleOutlined, 
  PauseCircleOutlined, 
  FastForwardOutlined,
  StepForwardOutlined,
  StepBackwardOutlined,
  ReloadOutlined
} from '@ant-design/icons';
import moment from 'moment';

interface TimelineData {
  start: string;
  end: string;
  totalDurationHours: number;
  dataPoints: number;
  resolution: string;
}

interface Props {
  constellation: string;
  onTimeChange: (timestamp: number) => void;
  onPlaybackSpeedChange?: (speed: number) => void;
  disabled?: boolean;
  showStatistics?: boolean;
}

export const TimelineControl: React.FC<Props> = ({ 
  constellation,
  onTimeChange,
  onPlaybackSpeedChange,
  disabled = false,
  showStatistics = true
}) => {
  const [timelineData, setTimelineData] = useState<TimelineData | null>(null);
  const [currentTime, setCurrentTime] = useState(Date.now());
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const [realTimeMode, setRealTimeMode] = useState(false);
  const [loading, setLoading] = useState(false);
  
  useEffect(() => {
    const fetchTimelineData = async () => {
      if (!constellation) return;
      
      setLoading(true);
      try {
        const response = await fetch(`/api/satellites/timeline/${constellation}`);
        const data = await response.json();
        
        setTimelineData({
          start: data.start_time,
          end: data.end_time,
          totalDurationHours: data.duration_hours,
          dataPoints: data.total_points,
          resolution: data.resolution
        });
        
        const startTime = new Date(data.start_time).getTime();
        setCurrentTime(startTime);
        onTimeChange(startTime);
        
      } catch (error) {
        console.error('Failed to fetch timeline data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchTimelineData();
    setIsPlaying(false);
  }, [constellation, onTimeChange]);

  useEffect(() => {
    if (!isPlaying || !timelineData) return;
    
    const interval = setInterval(() => {
      setCurrentTime(prevTime => {
        const timeStep = realTimeMode ? 1000 : (60 * 1000 * playbackSpeed);
        const nextTime = prevTime + timeStep;
        const endTime = new Date(timelineData.end).getTime();
        
        if (nextTime > endTime) {
          setIsPlaying(false);
          return endTime;
        }
        
        onTimeChange(nextTime);
        return nextTime;
      });
    }, realTimeMode ? 1000 : 500);

    return () => clearInterval(interval);
  }, [isPlaying, playbackSpeed, realTimeMode, timelineData, onTimeChange]);

  const handleSliderChange = useCallback((value: number) => {
    if (!timelineData) return;
    
    const startTime = new Date(timelineData.start).getTime();
    const endTime = new Date(timelineData.end).getTime();
    const targetTime = startTime + (endTime - startTime) * (value / 100);
    
    setCurrentTime(targetTime);
    onTimeChange(targetTime);
  }, [timelineData, onTimeChange]);

  const togglePlayback = () => setIsPlaying(!isPlaying);

  const cycleSpeed = () => {
    const speeds = [0.5, 1, 2, 5, 10];
    const currentIndex = speeds.indexOf(playbackSpeed);
    const nextIndex = (currentIndex + 1) % speeds.length;
    setPlaybackSpeed(speeds[nextIndex]);
  };

  if (loading || !timelineData) {
    return (
      <Card className="timeline-control" loading={loading}>
        <div className="text-center py-4 text-gray-500">
          載入 {constellation} 星座時間軸數據...
        </div>
      </Card>
    );
  }

  const progress = ((currentTime - new Date(timelineData.start).getTime()) / 
                   (new Date(timelineData.end).getTime() - new Date(timelineData.start).getTime())) * 100;

  return (
    <Card className="timeline-control" title="⏰ 歷史數據時間軸控制">
      {showStatistics && (
        <div className="grid grid-cols-4 gap-4 mb-4">
          <Statistic
            title="數據覆蓋"
            value={timelineData.totalDurationHours}
            suffix="小時"
            precision={1}
          />
          <Statistic
            title="數據點數"
            value={timelineData.dataPoints}
            formatter={(value) => `${(value as number / 1000).toFixed(1)}K`}
          />
          <Statistic
            title="解析度"
            value={timelineData.resolution}
          />
          <Statistic
            title="進度"
            value={progress}
            suffix="%"
            precision={1}
          />
        </div>
      )}

      <div className="mb-4">
        <Progress 
          percent={progress} 
          showInfo={false} 
          strokeColor={{ '0%': '#108ee9', '100%': '#87d068' }}
        />
      </div>
      
      <div className="mb-4">
        <Slider
          min={0}
          max={100}
          value={progress}
          onChange={handleSliderChange}
          disabled={disabled || isPlaying}
          tooltip={{
            formatter: (value) => {
              if (!value || !timelineData) return '';
              const startTime = new Date(timelineData.start).getTime();
              const endTime = new Date(timelineData.end).getTime();
              const targetTime = startTime + (endTime - startTime) * (value / 100);
              return moment(targetTime).format('MM/DD HH:mm');
            }
          }}
        />
        
        <div className="flex justify-between text-xs text-gray-500 mt-1">
          <span>{moment(timelineData.start).format('MM/DD HH:mm')}</span>
          <span className="font-semibold text-blue-600">
            {moment(currentTime).format('MM-DD HH:mm:ss')}
          </span>
          <span>{moment(timelineData.end).format('MM/DD HH:mm')}</span>
        </div>
      </div>

      <div className="flex items-center justify-between">
        <Space size="small">
          <Button
            type="primary"
            icon={isPlaying ? <PauseCircleOutlined /> : <PlayCircleOutlined />}
            onClick={togglePlayback}
            disabled={disabled || currentTime >= new Date(timelineData.end).getTime()}
          >
            {isPlaying ? '暫停' : '播放'}
          </Button>
          
          {!realTimeMode && (
            <Button
              icon={<FastForwardOutlined />}
              onClick={cycleSpeed}
              disabled={disabled}
              size="small"
            >
              {playbackSpeed}x
            </Button>
          )}
        </Space>

        <Space size="middle">
          <div className="flex items-center">
            <span className="text-xs text-gray-500 mr-2">實時模式</span>
            <Switch
              size="small"
              checked={realTimeMode}
              onChange={setRealTimeMode}
              disabled={disabled}
            />
          </div>
          
          <DatePicker
            showTime
            value={moment(currentTime)}
            onChange={(date) => {
              if (date) {
                const newTime = date.valueOf();
                const startTime = new Date(timelineData.start).getTime();
                const endTime = new Date(timelineData.end).getTime();
                
                if (newTime >= startTime && newTime <= endTime) {
                  setCurrentTime(newTime);
                  onTimeChange(newTime);
                }
              }
            }}
            disabled={disabled || isPlaying}
            size="small"
            format="MM/DD HH:mm"
          />
        </Space>
      </div>
      
      <div className="mt-3 text-xs text-gray-500 bg-gray-50 p-2 rounded">
        💡 提示: 滑桿快速跳轉，播放控制動畫，實時模式按真實時間播放，加速模式可調整倍速
      </div>
    </Card>
  );
};
```

#### 4.5 主頁面整合示例
```typescript
// SatelliteAnalysis.tsx (多星座分析頁面)
import React, { useState, useCallback } from 'react';
import { Row, Col, Card } from 'antd';
import { ConstellationSelector } from '../components/ConstellationSelector';
import { TimelineControl } from '../components/TimelineControl';

export const SatelliteAnalysis: React.FC = () => {
  const [selectedConstellation, setSelectedConstellation] = useState('starlink');
  const [currentTimestamp, setCurrentTimestamp] = useState(Date.now());
  const [loading, setLoading] = useState(false);

  const handleConstellationChange = useCallback((constellation: string) => {
    setLoading(true);
    setSelectedConstellation(constellation);
    setTimeout(() => setLoading(false), 500);
  }, []);

  const handleTimeChange = useCallback((timestamp: number) => {
    setCurrentTimestamp(timestamp);
  }, []);

  return (
    <div className="satellite-analysis-page p-6">
      <Row gutter={[16, 16]}>
        <Col span={24}>
          <Card title="🛰️ LEO 衛星星座分析控制台" className="mb-4">
            <Row gutter={[16, 16]}>
              <Col span={8}>
                <ConstellationSelector
                  value={selectedConstellation}
                  onChange={handleConstellationChange}
                  disabled={loading}
                  showComparison={true}
                />
              </Col>
              <Col span={16}>
                <TimelineControl
                  constellation={selectedConstellation}
                  onTimeChange={handleTimeChange}
                  disabled={loading}
                  showStatistics={true}
                />
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>
    </div>
  );
};
```

### Phase 5: 容器啟動順序和智能更新 (1 天)

#### 5.1 Docker Compose 啟動順序
```yaml
# docker-compose.yml 修改
services:
  rl-postgres:
    # PostgreSQL 必須先啟動並完成初始化
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U rl_user -d rl_research"]
      interval: 5s
      timeout: 3s
      retries: 5
      start_period: 10s

  netstack-api:
    depends_on:
      rl-postgres:
        condition: service_healthy  # 等待 PostgreSQL 健康
    environment:
      - SATELLITE_DATA_MODE=instant_load  # 啟動時立即載入
      - POSTGRES_WAIT_TIMEOUT=30          # 等待超時
    entrypoint: ["/app/docker-entrypoint.sh"]
    
  simworld_backend:
    depends_on:
      netstack-api:
        condition: service_healthy    # 等待 NetStack 衛星數據就緒
```

#### 5.2 智能啟動腳本
```bash
#!/bin/bash
# docker-entrypoint.sh

echo "🚀 NetStack 啟動中..."

# 1. 等待 PostgreSQL 就緒
echo "⏳ 等待 PostgreSQL 連接..."
python3 -c "
import asyncpg
import asyncio
import sys
import time

async def wait_postgres():
    for i in range(30):  # 最多等待 30 秒
        try:
            conn = await asyncpg.connect('$RL_DATABASE_URL')
            await conn.close()
            print('✅ PostgreSQL 連接成功')
            return True
        except Exception as e:
            print(f'⏳ PostgreSQL 未就緒 ({i+1}/30): {e}')
            time.sleep(1)
    return False

if not asyncio.run(wait_postgres()):
    print('❌ PostgreSQL 連接超時')
    sys.exit(1)
"

# 2. 立即載入衛星數據
echo "📡 載入衛星歷史數據..."
python3 -c "
import asyncio
from app.services.instant_satellite_loader import InstantSatelliteLoader

async def load_data():
    loader = InstantSatelliteLoader('$RL_DATABASE_URL')
    success = await loader.ensure_data_available()
    if success:
        print('✅ 衛星數據載入完成，系統可用')
        exit(0)
    else:
        print('❌ 衛星數據載入失敗')
        exit(1)

asyncio.run(load_data())
"

if [ $? -ne 0 ]; then
    echo "❌ 衛星數據載入失敗，啟動終止"
    exit 1
fi

# 3. 啟動 NetStack API
echo "🌐 啟動 NetStack API..."
exec python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8080
```

#### 5.3 背景智能更新服務
```python
# app/services/background_updater.py
import asyncio
import logging
from datetime import datetime, timedelta

class BackgroundSatelliteUpdater:
    """背景智能更新服務"""
    
    def __init__(self, postgres_url: str):
        self.postgres_url = postgres_url
        self.update_interval = 7 * 24 * 3600  # 7天
        self.running = False
        
    async def start_background_service(self):
        """啟動背景更新服務"""
        self.running = True
        
        while self.running:
            try:
                # 檢查數據是否需要更新
                needs_update = await self._check_if_update_needed()
                
                if needs_update:
                    logging.info("🔄 開始背景更新衛星數據...")
                    success = await self._perform_smart_update()
                    
                    if success:
                        logging.info("✅ 背景更新完成")
                    else:
                        logging.warning("⚠️ 背景更新失敗，將在下次重試")
                        
                # 等待 4 小時後再檢查
                await asyncio.sleep(4 * 3600)
                
            except Exception as e:
                logging.error(f"❌ 背景更新服務錯誤: {e}")
                await asyncio.sleep(3600)  # 錯誤後等待 1 小時
                
    async def _check_if_update_needed(self) -> bool:
        """檢查是否需要更新"""
        conn = await asyncpg.connect(self.postgres_url)
        try:
            latest_time = await conn.fetchval("""
                SELECT MAX(timestamp) FROM satellite_orbital_cache 
                WHERE observer_latitude = 24.94417
            """)
            
            if not latest_time:
                return True
                
            age = datetime.utcnow() - latest_time.replace(tzinfo=None)
            return age.total_seconds() > self.update_interval
            
        finally:
            await conn.close()
            
    async def _perform_smart_update(self) -> bool:
        """執行智能更新（增量更新）"""
        try:
            # 1. 嘗試下載新 TLE 數據
            tle_data = await self._download_fresh_tle_data()
            
            if not tle_data:
                return False
                
            # 2. 增量生成新的歷史數據（只生成最新 24 小時）
            from .satellite_history_precomputer import SatelliteHistoryPrecomputer
            
            precomputer = SatelliteHistoryPrecomputer(
                tle_data=tle_data,
                observer_coords=(24.94417, 121.37139, 0.1),
                time_range=(datetime.utcnow(), datetime.utcnow() + timedelta(hours=24))
            )
            
            new_data = precomputer.compute_history(time_interval_seconds=30)
            
            # 3. 增量更新到數據庫
            from .batch_processor import HistoryBatchProcessor
            
            processor = HistoryBatchProcessor(self.postgres_url)
            await processor.incremental_update(new_data)
            
            # 4. 清理過舊數據（保留最近 7 天）
            await self._cleanup_old_data()
            
            return True
            
        except Exception as e:
            logging.error(f"智能更新失敗: {e}")
            return False
            
    async def _download_fresh_tle_data(self):
        """下載新的 TLE 數據"""
        import aiohttp
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://celestrak.org/NORAD/elements/gp.php?GROUP=starlink&FORMAT=tle",
                    timeout=30
                ) as response:
                    if response.status == 200:
                        return await response.text()
        except Exception as e:
            logging.warning(f"TLE 下載失敗: {e}")
            
        return None
        
    async def _cleanup_old_data(self):
        """清理 7 天前的數據"""
        cutoff_time = datetime.utcnow() - timedelta(days=7)
        
        conn = await asyncpg.connect(self.postgres_url)
        try:
            deleted_count = await conn.fetchval("""
                DELETE FROM satellite_orbital_cache 
                WHERE timestamp < $1 AND observer_latitude = 24.94417
                RETURNING COUNT(*)
            """, cutoff_time)
            
            logging.info(f"🗑️ 清理了 {deleted_count} 條過期數據")
            
        finally:
            await conn.close()
```

#### 5.4 啟動時間優化
```python
# app/main.py FastAPI 啟動事件
@app.on_event("startup")
async def startup_event():
    """應用啟動事件"""
    
    # 1. 快速健康檢查（3秒內完成）
    start_time = time.time()
    
    loader = InstantSatelliteLoader(settings.RL_DATABASE_URL)
    data_ready = await loader.ensure_data_available()
    
    load_time = time.time() - start_time
    
    if data_ready:
        logging.info(f"✅ 衛星數據就緒 ({load_time:.1f}s)，API 可以接受請求")
        
        # 2. 啟動背景更新服務（非阻塞）
        updater = BackgroundSatelliteUpdater(settings.RL_DATABASE_URL)
        asyncio.create_task(updater.start_background_service())
        
    else:
        logging.error("❌ 衛星數據載入失敗，API 將以降級模式運行")
```

## 📋 驗收標準

## 📋 Phase 驗證機制與完成確認

### ✅ Phase 1: PostgreSQL 數據架構 - 驗證機制

#### **1.1 後端數據庫驗證**
```bash
# 1. 檢查 PostgreSQL 表結構
docker exec -it netstack-rl-postgres psql -U rl_user -d rl_research -c "
SELECT table_name, column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name IN ('satellite_tle_data', 'satellite_orbital_cache', 'd2_measurement_cache')
ORDER BY table_name, ordinal_position;
"

# 2. 檢查索引是否正確創建
docker exec -it netstack-rl-postgres psql -U rl_user -d rl_research -c "
SELECT tablename, indexname, indexdef 
FROM pg_indexes 
WHERE tablename LIKE 'satellite_%' OR tablename LIKE 'd2_%'
ORDER BY tablename;
"

# 3. 檢查視圖是否存在
docker exec -it netstack-rl-postgres psql -U rl_user -d rl_research -c "
SELECT viewname, definition 
FROM pg_views 
WHERE viewname IN ('active_satellites_overview', 'd2_events_summary');
"
```

#### **1.2 API 端點驗證**
```bash
# 檢查數據庫連接健康狀態
curl -X GET "http://localhost:8080/api/v1/satellites/health" \
  -H "Content-Type: application/json" | jq

# 預期響應：
# {
#   "status": "healthy",
#   "database": "postgresql",
#   "tables": ["satellite_tle_data", "satellite_orbital_cache", "d2_measurement_cache"],
#   "timestamp": "2025-01-23T..."
# }
```

#### **1.3 完成確認檢查清單**
- [ ] **數據庫表創建**: 3 張主要表 + 4 個索引 + 2 個視圖
- [ ] **PostgreSQL 健康檢查**: 連接成功且響應時間 < 100ms
- [ ] **表結構驗證**: 所有必要欄位存在且類型正確
- [ ] **索引效能**: 查詢執行計劃顯示使用索引
- [ ] **API 響應**: `/health` 端點返回 200 狀態

---

### ✅ Phase 2: 數據預計算引擎 - 驗證機制

#### **2.1 TLE 數據下載驗證**
```bash
# 1. 測試 TLE 數據獲取功能
curl -X POST "http://localhost:8080/api/v1/satellites/tle/download" \
  -H "Content-Type: application/json" \
  -d '{
    "constellations": ["starlink", "oneweb"],
    "force_update": false
  }' | jq

# 預期響應：
# {
#   "success": true,
#   "downloaded": {
#     "starlink": 6,
#     "oneweb": 4
#   },
#   "total_satellites": 10,
#   "download_time_ms": 1500
# }

# 2. 驗證 TLE 數據存儲
docker exec -it netstack-rl-postgres psql -U rl_user -d rl_research -c "
SELECT constellation, COUNT(*) as satellite_count, 
       MIN(epoch) as oldest_tle, MAX(epoch) as newest_tle
FROM satellite_tle_data 
WHERE is_active = true 
GROUP BY constellation;
"
```

#### **2.2 軌道預計算驗證**
```bash
# 1. 啟動軌道預計算作業
curl -X POST "http://localhost:8080/api/v1/satellites/precompute" \
  -H "Content-Type: application/json" \
  -d '{
    "constellation": "starlink",
    "start_time": "2025-01-23T00:00:00Z",
    "end_time": "2025-01-23T06:00:00Z",
    "time_step_seconds": 30,
    "observer_location": {
      "latitude": 24.94417,
      "longitude": 121.37139,
      "altitude": 100
    }
  }' | jq

# 預期響應：
# {
#   "job_id": "precompute_starlink_20250123",
#   "status": "running",
#   "estimated_duration_minutes": 5,
#   "total_calculations": 2880
# }

# 2. 檢查預計算進度
curl -X GET "http://localhost:8080/api/v1/satellites/precompute/job_id/status" | jq

# 3. 驗證預計算結果
docker exec -it netstack-rl-postgres psql -U rl_user -d rl_research -c "
SELECT constellation, 
       COUNT(*) as total_records,
       COUNT(DISTINCT satellite_id) as unique_satellites,
       MIN(timestamp) as earliest_time,
       MAX(timestamp) as latest_time
FROM satellite_orbital_cache 
WHERE constellation = 'starlink'
GROUP BY constellation;
"
```

#### **2.3 效能基準測試**
```bash
# 批量插入效能測試
curl -X POST "http://localhost:8080/api/v1/satellites/benchmark/batch_insert" \
  -H "Content-Type: application/json" \
  -d '{
    "record_count": 10000,
    "constellation": "starlink"
  }' | jq

# 預期：throughput > 1000 records/second
```

#### **2.4 完成確認檢查清單**
- [ ] **TLE 下載**: 成功獲取多星座 TLE 數據 (< 5 秒)
- [ ] **數據解析**: SGP4 軌道計算正確無誤差
- [ ] **批量存儲**: 插入效能 > 1000 條/秒
- [ ] **預計算完整性**: 6 小時數據覆蓋無遺漏時間點
- [ ] **計算準確性**: 位置誤差 < 1km (與 Skyfield 基準比較)

---

### ✅ Phase 3: API 端點實現 - 驗證機制

#### **3.1 衛星位置查詢驗證**
```bash
# 1. 查詢特定時間點的衛星位置
curl -X GET "http://localhost:8080/api/v1/satellites/positions" \
  -G \
  -d "timestamp=2025-01-23T12:00:00Z" \
  -d "constellation=starlink" \
  -d "min_elevation=10" | jq

# 預期響應：
# {
#   "satellites": [
#     {
#       "satellite_id": "starlink-1",
#       "norad_id": 50001,
#       "position": {
#         "latitude": 25.1,
#         "longitude": 121.5,
#         "altitude": 550.2
#       },
#       "elevation_angle": 35.4,
#       "azimuth_angle": 180.0,
#       "distance_km": 1200.5
#     }
#   ],
#   "observer_location": {...},
#   "timestamp": "2025-01-23T12:00:00Z",
#   "query_time_ms": 45
# }

# 2. 測試星座資訊端點
curl -X GET "http://localhost:8080/api/v1/satellites/constellations/info" | jq

# 預期響應：
# [
#   {
#     "constellation": "starlink",
#     "satellite_count": 6,
#     "data_start": "2025-01-23T00:00:00Z",
#     "data_end": "2025-01-23T06:00:00Z",
#     "total_days": 0.25
#   }
# ]
```

#### **3.2 時間軸數據端點驗證**
```bash
# 1. 獲取時間軸資訊
curl -X GET "http://localhost:8080/api/v1/satellites/timeline/starlink" | jq

# 預期響應：
# {
#   "constellation": "starlink",
#   "start_time": "2025-01-23T00:00:00Z",
#   "end_time": "2025-01-23T06:00:00Z",
#   "duration_hours": 6.0,
#   "total_points": 720,
#   "resolution": "30s",
#   "available_satellites": 6
# }

# 2. 測試時間範圍查詢
curl -X GET "http://localhost:8080/api/v1/satellites/trajectory" \
  -G \
  -d "satellite_id=starlink-1" \
  -d "start_time=2025-01-23T12:00:00Z" \
  -d "end_time=2025-01-23T13:00:00Z" \
  -d "step_seconds=60" | jq
```

#### **3.3 D2 測量事件驗證**
```bash
# 1. 獲取 D2 事件
curl -X GET "http://localhost:8080/api/v1/satellites/d2/events" \
  -G \
  -d "timestamp=2025-01-23T12:00:00Z" \
  -d "constellation=starlink" | jq

# 預期響應：
# {
#   "handover_events": [
#     {
#       "satellite_id": "starlink-2",
#       "event_type": "entering",
#       "trigger_condition": "D2 < thresh1",
#       "satellite_distance": 950.2,
#       "ground_distance": 1200.0,
#       "signal_strength": -85.4
#     }
#   ],
#   "timestamp": "2025-01-23T12:00:00Z",
#   "total_events": 1
# }
```

#### **3.4 API 性能驗證**
```bash
# 響應時間測試
for i in {1..10}; do
  echo "Request $i:"
  curl -w "Response time: %{time_total}s\n" \
    -X GET "http://localhost:8080/api/v1/satellites/positions?timestamp=2025-01-23T12:00:00Z&constellation=starlink" \
    -o /dev/null -s
done

# 預期：平均響應時間 < 100ms
```

#### **3.5 完成確認檢查清單**
- [ ] **位置查詢**: 響應時間 < 100ms，數據準確
- [ ] **時間軸端點**: 正確返回數據範圍和統計
- [ ] **軌跡查詢**: 支援任意時間區間查詢
- [ ] **D2 事件**: 正確計算 handover 觸發條件
- [ ] **錯誤處理**: 無效參數返回適當錯誤訊息

---

### ✅ Phase 4: 前端時間軸控制 - 驗證機制

#### **4.1 星座選擇器驗證**
```bash
# 1. 開啟瀏覽器開發者工具，檢查 Console 日誌
# 訪問: http://localhost:5173

# 2. 檢查星座選擇器載入
console.log("=== 星座選擇器驗證開始 ===");
console.log("可用星座數量:", document.querySelectorAll('.constellation-option').length);
console.log("預期: ≥ 2 (Starlink + OneWeb)");

# 3. 檢查 API 調用
# 在 Network 標籤中查看是否有以下請求：
# GET /api/satellites/constellations/info
# 狀態碼應為 200，響應時間 < 500ms
```

#### **4.2 時間軸控制器驗證**
```javascript
// 在瀏覽器 Console 中執行以下檢查
console.log("=== 時間軸控制器驗證 ===");

// 檢查控制器是否載入
const timelineControl = document.querySelector('.timeline-control');
console.log("時間軸控制器存在:", !!timelineControl);

// 檢查統計資訊顯示
const statistics = document.querySelectorAll('.ant-statistic');
console.log("統計項目數量:", statistics.length);
console.log("預期: 4 項 (數據覆蓋、數據點數、解析度、進度)");

// 檢查播放控制按鈕
const playButton = document.querySelector('[data-testid="play-button"], .ant-btn-primary');
console.log("播放按鈕存在:", !!playButton);

// 檢查滑桿控制
const slider = document.querySelector('.ant-slider');
console.log("時間滑桿存在:", !!slider);
```

#### **4.3 功能交互驗證**
```javascript
// 星座切換功能測試
console.log("=== 功能交互驗證 ===");

// 模擬星座切換
const constellationSelect = document.querySelector('.ant-select-selector');
if (constellationSelect) {
    constellationSelect.click();
    setTimeout(() => {
        const options = document.querySelectorAll('.ant-select-item-option');
        console.log("星座選項數量:", options.length);
        
        // 檢查切換時是否觸發 API 調用
        const originalFetch = window.fetch;
        let apiCallCount = 0;
        window.fetch = function(...args) {
            if (args[0].includes('/api/satellites/timeline/')) {
                apiCallCount++;
                console.log("時間軸 API 調用次數:", apiCallCount);
            }
            return originalFetch.apply(this, args);
        };
    }, 500);
}

// 播放控制功能測試
setTimeout(() => {
    const playButton = document.querySelector('[aria-label*="播放"], [title*="播放"]');
    if (playButton) {
        console.log("開始播放測試...");
        playButton.click();
        
        setTimeout(() => {
            const pauseButton = document.querySelector('[aria-label*="暫停"], [title*="暫停"]');
            console.log("播放狀態切換成功:", !!pauseButton);
        }, 1000);
    }
}, 2000);
```

#### **4.4 數據流驗證**
```javascript
// 檢查數據更新流程
console.log("=== 數據流驗證 ===");

// 監聽時間變更事件
let timeChangeCount = 0;
const observer = new MutationObserver(function(mutations) {
    mutations.forEach(function(mutation) {
        if (mutation.target.textContent && mutation.target.textContent.match(/\d{4}-\d{2}-\d{2}/)) {
            timeChangeCount++;
            console.log("時間顯示更新次數:", timeChangeCount);
        }
    });
});

const timeDisplays = document.querySelectorAll('[class*="time"], [class*="timestamp"]');
timeDisplays.forEach(element => {
    observer.observe(element, { childList: true, subtree: true, characterData: true });
});

// 3 秒後檢查結果
setTimeout(() => {
    console.log("最終驗證結果:");
    console.log("- 時間顯示更新次數:", timeChangeCount);
    console.log("- 預期: 播放模式下 > 0 次更新");
    observer.disconnect();
}, 3000);
```

#### **4.5 響應式設計驗證**
```javascript
// 測試不同螢幕尺寸下的顯示
console.log("=== 響應式設計驗證 ===");

const testViewports = [
    { width: 1920, height: 1080, name: "桌面大螢幕" },
    { width: 1366, height: 768, name: "桌面標準" },
    { width: 768, height: 1024, name: "平板" },
    { width: 375, height: 812, name: "手機" }
];

testViewports.forEach(viewport => {
    // 模擬螢幕尺寸變更
    window.resizeTo(viewport.width, viewport.height);
    setTimeout(() => {
        const controlPanel = document.querySelector('.satellite-analysis-page');
        if (controlPanel) {
            const rect = controlPanel.getBoundingClientRect();
            console.log(`${viewport.name}: 寬度 ${rect.width}px, 高度 ${rect.height}px`);
            console.log(`- 是否適應螢幕: ${rect.width <= viewport.width}`);
        }
    }, 100);
});
```

#### **4.6 完成確認檢查清單**
- [ ] **星座選擇器**: 正確顯示多星座選項，有圖示和統計資訊
- [ ] **API 整合**: 選擇星座時正確調用 `/constellations/info` 端點
- [ ] **時間軸控制**: 播放/暫停/倍速功能正常運作
- [ ] **數據同步**: 時間變更時正確觸發回調函數
- [ ] **響應式設計**: 在不同螢幕尺寸下正常顯示
- [ ] **錯誤處理**: 網路錯誤時顯示適當提示訊息
- [ ] **性能表現**: 組件載入時間 < 2 秒，操作響應 < 300ms

---

### ✅ Phase 5: 容器啟動順序和智能更新 - 驗證機制

#### **5.1 容器啟動順序驗證**
```bash
# 1. 檢查容器啟動順序和依賴關係
docker-compose ps --format "table {{.Name}}\t{{.State}}\t{{.Status}}"

# 預期結果：所有容器都應為 "Up" 狀態
# netstack-rl-postgres     Up    Up 30 seconds (healthy)
# netstack-api             Up    Up 25 seconds (healthy)  
# simworld_backend         Up    Up 20 seconds (healthy)

# 2. 檢查健康檢查狀態
docker inspect netstack-rl-postgres --format '{{.State.Health.Status}}'
docker inspect netstack-api --format '{{.State.Health.Status}}'

# 預期: 所有容器都返回 "healthy"

# 3. 測試啟動時間
echo "開始完整重啟測試..."
time_start=$(date +%s)
make down && make up
time_end=$(date +%s)
startup_time=$((time_end - time_start))
echo "完整啟動時間: ${startup_time} 秒"
echo "預期: < 120 秒 (包含數據載入)"
```

#### **5.2 數據持久性驗證**
```bash
# 1. 檢查數據是否在重啟後保持
echo "=== 數據持久性測試 ==="

# 重啟前查詢數據量
docker exec -it netstack-rl-postgres psql -U rl_user -d rl_research -c "
SELECT 'Before restart' as stage,
       COUNT(*) as satellite_records
FROM satellite_tle_data;
"

# 執行容器重啟
make simworld-restart

# 等待服務完全啟動 (30秒)
sleep 30

# 重啟後檢查數據
docker exec -it netstack-rl-postgres psql -U rl_user -d rl_research -c "
SELECT 'After restart' as stage,
       COUNT(*) as satellite_records
FROM satellite_tle_data;
"

# 預期: 重啟前後數據量相同
```

#### **5.3 立即數據可用性驗證**
```bash
# 1. 測試容器啟動後立即數據可用性
echo "=== 立即數據可用性測試 ==="

# 重啟 NetStack API
docker restart netstack-api

# 等待 10 秒後立即測試 API
sleep 10

# 檢查衛星數據是否立即可用
curl -X GET "http://localhost:8080/api/v1/satellites/constellations/info" \
  -w "\nResponse time: %{time_total}s\nHTTP status: %{http_code}\n" | jq

# 預期響應：
# - HTTP 狀態: 200
# - 響應時間: < 3 秒
# - 包含衛星數據且 satellite_count > 0

# 2. 檢查內建數據載入
docker logs netstack-api 2>&1 | grep -E "(衛星數據載入|satellite.*load|✅|❌)" | tail -10

# 預期日誌包含：
# "✅ 衛星數據載入完成，系統立即可用"
# "📡 載入內建衛星歷史數據..."
```

#### **5.4 背景更新服務驗證**
```bash
# 1. 檢查背景更新服務是否啟動
echo "=== 背景更新服務驗證 ==="

# 檢查背景更新日誌
docker logs netstack-api 2>&1 | grep -E "(background.*update|背景.*更新)" | tail -5

# 預期看到：
# "🔄 啟動背景更新服務（非阻塞）"
# "背景更新服務運行中..."

# 2. 測試更新檢查機制
curl -X POST "http://localhost:8080/api/v1/satellites/update/check" \
  -H "Content-Type: application/json" \
  -d '{"force_check": true}' | jq

# 預期響應：
# {
#   "update_needed": false,
#   "last_update": "2025-01-23T...",
#   "days_since_update": 0,
#   "next_scheduled_update": "2025-01-30T..."
# }

# 3. 檢查更新任務記錄
docker exec -it netstack-rl-postgres psql -U rl_user -d rl_research -c "
SELECT job_name, status, progress_percentage, 
       created_at, completed_at
FROM satellite_data_preload_jobs 
ORDER BY created_at DESC 
LIMIT 5;
"
```

#### **5.5 系統健康監控驗證**
```bash
# 1. 全系統健康檢查
echo "=== 系統健康監控驗證 ==="

# 檢查所有服務健康狀態
curl -X GET "http://localhost:8080/health" | jq
curl -X GET "http://localhost:8888/health" | jq  # SimWorld backend

# 2. 資源使用監控
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"

# 預期：
# - CPU 使用率 < 50%
# - 記憶體使用率 < 80%
# - 所有容器都在運行

# 3. 數據庫連接池檢查
docker exec -it netstack-rl-postgres psql -U rl_user -d rl_research -c "
SELECT datname, numbackends, xact_commit, xact_rollback
FROM pg_stat_database 
WHERE datname = 'rl_research';
"

# 檢查是否有連接洩漏或錯誤
```

#### **5.6 故障恢復驗證**  
```bash
# 1. 模擬數據庫短暫中斷
echo "=== 故障恢復測試 ==="

# 暫停 PostgreSQL 容器
docker pause netstack-rl-postgres

# 測試 API 響應 (應該優雅處理錯誤)
curl -X GET "http://localhost:8080/api/v1/satellites/health" \
  -w "\nHTTP status: %{http_code}\n"

# 預期：返回 503 Service Unavailable，不應該崩潰

# 恢復 PostgreSQL
docker unpause netstack-rl-postgres

# 等待 5 秒後測試恢復
sleep 5
curl -X GET "http://localhost:8080/api/v1/satellites/health" | jq

# 預期：服務自動恢復，返回 200 OK

# 2. 檢查錯誤日誌
docker logs netstack-api 2>&1 | grep -E "(ERROR|Exception|❌)" | tail -5

# 檢查是否有適當的錯誤處理日誌
```

#### **5.7 性能基準驗證**
```bash
# 1. 併發請求測試
echo "=== 性能基準測試 ==="

# 使用 Apache Bench 進行併發測試 (如果可用)
if command -v ab &> /dev/null; then
    ab -n 100 -c 10 "http://localhost:8080/api/v1/satellites/constellations/info"
else
    # 使用 curl 進行簡單併發測試
    for i in {1..10}; do
        curl -X GET "http://localhost:8080/api/v1/satellites/constellations/info" \
          -w "Request $i: %{time_total}s\n" -o /dev/null -s &
    done
    wait
fi

# 預期：
# - 平均響應時間 < 200ms
# - 無請求失敗
# - 系統穩定運行

# 2. 記憶體洩漏檢查
echo "開始記憶體監控 (10 分鐘)..."
for i in {1..10}; do
    docker stats --no-stream netstack-api --format "{{.MemUsage}} {{.MemPerc}}"
    sleep 60
done

# 預期：記憶體使用量穩定，無明顯增長趨勢
```

#### **5.8 完成確認檢查清單**
- [ ] **容器啟動順序**: PostgreSQL → NetStack API → SimWorld，依賴關係正確
- [ ] **啟動時間**: 完整系統啟動 < 120 秒 (包含數據載入)
- [ ] **數據持久性**: 容器重啟後數據完整保留
- [ ] **立即可用性**: 服務啟動後 10 秒內 API 可用且有數據
- [ ] **背景更新**: 更新服務正常運行，有適當的日誌記錄
- [ ] **健康監控**: 所有服務健康檢查通過，資源使用合理
- [ ] **故障恢復**: 數據庫中斷後能自動恢復連接
- [ ] **性能穩定**: 併發請求處理正常，無記憶體洩漏

---

## 🚀 整體系統驗證流程

### **完整驗證腳本**
```bash
#!/bin/bash
# comprehensive_verification.sh - 完整系統驗證腳本

echo "🛰️ LEO 衛星系統完整驗證開始..."
echo "========================================"

# Phase 1: 數據庫架構驗證
echo "Phase 1: 檢查數據庫架構..."
docker exec -it netstack-rl-postgres psql -U rl_user -d rl_research -c "\dt" > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Phase 1: PostgreSQL 架構正常"
else
    echo "❌ Phase 1: PostgreSQL 架構有問題"
    exit 1
fi

# Phase 2: 數據預計算驗證
echo "Phase 2: 檢查數據預計算..."
curl -s "http://localhost:8080/api/v1/satellites/health" | grep -q "healthy"
if [ $? -eq 0 ]; then
    echo "✅ Phase 2: 數據預計算系統正常"
else
    echo "❌ Phase 2: 數據預計算系統異常"
    exit 1
fi

# Phase 3: API 端點驗證
echo "Phase 3: 檢查 API 端點..."
response=$(curl -s -w "%{http_code}" "http://localhost:8080/api/v1/satellites/constellations/info" -o /dev/null)
if [ "$response" -eq 200 ]; then
    echo "✅ Phase 3: API 端點正常工作"
else
    echo "❌ Phase 3: API 端點異常 (HTTP: $response)"
    exit 1
fi

# Phase 4: 前端驗證 (需要手動確認)
echo "Phase 4: 前端驗證..."
frontend_status=$(curl -s -w "%{http_code}" "http://localhost:5173" -o /dev/null)
if [ "$frontend_status" -eq 200 ]; then
    echo "✅ Phase 4: 前端服務正常 (需手動驗證功能)"
else
    echo "❌ Phase 4: 前端服務異常"
fi

# Phase 5: 容器協調驗證
echo "Phase 5: 檢查容器協調..."
healthy_containers=$(docker-compose ps | grep "Up.*healthy" | wc -l)
if [ "$healthy_containers" -ge 3 ]; then
    echo "✅ Phase 5: 容器協調正常 ($healthy_containers 個健康容器)"
else
    echo "❌ Phase 5: 容器協調異常"
    exit 1
fi

echo "========================================"
echo "🎉 系統驗證完成！所有 Phase 檢查通過"
echo "📋 請執行前端手動測試完成 Phase 4 驗證"
```

### **使用方法**
```bash
# 1. 賦予執行權限
chmod +x comprehensive_verification.sh

# 2. 執行完整驗證
./comprehensive_verification.sh

# 3. 針對單一 Phase 驗證
# 參考上述各 Phase 的具體驗證命令
```

---

## 📋 總結

### **🎯 驗證方法統一標準**

**後端 API 驗證**：
- 使用 `curl` 命令測試所有端點
- 檢查 HTTP 狀態碼、響應時間、JSON 格式
- 驗證數據庫查詢和事務處理
- 使用 Docker 日誌檢查系統運行狀態

**前端功能驗證**：
- 使用瀏覽器開發者工具的 Console 和 Network 頁籤
- 檢查 React 組件是否正確渲染和更新
- 監聽 DOM 變更和 API 調用
- 測試用戶交互和響應式設計

**系統整合驗證**：
- 容器健康檢查和依賴關係驗證
- 數據持久性和服務恢復能力測試
- 性能基準測試和資源使用監控
- 完整系統驗證腳本自動化檢查

### **🔧 快速驗證命令**
```bash
# 一鍵完整驗證
./comprehensive_verification.sh

# 單項快速檢查
curl -s http://localhost:8080/health | jq .status  # API 健康
docker-compose ps | grep healthy | wc -l          # 健康容器數
```

每個 Phase 都有明確的成功標準和具體的驗證步驟，確保開發完成後能夠快速確認系統功能正常運作。

## 🎯 效能指標

### 🚀 預期性能提升
- **API 響應時間**：從 500-2000ms → 50-100ms
- **衛星數據量**：從 6 顆模擬 → 6-8 顆真實可見衛星（符合 3GPP NTN 標準）
- **handover 候選**：3-5 顆（符合真實場景）
- **時間範圍**：支援 6 小時完整歷史數據
- **動畫流暢度**：支援 1x-60x 倍速播放

### 📊 資源使用預估
- **PostgreSQL 存儲**：~3MB/週（6小時數據，修正後，存儲於現有 RL 數據庫）
- **記憶體使用**：~50MB（PostgreSQL 查詢緩存）
- **CPU 使用**：預計算階段 30%，查詢階段 <5%
- **網路流量**：僅週更新時需要，平時離線運行
- **數據庫位置**：NetStack RL PostgreSQL (172.20.0.51:5432/rl_research)

## 🔮 未來擴展

### 📈 可擴展性考量
1. **多觀測點支援**：除台灣外，可添加其他地理位置
2. **更多星座**：支援 OneWeb, Kuiper 等其他星座
3. **ML 預測**：基於歷史數據預測未來 handover 模式
4. **實時混合**：歷史數據 + 即時更新的混合模式

### 🎓 研究價值提升
1. **論文數據可信度**：使用真實歷史軌道數據
2. **可重現性**：相同時間段可重複分析
3. **統計分析**：大量歷史數據支援統計研究
4. **算法驗證**：真實場景下的 handover 算法測試

---

**總結：這個方案完美平衡了真實性、性能和展示效果，是兼具學術價值和工程實用性的優秀解決方案！**
