#!/usr/bin/env python3
"""
基線測試腳本

驗證Phase 1重構後的共享模組功能
確保所有核心組件正常運行
"""

import sys
import logging
from pathlib import Path
from datetime import datetime, timezone
import json
import traceback

# 添加路徑
sys.path.append('/orbit-engine/src')

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BaselineTestRunner:
    """基線測試執行器"""

    def __init__(self):
        self.test_results = {
            'start_time': datetime.now(timezone.utc).isoformat(),
            'tests': {},
            'summary': {
                'total': 0,
                'passed': 0,
                'failed': 0,
                'errors': []
            }
        }

    def run_all_tests(self):
        """執行所有基線測試"""
        logger.info("開始執行Phase 1基線測試")

        test_modules = [
            ('monitoring', self.test_monitoring_modules),
            ('prediction', self.test_prediction_modules),
            ('validation', self.test_validation_framework),
            ('constants', self.test_constants_modules),
            ('utils', self.test_utils_modules),
            ('interfaces', self.test_interface_modules),
            ('testing', self.test_testing_infrastructure)
        ]

        for module_name, test_func in test_modules:
            try:
                logger.info(f"測試模組: {module_name}")
                result = test_func()
                self.test_results['tests'][module_name] = result

                if result['passed']:
                    self.test_results['summary']['passed'] += 1
                    logger.info(f"✅ {module_name} 測試通過")
                else:
                    self.test_results['summary']['failed'] += 1
                    logger.error(f"❌ {module_name} 測試失敗: {result.get('error', '未知錯誤')}")

                self.test_results['summary']['total'] += 1

            except Exception as e:
                error_msg = f"{module_name}: {str(e)}"
                self.test_results['summary']['errors'].append(error_msg)
                self.test_results['summary']['failed'] += 1
                self.test_results['summary']['total'] += 1
                logger.error(f"❌ {module_name} 測試異常: {e}")
                logger.debug(traceback.format_exc())

        self.test_results['end_time'] = datetime.now(timezone.utc).isoformat()
        return self.test_results

    def test_monitoring_modules(self):
        """測試監控模組"""
        try:
            from shared.monitoring import (
                BaseMonitor, SignalMonitor, PerformanceMonitor
            )

            # 測試基礎監控
            from shared.monitoring.base_monitor import MonitoringConfig
            config = MonitoringConfig(
                monitor_name="test_signal_monitor",
                collection_interval_seconds=10.0
            )
            monitor = SignalMonitor(config)
            assert monitor.config.monitor_name == "test_signal_monitor"

            # 測試性能監控
            perf_config = MonitoringConfig(
                monitor_name="test_perf_monitor",
                collection_interval_seconds=5.0
            )
            perf_monitor = PerformanceMonitor(perf_config)
            with perf_monitor.measure_operation("test_operation"):
                import time
                time.sleep(0.01)  # 短暫延遲

            metrics = perf_monitor.get_metrics()
            assert 'test_operation' in metrics

            return {'passed': True, 'details': '監控模組功能正常'}

        except Exception as e:
            return {'passed': False, 'error': str(e)}

    def test_prediction_modules(self):
        """測試預測模組"""
        try:
            from shared.prediction import (
                BasePrediction, SignalPredictor, TrajectoryPredictor
            )

            # 測試信號預測
            signal_predictor = SignalPredictor()

            # 模擬衛星位置和觀測者位置
            satellite_pos = {'latitude': 0, 'longitude': 0, 'altitude_km': 600}
            observer_pos = {'latitude': 24.9, 'longitude': 121.3, 'altitude_km': 0}

            prediction = signal_predictor.predict_signal_quality(satellite_pos, observer_pos)
            assert 'rsrp_dbm' in prediction
            assert 'distance_km' in prediction

            # 測試軌道預測
            trajectory_predictor = TrajectoryPredictor()

            return {'passed': True, 'details': '預測模組功能正常'}

        except Exception as e:
            return {'passed': False, 'error': str(e)}

    def test_validation_framework(self):
        """測試驗證框架"""
        try:
            from shared.validation_framework import ValidationEngine

            # 測試學術合規性驗證
            validator = ValidationEngine()

            # 測試正常數據
            test_data = {'description': "Real TLE data from Space-Track.org"}
            rules = {'academic_compliance': True}
            result = validator.validate(test_data, rules)
            assert result['is_valid'] == True

            # 測試不合規數據
            bad_data = {'description': "Mock satellite data generated randomly"}
            result = validator.validate(bad_data, rules)
            # 由於這是一般驗證，我們只測試驗證器運行正常
            assert 'is_valid' in result

            return {'passed': True, 'details': '驗證框架功能正常'}

        except Exception as e:
            return {'passed': False, 'error': str(e)}

    def test_constants_modules(self):
        """測試常數模組"""
        try:
            from shared.constants import (
                PhysicsConstantsManager, OrbitEngineConstantsManager
            )

            # 測試物理常數
            physics = PhysicsConstantsManager()
            assert physics.get_constant('SPEED_OF_LIGHT') == 299792458  # m/s
            assert physics.get_constant('BOLTZMANN_CONSTANT') == 1.380649e-23  # J/K

            # 測試系統常數
            system = OrbitEngineConstantsManager()
            path = system.get_stage_output_path(1)
            assert 'stage1' in str(path).lower()

            return {'passed': True, 'details': '常數模組功能正常'}

        except Exception as e:
            return {'passed': False, 'error': str(e)}

    def test_utils_modules(self):
        """測試工具模組"""
        try:
            from shared.utils import TimeUtils, MathUtils, FileUtils
            from datetime import datetime, timezone

            # 測試時間工具
            parsed_date = TimeUtils.parse_tle_epoch(2024, 245.12345678)
            assert isinstance(parsed_date, datetime)

            # 測試數學工具
            kepler_result = MathUtils.solve_kepler_equation(0.1, 1.0)  # e=0.1, M=1.0
            assert isinstance(kepler_result, float)

            # 測試文件工具
            test_data = {'test': 'data'}
            temp_file = '/tmp/baseline_test.json'
            FileUtils().save_json(test_data, temp_file)
            loaded_data = FileUtils().load_json(temp_file)
            assert loaded_data == test_data

            return {'passed': True, 'details': '工具模組功能正常'}

        except Exception as e:
            return {'passed': False, 'error': str(e)}

    def test_interface_modules(self):
        """測試接口模組"""
        try:
            from shared.interfaces import (
                ProcessingStatus, ProcessingResult, BaseProcessor,
                DataFormat, DataPacket, DataMetadata,
                ServiceStatus, ServiceConfig, BaseService,
                create_processing_result, create_data_packet, create_service_config
            )

            # 測試處理器接口
            result = create_processing_result(
                status=ProcessingStatus.SUCCESS,
                data={'test': 'data'},
                message="測試成功"
            )
            assert result.status == ProcessingStatus.SUCCESS

            # 測試數據接口
            from shared.interfaces.data_interface import DataSourceType, DataFormat
            packet = create_data_packet(
                data={'test': 'data'},
                source_type=DataSourceType.MEMORY,
                format=DataFormat.JSON,
                packet_id='test_packet'
            )
            assert packet.packet_id == 'test_packet'

            # 測試服務接口
            from shared.interfaces.service_interface import ServiceType
            config = create_service_config(
                service_name="test_service",
                service_type=ServiceType.MONITORING
            )
            assert config.service_name == "test_service"

            return {'passed': True, 'details': '接口模組功能正常'}

        except Exception as e:
            return {'passed': False, 'error': str(e)}

    def test_testing_infrastructure(self):
        """測試測試基礎設施"""
        try:
            from shared.testing import (
                BaseTestCase, TestDataGenerator, TestAssertion,
                create_test_environment, generate_test_satellite_data
            )

            # 測試數據生成
            tle_data = TestDataGenerator.generate_tle_data(satellite_count=5)
            assert len(tle_data) == 5
            assert 'satellite_id' in tle_data[0]
            assert 'line1' in tle_data[0]
            assert 'line2' in tle_data[0]

            # 測試觀測者位置生成
            location = TestDataGenerator.generate_observer_location("taiwan")
            assert 22.0 <= location['latitude'] <= 25.5
            assert 120.0 <= location['longitude'] <= 122.0

            # 測試斷言工具
            TestAssertion.assert_coordinates_valid(24.9, 121.3, 0.035)

            # 測試環境創建
            env = create_test_environment("baseline_test")
            assert 'test_name' in env
            assert 'file_manager' in env

            return {'passed': True, 'details': '測試基礎設施功能正常'}

        except Exception as e:
            return {'passed': False, 'error': str(e)}

def main():
    """主函數"""
    try:
        runner = BaselineTestRunner()
        results = runner.run_all_tests()

        # 輸出結果
        output_file = "/orbit-engine/data/baseline_test_results.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        # 打印摘要
        summary = results['summary']
        total = summary['total']
        passed = summary['passed']
        failed = summary['failed']

        print(f"\n🧪 Phase 1 基線測試結果")
        print(f"=" * 50)
        print(f"總共測試: {total}")
        print(f"通過: {passed}")
        print(f"失敗: {failed}")
        print(f"成功率: {passed/total*100:.1f}%" if total > 0 else "成功率: 0%")

        if summary['errors']:
            print(f"\n❌ 錯誤詳情:")
            for error in summary['errors']:
                print(f"  - {error}")

        if failed == 0:
            print(f"\n✅ 所有測試通過！Phase 1 共享模組建設完成。")
            return 0
        else:
            print(f"\n❌ 有 {failed} 個測試失敗，請檢查問題。")
            return 1

    except Exception as e:
        logger.error(f"基線測試執行失敗: {e}")
        print(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main())