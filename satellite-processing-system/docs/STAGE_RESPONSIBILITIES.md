# 六階段處理系統責任分工規範

## 🚨 核心原則

**每個階段只負責自己的核心功能，嚴禁功能重疊和過度開發**

避免過去 Stage 2 出現的問題：14 個檔案、7,987 行代碼包含了其他階段的功能，導致無限循環和維護困難。

## 📋 階段責任分工表

### Stage 1: 軌道計算 (Orbital Calculation)
**核心責任**: TLE 數據處理和衛星軌道位置計算

**包含功能**:
- ✅ TLE 數據載入和解析
- ✅ SGP4/SDP4 軌道動力學計算
- ✅ ECI 座標系統位置計算
- ✅ 時間序列軌道預測
- ✅ 軌道精度驗證

**輸出數據**:
```json
{
  "data": {
    "starlink_satellites": [
      {
        "name": "STARLINK-1234",
        "norad_id": 12345,
        "position_timeseries": [
          {
            "timestamp": "2025-09-18T04:00:00Z",
            "position_eci": {"x": 1234.5, "y": -5678.9, "z": 3456.7}
          }
        ]
      }
    ],
    "oneweb_satellites": [...]
  }
}
```

**檔案數**: 4 個
**代碼行數**: ~2,676 行

---

### Stage 2: 地理可見性過濾 (Geographic Visibility Filtering)
**核心責任**: 基本地理可見性過濾，只處理座標轉換和仰角門檻

**包含功能**:
- ✅ ECI → 地平座標轉換
- ✅ 仰角計算 (elevation angle)
- ✅ 基本仰角門檻過濾 (Starlink: 5°, OneWeb: 10°)
- ✅ 地理位置可見性判定

**🚫 禁止功能** (已移至其他階段):
- ❌ 信號強度計算 (RSRP, RSRQ) → Stage 3
- ❌ 換手決策邏輯 → Stage 3
- ❌ 覆蓋規劃算法 → Stage 6
- ❌ 學術驗證系統 → 系統級功能

**簡化實現**:
- 使用 `SimpleStage2Processor` 和 `SimpleGeographicFilter`
- 檔案數: 2 個主要檔案
- 執行時間: ~13秒 (vs 原版無限循環)
- 跳過複雜功能，專注核心責任

**輸出數據**:
```json
{
  "data": {
    "filtered_satellites": {
      "starlink": [
        {
          "name": "STARLINK-1234",
          "position_timeseries": [
            {
              "timestamp": "2025-09-18T04:00:00Z",
              "position_eci": {"x": 1234.5, "y": -5678.9, "z": 3456.7},
              "elevation_deg": 15.4
            }
          ],
          "visibility_summary": {
            "total_positions": 100,
            "visible_positions": 25,
            "visibility_ratio": 0.25,
            "max_elevation_deg": 45.7
          }
        }
      ],
      "oneweb": [...]
    }
  }
}
```

---

### Stage 3: 信號分析 (Signal Analysis)
**核心責任**: 信號品質計算、3GPP 事件分析、換手決策

**包含功能**:
- ✅ RSRP (Reference Signal Received Power) 計算
- ✅ RSRQ (Reference Signal Received Quality) 計算
- ✅ SINR (Signal to Interference plus Noise Ratio) 計算
- ✅ 3GPP NTN 事件分析 (A4, A5, D2 事件)
- ✅ 換手候選管理
- ✅ 換手決策引擎
- ✅ 動態門檻控制
- ✅ Friis 傳播損耗模型
- ✅ ITU-R P.618 大氣衰減

**檔案數**: 21 個
**核心處理器**: `Stage3SignalAnalysisProcessor`

**輸入**: Stage 2 地理可見性過濾結果
**輸出**: 信號品質和換手決策數據

---

### Stage 4: 時序預處理 (Timeseries Preprocessing)
**核心責任**: 時間序列數據預處理和強化學習準備

**包含功能**:
- ✅ 時序數據格式轉換
- ✅ 強化學習預處理
- ✅ 動畫建構器
- ✅ 即時監控系統
- ✅ 數據載入器

**檔案數**: 11 個
**核心處理器**: `TimesSeriesPreprocessingProcessor`

---

### Stage 5: 數據整合 (Data Integration)
**核心責任**: 跨階段數據整合和存儲管理

**包含功能**:
- ✅ 多階段數據融合
- ✅ PostgreSQL 整合
- ✅ 智能數據融合引擎
- ✅ 換手場景引擎
- ✅ 存儲平衡分析
- ✅ 跨階段驗證器

**檔案數**: 13 個
**核心處理器**: `Stage5Processor`

---

### Stage 6: 動態池規劃 (Dynamic Pool Planning)
**核心責任**: 衛星池動態規劃和覆蓋優化

**包含功能**:
- ✅ 動態覆蓋優化
- ✅ 衛星選擇引擎
- ✅ 軌跡預測引擎
- ✅ 動態池優化引擎
- ✅ 科學覆蓋設計器
- ✅ 演算法基準測試

**檔案數**: 20 個
**核心處理器**: `Stage6Processor`

---

## 🛡️ 防止功能重疊的規範

### 開發前檢查清單
**任何新功能開發前必須確認**:

1. **🔍 功能歸屬檢查**:
   - [ ] 這個功能屬於哪個階段的核心責任？
   - [ ] 是否與其他階段的功能重疊？
   - [ ] 是否已經存在類似實現？

2. **📋 階段邊界檢查**:
   - [ ] 輸入數據來源明確？
   - [ ] 輸出數據格式標準？
   - [ ] 與上下游階段接口清晰？

3. **🚫 禁止行為檢查**:
   - [ ] 沒有跨階段實現功能？
   - [ ] 沒有重複其他階段的邏輯？
   - [ ] 沒有引入不必要的複雜性？

### 階段間數據流
```
Stage 1 (TLE + Orbital)
    ↓ (ECI coordinates)
Stage 2 (Geographic Filter)
    ↓ (Visible satellites)
Stage 3 (Signal Analysis)
    ↓ (Signal quality + Handover)
Stage 4 (Timeseries Prep)
    ↓ (Preprocessed data)
Stage 5 (Data Integration)
    ↓ (Integrated dataset)
Stage 6 (Dynamic Planning)
    ↓ (Optimized satellite pools)
```

### 常見違規模式
**🚫 嚴禁以下行為**:

1. **功能越界**:
   - Stage 2 實現信號計算 → 應在 Stage 3
   - Stage 3 實現覆蓋規劃 → 應在 Stage 6
   - Stage 1 實現換手邏輯 → 應在 Stage 3

2. **重複實現**:
   - 多個階段都有座標轉換邏輯
   - 多個階段都有仰角計算
   - 多個階段都有相同的驗證邏輯

3. **過度複雜化**:
   - 簡單功能包裝成複雜框架
   - 不必要的配置系統
   - 過度的抽象層次

## 📊 階段複雜度監控

### 複雜度警報門檻
- **檔案數**: 超過 15 個檔案 → 🚨 檢查功能越界
- **代碼行數**: 超過 5,000 行 → 🚨 檢查重複實現
- **執行時間**: 超過 30 秒 → 🚨 檢查演算法效率
- **記憶體使用**: 超過 2GB → 🚨 檢查數據處理邏輯

### Stage 2 重構案例
**問題**: 14 檔案、7,987 行 → 無限循環
**解決**: 2 檔案、簡化實現 → 13秒完成
**教訓**: 專注核心責任，避免功能溢出

## 🔧 實施指南

### 新功能開發流程
1. **需求分析** → 確定功能歸屬階段
2. **介面設計** → 定義輸入輸出格式
3. **實現開發** → 只在指定階段實現
4. **整合測試** → 驗證階段間數據流
5. **文檔更新** → 更新本責任分工文檔

### 重構指導原則
- **簡化優於複雜** → 偏向簡單實現
- **專責優於多功能** → 每階段只做一件事
- **標準優於客製** → 使用統一介面格式
- **測試優於假設** → 實際測試階段邊界

---

**更新日期**: 2025-09-18
**版本**: v1.0
**責任人**: 六階段處理系統維護團隊