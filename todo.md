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

### 檔案結構 ✅
```
simworld/frontend/src/
├── components/domains/measurement/
│   ├── charts/EventA4Chart.tsx      # Event A4 主要圖表組件
│   ├── charts/EventA4Chart.scss     # 專業樣式設計
│   ├── types/index.ts               # TypeScript 類型定義
│   └── index.ts                     # 領域匯出
├── pages/MeasurementEventsPage.tsx  # 儀表板頁面
├── pages/MeasurementEventsPage.scss # 頁面樣式
├── utils/csvDataParser.ts           # 數據處理工具
└── public/Line-Plot.csv             # RSRP 曲線數據
```

## 🔄 進行中項目

### Event A4 進階註解 🔄
- [ ] 添加所有 Event A4 註解：Trigger Condition, Cancel Condition, Offset, Hys 標籤與箭頭
- [ ] 實現 TimeToTrigger, reportInterval, reportAmount, reportOnLeave 標記和註解
- [ ] 實現觸發條件邏輯（Mn + Ofn + Ocn – Hys > Thresh）並提供視覺反饋

## 📋 待完成項目

### Event D1 實作（距離門檻事件）
- [ ] 設計 Event D1 圖表結構，雙距離曲線（UE-referenceLocation1, UE-referenceLocation2）對時間
- [ ] 創建 D1 事件的兩條距離曲線，不同顏色（綠色距離1，橙色距離2）
- [ ] 添加 D1 雙門檻線（Thresh1 和 Thresh2），適當距離單位（公尺）
- [ ] 實現 D1 雙條件邏輯（Ml1 > Thresh1 AND Ml2 < Thresh2）與視覺指示器

### Event D2 實作（移動參考位置）
- [ ] 設計 Event D2 圖表，類似 D1 但考慮移動參考位置
- [ ] 實現 D2 移動參考位置邏輯和衛星星曆考量

### Event T1 實作（時間窗口事件）
- [ ] 設計 Event T1 時間基礎圖表（Mt > Thresh1 持續時間窗口）
- [ ] 實現 T1 時間窗口視覺化，垂直門檻線和持續時間高亮

### 系統整合
- [ ] 創建圖表導航系統，切換 A4, D1, D2, T1 圖表視圖
- [ ] 添加全面文檔，解釋每個事件類型和圖表互動
- [ ] 測試所有圖表，不同參數值並驗證 3GPP TS 38.331 規範

## 🎯 Event A4 圖表位置

**主要檔案位置：**
- **React 組件**: `/home/sat/ntn-stack/simworld/frontend/src/components/domains/measurement/charts/EventA4Chart.tsx`
- **頁面**: `/home/sat/ntn-stack/simworld/frontend/src/pages/MeasurementEventsPage.tsx`
- **數據**: `/home/sat/ntn-stack/simworld/frontend/public/Line-Plot.csv`

**如何訪問：**
1. 啟動前端服務：`cd /home/sat/ntn-stack/simworld/frontend && npm run dev`
2. 瀏覽器打開：`http://localhost:5173`
3. **方法一 - 直接網址**：瀏覽器訪問 `http://localhost:5173/measurement-events`
4. **方法二 - Navbar 按鈕**：點擊頂部導航欄的 "📡 Event A4" 按鈕

## 📊 Event A4 功能特點

### 3GPP TS 38.331 合規性 ✅
- **進入條件 A4-1**: `Mn + Ofn + Ocn – Hys > Thresh`
- **離開條件 A4-2**: `Mn + Ofn + Ocn + Hys < Thresh`
- **參數範圍**: 符合 3GPP 標準值範圍
- **時間窗口**: TimeToTrigger 標準選項

### 視覺化元素 ✅
- 藍色 RSRP 曲線（鄰小區信號強度）
- 紅色虛線門檻線（a4-Threshold）
- 遲滯（Hys）上下界線
- 移動節點動畫播放系統
- 即時參數調整控制面板

### 互動功能 ✅
- 播放/暫停/重置動畫控制
- 即時參數調整（閾值、遲滯、偏置等）
- 響應式設計支援多種設備
- 專業樣式符合工程標準

## 🔧 技術規格

- **框架**: React 19 + TypeScript
- **圖表引擎**: Chart.js 4.5 + react-chartjs-2
- **註解系統**: chartjs-plugin-annotation 3.1
- **樣式**: SCSS 模組化設計
- **數據格式**: CSV 解析與處理
- **動畫**: requestAnimationFrame 平滑動畫

## 📈 下一步開發重點

1. **完善 Event A4 註解系統** - 添加所有箭頭和標籤
2. **實現觸發邏輯視覺化** - 條件滿足時的即時視覺反饋
3. **開始 Event D1 開發** - 距離測量事件圖表
4. **建立事件切換導航** - 統一的多事件儀表板

Event A4 圖表已成功實現並可以使用！