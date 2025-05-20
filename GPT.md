### 一、簡報中「最終具體目標」

> **在 FY114-115 完成一套可部署於 30 km 營級作戰範圍的 Two-Tier BLOS (NTN + Legacy Mesh) 通訊系統，能在**
> *真實場域* 與 *數位分身* 同步展示下
>
> 1. **UAV 群作為行動終端 (NTN UE)** 與
> 2. **LEO 衛星作為空中 gNodeB/NTN 基地台**
> 3. 透過 **AI-RAN / 抗干擾模組** 動態避干擾
> 4. 支援 **Tier-1 Mesh** 回傳與 **5G 核心網** 連結
> 5. 於實驗室與戶外驗測達到 SINR、吞吐、干擾避讓等量化指標。&#x20;

### 二、UAV 與衛星在系統中的角色

| 元件                  | 主要身份                       | 功能任務                                                                | 關鍵工具                                          |
| ------------------- | -------------------------- | ------------------------------------------------------------------- | --------------------------------------------- |
| **UAV**             | 行動 UE (Rx)；亦可部署 Jammer 或中繼 | - 根據飛行軌跡向衛星/地面請求連線<br>- 回報位置與信道量測 (SINR/CSI)<br>- 作為干擾源測試快速跳頻/移頻演算法 | UERANSIM UE、Sionna Rx 模型、React Three Fiber 動畫 |
| **LEO 衛星 (OneWeb)** | gNodeB / NTN 基地台 (Tx)      | - 依 Skyfield TLE 即時更新軌道<br>- 提供下行波束給 UAV 群<br>- 觸發 AI-RAN 及抗干擾控制邏輯  | Skyfield、UERANSIM gNB、Open5GS N2/N3 介面        |
| **地面 Tier-1 Mesh**  | 傳統 600-700 MHz 自組網         | - 為失聯 UAV 提供備援回程<br>- 與 NTN 網關匯流                                    | Mesh 控制模組 (既有)                                |

（角色設定來自「UAV with NTN payload」「NTN 基地台」等頁面）

---

### 三、整合 FastAPI + React + Blender + Sionna + Skyfield + Open5GS/UERANSIM 的工作流程

```
┌───────────────┐     XML      ┌───────────────┐  CSI/影像  ┌────────────┐
│  Blender        ├──────────►│  FastAPI-Sionna │──────────►│  React F/E │
│(場景/模型匯出) │ GLB        │  (GPU RT/AI)  │ WebSocket │  (Three.js) │
└───────────────┘             └───────────────┘            └────────────┘
         ▲ TLE                ▲ UERANSIM 控制 ▲ 指令/API               ▲
         │                    │               │                       │
         │                    │N2/N3          │位置/SINR              │
┌────────┴──────┐      ┌──────┴─────┐   ┌────┴────┐           ┌──────┴───────┐
│ Skyfield OneWeb │     │ Open5GS Core │  │ Redis/Celery│ …   │  DB / Grafana │
└─────────────────┘     └─────────────┘  └───────────┘       └──────────────┘
```

| 流程階段             | 具體作業                                                                                                                                                                                                                  | 關鍵說明                                                                                     |
| ---------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| **1. 3D/電磁場建模**  | - 在 Blender 建築物/地形/材質<br>- 匯出 **XML** (含材質、介電參數) 給 Sionna RT<br>- 同時匯出 **GLB** 給前端                                                                                                                                    | Blender→Sionna/React 的雙軌匯出在簡報中「Blender 模型建模 / Sionna RT / Wireless Digital Twins」流程明確指示  |
| **2. 後端通道與干擾計算** | - FastAPI 觸發 GPU 任務 (Celery Worker) 讀 XML<br>- Sionna RT 產生光線追蹤結果 + SINR/CSI<br>- 把 jammer 參數、AI-RAN 跳頻策略納入迭代                                                                                                         | Sionna 被列為用於「模擬無線通道」                                                                     |
| **3. LEO 衛星定位**  | - Daemon 服務每 n 秒用 Skyfield 拉 OneWeb TLE<br>- FastAPI 轉換成 ECEF/ENU，寫入 Redis<br>- 同步更新 UERANSIM gNB 位置 + 前端 GLB 動畫                                                                                                      |                                                                                          |
| **4. 5G 協定模擬**   | - FastAPI 產生動態 UERANSIM cfg (gNodeB=衛星, UE=UAV)<br>- 啟動 UERANSIM Container，經 N2/N3 接 Open5GS<br>- Core 回傳 PDU Session / QoS 給 FastAPI                                                                                 | 簡報要求「NTN GW、AI-RAN 基地台、核網」連結                                                             |
| **5. 前端即時渲染**    | - React+React Three Fiber 載入 GLB：<br> • UAV (Rx/UE) 按航跡移動<br> • 衛星 (gNB) 依 Skyfield 更新<br> • Jammer/Tx 模型<br>- 透過 WebSocket 收到：<br> • Channel heat-map 影像 (Matplotlib→PNG)<br> • SINR 數據流 (繪折線圖)<br>- 使用帧同步把 3D 與圖層合成 |                                                                                          |
| **6. 監控與日誌**     | - Prometheus + Grafana 收集 Sionna GPU 使用率、5G KPI<br>- Loki 收集 UERANSIM/Open5GS log                                                                                                                                     |                                                                                          |

---

### 四、建議的技術棧與額外工具

| 模組              | 推薦技術 / 容器                        | 理由                                                 |
| --------------- | -------------------------------- | -------------------------------------------------- |
| **佇列/非同步任務**    | Redis + Celery                   | 將 Sionna GPU 任務、Skyfield 更新與 UERANSIM 啟動解耦         |
| **資料庫**         | PostgreSQL + PostGIS             | 儲存場景 ⇄ ECEF/LLH 空間資料，便於查詢/版本控管                     |
| **WebSocket 層** | FastAPI-WebSocket (Starlette)    | 低延遲把 CSI/SINR 推送到 React                            |
| **3D 前端**       | React Three Fiber, drei, zustand | 與 GLB 整合最成熟；compose 與 UI 狀態簡潔                      |
| **打包/部署**       | Docker Compose → k8s/Helm (後期)   | 方便把 GPU Sionna、Open5GS、UERANSIM、FastAPI、Redis 拆成服務 |
| **CI/CD**       | GitHub Actions                   | 自動化建構場景驗證 (headless Sionna test)                   |

---

### 五、里程碑提議（對齊簡報 FY115-116 驗測節點）

| 時程                | 交付物                                                                                     | 量化驗收                                                   |
| ----------------- | --------------------------------------------------------------------------------------- | ------------------------------------------------------ |
| **M-3 (115 Q4)**  | ① 數位分身 MVP：<br>- Blender→GLB 場景<br>- React 前端載入 UAV & 衛星動態<br>- FastAPI 提供 Skyfield API | 能在前端看到 UAV-LEO 互動動畫                                    |
| **M-6 (116 Q1)**  | ② Sionna RT + 衛星通道<br>③ Jammer 與 AI-RAN 跳頻 Demo                                         | SINR 圖與 Three.js 場景同步；跳頻演算法於 1 ms 內響應                  |
| **M-9 (116 Q2)**  | ④ Open5GS+UERANSIM 整合<br>⑤ Tier-1 Mesh Bridge                                           | E2E Ping < 50 ms；中斷後 2 s 內重建連線                         |
| **M-12 (116 Q3)** | ⑥ 戶外 5 km 驗測 + KPI 報告                                                                   | 簡報指標：Coverage > 0.75、Transport Rate > 0.65、更新頻率 ≤ 2 s  |

---

### 六、結語

依照簡報的戰術需求，本方案把 **「數位分身 + 5G-NTN-Mesh + AI-RAN 抗干擾」** 三大主軸串成一條 DevOps 流水線：

> **Blender ⇒ Sionna ⇒ FastAPI ⇒ Open5GS/UERANSIM ⇒ React Three Fiber**

如此即可在實驗室到戶外的 *連續測試* 中，同時驗證 **通道物理層、5G 協定層、網狀路由層** 與 **視覺化決策層** 成果，達成簡報所列 FY116 Q2「無人載具 NTN MESH 通訊系統」展示目標。
