#!/usr/bin/env python3
"""
重構驗證測試腳本

驗證所有重構後的組件是否正常工作:
1. 共享模組功能測試
2. 處理器接口一致性測試
3. 數據流完整性測試
4. 錯誤處理機制測試
"""

import sys
import os
import json
import time
import logging
from datetime import datetime, timezone
from pathlib import Path

# 確保能找到模組
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_shared_modules():
    """測試共享模組功能"""
    print('\n🧪 測試共享模組功能')
    print('-' * 50)

    test_results = {}

    # 測試接口模組
    try:
        from shared.interfaces import BaseProcessor, ProcessingStatus, ProcessingResult, create_processing_result
        test_result = create_processing_result(
            status=ProcessingStatus.SUCCESS,
            data={"test": "data"},
            message="測試成功"
        )
        assert test_result.status == ProcessingStatus.SUCCESS
        test_results['interfaces'] = {'status': '✅ 通過', 'details': '接口模組正常'}
        print('✅ 接口模組測試通過')
    except Exception as e:
        test_results['interfaces'] = {'status': '❌ 失敗', 'details': str(e)}
        print(f'❌ 接口模組測試失敗: {e}')

    # 測試驗證框架
    try:
        from shared.validation_framework import ValidationEngine
        validation_engine = ValidationEngine('test')
        test_results['validation_framework'] = {'status': '✅ 通過', 'details': '驗證框架初始化正常'}
        print('✅ 驗證框架測試通過')
    except Exception as e:
        test_results['validation_framework'] = {'status': '❌ 失敗', 'details': str(e)}
        print(f'❌ 驗證框架測試失敗: {e}')

    # 測試監控模組
    try:
        from shared.monitoring import PerformanceMonitor, MonitoringConfig
        config = MonitoringConfig(monitor_name="test_monitor")
        monitor = PerformanceMonitor(config)
        test_results['monitoring'] = {'status': '✅ 通過', 'details': '監控模組正常'}
        print('✅ 監控模組測試通過')
    except Exception as e:
        test_results['monitoring'] = {'status': '❌ 失敗', 'details': str(e)}
        print(f'❌ 監控模組測試失敗: {e}')

    # 測試預測模組
    try:
        from shared.prediction import SignalPredictor, PredictionConfig
        from datetime import timedelta
        config = PredictionConfig(
            predictor_name="test_predictor",
            model_type="physics_based",
            prediction_horizon=timedelta(minutes=30)
        )
        predictor = SignalPredictor(config)
        test_results['prediction'] = {'status': '✅ 通過', 'details': '預測模組正常'}
        print('✅ 預測模組測試通過')
    except Exception as e:
        test_results['prediction'] = {'status': '❌ 失敗', 'details': str(e)}
        print(f'❌ 預測模組測試失敗: {e}')

    # 測試工具模組
    try:
        from shared.utils import TimeUtils, MathUtils, FileUtils
        time_utils = TimeUtils()
        math_utils = MathUtils()
        file_utils = FileUtils()
        test_results['utils'] = {'status': '✅ 通過', 'details': '工具模組正常'}
        print('✅ 工具模組測試通過')
    except Exception as e:
        test_results['utils'] = {'status': '❌ 失敗', 'details': str(e)}
        print(f'❌ 工具模組測試失敗: {e}')

    # 測試常數管理
    try:
        from shared.constants import OrbitEngineConstantsManager, PhysicsConstantsManager
        system_constants = OrbitEngineConstantsManager()
        physics_constants = PhysicsConstantsManager()
        test_results['constants'] = {'status': '✅ 通過', 'details': '常數管理正常'}
        print('✅ 常數管理測試通過')
    except Exception as e:
        test_results['constants'] = {'status': '❌ 失敗', 'details': str(e)}
        print(f'❌ 常數管理測試失敗: {e}')

    return test_results


def test_processor_interfaces():
    """測試處理器接口一致性"""
    print('\n🔧 測試處理器接口一致性')
    print('-' * 50)

    test_results = {}

    # 測試各階段處理器的接口一致性
    processors_to_test = [
        ('Stage1DataLoadingProcessor', 'stages.stage1_orbital_calculation.stage1_data_loading_processor', 'create_stage1_processor'),
        ('Stage2OrbitalComputingProcessor', 'stages.stage2_visibility_filter.stage2_orbital_computing_processor', 'create_stage2_processor'),
        ('Stage3SignalAnalysisProcessor', 'stages.stage3_signal_analysis.stage3_signal_analysis_processor', 'create_stage3_processor'),
        ('TimeseriesPreprocessingProcessor', 'stages.stage4_timeseries_preprocessing.timeseries_preprocessing_processor', 'create_stage4_processor'),
        ('DataIntegrationProcessor', 'stages.stage5_data_integration.data_integration_processor', 'create_stage5_processor'),
        ('Stage6PersistenceProcessor', 'stages.stage6_dynamic_pool_planning.stage6_persistence_processor', 'create_stage6_processor')
    ]

    for processor_name, module_path, factory_function in processors_to_test:
        try:
            module = __import__(module_path, fromlist=[factory_function])
            factory = getattr(module, factory_function)
            processor = factory()

            # 檢查必需的方法
            required_methods = ['process', 'validate_input', 'extract_key_metrics']
            missing_methods = []

            for method in required_methods:
                if not hasattr(processor, method):
                    missing_methods.append(method)

            if missing_methods:
                test_results[processor_name] = {
                    'status': '❌ 失敗',
                    'details': f'缺少方法: {missing_methods}'
                }
                print(f'❌ {processor_name} 接口測試失敗: 缺少方法 {missing_methods}')
            else:
                test_results[processor_name] = {
                    'status': '✅ 通過',
                    'details': '接口完整'
                }
                print(f'✅ {processor_name} 接口測試通過')

        except Exception as e:
            test_results[processor_name] = {
                'status': '❌ 失敗',
                'details': f'導入或初始化失敗: {str(e)}'
            }
            print(f'❌ {processor_name} 測試失敗: {e}')

    return test_results


def test_data_flow():
    """測試數據流完整性"""
    print('\n📊 測試數據流完整性')
    print('-' * 50)

    test_results = {}

    try:
        # 測試 Stage 1 處理器
        from stages.stage1_orbital_calculation.stage1_data_loading_processor import create_stage1_processor
        stage1_processor = create_stage1_processor()

        # 測試輸入驗證
        validation_result = stage1_processor.validate_input(None)
        if validation_result:
            test_results['stage1_validation'] = {'status': '✅ 通過', 'details': 'Stage 1 輸入驗證正常'}
            print('✅ Stage 1 輸入驗證測試通過')
        else:
            test_results['stage1_validation'] = {'status': '⚠️ 警告', 'details': 'Stage 1 輸入驗證返回 False'}
            print('⚠️ Stage 1 輸入驗證返回 False (可能是設計行為)')

        # 測試關鍵指標提取
        metrics = stage1_processor.extract_key_metrics()
        if isinstance(metrics, dict) and 'stage' in metrics:
            test_results['stage1_metrics'] = {'status': '✅ 通過', 'details': f'指標: {metrics}'}
            print(f'✅ Stage 1 關鍵指標提取測試通過: {metrics}')
        else:
            test_results['stage1_metrics'] = {'status': '❌ 失敗', 'details': f'指標格式錯誤: {metrics}'}
            print(f'❌ Stage 1 關鍵指標提取測試失敗: {metrics}')

    except Exception as e:
        test_results['stage1_data_flow'] = {'status': '❌ 失敗', 'details': str(e)}
        print(f'❌ Stage 1 數據流測試失敗: {e}')

    try:
        # 測試處理結果格式
        from shared.interfaces import ProcessingStatus, create_processing_result

        sample_result = create_processing_result(
            status=ProcessingStatus.SUCCESS,
            data={'test': 'data'},
            message='測試成功'
        )

        if hasattr(sample_result, 'status') and hasattr(sample_result, 'data') and hasattr(sample_result, 'message'):
            test_results['result_format'] = {'status': '✅ 通過', 'details': '處理結果格式正確'}
            print('✅ 處理結果格式測試通過')
        else:
            test_results['result_format'] = {'status': '❌ 失敗', 'details': '處理結果格式錯誤'}
            print('❌ 處理結果格式測試失敗')

    except Exception as e:
        test_results['result_format'] = {'status': '❌ 失敗', 'details': str(e)}
        print(f'❌ 處理結果格式測試失敗: {e}')

    return test_results


def test_error_handling():
    """測試錯誤處理機制"""
    print('\n🛡️ 測試錯誤處理機制')
    print('-' * 50)

    test_results = {}

    try:
        # 測試無效輸入處理
        from stages.stage1_orbital_calculation.stage1_data_loading_processor import create_stage1_processor
        stage1_processor = create_stage1_processor()

        # 測試無效輸入
        invalid_inputs = [
            "invalid_string",
            12345,
            [],
            {'invalid': 'structure'}
        ]

        error_handled_correctly = True
        for invalid_input in invalid_inputs:
            try:
                result = stage1_processor.process(invalid_input)
                # 檢查是否正確處理錯誤
                if not result or result.status != ProcessingStatus.SUCCESS:
                    # 正確處理了錯誤
                    continue
                else:
                    # 沒有正確處理錯誤
                    error_handled_correctly = False
                    break
            except Exception:
                # 拋出異常也算是一種錯誤處理方式
                continue

        if error_handled_correctly:
            test_results['error_handling'] = {'status': '✅ 通過', 'details': '錯誤處理機制正常'}
            print('✅ 錯誤處理機制測試通過')
        else:
            test_results['error_handling'] = {'status': '❌ 失敗', 'details': '錯誤處理機制異常'}
            print('❌ 錯誤處理機制測試失敗')

    except Exception as e:
        test_results['error_handling'] = {'status': '❌ 失敗', 'details': str(e)}
        print(f'❌ 錯誤處理機制測試失敗: {e}')

    return test_results


def generate_validation_report(all_test_results):
    """生成驗證報告"""
    print('\n📋 生成驗證報告')
    print('-' * 50)

    report = {
        'validation_timestamp': datetime.now(timezone.utc).isoformat(),
        'test_results': all_test_results,
        'summary': {}
    }

    # 統計結果
    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    warning_tests = 0

    for category, tests in all_test_results.items():
        for test_name, result in tests.items():
            total_tests += 1
            if '✅' in result['status']:
                passed_tests += 1
            elif '❌' in result['status']:
                failed_tests += 1
            elif '⚠️' in result['status']:
                warning_tests += 1

    report['summary'] = {
        'total_tests': total_tests,
        'passed_tests': passed_tests,
        'failed_tests': failed_tests,
        'warning_tests': warning_tests,
        'pass_rate': round((passed_tests / total_tests) * 100, 2) if total_tests > 0 else 0
    }

    # 保存報告
    report_path = f"{project_root}/data/refactoring_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    os.makedirs(os.path.dirname(report_path), exist_ok=True)

    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f'✅ 驗證報告已保存: {report_path}')

    return report


def main():
    """主函數"""
    print('🚀 開始重構驗證測試')
    print('=' * 80)

    start_time = time.time()

    # 執行所有測試
    all_test_results = {}

    all_test_results['shared_modules'] = test_shared_modules()
    all_test_results['processor_interfaces'] = test_processor_interfaces()
    all_test_results['data_flow'] = test_data_flow()
    all_test_results['error_handling'] = test_error_handling()

    # 生成報告
    report = generate_validation_report(all_test_results)

    end_time = time.time()
    execution_time = end_time - start_time

    # 輸出總結
    print('\n🎯 驗證測試總結')
    print('=' * 80)
    print(f'執行時間: {execution_time:.2f} 秒')
    print(f'總測試數: {report["summary"]["total_tests"]}')
    print(f'通過測試: {report["summary"]["passed_tests"]} (✅)')
    print(f'失敗測試: {report["summary"]["failed_tests"]} (❌)')
    print(f'警告測試: {report["summary"]["warning_tests"]} (⚠️)')
    print(f'通過率: {report["summary"]["pass_rate"]}%')

    if report["summary"]["failed_tests"] == 0:
        print('\n🎉 重構驗證測試全部通過!')
        print('✅ 重構後的系統架構正常運行')
        success = True
    else:
        print('\n⚠️ 重構驗證測試發現問題')
        print('❌ 需要修復失敗的測試項目')
        success = False

    print('=' * 80)

    return 0 if success else 1


if __name__ == "__main__":
    exit(main())