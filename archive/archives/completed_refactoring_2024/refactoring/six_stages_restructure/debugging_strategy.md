# 六階段重構除錯策略

## 🎯 除錯能力革命性提升

### 核心優勢
重構後的模組化架構將除錯能力從「**不可能**」提升到「**精確定位**」，這是本次重構最重要的實用價值。

### 現狀 vs 重構後對比
```
現狀問題：
❌ Stage 5 (3,400行) 出錯，無法快速定位問題
❌ 必須執行完整六階段才能發現錯誤  
❌ 錯誤影響整個流程，難以隔離
❌ 無法注入測試數據進行局部驗證

重構後能力：
✅ 精確定位到具體模組和函數
✅ 可單獨執行任何階段或模組
✅ 錯誤完全隔離，不影響其他部分
✅ 靈活的數據注入和測試能力
```

## 🔧 分階段除錯功能設計

### 1. 單階段執行除錯

#### 核心工具：
```python
# netstack/src/pipeline/scripts/run_single_stage.py

import argparse
import json
import logging
from pathlib import Path
from pipeline.shared.pipeline_coordinator import PipelineCoordinator

class SingleStageDebugger:
    """單階段除錯工具"""
    
    def __init__(self, stage_number: int, debug_level: str = 'INFO'):
        self.stage_number = stage_number
        self.setup_logging(debug_level)
        self.coordinator = PipelineCoordinator()
    
    def execute_stage_only(self, input_file: str = None, output_dir: str = None):
        """只執行指定階段"""
        print(f"🔍 開始除錯 Stage {self.stage_number}")
        
        # 載入輸入數據
        if input_file:
            with open(input_file, 'r') as f:
                input_data = json.load(f)
            print(f"📥 已載入輸入數據: {input_file}")
        else:
            # 從前一階段載入標準輸出
            input_data = self.load_previous_stage_output()
        
        # 執行單階段
        try:
            result = self.coordinator.execute_single_stage(
                self.stage_number, 
                input_data,
                debug_mode=True
            )
            
            # 保存結果  
            if output_dir:
                output_file = Path(output_dir) / f"stage{self.stage_number}_debug_output.json"
                with open(output_file, 'w') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                print(f"💾 結果已保存: {output_file}")
            
            print(f"✅ Stage {self.stage_number} 除錯成功完成")
            return result
            
        except Exception as e:
            print(f"❌ Stage {self.stage_number} 執行失敗: {e}")
            self.print_debug_info(e)
            raise

# 命令行使用
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='單階段除錯工具')
    parser.add_argument('--stage', type=int, required=True, help='階段編號 (1-6)')
    parser.add_argument('--input', help='輸入數據文件路徑')
    parser.add_argument('--output-dir', help='輸出目錄')
    parser.add_argument('--debug', default='INFO', help='除錯等級 (DEBUG/INFO/WARNING)')
    
    args = parser.parse_args()
    
    debugger = SingleStageDebugger(args.stage, args.debug)
    debugger.execute_stage_only(args.input, args.output_dir)
```

#### 使用範例
```bash
# 只執行Stage 5，使用Stage 4的輸出
python -m pipeline.scripts.run_single_stage --stage=5 --debug=DEBUG

# 使用自定義測試數據
python -m pipeline.scripts.run_single_stage --stage=5 --input=test_data.json --output-dir=/tmp/debug

# 執行Stage 3到Stage 5
python -m pipeline.scripts.run_pipeline_range --start=3 --end=5 --debug=DEBUG
```

### 2. 模組級除錯

#### 核心工具：
```python
# netstack/src/pipeline/scripts/debug_module.py

class ModuleDebugger:
    """模組級除錯工具"""
    
    def debug_stage5_data_merger(self, test_data: dict):
        """除錯Stage 5的data_merger模組"""
        from pipeline.stages.stage5_data_integration.data_merger import DataMerger
        
        print("🔍 開始除錯 Stage5.DataMerger")
        
        # 啟用除錯模式
        merger = DataMerger(debug_mode=True)
        
        # 設置詳細日誌
        logging.getLogger('Stage5.DataMerger').setLevel(logging.DEBUG)
        
        try:
            # 逐步執行並監控
            print("📊 輸入數據統計:")
            print(f"  - Starlink衛星: {len(test_data.get('starlink', []))}")
            print(f"  - OneWeb衛星: {len(test_data.get('oneweb', []))}")
            
            # 執行合併
            result = merger.merge_satellite_data(test_data)
            
            # 詳細結果分析
            print("📈 合併結果統計:")
            print(f"  - 總計衛星: {len(result.get('satellites', []))}")
            print(f"  - 數據完整性: {result.get('completeness_score', 0):.2f}")
            print(f"  - 處理時間: {result.get('processing_time', 0):.2f} 秒")
            
            # 檢查潛在問題
            self.analyze_merge_quality(result)
            
            return result
            
        except Exception as e:
            print(f"❌ DataMerger除錯失敗: {e}")
            self.print_merger_debug_info(merger, test_data, e)
            raise
    
    def analyze_merge_quality(self, result: dict):
        """分析合併質量"""
        issues = []
        
        # 檢查數據一致性
        satellites = result.get('satellites', [])
        for sat in satellites:
            if not sat.get('tle_data'):
                issues.append(f"衛星 {sat.get('name')} 缺少 TLE 數據")
            
            if sat.get('signal_quality', 0) < 0.5:
                issues.append(f"衛星 {sat.get('name')} 信號質量偏低: {sat.get('signal_quality')}")
        
        # 報告問題
        if issues:
            print("⚠️  發現數據質量問題:")
            for issue in issues:
                print(f"   - {issue}")
        else:
            print("✅ 數據質量檢查通過")

# 互動式使用
if __name__ == "__main__":
    debugger = ModuleDebugger()
    
    # 載入測試數據
    with open('stage4_output.json', 'r') as f:
        test_data = json.load(f)
    
    # 除錯特定模組
    result = debugger.debug_stage5_data_merger(test_data)
```

### 3. 數據注入除錯

#### 核心功能：標準化數據接口
```python
# netstack/src/pipeline/shared/debug_data_injector.py

class DebugDataInjector:
    """數據注入除錯工具"""
    
    def create_stage_test_data(self, stage_number: int, scenario: str = 'normal'):
        """創建特定階段的測試數據"""
        
        if stage_number == 5:
            return self.create_stage5_test_data(scenario)
        elif stage_number == 6:
            return self.create_stage6_test_data(scenario)
        # ... 其他階段
    
    def create_stage5_test_data(self, scenario: str):
        """創建Stage 5測試數據"""
        base_data = {
            "data": {
                "starlink": [
                    {
                        "satellite_id": "STARLINK-1234",
                        "name": "Starlink-1234",
                        "tle_data": {
                            "tle_line1": "1 44713U 19074A   21275.91667824  .00001874  00000-0  13717-3 0  9995",
                            "tle_line2": "2 44713  53.0000 123.4567   0.0013 269.3456 162.7890 15.05000000123456"
                        },
                        "orbital_positions": [...],  # 192個位置點
                        "signal_quality": 0.85
                    }
                    # ... 更多Starlink衛星
                ],
                "oneweb": [
                    # ... OneWeb衛星數據
                ]
            },
            "metadata": {
                "stage_number": 4,
                "stage_name": "signal_analysis", 
                "processing_timestamp": "2021-10-02T10:30:00Z",
                "total_records": 1500,
                "data_format_version": "unified_v1.2_phase3"
            }
        }
        
        # 根據測試場景調整數據
        if scenario == 'error':
            # 注入錯誤數據用於測試錯誤處理
            base_data['data']['starlink'][0]['tle_data'] = None  # 缺少TLE數據
        elif scenario == 'performance':
            # 大量數據用於性能測試
            base_data['data']['starlink'] *= 100  # 放大100倍
        
        return base_data

# 使用範例
injector = DebugDataInjector()

# 測試正常情況
normal_data = injector.create_stage5_test_data('normal')
stage5_result = stage5_processor.execute(normal_data)

# 測試錯誤情況  
error_data = injector.create_stage5_test_data('error')
try:
    stage5_result = stage5_processor.execute(error_data)
except Exception as e:
    print(f"錯誤處理測試通過: {e}")
```

### 4. 性能分析除錯

#### 核心工具：
```python
# netstack/src/pipeline/scripts/performance_profiler.py

import time
import psutil
import cProfile
import pstats
from contextlib import contextmanager

class PerformanceProfiler:
    """性能分析工具"""
    
    @contextmanager
    def profile_stage(self, stage_number: int, module_name: str = None):
        """性能分析上下文管理器"""
        
        # 記錄開始狀態
        start_time = time.time()
        process = psutil.Process()
        start_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 開始CPU profiling
        profiler = cProfile.Profile()
        profiler.enable()
        
        try:
            yield
        finally:
            # 停止profiling
            profiler.disable()
            
            # 計算性能指標
            end_time = time.time()
            end_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            duration = end_time - start_time
            memory_used = end_memory - start_memory
            
            # 輸出性能報告
            print(f"\n📊 性能分析報告 - Stage {stage_number} {module_name or ''}:")
            print(f"   ⏱️  執行時間: {duration:.2f} 秒")
            print(f"   🧠 記憶體使用: {memory_used:.1f} MB")
            
            # 詳細CPU分析
            stats = pstats.Stats(profiler)
            stats.sort_stats('cumulative')
            
            print(f"\n🔥 最耗時的10個函數:")
            stats.print_stats(10)

# 使用範例
profiler = PerformanceProfiler()

# 分析整個Stage 5
with profiler.profile_stage(5):
    result = stage5_processor.execute(test_data)

# 分析特定模組
with profiler.profile_stage(5, 'DataMerger'):
    merger = DataMerger()
    result = merger.merge_satellite_data(test_data)
```

### 5. 實時監控除錯

#### 核心工具：
```python
# netstack/src/pipeline/scripts/debug_monitor.py

class DebugMonitor:
    """實時除錯監控"""
    
    def monitor_pipeline_execution(self, stages: list = None):
        """監控管道執行狀態"""
        stages = stages or list(range(1, 7))
        
        print("🖥️  開始實時監控管道執行...")
        
        for stage_num in stages:
            print(f"\n📡 監控 Stage {stage_num}:")
            
            # 監控執行狀態
            self.monitor_stage_status(stage_num)
            
            # 監控資源使用
            self.monitor_resource_usage(stage_num)
            
            # 監控錯誤日誌
            self.monitor_error_logs(stage_num)
    
    def monitor_stage_status(self, stage_number: int):
        """監控階段執行狀態"""
        status_file = f"/app/data/stage{stage_number}_status.json"
        
        if Path(status_file).exists():
            with open(status_file, 'r') as f:
                status = json.load(f)
            
            print(f"   ✅ 狀態: {status.get('status', 'unknown')}")
            print(f"   ⏱️  進度: {status.get('progress', 0):.1f}%")
            print(f"   📊 處理記錄: {status.get('processed_records', 0)}")
        else:
            print(f"   ⏸️  尚未開始執行")
    
    def watch_stage_logs(self, stage_number: int):
        """實時監控階段日誌"""
        import subprocess
        
        log_file = f"/app/logs/stage{stage_number}.log"
        
        if Path(log_file).exists():
            print(f"🔍 實時監控 Stage {stage_number} 日誌:")
            
            # 使用tail -f監控日誌
            process = subprocess.Popen(['tail', '-f', log_file], 
                                     stdout=subprocess.PIPE, 
                                     stderr=subprocess.PIPE, 
                                     text=True)
            
            try:
                for line in process.stdout:
                    if 'ERROR' in line:
                        print(f"❌ {line.strip()}")
                    elif 'WARNING' in line:
                        print(f"⚠️  {line.strip()}")
                    elif 'INFO' in line:
                        print(f"ℹ️  {line.strip()}")
                        
            except KeyboardInterrupt:
                process.terminate()
                print(f"\n⏹️  停止監控 Stage {stage_number}")

# 使用範例
monitor = DebugMonitor()

# 監控所有階段
monitor.monitor_pipeline_execution()

# 實時監控特定階段
monitor.watch_stage_logs(5)
```

## 🎯 除錯工具實施計劃

### Phase 1: 基礎除錯工具 (第8-10天)

#### 第8天: 單階段執行工具
- 實施 
- 實施 
- 測試單階段執行功能

#### 第9天: 模組級除錯工具
- 實施 
- 實施 
- 創建測試數據生成器

#### 第10天: 性能分析工具
- 實施 
- 實施 
- 整合所有除錯工具

### Phase 2: 進階除錯功能 (隨各階段重構)

#### Stage 1 重構時
- 實施 Stage 1 專用除錯工具
- 建立除錯數據集
- 驗證除錯功能可用性

#### 後續階段
- 為每個重構階段建立專用除錯工具
- 累積除錯案例和最佳實踐
- 持續優化除錯體驗

## 📚 除錯使用指南

### 常見除錯場景

#### 場景1: Stage 5處理時間過長
```bash
# 1. 性能分析
python -m pipeline.scripts.performance_profiler --stage=5

# 2. 模組級分析
python -m pipeline.scripts.debug_module --stage=5 --module=data_merger

# 3. 數據量分析
python -c "
from debug_data_injector import DebugDataInjector
injector = DebugDataInjector()
small_data = injector.create_stage5_test_data('small')
# 用小數據集測試是否仍然慢
"
```

#### 場景2: 數據格式錯誤
```bash
# 1. 檢查輸入數據格式
python -m pipeline.scripts.validate_data_format --stage=5 --input=stage4_output.json

# 2. 注入標準測試數據
python -c "
from debug_data_injector import DebugDataInjector
injector = DebugDataInjector()
standard_data = injector.create_stage5_test_data('normal')
# 測試標準數據是否正常處理
"

# 3. 逐模組檢查
python -m pipeline.scripts.debug_module --stage=5 --module=validator
```

#### 場景3: 間歇性錯誤
```bash
# 1. 實時監控執行
python -m pipeline.scripts.debug_monitor --stage=5 --watch-logs

# 2. 多次執行測試
for i in {1..10}; do
  python -m pipeline.scripts.run_single_stage --stage=5
  if [ 127 -ne 0 ]; then
    echo "第  次執行失敗"
    break
  fi
done

# 3. 保存每次執行的狀態
python -m pipeline.scripts.run_single_stage --stage=5 --save-debug-state
```

## 🚀 除錯效益預期

### 開發效率提升
- **問題定位時間**: 從數小時縮短到數分鐘
- **修復驗證時間**: 從完整測試縮短到局部驗證
- **學習曲線**: 新人可快速理解各模組功能

### 系統穩定性提升
- **錯誤隔離**: 問題不會影響整個系統
- **漸進修復**: 可逐模組修復，不影響其他功能
- **預防性除錯**: 可提前發現潛在問題

### 維護成本降低
- **精確修復**: 只需要修改有問題的模組
- **影響評估**: 清楚知道修改的影響範圍
- **測試效率**: 可針對性測試修改的部分

---

**重要**: 這套除錯功能將使重構後的系統除錯能力從「幾乎不可能」提升到「精確高效」，是本次重構最重要的實用價值。
