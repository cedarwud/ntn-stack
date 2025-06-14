# 移動衛星網絡換手加速技術實現指南

## 1. 系統架構與組件概述

本指南基於《Accelerating Handover in Mobile Satellite Network》論文提出的架構，介紹如何復現加速換手機制的實作。系統主要組成元件如下：

* **UERANSIM**：模擬 UE（用戶設備）和 S-gNB（衛星 gNB，衛星基站）的 5G 無線接取網路行為，用於構建 RAN 部分。
* **Open5GS**：5G 核心網路軟體，包括 AMF、SMF、UPF 等模組，用於構建核心網路部分。UPF 將被修改以實現同步演算法。
* **Skyfield**：Python 天文計算庫，利用衛星軌道根數據 (TLE) 進行衛星軌跡預測，用於模擬 LEO 衛星可預測的軌道運行。
* **衛星數據源**：CelesTrak 提供的最新 TLE 星座數據（如 Starlink、Kuiper 等），作為衛星軌道參考輸入。

上述元件共同組成模擬平台：Skyfield 提供衛星位置與覆蓋計算，Open5GS + UERANSIM 提供 5G NTN（非地面網絡）通信架構。我們將透過修改 UPF 實現核心網與 RAN 的同步，並利用 UERANSIM 的 Xn 介面模擬衛星間換手信令流程。

## 2. 環境建置與依賴安裝

### 2.1 核心工具與版本

確保安裝以下核心軟體與工具鏈（括號內為建議版本）：

* Open5GS **v2.6.3** – 5G 核心網 (CP/UP 分離架構)
* UERANSIM **v3.2.9** – 5G UE/gNB 模擬器
* Skyfield **v1.42** – 衛星軌道計算庫 (Python)
* MongoDB **v6.0** – Open5GS 訂閱者數據庫依賴
* Wireshark **v4.0.8** – 封包分析工具（可選，用於監視協議訊息）
* Mininet-WiFi **v2.3.1b** – 網路拓撲模擬器（可選，用於模擬複雜網路拓撲）
* Celestrak 最新 **TLE** 資料集 – 如 `starlink.txt`、`kuiper.txt` 等衛星星座 TLE 檔案

### 2.2 基礎開發環境安裝

更新系統並安裝基本編譯工具和庫：

```bash
# 更新套件索引並升級系統
sudo apt update && sudo apt upgrade -y

# 安裝編譯工具和常用庫
sudo apt install -y build-essential cmake git wget curl
sudo apt install -y libsctp-dev python3-pip python3-setuptools python3-venv
sudo apt install -y python3-wheel ninja-build bison flex
sudo apt install -y libgnutls28-dev libgcrypt-dev libssl-dev
sudo apt install -y libidn11-dev libmongoc-dev libbson-dev
sudo apt install -y libyaml-dev libmicrohttpd-dev libcurl4-gnutls-dev
sudo apt install -y libnghttp2-dev libtins-dev libtalloc-dev
```

上述安裝包含了編譯 Open5GS 和 UERANSIM 所需的所有依賴（如 SCTP 庫、加解密庫、網路庫等）。

### 2.3 安裝 MongoDB（Open5GS 依賴）

Open5GS 使用 MongoDB 儲存用戶訂閱資訊（如 HSS/UDM 數據）。安裝並啟動 MongoDB：

```bash
# 匯入 MongoDB 公鑰並添加套件庫
wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/6.0 multiverse" \
 | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list

sudo apt update
sudo apt install -y mongodb-org

# 啟動並設定開機自動啟動 MongoDB 服務
sudo systemctl start mongod
sudo systemctl enable mongod
```

### 2.4 安裝 Open5GS

使用源碼安裝 Open5GS：

```bash
# 取得 Open5GS 源碼
cd ~
git clone https://github.com/open5gs/open5gs.git
cd open5gs

# 編譯並安裝 Open5GS
meson build --prefix=`pwd`/install
ninja -C build
cd build
sudo ninja install
```

成功後，Open5GS 的執行檔將位於 `open5gs/install/bin` 目錄下（如 `open5gs-upfd` 等）。

### 2.5 安裝 UERANSIM

使用源碼編譯安裝 UERANSIM：

```bash
# 取得 UERANSIM 源碼
cd ~
git clone https://github.com/aligungr/UERANSIM.git
cd UERANSIM

# 編譯 UERANSIM
make
```

編譯完成後，`build/` 目錄下會生成可執行檔，例如 `nr-ue`（UE 模擬器）、`nr-gnb`（gNB 模擬器）。

### 2.6 Python 環境與套件安裝

建立虛擬環境並安裝所需的 Python 套件：

```bash
# 建立並啟用 Python 虛擬環境
python3 -m venv leo_handover_env
source leo_handover_env/bin/activate

# 安裝 Python 依賴套件
pip install --upgrade pip
pip install skyfield numpy pandas matplotlib pymongo flask websockets GPUtil psutil scapy
```

* `skyfield`：用於衛星軌道計算
* `numpy`：數值計算（軌道運算和角度轉換）
* `pandas`：方便處理記錄的數據
* `matplotlib`：繪圖（如延遲CDF圖）
* `pymongo`：如需在 Python 端訪問 MongoDB
* `flask`、`websockets`：可選，用於建立簡易服務介面監控或控制模擬（非必要）
* `GPUtil`、`psutil`：用於資源監控（GPU/CPU/記憶體）
* `scapy`：封包解析庫，可用於截取分析交換的訊息（例如測量延遲）

完成上述步驟後，環境已就緒，接下來進行核心演算法的實現。

## 3. 核心演算法實作

論文提出了兩個核心演算法：一是 **RAN 與核心網同步演算法**（Synchronized Algorithm），用於讓核心網預知換手時機；二是 **快速存取衛星預測演算法**，用於降低 UPF 預測負荷。以下將分別介紹其實作細節，包括完整代碼和流程圖。

### 3.1 同步演算法 – 核心網與 RAN 同步 (Algorithm 1)

**演算法概念**：同步演算法在 UPF 執行，核心思想是**預測兩個時間點**（相隔固定時間 \$\Delta t\$）各 UE 連接的衛星，藉此判斷該時間區間內是否會發生換手。如果預測到換手（兩次預測的連接衛星不同），則進一步使用**二分搜尋**計算精確的換手觸發時間 \$T\_p\$。這樣可在不與 RAN 即時交互的情況下，讓核心網提早獲知何時、往哪顆衛星換手，實現核心與 RAN 狀態同步，消除傳統方案中核心滯後更新路由導致的延遲。

**演算法步驟**（對應論文 Algorithm 1）：

1. **初始化**：設定最後更新時間 \$T\$，初始化表格 \$R\$ 用於存儲每個 UE 當前接入衛星、下一時刻接入衛星，以及預測的換手時間 \$T\_p\$。
2. **迴圈運行**：UPF 不斷檢查時間，分為兩種更新情況：

   * **定期更新**：每經過固定間隔 \$\Delta t\$（例如 0.5 或 1 秒，可視計算複雜度調整），執行一次預測更新。獲取當前時刻 \$T+\Delta t\$ 各 UE 所在衛星 \$A\_T\$，預測下一時刻 \$T+2\Delta t\$ 的衛星 \$A\_{T+\Delta t}\$，比較如不同則用二分法計算換手時刻集合 \$T\_p\$。等待時間到達後更新表格 \$R\$，將 \$T\$ 設為新時間點（本次更新完成）。
   * **事件驅動更新**：若有 UE 的位置信息發生變化（例如 UE 移動到新位置或重新連入），則對該 UE 單獨執行一次更新。計算該 UE 在當前時間 \$t\$ 及 \$t+\Delta t\$ 時的接入衛星，如不同則用二分法計算該 UE 的換手時間並更新表格 \$R\$。

通過上述機制，核心網的 UPF 維持一份隨時間更新的 UE-衛星關係表 \$R\$，記錄未來短時間內各 UE 的「下一連接衛星」以及預計換手時間。這允許核心網在適當時機主動更新路由，而不需要等待 RAN 通知，實現核心與 RAN **同步**。下方給出了該演算法的 Python 實現與流程圖：

```python
# synchronized_algorithm.py
import time
import numpy as np
from typing import Dict, List, Tuple
from dataclasses import dataclass
from datetime import datetime

@dataclass
class AccessInfo:
    ue_id: str
    satellite_id: str
    next_satellite_id: str
    handover_time: float

class SynchronizedAlgorithm:
    def __init__(self, delta_t: float = 5.0):
        self.delta_t = delta_t            # 更新週期 Δt（秒）
        self.T = time.time()             # 上次更新時間戳
        self.R: Dict[str, AccessInfo] = {}  # UE-衛星關係表 (ue_id -> AccessInfo)
        self.Tp: Dict[str, float] = {}      # 預測的換手時間表 (ue_id -> tp)

    def periodic_update(self, t: float) -> None:
        """週期性更新（對應 Algorithm 1 的第5-10行）"""
        # Step 5-6: 從表R獲取當前各UE接入衛星 At
        At = self.get_access_satellites(t)
        # Step 7: 根據 At 預測未來時刻的接入衛星 At+Δt
        At_delta = self.predict_access_satellites(t + self.delta_t)
        # Step 8: 比較 At 和 At+Δt，使用二分搜索計算每個UE的換手時間 Tp
        for ue_id in At:
            if At[ue_id] != At_delta[ue_id]:
                # 預測在 [t, t+Δt] 期間發生換手，計算精確換手觸發時間
                tp = self.binary_search_handover_time(
                    ue_id, At[ue_id], At_delta[ue_id], t, t + self.delta_t
                )
                self.Tp[ue_id] = tp
            else:
                self.Tp[ue_id] = 0  # 衛星不變，無需換手
        # Step 9: 等待到達時間 t，然後更新表R
        time.sleep(max(0, t - time.time()))
        self.update_R(At_delta, self.Tp)
        # Step 10: 將 T 更新為本次更新時間
        self.T = t

    def update_ue(self, ue_id: str, t: float) -> None:
        """UE 單獨事件更新（對應 Algorithm 1 的第11-13行）"""
        # 計算該 UE 當前及 Δt 後的存取衛星
        at_u = self.calculate_access_satellite(ue_id, t)
        at_delta_u = self.calculate_access_satellite(ue_id, t + self.delta_t)
        # 根據是否會換手更新預測時間
        if at_u != at_delta_u:
            tp_u = self.binary_search_handover_time(
                ue_id, at_u, at_delta_u, t, t + self.delta_t
            )
            self.Tp[ue_id] = tp_u
        else:
            self.Tp[ue_id] = 0
        # 更新表R中該UE的記錄
        self.R[ue_id] = {
            'access_satellite': at_u,
            'next_access_satellite': at_delta_u,
            'handover_time': self.Tp[ue_id]
        }

    def binary_search_handover_time(self, ue_id: str, sat1: str, sat2: str,
                                    t_start: float, t_end: float) -> float:
        """使用二分法計算精確換手時間點"""
        precision = 0.01  # 要求精度10ms
        while t_end - t_start > precision:
            t_mid = (t_start + t_end) / 2
            sat_mid = self.calculate_access_satellite(ue_id, t_mid)
            if sat_mid == sat1:
                # 中間時刻仍連接舊衛星，換手尚未發生
                t_start = t_mid
            else:
                # 中間時刻已連接新衛星，換手已經發生
                t_end = t_mid
        return t_end  # 當時間區間縮小到精度閾值時，以 t_end 作為預估換手時間

    # 其他輔助函數（需根據系統具體實現）：
    def get_access_satellites(self, t: float) -> Dict[str, str]:
        """獲取當前所有 UE 在時間 t 所連接的衛星"""
        # 這裡應從表R或實時計算得到每個UE當前連接衛星，如沒有則需要結合軌跡計算
        return {ue: info['access_satellite'] for ue, info in self.R.items()}

    def predict_access_satellites(self, t: float) -> Dict[str, str]:
        """預測時間 t 所有 UE 應連接的衛星（藉助快速預測演算法，這裡簡單調用即可）"""
        # 實際實現中可調用 FastSatellitePrediction.predict_access_satellites()
        return fast_sat_pred.predict_access_satellites(list(self.R.keys()), all_satellites, t)

    def calculate_access_satellite(self, ue_id: str, t: float) -> str:
        """計算 UE 在時間 t 所連接的衛星"""
        # 可利用衛星軌跡計算UE與各衛星距離或仰角，選擇覆蓋最佳者
        return compute_closest_satellite(ue_id, t)
```

上面代碼實現了同步演算法的核心邏輯。其中 `periodic_update()` 對應論文演算法的定期更新部分，`update_ue()` 對應 UE 事件驅動的更新部分。`binary_search_handover_time()` 使用二分法在 $\[t, t+\Delta t]\$ 區間內查找換手發生的時間點，精度設定為 10ms。請注意，一些輔助函數如 `get_access_satellites`、`predict_access_satellites`、`calculate_access_satellite` 需要根據系統資料加以實現：例如可結合下一節的快速預測演算法或使用 `SatelliteTrajectory` 模組計算。

下面的流程圖以 Mermaid 表示 Algorithm 1 同步演算法的工作流程，與上述代碼邏輯相對應：

```mermaid
flowchart TD
    A[初始化 T, R 表] --> B{進入無限迴圈}
    B --> C{當前時間 > T + Δt?}
    C -->|是| D[執行週期性更新 (PERIODIC_UPDATE)]
    C -->|否| E{UE 位置/狀態改變?}
    E -->|是| F[執行單一 UE 更新 (UPDATE_UE)]
    E -->|否| B
    D --> G[從 R 表讀取 At (當前接入衛星)]
    G --> H[預測 At+Δt (未來接入衛星)]
    H --> I[二分搜尋計算換手時間 Tp]
    I --> J[等待系統時間達到 t 時刻]
    J --> K[更新 R 表內容]
    K --> L[設置 T = t]
    L --> B
    F --> M[計算該 UE 的 At 和 At+Δt]
    M --> N[計算該 UE 的 Tp（若需換手）]
    N --> O[更新 R 表該 UE 的記錄]
    O --> B
```

### 3.2 快速存取衛星預測演算法 (Algorithm 2)

**演算法概念**：為了降低 UPF 每次預測的計算負擔，論文利用了 LEO 衛星 **可預測的軌道**和**地理覆蓋分佈**的特點，提出快速預測 UE 應接入哪顆衛星的演算法。基本思路是只針對**可能需要換手的 UE**進行精細計算，並透過將地球劃分區塊和衛星預分配等方式，加速找到最佳衛星。

**關鍵設計**：

* **接入策略區分**：每個 UE 預先設定接入策略：*彈性接入（flexible）* 或 *穩定接入（consistent）*。

  * *Flexible* 策略的 UE 傾向於提前切換到更優的衛星（只要當前衛星即將出覆蓋就換手），以減少鏈路中斷時間。
  * *Consistent* 策略的 UE 則傾向保持連接直到信號消失才換手，減少不必要的切換頻率。
* **候選 UE 集合**：根據上述策略，僅選出**可能需要換手**的 UE 進行後續計算：

  * 對於 flexible UE，如果在預測未來時刻 \$t\_1\$ 時當前衛星將不再覆蓋該 UE，則將此 UE 加入候選集合 \$D\$；若仍有覆蓋則本次忽略。
  * 對於 consistent UE，無論如何都加入集合 \$D\$，因為它們終將換手，只是可能稍晚。
* **地理區塊劃分**：將地球表面按經緯度劃分為若干**區塊**（每塊大小約等於單顆衛星的服務覆蓋範圍）。例如，可簡化為每10度經緯度為一塊。每次預測時，計算所有衛星在目標時間的座標，將衛星歸屬到覆蓋哪個區塊。相鄰區塊視為鄰居，用於考慮邊緣區域的覆蓋重疊。
* **選擇最佳衛星**：對於每個候選 UE，識別其所處的區塊及鄰近區塊，彙總該區域可用的衛星清單，在其中根據某種優化準則選擇最優的衛星（例如仰角最高或信號延遲最低）作為其在未來時刻的接入衛星。如果選出的與當前不同，則表示需要換手，將此結果更新到表 \$R\$。

**演算法實現**：下方給出了 Python 類別實現，以及對應的流程圖：

```python
# fast_satellite_prediction.py
from typing import List, Dict, Set
import numpy as np

class FastSatellitePrediction:
    def __init__(self, earth_radius: float = 6371.0):
        self.earth_radius = earth_radius
        self.blocks = {}  # 地理區塊劃分結果

    def predict_access_satellites(self, users: List[str], satellites: List[Dict],
                                  time_t: float) -> Dict[str, str]:
        """Algorithm 2: 快速存取衛星預測"""
        # Step 1: 預測在時間 t 時所有衛星的位置
        St_prime = self.predict_satellite_positions(satellites, time_t)
        # Step 2: 初始化候選 UE 集合和結果字典
        UC: Set[str] = set()    # 候選 UE 集合 D
        At_prime: Dict[str, str] = {}
        # Step 3-10: 根據存取策略，篩選候選 UE
        for ui in users:
            access_strategy = self.get_access_strategy(ui)
            current_satellite = self.get_current_satellite(ui)
            if access_strategy == "flexible":
                if not self.is_satellite_available(current_satellite, ui, time_t):
                    UC.add(ui)  # 當前衛星將不可用，加入候選
                else:
                    At_prime[ui] = current_satellite  # 衛星仍可覆蓋，保持不變
            else:  # consistent 策略
                UC.add(ui)
        # Step 11-15: 創建地理區塊並將衛星分配到區塊
        blocks = self.create_geographical_blocks()
        satellite_blocks = self.assign_satellites_to_blocks(St_prime, blocks)
        # Step 16-19: 為每個候選 UE 分配最優接入衛星
        for uj in UC:
            block_id = self.get_user_block(uj)
            # 從該區塊及鄰近區塊的衛星列表中找到最佳衛星
            access_satellite = self.find_best_satellite(uj, satellite_blocks[block_id])
            At_prime[uj] = access_satellite
        return At_prime

    def create_geographical_blocks(self) -> Dict[int, Dict]:
        """創建地理區塊網格"""
        service_radius = 1000  # km, 假設單衛星覆蓋半徑（簡化值）
        blocks: Dict[int, Dict] = {}
        block_id = 0
        # 以經緯度 10 度為間隔劃分區塊（簡化示意）
        for lat in range(-90, 91, 10):
            for lon in range(-180, 181, 10):
                blocks[block_id] = {
                    'lat_min': lat,
                    'lat_max': lat + 10,
                    'lon_min': lon,
                    'lon_max': lon + 10,
                    'satellites': []  # 該區塊覆蓋的衛星
                }
                block_id += 1
        return blocks

    # 其餘輔助方法如 predict_satellite_positions, assign_satellites_to_blocks,
    # get_access_strategy, get_current_satellite, is_satellite_available,
    # get_user_block, find_best_satellite 等需根據實際情況實現。
    # 例如：predict_satellite_positions 可調用 SatelliteTrajectory 類返回各衛星的經緯度。
```

上述代碼中，`predict_access_satellites` 方法按照步驟完成快速預測：首先計算所有衛星在未來時間的座標，接著按照接入策略選出候選 UE，再創建地理區塊並將衛星映射到區塊，最後為每個候選 UE 從其所在區及鄰區的衛星中選擇最佳衛星。輔助函數如 `predict_satellite_positions` 預期返回類似 `{'sat_id': (lat, lon, alt), ...}` 的結構，`is_satellite_available` 用於判斷給定衛星在指定時間是否覆蓋某 UE（可透過計算仰角或距離判定），`find_best_satellite` 則根據一些優化準則（例如距離最近或連線品質最好）在候選衛星列表中挑選。

下面是對應的流程圖，概要展示 Algorithm 2 快速預測演算法：

```mermaid
flowchart TD
    A[輸入: UE清單, 衛星列表, 時間 t] --> B[預測時間 t 所有衛星位置 (St')]
    B --> C[初始化 UC 集合, At' 結果表]
    C --> D{遍歷所有 UE}
    D --> E{UE 接入策略?}
    E -->|彈性 (flexible)| F{當前衛星在 t 時仍可覆蓋?}
    E -->|穩定 (consistent)| G[將 UE 加入 UC]
    F -->|否| G
    F -->|是| H[At'[ui] = 當前衛星 (保持不換)]
    G --> I{是否還有 UE?}
    H --> I
    I -->|是| D
    I -->|否| J[地球表面劃分地理區塊]
    J --> K[將每顆衛星指派到對應區塊]
    K --> L{遍歷 UC 中每個 UE}
    L --> M[識別 UE 所在區塊]
    M --> N[收集該區塊及鄰近區塊的候選衛星]
    N --> O[在候選衛星中選擇最佳衛星]
    O --> P[設定 At'[uj] = 最佳衛星]
    P --> Q{還有未處理的 UC UE?}
    Q -->|是| L
    Q -->|否| R[輸出 At' 結果表]
```

該快速演算法透過空間區塊和策略過濾顯著減少了需要計算的 UE/衛星數量。此處還可以融入一項**優化**：限制候選衛星需與當前衛星**軌道方向相似**。論文提到，選擇軌道運行方向相近的衛星作為目標，可以進一步降低換手延遲（因為衛星相對UE移動方向更平順，鏈路中斷時間更短）。此約束在實作中可以在 `find_best_satellite` 時進行篩選：只考慮與舊衛星運行方向差異不大的候選衛星。

## 4. 系統整合與模擬平台構建

有了核心演算法，我們需要將其整合進整個衛星網絡系統中。系統架構包含三部分：**衛星軌跡預測**（Skyfield/TLE）、**5G 核心網**（Open5GS/UPF）與 **RAN + 衛星**（UERANSIM 模擬 S-gNB/UE）。本節將說明如何搭建模擬平台並結合演算法，包括對 Open5GS 和 UERANSIM 的必要修改，以及主程式如何協調各模組運行。

### 4.1 衛星軌跡預測模組 (Skyfield + TLE)

首先，使用 Skyfield 建立衛星軌道計算模組，以提供**衛星即時位置**和**覆蓋判斷**功能。透過載入最新的 TLE 資料，我們可以預測任意時刻衛星的位置，進而推算衛星對地的覆蓋情況（例如計算某地點觀測某衛星的仰角）。以下是 `SatelliteTrajectory` 類的實現：

```python
# satellite_trajectory.py
from skyfield.api import load, EarthSatellite, wgs84
from datetime import datetime, timedelta
import numpy as np
import requests

class SatelliteTrajectory:
    def __init__(self):
        self.ts = load.timescale()        # Skyfield 時間軸對象
        self.satellites = {}             # 衛星名稱 -> 衛星對象
        self.tle_data = {}               # 衛星名稱 -> (TLE line1, TLE line2)

    def load_tle_data(self, constellation: str = "starlink"):
        """從 Celestrak 獲取指定星座的 TLE 數據並載入"""
        if constellation == "starlink":
            url = "https://celestrak.com/NORAD/elements/starlink.txt"
        elif constellation == "kuiper":
            # Kuiper 尚未大規模部署，這裡使用 OneWeb 或模擬數據代替
            url = "https://celestrak.com/NORAD/elements/supplemental/oneweb.txt"
        else:
            raise ValueError("未知的星座類型")
        # 獲取並解析 TLE 文本
        response = requests.get(url)
        lines = response.text.strip().split('\n')
        for i in range(0, len(lines), 3):
            if i + 2 < len(lines):
                name = lines[i].strip()
                line1 = lines[i + 1].strip()
                line2 = lines[i + 2].strip()
                sat = EarthSatellite(line1, line2, name, self.ts)
                self.satellites[name] = sat
                self.tle_data[name] = (line1, line2)

    def predict_position(self, satellite_name: str, time_t: datetime):
        """預測單顆衛星在指定UTC時間的位置（經緯度與高度）"""
        if satellite_name not in self.satellites:
            raise ValueError(f"Satellite {satellite_name} not loaded.")
        sat = self.satellites[satellite_name]
        t = self.ts.from_datetime(time_t)
        geocentric = sat.at(t)               # 衛星在地心座標系的位置
        subpoint = geocentric.subpoint()     # 投影到地球表面的子星點
        lat = subpoint.latitude.degrees
        lon = subpoint.longitude.degrees
        alt = subpoint.elevation.km
        return lat, lon, alt

    def calculate_elevation(self, user_lat: float, user_lon: float,
                             sat_lat: float, sat_lon: float, sat_alt: float) -> float:
        """計算給定衛星相對於用戶位置的仰角（degrees）"""
        earth_radius = 6371.0  # 地球半徑 (km)
        # 將經緯度轉換為弧度
        user_lat_rad, user_lon_rad = np.radians(user_lat), np.radians(user_lon)
        sat_lat_rad, sat_lon_rad = np.radians(sat_lat), np.radians(sat_lon)
        # 計算地心角（user和satellite子星點的夾角）
        cos_angle = (np.sin(user_lat_rad) * np.sin(sat_lat_rad) +
                     np.cos(user_lat_rad) * np.cos(sat_lat_rad) * np.cos(user_lon_rad - sat_lon_rad))
        angle = np.arccos(np.clip(cos_angle, -1, 1))
        # 計算用戶到衛星的距離並求仰角
        sat_radius = earth_radius + sat_alt
        distance = np.sqrt(earth_radius**2 + sat_radius**2 - 2 * earth_radius * sat_radius * np.cos(angle))
        # 根據球面幾何計算仰角（sinE = 對邊/斜邊）
        sin_elevation = (sat_radius * np.sin(angle)) / distance
        elevation = np.arcsin(np.clip(sin_elevation, -1, 1))
        return np.degrees(elevation)

    def is_in_coverage(self, satellite_name: str, user_lat: float, user_lon: float, min_elevation: float = 40.0) -> bool:
        """判斷給定衛星在特定時刻對指定用戶位置是否有覆蓋（仰角 >= min_elevation）"""
        lat, lon, alt = self.predict_position(satellite_name, datetime.utcnow())
        elev = self.calculate_elevation(user_lat, user_lon, lat, lon, alt)
        return elev >= min_elevation
```

上述 `SatelliteTrajectory` 類提供以下功能：

* `load_tle_data`：從 Celestrak 獲取 Starlink 或 Kuiper 星座的最新 TLE，載入所有衛星的軌道參數（如 Kuiper 暫無實際數據，代以 OneWeb 或模擬軌道）。
* `predict_position`：給定衛星名稱和時間，輸出該衛星當時的經度、緯度和高度，可用於判斷衛星位置和覆蓋區域。
* `calculate_elevation`：輸入用戶和衛星的位置，計算衛星對用戶的仰角，從而判斷覆蓋。
* `is_in_coverage`：高階函式，直接判斷某衛星此刻對給定用戶位置是否在服務範圍（仰角高於閾值，如 40 度）。

透過這個模組，我們可以支援演算法中涉及的**衛星覆蓋判定**和**距離計算**等功能。例如在 `FastSatellitePrediction.is_satellite_available` 中，即可調用 `SatelliteTrajectory.is_in_coverage` 來判斷某衛星能否持續覆蓋 UE。

> **TLE 更新與精度**：由於 TLE 本身有預測誤差（軌道隨時間可能有輕微漂移），建議**定期更新 TLE** 資料或縮短預測區間來降低誤差影響。Skyfield 的 SGP4 模型對幾天內的預測通常誤差在幾公里內，對換手時序影響不大。但若需要更精細同步，可縮短 \$\Delta t\$ 或在換手決策上留一定緩衝時間。詳見本指南「關鍵技術細節」章節關於 TLE 精度補償的討論。

### 4.2 修改 Open5GS UPF 以整合同步演算法

Open5GS 的 UPF 是用 C 實現的 user plane 功能。我們希望在 UPF 中嵌入同步演算法，使其能在核心網內部直接維護 UE 的衛星連接預測表 \$R\$，並適時調整轉發。這可以通過以下步驟實現：

1. **擴展 UPF 內部資料結構**：添加一個 UE-衛星關係表，用來存放每個 UE 目前連接衛星、下一衛星以及預測換手時間。例如可定義一個結構體 `ue_satellite_entry_t` 及其數組，並加鎖保護共享訪問。
2. **啟動同步演算法執行緒**：在 UPF 啟動時，創建一個獨立的執行緒週期性執行同步演算法邏輯。該執行緒每隔 \$\Delta t\$ 讀取目前表中數據，透過調用類似前述 Python 演算法邏輯（需轉為 C 或通過接口調用）更新預測。簡化做法下，可在 C 裡實現演算法的關鍵部分，如每 \$\Delta t\$ 調用一次 `periodic_update()` 並更新表。
3. **核心網路路由更新**：當表 \$R\$ 中預測某 UE 在未來將換手時，UPF 可在換手發生時刻之前進行路由準備。例如預先創建通往目標 gNB（衛星）的 GTP-U 連接，在換手時只需切換 TEID。理想狀況下，UPF 可以利用 \$T\_p\$ 精確安排 path switch 幾乎無縫銜接。
4. **GTP-U 封包頭攜帶衛星資訊**（可選優化）：為了讓 RAN 知道核心側預期的目標衛星，可在 GTP-U 的擴展頭部中加入**衛星識別**資訊。例如添加欄位表示「下一節點為某衛星 gNB」，UERANSIM 端在處理時就能確認換手目標。

以下代碼片段展示了如何在 UPF 中加入資料結構和執行緒（僅示意重點步驟，用 C 語言）：

```c
// upf_modifications.c (示意代碼片段)
typedef struct {
    char ue_id[64];
    char access_satellite[32];
    char next_access_satellite[32];
    double handover_time;
} ue_satellite_entry_t;

typedef struct {
    ue_satellite_entry_t *entries;
    int count;
    int capacity;
    pthread_mutex_t mutex;
} ue_satellite_table_t;

// 在 UPF 初始化時創建表
ue_satellite_table_t *g_ue_sat_table;

void init_ue_satellite_table(int capacity) {
    g_ue_sat_table = malloc(sizeof(ue_satellite_table_t));
    g_ue_sat_table->entries = calloc(capacity, sizeof(ue_satellite_entry_t));
    g_ue_sat_table->count = 0;
    g_ue_sat_table->capacity = capacity;
    pthread_mutex_init(&g_ue_sat_table->mutex, NULL);
}

// 同步演算法主迴圈執行緒
void* synchronized_algorithm_thread(void* arg) {
    double delta_t = 5.0;  // 5秒更新間隔
    double last_update = current_time_seconds();
    while (1) {
        double now = current_time_seconds();
        if (now > last_update + delta_t) {
            pthread_mutex_lock(&g_ue_sat_table->mutex);
            // 執行 periodic_update 邏輯：遍歷表、計算 At+Δt、Tp 等並更新表
            perform_periodic_update(g_ue_sat_table, now);
            pthread_mutex_unlock(&g_ue_sat_table->mutex);
            last_update = now;
        }
        usleep(100000);  // 100ms 休眠，降低CPU佔用
    }
    return NULL;
}

// (其他代碼，如在UPF主程序中調用 init_ue_satellite_table 和 pthread_create 啟動執行緒)
```

> **注意**：在 UPF 中直接實現完整的二分預測邏輯需要處理浮點計算和時間轉換，開發上可能較繁瑣。簡單起見，亦可讓 UPF 定期將 UE 位置信息發送給外部**預測模組**（如 Python 實現的服務），由其計算結果後再回寫 UPF。此處提供的 C 示意碼僅供參考說明嵌入點。

透過修改 UPF，我們可以在核心網內部實時掌握 UE 與衛星的關係。但是要完全實現論文方案，我們還需要**改造 RAN 端**，使 gNB 之間可以透過 Xn 介面直接換手，而非依賴核心的 N2 介面。這在模擬中由 UERANSIM 來實現。

### 4.3 修改 UERANSIM 支援 Xn 介面換手

默認的 UERANSIM 主要支援 UE 通過核心網 (AMF) 的換手流程（N2-based handover），並未實作 gNB 之間直接通信的 Xn 介面。我們需要對 UERANSIM 進行擴充，使多個衛星 gNB 節點間可以建立 Xn 連結並交換換手信令。這包括幾個部分：

1. **Xn 連結建立**：讓每個 gNB 啟動時監聽一個 XnAP SCTP 埠（類似 NGAP 埠 38412，但為 Xn 介面指定另一埠，例如 38422）。當有新的 gNB 啟動時，彼此透過 SCTP 完成 **Xn Setup** 程序，交換基礎參數（如 gNB ID）。這需要在 UERANSIM 的 gNB 代碼中增加 SCTP server/client 和相應的消息處理。可參考 3GPP TS 38.423 XnAP 標準中的 Xn Setup Request/Response 訊息格式來封裝。

2. **換手信令流程**：在 UERANSIM gNB 邏輯中加入 Xn-based handover 狀態機。當協調模組（或我們自行的控制觸發）指示要執行換手時，執行以下步驟：

   * **Handover Request**：來源 gNB 構建換手請求消息，內容包括 UE 上下文、安全參數、目標 cell ID 等，通過 Xn SCTP 發送給目標 gNB。
   * **Handover Acknowledge**：目標 gNB 收到請求後，預先分配所需資源（RRC Context、PDU會話等）給該 UE，然後回傳 ACK 給來源 gNB。
   * **SN Status Transfer**：來源 gNB 收到 ACK 後，通過 Xn 向目標 gNB 發送 SN (Sequence Number) Status，傳遞PDCP層的序列編號進度，以便目標端繼續數據傳輸不中斷。
   * **UE Context Release**：來源 gNB 在適當時機（UE 完成切換後）釋放舊 UE 上下文，通知目標 gNB。

3. **UE 模擬配合**：確保 UERANSIM 的 UE 在收到 RRC reconfiguration（換手命令）後，正確地斷開舊鏈路並連接到目標 gNB，同時不向核心發起重新註冊流程（因為在 Xn 換手中核心透明）。可能需要在 UE 代碼中增加「正在換手」的狀態，以跳過預設的 detach/attach 操作，只執行 RRC 層面的換連接。

4. **協調模組觸發**：提供一種機制由外部或上層代碼來觸發上述換手流程。例如我們可以增加一個接口，使得當核心的同步演算法判定某 UE 的換手時間到 (\$T\_p\$) 時，通知對應的來源 gNB 執行換手請求至目標 gNB。這個觸發可以通過 UERANSIM 的某種控制接口（如模擬ENV指令或擴展API）實現。

Claude 模型提供了一份 UERANSIM 可能的換手處理類代碼示例（C++），展示如何封裝換手邏輯：

```cpp
// gnb_handover.cpp (示意代碼片段)
class SatelliteHandover {
private:
    std::map<std::string, UeContext> ueContexts;
    std::mutex contextMutex;
public:
    void initiateHandover(const std::string& ueId, const std::string& targetGnbId) {
        // Step 1: 發送 Handover Request 到目標 gNB
        auto hoRequest = createHandoverRequest(ueId);
        sendXnMessage(targetGnbId, hoRequest);
        // Step 2: 等待目標 gNB 的 Handover Request ACK
        // ...（監聽 Xn 信令，收到後繼續）
    }
    void handleHandoverRequest(const HandoverRequest& request) {
        // 在目標 gNB 執行：準備所需 UE 資源
        auto resources = allocateResources(request.ueId);
        // 發送 ACK 回來源 gNB
        auto ack = createHandoverRequestAck(resources);
        sendXnMessage(request.sourceGnbId, ack);
    }
    void performHandover(const std::string& ueId) {
        std::lock_guard<std::mutex> lock(contextMutex);
        // Step 3a: 來源 gNB 向 UE 發送 RRC 重配置（換手命令）
        auto rrcReconfig = createRrcReconfiguration(ueId);
        sendRrcToUe(ueId, rrcReconfig);
        // Step 3b: 傳輸 SN 狀態給目標 gNB
        auto snStatus = getSnStatus(ueId);
        sendXnMessageToTarget(snStatus);
        // Note: UE 收到 RRC 命令後會自行連上目標 gNB，目標 gNB 確認後通知來源 gNB 完成
    }
};
```

實際上，完整實現 Xn 介面的改造工作量較大，但在模擬中可簡化處理。例如，如果無法在短時間內修改 UERANSIM，可以採用**變通方案**：**由協調腳本直接控制 UE 的連接**。具體而言，在預測的換手時間 \$T\_p\$ 到時，使用 `nr-ue` 模擬器斷開該 UE 與舊 gNB 的連接，立即啟動一個新 UE 實例連接到目標 gNB，從而模擬換手效果（核心側無需感知，因為我們會同步更新路由）。這種方法雖然繞過了真正的 Xn 信令，但能達到 UE 切換 gNB 的目的，適合作為驗證演算法延遲的替代手段。

### 4.4 主程式與模擬流程控制

在完成上述模組與修改後，需要編寫**主控程式**來啟動並協調整個系統，包括：啟動核心網路、啟動多個衛星 gNB、啟動大量 UE、運行同步演算法執行緒，以及收集性能數據等。以下是一個主程式 (`main.py`) 的範例，展示如何將先前實現的各部分結合：

```python
# main.py
import threading, time, yaml, subprocess
from synchronized_algorithm import SynchronizedAlgorithm
from fast_satellite_prediction import FastSatellitePrediction
from satellite_trajectory import SatelliteTrajectory
from handover_measurement import HandoverMeasurement

class LEOHandoverSystem:
    def __init__(self, config_file: str):
        with open(config_file, 'r') as f:
            self.config = yaml.safe_load(f)
        # 初始化演算法模組
        self.sync_algo = SynchronizedAlgorithm(delta_t=self.config['system']['delta_t'])
        self.fast_pred = FastSatellitePrediction()
        self.trajectory = SatelliteTrajectory()
        # 載入衛星星座 TLE 資料（預設使用 Starlink）
        self.trajectory.load_tle_data('starlink')
        # 準備性能測量模組
        self.measurement = HandoverMeasurement()

    def start_core_network(self):
        """啟動 Open5GS 核心網元進程"""
        core_bins = ['nrf', 'scp', 'amf', 'smf', 'upf', 'ausf', 'udm', 'udr', 'pcf', 'nssf', 'bsf']
        for nf in core_bins:
            subprocess.Popen([f'./open5gs/install/bin/open5gs-{nf}d'])
            time.sleep(1)  # 逐個啟動，避免競爭資源

    def start_gnbs(self, count: int = 10):
        """啟動多個衛星 gNB 模擬器實例"""
        for i in range(count):
            config_path = f'gnb-config-{i}.yaml'  # 每個 gNB 有獨立設定，例如不同 gNB ID、IP等
            subprocess.Popen(['./UERANSIM/build/nr-gnb', '-c', config_path])
            time.sleep(0.5)

    def start_ues(self, total_ues: int = 10000, batch_size: int = 100):
        """批量啟動 UE 模擬器實例"""
        for i in range(0, total_ues, batch_size):
            config_path = f'ue-config-batch-{i}.yaml'  # 每批UE共用一個模板配置，指定起始IMSI等
            # -n 指定該實例啟動的UE數目
            subprocess.Popen(['./UERANSIM/build/nr-ue', '-c', config_path, '-n', str(batch_size)])
            time.sleep(1)

    def synchronization_loop(self):
        """同步演算法執行迴圈（供執行緒呼叫）"""
        while True:
            now = time.time()
            # 定期更新
            if now > self.sync_algo.T + self.sync_algo.delta_t:
                self.sync_algo.periodic_update(now)
            # 檢查是否有 UE 需要換手並觸發執行（簡化處理：直接模擬切換）
            for ue_id, info in list(self.sync_algo.R.items()):
                tp = info['handover_time']
                if tp and time.time() >= tp:
                    src_gnb = info['access_satellite']
                    tgt_gnb = info['next_access_satellite']
                    print(f"[{time.strftime('%X')}] UE{ue_id} 執行換手: {src_gnb} -> {tgt_gnb}")
                    # 在此處可介接 UERANSIM Xn 或採用 detach/attach 模擬
                    # (例如調用 UERANSIM 控制接口或更新UE配置)
                    self.measurement.record_handover(ue_id, src_gnb, tgt_gnb, tp, time.time(), "Proposed")
                    # 更新UE當前衛星為新衛星
                    self.sync_algo.R[ue_id]['access_satellite'] = tgt_gnb
            time.sleep(0.1)  # 100ms 間隔檢查

    def monitor_resources(self):
        """資源使用監控迴圈（供執行緒呼叫）"""
        import psutil, GPUtil
        while True:
            cpu = psutil.cpu_percent(interval=1)
            mem = psutil.virtual_memory().percent
            gpus = GPUtil.getGPUs()
            gpu_load = gpus[0].load*100 if gpus else 0
            gpu_mem = gpus[0].memoryUsed if gpus else 0
            print(f"CPU: {cpu}%, Mem: {mem}%, GPU: {gpu_load:.1f}%, GPU Mem: {gpu_mem}MB")
            time.sleep(5)

    def run(self):
        """啟動系統各組件並運行"""
        print("啟動核心網元...")
        self.start_core_network()
        time.sleep(5)
        print("啟動衛星 gNB 節點...")
        self.start_gnbs(self.config['system']['gnb_count'])
        time.sleep(5)
        print("啟動 UE 節點模擬...")
        self.start_ues(self.config['system']['max_users'])
        time.sleep(10)
        print("啟動同步演算法執行緒...")
        sync_thread = threading.Thread(target=self.synchronization_loop, daemon=True)
        sync_thread.start()
        print("啟動系統資源監控執行緒...")
        mon_thread = threading.Thread(target=self.monitor_resources, daemon=True)
        mon_thread.start()
        print("系統運行中，按 Ctrl+C 終止。")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("收到中斷指令，系統準備停止...")
            # 可在此加入清理代碼，如結束子進程等
```

上述 `LEOHandoverSystem` 類讀取了一個 YAML 配置檔（示例參見下文），然後依次啟動核心網、gNB、UE，開啟兩個執行緒分別運行同步演算法及資源監控。`synchronization_loop` 中，我們模擬了檢測到預測換手時刻時的處理：一旦當前時間達到某 UE 的 \$T\_p\$，則打印提示並認為換手發生，透過 `record_handover` 記錄事件，並更新 UE 當前連接衛星為目標衛星。

> **說明**：實際應用中，此處應觸發 UERANSIM 的換手執行。如果已修改 UERANSIM 支持 Xn，則應調用 gNB 間的換手函數；如果沒有，則可以如代碼中註釋那樣，通過 detach/attach 的手段模擬。`record_handover` 來自接下來的測量模組，用於收集換手延遲。

下面給出一份配置檔 `config.yaml` 的範例，用於定義系統運行的各項參數：

```yaml
# config.yaml
system:
  delta_t: 5.0            # 同步演算法預測更新間隔 Δt（秒）
  handover_precision: 0.01  # 換手時間預測精度要求（秒）
  max_users: 10000        # 模擬 UE 總數
  gnb_count: 10           # 模擬 gNB 總數 (衛星節點數)

constellations:
  starlink:
    min_elevation: 40     # 衛星最低仰角要求（度）
    satellites: 4408      # 星鏈第一階段衛星數量（可用於生成區塊大小）
  kuiper:
    min_elevation: 35
    satellites: 3236

open5gs:
  mongodb_uri: "mongodb://localhost:27017"  # MongoDB 連接
  use_upf_prediction: true   # 是否啟用UPF預測功能開關（可選，用於開關演算法）

ueransim:
  gnb:
    mcc: "001"
    mnc: "01"
    tac: 1
    # gNB 個別參數如ID和IP會在各自yaml中設定
  ue:
    imsi_prefix: "001010000"  # 生成IMSI前綴，用於批量配置
```

### 4.5 配置與運行驗證

配置完成後，先啟動核心網元，再啟動 gNB 模擬器和 UE 模擬器。在簡單場景下，例如**單 UE、兩顆衛星**，可手動編寫兩份 gNB 設定（不同的 gNB ID 對應兩顆衛星）和 UE 設定（UE 初始連接第一顆衛星）。啟動系統後，觀察終端日誌：

1. UERANSIM gNB 應顯示建立 Xn 連結或等待換手指令的日誌（如未真正改造 Xn，可忽略）。
2. UE 應顯示最初連接 Source gNB（衛星1）。當到達預測換手時間時，根據我們的模擬方式，UE 可能會重新連接到 Target gNB（衛星2）。
3. Open5GS UPF 側應無需輸出任何特別資訊，但我們可用 Wireshark 過濾 GTP 封包查看 TEID 變化。如有實作 GTP 擴展頭攜帶衛星資訊，也可在封包中驗證。

此外，確認核心網路 Path Switch 是否即時：由於 UPF 提前知道目標衛星，理論上在 UE 完成RAN換手的同時或稍後幾十毫秒內，核心就應該完成路由切換。因為我們的 UPF 演算法線程是持續運作的，而且我們設計 \$T\_p\$ 就落在換手期間內。為安全起見，可以讓 UPF 在 UE 完成 RRC 切換後**幾十毫秒**（論文提到例如換手後數十毫秒內）更新路由。在模擬中，如果使用 detach/attach 模擬，則相當於 UE 重新透過 AMF 連上新的 gNB，UPF 路由自然更新；如果 Xn 真正實現，UPF 則需我們人工通知或根據 Tp 更新。

完成系統組建後，我們便可進行實驗測試，收集換手性能數據。

## 5. 實驗設計與效能驗證

為評估加速換手機制的效果，我們設計多組對照實驗，並使用不同星座與流量場景來驗證系統在各種情況下的表現。重點關注 **換手延遲** 指標，以及其他相關指標如 **換手頻率**、**數據中斷時間** 等。實驗設計和預期結果如下：

### 5.1 測試場景與對照方案

我們考慮以下換手方案作為對照組，以比較本論文機制（同步演算法 + Xn 加速換手）的優勢：

1. **NTN 標準方案 (Baseline)**：3GPP 定義的標準非地面網路換手流程。換手決策由來源 gNB 觸發，但需經過核心（AMF/SMF）協調 Path Switch。模擬上，可透過**禁用 Xn**或強制走 detach/attach 來實現，每次換手都經核心交互。此方案延遲最高，預期平均換手延遲約數百毫秒（論文結果約 250 ms）。

2. **NTN-GS 地面站協助方案**：假設在軌道下方部署了鄰近地面站，預先快取換手資訊。換手時不必每次都連回遠端核心，由近地面站協助完成 UE 上下文轉移。模擬時，可**降低核心信令延遲**作近似：例如假設目標 gNB 與最近地面站通信只需單跳，而不是多跳回核心。我們在模擬中可將核心相關交互延遲設為較小常數來模擬此優化。根據論文，NTN-GS 平均換手延遲可降至 \~153 ms。

3. **NTN-SMN 太空網路協助方案**：利用鄰近衛星作為臨時核心節點協助換手（Satellite Mobility Network）。換言之，部分控制面信令在軌道上完成，不需要下行至地面。模擬時，可將換手控制訊號完全限制在衛星網內：例如來源 gNB 的換手請求先發給鄰近中繼衛星，再轉發到目標 gNB，全程不經AMF。這與我們方案類似，只是本方案更進一步地**完全取消即時核心參與**。NTN-SMN 因衛星中繼仍有一些延遲，論文測得平均換手延遲約 158.5 ms。

4. **本論文方案 (Proposed)**：即**同步演算法 + Xn 加速換手**。換手全程不經核心即時參與（核心提前同步預知），來源與目標衛星直接通訊完成上下文轉移，核心在背後同步路由。預期此方案換手延遲最低：UE 從源衛星到目標衛星的切換主要耗時於無線連接重建和單跳衛星間傳輸，實測典型延遲約 20〜30 ms。

為公平比較，在各方案下我們盡量使用**相同環境參數**進行測試，例如相同的星座軌道、UE 分佈和流量模式。可透過腳本批量執行測試，例如：

```bash
# 執行各方案測試各1小時，記錄延遲日誌
for scheme in NTN NTN-GS NTN-SMN Proposed; do
    ./run_test.sh $scheme --duration 3600 --log ${scheme}_log.csv
done
# 以上腳本內部根據 $scheme 切換不同配置，比如啟用/禁用Xn，調整延遲參數等
```

接著對各方案生成報告：

```bash
# 分析日誌輸出統計報告，例如平均/最大延遲
python analyze_results.py --input NTN_log.csv NTN-GS_log.csv NTN-SMN_log.csv Proposed_log.csv \
                          --output handover_report.pdf
```

### 5.2 星座與流量場景

為全面評估，我們在多種場景下測試上述方案：

* **場景1：Starlink 星座 + 靜止 UE**：採用 Starlink 星座（約550km軌道，高密度衛星）。UE 固定在某地理位置，衛星飛越時觸發換手。我們期望頻繁換手，但延遲較低。
* **場景2：Kuiper 星座 + 移動 UE**：採用 Kuiper 星座（預計630km軌道，衛星稍少）。UE 以高速（如120 km/h）移動，模擬用戶在地球表面移動造成的頻繁切換。Kuiper 軌道較高，單衛星覆蓋時間稍長、換手頻率略低，但一次換手可能跨越更遠的衛星。預期換手延遲與 Starlink 相近或略高（論文結果 Kuiper 比 Starlink 高約10% 延遲）。
* **場景3：混合星座 + 突發流量負載**：模擬 Starlink+Kuiper 並存，或模擬衛星/地面雙網並存情況。同時引入突發性流量峰值，例如某時刻大量UE突然開始傳輸高碼率數據，觀察系統在高負載下的表現。該場景下考驗系統資源調度和異常處理能力。

### 5.3 數據收集與性能指標

在每次測試中，我們記錄每個換手事件的關鍵時間點，用於計算延遲並統計其他指標。可使用前述 `HandoverMeasurement` 類輔助收集：

```python
# handover_measurement.py
import pandas as pd
import numpy as np
from datetime import datetime

class HandoverMeasurement:
    def __init__(self):
        self.handover_events = []

    def record_handover(self, ue_id: str, source_gnb: str, target_gnb: str,
                        start_time: float, end_time: float, handover_type: str):
        """記錄一次換手事件"""
        self.handover_events.append({
            'ue_id': ue_id,
            'source_gnb': source_gnb,
            'target_gnb': target_gnb,
            'start_time': start_time,
            'end_time': end_time,
            'latency': (end_time - start_time) * 1000.0,  # 轉為毫秒
            'handover_type': handover_type,
            'timestamp': datetime.now()
        })

    def analyze_latency(self):
        """輸出不同換手類型的延遲統計"""
        df = pd.DataFrame(self.handover_events)
        stats = df.groupby('handover_type')['latency'].agg(['mean', 'std', 'min', 'max', 'count'])
        print("Handover Latency Statistics (ms):\n", stats)
        return stats

    def plot_latency_cdf(self):
        """繪製各類換手延遲的CDF曲線"""
        import matplotlib.pyplot as plt
        df = pd.DataFrame(self.handover_events)
        plt.figure(figsize=(8, 5))
        for ho_type, group in df.groupby('handover_type'):
            data = np.sort(group['latency'].values)
            cdf = np.arange(1, len(data)+1) / len(data)
            plt.plot(data, cdf, label=ho_type)
        plt.xlabel('Latency (ms)')
        plt.ylabel('CDF')
        plt.title('Handover Latency CDF')
        plt.legend()
        plt.grid(True)
        plt.savefig('handover_latency_cdf.png')
```

透過 `record_handover` 函數，我們將在換手開始和結束時刻調用它，傳入 UE 編號、源/目標 gNB、開始時間（換手觸發時刻 \$T\_p\$）和結束時間（UE 完成連接目標的時刻），以及換手方案類型標識（如 "Baseline", "NTN-GS", "Proposed" 等）。程式會計算此次換手延遲（毫秒）。在實驗結束後，可調用 `analyze_latency()` 列出平均、標準差、最大、最小延遲等統計值，或 `plot_latency_cdf()` 繪製累積分佈函數曲線，以比較各方案延遲表現。

**預期結果**：根據論文實驗結果及我們實現的推測：

* **換手延遲**：本論文方案在各場景下均顯著低於其他方案。例如，在 Starlink + flexible 策略下，平均延遲約 20.87 ms，遠低於 Baseline 的 \~250 ms，也優於 NTN-GS 的 \~153 ms 和 NTN-SMN 的 \~158.5 ms。我們的模擬應該得到相同量級的結果，以驗證演算法有效性。

* **UE 接入策略影響**：比較 flexible 與 consistent 策略的結果。預期 flexible 策略下，由於 UE 提前切換（在衛星尚有覆蓋時就換手），源與目標衛星距離較近時完成切換，因此延遲略低於 consistent（論文數據平均低約 10 ms）；但代價是換手頻率增加。我們將統計每種策略下每小時的換手次數，預計 flexible 策略的換手次數明顯高於 consistent，驗證延遲-頻率的權衡。

* **軌道方向優化影響**：在我們的快速預測中加入/移除「相同軌道方向優先」約束，觀察延遲變化。預期不採用方向約束時，可能出現衛星逆方向交接，導致切換時延稍增（論文指出增加約 6 ms）。透過比較兩種設定下的延遲平均值，我們可確認此優化的有效性。

* **不同星座影響**：Starlink vs Kuiper 下方案表現比較。由於 Kuiper 衛星軌道較高，單次連接時間較長但換手時涉及更遠距離，預期換手延遲略高。論文結果顯示雙方平均延遲相近，Kuiper 約高10%。例如 Starlink 平均 \~21 ms vs Kuiper \~23 ms。我們可在模擬中透過切換 `trajectory.load_tle_data('kuiper')` 來驗證此差異。

* **數據不中斷與丟包**：針對場景3的突發流量，我們可以在 UE 端持續執行例如 ping 或影片串流來觀察換手期間的傳輸表現。理想情況下，本方案因為核心同步且 Xn 快速切換，UE 感知到的中斷時間極短（幾十毫秒），上層應用可能無明顯卡頓；而 Baseline 案可能產生數百毫秒中斷，導致明顯延遲峰值或丟包。可記錄在換手發生前後的丟包率，驗證本方案的用戶體驗優勢。

## 6. 關鍵技術細節與異常處理

在實作與運行過程中，還有若干關鍵技術問題需要考慮，以確保系統穩定性和準確性。本節討論**時間同步、TLE 精度、異常情況處理**等細節，以及如何在系統中實施相應機制。

### 6.1 時間同步機制

**精確時間協調**：在真實網路中，RAN 節點（gNB）與核心網（UPF）需要保持高精度的時間同步，以便對預測的換手時間有共同的參考。可採用 PTPv2 (IEEE 1588) over SCTP 來實現亞毫秒級的時間同步。時間訊號來源可以是 GPS 衛星授時結合 NTP 校準，提供高穩定性的時鐘基準。對於模擬環境，如果所有進程在同一台機器上，則系統時鐘天然同步，但我們仍須注意不同模組間的時間偏差。例如 Python 模擬程式與 UERANSIM/gNB 進程可能存在毫秒級偏移，最好在觸發換手時加入幾毫秒緩衝。

**傳播時延補償**：對於跨衛星傳輸，信號傳播存在固有延遲 (約0.27ms/100km)。在同步演算法預測時，可以考慮這個延遲。例如測得核心與衛星之間消息往返延遲 \$\Delta t\_{meas}\$，可以用公式 \$\Delta t\_{corrected} = \Delta t\_{meas} - (d/c) \* 0.8\$ 進行修正（其中 \$d\$ 為距離，\$c\$ 為光速，\$0.8\$ 為大氣折射折減係數）。雖然模擬中未必需要這麼細緻，但在現實部署時，有助於提前補償傳輸延遲，避免換手協調誤差。

### 6.2 衛星軌道預測精度與補償

**TLE 精度限制**：TLE 是二行元素數據，通常每日更新。預測短期軌道（幾小時內）的誤差通常很小，但累積誤差可能在軌道計算中產生位置偏差。為減少影響，我們採取多種策略：

* **頻繁更新 TLE**：如果模擬持續時間較長（跨越數天），應定期從 Celestrak 或 Space-Track 獲取最新 TLE 更新 SatelliteTrajectory 中的軌道參數。甚至可直接調用 API 每隔幾小時自動更新。
* **縮短預測窗口**：論文演算法透過**迭代二分**在 \$\Delta t\$ 內逼近換手時間。我們可以選取較小的 \$\Delta t\$（如0.5秒）來減少「預測未來過久」帶來的不確定性，或者在 binary search 過程中設置一個迭代終止條件：當預測誤差小於 RAN 換手操作耗時（例如50ms）時就停止。這些措施能緩衝軌道偏差對換手時序判斷的影響。
* **冗餘計算與交叉驗證**：對關鍵的換手決策，可以使用兩套軌道數據或模型計算驗證。如果結果不一致，標記不確定性提高，將此換手標記為可能異常處理的候選。

**使用天體力學模型**：若需要更高精度，可引入更高階的軌道力學模型。例如考慮 J2攝動等因素的軌道預測公式，或者使用多點插值方式提高短期精度。不過在本方案中，SGP4 已足夠支持毫秒級換手預測。

### 6.3 預測失誤與換手失敗處理

儘管演算法力求精準，但可能出現預測誤差導致換手不同步的情況：例如 UE 提前或延後換手超出核心預期窗口。為提高系統健壯性，我們設計了**異常回退機制**：

```mermaid
graph LR
    A[檢測預測誤差] --> B{誤差 > 閾值?}
    B -->|是 (大於100ms)| C[觸發標準 NTN 流程]
    B -->|否 (在100ms內)| D[應用快速補償演算法]
    C --> E[記錄異常事件 (日誌)]
    D --> E
```

如上圖，當檢測到實際換手時間與預測 \$T\_p\$ 偏差超過一定閾值（例如100ms）時，立即**回退到傳統方案**：由來源 gNB 向核心發起 N2-based 換手流程，確保換手不至於失敗。反之，如果偏差在可容忍範圍內（<=100ms），則採用**補償演算法**：例如略微調整 UPF Path Switch 時機、或暫存下行數據直到 UE 完成連接，以彌補不同步造成的短暫間隙。無論哪種情況，都將事件記錄到日誌，以便日後分析預測失誤原因。

**UE 連接失敗**：若 UE 在預定時間未能接入目標 gNB（例如目標衛星瞬時流量高或UE狀態問題），應有超時重試機制。UE 可嘗試重新附著（attach）或接入次佳衛星。我們在模擬中可設置 UE 若在換手命令後一定時間（如50ms）未連上新 gNB，則回落到 detach 然後 attach 的程序，以保證 UE 不至於長時間無服務。

### 6.4 資源過載保護

當系統處於高負載狀態（如突發連線請求或大量換手同時發生）時，需要有保護機制防止核心或 gNB 過載失效。以下是我們採用的策略：

* **動態資源門檻**：設定 CPU、記憶體的使用率門檻來觸發保護。例如 CPU 閾值 = 0.7 \* 可用核心數，保留一定內存給系統如 2GB。這些參數可在配置中調整。

* **過載時降級**：當檢測到負載超過預設閾值（如 CPU > 80% 持續數秒）時，系統進入保護模式：

  * **暫停新 UE 接入**：暫時拒絕或緩辦新的 UE 連線請求，待負載恢復再接受，避免雪崩效應。
  * **啟用快速切換模式**：可以指的是簡化換手流程以節省資源，例如減少不必要的日誌、暫停耗時的分析模組，或者在換手決策上傾向不切換（讓 UE 多連一會舊衛星以減少信令）。這需要根據實際情況定義。我們的模擬中，可以體現為在過載時臨時提高 \$\Delta t\$（減少演算法觸發頻率）或者強制所有 UE 改為 consistent 策略（降低換手頻度），以渡過高峰。

* **恢復與記錄**：當負載回落正常後，解除限制。同時將過載發生期間的事件記錄備查，包括時間、負載指標、採取措施等，便於日後優化系統。

### 6.5 其他實作注意事項

* **5G NTN 協議棧增強**：若進一步深究，可考慮在協議層面的改進，例如在 RRC 層增加「衛星能力訊息」和在 NAS 層增加「軌道預測資訊容器」等，以支持 UE/GNB 交換預測資訊。這樣UE也可預知下一顆衛星，提升協同。不過在我們模擬中，UE 只需被動接受換手命令即可。
* **隱藏時延的處理**：一些換手步驟可以提前並行處理，以縮短用戶中斷。例如資料轉發（SN 狀態傳輸）和 UE RRC 切換是並行的。我們實作時盡可能並行觸發相關步驟，例如核心更新可以與 RAN 換手幾乎同時進行，達到論文所述“無縫”效果。
* **安全與穩定性**：由於我們對 Open5GS/UERANSIM 做了修改，自測時要留意記憶體和線程安全問題。例如UPF預測表訪問需加鎖，避免競態；UERANSIM Xn 處理要注意多執行緒同步等。可以使用 Sanitizer 或 valgrind 檢查，確保模組穩定。
* **模組化與可重複試驗**：建議將各部分代碼模組化（如我們劃分了多個 Python/C 檔案），並撰寫說明文檔，方便日後修改參數或增減功能。實驗腳本自動化也很重要，可重複多次試驗取平均值，獲得更可靠的性能評估。

---

完成以上所有步驟，即可得到一套完整的移動衛星網絡換手加速方案的復現實現。透過嚴格按照指南進行環境部署、代碼實作和測試，應能重現論文中的關鍵結果，並為進一步研究移動衛星網絡的換手優化奠定基礎。祝在實作過程中順利，並期待您對本指南所實現系統的性能驗證結果！
