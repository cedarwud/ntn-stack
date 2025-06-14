# LEO Satellite Handover 實現與優化開發指南

## 🎯 項目目標

實現和優化 LEO (Low Earth Orbit) 衛星間的 handover 功能，構建完整的 5G NTN (Non-Terrestrial Networks) 仿真平台，支援 OneWeb 星座的動態衛星切換和服務連續性。

## 🔍 LEO Satellite Handover 技術背景

### 什麼是 LEO Satellite Handover？
LEO 衛星 handover 是指當用戶設備 (UE) 或衛星移動導致信號質量下降時，將通信服務從當前服務衛星切換到另一個更適合的衛星的過程。

### 為什麼需要 Handover？
1. **衛星快速移動** - OneWeb 衛星軌道高度 ~1200km，軌道週期 ~100分鐘
2. **有限服務時間** - 單顆衛星對固定地點的服務時間通常只有 5-15 分鐘
3. **信號衰減** - 衛星接近地平線時信號質量下降
4. **服務連續性** - 確保 UE 始終有可用的衛星連接

### OneWeb 星座特性
- **衛星數量**: 651 顆衛星
- **軌道傾角**: 87.9° (極地軌道)
- **軌道高度**: ~1200 km
- **覆蓋特性**: 全球覆蓋，台灣地區通常有 2-6 顆可見衛星

## 📊 當前系統狀態分析

### ✅ 已實現功能 (95%)
1. **軌道計算引擎** - Skyfield 完整集成
2. **OneWeb 數據管理** - 651 顆衛星的 TLE 數據
3. **實時位置計算** - SGP4 軌道預測
4. **資料庫架構** - PostgreSQL + 衛星數據模型
5. **基礎 API 服務** - REST API 框架

### ⚠️ Handover 關鍵缺失功能 (5%)
1. **實時軌道計算 API** - handover 決策的數據源
2. **多衛星可見性分析** - 尋找 handover 候選衛星
3. **信號質量評估** - handover 觸發條件
4. **Handover 決策算法** - 核心業務邏輯
5. **切換執行機制** - 與 NetStack 的集成

## 🚀 開發流程與優先級

### Phase 1: 軌道計算 API 完善 (高優先級)
**目標**: 為 handover 決策提供實時衛星位置數據
**預期效果**: 能夠實時查詢任意衛星的位置、速度、可見性

### Phase 2: Handover 決策引擎 (最高優先級)  
**目標**: 實現 handover 觸發和目標選擇算法
**預期效果**: 自動識別 handover 時機並選擇最佳目標衛星

### Phase 3: NetStack 集成 (高優先級)
**目標**: 與 5G 核心網實現 handover 信令交互
**預期效果**: 完整的端到端 handover 流程

### Phase 4: 性能優化 (中等優先級)
**目標**: 優化 handover 延遲和成功率
**預期效果**: 達到 5G NTN 標準要求的性能指標

## 📋 詳細開發計劃

### Phase 1: 軌道計算 API 完善

#### 1.1 實時位置查詢 API
```python
GET /api/v1/satellites/{id}/position
→ 返回: 緯度、經度、高度、速度、方位角、仰角
```

#### 1.2 多衛星批量位置查詢
```python
POST /api/v1/satellites/batch-positions  
→ 輸入: 衛星 ID 列表、觀測者位置
→ 返回: 所有衛星的實時位置數據
```

#### 1.3 可見衛星發現 API
```python
GET /api/v1/satellites/visible
→ 輸入: 觀測者位置、最小仰角
→ 返回: 當前可見的所有衛星列表
```

#### 1.4 軌道預測 API
```python
GET /api/v1/satellites/{id}/orbit/predict
→ 輸入: 時間範圍
→ 返回: 未來軌道位置序列
```

### Phase 2: Handover 決策引擎

#### 2.1 信號質量評估模型
```python
class SignalQualityEvaluator:
    - 計算路徑損耗 (基於距離和仰角)
    - 評估多普勒頻移
    - 分析信號衰減趨勢
    - 預測服務中斷時間
```

#### 2.2 Handover 觸發條件
```python
class HandoverTrigger:
    - 信號強度閾值檢查
    - 仰角下降趨勢分析  
    - 服務剩餘時間預測
    - 備選衛星可用性確認
```

#### 2.3 目標衛星選擇算法
```python
class SatelliteSelector:
    - 候選衛星發現 (可見性 + 信號質量)
    - 多準則決策 (信號強度、服務時間、負載)
    - 最佳切換時機計算
    - Handover 執行計劃生成
```

### Phase 3: NetStack 集成

#### 3.1 Handover 信令接口
```python
# 與 NetStack AMF 的接口
POST /netstack/api/v1/handover/initiate
POST /netstack/api/v1/handover/execute  
GET /netstack/api/v1/handover/status
```

#### 3.2 UE 位置追蹤集成
```python
# 接收 NetStack 的 UE 位置更新
POST /api/v1/ue/location-update
→ 觸發 handover 評估
```

#### 3.3 切換執行協調
```python
class HandoverCoordinator:
    - SimWorld handover 決策
    - NetStack 切換執行
    - 狀態同步和確認
    - 失敗回滾處理
```

### Phase 4: 性能優化

#### 4.1 算法優化
- 預測性 handover (提前準備)
- 多衛星併發評估
- 緩存和預計算策略

#### 4.2 系統監控
- Handover 成功率統計
- 切換延遲監控
- 服務中斷時間分析

## 📈 預期成果

### 技術指標
- **Handover 延遲**: < 500ms (目標 < 200ms)
- **成功率**: > 95% (目標 > 99%)
- **服務中斷時間**: < 100ms
- **併發處理能力**: > 1000 UE

### 功能特性
1. **智能 Handover** - 基於多準則的最佳衛星選擇
2. **預測性切換** - 提前識別切換需求
3. **無縫服務** - 最小化服務中斷
4. **自適應優化** - 根據實際性能調整參數

### 應用價值
1. **5G NTN 標準驗證** - 驗證 3GPP 標準實施
2. **產品開發支援** - 支援衛星通信產品設計
3. **學術研究平台** - 提供 handover 算法研究環境
4. **性能基準測試** - 建立 LEO handover 性能基準

## 🛠️ 開發環境準備

### 依賴確認
- ✅ Skyfield 1.49 - 軌道計算
- ✅ SGP4 - TLE 處理  
- ✅ PostgreSQL - 數據存儲
- ✅ FastAPI - API 服務
- ✅ OneWeb TLE 數據 - 651 顆衛星

### 開發工具
- Docker 容器環境
- Python 3.11 異步編程
- 數學計算庫 (NumPy, SciPy)
- 時間處理庫 (datetime, timezone)

## 📝 開發檢查清單

### Phase 1 檢查點 ✅ 已完成
- [x] 實時位置 API 實現 ✅
- [x] 批量查詢 API 實現 ✅
- [x] 可見衛星 API 實現 ✅
- [x] 軌道預測 API 實現 ✅
- [x] Handover 候選衛星 API 實現 ✅
- [x] API 性能測試通過 ✅

### Phase 2 檢查點  
- [ ] 信號質量模型完成
- [ ] Handover 觸發邏輯完成
- [ ] 衛星選擇算法完成
- [ ] 決策引擎測試通過

### Phase 3 檢查點
- [ ] NetStack 接口定義
- [ ] UE 追蹤集成完成
- [ ] 切換協調器實現
- [ ] 端到端測試通過

### Phase 4 檢查點
- [ ] 性能優化完成
- [ ] 監控系統部署
- [ ] 文檔和示例完整
- [ ] 最終驗收測試