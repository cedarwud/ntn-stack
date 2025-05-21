# Open5GS 與 UERANSIM 整合指南

本文檔提供有關如何將 Open5GS 和 UERANSIM 整合到現有後端系統的指南，以及 MongoDB 訂閱者管理的最佳實踐。

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

## 檔案結構

專案中與 Open5GS 相關的檔案組織如下：

```
ntn-stack/
├── scripts/
│   ├── mongo_init.js          # MongoDB 初始化腳本，添加訂閱者
│   ├── register_subscriber.sh # 使用 open5gs-dbctl 註冊訂閱者的腳本
│   └── open5gs-dbctl          # Open5GS 的資料庫管理工具
├── config/
│   ├── open5gs/               # Open5GS 配置檔案目錄
│   └── ueransim/              # UERANSIM 配置檔案目錄
└── backend/
    └── app/
        ├── api/
        │   └── open5gs.py     # Open5GS API 端點定義
        ├── core/
        │   └── open5gs_config.py # Open5GS 配置設定
        └── services/
            └── open5gs_service.py # Open5GS 服務實現
```

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

## 訂閱者管理

### 訂閱者初始化

系統啟動時，MongoDB 容器會自動執行 `/docker-entrypoint-initdb.d/mongo_init.js` 腳本初始化訂閱者數據。這個腳本會：

1. 清空現有訂閱者表
2. 添加預設的 6 個訂閱者
3. 輸出訂閱者數量和列表

訂閱者 IMSI 列表：
- 999700000000001
- 999700000000002
- 999700000000003
- 999700000000011
- 999700000000012
- 999700000000013

### 訂閱者結構

每個訂閱者的數據結構包含以下關鍵字段：

```json
{
  "imsi": "999700000000001",
  "subscribed_rau_tau_timer": 12,
  "network_access_mode": 2,
  "subscriber_status": 0,
  "access_restriction_data": 32,
  "security": {
    "k": "465B5CE8B199B49FAA5F0A2EE238A6BC",
    "opc": "E8ED289DEBA952E4283B54E88E6183CA",
    "amf": "8000",
    "op": null,
    "sqn": Long("97")
  },
  "ambr": {
    "uplink": { "value": 1, "unit": 3 },
    "downlink": { "value": 1, "unit": 3 }
  },
  "slice": [
    {
      "sst": 1,
      "default_indicator": true,
      "session": [
        {
          "name": "internet",
          "type": 3,
          "qos": {
            "index": 9,
            "arp": {
              "priority_level": 8,
              "pre_emption_capability": 1,
              "pre_emption_vulnerability": 1
            }
          },
          "ambr": {
            "uplink": { "value": 1, "unit": 3 },
            "downlink": { "value": 1, "unit": 3 }
          }
        }
      ]
    }
  ],
  "imeisv": "4370816125816151"
}
```

### 訂閱者管理 API

後端提供了以下 API 端點來管理訂閱者：

- `GET /api/v1/open5gs/subscribers` - 獲取所有訂閱者
- `GET /api/v1/open5gs/subscribers/{imsi}` - 獲取特定訂閱者
- `POST /api/v1/open5gs/subscribers` - 添加新訂閱者
- `DELETE /api/v1/open5gs/subscribers/{imsi}` - 刪除訂閱者

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

可以通過以下方式管理5G訂閱者：

#### 1. 使用API

```bash
# 獲取所有訂閱者
curl http://localhost:8000/api/v1/open5gs/subscribers

# 獲取特定訂閱者
curl http://localhost:8000/api/v1/open5gs/subscribers/999700000000001
```

#### 2. 直接操作MongoDB

```bash
# 查看所有訂閱者
docker exec -it open5gs-mongo mongosh open5gs --eval "db.subscribers.find().pretty()"

# 查看訂閱者數量
docker exec -it open5gs-mongo mongosh open5gs --eval "db.subscribers.count()"
```

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
docker exec -it open5gs-mongo mongosh open5gs --eval "db.subscribers.find().pretty()"
```

應該能看到6個訂閱者記錄，IMSI從999700000000001到999700000000013，這些是由`mongo_init.js`腳本添加的。

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

## 測試結果範例

### 1. MongoDB中的訂閱者

查詢MongoDB中的訂閱者資訊:

```
docker exec -it open5gs-mongo mongosh open5gs --eval "db.subscribers.find().pretty()"
```

結果會看到6個訂閱者，每個訂閱者包含完整的配置資訊，例如：

```json
{
  "_id": ObjectId('682d5174827520cd3ad861e0'),
  "imsi": "999700000000001",
  "subscribed_rau_tau_timer": 12,
  "network_access_mode": 2,
  "subscriber_status": 0,
  "access_restriction_data": 32,
  "security": {
    "k": "465B5CE8B199B49FAA5F0A2EE238A6BC",
    "opc": "E8ED289DEBA952E4283B54E88E6183CA",
    "amf": "8000",
    "op": null,
    "sqn": Long("97")
  },
  "ambr": { "uplink": { "value": 1, "unit": 3 }, "downlink": { "value": 1, "unit": 3 } },
  "slice": [
    {
      "sst": 1,
      "default_indicator": true,
      "session": [
        {
          "name": "internet",
          "type": 3,
          "qos": {
            "index": 9,
            "arp": {
              "priority_level": 8,
              "pre_emption_capability": 1,
              "pre_emption_vulnerability": 1
            }
          },
          "ambr": {
            "uplink": { "value": 1, "unit": 3 },
            "downlink": { "value": 1, "unit": 3 }
          }
        }
      ]
    }
  ],
  "imeisv": "4370816125816151"
}
```

### 2. API查詢結果

通過API查詢訂閱者:

```
curl http://localhost:8000/api/v1/open5gs/subscribers
```

將返回所有訂閱者的JSON資料。

### 3. UE網絡接口

進入UE容器查看網絡接口:

```
docker exec -it ntn-stack-ues1-1 /bin/bash
ip addr
```

可以看到多個網絡接口，包括:
- `lo`: 本地回環
- `eth0`: 容器網絡接口
- `uesimtun0`, `uesimtun1`, `uesimtun2`: 虛擬UE網絡接口，用於5G連接

每個UE接口都有獲得IP地址，如:
```
3: uesimtun0: <POINTOPOINT,PROMISC,NOTRAILERS,UP,LOWER_UP> mtu 1400 qdisc fq_codel state UNKNOWN group default qlen 500
    link/none
    inet 10.45.0.2/32 scope global uesimtun0
```

### 4. 網絡連接測試

通過UE接口測試網絡連接:

```
ping -I uesimtun0 8.8.8.8
```

結果顯示可以成功ping通:
```
PING 8.8.8.8 (8.8.8.8) from 10.45.0.2 uesimtun0: 56(84) bytes of data.
64 bytes from 8.8.8.8: icmp_seq=1 ttl=114 time=7.62 ms
64 bytes from 8.8.8.8: icmp_seq=2 ttl=114 time=6.89 ms
64 bytes from 8.8.8.8: icmp_seq=3 ttl=114 time=7.02 ms
64 bytes from 8.8.8.8: icmp_seq=4 ttl=114 time=6.49 ms
64 bytes from 8.8.8.8: icmp_seq=5 ttl=114 time=7.06 ms
--- 8.8.8.8 ping statistics ---
5 packets transmitted, 5 received, 0% packet loss, time 4006ms
rtt min/avg/max/mdev = 6.489/7.016/7.617/0.362 ms
```

traceroute測試:
```
traceroute -i uesimtun0 google.com
```

可以看到完整的網絡路由路徑，證明5G網絡接口可以成功訪問互聯網。

## 故障排除

### 問題：MongoDB 中看不到訂閱者

如果在 MongoDB 中看不到訂閱者數據，可能是以下原因：

1. MongoDB 初始化腳本未能正確執行
2. 訂閱者初始化容器未正確運行

**解決方案**：
1. 確認 MongoDB 容器已正確掛載初始化腳本：
   ```yaml
   volumes:
     - ./scripts/mongo_init.js:/docker-entrypoint-initdb.d/mongo_init.js
   ```

2. 手動執行初始化腳本：
   ```bash
   docker cp scripts/mongo_init.js open5gs-mongo:/tmp/
   docker exec -it open5gs-mongo mongosh --file /tmp/mongo_init.js
   ```

3. 查看訂閱者數量：
   ```bash
   docker exec -it open5gs-mongo mongosh open5gs --eval "db.subscribers.find().count()"
   ```

### 問題：訂閱者API返回不正確的數據

如果API返回的訂閱者數據與預期不符，可能是以下原因：

1. 後端服務未正確連接到 MongoDB
2. MongoDB中的數據有問題

**解決方案**：
1. 檢查後端配置文件中的 MongoDB 連接 URI
2. 比較API返回的數據與直接在 MongoDB 中查詢的數據

### 問題：gNodeB 連接問題

1. 確保 AMF 服務器已啟動並運行
2. 檢查 gNodeB 的 TAC, MCC, MNC 設置
3. 查看gNodeB日誌：`docker logs gnb1`

### 問題：UE 連接問題

1. 確保訂閱者已在 Open5GS 中註冊
2. 檢查 UE 的 IMSI, Key, OPC 與註冊的值匹配
3. 檢查UE日誌：`docker logs ntn-stack-ues1-1`

### 問題：網路連接問題

1. 確認UPF的NAT功能正常工作
2. 檢查容器網絡設置：`docker network inspect open5gs-net`
3. 確認UE獲取了正確的IP地址：`docker exec -it ntn-stack-ues1-1 ip addr`

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

## 測試成功的意義

成功整合與測試表明：

1. **系統共存**：原有的後端系統與Open5GS/UERANSIM可以在同一個Docker環境中共存，不會互相衝突。

2. **網絡互通**：所有服務能在Docker網絡中正確通信，特別是後端可以訪問Open5GS的MongoDB。

3. **API整合**：FastAPI後端能夠查詢和管理Open5GS中的訂閱者數據。

4. **功能完整**：完整的5G端到端功能可用，從UE到互聯網的數據路徑已建立。

5. **單一管理**：所有組件可以通過一個命令(`docker compose up`)啟動和管理。

## 參考資料

- [Open5GS 文檔](https://open5gs.org/open5gs/docs/)
- [UERANSIM 文檔](https://github.com/aligungr/UERANSIM/wiki)
- [5G網絡架構](https://www.3gpp.org/technologies/5g-system-overview) 