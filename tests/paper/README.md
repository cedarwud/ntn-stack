# 論文復現測試程式集

## 📋 概述

本資料夾包含論文《Accelerating Handover in Mobile Satellite Network》復現專案的所有測試程式，按階段分類組織。

## 📊 當前測試狀態

**最近測試結果 (2024-12-06)**:
- 🚀 **快速驗證**: 80% 通過率 (4/5 測試通過)
- 🧪 **核心功能驗證**: 60% 通過率 (3/5 測試通過)
- ✅ **Algorithm 2**: 完全正常 - 648個地理區塊、UE策略管理
- 🔧 **Algorithm 1**: 需要修正 AccessInfo 參數
- 🔧 **整合橋接**: 需要修正方法名稱 (switch_mode)
- ⚠️  **HTTP 422 錯誤**: 外部 TLE API 問題，不影響演算法邏輯

## 🎯 測試環境

**建議使用 venv 環境進行測試 (推薦)**

### 環境分析：

#### ✅ **venv 環境 (推薦用於開發測試)**
- ✅ **完整代碼訪問** - 可直接導入所有論文復現模組
- ✅ **路徑配置正確** - 所有依賴項目已配置
- ✅ **快速迭代** - 適合開發階段的快速測試

#### 🌐 **Docker 容器環境 (適合整合測試)**
- ✅ **網路層面突破** - simworld_backend 可訪問 netstack-core 網路
- ✅ **服務調用正常** - HTTP API 跨容器調用成功
- ❌ **代碼層面隔離** - 無法直接導入 NetStack 模組 (可透過 API 調用)
- 🔧 **可通過 Volume 掛載解決代碼隔離問題**

### 測試執行方式：
```bash
# 在 ntn-stack 根目錄執行
cd /home/sat/ntn-stack
source venv/bin/activate
python paper/階段資料夾/測試腳本.py
```

## 📁 資料夾結構

```
paper/
├── 1.1_satellite_orbit/          # 1.1 衛星軌道預測模組整合
│   └── test_tle_integration.py         # 完整測試 (已修正方法缺失和時間戳問題)
├── 1.2_synchronized_algorithm/   # 1.2 同步演算法 (Algorithm 1)
│   └── test_algorithm_1.py
├── 1.3_fast_prediction/          # 1.3 快速衛星預測演算法 (Algorithm 2)
│   └── test_algorithm_2.py
├── comprehensive/                # 綜合測試執行器
│   ├── run_all_tests.py               # 完整測試執行器
│   ├── test_core_validation.py        # 核心功能驗證 (無外部依賴)  
│   ├── quick_validation.py            # 快速驗證 (整合 quick_test)
│   ├── run_docker_tests.py            # 容器內測試執行器
│   └── test_cleanup_summary.py        # 檔案清理摘要報告
└── README.md                     # 本說明文件
```

## 🧪 測試階段詳細說明

### 1.1 衛星軌道預測模組整合
**檔案**: `1.1_satellite_orbit/test_tle_integration.py`

**測試內容**:
- NetStack ↔ SimWorld TLE 資料橋接
- 衛星位置計算準確性
- 軌道預測功能驗證
- 跨容器通信測試
- 快取機制驗證

**執行方式**:
```bash
source venv/bin/activate
python paper/1.1_satellite_orbit/test_tle_integration.py
```

### 1.2 同步演算法 (Algorithm 1)
**檔案**: `1.2_synchronized_algorithm/test_algorithm_1.py`

**測試內容**:
- 二分搜尋換手時間預測 (<25ms 精度)
- 週期性更新機制 (Δt=5s)
- UE-衛星關係表管理 (R表)
- 換手時間表管理 (Tp表)
- 無信令同步協調
- 多 UE 並行處理
- 整合橋接服務

**執行方式**:
```bash
source venv/bin/activate
python paper/1.2_synchronized_algorithm/test_algorithm_1.py
```

### 1.3 快速衛星預測演算法 (Algorithm 2)
**檔案**: `1.3_fast_prediction/test_algorithm_2.py`

**測試內容**:
- 地理區塊劃分 (10度網格，648個全球區塊)
- UE 存取策略管理 (Flexible/Consistent)
- 衛星分配到區塊演算法
- 最佳衛星選擇演算法
- 軌道方向最佳化
- 預測準確率驗證 (>95% 目標)
- 效能統計追蹤

**執行方式**:
```bash
source venv/bin/activate
python paper/1.3_fast_prediction/test_algorithm_2.py
```

### 綜合測試執行器
**檔案**: `comprehensive/run_all_tests.py`

**功能**:
- 統一執行所有階段測試
- 生成完整論文復現報告
- 支援選擇性執行特定階段
- 自動保存測試報告為 JSON 格式

**執行方式**:
```bash
# 執行所有測試
source venv/bin/activate
python paper/comprehensive/run_all_tests.py

# 執行特定階段
python paper/comprehensive/run_all_tests.py --stage 1.2
python paper/comprehensive/run_all_tests.py --stage 1.3

# 啟用詳細輸出
python paper/comprehensive/run_all_tests.py --verbose
```

## 📊 測試驗證項目

### 論文復現核心項目：
- 🔧 **Algorithm 1 實現** - 二分搜尋精度 <25ms (需修正 AccessInfo 參數)
- ✅ **Algorithm 2 實現** - 地理區塊劃分 + UE 策略管理 (648個區塊)
- 🔧 **TLE 整合** - NetStack ↔ SimWorld 資料橋接 (HTTP 422 錯誤)
- ✅ **預測準確率** - 目標 >95%
- 🔧 **整合橋接** - 多模式演算法切換 (需修正方法名稱)

### 效能指標：
- 二分搜尋執行時間 <25ms
- 地理區塊覆蓋全球 (648個區塊)
- UE 註冊和策略管理功能正常
- 衛星位置預測準確性
- 跨容器通信穩定性

## 🎯 使用建議

### 1. 首次執行建議順序：
```bash
# 1. 先執行快速驗證，獲得整體狀況
python paper/comprehensive/quick_validation.py

# 2. 執行核心功能驗證 (無外部依賴)
python paper/comprehensive/test_core_validation.py

# 3. 如有特定階段失敗，單獨執行該階段
python paper/1.2_synchronized_algorithm/test_algorithm_1.py

# 4. 查看詳細報告
ls paper/comprehensive/paper_reproduction_report_*.json
```

### 2. 日常開發測試：
```bash
# 測試特定功能修改
python paper/1.3_fast_prediction/test_algorithm_2.py

# 驗證整合功能
python paper/1.1_satellite_orbit/test_tle_integration.py
```

### 3. 持續整合：
```bash
# 完整驗證管道
python paper/comprehensive/run_all_tests.py --verbose
```

## 📝 報告輸出

測試報告將保存在：
- **綜合報告**: `paper/comprehensive/paper_reproduction_report_YYYYMMDD_HHMMSS.json`
- **控制台輸出**: 即時顯示測試進度和結果統計

報告包含：
- 各階段詳細測試結果
- 論文復現狀態驗證
- 效能統計數據
- 後續步驟建議

## ⚠️  注意事項

1. **必須在 ntn-stack 根目錄執行**
2. **必須啟用 venv 環境**
3. **確保 Docker 容器正在運行** (SimWorld 服務需要)
4. **測試過程中避免修改相關服務代碼**

## 🔧 故障排除

### 常見問題：

1. **模組導入失敗**
   ```bash
   # 確認路徑設置
   echo $PWD  # 應該在 /home/sat/ntn-stack
   source venv/bin/activate
   ```

2. **SimWorld 連接失敗**
   ```bash
   # 檢查容器狀態
   docker ps | grep simworld
   ```

3. **權限問題**
   ```bash
   # 確認檔案權限
   chmod +x paper/*/test_*.py
   ```

## 📞 支援

如遇問題請檢查：
1. CLAUDE.md 專案環境說明
2. 各測試腳本的詳細錯誤輸出
3. Docker 容器運行狀態
4. Python 虛擬環境配置

---

## 📍 檔案整理說明

**2024-12-06 更新**: 已完成測試檔案整理和修正
- ❌ 移除了 12 個重複檔案 (包含原始 1.1 測試檔案)
- ✅ 統一整合至 `paper/` 資料夾，只保留可用版本
- ✅ 修正了 SimWorldTLEBridgeService 缺失方法
- ✅ 修正了時間戳格式錯誤 ('float' object has no attribute 'isoformat')
- ✅ 更新所有路徑從 `Desktop/paper/` 至 `paper/`
- 🔧 需要修正: AccessInfo 參數、整合橋接方法名稱
- ⚠️  HTTP 422 錯誤不影響演算法核心邏輯