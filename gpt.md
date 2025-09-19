LEO 衛星網路換手（Handover）流程與挑戰

LEO（低軌衛星）網路面臨高速移動與遠距離傳輸的挑戰，導致換手（HO）程序延遲增大、能耗提升和資源衝突。依據 3GPP NR 標準，換手一般分成測量（Measurement）、決策（Decision）、準備（Preparation）、執行（Execution）和完成（Completion）五個階段

。在傳統 HO 流程中，基地台（gNB）和用戶裝置（UE）首先測量 Serving 與 Target 小區的信號品質，若符合事件觸發條件（如 TS 38.331 中的 A3 事件，表示目標小區信號優於當前 Serving 小區一定閾值），UE 即發送**測量報告（MR）**給 Serving gNB，由 Serving gNB 再向 Target gNB 請求換手。換手完成後，UE 通過隨機接入（RACH）程序接入 Target gNB。

在 LEO 網路中，由於信號往返傳輸時間極長（單程可達數十毫秒），任何上行訊令都很可能過時。此外，大量用戶同時換手會引發資源請求衝突（collision）。例如，許多 UE 同時收到 A3 事件觸發並發送 HO 請求，可能造成目標衛星資源不足（RB 衝突）或隨機接入前導碼衝突。因此，必須設計新的 HO 協議來減少延遲、降低衝突率，並兼顧成功換手率。

研究方法與核心貢獻

本論文提出了一種稱為 DHO (Deep Handover) 的新型 HO 協議，利用深度強化學習（DRL）優化 LEO 衛星換手流程。其核心思想是跳過傳統流程中的測量報告階段，讓 Serving 衛星代理（agent）直接根據局部觀測資訊預測並決定 HO 動作（HO Request），從而消除 MR 引入的長程延遲。DHO 融合了衛星已知的軌道模式訓練 DRL 模型，使 Serving 衛星能夠憑自身觀測（如 UE 的存取狀態）來估測何時該執行換手，避免 UE 必須花費大量上行功率回報 MR 信號。

主要創新點包括：

新穎的 HO 協議設計（DHO）： 專為可再生型 LEO 衛星設計，重構傳統 HO 流程，利用在地（locally observable）的資訊做決策。例如，DHO 只使用哪些 UE 已完成換手的二元指標，以及上一次換手動作，完全不需要衛星位置等額外資訊。

跳過測量報告、降低延遲： DHO 在準備階段省略 MR 步驟，只讓 Serving 衛星根據預測直接發出 HO 請求，省去來回傳送的長延遲。實驗結果證實，即使省略 MR，DHO 仍能做出有效換手決策，顯著降低存取延遲（access delay）並減少功耗。

強化學習算法（IMPALA）： DHO 採用IMPALA（Importance-weighted Actor-Learner Architecture）的 DRL 框架。IMPALA 利用多個平行演員-學習器（actor-learner）非同步更新，搭配 V-trace 演算法校正策略滯後，能有效處理高維度狀態與動作空間。相較其他 DRL 演算法（如 DQN、A3C、PPO），IMPALA 具有收斂穩定性更高的優勢（論文附錄 B 有詳細比較）。

效能評估與結論： 模擬結果顯示，DHO 在各種網路條件下均優於傳統 HO 協議和基準隨機策略。具體來說，在資源充足的情況下，DHO 的平均存取延遲比傳統 HO 快約 6.8 倍，在資源稀缺時亦快 5 倍以上。此外，在可用隨機接入前導碼數量改變的測試中，DHO 最大可達 4.83 倍的延遲提升。從 DHO agent 的決策行為觀察到，DHO 會根據網路資源狀況在優先降低延遲或避免衝突之間取得平衡，體現了其學習到的靈活策略。

強化學習詳解：IMPALA、State/Action/Reward 及超參數 DHO 將換手決策問題建模為一個強化學習（RL）場景，其中 狀態（State）、動作（Action）、獎勵（Reward） 定義如下：

狀態 (State): 表示時間步長 𝑡 及網路當下情況的向量。具體而言，DHO 的狀態包括時間指標 𝑡 (可正規化後有單位時間)、以及所有 UE 是否已完成換手的二元指標向量 𝑜𝑡𝑢otu。其中也加入了上一次各 UE 的換手動作作為「指紋」，以穩定學習。這些資訊都是「在地可觀測」(locally observable)，不需要全網路的全局狀態。例如，如果第 u 個 UE 在當前時刻已完成換手，狀態向量對應分量為 1，否則為 0。

動作 (Action): 表示 Serving 衛星對所有 UE 的換手請求決策。每個 UE 在每個 HO 機會時刻可選擇「對哪一個目標軌道平面 Satellite 發 HO 請求」或「不發送任何 HO 請求」。因此對於每個 UE，動作使用one-hot 編碼：一個動作向量對應某個目標衛星軌道，若選擇「無換手」，則編碼為零向量。整體動作 𝑎𝑡at 是包含所有 UE 動作的組合，每步只能選一個方向發送 HO 請求。

獎勵 (Reward): DHO 的獎勵設計是要最小化存取延遲與衝突率。因此，他們定義目標函數（公式 (12)）將平均存取延遲與碰撞率加權相加。演算法中採取獎勵 𝑟𝑡rt 為該目標函數的負值（即延遲與碰撞越低，獎勵越高）。其中有一個正規化係數平衡延遲與碰撞的重要性，可調整策略偏好（論文第 V-D 節表 VII 描述這權重變化對效能的影響）。

算法與超參數： DHO 使用 IMPALA 演算法。IMPALA 是一種離線（off-policy）的分布式強化學習方法，結合多個演員產生經驗和重要性抽樣校正（V-trace）來穩定學習。主要訓練超參數包括折扣因子 γ（通常 0<γ<1，例如 0.99），學習率等。論文設定了適當的學習率和批次大小（訓練參數見表III），並使用熵正則化（entropy bonus）鼓勵探索，避免過早收斂

。訓練過程會持續多個時間步及回合，直到累積獎勵收斂。與此同時，研究也在附錄 B 比較了其他 DRL 算法（DQN、A3C、PPO）的性能，結果顯示 IMPALA 在高維狀態/動作空間下收斂更快、更穩定。

基準方法比較： 文中實驗使用了兩種基準換手策略作對照
：(1) 傳統 4G/5G HO 協議：以 3GPP 定義的 A3 事件（鄰區信號比服務信號高一定門檻）觸發換手，UE 做常規 RSRP 測量並送 MR。實驗中將事件 A3 作為主要觸發條件（腳註提到亦可用 A2、A4、A5 等）。(2) 隨機（Random）策略：每次 HO 機會隨機選擇目標，忽略信號品質；此方法雖然簡單，但容易造成頻寬和前導碼衝突。結果顯示，DHO 在上述所有條件下均遠超這兩種基準方法，特別是在可用資源（RB 數量或前導碼數量）不足時仍可有效降低延遲。

3GPP 事件與觸發條件對應

論文將換手觸發條件與 3GPP TS 38.331 定義的測量事件相對應。在 Table I 中列出了事件 A1–A5 的條件：
A1： 服務小區信號強度超過門檻（主要用於停止測量）。
A2： 服務小區信號強度低於門檻。
A3： 目標小區信號強度優於服務小區一定偏移量（OFFSET）。
A4： 目標小區信號強度超過門檻。
A5： 服務小區信號低於門檻 1 且目標小區信號高於門檻 2。
上述 A1–A5 與 TS 38.331 對應，並已被論文直接引用。論文中明確指出，傳統換手協議主要使用 A3 事件 作為換手觸發條件
（※ 註腳提及可替換為 A2、A4 或 A5）。換手決策還會搭配手差（HOM）與觸發時長（TTT）做進一步判斷。

論文中並未提及 TS 38.331 中的其他事件（如 A6、B1–B2、C1、D1–D2、T1 等）。若推測對應關係，可認為：

A6 事件（多載波中鄰小區較次要 Serving 優勢）主要用於載波聚合，與單一衛星 HO 無關，因此未使用。
B1/B2（異系統測量事件）與衛星 HO 無關。
C1（空閒模式測量）與本研究目標不符。
D1/D2（LTE-to-NR 掉話機制）與 HO 無關。
T1 事件 通常與定時或距離相關，如持續時間門檻，論文未明示使用，但可視為在模擬中固定 HO 時隙間隔（如 𝑇𝐻TH 時間槽）之類同機制。

總之，論文直接利用 TS 38.331 中定義的 A1–A5 事件條件
來描述換手觸發，並在基準方案中使用 A3 事件。若引入其他觸發邏輯（如距離或時間閾值），可對應為類似 A4/A5 或延時觸發，但論文並未明示此類設定，主要聚焦於信號強度門檻。

論文章節架構與創新總結

論文分為以下章節：

第 I 節 緒論：說明 LEO 衛星網路換手問題及研究動機。
第 II 節 相關研究：回顧現有非地面網路（NTN）換手機制與先進方法。
第 III 節 LEO 衛星換手背景：介紹衛星 HO 的傳統流程（準備、執行、完成階段）
，並分析 LEO 特有挑戰（長延遲、覆蓋大、資源有限）及老舊 MR 問題。表 I 列出 5G 換手事件 A1–A5 的判斷條件。

第 IV 節 基於 DRL 的換手協議設計：提出 DHO 算法及評估方法。子節包括：IV-A 網路場景（衛星軌道與 UE 分布模型），IV-B 性能指標（碰撞率、存取延遲、HO 成功率定義），IV-C MDP 模型（狀態/動作/獎勵定義與目標函數 (12)）；IV-D 算法細節（IMPALA 介紹、V-trace 更新等）；IV-E 複雜度分析（簡化 HO 與訓練複雜度）。

第 V 節 模擬結果：展示 DHO 的效能。包括 V-A 模擬設置（環境參數見表 III）、基準方法說明；V-B 性能分析（考察 RB 數量和前導碼數量對延遲和碰撞率的影響，圖表呈現比較結果）；並分析不同訓練參數影響及 DHO 行為（表 VI、VII 顯示策略分佈與延遲/碰撞權重平衡）。

第 VI 節 結論與未來工作：總結 DHO 的優勢與適用性，並提出未來可改進方向。

創新點總結： 本文提出的 DHO 協議針對 LEO 衛星網路的問題做出了多項創新：（1）重新設計 HO 流程，利用區域可觀測資訊來決策；（2）跳過量測回報，直接在交換階段作出預測，顯著降低存取延遲；（3）採用分布式 DRL（IMPALA）有效處理大規模網路環境；（4）實驗表明 DHO 在多種網路條件下大幅優於傳統方法，在存取延遲、碰撞率和換手成功率方面都有一致的提升。

Mermaid 流程圖節點與性能指標建議

流程圖草稿（Mermaid nodes & connections）： 可繪製 DHO 換手流程的活動圖，主要節點可包括：
UE 量測階段：UE 周期性量測 Serving 與鄰區衛星的 RSRP（傳統有此步驟，但 DHO 中可略過 MR ）。觸發判斷：根據事件 A1–A5 條件（例如 A3: 目標 RSRP 優於服務 RSRP+偏移）判斷是否觸發換手。

HO 決策 (DHO 模型)：如果觸發換手，Serving 衛星代理根據學習到的策略（State → Action）決定「對哪個目標衛星發 HO 請求」或「本時段不換手」。

執行階段：一旦決定換手，Serving 衛星向 UE 下達 HO 命令，UE 開始切換並進行 RACH 隨機接入。此處可能產生前導碼衝突或資源不足衝突。

換手完成：UE 成功接入 Target 衛星並傳送 HO 完成訊息，Serving 釋放資源。若失敗，UE 保留原衛星或重試。節點連線可顯示：從量測→判斷→決策→執行→完成的流程；並標記出 DHO 與傳統流程的差異（如 DHO 省略 MR 步驟）。此外可加入並行動作：多個 UE 同時觸發換手請求，最終可能導致衝突。

性能指標與圖表建議： 主要評估指標包括 存取延遲 (Access Delay)、碰撞率 (Collision Rate)、換手成功率 (HO Success Rate)。可採用如下圖表呈現：

延遲與碰撞對比圖（Bar Chart）：如圖表顯示 DHO、傳統 HO、隨機策略在不同資源情境下（e.g. 不同 RB 數、前導碼數）下的平均存取延遲和碰撞率對比。表格 IV、V 及圖 5、6 就是這類圖表的示例。
CDF 曲線：繪製存取延遲的累積分布函數（CDF），比較各方案延遲的整體分佈差異，有助觀察極端情況下的性能。
時間序列：如果關注學習過程，可繪製訓練過程中累積獎勵或損失函數隨迭代次數變化的曲線，觀察算法收斂。
折衷圖（Trade-off Scatter or Pareto Curve）：改變獎勵中延遲與碰撞的權重比例，繪製不同策略下延遲與碰撞率的關係圖（如表 VII 所示）。
策略行為統計（Pie/Bar Chart）：顯示 DHO 在不同場景（如資源充足 vs 不足）下選擇發送 HO 請求的概率（表 VI）或不換手的比例。
鍛鍊過程圖：在附錄分析中，可繪製不同 DRL 算法的訓練收斂曲線，強調 IMPALA 的收斂優勢。
以上圖表以 Bar chart 和 Time series 曲線為主，也可加入 CDF 或散點圖來豐富比較。關鍵是突出 存取延遲、碰撞率 與 換手成功率 之間的關係和 DHO 與基準方法的差異。

參考來源

本文所有技術內容與結論均基於論文原文所述資料，例如 DHO 協議設計與實驗結果，狀態/動作/獎勵定義，以及 3GPP 換手事件說明等。上述引用可供後續驗證。

好的 — 我會以清楚、有條理的方式把 **DHO（論文提出的 Handover 協議）** 與 **IMPALA（用於訓練 DHO 的 DRL 演算法）** 的內容、流程、所有重要變數與符號一一拆解說明，並標註論文中對應的章節／方程式位置，方便你回到原文驗證。說明會分成三大部分：
(一) DHO（問題建模 + 執行流程 + 變數定義），(二) IMPALA（演算法機制、V-trace 推導與更新規則、演員–學習器流程），(三) 實務/調校要點與訓練細節。

---

# (一) DHO：問題建模、執行流程與變數定義（來自論文 Section IV）

> 核心概念：把 LEO HO 問題建成一個 MDP（部分觀測），由 **serving-SAT 當作 agent**，在每一個 HO 機會（time slot）觀察局部 state、輸出對每個 UE 的 HO 請求動作（或不送出），目標是同時**最小化 access delay 與 collision rate**。相關公式詳見論文 IV-C、IV-D（公式 (11)–(16) 等）。【IV-C；公式(11),(12),(15),(16)】。

## 1. 目標函數（論文式子）

論文把優化目標寫成（式 (11)）：

$$
\min_{a_j[n]} \sum_{n=1}^{N} \big( D[n] + \nu\, C[n] \big)
$$

其中 $\nu$ 為權重，用於平衡延遲 $D[n]$ 與碰撞率 $C[n]$（見 Sec. IV-C, Eq.(11)）。獎勵在 RL 中取作該目標的負值（式 (15)）：

$$
r[n] = -D[n] - \nu C[n]. \tag{15}
$$

【IV-C；Eq.(11),(15)】。

---

## 2. State / Action / Reward（MDP 定義，Sec. IV-C）

### State（狀態） — 論文給定（式 (12)）

$$
s[n] = \{\, n,\; a^{\text{HO}}[n],\; a[n-1] \,\} \tag{12}
$$

* $n$：當前 HO 時間索引（time slot index）。
* $a^{\text{HO}}[n] = \{a^{\text{HO}}_1[n],\dots,a^{\text{HO}}_J[n]\}$：每個 UE 是否已完成 HO 的二元指標（1: 已完成 HO，0: 尚未完成）。
* $a[n-1]$：前一時間步的動作（用作 fingerprint，幫助穩定 experience replay）。

> 設計意圖：state 僅使用「在地可觀測（locally-observable）」資訊（不需要衛星精確位置），以降低資訊收集成本並加速收斂。【IV-C；Eq.(12)；相關敘述】。

### Action（動作） — 每個 UE 的 HO 請求（式 (3),(13),(14)）

對於 UE $j$ 在時刻 $n$，動作定義為：

$$
a_j[n] \in \{0,1,\dots,K-1\}
$$

其中 $K$ 為軌道平面（orbital planes）數量，且 $a_j[n]=0$ 表示「不發 HO Request」（等待下一個 HO 機會）。論文用**one-hot** 表示：

$$
a_j[n] = \{a_0,a_1,\dots,a_{K-1}\},\quad \sum_{k=0}^{K-1} a_k = 1. \tag{13}
$$

整體動作向量把所有 UE 的動作堆疊：

$$
a[n] = [a_1[n], a_2[n], \dots, a_J[n]]^\top. \tag{14}
$$

> 意義：agent (serving-SAT) 在每個 HO 機會一次輸出 J 個 one-hot 子動作（每個子動作選擇「哪個目標軌道」或「不換手」）。【IV-C；Eq.(3),(13),(14)】。

### Reward（獎勵） — 與效能指標直接關聯（式 (15)）

如上所述，獎勵是負的目標函數：$r[n] = -D[n] - \nu C[n]$，直接把系統級效能（延遲與碰撞）反向映射為要最大化的回報。調整 $\nu$ 可改變 agent 在**優先降低延遲**或**優先降低碰撞**間的取捨（Sec. V-D, Table VII）。【IV-C；Eq.(15)；V-D 表 VII】。

---

## 3. 關鍵中介/輸入量與指標（方程式與解釋，Sec. IV-B）

### Access delay $D[n]$（式 (9)）

論文以簡化方式定義平均存取延遲（per time-slot 指標）：

$$
D[n] = \frac{1}{|J|}\sum_{j\in J} \big(1 - a^{\text{HO}}_j[n]\big). \tag{9}
$$

解釋：在時刻 $n$，若 UE j 尚未完成 HO ($a^{\text{HO}}_j[n]=0$)，則會被計入延遲量；此式實際代表「尚未完成 HO 的 UE 比例」，可與實際耗時尺度相乘得到時間值。【IV-B；Eq.(9)】。

### Collision rate $C[n]$（式 (4)–(8)）

Collision 分兩類：

1. **Target RB NACK（資源不足）**：對於 target-SAT $k$，若收到的 HO Request 數量超過可用 RB（$R_k[n]$），則會發生 NACK 類 collision。定義請求指標：

$$
h^R_{k,j}[n] = \begin{cases}1 & \text{若 } a_j[n]>0,\ a^{\text{HO}}_j[n]=0,\\ 0 & \text{否則.}\end{cases} \tag{4}
$$

並定義對應的 collision rate（式 (5)）：

$$
CR_k[n] = \begin{cases}
0 & \text{if }\; R_k[n] - \sum_j h^R_{k,j}[n] > 0,\\
\frac{\sum_j h^R_{k,j}[n] - R_k[n]}{|J|} & \text{otherwise.}
\end{cases} \tag{5}
$$

（簡化說：若請求>資源，超過比例為 collision。）【IV-B；Eq.(4),(5)】。

2. **PRACH（preamble）碰撞**：當多個 UE 選到相同 preamble 進行 RACH，會發生 PRACH collision。定義碰撞指示（式 (6)）：

$$
c^P_j[n] = \begin{cases}1 & \text{if }(h^C_j[n],p_j[n])=(h^C_{j'},p_{j'}[n])\ \text{for some}\ j'\neq j,\\ 0 & \text{otherwise.}\end{cases} \tag{6}
$$

並取平均得到 $CP[n]$（式 (7)）。最後總 collision：

$$
C[n] = \sum_{k=1}^{K-1} CR_k[n] + CP[n]. \tag{8}
$$

變數說明：$R_k[n]$ = 可用 RB 數；$p_j[n]$ = UE j 選的 preamble（uniform random）；P = preamble total 數量；$h^C_j[n]$ = 是否收到 HO Command（target-SAT 承認）。【IV-B；Eq.(6),(7),(8)；相關段落】。

---

## 4. DHO 的執行序列（Protocol sequence，Sec. IV-C）

論文將 DHO 流程簡化為四個步驟（序列略同 Fig.4）【IV-C】：

1. **HO Decision（決策）**：serving-SAT agent 根據 $s[n]$ 決定 $a[n]$（對每 UE 是否送 HO Request 以及送給哪一 target-SAT）。【IV-C，Sequence】
2. **HO Admission（入網承認）**：target-SAT 若有足夠 RB，回 ACK；serving-SAT 向被允許的 UE 發 HO Command。
3. **Random Access（RACH）**：UE 收到 HO Command 後以隨機前導碼發起接入；可能產生 PRACH collision。
4. **HO Completion（完成）**：若接入成功，UE 設定 $a^{\text{HO}}_j[n]=1$；否則保留在原 Serving 或重試。

> 關鍵設計：DHO **跳過** UE → Serving 的 Measurement Report（MR）步驟，改由 serving-SAT 自身預測/決策以節省往返延遲與 UE 上行功率（Sec. IV-C 說明）。【IV-C；Sequence；Fig.4】。

---

# (二) IMPALA：機制、V-trace 及訓練更新（論文 Section IV-D 與 Algorithm 1）

論文選擇 **IMPALA**（Importance-weighted Actor-Learner Architecture）來訓練 DHO，原因是 IMPALA 能處理**大狀態/動作空間**與\*\*分散式演員（actors）\*\*收集資料的情況，並用 **V-trace** 來校正行為政策（behavior policy）與目標政策（target policy）之間的差異（policy-lag）。【IV-D；Algorithm 1】。

---

## 1. 高層架構（actor-learner）

* 多個 **actor**（平行環境實例）依照當前 learner 的 policy 輪流與環境互動，收集經驗序列 $\xi = (s,a,r,s')$，存入本地 replay buffer $D_i$。【Algorithm 1 Step 3–11】
* actor 會定期把經驗與行為 policy $\mu_{\theta_i}$ 上傳給 learner。Learner 接收來自各 actor 的資料，計算更新（policy/value），並把新的參數回傳給 actors（Algorithm 1 Step 12–14）。【Algorithm 1】
* 優勢：可大幅並行採樣，提升樣本效率；缺點：actor 與 learner 間存在 policy 滯後，需要 off-policy 校正（下述 V-trace）。【IV-D 說明】。

---

## 2. V-trace（離線校正目標）：數學式與變數定義（論文 Eq.(16) 及後續敘述）

### V-trace 目標 $v[n]$（式 (16)）

對於由行為政策 $\mu$ 產生的一段軌跡 $(s[t],a[t],r[t])_{t=s}^{s+k}$，定義 k-step V-trace 目標：

$$
v[n] = V(s[n]) + \sum_{t=n}^{n+k-1} \gamma^{t-n}\Big(\prod_{i=n}^{t-1} c[i]\Big)\, \delta^V_t
$$

其中

$$
\delta^V_t = \rho[t]\big( r[t] + \gamma V(s[t+1]) - V(s[t])\big).
$$

* $\rho[t] = \min(\bar{\rho},\; \frac{\pi(a[t]\mid s[t])}{\mu(a[t]\mid s[t])})$：**截斷的重要性權重（IS weight）**，用來校正使用行為政策收集資料但希望估計目標政策的情況。
* $c[t] = \min(\bar{c},\; \frac{\pi(a[t]\mid s[t])}{\mu(a[t]\mid s[t])})$：類似但通常較小的截斷係數，用於乘積項以控制方差。
* $\bar{\rho}$ 與 $\bar{c}$ 是截斷上界，且 $\bar{\rho}\ge\bar{c}$。論文說明 $\bar{\rho}$ 影響收斂到何種 value function，而 $\bar{c}$ 影響收斂速度（Sec. IV-D 描述）。【IV-D；Eq.(16)及後段說明】。

**註**：上述寫法與論文式 (16) 同義（論文使用相同記號 ρ 與 c 及截斷）。V-trace 的作用是以 truncated importance sampling 把 off-policy sample 的偏差做修正，同時避免極端 ratio 導致巨大方差。

---

## 3. 更新規則（value 與 policy gradient）

* **Value update（以 $v[n]$ 為目標）**：最小化 L2 loss：

$$
\mathcal{L}_{\text{value}} = \big(v[n] - V_\phi(s[n])\big)^2,
$$

對 $\phi$ 做梯度下降（backprop）。【IV-D 說明】。

* **Policy update（Actor-Critic）**：使用 importance-weighted policy gradient（V-trace 補正），更新 θ：

$$
\Delta \theta \propto \rho[n] \,\nabla_\theta\log \pi_\theta(a[n]\mid s[n])\cdot \big( r[n] + \gamma v[n+1] - V_\phi(s[n]) \big).
$$

其中 $q[n] := r[n] + \gamma v[n+1]$ 近似 $Q^{\pi}(s[n],a[n])$。此外可加入熵正則項（entropy bonus）$-\beta\sum_a \pi_\theta(a\mid s)\log\pi_\theta(a\mid s)$ 以鼓勵探索（論文提到熵 bonus 與 A3C 類似）【IV-D；V-trace 與 policy gradient 公式】。

---

## 4. 演算法流程（Algorithm 1 的步驟解釋）

（依論文 Algorithm 1 列點解釋）

1. Learner 初始化 network 參數 $\phi$.
2. 對每個 actor i：初始化其 replay buffer $D_i=\emptyset$，並把 learner 的參數複製到 actor（$\theta_i \leftarrow \phi$）。【Algo1 Step 1–5】
3. Actor 在其環境跑 MaxStep 步：根據本地 policy $\mu_{\theta_i}$ 選 action，觀察 reward 與 next state，將 experience $\xi_i[n]=(s,a,r,s')$ 放入 $D_i$。【Algo1 Step 6–11】
4. Actor 把 $D_i$ 與 $\mu_{\theta_i}$ 上傳給 learner（Step 12）。
5. Learner 使用來自各 actor 的資料計算 V-trace 目標 $v[n]$，並更新 $\phi$ 與 policy 參數（Step 13）。Learner 之後再將新參數回傳 actors（循環）。
6. 為避免過早收斂，可加入 entropy bonus（論文建議採 A3C 類似的熵項）【Algo1 & IV-D 說明】。

---

## 5. 重要變數總覽（IMPALA / V-trace 相關）

* $\pi_\theta(a\mid s)$：目標政策（learner 的 policy，參數 θ）。
* $\mu(a\mid s)$：行為政策（actor 當下使用的 policy，可能滯後）。
* $\rho[n] = \min(\bar{\rho}, \frac{\pi}{\mu})$：截斷 importance weight（用於 TD-error）。
* $c[n] = \min(\bar{c}, \frac{\pi}{\mu})$：乘積中的截斷因子（穩定性用）。
* $\bar{\rho}, \bar{c}$：截斷上界（超參）。
* $\gamma$：折扣因子（discount factor），0<γ<1。
* entropy coefficient（熵項係數，用於鼓勵探索）。
* MaxEpoch / MaxStep、batch size、learning rate（訓練控制參數；論文 Table III 列出訓練參數設定）。【IV-D；Algorithm 1；Table III】。

---

## 6. 為什麼選 IMPALA？（論文理由）

* **大規模並行化**：可同時以多個 actor 採樣，加速樣本收集。
* **處理 policy-lag 的機制**：V-trace 用截斷 IS weight 校正 off-policy bias，兼顧方差控制與偏差校正。
* **對高維 action/state 的穩定性**：相較 DQN/A3C/PPO，IMPALA 在作者實驗（附錄 B）顯示對 DHO 這種 J×K 大維度情境更穩定（論文提供比較圖）。【IV-D；附錄 B】。

---

# (三) 實務/調校細節與重要觀察（論文實驗節與附錄）

* **狀態與動作維度成長**：論文指出當 UE 數量 J 增大時，state/action 空間指數成長，增加訓練難度；因此 IMPALA 的分布式加速與 V-trace 校正是實務上可行的選擇（Sec. IV-E & V-E）。【IV-E；V-E】。
* **執行延遲**：作者測得訓練完成後，DHO 在 NVIDIA GeForce RTX 3080 Ti 上可於數毫秒內輸出 action（即可符合實時執行需求）【IV-E】。
* **獎勵權重 $\nu$ 的調整**：透過改變 $\nu$ 可以在 access delay 與 collision 之間做 trade-off（表 VII 提供了實驗結果），實務應用時可依應用型態（URLLC vs MMTC）調整。
* **熵 bonus**：可避免策略過快收斂到 suboptimal；實務上調整熵係數能改善探索。
* **初始化/transfer learning 建議**：論文提到 DHO agent 可透過 transfer learning 在新場景下僅需少量額外訓練即可適應（未給詳細實作，但為未來工作方向）。【V-C 註腳】。

---

# 精簡快速查證索引（論文位置 / 公式一覽）

> 若要回到原文核對，請對照以下章節 / 公式：

* DHO 協議概念與跳過 MR 的說明：Sec. IV-C（Sequence 圖、說明）【IV-C，Fig.4】。
* MDP state/ action/ reward：式 (12)、(13)、(14)、(15)。【IV-C；Eq.(12)–(15)】。
* Access delay / Collision definitions：式 (4)–(9)（hR, CR\_k, cP, CP, D\[n]）。【IV-B；Eq.(4)–(9)】。
* 最小化目標（整體）與 reward：式 (11) 與 (15)。【IV-C；Eq.(11),(15)】。
* IMPALA 與 V-trace 敘述與公式：Sec. IV-D，式 (16)（V-trace 目標）、policy/value update；Algorithm 1（訓練流程）。【IV-D；Eq.(16); Algorithm 1】。
* 訓練/模擬參數（Table III）、性能比較（Table IV, V, VI, VII）與訓練收斂圖（Fig.9）。【V-A；Table III；V-B；Fig.5–9；Tables IV–VII】。
  （以上標號即論文內對應段落／方程位置；可直接回查 Sec. IV、V 與附錄 B）

---

# 總結（重點回顧）

* **DHO**：把換手當成 agent 的決策問題，state 只包含時間索引、UE 是否已換手指標與前一動作，action 為每 UE 的 one-hot HO 請求（或不請求），reward 直接用負的（access delay + ν × collision rate）以強化同時降低延遲與衝突的行為；DHO 的特色是 **跳過 UE → Serving 的 MR**，由 serving-SAT 直接預測並發 HO Request，減少長距離回傳延遲與 UE uplink power。
* **IMPALA（與 V-trace）**：為了處理分散式 actors 與 large action/state 的情境，論文採用 IMPALA：actors 並行採樣，learner 用 V-trace（截斷 importance sampling weight）修正 off-policy 偏差，再更新 policy/value；policy gradient 會以 ρ-weighted 的方式計算，並有 entropy bonus 幫助探索。這套機制在實驗中對 DHO 顯示出穩定收斂與效能優勢。
* 若你要把這些細節轉成實作步驟（雖你先前表示暫時不需要 pseudocode），建議抓取下列原文位置作依據：**IV-C（MDP）→ IV-D（IMPALA/V-trace）→ Algorithm 1（Train loop）→ Table III（訓練參數）→ V（實驗結果驗證）**。