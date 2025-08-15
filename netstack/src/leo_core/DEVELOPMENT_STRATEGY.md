# 🚀 LEO重構高效開發策略

**版本**: v1.0  
**更新日期**: 2025-08-15  
**目標**: 最大化開發效率，最小化重複建構時間

## 🎯 核心原則

### ⚡ 開發效率優先
- **避免重複建構**: 開發階段使用直接執行，減少映像檔建構次數
- **漸進式驗證**: 取樣 → 全量 → 映像檔建構的階段性驗證
- **自動清理機制**: 每次執行自動清理舊JSON，確保數據新鮮度
- **增量更新策略**: 智能檢測變更，僅處理必要的重計算

---

## 📋 4階段漸進式開發流程

### 🔧 Stage D1: 快速取樣開發 (2-5分鐘/次)
**目標**: 快速驗證核心邏輯，使用最小數據集

```bash
# 執行環境: Host 直接執行 (非容器)
cd /home/sat/ntn-stack/leo_restructure

# 超快速取樣模式 (10顆衛星，30分鐘時間範圍)
python run_phase1.py --ultra-fast \
  --satellites-limit 10 \
  --time-range 30 \
  --iterations 50 \
  --auto-cleanup

# 預期執行時間: 30-60秒
# 用途: 邏輯驗證、算法調試、介面測試
```

**Stage D1 配置**:
```python
# shared_core/dev_config.py
DEVELOPMENT_CONFIG = {
    'ultra_fast_mode': {
        'starlink_sample': 5,      # 僅5顆Starlink
        'oneweb_sample': 5,        # 僅5顆OneWeb  
        'time_range_minutes': 30,  # 30分鐘時間範圍
        'time_interval_seconds': 60, # 1分鐘間隔
        'max_iterations': 50,      # SA算法50次迭代
        'skip_complex_analysis': True, # 跳過複雜分析
        'output_dir': '/tmp/dev_stage1_outputs'
    }
}
```

**自動清理機制**:
```python
class AutoCleanupManager:
    """自動清理管理器"""
    
    def __init__(self, output_dir):
        self.output_dir = Path(output_dir)
        
    def cleanup_before_run(self):
        """執行前清理舊數據"""
        if self.output_dir.exists():
            for json_file in self.output_dir.glob("*.json"):
                json_file.unlink()
                print(f"🧹 已清理舊檔案: {json_file.name}")
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        print(f"✅ 輸出目錄已準備: {self.output_dir}")
```

---

### 🎯 Stage D2: 中型數據驗證 (5-10分鐘/次)
**目標**: 使用中等規模數據驗證系統穩定性和性能

```bash
# 中型取樣模式 (100顆衛星，96分鐘完整軌道週期)
python run_phase1.py --dev-mode \
  --satellites-limit 100 \
  --time-range 96 \
  --iterations 500 \
  --auto-cleanup \
  --enable-signal-analysis

# 預期執行時間: 3-5分鐘
# 用途: 性能測試、算法調優、事件檢測驗證
```

**Stage D2 配置**:
```python
DEVELOPMENT_CONFIG = {
    'dev_mode': {
        'starlink_sample': 50,      # 50顆Starlink
        'oneweb_sample': 50,        # 50顆OneWeb
        'time_range_minutes': 96,   # 完整軌道週期
        'time_interval_seconds': 30, # 標準30秒間隔
        'max_iterations': 500,      # SA算法500次迭代
        'enable_signal_analysis': True, # 啟用信號分析
        'enable_handover_events': True, # 啟用換手事件
        'output_dir': '/tmp/dev_stage2_outputs'
    }
}
```

**性能監控**:
```python
class PerformanceMonitor:
    """開發階段性能監控"""
    
    def monitor_stage_performance(self, stage_name, start_time, end_time):
        duration = end_time - start_time
        
        benchmarks = {
            'ultra_fast': 60,    # 1分鐘基準
            'dev_mode': 300,     # 5分鐘基準
            'full_sample': 600,  # 10分鐘基準
            'production': 1800   # 30分鐘基準
        }
        
        benchmark = benchmarks.get(stage_name, 300)
        
        if duration <= benchmark:
            print(f"✅ {stage_name} 性能達標: {duration:.1f}s ≤ {benchmark}s")
        else:
            print(f"⚠️ {stage_name} 性能警告: {duration:.1f}s > {benchmark}s")
```

---

### 🌍 Stage D3: 全量數據驗證 (10-20分鐘/次)
**目標**: 使用完整數據驗證最終效果，但仍在Host環境執行

```bash
# 全量數據模式 (8,736顆衛星，200分鐘時間範圍)
python run_phase1.py --full-test \
  --auto-cleanup \
  --enable-all-features \
  --performance-monitoring

# 預期執行時間: 10-15分鐘
# 用途: 最終驗證、性能基準、完整功能測試
```

**Stage D3 配置**:
```python
DEVELOPMENT_CONFIG = {
    'full_test': {
        'use_all_satellites': True,   # 使用全部8,736顆衛星
        'time_range_minutes': 200,    # 完整200分鐘
        'time_interval_seconds': 30,  # 標準間隔
        'max_iterations': 5000,       # SA算法完整迭代
        'enable_all_features': True,  # 啟用所有功能
        'output_dir': '/tmp/dev_stage3_outputs',
        'performance_logging': True,  # 性能日誌
        'memory_monitoring': True     # 記憶體監控
    }
}
```

**記憶體監控**:
```python
import psutil
import gc

class MemoryMonitor:
    """記憶體使用監控"""
    
    def __init__(self):
        self.initial_memory = psutil.virtual_memory().used
        
    def check_memory_usage(self, stage_name):
        current_memory = psutil.virtual_memory().used
        memory_increase = (current_memory - self.initial_memory) / 1024 / 1024  # MB
        
        if memory_increase > 2048:  # 2GB 警告線
            print(f"⚠️ {stage_name} 記憶體使用過高: {memory_increase:.1f}MB")
            gc.collect()  # 強制垃圾回收
        else:
            print(f"✅ {stage_name} 記憶體使用正常: {memory_increase:.1f}MB")
```

---

### 🐳 Stage D4: 容器映像檔驗證 (20-30分鐘/次)
**目標**: 最終容器環境驗證，確保生產環境一致性

```bash
# 容器建構驗證 (僅在前三階段全部通過後執行)
# 1. 清理舊映像檔
make clean-i

# 2. 建構新映像檔
make build-n

# 3. 完整系統測試
make up && make status

# 4. API和前端驗證
curl http://localhost:8080/health
curl http://localhost:8080/api/v1/satellites/positions

# 預期執行時間: 20-30分鐘 (包含建構+測試)
# 用途: 生產環境驗證、最終集成測試
```

**容器驗證腳本**:
```bash
#!/bin/bash
# container_validation.sh

echo "🐳 Stage D4: 容器映像檔驗證開始..."

# 1. 自動清理舊數據
echo "🧹 清理舊容器數據..."
docker volume rm compose_satellite_precomputed_data 2>/dev/null || true
docker system prune -f

# 2. 建構驗證
echo "🔨 開始映像檔建構..."
start_time=$(date +%s)
make build-n
build_status=$?
end_time=$(date +%s)
build_duration=$((end_time - start_time))

if [ $build_status -eq 0 ]; then
    echo "✅ 映像檔建構成功 (${build_duration}秒)"
else
    echo "❌ 映像檔建構失敗"
    exit 1
fi

# 3. 啟動驗證
echo "🚀 開始容器啟動測試..."
start_time=$(date +%s)
make up
while ! curl -s http://localhost:8080/health > /dev/null 2>&1; do
    sleep 2
done
end_time=$(date +%s)
startup_duration=$((end_time - start_time))

if [ $startup_duration -lt 30 ]; then
    echo "✅ 容器啟動成功 (${startup_duration}秒)"
else
    echo "⚠️ 容器啟動較慢 (${startup_duration}秒)"
fi

echo "🎉 Stage D4 容器驗證完成！"
```

---

## 🧹 自動清理系統

### 智能清理策略
```python
class IntelligentCleanup:
    """智能數據清理系統"""
    
    def __init__(self):
        self.cleanup_patterns = {
            # 開發階段輸出
            'dev_outputs': [
                '/tmp/dev_stage*_outputs/*.json',
                '/tmp/phase1_outputs/*.json'
            ],
            # 容器數據
            'container_data': [
                '/app/data/stage*.json',
                '/app/data/*_results.json'
            ],
            # 臨時快取
            'temp_cache': [
                '/tmp/tle_cache/*.tle',
                '/tmp/sgp4_cache/*.pkl'
            ]
        }
    
    def cleanup_before_run(self, mode='dev_outputs'):
        """執行前智能清理"""
        patterns = self.cleanup_patterns.get(mode, [])
        cleaned_files = 0
        
        for pattern in patterns:
            for file_path in glob.glob(pattern):
                try:
                    os.remove(file_path)
                    cleaned_files += 1
                    print(f"🧹 已清理: {file_path}")
                except Exception as e:
                    print(f"⚠️ 清理失敗: {file_path} - {e}")
        
        if cleaned_files > 0:
            print(f"✅ 清理完成，共清理 {cleaned_files} 個檔案")
        else:
            print("📝 無舊檔案需要清理")
    
    def cleanup_by_age(self, hours=24):
        """按時間清理舊檔案"""
        cutoff_time = time.time() - (hours * 3600)
        
        for pattern in self.cleanup_patterns['dev_outputs']:
            for file_path in glob.glob(pattern):
                if os.path.getmtime(file_path) < cutoff_time:
                    os.remove(file_path)
                    print(f"🕒 清理過期檔案: {file_path}")
```

---

## 📈 增量更新策略

### 智能變更檢測
```python
class IncrementalUpdateManager:
    """增量更新管理器"""
    
    def __init__(self):
        self.change_detection_file = '/tmp/leo_change_tracking.json'
        self.last_update_info = self._load_last_update()
    
    def detect_changes(self):
        """檢測系統變更"""
        changes = {
            'tle_data_updated': self._check_tle_updates(),
            'code_modified': self._check_code_changes(),
            'config_changed': self._check_config_changes(),
            'force_full_rebuild': self._check_force_rebuild()
        }
        
        return changes
    
    def _check_tle_updates(self):
        """檢查TLE數據更新"""
        tle_files = [
            '/home/sat/ntn-stack/netstack/tle_data/starlink/tle/starlink_*.tle',
            '/home/sat/ntn-stack/netstack/tle_data/oneweb/tle/oneweb_*.tle'
        ]
        
        latest_tle_time = 0
        for pattern in tle_files:
            for file_path in glob.glob(pattern):
                file_time = os.path.getmtime(file_path)
                latest_tle_time = max(latest_tle_time, file_time)
        
        last_tle_time = self.last_update_info.get('tle_update_time', 0)
        return latest_tle_time > last_tle_time
    
    def _check_code_changes(self):
        """檢查代碼變更"""
        code_dirs = [
            '/home/sat/ntn-stack/leo_restructure/phase1_core_system',
            '/home/sat/ntn-stack/leo_restructure/shared_core'
        ]
        
        latest_code_time = 0
        for code_dir in code_dirs:
            for py_file in Path(code_dir).rglob('*.py'):
                file_time = os.path.getmtime(py_file)
                latest_code_time = max(latest_code_time, file_time)
        
        last_code_time = self.last_update_info.get('code_update_time', 0)
        return latest_code_time > last_code_time
    
    def suggest_update_strategy(self, changes):
        """建議更新策略"""
        if changes['force_full_rebuild']:
            return 'full_rebuild'
        elif changes['tle_data_updated']:
            return 'tle_incremental'
        elif changes['code_modified']:
            return 'code_incremental'
        elif changes['config_changed']:
            return 'config_incremental'
        else:
            return 'no_update_needed'
    
    def execute_incremental_update(self, strategy):
        """執行增量更新"""
        strategies = {
            'tle_incremental': self._update_tle_data_only,
            'code_incremental': self._update_code_only,
            'config_incremental': self._update_config_only,
            'full_rebuild': self._full_rebuild
        }
        
        update_func = strategies.get(strategy)
        if update_func:
            print(f"🔄 執行增量更新策略: {strategy}")
            return update_func()
        else:
            print("📝 無需更新")
            return True
    
    def _update_tle_data_only(self):
        """僅更新TLE數據"""
        print("📡 僅重新處理TLE數據...")
        # 只執行F1_TLE_Loader，保留其他緩存結果
        # 預期時間: 2-3分鐘
        pass
    
    def _update_code_only(self):
        """僅更新代碼邏輯"""
        print("💻 僅重新執行代碼邏輯...")
        # 保留TLE計算結果，重新執行篩選和優化
        # 預期時間: 1-2分鐘
        pass
```

---

## 🕒 Cron增量更新整合

### 智能Cron調度
```bash
#!/bin/bash
# intelligent_cron_update.sh

echo "🕒 開始智能增量更新檢查..."

cd /home/sat/ntn-stack/leo_restructure

# 1. 檢測變更
python -c "
from shared_core.incremental_manager import IncrementalUpdateManager
manager = IncrementalUpdateManager()
changes = manager.detect_changes()
strategy = manager.suggest_update_strategy(changes)
print(f'UPDATE_STRATEGY={strategy}')
" > /tmp/update_strategy.env

source /tmp/update_strategy.env

# 2. 根據策略執行更新
case $UPDATE_STRATEGY in
    "no_update_needed")
        echo "📝 無需更新，系統數據為最新"
        ;;
    "tle_incremental")
        echo "📡 執行TLE增量更新..."
        python run_phase1.py --incremental --tle-only --auto-cleanup
        ;;
    "code_incremental")
        echo "💻 執行代碼增量更新..."
        python run_phase1.py --incremental --code-only --auto-cleanup
        ;;
    "full_rebuild")
        echo "🔄 執行完整重建..."
        python run_phase1.py --full-test --auto-cleanup
        ;;
    *)
        echo "⚠️ 未知更新策略: $UPDATE_STRATEGY"
        ;;
esac

echo "✅ 智能增量更新完成"
```

**Cron設定**:
```bash
# 智能增量更新 (每2小時檢查一次)
0 */2 * * * /home/sat/ntn-stack/leo_restructure/intelligent_cron_update.sh >> /tmp/intelligent_update.log 2>&1

# TLE數據更新檢查 (每6小時)
0 2,8,14,20 * * * /home/sat/ntn-stack/scripts/daily_tle_download_enhanced.sh >> /tmp/tle_download.log 2>&1

# 完整系統更新 (每週日凌晨3點)
0 3 * * 0 cd /home/sat/ntn-stack && make down-v && make build-n && make up >> /tmp/weekly_rebuild.log 2>&1
```

---

## 📊 開發效率對比

| 開發階段 | 執行時間 | 數據規模 | 用途 | 頻率 |
|---------|---------|---------|------|------|
| **Stage D1** | 30-60秒 | 10顆衛星 | 邏輯驗證 | 每次修改 |
| **Stage D2** | 3-5分鐘 | 100顆衛星 | 性能測試 | 功能完成 |
| **Stage D3** | 10-15分鐘 | 8,736顆衛星 | 最終驗證 | 每日一次 |
| **Stage D4** | 20-30分鐘 | 完整容器 | 生產驗證 | 每週一次 |

**效率提升**:
- 日常開發: 從30分鐘 → 1分鐘 (30倍提升)
- 功能測試: 從30分鐘 → 5分鐘 (6倍提升)  
- 週期性驗證: 保持完整測試覆蓋

---

## 🎯 實施建議

### 立即採用策略
1. **Phase 0 執行前**: 先用 Stage D1 驗證基本功能
2. **開發迭代**: 主要使用 Stage D1 + D2
3. **階段完成**: Stage D3 完整驗證
4. **生產部署**: Stage D4 最終確認

### 工具整合
```bash
# 創建開發別名
alias leo-dev='python run_phase1.py --ultra-fast --auto-cleanup'
alias leo-test='python run_phase1.py --dev-mode --auto-cleanup' 
alias leo-full='python run_phase1.py --full-test --auto-cleanup'
alias leo-build='make down-v && make build-n && make up'

# 一鍵開發流程
alias leo-workflow='leo-dev && leo-test && leo-full && leo-build'
```

這個策略將大幅提升開發效率，讓你可以快速迭代驗證，只在必要時才進行耗時的完整建構！

---

## 🔗 文檔整合狀態

### ✅ 已整合到主要文檔
- **README.md**: ✅ 已添加"4階段漸進式開發工作流程"章節
- **DEVELOPMENT_STRATEGY.md**: ✅ 本文檔 (詳細技術實施)
- **DEVELOPMENT_WORKFLOW_IMPLEMENTATION.md**: ✅ 實施完成報告

### 📁 實施檔案清單
- ✅ `run_phase1.py` - 增強版執行器 (支援D1-D4模式)
- ✅ `shared_core/auto_cleanup_manager.py` - 智能清理系統
- ✅ `shared_core/incremental_update_manager.py` - 增量更新系統
- ✅ `setup_dev_aliases.sh` - 一鍵安裝開發工具
- ✅ `intelligent_cron_update.sh` - 智能Cron調度

### 🎯 立即使用指南
用戶現在可以通過 README.md 中的新章節快速開始使用：

1. **安裝**: `./setup_dev_aliases.sh && source ~/.bashrc`
2. **快速體驗**: `leo-dev` (30秒)
3. **查看幫助**: `leo-help`
4. **日常開發**: `leo-dev` → `leo-test` → `leo-full`

這個完整的工作流程已經從概念設計成功轉化為可立即使用的開發工具！