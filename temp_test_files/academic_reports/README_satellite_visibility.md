# 🛰️ 真實衛星可見性計算器

基於TLE數據和SGP4軌道傳播的**完整9步驟**衛星可見性計算程式。

## ✅ 實現的完整步驟

與之前的錯誤計算不同，本程式實現了**標準的9個步驟**：

1. **TLE數據解析** - 正確解析TLE文件，驗證格式
2. **SGP4軌道傳播初始化** - 使用WGS84引力模型
3. **時間序列設定** - 基於TLE epoch時間，非當前時間
4. **SGP4軌道計算** - 精確的軌道傳播計算
5. **座標系轉換** ⭐ - **TEME → ITRS，考慮地球自轉**
6. **觀測者座標計算** - WGS84橢球模型，精確地理定位
7. **相對幾何計算** - 精確的仰角、方位角、距離計算
8. **可見性判斷** - 基於準確幾何的可見性判斷
9. **統計分析** - 完整的統計分析和升起/降落事件

## 🎯 核心修正

### ❌ 之前的錯誤
- 沒有TEME → ECEF座標轉換
- 沒有考慮地球自轉
- 簡化的球形地球假設
- 錯誤的幾何計算

### ✅ 現在的正確實現
- 使用**Skyfield庫**自動處理所有座標轉換
- 精確考慮地球自轉、歲差、章動
- WGS84橢球模型
- 標準的球面三角學計算

## 📋 使用方法

### 安裝依賴
```bash
pip install sgp4 skyfield numpy
```

### 基本用法
```bash
# 計算100顆Starlink衛星在NTPU的可見性
python satellite_visibility_calculator.py --constellation starlink --satellites 100 --location ntpu

# 計算50顆OneWeb衛星在NTPU的可見性
python satellite_visibility_calculator.py --constellation oneweb --satellites 50 --location ntpu

# 計算兩個星座總共200顆衛星
python satellite_visibility_calculator.py --constellation both --satellites 200 --location ntpu

# 自定義位置（台北）
python satellite_visibility_calculator.py --constellation starlink --satellites 100 --location custom --lat 25.0330 --lon 121.5654 --alt 10

# 自定義計算參數
python satellite_visibility_calculator.py --constellation starlink --satellites 100 --location ntpu --duration 12 --interval 1 --elevation 10.0

# 指定輸出文件
python satellite_visibility_calculator.py --constellation starlink --satellites 100 --location ntpu --output results.json
```

### 參數說明

| 參數 | 必需 | 描述 | 預設值 |
|------|------|------|--------|
| `--constellation` `-c` | ✅ | 星座選擇：starlink, oneweb, both | - |
| `--satellites` `-s` | ✅ | 要計算的衛星數量 | - |
| `--location` `-l` | ✅ | 觀測位置：ntpu, taipei, custom | - |
| `--duration` `-d` | ❌ | 計算時長（小時） | 24 |
| `--interval` `-i` | ❌ | 時間間隔（分鐘） | 5 |
| `--elevation` `-e` | ❌ | 最小仰角門檻（度） | 5.0 |
| `--output` `-o` | ❌ | 輸出文件路徑 | 自動生成 |
| `--lat` | ❌ | 自定義緯度（配合custom使用） | - |
| `--lon` | ❌ | 自定義經度（配合custom使用） | - |
| `--alt` | ❌ | 自定義海拔（米） | 0.0 |
| `--tle-path` | ❌ | TLE數據目錄路徑 | 自動尋找 |

### 預定義位置

| 位置 | 座標 | 描述 |
|------|------|------|
| `ntpu` | 24.9439°N, 121.3711°E, 50m | 國立台北大學 |
| `taipei` | 25.0330°N, 121.5654°E, 10m | 台北市 |
| `custom` | 用戶指定 | 自定義位置 |

## 📊 輸出結果

### 控制台輸出
```
🎯 ===== 衛星可見性計算結果 =====
📅 計算參數:
   時長: 24 小時
   間隔: 5 分鐘
   時間點: 288 個
   衛星總數: 100 顆

📊 總體統計:
   最大同時可見: 15 顆
   最小同時可見: 8 顆
   平均可見數量: 11.2 顆
   中位數可見: 11.0 顆

🛰️ 按星座統計:
   STARLINK: (總數: 100 顆)
     最大: 15 顆
     最小: 8 顆
     平均: 11.2 顆

📡 覆蓋分析:
   覆蓋連續性: 100.0%
   無覆蓋時段: 0/288 個時間點

🌅 升起/降落事件:
   總事件數: 156
   升起事件: 78
   降落事件: 78
```

### JSON輸出檔案
```json
{
  "metadata": {
    "calculation_time": "2025-09-16T12:00:00Z",
    "observer_location": {
      "latitude": 24.9439,
      "longitude": 121.3711,
      "altitude": 50.0
    }
  },
  "analysis_results": {
    "total_statistics": {
      "max_visible": 15,
      "min_visible": 8,
      "avg_visible": 11.2
    },
    "constellation_statistics": {
      "starlink": {
        "max_visible": 15,
        "min_visible": 8,
        "avg_visible": 11.2,
        "total_satellites": 100
      }
    }
  }
}
```

## 🔬 技術特點

### 使用的庫和模型
- **SGP4庫**: 標準的軌道傳播算法
- **Skyfield庫**: 精確的天文計算和座標轉換
- **WGS84地球模型**: 精確的地球橢球面
- **ITRS座標系**: 國際陸地參考系

### 座標轉換流程
1. **TLE → SGP4** : 軌道要素解析
2. **SGP4 → TEME** : True Equator Mean Equinox 座標系
3. **TEME → ITRS** : 考慮地球自轉的陸地參考系
4. **ITRS → 觀測者本地** : 東北天座標系 (ENU)

### 時間標準處理
- **TLE Epoch時間**: 作為計算基準，非當前時間
- **UTC/UT1/TT轉換**: 精確的時間標準轉換
- **地球自轉**: 考慮格林威治恆星時變化

## 🆚 與六階段管道的對比

| 項目 | 本計算器 | 六階段管道 |
|------|----------|------------|
| **座標轉換** | ✅ 完整TEME→ITRS | ❓ 可能更複雜 |
| **物理建模** | ✅ 基礎軌道動力學 | ✅ 信號強度、衰減等 |
| **優化算法** | ❌ 無 | ✅ 智能選擇、RL |
| **計算速度** | ✅ 快速直接 | ❌ 複雜流程 |
| **用途** | 🎯 可見性分析 | 🎯 系統優化 |

## ⚠️ 重要注意事項

1. **TLE數據時效性**: TLE數據有時效性，超過1週後精度下降
2. **計算量**: 大量衛星 × 長時間計算會消耗較多時間和記憶體
3. **仰角門檻**: 5°是最小門檻，實際應用中可能需要10°或更高
4. **地形遮蔽**: 程式不考慮建築物、山峰等地形遮蔽
5. **大氣折射**: 程式不考慮大氣折射效應

## 🎯 適用場景

### ✅ 適合使用
- 衛星可見性快速分析
- 學術研究中的基礎計算
- 星座覆蓋能力評估
- 觀測時機預測

### ❌ 不適合使用
- 需要信號強度分析
- 需要考慮換手決策
- 需要複雜的物理建模
- 實時高精度預測

## 🧪 測試建議

```bash
# 小規模測試 (快速驗證)
python satellite_visibility_calculator.py --constellation starlink --satellites 10 --location ntpu --duration 2 --interval 10

# 中等規模測試 (詳細分析)
python satellite_visibility_calculator.py --constellation starlink --satellites 100 --location ntpu --duration 12 --interval 5

# 大規模測試 (完整評估)
python satellite_visibility_calculator.py --constellation both --satellites 500 --location ntpu --duration 24 --interval 5
```

---

**這個程式實現了真正的軌道計算，修正了之前所有的座標轉換錯誤！**