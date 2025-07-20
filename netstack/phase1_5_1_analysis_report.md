# Phase 1.5.1 統一 SIB19 基礎平台分析設計報告

## 🎯 核心理念
實現 "資訊統一、應用分化" 的理想圖表架構 - 統一的 SIB19 基礎平台 + 事件特定的視覺化應用

---

## 📊 當前圖表架構根本性問題分析

### 1. 資訊孤島問題 🚨
**現狀**: 各事件圖表獨立維護相似的軌道和時間數據

#### 具體問題：
- **A4 事件圖表**: 獨立計算衛星位置和信號強度
- **D1 事件圖表**: 重複實現距離計算和參考位置管理
- **D2 事件圖表**: 單獨維護動態參考位置和衛星軌道
- **T1 事件圖表**: 獨立的時間同步和計時器管理

#### 影響：
- 數據不一致性：同一時刻不同圖表顯示的衛星位置可能不同
- 資源浪費：重複的 API 調用和計算邏輯
- 維護困難：修改軌道算法需要更新多個圖表

### 2. 重複配置浪費 💸
**現狀**: D1、D2、A4、T1 分別計算類似的衛星參數

#### 重複的配置項：
- 衛星星曆數據 (satelliteEphemeris)
- 時間基準 (epochTime)
- 鄰居細胞配置 (ntn-NeighCellConfigList)
- SMTC 測量窗口配置

#### 浪費指標：
- **API 調用重複率**: 估計 70-80% 的 API 調用是重複的
- **計算資源浪費**: 相同的軌道計算在多個組件中重複執行
- **配置管理複雜度**: 4 個事件 × 8 個鄰居細胞 = 32 個獨立配置點

### 3. 缺乏統一基準 📏
**現狀**: 時間同步、位置基準不一致，影響跨事件比較

#### 不一致問題：
- **時間基準不統一**: 各事件使用不同的時間參考點
- **座標系統差異**: 地理座標和衛星座標系統混用
- **精度標準不同**: 不同事件使用不同的計算精度

#### 跨事件比較困難：
- 無法準確比較不同事件的觸發時機
- 難以分析事件間的相關性
- 缺乏全局的性能基準

### 4. 可擴展性差 🔧
**現狀**: 新增事件需要重新實現基礎軌道和時間邏輯

#### 擴展困難：
- 每個新事件都需要重新實現軌道計算
- 缺乏標準化的圖表組件接口
- 沒有統一的數據格式和 API 規範

---

## 🏗️ 統一 SIB19 基礎圖表平台設計

### 1. SIB19 統一數據層 📊
**設計理念**: 所有事件圖表共享同一套 SIB19 解析和管理

#### 核心組件：
```typescript
// SIB19 統一數據管理器
class SIB19UnifiedDataManager {
  // 單一數據源
  private sib19Data: SIB19Data
  private satellitePositions: Map<string, SatellitePosition>
  private neighborCells: NeighborCellConfig[]
  
  // 統一更新機制
  async updateSIB19Data(): Promise<void>
  
  // 事件特定數據萃取
  getA4SpecificData(): A4SIB19Data
  getD1SpecificData(): D1SIB19Data
  getD2SpecificData(): D2SIB19Data
  getT1SpecificData(): T1SIB19Data
}
```

#### 優勢：
- **數據一致性**: 所有圖表使用相同的 SIB19 數據源
- **更新效率**: 單次 API 調用更新所有圖表
- **緩存優化**: 統一的數據緩存和失效管理

### 2. 共享衛星星座視覺化 🛰️
**設計理念**: 統一的衛星軌道、位置、時間基準展示

#### 核心功能：
- **3D 衛星軌道視覺化**: 基於真實 TLE 數據的軌道展示
- **實時位置更新**: 統一的衛星位置計算和更新
- **可見性窗口**: 基於地面位置的衛星可見性計算
- **軌道預測**: 未來 24 小時的軌道預測展示

#### 技術實現：
```typescript
// 共享衛星星座組件
interface SharedSatelliteConstellationProps {
  sib19Data: SIB19Data
  groundPosition: Position
  timeRange: TimeRange
  visibilityThreshold: number
}

const SharedSatelliteConstellation: React.FC<SharedSatelliteConstellationProps>
```

### 3. 鄰居細胞統一管理 📡
**設計理念**: 支援最多 8 個鄰居細胞的統一配置和視覺化

#### 統一管理功能：
- **細胞配置面板**: 統一的鄰居細胞參數配置
- **載波頻率管理**: 自動分配和衝突檢測
- **物理細胞 ID 管理**: 唯一性檢查和自動分配
- **信號強度監控**: 實時的信號品質監控

#### 配置數據結構：
```typescript
interface UnifiedNeighborCellManager {
  cells: NeighborCellConfig[]  // 最多 8 個
  carrierFrequencies: number[]
  physCellIds: number[]
  
  // 統一配置方法
  addNeighborCell(config: NeighborCellConfig): boolean
  removeNeighborCell(cellId: string): boolean
  updateCellConfig(cellId: string, config: Partial<NeighborCellConfig>): boolean
  
  // 衝突檢測
  validateConfiguration(): ValidationResult
}
```

### 4. SMTC 整合的測量窗口管理 ⏰
**設計理念**: 統一的可見性窗口和測量時機指示

#### 核心功能：
- **測量窗口計算**: 基於衛星軌道的最佳測量時機
- **SMTC 配置優化**: 自動調整測量窗口以提高效率
- **功耗優化建議**: 基於衛星可見性的功耗優化
- **測量衝突檢測**: 多個測量事件的時間衝突檢測

---

## 🎨 事件特定的視覺化分化設計

### 1. A4 事件專屬視覺化 📶
**核心**: 位置補償 ΔS,T(t) 視覺化、修正觸發條件展示

#### 專屬組件：
- **位置補償向量圖**: 顯示 ΔS,T(t) 的方向和大小
- **信號強度熱力圖**: 基於位置補償的信號強度分佈
- **觸發條件監控**: A4 門檻值和遲滯的實時監控
- **服務衛星切換動畫**: 衛星切換過程的視覺化

### 2. D1 事件專屬視覺化 📍
**核心**: 固定參考位置 (referenceLocation) 距離計算展示

#### 專屬組件：
- **參考位置標記**: 固定參考點的地圖標記
- **距離測量線**: UE 到參考位置的距離線
- **雙重門檻視覺化**: Thresh1 和 Thresh2 的圓形區域
- **距離變化曲線**: 時間序列的距離變化圖

### 3. D2 事件專屬視覺化 🚀
**核心**: 動態參考位置 (movingReferenceLocation) 計算過程

#### 專屬組件：
- **動態參考軌跡**: 移動參考位置的軌跡展示
- **相對距離計算**: UE 到動態參考位置的距離
- **軌道預測線**: 未來的參考位置軌跡預測
- **速度向量顯示**: 參考位置的移動速度和方向

### 4. T1 事件專屬視覺化 ⏱️
**核心**: 時間框架 (epochTime, t-Service) 和計時器同步展示

#### 專屬組件：
- **時間軸視覺化**: epochTime 和 t-Service 的時間軸
- **同步精度指示器**: 時間同步精度的實時顯示
- **計時器倒數**: T1 觸發的倒數計時器
- **時間偏差圖表**: GNSS 時間偏差的歷史趨勢

---

## 🔄 統一圖表數據流架構重新設計

### 1. 單一 SIB19 數據源架構
```
┌─────────────────────────────────────────────────────────┐
│                SIB19 統一數據源                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │ 衛星星曆    │  │ 參考位置    │  │ 時間校正    │      │
│  │ Ephemeris   │  │ RefLocation │  │TimeCorrection│      │
│  └─────────────┘  └─────────────┘  └─────────────┘      │
└─────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┼─────────┐
                    │         │         │
            ┌───────▼───┐ ┌───▼───┐ ┌───▼───┐ ┌─────▼─────┐
            │A4 事件圖表│ │D1圖表 │ │D2圖表 │ │T1 事件圖表│
            └───────────┘ └───────┘ └───────┘ └───────────┘
```

### 2. 事件選擇性資訊萃取機制
```typescript
interface EventSpecificDataExtractor {
  extractA4Data(sib19: SIB19Data): A4VisualizationData
  extractD1Data(sib19: SIB19Data): D1VisualizationData
  extractD2Data(sib19: SIB19Data): D2VisualizationData
  extractT1Data(sib19: SIB19Data): T1VisualizationData
}
```

### 3. 統一的 validityTime 管理
- **全局有效期監控**: 統一監控所有 SIB19 數據的有效期
- **自動更新提醒**: 在數據即將過期時自動提醒
- **優雅降級**: 數據過期時的優雅降級處理

### 4. 共享的全球化地理支援
- **統一座標系統**: 所有圖表使用相同的地理座標系統 (WGS84)
- **時區處理**: 統一的 UTC 時間基準和本地時區轉換
- **地理計算**: 共享的距離、方位角、仰角計算函數
- **地圖投影**: 統一的地圖投影和視覺化標準

---

## 📋 實施計劃

### Phase 1.5.1 完成標準：
1. ✅ 完成當前架構問題分析
2. ✅ 設計統一 SIB19 基礎圖表平台
3. ✅ 定義事件特定視覺化分化方案
4. ✅ 制定統一數據流架構

### 下一步：Phase 1.5.2
- 實現 SIB19 統一基礎圖表元件
- 開發事件特定視覺化組件
- 整合統一數據流架構
