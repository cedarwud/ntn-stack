# 🛰️ NTN Stack 衛星架構重構開發計畫 (Sky Project)

## 🎯 專案概述

### 📋 核心目標
本計畫旨在解決 NTN Stack 中 SimWorld 和 NetStack 之間的衛星計算功能重複問題，並整合獨立的 Starlink 衛星篩選工具。

### 🚨 問題分析
- **架構重複**: SimWorld backend 和 NetStack 都有 skyfield 依賴
- **職責混亂**: 衛星軌道計算應集中在 NetStack，SimWorld 應專注於 3D 仿真
- **依賴衝突**: 不同版本的 skyfield 可能導致計算結果不一致
- **維護困難**: 相同功能分散在多個服務中難以維護

### 🏗️ 目標架構
```
🌐 SimWorld Frontend
    ↓ (API 調用)
🎮 SimWorld Backend (純3D仿真)
    ↓ (衛星數據請求)
🛰️ NetStack API (衛星計算中心)
    ↓ (TLE數據獲取)
📡 Starlink TLE API
```

## 🚀 開發步驟流程

### Phase 0: Starlink 完整數據下載與換手篩選工具 (1天) ⚡ **可立即開始**

#### 0.1 完整 Starlink TLE 數據下載器
**目標**: 下載96分鐘(一個完整 Starlink 週期)內所有 Starlink 衛星 TLE 歷史數據

```bash
# 下載當前所有 Starlink TLE 數據
cd /home/sat/ntn-stack/netstack/src/services/satellite
python starlink_tle_downloader.py --download-all --output starlink_complete_tle.json

# 驗證下載數據
python starlink_tle_downloader.py --verify starlink_complete_tle.json
```

**核心功能**:
- [ ] 從 CelesTrak 下載所有當前 Starlink TLE 數據（~6000 顆衛星）
- [ ] 本地存儲完整數據集，避免重複下載
- [ ] 數據驗證和完整性檢查
- [ ] 支援增量更新和快取機制

#### 0.2 衛星候選預篩選器
**目標**: 基於軌道參數預篩選，排除不可能在目標座標進行換手的衛星

```python
# 預篩選功能範例
def pre_filter_satellites_by_orbit(observer_lat, observer_lon, all_tle_data):
    """
    軌道幾何預篩選
    - 基於軌道傾角判斷緯度覆蓋範圍
    - 基於軌道高度計算最大可見距離
    - 排除在96分鐘內不可能達到5度仰角的衛星
    - 大幅減少後續詳細計算的工作量
    """
    candidate_satellites = []
    excluded_satellites = []
    
    for satellite in all_tle_data:
        if can_potentially_be_visible(satellite, observer_lat, observer_lon):
            candidate_satellites.append(satellite)
        else:
            excluded_satellites.append(satellite)
    
    return candidate_satellites, excluded_satellites
```

**預篩選標準**:
- [ ] **軌道傾角檢查** - 衛星能到達的最大/最小緯度範圍
- [ ] **軌道高度檢查** - 在目標緯度的理論最大仰角
- [ ] **地理覆蓋檢查** - 軌道平面是否可能經過目標經度
- [ ] **最小距離檢查** - 衛星與目標座標的最近可能距離

**預期優化效果**:
- [ ] 從 ~6000 顆衛星篩選到 ~500-1000 顆候選衛星
- [ ] 減少後續計算量 80-90%
- [ ] 加速整體分析時間從小時級到分鐘級

#### 0.3 最佳時間段分析與數據產出
**目標**: 找出30-45分鐘的最佳換手時間段，並產出完整的衛星配置數據

```python
# 最佳時間段分析功能範例
def find_optimal_handover_timeframe(observer_lat, observer_lon, candidate_satellites):
    """
    找出30-45分鐘的最佳換手時間段
    - 分析候選衛星在不同時間段的可見性
    - 找出包含6-10顆衛星的最佳時間段
    - 確保時間段長度適合動畫展示（30-45分鐘）
    - 產出該時間段的完整衛星軌跡數據
    """
    best_timeframe = None
    max_satellite_coverage = 0
    
    # 掃描不同的30-45分鐘時間窗
    for start_time in range(0, 5760, 300):  # 每5分鐘檢查一次
        for duration in [30, 35, 40, 45]:  # 測試不同時間段長度
            timeframe_satellites = analyze_timeframe_coverage(
                candidate_satellites, start_time, duration * 60, observer_lat, observer_lon
            )
            
            if len(timeframe_satellites) > max_satellite_coverage:
                max_satellite_coverage = len(timeframe_satellites)
                best_timeframe = {
                    'start_time': start_time,
                    'duration_minutes': duration,
                    'satellites': timeframe_satellites
                }
    
    return best_timeframe
```

**分析重點**:
- [ ] **時間段最佳化** - 30-45分鐘長度，適合動畫展示
- [ ] **衛星數量最大化** - 尋找包含6-10顆衛星的時間段
- [ ] **換手連續性** - 確保時間段內有完整的換手序列
- [ ] **軌跡完整性** - 包含衛星從出現到消失的完整軌跡

**產出數據結構**:
```json
{
  "optimal_timeframe": {
    "start_timestamp": "2025-07-27T12:15:00Z",
    "duration_minutes": 40,
    "satellite_count": 8,
    "satellites": [
      {
        "norad_id": 44713,
        "name": "STARLINK-1007",
        "trajectory": [
          {"time": "2025-07-27T12:15:00Z", "elevation": 5.2, "azimuth": 45.0, "lat": 24.9, "lon": 121.4},
          {"time": "2025-07-27T12:15:30Z", "elevation": 6.1, "azimuth": 46.2, "lat": 24.95, "lon": 121.45}
          // ... 每30秒一個數據點，共80個點
        ],
        "visibility_window": {
          "rise_time": "2025-07-27T12:15:00Z",
          "peak_time": "2025-07-27T12:28:15Z", 
          "set_time": "2025-07-27T12:41:30Z"
        },
        "handover_priority": 1
      }
      // ... 其他7顆衛星
    ]
  }
}
```

#### 0.4 前端數據源格式化
**目標**: 將最佳時間段數據格式化為側邊欄和立體圖動畫所需的數據源

```python
# 前端數據格式化功能範例
def format_for_frontend_display(optimal_timeframe_data, observer_location):
    """
    格式化數據以支援前端展示需求
    - 側邊欄「衛星 gNB」數據源
    - 立體圖動畫軌跡數據源
    - 換手序列展示數據
    """
    
    # 1. 側邊欄數據源
    sidebar_data = format_sidebar_satellite_list(optimal_timeframe_data)
    
    # 2. 動畫軌跡數據源
    animation_data = format_3d_animation_trajectories(optimal_timeframe_data)
    
    # 3. 換手序列數據源
    handover_sequence_data = format_handover_sequence(optimal_timeframe_data)
    
    return {
        "sidebar_data": sidebar_data,
        "animation_data": animation_data, 
        "handover_sequence": handover_sequence_data,
        "metadata": {
            "observer_location": observer_location,
            "timeframe_info": optimal_timeframe_data["optimal_timeframe"]
        }
    }
```

**前端數據源格式**:

**1. 側邊欄「衛星 gNB」數據源**:
```json
{
  "satellite_gnb_list": [
    {
      "id": "STARLINK-1007",
      "name": "STARLINK-1007", 
      "status": "visible",
      "signal_strength": 85,
      "elevation": 25.4,
      "azimuth": 120.8,
      "distance_km": 850,
      "handover_priority": 1,
      "availability_window": "12:15:00 - 12:41:30"
    }
    // ... 其他衛星
  ]
}
```

**2. 立體圖動畫軌跡數據源**:
```json
{
  "animation_trajectories": [
    {
      "satellite_id": "STARLINK-1007",
      "trajectory_points": [
        {"time_offset": 0, "x": 850.2, "y": 120.8, "z": 350.5, "visible": true},
        {"time_offset": 30, "x": 852.1, "y": 122.1, "z": 352.2, "visible": true}
        // ... 每30秒一個3D位置點
      ],
      "animation_config": {
        "color": "#00ff00",
        "trail_length": 10,
        "visibility_threshold": 5.0
      }
    }
    // ... 其他衛星軌跡
  ],
  "animation_settings": {
    "total_duration_seconds": 2400,
    "playback_speed_multiplier": 10,
    "camera_follow_mode": "overview"
  }
}
```

**3. 換手序列展示數據**:
```json
{
  "handover_sequence": [
    {
      "sequence_id": 1,
      "from_satellite": "STARLINK-1007",
      "to_satellite": "STARLINK-1019", 
      "handover_time": "2025-07-27T12:28:45Z",
      "handover_type": "planned",
      "signal_overlap_duration": 120
    }
    // ... 其他換手事件
  ]
}
```

**座標參數化支援**:
```python
# 支援任意座標的相同分析
def generate_optimal_timeframe_for_coordinates(lat, lon, alt=0):
    """
    對任意座標執行相同的最佳時間段分析
    - 下載完整 TLE 數據
    - 預篩選候選衛星
    - 找出最佳時間段
    - 格式化前端數據源
    """
    return {
        "coordinates": {"lat": lat, "lon": lon, "alt": alt},
        "optimal_timeframe": find_optimal_handover_timeframe(lat, lon, candidate_satellites),
        "frontend_data": format_for_frontend_display(optimal_timeframe_data, {"lat": lat, "lon": lon})
    }
```

**Phase 0 驗收標準：**
- [ ] 能成功下載所有當前 Starlink TLE 數據（~6000 顆）
- [ ] 基於完整數據找出在 NTPU 座標上空真實的最佳換手時間點
- [ ] 確定該時間點的真實衛星數量和配置（自然數量，不強制限制）
- [ ] 支援任意座標輸入進行相同的最佳時機分析
- [ ] 輸出適合學術研究的標準化數據格式
- [ ] 96分鐘完整分析在合理時間內完成（< 10分鐘）

---

### Phase 1: 架構審查與分析 (1-2天)

#### 1.1 SimWorld Backend 衛星功能審查
**目標**: 識別所有使用 skyfield 的程式碼

```bash
# 搜索 SimWorld 中的 skyfield 使用
cd /home/sat/ntn-stack/simworld/backend
grep -r "skyfield" . --include="*.py"
grep -r "EarthSatellite" . --include="*.py"
grep -r "SGP4" . --include="*.py"
```

**分析項目**:
- [ ] 導入 skyfield 的檔案列表
- [ ] 衛星軌道計算相關函數
- [ ] TLE 數據處理邏輯
- [ ] 座標轉換功能

#### 1.2 NetStack 衛星功能盤點
**目標**: 確認 NetStack 現有的衛星計算能力

```bash
# 搜索 NetStack 中的衛星相關功能
cd /home/sat/ntn-stack/netstack
grep -r "skyfield" . --include="*.py"
grep -r "satellite" . --include="*.py" -i
```

**分析項目**:
- [ ] 現有的衛星 API 端點
- [ ] 軌道計算功能完整性
- [ ] TLE 數據管理機制

#### 1.3 依賴衝突分析
**目標**: 識別所有潛在的依賴重複

```bash
# 比較依賴版本
echo "=== NetStack Dependencies ==="
cat /home/sat/ntn-stack/netstack/requirements.txt | grep -E "(skyfield|sgp4|pyephem)"
echo "=== SimWorld Dependencies ==="
cat /home/sat/ntn-stack/simworld/backend/requirements.txt | grep -E "(skyfield|sgp4|pyephem)"
```

**Phase 1 驗收標準：**
- [ ] 完整的 SimWorld 衛星功能清單
- [ ] NetStack 衛星功能缺口識別
- [ ] 依賴版本衝突清單
- [ ] 功能轉移清單

### Phase 2: NetStack 衛星 API 增強 (2-3天)

#### 2.1 設計統一的衛星 API
**目標**: 創建完整的衛星計算 API，包含對 Phase 0 數據的支援

```python
# /netstack/src/api/satellite/endpoints.py (範例)
@router.get("/satellites/visibility")
async def calculate_satellite_visibility(
    observer_lat: float,
    observer_lon: float,
    observer_alt: float = 0.0,
    min_elevation: float = 5.0,
    duration_minutes: int = 96,
    time_step_seconds: int = 30
):
    """計算衛星可見性"""
    pass

@router.get("/satellites/starlink/current")
async def get_current_starlink_data():
    """獲取當前 Starlink TLE 數據"""
    pass

@router.post("/satellites/positions")
async def calculate_satellite_positions(
    satellite_ids: List[str],
    timestamps: List[str],
    observer_location: ObserverLocation
):
    """批次計算衛星位置"""
    pass

# === Phase 0 數據支援 API ===
@router.get("/satellites/optimal-timeframe")
async def get_optimal_handover_timeframe(
    observer_lat: float,
    observer_lon: float,
    duration_minutes: int = 45
):
    """獲取最佳換手時間段（Phase 0 的產出）"""
    pass

@router.get("/satellites/historical-config/{timeframe_id}")
async def get_historical_satellite_config(
    timeframe_id: str,
    observer_lat: float,
    observer_lon: float
):
    """獲取特定歷史時間段的衛星配置"""
    pass

@router.get("/satellites/frontend-data/{timeframe_id}")
async def get_frontend_data_sources(
    timeframe_id: str,
    data_type: str = "all"  # "sidebar", "animation", "handover", "all"
):
    """獲取前端展示所需的數據源（側邊欄、動畫、換手序列）"""
    pass
```

#### 2.2 整合 Starlink 篩選工具
**目標**: 將獨立工具整合到 NetStack

```bash
# NetStack 衛星模組已創建
# starlink_ntpu_visibility_finder.py 已移至 
# /home/sat/ntn-stack/netstack/src/services/satellite/starlink_ntpu_visibility_finder.py
```

**整合要點**:
- [ ] 重構為 FastAPI 服務
- [ ] 添加異步支援
- [ ] 實現數據緩存
- [ ] 添加錯誤處理

#### 2.3 TLE 數據管理系統
**目標**: 建立可靠的 TLE 數據更新機制，包含 Phase 0 歷史數據持久化

```python
# /netstack/src/services/satellite/tle_manager.py (範例)
class TLEDataManager:
    async def download_latest_starlink_tle(self) -> List[TLEData]:
        """下載最新 Starlink TLE 數據"""
        pass
        
    async def cache_tle_data(self, tle_data: List[TLEData]) -> None:
        """緩存 TLE 數據"""
        pass
        
    async def get_cached_tle_data(self) -> Optional[List[TLEData]]:
        """獲取緩存的 TLE 數據"""
        pass
    
    # === Phase 0 歷史數據管理 ===
    async def store_optimal_timeframe(self, timeframe_data: dict, coordinates: dict) -> str:
        """存儲最佳時間段數據，返回 timeframe_id"""
        pass
    
    async def get_optimal_timeframe(self, timeframe_id: str) -> Optional[dict]:
        """獲取存儲的最佳時間段數據"""
        pass
    
    async def store_frontend_data(self, timeframe_id: str, frontend_data: dict) -> None:
        """存儲前端展示數據（側邊欄、動畫、換手序列）"""
        pass
    
    async def get_frontend_data(self, timeframe_id: str, data_type: str = "all") -> dict:
        """獲取前端展示數據"""
        pass
    
    async def cache_coordinate_analysis(self, coordinates: dict, analysis_result: dict) -> None:
        """緩存座標分析結果，支援座標參數化"""
        pass
```

**Phase 2 驗收標準：**
- [ ] 衛星可見性 API 正常運作
- [ ] Starlink TLE 數據自動更新
- [ ] 批次位置計算 API 測試通過
- [ ] **Phase 0 數據支援 API 正常運作**
- [ ] **最佳時間段數據能正確存儲和檢索**
- [ ] **前端數據源 API 回應格式正確**
- [ ] API 文檔自動生成

### Phase 3: SimWorld 衛星功能移除 (2-3天)

#### 3.1 識別需要移除的程式碼
**目標**: 準確識別所有需要移除的衛星計算相關程式碼

```bash
# 創建移除清單
echo "# SimWorld 衛星功能移除清單" > remove_list.md
echo "## 需要移除的檔案" >> remove_list.md
find /home/sat/ntn-stack/simworld/backend -name "*.py" -exec grep -l "skyfield\|EarthSatellite" {} \; >> remove_list.md
```

#### 3.2 重構 SimWorld 為 NetStack 客戶端
**目標**: 修改 SimWorld 使用 NetStack 的衛星 API

```python
# /simworld/backend/src/services/satellite_client.py (範例)
class NetStackSatelliteClient:
    def __init__(self, netstack_url: str):
        self.netstack_url = netstack_url
        
    async def get_satellite_visibility(self, params: VisibilityParams):
        """從 NetStack 獲取衛星可見性數據"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.netstack_url}/api/satellites/visibility",
                params=params.dict()
            )
            return response.json()
```

#### 3.3 更新 SimWorld API 端點
**目標**: 修改 SimWorld 的 API 端點使其代理到 NetStack

```python
# /simworld/backend/src/api/satellite_proxy.py (範例)
@router.get("/satellites/visibility")
async def get_satellite_visibility_proxy(
    observer_lat: float,
    observer_lon: float,
    params: dict = Depends()
):
    """代理到 NetStack 的衛星可見性 API"""
    client = NetStackSatelliteClient(settings.NETSTACK_URL)
    return await client.get_satellite_visibility(params)
```

#### 3.4 移除 skyfield 依賴
**目標**: 清理 SimWorld 的 requirements.txt

```bash
# 備份並更新 requirements.txt
cp /home/sat/ntn-stack/simworld/backend/requirements.txt \
   /home/sat/ntn-stack/simworld/backend/requirements.txt.backup

# 移除 skyfield 相關依賴
sed -i '/skyfield/d' /home/sat/ntn-stack/simworld/backend/requirements.txt
```

**Phase 3 驗收標準：**
- [ ] SimWorld 不再有 skyfield 依賴
- [ ] 所有衛星計算通過 NetStack API
- [ ] SimWorld 原有功能保持正常
- [ ] Docker 容器重建成功

### Phase 4: 整合測試與優化 (2-3天)

#### 4.1 端對端測試
**目標**: 確保整個數據流正常運作

```bash
# 測試完整流程
cd /home/sat/ntn-stack

# 1. 重建容器
make down && make up

# 2. 測試 NetStack 衛星 API
curl "http://localhost:8080/api/satellites/visibility?observer_lat=24.9441667&observer_lon=121.3713889"

# 3. 測試 Phase 0 數據 API
curl "http://localhost:8080/api/satellites/optimal-timeframe?observer_lat=24.9441667&observer_lon=121.3713889&duration_minutes=40"

# 4. 測試前端數據源 API
curl "http://localhost:8080/api/satellites/frontend-data/test_timeframe_id?data_type=all"

# 5. 測試 SimWorld 代理功能
curl "http://localhost:8888/api/satellites/visibility?observer_lat=24.9441667&observer_lon=121.3713889"

# 6. 測試前端顯示
curl "http://localhost:5173"
```

#### 4.2 性能測試
**目標**: 確保重構後性能沒有劣化

```python
# /tests/performance/satellite_api_benchmark.py (範例)
import asyncio
import time
import httpx

async def benchmark_satellite_api():
    """測試衛星 API 性能"""
    start_time = time.time()
    
    async with httpx.AsyncClient() as client:
        tasks = []
        for i in range(10):  # 並發10個請求
            task = client.get(
                "http://localhost:8080/api/satellites/visibility",
                params={"observer_lat": 24.9441667, "observer_lon": 121.3713889}
            )
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks)
    
    end_time = time.time()
    print(f"10個並發請求耗時: {end_time - start_time:.2f} 秒")
```

#### 4.3 數據一致性驗證
**目標**: 確保重構前後數據計算結果一致

```python
# /tests/validation/data_consistency_test.py (範例)
def test_orbital_calculation_consistency():
    """驗證軌道計算結果一致性"""
    # 使用相同的 TLE 數據和時間點
    # 比較重構前後的計算結果
    # 容差設定為 0.01 度
    pass
```

**Phase 4 驗收標準：**
- [ ] 所有 API 端點回應正常
- [ ] **Phase 0 數據 API 端點正確回應**
- [ ] **前端數據源格式驗證通過**
- [ ] 性能測試通過基準線
- [ ] 數據一致性測試通過
- [ ] 前端顯示正常

### Phase 5: 文檔更新與部署 (1天)

#### 5.1 API 文檔更新
**目標**: 更新所有相關文檔

```bash
# 生成 API 文檔
cd /home/sat/ntn-stack/netstack
python -c "
from src.main import app
import json
print(json.dumps(app.openapi(), indent=2))
" > api_docs.json
```

#### 5.2 架構文檔更新
**目標**: 更新系統架構圖和說明

```markdown
# 更新 README.md 中的架構說明
## 新的衛星數據流

SimWorld Frontend → SimWorld Backend → NetStack API → TLE 數據源
               ↑                    ↑             ↑
           衛星顯示              代理請求        計算處理
```

#### 5.3 部署檢查清單
**目標**: 確保生產環境部署順利

```bash
# 部署前檢查
echo "# 生產部署檢查清單" > deployment_checklist.md
echo "- [ ] 所有測試通過" >> deployment_checklist.md
echo "- [ ] Docker 映像建置成功" >> deployment_checklist.md
echo "- [ ] 環境變數配置正確" >> deployment_checklist.md
echo "- [ ] 數據庫遷移完成" >> deployment_checklist.md
```

**Phase 5 驗收標準：**
- [ ] API 文檔完整且正確
- [ ] 架構文檔已更新
- [ ] 部署指南完整
- [ ] 生產環境測試通過

## 🔧 技術實施細節

### 🛠️ 關鍵代碼重構

#### NetStack 衛星服務架構
```python
# /netstack/src/services/satellite/
├── __init__.py
├── tle_manager.py          # TLE 數據管理
├── orbital_calculator.py   # 軌道計算
├── visibility_analyzer.py  # 可見性分析
├── starlink_finder.py      # Starlink 篩選工具
└── models.py              # 數據模型
```

#### SimWorld 客戶端架構
```python
# /simworld/backend/src/clients/
├── __init__.py
├── netstack_client.py     # NetStack API 客戶端
└── satellite_proxy.py     # 衛星數據代理
```

### 🔄 數據流重新設計

#### 原有流程 (有問題)
```
SimWorld Frontend → SimWorld Backend (skyfield) → 直接計算
NetStack Backend → 獨立 skyfield 計算 → 重複功能
```

#### 新流程 (重構後)
```
SimWorld Frontend → SimWorld Backend → NetStack API → 統一計算
獨立篩選工具 → 整合到 NetStack → 統一管理
```

### 📊 性能優化策略

#### TLE 數據緩存
```python
# Redis 緩存策略
CACHE_TTL = 3600  # 1小時
CACHE_KEY_PATTERN = "starlink_tle:{date}"

async def get_cached_tle_data():
    cache_key = f"starlink_tle:{datetime.now().strftime('%Y%m%d')}"
    cached_data = await redis.get(cache_key)
    if cached_data:
        return json.loads(cached_data)
    return None
```

#### 批次計算優化
```python
# 向量化計算
async def batch_calculate_positions(satellites, times, observer):
    """批次計算多顆衛星在多個時間點的位置"""
    # 使用 NumPy 向量化操作
    # 減少循環次數，提升計算效率
    pass
```

## 🚨 風險管控

### ⚠️ 重構風險評估

| 風險項目 | 影響程度 | 機率 | 緩解措施 |
|---------|---------|------|---------|
| API 性能下降 | 高 | 中 | 性能基準測試 + 緩存優化 |
| 數據不一致 | 高 | 低 | 詳細的一致性測試 |
| 前端功能異常 | 中 | 中 | 完整的端對端測試 |
| 容器啟動失敗 | 中 | 低 | 分階段容器重建 |

### 🛡️ 回滾計畫

#### 緊急回滾步驟
```bash
# 1. 快速回滾到重構前狀態
git checkout HEAD~1
make down && make up

# 2. 恢復 SimWorld skyfield 依賴
cp simworld/backend/requirements.txt.backup simworld/backend/requirements.txt

# 3. 重建容器
docker-compose build simworld_backend
```

### 📋 測試策略

#### 單元測試
- [ ] TLE 數據下載測試
- [ ] 軌道計算準確性測試
- [ ] API 端點回應測試

#### 整合測試
- [ ] SimWorld → NetStack 數據流測試
- [ ] 前端顯示功能測試
- [ ] 錯誤處理機制測試

#### 性能測試
- [ ] 單一請求響應時間 < 100ms
- [ ] 並發10個請求處理正常
- [ ] 記憶體使用率 < 80%

## 📅 時程規劃

### 🗓️ 詳細時程表

| 階段 | 時間 | 主要任務 | 交付物 |
|------|------|---------|--------|
| **Phase 0** | **Day 1** | **獨立篩選工具完善** ⚡ | **穩定篩選工具、標準化輸出** |
| Phase 1 | Day 1-2 | 架構審查與分析 | 分析報告、功能清單 |
| Phase 2 | Day 3-5 | NetStack API 增強 | 衛星 API、整合工具 |
| Phase 3 | Day 6-8 | SimWorld 功能移除 | 重構代碼、客戶端 |
| Phase 4 | Day 9-11 | 整合測試與優化 | 測試報告、性能數據 |
| Phase 5 | Day 12 | 文檔更新與部署 | 更新文檔、部署指南 |

### ⏰ 里程碑檢查點

- **里程碑 0 (Day 1)**: 獨立篩選工具完善，可立即用於研究 ⚡
- **里程碑 1 (Day 2)**: 完成架構分析，確認重構範圍
- **里程碑 2 (Day 5)**: NetStack 衛星 API 基本功能完成
- **里程碑 3 (Day 8)**: SimWorld 成功切換到 NetStack 客戶端模式
- **里程碑 4 (Day 11)**: 所有測試通過，系統穩定運行
- **里程碑 5 (Day 12)**: 重構完成，文檔更新，準備生產部署

## 🏆 成功標準

### ✅ 功能性標準
- [ ] SimWorld 不再有 skyfield 依賴
- [ ] 所有衛星計算統一由 NetStack 處理
- [ ] Starlink 篩選工具整合到 NetStack
- [ ] 前端功能保持完整

### 📈 非功能性標準
- [ ] API 響應時間 ≤ 重構前
- [ ] 系統穩定性 ≥ 99.5%
- [ ] 記憶體使用優化 ≥ 10%
- [ ] 代碼維護性顯著提升

### 🎯 學術研究標準
- [ ] 衛星軌道計算精度保持
- [ ] TLE 數據更新機制可靠
- [ ] 支援大規模並發計算
- [ ] 數據來源可追溯性

---

**⚡ 重構成功的關鍵：簡化架構，統一數據源，提升維護性**

*📝 本計畫遵循 NTN Stack 開發原則，確保 LEO 衛星換手研究的學術嚴謹性*
