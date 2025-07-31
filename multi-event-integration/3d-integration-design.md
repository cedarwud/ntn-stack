# D2事件與3D立體圖整合設計

**階段**: Phase 1 - 核心整合 ⭐  
**版本**: 1.0.0  
**狀態**: 技術設計完成  

## 🎯 整合目標

實現 D2 距離事件圖表與 3D 立體圖的深度整合，提供時空同步的衛星換手可視化體驗，讓用戶能夠同時觀察：
- **D2圖表**: 衛星距離變化的時間序列
- **3D立體圖**: 衛星在三維空間中的實際位置和移動軌跡
- **同步動畫**: 兩者完全同步，形成立體化的數據分析體驗

## 🏗️ 技術架構設計

### 架構概述
```
┌─────────────────────────────────────────────────────────────┐
│                    統一時間控制器                            │
│    TimeSync: { currentTime, isPlaying, playbackSpeed }     │
└─────────────────┬───────────────────────────────────────────┘
                  │
        ┌─────────┴─────────┐
        │                   │
┌───────▼──────┐    ┌──────▼──────┐
│  D2圖表組件   │◄──►│ 3D立體視圖   │
│ EnhancedD2   │    │ Satellite3D │
│ Chart        │    │ Visualization│
└──────────────┘    └─────────────┘
        │                   │
        ▼                   ▼
┌──────────────┐    ┌─────────────┐
│ D2數據源     │    │ 3D渲染引擎  │
│ SGP4計算     │    │ Three.js    │
└──────────────┘    └─────────────┘
```

### 核心同步機制

#### 1. 統一時間管理器
```typescript
interface UnifiedTimeController {
    // 時間狀態
    currentTime: number              // 當前時間戳 (0-290秒)
    isPlaying: boolean              // 播放狀態
    playbackSpeed: number           // 播放速度 (0.5x - 5x)
    totalDuration: number           // 總時長 (290秒)
    
    // 同步控制
    syncTargets: Map<string, SyncTarget>
    syncPrecision: number           // 同步精度 (100ms)
    
    // 事件處理
    onTimeUpdate: (time: number) => void
    onPlayStateChange: (isPlaying: boolean) => void
    onSpeedChange: (speed: number) => void
}

class TimeControllerImplementation {
    private syncTargets = new Map<string, SyncTarget>()
    
    // 註冊同步目標
    registerSyncTarget(id: string, target: SyncTarget) {
        this.syncTargets.set(id, target)
    }
    
    // 統一時間更新
    updateTime(newTime: number) {
        this.currentTime = newTime
        
        // 同步所有目標
        this.syncTargets.forEach((target, id) => {
            target.syncToTime(newTime)
        })
        
        // 觸發更新事件
        this.onTimeUpdate?.(newTime)
    }
}
```

#### 2. D2圖表同步介面
```typescript
interface D2ChartSyncAdapter implements SyncTarget {
    syncToTime(time: number): void {
        // 更新游標位置
        this.updateTimeCursor(time)
        
        // 高亮當前數據點
        this.highlightCurrentDataPoint(time)
        
        // 更新測量值顯示
        this.updateMeasurementDisplay(time)
        
        // 觸發換手事件標記
        this.updateHandoverIndicators(time)
    }
    
    private updateTimeCursor(time: number) {
        const cursorData = {
            x: time,
            y: [this.yAxisMin, this.yAxisMax]
        }
        
        this.chart.data.datasets.find(d => d.label === 'currentTime')
            .data = cursorData
        this.chart.update('none') // 無動畫更新
    }
}
```

#### 3. 3D視圖同步介面
```typescript
interface Satellite3DSyncAdapter implements SyncTarget {
    syncToTime(time: number): void {
        // 更新衛星位置
        this.updateSatellitePositions(time)
        
        // 更新連接線
        this.updateConnectionLines(time)
        
        // 更新換手動畫
        this.updateHandoverAnimations(time)
        
        // 更新視角（可選）
        this.updateCameraFocus(time)
    }
    
    private updateSatellitePositions(time: number) {
        this.visibleSatellites.forEach(satellite => {
            const position = this.calculatePositionAtTime(satellite, time)
            satellite.mesh.position.set(...position)
            
            // 更新軌道軌跡
            this.updateOrbitTrail(satellite, time)
        })
    }
}
```

## 🎨 視覺整合設計

### 佈局方案A: 並排顯示（推薦）
```
┌─────────────────────────────────────────────────────────────┐
│                    統一控制面板                              │
│  ⏯️播放  🔄1.0x  📊290s  🛰️Starlink  ⏱️150s/290s         │
└─────────────────────────────────────────────────────────────┘
┌────────────────────┬────────────────────────────────────────┐
│                    │                                        │
│    3D 立體視圖      │           D2 距離圖表                   │
│                    │                                        │
│   🌍 地球           │    📈 衛星距離                          │
│   🛰️ 衛星軌道      │    📈 地面距離                          │
│   📡 通信連線      │    🔴 時間游標                          │
│   ⚡ 換手動畫      │    ⚡ 觸發事件                          │
│                    │                                        │
│                    │    💡 數據說明面板                      │
│                    │    - SGP4精確計算                       │
│                    │    - 真實歷史數據                       │
│                    │    - 當前測量值                         │
│                    │                                        │
└────────────────────┴────────────────────────────────────────┘
```

### 視覺關聯設計

#### 1. 顏色一致性映射
```typescript
const colorMapping = {
    // 衛星狀態顏色
    servingSatellite: '#059669',      // 深綠色 - 與D2圖表主線一致
    candidateSatellite: '#FB923C',    // 橙色 - 與地面距離線一致
    inactiveSatellite: '#6B7280',     // 灰色 - 非活躍狀態
    
    // 連接線顏色
    activeConnection: '#059669',       // 當前連接 - 綠色
    candidateConnection: '#FB923C',    // 候選連接 - 橙色
    handoverConnection: '#DC2626',     // 換手過程 - 紅色
    
    // 軌道軌跡顏色
    currentOrbit: 'rgba(5, 150, 105, 0.3)',     // 半透明綠色
    predictedOrbit: 'rgba(251, 146, 60, 0.2)',  // 半透明橙色
}
```

#### 2. 動畫同步機制
```typescript
class AnimationSynchronizer {
    // 關鍵幀定義
    keyFrames = [
        { time: 70, event: 'handover_preparation', duration: 10 },
        { time: 150, event: 'handover_trigger', duration: 5 },
        { time: 220, event: 'handover_complete', duration: 8 }
    ]
    
    // 同步動畫播放
    syncAnimation(currentTime: number) {
        const activeKeyFrame = this.getActiveKeyFrame(currentTime)
        
        if (activeKeyFrame) {
            // D2圖表: 高亮觸發區域
            this.d2Chart.highlightTriggerZone(activeKeyFrame)
            
            // 3D視圖: 播放換手動畫
            this.satellite3D.playHandoverAnimation(activeKeyFrame)
            
            // 狀態面板: 顯示事件詳情
            this.statusPanel.showEventDetails(activeKeyFrame)
        }
    }
}
```

## 🔧 技術實施方案

### Phase 1: 基礎同步架構 (2-3天)

#### 1.1 時間控制器實現
```typescript
// 文件: src/controllers/UnifiedTimeController.ts
export class UnifiedTimeController {
    private currentTime = 0
    private isPlaying = false
    private playbackSpeed = 1.0
    private syncTargets = new Map<string, SyncTarget>()
    
    constructor(private totalDuration: number = 290) {
        this.setupAnimationLoop()
    }
    
    private setupAnimationLoop() {
        const animate = () => {
            if (this.isPlaying) {
                const deltaTime = 16.67 * this.playbackSpeed / 1000 // 60 FPS
                this.updateTime(this.currentTime + deltaTime)
            }
            requestAnimationFrame(animate)
        }
        animate()
    }
}
```

#### 1.2 D2圖表整合
```typescript
// 修改: EnhancedD2Chart.tsx
export const EnhancedD2Chart: React.FC<Props> = (props) => {
    const timeController = useUnifiedTimeController()
    
    useEffect(() => {
        // 註冊到時間控制器
        const syncAdapter = new D2ChartSyncAdapter(chartRef.current)
        timeController.registerSyncTarget('d2-chart', syncAdapter)
        
        return () => {
            timeController.unregisterSyncTarget('d2-chart')
        }
    }, [])
    
    // ... 其他邏輯
}
```

#### 1.3 3D視圖整合
```typescript
// 修改: Satellite3DVisualization.tsx
export const Satellite3DVisualization: React.FC<Props> = (props) => {
    const timeController = useUnifiedTimeController()
    
    useEffect(() => {
        // 註冊到時間控制器
        const syncAdapter = new Satellite3DSyncAdapter(sceneRef.current)
        timeController.registerSyncTarget('3d-view', syncAdapter)
        
        return () => {
            timeController.unregisterSyncTarget('3d-view')
        }
    }, [])
}
```

### Phase 2: 數據同步優化 (2-3天)

#### 2.1 統一數據源
```typescript
// 新建: src/services/UnifiedD2DataService.ts
export class UnifiedD2DataService {
    async getTimeSeriesData(
        constellation: 'starlink' | 'oneweb',
        timeRange: number = 290
    ): Promise<UnifiedD2TimeSeriesData> {
        
        // 獲取SGP4計算數據
        const orbitData = await this.getSGP4OrbitData(constellation, timeRange)
        
        // 計算D2測量值
        const d2Measurements = this.calculateD2Measurements(orbitData)
        
        // 生成3D位置數據
        const satellitePositions = this.generate3DPositions(orbitData)
        
        return {
            timePoints: this.generateTimePoints(timeRange),
            d2Measurements,
            satellitePositions,
            metadata: {
                constellation,
                dataSource: 'sgp4_historical',
                accuracy: 'meter_level'
            }
        }
    }
}
```

#### 2.2 性能優化
```typescript
// 數據快取機制
class DataCacheManager {
    private cache = new Map<string, CachedData>()
    private readonly CACHE_TTL = 5 * 60 * 1000 // 5分鐘
    
    getCachedData(key: string): CachedData | null {
        const cached = this.cache.get(key)
        if (cached && Date.now() - cached.timestamp < this.CACHE_TTL) {
            return cached
        }
        return null
    }
    
    setCachedData(key: string, data: any) {
        this.cache.set(key, {
            data,
            timestamp: Date.now()
        })
    }
}
```

### Phase 3: 視覺增強 (2-3天)

#### 3.1 關聯視覺效果
```typescript
// 3D視圖中的D2事件可視化
class D2Event3DVisualizer {
    // 距離球體可視化
    createDistanceSphere(satellite: Satellite, distance: number) {
        const geometry = new THREE.SphereGeometry(distance / 1000, 32, 32)
        const material = new THREE.MeshBasicMaterial({
            color: 0x059669,
            transparent: true,
            opacity: 0.1,
            wireframe: true
        })
        
        return new THREE.Mesh(geometry, material)
    }
    
    // 換手路徑可視化
    createHandoverPath(fromSat: Satellite, toSat: Satellite) {
        const points = [
            fromSat.position,
            this.uePosition,
            toSat.position
        ]
        
        const geometry = new THREE.BufferGeometry().setFromPoints(points)
        const material = new THREE.LineBasicMaterial({
            color: 0xDC2626,
            linewidth: 3
        })
        
        return new THREE.Line(geometry, material)
    }
}
```

#### 3.2 互動增強
```typescript
// 點擊事件處理
class InteractionHandler {
    onSatelliteClick(satellite: Satellite) {
        // 3D視圖: 聚焦到衛星
        this.camera.lookAt(satellite.position)
        
        // D2圖表: 高亮對應數據線
        this.d2Chart.highlightSatelliteLine(satellite.id)
        
        // 狀態面板: 顯示詳細信息
        this.statusPanel.showSatelliteDetails(satellite)
    }
    
    onTimelineClick(time: number) {
        // 時間控制器: 跳轉到指定時間
        this.timeController.seekTo(time)
        
        // 3D視圖: 更新到對應時間的位置
        this.satellite3D.syncToTime(time)
    }
}
```

## 📊 測試與驗證

### 同步精度測試
```typescript
describe('D2-3D Integration Sync Tests', () => {
    test('時間同步精度', async () => {
        const timeController = new UnifiedTimeController()
        const d2Chart = new D2ChartSyncAdapter()
        const satellite3D = new Satellite3DSyncAdapter()
        
        // 註冊同步目標
        timeController.registerSyncTarget('d2', d2Chart)
        timeController.registerSyncTarget('3d', satellite3D)
        
        // 測試時間更新
        timeController.updateTime(150.5)
        
        // 驗證同步精度
        expect(d2Chart.getCurrentTime()).toBeCloseTo(150.5, 1)
        expect(satellite3D.getCurrentTime()).toBeCloseTo(150.5, 1)
    })
    
    test('數據一致性驗證', async () => {
        const dataService = new UnifiedD2DataService()
        const data = await dataService.getTimeSeriesData('starlink', 290)
        
        // 驗證D2測量數據
        expect(data.d2Measurements).toHaveLength(30) // 290秒/10秒間隔
        expect(data.satellitePositions).toHaveLength(30)
        
        // 驗證數據時間戳一致性
        data.d2Measurements.forEach((measurement, index) => {
            expect(measurement.timestamp).toBe(
                data.satellitePositions[index].timestamp
            )
        })
    })
})
```

### 性能基準測試
```bash
# 渲染性能測試
npm run test:performance

# 預期結果
# - 3D渲染: >30 FPS
# - D2圖表更新: <16ms (60 FPS)
# - 時間同步延遲: <100ms
# - 記憶體使用: <200MB
```

## 🎯 成功標準

### 功能完整性
- [ ] D2圖表與3D視圖完全時間同步
- [ ] 時間控制器統一管理播放狀態
- [ ] 衛星位置與距離數據一致
- [ ] 換手事件在兩個視圖中同步顯示
- [ ] 支持暫停、播放、快進/慢放

### 性能指標
- [ ] 3D渲染幀率 ≥30 FPS
- [ ] 時間同步精度 ≤100ms
- [ ] 數據載入時間 ≤2秒
- [ ] 內存使用穩定 (無洩漏)

### 用戶體驗
- [ ] 操作直觀，學習成本低
- [ ] 視覺效果專業，適合學術發表
- [ ] 響應迅速，無明顯延遲
- [ ] 多星座切換流暢

---

**D2事件與3D立體圖整合將為LEO衛星換手研究提供前所未有的可視化分析能力。**
EOF < /dev/null
