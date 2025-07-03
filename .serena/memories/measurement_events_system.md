# 測量事件系統架構

## 當前實現狀態

### Event A4 ✅ 已完成
- **文件位置**: `simworld/frontend/src/components/domains/measurement/`
- **核心組件**: `PureA4Chart.tsx` (高度優化的原生 Chart.js 實現)
- **功能**: 完整實現 3GPP TS 38.331 規範的 Event A4
- **優化**: 解決了重新渲染和主題切換問題

### Event D1 🔄 進行中
- **規範**: 3GPP TS 38.331 Section 5.5.4.15
- **條件**: 距離雙門檻事件
- **進入**: `Ml1 – Hys > Thresh1` AND `Ml2 + Hys < Thresh2`
- **離開**: `Ml1 + Hys < Thresh1` OR `Ml2 – Hys > Thresh2`

### Event D2 📅 待實現
- **規範**: 3GPP TS 38.331 Section 5.5.4.15a
- **條件**: 移動參考位置事件（考慮衛星軌道）

### Event T1 📅 待實現
- **規範**: 3GPP TS 38.331 Section 5.5.4.16
- **條件**: 時間窗口條件事件

## 技術架構

### 組件結構
```
measurement/
├── charts/
│   ├── PureA4Chart.tsx        # A4 圖表核心
│   ├── EventA4Chart.tsx       # A4 包裝器
│   ├── EventA4Viewer.tsx      # A4 查看器
│   └── PureD1Chart.tsx        # D1 圖表 (待創建)
├── viewers/
│   └── MeasurementEventsViewer.tsx
├── modals/
│   └── MeasurementEventsModal.tsx
└── types/
    └── index.ts               # 完整類型定義
```

### 重用策略
- 基於 PureA4Chart 成功經驗創建 PureD1Chart
- 使用相同的性能優化模式 (React.memo, useMemo, useCallback)
- 重用事件參數控制邏輯
- 統一的主題和樣式系統