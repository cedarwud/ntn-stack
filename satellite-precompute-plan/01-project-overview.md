# 01 - 專案總覽與技術參數

> **回到總覽**：[README.md](./README.md)  < /dev/null |  **下一階段**：[Phase 1 - 數據庫設置](./02-phase1-database-setup.md)

## 🎯 方案概述

**核心理念**：使用真實 TLE 歷史數據 + 預計算存儲 + 時間軸播放，解決即時計算性能問題，同時保持數據真實性。

### ✅ 方案優勢
- **真實性保證**：使用真實 Starlink TLE 數據，非模擬數據
- **性能優化**：預計算避免即時 SGP4 運算瓶頸
- **展示友好**：支援時間軸控制、加速播放、handover 動畫
- **研究價值**：可用於 3GPP events 計算和論文分析
- **穩定性**：不依賴網路即時連接

## 📊 技術參數建議

### ⏰ 時間段選擇（按研究等級分層）

#### **📊 展示級數據**：6 小時歷史數據
- **用途**：系統驗證、UI 展示、概念驗證  
- **理由**：展示完整的衛星覆蓋變化和 handover 場景

#### **🎓 研究級數據**：45 天歷史數據
- **訓練數據**：30 天（RL 主要學習期）
- **測試數據**：7 天（性能評估）
- **驗證數據**：7 天（交叉驗證）  
- **緩衝數據**：1 天（時間重疊處理）

#### **🏆 頂級期刊標準**：60 天歷史數據
- 符合 IEEE TCOM、TWC 等頂級期刊要求
- 支援大規模統計分析和長期趨勢研究

#### **💾 數據量估算（45天研究級）**：
```
45 天 × 24 小時 × 120 時間點(30秒) × 8 顆可見衛星 = 518,400 條記錄
518,400 × 500 bytes ≈ 260MB（映像檔完全可承受）
```

### 🕐 時間解析度
- **建議間隔**：30 秒
- **理由**：衛星速度 7.5 km/s，30 秒移動 225km，適合 handover 觸發精度
- **數據量**：6 小時 = 720 個時間點

## 🛰️ 多星座支援設計

### **🌟 主要星座：Starlink (SpaceX)**
- **衛星數量**：~5000 顆，覆蓋密度最高
- **軌道參數**：550km 高度，53° 傾角  
- **研究價值**：數據最豐富，學術熱度最高
- **handover 場景**：星座內切換

### **🌐 對比星座：OneWeb**  
- **衛星數量**：~648 顆，極地覆蓋優異
- **軌道參數**：1200km 高度，87.4° 傾角
- **研究價值**：不同軌道特性的對比研究
- **分析模式**：獨立分析，避免混合不同星座

### **⚠️ 重要限制：跨星座 handover 不可行**
- 不同星座使用不同頻段、協議、地面設施
- 論文研究應分別分析各星座的內部 handover
- UI 設計：需要星座切換功能，避免混合顯示

### **📊 可見衛星數量 & 數據規模**
```
各仰角範圍的可見衛星：
- 仰角 ≥ 15°（handover 主要候選）: 3-5 顆
- 仰角 ≥ 10°（handover 監測範圍）: 6-8 顆  
- 仰角 ≥ 5°（潛在候選）: 8-12 顆
- 仰角 ≥ 0°（理論可見）: 15-25 顆

多星座數據規模（45天研究級）：
Starlink: 45 天 × 2880 時間點 × 8 顆 = 1,036,800 條記錄 (518MB)
OneWeb: 45 天 × 2880 時間點 × 5 顆 = 648,000 條記錄 (324MB)
總計: ~842MB（Docker 映像檔完全可承受）

展示級數據（6小時）：僅 2.9MB
```

## 📱 真實 UE Handover 場景分析

### **🛰️ Starlink 可見衛星數量**

基於真實的 Starlink 星座配置：
- **總衛星數**: ~5000 顆 Starlink 衛星
- **軌道高度**: 550km
- **觀測半徑**: √((6371+550)² - 6371²) ≈ 2300km

### **📊 分層可見性設計**

```python
VISIBILITY_LEVELS = {
    "handover_candidates": {
        "min_elevation": 15, 
        "expected_count": "3-5 顆",
        "usage": "主要 handover 候選，信號強度足夠"
    },
    "monitoring_satellites": {
        "min_elevation": 10, 
        "expected_count": "6-8 顆",
        "usage": "handover 監測範圍，符合 3GPP NTN 標準"
    }, 
    "potential_satellites": {
        "min_elevation": 5, 
        "expected_count": "8-12 顆",
        "usage": "潛在候選，即將進入監測範圍"
    },
    "theoretical_visible": {
        "min_elevation": 0, 
        "expected_count": "15-25 顆",
        "usage": "理論可見但信號太弱，不參與 handover"
    }
}
```

### **🎯 典型 Handover 場景示例**

```
時間點: 2025-07-15 10:30:00 UTC
台灣 UE 位置: (24.94°N, 121.37°E)

🔗 服務衛星: STARLINK-1234 (仰角 45°, 信號強度 -95dBm)

📡 Handover 候選:
├── STARLINK-5678 (仰角 25°, 信號強度 -105dBm) ✅ 主要候選
├── STARLINK-9012 (仰角 18°, 信號強度 -108dBm) ✅ 次要候選  
└── STARLINK-3456 (仰角 12°, 信號強度 -112dBm) ⚠️ 備選候選

👁️ 監測中: 2 顆 (仰角 5-10°)
🌅 即將可見: 1 顆 (仰角 0-5°)

總計參與 handover 決策: 6-8 顆（符合 3GPP NTN 建議）
```

### **📋 3GPP NTN 標準符合性**

- **測量衛星數**: 最多 8 顆 ✅
- **handover 候選**: 3-5 顆 ✅
- **同時監測**: 6-8 顆 ✅
- **信號閾值**: 仰角 ≥ 10° ✅

## 🎯 觀測位置設定

### **📍 台灣觀測者位置**
- **緯度**: 24.94417°N (台北)
- **經度**: 121.37139°E 
- **高度**: 100m (海拔)
- **理由**: 亞太地區代表性位置，適合 LEO 衛星研究

### **🌏 地理優勢**
- **中緯度位置**: 可觀測到多種軌道傾角的衛星
- **海島地形**: 減少地形遮蔽影響
- **時區考量**: UTC+8，方便數據分析和展示

## 🎓 學術研究應用

### **📚 論文研究等級分類**

#### **🏆 頂級期刊級別** (90%+ 真實數據)
- 軌道計算、信號模型、切換算法全部真實
- 可發表於 IEEE TCOM、TWC 等頂級期刊
  
#### **📚 一般期刊級別** (70-90% 真實數據)  
- 核心算法真實，部分物理參數可用標準模型
- 適合發表於中等期刊和會議
  
#### **🔬 概念驗證級別** (50-70% 真實數據)
- 概念正確但細節可簡化
- 適合早期研究和系統驗證

### **📊 研究應用場景**
1. **Handover 算法比較**: DQN 性能分析
2. **3GPP Events 驗證**: A4, D1, D2, T1 事件觸發準確性
3. **多星座對比研究**: Starlink vs OneWeb 覆蓋特性
4. **時間序列分析**: 衛星可見性周期性模式研究

---

**🎯 下一步動作**：進入 [Phase 1 - 數據庫設置](./02-phase1-database-setup.md)

