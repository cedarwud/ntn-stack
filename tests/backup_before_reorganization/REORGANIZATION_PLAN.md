# 測試框架重組計劃

## 🎯 重組目標

基於對整個專案的全面檢視，發現測試目錄存在大量重複、不必要的測試和組織問題。本計劃旨在：

1. **清理重複測試**: 刪除80%的重複測試檔案
2. **重新組織結構**: 建立清晰的測試分類和階層
3. **填補測試空白**: 新增缺失的關鍵測試
4. **統一測試執行**: 建立單一測試運行器

## 📊 當前狀況分析

### ✅ 已完成階段 (依據 DR.md)
- **階段 1-3**: 完全實現 (5G 核心網、衛星軌道計算、NTN gNodeB 映射)
- **階段 4-8**: 實際上已大幅實現 (70-95%)，但 DR.md 標記為待實現

### 🔍 測試重複問題
- **5+ 個不同的測試運行器**
- **多個重複的 E2E 測試**
- **API 測試功能重疊**
- **性能測試重複**
- **工具和腳本冗餘**

## 🗂️ 重組後的目錄結構

```
tests/
├── unit/                          # 單元測試
│   ├── netstack/                  # NetStack 服務單元測試
│   ├── simworld/                  # SimWorld 單元測試
│   └── deployment/                # 部署相關單元測試
├── integration/                   # 整合測試
│   ├── api/                       # API 整合測試
│   ├── services/                  # 服務間整合測試
│   └── infrastructure/            # 基礎設施整合測試
├── e2e/                          # 端到端測試
│   ├── scenarios/                # 測試場景
│   ├── frameworks/               # E2E 測試框架
│   └── configs/                  # E2E 配置
├── performance/                   # 性能測試
│   ├── load/                     # 負載測試
│   ├── stress/                   # 壓力測試
│   └── benchmarks/               # 基準測試
├── security/                      # 安全測試 (新增)
├── stage_validation/              # 階段驗證測試
│   ├── stage4_sionna_ai/         # 階段4：Sionna + AI-RAN
│   ├── stage5_uav_mesh/          # 階段5：UAV 群組 + Mesh
│   ├── stage6_handover/          # 階段6：衛星換手
│   ├── stage7_performance/       # 階段7：性能優化
│   └── stage8_ai_decision/       # 階段8：AI 決策
├── utils/                        # 測試工具和輔助
│   ├── runners/                  # 測試運行器
│   ├── helpers/                  # 測試輔助函數
│   ├── fixtures/                 # 測試數據和 Mock
│   └── reporting/                # 報告生成
├── configs/                      # 統一測試配置
└── reports/                      # 測試報告輸出
```

## 🚮 刪除清單 (重複和不必要的檔案)

### E2E 測試重複
- `e2e/test_e2e_quick.py` (與 run_quick_test.py 重複)
- `e2e/stage4_quick_verification_test.py` (併入 scenarios)
- `e2e/stage5_uav_swarm_mesh_test.py` (重新組織)
- `e2e/stage6_handover_prediction_test.py` (重新組織)

### API 測試重複
- `integration/api/test_unified_api_simple.py` (併入 api_tests.py)

### 測試運行器重複
- `tools/run_all_tests.py`
- `tools/test_runner.py`
- `run_tests.py`
- `tools/run_all_integration_tests.py`

### 性能測試重複
- `performance/performance_tests.py` (併入 load_tests.py)

### 文檔重複
- `e2e/IMPLEMENTATION_COMPLETE.md`
- `e2e/QUICK_START.md`

## ➕ 新增測試清單 (填補空白)

### 安全測試 (新建 security/)
- `test_api_security.py` - API 安全驗證
- `test_authentication.py` - 認證機制測試
- `test_data_validation.py` - 輸入驗證測試

### 基礎設施整合測試
- `integration/infrastructure/test_docker_integration.py`
- `integration/infrastructure/test_database_integration.py`
- `integration/services/test_service_mesh.py`

### 階段驗證測試重新組織
- 將現有的階段測試重新分類
- 確保每個階段都有完整的驗證測試
- 統一測試格式和報告

## 🔧 實施步驟

### 第一階段：清理重複 (立即執行)
1. 刪除重複的測試檔案
2. 合併相似功能的測試
3. 統一測試配置

### 第二階段：重新組織 (1-2週)
1. 建立新的目錄結構
2. 移動和重構現有測試
3. 統一命名規範

### 第三階段：填補空白 (2-3週)
1. 新增缺失的測試
2. 完善測試覆蓋率
3. 建立統一測試運行器

### 第四階段：驗證和優化 (1週)
1. 執行完整測試套件
2. 優化測試性能
3. 完善文檔和使用指南

## 📈 預期成果

- **檔案數量減少 80%**: 從 50+ 個測試檔案減少到 10-15 個核心測試
- **測試覆蓋率提升**: 從分散的功能測試到全面的系統驗證
- **執行時間優化**: 消除重複測試，提升執行效率
- **維護性改善**: 清晰的結構和統一的標準
- **可靠性提升**: 更好的測試隔離和錯誤處理

## 🎯 最終目標

建立一個**簡潔、高效、全面**的測試框架，支持：
- **快速驗證**: 5分鐘內完成核心功能測試
- **全面測試**: 30分鐘內完成完整系統驗證
- **階段驗證**: 每個開發階段都有對應的驗證測試
- **持續整合**: 支持 CI/CD 流水線的自動化測試
- **問題定位**: 清晰的錯誤報告和問題追蹤

---

**注意**: 本重組計劃將確保測試框架與實際的專案實現狀況相符，並為後續的開發和維護提供堅實的基礎。