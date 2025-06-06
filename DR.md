# NTN Stack 執行指引

本文件說明如何使用本倉庫復現 *paper.pdf* (Accelerating Handover in Mobile Satellite Network) 中的系統。倉庫已整合 NetStack (5G 核心網與 API)、UERANSIM、SimWorld 視覺化及監控服務，依照以下步驟即可啟動並重現論文環境。

## 1. 環境需求

- Linux (建議 Ubuntu 22.04+)
- Docker 24 與 Docker Compose 2
- Python 3.11 以上
- Git

## 2. 取得程式碼

```bash
git clone https://github.com/your-org/ntn-stack.git
cd ntn-stack
```

## 3. 啟動完整系統

執行一次性建置與啟動流程，會下載映像檔、啟動核心網及 RAN 模擬器並初始化範例資料：

```bash
make setup-fresh
```

此命令等同於 `make clean`、`make up`、`make register-subscribers` 及 `make start-ran` 的組合，流程可參考 `netstack/README.md` 前段說明【F:netstack/README.md†L1-L24】。

啟動後可使用 `make verify-setup` 檢查環境【F:netstack/README.md†L52-L62】。

## 4. 確認服務狀態

- NetStack API: <http://localhost:8080>
- Swagger UI: <http://localhost:8080/docs>
- SimWorld: <http://localhost:8888>
- Prometheus/Grafana: <http://localhost:9090> / <http://localhost:3000>

可透過下列指令檢查各容器與服務狀態：

```bash
make status
curl http://localhost:8080/health
```

## 5. 執行基本測試

啟動後可直接執行端到端測試驗證系統功能：

```bash
make test-e2e
```

亦可在 `tests/e2e` 目錄下執行快速測試腳本：

```bash
cd tests/e2e
python run_quick_test.py
```

上述腳本會檢查連線並產生測試報告【F:tests/e2e/QUICK_START.md†L1-L27】。

## 6. 衛星軌跡與換手模擬

系統啟動後，預設已包含兩顆衛星的軌道及 UE 範例。可透過以下 API 更新軌道或觸發換手：

```bash
# 更新衛星軌道資料
curl -X POST http://localhost:8080/api/v1/oneweb/constellation/initialize

# 啟動軌跡追蹤與換手邏輯
curl -X POST http://localhost:8080/api/v1/oneweb/orbital-tracking/start
```

SimWorld 前端會即時顯示衛星位置與 UE 連線狀態，並在換手時於畫面上標示。若要重新產生展示用的 UAV 與 Mesh 拓撲，可執行：

```bash
make init-demo-data
```

## 7. 關閉與清理

測試完成後可關閉所有服務並清理資源：

```bash
make down
```

若需完全移除映像與資料，可改用：

```bash
make clean
```

## 8. 復現論文實驗

1. 依上述步驟啟動系統並初始化軌道資料。
2. 以 API 操作或前端介面控制 UE 移動，觀察兩顆衛星間的換手過程。
3. 使用 `make test-performance` 蒐集延遲及吞吐量指標，與論文中數據對照。
4. 若需調整衛星預測與換手演算法，可修改 `netstack/netstack_api/services` 下相關服務模組並重新執行測試。

完成以上流程即可依照倉庫內實作復現論文所述的衛星換手加速機制。
