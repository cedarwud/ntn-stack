# 3GPP TS 38.331 測量事件互動圖表實作狀態

## ✅ 已完成項目

### Event A4 圖表核心功能 ✅
- [x] 設置 Chart.js 專案環境（react-chartjs-2, chartjs-plugin-annotation）
- [x] 解析 Line-Plot.csv 數據並轉換為 Chart.js 格式
- [x] 創建 Event A4 基礎圖表配置（時間 X 軸，RSRP dBm Y 軸）
- [x] 實現藍色 RSRP 曲線，使用 CSV 數據點並平滑渲染
- [x] 添加紅色虛線門檻線（a4-Threshold）使用註解插件
- [x] 實現動畫按鈕和移動節點，沿 RSRP 曲線時間進行
- [x] 添加互動參數控制（閾值、遲滯、時間參數調整）
- [x] 實現響應式設計，適配不同螢幕尺寸
- [x] 性能優化（React.memo、useMemo、useCallback）- 解決重新渲染問題
- [x] 深度修復主題切換導致的圖表重新創建問題
- [x] 實現圖表更新策略（使用 Chart.js update() 而非重新創建）

### Event A4 進階功能 ✅  
- [x] 實現 3GPP TS 38.331 規範完整邏輯
  - [x] 進入條件 A4-1：`Mn + Ofn + Ocn – Hys > Thresh`
  - [x] 離開條件 A4-2：`Mn + Ofn + Ocn + Hys < Thresh`
  - [x] 支援所有參數：Offset (Ofn, Ocn), Hysteresis, TimeToTrigger
  - [x] 支援報告參數：reportAmount, reportInterval, reportOnLeave

### 檔案結構優化 ✅
```
simworld/frontend/src/
├── components/domains/measurement/
│   ├── charts/
│   │   ├── PureA4Chart.tsx          # 核心圖表組件（已優化）
│   │   └── EventA4Chart.tsx         # Event A4 主要圖表組件
│   ├── viewers/
│   │   ├── MeasurementEventsViewer.tsx  # 事件查看器
│   │   └── EventA4Viewer.tsx            # A4 專用查看器
│   ├── modals/
│   │   └── MeasurementEventsModal.tsx   # 事件模態框
│   ├── types/index.ts               # TypeScript 類型定義
│   └── index.ts                     # 領域匯出
├── pages/MeasurementEventsPage.tsx  # 儀表板頁面
├── utils/csvDataParser.ts           # 數據處理工具
└── public/Line-Plot.csv             # RSRP 曲線數據
```

## 🔄 進行中項目

### Event A4 完善註解系統 🔄
- [ ] 添加完整的 3GPP TS 38.331 註解標示
  - [ ] Trigger Condition 箭頭：指向觸發點，標示「A4-1 Enter」
  - [ ] Cancel Condition 箭頭：指向取消點，標示「A4-2 Leave」
  - [ ] Offset 垂直箭頭：標示 Ofn + Ocn 對有效門檻的影響
  - [ ] Hysteresis 雙向箭頭：標示進入/離開條件的遲滯差值
  - [ ] TimeToTrigger 時間範圍：標示觸發條件持續時間
  - [ ] reportAmount 報告點：標示多次測量報告的時間點
  - [ ] reportInterval 間隔箭頭：標示報告間隔時間
  - [ ] reportOnLeave 標記：標示離開時的最後報告

## 📋 待完成項目

### Phase 1: Event D1 實作（距離雙門檻事件）📅 預計2週
> 基於 3GPP TS 38.331 Section 5.5.4.15 規範

#### D1-1: 基礎圖表結構 (3天)
- [ ] 創建 `EventD1Chart.tsx` 組件
- [ ] 設計雙距離曲線圖表（X軸：時間，Y軸：距離(m)）
- [ ] 創建模擬距離數據集
  - [ ] 距離1：UE 到 referenceLocation1 的距離隨時間變化
  - [ ] 距離2：UE 到 referenceLocation2 的距離隨時間變化
- [ ] 使用不同顏色區分（綠色：距離1，橙色：距離2）
- [ ] 設置 Y軸單位為公尺(m)，範圍涵蓋所有門檻值

#### D1-2: 雙門檻線與條件邏輯 (3天)
- [ ] 實現雙門檻線繪製
  - [ ] Thresh1 水平線（距離1的門檻）
  - [ ] Thresh2 水平線（距離2的門檻）
- [ ] 實現 3GPP D1 事件邏輯
  - [ ] 進入條件：`Ml1 – Hys > Thresh1` AND `Ml2 + Hys < Thresh2`
  - [ ] 離開條件：`Ml1 + Hys < Thresh1` OR `Ml2 – Hys > Thresh2`
- [ ] 添加 hysteresisLocation 參數支援
- [ ] 實現雙條件同時滿足的視覺指示器

#### D1-3: 互動功能與註解 (2天)
- [ ] 移植 A4 的動畫控制系統
- [ ] 添加 D1 專用註解標示
  - [ ] 「D1-1 & D1-2 Enter」：雙條件觸發點
  - [ ] 「D1-3 or D1-4 Leave」：任一離開條件
  - [ ] 距離門檻標籤與箭頭
- [ ] 實現參數控制面板（distanceThreshFromReference1/2）
- [ ] 添加 TimeToTrigger 持續時間要求

#### D1-4: 系統整合 (2天)
- [ ] 創建 `EventD1Viewer.tsx` 查看器
- [ ] 更新 `MeasurementEventsViewer.tsx` 支援 D1 事件
- [ ] 添加 D1 事件類型定義
- [ ] 測試所有 D1 功能並驗證 3GPP 規範合規性

### Phase 2: Event D2 實作（移動參考位置事件）📅 預計1.5週
> 基於 3GPP TS 38.331 Section 5.5.4.15a 規範

#### D2-1: 移動參考位置邏輯 (3天)
- [ ] 基於 D1 程式碼創建 `EventD2Chart.tsx`
- [ ] 實現移動參考位置概念
  - [ ] 服務小區移動參考位置（基於 movingReferenceLocation + 衛星星曆）
  - [ ] 固定參考位置（基於 MeasObjectNR 的 referenceLocation）
- [ ] 創建考慮移動參考點的距離數據集
- [ ] 實現 D2 事件邏輯（與 D1 相同但參考點不同）

#### D2-2: 衛星軌道模擬 (2天)
- [ ] 添加移動參考位置的視覺化提示
- [ ] 實現基於時間的參考位置移動模擬
- [ ] 添加衛星星曆數據考量的註解說明
- [ ] 整合 D2 查看器與系統

#### D2-3: 測試與優化 (2天)
- [ ] 驗證 D2 與 D1 的邏輯差異
- [ ] 性能優化（參考 A4 的優化經驗）
- [ ] 完整測試移動參考位置功能

### Phase 3: Event T1 實作（時間窗口條件事件）📅 預計1週
> 基於 3GPP TS 38.331 Section 5.5.4.16 規範

#### T1-1: 時間基礎圖表 (3天)
- [ ] 創建 `EventT1Chart.tsx` 組件
- [ ] 設計時間窗口圖表（X軸：時間(ms)，Y軸：事件狀態 0/1）
- [ ] 實現 T1 條件邏輯
  - [ ] 進入條件：`Mt > Thresh1`
  - [ ] 離開條件：`Mt > Thresh1 + Duration`
- [ ] 繪製垂直門檻線（t1-Threshold 和 t1-Threshold+Duration）
- [ ] 實現狀態矩形脈衝曲線

#### T1-2: 時間窗口視覺化 (2天)
- [ ] 添加半透明時間窗口區域標記
- [ ] 實現時間游標動畫
- [ ] 添加 T1 專用註解（「T1-1 Enter」、「T1-2 Leave」）
- [ ] 隱藏不適用的參數（reportAmount/Interval，因為 T1 主要用於條件切換）

#### T1-3: 系統整合 (2天)
- [ ] 創建 `EventT1Viewer.tsx` 查看器
- [ ] 整合到主要事件系統
- [ ] 測試條件切換應用場景

### Phase 4: 多事件導航系統 📅 預計1週

#### 4-1: 統一事件管理 (3天)
- [ ] 創建 `EventSelector.tsx` 事件選擇器
- [ ] 實現事件類型切換功能（A4 ↔ D1 ↔ D2 ↔ T1）
- [ ] 統一事件配置管理
- [ ] 創建通用事件配置介面

#### 4-2: 比較功能 (2天)
- [ ] 實現多事件並排比較視圖
- [ ] 添加事件差異說明
- [ ] 創建 3GPP 規範對照表

#### 4-3: 最終整合 (2天)
- [ ] 更新主導航支援所有事件
- [ ] 性能優化整個事件系統
- [ ] 完整的系統測試

## 🎯 開發策略與技術重點

### 程式架構重用策略
- **Chart 組件模組化**：基於 A4 成功經驗，創建通用 Chart 基類
- **配置驅動**：使用 `eventConfigs` 對照表定義各事件的門檻、參數、註解
- **型別安全**：擴展 TypeScript 類型支援所有事件類型
- **性能優化**：沿用 A4 的 React.memo、useMemo、useCallback 優化模式

### 數據處理策略
- **A4**: 使用現有 `Line-Plot.csv` RSRP 數據
- **D1/D2**: 創建距離數據集，模擬 UE 移動軌跡
- **T1**: 程式化生成時間狀態數據

### 3GPP 規範合規性檢查點
- [ ] 每個事件實現後進行規範對照驗證
- [ ] 確保所有不等式條件實現正確
- [ ] 驗證參數單位與範圍符合標準
- [ ] 測試邊界條件與異常情況

## 📊 當前 Event A4 訪問方式

**主要檔案位置：**
- **React 組件**: `/home/sat/ntn-stack/simworld/frontend/src/components/domains/measurement/charts/PureA4Chart.tsx`
- **頁面**: `/home/sat/ntn-stack/simworld/frontend/src/pages/MeasurementEventsPage.tsx`
- **數據**: `/home/sat/ntn-stack/simworld/frontend/public/Line-Plot.csv`

**如何訪問：**
1. 啟動前端服務：`cd /home/sat/ntn-stack/simworld/frontend && npm run dev`
2. 瀏覽器打開：`http://localhost:5173`
3. **方法一 - 直接網址**：瀏覽器訪問 `http://localhost:5173/measurement-events`
4. **方法二 - Navbar 按鈕**：點擊頂部導航欄的 "📡 Event A4" 按鈕

## 🔧 技術規格

- **框架**: React 19 + TypeScript
- **圖表引擎**: Chart.js 4.5 + react-chartjs-2
- **註解系統**: chartjs-plugin-annotation 3.1
- **樣式**: SCSS 模組化設計
- **數據格式**: CSV 解析與處理
- **動畫**: requestAnimationFrame 平滑動畫
- **性能**: React.memo + useMemo + useCallback 優化

## 📈 開發里程碑

- **第1週**: 完成 Event A4 註解系統 ✅
- **第2-3週**: 完成 Event D1 實作
- **第4-5週**: 完成 Event D2 實作  
- **第6週**: 完成 Event T1 實作
- **第7週**: 完成多事件導航系統
- **第8週**: 整體優化與測試

Event A4 圖表已成功實現並經過性能優化，可以開始下一階段的 D1、D2、T1 事件開發！