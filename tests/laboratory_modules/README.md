# NTN Stack 實驗室驗測系統

這是專為 NTN Stack 系統設計的專業級實驗室驗測框架，旨在實現 100% 測試通過率，確保系統在實驗室環境下的各項關鍵指標達標。

## 📋 系統概述

實驗室驗測系統根據 TODO.md 第 14 項「實驗室驗測準備與執行」要求設計，包含以下核心功能：

### 🎯 關鍵驗測目標

-   **端到端延遲 < 50ms** 驗證
-   **連接中斷後 2s 內重建連線** 驗證
-   **SINR、吞吐量、干擾避讓** 量化測試
-   **系統功能完整性** 驗證
-   **性能基準達成** 評估

### 🧪 測試模組架構

```
tests/laboratory_modules/
├── __init__.py                 # 模組導出
├── connectivity_tests.py       # 連接性測試
├── api_tests.py                # API 功能測試
├── performance_tests.py        # 性能測試（核心指標）
├── load_tests.py               # 負載測試
├── interference_tests.py       # 干擾測試
├── failover_tests.py           # 故障切換測試
├── e2e_tests.py                # 端到端測試
├── stress_tests.py             # 壓力測試
└── README.md                   # 說明文檔
```

## 🚀 快速開始

### 1. 環境準備

確保 Docker 服務正常運行：

```bash
# 啟動 NTN Stack 服務
make up

# 檢查服務狀態
make status
```

### 2. 執行完整實驗室驗測

```bash
# 完整測試套件（推薦）
python tests/run_laboratory_tests.py

# 或者直接運行主測試套件
python tests/laboratory_test_suite.py
```

### 3. 執行特定測試模式

```bash
# 快速測試（基本功能驗證）
python tests/run_laboratory_tests.py --mode quick

# 性能測試（關鍵指標驗證）
python tests/run_laboratory_tests.py --mode performance

# 壓力測試（極限條件驗證）
python tests/run_laboratory_tests.py --mode stress

# 連接性測試
python tests/run_laboratory_tests.py --mode connectivity

# API 功能測試
python tests/run_laboratory_tests.py --mode api
```

### 4. 自定義配置

```bash
# 使用自定義配置文件
python tests/run_laboratory_tests.py --config tests/configs/custom_lab_config.yaml

# 啟用詳細日誌
python tests/run_laboratory_tests.py --verbose

# 不生成報告（僅執行測試）
python tests/run_laboratory_tests.py --no-reports
```

## 📊 測試模組詳解

### 🔗 ConnectivityTester (connectivity_tests.py)

**功能**：測試系統各組件間的基本連接性

-   Docker 容器間網路連接
-   服務間 API 通信
-   資料庫連接性
-   內外部網路訪問

**關鍵指標**：

-   網路延遲
-   連接成功率
-   服務可達性

### 🌐 APITester (api_tests.py)

**功能**：驗證 NetStack 和 SimWorld API 的功能正確性

-   端點響應驗證
-   數據格式檢查
-   錯誤處理測試
-   跨服務整合

**測試範圍**：

-   NetStack 核心/UAV/系統 API
-   SimWorld 無線/UAV API
-   API 響應驗證

### ⚡ PerformanceTester (performance_tests.py)

**功能**：驗證系統關鍵性能指標

-   **端到端延遲 < 50ms**（實驗室驗測要求）
-   **連接恢復時間 < 2s**（實驗室驗測要求）
-   API 響應時間
-   吞吐量測試
-   資源利用率監控

**核心指標**：

-   E2E 延遲：目標 < 50ms
-   恢復時間：目標 < 2s
-   API 響應：目標 < 100ms
-   成功率：目標 > 99%

### 🔥 LoadTester (load_tests.py)

**功能**：測試系統在高負載下的性能表現

-   高並發負載測試
-   持續負載測試
-   突增負載測試

**測試場景**：

-   並發用戶：100+ 同時連接
-   持續負載：30 秒穩定請求
-   負載突增：正常 → 高負載 → 恢復

### 📡 InterferenceTester (interference_tests.py)

**功能**：測試系統的抗干擾能力

-   頻率干擾模擬
-   信號劣化測試
-   干擾檢測與緩解
-   系統恢復能力

**干擾類型**：

-   頻率干擾
-   信號阻擋
-   噪聲注入

### 🔄 FailoverTester (failover_tests.py)

**功能**：驗證系統的故障切換和恢復能力

-   服務可用性檢查
-   優雅降級測試
-   恢復機制驗證
-   數據一致性保護

### 🔗 E2ETester (e2e_tests.py)

**功能**：測試完整的端到端工作流程

-   UAV-衛星連接流程
-   跨服務數據流
-   完整任務工作流
-   系統整合驗證

### 💥 StressTester (stress_tests.py)

**功能**：測試系統在極限條件下的穩定性

-   極限負載測試（500+ 並發）
-   記憶體壓力測試
-   長時間穩定性（5 分鐘+）
-   超載恢復測試

## 📈 測試報告

### 報告格式

測試完成後會生成詳細報告：

-   **JSON 格式**：`tests/reports/laboratory/laboratory_test_report_YYYYMMDD_HHMMSS.json`
-   **日誌文件**：`tests/reports/laboratory/lab_test_YYYYMMDD_HHMMSS.log`

### 報告內容

-   測試會話資訊
-   各階段執行結果
-   性能指標統計
-   失敗測試分析
-   系統資源使用情況

## ⚙️ 配置說明

### 主配置文件

`tests/configs/laboratory_test_config.yaml` 包含：

-   測試環境配置
-   性能基準設定
-   測試場景定義
-   成功標準配置

### 關鍵配置項

```yaml
performance_benchmarks:
    latency:
        e2e_target_ms: 50 # 端到端延遲目標
        api_response_target_ms: 100
    reliability:
        connection_recovery_target_s: 2.0 # 連接恢復目標
        uptime_target_percent: 99.9

success_criteria:
    overall_pass_rate: 100 # 必須 100% 通過
```

## 🎯 成功標準

### 實驗室驗測通過條件

1. **100% 測試通過率**
2. **端到端延遲 < 50ms**
3. **連接恢復時間 < 2s**
4. **API 響應時間 < 100ms**
5. **系統穩定性 > 99.9%**

### 關鍵性能指標

-   **延遲性能**：E2E < 50ms, API < 100ms
-   **可靠性**：恢復 < 2s, 穩定性 > 99.9%
-   **吞吐量**：最小 10Mbps, 目標 50Mbps
-   **連接性**：基本連接 100% 成功

## 🔧 疑難排解

### 常見問題

**Q: 測試失敗「容器未運行」**

```bash
# 檢查容器狀態
docker ps
make status

# 重新啟動服務
make down && make up
```

**Q: 延遲測試不達標**

```bash
# 檢查網路狀況
ping localhost
docker network ls

# 減少系統負載
# 確保測試期間無其他重負載程序
```

**Q: 記憶體/CPU 資源不足**

```bash
# 檢查系統資源
htop
free -h

# 調整測試並發度
# 修改配置文件中的並發參數
```

### 調試選項

```bash
# 啟用詳細日誌
python tests/run_laboratory_tests.py --verbose

# 延長超時時間
python tests/run_laboratory_tests.py --timeout 3600

# 執行單一測試類型
python tests/run_laboratory_tests.py --mode connectivity
```

## 📞 支援

如遇到問題，請：

1. 檢查系統日誌：`tests/reports/laboratory/`
2. 確認服務狀態：`make status`
3. 查看測試報告：JSON 和日誌文件
4. 參考配置文件：`tests/configs/laboratory_test_config.yaml`

---

## 🎉 總結

本實驗室驗測系統提供了完整的自動化測試框架，確保 NTN Stack 系統在實驗室環境下的各項關鍵指標達標。透過模組化設計，系統可以靈活地進行各種測試場景的驗證，為後續的戶外測試奠定堅實基礎。
