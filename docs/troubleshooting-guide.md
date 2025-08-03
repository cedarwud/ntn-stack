# LEO 衛星換手系統故障排除指南

**版本**: 2.0.0  
**建立日期**: 2025-08-03 (Phase 2)  
**適用範圍**: LEO 衛星換手系統全部組件  
**維護團隊**: 技術支援 + 開發團隊  

## 📋 概述

本指南提供了 LEO 衛星換手系統常見問題的診斷和解決方案，基於 Phase 1 統一配置系統和智能篩選機制的實際部署經驗，為運維人員和開發人員提供快速故障定位和修復指導。

## 🆘 緊急故障處理

### 🚨 系統完全無法啟動

**症狀**: Docker 容器無法啟動，所有服務不可用

**快速診斷**:
```bash
# 1. 檢查容器狀態
docker-compose ps

# 2. 檢查系統資源
df -h                    # 磁碟空間
free -h                  # 記憶體使用
docker system df         # Docker 空間使用

# 3. 檢查日誌
docker-compose logs --tail=50
```

**解決方案**:
```bash
# 方案 1: 清理 Docker 資源
docker system prune -f
docker volume prune -f

# 方案 2: 重置系統狀態
make down
docker-compose down --volumes
make up

# 方案 3: 回滾到穩定版本
git checkout HEAD~1
make down && make up
```

### 🚨 API 完全無響應

**症狀**: NetStack API (localhost:8080) 無法訪問

**快速診斷**:
```bash
# 1. 檢查 API 容器狀態
docker logs netstack-api --tail=20

# 2. 檢查網路連接
curl -I http://localhost:8080/health
netstat -tlnp | grep 8080

# 3. 檢查配置載入
docker exec netstack-api python -c "from config.satellite_config import SATELLITE_CONFIG; print('Config OK')"
```

**解決方案**:
```bash
# 方案 1: 重啟 API 服務
docker-compose restart netstack-api

# 方案 2: 檢查配置問題
docker exec netstack-api python -m config_management.config_validator validate

# 方案 3: 完全重建 API 容器
docker-compose stop netstack-api
docker-compose rm -f netstack-api
docker-compose up -d netstack-api
```

### 🚨 數據完全遺失

**症狀**: 預計算數據、TLE 數據全部消失

**快速診斷**:
```bash
# 1. 檢查 Docker Volume
docker volume ls | grep ntn-stack
docker volume inspect ntn-stack_netstack-data

# 2. 檢查數據文件
docker exec netstack-api ls -la /app/data/
docker exec simworld_backend ls -la /app/data/

# 3. 檢查備份狀態
ls -la /home/sat/ntn-stack/backup/
```

**解決方案**:
```bash
# 方案 1: 從最近備份恢復
backup_dir=$(ls -t /home/sat/ntn-stack/backup/ | head -1)
docker-compose down
cp -r /home/sat/ntn-stack/backup/$backup_dir/* /var/lib/docker/volumes/ntn-stack_netstack-data/_data/
docker-compose up -d

# 方案 2: 重新生成數據
docker exec netstack-api python -m scripts.batch_precompute_taiwan --force-regenerate

# 方案 3: 從歷史 TLE 重建
docker exec simworld_backend python -m app.services.historical_orbit_generator
```

## 🔧 常見問題診斷與修復

### 1. 配置相關問題

#### ❌ 統一配置系統載入失敗

**症狀**: 
- 日誌出現 "⚠️ 統一配置系統不可用，使用預設值"
- 衛星數量配置不一致
- SIB19 合規檢查失敗

**診斷步驟**:
```bash
# 1. 檢查配置文件是否存在
ls -la /home/sat/ntn-stack/netstack/config/

# 2. 檢查配置語法
python -c "from netstack.config.satellite_config import SATELLITE_CONFIG; print('✅ 配置載入成功')"

# 3. 檢查跨容器路徑
docker exec simworld_backend python -c "
import sys
sys.path.append('/app/netstack')
try:
    from config.satellite_config import SATELLITE_CONFIG
    print('✅ 跨容器配置存取成功')
except ImportError as e:
    print(f'❌ 跨容器配置存取失敗: {e}')
"
```

**解決方案**:
```bash
# 1. 修復配置文件權限
chmod 644 /home/sat/ntn-stack/netstack/config/*.py

# 2. 重新載入配置
docker-compose restart simworld_backend netstack-api

# 3. 驗證配置修復
python -m pytest tests/test_satellite_config.py -v
```

#### ❌ SIB19 合規性檢查失敗

**症狀**: 
- 候選衛星數量超過 8 顆
- 仰角門檻配置錯誤
- 3GPP NTN 標準違規警告

**診斷步驟**:
```python
# 執行完整合規性檢查
from netstack.config.satellite_config import SATELLITE_CONFIG
from netstack.config_management.config_validator import ConfigurationValidator

validator = ConfigurationValidator()
result = validator.validate_full_configuration(SATELLITE_CONFIG)
print(f"SIB19 合規性: {result.is_compliant}")
print(f"違規項目: {result.violations}")
```

**解決方案**:
```python
# 1. 修正候選衛星數量
SATELLITE_CONFIG.MAX_CANDIDATE_SATELLITES = 8  # 確保 ≤ 8

# 2. 修正仰角門檻順序
SATELLITE_CONFIG.elevation_thresholds.critical_threshold_deg = 5.0
SATELLITE_CONFIG.elevation_thresholds.execution_threshold_deg = 10.0
SATELLITE_CONFIG.elevation_thresholds.trigger_threshold_deg = 15.0

# 3. 重新驗證
validator.validate_full_configuration(SATELLITE_CONFIG)
```

### 2. 智能篩選系統問題

#### ❌ 智能篩選無效或過度篩選

**症狀**: 
- 篩選後衛星數量為 0
- 篩選效果異常（過多或過少）
- 地理相關性篩選失效

**診斷步驟**:
```python
# 檢查篩選配置
from netstack.config.satellite_config import SATELLITE_CONFIG

print(f"智能篩選啟用: {SATELLITE_CONFIG.intelligent_selection.enabled}")
print(f"地理篩選啟用: {SATELLITE_CONFIG.intelligent_selection.geographic_filter_enabled}")
print(f"目標位置: {SATELLITE_CONFIG.intelligent_selection.target_location}")

# 檢查篩選結果
from netstack.services.intelligent_satellite_filter import IntelligentSatelliteFilter

filter_engine = IntelligentSatelliteFilter()
# 模擬篩選過程
test_satellites = filter_engine.debug_filtering_process()
print(f"篩選結果: {len(test_satellites)} 顆衛星")
```

**解決方案**:
```python
# 1. 調整篩選參數
SATELLITE_CONFIG.intelligent_selection.scoring_weights = {
    'inclination': 0.20,      # 降低傾角權重
    'altitude': 0.15,         # 降低高度權重
    'eccentricity': 0.10,     # 降低偏心率權重
    'frequency': 0.25,        # 提高頻率權重
    'constellation': 0.30     # 提高星座權重
}

# 2. 暫時禁用地理篩選進行測試
SATELLITE_CONFIG.intelligent_selection.geographic_filter_enabled = False

# 3. 擴大目標位置容忍範圍
SATELLITE_CONFIG.intelligent_selection.geographic_tolerance_deg = 60.0  # 從 45° 增加到 60°
```

#### ❌ 篩選性能問題

**症狀**: 
- 篩選過程耗時過長（> 30 秒）
- 記憶體使用異常增高
- CPU 使用率持續 100%

**診斷步驟**:
```bash
# 1. 監控篩選性能
docker exec netstack-api python -c "
import time
from netstack.services.intelligent_satellite_filter import IntelligentSatelliteFilter

start_time = time.time()
filter_engine = IntelligentSatelliteFilter()
# 執行篩選測試
filtered_sats = filter_engine.filter_satellites_for_location('starlink')
end_time = time.time()

print(f'篩選耗時: {end_time - start_time:.2f} 秒')
print(f'篩選結果: {len(filtered_sats)} 顆衛星')
"

# 2. 檢查記憶體使用
docker stats netstack-api --no-stream
```

**解決方案**:
```python
# 1. 啟用分批處理
SATELLITE_CONFIG.intelligent_selection.batch_processing_enabled = True
SATELLITE_CONFIG.intelligent_selection.batch_size = 500  # 每批處理 500 顆

# 2. 啟用結果快取
SATELLITE_CONFIG.intelligent_selection.caching_enabled = True
SATELLITE_CONFIG.intelligent_selection.cache_ttl_seconds = 3600  # 1小時快取

# 3. 並行處理
SATELLITE_CONFIG.intelligent_selection.parallel_processing = True
SATELLITE_CONFIG.intelligent_selection.worker_threads = 4
```

### 3. SGP4 軌道計算問題

#### ❌ SGP4 計算失敗或精度異常

**症狀**: 
- 軌道計算返回 None 或異常值
- 衛星位置明顯錯誤
- 計算精度降級到簡化模型

**診斷步驟**:
```python
# 檢查 SGP4 計算器狀態
from netstack.services.sgp4_calculator import SGP4Calculator
from netstack.services.sgp4_calculator import TLEData

calculator = SGP4Calculator()

# 測試 TLE 數據
test_tle = TLEData(
    name="STARLINK-1007",
    line1="1 44713U 19074A   25215.12345678  .00001234  00000-0  12345-4 0  9990",
    line2="2 44713  53.0000 123.4567 0001234  90.1234 269.8765 15.12345678123456"
)

result = calculator.propagate_orbit(test_tle, datetime.utcnow())
print(f"SGP4 計算結果: {result}")
print(f"位置: ({result.latitude:.4f}°, {result.longitude:.4f}°, {result.altitude:.2f}km)")
```

**解決方案**:
```python
# 1. 更新 TLE 數據
from netstack.data.historical_tle_data import refresh_tle_data
refresh_tle_data(force_download=True)

# 2. 檢查 TLE 數據格式
def validate_tle_format(line1, line2):
    if not line1.startswith("1 ") or not line2.startswith("2 "):
        raise ValueError("TLE 格式錯誤")
    if len(line1) != 69 or len(line2) != 69:
        raise ValueError("TLE 長度錯誤")
    # 檢查校驗和
    return True

# 3. 啟用備用計算方案
SATELLITE_CONFIG.computation_precision.fallback_enabled = True
SATELLITE_CONFIG.computation_precision.strict_validation = False
```

#### ❌ 軌道預測時間漂移

**症狀**: 
- 預測位置與實際觀測不符
- 時間同步問題
- 星曆時間戳異常

**診斷步驟**:
```python
# 檢查時間同步
from datetime import datetime, timezone
import time

# 系統時間 vs UTC 時間
system_time = datetime.now()
utc_time = datetime.now(timezone.utc)
ntp_time = get_ntp_time()  # 如果有 NTP 客戶端

print(f"系統時間: {system_time}")
print(f"UTC 時間: {utc_time}")  
print(f"NTP 時間: {ntp_time}")
print(f"時間偏差: {abs((utc_time - ntp_time).total_seconds())} 秒")
```

**解決方案**:
```bash
# 1. 同步系統時間
sudo ntpdate -s time.nist.gov
sudo hwclock --systohc

# 2. 檢查時區設置
timedatectl status
sudo timedatectl set-timezone UTC

# 3. 重新計算星曆基準
docker exec netstack-api python -c "
from netstack.services.sib19_unified_platform import SIB19UnifiedPlatform
platform = SIB19UnifiedPlatform()
platform.synchronize_epoch_time()
"
```

### 4. 數據載入與存儲問題

#### ❌ Docker Volume 數據遺失

**症狀**: 
- 預計算數據消失
- TLE 數據無法載入
- 數據完整性檢查失敗

**診斷步驟**:
```bash
# 1. 檢查 Volume 狀態
docker volume inspect ntn-stack_netstack-data
docker volume inspect ntn-stack_simworld-data

# 2. 檢查數據目錄
docker exec netstack-api ls -la /app/data/
docker exec simworld_backend ls -la /app/data/

# 3. 檢查文件權限
docker exec netstack-api find /app/data -type f -not -readable
```

**解決方案**:
```bash
# 1. 修復 Volume 權限
docker exec --user root netstack-api chown -R app:app /app/data/
docker exec --user root simworld_backend chown -R app:app /app/data/

# 2. 重新掛載 Volume
docker-compose down
docker-compose up -d

# 3. 從備份恢復
if [ -d "/home/sat/ntn-stack/backup/latest/" ]; then
    docker-compose down
    sudo cp -r /home/sat/ntn-stack/backup/latest/* /var/lib/docker/volumes/ntn-stack_netstack-data/_data/
    docker-compose up -d
fi
```

#### ❌ TLE 數據解析失敗

**症狀**: 
- TLE 文件無法解析
- 衛星數據為空
- SGP4 初始化失敗

**診斷步驟**:
```python
# 檢查 TLE 數據完整性
from netstack.data.historical_tle_data import get_historical_tle_data, validate_tle_data

# 載入並驗證 TLE 數據
starlink_data = get_historical_tle_data("starlink")
print(f"Starlink 衛星數量: {len(starlink_data)}")

for i, sat in enumerate(starlink_data[:3]):  # 檢查前3顆
    print(f"衛星 {i+1}:")
    print(f"  名稱: {sat['name']}")
    print(f"  Line1: {sat['line1']}")
    print(f"  Line2: {sat['line2']}")
    
    # 驗證 TLE 格式
    is_valid = validate_tle_data(sat['line1'], sat['line2'])
    print(f"  格式正確: {is_valid}")
```

**解決方案**:
```python
# 1. 重新下載 TLE 數據
from netstack.scripts.daily_tle_download import download_fresh_tle_data
download_fresh_tle_data(constellations=["starlink", "oneweb"])

# 2. 修復損壞的 TLE 數據
def repair_tle_data(tle_file_path):
    with open(tle_file_path, 'r') as f:
        lines = f.readlines()
    
    repaired_lines = []
    for i in range(0, len(lines), 3):
        if i + 2 < len(lines):
            name = lines[i].strip()
            line1 = lines[i+1].strip()
            line2 = lines[i+2].strip()
            
            # 驗證並修復
            if line1.startswith("1 ") and line2.startswith("2 "):
                repaired_lines.extend([name + '\n', line1 + '\n', line2 + '\n'])
    
    with open(tle_file_path + '.repaired', 'w') as f:
        f.writelines(repaired_lines)

# 3. 重建數據索引
from netstack.services.data_indexer import rebuild_satellite_index
rebuild_satellite_index()
```

### 5. 性能問題

#### ❌ API 響應時間過長

**症狀**: 
- API 響應時間 > 1 秒
- 查詢操作超時
- 系統負載過高

**診斷步驟**:
```bash
# 1. 測試 API 性能
time curl -s "http://localhost:8080/api/v1/satellites/constellations/info" > /dev/null

# 2. 分析慢查詢
docker exec netstack-api python -c "
import time
import requests

# 測試各個端點
endpoints = [
    '/health',  
    '/api/v1/satellites/constellations/info',
    '/api/v1/satellites/positions?constellation=starlink&count=10'
]

for endpoint in endpoints:
    start = time.time()
    response = requests.get(f'http://localhost:8080{endpoint}')
    end = time.time()
    print(f'{endpoint}: {end-start:.3f}s ({response.status_code})')
"

# 3. 檢查數據庫性能
docker exec netstack-rl-postgres psql -U rl_user -d rl_research -c "
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;
"
```

**解決方案**:
```python
# 1. 啟用查詢快取
SATELLITE_CONFIG.performance_optimization.query_caching_enabled = True
SATELLITE_CONFIG.performance_optimization.cache_ttl_seconds = 300

# 2. 數據庫索引優化
docker exec netstack-rl-postgres psql -U rl_user -d rl_research -c "
CREATE INDEX IF NOT EXISTS idx_satellite_orbital_cache_timestamp 
ON satellite_orbital_cache(timestamp);

CREATE INDEX IF NOT EXISTS idx_satellite_orbital_cache_satellite_id 
ON satellite_orbital_cache(satellite_id);
"

# 3. 啟用結果分頁
SATELLITE_CONFIG.api_optimization.pagination_enabled = True
SATELLITE_CONFIG.api_optimization.default_page_size = 50
SATELLITE_CONFIG.api_optimization.max_page_size = 200
```

#### ❌ 記憶體使用過高

**症狀**: 
- 容器記憶體使用 > 2GB
- 系統出現 OOM (Out of Memory)
- 服務異常重啟

**診斷步驟**:
```bash
# 1. 檢查容器記憶體使用
docker stats --no-stream

# 2. 分析記憶體分配
docker exec netstack-api python -c "
import psutil
import gc

# 檢查 Python 記憶體使用
process = psutil.Process()
memory_info = process.memory_info()
print(f'RSS: {memory_info.rss / 1024 / 1024:.2f} MB')
print(f'VMS: {memory_info.vms / 1024 / 1024:.2f} MB')

# 檢查垃圾回收
gc.collect()
print(f'垃圾回收後: {process.memory_info().rss / 1024 / 1024:.2f} MB')
"

# 3. 檢查大對象
docker exec netstack-api python -c "
import sys
from pympler import tracker

tr = tracker.SummaryTracker()
# 載入衛星數據
from netstack.data.historical_tle_data import get_historical_tle_data
data = get_historical_tle_data('starlink')
tr.print_diff()
"
```

**解決方案**:
```python
# 1. 啟用分批處理
SATELLITE_CONFIG.memory_optimization.batch_processing_enabled = True
SATELLITE_CONFIG.memory_optimization.max_batch_size = 1000

# 2. 定期垃圾回收
import gc
import threading

def periodic_gc():
    while True:
        time.sleep(300)  # 每5分鐘執行一次
        collected = gc.collect()
        logger.info(f"垃圾回收: 清理了 {collected} 個對象")

gc_thread = threading.Thread(target=periodic_gc, daemon=True)
gc_thread.start()

# 3. 限制容器記憶體
# 在 docker-compose.yml 中添加：
# services:
#   netstack-api:
#     mem_limit: 1g
#     memswap_limit: 1g
```

## 🔍 日誌分析與監控

### 日誌收集命令

```bash
# 1. 收集所有服務日誌
mkdir -p /tmp/ntn-stack-logs/$(date +%Y%m%d_%H%M)
cd /tmp/ntn-stack-logs/$(date +%Y%m%d_%H%M)

# 收集容器日誌
docker-compose logs --no-color > docker-compose.log
docker logs netstack-api > netstack-api.log
docker logs simworld_backend > simworld_backend.log
docker logs netstack-rl-postgres > postgres.log

# 收集系統信息
docker-compose ps > container_status.txt
docker system df > docker_disk_usage.txt
free -h > memory_usage.txt
df -h > disk_usage.txt

# 打包日誌
cd /tmp/ntn-stack-logs/
tar -czf ntn-stack-logs-$(date +%Y%m%d_%H%M).tar.gz $(date +%Y%m%d_%H%M)/
```

### 關鍵錯誤模式識別

```bash
# 1. 檢查配置相關錯誤
docker-compose logs | grep -E "(配置|Config|SIB19|統一配置)"

# 2. 檢查 SGP4 計算錯誤  
docker-compose logs | grep -E "(SGP4|軌道|orbit|propagate)"

# 3. 檢查數據載入錯誤
docker-compose logs | grep -E "(TLE|載入|load|數據|data)"

# 4. 檢查性能問題
docker-compose logs | grep -E "(timeout|slow|performance|性能)"

# 5. 檢查記憶體問題
docker-compose logs | grep -E "(memory|OOM|out of memory|記憶體)"
```

### 健康檢查腳本

```bash
#!/bin/bash
# health_check.sh - 系統健康檢查腳本

echo "🏥 LEO 衛星系統健康檢查"
echo "================================"

# 1. 容器健康檢查
echo "📦 容器狀態檢查："
healthy_containers=$(docker-compose ps | grep "Up.*healthy" | wc -l)
total_containers=$(docker-compose ps | grep "Up" | wc -l)
echo "  健康容器: $healthy_containers/$total_containers"

if [ $healthy_containers -lt 3 ]; then
    echo "  ❌ 部分容器不健康"
    docker-compose ps | grep -v "Up.*healthy"
else
    echo "  ✅ 所有容器健康"
fi

# 2. API 可用性檢查
echo "🔗 API 可用性檢查："
api_response=$(curl -s -w "%{http_code}" -o /dev/null http://localhost:8080/health)
if [ "$api_response" -eq 200 ]; then
    echo "  ✅ NetStack API 正常 (200)"
else
    echo "  ❌ NetStack API 異常 ($api_response)"
fi

frontend_response=$(curl -s -w "%{http_code}" -o /dev/null http://localhost:5173)
if [ "$frontend_response" -eq 200 ]; then
    echo "  ✅ SimWorld Frontend 正常 (200)"
else
    echo "  ❌ SimWorld Frontend 異常 ($frontend_response)"
fi

# 3. 配置檢查
echo "⚙️  配置系統檢查："
config_check=$(docker exec netstack-api python -c "
try:
    from config.satellite_config import SATELLITE_CONFIG
    print('✅ 統一配置系統正常')
    print(f'  候選衛星數量: {SATELLITE_CONFIG.MAX_CANDIDATE_SATELLITES}')
    print(f'  智能篩選: {\"啟用\" if SATELLITE_CONFIG.intelligent_selection.enabled else \"禁用\"}')
except Exception as e:
    print(f'❌ 配置系統異常: {e}')
" 2>/dev/null)
echo "$config_check"

# 4. 數據檢查
echo "📊 數據完整性檢查："
data_check=$(docker exec netstack-api python -c "
import os
data_files = [
    '/app/data/phase0_precomputed_orbits.json',
    '/app/netstack/tle_data/starlink',
    '/app/netstack/tle_data/oneweb'
]

for file_path in data_files:
    if os.path.exists(file_path):
        if os.path.isfile(file_path):
            size = os.path.getsize(file_path)
            print(f'  ✅ {os.path.basename(file_path)}: {size} bytes')
        else:
            count = len(os.listdir(file_path)) if os.path.isdir(file_path) else 0
            print(f'  ✅ {os.path.basename(file_path)}: {count} files')
    else:
        print(f'  ❌ {os.path.basename(file_path)}: 不存在')
" 2>/dev/null)
echo "$data_check"

# 5. 性能檢查
echo "🚀 性能檢查："
start_time=$(date +%s%N)
curl -s http://localhost:8080/api/v1/satellites/constellations/info > /dev/null
end_time=$(date +%s%N)
response_time=$(( (end_time - start_time) / 1000000 ))
echo "  API 響應時間: ${response_time}ms"

if [ $response_time -lt 100 ]; then
    echo "  ✅ 性能優秀 (<100ms)"
elif [ $response_time -lt 500 ]; then
    echo "  ⚠️  性能一般 (100-500ms)"
else
    echo "  ❌ 性能較差 (>500ms)"
fi

echo "================================"
echo "🏁 健康檢查完成"
```

## 📋 預防性維護

### 定期維護任務

```bash
# 每日維護腳本 (daily_maintenance.sh)
#!/bin/bash

echo "📅 每日維護任務開始"

# 1. 清理 Docker 資源
docker system prune -f
docker volume prune -f

# 2. 檢查日誌文件大小
find /var/lib/docker/containers -name "*.log" -size +100M -exec truncate -s 50M {} \;

# 3. 備份配置
backup_dir="/home/sat/ntn-stack/backup/config_$(date +%Y%m%d)"
mkdir -p $backup_dir
cp -r /home/sat/ntn-stack/netstack/config/ $backup_dir/

# 4. 檢查數據完整性
docker exec netstack-api python -m netstack.scripts.data_integrity_check

# 5. 更新 TLE 數據 (如果需要)
docker exec netstack-api python -m netstack.scripts.daily_tle_download --check-age

echo "✅ 每日維護完成"
```

### 監控告警設置

```python
# 監控指標閾值
MONITORING_THRESHOLDS = {
    'api_response_time': 500,      # 毫秒
    'memory_usage_percent': 80,    # 百分比
    'disk_usage_percent': 85,      # 百分比
    'container_restart_count': 3,  # 每小時重啟次數
    'error_rate_percent': 5,       # 錯誤率百分比
}

# 告警腳本
def check_and_alert():
    alerts = []
    
    # 檢查 API 響應時間
    if get_api_response_time() > MONITORING_THRESHOLDS['api_response_time']:
        alerts.append("API 響應時間過長")
    
    # 檢查記憶體使用
    if get_memory_usage_percent() > MONITORING_THRESHOLDS['memory_usage_percent']:
        alerts.append("記憶體使用率過高")
    
    # 發送告警
    if alerts:
        send_alerts(alerts)
```

## 📞 緊急聯絡

### 技術支援團隊

**24/7 緊急支援**:
- 📧 Email: support@leo-satellite.com
- 📱 電話: +886-2-1234-5678
- 💬 Slack: #leo-satellite-support

**專業技術聯絡**:
- **系統架構師**: architect@leo-satellite.com
- **DevOps 工程師**: devops@leo-satellite.com  
- **數據工程師**: data@leo-satellite.com

### 升級路徑

```
Level 1: 基礎故障排除 (本指南)
    ↓ (無法解決)
Level 2: 技術支援團隊 (1-2 小時響應)
    ↓ (複雜問題)
Level 3: 專家團隊 (24 小時響應)
    ↓ (系統性問題)
Level 4: 架構師 + 外部專家 (48 小時響應)
```

---

## 📚 相關文檔

- [技術規範文檔](./tech.md)
- [配置管理指南](./configuration-management.md)
- [開發者上手指南](./developer-onboarding.md)
- [衛星數據架構](./satellite_data_architecture.md)
- [衛星換手仰角門檻標準](./satellite_handover_standards.md)

---

**最後更新**: 2025-08-03  
**維護團隊**: 技術支援 + 開發團隊  
**文檔版本**: 2.0.0 (Phase 2)
