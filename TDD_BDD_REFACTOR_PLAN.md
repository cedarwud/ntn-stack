# TDD/BDD 架構重構計劃

## 🎯 目標
將現有的 netstack 系統重構為適合 **pytest + TDD/BDD 練習** 的架構，同時清理未使用的功能和過度分散的目錄結構。

## 🏗️ 目標架構

### 📁 重構後的目錄結構
```
netstack/
├── src/                     # 源代碼 (核心實現)
│   ├── algorithms/          # 算法模組 (扁平化)
│   │   ├── __init__.py
│   │   ├── handover_decision.py      # Fine-Grained Handover
│   │   ├── fast_access_decision.py   # Fast Access Prediction
│   │   ├── orbit_prediction.py       # SGP4 軌道預測
│   │   ├── state_synchronization.py  # 狀態同步
│   │   └── base_algorithm.py         # 抽象基類 (TDD 友好)
│   ├── services/            # 服務層 (依賴注入友好)
│   │   ├── __init__.py
│   │   ├── satellite_service.py      # 衛星管理服務
│   │   ├── orbit_service.py          # 軌道計算服務
│   │   ├── measurement_service.py    # 測量事件服務
│   │   └── tle_service.py           # TLE 數據服務
│   ├── domain/              # 領域模型 (純業務邏輯)
│   │   ├── __init__.py
│   │   ├── satellite.py             # 衛星實體
│   │   ├── orbit.py                 # 軌道模型
│   │   ├── measurement_event.py     # 測量事件
│   │   └── handover_context.py      # 切換上下文
│   ├── infrastructure/      # 基礎設施 (可 mock 的外部依賴)
│   │   ├── __init__.py
│   │   ├── database/               # 數據庫相關
│   │   │   ├── __init__.py
│   │   │   ├── postgresql_client.py
│   │   │   └── redis_client.py
│   │   ├── external/              # 外部 API
│   │   │   ├── __init__.py
│   │   │   └── tle_downloader.py
│   │   └── filesystem/            # 文件系統操作
│   │       ├── __init__.py
│   │       └── data_loader.py
│   ├── interfaces/          # 抽象接口 (便於 mock)
│   │   ├── __init__.py
│   │   ├── repositories.py         # 數據倉庫接口
│   │   ├── services.py            # 服務接口
│   │   └── external_apis.py       # 外部 API 接口
│   └── api/                # FastAPI 端點 (簡化)
│       ├── __init__.py
│       ├── satellite_endpoints.py
│       ├── orbit_endpoints.py
│       └── health_endpoints.py
├── tests/                   # 測試套件 (與 src 對應)
│   ├── unit/               # 單元測試 (TDD 核心)
│   │   ├── algorithms/      # 算法單元測試
│   │   ├── services/       # 服務層單元測試
│   │   ├── domain/         # 領域模型單元測試
│   │   └── infrastructure/ # 基礎設施單元測試
│   ├── integration/        # 整合測試
│   │   ├── test_satellite_pipeline.py
│   │   └── test_api_endpoints.py
│   ├── acceptance/         # 驗收測試 (BDD)
│   │   ├── features/       # BDD 場景
│   │   └── step_definitions/
│   ├── fixtures/           # pytest fixtures
│   │   ├── satellite_fixtures.py
│   │   ├── orbit_fixtures.py
│   │   └── database_fixtures.py
│   ├── conftest.py         # pytest 全局配置
│   └── utils/              # 測試工具
│       ├── builders.py     # Test Data Builders
│       ├── matchers.py     # Custom Matchers
│       └── mock_helpers.py # Mock 輔助函數
├── config/                 # 配置文件
│   ├── test_config.py      # 測試環境配置
│   ├── dev_config.py       # 開發環境配置
│   └── satellite_data/     # 衛星配置數據
├── docs/                   # 文檔
│   ├── tdd_guidelines.md   # TDD 實踐指南
│   ├── bdd_scenarios.md    # BDD 場景說明
│   └── architecture.md     # 架構文檔
├── pytest.ini             # pytest 配置
├── tox.ini                # 多環境測試配置
└── requirements/           # 分離的依賴管理
    ├── base.txt           # 核心依賴
    ├── test.txt           # 測試依賴
    └── dev.txt            # 開發依賴
```

## 📊 現狀問題分析

### 🔍 過度分散的目錄結構
- `src/algorithms/access/` → 1個文件 (fast_access_decision.py)
- `src/algorithms/handover/` → 1個文件 (fine_grained_decision.py)
- `src/algorithms/prediction/` → 1個文件 (orbit_prediction.py)
- `src/services/handover/` → 1個文件
- `src/services/research/` → 1個文件

### 🔄 架構重複問題
- `netstack_api/` (86 文件) - FastAPI 架構
- `src/` (49 文件) - 研究代碼架構
- 功能重疊但結構分離

### ❓ 疑似未使用功能
需要在重構過程中識別和處理的潛在冗余：
- 重複的服務實現
- 過時的實驗代碼
- 未引用的工具函數
- 測試覆蓋率低的模組

## 🚀 重構執行策略

### 🎯 **實際執行階段** (Phase 1-2，總計 12-16小時)

### 階段 1: 結構分析與清理 (4-6小時)
**目標**: 識別核心功能，移除冗余

**執行內容**:
1. **依賴分析**: 分析各模組的實際使用情況
2. **功能審計**: 識別重複和未使用的功能
3. **核心提取**: 提取真正需要的核心算法和服務
4. **冗余清理**: 移除確定不需要的代碼 ⚠️ **需用戶確認後執行**

**輸出**:
- `DEPENDENCY_ANALYSIS.md` - 依賴關係分析報告
- `CLEANUP_REPORT.md` - 清理項目列表
- `CORE_MODULES.md` - 核心模組清單

### 階段 2: 架構重構 (8-10小時) ✅ **重構實際結束點**
**目標**: 建立 TDD/BDD 友好的新架構

**執行內容**:
1. **目錄重組**: 按新架構重新組織文件
2. **依賴注入**: 重構代碼支持依賴注入
3. **接口抽象**: 建立抽象接口便於 mock
4. **純函數化**: 將算法重構為更純的函數

**輸出**:
- ✅ **重構後的源代碼結構** (可直接用於 TDD/BDD 學習)
- ✅ **基本的依賴注入框架**
- ✅ **抽象接口定義**
- ✅ **適合測試的代碼架構**

**📋 Phase 2 完成標準**:
- [ ] 目錄結構符合 TDD/BDD 友好設計
- [ ] 過度分散問題已解決 (單文件目錄合併)
- [ ] 代碼支持依賴注入 (可 mock)
- [ ] 核心算法提取為純函數
- [ ] 冗余功能已清理
- [ ] 架構文檔已更新

---

### 📚 **未來擴展階段** (Phase 3-4，暫不執行)

> **注意**: 以下階段為未來的擴展計劃，目前僅作為參考，不在此次重構範圍內

### 階段 3: 測試基礎建設 (6-8小時) 📋 **未來計劃**
**目標**: 建立完整的測試基礎設施

**執行內容**:
1. **pytest 配置**: 設置 pytest.ini, conftest.py
2. **fixtures 框架**: 建立可重用的測試數據
3. **mock 框架**: 建立 mock 和 stub 輔助工具
4. **測試工具**: 建立自定義斷言和匹配器

**輸出**:
- 完整的測試目錄結構
- pytest 配置和 fixtures
- 測試工具集

### 階段 4: 示範實現 (4-6小時) 📋 **未來計劃**
**目標**: 提供 TDD/BDD 實踐示範

**執行內容**:
1. **TDD 示範**: 為 2-3 個核心算法實現 TDD 測試
2. **BDD 示範**: 建立 2-3 個 BDD 場景
3. **文檔完善**: 完成實踐指南和範例
4. **CI 集成**: 設置持續集成環境

**輸出**:
- 示範性的 TDD/BDD 測試
- 完整的實踐文檔
- CI/CD 配置

## 🧹 未使用功能處理策略

### 推薦方案: **重構時邊檢查** ✅

**理由**:
1. **效率最高**: 避免重複工作，重構和清理同時進行
2. **上下文完整**: 重構時能更準確判斷功能是否必要
3. **風險可控**: 可以逐步驗證移除功能的影響
4. **學習效果好**: 過程中能深入理解代碼結構

**執行方式**:
```bash
# 重構每個模組時的檢查清單
1. 分析模組的實際使用情況 (imports, references)
2. 檢查是否有測試覆蓋
3. 評估業務價值和維護成本
4. 決定保留、重構或移除
5. 記錄決策原因
```

### 其他方案比較

**方案 A: 現在先處理** ❌
- **優點**: 減少重構時的複雜度
- **缺點**: 可能誤刪重要功能，需要二次檢查
- **風險**: 缺乏使用上下文，判斷準確性低

**方案 B: 重構完再處理** ❌
- **優點**: 重構完成後結構清晰
- **缺點**: 可能攜帶冗余到新架構，增加維護負擔
- **風險**: 新架構可能包含不必要的複雜性

## 📋 檢查清單與工具

### 依賴分析工具
```bash
# Python 依賴分析
pip install pydeps
pydeps src --show-deps --max-bacon 2

# 未使用代碼檢測
pip install vulture
vulture src/

# 導入分析
pip install importchecker
importchecker src/
```

### 重構檢查清單
```markdown
對每個模組檢查:
- [ ] 是否被其他模組導入？
- [ ] 是否有對應的測試？
- [ ] 是否有 API 端點使用？
- [ ] 業務邏輯是否核心必要？
- [ ] 代碼品質如何？
- [ ] 是否有重複功能？
```

## 🎓 TDD/BDD 學習路徑

### Phase 1: pytest 基礎 (2-3 週)
- 單元測試編寫
- fixtures 使用
- 參數化測試
- mock 和 patch

### Phase 2: TDD 實踐 (3-4 週)
- 紅-綠-重構循環
- 測試先行開發
- 重構技巧
- 測試驅動設計

### Phase 3: BDD 導入 (2-3 週)
- Given-When-Then 語法
- 場景描述
- 驗收測試
- 活文檔概念

### Phase 4: 進階實踐 (開放式)
- 測試策略設計
- 持續集成
- 測試金字塔
- 性能測試

## 📚 參考資源

### 書籍推薦
- **TDD**: "Test-Driven Development by Example" - Kent Beck
- **BDD**: "The BDD Books" - Gojko Adzic
- **pytest**: "Python Testing with pytest" - Brian Okken

### 實踐指南
- [pytest 官方文檔](https://docs.pytest.org/)
- [pytest-bdd](https://pytest-bdd.readthedocs.io/)
- [Python TDD 最佳實踐](https://testdriven.io/)

---

**準備就緒後，可以按照此計劃開始執行重構。建議從階段 1 的結構分析開始，逐步建立適合 TDD/BDD 學習的代碼架構。**