# D2 圖表時間範圍修復總結

## 問題描述

在 navbar > 換手事件 > d2 圖表中，當切換到"真實"模式時：
- **2小時顯示1個週期** - 這是正確的
- **6小時和12小時顯示相同的圖表** - 這是錯誤的
- **實際上都只顯示比2小時多1/4週期的內容** - 因為固定顯示3小時數據

## 根本原因

系統在真實數據模式下，無論用戶選擇什麼時間範圍，都只獲取和顯示3小時的歷史數據：

1. **後端數據限制**：`HistoricalDataCache` 只提供3小時的預設時間段
2. **前端固定參數**：`fetchHistoricalD2Data` 硬編碼為180分鐘（3小時）
3. **參數傳遞缺失**：`PureD2Chart` 沒有接收用戶選擇的時間範圍

## 修復內容

### 1. 修改 PureD2Chart 接口
```typescript
interface PureD2ChartProps {
    // ... 其他屬性
    historicalDurationMinutes?: number // 新增：歷史數據時間長度（分鐘）
}

const PureD2Chart: React.FC<PureD2ChartProps> = ({
    // ... 其他參數
    historicalDurationMinutes = 180, // 預設3小時
}) => {
```

### 2. 修改 EventD2Viewer 參數傳遞
```typescript
<PureD2Chart
    // ... 其他屬性
    historicalDurationMinutes={selectedTimeRange.durationMinutes}
/>
```

### 3. 修復 fetchHistoricalD2Data 函數
```typescript
// 修復前
await fetchHistoricalD2Data(historicalStartTime, 180) // 固定3小時

// 修復後
await fetchHistoricalD2Data(historicalStartTime, historicalDurationMinutes) // 動態時間長度
```

## 理論週期數計算

基於 LEO 衛星軌道週期 95.6 分鐘：

| 時間範圍 | 分鐘數 | 理論週期數 | 完整週期 | 部分週期 |
|---------|--------|-----------|----------|----------|
| 5分鐘   | 5      | 0.05      | 0        | 0.05     |
| 15分鐘  | 15     | 0.16      | 0        | 0.16     |
| 30分鐘  | 30     | 0.31      | 0        | 0.31     |
| 1小時   | 60     | 0.63      | 0        | 0.63     |
| 2小時   | 120    | 1.26      | 1        | 0.26     |
| 6小時   | 360    | 3.77      | 3        | 0.77     |
| 12小時  | 720    | 7.53      | 7        | 0.53     |

## 修復前後對比

### 修復前
- 6小時和12小時都顯示：1.88 週期（3小時數據）
- 兩者圖表完全相同

### 修復後
- 6小時應顯示：3.77 週期
- 12小時應顯示：7.53 週期
- 兩者圖表明顯不同

## 驗證方法

1. 啟動前端應用
2. 導航到 navbar > 換手事件 > d2 圖表
3. 切換到"真實"模式
4. 測試不同時間範圍，觀察衛星距離曲線的波峰波谷數量：
   - 2小時：約1.3個週期
   - 6小時：約3.8個週期（比2小時多約2.5個週期）
   - 12小時：約7.5個週期（比6小時多約3.8個週期）

## 技術細節

### 後端支持
- `HistoricalD2Request` 模型已支持動態 `duration_minutes` 參數
- `/api/v1/tle/historical-d2-data` 端點已支持任意時間長度

### 前端修改
- `PureD2Chart.tsx`：新增 `historicalDurationMinutes` 參數
- `EventD2Viewer.tsx`：傳遞用戶選擇的時間範圍
- 保持向後兼容性，預設值為180分鐘

### 不需要修改的組件
- `RealD2Chart`：接收已處理的數據，不涉及時間範圍邏輯
- `EventD2Chart`：簡單包裝器，用於基本展示，不涉及歷史數據功能

## 文件修改清單

### 第一階段修復（PureD2Chart - 模擬/歷史模式）
1. `simworld/frontend/src/components/domains/measurement/charts/PureD2Chart.tsx`
   - 新增 `historicalDurationMinutes` 參數
   - 修改 `fetchHistoricalD2Data` 調用
   - 修改歷史數據X軸計算：`index * 5`
   - 修改X軸最大值計算：動態使用 `(totalCount - 1) * 5`

2. `simworld/frontend/src/components/domains/measurement/charts/EventD2Viewer.tsx`
   - 傳遞 `selectedTimeRange.durationMinutes` 到 `PureD2Chart`

### 第二階段修復（RealD2Chart - 真實數據模式）
3. `simworld/frontend/src/components/domains/measurement/charts/RealD2Chart.tsx`
   - 新增 `sampleIntervalSeconds` 參數
   - 修改時間標籤計算：`index * sampleIntervalSeconds`
   - 修改觸發區間計算：`index * sampleIntervalSeconds`

4. `simworld/frontend/src/components/domains/measurement/charts/EventD2Viewer.tsx`
   - 傳遞 `selectedTimeRange.sampleIntervalSeconds` 到 `RealD2Chart`

### 測試腳本
5. `test_d2_time_range_fix.js` - 理論計算驗證
6. `test_real_d2_chart_fix.js` - RealD2Chart 修復驗證

## 額外發現的問題

在測試過程中發現了第二個問題：**X軸顯示範圍限制**

### 問題現象
- 6小時和12小時的時間軸都只顯示到8970秒（約149.5分鐘）
- 實際數據已經獲取了完整的時間範圍，但X軸被截斷了

### 根本原因
1. **歷史數據X軸使用索引**：`x: index` 而不是實際時間秒數
2. **X軸最大值固定**：歷史數據類型使用固定的95秒最大值
3. **數據類型判斷問題**：歷史數據的 `dataSourceInfo.type` 是 `'historical'`，不是 `'realtime-series'`

### 額外修復內容

#### 4. 修改歷史數據X軸計算
```typescript
// 修復前
const points1 = displayData.map((entry, index) => ({
    x: index, // 使用索引
    y: entry.satelliteDistance,
}))

// 修復後
const points1 = displayData.map((entry, index) => ({
    x: index * 5, // 轉換為實際時間秒數（5秒間隔）
    y: entry.satelliteDistance,
}))
```

#### 5. 修改X軸最大值計算
```typescript
// 修復前
max: dataSourceInfo.type === 'realtime-series'
    ? (dataSourceInfo.count - 1) * 5
    : 95, // 固定95秒

// 修復後
max: dataSourceInfo.type === 'realtime-series'
    ? (dataSourceInfo.count - 1) * 5
    : dataSourceInfo.type === 'historical'
    ? Math.max(95, (dataSourceInfo.totalCount - 1) * 5) // 動態計算歷史數據範圍
    : 95, // 模擬數據固定範圍
```

## 最終預期結果

修復後的X軸顯示範圍：
- **2小時**：0-7195秒（119.9分鐘）≈ 1.26個軌道週期
- **6小時**：0-21595秒（359.9分鐘）≈ 3.77個軌道週期
- **12小時**：0-43195秒（719.9分鐘）≈ 7.53個軌道週期

## 第三個問題：數據點數量限制 ✅ 已修復

在進一步測試中發現了第三個問題：**數據獲取數量限制**

### 問題現象
- 無論選擇什麼時間範圍，最多只能獲取1000個數據點
- 6小時需要2160個數據點，12小時需要4320個數據點
- 超出1000個的數據被截斷，導致時間軸顯示不完整

### 根本原因
在 `unifiedD2DataService.ts` 中：
```typescript
async getCachedD2Measurements(scenarioHash: string, limit = 1000)
```
固定的 `limit = 1000` 限制了數據獲取數量。

### 第三階段修復內容

#### 6. 修改 unifiedD2DataService.getD2Data()
```typescript
// 修復前
const measurements = await this.getCachedD2Measurements(precomputeResult.scenario_hash)

// 修復後
const totalSeconds = config.duration_minutes * 60
const expectedDataPoints = Math.ceil(totalSeconds / config.sample_interval_seconds)
const limit = Math.max(1000, expectedDataPoints + 100) // 動態計算限制
const measurements = await this.getCachedD2Measurements(precomputeResult.scenario_hash, limit)
```

## 最終預期結果

修復後的完整數據流：
- **2小時**：720個數據點，X軸顯示0-7190秒 ≈ 1.26個軌道週期
- **6小時**：2160個數據點，X軸顯示0-21590秒 ≈ 3.77個軌道週期
- **12小時**：4320個數據點，X軸顯示0-43190秒 ≈ 7.53個軌道週期

用戶將能看到完整的時間範圍和正確的軌道週期數量，6小時和12小時將顯示明顯不同的圖表模式。
