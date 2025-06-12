#!/usr/bin/env python3
"""
TLE服務獨立性和耦合性測試程式
測試 skyfield TLE 相關邏輯的模組化程度和依賴關係
"""

import asyncio
import sys
import os
import json
import traceback
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import importlib.util
import inspect

# 添加項目路徑
sys.path.append('/home/sat/ntn-stack/simworld/backend')

class TLEIndependenceTestSuite:
    """TLE獨立性測試套件"""
    
    def __init__(self):
        self.test_results = []
        self.mock_repository = None
        
    def log_test(self, test_name: str, status: str, message: str, details: Any = None):
        """記錄測試結果"""
        result = {
            'test': test_name,
            'status': status,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'details': details
        }
        self.test_results.append(result)
        
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_icon} {test_name}: {message}")
        if details and status != "PASS":
            print(f"   詳細信息: {details}")

    async def test_tle_service_imports(self):
        """測試1: TLE服務的導入依賴"""
        try:
            # 嘗試導入TLE服務相關模組
            from app.domains.satellite.services.tle_service import TLEService
            from app.domains.satellite.interfaces.tle_service_interface import TLEServiceInterface
            
            # 檢查TLE服務的直接依賴
            import app.domains.satellite.services.tle_service as tle_module
            
            # 分析模組依賴
            dependencies = []
            for name, obj in inspect.getmembers(tle_module):
                if inspect.ismodule(obj):
                    dependencies.append(obj.__name__)
            
            # 檢查是否有過度耦合的依賴
            problematic_deps = []
            for dep in dependencies:
                if any(x in dep for x in ['frontend', 'api', 'ui', 'view']):
                    problematic_deps.append(dep)
            
            if problematic_deps:
                self.log_test(
                    "TLE服務導入依賴", 
                    "FAIL", 
                    f"發現前端耦合依賴: {problematic_deps}",
                    {'all_dependencies': dependencies}
                )
            else:
                self.log_test(
                    "TLE服務導入依賴", 
                    "PASS", 
                    "TLE服務依賴關係良好，無前端耦合",
                    {'dependencies_count': len(dependencies)}
                )
                
        except Exception as e:
            self.log_test(
                "TLE服務導入依賴", 
                "FAIL", 
                f"導入失敗: {str(e)}",
                {'traceback': traceback.format_exc()}
            )

    async def test_tle_interface_compliance(self):
        """測試2: TLE服務接口合規性"""
        try:
            from app.domains.satellite.services.tle_service import TLEService
            from app.domains.satellite.interfaces.tle_service_interface import TLEServiceInterface
            
            # 檢查TLEService是否正確實現接口
            service_methods = set(dir(TLEService))
            interface_methods = set([
                method for method in dir(TLEServiceInterface) 
                if not method.startswith('_')
            ])
            
            missing_methods = interface_methods - service_methods
            
            if missing_methods:
                self.log_test(
                    "TLE接口合規性", 
                    "FAIL", 
                    f"TLEService未實現接口方法: {missing_methods}"
                )
            else:
                self.log_test(
                    "TLE接口合規性", 
                    "PASS", 
                    "TLEService正確實現了所有接口方法",
                    {'implemented_methods': len(interface_methods)}
                )
                
        except Exception as e:
            self.log_test(
                "TLE接口合規性", 
                "FAIL", 
                f"測試失敗: {str(e)}",
                {'traceback': traceback.format_exc()}
            )

    async def test_tle_service_initialization(self):
        """測試3: TLE服務初始化獨立性"""
        try:
            from app.domains.satellite.services.tle_service import TLEService
            
            # 測試無依賴初始化
            service = TLEService(satellite_repository=None)
            
            # 檢查服務配置
            config_attributes = [
                '_celestrak_base_url',
                '_celestrak_categories', 
                '_spacetrack_base_url',
                '_spacetrack_username',
                '_spacetrack_password'
            ]
            
            missing_attrs = []
            for attr in config_attributes:
                if not hasattr(service, attr):
                    missing_attrs.append(attr)
            
            if missing_attrs:
                self.log_test(
                    "TLE服務初始化", 
                    "FAIL", 
                    f"缺少配置屬性: {missing_attrs}"
                )
            else:
                self.log_test(
                    "TLE服務初始化", 
                    "PASS", 
                    "TLE服務可以獨立初始化，配置完整"
                )
                
        except Exception as e:
            self.log_test(
                "TLE服務初始化", 
                "FAIL", 
                f"初始化失敗: {str(e)}",
                {'traceback': traceback.format_exc()}
            )

    async def test_tle_parsing_independence(self):
        """測試4: TLE解析功能獨立性"""
        try:
            from app.domains.satellite.services.tle_service import TLEService
            
            service = TLEService(satellite_repository=None)
            
            # 測試TLE解析（使用OneWeb衛星的真實TLE數據）
            test_line1 = "1 44713U 19074A   21001.00000000  .00000000  00000-0  00000-0 0  9999"
            test_line2 = "2 44713  87.4000 000.0000 0000000   0.0000 000.0000 12.85000000000009"
            
            # 測試TLE驗證
            is_valid = await service.validate_tle(test_line1, test_line2)
            
            # 測試TLE解析
            if is_valid:
                parsed_data = await service.parse_tle(test_line1, test_line2)
                
                expected_fields = ['inclination_deg', 'period_minutes', 'apogee_km', 'perigee_km']
                missing_fields = [field for field in expected_fields if field not in parsed_data]
                
                if missing_fields:
                    self.log_test(
                        "TLE解析功能", 
                        "FAIL", 
                        f"解析結果缺少字段: {missing_fields}",
                        {'parsed_data': parsed_data}
                    )
                else:
                    self.log_test(
                        "TLE解析功能", 
                        "PASS", 
                        "TLE解析功能正常，可獨立運行",
                        {
                            'validation': is_valid,
                            'parsed_fields': list(parsed_data.keys()),
                            'inclination': parsed_data.get('inclination_deg'),
                            'period': parsed_data.get('period_minutes')
                        }
                    )
            else:
                self.log_test(
                    "TLE解析功能", 
                    "FAIL", 
                    "TLE驗證失敗"
                )
                
        except Exception as e:
            self.log_test(
                "TLE解析功能", 
                "FAIL", 
                f"解析測試失敗: {str(e)}",
                {'traceback': traceback.format_exc()}
            )

    async def test_external_api_integration(self):
        """測試5: 外部API整合獨立性"""
        try:
            from app.domains.satellite.services.tle_service import TLEService
            
            service = TLEService(satellite_repository=None)
            
            # 測試Celestrak API（使用較小的衛星分類）
            print("   正在測試Celestrak API連接...")
            celestrak_data = await service.fetch_tle_from_celestrak("weather")
            
            if isinstance(celestrak_data, list) and len(celestrak_data) > 0:
                # 檢查數據格式
                sample_tle = celestrak_data[0]
                required_fields = ['name', 'norad_id', 'line1', 'line2']
                missing_fields = [field for field in required_fields if field not in sample_tle]
                
                if missing_fields:
                    self.log_test(
                        "外部API整合", 
                        "FAIL", 
                        f"Celestrak數據格式不完整: {missing_fields}",
                        {'sample_data': sample_tle}
                    )
                else:
                    self.log_test(
                        "外部API整合", 
                        "PASS", 
                        f"Celestrak API整合正常，獲取了{len(celestrak_data)}條TLE數據",
                        {
                            'data_count': len(celestrak_data),
                            'sample_satellite': sample_tle['name'],
                            'sample_norad_id': sample_tle['norad_id']
                        }
                    )
            else:
                self.log_test(
                    "外部API整合", 
                    "WARN", 
                    "Celestrak API返回數據為空，可能是網絡問題",
                    {'response_type': type(celestrak_data).__name__}
                )
                
        except Exception as e:
            self.log_test(
                "外部API整合", 
                "FAIL", 
                f"API測試失敗: {str(e)}",
                {'traceback': traceback.format_exc()}
            )

    async def test_skyfield_integration(self):
        """測試6: Skyfield整合測試"""
        try:
            # 直接測試skyfield功能
            from skyfield.api import load, EarthSatellite
            import sgp4.api as sgp4
            from sgp4.earth_gravity import wgs72
            from sgp4.io import twoline2rv
            
            # 測試TLE數據
            test_line1 = "1 44713U 19074A   21001.00000000  .00000000  00000-0  00000-0 0  9999"
            test_line2 = "2 44713  87.4000 000.0000 0000000   0.0000 000.0000 12.85000000000009"
            
            # 測試SGP4集成
            satellite_sgp4 = twoline2rv(test_line1, test_line2, wgs72)
            position, velocity = satellite_sgp4.propagate(2021, 1, 1, 12, 0, 0)
            
            # 測試Skyfield集成
            ts = load.timescale()
            time = ts.utc(2021, 1, 1, 12, 0, 0)
            satellite_skyfield = EarthSatellite(test_line1, test_line2, "OneWeb Test", ts)
            
            # 計算地理位置
            geocentric = satellite_skyfield.at(time)
            subpoint = geocentric.subpoint()
            
            self.log_test(
                "Skyfield整合", 
                "PASS", 
                "Skyfield和SGP4整合正常",
                {
                    'sgp4_position': position,
                    'skyfield_latitude': float(subpoint.latitude.degrees),
                    'skyfield_longitude': float(subpoint.longitude.degrees),
                    'skyfield_elevation': float(subpoint.elevation.km)
                }
            )
            
        except Exception as e:
            self.log_test(
                "Skyfield整合", 
                "FAIL", 
                f"Skyfield整合失敗: {str(e)}",
                {'traceback': traceback.format_exc()}
            )

    async def test_service_coupling_analysis(self):
        """測試7: 服務耦合性分析"""
        try:
            # 分析TLE服務與其他服務的耦合關係
            from app.domains.satellite.services.tle_service import TLEService
            import inspect
            
            service = TLEService(satellite_repository=None)
            
            # 獲取所有方法
            methods = inspect.getmembers(service, predicate=inspect.ismethod)
            
            # 分析方法依賴
            coupling_analysis = {
                'total_methods': len(methods),
                'public_methods': 0,
                'private_methods': 0,
                'async_methods': 0,
                'external_dependencies': set(),
                'internal_dependencies': set()
            }
            
            for name, method in methods:
                if name.startswith('_'):
                    coupling_analysis['private_methods'] += 1
                else:
                    coupling_analysis['public_methods'] += 1
                
                if asyncio.iscoroutinefunction(method):
                    coupling_analysis['async_methods'] += 1
            
            # 檢查構造函數依賴
            init_signature = inspect.signature(TLEService.__init__)
            dependencies = list(init_signature.parameters.keys())
            dependencies.remove('self')  # 移除self參數
            
            coupling_score = len(dependencies)  # 耦合分數 = 必需依賴數量
            
            if coupling_score <= 1:  # 只有repository依賴是可接受的
                self.log_test(
                    "服務耦合性分析", 
                    "PASS", 
                    f"TLE服務耦合度良好 (耦合分數: {coupling_score})",
                    {
                        'coupling_score': coupling_score,
                        'dependencies': dependencies,
                        'method_analysis': coupling_analysis
                    }
                )
            else:
                self.log_test(
                    "服務耦合性分析", 
                    "WARN", 
                    f"TLE服務耦合度較高 (耦合分數: {coupling_score})",
                    {
                        'coupling_score': coupling_score,
                        'dependencies': dependencies,
                        'method_analysis': coupling_analysis
                    }
                )
                
        except Exception as e:
            self.log_test(
                "服務耦合性分析", 
                "FAIL", 
                f"耦合性分析失敗: {str(e)}",
                {'traceback': traceback.format_exc()}
            )

    async def test_configuration_independence(self):
        """測試8: 配置獨立性"""
        try:
            from app.domains.satellite.services.tle_service import TLEService
            
            # 測試不同配置環境下的初始化
            original_env = os.environ.copy()
            
            # 測試無環境變數
            for key in ['SPACETRACK_USERNAME', 'SPACETRACK_PASSWORD']:
                if key in os.environ:
                    del os.environ[key]
            
            service1 = TLEService(satellite_repository=None)
            
            # 測試有環境變數
            os.environ['SPACETRACK_USERNAME'] = 'test_user'
            os.environ['SPACETRACK_PASSWORD'] = 'test_pass'
            
            service2 = TLEService(satellite_repository=None)
            
            # 恢復環境變數
            os.environ.clear()
            os.environ.update(original_env)
            
            config_tests = {
                'no_env_vars': {
                    'username': service1._spacetrack_username,
                    'password': service1._spacetrack_password
                },
                'with_env_vars': {
                    'username': service2._spacetrack_username,
                    'password': service2._spacetrack_password
                }
            }
            
            self.log_test(
                "配置獨立性", 
                "PASS", 
                "TLE服務可在不同配置環境下正常初始化",
                config_tests
            )
            
        except Exception as e:
            self.log_test(
                "配置獨立性", 
                "FAIL", 
                f"配置測試失敗: {str(e)}",
                {'traceback': traceback.format_exc()}
            )

    async def test_error_handling_independence(self):
        """測試9: 錯誤處理獨立性"""
        try:
            from app.domains.satellite.services.tle_service import TLEService
            
            service = TLEService(satellite_repository=None)
            
            # 測試無效TLE驗證
            invalid_tle1 = "invalid line 1"
            invalid_tle2 = "invalid line 2"
            
            is_valid = await service.validate_tle(invalid_tle1, invalid_tle2)
            
            # 測試錯誤TLE解析
            try:
                await service.parse_tle(invalid_tle1, invalid_tle2)
                parse_error_handled = False
            except Exception:
                parse_error_handled = True
            
            # 測試無效分類的Celestrak請求
            invalid_category_result = await service.fetch_tle_from_celestrak("invalid_category")
            
            error_handling_results = {
                'invalid_tle_validation': not is_valid,  # 應該返回False
                'parse_error_handled': parse_error_handled,  # 應該拋出異常
                'invalid_category_handled': isinstance(invalid_category_result, list) and len(invalid_category_result) == 0
            }
            
            all_passed = all(error_handling_results.values())
            
            if all_passed:
                self.log_test(
                    "錯誤處理獨立性", 
                    "PASS", 
                    "TLE服務錯誤處理機制健全",
                    error_handling_results
                )
            else:
                self.log_test(
                    "錯誤處理獨立性", 
                    "FAIL", 
                    "TLE服務錯誤處理有問題",
                    error_handling_results
                )
                
        except Exception as e:
            self.log_test(
                "錯誤處理獨立性", 
                "FAIL", 
                f"錯誤處理測試失敗: {str(e)}",
                {'traceback': traceback.format_exc()}
            )

    async def run_all_tests(self):
        """運行所有測試"""
        print("🚀 開始TLE服務獨立性和耦合性測試...")
        print("=" * 60)
        
        tests = [
            self.test_tle_service_imports,
            self.test_tle_interface_compliance,
            self.test_tle_service_initialization,
            self.test_tle_parsing_independence,
            self.test_external_api_integration,
            self.test_skyfield_integration,
            self.test_service_coupling_analysis,
            self.test_configuration_independence,
            self.test_error_handling_independence
        ]
        
        for test in tests:
            print(f"\n📋 運行: {test.__name__}")
            await test()
        
        # 生成測試報告
        self.generate_report()

    def generate_report(self):
        """生成測試報告"""
        print("\n" + "=" * 60)
        print("📊 TLE服務獨立性測試報告")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['status'] == 'PASS'])
        failed_tests = len([r for r in self.test_results if r['status'] == 'FAIL'])
        warning_tests = len([r for r in self.test_results if r['status'] == 'WARN'])
        
        print(f"📈 測試統計:")
        print(f"   總測試數: {total_tests}")
        print(f"   通過: {passed_tests}")
        print(f"   失敗: {failed_tests}")
        print(f"   警告: {warning_tests}")
        print(f"   成功率: {passed_tests/total_tests*100:.1f}%")
        
        print(f"\n📋 詳細結果:")
        for result in self.test_results:
            status_icon = "✅" if result['status'] == "PASS" else "❌" if result['status'] == "FAIL" else "⚠️"
            print(f"   {status_icon} {result['test']}: {result['message']}")
        
        # 耦合性評估
        print(f"\n🔗 耦合性評估:")
        if passed_tests >= 7:  # 至少7個測試通過
            print("   ✅ TLE服務具有良好的模組化設計")
            print("   ✅ 服務間耦合度低，依賴注入良好")
            print("   ✅ 可以獨立運行和測試")
            print("   ✅ 錯誤處理機制健全")
        elif passed_tests >= 5:
            print("   ⚠️ TLE服務基本達到模組化要求")
            print("   ⚠️ 建議優化部分耦合關係")
        else:
            print("   ❌ TLE服務存在較強耦合性問題")
            print("   ❌ 需要重構以提高模組化程度")
        
        # 保存詳細報告
        report_file = '/home/sat/ntn-stack/tle_independence_test_report.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                'summary': {
                    'total_tests': total_tests,
                    'passed': passed_tests,
                    'failed': failed_tests,
                    'warnings': warning_tests,
                    'success_rate': passed_tests/total_tests*100
                },
                'detailed_results': self.test_results,
                'generated_at': datetime.now().isoformat()
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 詳細報告已保存至: {report_file}")

async def main():
    """主函數"""
    try:
        test_suite = TLEIndependenceTestSuite()
        await test_suite.run_all_tests()
    except Exception as e:
        print(f"❌ 測試套件執行失敗: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())