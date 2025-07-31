# D2事件增強實施計劃

**階段**: Phase 1 - 優先實施 ⭐  
**版本**: 1.0.0  
**狀態**: 規劃完成，準備實施  

## 🎯 當前D2事件問題分析

基於用戶反饋和系統檢查，當前 navbar > D2事件 存在以下問題：

### 1. 圖表可見性問題 ⚠️
**問題描述**：
- **原始衛星距離線**（含噪聲）：線條太細、顏色太深，幾乎看不見
- **原始地面距離線**（含噪聲）：同樣存在可見性問題

**影響**：
- 用戶無法有效比較原始數據與處理後數據
- 降低了數據分析的完整性
- 影響學術研究的可視化效果

### 2. 時間範圍說明不足 ⏱️
**問題描述**：
- 當前290秒時間範圍缺乏充分說明
- 用戶不理解為何不是完整衛星週期
- 時間範圍選擇的研究意義不明確

### 3. 數據來源透明度不足 📊
**問題描述**：
- 用戶不確定是否使用真實歷史衛星數據
- 缺乏對SGP4精確軌道計算的說明
- 星座選擇（Starlink vs OneWeb）的意義不清

## 🚀 D2事件增強方案

### 方案1: 圖表可見性增強 ⭐

#### 1.1 線條視覺優化
```typescript
// 增強線條配置
const enhancedLineConfig = {
    // 原始衛星距離線（綠色系）
    rawSatelliteDistance: {
        borderColor: '#34D399',      // 明亮綠色
        borderWidth: 2,             // 增加線寬
        pointRadius: 3,             // 增加點大小
        borderDash: [5, 3],         // 虛線樣式區分
        backgroundColor: 'rgba(52, 211, 153, 0.1)' // 半透明填充
    },
    
    // 原始地面距離線（橙色系）
    rawGroundDistance: {
        borderColor: '#FB923C',      // 明亮橙色
        borderWidth: 2,
        pointRadius: 3,
        borderDash: [3, 2],
        backgroundColor: 'rgba(251, 146, 60, 0.1)'
    },
}
```

#### 1.2 圖例增強
```typescript
// 增強圖例說明
const enhancedLegend = {
    display: true,
    position: 'top',
    labels: {
        generateLabels: (chart) => [{
            text: '🔴 原始衛星距離 (含噪聲)',
            fillStyle: '#34D399',
            strokeStyle: '#34D399',
            lineWidth: 2
        }, {
            text: '🟠 原始地面距離 (含噪聲)', 
            fillStyle: '#FB923C',
            strokeStyle: '#FB923C',
            lineWidth: 2
        }]
    }
}
```

### 方案2: 多時間範圍支援 ⏰

#### 2.1 時間範圍選擇器
```typescript
interface TimeRangeOptions {
    'research_focused': {
        duration: 290,
        description: '研究聚焦模式 - 1-2次換手事件深度分析'
    },
    'single_pass': {
        duration: 420,
        description: '單次過境模式 - 完整衛星可見週期'
    }, 
    'multi_event': {
        duration: 900,
        description: '多事件分析 - 多次換手對比研究'
    },
    'full_orbit': {
        duration: 5400,
        description: '完整軌道週期 - 90分鐘完整分析'
    }
}

// 時間範圍說明組件
const TimeRangeExplanation = () => (
    <div className="time-range-info">
        <h4>💡 為什麼選擇290秒？</h4>
        <ul>
            <li>**換手事件密集度**: 捕捉1-2次關鍵換手決策</li>
            <li>**數據分析深度**: 足夠觀察完整的信號變化週期</li>
            <li>**計算效率**: 平衡研究需求與系統性能</li>
            <li>**學術標準**: 符合LEO衛星換手研究時間窗口</li>
        </ul>
    </div>
)
```

### 方案3: 數據來源透明度增強 📊

#### 3.1 數據來源資訊面板
```typescript
const DataSourceInfoPanel = () => (
    <div className="data-source-panel">
        <h4>📡 真實歷史衛星數據</h4>
        <div className="data-details">
            <div className="sgp4-info">
                <span className="badge sgp4">SGP4軌道計算</span>
                <p>米級精度軌道預測，符合國際航天標準</p>
            </div>
            
            <div className="constellation-info">
                <span className="badge starlink">Starlink</span>
                <p>40顆智能篩選衛星，高密度LEO星座</p>
                
                <span className="badge oneweb">OneWeb</span>
                <p>30顆智能篩選衛星，極地軌道覆蓋</p>
            </div>
            
            <div className="data-freshness">
                <span className="badge fresh">數據新鮮度</span>
                <p>基於最新TLE數據，每日自動更新</p>
            </div>
        </div>
    </div>
)
```

#### 3.2 星座切換功能
```typescript
// 星座切換控制器
const ConstellationSwitcher = ({ 
    currentConstellation, 
    onSwitch, 
    availableConstellations 
}) => (
    <div className="constellation-switcher">
        <label>🛰️ 選擇星座：</label>
        <select 
            value={currentConstellation}
            onChange={(e) => onSwitch(e.target.value)}
        >
            <option value="starlink">
                Starlink (550km, 53°傾角)
            </option>
            <option value="oneweb">
                OneWeb (1200km, 87°傾角)
            </option>
            <option value="dual">
                雙星座對比模式
            </option>
        </select>
        
        <div className="constellation-stats">
            <p>當前可見衛星: {visibleSatellites}顆</p>
            <p>換手候選: {handoverCandidates}顆</p>
        </div>
    </div>
)
```

## 🔧 實施技術方案

### 階段1: 前端組件增強 (1-2天)

#### 修改文件清單
- `simworld/frontend/src/components/domains/measurement/charts/EnhancedD2Chart.tsx`
- `simworld/frontend/src/components/domains/measurement/charts/EnhancedD2Chart.scss`
- `simworld/frontend/src/components/domains/measurement/shared/hooks/useEventD2Logic.ts`

#### 具體實施步驟
```bash
# 1. 備份現有文件
cp EnhancedD2Chart.tsx EnhancedD2Chart.tsx.backup

# 2. 實施線條可見性增強
# - 修改 borderColor, borderWidth, pointRadius
# - 添加虛線樣式區分
# - 優化顏色對比度

# 3. 添加時間範圍選擇器
# - 新增 TimeRangeSelector 組件
# - 整合到控制面板

# 4. 增加數據來源說明
# - 新增 DataSourceInfoPanel 組件
# - 添加星座切換功能
```

### 階段2: 後端數據增強 (2-3天)

#### API端點擴展
```python
# 新增統一D2事件API
@router.post("/api/measurement-events/D2/enhanced")
async def enhanced_d2_event(request: EnhancedD2Request):
    """
    增強版D2事件API
    - 支援多時間範圍
    - 支援雙星座切換
    - 包含數據品質資訊
    """
    return {
        "event_type": "D2",
        "constellation": request.constellation,
        "time_range_seconds": request.duration,
        "data_source": "sgp4_historical",
        "measurement_data": enhanced_d2_data,
        "metadata": {
            "satellites_processed": satellite_count,
            "data_freshness": freshness_info,
            "computation_accuracy": "meter_level"
        }
    }
```

#### 數據處理增強
```python
# D2數據處理增強
class EnhancedD2DataProcessor:
    def process_d2_measurements(self, tle_data, time_range):
        # 1. SGP4精確軌道計算
        positions = self.sgp4_calculator.calculate_positions(tle_data)
        
        # 2. 噪聲模擬（研究需要）
        raw_distances = self.add_realistic_noise(positions)
        
        # 3. 智能濾波處理
        processed_distances = self.intelligent_filter(raw_distances)
        
        return {
            "raw_satellite_distances": raw_distances.satellite,
            "raw_ground_distances": raw_distances.ground,
            "processed_distances": processed_distances,
            "quality_metrics": self.calculate_quality_metrics()
        }
```

### 階段3: 3D整合準備 (2-3天)

#### 3D同步數據結構
```typescript
interface D2_3D_SyncData {
    // 時間同步
    currentTime: number          // 當前時間戳
    timeRange: [number, number]  // 時間範圍
    
    // D2測量數據
    d2Measurements: {
        satelliteDistance: number
        groundDistance: number
        triggerState: boolean
    }
    
    // 3D視圖數據
    satellitePositions: Array<{
        id: string
        position: [number, number, number]
        isActive: boolean
        signalStrength: number
    }>
    
    // 視覺同步
    visualSync: {
        highlightedSatellite: string
        connectionLines: Array<ConnectionLine>
        handoverIndicators: Array<HandoverEvent>
    }
}
```

## 📊 測試驗證計劃

### 功能測試
```bash
# 1. 線條可見性測試
# - 確認三條線都清晰可見
# - 驗證顏色對比度適當
# - 檢查圖例正確顯示

# 2. 時間範圍切換測試  
# - 測試290s/420s/900s切換
# - 驗證數據正確載入
# - 檢查性能穩定性

# 3. 星座切換測試
# - Starlink ↔ OneWeb 切換
# - 雙星座對比模式
# - 數據一致性驗證
```

### 性能測試
```bash
# 1. 渲染性能
# - 3D視圖幀率 >30 FPS
# - 圖表更新延遲 <100ms
# - 記憶體使用穩定

# 2. 數據載入性能
# - 星座切換響應 <2s
# - 時間範圍切換 <1s
# - API響應時間 <500ms
```

### 數據準確性測試
```bash
# 1. SGP4計算驗證
# - 對比標準軌道預測工具
# - 驗證位置精度在米級
# - 檢查時間同步準確性

# 2. 噪聲模型驗證
# - 確認噪聲特性真實
# - 驗證濾波效果合理
# - 檢查統計特性符合預期
```

## 🎯 成功標準

### 用戶體驗改善
- [ ] 三條線都清晰可見，對比度適當
- [ ] 時間範圍選擇直觀，說明清楚
- [ ] 數據來源資訊透明，學術可信
- [ ] 星座切換功能流暢，響應快速

### 技術指標達成
- [ ] 圖表渲染性能 >30 FPS
- [ ] 星座切換響應時間 <2秒
- [ ] 數據精度達到米級（SGP4）
- [ ] API響應時間 <500ms

### 研究價值提升
- [ ] 真實歷史數據100%使用
- [ ] 多時間範圍靈活分析
- [ ] 雙星座對比研究支援
- [ ] 可視化效果達到發表級別

---

**D2事件增強完成後，將為後續3D整合和多事件擴展奠定堅實基礎。**
EOF < /dev/null
