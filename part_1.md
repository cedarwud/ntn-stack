# Open5GS 與 UERANSIM 整合、測試與系統擴展優化計劃

## 一、基礎5G網絡功能擴展

根據專案現況評估，我們已成功整合Open5GS與UERANSIM，建立了基本的5G網絡連接框架。系統優化和NTN場景適配是下一階段關鍵任務。以下是基於現有檔案結構和系統狀態的優先任務：

### 1. Open5GS 核心網優化配置 (優先級：高)

**目的**：優化Open5GS配置以支持NTN(非地面網絡)通信場景，重點關注信令時延、會話管理和QoS。

**專案目標關聯**：
本項目與「完成一套可部署於30 km營級作戰範圍的Two-Tier BLOS通訊系統」直接相關。衛星通信場景與標準地面5G網絡有根本差異：單向延遲達20-50毫秒（地面僅1-5毫秒）、信號強度和頻率偏移變化劇烈、覆蓋範圍和切換速度差異巨大。

**方法**：
- 修改Open5GS配置文件，調整AMF、SMF和UPF參數
- 實現自定義QoS策略控制，支持軍事應用中不同優先級任務
- 配置網絡切片支持多種業務場景，如控制信令和數據傳輸分離

**涉及檔案與資源**：

| 修改內容 | 檔案路徑 | 修改内容說明 |
|---------|----------|------------|
| AMF配置 | `/config/open5gs/amf.yaml`（需創建） | 增加N1/N2超時，提高重傳次數 |
| SMF配置 | `/config/open5gs/smf.yaml`（已存在） | 優化PDU會話超時參數 |
| PCF配置 | `/config/open5gs/pcf.yaml`（需創建） | 添加自定義QoS策略 |
| NSSF配置 | `/config/open5gs/nssf.yaml`（需創建） | 配置網絡切片 |
| 訂閱者配置 | `/scripts/mongo_init.js`（已存在） | 更新QoS參數和切片支持 |
| 服務實現 | `/backend/app/services/open5gs_service.py`（需創建） | 實現QoS管理API |
| Docker配置 | `/docker-compose.yml`（已存在） | 更新容器掛載配置文件 |
| 自動化腳本 | `/scripts/ntn_config_switcher.sh`（需創建） | 實現配置自動切換 |
| 測試腳本 | `/scripts/ntn_simulator.sh`（需創建） | 模擬NTN通信環境 |

**具體實施步驟**：

1. **高延遲容錯配置實現** (立即執行)
   - 創建缺失的配置文件：
     ```bash
     # 創建AMF配置文件
     cp /opt/open5gs/etc/open5gs/amf.yaml.in config/open5gs/amf.yaml
     # 創建PCF配置文件 
     cp /opt/open5gs/etc/open5gs/pcf.yaml.in config/open5gs/pcf.yaml
     # 創建NSSF配置文件
     cp /opt/open5gs/etc/open5gs/nssf.yaml.in config/open5gs/nssf.yaml
     ```
   - 修改AMF和SMF配置增加超時參數:
     - AMF: `t3513.value: 20000 # 毫秒，原6秒`
     - AMF: `t3513.max_count: 8 # 原4次`
     - AMF: `t3522.value: 15000 # 毫秒，原6秒`
     - SMF: `t3525.value: 18000 # 毫秒，原6秒`
     - SMF: `t3585.value: 15000 # 毫秒，原默認值`
   - 更新docker-compose.yml中的配置文件掛載:
     ```yaml
     amf:
       volumes:
         - ./config/open5gs/amf.yaml:/opt/open5gs/etc/open5gs/amf.yaml
     ```

2. **QoS策略和網絡切片實現** (第二階段)
   - 修改PCF配置實現差異化服務:
     ```yaml
     # PCF QoS配置
     pcrf:
       policy:
         - qos:
             index: 6  # 關鍵控制指令
             arp:
               priority_level: 1
               pre_emption_capability: 1
             mbr:
               downlink: 50000000  # 50Mbps保證帶寬
               uplink: 20000000    # 20Mbps上行
     ```
   - 建立Open5GS服務层:
     ```bash
     mkdir -p backend/app/services
     touch backend/app/services/__init__.py
     touch backend/app/services/open5gs_service.py
     ```
   - 實現QoS管理API到`open5gs_service.py`
   - 更新mongo_init.js添加多切片支持:
     ```javascript
     // 添加控制平面切片
     subscriber.slice.push({
       sst: 1,
       sd: "000001",
       default_indicator: false,
       session: [...]
     });
     ```

3. **配置自動化與測試框架** (第三階段)
   - 創建配置切換腳本:
     ```bash
     touch scripts/ntn_config_switcher.sh
     chmod +x scripts/ntn_config_switcher.sh
     ```
   - 實現NTN環境模擬腳本:
     ```bash
     touch scripts/ntn_simulator.sh
     chmod +x scripts/ntn_simulator.sh
     ```
   - 創建配置模板目錄:
     ```bash
     mkdir -p config/templates/satellite
     mkdir -p config/templates/ground
     ```

**驗證與測試方法**：
1. 建立執行測試的Docker容器命令集:
   ```bash
   # 在UE和gNodeB之間添加延遲和丟包模擬衛星環境
   scripts/ntn_simulator.sh --delay=25 --jitter=10 --loss=2
   
   # 測試連接穩定性
   docker exec -it ntn-stack-ues1-1 ping -I uesimtun0 8.8.8.8 -c 20
   
   # 監控連接狀態
   docker exec -it ntn-stack-ues1-1 nr-cli imsi-999700000000001 -e "ps-info"
   ```

2. 建立性能比較框架:
   ```bash
   # 創建性能測試腳本
   touch scripts/performance_test.sh
   chmod +x scripts/performance_test.sh
   ```

**執行時間表**：
- 第1週: 完成配置文件創建和基本參數調整
- 第2週: 實現QoS策略和網絡切片配置
- 第3週: 開發自動化配置和測試框架
- 第4週: 全面測試和參數優化

### 2. UERANSIM動態配置機制 (優先級：中)

**目的**：實現UERANSIM的動態配置機制，使其能夠自動適應衛星軌道變化和UAV移動，實現即時網路參數調整。

**專案目標關聯**：
專案核心是「UAV群作為行動終端(NTN UE)」與「LEO衛星作為空中gNodeB/NTN基地台」的通信。這兩個角色都具有高度移動性，需要動態調整網絡配置以適應位置變化。

**涉及檔案與資源**：

| 修改內容 | 檔案路徑 | 修改内容說明 |
|---------|----------|------------|
| 配置模板 | `/config/ueransim/templates/` （需創建） | 建立gNodeB和UE配置模板 |
| FastAPI端點 | `/backend/app/api/v1/ueransim.py` （需創建） | 實現配置生成接口 |
| 配置服務 | `/backend/app/services/ueransim_service.py` （需創建） | 處理配置邏輯 |
| 模板解析 | `/backend/app/core/template.py` （需創建） | Jinja2模板處理 |
| 同步機制 | `/scripts/apply_config.sh` （需創建） | 將生成的配置應用到容器 |
| Docker配置 | `/docker-compose.yml` （已存在） | 掛載配置目錄 |
| API文檔 | `/backend/app/api/v1/ueransim_api.md` （需創建） | API使用文檔 |

**具體實施步驟**：

1. **分析UERANSIM配置結構** (規劃階段)
   - 分析現有配置文件結構：`config/ueransim/gnb1.yaml`, `gnb2.yaml`
   - 識別需要動態調整的關鍵參數，如位置坐標、發射功率、切換參數等
   - 建立參數與位置/信號強度的映射關係

2. **建立配置模板系統** (實現階段)
   - 創建目錄結構：
     ```bash
     mkdir -p config/ueransim/templates
     mkdir -p config/ueransim/templates/gnb
     mkdir -p config/ueransim/templates/ue
     ```
   - 將現有配置轉換為Jinja2模板，替換關鍵參數為變量
   - 實現模板系統到後端服務

3. **開發FastAPI配置生成接口** (實現階段)
   - 在`backend/app/api/v1/`目錄下創建ueransim.py:
     - 實現`POST /api/v1/ueransim/config/generate`接口
     - 支持批量生成多個gNodeB/UE配置
     - 添加配置驗證邏輯
   - 開發配置分發機制，確保生成的配置能即時應用

### 3. 5G網絡監控系統整合 (優先級：中高)

**目的**：實現對5G網絡各組件的全方位實時監控，提供關鍵性能指標(KPI)的收集、存儲和可視化，建立完整可觀測性體系。

**專案目標關聯**：
專案明確要求「於實驗室與戶外驗測達到SINR、吞吐、干擾避讓等量化指標」，監控系統是量化評估的重要工具。

**涉及檔案與資源**：

| 修改內容 | 檔案路徑 | 修改内容說明 |
|---------|----------|------------|
| Prometheus配置 | `/config/prometheus/prometheus.yml` （需創建） | 定義監控目標和刮擦頻率 |
| Grafana配置 | `/config/grafana/provisioning/` （需創建） | 預配置dashboards和數據源 |
| Open5GS指標配置 | `/config/open5gs/*.yaml` （部分已存在） | 啟用指標導出功能 |
| Loki配置 | `/config/loki/local-config.yaml` （需創建） | 配置日誌收集 |
| Promtail配置 | `/config/promtail/config.yml` （需創建） | 定義日誌抓取和標記 |
| Docker配置 | `/docker-compose.yml` （已存在） | 添加監控服務和卷掛載 |
| 指標收集腳本 | `/scripts/metrics_exporter.py` （需創建） | 從UERANSIM收集指標 |
| 儀表板模板 | `/config/grafana/dashboards/` （需創建） | 5G專用儀表板JSON定義 |

**具體實施步驟**：

1. **擴展Docker Compose配置** (實現階段)
   - 在docker-compose.yml添加監控服務:
     ```yaml
     prometheus:
       image: prom/prometheus:latest
       volumes:
         - ./config/prometheus:/etc/prometheus
         - prometheus_data:/prometheus
       networks:
         - sionna-net
         - open5gs-net
       ports:
         - "9090:9090"
         
     grafana:
       image: grafana/grafana:latest
       volumes:
         - ./config/grafana:/etc/grafana
         - grafana_data:/var/lib/grafana
       networks:
         - sionna-net
       ports:
         - "3000:3000"
     
     loki:
       image: grafana/loki:latest
       volumes:
         - ./config/loki:/etc/loki
         - loki_data:/loki
       ports:
         - "3100:3100"
       networks:
         - sionna-net
     ```
   - 添加數據卷定義:
     ```yaml
     volumes:
       prometheus_data:
       grafana_data:
       loki_data:
     ```

2. **配置Prometheus和Open5GS指標導出** (實現階段)
   - 創建Prometheus配置:
     ```bash
     mkdir -p config/prometheus
     touch config/prometheus/prometheus.yml
     ```
   - 修改Open5GS配置文件啟用指標導出:
     ```yaml
     # 在amf.yaml中添加
     metrics:
       addr: 0.0.0.0
       port: 9090
     ```

3. **設置Grafana儀表板** (實現階段)
   - 配置Grafana自動加載儀表板:
     ```bash
     mkdir -p config/grafana/provisioning/datasources
     mkdir -p config/grafana/provisioning/dashboards
     mkdir -p config/grafana/dashboards
     ```
   - 創建5G專用儀表板JSON定義
     - 連接數和成功率儀表板
     - 信令時延監控面板
     - 吞吐量性能圖表
     - PDU會話狀態監控

### 2. UERANSIM動態配置機制

**目的**：實現UERANSIM的動態配置機制，使其能夠自動適應衛星軌道變化和UAV移動，實現即時網路參數調整，確保通信品質和連續性。

**專案目標關聯**：
專案核心是「UAV群作為行動終端(NTN UE)」與「LEO衛星作為空中gNodeB/NTN基地台」的通信。這兩個角色都具有高度移動性：OneWeb衛星軌道週期約100分鐘，位置持續變化；UAV按任務需求不斷移動。UERANSIM原本設計為靜態配置模擬器，無法反映這種動態性，與項目目標中「真實場域與數位分身同步展示」的要求不符。

**方法**：
- 開發FastAPI接口動態生成UERANSIM配置，實現GPT.md中提到的「FastAPI產生動態UERANSIM cfg (gNodeB=衛星, UE=UAV)」
- 實現配置模板系統，支持快速替換關鍵參數
- 建立配置參數與衛星/UAV位置的映射關係，實現物理世界移動到網絡配置的自動轉換
- 開發配置熱更新機制，實現不中斷服務的參數調整
- 設計配置驗證系統，防止無效配置導致服務中斷

**步驟**：
1. **分析UERANSIM配置結構與參數**：
   - 梳理gNodeB配置文件的關鍵參數，尤其是位置、頻率和發射功率相關參數
   - 識別UE配置中需要動態調整的參數，如接收增益、干擾閾值、切換參數
   - 建立參數優先級分類，區分靜態參數、準靜態參數和高頻變動參數
   - 研究UERANSIM配置重載機制，確定最佳的配置更新方式
   - 記錄配置參數間的依賴關係，避免不一致的配置組合

2. **設計配置模板系統**：
   - 開發Jinja2基於的配置模板格式，使用變量佔位符表示動態參數
   - 建立分層模板結構，支持基本配置、場景特定配置和實例特定配置
   - 實現模板版本控制機制，確保配置變更可追踪和回滾
   - 設計模板繼承系統，允許針對特定場景定制部分參數而不影響通用配置
   - 實現配置欄位驗證規則，確保生成的配置符合UERANSIM要求
   - 建立模板測試框架，驗證模板可以生成正確的配置文件
   - 開發模板管理API，支持模板的創建、更新、版本切換和回滾

3. **開發位置-配置映射算法**：
   - 設計座標轉換函數，將ECEF/ENU座標轉換為通信參數
   - 實現距離計算模塊，基於衛星/UAV相對位置計算通信距離
   - 開發角度計算組件，確定天線指向和波束方向
   - 建立功率映射模型，根據距離和角度調整發射/接收功率
   - 實現頻率調整算法，考慮多普勒效應的影響
   - 設計參數平滑化機制，避免因位置微小變化導致頻繁配置調整
   - 開發預測模型，基於軌道預測提前生成配置，減少延遲影響

4. **實現FastAPI配置生成服務**：
   - 開發`/api/v1/ueransim/config/gnb/generate`端點，生成衛星gNodeB配置
   - 實現`/api/v1/ueransim/config/ue/generate`端點，生成UAV UE配置
   - 添加`/api/v1/ueransim/config/validate`端點，提供配置驗證功能
   - 設計`/api/v1/ueransim/config/history`端點，支持查詢和恢復歷史配置
   - 實現參數批量更新API，減少配置更新的網絡開銷
   - 添加配置差異比較功能，自動識別變更的參數
   - 開發配置生成事件webhook，支持外部系統感知配置變更
   - 實現配置生成性能監控，確保毫秒級的響應時間

5. **開發配置同步與熱更新機制**：
   - 設計配置分發系統，將新配置推送到運行中的UERANSIM實例
   - 實現配置變更探測器，監控並報告配置應用狀態
   - 開發無縫重載機制，實現不中斷服務的配置更新
   - 建立配置版本控制系統，自動備份和管理配置歷史
   - 實現緊急回滾功能，在配置問題時快速恢復到已知良好狀態
   - 設計階段性配置應用策略，先應用非關鍵參數再更新關鍵參數
   - 開發配置同步狀態儀表板，可視化整個系統的配置一致性

6. **建立配置性能與效果監測系統**：
   - 開發配置性能評估指標，量化配置變更的效果
   - 設計A/B測試機制，比較不同配置策略的效果
   - 實現配置應用延遲監測，確保及時生效
   - 建立配置-性能關聯分析工具，識別最有影響力的參數
   - 開發自動化配置優化建議系統，基於性能數據提出調整方案
   - 設計配置審計和合規檢查機制，確保所有變更都符合技術標準
   - 實現配置變更的影響預測模型，評估調整的潛在效果

7. **性能優化與擴展能力**：
   - 實現配置生成的並行處理能力，支持同時處理多個UAV/衛星的配置請求
   - 開發配置緩存系統，避免重複計算相似配置
   - 優化配置差異計算算法，只更新發生變化的參數
   - 實現配置批處理機制，減少系統資源消耗
   - 設計配置模板預編譯機制，提高生成速度
   - 開發配置壓縮技術，減少網絡傳輸量
   - 實現基於優先級的配置更新排程，確保關鍵節點優先處理

**預期成果**：
- 一套完整的動態配置生成與管理系統，能夠在毫秒級響應時間內生成新配置並應用到UERANSIM實例
- 支持連續、平滑的位置更新，實現物理世界與網絡模型的精確同步
- 實現不同場景下的自適應配置模板，支持多種通信場景和應用需求
- 具備完善的監控、驗證和回滾機制，確保系統穩定性和可靠性
- 提供開放的API接口，支持與其他系統的集成和擴展
- 實現配置生成與應用的全流程自動化，無需人工干預

**階段性指標**：
- 配置生成延遲：< 10ms
- 配置應用延遲：< 100ms
- 配置錯誤率：< 0.1%
- 支持衛星位置更新頻率：每秒10次
- 支持同時配置的UAV數量：≥ 50個
- 配置模板種類：≥ 10種不同場景

**階段性意義與必要性**：
此機制是連接物理世界（衛星/UAV位置）與網絡模型的關鍵橋樑。若不實現此功能，系統將無法模擬移動節點間的動態連接變化，也無法支持目標中提到的「透過AI-RAN/抗干擾模組動態避干擾」，因為抗干擾策略需要實時調整無線參數。這一步驟使整個系統從靜態模擬轉變為動態模擬，大幅提升了模型的真實性和實用價值。動態配置機制也是實現衛星-UAV通信系統數位孿生的基礎設施，確保虛擬模型能夠精確反映物理世界的變化，支持更準確的預測和優化。

### 3. 5G網絡監控系統整合

**目的**：實現對5G網絡各組件的全方位實時監控，提供NTN場景特有的關鍵性能指標(KPI)可視化與分析能力，建立完整的可觀測性體系，支持性能評估、問題診斷和系統優化。

**專案目標關聯**：
專案明確要求「於實驗室與戶外驗測達到SINR、吞吐、干擾避讓等量化指標」，而GPT.md的技術棧中也明確提出使用「Prometheus + Grafana收集Sionna GPU使用率、5G KPI」及「Loki收集UERANSIM/Open5GS log」。缺乏監控系統將使性能評估、問題診斷和系統驗證變得極其困難，尤其是在30km營級作戰範圍內的複雜通信場景。高延遲、頻繁切換和干擾環境下的系統表現需要精確量化，以確保達到軍用級通信可靠性標準。

**方法**：
- 整合Prometheus和Grafana收集5G核心網和RAN的標準與自定義指標
- 實現Loki日誌聚合系統，集中管理分散式組件的日誌並支持複雜查詢
- 開發NTN特有指標採集器，關注衛星通信場景特有的性能參數
- 設計多層次儀表板體系，從總覽到詳細診斷提供完整監控視圖
- 建立指標關聯分析引擎，實現故障根因快速定位
- 實現智能告警系統，支持多條件觸發和自動恢復檢測
- 開發績效基準測試模組，提供標準化性能評估方法

**步驟**：
1. **建立核心指標採集架構**：
   - 分析Open5GS源碼，識別關鍵性能指標點和導出方式
   - 為Open5GS各核心組件(AMF/SMF/UPF等)實現Prometheus格式指標輸出
   - 自定義關鍵指標，包括NTN特有的衛星鏈路狀態、連接切換和恢復時間
   - 開發多種指標類型支持：計數器(counter)、測量值(gauge)、直方圖(histogram)和摘要(summary)
   - 實現指標標籤(label)體系，支持多維度數據分析
   - 建立指標元數據管理，包含詳細描述和正常範圍定義

2. **開發UERANSIM指標採集擴展**：
   - 分析UERANSIM代碼結構，識別關鍵監控點
   - 開發非侵入式監控插件，避免修改核心代碼
   - 實現無線介面關鍵指標採集：SINR、RSRP、RSRQ、CQI等
   - 添加信令面性能監控：RRC建立時間、註冊成功率、服務請求延遲
   - 開發用戶面性能指標：吞吐量、時延、丟包率、重傳率
   - 實現多普勒效應和頻偏監測能力，特別適用於衛星通信
   - 設計輕量級數據導出機制，最小化監控對系統性能的影響

3. **配置高可用監控後端**：
   - 部署Prometheus服務器集群，實現監控系統的高可用性
   - 配置階層式聯邦架構，支持大規模分布式監控
   - 優化存儲策略，實現長期趨勢分析與短期高精度數據平衡
   - 配置智能採樣頻率管理，依據指標重要性和變化速率調整
   - 實現資源使用效率監控，避免監控系統本身成為性能瓶頸
   - 設置安全訪問控制，確保監控數據安全性
   - 開發監控系統健康檢查機制，確保監控服務的可靠性

4. **實現日誌集中管理與分析**：
   - 部署Loki日誌聚合系統，集中收集所有組件日誌
   - 設計日誌標籤體系，支持多維度過濾和查詢
   - 配置日誌級別動態調整功能，根據診斷需求靈活控制詳細程度
   - 實現結構化日誌解析，提取關鍵事件和錯誤模式
   - 開發日誌與指標關聯分析能力，支持根因分析
   - 建立日誌保留策略，平衡存儲需求和數據可用性
   - 添加敏感信息保護機制，確保合規性和安全性

5. **設計多層次可視化儀表板**：
   - 在Grafana中建立總覽儀表板，提供系統整體健康狀態視圖
   - 開發核心網專用儀表板，監控AMF、SMF、UPF等組件性能
   - 設計RAN性能儀表板，聚焦gNodeB和UE連接狀況
   - 創建無線性能儀表板，專注SINR、干擾和覆蓋分析
   - 實現用戶體驗儀表板，從業務角度評估系統表現
   - 開發故障診斷專用視圖，加速問題排查
   - 建立趨勢分析視圖，支持長期性能評估和容量規劃
   - 實現多設備自適應顯示，支持從大螢幕到移動裝置的監控需求

6. **配置智能告警系統**：
   - 設計分層告警架構，區分嚴重性和緊急程度
   - 實現複合條件告警，減少告警風暴和誤報
   - 開發告警關聯分析，識別根因和次生告警
   - 配置自動恢復檢測，減少人工干預需求
   - 實現告警抑制和分組功能，提高告警可讀性
   - 開發多渠道通知系統，支持電子郵件、訊息和API回調
   - 建立告警響應工作流，明確處理流程和責任分工
   - 設計告警歷史分析工具，持續改進監控效果

7. **開發性能基準測試與評估系統**：
   - 設計標準化性能測試流程和腳本
   - 實現自動化測試框架，支持定期基準測試執行
   - 開發測試結果自動分析工具，計算關鍵績效指標
   - 建立性能基準數據庫，支持歷史比較和趨勢分析
   - 實現測試報告自動生成功能，提供標準化文檔
   - 設計A/B測試支持，評估配置變更的效果
   - 開發模擬負載生成器，測試系統在各種條件下的表現

**預期成果**：
- 一套完整的NTN通信監控系統，覆蓋從底層無線介面到上層應用服務的全棧指標
- 多層次儀表板集，提供從總覽到詳細診斷的全方位視圖
- 智能告警系統，能夠準確識別異常並支持快速響應
- 完整的日誌分析系統，支持複雜事件關聯和根因分析
- 標準化性能測試框架，提供一致的評估方法和可比較的結果
- 監控API，支持與其他系統集成和數據共享
- 詳細的性能基準報告，作為系統優化和驗收的依據

**階段性指標**：
- 指標收集覆蓋率：≥ 95% 的系統關鍵點
- 指標採集頻率：高優先級指標 ≤ 5秒，一般指標 ≤ 15秒
- 告警檢測延遲：≤ 10秒
- 儀表板刷新時間：≤ 5秒
- 歷史數據查詢性能：≤ 3秒（30天數據範圍內）
- 監控系統可用性：≥ 99.9%
- 監控數據存儲時長：高精度數據 ≥ 7天，聚合數據 ≥ 365天

**階段性意義與必要性**：
監控系統不僅是管理工具，也是驗證系統是否達到性能目標的關鍵手段。它直接支持GPT.md中提到的「M-12 (116 Q3): 戶外5 km驗測 + KPI報告」里程碑。此外，監控數據是AI-RAN決策的重要輸入，沒有監控就無法實現「干擾避讓」功能。在實際部署前，這套監控系統將幫助解決各種性能和穩定性問題，大幅降低現場測試的風險和成本。對於軍用通信系統，可觀測性尤為重要，它確保系統的可靠性和可維護性，支持在複雜環境中快速識別和解決問題。同時，監控系統產生的性能數據也將成為系統優化的科學依據，推動系統持續演進和改進。從戰術角度看，實時性能監控還能支持通信資源的動態調配，確保在戰場環境中維持最佳通信效果。

## 整合路線圖與優先順序

綜合現有專案資源與技術需求，基礎5G網絡功能擴展的實施優先順序如下：

1. **第一優先：Open5GS核心網優化配置**
   - 此為基礎設施的核心，所有其他功能都建立在穩定的核心網之上
   - 已有部分配置文件(config/open5gs/smf.yaml)和初步腳本(scripts/mongo_init.js)
   - 需迅速完成剩餘配置文件創建和參數優化

2. **第二優先：5G網絡監控系統整合**
   - 監控系統是排障和性能評估的關鍵工具
   - 需要在核心網穩定後立即建立，以便收集基準性能數據
   - 現有docker-compose.yml已包含部分服務，需擴展和配置

3. **第三優先：UERANSIM動態配置機制**
   - 依賴於穩定運行的核心網和基本的監控能力
   - 需要在前兩項基礎上進行開發和測試
   - 已有基礎配置文件(config/ueransim/)可作為開發起點

這三個基礎擴展組合起來，共同構建了實現NTN通信系統的底層基礎。它們解決了標準5G技術難以直接應用於衛星-UAV通信場景的核心問題：高延遲適應(Open5GS優化)、動態配置(UERANSIM機制)和性能監控(監控系統整合)。按此順序實施將最大化資源效益，確保項目順利進展。