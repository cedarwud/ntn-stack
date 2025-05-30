# 前端數據可視化組件開發 - Dashboard

## 📋 項目概述

本文檔記錄了 SimWorld 前端數據可視化組件的開發過程，實現了一個現代化的儀表板系統，用於展示 5G 網絡、衛星和 UAV 的狀態和性能數據。

## 🎯 開發目標

-   ✅ 創建統一的數據可視化儀表板
-   ✅ 實現實時數據更新和監控
-   ✅ 提供交互式網絡拓撲圖
-   ✅ 支援多種佈局和全螢幕模式
-   ✅ 整合 WebSocket 實時通信
-   ✅ 響應式設計支援多設備

## 🏗️ 架構設計

### 組件結構

```
src/components/dashboard/
├── Dashboard.tsx              # 主儀表板組件
├── Dashboard.scss            # 儀表板樣式
├── panels/                   # 面板組件
│   ├── SystemOverview.tsx    # 系統總覽
│   ├── RealTimeMetrics.tsx   # 實時指標
│   ├── PerformanceMetricsPanel.tsx # 性能指標
│   ├── AlertsPanel.tsx       # 告警面板
│   ├── ControlPanel.tsx      # 控制面板
│   └── PanelCommon.scss      # 公共樣式
├── charts/                   # 圖表組件
│   └── NetworkTopologyChart.tsx # 網絡拓撲圖
└── views/                    # 視圖組件
    ├── SatelliteOrbitView.tsx # 衛星軌道視圖
    └── UAVFlightTracker.tsx   # UAV 飛行追蹤

src/hooks/                    # 自定義 Hooks
├── useWebSocket.ts           # WebSocket 連接
└── useApiData.ts             # API 數據獲取

src/pages/
└── DashboardPage.tsx         # 儀表板頁面
```

### 數據流架構

```
API/WebSocket → Hooks → Dashboard → Panels/Charts → UI Components
```

## 🚀 主要功能

### 1. 儀表板佈局管理

-   **多佈局支援**: 系統總覽、網絡監控、UAV 追蹤
-   **動態格線**: 自適應組件排列
-   **全螢幕模式**: 單組件全螢幕展示
-   **響應式設計**: 支援桌面、平板、移動端

### 2. 實時數據可視化

-   **WebSocket 整合**: 實時數據更新
-   **狀態指示器**: 連接狀態和數據新鮮度
-   **趨勢分析**: 數據變化趨勢顯示
-   **自動刷新**: 可配置的自動刷新機制

### 3. 網絡拓撲圖

-   **交互式節點**: 點擊選擇和詳情顯示
-   **連線品質**: 視覺化連線品質指標
-   **節點分類**: 不同類型節點的顏色編碼
-   **圖例說明**: 清晰的圖例和說明

### 4. 系統監控面板

-   **服務狀態**: 各服務運行狀態監控
-   **性能指標**: 吞吐量、延遲、成功率
-   **告警系統**: 分級告警和通知
-   **控制操作**: 系統控制和操作面板

## 🎨 用戶界面設計

### 設計原則

-   **簡潔明瞭**: 清晰的信息層次和視覺引導
-   **一致性**: 統一的設計語言和交互模式
-   **可訪問性**: 支援鍵盤導航和螢幕閱讀器
-   **響應式**: 適配不同螢幕尺寸和設備

### 色彩系統

-   **主色調**: #4a7bff (藍色)
-   **成功**: #4CAF50 (綠色)
-   **警告**: #FF9800 (橙色)
-   **錯誤**: #F44336 (紅色)
-   **中性**: #607D8B (灰藍色)

### 交互設計

-   **Hover 效果**: 滑鼠懸停反饋
-   **點擊反饋**: 明確的點擊狀態
-   **載入狀態**: 優雅的載入動畫
-   **過渡動畫**: 平滑的狀態轉換

## 🔧 技術實現

### 核心技術棧

-   **React 18**: 組件化開發
-   **TypeScript**: 類型安全
-   **SCSS**: 樣式預處理
-   **WebSocket**: 實時通信
-   **Fetch API**: HTTP 請求

### 自定義 Hooks

```typescript
// WebSocket 連接管理
const { data, connected, error, connect, disconnect, send } = useWebSocket(url)

// API 數據獲取
const { data, loading, error, refetch } = useApiData(url, options)
```

### 狀態管理

-   **本地狀態**: useState 管理組件狀態
-   **副作用**: useEffect 處理生命週期
-   **記憶化**: useCallback/useMemo 優化性能
-   **引用**: useRef 管理 DOM 引用

## 📊 數據可視化特性

### 1. 網絡拓撲可視化

```typescript
interface SimpleNode {
    id: string
    name: string
    type: 'gateway' | 'mesh_node' | 'uav' | 'satellite'
    status: 'active' | 'inactive'
    x: number
    y: number
}
```

### 2. 實時指標展示

-   **連接品質**: 信號強度、延遲、吞吐量
-   **系統狀態**: CPU、記憶體、網絡使用率
-   **業務指標**: 用戶數、會話數、成功率

### 3. 告警和通知

```typescript
interface Alert {
    id: string
    level: 'info' | 'warning' | 'error'
    message: string
    timestamp: Date
}
```

## 🔗 整合點

### 1. Navbar 整合

-   新增「儀表板」菜單項
-   支援場景切換
-   保持導航一致性

### 2. 路由支援

```typescript
// 路由配置
;/{scene}/aabddhors
```

### 3. API 端點

-   `/api/v1/dashboard/overview` - 系統總覽
-   `/api/v1/dashboard/metrics` - 性能指標
-   `/api/v1/dashboard/topology` - 網絡拓撲
-   `/api/v1/dashboard/alerts` - 告警信息

### 4. WebSocket 端點

-   `ws://localhost:8888/ws/dashboard` - 實時數據推送

## 🧪 測試驗證

### 測試覆蓋範圍

-   ✅ 組件結構完整性 (14 個文件)
-   ✅ 儀表板功能特性 (11 項功能)
-   ✅ 數據可視化組件 (4 種類型)
-   ✅ 整合點配置 (6 個整合點)
-   ✅ 用戶體驗設計 (4 個類別)
-   ✅ 性能考量 (3 個方面)
-   ✅ 可擴展性 (3 個層面)

### 測試指令

```bash
# 儀表板測試
make test-frontend-dashboard

# 綜合前端測試
make test-frontend-comprehensive

# 建置測試
make test-frontend-build
```

## 🚀 使用方式

### 1. 啟動儀表板

1. 確保 SimWorld 服務運行
2. 訪問 `http://localhost:3000/{scene}/dashboard`
3. 或點擊 Navbar 中的「儀表板」

### 2. 佈局切換

-   使用頂部佈局選擇器切換不同視圖
-   支援「系統總覽」、「網絡監控」、「UAV 追蹤」

### 3. 全螢幕模式

-   點擊面板右上角的全螢幕按鈕
-   按 ESC 或點擊退出按鈕退出全螢幕

### 4. 實時數據

-   自動連接 WebSocket 獲取實時數據
-   可手動刷新或調整刷新頻率

## 🔮 後續擴展計劃

### 短期目標 (1-2 週)

-   [ ] 整合 D3.js 或 ECharts 進階圖表
-   [ ] 實現數據導出功能 (CSV, JSON, PDF)
-   [ ] 添加更多可視化圖表類型
-   [ ] 實現數據過濾和搜索功能

### 中期目標 (1-2 月)

-   [ ] 自定義儀表板佈局編輯器
-   [ ] 主題和個性化設置
-   [ ] 歷史數據查詢和回放
-   [ ] 高級告警規則配置

### 長期目標 (3-6 月)

-   [ ] 機器學習驅動的異常檢測
-   [ ] 預測性分析和趨勢預測
-   [ ] 多租戶支援和權限管理
-   [ ] 移動端原生應用

## 📈 性能優化

### 已實現優化

-   **組件記憶化**: 避免不必要的重渲染
-   **事件處理優化**: useCallback 優化事件處理器
-   **狀態更新優化**: 批量狀態更新
-   **WebSocket 重連**: 自動重連機制

### 待實現優化

-   **虛擬滾動**: 大量數據列表優化
-   **懶加載**: 按需載入組件
-   **數據分頁**: 大數據集分頁處理
-   **緩存策略**: API 響應緩存

## 🛠️ 開發指南

### 添加新面板

1. 在 `panels/` 目錄創建新組件
2. 實現標準面板接口
3. 在 `Dashboard.tsx` 中註冊
4. 添加對應的佈局配置

### 添加新圖表

1. 在 `charts/` 目錄創建圖表組件
2. 實現數據處理和可視化邏輯
3. 添加交互功能和響應式支援
4. 編寫對應的測試用例

### 樣式開發

-   使用 `PanelCommon.scss` 中的公共樣式
-   遵循 BEM 命名規範
-   確保響應式設計
-   保持設計系統一致性

## 📚 相關文檔

-   [前端圖表 Dropdown 開發](./FRONTEND_CHARTS_DROPDOWN.md)
-   [SimWorld 前端架構](./simworld/frontend/README.md)
-   [API 文檔](./API_DOCUMENTATION.md)
-   [測試指南](./TESTING_GUIDE.md)

## 🤝 貢獻指南

1. **Fork** 項目並創建功能分支
2. **開發** 新功能並編寫測試
3. **測試** 確保所有測試通過
4. **文檔** 更新相關文檔
5. **提交** Pull Request

## 📄 授權

本項目採用 MIT 授權條款。詳見 [LICENSE](./LICENSE) 文件。

---

**開發團隊**: NTN Stack Development Team  
**最後更新**: 2024 年 12 月  
**版本**: 1.0.0
