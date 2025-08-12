# 🛰️ 衛星軌道計算系統重構 - 全量SGP4軌道計算引擎

**版本**: v1.0.0  
**建立日期**: 2025-08-12  
**重構目標**: 澄清架構混亂，建立正確的全量衛星軌道計算系統  

## 🎯 重構背景

### 問題診斷
原系統存在嚴重的命名混亂：
- ❌ **錯誤認知**: `phase0` 被當作獨立階段
- ❌ **架構混亂**: 150+50、651+301 等子集配置與主要處理流程混淆
- ❌ **職責不清**: 建構時預計算與運行時處理邏輯混合

### 正確架構理解
```
🏗️ Docker 建構階段
├── TLE 數據載入與驗證
├── SGP4 完整算法預計算
└── 預計算數據打包進容器映像

🚀 衛星軌道計算引擎: 全量衛星軌道計算 (本專案重構目標)
├── 處理範圍: 8,715 顆衛星 (8,064 Starlink + 651 OneWeb)
├── 核心算法: 完整 SGP4 軌道計算 (符合 CLAUDE.md 原則)
├── 輸出目標: 完整軌道數據庫
└── 下游接口: 提供給信號品質計算引擎使用

⚡ 信號品質計算引擎: 3GPP Events & 信號品質計算 (後續階段)
├── 輸入: 衛星軌道計算引擎的完整軌道數據
├── 處理: RSRP/RSRQ/SINR 計算 + A4/A5/D2 事件
└── 輸出: 換手決策數據
```

## 📁 重構檔案結構

### 核心模組
```
phase1_refactor/
├── README.md                          # 本檔案 - 總覽說明
├── 01_data_source/                    # 數據源管理
│   ├── tle_loader.py                 # TLE 數據載入器
│   ├── satellite_catalog.py          # 完整衛星目錄管理
│   └── data_validation.py            # 數據完整性驗證
├── 02_orbit_calculation/              # 軌道計算核心
│   ├── sgp4_engine.py               # 純 SGP4 軌道計算引擎
│   ├── orbit_propagator.py          # 軌道傳播器
│   └── coordinate_transformation.py  # 座標轉換系統
├── 03_processing_pipeline/           # 處理管線
│   ├── phase1_coordinator.py        # Phase 1 主協調器
│   ├── batch_processor.py           # 批次處理器
│   └── progress_monitor.py          # 進度監控
├── 04_output_interface/              # 輸出接口
│   ├── phase1_api.py                # Phase 1 API 接口
│   ├── data_exporter.py             # 數據導出器
│   └── phase2_interface.py          # Phase 2 接口規範
└── 05_integration/                   # 整合測試
    ├── integration_tests.py         # 整合測試套件
    ├── algorithm_verification.py    # 算法驗證
    └── performance_benchmark.py     # 性能基準測試
```

### 配置與文檔
```
phase1_refactor/
├── config/                           # 統一配置
│   ├── phase1_config.yaml          # Phase 1 主要配置
│   ├── constellation_config.yaml    # 星座配置
│   └── observer_config.yaml        # 觀測點配置
├── docs/                            # 技術文檔
│   ├── architecture.md             # 架構設計文檔
│   ├── algorithm_specification.md   # 算法規格說明
│   ├── data_flow.md                # 數據流向文檔
│   └── integration_guide.md        # 整合指南
└── migration/                       # 遷移指南
    ├── phase0_to_phase1_mapping.md # phase0 代碼對應關係
    ├── api_changes.md              # API 變更說明
    └── deployment_guide.md         # 部署指南
```

## 🔍 重構原則

### 核心原則 (符合 CLAUDE.md)
1. **✅ 真實算法**: 100% 使用完整 SGP4 算法，禁止任何簡化
2. **✅ 真實數據**: 使用真實 TLE 數據，禁止模擬或假數據
3. **✅ 全量處理**: 處理所有 8,715 顆衛星，不做預篩選
4. **✅ 精確計算**: 米級軌道精度，符合學術研究標準

### 架構原則
1. **職責分離**: 每個模組職責明確，避免功能重疊
2. **接口清晰**: Phase 1 與 Phase 2 接口標準化
3. **可維護性**: 代碼結構清晰，易於理解和擴展
4. **性能優化**: 在保證算法正確性前提下優化性能

## 📊 Phase 1 技術規格

### 處理規模
- **衛星總數**: 8,715 顆 (全量真實數據)
  - Starlink: 8,064 顆
  - OneWeb: 651 顆
- **算法標準**: 完整 SGP4 (符合 SGDP4/SDP4 標準)
- **精度要求**: 米級位置精度
- **時間覆蓋**: 120 分鐘軌道預計算 (30 秒間隔)

### 性能目標
- **建構時間**: < 5 分鐘 (完整 SGP4 計算)
- **啟動時間**: < 30 秒 (數據載入驗證)
- **API 響應**: < 100ms (單次位置查詢)
- **記憶體使用**: < 2GB (完整軌道數據緩存)

### 數據來源確認
- **TLE 數據源**: `/netstack/tle_data/` (真實軌道根數)
- **預計算存儲**: `/app/data/phase1_orbit_database.json`
- **配置檔案**: 統一配置系統 (UnifiedSatelliteConfig)
- **觀測點**: NTPU (24.9441667°N, 121.3713889°E)

## 🚀 實施階段

### Stage 1: 代碼重構 (進行中)
- [x] 建立正確的檔案結構
- [x] 澄清 phase0 vs Phase 1 概念混亂
- [ ] 重新組織現有代碼到正確位置
- [ ] 統一命名規範

### Stage 2: 算法驗證
- [ ] 確認 SGP4 算法完整性
- [ ] 驗證軌道計算精度
- [ ] 測試全量衛星處理能力

### Stage 3: 接口標準化
- [ ] 建立 Phase 1 → Phase 2 標準接口
- [ ] 設計清晰的 API 規範
- [ ] 建立性能監控機制

### Stage 4: 整合測試
- [ ] 端到端流程測試
- [ ] 性能基準驗證
- [ ] 部署流程優化

## 🔧 關鍵問題澄清

### Q: phase0 與 Phase 1 的關係？
**A**: 原系統中的 "phase0" 實際上就是 Phase 1 的建構時預計算階段，不需要獨立的 phase0。正確理解：
- 建構時執行 Phase 1 的 SGP4 預計算
- 容器啟動時載入 Phase 1 的預計算結果
- API 直接提供 Phase 1 的軌道數據給 Phase 2

### Q: 150+50、651+301 配置的角色？
**A**: 這些是後續階段 (Phase 2/3) 的智能篩選策略，不屬於 Phase 1 的全量計算範疇：
- Phase 1: 全量處理 8,715 顆衛星
- Phase 2/3: 根據應用需求篩選出 150+50 或其他子集

### Q: 算法和數據來源的確認？
**A**: 完全符合 CLAUDE.md 原則：
- ✅ **算法**: 完整 SGP4 (非簡化版本)
- ✅ **數據**: 真實 TLE 軌道根數
- ✅ **處理**: 全量衛星，無預篩選
- ✅ **精度**: 米級軌道精度

## 📞 聯絡資訊

**重構負責**: Phase 1 重構專案團隊  
**技術支援**: 參考 `/docs/` 目錄下的技術文檔  
**問題回報**: 請在相關 GitHub Issue 中提出

---

**重構目標**: 建立清晰、正確、高效的 Phase 1 全量衛星軌道計算系統，為整個 NTN Stack 提供可靠的軌道數據基礎。