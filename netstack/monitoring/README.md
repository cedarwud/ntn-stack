# NTN Stack 可觀測性指標統一格式

## 概述

本系統為 NTN Stack 非地面網路項目提供統一的監控指標格式規範，確保來自不同組件的監控數據能夠一致整合，簡化儀表板開發和維護工作，提高系統診斷和分析能力。

## 核心組件

### 1. 指標命名空間規範 (`standards/metrics_namespace_spec.yaml`)

定義了系統中所有指標的統一命名結構：

```
{domain}_{subsystem}_{metric_name}_{unit}
```

**支援的領域 (Domain)**:

-   `ntn_` - 非地面網路組件 (UAV、衛星、空中基站)
-   `open5gs_` - 5G 核心網功能 (AMF、SMF、UPF、PCF)
-   `ueransim_` - RAN 模擬器 (gNB、UE 模擬)
-   `sionna_` - 無線模擬引擎 (GPU 計算、通道模擬)
-   `mesh_` - Mesh 網路 (UAV 間直接通信)
-   `ai_` - AI 智能控制 (機器學習、決策)

### 2. 標準標籤集 (`standards/standard_labels_spec.yaml`)

定義了多維度數據分析的一致標籤集：

-   **公共標籤**: environment, node, service, version, instance
-   **網路標籤**: component, interface, protocol
-   **無線標籤**: cell_id, frequency, bandwidth, modulation
-   **UAV 標籤**: uav_id, altitude, velocity, connection_type
-   **位置標籤**: location, coordinates, coverage_area
-   **測試標籤**: test_id, scenario, test_case
-   **品質標籤**: qos_class, priority, slice_type

### 3. Prometheus 最佳實踐 (`configs/prometheus_best_practices.yaml`)

包含：

-   標準化抓取間隔配置
-   告警規則定義
-   記錄規則 (Recording Rules)
-   資料保留策略
-   安全配置
-   性能優化設置

### 4. Grafana 儀表板模板 (`templates/grafana_dashboard_template.json`)

提供標準的系統總覽儀表板，包含：

-   系統狀態總覽
-   端到端延遲監控 (目標 < 50ms)
-   連接成功率追蹤
-   無線信號品質 (SINR)
-   數據吞吐量統計
-   5G 核心網狀態
-   系統資源使用率
-   GPU 使用率監控
-   API 請求統計

## 工具集

### 1. 指標驗證器 (`tools/metrics_validator.py`)

驗證 Prometheus 指標是否符合統一格式規範：

```bash
# 驗證本地 Prometheus 指標
python monitoring/tools/metrics_validator.py

# 驗證特定指標
python monitoring/tools/metrics_validator.py --metric-name ntn_uav_latency_ms

# 生成驗證報告
python monitoring/tools/metrics_validator.py --output validation_report.txt
```

**功能特點**:

-   指標命名格式檢查
-   標籤使用規範驗證
-   基數問題檢測
-   詳細的錯誤和警告報告
-   改進建議生成

### 2. 指標模擬器 (`tools/metrics_simulator.py`)

生成符合規範的測試指標數據：

```bash
# 啟動基本模擬器
python monitoring/tools/metrics_simulator.py

# 自定義配置
python monitoring/tools/metrics_simulator.py \
  --num-uavs 10 \
  --duration 7200 \
  --enable-anomalies \
  --port 8000
```

**模擬指標**:

-   NTN UAV 延遲、SINR、RSRP
-   連接成功率和數據傳輸
-   Open5GS 核心網統計
-   API 請求和響應時間
-   GPU 和系統資源使用

### 3. 部署工具 (`deploy_observability.py`)

自動化部署整個可觀測性系統：

```bash
# 完整部署
python monitoring/deploy_observability.py

# 僅驗證配置
python monitoring/deploy_observability.py --action validate

# 健康檢查
python monitoring/deploy_observability.py --action health-check
```

## 快速開始

### 1. 系統部署

```bash
# 克隆或進入項目目錄
cd ntn-stack

# 執行一鍵部署
python monitoring/deploy_observability.py

# 查看部署狀態
python monitoring/deploy_observability.py --action health-check
```

### 2. 訪問監控界面

部署完成後：

-   **Grafana 儀表板**: http://localhost:3000/d/ntn-stack-overview
-   **Prometheus**: http://localhost:9090
-   **指標模擬器**: http://localhost:8000/metrics

### 3. 驗證指標合規性

```bash
# 運行指標驗證
python monitoring/tools/metrics_validator.py --verbose

# 檢查驗證報告
cat monitoring/validation_report.txt
```

## 指標示例

### NTN UAV 指標

```prometheus
# UAV 延遲 (目標 < 50ms)
ntn_uav_latency_ms{environment="prod", uav_id="uav-12345678", connection_type="satellite"} 35.2

# UAV 信號品質
ntn_uav_sinr_db{environment="prod", uav_id="uav-12345678", cell_id="12345678", frequency_band="n78"} 18.5

# UAV 連接統計
ntn_uav_connection_success_total{environment="prod", uav_id="uav-12345678", connection_type="satellite"} 1250
ntn_uav_connection_attempts_total{environment="prod", uav_id="uav-12345678", connection_type="satellite"} 1275
```

### Open5GS 核心網指標

```prometheus
# AMF 註冊統計
open5gs_amf_registration_success_total{environment="prod", component="amf", slice_type="urllc"} 980
open5gs_amf_registration_attempts_total{environment="prod", component="amf", slice_type="urllc"} 1000

# UPF 數據傳輸
open5gs_upf_bytes_transmitted_total{environment="prod", component="upf", direction="uplink", slice_type="embb"} 1048576000
```

### API 性能指標

```prometheus
# API 請求統計
netstack_api_requests_total{environment="prod", method="GET", endpoint="/api/v1/uav", status="200"} 5420

# API 響應時間
netstack_api_request_duration_seconds{environment="prod", method="GET", endpoint="/api/v1/uav"} 0.045
```

## 最佳實踐

### 1. 指標命名

-   使用領域前綴 (如 `ntn_`, `open5gs_`)
-   包含測量單位 (如 `_ms`, `_bytes`, `_percent`)
-   保持一致的命名慣例
-   避免使用駝峰命名法

### 2. 標籤使用

-   使用標準標籤集中定義的標籤
-   避免高基數標籤 (如時間戳、UUID)
-   保持標籤值的穩定性
-   考慮查詢和聚合需求

### 3. 抓取配置

-   關鍵指標使用較短的抓取間隔 (1-5 秒)
-   一般指標使用標準間隔 (15 秒)
-   慢變化指標使用較長間隔 (60 秒)
-   設置適當的抓取超時

### 4. 告警設計

-   基於業務 SLA 設置閾值
-   使用分層告警 (Critical, Warning, Info)
-   包含足夠的上下文資訊
-   考慮告警疲勞問題

## 關鍵性能指標 (KPI)

### 系統級 KPI

| 指標         | 目標值  | 描述                   |
| ------------ | ------- | ---------------------- |
| 端到端延遲   | < 50ms  | UAV 到核心網的往返時間 |
| 連接成功率   | > 95%   | UAV 連接建立成功的比例 |
| 系統可用性   | > 99.9% | 服務正常運行時間比例   |
| 連接恢復時間 | < 2s    | 連接中斷後的恢復時間   |

### 無線性能 KPI

| 指標       | 目標值    | 描述               |
| ---------- | --------- | ------------------ |
| SINR       | > 10dB    | 信號與干擾加噪聲比 |
| RSRP       | > -100dBm | 參考信號接收功率   |
| 數據吞吐量 | > 100Mbps | 下行鏈路峰值速率   |

### 系統資源 KPI

| 指標         | 目標值 | 描述               |
| ------------ | ------ | ------------------ |
| CPU 使用率   | < 80%  | 系統 CPU 利用率    |
| 記憶體使用率 | < 85%  | 系統記憶體利用率   |
| GPU 使用率   | < 90%  | GPU 計算資源利用率 |

## 故障排除

### 常見問題

1. **指標驗證失敗**

    - 檢查指標命名是否符合規範
    - 驗證標籤值是否在允許範圍內
    - 確認領域前綴是否正確

2. **Grafana 儀表板顯示異常**

    - 確認 Prometheus 數據源配置
    - 檢查查詢語句是否正確
    - 驗證標籤選擇器是否匹配

3. **指標模擬器連接失敗**
    - 檢查端口是否被占用
    - 確認防火牆設置
    - 驗證網路連接

### 日誌分析

檢查相關日誌文件：

```bash
# 部署日誌
tail -f monitoring/deployment.log

# 指標驗證日誌
python monitoring/tools/metrics_validator.py --verbose

# 模擬器運行狀態
curl http://localhost:8000/metrics | head -20
```

## 擴展開發

### 添加新的指標領域

1. 編輯 `standards/metrics_namespace_spec.yaml`
2. 添加新的領域定義和子系統
3. 更新標籤規範
4. 運行驗證工具確認更改

### 創建自定義儀表板

1. 基於 `templates/grafana_dashboard_template.json`
2. 使用標準的查詢模式
3. 遵循視覺化最佳實踐
4. 測試所有變量和過濾器

### 集成新的監控組件

1. 確保指標符合命名規範
2. 使用標準標籤集
3. 配置適當的抓取間隔
4. 添加相應的告警規則

## 版本更新

### v1.0.0 (當前)

-   初始版本，包含基本指標規範
-   支援 NTN、Open5GS、Sionna 指標
-   提供驗證和模擬工具
-   標準 Grafana 儀表板模板

### 計劃功能

-   自動化指標發現
-   高級告警規則模板
-   多集群支援
-   性能基準測試

## 技術支援

如需技術支援或反饋問題：

1. 檢查本文檔的故障排除章節
2. 運行診斷工具: `python monitoring/deploy_observability.py --action health-check`
3. 查看詳細日誌: `--verbose` 選項
4. 提交問題報告，包含相關日誌和配置資訊

## 授權

本項目遵循 MIT 授權條款。
