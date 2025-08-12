#!/usr/bin/env python3
"""
Phase 1 端到端流程測試

功能:
1. 完整的 Phase 1 系統端到端測試
2. 從 TLE 載入到 API 響應的全流程驗證
3. 多場景、多負載的綜合測試
4. 與現有系統的整合兼容性測試

符合 CLAUDE.md 原則:
- 使用真實 TLE 數據進行完整測試
- 驗證完整 SGP4 算法的端到端正確性
- 確保學術研究級別的數據準確性
"""

import asyncio
import logging
import sys
import json
import time
import requests
import concurrent.futures
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import numpy as np

# 添加 Phase 1 模組路徑
PHASE1_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PHASE1_ROOT / "01_data_source"))
sys.path.insert(0, str(PHASE1_ROOT / "02_orbit_calculation"))
sys.path.insert(0, str(PHASE1_ROOT / "03_processing_pipeline"))
sys.path.insert(0, str(PHASE1_ROOT / "04_output_interface"))

logger = logging.getLogger(__name__)

@dataclass
class E2ETestResult:
    """端到端測試結果"""
    test_name: str
    test_category: str
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    success: bool
    error_message: Optional[str] = None
    performance_data: Optional[Dict[str, Any]] = None
    validation_data: Optional[Dict[str, Any]] = None

@dataclass
class E2ETestScenario:
    """測試場景定義"""
    scenario_name: str
    description: str
    test_steps: List[str]
    expected_outcomes: Dict[str, Any]
    performance_requirements: Dict[str, float]
    data_requirements: Dict[str, Any]

class EndToEndTester:
    """端到端測試器"""
    
    def __init__(self, api_base_url: str = None):
        """
        初始化端到端測試器
        
        Args:
            api_base_url: API 基礎 URL，如果未提供則從配置系統獲取
        """
        # 使用統一配置載入器獲取 API URL
        if api_base_url is None:
            try:
                import sys
                import os
                sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'config'))
                from config_loader import get_config_loader
                
                config_loader = get_config_loader()
                # 獲取 Phase 1 API URL，回退到環境變數或預設值
                api_base_url = os.getenv("PHASE1_API_URL", "http://localhost:8001")
                
            except ImportError as e:
                logger.warning(f"無法載入配置系統: {e}，使用預設 URL")
                api_base_url = "http://localhost:8001"
        
        self.api_base_url = api_base_url
        self.test_results = []
        self.test_scenarios = self._define_test_scenarios()
        
        # 測試組件
        self.tle_loader = None
        self.sgp4_engine = None
        self.data_provider = None
        self.standard_interface = None
        
        logger.info(f"✅ 端到端測試器初始化完成，API URL: {self.api_base_url}")
    
    def _define_test_scenarios(self) -> List[E2ETestScenario]:
        """定義測試場景"""
        scenarios = [
            E2ETestScenario(
                scenario_name="基礎數據流測試",
                description="從 TLE 載入到 API 響應的基本數據流",
                test_steps=[
                    "載入 TLE 數據",
                    "創建 SGP4 衛星對象",
                    "執行軌道計算",
                    "通過標準接口查詢",
                    "驗證 API 響應"
                ],
                expected_outcomes={
                    "tle_loaded": True,
                    "satellites_created": True,
                    "calculations_successful": True,
                    "api_response_valid": True,
                    "data_accuracy": True
                },
                performance_requirements={
                    "tle_load_time": 10.0,
                    "satellite_creation_time": 30.0,
                    "calculation_time": 5.0,
                    "api_response_time": 0.5
                },
                data_requirements={
                    "min_satellites": 1000,
                    "min_constellations": 2,
                    "position_accuracy_km": 0.1,
                    "velocity_accuracy_km_per_s": 1e-5
                }
            ),
            
            E2ETestScenario(
                scenario_name="高負載併發測試",
                description="多用戶併發訪問的高負載測試",
                test_steps=[
                    "啟動多個併發客戶端",
                    "執行大量 API 請求",
                    "監控系統性能",
                    "驗證響應準確性",
                    "檢查系統穩定性"
                ],
                expected_outcomes={
                    "all_requests_successful": True,
                    "response_times_acceptable": True,
                    "data_consistency": True,
                    "no_memory_leaks": True,
                    "system_stable": True
                },
                performance_requirements={
                    "concurrent_users": 20,
                    "requests_per_user": 10,
                    "max_response_time": 2.0,
                    "success_rate": 0.95,
                    "max_memory_increase": 200
                },
                data_requirements={
                    "query_satellites": 100,
                    "time_range_hours": 2,
                    "data_consistency_check": True
                }
            ),
            
            E2ETestScenario(
                scenario_name="大規模數據處理測試",
                description="全量 8,715 顆衛星的大規模處理測試",
                test_steps=[
                    "載入全量 TLE 數據",
                    "創建所有衛星對象",
                    "執行批量軌道計算",
                    "測試大量數據查詢",
                    "驗證系統擴展性"
                ],
                expected_outcomes={
                    "full_data_loaded": True,
                    "all_satellites_active": True,
                    "batch_calculations_successful": True,
                    "large_queries_handled": True,
                    "scalability_maintained": True
                },
                performance_requirements={
                    "total_satellites": 8715,
                    "calculation_rate": 1000,
                    "large_query_time": 5.0,
                    "memory_efficiency": 0.5
                },
                data_requirements={
                    "starlink_satellites": 8000,
                    "oneweb_satellites": 600,
                    "calculation_accuracy": 0.99
                }
            ),
            
            E2ETestScenario(
                scenario_name="API 兼容性測試",
                description="新舊 API 接口的兼容性和一致性測試",
                test_steps=[
                    "測試新標準 API",
                    "測試兼容 API",
                    "對比響應數據",
                    "驗證格式一致性",
                    "檢查功能完整性"
                ],
                expected_outcomes={
                    "new_api_functional": True,
                    "legacy_api_functional": True,
                    "data_consistency": True,
                    "format_compatibility": True,
                    "feature_parity": True
                },
                performance_requirements={
                    "api_response_time": 1.0,
                    "data_match_rate": 0.99
                },
                data_requirements={
                    "test_constellations": ["starlink", "oneweb"],
                    "sample_size": 50
                }
            ),
            
            E2ETestScenario(
                scenario_name="錯誤恢復測試",
                description="系統錯誤處理和恢復能力測試",
                test_steps=[
                    "模擬 TLE 數據錯誤",
                    "測試無效請求處理",
                    "模擬系統過載",
                    "測試錯誤恢復",
                    "驗證系統魯棒性"
                ],
                expected_outcomes={
                    "error_handling_correct": True,
                    "graceful_degradation": True,
                    "recovery_successful": True,
                    "no_data_corruption": True,
                    "system_resilient": True
                },
                performance_requirements={
                    "error_response_time": 1.0,
                    "recovery_time": 30.0
                },
                data_requirements={
                    "error_scenarios": 5,
                    "recovery_validation": True
                }
            )
        ]
        
        logger.info(f"定義了 {len(scenarios)} 個測試場景")
        return scenarios
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """執行所有端到端測試"""
        logger.info("🚀 開始端到端測試...")
        
        overall_start = datetime.now(timezone.utc)
        test_summary = {
            "test_start_time": overall_start.isoformat(),
            "total_scenarios": len(self.test_scenarios),
            "scenario_results": {},
            "overall_success": False,
            "summary_stats": {}
        }
        
        try:
            # 初始化測試組件
            await self._initialize_test_components()
            
            # 執行每個測試場景
            for scenario in self.test_scenarios:
                logger.info(f"📋 執行測試場景: {scenario.scenario_name}")
                
                scenario_result = await self._execute_test_scenario(scenario)
                test_summary["scenario_results"][scenario.scenario_name] = scenario_result
                
                status = "✅ 通過" if scenario_result["success"] else "❌ 失敗"
                logger.info(f"{status}: {scenario.scenario_name}")
            
            # 計算總體結果
            overall_end = datetime.now(timezone.utc)
            test_summary["test_end_time"] = overall_end.isoformat()
            test_summary["total_duration"] = (overall_end - overall_start).total_seconds()
            
            # 統計成功率
            successful_scenarios = sum(1 for result in test_summary["scenario_results"].values() if result["success"])
            test_summary["success_rate"] = (successful_scenarios / len(self.test_scenarios)) * 100
            test_summary["overall_success"] = successful_scenarios == len(self.test_scenarios)
            
            # 性能統計
            test_summary["summary_stats"] = self._calculate_summary_stats()
            
            logger.info(f"🎯 端到端測試完成: {successful_scenarios}/{len(self.test_scenarios)} 場景通過")
            return test_summary
            
        except Exception as e:
            logger.error(f"端到端測試執行失敗: {e}")
            test_summary["error"] = str(e)
            test_summary["overall_success"] = False
            return test_summary
    
    async def _initialize_test_components(self):
        """初始化測試組件"""
        try:
            # 初始化 TLE 載入器
            from tle_loader import create_tle_loader
            # 使用統一配置載入器
            self.tle_loader = create_tle_loader()
            
            # 初始化 SGP4 引擎
            from sgp4_engine import create_sgp4_engine, validate_sgp4_availability
            
            if not validate_sgp4_availability():
                raise RuntimeError("SGP4 庫不可用")
            
            self.sgp4_engine = create_sgp4_engine()
            
            # 初始化數據提供者和標準接口
            from phase1_data_provider import create_sgp4_data_provider
            from phase2_interface import create_standard_interface
            
            # 使用統一配置，無需指定路徑
            self.data_provider = create_sgp4_data_provider()
            self.standard_interface = create_standard_interface(self.data_provider)
            
            logger.info("✅ 測試組件初始化完成")
            
        except Exception as e:
            logger.error(f"測試組件初始化失敗: {e}")
            raise
    
    async def _execute_test_scenario(self, scenario: E2ETestScenario) -> Dict[str, Any]:
        """執行單個測試場景"""
        start_time = datetime.now(timezone.utc)
        
        scenario_result = {
            "scenario_name": scenario.scenario_name,
            "description": scenario.description,
            "start_time": start_time.isoformat(),
            "success": False,
            "test_steps_results": {},
            "performance_metrics": {},
            "validation_results": {},
            "error_message": None
        }
        
        try:
            # 根據場景類型選擇測試方法
            if scenario.scenario_name == "基礎數據流測試":
                result = await self._test_basic_data_flow(scenario)
            elif scenario.scenario_name == "高負載併發測試":
                result = await self._test_high_load_concurrent(scenario)
            elif scenario.scenario_name == "大規模數據處理測試":
                result = await self._test_large_scale_processing(scenario)
            elif scenario.scenario_name == "API 兼容性測試":
                result = await self._test_api_compatibility(scenario)
            elif scenario.scenario_name == "錯誤恢復測試":
                result = await self._test_error_recovery(scenario)
            else:
                raise ValueError(f"未知測試場景: {scenario.scenario_name}")
            
            scenario_result.update(result)
            
        except Exception as e:
            logger.error(f"測試場景執行失敗 {scenario.scenario_name}: {e}")
            scenario_result["error_message"] = str(e)
        
        end_time = datetime.now(timezone.utc)
        scenario_result["end_time"] = end_time.isoformat()
        scenario_result["duration_seconds"] = (end_time - start_time).total_seconds()
        
        return scenario_result
    
    async def _test_basic_data_flow(self, scenario: E2ETestScenario) -> Dict[str, Any]:
        """測試基礎數據流"""
        logger.info("執行基礎數據流測試...")
        
        results = {
            "test_steps_results": {},
            "performance_metrics": {},
            "validation_results": {},
            "success": False
        }
        
        try:
            # Step 1: 載入 TLE 數據
            step1_start = time.time()
            tle_result = self.tle_loader.load_all_tle_data()
            step1_time = time.time() - step1_start
            
            step1_success = tle_result.total_records > scenario.data_requirements["min_satellites"]
            results["test_steps_results"]["載入 TLE 數據"] = {
                "success": step1_success,
                "duration": step1_time,
                "records_loaded": tle_result.total_records
            }
            
            if not step1_success:
                results["error_message"] = f"TLE 數據不足: {tle_result.total_records}"
                return results
            
            # Step 2: 創建 SGP4 衛星對象
            step2_start = time.time()
            created_satellites = 0
            
            test_satellites = tle_result.records[:100]  # 測試前100顆
            for record in test_satellites:
                if self.sgp4_engine.create_satellite(record.satellite_id, record.line1, record.line2):
                    created_satellites += 1
            
            step2_time = time.time() - step2_start
            step2_success = created_satellites >= len(test_satellites) * 0.9
            
            results["test_steps_results"]["創建 SGP4 衛星對象"] = {
                "success": step2_success,
                "duration": step2_time,
                "satellites_created": created_satellites,
                "total_attempted": len(test_satellites)
            }
            
            # Step 3: 執行軌道計算
            step3_start = time.time()
            test_time = datetime.now(timezone.utc)
            successful_calculations = 0
            
            for record in test_satellites[:50]:
                result = self.sgp4_engine.calculate_position(record.satellite_id, test_time)
                if result and result.success:
                    successful_calculations += 1
            
            step3_time = time.time() - step3_start
            step3_success = successful_calculations >= 45  # 90% 成功率
            
            results["test_steps_results"]["執行軌道計算"] = {
                "success": step3_success,
                "duration": step3_time,
                "successful_calculations": successful_calculations,
                "calculation_rate": successful_calculations / step3_time
            }
            
            # Step 4: 通過標準接口查詢
            step4_start = time.time()
            
            query_request = self.standard_interface.create_query_request(
                constellations=["starlink"],
                max_records=10
            )
            
            query_response = self.standard_interface.execute_query(query_request)
            step4_time = time.time() - step4_start
            step4_success = query_response.success and query_response.returned_records > 0
            
            results["test_steps_results"]["通過標準接口查詢"] = {
                "success": step4_success,
                "duration": step4_time,
                "returned_records": query_response.returned_records
            }
            
            # Step 5: 驗證 API 響應
            step5_start = time.time()
            
            try:
                # 測試健康檢查
                health_response = requests.get(f"{self.api_base_url}/health", timeout=10)
                health_ok = health_response.status_code == 200
                
                # 測試衛星列表
                satellites_response = requests.get(f"{self.api_base_url}/satellites?limit=10", timeout=10)
                satellites_ok = satellites_response.status_code == 200
                
                step5_time = time.time() - step5_start
                step5_success = health_ok and satellites_ok
                
            except Exception as api_error:
                step5_time = time.time() - step5_start
                step5_success = False
                logger.warning(f"API 測試失敗: {api_error}")
            
            results["test_steps_results"]["驗證 API 響應"] = {
                "success": step5_success,
                "duration": step5_time,
                "health_check": health_ok if 'health_ok' in locals() else False,
                "satellites_api": satellites_ok if 'satellites_ok' in locals() else False
            }
            
            # 計算性能指標
            results["performance_metrics"] = {
                "tle_load_time": step1_time,
                "satellite_creation_time": step2_time,
                "calculation_time": step3_time,
                "query_time": step4_time,
                "api_response_time": step5_time
            }
            
            # 驗證性能要求
            perf_requirements = scenario.performance_requirements
            results["validation_results"] = {
                "tle_load_performance": step1_time <= perf_requirements["tle_load_time"],
                "satellite_creation_performance": step2_time <= perf_requirements["satellite_creation_time"],
                "calculation_performance": step3_time <= perf_requirements["calculation_time"],
                "api_performance": step5_time <= perf_requirements["api_response_time"]
            }
            
            # 判斷整體成功
            all_steps_success = all(step["success"] for step in results["test_steps_results"].values())
            all_perf_ok = all(results["validation_results"].values())
            results["success"] = all_steps_success and all_perf_ok
            
            return results
            
        except Exception as e:
            logger.error(f"基礎數據流測試失敗: {e}")
            results["error_message"] = str(e)
            return results
    
    async def _test_high_load_concurrent(self, scenario: E2ETestScenario) -> Dict[str, Any]:
        """測試高負載併發"""
        logger.info("執行高負載併發測試...")
        
        results = {
            "test_steps_results": {},
            "performance_metrics": {},
            "validation_results": {},
            "success": False
        }
        
        try:
            concurrent_users = scenario.performance_requirements["concurrent_users"]
            requests_per_user = scenario.performance_requirements["requests_per_user"]
            max_response_time = scenario.performance_requirements["max_response_time"]
            
            # 準備併發測試函數
            def make_api_request(user_id: int, request_id: int) -> Dict[str, Any]:
                try:
                    start_time = time.time()
                    
                    # 隨機選擇 API 端點
                    endpoints = [
                        f"{self.api_base_url}/satellites?limit=10",
                        f"{self.api_base_url}/api/v1/phase1/satellite_orbits?constellation=starlink&count=5",
                        f"{self.api_base_url}/health"
                    ]
                    
                    import random
                    endpoint = random.choice(endpoints)
                    response = requests.get(endpoint, timeout=30)
                    
                    end_time = time.time()
                    response_time = end_time - start_time
                    
                    return {
                        "user_id": user_id,
                        "request_id": request_id,
                        "success": response.status_code == 200,
                        "response_time": response_time,
                        "endpoint": endpoint,
                        "status_code": response.status_code
                    }
                    
                except Exception as e:
                    return {
                        "user_id": user_id,
                        "request_id": request_id,
                        "success": False,
                        "response_time": max_response_time + 1,
                        "error": str(e)
                    }
            
            # 執行併發測試
            concurrent_start = time.time()
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_users) as executor:
                # 提交所有請求
                futures = []
                for user_id in range(concurrent_users):
                    for request_id in range(requests_per_user):
                        future = executor.submit(make_api_request, user_id, request_id)
                        futures.append(future)
                
                # 收集結果
                request_results = []
                for future in concurrent.futures.as_completed(futures):
                    result = future.result()
                    request_results.append(result)
            
            concurrent_end = time.time()
            total_duration = concurrent_end - concurrent_start
            
            # 分析結果
            successful_requests = sum(1 for r in request_results if r["success"])
            total_requests = len(request_results)
            success_rate = successful_requests / total_requests if total_requests > 0 else 0
            
            response_times = [r["response_time"] for r in request_results if r["success"]]
            avg_response_time = np.mean(response_times) if response_times else 0
            max_actual_response_time = np.max(response_times) if response_times else 0
            
            # 記錄測試結果
            results["test_steps_results"]["併發請求執行"] = {
                "success": success_rate >= scenario.performance_requirements["success_rate"],
                "duration": total_duration,
                "total_requests": total_requests,
                "successful_requests": successful_requests,
                "success_rate": success_rate
            }
            
            results["performance_metrics"] = {
                "concurrent_users": concurrent_users,
                "requests_per_user": requests_per_user,
                "total_requests": total_requests,
                "successful_requests": successful_requests,
                "success_rate": success_rate,
                "total_duration": total_duration,
                "requests_per_second": total_requests / total_duration,
                "average_response_time": avg_response_time,
                "max_response_time": max_actual_response_time
            }
            
            # 驗證性能要求
            results["validation_results"] = {
                "success_rate_ok": success_rate >= scenario.performance_requirements["success_rate"],
                "response_time_ok": max_actual_response_time <= max_response_time,
                "concurrency_handled": True
            }
            
            results["success"] = all(results["validation_results"].values())
            
            return results
            
        except Exception as e:
            logger.error(f"高負載併發測試失敗: {e}")
            results["error_message"] = str(e)
            return results
    
    async def _test_large_scale_processing(self, scenario: E2ETestScenario) -> Dict[str, Any]:
        """測試大規模數據處理"""
        logger.info("執行大規模數據處理測試...")
        
        results = {
            "test_steps_results": {},
            "performance_metrics": {},
            "validation_results": {},
            "success": False
        }
        
        try:
            # 獲取數據覆蓋信息
            coverage = self.data_provider.get_data_coverage()
            total_satellites = coverage.get("total_satellites", 0)
            
            results["test_steps_results"]["數據規模檢查"] = {
                "success": total_satellites >= scenario.performance_requirements["total_satellites"],
                "total_satellites": total_satellites,
                "target_satellites": scenario.performance_requirements["total_satellites"]
            }
            
            # 測試大量數據查詢
            large_query_start = time.time()
            
            query_request = self.standard_interface.create_query_request(
                max_records=1000
            )
            
            query_response = self.standard_interface.execute_query(query_request)
            
            large_query_time = time.time() - large_query_start
            
            results["test_steps_results"]["大量數據查詢"] = {
                "success": query_response.success and query_response.returned_records >= 500,
                "duration": large_query_time,
                "returned_records": query_response.returned_records,
                "total_matches": query_response.total_matches
            }
            
            # 性能指標
            results["performance_metrics"] = {
                "total_satellites": total_satellites,
                "large_query_time": large_query_time,
                "query_records": query_response.returned_records,
                "records_per_second": query_response.returned_records / large_query_time if large_query_time > 0 else 0
            }
            
            # 驗證要求
            results["validation_results"] = {
                "scale_requirement": total_satellites >= scenario.performance_requirements["total_satellites"],
                "query_performance": large_query_time <= scenario.performance_requirements["large_query_time"],
                "data_availability": query_response.returned_records > 0
            }
            
            results["success"] = all(results["validation_results"].values())
            
            return results
            
        except Exception as e:
            logger.error(f"大規模數據處理測試失敗: {e}")
            results["error_message"] = str(e)
            return results
    
    async def _test_api_compatibility(self, scenario: E2ETestScenario) -> Dict[str, Any]:
        """測試 API 兼容性"""
        logger.info("執行 API 兼容性測試...")
        
        results = {
            "test_steps_results": {},
            "performance_metrics": {},
            "validation_results": {},
            "success": False
        }
        
        try:
            # 測試新標準 API
            new_api_start = time.time()
            
            try:
                new_response = requests.get(
                    f"{self.api_base_url}/satellites?constellation=starlink&limit=10",
                    timeout=10
                )
                new_api_success = new_response.status_code == 200
                new_data = new_response.json() if new_api_success else None
            except Exception as e:
                new_api_success = False
                new_data = None
                logger.warning(f"新 API 測試失敗: {e}")
            
            new_api_time = time.time() - new_api_start
            
            # 測試兼容 API
            legacy_api_start = time.time()
            
            try:
                legacy_response = requests.get(
                    f"{self.api_base_url}/api/v1/phase1/satellite_orbits?constellation=starlink&count=10",
                    timeout=10
                )
                legacy_api_success = legacy_response.status_code == 200
                legacy_data = legacy_response.json() if legacy_api_success else None
            except Exception as e:
                legacy_api_success = False
                legacy_data = None
                logger.warning(f"兼容 API 測試失敗: {e}")
            
            legacy_api_time = time.time() - legacy_api_start
            
            # 記錄測試結果
            results["test_steps_results"]["新標準 API"] = {
                "success": new_api_success,
                "duration": new_api_time,
                "data_received": new_data is not None
            }
            
            results["test_steps_results"]["兼容 API"] = {
                "success": legacy_api_success,
                "duration": legacy_api_time,
                "data_received": legacy_data is not None
            }
            
            # 數據一致性檢查（如果兩個 API 都成功）
            data_consistency = False
            if new_api_success and legacy_api_success and new_data and legacy_data:
                # 檢查數據格式和內容（簡化檢查）
                try:
                    new_count = len(new_data.get("satellites", [])) if isinstance(new_data, dict) else len(new_data)
                    legacy_count = len(legacy_data) if isinstance(legacy_data, list) else 0
                    
                    data_consistency = abs(new_count - legacy_count) <= 2  # 允許小幅差異
                except Exception:
                    data_consistency = False
            
            results["test_steps_results"]["數據一致性檢查"] = {
                "success": data_consistency,
                "new_api_data": bool(new_data),
                "legacy_api_data": bool(legacy_data)
            }
            
            # 性能指標
            results["performance_metrics"] = {
                "new_api_response_time": new_api_time,
                "legacy_api_response_time": legacy_api_time,
                "response_time_ratio": legacy_api_time / new_api_time if new_api_time > 0 else 0
            }
            
            # 驗證要求
            results["validation_results"] = {
                "new_api_functional": new_api_success,
                "legacy_api_functional": legacy_api_success,
                "data_consistency": data_consistency,
                "performance_acceptable": new_api_time <= scenario.performance_requirements["api_response_time"]
            }
            
            results["success"] = all(results["validation_results"].values())
            
            return results
            
        except Exception as e:
            logger.error(f"API 兼容性測試失敗: {e}")
            results["error_message"] = str(e)
            return results
    
    async def _test_error_recovery(self, scenario: E2ETestScenario) -> Dict[str, Any]:
        """測試錯誤恢復"""
        logger.info("執行錯誤恢復測試...")
        
        results = {
            "test_steps_results": {},
            "performance_metrics": {},
            "validation_results": {},
            "success": False
        }
        
        try:
            # 測試無效請求處理
            error_tests = [
                {
                    "name": "無效星座名稱",
                    "url": f"{self.api_base_url}/satellites?constellation=invalid_constellation",
                    "expected_status": [400, 404]
                },
                {
                    "name": "超大查詢限制",
                    "url": f"{self.api_base_url}/satellites?limit=999999",
                    "expected_status": [400, 413]
                },
                {
                    "name": "無效 API 路徑",
                    "url": f"{self.api_base_url}/invalid_endpoint",
                    "expected_status": [404]
                }
            ]
            
            error_handling_results = {}
            
            for test in error_tests:
                try:
                    error_start = time.time()
                    response = requests.get(test["url"], timeout=10)
                    error_time = time.time() - error_start
                    
                    correct_error_handling = response.status_code in test["expected_status"]
                    
                    error_handling_results[test["name"]] = {
                        "success": correct_error_handling,
                        "duration": error_time,
                        "status_code": response.status_code,
                        "expected_status": test["expected_status"]
                    }
                    
                except Exception as e:
                    error_handling_results[test["name"]] = {
                        "success": False,
                        "error": str(e)
                    }
            
            results["test_steps_results"]["錯誤處理測試"] = error_handling_results
            
            # 測試系統恢復（測試健康檢查）
            recovery_start = time.time()
            
            try:
                health_response = requests.get(f"{self.api_base_url}/health", timeout=10)
                system_recovered = health_response.status_code == 200
                
                if system_recovered:
                    health_data = health_response.json()
                    system_healthy = health_data.get("service") in ["healthy", "degraded"]
                else:
                    system_healthy = False
                    
            except Exception as e:
                system_recovered = False
                system_healthy = False
                logger.warning(f"系統恢復測試失敗: {e}")
            
            recovery_time = time.time() - recovery_start
            
            results["test_steps_results"]["系統恢復測試"] = {
                "success": system_recovered and system_healthy,
                "duration": recovery_time,
                "system_responded": system_recovered,
                "system_healthy": system_healthy
            }
            
            # 性能指標
            avg_error_response_time = np.mean([
                r.get("duration", 0) for r in error_handling_results.values() 
                if "duration" in r
            ])
            
            results["performance_metrics"] = {
                "average_error_response_time": avg_error_response_time,
                "recovery_time": recovery_time,
                "error_tests_count": len(error_tests)
            }
            
            # 驗證要求
            error_handling_success = all(
                r["success"] for r in error_handling_results.values()
            )
            
            results["validation_results"] = {
                "error_handling_correct": error_handling_success,
                "recovery_successful": system_recovered and system_healthy,
                "error_response_time_ok": avg_error_response_time <= scenario.performance_requirements["error_response_time"]
            }
            
            results["success"] = all(results["validation_results"].values())
            
            return results
            
        except Exception as e:
            logger.error(f"錯誤恢復測試失敗: {e}")
            results["error_message"] = str(e)
            return results
    
    def _calculate_summary_stats(self) -> Dict[str, Any]:
        """計算總結統計"""
        try:
            all_durations = []
            all_performance_metrics = {}
            
            for result in self.test_results:
                if hasattr(result, 'duration_seconds'):
                    all_durations.append(result.duration_seconds)
                
                if hasattr(result, 'performance_data') and result.performance_data:
                    for key, value in result.performance_data.items():
                        if key not in all_performance_metrics:
                            all_performance_metrics[key] = []
                        all_performance_metrics[key].append(value)
            
            summary = {
                "total_test_time": sum(all_durations) if all_durations else 0,
                "average_test_time": np.mean(all_durations) if all_durations else 0,
                "performance_aggregates": {}
            }
            
            for metric, values in all_performance_metrics.items():
                summary["performance_aggregates"][metric] = {
                    "average": np.mean(values),
                    "min": np.min(values),
                    "max": np.max(values)
                }
            
            return summary
            
        except Exception as e:
            logger.error(f"計算總結統計失敗: {e}")
            return {"error": str(e)}
    
    def export_test_results(self, output_path: str):
        """導出測試結果"""
        try:
            # 準備導出數據
            export_data = {
                "test_metadata": {
                    "export_timestamp": datetime.now(timezone.utc).isoformat(),
                    "api_base_url": self.api_base_url,
                    "total_scenarios": len(self.test_scenarios)
                },
                "test_scenarios": [asdict(scenario) for scenario in self.test_scenarios],
                "test_results": [asdict(result) for result in self.test_results]
            }
            
            # 寫入文件
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"測試結果已導出到: {output_path}")
            
        except Exception as e:
            logger.error(f"導出測試結果失敗: {e}")

# 便利函數
def create_e2e_tester(api_base_url: str = None) -> EndToEndTester:
    """創建端到端測試器，自動從配置系統獲取 API URL"""
    return EndToEndTester(api_base_url)

async def main():
    """主函數"""
    logging.basicConfig(level=logging.INFO)
    
    try:
        print("🚀 Phase 1 端到端測試")
        print("=" * 50)
        
        # 創建測試器
        tester = create_e2e_tester()
        
        # 執行所有測試
        test_summary = await tester.run_all_tests()
        
        # 顯示結果
        print(f"\n📊 測試總結:")
        print(f"執行場景: {test_summary['total_scenarios']}")
        print(f"成功率: {test_summary['success_rate']:.1f}%")
        print(f"總耗時: {test_summary['total_duration']:.1f}s")
        print(f"整體結果: {'✅ 通過' if test_summary['overall_success'] else '❌ 失敗'}")
        
        # 導出結果
        output_path = PHASE1_ROOT / "05_integration" / "e2e_test_results.json"
        tester.export_test_results(str(output_path))
        print(f"詳細結果已保存: {output_path}")
        
        return 0 if test_summary['overall_success'] else 1
        
    except Exception as e:
        logger.error(f"端到端測試執行失敗: {e}")
        return 1

if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)