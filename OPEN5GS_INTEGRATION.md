# Open5GS 與 UERANSIM 整合指南

本文檔提供有關如何將 Open5GS 和 UERANSIM 整合到現有後端系統的指南。

## 背景

- **Open5GS**：開源的5G核心網路實現，提供完整的5G核心網功能，包括AMF、SMF、UPF等所有5G核心網元件。它處理用戶身份驗證、會話管理、策略控制等核心網功能。
- **UERANSIM**：開源的5G用戶設備(UE)和無線接入網路(RAN)模擬器，可以作為基站(gNodeB)連接到核心網，並模擬用戶手機(UE)連接到基站。

### Open5GS 與 UERANSIM 之間的關係

在5G網路架構中，Open5GS和UERANSIM扮演不同但互補的角色：

1. **Open5GS** 負責核心網功能：
   - 用戶認證與註冊（AMF、AUSF、UDM、UDR）
   - 會話管理（SMF）
   - 數據轉發（UPF）
   - 網絡功能註冊與發現（NRF）
   - 網絡切片選擇（NSSF）
   - 策略控制（PCF）

2. **UERANSIM** 負責接入網與終端功能：
   - 基站(gNodeB)模擬
   - 用戶設備(UE)模擬
   - 無線介面協議實現

這兩者共同形成了完整的5G網路端到端解決方案：核心網 + 無線接入網 + 終端設備。

## 整合步驟

1. **Docker Compose 整合**
   - 將 Open5GS 和 UERANSIM 的服務添加到主 docker-compose.yml
   - 創建單獨的網絡 (open5gs-net) 用於5G組件之間的通信
   - 同時保持與現有服務的網絡連接性

2. **API 集成**
   - 在後端添加 pymongo 依賴項，用於與 Open5GS 的 MongoDB 數據庫交互
   - 創建 Open5GSService 類，用於與 MongoDB 交互
   - 添加 API 路由，提供對5G用戶管理的訪問

3. **修改用戶註冊腳本**
   - 更新 register_subscriber.sh 腳本以適應新的 Docker Compose 環境

## 使用方法

### 啟動服務

```bash
docker compose up -d
```

這將啟動以下服務：
- 現有的後端和前端服務
- Open5GS 核心網路組件
- UERANSIM gNodeB 和 UE 模擬器
- 其他依賴的服務（PostgreSQL、Redis 等）

### 管理5G訂閱者

可以通過以下API端點管理5G訂閱者：

- 獲取所有訂閱者: `GET /api/v1/open5gs/subscribers`
- 獲取特定訂閱者: `GET /api/v1/open5gs/subscribers/{imsi}`
- 添加訂閱者: `POST /api/v1/open5gs/subscribers`
- 刪除訂閱者: `DELETE /api/v1/open5gs/subscribers/{imsi}`

## 測試流程

按照以下步驟測試整合是否成功並驗證5G網絡功能：

### 1. 驗證服務啟動

執行 `docker compose up` 啟動所有服務後，檢查日誌確認：
- MongoDB 數據庫已正確啟動
- 所有 Open5GS 服務 (AMF、SMF、UPF等) 已啟動
- UERANSIM gNodeB 和 UE 容器已啟動
- 您的 FastAPI 後端已正確連接到 MongoDB

### 2. 驗證訂閱者註冊

確認訂閱者（SIM卡用戶）是否正確註冊到系統：

```bash
# 查看註冊的訂閱者
docker exec open5gs-mongo mongo open5gs --eval "db.subscribers.find().pretty()"
```

應該能看到6個訂閱者記錄，IMSI從999700000000001到999700000000013，這些是由`register_subscriber.sh`腳本添加的。

### 3. 驗證API功能

測試後端API是否能與Open5GS通信：

```bash
# 獲取所有訂閱者
curl http://localhost:8000/api/v1/open5gs/subscribers

# 獲取特定訂閱者
curl http://localhost:8000/api/v1/open5gs/subscribers/999700000000001
```

### 4. 測試網絡連接

進入UE容器測試網絡連接：

```bash
# 進入UE容器
docker exec -it ntn-stack-ues1-1 /bin/bash

# 查看網絡接口
ip addr

# 測試連接
ping -I uesimtun0 8.8.8.8
traceroute -i uesimtun0 google.com
```

如果以上步驟都成功，則表示：
1. UE成功連接到gNodeB
2. gNodeB成功連接到核心網AMF
3. UE通過了身份驗證
4. SMF和UPF正確配置了數據路徑
5. 5G網絡連接已建立並能訪問互聯網

## 測試成功的意義

成功整合與測試表明：

1. **系統共存**：原有的後端系統與Open5GS/UERANSIM可以在同一個Docker環境中共存，不會互相衝突。

2. **網絡互通**：所有服務能在Docker網絡中正確通信，特別是後端可以訪問Open5GS的MongoDB。

3. **API整合**：FastAPI後端能夠查詢和管理Open5GS中的訂閱者數據。

4. **功能完整**：完整的5G端到端功能可用，從UE到互聯網的數據路徑已建立。

5. **單一管理**：所有組件可以通過一個命令(`docker compose up`)啟動和管理。

## 網絡架構

```
+------------------+     +-------------------+     +------------------+
| 前端 (React)     |---->| 後端 (FastAPI)    |---->| PostgreSQL/Redis |
+------------------+     +-------------------+     +------------------+
                                |
                                |
                                v
+------------------+     +-------------------+     +------------------+
| UERANSIM (UEs)   |---->| UERANSIM (gNodeB) |---->| Open5GS (核心網) |
+------------------+     +-------------------+     +------------------+
```

## 進階測試和應用

成功整合後，可以進行以下進階測試與應用：

1. **透過API動態管理訂閱者**：使用API添加、刪除或修改訂閱者，測試動態管理功能。

2. **模擬多用戶場景**：通過多個UE同時連接，分析網絡行為和性能。

3. **網絡切片測試**：配置不同的網絡切片(Network Slices)並測試不同服務質量(QoS)的數據流。

4. **與衛星通信系統集成**：結合衛星通信模擬與5G網絡，研究非地面網絡(NTN)場景。

5. **開發網絡監控界面**：使用前端展示5G網絡狀態、連接的設備和網絡性能指標。

## 故障排除

1. **MongoDB 連接問題**
   - 確保 MongoDB 服務處於運行狀態
   - 檢查連接 URI: `mongodb://mongo:27017/open5gs`
   - 檢查MongoDB日誌：`docker logs open5gs-mongo`

2. **gNodeB 連接問題**
   - 確保 AMF 服務器已啟動並運行
   - 檢查 gNodeB 的 TAC, MCC, MNC 設置
   - 查看gNodeB日誌：`docker logs gnb1`

3. **UE 連接問題**
   - 確保訂閱者已在 Open5GS 中註冊
   - 檢查 UE 的 IMSI, Key, OPC 與註冊的值匹配
   - 檢查UE日誌：`docker logs ntn-stack-ues1-1`

4. **網路連接問題**
   - 確認UPF的NAT功能正常工作
   - 檢查容器網絡設置：`docker network inspect open5gs-net`
   - 確認UE獲取了正確的IP地址：`docker exec -it ntn-stack-ues1-1 ip addr`

## 參考資料

- [Open5GS 文檔](https://open5gs.org/open5gs/docs/)
- [UERANSIM 文檔](https://github.com/aligungr/UERANSIM/wiki)
- [5G網絡架構](https://www.3gpp.org/technologies/5g-system-overview) 