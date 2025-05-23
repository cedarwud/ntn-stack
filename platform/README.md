# NTN 平台層

此目錄包含與 Open5GS 和 UERANSIM 相關的配置、服務和工具，作為整個 NTN 系統的基礎設施層。

## 主要組件

-   **config/** - Open5GS、UERANSIM 和監控工具的配置

    -   open5gs/ - Open5GS 核心網配置
    -   ueransim/ - UERANSIM gNodeB 和 UE 配置
    -   prometheus/ - 監控配置
    -   grafana/ - 可視化配置
    -   loki/ - 日誌管理配置
    -   alertmanager/ - 告警配置
    -   mongodb_exporter/ - MongoDB 指標導出器配置
    -   generated/ - 自動生成的配置
    -   templates/ - 配置模板

-   **services/** - 核心網路服務和 API

    -   proxy/ - 代理服務
    -   config_api/ - 配置管理 API
    -   monitor_api/ - 監控 API

-   **proxy_api/** - 代理 API 服務

    -   proxy_api.py - 主要 API 實現
    -   Dockerfile - 容器化配置
    -   start_proxy.sh - 啟動腳本

-   **scripts/** - 自動化部署和管理腳本
    -   apply_config.sh - 配置應用腳本
    -   register_subscriber.sh/ - 用戶註冊腳本
    -   mongo_init.js/ - MongoDB 初始化腳本
    -   startup/ - 啟動腳本
    -   recovery/ - 恢復腳本
    -   network/ - 網絡配置腳本
    -   diagnostic/ - 診斷工具
    -   testing/ - 測試腳本
    -   **fix_ue_registration.sh** - UE註冊問題修復腳本
-   **metrics/** - 指標收集和導出工具
    -   metrics_exporter.py - NTN 特有指標導出器

## 使用方式

平台層組件主要通過容器化方式部署和管理。請參考各子目錄的 README 文件了解具體使用方法。

## 常見問題解決方案

### UE註冊問題

如果UE無法成功註冊到Open5GS網絡（報錯 "FIVEG_SERVICES_NOT_ALLOWED" 或 "5U3-ROAMING-NOT-ALLOWED"），可能是由於以下原因：

1. UE配置與Open5GS中的訂閱者信息不匹配
2. SIM卡未被正確識別為已插入
3. KEY/OPC鑰匙不匹配
4. 服務啟動順序問題

**解決方案：**

執行修復腳本：

```bash
cd /home/sat/ntn-stack
./platform/scripts/fix_ue_registration.sh
```

這個腳本將：
- 檢查並確保所有必要的服務正在運行
- 重新初始化Open5GS中的訂閱者數據
- 重啟UE容器，使新的配置生效
- 檢查UE的註冊狀態

如果問題仍然存在，可以手動檢查UE日誌：

```bash
docker logs $(docker ps -qf name=ues1) --tail 100
```
