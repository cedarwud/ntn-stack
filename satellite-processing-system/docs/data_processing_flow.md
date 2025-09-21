# 🔄 NTN Stack 數據處理流程

**版本**: v2.0 (模組化架構+單一責任+學術標準)
**更新日期**: 2025-09-21
**專案狀態**: ✅ 重構完成 + 模組化設計 + 學術標準合規 + 性能優化
**適用於**: LEO 衛星切換研究 - v2.0六階段處理管道

## 🎯 v2.0 重構核心成果

### 架構創新
- **單一責任**: 每個階段專注核心功能，消除功能重疊
- **模組化設計**: 每階段採用4-5模組架構，便於維護和擴展
- **學術標準**: 嚴格符合Grade A學術要求，禁止模擬數據和簡化算法
- **性能優化**: 明確的性能指標和優化策略

### 重大簡化
- **Stage 6**: 從44個檔案精簡到約10個核心檔案（75%減少）
- **時間基準**: 統一使用TLE epoch時間，解決8000→0衛星問題
- **標準算法**: 強制使用標準SGP4庫，確保計算精度
- **記憶體傳遞**: 優先使用記憶體傳遞，減少I/O開銷

## 📋 概述

本文檔詳細說明 **v2.0模組化架構** 的六階段數據處理流程：系統採用嚴格的單一責任原則，通過模組化設計實現高效、可靠的衛星數據處理管道。

**核心特點**：
- ✅ **本地TLE數據** - 系統使用預下載的本地TLE文件，無依賴外部API
- ✅ **記憶體優先** - 階段間主要使用記憶體傳遞，提升處理效率
- ✅ **完整SGP4算法** - 絕不使用簡化或模擬數據，保證學術研究準確性
- ✅ **模組化架構** - 每階段採用標準化模組設計，便於維護

## 🚀 v2.0六階段架構設計

### 📦 整體架構圖

```
┌─────────────────────────────────────────────────────────────┐
│                   v2.0 六階段處理管道                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Stage 1: 數據載入層 (Data Loading)                         │
│  ├── TLE Data Loader                                       │
│  ├── Data Validator                                        │
│  ├── Time Reference Establisher                            │
│  └── Stage1 Data Loading Processor                         │
│                     ↓                                       │
│  Stage 2: 軌道計算層 (Orbital Computing)                    │
│  ├── SGP4 Calculator                                       │
│  ├── Coordinate Converter                                  │
│  ├── Visibility Filter                                     │
│  └── Stage2 Orbital Computing Processor                    │
│                     ↓                                       │
│  Stage 3: 信號分析層 (Signal Analysis)                      │
│  ├── Signal Quality Calculator                             │
│  ├── 3GPP Event Detector                                   │
│  ├── Physics Calculator                                    │
│  └── Stage3 Signal Analysis Processor                      │
│                     ↓                                       │
│  Stage 4: 優化決策層 (Optimization Decision)                │
│  ├── Pool Planner                                          │
│  ├── Handover Optimizer                                    │
│  ├── Multi-Objective Optimizer                             │
│  └── Stage4 Optimization Processor                         │
│                     ↓                                       │
│  Stage 5: 數據整合層 (Data Integration)                     │
│  ├── Timeseries Converter                                  │
│  ├── Animation Builder                                     │
│  ├── Layer Data Generator                                  │
│  ├── Format Converter Hub                                  │
│  └── Stage5 Data Integration Processor                     │
│                     ↓                                       │
│  Stage 6: 持久化與API層 (Persistence & API)                │
│  ├── Storage Manager                                       │
│  ├── Cache Manager                                         │
│  ├── API Service                                           │
│  ├── WebSocket Service                                     │
│  └── Stage6 Persistence Processor                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 📊 階段處理詳解

### Stage 1: 數據載入層
**核心職責**: TLE數據載入、驗證和時間基準建立
- **輸入**: 8,837顆衛星TLE文件
- **處理時間**: <30秒
- **輸出**: 約4-5MB驗證過的TLE數據
- **關鍵功能**: 統一時間基準建立（使用TLE epoch時間）

### Stage 2: 軌道計算層
**核心職責**: SGP4軌道計算和初步可見性篩選
- **輸入**: 驗證過的TLE數據 + 時間基準
- **處理時間**: 2-3分鐘（完整SGP4計算）
- **輸出**: 約500-1000顆可見衛星軌道數據
- **關鍵功能**: 標準SGP4算法、座標轉換、可見性篩選

### Stage 3: 信號分析層
**核心職責**: 信號品質計算和3GPP事件檢測
- **輸入**: 可見衛星軌道數據
- **處理時間**: 6-7秒
- **輸出**: 信號品質數據 + 3GPP事件數據
- **關鍵功能**: RSRP/RSRQ/SINR計算、A4/A5/D2事件檢測

### Stage 4: 優化決策層
**核心職責**: 衛星選擇優化和換手決策
- **輸入**: 信號品質數據
- **處理時間**: 8-10秒
- **輸出**: 優化決策結果 + 換手策略
- **關鍵功能**: 動態池規劃、多目標優化、換手決策

### Stage 5: 數據整合層
**核心職責**: 多格式數據轉換和前端準備
- **輸入**: 優化決策結果
- **處理時間**: 50-60秒
- **輸出**: 多格式數據包 + 動畫數據
- **關鍵功能**: 時間序列轉換、動畫建構、格式轉換

### Stage 6: 持久化與API層
**核心職責**: 數據持久化、快取管理和API服務
- **輸入**: 多格式數據包
- **響應時間**: <100ms（API）
- **輸出**: API服務 + 實時數據推送
- **關鍵功能**: 存儲管理、多層快取、RESTful API、WebSocket

## ⚡ 性能指標總覽

### 處理時間
- **Stage 1**: <30秒（數據載入）
- **Stage 2**: 2-3分鐘（軌道計算）
- **Stage 3**: 6-7秒（信號分析）
- **Stage 4**: 8-10秒（優化決策）
- **Stage 5**: 50-60秒（數據整合）
- **Stage 6**: <100ms（API響應）

**總處理時間**: 約4-5分鐘（完整六階段管道）

### 記憶體使用
- **Stage 1**: <200MB
- **Stage 2**: <1GB
- **Stage 3**: <500MB
- **Stage 4**: <300MB
- **Stage 5**: <1GB
- **Stage 6**: <500MB

### 數據處理量
- **輸入**: 8,837顆衛星TLE數據
- **可見衛星**: 約500-1000顆
- **最終服務**: 約150-250顆優化後衛星

## 🛡️ 學術標準合規

### Grade A 要求
- ✅ **真實數據**: 使用Space-Track.org TLE數據
- ✅ **標準算法**: 強制使用標準SGP4/SDP4實現
- ✅ **時間精度**: 嚴格的TLE epoch時間基準
- ✅ **物理模型**: ITU-R P.618、3GPP標準合規

### 禁止項目
- ❌ 模擬數據或隨機生成數據
- ❌ 簡化算法或假設值
- ❌ 硬編碼參數或魔數
- ❌ 未經驗證的近似計算

## 🔧 數據流設計

### 記憶體傳遞優先
```python
# v2.0標準數據流
stage1_output = stage1_processor.execute()
stage2_output = stage2_processor.execute(stage1_output)
stage3_output = stage3_processor.execute(stage2_output)
stage4_output = stage4_processor.execute(stage3_output)
stage5_output = stage5_processor.execute(stage4_output)
stage6_output = stage6_processor.execute(stage5_output)
```

### 統一輸出格式
```python
# 標準階段輸出格式
{
    'stage': 'stage_name',
    'data': {...},           # 核心處理數據
    'metadata': {
        'processing_time': '...',
        'input_count': 123,
        'output_count': 456,
        'performance_metrics': {...}
    },
    'validation_result': {...}  # 學術標準驗證
}
```

## 📋 相關文檔

### 核心文檔
- **[階段職責規範](./STAGE_RESPONSIBILITIES.md)** - v2.0六階段職責分工
- **[Stage 1: 數據載入層](./stages/stage1-tle-loading.md)** - TLE數據載入設計
- **[Stage 2: 軌道計算層](./stages/stage2-orbital-computing.md)** - SGP4軌道計算設計
- **[Stage 3: 信號分析層](./stages/stage3-signal-analysis.md)** - 信號品質分析設計
- **[Stage 4: 優化決策層](./stages/stage4-optimization.md)** - 優化決策設計
- **[Stage 5: 數據整合層](./stages/stage5-data-integration.md)** - 數據整合設計
- **[Stage 6: 持久化與API層](./stages/stage6-persistence-api.md)** - API服務設計

### 學術標準
- **[學術數據標準](./academic_data_standards.md)** - Grade A學術要求
- **[衛星換手標準](./satellite_handover_standards.md)** - 換手算法標準

## 🎯 v2.0重構總結

### 核心成就
1. **架構簡化**: 模組化設計，單一責任原則
2. **性能優化**: 明確的性能指標和優化策略
3. **學術合規**: 嚴格的Grade A學術標準
4. **可維護性**: 每階段職責明確，便於維護和擴展

### 未來發展
- **強化學習**: Stage 4已預留RL擴展接口
- **實時處理**: 支援增量更新和實時數據流
- **水平擴展**: 模組化設計支援分散式部署

---

**版本**: v2.0
**架構基礎**: refactoring_plan_v2
**文檔狀態**: 與 stages/ 目錄完全一致
**最終更新**: 2025-09-21