# 階段8：除錯和故障排除

## 課程目標與學習重點

### 完成本階段後您將能夠：
- 掌握衛星軌道計算系統的完整除錯方法論
- 建立系統性的故障診斷和修復流程
- 實現自動化的問題檢測和預警機制
- 處理生產環境中的複雜故障場景
- 建立完整的運維和故障恢復體系

### 職業發展價值：
- 具備複雜系統故障排除的專業技能
- 掌握生產級軟體的維運經驗
- 理解航太系統的高可靠性要求
- 具備系統架構診斷和優化能力

## 故障分類與診斷體系

### 故障分類架構

**按影響層級分類：**
```
L1 - 系統級故障        ← 完全無法處理，系統停機
    ↓
L2 - 組件級故障        ← 單個組件失效，影響部分功能
    ↓
L3 - 數據級故障        ← 部分數據異常，跳過問題數據
    ↓
L4 - 精度級故障        ← 計算精度下降，但不影響基本功能
```

**按故障原因分類：**
- **數據問題** - TLE格式錯誤、數據過期、缺失
- **算法問題** - SGP4計算異常、座標轉換錯誤
- **環境問題** - 記憶體不足、依賴缺失、權限問題
- **配置問題** - 參數設置錯誤、閾值不當、路徑錯誤

### 常見故障症狀對照表

**症狀 → 可能原因 → 診斷方法：**

| 症狀 | 可能原因 | 診斷方法 | 優先級 |
|------|----------|----------|--------|
| 8000+衛星→0顆可見 | 時間基準錯誤 | 檢查TLE epoch vs 計算時間 | 🔥 CRITICAL |
| 位置誤差>10km | SGP4實現錯誤 | 與skyfield比較 | 🔥 HIGH |
| 記憶體使用爆炸 | 快取未清理/批處理過大 | 監控記憶體使用曲線 | ⚠️ MEDIUM |
| 處理速度驟降 | 數據品質差/大量錯誤 | 分析錯誤率統計 | ⚠️ MEDIUM |
| 間歇性計算失敗 | TLE數據損壞 | 驗證TLE檢查碼 | ⚠️ MEDIUM |

## 核心除錯工具實現

### 1. DiagnosticTool - 診斷工具

**debugging/diagnostic_tool.py 完整實現：**
```python
#!/usr/bin/env python3
"""
診斷工具
提供系統故障的自動診斷和分析功能
"""

import os
import sys
import psutil
import logging
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import traceback
import json

from ..data.parser import TLEData, TLEParser
from ..data.loader import TLEDataLoader
from ..calculation.sgp4_engine import SGP4Calculator
from ..utils.quality_validator import QualityValidator
from ..utils.accuracy_comparator import AccuracyComparator

logger = logging.getLogger(__name__)

class DiagnosticTool:
    """系統診斷工具"""
    
    def __init__(self):
        """初始化診斷工具"""
        self.diagnostic_results = {}
        self.system_info = self._collect_system_info()
        
    def run_comprehensive_diagnosis(self, 
                                  tle_file_path: Optional[str] = None,
                                  sample_size: int = 10) -> Dict:
        """
        執行綜合系統診斷
        
        Args:
            tle_file_path: TLE檔案路徑（可選，用於測試）
            sample_size: 樣本測試大小
            
        Returns:
            Dict: 診斷報告
        """
        logger.info("開始綜合系統診斷...")
        
        diagnosis = {
            'timestamp': datetime.now().isoformat(),
            'system_info': self.system_info,
            'test_results': {},
            'issues_found': [],
            'recommendations': [],
            'overall_health': 'UNKNOWN'
        }
        
        # 1. 環境診斷
        env_result = self._diagnose_environment()
        diagnosis['test_results']['environment'] = env_result
        
        # 2. 依賴檢查
        deps_result = self._check_dependencies()
        diagnosis['test_results']['dependencies'] = deps_result
        
        # 3. 基礎功能測試
        basic_result = self._test_basic_functionality()
        diagnosis['test_results']['basic_functionality'] = basic_result
        
        # 4. 如果提供了TLE檔案，進行數據測試
        if tle_file_path and os.path.exists(tle_file_path):
            data_result = self._test_tle_data_processing(tle_file_path, sample_size)
            diagnosis['test_results']['data_processing'] = data_result
            
            # 5. 精度測試
            accuracy_result = self._test_accuracy(tle_file_path, sample_size)
            diagnosis['test_results']['accuracy'] = accuracy_result
        
        # 6. 性能基準測試
        perf_result = self._benchmark_performance()
        diagnosis['test_results']['performance'] = perf_result
        
        # 彙總問題和建議
        self._analyze_results(diagnosis)
        
        # 儲存診斷結果
        self.diagnostic_results = diagnosis
        
        logger.info(f"系統診斷完成 - 整體健康度: {diagnosis['overall_health']}")
        return diagnosis
    
    def _collect_system_info(self) -> Dict:
        """收集系統信息"""
        try:
            return {
                'platform': sys.platform,
                'python_version': sys.version,
                'cpu_count': psutil.cpu_count(),
                'memory_total_gb': psutil.virtual_memory().total / (1024**3),
                'memory_available_gb': psutil.virtual_memory().available / (1024**3),
                'disk_free_gb': psutil.disk_usage('.').free / (1024**3),
                'current_directory': os.getcwd()
            }
        except Exception as e:
            logger.error(f"收集系統信息失敗: {e}")
            return {'error': str(e)}
    
    def _diagnose_environment(self) -> Dict:
        """診斷運行環境"""
        issues = []
        status = 'HEALTHY'
        
        try:
            # 檢查Python版本
            if sys.version_info < (3, 8):
                issues.append(f"Python版本過低: {sys.version_info}, 建議3.8+")
                status = 'WARNING'
            
            # 檢查記憶體
            memory = psutil.virtual_memory()
            if memory.available < 2 * 1024**3:  # 少於2GB可用記憶體
                issues.append(f"可用記憶體不足: {memory.available/(1024**3):.1f}GB")
                status = 'WARNING'
            
            # 檢查磁碟空間
            disk = psutil.disk_usage('.')
            if disk.free < 1 * 1024**3:  # 少於1GB磁碟空間
                issues.append(f"磁碟空間不足: {disk.free/(1024**3):.1f}GB")
                status = 'WARNING'
            
            # 檢查CPU負載
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > 90:
                issues.append(f"CPU負載過高: {cpu_percent}%")
                status = 'WARNING'
                
        except Exception as e:
            issues.append(f"環境診斷失敗: {e}")
            status = 'ERROR'
        
        return {
            'status': status,
            'issues': issues,
            'details': self.system_info
        }
    
    def _check_dependencies(self) -> Dict:
        """檢查依賴套件"""
        required_packages = [
            'numpy', 'skyfield', 'astropy', 'pandas', 
            'scipy', 'psutil', 'pytz'
        ]
        
        missing_packages = []
        version_info = {}
        
        for package in required_packages:
            try:
                module = __import__(package)
                if hasattr(module, '__version__'):
                    version_info[package] = module.__version__
                else:
                    version_info[package] = 'unknown'
            except ImportError:
                missing_packages.append(package)
        
        status = 'ERROR' if missing_packages else 'HEALTHY'
        
        return {
            'status': status,
            'missing_packages': missing_packages,
            'installed_versions': version_info,
            'issues': [f"缺少套件: {pkg}" for pkg in missing_packages]
        }
    
    def _test_basic_functionality(self) -> Dict:
        """測試基礎功能"""
        tests = {}
        overall_status = 'HEALTHY'
        
        # 測試TLE解析器
        try:
            parser = TLEParser()
            test_tle = [
                "ISS (ZARYA)",
                "1 25544U 98067A   25245.12345678  .00002182  00000-0  14829-4 0  9999",
                "2 25544  51.6461 339.7760 0003363  31.3921 328.8071 15.54225995123459"
            ]
            result = parser.parse_tle_group(test_tle)
            tests['tle_parser'] = {
                'status': 'PASSED' if result else 'FAILED',
                'details': 'TLE解析器基本功能測試'
            }
            if not result:
                overall_status = 'ERROR'
        except Exception as e:
            tests['tle_parser'] = {
                'status': 'FAILED',
                'error': str(e)
            }
            overall_status = 'ERROR'
        
        # 測試SGP4計算器
        try:
            calculator = SGP4Calculator()
            if 'tle_parser' in tests and tests['tle_parser']['status'] == 'PASSED':
                # 使用解析的TLE數據測試SGP4
                tle_data = TLEData(
                    satellite_number=25544,
                    satellite_name="ISS (ZARYA)",
                    epoch_year=25,
                    epoch_day=245.12345678,
                    mean_motion=15.54225995,
                    eccentricity=0.0003363,
                    inclination=51.6461,
                    raan=339.7760,
                    argument_of_perigee=31.3921,
                    mean_anomaly=328.8071,
                    mean_motion_derivative=0.00002182,
                    mean_motion_second_derivative=0.0,
                    bstar=0.00014829,
                    element_number=999,
                    revolution_number=12345
                )
                
                calc_time = tle_data.get_epoch_datetime()
                result = calculator.calculate_satellite_position(tle_data, calc_time)
                
                tests['sgp4_calculator'] = {
                    'status': 'PASSED' if 'position_eci_km' in result else 'FAILED',
                    'details': 'SGP4計算器基本功能測試'
                }
                if 'position_eci_km' not in result:
                    overall_status = 'ERROR'
            else:
                tests['sgp4_calculator'] = {
                    'status': 'SKIPPED',
                    'reason': 'TLE解析器測試失敗'
                }
        except Exception as e:
            tests['sgp4_calculator'] = {
                'status': 'FAILED',
                'error': str(e)
            }
            overall_status = 'ERROR'
        
        # 測試品質驗證器
        try:
            validator = QualityValidator()
            # 使用測試數據
            validation_result = validator.validate_calculation_result({
                'position_eci_km': [6800, 0, 0],
                'velocity_eci_kmps': [0, 7.5, 0],
                'calculation_time': datetime.now(),
                'tle_epoch': datetime.now()
            })
            
            tests['quality_validator'] = {
                'status': 'PASSED' if validation_result.is_valid else 'WARNING',
                'details': '品質驗證器基本功能測試'
            }
        except Exception as e:
            tests['quality_validator'] = {
                'status': 'FAILED',
                'error': str(e)
            }
            if overall_status == 'HEALTHY':
                overall_status = 'WARNING'
        
        return {
            'status': overall_status,
            'test_results': tests
        }
    
    def _test_tle_data_processing(self, tle_file_path: str, sample_size: int) -> Dict:
        """測試TLE數據處理"""
        issues = []
        status = 'HEALTHY'
        stats = {}
        
        try:
            # 載入TLE數據
            loader = TLEDataLoader()
            tle_lines = loader.load_tle_file(tle_file_path)
            
            stats['total_lines'] = len(tle_lines)
            stats['expected_satellites'] = len(tle_lines) // 3
            
            # 驗證數據格式
            validation_result = loader.validate_tle_data(tle_lines)
            if not validation_result:
                issues.append("TLE數據格式驗證失敗")
                status = 'ERROR'
            
            # 解析樣本數據
            parser = TLEParser()
            sample_lines = tle_lines[:sample_size * 3]
            parsed_data = parser.parse_tle_file(sample_lines)
            
            stats['sample_size'] = len(parsed_data)
            stats['parse_success_rate'] = len(parsed_data) / sample_size if sample_size > 0 else 0
            
            if stats['parse_success_rate'] < 0.9:
                issues.append(f"TLE解析成功率過低: {stats['parse_success_rate']:.1%}")
                status = 'WARNING' if status == 'HEALTHY' else status
            
            # 驗證解析結果的品質
            validator = QualityValidator()
            validation_issues = 0
            
            for tle_data in parsed_data[:5]:  # 檢查前5個
                result = validator.validate_tle_data(tle_data)
                if not result.is_valid:
                    validation_issues += 1
            
            stats['validation_issue_rate'] = validation_issues / min(5, len(parsed_data)) if parsed_data else 1
            
            if stats['validation_issue_rate'] > 0.2:
                issues.append(f"TLE數據品質問題率過高: {stats['validation_issue_rate']:.1%}")
                status = 'WARNING' if status == 'HEALTHY' else status
                
        except Exception as e:
            issues.append(f"TLE數據處理測試失敗: {e}")
            status = 'ERROR'
        
        return {
            'status': status,
            'issues': issues,
            'statistics': stats
        }
    
    def _test_accuracy(self, tle_file_path: str, sample_size: int) -> Dict:
        """測試計算精度"""
        issues = []
        status = 'HEALTHY'
        accuracy_stats = {}
        
        try:
            # 載入和解析測試數據
            loader = TLEDataLoader()
            tle_lines = loader.load_tle_file(tle_file_path)
            
            parser = TLEParser()
            sample_lines = tle_lines[:sample_size * 3]
            parsed_data = parser.parse_tle_file(sample_lines)
            
            if not parsed_data:
                return {
                    'status': 'ERROR',
                    'issues': ['無有效的TLE數據進行精度測試'],
                    'statistics': {}
                }
            
            # 進行SGP4計算
            calculator = SGP4Calculator()
            comparator = AccuracyComparator()
            
            calculation_results = []
            for tle_data in parsed_data[:3]:  # 只測試前3個以節省時間
                try:
                    calc_time = tle_data.get_epoch_datetime()
                    result = calculator.calculate_satellite_position(tle_data, calc_time)
                    calculation_results.append(result)
                except Exception as e:
                    logger.warning(f"跳過計算失敗的衛星: {e}")
            
            if not calculation_results:
                return {
                    'status': 'ERROR',
                    'issues': ['所有SGP4計算都失敗'],
                    'statistics': {}
                }
            
            # 精度比較測試
            accuracy_report = comparator.batch_accuracy_analysis(
                parsed_data[:len(calculation_results)], 
                calculation_results
            )
            
            if 'error' in accuracy_report:
                issues.append(f"精度測試失敗: {accuracy_report['error']}")
                status = 'ERROR'
            else:
                accuracy_stats = accuracy_report
                
                # 檢查精度標準
                pos_error = accuracy_report['position_accuracy']['mean_error_km']
                vel_error = accuracy_report['velocity_accuracy']['mean_error_kmps']
                
                if pos_error > 5.0:
                    issues.append(f"位置精度過低: {pos_error:.3f}km")
                    status = 'ERROR'
                elif pos_error > 1.0:
                    issues.append(f"位置精度較低: {pos_error:.3f}km")
                    status = 'WARNING' if status == 'HEALTHY' else status
                
                if vel_error > 0.05:
                    issues.append(f"速度精度過低: {vel_error:.5f}km/s")
                    status = 'ERROR'
                elif vel_error > 0.01:
                    issues.append(f"速度精度較低: {vel_error:.5f}km/s")
                    status = 'WARNING' if status == 'HEALTHY' else status
                
        except Exception as e:
            issues.append(f"精度測試失敗: {e}")
            status = 'ERROR'
        
        return {
            'status': status,
            'issues': issues,
            'statistics': accuracy_stats
        }
    
    def _benchmark_performance(self) -> Dict:
        """性能基準測試"""
        issues = []
        status = 'HEALTHY'
        perf_stats = {}
        
        try:
            # 創建測試數據
            test_tle_data = TLEData(
                satellite_number=25544,
                satellite_name="TEST_SAT",
                epoch_year=25,
                epoch_day=245.0,
                mean_motion=15.54,
                eccentricity=0.001,
                inclination=51.6,
                raan=339.8,
                argument_of_perigee=31.4,
                mean_anomaly=328.8,
                mean_motion_derivative=0.0,
                mean_motion_second_derivative=0.0,
                bstar=0.0001,
                element_number=1,
                revolution_number=1000
            )
            
            calculator = SGP4Calculator()
            calc_time = test_tle_data.get_epoch_datetime()
            
            # 測試單次計算性能
            start_time = datetime.now()
            for _ in range(100):  # 計算100次
                result = calculator.calculate_satellite_position(test_tle_data, calc_time)
            single_calc_time = (datetime.now() - start_time).total_seconds()
            
            calculations_per_second = 100 / single_calc_time
            perf_stats['calculations_per_second'] = calculations_per_second
            
            # 性能基準檢查
            if calculations_per_second < 100:
                issues.append(f"計算性能過低: {calculations_per_second:.1f} calc/s")
                status = 'WARNING'
            
            # 測試記憶體使用
            import psutil
            process = psutil.Process()
            memory_before = process.memory_info().rss / (1024**2)  # MB
            
            # 執行批量計算
            batch_results = calculator.calculate_batch_positions(
                [test_tle_data] * 50,
                [calc_time + timedelta(minutes=i) for i in range(10)]
            )
            
            memory_after = process.memory_info().rss / (1024**2)  # MB
            memory_increase = memory_after - memory_before
            
            perf_stats['memory_increase_mb'] = memory_increase
            perf_stats['batch_results_count'] = len(batch_results)
            
            if memory_increase > 500:  # 記憶體增加超過500MB
                issues.append(f"記憶體使用增長過多: {memory_increase:.1f}MB")
                status = 'WARNING' if status == 'HEALTHY' else status
                
        except Exception as e:
            issues.append(f"性能測試失敗: {e}")
            status = 'ERROR'
        
        return {
            'status': status,
            'issues': issues,
            'statistics': perf_stats
        }
    
    def _analyze_results(self, diagnosis: Dict):
        """分析診斷結果並生成建議"""
        all_issues = []
        critical_count = 0
        warning_count = 0
        
        # 收集所有問題
        for test_name, result in diagnosis['test_results'].items():
            if 'issues' in result:
                all_issues.extend(result['issues'])
            
            if result.get('status') == 'ERROR':
                critical_count += 1
            elif result.get('status') == 'WARNING':
                warning_count += 1
        
        diagnosis['issues_found'] = all_issues
        
        # 生成建議
        recommendations = []
        
        if critical_count > 0:
            recommendations.append("🔥 發現關鍵問題，需要立即修復")
            diagnosis['overall_health'] = 'CRITICAL'
        elif warning_count > 2:
            recommendations.append("⚠️ 發現多個警告，建議檢查和優化")
            diagnosis['overall_health'] = 'WARNING'
        elif warning_count > 0:
            recommendations.append("💡 發現輕微問題，建議定期檢查")
            diagnosis['overall_health'] = 'MINOR_ISSUES'
        else:
            recommendations.append("✅ 系統狀態良好")
            diagnosis['overall_health'] = 'HEALTHY'
        
        # 具體建議
        if any('記憶體' in issue for issue in all_issues):
            recommendations.append("考慮啟用流式處理模式")
        
        if any('精度' in issue for issue in all_issues):
            recommendations.append("檢查時間基準設置和TLE數據品質")
        
        if any('性能' in issue for issue in all_issues):
            recommendations.append("優化計算算法或增加計算資源")
        
        if any('依賴' in issue or '套件' in issue for issue in all_issues):
            recommendations.append("安裝缺失的依賴套件")
        
        diagnosis['recommendations'] = recommendations
    
    def export_diagnosis_report(self, file_path: str):
        """導出診斷報告"""
        if not self.diagnostic_results:
            logger.error("無診斷結果可導出")
            return
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.diagnostic_results, f, 
                         indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"診斷報告已導出到: {file_path}")
        except Exception as e:
            logger.error(f"導出診斷報告失敗: {e}")
    
    def quick_health_check(self) -> str:
        """快速健康檢查"""
        try:
            # 基本環境檢查
            if sys.version_info < (3, 8):
                return "CRITICAL: Python版本過低"
            
            # 記憶體檢查
            memory = psutil.virtual_memory()
            if memory.available < 1 * 1024**3:
                return "WARNING: 記憶體不足"
            
            # 依賴檢查
            try:
                import numpy, skyfield, astropy
                return "HEALTHY: 基本環境正常"
            except ImportError as e:
                return f"ERROR: 缺少依賴 {e}"
                
        except Exception as e:
            return f"ERROR: 健康檢查失敗 {e}"
```

### 2. 時間基準錯誤專項診斷

**debugging/time_diagnosis.py 實現：**
```python
#!/usr/bin/env python3
"""
時間基準專項診斷
針對最常見的時間基準錯誤提供專項診斷
"""

import logging
from typing import Dict, List
from datetime import datetime, timezone, timedelta
import numpy as np

from ..data.parser import TLEData
from ..calculation.sgp4_engine import SGP4Calculator

logger = logging.getLogger(__name__)

class TimeBasisDiagnostic:
    """時間基準專項診斷"""
    
    def diagnose_time_basis_error(self, 
                                tle_data: TLEData, 
                                calculation_time: datetime) -> Dict:
        """
        診斷時間基準錯誤
        
        這是最常見和最致命的錯誤：8000+衛星→0顆可見
        
        Args:
            tle_data: TLE數據
            calculation_time: 計算時間
            
        Returns:
            Dict: 診斷結果
        """
        diagnosis = {
            'error_detected': False,
            'error_type': None,
            'severity': 'INFO',
            'time_analysis': {},
            'recommendations': []
        }
        
        try:
            # 獲取TLE epoch時間
            tle_epoch = tle_data.get_epoch_datetime()
            
            # 計算時間差
            time_diff = (calculation_time - tle_epoch).total_seconds()
            time_diff_days = time_diff / (24 * 3600)
            time_diff_hours = time_diff / 3600
            
            diagnosis['time_analysis'] = {
                'tle_epoch': tle_epoch.isoformat(),
                'calculation_time': calculation_time.isoformat(),
                'time_difference_seconds': time_diff,
                'time_difference_days': time_diff_days,
                'time_difference_hours': time_diff_hours
            }
            
            # 檢查時間基準錯誤
            if abs(time_diff_days) > 30:
                diagnosis['error_detected'] = True
                diagnosis['error_type'] = 'CRITICAL_TIME_GAP'
                diagnosis['severity'] = 'CRITICAL'
                diagnosis['recommendations'].append(
                    f"時間差過大({time_diff_days:.1f}天)！"
                    "這會導致軌道預測完全不準確。"
                    "請使用TLE epoch時間作為基準時間進行計算。"
                )
            elif abs(time_diff_days) > 14:
                diagnosis['error_detected'] = True
                diagnosis['error_type'] = 'WARNING_TIME_GAP'
                diagnosis['severity'] = 'WARNING'
                diagnosis['recommendations'].append(
                    f"時間差較大({time_diff_days:.1f}天)，"
                    "軌道預測精度可能下降。"
                )
            elif abs(time_diff_days) > 7:
                diagnosis['error_detected'] = True
                diagnosis['error_type'] = 'MINOR_TIME_GAP'
                diagnosis['severity'] = 'INFO'
                diagnosis['recommendations'].append(
                    f"時間差{time_diff_days:.1f}天，在可接受範圍內但建議更新TLE數據。"
                )
            
            # 檢查是否使用了當前時間而非epoch時間
            current_time = datetime.now(timezone.utc)
            diff_to_current = abs((calculation_time - current_time).total_seconds())
            
            if diff_to_current < 3600:  # 計算時間接近當前時間
                diagnosis['time_analysis']['likely_using_current_time'] = True
                if abs(time_diff_days) > 3:
                    diagnosis['error_detected'] = True
                    diagnosis['error_type'] = 'CURRENT_TIME_USAGE_ERROR'
                    diagnosis['severity'] = 'CRITICAL'
                    diagnosis['recommendations'].append(
                        "⚠️ 檢測到可能使用了當前時間進行軌道計算！"
                        "這是導致8000+衛星→0顆可見的主要原因。"
                        "正確做法：使用TLE epoch時間作為計算基準。"
                    )
            else:
                diagnosis['time_analysis']['likely_using_current_time'] = False
            
            # 檢查epoch時間是否合理
            if tle_epoch.year < 1957 or tle_epoch.year > 2030:
                diagnosis['error_detected'] = True
                diagnosis['error_type'] = 'INVALID_EPOCH_YEAR'
                diagnosis['severity'] = 'ERROR'
                diagnosis['recommendations'].append(
                    f"TLE epoch年份異常: {tle_epoch.year}，"
                    "請檢查TLE數據解析是否正確。"
                )
            
        except Exception as e:
            diagnosis['error_detected'] = True
            diagnosis['error_type'] = 'TIME_ANALYSIS_FAILED'
            diagnosis['severity'] = 'ERROR'
            diagnosis['recommendations'].append(f"時間分析失敗: {e}")
        
        return diagnosis
    
    def demonstrate_time_basis_impact(self, tle_data: TLEData) -> Dict:
        """
        演示時間基準錯誤的影響
        
        Args:
            tle_data: TLE數據
            
        Returns:
            Dict: 影響演示結果
        """
        calculator = SGP4Calculator()
        tle_epoch = tle_data.get_epoch_datetime()
        current_time = datetime.now(timezone.utc)
        
        results = {}
        
        try:
            # 1. 正確方法：使用TLE epoch時間
            correct_result = calculator.calculate_satellite_position(
                tle_data, tle_epoch
            )
            
            # 2. 錯誤方法：使用當前時間
            wrong_result = calculator.calculate_satellite_position(
                tle_data, current_time
            )
            
            # 計算位置差異
            correct_pos = np.array(correct_result['position_eci_km'])
            wrong_pos = np.array(wrong_result['position_eci_km'])
            position_difference = np.linalg.norm(wrong_pos - correct_pos)
            
            # 計算高度差異
            earth_radius = 6371.0
            correct_alt = np.linalg.norm(correct_pos) - earth_radius
            wrong_alt = np.linalg.norm(wrong_pos) - earth_radius
            
            results = {
                'time_difference_days': (current_time - tle_epoch).total_seconds() / (24 * 3600),
                'correct_method': {
                    'calculation_time': tle_epoch.isoformat(),
                    'position_eci_km': correct_pos.tolist(),
                    'altitude_km': correct_alt,
                    'method': 'TLE epoch時間（正確）'
                },
                'wrong_method': {
                    'calculation_time': current_time.isoformat(),
                    'position_eci_km': wrong_pos.tolist(),
                    'altitude_km': wrong_alt,
                    'method': '當前系統時間（錯誤）'
                },
                'impact_analysis': {
                    'position_difference_km': position_difference,
                    'altitude_difference_km': abs(wrong_alt - correct_alt),
                    'impact_severity': self._assess_impact_severity(position_difference)
                }
            }
            
        except Exception as e:
            results['error'] = f"影響演示失敗: {e}"
        
        return results
    
    def _assess_impact_severity(self, position_diff_km: float) -> str:
        """評估時間基準錯誤的影響嚴重程度"""
        if position_diff_km > 10000:
            return "CATASTROPHIC - 軌道預測完全錯誤"
        elif position_diff_km > 1000:
            return "SEVERE - 軌道預測嚴重偏差"
        elif position_diff_km > 100:
            return "MAJOR - 軌道預測重大偏差"
        elif position_diff_km > 10:
            return "MODERATE - 軌道預測中度偏差"
        elif position_diff_km > 1:
            return "MINOR - 軌道預測輕微偏差"
        else:
            return "NEGLIGIBLE - 影響可忽略"
```

## 自動化故障修復機制

### 自動修復器實現

**debugging/auto_repair.py 實現：**
```python
#!/usr/bin/env python3
"""
自動故障修復器
實現常見問題的自動檢測和修復
"""

import logging
import os
import shutil
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class AutoRepairSystem:
    """自動故障修復系統"""
    
    def __init__(self):
        """初始化自動修復系統"""
        self.repair_log = []
        self.supported_repairs = [
            'clear_cache',
            'reset_configuration',
            'cleanup_memory',
            'update_time_reference',
            'repair_tle_data',
            'optimize_performance'
        ]
    
    def attempt_auto_repair(self, diagnosis: Dict) -> Dict:
        """
        嘗試自動修復檢測到的問題
        
        Args:
            diagnosis: 診斷結果
            
        Returns:
            Dict: 修復結果
        """
        repair_result = {
            'timestamp': datetime.now().isoformat(),
            'attempted_repairs': [],
            'successful_repairs': [],
            'failed_repairs': [],
            'recommendations_for_manual_fix': []
        }
        
        issues = diagnosis.get('issues_found', [])
        
        for issue in issues:
            repair_action = self._identify_repair_action(issue)
            
            if repair_action:
                repair_result['attempted_repairs'].append({
                    'issue': issue,
                    'action': repair_action
                })
                
                success = self._execute_repair(repair_action, issue)
                
                if success:
                    repair_result['successful_repairs'].append(repair_action)
                    logger.info(f"自動修復成功: {repair_action}")
                else:
                    repair_result['failed_repairs'].append(repair_action)
                    repair_result['recommendations_for_manual_fix'].append(
                        self._get_manual_fix_recommendation(issue)
                    )
                    logger.warning(f"自動修復失敗: {repair_action}")
            else:
                repair_result['recommendations_for_manual_fix'].append(
                    self._get_manual_fix_recommendation(issue)
                )
        
        return repair_result
    
    def _identify_repair_action(self, issue: str) -> Optional[str]:
        """識別問題對應的修復動作"""
        issue_lower = issue.lower()
        
        if '快取' in issue_lower or 'cache' in issue_lower:
            return 'clear_cache'
        elif '記憶體' in issue_lower or 'memory' in issue_lower:
            return 'cleanup_memory'
        elif '時間' in issue_lower or 'time' in issue_lower or 'epoch' in issue_lower:
            return 'update_time_reference'
        elif 'tle' in issue_lower and ('格式' in issue_lower or '解析' in issue_lower):
            return 'repair_tle_data'
        elif '性能' in issue_lower or 'performance' in issue_lower:
            return 'optimize_performance'
        elif '配置' in issue_lower or 'config' in issue_lower:
            return 'reset_configuration'
        else:
            return None
    
    def _execute_repair(self, repair_action: str, issue: str) -> bool:
        """執行修復動作"""
        try:
            if repair_action == 'clear_cache':
                return self._clear_all_caches()
            elif repair_action == 'cleanup_memory':
                return self._cleanup_memory()
            elif repair_action == 'update_time_reference':
                return self._update_time_reference()
            elif repair_action == 'repair_tle_data':
                return self._repair_tle_data()
            elif repair_action == 'optimize_performance':
                return self._optimize_performance()
            elif repair_action == 'reset_configuration':
                return self._reset_configuration()
            else:
                return False
        except Exception as e:
            logger.error(f"執行修復動作 {repair_action} 時發生錯誤: {e}")
            return False
    
    def _clear_all_caches(self) -> bool:
        """清除所有快取"""
        try:
            # 清除計算器快取
            from ..calculation.sgp4_engine import SGP4Calculator
            calculator = SGP4Calculator()
            calculator.clear_cache()
            
            # 清除數據載入器快取
            from ..data.loader import TLEDataLoader
            loader = TLEDataLoader()
            loader.clear_cache()
            
            logger.info("所有快取已清除")
            return True
        except Exception as e:
            logger.error(f"清除快取失敗: {e}")
            return False
    
    def _cleanup_memory(self) -> bool:
        """清理記憶體"""
        try:
            import gc
            
            # 強制垃圾回收
            collected = gc.collect()
            
            # 清除快取
            self._clear_all_caches()
            
            logger.info(f"記憶體清理完成，回收了 {collected} 個對象")
            return True
        except Exception as e:
            logger.error(f"記憶體清理失敗: {e}")
            return False
    
    def _update_time_reference(self) -> bool:
        """更新時間基準設置"""
        try:
            # 這個修復主要是提醒和配置檢查
            logger.info("時間基準檢查：確保使用TLE epoch時間進行計算")
            
            # 檢查是否有時間基準配置檔案
            config_file = 'time_config.json'
            if os.path.exists(config_file):
                import json
                with open(config_file, 'r') as f:
                    config = json.load(f)
                
                # 更新配置確保使用正確的時間基準
                config['use_tle_epoch_time'] = True
                config['warn_large_time_gap'] = True
                config['max_time_gap_days'] = 30
                
                with open(config_file, 'w') as f:
                    json.dump(config, f, indent=2)
                
                logger.info("時間基準配置已更新")
            else:
                # 創建預設時間基準配置
                default_config = {
                    'use_tle_epoch_time': True,
                    'warn_large_time_gap': True,
                    'max_time_gap_days': 30,
                    'created_by_auto_repair': True,
                    'creation_time': datetime.now().isoformat()
                }
                
                with open(config_file, 'w') as f:
                    json.dump(default_config, f, indent=2)
                
                logger.info("創建了預設時間基準配置")
            
            return True
        except Exception as e:
            logger.error(f"更新時間基準失敗: {e}")
            return False
    
    def _repair_tle_data(self) -> bool:
        """修復TLE數據問題"""
        try:
            # 這裡實現基本的TLE數據修復邏輯
            # 實際應用中可能需要更複雜的修復策略
            
            logger.info("TLE數據修復：建議重新下載最新的TLE數據")
            
            # 創建數據修復建議檔案
            repair_suggestions = {
                'tle_data_repair_suggestions': [
                    '檢查TLE數據來源是否正確',
                    '驗證TLE檔案編碼格式（UTF-8）',
                    '確認TLE行格式符合標準（每組3行）',
                    '檢查TLE檢查碼是否正確',
                    '考慮從Space-Track.org重新下載最新數據'
                ],
                'generated_time': datetime.now().isoformat()
            }
            
            import json
            with open('tle_repair_suggestions.json', 'w') as f:
                json.dump(repair_suggestions, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            logger.error(f"TLE數據修復建議生成失敗: {e}")
            return False
    
    def _optimize_performance(self) -> bool:
        """優化性能設置"""
        try:
            # 創建性能優化配置
            perf_config = {
                'batch_size': 100,
                'max_threads': 4,
                'enable_caching': True,
                'memory_limit_mb': 4096,
                'enable_stream_processing': True,
                'optimization_applied': True,
                'applied_time': datetime.now().isoformat()
            }
            
            import json
            with open('performance_config.json', 'w') as f:
                json.dump(perf_config, f, indent=2)
            
            logger.info("性能優化配置已應用")
            return True
        except Exception as e:
            logger.error(f"性能優化失敗: {e}")
            return False
    
    def _reset_configuration(self) -> bool:
        """重置配置到預設狀態"""
        try:
            config_files = [
                'config.json',
                'time_config.json', 
                'performance_config.json'
            ]
            
            # 備份現有配置
            backup_dir = f'config_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
            os.makedirs(backup_dir, exist_ok=True)
            
            for config_file in config_files:
                if os.path.exists(config_file):
                    shutil.copy2(config_file, os.path.join(backup_dir, config_file))
                    os.remove(config_file)
            
            logger.info(f"配置已重置，備份保存在 {backup_dir}")
            return True
        except Exception as e:
            logger.error(f"重置配置失敗: {e}")
            return False
    
    def _get_manual_fix_recommendation(self, issue: str) -> str:
        """獲取手動修復建議"""
        issue_lower = issue.lower()
        
        if 'python版本' in issue_lower or 'python' in issue_lower and '版本' in issue_lower:
            return "請升級Python到3.8或更高版本"
        elif '套件' in issue_lower or 'package' in issue_lower:
            return "請安裝缺失的Python套件：pip install -r requirements.txt"
        elif '權限' in issue_lower or 'permission' in issue_lower:
            return "請檢查檔案和目錄權限設置"
        elif '磁碟空間' in issue_lower or 'disk' in issue_lower:
            return "請清理磁碟空間或移動到更大的儲存設備"
        elif 'tle' in issue_lower and '時效' in issue_lower:
            return "請從Space-Track.org下載最新的TLE數據"
        else:
            return f"手動檢查和修復：{issue}"
```

## 階段總結

### 階段8學習成果確認：

**掌握的核心技術：**
- 系統性故障診斷和分類方法
- 自動化問題檢測和修復機制
- 時間基準錯誤的專項診斷技術
- 生產級系統的監控和維運技能
- 複雜系統的故障隔離和恢復策略

**完成的除錯工作：**
- DiagnosticTool綜合診斷系統
- TimeBasisDiagnostic時間專項診斷
- AutoRepairSystem自動修復系統
- 完整的故障分類和處理流程
- 詳細的修復建議和操作指南

**實際應用能力：**
- 能夠快速定位和解決衛星軌道計算系統故障
- 具備複雜系統的運維和故障排除經驗
- 掌握自動化監控和修復技術
- 理解航太系統的高可靠性和容錯設計

**完整課程總結：**
經過8個階段的系統學習，您現在具備了：
1. **LEO衛星通訊系統基礎知識** (階段1)
2. **TLE數據格式的完全掌握** (階段2)
3. **SGP4算法的深度理解** (階段3)
4. **座標系統轉換的精確實現** (階段4)
5. **Stage1TLEProcessor的架構設計** (階段5)
6. **完整系統的程式實作** (階段6)
7. **數據驗證和品質控制** (階段7)
8. **除錯和故障排除** (階段8)

**職業成就解鎖：**
- ✅ 衛星系統工程師核心技能
- ✅ 8000+顆衛星批量處理能力
- ✅ 生產級軟體開發經驗
- ✅ 航太工程實際應用技術
- ✅ 學術研究和論文發表基礎

## 故障排除最佳實踐

### 1. 金律：時間基準絕不出錯
- **永遠使用TLE epoch時間作為計算基準**
- **絕不使用當前系統時間進行軌道計算**
- **時間差>3天立即發出警告**

### 2. 診斷優先順序
1. **時間基準檢查** - 最常見致命錯誤
2. **TLE數據格式驗證** - 基礎數據完整性
3. **物理合理性檢查** - 結果正確性驗證
4. **系統資源監控** - 性能和穩定性

### 3. 自動化修復原則
- **能自動修復的問題立即修復**
- **不能自動修復的提供明確指導**
- **所有修復動作都有完整記錄**
- **關鍵問題需要人工確認**

### 4. 預防性維護
- **定期更新TLE數據（建議每週）**
- **監控系統性能指標**
- **定期進行精度比較測試**
- **維護詳細的操作日誌**

**恭喜！您已完成Stage1TLEProcessor的完整開發課程！** 🎉