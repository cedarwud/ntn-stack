# 衛星數據預處理系統 - Mermaid 流程圖

## 🔄 完整數據處理流程

### 1. Pure Cron 驅動架構總覽

```mermaid
graph TB
    subgraph "🏗️ 建構階段 (2-5分鐘)"
        A[CelesTrak TLE 數據] --> B[SGP4 軌道計算]
        B --> C[智能衛星篩選]
        C --> D[時間序列預計算]
        D --> E[映像檔數據打包]
    end
    
    subgraph "🚀 啟動階段 (<30秒)"
        E --> F[純數據載入]
        F --> G[完整性驗證]
        G --> H[API 服務啟動]
    end
    
    subgraph "🕒 Cron 調度階段 (背景自動)"
        I[定時 TLE 下載<br/>02:00, 08:00, 14:00, 20:00] --> J[智能變更分析<br/>30分鐘後]
        J --> K{是否有變更?}
        K -->|有變更| L[增量重新計算]
        K -->|無變更| M[跳過處理]
        L --> N[容器熱更新]
        M --> O[繼續監控]
        N --> O
    end
    
    H --> P[系統就緒]
    O --> Q[持續服務]
```

### 2. SGP4 軌道計算引擎詳細流程

```mermaid
flowchart TD
    subgraph "📡 TLE 數據輸入"
        A1[STARLINK-1007<br/>Line1: 1 44713U 19074A...]
        A2[Line2: 2 44713 53.0532...]
        A1 --> B[TLE 參數解析]
        A2 --> B
    end
    
    subgraph "🧮 SGP4 核心計算"
        B --> C[軌道元素提取]
        C --> D[時間傳播計算]
        D --> E[攝動力修正]
        
        E --> E1[J2 地球扁率攝動]
        E --> E2[大氣阻力攝動] 
        E --> E3[重力場攝動]
        
        E1 --> F[位置速度向量]
        E2 --> F
        E3 --> F
    end
    
    subgraph "📍 座標轉換"
        F --> G[ECEF 座標系]
        G --> H[經緯高座標]
        H --> I[觀測者視角轉換]
    end
    
    subgraph "📊 輸出結果"
        I --> J1[仰角 Elevation]
        I --> J2[方位角 Azimuth] 
        I --> J3[距離 Range]
        I --> J4[經度 Longitude]
        I --> J5[緯度 Latitude]
        I --> J6[高度 Altitude]
    end
```

### 3. 智能衛星篩選系統流程

```mermaid
flowchart TD
    subgraph "🛰️ 原始數據"
        A[Starlink: 8,042 顆]
        B[OneWeb: 651 顆]
    end
    
    subgraph "🎯 星座分離篩選"
        A --> C1[Starlink 專用篩選<br/>傾角53° + 高度550km]
        B --> C2[OneWeb 專用篩選<br/>傾角87° + 高度1200km]
    end
    
    subgraph "🌍 地理相關性篩選"
        C1 --> D1[NTPU 觀測點匹配<br/>24.9441°N, 121.3713°E]
        C2 --> D2[NTPU 觀測點匹配<br/>24.9441°N, 121.3713°E]
    end
    
    subgraph "📊 動態篩選策略"
        D1 --> E{估計可見數量}
        D2 --> E
        
        E -->|< 8顆| F1[放寬篩選<br/>確保最少候選]
        E -->|8-45顆| F2[標準篩選<br/>平衡品質數量]
        E -->|> 45顆| F3[嚴格篩選<br/>選擇最優衛星]
    end
    
    subgraph "⭐ 最終結果"
        F1 --> G1[Starlink: 15-25顆]
        F2 --> G1
        F3 --> G1
        
        F1 --> G2[OneWeb: 8-15顆]
        F2 --> G2
        F3 --> G2
    end
```

### 4. 3GPP 換手事件判斷流程

```mermaid
graph TD
    subgraph "📊 信號測量"
        A[RSRP 計算<br/>基於 FSPL 模型] --> B[服務衛星 RSRP]
        A --> C[鄰近衛星 RSRP] 
        A --> D[距離測量<br/>3D 精確計算]
    end
    
    subgraph "🔍 Event A4 判斷"
        C --> E{鄰近 RSRP<br/>> -100dBm?}
        E -->|是| F1[觸發 A4 事件<br/>MEDIUM 優先級]
        E -->|否| F2[不觸發 A4]
    end
    
    subgraph "🚨 Event A5 判斷"
        B --> G{服務 RSRP<br/>< -110dBm?}
        C --> H{鄰近 RSRP<br/>> -100dBm?}
        G -->|是| I{雙重條件}
        H -->|是| I
        I -->|都滿足| J1[觸發 A5 事件<br/>HIGH 優先級]
        I -->|不滿足| J2[不觸發 A5]
    end
    
    subgraph "📏 Event D2 判斷"
        D --> K{服務距離<br/>> 5000km?}
        D --> L{候選距離<br/>< 3000km?}
        K -->|是| M{距離條件}
        L -->|是| M
        M -->|都滿足| N1[觸發 D2 事件<br/>LOW 優先級]
        M -->|不滿足| N2[不觸發 D2]
    end
    
    subgraph "🎯 換手決策"
        F1 --> O[換手候選評估]
        J1 --> P[緊急換手執行]
        N1 --> Q[距離優化換手]
        
        P --> R[最終換手決策]
        O --> R
        Q --> R
    end
```

### 5. RSRP 精確計算流程

```mermaid
flowchart LR
    subgraph "📡 衛星參數"
        A[發射功率<br/>43 dBm] 
        B[頻段<br/>Ku 12 GHz]
        C[3D 距離<br/>SGP4 計算]
        D[仰角<br/>觀測者視角]
    end
    
    subgraph "🧮 FSPL 計算"
        C --> E["FSPL = 20×log₁₀(距離)<br/>+ 20×log₁₀(頻率)<br/>+ 32.45 dB"]
    end
    
    subgraph "🌡️ 環境損耗"
        D --> F["大氣損耗 =<br/>(90-仰角)/90 × 3.0 dB"]
        D --> G["仰角增益 =<br/>min(仰角/90, 1.0) × 15 dB"]
    end
    
    subgraph "📊 最終計算"
        A --> H["RSRP = 發射功率<br/>- FSPL<br/>- 大氣損耗<br/>+ 仰角增益"]
        E --> H
        F --> H
        G --> H
    end
    
    H --> I[RSRP 結果<br/>-150 ~ -50 dBm]
```

### 6. 時間序列預處理流程

```mermaid
gantt
    title 衛星軌跡時間序列預處理 (120分鐘)
    dateFormat X
    axisFormat %H:%M
    
    section 時間軸設定
    起始時間          :0, 30s
    採樣間隔 30秒     :30s, 30s
    總時間點 240個    :60s, 30s
    
    section Starlink 處理
    15顆衛星軌跡計算  :0, 3600s
    仰角方位角轉換    :1800s, 1800s
    可見性判斷        :3000s, 1200s
    
    section OneWeb 處理  
    10顆衛星軌跡計算  :0, 2400s
    仰角方位角轉換    :1200s, 1200s
    可見性判斷        :2000s, 800s
    
    section 數據輸出
    JSON 格式生成     :4200s, 600s
    完整性驗證        :4800s, 300s
    系統就緒          :5100s, 300s
```

### 7. 系統整體架構圖

```mermaid
graph TB
    subgraph "🌐 外部數據源"
        CelesTrak[CelesTrak.org<br/>官方 TLE 數據]
    end
    
    subgraph "🏗️ Docker 建構層"
        Build[build_with_phase0_data.py<br/>SGP4 完整計算引擎]
    end
    
    subgraph "🐳 容器運行層"
        Container[NetStack 容器<br/>純數據載入模式]
        API[REST API 服務<br/>localhost:8080]
    end
    
    subgraph "🕒 Cron 調度層"
        Cron1[TLE 下載器<br/>每6小時執行]
        Cron2[增量處理器<br/>智能變更分析]
        Cron3[數據清理器<br/>每日維護]
    end
    
    subgraph "💾 數據存儲層"
        Volume[Docker Volume<br/>持久化數據存儲]
        Files[預計算數據文件<br/>61MB 總大小]
    end
    
    subgraph "🎯 應用服務層"
        Frontend[SimWorld 前端<br/>3D 軌跡動畫]
        Research[研究分析工具<br/>換手場景測試]
    end
    
    CelesTrak --> Cron1
    Cron1 --> Build
    Build --> Volume
    Volume --> Container
    Container --> API
    API --> Frontend
    API --> Research
    
    Cron1 --> Cron2
    Cron2 --> Volume
    Cron3 --> Volume
```

## 🎯 關鍵技術指標儀表板

```mermaid
pie title 衛星篩選效率
    "原始數據" : 8693
    "地理篩選後" : 1738  
    "智能篩選後" : 40
    "最終精選" : 25
```

```mermaid
xychart-beta
    title "系統性能指標對比"
    x-axis ["啟動時間", "數據精度", "維護成本", "可靠性", "真實性"]
    y-axis "評分 (1-10)" 0 --> 10
    bar [2, 10, 10, 10, 10]
```

## 📊 數據流量統計

```mermaid
flowchart LR
    A["8,693 顆衛星"] --> B["地理篩選<br/>減少 80%"]
    B --> C["1,738 顆相關衛星"]
    C --> D["智能篩選<br/>動態選擇"]
    D --> E["25-40 顆精選衛星"]
    E --> F["240 時間點計算"]
    F --> G["9,600 個數據點"]
    G --> H["61MB 結構化數據"]
```
