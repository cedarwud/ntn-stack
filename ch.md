# 衛星通訊事件圖表重構計畫

## 現況分析 (UltraThink 評估)

### 核心問題識別
經過深度分析，專案中的4個事件圖表存在**極度嚴重的代碼重複問題**：

#### 1. **Viewer 組件重複度 > 80%**
- `EventA4Viewer.tsx` (1,185行)
- `EventD1Viewer.tsx` (類似結構)
- `EventD2Viewer.tsx` (類似結構)
- `EventT1Viewer.tsx` (類似結構)

#### 2. **重複的核心功能模塊**
- **動畫狀態管理** (100+ 行相同代碼)
- **解說面板系統** (500+ 行相同代碼)
- **拖拽邏輯** (200+ 行完全相同)
- **控制面板結構** (400+ 行相似結構)
- **事件狀態顯示** (150+ 行相同邏輯)
- **主題管理** (100+ 行相同代碼)

#### 3. **Pure Chart 組件重複**
- `PureA4Chart.tsx`, `PureD1Chart.tsx`, `PureD2Chart.tsx`, `PureT1Chart.tsx`
- Chart.js 配置、數據處理、主題切換邏輯高度相似

#### 4. **樣式重複使用**
- 所有組件都引用 `'./EventA4Viewer.scss'` (重用 A4 樣式)
- 所有組件都使用 `'./NarrationPanel.scss'`

### 影響評估
- **開發效率**: 新功能需要4倍開發時間
- **維護成本**: 錯誤修復需要4個地方同步
- **一致性風險**: 功能實現容易不同步
- **Bundle 大小**: 重複代碼導致不必要的體積增加
- **代碼品質**: 違反 DRY 原則，可讀性降低

## 重構方案設計

### 階段一：核心共享組件建立
#### 1.1 建立 `BaseEventViewer` 抽象組件
```typescript
// components/domains/measurement/shared/BaseEventViewer.tsx
interface BaseEventViewerProps<T extends MeasurementEventParams> {
  eventType: EventType
  params: T
  onParamsChange: (params: T) => void
  chartComponent: React.ComponentType<any>
  // 其他共享屬性
}
```

#### 1.2 提取 `AnimationController` 組件
```typescript
// components/domains/measurement/shared/AnimationController.tsx
- 動畫狀態管理 (isPlaying, currentTime, speed)
- 播放/暫停/重置控制
- 時間軸拖拽控制
- 動畫進度更新邏輯
```

#### 1.3 建立 `NarrationPanel` 獨立組件
```typescript
// components/domains/measurement/shared/NarrationPanel.tsx
- 拖拽邏輯 (200+ 行完全相同代碼)
- 位置管理和邊界限制
- 透明度控制
- 最小化/展開功能
- 技術細節切換
```

#### 1.4 建立 `EventControlPanel` 組件
```typescript
// components/domains/measurement/shared/EventControlPanel.tsx
- 參數控制面板基礎結構
- 重置功能
- 主題切換
- 門檻線顯示控制
```

### 階段二：事件特定邏輯模塊化
#### 2.1 建立事件特定的 Hook
```typescript
// hooks/useEventA4Logic.ts
// hooks/useEventD1Logic.ts
// hooks/useEventD2Logic.ts
// hooks/useEventT1Logic.ts
```

#### 2.2 參數配置抽象化
```typescript
// config/eventParameterConfigs.ts
export const EVENT_PARAMETER_CONFIGS = {
  A4: { /* A4 特定參數配置 */ },
  D1: { /* D1 特定參數配置 */ },
  D2: { /* D2 特定參數配置 */ },
  T1: { /* T1 特定參數配置 */ }
}
```

#### 2.3 解說內容生成器
```typescript
// utils/narrationGenerators.ts
export const createNarrationGenerator = (eventType: EventType) => {
  // 基於事件類型生成解說內容
}
```

### 階段三：圖表組件統一化
#### 3.1 建立 `BaseChart` 組件
```typescript
// components/domains/measurement/shared/BaseChart.tsx
- Chart.js 基礎配置
- 主題切換邏輯
- 門檻線渲染
- 動畫游標
```

#### 3.2 圖表配置工廠
```typescript
// utils/chartConfigFactory.ts
export const createChartConfig = (
  eventType: EventType,
  params: MeasurementEventParams,
  theme: 'light' | 'dark'
) => {
  // 根據事件類型生成圖表配置
}
```

### 階段四：最終整合
#### 4.1 重構後的 Viewer 組件結構
```typescript
// EventA4Viewer.tsx (簡化後 < 200 行)
export const EventA4Viewer = () => {
  const eventLogic = useEventA4Logic()
  const narrationGenerator = createNarrationGenerator('A4')
  
  return (
    <BaseEventViewer
      eventType="A4"
      params={eventLogic.params}
      onParamsChange={eventLogic.setParams}
      chartComponent={PureA4Chart}
      narrationGenerator={narrationGenerator}
    />
  )
}
```

## 實施步驟流程

### Step 1: 準備階段 (估計 1-2 天)
1. **建立共享目錄結構**
   ```
   measurement/
   ├── shared/
   │   ├── components/
   │   ├── hooks/
   │   ├── utils/
   │   └── types/
   ```

2. **建立基礎類型定義**
   - 擴展現有的 `MeasurementEventParams`
   - 定義共享組件的接口

### Step 2: 核心組件抽取 (估計 2-3 天)
1. **抽取 AnimationController**
   - 從 EventA4Viewer 中提取動畫邏輯
   - 建立通用的動畫狀態管理

2. **抽取 NarrationPanel**  
   - 提取拖拽邏輯 (200+ 行完全相同代碼)
   - 建立通用的解說面板組件

3. **抽取 EventControlPanel**
   - 提取參數控制面板基礎結構
   - 建立可配置的控制面板組件

### Step 3: 事件特定邏輯重構 (估計 2-3 天)
1. **建立事件特定 Hook**
   - 將各事件的參數邏輯封裝成 Hook
   - 處理事件特定的狀態管理

2. **建立解說內容生成器**
   - 抽取解說文本生成邏輯
   - 建立事件特定的解說內容模板

### Step 4: BaseEventViewer 建立 (估計 2-3 天)
1. **設計 BaseEventViewer 架構**
   - 整合所有共享組件
   - 建立插件化的架構

2. **建立配置驅動的渲染系統**
   - 基於事件類型渲染不同的參數控制
   - 動態載入事件特定的邏輯

### Step 5: 圖表組件統一化 (估計 1-2 天)
1. **建立 BaseChart 組件**
   - 抽取 Chart.js 共享配置
   - 統一主題和動畫邏輯

2. **建立圖表配置工廠**
   - 根據事件類型生成專屬配置
   - 處理數據格式轉換

### Step 6: 逐步遷移 (估計 3-4 天)
1. **A4 事件遷移** (第一個，作為範本)
2. **D1 事件遷移** (驗證架構可行性)
3. **D2 事件遷移** (進一步驗證)
4. **T1 事件遷移** (最終驗證)

### Step 7: 測試與優化 (估計 1-2 天)
1. **功能測試**
   - 確保所有事件功能正常
   - 驗證動畫和交互

2. **性能測試**
   - 測量 Bundle 大小減少
   - 確認渲染性能

## 預期成果

### 代碼品質提升
- **代碼重複度**: 從 80% 降到 < 20%
- **單個 Viewer 組件**: 從 1000+ 行降到 < 200 行
- **維護性**: 單一修改點，自動同步所有事件

### 開發效率提升
- **新功能開發**: 從 4x 時間降到 1x 時間
- **錯誤修復**: 從 4 個地方修復降到 1 個地方
- **一致性保證**: 架構自動保證功能一致性

### 性能優化
- **Bundle 大小**: 預計減少 30-40%
- **載入性能**: 共享組件提升載入速度
- **運行時性能**: 統一的優化策略

## 風險評估與應對

### 高風險項目
1. **架構設計複雜性**
   - **風險**: 過度抽象導致維護困難
   - **應對**: 分階段實施，每階段驗證可行性

2. **現有功能破壞**
   - **風險**: 重構過程中破壞現有功能
   - **應對**: 建立完整的測試套件，逐步遷移

### 中風險項目
1. **性能回退**
   - **風險**: 抽象層次增加導致性能問題
   - **應對**: 持續性能監控，適時優化

2. **學習成本**
   - **風險**: 新架構增加團隊學習成本
   - **應對**: 詳細文檔和範例，漸進式培訓

## 成功指標

### 量化指標
- **代碼重複度**: < 20%
- **單個 Viewer 組件行數**: < 200 行
- **Bundle 大小減少**: > 30%
- **新功能開發時間**: 減少 75%

### 質化指標
- **維護性**: 單一修改點影響所有事件
- **一致性**: 所有事件功能保持同步
- **可擴展性**: 新事件類型快速添加
- **開發體驗**: 團隊開發效率顯著提升

---

## 後續優化建議

### 階段二優化
1. **事件比較功能**: 利用統一架構建立事件對比
2. **測試自動化**: 建立自動化測試套件
3. **性能監控**: 建立性能監控儀表板

### 長期演進
1. **事件模擬器**: 建立通用的事件模擬框架
2. **配置視覺化**: 建立參數配置的視覺化編輯器
3. **AI 輔助**: 利用 AI 自動優化事件參數

---

**總結**: 這是一個複雜但必要的重構專案，將從根本上解決代碼重複問題，大幅提升開發效率和維護性。透過分階段實施和持續驗證，可以將風險控制在可接受範圍內。