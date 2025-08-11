# 🔧 衛星數據預處理流程 - 技術實現詳細說明

**版本**: 1.0.0  
**更新日期**: 2025-08-11  
**適用於**: 開發參考、程式實現、系統維護  

## 🗂️ 程式實現架構

### 主要處理器位置
```bash
# 核心控制器
/netstack/docker/build_with_phase0_data_refactored.py
├── Phase25DataPreprocessor.process_all_tle_data()           # 主流程控制
├── Phase25DataPreprocessor._execute_phase1_orbit_calculation() # 階段一執行
├── Phase25DataPreprocessor._execute_phase2_signal_enhancement() # 階段二執行
└── Phase25DataPreprocessor._execute_phase3_intelligent_filtering() # 階段三執行

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

### 核心處理邏輯
```python
# 實際程式邏輯 (build_with_phase0_data_refactored.py:349-400)
def load_tle_satellites(constellation, date_str):
    """載入指定星座的全部 TLE 數據"""
    # 1. 讀取完整 TLE 文件
    # 2. 逐一解析每個 TLE 記錄 (3行為一組)
    # 3. 驗證 TLE 格式正確性
    # 4. 提取 NORAD ID、軌道參數
    # 5. 返回所有有效衛星記錄
    
    # 關鍵：沒有任何篩選邏輯！
    # 目的：確保不遺漏任何可能經過觀測點的衛星
```

### 子組件詳細位置
```python
# TLE掃描器 (/netstack/docker/build_with_phase0_data_refactored.py:258-336)
Phase25DataPreprocessor.scan_tle_data()

# 數據載入器 (/netstack/docker/build_with_phase0_data_refactored.py:238-256)
Phase25DataPreprocessor._load_constellation_satellites()

# 衛星池建構器 (/netstack/config/satellite_data_pool_builder.py)
SatelliteDataPoolBuilder.build_satellite_pools()

# SGP4軌道計算引擎 (/netstack/src/services/satellite/coordinate_specific_orbit_engine.py)
CoordinateSpecificOrbitEngine.calculate_satellite_orbit()
```

## 🔧 階段二：3GPP Events & 信號品質計算

### 星座特定信號模型實現

#### Starlink 信號處理
```python
# Starlink 特定參數
constellation_config = {
    "frequency_ghz": 12.0,        # Ku 頻段
    "altitude_km": 550,           # 平均軌道高度
    "inclination_deg": 53,        # 軌道傾角
    "tx_power_dbm": 43.0,         # 發射功率
    "antenna_gain_db": 15.0       # 最大天線增益
}

def calculate_starlink_rsrp(satellite_data):
    """Starlink 專用 RSRP 計算"""
    # 自由空間路徑損耗
    fspl_db = 20 * log10(satellite_data.distance_km) + \
              20 * log10(12.0) + 32.44
    
    # 仰角相關增益
    elevation_gain = min(satellite_data.elevation_deg / 90.0, 1.0) * 15.0
    
    # 大氣衰減 (仰角相關)
    atmospheric_loss = (90 - satellite_data.elevation_deg) / 90.0 * 3.0
    
    # 最終 RSRP
    rsrp_dbm = 43.0 - fspl_db + elevation_gain - atmospheric_loss
    
    return rsrp_dbm
```

### 3GPP Events 實現

#### Event A4 實現
```python
def check_a4_event(satellite_data):
    """A4 事件條件檢查 - 3GPP TS 38.331 Section 5.5.4.5"""
    Mn = satellite_data.rsrp_dbm          # 測量結果
    Ofn = 0.0                             # 測量對象偏移
    Ocn = 0.0                             # 小區特定偏移
    Hys = 3.0                             # 滯後參數 3dB
    Thresh = -80.0                        # A4 門檻 -80dBm
    
    entering_condition = (Mn + Ofn + Ocn - Hys) > Thresh
    leaving_condition = (Mn + Ofn + Ocn + Hys) < Thresh
    
    return {
        'a4_entering': entering_condition,
        'a4_leaving': leaving_condition,
        'measurement_dbm': Mn
    }
```

## 🎯 階段三：智能衛星篩選

### 篩選策略實現
```python
# 動態篩選策略 (build_with_phase0_data.py:235-245)
if estimated_visible > max_display * 3:
    target_count = max_display  # 通常 15 顆
    strategy = "strict_filtering"
    
    # 星座特定評分權重 (constellation_specific_score)
    Starlink_評分 = {
        "軌道傾角適用性": 30分,  # 針對 53° 傾角優化
        "高度適用性": 25分,      # 550km 最佳高度
        "相位分散度": 20分,      # 避免同步出現/消失
        "換手頻率": 15分,        # 適中的切換頻率
        "信號穩定性": 10分       # 軌道穩定性評估
    }
```

### 智能篩選器位置
```bash
# 主要智能篩選實現
/netstack/src/services/satellite/preprocessing/satellite_selector.py
├── IntelligentSatelliteSelector                    # 智能篩選主類
├── evaluate_handover_suitability()                 # 換手適用性評估
└── select_optimal_satellites()                     # 最佳衛星選擇
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
{
    "satellite_id": "STARLINK-1007",
    "timestamp": "2025-07-30T12:00:00Z",
    "position": {
        "x": 1234.567,  # km, ECEF 座標
        "y": -5678.901, # km
        "z": 3456.789   # km
    },
    "velocity": {
        "vx": 7.123,    # km/s
        "vy": -2.456,   # km/s
        "vz": 1.789     # km/s
    }
}
```

#### 階段二輸出（信號品質增強）
```python
{
    "constellation": "starlink",
    "satellite_id": "STARLINK-1007", 
    "timestamp": "2025-08-10T12:00:00Z",
    
    # 第1階段軌道數據
    "orbit_data": {
        "position": {"x": 1234.5, "y": -5678.9, "z": 3456.7},
        "velocity": {"vx": 7.12, "vy": -2.45, "vz": 1.78},
        "elevation_deg": 45.7,
        "azimuth_deg": 152.3,
        "distance_km": 589.2
    },
    
    # 第2階段信號品質增強
    "signal_quality": {
        "rsrp_dbm": -85.3,
        "rsrq_db": -8.5,
        "sinr_db": 22.1,
        "fspl_db": 162.4,
        "atmospheric_loss_db": 1.2
    },
    
    # 3GPP Events 參數
    "3gpp_events": {
        "a4_eligible": true,
        "a4_measurement_dbm": -85.3,
        "a5_serving_poor": false,
        "a5_neighbor_good": true,
        "d2_distance_m": 589200.0,
        "d2_within_threshold": true
    }
}
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
docker logs netstack-api | grep -E "(Phase|階段)" | tail -20
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