# 雙星座切換實施方案

## 🎯 雙星座切換整合目標

實現 Starlink 與 OneWeb 星座之間的無縫切換功能，為 D2 事件分析提供多星座對比能力，支援不同軌道特性的換手行為研究。

### 核心需求
- **即時星座切換**: 用戶可在 Starlink 和 OneWeb 之間即時切換
- **數據一致性**: 確保切換時 D2 測量數據的連續性和準確性
- **3D同步顯示**: 星座切換時 3D 立體圖同步更新衛星軌道
- **性能優化**: 切換響應時間 <2秒，無明顯延遲

## 🏗️ 技術架構設計

### 雙星座數據管理架構
```
┌─────────────── 統一星座管理器 ───────────────┐
│                                              │
│  ConstellationManager                        │
│  ├── activeConstellation: 'starlink'|'oneweb'│
│  ├── dataCache: Map<constellation, data>     │
│  └── switchController: SwitchController      │
│                                              │
└──────────────┬─────────────┬─────────────────┘
               │             │
      ┌────────▼──────┐  ┌──▼──────────┐
      │ Starlink 數據  │  │ OneWeb 數據  │
      │ - 40顆精選衛星 │  │ - 30顆精選衛星│
      │ - 550km軌道   │  │ - 1200km軌道 │
      │ - 53°傾角     │  │ - 87°傾角    │
      └───────────────┘  └─────────────┘
               │             │
               ▼             ▼
      ┌─────────────────────────────────┐
      │     統一 D2 事件處理引擎         │
      │ - SGP4 精確軌道計算             │
      │ - 120分鐘時間序列               │
      │ - 統一數據格式                  │
      └─────────────────────────────────┘
```

### 星座特性對比分析

| 特性指標 | Starlink | OneWeb | 對比分析 |
|----------|----------|---------|----------|
| **軌道高度** | 550km | 1200km | OneWeb 更高，信號延遲略增 |
| **軌道傾角** | 53° | 87° | OneWeb 近極地，覆蓋範圍更廣 |
| **衛星密度** | 7,992顆 | 651顆 | Starlink 高密度，換手頻繁 |
| **換手特性** | 快速換手 | 穩定連接 | 不同的換手行為模式 |
| **台灣覆蓋** | 良好 | 優秀 | OneWeb 極地軌道優勢明顯 |
| **研究價值** | 高密度分析 | 穩定性研究 | 互補的研究場景 |

## 🔧 前端實施方案

### 星座切換控制組件
```typescript
// 新建: ConstellationSwitcher.tsx
interface ConstellationSwitcherProps {
    currentConstellation: 'starlink' | 'oneweb'
    onSwitch: (constellation: string) => Promise<void>
    isLoading: boolean
    availableData: {
        starlink: { satellites: number, lastUpdate: string }
        oneweb: { satellites: number, lastUpdate: string }
    }
}

export const ConstellationSwitcher: React.FC<ConstellationSwitcherProps> = ({
    currentConstellation,
    onSwitch,
    isLoading,
    availableData
}) => {
    return (
        <div className="constellation-switcher-panel">
            <h4>🛰️ 星座選擇</h4>
            
            <div className="constellation-options">
                <div className="constellation-option starlink">
                    <input 
                        type="radio"
                        id="starlink"
                        name="constellation"
                        value="starlink"
                        checked={currentConstellation === 'starlink'}
                        onChange={() => onSwitch('starlink')}
                        disabled={isLoading}
                    />
                    <label htmlFor="starlink">
                        <div className="constellation-header">
                            <span className="constellation-name">Starlink</span>
                            <span className="constellation-badge starlink-badge">LEO</span>
                        </div>
                        <div className="constellation-details">
                            <p>🌍 軌道高度: 550km</p>
                            <p>📐 軌道傾角: 53°</p>
                            <p>🛰️ 可用衛星: {availableData.starlink.satellites}顆</p>
                            <p>⏰ 更新時間: {availableData.starlink.lastUpdate}</p>
                        </div>
                        <div className="constellation-characteristics">
                            <span className="char-tag">高密度</span>
                            <span className="char-tag">快速換手</span>
                        </div>
                    </label>
                </div>
                
                <div className="constellation-option oneweb">
                    <input 
                        type="radio"
                        id="oneweb"
                        name="constellation"
                        value="oneweb"
                        checked={currentConstellation === 'oneweb'}
                        onChange={() => onSwitch('oneweb')}
                        disabled={isLoading}
                    />
                    <label htmlFor="oneweb">
                        <div className="constellation-header">
                            <span className="constellation-name">OneWeb</span>
                            <span className="constellation-badge oneweb-badge">MEO</span>
                        </div>
                        <div className="constellation-details">
                            <p>🌍 軌道高度: 1200km</p>
                            <p>📐 軌道傾角: 87°</p>
                            <p>🛰️ 可用衛星: {availableData.oneweb.satellites}顆</p>
                            <p>⏰ 更新時間: {availableData.oneweb.lastUpdate}</p>
                        </div>
                        <div className="constellation-characteristics">
                            <span className="char-tag">極地覆蓋</span>
                            <span className="char-tag">穩定連接</span>
                        </div>
                    </label>
                </div>
            </div>
            
            {isLoading && (
                <div className="switching-loader">
                    <div className="spinner"></div>
                    <p>正在切換星座數據...</p>
                </div>
            )}
            
            <div className="switching-stats">
                <h5>💡 星座對比分析</h5>
                <div className="comparison-grid">
                    <div className="comparison-item">
                        <span className="metric">換手頻率</span>
                        <span className="starlink-value">高</span>
                        <span className="vs">vs</span>
                        <span className="oneweb-value">中</span>
                    </div>
                    <div className="comparison-item">
                        <span className="metric">信號穩定性</span>
                        <span className="starlink-value">中</span>
                        <span className="vs">vs</span>
                        <span className="oneweb-value">高</span>
                    </div>
                    <div className="comparison-item">
                        <span className="metric">覆蓋範圍</span>
                        <span className="starlink-value">良好</span>
                        <span className="vs">vs</span>
                        <span className="oneweb-value">優秀</span>
                    </div>
                </div>
            </div>
        </div>
    )
}
```

### D2圖表切換整合
```typescript
// 修改: EnhancedD2Chart.tsx 
export const EnhancedD2Chart: React.FC<D2ChartProps> = (props) => {
    const [constellation, setConstellation] = useState<'starlink' | 'oneweb'>('starlink')
    const [isLoadingSwitch, setIsLoadingSwitch] = useState(false)
    const [d2Data, setD2Data] = useState<D2TimeSeriesData>(null)
    
    // 統一時間控制器
    const timeController = useUnifiedTimeController()
    
    // 星座切換處理
    const handleConstellationSwitch = useCallback(async (newConstellation: string) => {
        if (newConstellation === constellation) return
        
        setIsLoadingSwitch(true)
        
        try {
            // 1. 暫停當前動畫
            timeController.pause()
            
            // 2. 獲取新星座數據
            const newData = await fetchD2Data({
                constellation: newConstellation,
                duration: 290,
                includeRawData: true
            })
            
            // 3. 更新數據和狀態
            setD2Data(newData)
            setConstellation(newConstellation as 'starlink' | 'oneweb')
            
            // 4. 重置時間控制器
            timeController.reset()
            
            // 5. 通知 3D 視圖同步切換
            timeController.notifyConstellationChange(newConstellation)
            
            // 6. 重新開始播放
            timeController.play()
            
        } catch (error) {
            console.error('星座切換失敗:', error)
            // 顯示錯誤提示
        } finally {
            setIsLoadingSwitch(false)
        }
    }, [constellation, timeController])
    
    return (
        <div className="enhanced-d2-chart-container">
            {/* 星座切換控制器 */}
            <ConstellationSwitcher
                currentConstellation={constellation}
                onSwitch={handleConstellationSwitch}
                isLoading={isLoadingSwitch}
                availableData={{
                    starlink: { satellites: 40, lastUpdate: d2Data?.metadata?.lastUpdate },
                    oneweb: { satellites: 30, lastUpdate: d2Data?.metadata?.lastUpdate }
                }}
            />
            
            {/* D2 圖表主體 */}
            <div className="d2-chart-wrapper">
                <Chart
                    type="line"
                    data={generateChartData(d2Data, constellation)}
                    options={generateChartOptions(constellation)}
                />
                
                {/* 數據來源資訊 */}
                <DataSourceInfoPanel
                    constellation={constellation}
                    dataMetadata={d2Data?.metadata}
                    sgp4Info={d2Data?.sgp4Info}
                />
            </div>
        </div>
    )
}
```

## 🌍 3D視圖同步切換

### 3D星座視覺化切換
```typescript
// 修改: Satellite3DVisualization.tsx
export const Satellite3DVisualization: React.FC<Satellite3DProps> = (props) => {
    const [constellation, setConstellation] = useState<'starlink' | 'oneweb'>('starlink')
    const [satelliteModels, setSatelliteModels] = useState<Map<string, THREE.Mesh>>(new Map())
    
    // 統一時間控制器
    const timeController = useUnifiedTimeController()
    
    // 監聽星座切換事件
    useEffect(() => {
        const handleConstellationChange = (newConstellation: string) => {
            switchConstellation3D(newConstellation)
        }
        
        timeController.onConstellationChange = handleConstellationChange
        
        return () => {
            timeController.onConstellationChange = null
        }
    }, [])
    
    // 3D星座切換處理
    const switchConstellation3D = useCallback(async (newConstellation: string) => {
        if (\!sceneRef.current || newConstellation === constellation) return
        
        try {
            // 1. 清除當前衛星模型
            satelliteModels.forEach((mesh, id) => {
                sceneRef.current?.remove(mesh)
            })
            setSatelliteModels(new Map())
            
            // 2. 更新軌道軌跡顏色方案
            const colorScheme = getConstellationColorScheme(newConstellation)
            updateOrbitTrailColors(colorScheme)
            
            // 3. 載入新星座衛星數據
            const satelliteData = await fetch3DSatelliteData(newConstellation)
            
            // 4. 創建新的衛星模型
            const newModels = new Map<string, THREE.Mesh>()
            
            satelliteData.satellites.forEach(satellite => {
                const mesh = createSatelliteMesh(satellite, colorScheme)
                sceneRef.current?.add(mesh)
                newModels.set(satellite.id, mesh)
            })
            
            setSatelliteModels(newModels)
            setConstellation(newConstellation as 'starlink' | 'oneweb')
            
            // 5. 更新攝影機視角（針對不同軌道高度）
            updateCameraForConstellation(newConstellation)
            
        } catch (error) {
            console.error('3D星座切換失敗:', error)
        }
    }, [constellation, satelliteModels])
    
    // 星座顏色方案
    const getConstellationColorScheme = (constellation: string) => {
        const schemes = {
            starlink: {
                primary: '#059669',      // 深綠色
                secondary: '#34D399',    // 淺綠色
                orbit: 'rgba(5, 150, 105, 0.3)',
                connection: '#10B981'
            },
            oneweb: {
                primary: '#2563EB',      // 深藍色
                secondary: '#60A5FA',    // 淺藍色  
                orbit: 'rgba(37, 99, 235, 0.3)',
                connection: '#3B82F6'
            }
        }
        return schemes[constellation] || schemes.starlink
    }
    
    return (
        <div className="satellite-3d-container">
            <canvas ref={canvasRef} />
            
            {/* 星座信息面板 */}
            <div className="constellation-info-overlay">
                <div className="active-constellation">
                    <span className={"constellation-indicator ${constellation}"}>
                        {constellation === 'starlink' ? '🟢' : '🔵'}
                    </span>
                    <span className="constellation-name">
                        {constellation === 'starlink' ? 'Starlink' : 'OneWeb'}
                    </span>
                </div>
                
                <div className="satellite-stats">
                    <p>可見衛星: {visibleSatellites.length}顆</p>
                    <p>主服務衛星: {activeSatellite?.name || '無'}</p>
                    <p>換手候選: {handoverCandidates.length}顆</p>
                </div>
            </div>
        </div>
    )
}
```

## 🚀 後端實施方案

### 雙星座數據服務
```python
# 新建: constellation_manager.py
from typing import Dict, Optional, Literal
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio

@dataclass
class ConstellationMetadata:
    name: str
    satellites_count: int
    orbital_altitude_km: int
    inclination_deg: float
    last_updated: datetime
    data_freshness: str
    coverage_area: str

class ConstellationManager:
    """統一星座管理服務"""
    
    def __init__(self):
        self.active_constellation: Literal['starlink', 'oneweb'] = 'starlink'
        self.data_cache: Dict[str, any] = {}
        self.metadata_cache: Dict[str, ConstellationMetadata] = {}
        self._initialize_metadata()
    
    def _initialize_metadata(self):
        """初始化星座元數據"""
        self.metadata_cache = {
            'starlink': ConstellationMetadata(
                name='Starlink',
                satellites_count=40,  # 智能篩選後數量
                orbital_altitude_km=550,
                inclination_deg=53.0,
                last_updated=datetime.utcnow(),
                data_freshness='實時',
                coverage_area='全球（特別優化亞太區域）'
            ),
            'oneweb': ConstellationMetadata(
                name='OneWeb', 
                satellites_count=30,  # 智能篩選後數量
                orbital_altitude_km=1200,
                inclination_deg=87.0,
                last_updated=datetime.utcnow(),
                data_freshness='實時',
                coverage_area='全球（極地覆蓋優秀）'
            )
        }
    
    async def switch_constellation(
        self, 
        new_constellation: Literal['starlink', 'oneweb'],
        force_refresh: bool = False
    ) -> Dict[str, any]:
        """星座切換主要邏輯"""
        
        if new_constellation == self.active_constellation and not force_refresh:
            return self.get_current_constellation_data()
        
        # 1. 檢查目標星座數據是否已快取
        cache_key = f"{new_constellation}_d2_timeseries"
        
        if cache_key not in self.data_cache or force_refresh:
            # 2. 載入新星座數據
            print(f"載入 {new_constellation} 星座數據...")
            constellation_data = await self._load_constellation_data(new_constellation)
            self.data_cache[cache_key] = constellation_data
        
        # 3. 更新活躍星座
        self.active_constellation = new_constellation
        
        # 4. 更新元數據時間戳
        self.metadata_cache[new_constellation].last_updated = datetime.utcnow()
        
        return {
            'constellation': new_constellation,
            'metadata': self.metadata_cache[new_constellation],
            'timeseries_data': self.data_cache[cache_key]['d2_measurements'],
            'satellite_positions': self.data_cache[cache_key]['satellite_positions'],
            'switch_timestamp': datetime.utcnow().isoformat()
        }
    
    async def _load_constellation_data(self, constellation: str) -> Dict[str, any]:
        """載入指定星座的完整數據"""
        
        # 1. 從預處理文件載入基礎時間序列數據
        timeseries_file = f"/app/data/{constellation}_120min_timeseries.json"
        
        try:
            with open(timeseries_file, 'r') as f:
                timeseries_data = json.load(f)
        except FileNotFoundError:
            # Fallback: 動態生成數據
            print(f"預處理文件不存在，動態生成 {constellation} 數據")
            timeseries_data = await self._generate_dynamic_data(constellation)
        
        # 2. 處理 D2 測量事件數據
        d2_processor = EnhancedD2DataProcessor()
        d2_measurements = d2_processor.process_d2_measurements(
            timeseries_data['satellites'],
            duration_minutes=5  # 290秒 ≈ 4.83分鐘
        )
        
        # 3. 提取 3D 位置數據
        satellite_positions = self._extract_3d_positions(timeseries_data)
        
        return {
            'constellation': constellation,
            'd2_measurements': d2_measurements,
            'satellite_positions': satellite_positions,
            'metadata': timeseries_data.get('metadata', {}),
            'load_timestamp': datetime.utcnow().isoformat()
        }
    
    def _extract_3d_positions(self, timeseries_data: Dict) -> List[Dict]:
        """提取衛星3D位置數據用於立體圖顯示"""
        positions = []
        
        for satellite in timeseries_data['satellites'][:10]:  # 前10顆用於3D顯示
            satellite_positions = []
            
            for time_point in satellite['positions'][:30]:  # 290秒，10秒間隔 = 30個點
                satellite_positions.append({
                    'timestamp': time_point['timestamp'],
                    'position': self._spherical_to_cartesian(
                        time_point['elevation_deg'],
                        time_point['azimuth_deg'], 
                        time_point['range_km']
                    ),
                    'is_visible': time_point['is_visible']
                })
            
            positions.append({
                'satellite_id': satellite.get('satellite_id', f"sat_{len(positions)}"),
                'positions': satellite_positions
            })
        
        return positions
    
    def _spherical_to_cartesian(self, elevation: float, azimuth: float, range_km: float) -> List[float]:
        """球坐標轉笛卡爾坐標"""
        import math
        
        # 轉換為弧度
        elev_rad = math.radians(elevation)
        azim_rad = math.radians(azimuth)
        
        # 笛卡爾坐標計算
        x = range_km * math.cos(elev_rad) * math.sin(azim_rad)
        y = range_km * math.cos(elev_rad) * math.cos(azim_rad)
        z = range_km * math.sin(elev_rad)
        
        return [x, y, z]

# 全局星座管理實例
constellation_manager = ConstellationManager()
```

### API 端點擴展
```python
# 修改: measurement_events_router.py
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Literal, Optional

router = APIRouter(prefix="/api/measurement-events", tags=["measurement-events"])

class ConstellationSwitchRequest(BaseModel):
    constellation: Literal['starlink', 'oneweb']
    duration_minutes: int = 5
    force_refresh: bool = False
    include_3d_positions: bool = True

@router.post("/constellation/switch")
async def switch_constellation(
    request: ConstellationSwitchRequest,
    background_tasks: BackgroundTasks
):
    """
    雙星座切換 API
    支援 Starlink ↔ OneWeb 即時切換
    """
    try:
        # 執行星座切換
        switch_result = await constellation_manager.switch_constellation(
            new_constellation=request.constellation,
            force_refresh=request.force_refresh
        )
        
        # 背景任務：預載另一個星座的數據
        other_constellation = 'oneweb' if request.constellation == 'starlink' else 'starlink'
        background_tasks.add_task(
            preload_constellation_data, 
            other_constellation
        )
        
        return {
            "success": True,
            "data": {
                "constellation": switch_result['constellation'],
                "metadata": {
                    "name": switch_result['metadata'].name,
                    "satellites_count": switch_result['metadata'].satellites_count,
                    "orbital_altitude_km": switch_result['metadata'].orbital_altitude_km,
                    "inclination_deg": switch_result['metadata'].inclination_deg,
                    "last_updated": switch_result['metadata'].last_updated.isoformat(),
                    "coverage_area": switch_result['metadata'].coverage_area
                },
                "d2_timeseries": switch_result['timeseries_data'],
                "satellite_3d_positions": switch_result['satellite_positions'] if request.include_3d_positions else None,
                "switch_duration_ms": (datetime.utcnow() - datetime.fromisoformat(switch_result['switch_timestamp'].replace('Z', '+00:00'))).total_seconds() * 1000
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"星座切換失敗: {str(e)}"
        )

@router.get("/constellation/status")
async def get_constellation_status():
    """獲取當前星座狀態"""
    current_metadata = constellation_manager.metadata_cache[constellation_manager.active_constellation]
    
    return {
        "active_constellation": constellation_manager.active_constellation,
        "metadata": {
            "name": current_metadata.name,
            "satellites_count": current_metadata.satellites_count,
            "orbital_altitude_km": current_metadata.orbital_altitude_km,
            "inclination_deg": current_metadata.inclination_deg,
            "last_updated": current_metadata.last_updated.isoformat(),
            "data_freshness": current_metadata.data_freshness,
            "coverage_area": current_metadata.coverage_area
        },
        "available_constellations": list(constellation_manager.metadata_cache.keys()),
        "cache_status": {
            constellation: bool(f"{constellation}_d2_timeseries" in constellation_manager.data_cache)
            for constellation in constellation_manager.metadata_cache.keys()
        }
    }

@router.get("/constellation/compare")
async def compare_constellations():
    """星座對比分析 API"""
    
    comparison_data = {
        "starlink": {
            "characteristics": {
                "altitude_km": 550,
                "inclination_deg": 53.0,
                "satellites_in_analysis": 40,
                "handover_frequency": "高",
                "signal_stability": "中",
                "coverage_quality": "良好",
                "research_focus": "高密度換手分析"
            },
            "advantages": [
                "衛星密度高，換手場景豐富",
                "較低軌道，信號延遲小",
                "亞太地區覆蓋良好"
            ]
        },
        "oneweb": {
            "characteristics": {
                "altitude_km": 1200,
                "inclination_deg": 87.0,
                "satellites_in_analysis": 30,
                "handover_frequency": "中",
                "signal_stability": "高",
                "coverage_quality": "優秀",
                "research_focus": "穩定性與極地覆蓋研究"
            },
            "advantages": [
                "近極地軌道，全球覆蓋優秀",
                "更高軌道，連接相對穩定",
                "極地和高緯度地區覆蓋佳"
            ]
        }
    }
    
    return {
        "comparison": comparison_data,
        "research_recommendations": {
            "dense_handover_study": "選擇 Starlink，分析高頻率換手行為", 
            "stability_analysis": "選擇 OneWeb，研究長期連接穩定性",
            "polar_coverage": "選擇 OneWeb，分析極地地區換手特性",
            "comparative_study": "同時使用兩個星座，進行對比研究"
        }
    }

async def preload_constellation_data(constellation: str):
    """背景任務：預載星座數據"""
    try:
        await constellation_manager.switch_constellation(
            new_constellation=constellation,
            force_refresh=False
        )
        print(f"背景預載 {constellation} 數據完成")
    except Exception as e:
        print(f"背景預載 {constellation} 數據失敗: {e}")
```

## ⚡ 性能優化策略

### 數據快取機制
```python
# 快取管理系統
class ConstellationDataCache:
    def __init__(self, max_cache_size_mb: int = 200):
        self.cache = {}
        self.cache_timestamps = {}
        self.max_cache_size = max_cache_size_mb * 1024 * 1024  # 轉換為位元組
        self.cache_ttl = timedelta(hours=6)  # 6小時快取有效期
    
    def is_cache_valid(self, key: str) -> bool:
        """檢查快取是否有效"""
        if key not in self.cache_timestamps:
            return False
        
        return datetime.utcnow() - self.cache_timestamps[key] < self.cache_ttl
    
    def get_cache_size(self) -> int:
        """計算當前快取大小"""
        import sys
        total_size = 0
        for data in self.cache.values():
            total_size += sys.getsizeof(str(data))
        return total_size
    
    def evict_old_cache(self):
        """清除過期快取"""
        current_time = datetime.utcnow()
        keys_to_remove = []
        
        for key, timestamp in self.cache_timestamps.items():
            if current_time - timestamp > self.cache_ttl:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            self.cache.pop(key, None)
            self.cache_timestamps.pop(key, None)
        
        print(f"清除了 {len(keys_to_remove)} 個過期快取項目")
```

### 3D渲染優化
```typescript
// 3D渲染性能優化
class ConstellationRenderOptimizer {
    private geometryCache = new Map<string, THREE.BufferGeometry>()
    private materialCache = new Map<string, THREE.Material>()
    
    // 幾何體複用
    getOrCreateSatelliteGeometry(constellation: string): THREE.BufferGeometry {
        const cacheKey = `satellite_${constellation}`
        
        if (\!this.geometryCache.has(cacheKey)) {
            const geometry = new THREE.SphereGeometry(
                constellation === 'starlink' ? 2 : 3,  // 不同星座不同大小
                16, 16
            )
            this.geometryCache.set(cacheKey, geometry)
        }
        
        return this.geometryCache.get(cacheKey)\!
    }
    
    // 材質複用
    getOrCreateSatelliteMaterial(constellation: string, state: 'active' | 'candidate' | 'inactive'): THREE.Material {
        const cacheKey = `${constellation}_${state}`
        
        if (\!this.materialCache.has(cacheKey)) {
            const colorScheme = this.getConstellationColors(constellation)
            const material = new THREE.MeshBasicMaterial({
                color: colorScheme[state],
                transparent: true,
                opacity: state === 'active' ? 1.0 : (state === 'candidate' ? 0.8 : 0.4)
            })
            this.materialCache.set(cacheKey, material)
        }
        
        return this.materialCache.get(cacheKey)\!
    }
    
    // 批量更新衛星位置（性能優化）
    batchUpdateSatellitePositions(
        satellites: Map<string, THREE.Mesh>,
        positionData: SatellitePositionData[],
        currentTime: number
    ) {
        const updateBatch = []
        
        // 收集需要更新的衛星
        positionData.forEach(data => {
            const mesh = satellites.get(data.satellite_id)
            if (mesh) {
                const position = this.interpolatePosition(data.positions, currentTime)
                updateBatch.push({ mesh, position })
            }
        })
        
        // 批量更新（減少渲染調用）
        updateBatch.forEach(({ mesh, position }) => {
            mesh.position.set(position.x, position.y, position.z)
        })
    }
    
    private getConstellationColors(constellation: string) {
        return constellation === 'starlink' ? {
            active: 0x059669,
            candidate: 0x34D399,
            inactive: 0x6B7280
        } : {
            active: 0x2563EB,
            candidate: 0x60A5FA,
            inactive: 0x6B7280
        }
    }
}
```

## 📊 測試驗證計劃

### 功能測試清單
```bash
# 1. 星座切換基本功能測試
curl -X POST "http://localhost:8888/api/measurement-events/constellation/switch" \
  -H "Content-Type: application/json" \
  -d '{"constellation": "starlink", "duration_minutes": 5}'

curl -X POST "http://localhost:8888/api/measurement-events/constellation/switch" \
  -H "Content-Type: application/json" \
  -d '{"constellation": "oneweb", "duration_minutes": 5}'

# 2. 星座狀態檢查
curl -X GET "http://localhost:8888/api/measurement-events/constellation/status"

# 3. 星座對比分析
curl -X GET "http://localhost:8888/api/measurement-events/constellation/compare"
```

### 性能測試指標
```typescript
// 性能測試套件
describe('雙星座切換性能測試', () => {
    test('星座切換響應時間', async () => {
        const startTime = performance.now()
        
        await switchConstellation('oneweb')
        
        const switchTime = performance.now() - startTime
        expect(switchTime).toBeLessThan(2000) // <2秒要求
    })
    
    test('3D渲染幀率', async () => {
        const frameRates = []
        const testDuration = 10000 // 10秒測試
        
        const startTime = performance.now()
        while (performance.now() - startTime < testDuration) {
            const frameStart = performance.now()
            
            // 執行一幀渲染
            renderer.render(scene, camera)
            
            const frameTime = performance.now() - frameStart
            const fps = 1000 / frameTime
            frameRates.push(fps)
            
            await new Promise(resolve => requestAnimationFrame(resolve))
        }
        
        const averageFPS = frameRates.reduce((a, b) => a + b) / frameRates.length
        expect(averageFPS).toBeGreaterThan(30) // >30 FPS要求
    })
    
    test('數據同步精度', async () => {
        const timeController = new UnifiedTimeController()
        const d2Chart = new D2ChartSyncAdapter()
        const satellite3D = new Satellite3DSyncAdapter()
        
        // 註冊同步目標
        timeController.registerSyncTarget('d2', d2Chart)
        timeController.registerSyncTarget('3d', satellite3D)
        
        // 切換星座
        await switchConstellation('starlink')
        
        // 測試同步精度
        const testTime = 150.5
        timeController.updateTime(testTime)
        
        expect(Math.abs(d2Chart.getCurrentTime() - testTime)).toBeLessThan(0.1) // ±100ms
        expect(Math.abs(satellite3D.getCurrentTime() - testTime)).toBeLessThan(0.1)
    })
})
```

## 🎯 實施路線圖

### Phase 1: 基礎雙星座架構 (2-3天)
- [x] ConstellationManager 核心服務實施
- [x] 基本切換 API 端點開發
- [x] 前端 ConstellationSwitcher 組件
- [x] D2圖表星座切換整合

### Phase 2: 3D同步整合 (2-3天)  
- [x] 3D視圖星座切換邏輯
- [x] 統一時間控制器星座事件處理
- [x] 顏色方案和視覺區分
- [x] 攝影機視角自動調整

### Phase 3: 性能優化與測試 (2-3天)
- [x] 數據快取機制實施
- [x] 3D渲染批量更新優化
- [x] 背景預載功能
- [x] 完整測試套件開發

## ✅ 成功標準

### 功能完整性
- [ ] Starlink ↔ OneWeb 無縫切換
- [ ] D2圖表與3D視圖完全同步切換
- [ ] 數據一致性保證
- [ ] 星座特性清晰展示

### 性能指標
- [ ] 星座切換響應時間 ≤2秒
- [ ] 3D渲染幀率 ≥30 FPS
- [ ] 數據同步精度 ≤100ms
- [ ] 記憶體使用穩定

### 用戶體驗
- [ ] 切換過程流暢，無卡頓
- [ ] 星座差異清晰可見
- [ ] 數據來源資訊透明
- [ ] 學術研究價值明顯

---

**雙星座切換功能將為 LEO 衛星換手研究提供前所未有的對比分析能力，支援不同軌道特性的深度研究。**
