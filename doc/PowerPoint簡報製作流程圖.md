# PowerPoint 簡報製作流程圖 (Mermaid)
## 完整技術流程與 MC-HO 演算法視覺化

---

## 🔧 PowerPoint 簡報製作完整流程

### 1. 主流程圖
```mermaid
graph TD
    A[開始 PowerPoint 簡報製作] --> B{檢查虛擬環境}
    B -->|不存在| C[創建虛擬環境<br/>python3 -m venv pptx_env]
    B -->|存在| D[啟用虛擬環境<br/>source pptx_env/bin/activate]
    C --> D
    
    D --> E{檢查 python-pptx}
    E -->|未安裝| F[安裝套件<br/>pip install python-pptx]
    E -->|已安裝| G[驗證套件版本]
    F --> G
    
    G --> H[載入 PowerPoint 模板<br/>template.pptx]
    H --> I{模板是否存在?}
    I -->|是| J[使用模板]
    I -->|否| K[使用預設模板]
    J --> L[清理現有投影片]
    K --> L
    
    L --> M[設定版型變數<br/>title_layout, content_layout]
    M --> N[開始創建投影片內容]
    
    N --> O[創建標題頁]
    O --> P[設定中英文混合字體]
    P --> Q[估算內容長度]
    Q --> R{內容是否超過 20 行?}
    R -->|是| S[執行自動分頁]
    R -->|否| T[直接創建投影片]
    S --> U[創建多頁投影片]
    T --> V[應用字體設定]
    U --> V
    
    V --> W[驗證投影片內容]
    W --> X{所有內容完成?}
    X -->|否| Y[繼續下一投影片]
    Y --> Q
    X -->|是| Z[儲存簡報文件]
    
    Z --> AA[驗證文件完整性]
    AA --> BB{驗證通過?}
    BB -->|否| CC[檢查錯誤並修正]
    CC --> Z
    BB -->|是| DD[✅ 簡報製作完成]
    
    style A fill:#e1f5fe
    style DD fill:#c8e6c9
    style CC fill:#ffcdd2
```

### 2. 中英文字體設定詳細流程
```mermaid
graph TD
    A[接收文字內容 text_frame] --> B[遍歷每個段落 paragraph]
    B --> C[取得段落文字 text]
    C --> D{文字是否為空?}
    D -->|是| E[跳過此段落]
    D -->|否| F[清除現有格式 paragraph.clear()]
    
    F --> G[初始化字符索引 i = 0]
    G --> H{i < 文字長度?}
    H -->|否| I[完成此段落處理]
    H -->|是| J[取得當前字符 char = text[i]]
    
    J --> K{使用正規表達式<br/>判斷字符類型}
    K -->|英文字符<br/>[a-zA-Z0-9\s\-_.,()[\]/+=<>&%]| L[收集連續英文字符]
    K -->|中文字符<br/>其他所有字符| M[收集連續中文字符]
    
    L --> N[創建 run 物件<br/>run = paragraph.add_run()]
    M --> N
    N --> O[設定文字內容 run.text]
    O --> P{字符類型?}
    P -->|英文| Q[設定英文字體<br/>Times New Roman]
    P -->|中文| R[設定中文字體<br/>標楷體]
    
    Q --> S[設定字體大小<br/>run.font.size = Pt(font_size)]
    R --> S
    S --> T[更新字符索引 i]
    T --> H
    
    I --> U{還有更多段落?}
    U -->|是| B
    U -->|否| V[✅ 字體設定完成]
    
    style A fill:#e3f2fd
    style V fill:#c8e6c9
    style K fill:#fff3e0
```

### 3. 投影片高度控制與分頁流程
```mermaid
graph TD
    A[接收投影片內容 content_text] --> B[分割內容為行陣列<br/>lines = content_text.split('\n')]
    B --> C[初始化計數器<br/>total_lines = 0]
    
    C --> D[遍歷每一行 line in lines]
    D --> E{行內容是否為空?}
    E -->|是| F[空行計數 +1<br/>total_lines += 1]
    E -->|否| G[計算字符數<br/>char_count = len(line)]
    
    G --> H[估算換行數<br/>estimated_lines = max(1, (char_count + 79) // 80)]
    H --> I[累加行數<br/>total_lines += estimated_lines]
    
    F --> J{還有更多行?}
    I --> J
    J -->|是| D
    J -->|否| K[完成行數統計]
    
    K --> L{總行數 > MAX_LINES (20)?}
    L -->|否| M[✅ 單頁顯示<br/>return [content_text]]
    L -->|是| N[執行分頁演算法]
    
    N --> O[初始化分頁變數<br/>parts = [], current_part = [], current_lines = 0]
    O --> P[重新遍歷每一行]
    P --> Q[計算行的佔用空間]
    Q --> R{current_lines + line_count > MAX_LINES?}
    R -->|是且 current_part 不為空| S[完成當前頁面<br/>parts.append(current_part)]
    R -->|否| T[添加到當前頁面<br/>current_part.append(line)]
    
    S --> U[開始新頁面<br/>current_part = [line]<br/>current_lines = line_count]
    T --> V[累加行數<br/>current_lines += line_count]
    U --> W{還有更多行?}
    V --> W
    W -->|是| P
    W -->|否| X[處理最後一頁<br/>if current_part: parts.append(current_part)]
    
    X --> Y[✅ 分頁完成<br/>return parts]
    
    style A fill:#e8f5e8
    style M fill:#c8e6c9
    style Y fill:#c8e6c9
    style R fill:#fff3e0
```

---

## 🛰️ MC-HO 演算法詳細流程圖

### 1. MC-HO 主要演算法流程
```mermaid
graph TD
    A[🚀 MC-HO 演算法開始] --> B[Phase 1: 初始化]
    B --> C[UE 連接到 SSAT<br/>設定為 Master Node MN]
    C --> D[啟動 GNSS 位置監控]
    D --> E[計算到候選衛星距離<br/>d_SSAT, d_TSAT]
    
    E --> F[Phase 2: 條件評估]
    F --> G{CHO 觸發條件檢查<br/>d_TSAT ≤ R_b - d_offset<br/>AND d_SSAT ≤ R_b - d_offset}
    G -->|否| H[繼續監控位置]
    H --> E
    G -->|是| I[✅ 條件滿足]
    
    I --> J[Phase 3: 雙重連線建立]
    J --> K[SSAT 發送 SN Addition Request → TSAT]
    K --> L[TSAT 回應 SN Addition Response]
    L --> M[UE 執行 Random Access Procedure]
    M --> N[建立 UE ↔ TSAT 連線]
    N --> O[🔄 啟動 Packet Duplication]
    
    O --> P[Phase 4: 選擇合併循環]
    P --> Q[測量 SINR_SSAT 和 SINR_TSAT]
    Q --> R{SINR_TSAT > SINR_SSAT + threshold?}
    R -->|是| S[選擇 TSAT 路徑]
    R -->|否| T[選擇 SSAT 路徑]
    S --> U{UE 仍在重疊區域?}
    T --> U
    U -->|是| P
    U -->|否| V[執行路徑切換程序]
    
    V --> W[TSAT 發送 Path Switch Request → AMF]
    W --> X[AMF 執行 Bearer Modification]
    X --> Y[UPF 重新路由核心網路流量]
    Y --> Z[TSAT 成為新的 Master Node]
    Z --> AA[釋放 SSAT 連線]
    AA --> BB[🏁 MC-HO 完成]
    
    style A fill:#e1f5fe
    style BB fill:#c8e6c9
    style G fill:#fff3e0
    style O fill:#e8f5e8
    style R fill:#ffecb3
```

### 2. 封包複製機制詳細流程
```mermaid
graph TD
    A[📡 CHO 條件滿足] --> B[啟動 Master Cell Group<br/>with Split Bearer]
    B --> C[核心網路連接到 SSAT MN]
    
    C --> D[資料流路徑建立]
    D --> E[Path 1: Core Network → SSAT → UE]
    D --> F[Path 2: Core Network → SSAT → TSAT → UE]
    
    E --> G[🔄 封包複製開始]
    F --> G
    G --> H[UE 接收雙重資料流]
    
    H --> I[即時 SINR 測量]
    I --> J[測量 SINR_Path1 SSAT→UE]
    I --> K[測量 SINR_Path2 TSAT→UE]
    
    J --> L[選擇合併演算法<br/>Selection Combining]
    K --> L
    L --> M[SINR_selected = max SINR_SSAT, SINR_TSAT]
    
    M --> N{路徑品質評估}
    N -->|Path 1 較佳| O[使用 SSAT 路徑資料]
    N -->|Path 2 較佳| P[使用 TSAT 路徑資料]
    
    O --> Q[分集增益獲得<br/>典型值: 2-5 dB]
    P --> Q
    Q --> R{繼續封包複製?}
    R -->|是| I
    R -->|否| S[✅ 封包複製結束<br/>切換至單一路徑]
    
    style A fill:#e3f2fd
    style G fill:#e8f5e8
    style S fill:#c8e6c9
    style L fill:#fff3e0
```

### 3. 系統架構與訊息流程圖
```mermaid
sequenceDiagram
    participant UE as 📱 UE
    participant SSAT as 🛰️ SSAT (MN)
    participant TSAT as 🛰️ TSAT (SN)
    participant AMF as 🏢 AMF
    participant UPF as 🌐 UPF
    
    Note over UE, UPF: Phase 1: 初始化與監控
    UE->>SSAT: Initial Connection
    SSAT->>UE: Connection Established (MN)
    UE->>UE: GNSS Position Monitoring
    
    Note over UE, UPF: Phase 2: 觸發條件評估
    UE->>SSAT: Measurement Report
    SSAT->>SSAT: CHO Condition Evaluation
    
    Note over UE, UPF: Phase 3: SN 新增與雙重連線
    SSAT->>TSAT: SN Addition Request
    TSAT->>SSAT: SN Addition Response
    SSAT->>UE: RRC Reconfiguration
    UE->>TSAT: Random Access Procedure
    TSAT->>UE: Connection Established
    
    Note over UE, UPF: 封包複製階段
    SSAT-->>UE: Data Stream (Path 1)
    TSAT-->>UE: Data Stream (Path 2)
    UE->>UE: Selection Combining
    
    Note over UE, UPF: Phase 4: 路徑切換
    TSAT->>UE: First Packet Transmission
    TSAT->>AMF: Path Switch Request
    AMF->>UPF: Modify Bearer Request
    UPF->>AMF: Modify Bearer Response
    AMF->>TSAT: Path Switch Acknowledge
    
    Note over UE, UPF: 連線釋放
    TSAT->>SSAT: UE Context Release Request
    SSAT->>UE: Connection Release
    TSAT-->>UE: Single Data Stream (New MN)
    
    rect rgb(200, 230, 200)
        Note over UE, UPF: ✅ MC-HO 完成，TSAT 成為新 MN
    end
```

### 4. 性能比較分析流程圖
```mermaid
graph TD
    A[📊 MC-HO vs SC-HO 性能分析] --> B[實驗環境設定]
    B --> C[LEO 衛星參數<br/>高度: 600km, 速度: 7.56km/s<br/>波束直徑: 50km]
    
    C --> D[變數設定]
    D --> E[波束重疊比例: 0%, 10%, 20%, 30%, 40%]
    D --> F[距離偏移: 1km, 5km]
    D --> G[仿真時間: 200秒]
    
    E --> H[執行 SC-HO 測試]
    E --> I[執行 MC-HO 測試]
    
    H --> J[測量指標]
    I --> J
    J --> K[📈 平均換手次數/秒]
    J --> L[📉 無線連結失效/秒]
    J --> M[📊 平均系統容量]
    
    K --> N{重疊比例分析}
    L --> N
    M --> N
    N -->|0%| O[SC-HO: 148, MC-HO: 148<br/>改善: 0%]
    N -->|10%| P[SC-HO: 165, MC-HO: 162<br/>改善: 1.8%]
    N -->|20%| Q[SC-HO: 185, MC-HO: 145<br/>改善: 21.6%]
    N -->|30%| R[SC-HO: 212, MC-HO: 129<br/>改善: 39.2%]
    N -->|40%| S[SC-HO: 247, MC-HO: 130<br/>改善: 47.4%]
    
    O --> T[📋 結果分析]
    P --> T
    Q --> T
    R --> T
    S --> T
    
    T --> U[✅ 關鍵發現<br/>• 重疊比例越高，MC-HO 優勢越顯著<br/>• 40% 重疊時換手次數減少近一半<br/>• 有效避免 ping-pong 效應]
    
    style A fill:#e3f2fd
    style U fill:#c8e6c9
    style N fill:#fff3e0
```

---

## 🔗 如何使用這些 Mermaid 流程圖

### 1. 在 GitHub/GitLab 中顯示
直接將 mermaid 程式碼貼入 `.md` 檔案中，平台會自動渲染。

### 2. 在線上編輯器
- **Mermaid Live Editor**: https://mermaid.live/
- **Draw.io**: 支援 Mermaid 匯入
- **Notion**: 支援 Mermaid 語法

### 3. VS Code 擴充功能
安裝 "Mermaid Preview" 擴充功能，可即時預覽流程圖。

### 4. 匯出為圖片
```bash
# 使用 mermaid-cli
npm install -g @mermaid-js/mermaid-cli
mmdc -i flowchart.md -o flowchart.png
```

### 5. 嵌入 PowerPoint
將 Mermaid 渲染為 PNG 圖片後，可直接插入到 PowerPoint 簡報中。

---

*這些流程圖提供了完整的視覺化呈現，可用於技術文檔、簡報製作或系統設計討論。所有圖表都基於實際的 MC-HO 演算法實作與 PowerPoint 製作流程。*