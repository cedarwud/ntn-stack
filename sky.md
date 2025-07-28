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
    ↓ (本地TLE數據讀取)
📂 45天收集TLE數據 (/tle_data/)
    ├── starlink/ (45個每日文件)
    └── oneweb/ (45個每日文件)
```

## 🚀 開發步驟流程

### Phase 0: 本地 TLE 數據收集與換手篩選工具 (45天收集 + 1天分析) ⚡ **可立即開始**

#### 0.1 45天本地 TLE 數據收集基礎設施
**目標**: 建立每日 TLE 數據收集系統，支援 45 天 RL 研究數據需求

**數據收集架構**:
```bash
# 實際的數據收集結構 (基於實際日期命名)
/home/sat/ntn-stack/tle_data/
├── starlink/                         # Starlink 數據目錄
│   ├── tle/                         # TLE 格式數據
│   │   ├── starlink_20250727.tle   # 基於數據實際日期
│   │   ├── starlink_20250728.tle   # 智能日期命名
│   │   └── ...                      # 收集期間的所有日期
│   └── json/                        # JSON 格式數據
│       ├── starlink_20250727.json  # 與 TLE 使用相同日期
│       ├── starlink_20250728.json
│       └── ...
└── oneweb/                           # OneWeb 數據目錄
    ├── tle/
    │   ├── oneweb_20250727.tle     # 基於數據實際日期
    │   └── ...
    └── json/
        ├── oneweb_20250727.json    # 與 TLE 使用相同日期
        └── ...
```

**核心功能**:
- [x] **數據目錄結構建立** - 支援 TLE + JSON 雙格式
- [x] **智能檔案命名** - 基於數據實際日期而非下載日期
- [x] **自動化收集工具** - 增強版下載腳本支援智能更新檢查
- [ ] **本地TLE數據加載器** - 從收集的文件讀取歷史數據
- [ ] **數據完整性檢查** - 驗證每日數據品質和連續性
- [ ] **建置時數據預處理** - Docker建置階段處理所有45天數據

#### 0.2 本地數據加載與驗證系統
**目標**: 處理用戶手動收集的真實 TLE 歷史數據

```python
# 本地數據加載器增強 (支援實際日期命名和雙格式)
def load_collected_tle_data(constellation='starlink', start_date=None, end_date=None):
    """
    載入手動收集的TLE歷史數據
    - 自動掃描可用的日期檔案 (YYYYMMDD 格式)
    - 支援 TLE 和 JSON 雙格式讀取
    - 驗證格式完整性和數據品質
    - 支援 Starlink 和 OneWeb 雙星座
    - 可指定日期範圍或自動檢測
    """
    tle_dir = f"/app/tle_data/{constellation}/tle/"
    json_dir = f"/app/tle_data/{constellation}/json/"
    collected_data = []
    available_dates = []
    
    # 掃描可用的 TLE 檔案日期
    import glob
    import re
    
    tle_pattern = f"{tle_dir}{constellation}_*.tle"
    tle_files = glob.glob(tle_pattern)
    
    for tle_file in tle_files:
        # 提取日期 (YYYYMMDD)
        match = re.search(r'(\d{8})\.tle$', tle_file)
        if match:
            date_str = match.group(1)
            
            # 檢查日期範圍過濾
            if start_date and date_str < start_date:
                continue
            if end_date and date_str > end_date:
                continue
                
            if file_exists_and_valid(tle_file):
                # 檢查對應的 JSON 檔案
                json_file = f"{json_dir}{constellation}_{date_str}.json"
                has_json = file_exists_and_valid(json_file)
                
                # 解析 TLE 數據
                daily_tle_data = parse_tle_file(tle_file)
                daily_json_data = parse_json_file(json_file) if has_json else None
                
                collected_data.append({
                    'date': date_str,
                    'tle_file': tle_file,
                    'json_file': json_file if has_json else None,
                    'satellite_count': len(daily_tle_data),
                    'tle_data': daily_tle_data,
                    'json_data': daily_json_data,
                    'has_dual_format': has_json
                })
                available_dates.append(date_str)
    
    # 按日期排序
    collected_data.sort(key=lambda x: x['date'])
    available_dates.sort()
    
    return {
        'constellation': constellation,
        'total_days_collected': len(collected_data),
        'date_range': {
            'start': available_dates[0] if available_dates else None,
            'end': available_dates[-1] if available_dates else None,
            'available_dates': available_dates
        },
        'dual_format_coverage': sum(1 for d in collected_data if d['has_dual_format']),
        'coverage_percentage': len(collected_data) / len(available_dates) * 100 if available_dates else 0,
        'daily_data': collected_data
    }
```

**驗證標準**:
- [ ] **格式正確性** - 所有TLE行符合標準格式(69字符)
- [ ] **時間連續性** - 檢查45天數據的時間跨度
- [ ] **星座完整性** - Starlink(~7000顆) + OneWeb(~600顆)
- [ ] **軌道參數合理性** - 高度、傾角、週期在合理範圍

#### 0.3 Docker建置時預計算整合
**目標**: 在容器建置階段處理手動收集的歷史數據，實現RL研究需求

```dockerfile
# 修改後的Dockerfile預計算整合
# 位置: /netstack/docker/Dockerfile

# 複製手動收集的TLE數據到容器 (支援TLE+JSON雙格式)
COPY ../tle_data/ /app/tle_data/

# 建置時預計算基於實際收集數據的軌道計算
RUN python3 generate_precomputed_satellite_data.py \
    --tle_source local_collection \
    --input_dir /app/tle_data \
    --output /app/data/rl_research_collected_data.sql \
    --observer_lat 24.94417 --observer_lon 121.37139 \
    --time_step_seconds 30 \
    --constellations starlink,oneweb \
    --auto_detect_date_range \
    --support_dual_format
```

**建置階段增強功能**:
```python
# 建置時數據處理邏輯 (generate_precomputed_satellite_data.py)
def process_collected_data():
    """
    處理手動收集的數據，支援實際日期命名
    """
    # 1. 自動掃描可用的數據檔案
    starlink_data = load_collected_tle_data('starlink')
    oneweb_data = load_collected_tle_data('oneweb')
    
    # 2. 檢查數據覆蓋率和品質
    total_days = len(set(starlink_data['date_range']['available_dates'] + 
                        oneweb_data['date_range']['available_dates']))
    
    print(f"📊 建置時數據統計:")
    print(f"  - Starlink: {starlink_data['total_days_collected']} 天數據")
    print(f"  - OneWeb: {oneweb_data['total_days_collected']} 天數據") 
    print(f"  - 總覆蓋期間: {total_days} 天")
    print(f"  - 雙格式支援: {starlink_data['dual_format_coverage']}/Starlink + {oneweb_data['dual_format_coverage']}/OneWeb")
    
    # 3. 預計算軌道數據
    return precompute_orbital_data(starlink_data, oneweb_data)
```

**預計算增強功能**:
- [x] **智能日期掃描** - 自動檢測可用數據的日期範圍，無需固定45天
- [x] **雙格式支援** - 同時處理 TLE 和 JSON 格式數據
- [ ] **多星座支援** - 同時處理Starlink和OneWeb歷史數據
- [ ] **時間軸重建** - 基於實際收集日期重現歷史軌道演化
- [ ] **數據品質評估** - 建置時檢查數據完整性和覆蓋率
- [ ] **RL訓練數據格式** - 產出適合強化學習的標準化數據集

#### 0.4 換手分析與最佳時間段識別
**目標**: 基於45天真實歷史數據找出最佳換手時間段

```python
# 45天歷史分析增強
def analyze_45day_handover_patterns(collected_data, observer_location):
    """
    基於45天歷史數據分析換手模式
    - 識別重複出現的最佳換手時間段
    - 分析星座間的互補性（Starlink vs OneWeb）
    - 計算長期可見性統計
    - 產出RL研究用的训练数据
    """
    optimal_timeframes = []
    constellation_comparison = {}
    
    for day_data in collected_data:
        # 分析每日的30-45分鐘最佳時間段
        daily_optimal = find_optimal_handover_timeframe(
            day_data['data'], observer_location, duration_minutes=40
        )
        
        # 記錄每日最佳配置
        optimal_timeframes.append({
            'day': day_data['day'],
            'timeframe': daily_optimal,
            'satellite_count': len(daily_optimal.get('satellites', [])),
            'constellation': 'starlink'  # 或 'oneweb'
        })
    
    return {
        'daily_optimal_timeframes': optimal_timeframes,
        'pattern_analysis': analyze_recurring_patterns(optimal_timeframes),
        'constellation_coverage': constellation_comparison,
        'rl_training_dataset': format_for_rl_training(optimal_timeframes)
    }
```

**Phase 0 驗收標準：**
- [x] **數據收集基礎設施** - TLE+JSON 雙格式目錄結構完全建立
- [x] **智能下載工具** - 增強版腳本支援實際日期命名和智能更新檢查
- [ ] **本地數據加載器** - 能處理基於實際日期命名的手動收集數據
- [ ] **Docker建置階段預處理** - 自動掃描並處理所有可用歷史數據
- [ ] **數據品質評估** - 建置時檢查數據完整性、覆蓋率和雙格式支援度
- [ ] **最佳換手時間模式** - 基於真實歷史數據找出台灣上空最佳時間段
- [ ] **RL訓練數據集** - 產出標準化的強化學習訓練數據
- [x] **雙星座支援** - Starlink和OneWeb數據同時收集和分析
- [x] **完整文檔** - 數據收集工作流程完整，支援每日自動化操作

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

#### 2.3 本地TLE數據管理系統
**目標**: 建立基於45天收集數據的管理機制，取代網路即時下載

```python
# /netstack/src/services/satellite/local_tle_manager.py (範例)
class LocalTLEDataManager:
    def __init__(self, tle_data_dir: str = "/app/tle_data"):
        self.tle_data_dir = Path(tle_data_dir)
        
    async def load_collected_data(self, constellation: str = "starlink", 
                                 start_date: str = None, end_date: str = None) -> List[Dict]:
        """載入手動收集的TLE數據 (支援實際日期命名)"""
        tle_dir = self.tle_data_dir / constellation / "tle"
        json_dir = self.tle_data_dir / constellation / "json"
        collected_data = []
        
        # 掃描所有可用的 TLE 檔案
        import glob
        import re
        
        tle_pattern = str(tle_dir / f"{constellation}_*.tle")
        tle_files = glob.glob(tle_pattern)
        
        for tle_file in tle_files:
            # 提取實際日期 (YYYYMMDD)
            match = re.search(r'(\d{8})\.tle$', tle_file)
            if match:
                date_str = match.group(1)
                
                # 日期範圍過濾
                if start_date and date_str < start_date:
                    continue
                if end_date and date_str > end_date:
                    continue
                
                tle_path = Path(tle_file)
                json_path = json_dir / f"{constellation}_{date_str}.json"
                
                if tle_path.exists() and tle_path.stat().st_size > 0:
                    # 解析 TLE 數據
                    daily_tle_data = await self.parse_tle_file(tle_path)
                    daily_json_data = None
                    
                    # 嘗試讀取對應的 JSON 數據
                    if json_path.exists() and json_path.stat().st_size > 0:
                        daily_json_data = await self.parse_json_file(json_path)
                    
                    if daily_tle_data:
                        collected_data.append({
                            'date': date_str,
                            'tle_file': str(tle_path),
                            'json_file': str(json_path) if daily_json_data else None,
                            'satellites': daily_tle_data,
                            'satellite_count': len(daily_tle_data),
                            'json_metadata': daily_json_data,
                            'has_dual_format': daily_json_data is not None
                        })
        
        # 按日期排序
        collected_data.sort(key=lambda x: x['date'])
        return collected_data
        
    async def get_data_coverage_status(self) -> Dict[str, Any]:
        """檢查手動收集數據的狀態和覆蓋率"""
        # 獲取兩個星座的數據
        starlink_data = await self.load_collected_data('starlink')
        oneweb_data = await self.load_collected_data('oneweb')
        
        # 計算日期覆蓋範圍
        all_dates = set()
        starlink_dates = {d['date'] for d in starlink_data}
        oneweb_dates = {d['date'] for d in oneweb_data}
        all_dates.update(starlink_dates)
        all_dates.update(oneweb_dates)
        
        status = {
            'starlink': {
                'days_collected': len(starlink_data),
                'dates': sorted(list(starlink_dates)),
                'dual_format_count': sum(1 for d in starlink_data if d['has_dual_format']),
                'dual_format_percentage': sum(1 for d in starlink_data if d['has_dual_format']) / len(starlink_data) * 100 if starlink_data else 0
            },
            'oneweb': {
                'days_collected': len(oneweb_data),
                'dates': sorted(list(oneweb_dates)),
                'dual_format_count': sum(1 for d in oneweb_data if d['has_dual_format']),
                'dual_format_percentage': sum(1 for d in oneweb_data if d['has_dual_format']) / len(oneweb_data) * 100 if oneweb_data else 0
            },
            'overall': {
                'total_unique_dates': len(all_dates),
                'date_range': {
                    'start': min(all_dates) if all_dates else None,
                    'end': max(all_dates) if all_dates else None
                },
                'common_dates': len(starlink_dates & oneweb_dates),
                'coverage_days': len(all_dates)
            }
        }
        
        return status
    
    async def validate_daily_data_quality(self, constellation: str, date_str: str) -> Dict[str, Any]:
        """驗證特定日期數據品質 (基於實際日期 YYYYMMDD)"""
        tle_path = self.tle_data_dir / constellation / "tle" / f"{constellation}_{date_str}.tle"
        json_path = self.tle_data_dir / constellation / "json" / f"{constellation}_{date_str}.json"
        
        if not tle_path.exists():
            return {'valid': False, 'error': 'TLE file not found', 'date': date_str}
            
        # 解析 TLE 數據
        satellites = await self.parse_tle_file(tle_path)
        
        # 嘗試解析 JSON 數據
        json_data = None
        has_json = json_path.exists() and json_path.stat().st_size > 0
        if has_json:
            json_data = await self.parse_json_file(json_path)
        
        validation_result = {
            'valid': True,
            'date': date_str,
            'satellite_count': len(satellites),
            'has_dual_format': has_json,
            'json_satellite_count': len(json_data) if json_data else 0,
            'format_errors': [],
            'orbit_warnings': [],
            'data_quality_score': 0
        }
        
        # 詳細驗證邏輯
        for sat in satellites:
            if not self.validate_tle_format(sat):
                validation_result['format_errors'].append(f"Invalid TLE: {sat.get('name', 'Unknown')}")
            
            if not self.validate_orbital_parameters(sat):
                validation_result['orbit_warnings'].append(f"Suspicious orbit: {sat.get('name', 'Unknown')}")
        
        # 計算品質分數
        total_sats = len(satellites)
        format_errors = len(validation_result['format_errors'])
        orbit_warnings = len(validation_result['orbit_warnings'])
        
        if total_sats > 0:
            validation_result['data_quality_score'] = max(0, 
                100 - (format_errors * 10) - (orbit_warnings * 2))
        
        validation_result['valid'] = (format_errors == 0 and total_sats > 0)
        
        return validation_result
    
    # === Phase 0 歷史數據管理增強 ===
    async def store_optimal_timeframe(self, timeframe_data: dict, coordinates: dict) -> str:
        """存儲基於45天數據分析的最佳時間段"""
        timeframe_id = f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        analysis_result = {
            'id': timeframe_id,
            'coordinates': coordinates,
            'analysis_period': '45_days',
            'data_source': 'local_collection',
            'timeframe_data': timeframe_data,
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        # 存儲到數據庫或文件
        await self.save_analysis_result(analysis_result)
        return timeframe_id
    
    async def get_optimal_timeframe(self, timeframe_id: str) -> Optional[dict]:
        """獲取存儲的最佳時間段數據"""
        return await self.load_analysis_result(timeframe_id)
    
    async def get_rl_training_dataset(self, constellation: str = "starlink", 
                                     start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        """產出RL研究用的收集期間訓練數據集"""
        collected_data = await self.load_collected_data(constellation, start_date, end_date)
        
        if not collected_data:
            return {'error': 'No collected data available'}
        
        # 計算日期統計
        dates = [d['date'] for d in collected_data]
        dual_format_count = sum(1 for d in collected_data if d['has_dual_format'])
        
        training_dataset = {
            'metadata': {
                'constellation': constellation,
                'total_days': len(collected_data),
                'date_range': {
                    'start': min(dates) if dates else None,
                    'end': max(dates) if dates else None,
                    'available_dates': sorted(dates)
                },
                'dual_format_coverage': {
                    'count': dual_format_count,
                    'percentage': dual_format_count / len(collected_data) * 100 if collected_data else 0
                },
                'data_source': 'local_manual_collection',
                'collection_method': 'enhanced_download_script_with_intelligent_dating'
            },
            'daily_samples': [],
            'aggregated_statistics': {},
            'handover_patterns': {}
        }
        
        # 處理每日數據為RL訓練樣本
        for day_data in collected_data:
            daily_sample = await self.process_daily_data_for_rl(day_data)
            training_dataset['daily_samples'].append(daily_sample)
        
        # 計算收集期間統計
        training_dataset['aggregated_statistics'] = self.calculate_collection_period_statistics(collected_data)
        
        # 分析換手模式
        training_dataset['handover_patterns'] = await self.analyze_handover_patterns(collected_data)
        
        return training_dataset
    
    async def cache_coordinate_analysis(self, coordinates: dict, analysis_result: dict) -> None:
        """緩存座標分析結果，支援座標參數化"""
        pass
```

**Phase 2 驗收標準：**
- [ ] 衛星可見性 API 正常運作
- [ ] **本地收集TLE數據載入系統** - 支援實際日期命名和雙格式讀取
- [ ] **數據覆蓋率檢查API** - 能正確回報收集狀態、日期範圍和雙格式覆蓋度
- [ ] 批次位置計算 API 測試通過
- [ ] **基於實際收集數據的最佳時間段分析API**
- [ ] **RL訓練數據集生成API** - 支援日期範圍過濾和雙格式元數據
- [ ] **雙星座(Starlink+OneWeb)完整支援** - 自動檢測可用日期範圍
- [ ] **Docker建置時預處理** - 自動掃描並處理所有收集的歷史數據
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
SimWorld Frontend → SimWorld Backend (skyfield) → 網路即時下載TLE → 直接計算
NetStack Backend → 獨立 skyfield 計算 → 網路即時下載TLE → 重複功能
```

#### 新流程 (重構後)
```
SimWorld Frontend → SimWorld Backend → NetStack API → 本地45天TLE數據 → 統一計算
RL研究需求 → NetStack API → 45天歷史數據集 → 訓練數據生成
手動數據收集 → 每日填入TLE檔案 → 建置時預處理 → 容器內嵌數據
```

### 📊 性能優化策略

#### 本地TLE數據優化
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
