# 前端數據可視化組件開發 - 圖表 Dropdown 整合

## 概述

本次實現將 SimWorld 前端 Navbar 中的 4 個獨立圖表菜單項整合為一個統一的「數據可視化」dropdown，提升用戶體驗和界面整潔度。

## 實現內容

### 1. 圖表整合

將以下 4 個圖表菜單項：

-   **SINR MAP** - 信號干擾噪聲比地圖
-   **Constellation & CFR** - 星座圖與通道頻率響應
-   **Delay–Doppler** - 延遲多普勒圖
-   **Time-Frequency** - 時頻圖

整合為一個「**數據可視化**」dropdown 菜單。

### 2. 技術實現

#### 2.1 組件修改 (`simworld/frontend/src/components/layout/Navbar.tsx`)

-   新增 `isChartsDropdownOpen` 狀態管理 dropdown 開關
-   新增 `isMobile` 狀態檢測移動端設備
-   實現 `handleChartsDropdownToggle` 處理移動端點擊切換
-   實現 `handleChartsMouseEnter/Leave` 處理桌面端 hover 效果
-   保留所有原有的模態框功能和配置

#### 2.2 樣式實現 (`simworld/frontend/src/styles/Navbar.scss`)

**桌面端樣式：**

-   `.navbar-dropdown-item` - dropdown 容器樣式
-   `.dropdown-trigger` - 觸發器樣式，包含箭頭動畫
-   `.charts-dropdown` - dropdown 菜單樣式
-   `.charts-dropdown-item` - 菜單項樣式

**移動端響應式設計：**

-   768px 斷點響應式設計
-   移動端點擊切換機制
-   `.mobile-expanded` 類處理移動端展開狀態

### 3. 交互設計

#### 3.1 桌面端 (>768px)

-   **Hover 觸發**：滑鼠懸停顯示 dropdown
-   **平滑動畫**：opacity 和 visibility 過渡效果
-   **箭頭動畫**：hover 時箭頭旋轉 180 度

#### 3.2 移動端 (≤768px)

-   **點擊觸發**：觸摸點擊切換 dropdown
-   **自動收合**：選擇圖表後自動關閉菜單
-   **垂直佈局**：適配移動端垂直菜單結構

### 4. 功能保持

✅ **完全保留原有功能：**

-   所有圖表模態框正常運作
-   圖表刷新和載入狀態管理
-   最後更新時間顯示
-   錯誤處理和重試機制
-   Floor Plan 和 Stereogram 菜單項

## 使用方式

### 桌面端

1. 將滑鼠懸停在「數據可視化」菜單項上
2. dropdown 自動展開顯示 4 個圖表選項
3. 點擊任一圖表選項開啟對應的模態框

### 移動端

1. 點擊「數據可視化」菜單項
2. dropdown 展開顯示 4 個圖表選項
3. 點擊任一圖表選項開啟模態框並自動收合菜單

## 測試驗證

### 自動化測試

```bash
# 執行前端圖表 dropdown 驗證
make test-frontend-charts-dropdown

# 執行完整前端驗證
make test-frontend-validation
```

### 測試覆蓋範圍

-   ✅ 組件結構完整性
-   ✅ 圖表整合正確性
-   ✅ Dropdown 功能實現
-   ✅ 移動端響應性
-   ✅ SCSS 樣式完整性
-   ✅ 無障礙功能支援
-   ✅ 原有功能保持

## 技術特點

### 1. 響應式設計

-   桌面端 hover 交互
-   移動端 touch 友好
-   流暢的動畫過渡

### 2. 無障礙設計

-   鍵盤導航支援
-   適當的 hover 狀態
-   清晰的視覺反饋

### 3. 性能優化

-   條件渲染減少 DOM 操作
-   CSS 過渡動畫硬體加速
-   事件處理優化

## 文件結構

```
simworld/frontend/src/
├── components/layout/
│   └── Navbar.tsx          # 主要修改文件
├── styles/
│   └── Navbar.scss         # 樣式修改文件
└── components/viewers/     # 圖表組件（無修改）
    ├── SINRViewer.tsx
    ├── CFRViewer.tsx
    ├── DelayDopplerViewer.tsx
    └── TimeFrequencyViewer.tsx
```

## 後續擴展建議

### 1. 圖表管理增強

-   圖表收藏功能
-   自定義圖表順序
-   圖表分組管理

### 2. 用戶體驗優化

-   圖表預覽縮圖
-   快速切換功能
-   鍵盤快捷鍵支援

### 3. 數據可視化擴展

-   新增更多圖表類型
-   圖表組合視圖
-   實時數據更新指示器

## 總結

本次實現成功將 4 個獨立的圖表菜單項整合為一個統一的「數據可視化」dropdown，在保持所有原有功能的同時，顯著提升了用戶界面的整潔度和用戶體驗。實現包含完整的響應式設計、無障礙支援和自動化測試驗證。
