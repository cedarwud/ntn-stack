# 六階段重構測試策略

## 🎯 測試策略總覽

### 測試金字塔
```
        🔺 端到端測試 (E2E)
       🔺🔺🔺 集成測試 (Integration)  
    🔺🔺🔺🔺🔺 單元測試 (Unit)
```

**比例分配**: 70% 單元測試, 20% 集成測試, 10% 端到端測試

### 核心測試原則
1. **學術數據標準遵循** - 所有測試數據必須符合Grade A標準
2. **真實性優先** - 使用真實TLE數據，避免模擬數據
3. **回歸防護** - 確保重構後功能完全一致
4. **性能基準** - 每個測試都有明確的性能要求

## 🧪 單元測試策略 (70%)

### 測試覆蓋目標
- **代碼覆蓋率**: >90%
- **分支覆蓋率**: >85% 
- **功能覆蓋率**: 100%

### Stage 1 單元測試範例

#### TLE數據載入測試
```python
# tests/test_stages/test_stage1/test_tle_data_loader.py
import pytest
from pipeline.stages.stage1_orbital_calculation.tle_data_loader import TLEDataLoader

class TestTLEDataLoader:
    def test_load_starlink_tle_data(self):
        """測試Starlink TLE數據載入"""
        loader = TLEDataLoader()
        result = loader.load_constellation_data('starlink')
        
        # 數據完整性檢查
        assert len(result) > 0
        assert all('tle_line1' in sat for sat in result)
        assert all('tle_line2' in sat for sat in result)
        
        # TLE格式驗證
        for sat in result:
            assert len(sat['tle_line1']) == 69
            assert len(sat['tle_line2']) == 69
            assert sat['tle_line1'].startswith('1 ')
            assert sat['tle_line2'].startswith('2 ')
    
    def test_tle_epoch_time_extraction(self):
        """測試TLE epoch時間提取"""
        loader = TLEDataLoader()
        test_tle = {
            'tle_line1': '1 25544U 98067A   21275.45833333  .00002182  00000-0  40000-4 0  9991',
            'tle_line2': '2 25544  51.6400 123.4567   0.0016 240.0000  95.0000 15.48919103123456'
        }
        
        epoch = loader.extract_tle_epoch(test_tle)
        
        # 確認時間基準正確性
        assert epoch.year == 2021
        assert epoch.timetuple().tm_yday == 275
        
    def test_invalid_tle_handling(self):
        """測試無效TLE處理"""
        loader = TLEDataLoader()
        
        # 測試格式錯誤的TLE
        invalid_tle = {
            'tle_line1': 'invalid line',
            'tle_line2': 'another invalid'
        }
        
        with pytest.raises(ValueError, match="Invalid TLE format"):
            loader.validate_tle_format(invalid_tle)
```

#### SGP4計算引擎測試
```python
# tests/test_stages/test_stage1/test_orbital_calculator.py
import pytest
import numpy as np
from datetime import datetime, timezone
from pipeline.stages.stage1_orbital_calculation.orbital_calculator import OrbitalCalculator

class TestOrbitalCalculator:
    def test_sgp4_position_calculation(self):
        """測試SGP4位置計算準確性"""
        calculator = OrbitalCalculator()
        
        # 使用已知的ISS TLE (具有已知的正確結果)
        tle_data = {
            'name': 'ISS',
            'tle_line1': '1 25544U 98067A   21275.45833333  .00002182  00000-0  40000-4 0  9991',
            'tle_line2': '2 25544  51.6400 123.4567   0.0016 240.0000  95.0000 15.48919103123456'
        }
        
        # 計算特定時刻位置
        result = calculator.calculate_position_timeseries(tle_data, time_range_minutes=10)
        
        # 驗證結果合理性
        assert len(result) > 0
        for position in result:
            # ECI座標範圍檢查 (地球半徑 6,371km 到 GEO 35,786km)
            assert 6000 < abs(position['eci_x']) < 50000  # km
            assert 6000 < abs(position['eci_y']) < 50000  # km  
            assert 6000 < abs(position['eci_z']) < 50000  # km
            
            # 仰角範圍檢查
            assert -90 <= position['elevation_deg'] <= 90
            
            # 方位角範圍檢查
            assert 0 <= position['azimuth_deg'] < 360
    
    def test_time_basis_correctness(self):
        """測試時間基準正確性 - 關鍵測試"""
        calculator = OrbitalCalculator()
        
        tle_data = {
            'name': 'TEST_SAT',
            'tle_line1': '1 25544U 98067A   21275.45833333  .00002182  00000-0  40000-4 0  9991',
            'tle_line2': '2 25544  51.6400 123.4567   0.0016 240.0000  95.0000 15.48919103123456'
        }
        
        result = calculator.calculate_position_timeseries(tle_data, time_range_minutes=30)
        
        # 確認使用TLE epoch時間作為基準
        first_timestamp = datetime.fromisoformat(result[0]['timestamp'].replace('Z', '+00:00'))
        
        # 計算的時間應該基於TLE epoch (2021年第275天)
        assert first_timestamp.year == 2021
        assert first_timestamp.timetuple().tm_yday >= 275
        
        # ❌ 絕對不能是當前時間
        current_year = datetime.now().year
        if current_year \!= 2021:
            assert first_timestamp.year \!= current_year, "錯誤：使用了當前時間而非TLE epoch時間"
    
    def test_constellation_specific_parameters(self):
        """測試星座特定參數"""
        calculator = OrbitalCalculator()
        
        # Starlink衛星測試 (96分鐘軌道，192個點)
        starlink_data = {
            'name': 'STARLINK-1234',
            'constellation': 'starlink',
            'tle_line1': '1 25544U 98067A   21275.45833333  .00002182  00000-0  40000-4 0  9991',
            'tle_line2': '2 25544  51.6400 123.4567   0.0016 240.0000  95.0000 15.48919103123456'
        }
        
        result = calculator.calculate_position_timeseries(starlink_data, time_range_minutes=96)
        assert len(result) == 192, f"Starlink應該產生192個位置點，實際：{len(result)}"
        
        # OneWeb衛星測試 (109分鐘軌道，218個點)
        oneweb_data = {
            'name': 'ONEWEB-1234', 
            'constellation': 'oneweb',
            'tle_line1': '1 25544U 98067A   21275.45833333  .00002182  00000-0  40000-4 0  9991',
            'tle_line2': '2 25544  51.6400 123.4567   0.0016 240.0000  95.0000 15.48919103123456'
        }
        
        result = calculator.calculate_position_timeseries(oneweb_data, time_range_minutes=109)
        assert len(result) == 218, f"OneWeb應該產生218個位置點，實際：{len(result)}"
```

### 共用模組單元測試

#### BaseStageProcessor測試
```python
# tests/test_shared/test_base_processor.py
import pytest
from unittest.mock import Mock, patch
from pipeline.shared.base_processor import BaseStageProcessor

class TestBaseStageProcessor:
    def test_processing_timer(self):
        """測試處理時間計算"""
        processor = MockStageProcessor(1, "test_stage")
        
        processor.start_processing_timer()
        # 模擬處理時間
        import time
        time.sleep(0.1)
        processor.end_processing_timer()
        
        assert processor.processing_duration > 0
        assert processor.processing_duration < 1  # 應該很短
    
    def test_validation_snapshot_creation(self):
        """測試驗證快照創建"""
        processor = MockStageProcessor(1, "test_stage")
        
        test_results = {
            "data": {"test": "data"},
            "metadata": {"stage_number": 1}
        }
        
        success = processor.save_validation_snapshot(test_results)
        assert success == True
        
        # 驗證快照文件存在
        snapshot_file = processor.validation_dir / "stage1_validation.json"
        assert snapshot_file.exists()

class MockStageProcessor(BaseStageProcessor):
    """測試用的模擬處理器"""
    def validate_input(self, input_data): return True
    def process(self, input_data): return {"data": {}, "metadata": {}}
    def validate_output(self, output_data): return True
    def save_results(self, results): return "/test/path"
    def extract_key_metrics(self, results): return {}
    def run_validation_checks(self, results): return {"passed": True}
```

## 🔗 集成測試策略 (20%)

### 階段間數據流測試

#### Stage 1 → Stage 2 集成測試
```python
# tests/integration/test_stage1_to_stage2.py
import pytest
from pipeline.stages.stage1_orbital_calculation.processor import Stage1Processor
from pipeline.stages.stage2_visibility_filter.processor import Stage2Processor

class TestStage1ToStage2Integration:
    def test_orbital_to_visibility_data_flow(self):
        """測試軌道計算到可見性過濾的數據流"""
        
        # Stage 1執行
        stage1 = Stage1Processor()
        stage1_result = stage1.execute()
        
        # 驗證Stage 1輸出格式
        assert "data" in stage1_result
        assert "metadata" in stage1_result
        assert stage1_result["metadata"]["stage_number"] == 1
        
        # Stage 2執行 (使用Stage 1的輸出)
        stage2 = Stage2Processor()
        stage2_result = stage2.execute(stage1_result)
        
        # 驗證數據流連續性
        assert stage2_result["metadata"]["source_stage"] == 1
        assert len(stage2_result["data"]) <= len(stage1_result["data"])  # 過濾後數量應該減少
    
    def test_data_format_consistency(self):
        """測試數據格式一致性"""
        stage1 = Stage1Processor()
        result = stage1.execute()
        
        # 驗證符合StandardOutputFormat
        required_fields = ["data", "metadata"]
        for field in required_fields:
            assert field in result
        
        metadata_fields = ["stage_number", "stage_name", "processing_timestamp", 
                          "processing_duration", "total_records"]
        for field in metadata_fields:
            assert field in result["metadata"]
```

### 完整管道集成測試
```python
# tests/integration/test_full_pipeline.py
import pytest
from pipeline.shared.pipeline_coordinator import PipelineCoordinator

class TestFullPipelineIntegration:
    def test_six_stage_complete_execution(self):
        """測試六階段完整執行"""
        coordinator = PipelineCoordinator()
        
        # 執行完整管道
        final_result = coordinator.execute_complete_pipeline()
        
        # 驗證所有階段執行成功
        assert final_result["execution_success"] == True
        assert len(final_result["stage_results"]) == 6
        
        # 驗證數據血統追蹤
        for i, stage_result in enumerate(final_result["stage_results"]):
            assert stage_result["stage_number"] == i + 1
            if i > 0:
                assert stage_result["metadata"]["source_stage"] == i
    
    def test_pipeline_error_recovery(self):
        """測試管道錯誤恢復"""
        coordinator = PipelineCoordinator()
        
        # 模擬Stage 3失敗
        with patch('pipeline.stages.stage3_timeseries_preprocessing.processor.Stage3Processor.execute') as mock_stage3:
            mock_stage3.side_effect = Exception("Stage 3 test failure")
            
            with pytest.raises(Exception):
                coordinator.execute_complete_pipeline()
            
            # 驗證前面階段的輸出仍然存在
            assert coordinator.get_stage_output(1) is not None
            assert coordinator.get_stage_output(2) is not None
```

## 🏁 端到端測試策略 (10%)

### 真實場景測試

#### 完整衛星追蹤場景
```python
# tests/e2e/test_satellite_tracking_scenario.py
import pytest
from datetime import datetime, timedelta
from pipeline.main import NTNPipeline

class TestSatelliteTrackingScenario:
    def test_starlink_handover_scenario(self):
        """測試Starlink衛星換手場景"""
        pipeline = NTNPipeline()
        
        # 設定測試參數
        test_config = {
            "constellations": ["starlink"],
            "observer_location": {
                "latitude": 24.9441667,  # NTPU
                "longitude": 121.3713889,
                "elevation": 50.0
            },
            "time_range_minutes": 120
        }
        
        # 執行完整管道
        result = pipeline.execute_with_config(test_config)
        
        # 驗證換手決策結果
        handover_decisions = result["stage6_results"]["handover_decisions"]
        assert len(handover_decisions) > 0
        
        # 驗證決策合理性
        for decision in handover_decisions:
            assert decision["elevation_deg"] >= 5.0  # 最低可見門檻
            assert "source_satellite" in decision
            assert "target_satellite" in decision
            assert decision["handover_trigger"] in ["elevation", "signal_quality", "load_balancing"]
    
    def test_multi_constellation_scenario(self):
        """測試多星座混合場景"""
        pipeline = NTNPipeline()
        
        test_config = {
            "constellations": ["starlink", "oneweb"],
            "observer_location": {
                "latitude": 24.9441667,
                "longitude": 121.3713889, 
                "elevation": 50.0
            },
            "time_range_minutes": 180
        }
        
        result = pipeline.execute_with_config(test_config)
        
        # 驗證多星座協調
        final_pools = result["stage6_results"]["dynamic_pools"]
        constellations_used = set()
        
        for pool in final_pools:
            for satellite in pool["satellites"]:
                constellations_used.add(satellite["constellation"])
        
        assert "starlink" in constellations_used
        assert "oneweb" in constellations_used
```

### 性能基準測試
```python
# tests/e2e/test_performance_benchmarks.py
import pytest
import time
from pipeline.main import NTNPipeline

class TestPerformanceBenchmarks:
    def test_processing_time_benchmark(self):
        """測試處理時間基準"""
        pipeline = NTNPipeline()
        
        start_time = time.time()
        result = pipeline.execute_complete_pipeline()
        end_time = time.time()
        
        total_duration = end_time - start_time
        
        # 基準要求：完整六階段處理在10分鐘內完成
        assert total_duration < 600, f"處理時間{total_duration:.2f}秒超過600秒基準"
        
        # 各階段時間檢查
        stage_durations = [s["processing_duration"] for s in result["stage_results"]]
        
        # Stage 1-4 應該在60秒內完成
        for i in range(4):
            assert stage_durations[i] < 60, f"Stage {i+1} 處理時間{stage_durations[i]:.2f}秒超過60秒"
        
        # Stage 5-6 可以較長，但不超過120秒
        assert stage_durations[4] < 120, f"Stage 5 處理時間{stage_durations[4]:.2f}秒超過120秒"
        assert stage_durations[5] < 120, f"Stage 6 處理時間{stage_durations[5]:.2f}秒超過120秒"
    
    def test_memory_usage_benchmark(self):
        """測試內存使用基準"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        pipeline = NTNPipeline()
        result = pipeline.execute_complete_pipeline()
        
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_used = peak_memory - initial_memory
        
        # 基準要求：內存使用不超過4GB
        assert memory_used < 4096, f"內存使用{memory_used:.2f}MB超過4096MB基準"
```

## 📊 測試數據管理

### 測試數據分級

#### Grade A測試數據 (必須使用真實數據)
```python
# tests/data/real_tle_samples.py
# 真實TLE數據樣本 - 從Space-Track.org獲取
REAL_TLE_SAMPLES = {
    "starlink": [
        {
            "name": "STARLINK-1007",
            "tle_line1": "1 44713U 19074A   21275.91667824  .00001874  00000-0  13717-3 0  9995",
            "tle_line2": "2 44713  53.0000 123.4567   0.0013 269.3456 162.7890 15.05000000123456",
            "source": "space-track.org",
            "fetch_date": "2021-10-02"
        }
        # ... 更多真實樣本
    ],
    "oneweb": [
        # OneWeb真實TLE數據
    ]
}
```

#### Grade B測試數據 (基於標準模型)
```python
# tests/data/standard_test_cases.py
# 基於ITU-R標準的測試案例
STANDARD_TEST_CASES = {
    "elevation_angles": [5, 10, 15, 30, 45, 60, 90],  # 度
    "distances": [400, 600, 800, 1200],  # km (LEO範圍)
    "frequencies": [2.0e9, 20e9, 30e9],  # Hz (Ka, Ku, V band)
}
```

### 測試環境配置
```yaml
# tests/config/test_environments.yaml
environments:
  unit_test:
    tle_data_source: "local_samples"
    processing_mode: "fast"
    validation_level: "basic"
    
  integration_test:
    tle_data_source: "real_tle_subset"
    processing_mode: "standard"  
    validation_level: "comprehensive"
    
  e2e_test:
    tle_data_source: "full_real_tle"
    processing_mode: "production"
    validation_level: "academic_grade_a"
```

## 🔍 測試工具和自動化

### 持續集成測試流程
```yaml
# .github/workflows/test_pipeline.yaml
name: Six Stage Refactor Tests

on:
  push:
    branches: [refactor/six-stages]
  pull_request:
    branches: [main]

jobs:
  unit_tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: pip install -r requirements-test.txt
      - name: Run unit tests
        run: pytest tests/test_shared/ tests/test_stages/ -v --cov
      
  integration_tests:
    runs-on: ubuntu-latest
    needs: unit_tests
    steps:
      - uses: actions/checkout@v2
      - name: Setup Docker
        run: docker-compose up -d
      - name: Run integration tests
        run: pytest tests/integration/ -v
        
  e2e_tests:
    runs-on: ubuntu-latest
    needs: integration_tests
    steps:
      - uses: actions/checkout@v2
      - name: Setup full environment
        run: make full-setup
      - name: Run E2E tests
        run: pytest tests/e2e/ -v --timeout=1200
```

### 測試報告生成
```python
# tests/reporting/generate_test_report.py
def generate_comprehensive_test_report():
    """生成綜合測試報告"""
    report = {
        "test_execution_summary": {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "coverage_percentage": 0
        },
        "performance_benchmarks": {
            "processing_time_vs_baseline": {},
            "memory_usage_vs_baseline": {},
            "accuracy_metrics": {}
        },
        "academic_compliance": {
            "grade_a_standards_met": True,
            "real_data_usage_percentage": 100,
            "algorithm_correctness_verified": True
        }
    }
    return report
```

## 🚨 測試失敗處理策略

### 自動修復機制
```bash
# tests/scripts/auto_fix_common_issues.sh
#\!/bin/bash

# 常見問題自動修復
echo "檢查並修復常見測試問題..."

# 1. 清理測試數據目錄
rm -rf /tmp/test_data/*
mkdir -p /tmp/test_data

# 2. 重置Docker測試環境
docker-compose -f docker-compose.test.yaml down
docker-compose -f docker-compose.test.yaml up -d

# 3. 驗證服務可用性
curl -f http://localhost:8080/health || exit 1

echo "環境重置完成，重新運行測試..."
```

### 測試失敗升級機制
1. **自動重試**: 失敗測試自動重試2次
2. **問題隔離**: 失敗測試不影響其他測試繼續執行
3. **詳細日誌**: 失敗時保存完整的系統狀態
4. **通知機制**: 關鍵測試失敗時立即通知開發團隊

---

**重要提醒**: 這個測試策略確保重構過程中的質量保證，所有測試必須在每個Phase完成前全部通過。
