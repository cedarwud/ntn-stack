# 🔍 驗證與動態調整機制

**文檔編號**: 06  
**主題**: 衛星數量驗證、動態調整與預處理資料管理

## 1. 覆蓋驗證腳本

### 1.1 核心驗證邏輯
```python
#!/usr/bin/env python3
# validate_satellite_coverage.py

import numpy as np
from datetime import datetime, timedelta, timezone
from collections import defaultdict

class CoverageValidator:
    """衛星覆蓋驗證器"""
    
    def __init__(self):
        self.NTPU_LAT = 24.9441667
        self.NTPU_LON = 121.3713889
        self.MIN_ELEVATION = 10.0  # 度
        self.TARGET_VISIBLE = (8, 12)  # 目標範圍
        
    def validate_coverage(self, satellite_pool, test_duration_hours=24):
        """驗證24小時覆蓋品質"""
        
        # 每30秒採樣一次
        sample_points = test_duration_hours * 120  # 24h * 120 = 2880 點
        
        results = {
            'timestamps': [],
            'visible_counts': [],
            'coverage_gaps': [],
            'statistics': {}
        }
        
        start_time = datetime.now(timezone.utc)
        
        for i in range(sample_points):
            timestamp = start_time + timedelta(seconds=i*30)
            
            # 計算該時刻可見衛星
            visible_sats = self.count_visible_satellites(
                satellite_pool, 
                timestamp
            )
            
            results['timestamps'].append(timestamp)
            results['visible_counts'].append(visible_sats)
            
            # 記錄覆蓋缺口
            if visible_sats < self.TARGET_VISIBLE[0]:
                results['coverage_gaps'].append({
                    'timestamp': timestamp,
                    'visible': visible_sats,
                    'deficit': self.TARGET_VISIBLE[0] - visible_sats
                })
        
        # 計算統計
        results['statistics'] = self.calculate_statistics(results)
        
        return results
    
    def calculate_statistics(self, results):
        """計算覆蓋統計"""
        
        visible_array = np.array(results['visible_counts'])
        
        return {
            'min_visible': int(np.min(visible_array)),
            'max_visible': int(np.max(visible_array)),
            'mean_visible': float(np.mean(visible_array)),
            'std_visible': float(np.std(visible_array)),
            'median_visible': float(np.median(visible_array)),
            
            # 關鍵指標
            'below_target_ratio': len(results['coverage_gaps']) / len(visible_array),
            'optimal_coverage_ratio': np.sum(
                (visible_array >= self.TARGET_VISIBLE[0]) & 
                (visible_array <= self.TARGET_VISIBLE[1])
            ) / len(visible_array),
            
            # 連續性指標
            'max_gap_duration': self.find_max_gap_duration(results['coverage_gaps']),
            'total_gap_time': len(results['coverage_gaps']) * 30 / 60,  # 分鐘
            
            # 判定結果
            'validation_passed': self.check_validation_criteria(results)
        }
    
    def check_validation_criteria(self, results):
        """檢查是否通過驗證標準"""
        
        stats = results['statistics'] if 'statistics' in results else {}
        
        criteria = {
            'min_visible_ok': stats.get('min_visible', 0) >= 6,
            'mean_visible_ok': 8 <= stats.get('mean_visible', 0) <= 12,
            'gap_ratio_ok': stats.get('below_target_ratio', 1) <= 0.05,  # <5% 時間缺口
            'optimal_ratio_ok': stats.get('optimal_coverage_ratio', 0) >= 0.90  # >90% 理想覆蓋
        }
        
        return all(criteria.values()), criteria
```

### 1.2 動態調整算法（澄清版）
```python
class DynamicAdjustment:
    """動態調整衛星選擇策略 - 不是憑空增加衛星"""
    
    def __init__(self):
        self.all_available_satellites = []  # 所有真實存在的衛星
        self.selected_subset = []           # 當前選中的子集
        
    def calculate_adjustment(self, validation_results, current_subset):
        """根據驗證結果調整選擇策略"""
        
        stats = validation_results['statistics']
        mean_visible = stats['mean_visible']
        
        if mean_visible < 8:
            # 從真實衛星池中選擇更多衛星
            return {
                'action': 'EXPAND_SELECTION',
                'strategy': self.expand_selection_strategy(),
                'reason': f'平均可見 {mean_visible:.1f} < 8'
            }
            
        elif mean_visible > 12:
            # 可以選擇較少的衛星（節省計算資源）
            return {
                'action': 'REDUCE_SELECTION',
                'strategy': self.reduce_selection_strategy(),
                'reason': f'平均可見 {mean_visible:.1f} > 12'
            }
        
        return {
            'action': 'MAINTAIN',
            'strategy': 'current',
            'reason': '覆蓋品質符合標準'
        }
    
    def expand_selection_strategy(self):
        """擴大選擇策略 - 從真實衛星中選更多"""
        
        return {
            'method_1': '降低相位間隔要求（從15°降到10°）',
            'method_2': '放寬軌道平面限制（每平面選3-4顆而非2-3顆）',
            'method_3': '擴大地理搜索範圍（考慮更遠的衛星）',
            'method_4': '選擇更多軌道平面的衛星'
        }
    
    def select_more_satellites_from_real_pool(self, time_window):
        """從真實衛星池中選擇更多衛星"""
        
        # 重要：這些都是真實存在的衛星，在特定時間有真實軌道
        candidate_satellites = []
        
        for sat in self.all_available_satellites:
            # 檢查該衛星在時間窗口內是否會經過 NTPU
            if self.will_pass_over_ntpu(sat, time_window):
                candidate_satellites.append(sat)
        
        # 按照可見性評分排序
        scored = self.score_satellites(candidate_satellites)
        
        # 選擇前 N 顆
        return scored[:self.target_count]
```

## 2. 預處理資料更新策略（修正版）

### 2.1 TLE 更新追蹤機制
```python
class TLEUpdateTracker:
    """追蹤 TLE 更新狀態，處理不定期更新"""
    
    def __init__(self):
        self.update_log = {
            'last_processed_date': None,    # 上次處理的 TLE 日期
            'last_check_time': None,         # 上次檢查時間
            'pending_updates': []            # 待處理的更新
        }
        
    def check_for_updates(self):
        """檢查是否有新的 TLE 數據"""
        
        # 掃描 TLE 目錄
        latest_tle_date = self.scan_tle_directory()
        
        if latest_tle_date > self.update_log['last_processed_date']:
            # 計算需要更新的日期範圍
            date_gap = (latest_tle_date - self.update_log['last_processed_date']).days
            
            return {
                'has_updates': True,
                'gap_days': date_gap,
                'date_range': {
                    'from': self.update_log['last_processed_date'],
                    'to': latest_tle_date
                }
            }
        
        return {'has_updates': False}
    
    def scan_tle_directory(self):
        """掃描 TLE 目錄找出最新日期"""
        
        import os
        import re
        from datetime import datetime
        
        tle_dir = '/home/sat/ntn-stack/netstack/tle_data/starlink/tle/'
        date_pattern = r'starlink_(\d{8})\.tle'
        
        latest_date = None
        for filename in os.listdir(tle_dir):
            match = re.match(date_pattern, filename)
            if match:
                date_str = match.group(1)
                file_date = datetime.strptime(date_str, '%Y%m%d')
                if latest_date is None or file_date > latest_date:
                    latest_date = file_date
        
        return latest_date

class IncrementalUpdateManager:
    """處理增量更新 - 支援任意時間間隔"""
    
    def __init__(self):
        self.tle_tracker = TLEUpdateTracker()
        self.processing_window = 48  # 預處理48小時數據
        
    def perform_incremental_update(self):
        """執行增量更新 - 自動處理時間差"""
        
        # 1. 檢查更新
        update_info = self.tle_tracker.check_for_updates()
        
        if not update_info['has_updates']:
            print("無新的 TLE 數據")
            return
        
        # 2. 處理更新
        gap_days = update_info['gap_days']
        
        if gap_days <= 7:
            # 小間隔：增量更新
            self.incremental_process(update_info['date_range'])
        else:
            # 大間隔：完整重算
            print(f"TLE 間隔 {gap_days} 天，執行完整重算")
            self.full_recalculation()
    
    def incremental_process(self, date_range):
        """增量處理指定日期範圍"""
        
        # 載入新舊 TLE
        old_tle = self.load_tle(date_range['from'])
        new_tle = self.load_tle(date_range['to'])
        
        # 找出變化的衛星
        changed_satellites = self.detect_changes(old_tle, new_tle)
        
        print(f"檢測到 {len(changed_satellites)} 顆衛星軌道變化")
        
        # 只重算變化的衛星
        for sat in changed_satellites:
            self.recalculate_satellite_trajectory(
                sat,
                start_time=datetime.now(),
                duration_hours=self.processing_window
            )
        
        # 更新記錄
        self.tle_tracker.update_log['last_processed_date'] = date_range['to']
```

### 2.2 智能預處理排程
```python
# cron_preprocessor.py
import schedule
import time

class SmartPreprocessor:
    """智能預處理排程器"""
    
    def __init__(self):
        self.setup_schedule()
        
    def setup_schedule(self):
        """設置排程任務"""
        
        # TLE 更新後觸發
        schedule.every(6).hours.do(self.process_after_tle_update)
        
        # 滑動窗口更新
        schedule.every(1).hours.do(self.sliding_window_update)
        
        # 驗證覆蓋品質
        schedule.every(12).hours.do(self.validate_coverage)
        
        # 清理過期數據
        schedule.every(24).hours.do(self.cleanup_expired_data)
    
    def process_after_tle_update(self):
        """TLE 更新後的處理"""
        
        print(f"[{datetime.now()}] 開始預處理更新...")
        
        # 1. 檢測 TLE 變化
        changed = self.detect_tle_changes()
        
        # 2. 增量計算
        if changed:
            self.incremental_calculate(changed)
        
        # 3. 驗證覆蓋
        validation = self.quick_validate()
        
        # 4. 動態調整
        if not validation['passed']:
            self.dynamic_adjust()
    
    def sliding_window_update(self):
        """滑動窗口更新"""
        
        # 移除過期數據
        self.remove_expired_data()
        
        # 計算新時間段
        self.calculate_new_window()
        
        # 更新緩存
        self.refresh_cache()
```

## 3. 存儲架構重設計

### 3.1 分層存儲設計
```yaml
# storage_architecture.yaml

熱數據層 (Redis):
  容量: 1GB
  內容: 未來1小時衛星位置
  更新: 每30秒
  格式: 
    key: "sat:{sat_id}:{timestamp}"
    value: {lat, lon, alt, elevation, azimuth, rsrp}
  TTL: 3600秒

溫數據層 (PostgreSQL):
  容量: 10GB
  內容: 24-48小時完整軌跡
  更新: 每6小時
  表結構:
    - satellite_positions_current (分區表)
    - satellite_events_predicted
    - handover_candidates_cache
  索引: (satellite_id, timestamp)

冷數據層 (壓縮文件):
  容量: 無限制
  內容: 歷史數據存檔
  格式: Parquet/壓縮JSON
  路徑: /data/satellite_archive/
```

### 3.2 讀取優化策略
```python
class OptimizedDataReader:
    """優化的數據讀取器"""
    
    def __init__(self):
        self.cache_hierarchy = [
            self.read_from_memory,
            self.read_from_redis,
            self.read_from_postgres,
            self.read_from_file
        ]
    
    async def get_satellite_data(self, satellite_id, timestamp, window_minutes=5):
        """分層讀取衛星數據"""
        
        # 1. 記憶體快取
        cached = self.memory_cache.get(f"{satellite_id}:{timestamp}")
        if cached:
            return cached
        
        # 2. Redis 熱數據
        if self.is_near_future(timestamp):
            data = await self.redis_client.get_range(
                satellite_id, 
                timestamp,
                window_minutes
            )
            if data:
                self.memory_cache.set(data)
                return data
        
        # 3. PostgreSQL 溫數據
        if self.is_within_48h(timestamp):
            data = await self.pg_client.query_trajectory(
                satellite_id,
                timestamp,
                window_minutes
            )
            # 預載入到 Redis
            await self.preload_to_redis(data)
            return data
        
        # 4. 文件系統冷數據
        return await self.load_from_archive(satellite_id, timestamp)
```

## 4. 資料量估算與優化

### 4.1 存儲需求計算
```python
storage_estimation = {
    "單顆衛星": {
        "每個時間點": 100,  # bytes
        "30秒間隔": 2880,   # 點/天
        "日數據量": 288000  # bytes ≈ 281 KB
    },
    "200顆衛星": {
        "日數據量": 56.25,  # MB
        "48小時": 112.5,    # MB
        "壓縮後": 20        # MB (壓縮率 80%)
    },
    "事件數據": {
        "每小時事件": 50,
        "每個事件": 500,    # bytes
        "日數據量": 1.2      # MB
    },
    "總計": {
        "熱數據": 10,        # MB (1小時)
        "溫數據": 120,       # MB (48小時)
        "每月冷數據": 600    # MB (壓縮)
    }
}
```

### 4.2 性能優化措施
```python
optimization_strategies = {
    "批量處理": "使用 NumPy 向量化計算",
    "並行計算": "多進程處理不同衛星",
    "增量更新": "只計算變化部分",
    "數據壓縮": "使用 Parquet 格式",
    "索引優化": "時間+衛星複合索引",
    "預計算": "提前計算下一小時",
    "緩存預熱": "預載入熱門數據"
}
```

## 5. 自動化運維腳本

### 5.1 主控制腳本
```bash
#!/bin/bash
# satellite_preprocessing_manager.sh

# 驗證覆蓋
validate_coverage() {
    python3 validate_satellite_coverage.py \
        --constellation $1 \
        --count $2 \
        --output coverage_report.json
    
    if [ $? -ne 0 ]; then
        echo "覆蓋驗證失敗，執行動態調整..."
        adjust_satellite_count $1 $2
    fi
}

# 更新預處理數據
update_preprocessed_data() {
    echo "[$(date)] 開始更新預處理數據..."
    
    # 增量更新
    python3 incremental_preprocessor.py \
        --mode incremental \
        --hours 6
    
    # 驗證
    validate_coverage "starlink" 120
    validate_coverage "oneweb" 80
}

# Cron 任務設置
setup_cron() {
    # TLE 更新後處理
    echo "5 */6 * * * /path/to/update_preprocessed_data" | crontab -
    
    # 每小時滑動窗口
    echo "0 * * * * /path/to/sliding_window_update.sh" | crontab -
    
    # 每日完整驗證
    echo "0 3 * * * /path/to/full_validation.sh" | crontab -
}
```

## 6. 監控指標

```python
monitoring_metrics = {
    "覆蓋品質": {
        "min_visible_satellites": "gauge",
        "mean_visible_satellites": "gauge", 
        "coverage_gap_ratio": "gauge"
    },
    "預處理性能": {
        "preprocessing_time": "histogram",
        "data_freshness": "gauge",
        "cache_hit_ratio": "gauge"
    },
    "存儲使用": {
        "redis_memory_usage": "gauge",
        "postgres_table_size": "gauge",
        "archive_disk_usage": "gauge"
    }
}
```

---

**結論**: 
- 驗證腳本確保 120/80 顆衛星足夠，不夠時自動調整
- 預處理數據通過 Cron 自動更新（增量+滑動窗口）
- 分層存儲架構處理大數據量（熱/溫/冷）
- 完整的自動化運維流程