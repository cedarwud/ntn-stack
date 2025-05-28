以下內容將「FY114 超視距 (BLOS) 數據鏈路—無人機群型通訊裝備」計畫書中，與 **Sionna、Blender、Skyfield、Open5GS、UERANSIM** 等模擬工具直接相關的重點抽取並整合，按「為何要用 → 要做什麼 → 具體操作步驟 → 與其他工具如何串接」四層脈絡說明，方便後續實作。整篇以文字段落與條列呈現，**無使用表格**。

---

## 1. 數位分身（Wireless Digital Twins）總覽

-   目標是在 NYCU 校園等實地場域中，同步呈現 UAV 與 NTN 基地台的 3D 位置、SINR/Delay-Doppler 等無線指標，並能插入干擾源、即時觀測干擾避讓策略成效。計畫書將該數位分身列為 Tier-2 Mesh 第一年度驗測的核心展示項目，並明確點名「**Nvidia Sionna 模擬無線通道**」與「**Blender 模型建模**」、「Blender → Sionna RT → 光線追蹤模擬」。
-   第二年度展示場景還需接上「NTN UE / UE Emulator」與 Tier-1 Mesh，最終在 3D 介面中即時呈現路由、跳頻、干擾管理等決策結果。

---

## 2. Blender：3D 場景模型的建立與輸出

1. **用途**

    - 還原校園建築、UAV 航線、高度差異與材質，為 Sionna RT 提供可進行毫米波/微波射線追蹤的幾何基礎。

2. **操作重點**

    - 以現有 GIS / 立體地圖（NYCU 3D 衛星圖）為底，匯入到 Blender；使用 GIS-to-Blender 外掛或任何支援 glTF / OBJ 匯出格式的工作流。
    - 依計畫需求為主要牆面、玻璃、金屬、植栽等設定 dielectric / conductor 材質參數（εr、σ）；這些參數將被 Sionna RT 射線追蹤載入。
    - 使用 **collections** 將「動態物件（UAV 與干擾源）」與「靜態場景」分層；動態物件可由 Python 腳本在執行期即時更新座標。
    - 最終以 **glb/glTF 2.0** 形式匯出；確保 **右手座標系**（Sionna 採用）與 **公尺** 設定一致。匯出時可選「Apply Modifiers」「Include UVs」，避免射線追蹤時 mesh 面數不足。

3. **串接**

    - glb 檔在 Sionna RT 中以 `sionna.rt.Scene.from_gltf(path)` 載入。
    - 為支援即時演示，可將 Blender 場景與 Python API 連線（Blender as a server），以便在干擾源或基地台位置改變時重新發佈增量 mesh。

---

## 3. Sionna RT：空中通道與干擾場景模擬

1. **用途**

    - 以射線追蹤（Deterministic channel）產生 **Path-loss、Delay Spread、Doppler**，並輸出位置相關的 **SINR grid**。計畫書中示範了「在 UAV 位置即時畫出 SINR 圖與 Delay-Doppler 圖」。

2. **操作重點**

    - **頻段設定**：Tier-1 Mesh 標註為 600–700 MHz；NTN Feeder Link 可能在 Ku/Ka 頻段。於 `scene.tx.rx.frequency = ...` 切換並分別產生通道樣本。
    - **射線數**與 **最大彈射次數**：對 UAV-to-RU 鏈路建議使用 3–5 bounces；對 UAV-to-UAV 空對空鏈路可放寬至 1–2 bounces 減少計算。
    - **干擾源注入**：在 Scene 中新增 `Transmitter`，對應計畫書列舉的 **spot/barrage/sweep** 三類 jamming signal，調整相對功率、頻寬與掃頻速率。
    - **資料匯出格式**：

        - 連續 SINR heat-map 以 numpy array 存檔，供 Digital Twin 可視化。
        - 抽樣後的 **CQI/RSRP** 時序，透過 WebSocket 推送給 UERANSIM RAN 模擬介面。

3. **串接**

    - **上行 Skyfield**：即時衛星座標（見下一節）變動後，以 `scene.update()` 重算鏈路損耗。
    - **下行 UERANSIM/Open5GS**：將 Sionna 計算出的 SNR 輸入 UERANSIM 之 `max_rxlev` 或自定 `channel_model` hook，影響 UE 連接與 Handover 決策。

---

## 4. Skyfield：NTN 衛星與 UAV 機隊軌跡

1. **用途**

    - 精準計算 LEO 衛星或中繼氣球的 **位置/速度/視角**，並產生給 Sionna RT 射線追蹤的動態發射點（Tx）。

2. **操作重點**

    - 以最新 TLE 檔 `EarthSatellite(...)` 建立物件，設定 `timescale.now()` 取得當前 `geocentric` XYZ；每 1–2 s 回調一次即可滿足計畫中 2 s 更新頻率要求。
    - 車輛 / UAV 航線可用 cubic-spline 由任務規劃器產生；Skyfield 同樣拿來計算 local horizon 與最小仰角 (elevation mask)。

3. **串接**

    - 將衛星 Tx 加入 Sionna `scene.tx_positions`，動態重算通道。
    - 對 Open5GS 設定 **TA (Timing Advance)** 與 **PropagationDelay**；Skyfield + Sionna 提供的 distance / propagation time 直接進入核心網計算。

---

## 5. Open5GS：核心網路 (5GC) 模擬與 NTN 調校

1. **用途**

    - 作為 NTN RAN（AI-RAN、NTN gNB Emulator）後端，提供 AMF/SMF/UPF 等服務，並支援長距離 RTT 與頻偏場景。雖未在簡報中點名，但「NTN GW + Core Network」框圖隱含核心網需求。

2. **操作重點**

    - **Docker Compose** 佈署（與你的既有 ns-3/Open5GS 容器一致）：`AMF > SMF > UPF`，保持 GTP-U 埠與 UERANSIM 一致。
    - **NTN 參數**：

        - `amf > guami_timer.delay`、`smf > pdu_session_inactivity_timer` 調長至 30–60 s。
        - `upf > n3.delay` 模擬 40–60 ms 單向衛星時延。

    - **N3IWF/Non-IP PDU** 可選：若打算直傳 MQTT/Protobuf，開啟 NIDD。

3. **串接**

    - UERANSIM UE/gNB 的 GTP-U 介面直接對接 UPF；Sionna 出的 SINR 會透過 UERANSIM 影響 gNB 決策，進而影響 SMF 路由。

---

## 6. UERANSIM：UE / gNB Emulator

1. **用途**

    - 模擬 UAV 與 NTN gNB，產生 RRC/NGAP 流量並與 Open5GS 對接；可快速測試 **Handover、路由切換、QoS**。

2. **操作重點**

    - **gNB Config**：

        - 允許 FR1 600–700 MHz 與 FR2 帶寬（如 NTN 回傳鏈路）。
        - `force_conn_reestablishment` 設定配合干擾測試，在 SINR 低於閾值時強制重選。

    - **UE Config**：

        - 設定 `tracking_area_code` 與開通 NTN-specific SIB 資訊（可自定 `sib23`）以提高偵測衛星載波能力。
        - 代理擴充：在 UE 程式插入自製 `channel_model.py`，讀取 Sionna 即時 SINR 值並動態改寫 `ue->phy->rxlev`。

3. **結果輸出**

    - 透過 UERANSIM 的 `--pcap` 可取得 NGAP/GTP 封包，供 Wireshark 解析。
    - 使用 Prometheus exporter 對接 LLM 指管中心，展示 Coverage Rate / Average Transport Rate 指標（計畫驗證 D 指標）。

---

## 7. 工具鏈整合流程建議

1. **Offline 預處理**：Blender → glb → Sionna Scene; 基站／建築物靜態元素一次生成。
2. **Online 迴圈**（每 Δt ≤ 2 s）：

    1. Skyfield 更新衛星座標、UAV 航點。
    2. Sionna RT 重新計算路徑損耗與干擾，加總至 SINR。
    3. Python 橋接腳本透過 ZeroMQ/WebSocket 把 SINR 推給 UERANSIM。
    4. UERANSIM 決策 → Open5GS 核心網流量 → LLM 指管中心回饋決策與任務成功率。

3. **干擾實驗腳本**：在 Sionna 中切換 spot ↔ barrage ↔ sweep，驗證跳頻/移頻成效，並比對計畫書 E-1\~E-6 指標。

---

## 8. 測試里程碑對齊

-   **FY115 Q2（第一年度展示）**：室內實驗室 + 部分校園；無須真衛星，可用 Skyfield 將 TLE 替換成假衛星進行動態測試，重點在「Sionna-Blender-UERANSIM-Open5GS 閉環」。
-   **FY116 Q2（第二年度展示）**：加入真 LEO 衛星 TLE，再將整個 pipeline 移到南寮漁港–天德堂 5 km 外場，驗證 Tier-1/2 Mesh 無縫切換能力。

---

### 小結

透過 **Blender → Sionna RT → Skyfield → UERANSIM → Open5GS** 這條仿真鏈，計畫書所要求的「長距離 NTN MESH 數位分身、干擾感知、跳頻/移頻決策效能展示」即可在純軟體環境先完成驗證，再移植到實體 UAV 與實網衛星場域。以上步驟各自對應計畫書標註之驗測項目與時間表，可直接納入你的 Docker 與 CI 流程，確保每兩秒即時更新並滿足驗證指標。
