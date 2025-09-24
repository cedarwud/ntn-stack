# 六階段處理系統責任分工規範 v2.0

## 🚨 核心原則

**每個階段只負責自己的核心功能，嚴禁功能重疊和過度開發**

v2.0架構基於單一責任原則，確保每個階段職責明確，避免功能重疊和維護困難。

## 📋 v2.0階段責任分工表

### Stage 1: 數據載入層 (Data Loading Layer)
**核心責任**: TLE 數據載入、驗證和時間基準建立

**包含功能**:
- ✅ TLE 數據載入和解析
- ✅ 數據完整性驗證
- ✅ 時間基準建立 (使用TLE epoch時間)
- ✅ 衛星數據分組和標準化

**模組化架構** (v2.0):
1. **TLE Data Loader** - 原始TLE文件載入
2. **Data Validator** - 數據完整性和格式驗證
3. **Time Reference Establisher** - 統一時間基準建立
4. **Stage1 Data Loading Processor** - 整合處理流程

**性能指標**:
- 處理時間: <30秒 (8,837顆衛星)
- 記憶體使用: <200MB
- 輸出大小: 約4-5MB

---

### Stage 2: 軌道計算與鏈路可行性評估層 (Orbital Computing & Link Feasibility Layer)
**核心責任**: SGP4軌道計算和衛星鏈路可行性評估

**包含功能**:
- ✅ SGP4/SDP4軌道傳播計算
- ✅ TEME→ITRF→WGS84座標系統轉換（使用Skyfield專業庫）
- ✅ 計算仰角、方位角、距離
- ✅ 多重約束篩選：
  - 基礎可見性檢查（仰角 > 0°）
  - 星座特定服務門檻（Starlink: 5°, OneWeb: 10°）
  - 鏈路預算約束（200-2000km距離範圍）
  - 系統邊界驗證（地理邊界）

**模組化架構** (v2.0):
1. **SGP4 Calculator** - SGP4/SDP4軌道計算
2. **Coordinate Converter** - 座標系統轉換（Skyfield庫）
3. **Link Feasibility Filter** - 鏈路可行性篩選
4. **Stage2 Orbital Computing Processor** - 軌道計算協調

**性能指標**:
- 處理時間: 2-3分鐘 (完整SGP4計算)
- 記憶體使用: <1GB
- 輸出數據: 約500-1000顆可建立通訊鏈路的衛星

---

### Stage 3: 信號分析層 (Signal Analysis Layer)
**核心責任**: 信號品質計算和3GPP事件檢測

**包含功能**:
- ✅ RSRP/RSRQ/SINR信號品質計算
- ✅ 3GPP NTN標準事件檢測（A4/A5/D2事件）
- ✅ 物理層參數計算（路徑損耗、都卜勒偏移）
- ✅ 信號品質評估和分類

**模組化架構** (v2.0):
1. **Signal Quality Calculator** - 信號品質計算
2. **3GPP Event Detector** - 3GPP事件檢測
3. **Physics Calculator** - 物理參數計算
4. **Stage3 Signal Analysis Processor** - 信號分析協調

**性能指標**:
- 處理時間: 6-7秒
- 記憶體使用: <500MB
- 分析精度: RSRP精度±2dBm

---

### Stage 4: 優化決策層 (Optimization Decision Layer)
**核心責任**: 衛星選擇優化和換手決策

**包含功能**:
- ✅ 動態池規劃和衛星選擇優化
- ✅ 換手決策算法和策略制定
- ✅ 多目標優化（信號品質vs覆蓋範圍vs切換成本）
- ✅ 強化學習擴展點預留

**模組化架構** (v2.0):
1. **Pool Planner** - 動態池規劃
2. **Handover Optimizer** - 換手決策優化
3. **Multi-Objective Optimizer** - 多目標優化
4. **Stage4 Optimization Processor** - 決策流程協調

**性能指標**:
- 處理時間: 8-10秒
- 輸入處理: 約500-1000顆衛星
- 優化效果: 覆蓋改善>15%，換手減少>20%

---

### Stage 5: 數據整合層 (Data Integration Layer)
**核心責任**: 多格式數據轉換和前端準備

**包含功能**:
- ✅ 時間序列數據轉換和插值處理
- ✅ 動畫軌跡數據建構和關鍵幀生成
- ✅ 分層數據結構和索引建立
- ✅ 多格式輸出（JSON、GeoJSON、CSV等）

**模組化架構** (v2.0):
1. **Timeseries Converter** - 時間序列轉換
2. **Animation Builder** - 動畫數據建構
3. **Layer Data Generator** - 分層數據生成
4. **Format Converter Hub** - 格式轉換中心
5. **Stage5 Data Integration Processor** - 數據處理協調

**性能指標**:
- 處理時間: 50-60秒
- 輸入處理: 約150-250顆優化後衛星
- 壓縮比: >70%

---

### Stage 6: 持久化與API層 (Persistence & API Layer)
**核心責任**: 數據持久化、快取管理和API服務

**包含功能**:
- ✅ 統一數據存儲和備份管理
- ✅ 多層快取策略和性能優化
- ✅ RESTful API和GraphQL服務
- ✅ 實時WebSocket事件推送

**模組化架構** (v2.0):
1. **Storage Manager** - 統一存儲管理（替代8個backup_*模組）
2. **Cache Manager** - 多層快取管理
3. **API Service** - RESTful和GraphQL服務
4. **WebSocket Service** - 實時數據推送
5. **Stage6 Persistence Processor** - 服務協調

**性能指標**:
- API響應時間: <100ms（快取）、<500ms（存儲）
- WebSocket延遲: <50ms
- 併發連接: 支援1000+同時連接
- 檔案減少: 從44個檔案精簡到約10個（75%減少）

---

## 🔄 v2.0架構數據流

```
Stage 1 (Data Loading)
    ↓ (Validated TLE + Time Base)
Stage 2 (Orbital Computing)
    ↓ (Orbital Data + Visibility)
Stage 3 (Signal Analysis)
    ↓ (Signal Quality + 3GPP Events)
Stage 4 (Optimization Decision)
    ↓ (Optimized Pool + Handover Strategy)
Stage 5 (Data Integration)
    ↓ (Multi-format Data + Animation)
Stage 6 (Persistence & API)
    ↓ (API Services + Real-time Updates)
```

## 🛡️ v2.0架構設計原則

### 核心原則
- **單一責任**: 每個階段專注一個核心功能
- **模組化設計**: 每階段採用4-5模組架構
- **學術標準**: 符合Grade A學術要求
- **性能優化**: 明確的性能指標和優化策略

### 防止功能重疊規範
**開發前檢查清單**:
1. **🔍 功能歸屬檢查**: 功能屬於哪個階段的核心責任？
2. **📋 階段邊界檢查**: 輸入輸出接口是否清晰？
3. **🚫 禁止行為檢查**: 是否跨階段實現功能？

### 階段複雜度監控
- **檔案數**: <15個檔案（Stage 6例外：大幅簡化到10個）
- **處理時間**: 各階段都有明確時間要求
- **記憶體使用**: 合理的記憶體使用限制

## 🎯 v2.0重構成果

### 重大簡化
- **Stage 6**: 從44個檔案精簡到10個檔案（75%減少）
- **功能集中**: 動態池功能移至Stage 4，API功能集中管理
- **架構清晰**: 每階段職責明確，無功能重疊

### 性能提升
- **Stage 1**: <30秒（數據載入）
- **Stage 2**: 2-3分鐘（完整軌道計算）
- **Stage 3**: 6-7秒（信號分析）
- **Stage 4**: 8-10秒（優化決策）
- **Stage 5**: 50-60秒（數據整合）
- **Stage 6**: <100ms API響應

---

**版本**: v2.0
**更新日期**: 2025-09-21
**架構基礎**: refactoring_plan_v2
**文檔狀態**: 與 stages/ 目錄完全一致