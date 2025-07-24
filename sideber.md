# EnhancedSidebar 模組化重構計畫

## 🎯 重構目標

**問題分析：**
- 當前 EnhancedSidebar.tsx 檔案過於龐大（1771行）
- 功能耦合度高，維護困難
- 換手管理等功能未來可能需要移除
- 缺乏模組化架構，不利於團隊協作開發

**重構目標：**
- 將主檔案從 1771行 減少到 500-600行（減少 65-70%）
- 創建 8-10 個獨立功能模組
- 提升代碼可維護性、可測試性和可重用性
- 支持功能模組的獨立開發和按需載入

## 📊 現狀分析

### 當前檔案結構分佈

| 功能區塊 | 行數範圍 | 代碼行數 | 佔比 | 重構優先級 |
|---------|---------|---------|------|-----------|
| 換手管理模組 | 788-1032, 1034-1064 | 304行 | 17.2% | 🔴 高 |
| 設備列表模組 | 1484-1763 | 279行 | 15.8% | 🔴 高 |
| UAV選擇模組 | 1207-1444 | 237行 | 13.4% | 🔴 高 |
| 衛星數據管理 | 161-253, 500-565 | 157行 | 8.9% | 🔴 高 |
| 手動控制模組 | 659-687, 1067-1203 | 165行 | 9.3% | 🟡 中 |
| 功能開關模組 | 413-491, 716-748 | 110行 | 6.2% | 🟡 中 |
| 設備管理模組 | 567-617, 691-714 | 80行 | 4.5% | 🟢 低 |
| 類別導航模組 | 492-498, 761-783 | 45行 | 2.5% | 🟢 低 |
| **總計可模組化** | | **1377行** | **77.8%** | |

## 🏗️ 模組化設計

### 新的檔案結構

```
components/layout/
├── EnhancedSidebar.tsx                 # 主檔案（重構後 500-600行）
├── sidebar/                           # 側邊欄模組目錄
│   ├── CategoryNavigation.tsx         # 類別導航（45行）
│   ├── FeatureToggleManager.tsx       # 功能開關管理（110行）
│   ├── UAVSelectionPanel.tsx          # UAV選擇面板（237行）
│   ├── ManualControlPanel.tsx         # 手動控制面板（165行）
│   ├── DeviceListPanel.tsx            # 設備列表面板（279行）
│   ├── HandoverManagementTab.tsx      # 換手管理分頁（304行）
│   └── SatelliteDataManager.tsx       # 衛星數據管理（100行）
├── hooks/                             # 自訂 Hooks
│   ├── useSatelliteData.ts           # 衛星數據邏輯（57行）
│   └── useDeviceManagement.ts        # 設備管理邏輯（80行）
└── types/
    └── sidebar.types.ts               # 共用類型定義
```

### 模組職責劃分

#### 🔴 高優先級模組

**1. HandoverManagementTab.tsx**
- **功能**：換手管理的完整UI和邏輯
- **包含**：換手模式切換、速度控制、HandoverManager組件
- **原因**：未來可能整個移除，獨立後便於操作
- **減少**：304行（17.2%）

**2. DeviceListPanel.tsx**
- **功能**：各類型設備的列表顯示和管理
- **包含**：設備分組、DeviceItem渲染、展開/收合邏輯
- **原因**：功能完整獨立，UI邏輯複雜
- **減少**：279行（15.8%）

**3. UAVSelectionPanel.tsx**
- **功能**：UAV接收器選擇和狀態顯示
- **包含**：徽章網格、選擇邏輯、狀態指示器
- **原因**：獨立的選擇器組件，可復用性高
- **減少**：237行（13.4%）

**4. SatelliteDataManager.tsx + useSatelliteData.ts**
- **功能**：衛星數據獲取、管理和狀態維護
- **包含**：fetchVisibleSatellites、數據初始化、狀態管理
- **原因**：複雜的數據邏輯，適合抽離成 hook
- **減少**：157行（8.9%）

#### 🟡 中優先級模組

**5. ManualControlPanel.tsx**
- **功能**：UAV手動控制面板
- **包含**：控制按鈕網格、事件處理
- **原因**：UI邏輯獨立，條件顯示
- **減少**：165行（9.3%）

**6. FeatureToggleManager.tsx**
- **功能**：功能開關的配置和渲染
- **包含**：featureToggles配置、渲染邏輯
- **原因**：可復用的開關組件
- **減少**：110行（6.2%）

#### 🟢 低優先級模組

**7. useDeviceManagement.ts**
- **功能**：設備相關的狀態管理和邏輯
- **包含**：方向輸入處理、設備分組、角色變更
- **原因**：抽離邏輯，提升可測試性
- **減少**：80行（4.5%）

**8. CategoryNavigation.tsx**
- **功能**：分頁類別選擇導航
- **包含**：類別定義、選擇邏輯
- **原因**：簡單但獨立的UI組件
- **減少**：45行（2.5%）

## 🚀 重構步驟流程

### Phase 1: 準備階段 (1週)

#### 1.1 創建目錄結構
```bash
mkdir -p simworld/frontend/src/components/layout/sidebar
mkdir -p simworld/frontend/src/components/layout/hooks
mkdir -p simworld/frontend/src/components/layout/types
```

#### 1.2 定義共用類型
創建 `sidebar.types.ts`：
```typescript
// 功能開關介面
export interface FeatureToggle {
    id: string
    label: string
    category: 'uav' | 'satellite' | 'handover_mgr' | 'quality'
    enabled: boolean
    onToggle: (enabled: boolean) => void
    icon?: string
    description?: string
    hidden?: boolean
}

// 類別定義
export interface SidebarCategory {
    id: string
    label: string
    icon: string
}

// 設備選擇相關
export interface DeviceSelectionProps {
    devices: Device[]
    selectedIds: number[]
    onSelectionChange: (ids: number[]) => void
}
```

#### 1.3 建立測試框架
```bash
# 為每個模組創建測試檔案
touch simworld/frontend/src/components/layout/sidebar/__tests__/CategoryNavigation.test.tsx
touch simworld/frontend/src/components/layout/sidebar/__tests__/FeatureToggleManager.test.tsx
# ... 其他測試檔案
```

**Phase 1 驗收標準：**
- [ ] 目錄結構創建完成
- [ ] 共用類型定義完成
- [ ] 測試框架建立完成
- [ ] 現有功能正常運行（基線測試）

### Phase 2: 高優先級模組重構 (2-3週)

#### 2.1 換手管理模組重構 (3天)

**步驟 2.1.1：創建 HandoverManagementTab.tsx**
```typescript
interface HandoverManagementTabProps {
    satellites: VisibleSatelliteInfo[]
    selectedUEId: number
    isVisible: boolean
    handoverMode: 'demo' | 'real'
    satelliteMovementSpeed: number
    handoverTimingSpeed: number
    handoverStableDuration: number
    satelliteUavConnectionEnabled: boolean
    onHandoverModeChange: (mode: 'demo' | 'real') => void
    onSatelliteMovementSpeedChange: (speed: number) => void
    onHandoverTimingSpeedChange: (speed: number) => void
    onHandoverStableDurationChange: (duration: number) => void
    // 所有換手相關的回調函數
    onHandoverStateChange?: (state: HandoverState) => void
    onCurrentConnectionChange?: (connection: SatelliteConnection) => void
    onPredictedConnectionChange?: (connection: SatelliteConnection) => void
    onTransitionChange?: (isTransitioning: boolean, progress: number) => void
    onAlgorithmResults?: (results: any) => void
}
```

**步驟 2.1.2：遷移換手相關邏輯**
- 將 788-1032行的衛星動畫控制移到新組件
- 將 1034-1064行的 HandoverManager 移到新組件
- 保持懶加載的 HandoverManager import

**步驟 2.1.3：在主組件中集成**
```typescript
// 在 EnhancedSidebar.tsx 中
{activeCategory === 'handover_mgr' && (
    <HandoverManagementTab
        satellites={skyfieldSatellites}
        selectedUEId={selectedReceiverIds[0]}
        isVisible={true}
        // ... 其他 props
    />
)}
```

#### 2.2 設備列表模組重構 (3天)

**步驟 2.2.1：創建 DeviceListPanel.tsx**
```typescript
interface DeviceListPanelProps {
    devices: Device[]
    tempDevices: Device[]
    receiverDevices: Device[]
    desiredDevices: Device[]
    jammerDevices: Device[]
    skyfieldSatellites: VisibleSatelliteInfo[]
    satelliteEnabled: boolean
    loadingSatellites: boolean
    orientationInputs: Record<string, {x: string, y: string, z: string}>
    onDeviceChange: (id: number, field: keyof Device, value: unknown) => void
    onDeleteDevice: (id: number) => void
    onOrientationInputChange: (deviceId: number, axis: 'x'|'y'|'z', value: string) => void
    onDeviceRoleChange: (deviceId: number, newRole: string) => void
}
```

**步驟 2.2.2：遷移設備列表邏輯**
- 將 1484-1763行的完整設備列表渲染移到新組件
- 包含所有設備類型的展開/收合邏輯
- 保持 DeviceItem 的現有功能

#### 2.3 UAV選擇模組重構 (2天)

**步驟 2.3.1：創建 UAVSelectionPanel.tsx**
```typescript
interface UAVSelectionPanelProps {
    devices: Device[]
    selectedReceiverIds: number[]
    isVisible: boolean
    onSelectionChange: (ids: number[]) => void
    onBadgeClick: (id: number) => void
}
```

**步驟 2.3.2：遷移 UAV 選擇邏輯**
- 將 1207-1444行的 UAV 選擇容器移到新組件
- 保持現有的徽章網格和選擇邏輯
- 維持狀態指示器的功能

#### 2.4 衛星數據管理重構 (3天)

**步驟 2.4.1：創建 useSatelliteData.ts hook**
```typescript
export interface UseSatelliteDataReturn {
    satellites: VisibleSatelliteInfo[]
    loadingSatellites: boolean
    initializeSatellites: () => Promise<void>
    clearSatellites: () => void
}

export const useSatelliteData = (
    enabled: boolean,
    onDataUpdate?: (satellites: VisibleSatelliteInfo[]) => void
): UseSatelliteDataReturn
```

**步驟 2.4.2：遷移衛星數據邏輯**
- 將 fetchVisibleSatellites 函數移到 hook 中
- 將 500-565行的 useEffect 邏輯移到 hook 中
- 保持數據初始化的單次載入邏輯

**步驟 2.4.3：創建 SatelliteDataManager.tsx**
- 創建簡單的容器組件包裝 hook
- 處理衛星數據的 UI 顯示邏輯

**Phase 2 驗收標準：**
- [ ] HandoverManagementTab 獨立運行正常
- [ ] DeviceListPanel 顯示所有設備類型
- [ ] UAVSelectionPanel 選擇功能正常
- [ ] useSatelliteData hook 數據載入正常
- [ ] 主檔案減少約 977行（55%）
- [ ] 所有現有功能保持正常
- [ ] 單元測試覆蓋新模組

### Phase 3: 中優先級模組重構 (1-2週)

#### 3.1 手動控制模組重構 (2天)

**步驟 3.1.1：創建 ManualControlPanel.tsx**
```typescript
interface ManualControlPanelProps {
    isVisible: boolean
    auto: boolean
    manualControlEnabled: boolean
    onManualControl: (direction: UAVManualDirection) => void
}
```

**步驟 3.1.2：遷移手動控制邏輯**
- 將 659-687行的手動控制事件處理移到新組件
- 將 1067-1203行的手動控制面板 UI 移到新組件
- 保持現有的按鍵事件處理

#### 3.2 功能開關模組重構 (3天)

**步驟 3.2.1：創建 FeatureToggleManager.tsx**
```typescript
interface FeatureToggleManagerProps {
    activeCategory: string
    featureToggles: FeatureToggle[]
    onToggle: (toggleId: string, enabled: boolean) => void
}
```

**步驟 3.2.2：遷移功能開關邏輯**
- 將 413-491行的 featureToggles 配置移到新組件
- 將 716-748行的 renderFeatureToggles 函數移到新組件
- 創建可復用的功能開關系統

**Phase 3 驗收標準：**
- [ ] ManualControlPanel 控制功能正常
- [ ] FeatureToggleManager 開關邏輯正常
- [ ] 主檔案再減少約 275行（15%）
- [ ] 累積減少約 1252行（70%）

### Phase 4: 低優先級模組重構 (1週)

#### 4.1 設備管理 Hook 重構 (3天)

**步驟 4.1.1：創建 useDeviceManagement.ts**
```typescript
export interface UseDeviceManagementReturn {
    orientationInputs: Record<string, {x: string, y: string, z: string}>
    tempDevices: Device[]
    receiverDevices: Device[]
    desiredDevices: Device[]
    jammerDevices: Device[]
    handleOrientationInputChange: (deviceId: number, axis: 'x'|'y'|'z', value: string) => void
    handleDeviceRoleChange: (deviceId: number, newRole: string) => void
}
```

**步驟 4.1.2：遷移設備管理邏輯**
- 將 567-617行的設備方向輸入處理移到 hook
- 將 691-714行的設備分組邏輯移到 hook
- 優化無限循環問題的修復邏輯

#### 4.2 類別導航模組重構 (1天)

**步驟 4.2.1：創建 CategoryNavigation.tsx**
```typescript
interface CategoryNavigationProps {
    categories: SidebarCategory[]
    activeCategory: string
    onCategoryChange: (categoryId: string) => void
}
```

**步驟 4.2.2：遷移類別導航邏輯**
- 將 492-498行的類別定義移到新組件
- 將 761-783行的類別選擇 UI 移到新組件

**Phase 4 驗收標準：**
- [ ] useDeviceManagement hook 邏輯正常
- [ ] CategoryNavigation 導航功能正常
- [ ] 主檔案再減少約 125行（7%）
- [ ] 累積減少約 1377行（77%）

### Phase 5: 整合和優化 (1週)

#### 5.1 主組件重構 (3天)

**步驟 5.1.1：簡化 EnhancedSidebar.tsx**
```typescript
const EnhancedSidebar: React.FC<SidebarProps> = (props) => {
    // 使用自訂 hooks
    const satelliteData = useSatelliteData(props.satelliteEnabled, props.onSatelliteDataUpdate)
    const deviceManagement = useDeviceManagement(props.devices, props.onDeviceChange)
    
    return (
        <div className="enhanced-sidebar-container">
            <SidebarStarfield />
            
            <CategoryNavigation 
                categories={categories}
                activeCategory={activeCategory}
                onCategoryChange={setActiveCategory}
            />
            
            <FeatureToggleManager
                activeCategory={activeCategory}
                featureToggles={featureToggles}
                onToggle={handleFeatureToggle}
            />
            
            {activeCategory === 'handover_mgr' && (
                <HandoverManagementTab {...handoverProps} />
            )}
            
            {activeCategory === 'uav' && (
                <>
                    <UAVSelectionPanel {...uavSelectionProps} />
                    <ManualControlPanel {...manualControlProps} />
                    <DeviceListPanel {...deviceListProps} />
                </>
            )}
        </div>
    )
}
```

#### 5.2 效能優化 (2天)

**步驟 5.2.1：實施懶加載**
```typescript
// 懶加載非關鍵模組
const HandoverManagementTab = React.lazy(() => import('./sidebar/HandoverManagementTab'))
const DeviceListPanel = React.lazy(() => import('./sidebar/DeviceListPanel'))
```

**步驟 5.2.2：優化重新渲染**
- 使用 React.memo 包裝純組件
- 使用 useCallback 優化回調函數
- 使用 useMemo 快取計算結果

#### 5.3 測試驗證 (2天)

**步驟 5.3.1：整合測試**
```bash
npm run test:unit          # 單元測試
npm run test:integration   # 整合測試
npm run test:e2e          # E2E 測試
```

**步驟 5.3.2：效能測試**
- Bundle 大小分析
- 渲染效能測試
- 記憶體使用量檢查

**Phase 5 驗收標準：**
- [ ] 主檔案最終約 500-600行
- [ ] 總減少約 1200-1300行（65-70%）
- [ ] 所有功能測試通過
- [ ] 效能指標符合要求
- [ ] Bundle 大小優化完成

## ✅ 重構後效果預期

### 📈 量化指標

| 指標 | 重構前 | 重構後 | 改善幅度 |
|------|--------|--------|----------|
| 主檔案行數 | 1771行 | 500-600行 | ↓65-70% |
| 單一檔案複雜度 | 極高 | 中等 | ↓顯著降低 |
| 模組數量 | 1個 | 8-10個 | ↑8-10倍 |
| 功能獨立性 | 低 | 高 | ↑顯著提升 |
| 可測試性 | 困難 | 容易 | ↑顯著提升 |
| 團隊協作效率 | 低 | 高 | ↑顯著提升 |

### 🎯 功能性改善

**開發體驗改善：**
- ✅ 單一職責：每個模組只負責一個功能領域
- ✅ 低耦合：模組間通過 props 和 callbacks 通信
- ✅ 高內聚：相關邏輯集中在同一模組
- ✅ 可配置：支援功能開關和條件渲染
- ✅ 可測試：每個模組可獨立測試

**維護效率提升：**
- ✅ 問題定位更快速：功能分散到專門模組
- ✅ 程式碼審查更容易：小模組更易理解
- ✅ 功能開發更獨立：減少開發衝突
- ✅ 錯誤影響範圍更小：模組化減少連鎖反應

**未來擴展支援：**
- ✅ 新功能開發：可獨立創建新模組
- ✅ 功能移除：如換手管理可輕易移除
- ✅ A/B 測試：模組化支援功能切換
- ✅ 效能優化：支援按需載入

## 🚨 風險控制與注意事項

### ⚠️ 重構風險識別

**高風險項目：**
1. **功能回歸風險**：模組化可能引入新的 bug
2. **效能影響風險**：過度模組化可能影響載入效能
3. **測試覆蓋風險**：新模組需要完整的測試覆蓋
4. **整合複雜度風險**：模組間的資料流可能變複雜

**中風險項目：**
1. **型別定義風險**：共用型別可能不夠完整
2. **樣式隔離風險**：CSS 樣式可能需要調整
3. **狀態管理風險**：狀態可能在模組間不同步

### 🛡️ 風險控制策略

**階段性驗證：**
- 每個 Phase 完成後進行完整功能測試
- 使用自動化測試確保功能無回歸
- 保持現有的 E2E 測試覆蓋

**回滾計畫：**
- 每個階段完成後創建 git tag
- 保持原始檔案的備份版本
- 發現問題時可快速回滾到穩定版本

**漸進式重構：**
- 不進行大爆炸式重寫
- 每次只重構一個模組
- 保持系統在重構過程中的可用性

### 📋 檢查清單

#### 重構前檢查
- [ ] 現有功能完整測試通過
- [ ] 建立完整的測試基線
- [ ] 確定重構範圍和優先順序
- [ ] 準備回滾計畫

#### 重構中監控
- [ ] 每個階段後功能驗證
- [ ] 效能指標持續監控
- [ ] 程式碼品質檢查通過
- [ ] 團隊 code review 完成

#### 重構後驗證
- [ ] 完整功能測試通過
- [ ] 效能指標符合預期
- [ ] 程式碼覆蓋率達標
- [ ] 文件更新完成

## 🏆 成功標準

**技術指標：**
- 主檔案行數 < 600行
- 模組化覆蓋率 > 75%
- 測試覆蓋率 > 80%
- Build 時間變化 < 10%

**功能指標：**
- 所有現有功能正常運作
- 新模組獨立性驗證通過
- 效能回歸測試通過
- 使用者體驗無變化

**維護指標：**
- 新功能開發時間減少 > 30%
- Bug 修復時間減少 > 40%
- 程式碼審查效率提升 > 50%
- 團隊協作滿意度提升

---

**📝 備註：**
- 本重構計畫遵循漸進式重構原則，確保系統穩定性
- 所有階段都有明確的驗收標準和回滾機制
- 重構過程中保持與利害相關人的溝通和反饋
- 重構完成後需要更新相關技術文件和開發指南
