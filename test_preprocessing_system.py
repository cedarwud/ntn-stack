#!/usr/bin/env python3
"""
衛星預處理系統測試腳本

測試新實現的衛星預處理功能，包括：
1. API 端點可用性測試
2. 智能衛星選擇邏輯測試
3. 軌道分群和相位分散測試
4. 整合功能測試
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime, timezone, timedelta

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PreprocessingSystemTester:
    """預處理系統測試器"""
    
    def __init__(self):
        self.netstack_api_url = "http://localhost:8080/api/v1/satellite-ops"
        self.test_results = {}
    
    async def run_all_tests(self):
        """執行所有測試"""
        logger.info("🚀 開始衛星預處理系統測試")
        
        tests = [
            ("API 健康檢查", self.test_health_check),
            ("可見衛星 API 測試", self.test_visible_satellites_api),
            ("預處理池 API 測試", self.test_preprocessing_pool_api),
            ("最佳時間窗口 API 測試", self.test_optimal_time_window_api),
            ("事件時間線 API 測試", self.test_event_timeline_api),
            ("換手決策 API 測試", self.test_handover_evaluation_api),
        ]
        
        for test_name, test_func in tests:
            try:
                logger.info(f"🧪 執行測試: {test_name}")
                result = await test_func()
                self.test_results[test_name] = {"status": "PASS", "result": result}
                logger.info(f"✅ {test_name} - 通過")
            except Exception as e:
                self.test_results[test_name] = {"status": "FAIL", "error": str(e)}
                logger.error(f"❌ {test_name} - 失敗: {e}")
        
        # 生成測試報告
        self.generate_test_report()
    
    async def test_health_check(self):
        """測試健康檢查端點"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.netstack_api_url}/health") as response:
                if response.status != 200:
                    raise Exception(f"健康檢查失敗，狀態碼: {response.status}")
                
                data = await response.json()
                
                # 驗證回應內容
                required_fields = ["healthy", "service", "endpoints"]
                for field in required_fields:
                    if field not in data:
                        raise Exception(f"健康檢查回應缺少字段: {field}")
                
                # 驗證新增的端點
                expected_endpoints = [
                    "/api/v1/satellite-ops/visible_satellites",
                    "/api/v1/satellite-ops/preprocess_pool",
                    "/api/v1/satellite-ops/optimal_time_window",
                    "/api/v1/satellite-ops/event_stream"
                ]
                
                for endpoint in expected_endpoints:
                    if endpoint not in data["endpoints"]:
                        raise Exception(f"健康檢查回應缺少端點: {endpoint}")
                
                return data
    
    async def test_visible_satellites_api(self):
        """測試可見衛星 API"""
        params = {
            "count": 10,
            "constellation": "starlink",
            "min_elevation_deg": 10,
            "observer_lat": 24.9441667,
            "observer_lon": 121.3713889,
            "global_view": "false"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.netstack_api_url}/visible_satellites", params=params) as response:
                if response.status != 200:
                    raise Exception(f"可見衛星 API 失敗，狀態碼: {response.status}")
                
                data = await response.json()
                
                # 驗證回應結構
                required_fields = ["satellites", "total_count", "constellation", "timestamp"]
                for field in required_fields:
                    if field not in data:
                        raise Exception(f"可見衛星回應缺少字段: {field}")
                
                if not isinstance(data["satellites"], list):
                    raise Exception("satellites 字段應為列表")
                
                return {
                    "total_satellites": data["total_count"],
                    "constellation": data["constellation"],
                    "has_data_source": "data_source" in data
                }
    
    async def test_preprocessing_pool_api(self):
        """測試預處理池 API"""
        request_data = {
            "constellation": "starlink",
            "target_count": 120,
            "optimization_mode": "event_diversity",
            "observer_lat": 24.9441667,
            "observer_lon": 121.3713889,
            "time_window_hours": 24
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.netstack_api_url}/preprocess_pool", 
                json=request_data
            ) as response:
                if response.status != 200:
                    response_text = await response.text()
                    raise Exception(f"預處理池 API 失敗，狀態碼: {response.status}，回應: {response_text}")
                
                data = await response.json()
                
                # 驗證回應結構
                required_fields = ["selected_satellites", "selection_stats", "quality_metrics", "processing_time"]
                for field in required_fields:
                    if field not in data:
                        raise Exception(f"預處理池回應缺少字段: {field}")
                
                return {
                    "selected_count": len(data["selected_satellites"]),
                    "processing_time": data["processing_time"],
                    "overall_quality": data["quality_metrics"].get("overall_quality", 0)
                }
    
    async def test_optimal_time_window_api(self):
        """測試最佳時間窗口 API"""
        params = {
            "constellation": "starlink"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.netstack_api_url}/optimal_time_window", params=params) as response:
                if response.status != 200:
                    response_text = await response.text()
                    raise Exception(f"最佳時間窗口 API 失敗，狀態碼: {response.status}，回應: {response_text}")
                
                data = await response.json()
                
                # 驗證回應結構
                required_fields = ["start_time", "end_time", "quality_score", "expected_visible_range"]
                for field in required_fields:
                    if field not in data:
                        raise Exception(f"最佳時間窗口回應缺少字段: {field}")
                
                return {
                    "start_time": data["start_time"],
                    "end_time": data["end_time"],
                    "quality_score": data["quality_score"]
                }
    
    async def test_event_timeline_api(self):
        """測試事件時間線 API"""
        now = datetime.now(timezone.utc)
        start_time = now.isoformat()
        end_time = (now + timedelta(hours=2)).isoformat()
        
        params = {
            "start_time": start_time,
            "end_time": end_time,
            "constellation": "starlink"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.netstack_api_url}/event_stream", params=params) as response:
                if response.status != 200:
                    response_text = await response.text()
                    raise Exception(f"事件時間線 API 失敗，狀態碼: {response.status}，回應: {response_text}")
                
                data = await response.json()
                
                # 驗證回應結構
                required_fields = ["events", "event_summary"]
                for field in required_fields:
                    if field not in data:
                        raise Exception(f"事件時間線回應缺少字段: {field}")
                
                return {
                    "total_events": len(data["events"]),
                    "event_summary": data["event_summary"]
                }
    
    async def test_handover_evaluation_api(self):
        """測試換手決策評估 API"""
        params = {
            "serving_satellite_id": "44713",  # 測試用衛星ID
            "count": 10,
            "constellation": "starlink",
            "min_elevation_deg": 10,
            "observer_lat": 24.9441667,
            "observer_lon": 121.3713889
        }
        
        async with aiohttp.ClientSession() as session:
            # 注意：evaluate_handover 是 POST 端點，但參數通過查詢字符串傳遞
            async with session.post(f"{self.netstack_api_url}/evaluate_handover", params=params) as response:
                if response.status != 200:
                    response_text = await response.text()
                    raise Exception(f"換手決策 API 失敗，狀態碼: {response.status}，回應: {response_text}")
                
                data = await response.json()
                
                # 驗證回應結構
                required_fields = ["handover_decision", "serving_satellite", "neighbor_satellites"]
                for field in required_fields:
                    if field not in data:
                        raise Exception(f"換手決策回應缺少字段: {field}")
                
                return {
                    "should_handover": data["handover_decision"]["should_handover"],
                    "target_satellite": data["handover_decision"]["target_satellite_id"],
                    "neighbor_count": len(data["neighbor_satellites"])
                }
    
    def generate_test_report(self):
        """生成測試報告"""
        logger.info("📊 生成測試報告")
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result["status"] == "PASS")
        failed_tests = total_tests - passed_tests
        
        print("\n" + "="*80)
        print("🛰️ 衛星預處理系統測試報告")
        print("="*80)
        print(f"總測試數: {total_tests}")
        print(f"通過: {passed_tests}")
        print(f"失敗: {failed_tests}")
        print(f"成功率: {(passed_tests/total_tests)*100:.1f}%")
        print("="*80)
        
        for test_name, result in self.test_results.items():
            status_icon = "✅" if result["status"] == "PASS" else "❌"
            print(f"{status_icon} {test_name}: {result['status']}")
            
            if result["status"] == "PASS" and "result" in result:
                # 顯示測試結果摘要
                test_result = result["result"]
                if isinstance(test_result, dict):
                    for key, value in test_result.items():
                        print(f"   - {key}: {value}")
            elif result["status"] == "FAIL":
                print(f"   錯誤: {result['error']}")
            print()
        
        print("="*80)
        
        if failed_tests == 0:
            print("🎉 所有測試通過！預處理系統運行正常")
        else:
            print(f"⚠️ 有 {failed_tests} 個測試失敗，請檢查系統配置")
        
        print("="*80)

async def main():
    """主函數"""
    tester = PreprocessingSystemTester()
    
    try:
        await tester.run_all_tests()
    except KeyboardInterrupt:
        logger.info("測試被用戶中斷")
    except Exception as e:
        logger.error(f"測試執行出錯: {e}")

if __name__ == "__main__":
    asyncio.run(main())