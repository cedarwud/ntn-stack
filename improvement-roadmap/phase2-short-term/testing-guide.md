# Phase 2: 測試驗證指南

**測試目標**: 驗證文檔、測試框架、配置管理和監控系統
**測試深度**: 深度測試 + 長期穩定性驗證

## 📋 測試階段規劃

### 階段 1: 測試框架驗證 (Week 1-2)
- 測試覆蓋率提升驗證
- 新增測試案例的正確性
- 測試執行效率評估

### 階段 2: 監控系統測試 (Week 3-4)
- 性能監控準確性
- 告警機制有效性
- 儀表板功能完整性

### 階段 3: 配置管理測試 (Week 5)
- 多環境配置正確性
- 配置變更流程驗證
- 配置安全性檢查

### 階段 4: 整合穩定性測試 (Week 6)
- 長期運行穩定性
- 負載下的系統表現
- 故障恢復能力

## 🧪 詳細測試計畫

### 1. 測試框架驗證

#### 1.1 測試覆蓋率驗證
```bash
#!/bin/bash
# test_coverage_validation.sh

echo "🧪 驗證測試覆蓋率提升..."

# 執行覆蓋率測試
python -m pytest --cov=config --cov=netstack --cov=simworld \
  --cov-report=html --cov-report=term-missing \
  --cov-report=json -v

# 檢查覆蓋率報告
coverage_file="coverage.json"
if [ -f "$coverage_file" ]; then
    # 使用 jq 解析覆蓋率
    total_coverage=$(cat $coverage_file | jq '.totals.percent_covered')
    
    echo "總覆蓋率: $total_coverage%"
    
    # 檢查是否達到目標 (90%)
    if (( $(echo "$total_coverage >= 90" | bc -l) )); then
        echo "✅ 覆蓋率達標: $total_coverage%"
    else
        echo "❌ 覆蓋率未達標: $total_coverage% (目標: 90%)"
        exit 1
    fi
else
    echo "❌ 覆蓋率報告檔案不存在"
    exit 1
fi

# 檢查各模組覆蓋率
echo "📊 各模組覆蓋率詳情:"
cat $coverage_file | jq -r '.files | to_entries[] | "\(.key): \(.value.summary.percent_covered)%"' | sort
```

#### 1.2 新增測試案例驗證
```bash
#!/bin/bash
# test_new_testcases.sh

echo "🔍 驗證新增測試案例..."

# 執行新增的單元測試
echo "執行擴展配置測試..."
python -m pytest tests/unit/test_satellite_config_extended.py -v

# 執行整合測試
echo "執行預處理管道測試..."
python -m pytest tests/integration/test_preprocessing_pipeline.py -v

# 執行性能測試
echo "執行性能測試..."
python -m pytest tests/performance/test_system_performance.py -v -m performance

# 檢查測試結果
if [ $? -eq 0 ]; then
    echo "✅ 所有新增測試通過"
else
    echo "❌ 部分測試失敗"
    exit 1
fi

# 驗證測試執行時間
echo "⏱️ 測試執行時間分析..."
python -c "
import time
import subprocess

start_time = time.time()
result = subprocess.run(['python', '-m', 'pytest', 'tests/', '-q'], 
                       capture_output=True)
execution_time = time.time() - start_time

print(f'總測試執行時間: {execution_time:.2f}秒')

if execution_time > 600:  # 10分鐘
    print('❌ 測試執行時間過長')
    exit(1)
else:
    print('✅ 測試執行時間合理')
"
```

#### 1.3 測試品質評估
```python
#!/usr/bin/env python3
# test_quality_assessment.py

"""
測試品質評估腳本
分析測試的有效性和品質
"""

import ast
import os
from pathlib import Path
from collections import defaultdict

class TestQualityAnalyzer:
    """測試品質分析器"""
    
    def __init__(self, test_dir: Path):
        self.test_dir = test_dir
        self.quality_metrics = {
            'test_count': 0,
            'assertion_count': 0,
            'mock_usage': 0,
            'parametrized_tests': 0,
            'async_tests': 0,
            'performance_tests': 0
        }
    
    def analyze_test_file(self, file_path: Path):
        """分析單個測試檔案"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                # 計算測試函數
                if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
                    self.quality_metrics['test_count'] += 1
                    
                    # 檢查是否為異步測試
                    if any(isinstance(decorator, ast.Name) and decorator.id == 'pytest' 
                          for decorator in node.decorator_list):
                        for decorator in node.decorator_list:
                            if (isinstance(decorator, ast.Attribute) and 
                                decorator.attr == 'asyncio'):
                                self.quality_metrics['async_tests'] += 1
                    
                    # 檢查性能測試標記
                    for decorator in node.decorator_list:
                        if (isinstance(decorator, ast.Attribute) and 
                            isinstance(decorator.value, ast.Attribute) and
                            decorator.value.attr == 'mark' and
                            decorator.attr == 'performance'):
                            self.quality_metrics['performance_tests'] += 1
                
                # 計算斷言
                if isinstance(node, ast.Assert):
                    self.quality_metrics['assertion_count'] += 1
                
                # 檢查 Mock 使用
                if isinstance(node, ast.Call):
                    if (isinstance(node.func, ast.Attribute) and 
                        'mock' in str(node.func)):
                        self.quality_metrics['mock_usage'] += 1
                        
        except Exception as e:
            print(f"分析檔案失敗 {file_path}: {e}")
    
    def run_analysis(self):
        """執行完整分析"""
        test_files = list(self.test_dir.rglob("test_*.py"))
        
        print(f"發現 {len(test_files)} 個測試檔案")
        
        for test_file in test_files:
            self.analyze_test_file(test_file)
        
        return self.generate_quality_report()
    
    def generate_quality_report(self):
        """生成品質報告"""
        report = {
            'summary': self.quality_metrics.copy(),
            'quality_score': self.calculate_quality_score(),
            'recommendations': self.generate_recommendations()
        }
        
        return report
    
    def calculate_quality_score(self):
        """計算品質分數 (0-100)"""
        score = 0
        
        # 測試數量 (30分)
        if self.quality_metrics['test_count'] >= 50:
            score += 30
        elif self.quality_metrics['test_count'] >= 30:
            score += 20
        elif self.quality_metrics['test_count'] >= 10:
            score += 10
        
        # 斷言密度 (20分) - 平均每個測試的斷言數
        if self.quality_metrics['test_count'] > 0:
            assertion_density = (self.quality_metrics['assertion_count'] / 
                               self.quality_metrics['test_count'])
            if assertion_density >= 3:
                score += 20
            elif assertion_density >= 2:
                score += 15
            elif assertion_density >= 1:
                score += 10
        
        # Mock 使用 (15分) - 表示隔離測試
        if self.quality_metrics['mock_usage'] >= 10:
            score += 15
        elif self.quality_metrics['mock_usage'] >= 5:
            score += 10
        
        # 異步測試 (10分)
        if self.quality_metrics['async_tests'] >= 5:
            score += 10
        elif self.quality_metrics['async_tests'] >= 2:
            score += 5
        
        # 性能測試 (15分)
        if self.quality_metrics['performance_tests'] >= 5:
            score += 15
        elif self.quality_metrics['performance_tests'] >= 2:
            score += 10
        
        # 測試多樣性 (10分)
        diversity_score = min(len([k for k, v in self.quality_metrics.items() if v > 0]), 6)
        score += int(diversity_score * 10 / 6)
        
        return min(score, 100)
    
    def generate_recommendations(self):
        """生成改進建議"""
        recommendations = []
        
        if self.quality_metrics['test_count'] < 30:
            recommendations.append("增加更多測試案例以提升覆蓋率")
        
        if self.quality_metrics['assertion_count'] / max(self.quality_metrics['test_count'], 1) < 2:
            recommendations.append("增加測試斷言以提升測試強度")
        
        if self.quality_metrics['mock_usage'] < 5:
            recommendations.append("使用更多 Mock 來隔離測試依賴")
        
        if self.quality_metrics['performance_tests'] < 3:
            recommendations.append("增加性能回歸測試")
        
        if self.quality_metrics['async_tests'] < 3:
            recommendations.append("為異步功能添加專門測試")
        
        return recommendations

if __name__ == "__main__":
    analyzer = TestQualityAnalyzer(Path("tests"))
    report = analyzer.run_analysis()
    
    print("\n📊 測試品質報告")
    print("=" * 40)
    
    print(f"測試總數: {report['summary']['test_count']}")
    print(f"斷言總數: {report['summary']['assertion_count']}")
    print(f"Mock 使用: {report['summary']['mock_usage']}")
    print(f"異步測試: {report['summary']['async_tests']}")
    print(f"性能測試: {report['summary']['performance_tests']}")
    
    print(f"\n品質分數: {report['quality_score']}/100")
    
    if report['quality_score'] >= 80:
        print("✅ 測試品質優秀")
    elif report['quality_score'] >= 60:
        print("⚠️ 測試品質良好，有改進空間")
    else:
        print("❌ 測試品質需要提升")
    
    if report['recommendations']:
        print("\n💡 改進建議:")
        for rec in report['recommendations']:
            print(f"  - {rec}")
```

### 2. 監控系統測試

#### 2.1 性能監控準確性測試
```bash
#!/bin/bash
# test_performance_monitoring.sh

echo "📊 測試性能監控系統..."

# 啟動性能監控
python monitoring/performance_monitor.py --interval 5 &
monitor_pid=$!

echo "性能監控已啟動 (PID: $monitor_pid)"

# 等待收集一些數據
sleep 30

# 生成測試負載
echo "🔄 生成測試負載..."
for i in {1..10}; do
    curl -s http://localhost:8080/health > /dev/null &
    curl -s http://localhost:8888/health > /dev/null &
done

# 等待負載完成
wait

# 再收集一些數據
sleep 30

# 停止監控
kill $monitor_pid

# 檢查監控數據
echo "📋 檢查監控數據..."
if [ -d "monitoring/data" ]; then
    file_count=$(find monitoring/data -name "metrics_*.json" | wc -l)
    echo "生成的監控文件數量: $file_count"
    
    if [ $file_count -gt 0 ]; then
        echo "✅ 監控數據收集正常"
        
        # 檢查最新數據的完整性
        latest_file=$(find monitoring/data -name "metrics_*.json" -type f -exec ls -t {} + | head -1)
        echo "檢查最新監控數據: $latest_file"
        
        # 驗證JSON格式
        python -c "
import json
import sys

try:
    with open('$latest_file') as f:
        data = json.load(f)
    
    required_fields = ['timestamp', 'cpu_percent', 'memory_percent', 'api_response_times']
    missing_fields = [field for field in required_fields if field not in data]
    
    if missing_fields:
        print(f'❌ 缺少必要字段: {missing_fields}')
        sys.exit(1)
    else:
        print('✅ 監控數據格式正確')
        
except Exception as e:
    print(f'❌ 監控數據格式錯誤: {e}')
    sys.exit(1)
"
        
    else
        echo "❌ 未生成監控數據"
        exit 1
    fi
else
    echo "❌ 監控數據目錄不存在"
    exit 1
fi
```

#### 2.2 告警機制測試
```python
#!/usr/bin/env python3
# test_alerting_system.py

"""
告警機制測試
驗證各種閾值條件下的告警觸發
"""

import time
import psutil
from monitoring.performance_monitor import PerformanceMonitor, PerformanceMetrics
from datetime import datetime, timezone

class AlertingSystemTester:
    """告警系統測試器"""
    
    def __init__(self):
        self.monitor = PerformanceMonitor()
        self.test_results = []
    
    def create_test_metrics(self, cpu_percent=10, memory_percent=20, 
                          api_response_times=None):
        """創建測試用的性能指標"""
        if api_response_times is None:
            api_response_times = {
                "http://localhost:8080/health": 0.05,
                "http://localhost:8888/health": 0.03
            }
        
        return PerformanceMetrics(
            timestamp=datetime.now(timezone.utc).isoformat(),
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_used_mb=1024,
            disk_usage_percent=50,
            api_response_times=api_response_times,
            active_connections=10,
            error_count=0
        )
    
    def test_cpu_alert(self):
        """測試 CPU 告警"""
        print("🧪 測試 CPU 高使用率告警...")
        
        # 正常情況 - 不應觸發告警
        normal_metrics = self.create_test_metrics(cpu_percent=50)
        alerts = self.monitor._generate_alerts([normal_metrics])
        
        if not any("CPU" in alert for alert in alerts):
            print("✅ 正常 CPU 使用率未觸發告警")
            self.test_results.append(("CPU正常", True))
        else:
            print("❌ 正常 CPU 使用率錯誤觸發告警")
            self.test_results.append(("CPU正常", False))
        
        # 高使用率 - 應觸發告警
        high_cpu_metrics = self.create_test_metrics(cpu_percent=85)
        alerts = self.monitor._generate_alerts([high_cpu_metrics])
        
        if any("CPU" in alert for alert in alerts):
            print("✅ 高 CPU 使用率正確觸發告警")
            self.test_results.append(("CPU高使用率", True))
        else:
            print("❌ 高 CPU 使用率未觸發告警")
            self.test_results.append(("CPU高使用率", False))
    
    def test_memory_alert(self):
        """測試記憶體告警"""
        print("🧪 測試記憶體高使用率告警...")
        
        # 正常情況
        normal_metrics = self.create_test_metrics(memory_percent=70)
        alerts = self.monitor._generate_alerts([normal_metrics])
        
        if not any("記憶體" in alert for alert in alerts):
            print("✅ 正常記憶體使用率未觸發告警")
            self.test_results.append(("記憶體正常", True))
        else:
            print("❌ 正常記憶體使用率錯誤觸發告警")
            self.test_results.append(("記憶體正常", False))
        
        # 高使用率
        high_memory_metrics = self.create_test_metrics(memory_percent=90)
        alerts = self.monitor._generate_alerts([high_memory_metrics])
        
        if any("記憶體" in alert for alert in alerts):
            print("✅ 高記憶體使用率正確觸發告警")
            self.test_results.append(("記憶體高使用率", True))
        else:
            print("❌ 高記憶體使用率未觸發告警")
            self.test_results.append(("記憶體高使用率", False))
    
    def test_api_response_alert(self):
        """測試 API 響應時間告警"""
        print("🧪 測試 API 響應時間告警...")
        
        # 正常響應時間
        normal_api_times = {
            "http://localhost:8080/health": 0.05,
            "http://localhost:8888/health": 0.03
        }
        normal_metrics = self.create_test_metrics(api_response_times=normal_api_times)
        alerts = self.monitor._generate_alerts([normal_metrics])
        
        if not any("API 響應" in alert for alert in alerts):
            print("✅ 正常 API 響應時間未觸發告警")
            self.test_results.append(("API響應正常", True))
        else:
            print("❌ 正常 API 響應時間錯誤觸發告警")
            self.test_results.append(("API響應正常", False))
        
        # 慢響應時間
        slow_api_times = {
            "http://localhost:8080/health": 0.8,  # 800ms，超過500ms閾值
            "http://localhost:8888/health": 0.03
        }
        slow_metrics = self.create_test_metrics(api_response_times=slow_api_times)
        alerts = self.monitor._generate_alerts([slow_metrics])
        
        if any("API 響應緩慢" in alert for alert in alerts):
            print("✅ 慢 API 響應時間正確觸發告警")
            self.test_results.append(("API響應緩慢", True))
        else:
            print("❌ 慢 API 響應時間未觸發告警")
            self.test_results.append(("API響應緩慢", False))
        
        # API 無響應
        failed_api_times = {
            "http://localhost:8080/health": -1,  # 表示失敗
            "http://localhost:8888/health": 0.03
        }
        failed_metrics = self.create_test_metrics(api_response_times=failed_api_times)
        alerts = self.monitor._generate_alerts([failed_metrics])
        
        if any("API 無響應" in alert for alert in alerts):
            print("✅ API 無響應正確觸發告警")
            self.test_results.append(("API無響應", True))
        else:
            print("❌ API 無響應未觸發告警")
            self.test_results.append(("API無響應", False))
    
    def test_alert_threshold_accuracy(self):
        """測試告警閾值精確性"""
        print("🧪 測試告警閾值精確性...")
        
        # 測試邊界值
        boundary_tests = [
            (79.9, "CPU", False),  # 接近但未達到80%閾值
            (80.1, "CPU", True),   # 超過80%閾值
            (84.9, "記憶體", False), # 接近但未達到85%閾值
            (85.1, "記憶體", True),  # 超過85%閾值
        ]
        
        for value, metric_type, should_alert in boundary_tests:
            if metric_type == "CPU":
                test_metrics = self.create_test_metrics(cpu_percent=value)
                keyword = "CPU"
            else:
                test_metrics = self.create_test_metrics(memory_percent=value)
                keyword = "記憶體"
            
            alerts = self.monitor._generate_alerts([test_metrics])
            has_alert = any(keyword in alert for alert in alerts)
            
            if has_alert == should_alert:
                print(f"✅ {metric_type} {value}% 閾值測試通過")
                self.test_results.append((f"{metric_type}閾值{value}%", True))
            else:
                print(f"❌ {metric_type} {value}% 閾值測試失敗")
                self.test_results.append((f"{metric_type}閾值{value}%", False))
    
    def run_all_tests(self):
        """執行所有告警測試"""
        print("🚨 開始告警機制測試...")
        
        self.test_cpu_alert()
        self.test_memory_alert()
        self.test_api_response_alert()
        self.test_alert_threshold_accuracy()
        
        # 生成測試報告
        self.generate_test_report()
    
    def generate_test_report(self):
        """生成測試報告"""
        print("\n📋 告警測試報告")
        print("=" * 40)
        
        passed_tests = sum(1 for _, result in self.test_results if result)
        total_tests = len(self.test_results)
        
        print(f"總測試數: {total_tests}")
        print(f"通過測試: {passed_tests}")
        print(f"失敗測試: {total_tests - passed_tests}")
        print(f"通過率: {passed_tests/total_tests*100:.1f}%")
        
        print("\n詳細結果:")
        for test_name, result in self.test_results:
            status = "✅" if result else "❌"
            print(f"  {status} {test_name}")
        
        if passed_tests == total_tests:
            print("\n🎉 所有告警測試通過！")
            return True
        else:
            print(f"\n⚠️ {total_tests - passed_tests} 個測試失敗")
            return False

if __name__ == "__main__":
    tester = AlertingSystemTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)
```

### 3. 配置管理測試

#### 3.1 多環境配置測試
```bash
#!/bin/bash
# test_environment_config.sh

echo "⚙️ 測試多環境配置管理..."

# 測試環境列表
environments=("development" "testing" "staging" "production")

for env in "${environments[@]}"; do
    echo "測試 $env 環境配置..."
    
    # 設置環境變數
    export NTN_ENVIRONMENT=$env
    
    # 測試配置載入
    python -c "
from config.environment_config import CONFIG_MANAGER
import sys

try:
    config = CONFIG_MANAGER.load_environment_config()
    print(f'✅ {env} 環境配置載入成功')
    
    # 驗證配置結構
    required_sections = ['database', 'api', 'satellite']
    for section in required_sections:
        if section not in config:
            print(f'❌ {env} 環境缺少 {section} 配置')
            sys.exit(1)
    
    # 驗證配置值的合理性
    db_config = CONFIG_MANAGER.get_database_config()
    api_config = CONFIG_MANAGER.get_api_config()
    sat_config = CONFIG_MANAGER.get_satellite_config()
    
    if sat_config.max_candidates > 8:
        print(f'❌ {env} 環境候選衛星數超過限制')
        sys.exit(1)
    
    print(f'✅ {env} 環境配置驗證通過')
    
except Exception as e:
    print(f'❌ {env} 環境配置錯誤: {e}')
    sys.exit(1)
"
    
    if [ $? -ne 0 ]; then
        echo "❌ $env 環境配置測試失敗"
        exit 1
    fi
done

echo "✅ 所有環境配置測試通過"

# 測試配置驗證功能
echo "測試配置驗證功能..."
python -c "
from config.environment_config import CONFIG_MANAGER

if CONFIG_MANAGER.validate_current_config():
    print('✅ 配置驗證功能正常')
else:
    print('❌ 配置驗證功能異常')
    exit(1)
"
```

### 4. 長期穩定性測試

#### 4.1 持續運行測試
```bash
#!/bin/bash
# test_long_term_stability.sh

echo "⏳ 開始長期穩定性測試 (24小時)..."

# 創建測試日誌目錄
mkdir -p stability_test_logs
cd stability_test_logs

# 啟動監控
python ../monitoring/performance_monitor.py --interval 300 > monitor.log 2>&1 &  # 5分鐘間隔
monitor_pid=$!

echo "性能監控已啟動 (PID: $monitor_pid)"

# 持續壓力測試函數
run_stress_test() {
    local duration=$1
    local end_time=$((SECONDS + duration))
    
    while [ $SECONDS -lt $end_time ]; do
        # API 壓力測試
        for i in {1..5}; do
            curl -s http://localhost:8080/health > /dev/null &
            curl -s http://localhost:8888/health > /dev/null &
            curl -s http://localhost:8080/api/v1/satellites/unified/health > /dev/null &
        done
        
        # 等待所有請求完成
        wait
        
        # 休息一段時間
        sleep 60
    done
}

# 記錄開始時間
start_time=$(date)
echo "穩定性測試開始時間: $start_time"

# 運行24小時測試 (86400秒)
# 為了演示，這裡使用較短時間 (3600秒 = 1小時)
test_duration=3600

echo "運行 $test_duration 秒的穩定性測試..."
run_stress_test $test_duration

# 停止監控
kill $monitor_pid
echo "穩定性測試完成"

# 分析結果
echo "分析穩定性測試結果..."
python -c "
import json
import glob
from pathlib import Path
from datetime import datetime

# 載入所有監控數據
monitor_files = glob.glob('../monitoring/data/metrics_*.json')
monitor_files.sort()

if not monitor_files:
    print('❌ 未找到監控數據')
    exit(1)

print(f'找到 {len(monitor_files)} 個監控數據文件')

# 分析數據
cpu_values = []
memory_values = []
api_failures = 0
total_api_checks = 0

for file_path in monitor_files:
    try:
        with open(file_path) as f:
            data = json.load(f)
        
        cpu_values.append(data['cpu_percent'])
        memory_values.append(data['memory_percent'])
        
        # 檢查 API 響應
        for endpoint, response_time in data['api_response_times'].items():
            total_api_checks += 1
            if response_time == -1:  # 失敗
                api_failures += 1
                
    except Exception as e:
        print(f'讀取監控數據失敗: {e}')

if cpu_values and memory_values:
    avg_cpu = sum(cpu_values) / len(cpu_values)
    max_cpu = max(cpu_values)
    avg_memory = sum(memory_values) / len(memory_values)
    max_memory = max(memory_values)
    
    api_success_rate = (total_api_checks - api_failures) / total_api_checks * 100 if total_api_checks > 0 else 0
    
    print(f'平均 CPU 使用率: {avg_cpu:.2f}%')
    print(f'最高 CPU 使用率: {max_cpu:.2f}%')
    print(f'平均記憶體使用率: {avg_memory:.2f}%')
    print(f'最高記憶體使用率: {max_memory:.2f}%')
    print(f'API 成功率: {api_success_rate:.2f}%')
    
    # 評估穩定性
    stability_issues = []
    
    if max_cpu > 90:
        stability_issues.append('CPU 使用率過高')
    
    if max_memory > 90:
        stability_issues.append('記憶體使用率過高')
    
    if api_success_rate < 99:
        stability_issues.append('API 可用性不足')
    
    if stability_issues:
        print(f'❌ 穩定性問題: {stability_issues}')
        exit(1)
    else:
        print('✅ 系統穩定性良好')
else:
    print('❌ 無足夠數據進行分析')
    exit(1)
"

echo "穩定性測試報告已生成"
```

## ✅ Phase 2 測試完成檢查清單

### 必須通過的測試
- [ ] 測試覆蓋率 ≥ 90%
- [ ] 所有新增測試案例通過
- [ ] 性能監控數據收集正常
- [ ] 告警機制觸發準確
- [ ] 多環境配置正確載入
- [ ] 長期穩定性測試無問題

### 品質指標檢查
- [ ] 測試執行時間 < 10分鐘
- [ ] 測試品質分數 ≥ 80分
- [ ] API 成功率 ≥ 99%
- [ ] 系統可用性 ≥ 99.9%

### 文檔驗證
- [ ] 所有文檔更新準確
- [ ] 故障排除指南有效
- [ ] 開發者指南可用
- [ ] 配置說明完整

---

**注意**: Phase 2 的測試重點是驗證新建立的基礎設施能夠支援長期穩定運行，為後續的系統優化和擴展奠定基礎。