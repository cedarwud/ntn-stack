# NTN Stack 端到端測試 - 快速開始指南

## 🚀 快速開始

本指南將幫助您在幾分鐘內運行基本的端到端測試，驗證 NTN Stack 系統的核心功能。

### 方法一：快速驗證測試 (推薦新用戶)

這是最簡單的測試方法，無需安裝複雜依賴，適合快速驗證系統基本功能：

```bash
# 進入測試目錄
cd tests/e2e

# 運行快速測試（只需要 Python 3.8+）
python run_quick_test.py
```

這個測試將會：

-   ✅ 檢查系統基本需求
-   ✅ 驗證目錄結構
-   ✅ 執行模擬的連接測試
-   ✅ 執行模擬的備援測試
-   ✅ 生成詳細的測試報告

**預期輸出**：

```
============================================================
NTN Stack 端到端測試 - 快速啟動
============================================================
時間: 2024-12-01 14:30:25

🔍 檢查基本需求...
✅ Python 版本: 3.11.0
✅ 模組 json 可用
✅ 模組 asyncio 可用
✅ 模組 pathlib 可用
✅ 模組 subprocess 可用
✅ 目錄 standards 存在
✅ 目錄 tools 存在
...

🚀 開始執行快速端到端測試...

🔗 執行基本連接測試...
  執行: 初始化 UAV 終端...
  ✅ 初始化 UAV 終端 完成 (1.0s)
  ...

📋 測試完成摘要
============================================================
總測試數: 2
通過測試: 2
失敗測試: 0
成功率: 100.0%

🎉 所有測試都通過了！系統基本功能正常。
```

### 方法二：完整測試系統

如果您需要運行完整的測試系統，請先安裝依賴：

```bash
# 安裝測試依賴
pip install -r requirements.txt

# 運行測試場景執行器
python tools/scenario_executor.py --help

# 執行基本測試場景
python tools/scenario_executor.py --scenario uav_satellite_basic_connectivity --report html

# 執行測試套件
python tools/scenario_executor.py --suite critical_path --report json

# 運行系統監控器
python tools/system_monitor.py --duration 300 --report html
```

### 方法三：使用 Docker (計劃中)

```bash
# 構建測試容器
docker-compose -f docker-compose.test.yml build

# 運行測試套件
docker-compose -f docker-compose.test.yml up test-runner
```

## 📊 查看測試報告

測試完成後，報告會保存在以下位置：

-   **JSON 報告**: `tests/e2e/reports/quick_test_report_YYYYMMDD_HHMMSS.json`
-   **HTML 報告**: `tests/e2e/reports/quick_test_report_YYYYMMDD_HHMMSS.html`

打開 HTML 報告可以看到詳細的測試結果，包括：

-   測試執行摘要
-   關鍵性能指標
-   測試步驟詳情
-   改進建議

## 🎯 關鍵指標驗證

快速測試會驗證以下關鍵指標：

| 指標         | 目標值    | 驗證內容               |
| ------------ | --------- | ---------------------- |
| 端到端延遲   | < 50ms    | UAV 與衛星連接建立時間 |
| 數據吞吐量   | > 100Mbps | 數據傳輸速率           |
| 故障恢復時間 | < 2s      | Mesh 網路切換時間      |
| 連接成功率   | > 95%     | 連接建立成功的百分比   |
| 數據完整性   | 100%      | 數據傳輸無損失         |

## 🔧 故障排除

### 常見問題

**1. Python 版本過低**

```
❌ Python 版本過低，需要 Python 3.8+
```

**解決方案**: 升級 Python 到 3.8 或更高版本

**2. 模組不可用**

```
❌ 模組 pandas 不可用
```

**解決方案**: 安裝缺少的依賴

```bash
pip install pandas
# 或安裝所有依賴
pip install -r requirements.txt
```

**3. 服務不可用**

```
❌ netstack 不可用: Connection refused
```

**解決方案**: 確保相關服務正在運行

```bash
# 檢查服務狀態
curl http://localhost:8000/health
curl http://localhost:8100/health
```

### 調試模式

如果遇到問題，可以啟用詳細的調試輸出：

```bash
# 快速測試 - 調試模式
python run_quick_test.py 2>&1 | tee debug.log

# 完整測試 - 調試模式
python tools/scenario_executor.py --scenario uav_satellite_basic_connectivity --log-level DEBUG
```

## 📚 進一步學習

-   📖 **完整文檔**: [README.md](README.md)
-   🔬 **實現摘要**: [E2E_INTEGRATION_TESTING_SUMMARY.md](E2E_INTEGRATION_TESTING_SUMMARY.md)
-   ⚙️ **配置指南**: [configs/development.yaml](configs/development.yaml)
-   🛠️ **工具文檔**: [tools/](tools/)

## 🤝 獲得幫助

如果您在使用過程中遇到問題：

1. **檢查日誌**: 查看 `tests/e2e/logs/` 目錄下的日誌文件
2. **查看報告**: 分析測試報告中的錯誤信息
3. **調試模式**: 使用 `--log-level DEBUG` 獲取詳細信息
4. **系統檢查**: 運行 `python run_quick_test.py` 進行基本診斷

## 🎉 成功案例

如果您看到以下輸出，說明系統基本功能正常：

```
🎉 所有測試都通過了！系統基本功能正常。

建議下一步:
  1. 運行完整的端到端測試套件
  2. 執行性能壓力測試
  3. 進行長時間穩定性測試
```

恭喜！您已經成功驗證了 NTN Stack 系統的核心功能。現在可以進行更深入的測試或開始使用系統了。
