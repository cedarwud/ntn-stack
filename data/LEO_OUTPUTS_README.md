# LEO Outputs 目錄文件說明

本目錄包含六階段衛星數據處理管道的輸出文件，已優化為扁平化結構。

## 📊 六階段輸出文件對應表

| 階段 | 文件名 | 大小 | 說明 |
|------|--------|------|------|
| Stage 1 | `tle_orbital_calculation_output.json` | 1.4GB | TLE載入與SGP4軌道計算 |
| Stage 2 | `intelligent_filtered_output.json` | 105K | 智能衛星篩選 |  
| Stage 3 | `signal_event_analysis_output.json` | 119K | 信號分析與3GPP事件 |
| Stage 4 | `oneweb_enhanced_stage4.json` | 47K | 時間序列預處理 |
| Stage 5 | `data_integration_output.json` | 53K | 數據整合 |
| Stage 6 | `enhanced_dynamic_pools_stage6.json` | 935B | 動態池規劃 |

## 🔄 數據流向

```
tle_orbital_calculation_output.json (1.4GB)
    ↓ Stage 1 → 2
intelligent_filtered_output.json (105K)
    ↓ Stage 2 → 3  
signal_event_analysis_output.json (119K)
    ↓ Stage 3 → 4
oneweb_enhanced_stage4.json (47K)
    ↓ Stage 4 → 5
data_integration_output.json (53K)
    ↓ Stage 5 → 6
enhanced_dynamic_pools_stage6.json (935B)
```

## 📁 目錄結構
```
leo_outputs/
├── tle_orbital_calculation_output.json    # Stage 1: TLE載入與SGP4軌道計算
├── intelligent_filtered_output.json       # Stage 2: 智能衛星篩選
├── signal_event_analysis_output.json      # Stage 3: 信號分析與3GPP事件
├── oneweb_enhanced_stage4.json           # Stage 4: 時間序列預處理
├── data_integration_output.json          # Stage 5: 數據整合
├── enhanced_dynamic_pools_stage6.json    # Stage 6: 動態池規劃
└── validation_snapshots/                 # 調試快照
```

## ❓ validation_snapshots 目錄分析

### 📋 目錄內容
```
validation_snapshots/
├── stage1_validation.json    # 1.5KB
├── stage2_validation.json    # 1.5KB  
├── stage3_validation.json    # 1.4KB
├── stage4_validation.json    # 1.4KB
├── stage5_validation.json    # 1.3KB
└── stage6_validation.json    # 1.4KB
總計: ~8KB
```

### 🎯 用途分析
1. **API 端點支持**
   - `/pipeline/validation/stage/{stage_number}` - 獲取特定階段驗證
   - `/pipeline/validation/summary` - 獲取整個管道驗證總覽
   - `/pipeline/health` - 快速健康檢查
   - `/pipeline/statistics` - 管道統計信息

2. **調試和監控**
   - 記錄每個階段的執行狀態
   - 包含關鍵指標和性能數據
   - 驗證檢查結果和失敗原因

3. **開發支持**
   - ValidationSnapshotBase 基礎類使用
   - 各階段處理器自動生成驗證快照

### 💡 保留建議
✅ **建議保留**，原因：
- **檔案極小** (總共僅 8KB)  
- **功能重要** (API 和監控依賴)
- **調試價值** (問題排查必需)
- **自動生成** (系統運行時自動維護)

如果確定不需要調試和API功能，可考慮刪除。
但建議保留，因為佔用空間微乎其微，且對系統監控很有價值。

---

*最後更新: 2025-09-06 04:34:04*
*目錄結構優化完成，文檔自動生成*
