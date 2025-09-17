# DHO演算法流程圖表集合

> **用途說明**：本文檔包含完整的DHO演算法視覺化流程圖，協助理解演算法的各個組成部分和執行流程。

## 1. 總體架構流程圖

### 1.1 DHO系統整體架構

```mermaid
graph TB
    subgraph "LEO衛星環境"
        A[服務衛星<br/>Serving Satellite] --> B[多個目標衛星<br/>Target Satellites]
        C[地面用戶設備<br/>UEs] --> A
    end
    
    subgraph "DHO核心系統"
        D[狀態觀察器<br/>State Observer] --> E[智能代理<br/>DHO Agent]
        E --> F[動作執行器<br/>Action Executor]
        F --> G[環境反饋<br/>Environment Feedback]
        G --> D
    end
    
    subgraph "學習系統"
        H[經驗收集<br/>Experience Collection] --> I[IMPALA學習器<br/>IMPALA Learner]
        I --> J[策略更新<br/>Policy Update]
        J --> E
    end
    
    A --> D
    F --> A
    E --> H
    
    style E fill:#e1f5fe
    style I fill:#f3e5f5
    style A fill:#e8f5e8
```

### 1.2 傳統HO vs DHO比較流程

```mermaid
graph TD
    subgraph "傳統HO流程"
        T1[UE週期性測量<br/>RSRP/RSRQ] --> T2[生成測量報告<br/>MR Generation]
        T2 --> T3[MR傳輸<br/>3.2~12ms延遲]
        T3 --> T4[服務gNB接收MR<br/>Signal Analysis]
        T4 --> T5[HO決策<br/>A3事件觸發]
        T5 --> T6[HO執行<br/>Target Selection]
    end
    
    subgraph "DHO流程"
        D1[狀態觀察<br/>Time/Access/History] --> D2[模式匹配<br/>Pattern Recognition]
        D2 --> D3[預測決策<br/>Predictive Decision]
        D3 --> D4[HO執行<br/>Immediate Action]
    end
    
    subgraph "關鍵差異"
        K1["⏱️ 延遲對比<br/>傳統: 112-212ms<br/>DHO: <1ms"]
        K2["🔋 功耗對比<br/>傳統: 持續測量+傳輸<br/>DHO: 僅觀察狀態"]
        K3["🎯 準確性對比<br/>傳統: 基於過時測量<br/>DHO: 基於學習模式"]
    end
    
    T6 --> K1
    D4 --> K1
    
    style D1 fill:#e1f5fe
    style D2 fill:#e1f5fe
    style D3 fill:#e1f5fe
    style D4 fill:#e1f5fe
    style K1 fill:#fff3e0
    style K2 fill:#fff3e0
    style K3 fill:#fff3e0
```

## 2. 核心演算法流程圖

### 2.1 DHO決策流程詳解

```mermaid
flowchart TD
    A[開始新時隙 n] --> B[獲取當前狀態<br/>s[n] = {n, aᴴᴼ[n], a[n-1]}]
    B --> C{是否為訓練階段?}
    
    C -->|是| D[隨機探索策略<br/>ε-greedy]
    C -->|否| E[使用學習策略<br/>π(a|s)]
    
    D --> F[選擇動作 a[n]]
    E --> F
    
    F --> G[執行HO決策<br/>多UE聯合優化]
    G --> H[觀察環境反饋<br/>r[n], s[n+1]]
    
    H --> I{是否達到<br/>終止條件?}
    I -->|否| J[存儲經驗<br/>(s,a,r,s')]
    J --> K[更新狀態<br/>n = n+1]
    K --> B
    
    I -->|是| L[回合結束]
    L --> M[策略更新]
    M --> N{是否收斂?}
    N -->|否| A
    N -->|是| O[部署最終策略]
    
    style B fill:#e3f2fd
    style F fill:#f1f8e9
    style G fill:#fce4ec
    style M fill:#f3e5f5
```

### 2.2 狀態編碼與動作選擇詳解

```mermaid
graph LR
    subgraph "狀態空間 S"
        S1[時間索引 n<br/>軌道位置指示器] 
        S2[存取狀態向量<br/>aᴴᴼ[n] ∈ {0,1}ᴶ]
        S3[歷史動作<br/>a[n-1]]
    end
    
    subgraph "狀態處理"
        P1[狀態編碼<br/>State Encoding]
        P2[特徵提取<br/>Feature Extraction] 
        P3[模式識別<br/>Pattern Recognition]
    end
    
    subgraph "動作空間 A"
        A1[不進行HO<br/>a₀ = 1]
        A2[選擇目標1<br/>a₁ = 1] 
        A3[選擇目標2<br/>a₂ = 1]
        A4[選擇目標K<br/>aₖ = 1]
    end
    
    subgraph "約束條件"
        C1[One-hot約束<br/>Σaₖ = 1]
        C2[多UE協調<br/>負載均衡]
    end
    
    S1 --> P1
    S2 --> P1  
    S3 --> P1
    P1 --> P2
    P2 --> P3
    P3 --> A1
    P3 --> A2
    P3 --> A3
    P3 --> A4
    
    A1 --> C1
    A2 --> C1
    A3 --> C1
    A4 --> C1
    C1 --> C2
    
    style P2 fill:#e8eaf6
    style C1 fill:#fff8e1
```

## 3. IMPALA學習機制圖

### 3.1 Actor-Learner架構

```mermaid
graph TB
    subgraph "多個Actor"
        A1[Actor 1<br/>收集經驗]
        A2[Actor 2<br/>收集經驗] 
        A3[Actor N<br/>收集經驗]
    end
    
    subgraph "經驗緩存"
        B[Experience Buffer<br/>經驗池]
    end
    
    subgraph "中央學習器"
        C[Learner<br/>策略學習]
        D[V-trace計算<br/>重要性權重修正]
        E[策略更新<br/>神經網路訓練]
    end
    
    subgraph "策略分發"
        F[Policy Distribution<br/>策略同步]
    end
    
    A1 --> B
    A2 --> B
    A3 --> B
    B --> C
    C --> D
    D --> E
    E --> F
    F --> A1
    F --> A2  
    F --> A3
    
    style C fill:#e1f5fe
    style D fill:#f3e5f5
    style B fill:#e8f5e8
```

### 3.2 V-trace機制詳解

```mermaid
flowchart TD
    A[接收經驗批次<br/>{s,a,r,s'}] --> B[計算策略概率<br/>π(a|s) vs μ(a|s)]
    
    B --> C[計算重要性權重<br/>ρ = min(ρ̄, π/μ)<br/>c = min(c̄, π/μ)]
    
    C --> D[V-trace目標計算<br/>v_s = V(s) + Σγⁱ∏cⱼδᵢ]
    
    D --> E[TD誤差計算<br/>δ = ρ(r + γV(s') - V(s))]
    
    E --> F[損失函數<br/>L = L_policy + L_value]
    
    F --> G[梯度反向傳播<br/>更新神經網路參數]
    
    G --> H[策略改進<br/>π_new ← π_old + α∇L]
    
    H --> I{收斂檢查}
    I -->|未收斂| A
    I -->|已收斂| J[部署最終策略]
    
    style C fill:#fff3e0
    style D fill:#e8f5e8
    style F fill:#fce4ec
```

## 4. 學習過程階段圖

### 4.1 三階段學習過程

```mermaid
gantt
    title DHO學習過程時間軸
    dateFormat X
    axisFormat %s

    section 隨機探索期
    隨機動作選擇    :active, exploration, 0, 30
    經驗收集        :active, collection1, 0, 30
    
    section 模式識別期  
    模式學習        :learning, 30, 60
    策略改善        :improvement, 35, 60
    經驗累積        :collection2, 30, 60
    
    section 策略成熟期
    穩定決策        :stable, 60, 90
    持續優化        :optimize, 65, 90
    性能監控        :monitor, 60, 90
```

### 4.2 收斂過程可視化

```mermaid
xychart-beta
    title "DHO學習收斂曲線"
    x-axis [0, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]
    y-axis "獎勵值" -100 --> 0
    line [−95, −85, −75, −65, −60, −50, −45, −35, −30, −25, −20]
```

## 5. 系統性能比較圖

### 5.1 關鍵指標對比

```mermaid
xychart-beta
    title "DHO vs 傳統HO性能對比"
    x-axis ["存取延遲", "碰撞率", "決策延遲", "功耗"]
    y-axis "改善倍數" 0 --> 8
    bar [6.86, 3.2, 100, 2.5]
```

### 5.2 網路負載影響分析

```mermaid
graph LR
    subgraph "低負載環境"
        L1[用戶數: <50%容量]
        L2[DHO優勢: 延遲優化]
        L3[改善: 3-4倍]
    end
    
    subgraph "中負載環境"  
        M1[用戶數: 50-80%容量]
        M2[DHO優勢: 聯合優化]
        M3[改善: 5-6倍]
    end
    
    subgraph "高負載環境"
        H1[用戶數: >80%容量] 
        H2[DHO優勢: 碰撞避免]
        H3[改善: 7-8倍]
    end
    
    L1 --> L2 --> L3
    M1 --> M2 --> M3  
    H1 --> H2 --> H3
    
    style M2 fill:#e1f5fe
    style H2 fill:#f3e5f5
```

## 6. 實際部署架構圖

### 6.1 系統整合架構

```mermaid
graph TB
    subgraph "衛星平台"
        S1[衛星處理器<br/>Neural Network Inference]
        S2[DHO決策引擎<br/>Real-time Decision]
        S3[傳統HO備援<br/>Fallback Mechanism]
    end
    
    subgraph "地面控制"
        G1[訓練數據中心<br/>Model Training]
        G2[策略更新服務<br/>Policy Distribution]
        G3[性能監控<br/>Performance Analytics]
    end
    
    subgraph "3GPP標準介面"
        I1[gNB-CU介面<br/>Standard Signaling]
        I2[Xn介面<br/>Inter-satellite Communication]
        I3[NG介面<br/>Core Network]
    end
    
    S1 <--> G1
    S2 <--> G2
    S3 <--> G3
    
    S2 --> I1
    S2 --> I2
    I1 --> I3
    
    style S2 fill:#e1f5fe
    style G1 fill:#f3e5f5
    style I1 fill:#e8f5e8
```

### 6.2 即時決策流水線

```mermaid
sequenceDiagram
    participant UE as 用戶設備
    participant Sat as 服務衛星
    participant DHO as DHO引擎
    participant Target as 目標衛星
    
    Note over Sat: 每個時隙開始
    Sat->>DHO: 當前狀態 s[n]
    DHO->>DHO: 神經網路推理 (<1ms)
    DHO->>Sat: HO決策 a[n]
    
    alt HO執行
        Sat->>Target: HO請求
        Target->>Sat: HO回應
        Sat->>UE: HO指令
        UE->>Target: 接入請求
        Target->>UE: 接入確認
    else 維持連接
        Sat->>UE: 繼續服務
    end
    
    Note over DHO: 經驗記錄用於後續學習
```

## 7. 未來擴展架構圖

### 7.1 多層協作架構

```mermaid
graph TB
    subgraph "應用層智能"
        A1[QoS感知HO<br/>應用需求驅動]
        A2[用戶行為學習<br/>個性化服務]
    end
    
    subgraph "網路層智能" 
        N1[路由優化<br/>端到端路徑選擇]
        N2[負載均衡<br/>星座級協調]
    end
    
    subgraph "物理層智能"
        P1[波束成型<br/>天線自適應]
        P2[功率控制<br/>干擾管理]
    end
    
    A1 --> N1
    A2 --> N2
    N1 --> P1
    N2 --> P2
    
    style N1 fill:#e1f5fe
    style N2 fill:#e1f5fe
```

### 7.2 跨域協作學習

```mermaid
mindmap
  root((DHO擴展))
    多目標優化
      能源效率
      服務品質  
      負載均衡
    跨層協作
      PHY層
      MAC層
      網路層
    應用場景
      IoT大連接
      緊急通訊
      車聯網
    技術融合
      邊緣計算
      區塊鏈
      6G網路
```

---

## 使用說明

### 圖表解讀指南

1. **流程圖**：展示演算法的時序執行邏輯
2. **架構圖**：說明系統組件間的關係和數據流
3. **對比圖**：突出DHO相對傳統方法的優勢
4. **時序圖**：描述即時決策的精確時序要求

### 技術細節索引

- **狀態編碼**：參見圖2.2
- **學習機制**：參見圖3.1-3.2  
- **性能優勢**：參見圖5.1-5.2
- **部署架構**：參見圖6.1-6.2

---

*本圖表集合提供DHO演算法的完整視覺化說明，配合技術文檔使用可獲得最佳理解效果。*
