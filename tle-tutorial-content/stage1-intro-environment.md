# 階段1：課程介紹與環境設置

## 課程目標與學習成果

### 完成本課程後您將能夠：
- 完全理解TLE數據的每一個參數含義
- 獨立設置完整的SGP4計算環境
- 編寫專業級的衛星軌道計算程式
- 開發完整的Stage1TLEProcessor處理器
- 處理8000+顆衛星的批量軌道計算
- 驗證計算結果的物理合理性
- 解決實際專案中的常見技術問題

### 職業發展價值：
- 具備衛星系統工程師的核心技能
- 能夠參與商業衛星專案開發
- 掌握航太工程的實際應用技術
- 具備學術研究和論文發表基礎

## 完整學習路徑規劃

### 8階段系統性學習路徑：

1. **課程介紹與環境設置** (本階段)
   - Docker + Python 開發環境
   - 衛星星座基礎數據

2. **TLE數據格式深度解析**
   - 三行TLE格式完全掌握

3. **SGP4軌道計算算法**
   - 時間基準關鍵原則

4. **座標系統轉換實作**
   - ECI/ECEF/地理座標

5. **Stage1TLEProcessor架構設計**

6. **完整程式實作 Step by Step**

7. **數據驗證和品質控制**

8. **除錯和故障排除**

## LEO衛星通訊系統基礎

### LEO (Low Earth Orbit) 低軌道衛星特性：

**基本參數：**
- 軌道高度：500-2000 km
- 軌道速度：約7.8 km/s
- 軌道週期：90-120分鐘
- 通訊延遲：5-25 ms (vs GEO 250ms)

### 為什麼選擇LEO？
- **低延遲**：即時通訊體驗
- **高吞吐量**：更好的信號品質
- **全球覆蓋**：包含極地區域
- **成本效益**：發射成本相對較低

### 技術挑戰：
- 快速移動→需要精確軌道預測
- 頻繁換手→需要智慧路由算法
- 大規模星座→需要高效管理系統

## Starlink星座數據分析

### 最新數據 (2025年9月)：
- **運行衛星數**：8,370 顆
- **總發射數**：9,000+ 顆
- **成功率**：約93%

### 軌道配置：
- **Shell 1**：540 km，53°傾角
- **Shell 2**：570 km，53°傾角  
- **Shell 3**：560 km，70°傾角
- **Shell 4**：540 km，97.6°傾角

### 技術規格：
- 衛星重量：260-300 kg (V1.5/V2)
- 通訊頻段：Ku/Ka波段
- 功率：~5kW 太陽能板
- 服務：寬頻網路、直連手機

### 創新特色：
- 激光星間鏈路
- 自主避碰系統

## OneWeb星座數據分析

### 最新數據 (2025年9月)：
- **運行衛星數**：648 顆
- **計畫總數**：648 顆
- 軌道高度：1200 km
- 軌道傾角：87.4° (近極地軌道)

### 市場定位：
- 企業和政府客戶
- 偏遠地區連接
- 海事和航空通訊
- 5G回程網路

### 與Starlink差異比較：
- 更高軌道 (1200km vs 550km)
- 更少衛星需求 (648 vs 8000+)
- 極地覆蓋更優 (87.4° vs 53°)
- B2B市場導向 vs B2C

### 技術規格：
- 衛星重量：147kg
- 通訊頻段：Ku/Ka波段

## 為什麼需要精確的TLE軌道計算？

### 實際應用需求：

**衛星通訊優化：**
- 預測最佳衛星選擇時機
- 計算信號強度和仰角
- 規劃換手策略

**網路路由決策：**
- 動態選擇最優衛星
- 預測連接中斷時間
- 負載平衡優化

### 精確度的重要性：
- 誤差1度 = 100km位置偏差
- 時間基準錯誤 → 完全無法預測
- 實際案例：8000顆→0顆可見

### 商業價值：
- 提升用戶體驗
- 降低運營成本
- 增強系統可靠性

## Docker開發環境完整設置

### 系統需求：
- Ubuntu 20.04+ 或 macOS 10.15+
- 8GB+ RAM，4核心+ CPU
- 20GB+ 可用磁碟空間

### 安裝步驟：
1. 安裝Docker Engine
2. 配置用戶權限
3. 下載衛星處理基礎映像
4. 設置數據卷映射

### 驗證指令：
```bash
docker --version
docker run hello-world
docker pull python:3.9-slim
```

### 為什麼使用Docker？
- 環境一致性
- 依賴隔離
- 快速部署
- 跨平台支援

## Python環境配置

### Python版本需求：
- Python 3.8+ (建議 3.9+)
- pip 最新版本
- venv 虛擬環境支援

### 虛擬環境設置：
```bash
# 創建虛擬環境
python -m venv tle_env

# 啟動虛擬環境
source tle_env/bin/activate  # Linux/Mac
tle_env\Scripts\activate     # Windows

# 升級pip
pip install --upgrade pip
```

### 版本驗證：
```bash
python --version  # 應該 >= 3.8
pip --version     # 確認pip可用
```

## 核心依賴套件安裝

### 必要套件清單：

```bash
# 核心計算套件
pip install skyfield>=1.46
pip install numpy>=1.21.0
pip install astropy>=5.0

# 時間處理
pip install pytz>=2021.1

# 數據處理
pip install pandas>=1.3.0
pip install scipy>=1.7.0

# 開發工具
pip install jupyter>=1.0.0
pip install matplotlib>=3.4.0
```

### 一次性安裝：
```bash
pip install skyfield numpy astropy pytz \
            pandas scipy jupyter matplotlib
```

## 環境驗證程式實作

### 環境驗證Python程式：

```python
#!/usr/bin/env python3
import sys
import importlib

def verify_tle_environment():
    print("🔍 驗證TLE計算環境...")
    
    # 檢查Python版本
    if sys.version_info >= (3, 8):
        print(f"✅ Python: {sys.version_info}")
    else:
        print(f"❌ Python版本不足")
        return False
    
    # 檢查必要套件
    packages = ['skyfield', 'numpy', 'astropy']
    for pkg in packages:
        try:
            importlib.import_module(pkg)
            print(f"✅ {pkg}: 已安裝")
        except ImportError:
            print(f"❌ 缺少: {pkg}")
            return False
    
    print("🎉 環境驗證完成！")
    return True

if __name__ == "__main__":
    verify_tle_environment()
```

## 推薦開發工具配置

### 推薦IDE選擇：

**Visual Studio Code (推薦)**
- Python 擴展套件
- Jupyter 支援
- Git 整合
- Docker 擴展

**PyCharm Professional**
- 強大的除錯功能
- 智慧程式碼完成
- 內建測試工具

**Jupyter Lab**
- 適合數據分析
- 互動式開發
- 視覺化支援

### 必要VSCode擴展：
- Python (Microsoft)
- Pylance
- Jupyter
- Docker
- GitLens

## 開發前準備檢查清單

### 環境準備檢查清單：

**Docker環境：**
- [ ] Docker Engine 已安裝
- [ ] docker --version 顯示正常
- [ ] docker run hello-world 成功

**Python環境：**
- [ ] Python 3.8+ 已安裝
- [ ] 虛擬環境已創建並啟動
- [ ] pip 已升級到最新版本

**依賴套件：**
- [ ] skyfield 已安裝
- [ ] numpy、astropy 已安裝
- [ ] 環境驗證程式執行成功

**開發工具：**
- [ ] IDE (VSCode/PyCharm) 已配置
- [ ] Git 已安裝並配置
- [ ] 專案目錄已準備

**全部勾選完成後，即可開始TLE實作學習！**

## 階段總結

### 階段1學習成果確認：

**掌握的核心知識：**
- LEO衛星系統基礎概念
- Starlink 8,370顆衛星數據
- OneWeb 648顆衛星數據
- TLE計算的重要性和應用

**完成的技術準備：**
- Docker + Python 開發環境
- skyfield等核心套件安裝
- 環境驗證程式測試通過
- IDE開發工具配置

**下一步行動計畫：**
- 進入階段2：TLE數據格式深度解析
- 學習三行TLE數據的每個參數
- 實作完整的TLE解析器

**重要提醒：確保環境設置都正常運作再繼續！**