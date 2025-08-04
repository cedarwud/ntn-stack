1. NetStack 事件驅動架構（干擾檢測異步化）
2. SimWorld CQRS 模式（衛星位置讀寫分離）
3. 全面異步微服務架構

4. Central Unit (CU) 和 Distributed Unit (DU) 分析
   基於代碼分析，CU 和 DU 概念屬於 UERANSIM 的實現，不是 Open5GS：
   分工說明：
   Open5GS：實現 5G 核心網（5GC），包括 AMF、SMF、UPF 等網路功能
   UERANSIM：實現 5G 無線接入網（RAN），包括 gNodeB 和 UE 模擬
   在這個架構中：
   Central Unit (CU) 和 Distributed Unit (DU) 是 5G gNodeB 的邏輯分割
   可以分開部署，這是 5G 標準的重要特性
   CU 處理較高層協議（RRC、PDCP）
   DU 處理較低層協議（RLC、MAC、PHY）
