# 🔧 衛星數據預處理流程 - 技術實現詳細說明

**版本**: 2.1.0  
**更新日期**: 2025-08-13  
**適用於**: 開發參考、程式實現、系統維護  

## 🗂️ 程式實現架構

### 主要處理器位置
```bash
# 核心控制器
/netstack/docker/satellite_orbit_preprocessor.py
├── SatelliteOrbitPreprocessor.process_all_tle_data()           # 主流程控制
├── SatelliteOrbitPreprocessor._execute_orbit_calculation() # 軌道計算執行
├── SatelliteOrbitPreprocessor._execute_signal_enhancement() # 信號增強執行
└── SatelliteOrbitPreprocessor._execute_intelligent_filtering() # 智能篩選執行

# 支援組件
/netstack/config/satellite_data_pool_builder.py             # 基礎篩選
/netstack/src/services/satellite/coordinate_specific_orbit_engine.py # SGP4引擎
/netstack/src/services/satellite/preprocessing/satellite_selector.py # 智能篩選
```

### 配置與腳本
```bash
# 系統配置
/netstack/config/satellite_config.py                        # 衛星系統配置
/netstack/docker/simple-entrypoint.sh                       # 簡化啟動腳本

# Cron 自動化
/scripts/daily_tle_download_enhanced.sh                     # TLE自動下載
/scripts/incremental_data_processor.sh                      # 增量處理
```

## 🔄 階段一：TLE數據載入與SGP4軌道計算

### 核心處理器位置
```bash
# 主要處理器實現
/netstack/src/stages/stage1_tle_processor.py
├── Stage1TLEProcessor.scan_tle_data()              # TLE檔案掃描
├── Stage1TLEProcessor.load_raw_satellite_data()    # 原始數據載入  
├── Stage1TLEProcessor.calculate_all_orbits()       # 完整SGP4計算
├── Stage1TLEProcessor.save_stage1_output()         # Debug模式控制輸出
└── Stage1TLEProcessor.process_stage1()             # 完整流程執行
```

### 核心處理邏輯
```python
# 階段一處理器主要流程 - v3.0 重新設計版本
class Stage1TLEProcessor:
    def __init__(self, sample_mode: bool = False, sample_size: int = 50):
        """初始化處理器 - v3.0版本
        Args:
            sample_mode: False=全量處理(8735顆), True=取樣模式(50顆/星座)
            sample_size: sample_mode=True時的取樣數量
        """
        self.sample_mode = sample_mode
        self.sample_size = sample_size
        
    def process_stage1(self) -> Dict[str, Any]:
        """完整階段一流程"""
        # 1. 掃描 TLE 數據檔案
        scan_result = self.scan_tle_data()
        
        # 2. 載入所有原始衛星數據 (無篩選)
        raw_data = self.load_raw_satellite_data(scan_result)
        
        # 3. 全量 SGP4 軌道計算
        stage1_data = self.calculate_all_orbits(raw_data)
        
        # 4. v3.0記憶體傳遞策略
        self.save_stage1_output(stage1_data)  # 清理舊檔案，不生成新檔案
        
        # 直接透過記憶體傳遞給階段二（無檔案I/O）
        return stage1_data
```

### 處理模式控制機制 (v3.0 重新設計版本)
```python
# v3.0版本：完全停用檔案儲存，採用記憶體傳遞策略
def save_stage1_output(self, stage1_data: Dict[str, Any]) -> Optional[str]:
    """v3.0版本：完全停用檔案儲存，採用純記憶體傳遞策略"""
    logger.info("🚀 v3.0記憶體傳遞策略：不產生任何JSON檔案")
    
    # 清理任何可能存在的舊檔案
    legacy_files = [
        self.output_dir / "stage1_tle_sgp4_output.json",
        self.output_dir / "stage1_tle_sgp4_output.tmp",
    ]
    
    for legacy_file in legacy_files:
        if legacy_file.exists():
            logger.info(f"🗑️ 清理舊檔案: {legacy_file}")
            legacy_file.unlink()
    
    logger.info("✅ v3.0策略：數據準備完成，將直接透過記憶體傳遞給階段二")
    return None  # 不返回檔案路徑，表示採用記憶體傳遞

# v3.0處理模式控制
def process_stage1(self) -> Dict[str, Any]:
    """執行完整的階段一處理流程 - v3.0版本"""
    logger.info("🚀 開始階段一：TLE數據載入與SGP4軌道計算 (v3.0)")
    
    # v3.0儲存策略：完全停用檔案儲存，純記憶體傳遞
    logger.info("🚀 v3.0記憶體傳遞模式：執行即時計算（不儲存檔案）")
    
    # 執行計算（支援取樣模式）
    stage1_data = self._execute_full_calculation()
    
    # 清理舊檔案但不生成新檔案
    self.save_stage1_output(stage1_data)
    
    processing_mode = "取樣模式" if self.sample_mode else "全量處理模式"
    logger.info(f"  🎯 處理模式: {processing_mode}")
    logger.info("  💾 v3.0記憶體傳遞：數據已準備好直接傳遞給階段二（零檔案儲存）")
    
    return stage1_data

# 取樣邏輯實現
def load_raw_satellite_data(self, scan_result) -> Dict[str, List[Dict]]:
    """載入原始衛星數據 - v3.0統一處理模式"""
    # ... TLE解析邏輯 ...
    
    if self.sample_mode:
        # 取樣模式：限制衛星數量
        satellites = satellites[:self.sample_size]
        logger.info(f"🔧 {constellation} 取樣模式: {original_count} → {len(satellites)} 顆衛星")
    else:
        # 全量處理模式：使用所有衛星
        logger.info(f"🚀 {constellation}: 全量載入 {len(satellites)} 顆衛星")
```

### v3.0處理模式說明
- **sample_mode=False** (預設): 全量處理模式，處理所有8,735顆衛星，適用於生產環境
- **sample_mode=True**: 取樣模式，每星座取樣50顆衛星，適用於快速開發測試
- **檔案策略**: 完全停用JSON檔案儲存，避免2.2GB檔案問題
- **記憶體傳遞**: 數據直接透過記憶體傳遞給階段二，無I/O延遲
- **驗證機制**: 階段二的處理結果就是最好的數據正確性驗證

### 支援組件位置
```python
# SGP4軌道計算引擎 (/netstack/src/services/satellite/sgp4_engine.py)
SGP4Engine.create_satellite()         # 從TLE創建衛星對象
SGP4Engine.calculate_position()       # 單點位置計算
SGP4Engine.calculate_trajectory()     # 軌跡時間序列計算

# 座標特定軌道引擎 (/netstack/src/services/satellite/coordinate_specific_orbit_engine.py)
CoordinateSpecificOrbitEngine.compute_96min_orbital_cycle()  # 96分鐘完整軌道週期
```

## 🎯 階段二：智能衛星篩選 (v3.0 記憶體傳遞版本)

### 核心處理器實現
```bash
# 統一智能篩選系統 - 階段二的核心實現
/netstack/src/services/satellite/intelligent_filtering/unified_intelligent_filter.py
├── UnifiedIntelligentFilter.process_stage2_filtering_only()    # 階段二專用篩選
├── UnifiedIntelligentFilter._extract_satellites_from_sgp4_data() # SGP4數據提取
├── UnifiedIntelligentFilter._enhance_with_signal_quality()      # 信號品質增強
├── UnifiedIntelligentFilter._enhance_with_event_analysis()      # 3GPP事件分析
├── UnifiedIntelligentFilter._build_stage2_output()             # 階段二輸出構建
└── UnifiedIntelligentFilter._extract_selected_orbit_data()     # 篩選數據提取

# 階段二處理器 - v3.0 記憶體傳遞版本
/netstack/src/stages/stage2_filter_processor.py
├── Stage2FilterProcessor.process_stage2()          # 階段二主流程 (支援記憶體傳遞)
├── Stage2FilterProcessor.load_stage1_output()      # 階段一數據載入 (檔案模式)
└── Stage2FilterProcessor.save_stage2_output()      # 階段二結果保存 (可選輸出)
```

### 統一智能篩選實現 (v3.0 實際驗證版)
```python
class UnifiedIntelligentFilter:
    """統一智能篩選系統 - 整合6階段篩選管道"""
    
    def __init__(self):
        """初始化統一篩選系統"""
        # 觀測點配置 (NTPU)
        self.observer_lat = 24.9442
        self.observer_lon = 121.3714
        
        # 載入篩選組件
        self.constellation_separator = ConstellationSeparator()
        self.geographic_filter = GeographicFilter(self.observer_lat, self.observer_lon)
        self.handover_scorer = HandoverSuitabilityScorer()
        self.rsrp_calculator = RSRPCalculator()
        self.event_analyzer = GPPEventAnalyzer()
    
    def process_stage2_filtering_only(self, sgp4_data: Dict[str, Any]) -> Dict[str, Any]:
        """階段二專用篩選流程 - 6階段智能篩選管道"""
        
        # 🔍 提取衛星數據 (8,735顆)
        all_satellites = self._extract_satellites_from_sgp4_data(sgp4_data)
        logger.info(f"📡 輸入衛星總數: {len(all_satellites)}")
        
        # 階段 2.1: 星座分離篩選
        separated_satellites = self.constellation_separator.separate_constellations(all_satellites)
        logger.info("⚙️ 執行階段 2.1: 星座分離篩選")
        
        # 階段 2.2: 地理相關性篩選 (關鍵篩選步驟)
        geographic_filtered = {}
        total_after_geo = 0
        for constellation, satellites in separated_satellites.items():
            filtered = self.geographic_filter.filter_by_geographic_relevance(satellites)
            geographic_filtered[constellation] = filtered
            total_after_geo += len(filtered)
        
        logger.info(f"🌍 執行階段 2.2: 地理相關性篩選")
        logger.info(f"✅ 地理篩選完成: {total_after_geo}/{len(all_satellites)} 顆衛星保留 "
                   f"(減少 {100*(1-total_after_geo/len(all_satellites)):.1f}%)")
        
        # 階段 2.3: 換手適用性評分
        scored_satellites = {}
        for constellation, satellites in geographic_filtered.items():
            scored = self.handover_scorer.score_handover_suitability(satellites, constellation)
            scored_satellites[constellation] = scored
        logger.info("📊 執行階段 2.3: 換手適用性評分")
        
        # 階段 2.4: 信號品質評估 (整合到篩選流程)
        enhanced_satellites = {}
        for constellation, satellites in scored_satellites.items():
            enhanced = self._enhance_with_signal_quality(satellites, constellation)
            enhanced_satellites[constellation] = enhanced
        logger.info("📡 執行階段 2.4: 信號品質評估")
        
        # 階段 2.5: 3GPP 事件分析
        analyzed_satellites = {}
        total_final = 0
        for constellation, satellites in enhanced_satellites.items():
            analyzed = self._enhance_with_event_analysis(satellites)
            analyzed_satellites[constellation] = analyzed
            total_final += len(analyzed)
        logger.info("🎯 執行階段 2.5: 3GPP 事件分析")
        
        # 階段 2.6: 頂級衛星選擇 (動態篩選模式)
        logger.info("🎯 執行動態篩選模式 - 保留所有通過篩選的衛星")
        final_selected = analyzed_satellites
        
        logger.info(f"✅ 最終選擇: {total_final} 顆頂級衛星")
        logger.info(f"🎉 階段二篩選完成: {len(all_satellites)} → {total_final} 顆衛星 "
                   f"(篩選率: {100*(1-total_final/len(all_satellites)):.1f}%)")
        
        # 構建階段二輸出
        processing_stats = {
            "input_satellites": len(all_satellites),
            "output_satellites": total_final,
            "filtering_rate": f"{100*(1-total_final/len(all_satellites)):.1f}%",
            "starlink_selected": len(final_selected.get("starlink", [])),
            "oneweb_selected": len(final_selected.get("oneweb", [])),
        }
        
        return self._build_stage2_output(sgp4_data, final_selected, processing_stats)
```

### 關鍵篩選組件實現

#### 地理相關性篩選器 (關鍵組件)
```python
class GeographicFilter:
    """地理相關性篩選器 - 階段2.2核心實現"""
    
    def filter_by_geographic_relevance(self, satellites: List[Dict]) -> List[Dict]:
        """基於NTPU觀測點的地理相關性篩選"""
        relevant_satellites = []
        
        for satellite in satellites:
            # 檢查軌道數據中的可見性
            has_positive_elevation = False
            for position in satellite.get("orbit_data", {}).get("positions", []):
                if position.get("elevation_deg", -999) > 5.0:  # 最低仰角門檻
                    has_positive_elevation = True
                    break
            
            if has_positive_elevation:
                relevant_satellites.append(satellite)
        
        return relevant_satellites
```

#### 數據提取修復實現 (關鍵修復)
```python
def _extract_selected_orbit_data(self, original_constellation: Dict, selected_sats: List[Dict]) -> Dict:
    """提取篩選後衛星的完整軌道數據 - 完全修復版本"""
    selected_orbit_data = {}
    original_satellites = original_constellation.get("orbit_data", {}).get("satellites", {})
    
    logger.info(f"🔧 強制修復版本: 開始提取篩選後的軌道數據")
    logger.info(f"   篩選後衛星數: {len(selected_sats)} 顆")
    logger.info(f"   原始衛星數據庫: {len(original_satellites)} 顆")
    
    # 🎯 修復：直接按 selected_sats 提取，忽略所有其他邏輯
    extracted_count = 0
    for selected_sat in selected_sats:
        satellite_id = selected_sat.get("satellite_id")
        if satellite_id and satellite_id in original_satellites:
            selected_orbit_data[satellite_id] = original_satellites[satellite_id]
            extracted_count += 1
    
    logger.info(f"✅ 修復版本完成: 提取了 {extracted_count} 顆衛星的軌道數據")
    
    # 🚨 最終驗證：如果提取的衛星數超過篩選數的2倍，強制只返回前N顆
    if len(selected_orbit_data) > len(selected_sats) * 2:
        logger.error(f"❌ 異常檢測: 提取了 {len(selected_orbit_data)} 顆，但只應該有 {len(selected_sats)} 顆")
        limited_data = {}
        for i, (sat_id, sat_data) in enumerate(selected_orbit_data.items()):
            if i >= len(selected_sats):
                break
            limited_data[sat_id] = sat_data
        logger.info(f"🛡️ 強制限制為 {len(limited_data)} 顆衛星")
        return limited_data
    
    return selected_orbit_data
```

### 記憶體傳遞模式處理器 (v3.0 新增功能)
```python
class Stage2FilterProcessor:
    """階段二：智能衛星篩選處理器 - v3.0 記憶體傳遞版本"""
    
    def process_stage2(self, stage1_file: Optional[str] = None, 
                      stage1_data: Optional[Dict[str, Any]] = None, 
                      save_output: bool = True) -> Dict[str, Any]:
        """執行完整的階段二處理流程 - 支援記憶體傳遞模式"""
        
        # 1. 優先使用記憶體數據（Zero File I/O 模式）
        if stage1_data is not None:
            logger.info("📥 使用提供的階段一內存數據")
            # 驗證內存數據格式
            if 'constellations' not in stage1_data:
                raise ValueError("階段一數據缺少 constellations 欄位")
            total_satellites = 0
            for constellation_name, constellation_data in stage1_data['constellations'].items():
                satellites = constellation_data.get('orbit_data', {}).get('satellites', {})
                total_satellites += len(satellites)
                logger.info(f"  {constellation_name}: {len(satellites)} 顆衛星")
            logger.info(f"✅ 階段一內存數據驗證完成: 總計 {total_satellites} 顆衛星")
        else:
            # 回退到檔案模式
            stage1_data = self.load_stage1_output(stage1_file)
        
        # 2. 執行智能篩選
        filtered_data = self.execute_intelligent_filtering(stage1_data)
        
        # 3. 可選的輸出策略 (支援記憶體傳遞模式)
        output_file = None
        if save_output:
            output_file = self.save_stage2_output(filtered_data)
            logger.info(f"💾 階段二數據已保存到: {output_file}")
        else:
            logger.info("🚀 階段二使用內存傳遞模式，未保存檔案")
        
        # 返回處理結果供階段三使用
        return filtered_data
```

### 實際執行結果驗證 (2025-08-14 記憶體傳遞驗證)
```python
# 階段二處理結果統計 - v3.0 記憶體傳遞版本
Stage2_實際結果 = {
    "輸入數據": {
        "總衛星數": 8735,
        "Starlink": 8086,
        "OneWeb": 651,
        "處理模式": "記憶體傳遞模式 (Zero File I/O)"
    },
    "篩選處理": {
        "星座分離": "8735/8735 顆保留",
        "地理篩選": "563/8735 顆保留 (減少93.6%)",
        "換手評分": "563 顆已評分",
        "信號品質": "563/563 通過",
        "事件分析": "563/563 事件能力"
    },
    "最終輸出": {
        "總衛星數": 563,
        "Starlink": 515,
        "OneWeb": 48,
        "處理模式": "記憶體傳遞 → Stage3",
        "篩選率": "93.6%",
        "記憶體優化": "避免 2.4GB 檔案問題"
    }
}
```

## 📡 階段三：信號品質分析與3GPP事件處理 (v3.0 完整實現版本)

### 核心處理器位置
```bash
# 階段三信號品質分析處理器 - v3.0 完整實現版本
/netstack/src/stages/stage3_signal_processor.py
├── Stage3SignalProcessor.calculate_signal_quality()      # 信號品質分析模組
├── Stage3SignalProcessor.analyze_3gpp_events()          # 3GPP事件分析模組
├── Stage3SignalProcessor.generate_final_recommendations() # 最終建議生成模組
├── Stage3SignalProcessor.save_stage3_output()           # v3.0 清理重生成模式
└── Stage3SignalProcessor.process_stage3()               # 完整流程 (支援記憶體傳遞)
```

### 信號品質分析實現 (calculate_signal_quality)
```python
class Stage3SignalProcessor:
    """階段三：純信號品質分析與3GPP事件處理器 - v3.0版本"""
    
    def __init__(self, observer_lat: float = 24.9441667, observer_lon: float = 121.3713889):
        self.observer_lat = observer_lat
        self.observer_lon = observer_lon
        
        # 初始化信號計算器
        self.rsrp_calculator = create_rsrp_calculator(observer_lat, observer_lon)
        self.event_analyzer = create_gpp_event_analyzer(self.rsrp_calculator)
    
    def calculate_signal_quality(self, stage2_data: Dict[str, Any]) -> Dict[str, Any]:
        """計算所有衛星的信號品質 - 多仰角RSRP分析"""
        
        enhanced_data = {
            'metadata': stage2_data.get('metadata', {}),
            'constellations': {}
        }
        
        # 更新metadata
        enhanced_data['metadata'].update({
            'stage3_processing': 'signal_quality_analysis',
            'stage3_timestamp': datetime.now(timezone.utc).isoformat(),
            'signal_calculation_standard': 'ITU-R_P.618_20GHz_Ka_band'
        })
        
        total_processed = 0
        
        for constellation_name, constellation_data in stage2_data['constellations'].items():
            # Handle both file-based and memory-based data structures
            satellites_list = []
            
            # 🔧 v3.0 數據結構兼容性處理
            if 'orbit_data' in constellation_data:
                orbit_data = constellation_data.get('orbit_data', {})
                satellites_data = orbit_data.get('satellites', {})
                
                if isinstance(satellites_data, dict):
                    # Convert dictionary to list of satellite objects
                    satellites_list = list(satellites_data.values())
                elif isinstance(satellites_data, list):
                    satellites_list = satellites_data
            elif 'satellites' in constellation_data:
                # File-based format: satellites is already a list
                satellites_data = constellation_data.get('satellites', [])
                if isinstance(satellites_data, list):
                    satellites_list = satellites_data
                elif isinstance(satellites_data, dict):
                    satellites_list = list(satellites_data.values())
            
            logger.info(f"   處理 {constellation_name}: {len(satellites_list)} 顆衛星")
            
            enhanced_satellites = []
            
            for i, satellite in enumerate(satellites_list):
                try:
                    # Ensure satellite is a dictionary, not a string or other type
                    if not isinstance(satellite, dict):
                        logger.warning(f"跳過無效衛星數據類型 {i}: {type(satellite)}")
                        continue
                        
                    enhanced_satellite = satellite.copy()
                    
                    # 📡 計算多個仰角下的RSRP (8個仰角度數)
                    rsrp_calculations = {}
                    rsrp_values = []
                    
                    for elevation_deg in [5, 10, 15, 30, 45, 60, 75, 90]:
                        rsrp = self.rsrp_calculator.calculate_rsrp(satellite, elevation_deg)
                        rsrp_calculations[f'elev_{elevation_deg}deg'] = round(rsrp, 2)
                        rsrp_values.append(rsrp)
                    
                    # 📊 計算信號統計信息
                    mean_rsrp = sum(rsrp_values) / len(rsrp_values)
                    max_rsrp = max(rsrp_values)
                    min_rsrp = min(rsrp_values)
                    rsrp_stability = max_rsrp - min_rsrp  # 越小越穩定
                    
                    # 添加信號品質數據
                    enhanced_satellite['signal_quality'] = {
                        'rsrp_by_elevation': rsrp_calculations,
                        'statistics': {
                            'mean_rsrp_dbm': round(mean_rsrp, 2),
                            'max_rsrp_dbm': round(max_rsrp, 2),
                            'min_rsrp_dbm': round(min_rsrp, 2),
                            'rsrp_stability_db': round(rsrp_stability, 2),
                            'signal_quality_grade': self._grade_signal_quality(mean_rsrp)
                        },
                        'calculation_standard': 'ITU-R_P.618_Ka_band_20GHz',
                        'observer_location': {
                            'latitude': self.observer_lat,
                            'longitude': self.observer_lon
                        }
                    }
                    
                    enhanced_satellites.append(enhanced_satellite)
                    total_processed += 1
                    
                except Exception as e:
                    # 🛡️ 錯誤處理機制：個別衛星失敗不影響整體處理
                    sat_id = satellite.get('satellite_id', 'Unknown') if isinstance(satellite, dict) else f'Invalid_{i}'
                    logger.warning(f"衛星 {sat_id} 信號計算失敗: {e}")
                    
                    # 保留原始衛星數據，但標記錯誤
                    if isinstance(satellite, dict):
                        satellite_copy = satellite.copy()
                        satellite_copy['signal_quality'] = {
                            'error': str(e),
                            'status': 'calculation_failed'
                        }
                        enhanced_satellites.append(satellite_copy)
            
            # 更新星座數據
            enhanced_constellation_data = constellation_data.copy()
            enhanced_constellation_data['satellites'] = enhanced_satellites
            enhanced_constellation_data['signal_analysis_completed'] = True
            enhanced_constellation_data['signal_processed_count'] = len(enhanced_satellites)
            
            enhanced_data['constellations'][constellation_name] = enhanced_constellation_data
            
            logger.info(f"  {constellation_name}: {len(enhanced_satellites)} 顆衛星信號分析完成")
        
        enhanced_data['metadata']['stage3_signal_processed_total'] = total_processed
        
        logger.info(f"✅ 信號品質分析完成: {total_processed} 顆衛星")
        return enhanced_data
```

### 3GPP事件分析實現 (analyze_3gpp_events)
```python
    def analyze_3gpp_events(self, signal_enhanced_data: Dict[str, Any]) -> Dict[str, Any]:
        """執行3GPP NTN事件分析 - A4/A5/D2事件處理"""
        logger.info("🎯 開始3GPP事件分析...")
        
        event_enhanced_data = {
            'metadata': signal_enhanced_data.get('metadata', {}),
            'constellations': {}
        }
        
        # 更新metadata
        event_enhanced_data['metadata'].update({
            'stage3_event_analysis': '3GPP_NTN_A4_A5_D2_events',
            'event_analysis_timestamp': datetime.now(timezone.utc).isoformat(),
            'supported_events': ['A4_intra_frequency', 'A5_intra_frequency', 'D2_beam_switch']
        })
        
        total_analyzed = 0
        
        for constellation_name, constellation_data in signal_enhanced_data['constellations'].items():
            satellites = constellation_data.get('satellites', [])
            
            if not satellites:
                logger.warning(f"跳過 {constellation_name}: 無可用衛星")
                continue
                
            logger.info(f"   處理 {constellation_name}: {len(satellites)} 顆衛星事件分析")
            
            try:
                # 使用現有的事件分析器進行批量分析
                event_results = self.event_analyzer.analyze_batch_events(satellites)
                
                if 'satellites_with_events' in event_results:
                    event_analyzed_satellites = event_results['satellites_with_events']
                    
                    # 更新星座數據
                    event_constellation_data = constellation_data.copy()
                    event_constellation_data['satellites'] = event_analyzed_satellites
                    event_constellation_data['event_analysis_completed'] = True
                    event_constellation_data['event_statistics'] = event_results.get('statistics', {})
                    
                    event_enhanced_data['constellations'][constellation_name] = event_constellation_data
                    
                    total_analyzed += len(event_analyzed_satellites)
                    logger.info(f"  {constellation_name}: {len(event_analyzed_satellites)} 顆衛星事件分析完成")
                    
                else:
                    logger.error(f"❌ {constellation_name} 事件分析結果格式錯誤")
                    # 保留原始數據
                    event_enhanced_data['constellations'][constellation_name] = constellation_data
                    
            except Exception as e:
                logger.error(f"❌ {constellation_name} 事件分析失敗: {e}")
                # 保留原始數據，但標記錯誤
                error_constellation_data = constellation_data.copy()
                error_constellation_data['event_analysis_error'] = str(e)
                event_enhanced_data['constellations'][constellation_name] = error_constellation_data
        
        event_enhanced_data['metadata']['stage3_event_analyzed_total'] = total_analyzed
        
        logger.info(f"✅ 3GPP事件分析完成: {total_analyzed} 顆衛星")
        return event_enhanced_data
```

### 最終建議生成實現 (generate_final_recommendations)
```python
    def generate_final_recommendations(self, event_enhanced_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成最終的衛星選擇建議 - 綜合評分排名系統"""
        logger.info("🏆 生成最終衛星選擇建議...")
        
        final_data = {
            'metadata': event_enhanced_data.get('metadata', {}),
            'constellations': {},
            'selection_recommendations': {}
        }
        
        # 更新metadata
        final_data['metadata'].update({
            'stage3_completion': 'signal_and_event_analysis_complete',
            'final_processing_timestamp': datetime.now(timezone.utc).isoformat(),
            'processing_pipeline_complete': [
                'stage1_tle_sgp4_calculation',
                'stage2_intelligent_filtering',
                'stage3_signal_event_analysis'
            ],
            'ready_for_handover_simulation': True
        })
        
        total_recommended = 0
        
        for constellation_name, constellation_data in event_enhanced_data['constellations'].items():
            satellites = constellation_data.get('satellites', [])
            
            if not satellites:
                continue
                
            # 對衛星進行綜合評分排序
            scored_satellites = []
            
            for satellite in satellites:
                score = self._calculate_composite_score(satellite)
                satellite_with_score = satellite.copy()
                satellite_with_score['composite_score'] = score
                scored_satellites.append(satellite_with_score)
            
            # 按分數排序
            scored_satellites.sort(key=lambda x: x.get('composite_score', 0), reverse=True)
            
            # 更新星座數據
            final_constellation_data = constellation_data.copy()
            final_constellation_data['satellites'] = scored_satellites
            final_constellation_data['satellites_ranked'] = True
            final_constellation_data['top_satellite_score'] = scored_satellites[0].get('composite_score', 0) if scored_satellites else 0
            
            final_data['constellations'][constellation_name] = final_constellation_data
            
            # 🏆 生成選擇建議 (前5顆衛星推薦)
            top_satellites = scored_satellites[:5]
            final_data['selection_recommendations'][constellation_name] = {
                'top_5_satellites': [
                    {
                        'satellite_id': sat.get('satellite_id', 'Unknown'),
                        'composite_score': sat.get('composite_score', 0),
                        'signal_grade': sat.get('signal_quality', {}).get('statistics', {}).get('signal_quality_grade', 'Unknown'),
                        'event_potential': sat.get('event_potential', {}).get('composite', 0),
                        'handover_suitability': sat.get('handover_score', {}).get('overall_score', 0)
                    }
                    for sat in top_satellites
                ],
                'constellation_quality': self._assess_constellation_quality(scored_satellites),
                'recommended_for_handover': len([s for s in top_satellites if s.get('composite_score', 0) > 0.6])
            }
            
            total_recommended += len(scored_satellites)
            
            logger.info(f"  {constellation_name}: {len(scored_satellites)} 顆衛星完成最終評分")
        
        final_data['metadata']['stage3_final_recommended_total'] = total_recommended
        
        logger.info(f"✅ 最終建議生成完成: {total_recommended} 顆衛星完成綜合評分")
        return final_data
```

### 綜合評分算法實現
```python
    def _calculate_composite_score(self, satellite: Dict[str, Any]) -> float:
        """計算衛星的綜合評分 - 多維度加權評分系統"""
        score = 0.0
        weights = {
            'signal_quality': 0.4,    # 信號品質 40%
            'event_potential': 0.3,   # 事件潛力 30%
            'handover_score': 0.2,    # 換手評分 20%
            'geographic_score': 0.1   # 地理評分 10%
        }
        
        # 📡 信號品質評分 (0-1)
        signal_quality = satellite.get('signal_quality', {}).get('statistics', {})
        mean_rsrp = signal_quality.get('mean_rsrp_dbm', -150)
        signal_score = max(0, min(1, (mean_rsrp + 120) / 40))  # -120到-80的範圍映射到0-1
        score += signal_score * weights['signal_quality']
        
        # 🎯 事件潛力評分 (0-1)
        event_potential = satellite.get('event_potential', {}).get('composite', 0)
        score += event_potential * weights['event_potential']
        
        # 🔄 換手評分 (0-1)
        handover_score = satellite.get('handover_score', {}).get('overall_score', 0)
        normalized_handover = handover_score / 100.0  # 假設原始評分是0-100
        score += normalized_handover * weights['handover_score']
        
        # 🌍 地理評分 (0-1)
        geographic_score = satellite.get('geographic_score', {}).get('overall_score', 0)
        normalized_geographic = geographic_score / 100.0  # 假設原始評分是0-100
        score += normalized_geographic * weights['geographic_score']
        
        return round(score, 3)
    
    def _grade_signal_quality(self, mean_rsrp_dbm: float) -> str:
        """根據RSRP值評定信號品質等級 - ITU-R P.618標準"""
        if mean_rsrp_dbm >= -80:
            return "Excellent"
        elif mean_rsrp_dbm >= -90:
            return "Good"
        elif mean_rsrp_dbm >= -100:
            return "Fair"
        elif mean_rsrp_dbm >= -110:
            return "Poor"
        else:
            return "Very_Poor"
    
    def _assess_constellation_quality(self, satellites: List[Dict[str, Any]]) -> str:
        """評估星座整體品質"""
        if not satellites:
            return "No_Data"
            
        scores = [s.get('composite_score', 0) for s in satellites]
        avg_score = sum(scores) / len(scores)
        
        if avg_score >= 0.8:
            return "Excellent"
        elif avg_score >= 0.6:
            return "Good"
        elif avg_score >= 0.4:
            return "Fair"
        elif avg_score >= 0.2:
            return "Poor"
        else:
            return "Very_Poor"
```

### v3.0 記憶體傳遞處理器
```python
    def process_stage3(self, stage2_file: Optional[str] = None, stage2_data: Optional[Dict[str, Any]] = None,
                      save_output: bool = True) -> Dict[str, Any]:
        """執行完整的階段三處理流程 - v3.0 記憶體傳遞支援"""
        logger.info("🚀 開始階段三：信號品質分析與3GPP事件處理")
        
        # 1. 載入階段二數據（優先使用內存數據）
        if stage2_data is not None:
            logger.info("📥 使用提供的階段二內存數據")
            # 驗證內存數據格式
            if 'constellations' not in stage2_data:
                raise ValueError("階段二數據缺少 constellations 欄位")
            total_satellites = 0
            for constellation_name, constellation_data in stage2_data['constellations'].items():
                # Handle both file-based and memory-based data structures
                if 'satellites' in constellation_data:
                    satellites = constellation_data.get('satellites', [])
                elif 'orbit_data' in constellation_data:
                    satellites = constellation_data.get('orbit_data', {}).get('satellites', [])
                else:
                    satellites = []
                total_satellites += len(satellites)
                logger.info(f"  {constellation_name}: {len(satellites)} 顆衛星")
            logger.info(f"✅ 階段二內存數據驗證完成: 總計 {total_satellites} 顆衛星")
        else:
            stage2_data = self.load_stage2_output(stage2_file)
        
        # 2. 📡 信號品質分析
        signal_enhanced_data = self.calculate_signal_quality(stage2_data)
        
        # 3. 🎯 3GPP事件分析
        event_enhanced_data = self.analyze_3gpp_events(signal_enhanced_data)
        
        # 4. 🏆 生成最終建議
        final_data = self.generate_final_recommendations(event_enhanced_data)
        
        # 5. 可選的輸出策略 (支援記憶體傳遞模式)
        output_file = None
        if save_output:
            output_file = self.save_stage3_output(final_data)
            logger.info(f"📁 階段三數據已保存到: {output_file}")
        else:
            logger.info("🚀 階段三使用內存傳遞模式，未保存檔案")
        
        logger.info("✅ 階段三處理完成")
        logger.info(f"  分析的衛星數: {final_data['metadata'].get('stage3_final_recommended_total', 0)}")
        if output_file:
            logger.info(f"  輸出檔案: {output_file}")
        
        return final_data
```

### 實際處理結果驗證 (2025-08-14 記憶體傳遞驗證)
```python
# 階段三處理結果統計 - v3.0 記憶體傳遞版本
Stage3_實際結果 = {
    "輸入數據": {
        "總衛星數": 575,
        "Starlink": 527,
        "OneWeb": 48,
        "處理模式": "記憶體傳遞模式 + 可選檔案輸出"
    },
    "信號品質分析": {
        "RSRP計算": "8個仰角度數 (5°-90°) 完整覆蓋",
        "信號統計": "平均值、最大值、最小值、穩定性",
        "品質分級": "Excellent → Very_Poor 5級分類",
        "計算標準": "ITU-R P.618 Ka-band 20GHz"
    },
    "3GPP事件分析": {
        "A4事件": "Intra-frequency 換手觸發事件",
        "A5事件": "Serving cell and neighbour cell 門檻事件",
        "D2事件": "波束切換事件分析",
        "批量處理": "575顆衛星完整事件分析"
    },
    "最終建議生成": {
        "綜合評分": "信號40% + 事件30% + 換手20% + 地理10%",
        "衛星排名": "按綜合評分降序排列",
        "星座品質": "Excellent → Very_Poor 星座評估",
        "推薦清單": "每星座前5顆衛星詳細推薦"
    },
    "輸出特性": {
        "記憶體模式": "save_output=False 零檔案處理",
        "檔案模式": "save_output=True 生成 ~295MB 檔案",
        "數據完整性": "完整保留所有處理階段數據",
        "向後兼容": "支援檔案模式和記憶體模式"
    }
}
```

## 📂 數據結構與格式

### TLE 數據來源結構
```bash
/netstack/tle_data/
├── starlink/
│   ├── tle/
│   │   └── starlink_20250809.tle      # 8,064 顆衛星
│   └── json/
│       └── starlink.json
└── oneweb/
    ├── tle/
    │   └── oneweb_20250809.tle        # 651 顆衛星
    └── json/
        └── oneweb.json
```

### 輸出數據格式

#### 階段一輸出（軌道數據）
```python
# stage1_tle_sgp4_output.json (Debug Mode = True)
{
    "metadata": {
        "version": "1.0.0-stage1-only",
        "created_at": "2025-08-13T08:25:00Z",
        "processing_stage": "stage1_tle_sgp4",
        "observer_coordinates": {
            "latitude": 24.9441667,
            "longitude": 121.3713889,
            "altitude_m": 50.0
        },
        "total_satellites": 8715,
        "total_constellations": 2
    },
    "constellations": {
        "starlink": {
            "satellite_count": 8064,
            "orbit_data": {
                "satellites": {
                    "starlink_00001": {
                        "satellite_id": "starlink_00001",
                        "name": "STARLINK-1007",
                        "constellation": "starlink",
                        "tle_data": {
                            "line1": "1 44235U 19029A   ...",
                            "line2": "2 44235  53.0538 ..."
                        },
                        "orbit_data": {
                            "orbital_period_minutes": 96.0,
                            "positions": [
                                {
                                    "timestamp": "2025-08-13T08:00:00Z",
                                    "position": {"x": 1234.567, "y": -5678.901, "z": 3456.789},
                                    "velocity": {"vx": 7.123, "vy": -2.456, "vz": 1.789},
                                    "elevation_deg": 45.7,
                                    "azimuth_deg": 152.3,
                                    "distance_km": 589.2
                                }
                                // ... 192 個時間點 (30秒間隔)
                            ]
                        }
                    }
                    // ... 8064 顆 Starlink 衛星
                }
            }
        },
        "oneweb": {
            // ... 651 顆 OneWeb 衛星，結構相同
        }
    }
}

# v3.0記憶體傳遞模式: 不生成檔案，數據直接透過記憶體傳遞給階段二
# 這解決了2.2GB檔案問題，並提供更好的數據驗證機制
```

#### 階段二輸出（智能篩選結果 - v3.0 記憶體傳遞版本）
```python
# stage2_intelligent_filtered_output.json (v3.0 記憶體傳遞版本)
{
    "metadata": {
        "version": "3.0.0-stage2-memory-passing",
        "created_at": "2025-08-14T10:30:00Z", 
        "processing_stage": "stage2_intelligent_filtering",
        "processing_mode": "memory_passing_mode",
        "unified_filtering_results": {
            "total_selected": 563,
            "starlink_selected": 515,
            "oneweb_selected": 48,
            "filtering_rate": "93.6%"
        },
        "stage2_completion": "intelligent_filtering_complete",
        "ready_for_stage3": true,
        "file_generation": "memory_passing_or_optional_save"
    },
    "constellations": {
        "starlink": {
            "satellite_count": 515,
            "filtering_completed": true,
            "satellites": [
                {
                    "satellite_id": "STARLINK-1007",
                    "constellation": "starlink",
                    "orbit_data": {
                        "positions": [
                            {
                                "timestamp": "2025-08-14T10:00:00Z",
                                "position": {"x": 1234.5, "y": -5678.9, "z": 3456.7},
                                "velocity": {"vx": 7.12, "vy": -2.45, "vz": 1.78},
                                "elevation_deg": 45.7,
                                "azimuth_deg": 152.3,
                                "distance_km": 589.2
                            }
                            // ... 192 個時間點
                        ]
                    },
                    "geographic_score": {
                        "overall_score": 85.3,
                        "visibility_quality": "excellent",
                        "handover_potential": "high"
                    },
                    "handover_score": {
                        "overall_score": 78.5,
                        "constellation_specific_score": 82.1,
                        "suitable_for_handover": true
                    }
                }
                // ... 515 顆 Starlink 篩選後衛星
            ]
        },
        "oneweb": {
            // ... 48 顆 OneWeb 篩選後衛星，結構相同
        }
    }
}

# v3.0 記憶體傳遞模式特點:
# 1. 可選檔案儲存 (save_output=False 時不生成檔案)
# 2. 數據直接透過記憶體傳遞給階段三
# 3. 避免 2.4GB 檔案問題
# 4. 提供更快的處理速度和更好的資源效率
```

## 📁 存儲架構實現

### PostgreSQL 數據庫存儲
```sql
-- 結構化數據和快速查詢優化
衛星基礎資訊存儲:
├── satellite_metadata (衛星ID, 星座, 軌道參數摘要)
├── orbital_parameters (傾角, 高度, 週期, NORAD ID)
├── handover_suitability_scores (篩選評分記錄)
└── constellation_statistics (星座級別統計數據)

3GPP事件記錄存儲:
├── a4_events_log (觸發時間, 衛星ID, RSRP值, 門檻參數)
├── a5_events_log (雙門檻事件, 服務衛星狀態, 鄰居衛星狀態)
├── d2_events_log (距離事件, UE位置, 衛星距離)
└── handover_decisions_log (換手決策記錄, 成功率統計)
```

### Docker Volume 文件存儲結構
```bash
/app/data/
├── enhanced_phase0_precomputed_orbits.json    # 包含3GPP事件的主數據文件
├── enhanced_timeseries/                       # 增強時間序列目錄
│   ├── starlink_enhanced_555sats.json        # ~50-60MB
│   └── oneweb_enhanced_134sats.json          # ~35-40MB
├── layered_phase0_enhanced/                   # 分層仰角+3GPP事件數據
│   ├── elevation_5deg/
│   ├── elevation_10deg/
│   └── elevation_15deg/
├── handover_scenarios/                        # 換手場景專用數據
├── signal_quality_analysis/                  # 信號品質分析數據
├── processing_cache/                          # 處理緩存優化
└── status_files/                              # 系統狀態追蹤
```

## 🕒 Pure Cron 驅動機制

### Cron 調度配置
```bash
# TLE 自動下載 (每6小時)
0 2,8,14,20 * * * /home/sat/ntn-stack/scripts/daily_tle_download_enhanced.sh

# 智能增量處理 (下載後30分鐘)
30 2,8,14,20 * * * /home/sat/ntn-stack/scripts/incremental_data_processor.sh

# 安全數據清理 (每日03:15)
15 3 * * * /home/sat/ntn-stack/scripts/safe_data_cleanup.sh
```

### 增量處理邏輯
```python
Cron_調度流程 = {
    "TLE 下載": "每6小時自動下載最新 TLE 數據 (02:00, 08:00, 14:00, 20:00)",
    "增量處理": "下載後30分鐘進行智能增量分析 (02:30, 08:30, 14:30, 20:30)", 
    "變更檢測": "比較 TLE 數據與預計算數據的衛星清單差異",
    "按需重算": "僅當檢測到新衛星或顯著變更時才重新計算",
    "安全清理": "每日03:15清理臨時文件，保護原始TLE數據"
}
```

## 🔄 檔案生成規則與清理機制 (v3.0 統一實現)

### 📋 檔案生成規則總覽

**核心原則**: 所有階段的輸出檔案都遵循「先刪除舊檔，再生成新檔」的清理機制，確保資料一致性和避免累積殘留檔案。

#### 🗂️ 各階段檔案處理策略

```python
# 統一的檔案清理和生成流程
檔案生成規則 = {
    "階段一 (Stage1)": {
        "策略": "v3.0記憶體傳遞模式",
        "檔案處理": "清理舊檔案，不生成新檔案", 
        "優勢": "避免2.2GB檔案問題，零I/O延遲",
        "清理目標": ["stage1_tle_sgp4_output.json", "stage1_tle_sgp4_output.tmp"]
    },
    
    "階段二 (Stage2)": {
        "策略": "v3.0 記憶體傳遞模式",
        "檔案處理": "可選檔案儲存 (save_output 參數控制)",
        "優勢": "避免 2.4GB 檔案問題，Zero File I/O 處理", 
        "清理目標": ["stage2_intelligent_filtered_output.json (可選)"],
        "生成檔案": "記憶體傳遞模式 或 141MB (563顆衛星)"
    },
    
    "階段三 (Stage3)": {
        "策略": "清理重生成模式", 
        "檔案處理": "刪除舊檔案 → 生成新檔案",
        "優勢": "信號品質和事件分析資料清潔",
        "清理目標": ["stage3_signal_event_analysis_output.json"],
        "生成檔案": "增強型衛星數據 (含3GPP事件)"
    }
}
```

#### 🔧 檔案清理實現細節

**階段一清理邏輯** (記憶體傳遞模式):
```python
def save_stage1_output(self, stage1_data: Dict[str, Any]) -> Optional[str]:
    """v3.0版本：完全停用檔案儲存，採用純記憶體傳遞策略"""
    logger.info("🚀 v3.0記憶體傳遞策略：不產生任何JSON檔案")
    
    # 🗑️ 清理任何可能存在的舊檔案
    legacy_files = [
        self.output_dir / "stage1_tle_sgp4_output.json",
        self.output_dir / "stage1_tle_sgp4_output.tmp",
    ]
    
    for legacy_file in legacy_files:
        if legacy_file.exists():
            logger.info(f"🗑️ 清理舊檔案: {legacy_file}")
            legacy_file.unlink()
    
    return None  # 不返回檔案路徑，表示採用記憶體傳遞
```

**階段二記憶體傳遞邏輯** (v3.0 記憶體傳遞模式):
```python
def process_stage2(self, stage1_file: Optional[str] = None, 
                  stage1_data: Optional[Dict[str, Any]] = None, 
                  save_output: bool = True) -> Dict[str, Any]:
    """執行完整的階段二處理流程 - v3.0 記憶體傳遞版本"""
    logger.info("🚀 開始階段二：智能衛星篩選")
    
    # 1. 載入階段一數據（優先使用內存數據）
    if stage1_data is not None:
        logger.info("📥 使用提供的階段一內存數據")
        # 驗證內存數據格式
        if 'constellations' not in stage1_data:
            raise ValueError("階段一數據缺少 constellations 欄位")
        total_satellites = 0
        for constellation_name, constellation_data in stage1_data['constellations'].items():
            satellites = constellation_data.get('orbit_data', {}).get('satellites', {})
            total_satellites += len(satellites)
            logger.info(f"  {constellation_name}: {len(satellites)} 顆衛星")
        logger.info(f"✅ 階段一內存數據驗證完成: 總計 {total_satellites} 顆衛星")
    else:
        stage1_data = self.load_stage1_output(stage1_file)
    
    # 2. 執行智能篩選
    filtered_data = self.execute_intelligent_filtering(stage1_data)
    
    # 3. 可選的輸出策略 (支援記憶體傳遞模式)
    output_file = None
    if save_output:
        output_file = self.save_stage2_output(filtered_data)
        logger.info(f"💾 階段二數據已保存到: {output_file}")
    else:
        logger.info("🚀 階段二使用內存傳遞模式，未保存檔案")
    
    logger.info("✅ 階段二處理完成")
    # 獲取篩選結果統計
    total_selected = filtered_data['metadata'].get('unified_filtering_results', {}).get('total_selected', 0)
    starlink_selected = filtered_data['metadata'].get('unified_filtering_results', {}).get('starlink_selected', 0)
    oneweb_selected = filtered_data['metadata'].get('unified_filtering_results', {}).get('oneweb_selected', 0)
    
    logger.info(f"  篩選的衛星數: {total_selected} (Starlink: {starlink_selected}, OneWeb: {oneweb_selected})")
    if output_file:
        logger.info(f"  輸出檔案: {output_file}")
    
    return filtered_data

def save_stage2_output(self, filtered_data: Dict[str, Any]) -> str:
    """保存階段二輸出數據 - v3.0 清理舊檔案版本 (可選執行)"""
    output_file = self.output_dir / "stage2_intelligent_filtered_output.json"
    
    # 🗑️ 清理舊檔案 - 確保資料一致性
    if output_file.exists():
        file_size = output_file.stat().st_size
        logger.info(f"🗑️ 清理舊階段二輸出檔案: {output_file}")
        logger.info(f"   舊檔案大小: {file_size / (1024*1024):.1f} MB")
        output_file.unlink()
        logger.info("✅ 舊檔案已刪除")
    
    # 添加階段二完成標記
    filtered_data['metadata'].update({
        'stage2_completion': 'intelligent_filtering_complete',
        'stage2_timestamp': datetime.now(timezone.utc).isoformat(),
        'ready_for_stage3': True,
        'file_generation': 'memory_passing_or_optional_save'  # v3.0 標記
    })
    
    # 💾 生成新的階段二輸出檔案
    logger.info(f"💾 生成新的階段二輸出檔案: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(filtered_data, f, indent=2, ensure_ascii=False)
        
    # 檢查新檔案大小和內容
    new_file_size = output_file.stat().st_size
    logger.info(f"✅ 階段二數據已保存: {output_file}")
    logger.info(f"   新檔案大小: {new_file_size / (1024*1024):.1f} MB")
    logger.info(f"   包含衛星數: {filtered_data['metadata'].get('unified_filtering_results', {}).get('total_selected', 'unknown')}")
    
    return str(output_file)
```

**階段三清理邏輯** (清理重生成模式):
```python
def save_stage3_output(self, final_data: Dict[str, Any]) -> str:
    """保存階段三輸出數據 - v3.0 清理舊檔案版本"""
    output_file = self.output_dir / "stage3_signal_event_analysis_output.json"
    
    # 🗑️ 清理舊檔案 - 確保資料一致性
    if output_file.exists():
        file_size = output_file.stat().st_size
        logger.info(f"🗑️ 清理舊階段三輸出檔案: {output_file}")
        logger.info(f"   舊檔案大小: {file_size / (1024*1024):.1f} MB")
        output_file.unlink()
        logger.info("✅ 舊檔案已刪除")
    
    # 添加階段三完成標記
    final_data['metadata'].update({
        'stage3_completion': 'signal_event_analysis_complete',
        'stage3_timestamp': datetime.now(timezone.utc).isoformat(),
        'ready_for_stage4': True,
        'file_generation': 'clean_regeneration'  # 標記為重新生成
    })
    
    # 💾 生成新的階段三輸出檔案
    logger.info(f"💾 生成新的階段三輸出檔案: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, indent=2, ensure_ascii=False)
        
    # 檢查新檔案大小和內容
    new_file_size = output_file.stat().st_size
    logger.info(f"✅ 階段三數據已保存: {output_file}")
    logger.info(f"   新檔案大小: {new_file_size / (1024*1024):.1f} MB")
    logger.info(f"   包含衛星數: {final_data['metadata'].get('unified_filtering_results', {}).get('total_selected', 'unknown')}")
    
    return str(output_file)
```

#### 🎯 v3.0 記憶體傳遞機制優勢

**1. 避免檔案大小問題**
- 階段一：避免 2.2GB 檔案問題（完全記憶體傳遞）
- 階段二：避免 2.4GB 擴展問題（可選記憶體傳遞）
- 資源效率：大幅減少 I/O 操作和磁碟使用

**2. 處理性能提升**
- Zero File I/O：消除檔案讀寫延遲
- 記憶體傳遞：直接數據結構傳遞，無序列化開銷
- 實時驗證：階段間數據即時驗證，發現問題更快

**3. 系統架構優化**
- 彈性輸出：save_output 參數控制是否生成檔案
- 混合模式：支援記憶體傳遞和檔案保存並存
- 向後兼容：保持對檔案模式的完整支援

**4. 資料一致性保證**
- 消除舊檔案和新檔案混淆的風險
- 確保每次處理都是從零開始的清潔狀態
- 避免部分更新導致的資料不一致

**5. 故障排除友善**
- 清楚記錄記憶體傳遞和檔案生成過程
- 提供處理統計，便於驗證處理效果
- 處理模式標記便於追蹤系統狀態

#### 🔍 記憶體傳遞模式驗證

**檢查記憶體傳遞處理效果**:
```bash
# 檢查各階段輸出檔案狀態（記憶體傳遞模式可能不生成檔案）
ls -la /app/data/stage*_output.json

# 檢查是否使用記憶體傳遞模式（查看處理日誌）
docker logs netstack-api | grep -E "(記憶體傳遞|內存傳遞|memory.*pass)" | tail -10

# 檢查處理統計（在記憶體中的數據驗證）
docker logs netstack-api | grep -E "篩選的衛星數|階段.*完成" | tail -10

# 如果生成了檔案，檢查檔案大小和內容
if [ -f /app/data/stage2_intelligent_filtered_output.json ]; then
    du -h /app/data/stage2_intelligent_filtered_output.json  # 應該約141MB (563顆衛星)
    jq '.metadata.unified_filtering_results.total_selected' /app/data/stage2_intelligent_filtered_output.json
fi
```

**記憶體傳遞日誌追蹤**:
```bash
# 查看記憶體傳遞和處理日誌
docker logs netstack-api | grep -E "(使用內存數據|記憶體傳遞模式|memory.*mode)" | tail -10

# 檢查處理模式標記
if [ -f /app/data/stage2_intelligent_filtered_output.json ]; then
    jq '.metadata.file_generation' /app/data/stage2_intelligent_filtered_output.json  
    # 應該顯示 "memory_passing_or_optional_save"
fi

# 檢查三階段記憶體傳遞管道的執行情況
docker logs netstack-api | grep -E "階段.*處理完成|衛星數.*→" | tail -15
```

**v3.0 記憶體傳遞模式測試**:
```bash
# 執行完整的三階段記憶體傳遞管道測試
docker exec netstack-api python -c "
from src.stages.stage1_tle_processor import Stage1TLEProcessor
from src.stages.stage2_filter_processor import Stage2FilterProcessor  
from src.stages.stage3_signal_processor import Stage3SignalProcessor

# 建立處理器
stage1 = Stage1TLEProcessor(sample_mode=False)  # 全量模式
stage2 = Stage2FilterProcessor()
stage3 = Stage3SignalProcessor()

# 執行記憶體傳遞管道
print('🚀 執行階段一...')
stage1_data = stage1.process_stage1()

print('🚀 執行階段二（記憶體傳遞）...')
stage2_data = stage2.process_stage2(stage1_data=stage1_data, save_output=False)

print('🚀 執行階段三（記憶體傳遞）...')
stage3_data = stage3.process_stage3(stage2_data=stage2_data, save_output=False)

print('✅ 三階段記憶體傳遞管道完成！')
print(f'最終處理衛星數：{stage3_data[\"metadata\"].get(\"stage3_final_recommended_total\", 0)}')
"
```

## 🛠️ 維護與故障排除

### 日常檢查指令
```bash
# 1. 檢查系統整體狀態
make status

# 2. 檢查 Cron 調度狀態
make status-cron

# 3. 檢查衛星數據狀態
curl -s http://localhost:8080/api/v1/satellites/unified/status | jq

# 4. 檢查數據文件完整性
docker exec netstack-api ls -la /app/data/

# 5. 檢查各階段處理日誌
docker logs netstack-api | grep -E "階段" | tail -20
```

### Pure Cron 故障排除
```bash
# 檢查 Cron 任務是否正常安裝
crontab -l | grep -E "(tle_download|incremental)"

# 檢查 Cron 執行日誌
tail -20 /tmp/tle_download.log
tail -20 /tmp/incremental_update.log

# 重新安裝 Cron 任務（修復調度問題）
make install-cron

# 手動測試下載器
./scripts/daily_tle_download_enhanced.sh

# 手動測試增量處理器
./scripts/incremental_data_processor.sh

# 強制重新計算（終極解決方案）
make update-satellite-data
```

### 常見問題解決

#### 1. TLE 數據問題
```bash
# 問題：TLE 數據過期或損壞
# 解決：檢查下載狀態和格式
grep -c "^1 " /netstack/tle_data/starlink/tle/starlink.tle  # 應該 > 8000
file /netstack/tle_data/starlink/tle/starlink.tle          # 應該是 ASCII text
```

#### 2. SGP4 計算錯誤
```bash
# 問題：軌道計算失敗
# 解決：檢查TLE格式和算法狀態
docker logs netstack-api | grep -i "sgp4\|orbit" | tail -10
curl -s http://localhost:8080/api/v1/satellites/health | jq .sgp4_status
```

#### 3. 記憶體使用過高
```bash
# 問題：處理大量衛星數據時記憶體不足
# 解決：檢查處理批次和緩存策略
docker stats netstack-api --no-stream
docker exec netstack-api cat /app/data/.processing_stats
```

## 📊 性能監控

### 關鍵性能指標 (KPI)
```bash
# API 響應時間監控
curl -w "@curl-format.txt" -s -o /dev/null http://localhost:8080/api/v1/satellites/positions

# 處理時間統計
docker exec netstack-api cat /app/data/.build_timestamp
docker exec netstack-api cat /app/data/.processing_stats

# 系統資源使用
docker stats --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"
```

### 預期性能基準
- **建構時間**: 2-5 分鐘（首次完整計算）
- **啟動時間**: < 30秒（Pure Cron 穩定保證）
- **API 響應**: < 100ms（衛星位置查詢）
- **記憶體使用**: < 2GB（完整處理期間）
- **存儲需求**: ~450-500MB（Volume + PostgreSQL）

---

**本文檔提供完整的技術實現參考，涵蓋所有開發和維護所需的詳細信息。**