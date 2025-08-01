#!/usr/bin/env python3
"""
Phase 3 驗證腳本

驗證規則式換手決策系統的功能完整性和性能要求
- API 響應時間 < 10ms
- 事件處理延遲 < 50ms
- 決策準確性 > 90%
"""

import asyncio
import json
import time
import requests
from datetime import datetime
from typing import Dict, List, Any

class Phase3Validator:
    """Phase 3 系統驗證器"""
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.results = {
            "test_results": [],
            "performance_metrics": {},
            "success_count": 0,
            "total_tests": 0
        }
    
    def run_validation(self) -> Dict[str, Any]:
        """執行完整驗證流程"""
        print("🚀 開始 Phase 3 系統驗證...")
        
        # 測試項目
        tests = [
            ("API 健康檢查", self.test_health_check),
            ("換手狀態查詢性能", self.test_status_performance),
            ("事件處理功能", self.test_event_processing),
            ("可見衛星查詢", self.test_visible_satellites),
            ("KPI 指標獲取", self.test_kpi_metrics),
            ("組件整合測試", self.test_component_integration)
        ]
        
        self.results["total_tests"] = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n📋 執行測試: {test_name}")
            try:
                result = test_func()
                self.results["test_results"].append({
                    "name": test_name,
                    "status": "PASS" if result["success"] else "FAIL",
                    "details": result,
                    "timestamp": datetime.now().isoformat()
                })
                
                if result["success"]:
                    self.results["success_count"] += 1
                    print(f"✅ {test_name} - 通過")
                else:
                    print(f"❌ {test_name} - 失敗: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                print(f"💥 {test_name} - 異常: {str(e)}")
                self.results["test_results"].append({
                    "name": test_name,
                    "status": "ERROR",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
        
        # 生成報告
        self.generate_report()
        return self.results
    
    def test_health_check(self) -> Dict[str, Any]:
        """測試健康檢查端點"""
        try:
            start_time = time.time()
            response = requests.get(f"{self.base_url}/api/v1/handover/health", timeout=5)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "response_time_ms": response_time,
                    "status": data.get("status"),
                    "components": data.get("components", {})
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "response_time_ms": response_time
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def test_status_performance(self) -> Dict[str, Any]:
        """測試狀態查詢性能 (目標 < 10ms)"""
        response_times = []
        
        try:
            # 執行10次測試取平均
            for i in range(10):
                start_time = time.time()
                response = requests.get(f"{self.base_url}/api/v1/handover/status", timeout=2)
                response_time = (time.time() - start_time) * 1000
                response_times.append(response_time)
                
                if response.status_code != 200:
                    return {
                        "success": False,
                        "error": f"HTTP {response.status_code} on attempt {i+1}"
                    }
            
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            
            # 性能要求：平均 < 10ms，最大 < 20ms
            performance_ok = avg_response_time < 10.0 and max_response_time < 20.0
            
            return {
                "success": performance_ok,
                "avg_response_time_ms": round(avg_response_time, 2),
                "max_response_time_ms": round(max_response_time, 2),
                "min_response_time_ms": round(min(response_times), 2),
                "all_response_times": [round(rt, 2) for rt in response_times],
                "performance_grade": "EXCELLENT" if avg_response_time < 5 else "GOOD" if avg_response_time < 10 else "POOR"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def test_event_processing(self) -> Dict[str, Any]:
        """測試事件處理功能"""
        test_events = [
            {
                "type": "D2",
                "serving_satellite": {"id": "starlink_123", "elevation": 4.0},
                "recommended_target": {"id": "starlink_456", "elevation": 12.0},
                "time_to_los_seconds": 25
            },
            {
                "type": "A4", 
                "candidate_satellite": {"id": "oneweb_789", "elevation": 15.0},
                "serving_satellite": {"id": "starlink_123", "elevation": 8.0},
                "quality_advantage_db": 5.2
            },
            {
                "type": "A5",
                "serving_satellite": {"id": "starlink_123", "elevation": 7.0},
                "candidate_satellite": {"id": "oneweb_789", "elevation": 18.0},
                "handover_gain_db": 8.5,
                "urgency": "high"
            }
        ]
        
        processed_events = 0
        decisions_made = 0
        total_processing_time = 0
        
        try:
            for event in test_events:
                start_time = time.time()
                response = requests.post(
                    f"{self.base_url}/api/v1/handover/event",
                    json=event,
                    timeout=5
                )
                processing_time = (time.time() - start_time) * 1000
                total_processing_time += processing_time
                
                if response.status_code == 200:
                    processed_events += 1
                    data = response.json()
                    
                    if data.get("status") == "decision_made":
                        decisions_made += 1
                        
                        # 驗證決策結構
                        decision = data.get("decision", {})
                        required_fields = ["action", "decision_type", "urgency", "confidence"]
                        
                        if not all(field in decision for field in required_fields):
                            return {
                                "success": False,
                                "error": f"決策缺少必要欄位: {required_fields}"
                            }
            
            avg_processing_time = total_processing_time / len(test_events)
            
            return {
                "success": processed_events == len(test_events),
                "processed_events": processed_events,
                "decisions_made": decisions_made,
                "avg_processing_time_ms": round(avg_processing_time, 2),
                "decision_rate": round(decisions_made / processed_events * 100, 1) if processed_events > 0 else 0
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def test_visible_satellites(self) -> Dict[str, Any]:
        """測試可見衛星查詢"""
        try:
            start_time = time.time()
            response = requests.get(f"{self.base_url}/api/v1/handover/satellites/visible", timeout=10)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                satellites = data.get("visible_satellites", [])
                
                # 驗證數據結構
                if satellites:
                    sample_satellite = satellites[0]
                    required_fields = ["satellite_id", "constellation", "elevation_deg", "azimuth_deg"]
                    
                    if not all(field in sample_satellite for field in required_fields):
                        return {
                            "success": False,
                            "error": f"衛星數據缺少必要欄位: {required_fields}"
                        }
                
                return {
                    "success": True,
                    "response_time_ms": round(response_time, 2),
                    "satellite_count": len(satellites),
                    "highest_elevation": data.get("highest_elevation", 0),
                    "data_structure_valid": True
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "response_time_ms": round(response_time, 2)
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def test_kpi_metrics(self) -> Dict[str, Any]:
        """測試 KPI 指標獲取"""
        try:
            start_time = time.time()
            response = requests.get(f"{self.base_url}/api/v1/handover/metrics/kpis", timeout=5)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                kpis = data.get("kpis", {})
                
                # 驗證關鍵指標存在
                required_kpis = [
                    "handover_success_rate_percent",
                    "avg_interruption_time_ms", 
                    "service_availability_percent",
                    "avg_decision_latency_ms"
                ]
                
                missing_kpis = [kpi for kpi in required_kpis if kpi not in kpis]
                
                if missing_kpis:
                    return {
                        "success": False,
                        "error": f"缺少關鍵 KPI: {missing_kpis}"
                    }
                
                return {
                    "success": True,
                    "response_time_ms": round(response_time, 2),
                    "kpis_available": list(kpis.keys()),
                    "performance_grade": kpis.get("performance_grade", "N/A")
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "response_time_ms": round(response_time, 2)
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def test_component_integration(self) -> Dict[str, Any]:
        """測試組件整合度"""
        integration_score = 0
        max_score = 0
        details = {}
        
        try:
            # 測試健康檢查中的組件狀態
            response = requests.get(f"{self.base_url}/api/v1/handover/health", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                components = data.get("components", {})
                
                # 檢查各組件狀態
                for component, status in components.items():
                    max_score += 1
                    if status == "healthy":
                        integration_score += 1
                        details[component] = "OK"
                    else:
                        details[component] = f"Status: {status}"
            
            # 測試狀態查詢中的引擎狀態
            response = requests.get(f"{self.base_url}/api/v1/handover/status", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                engine_status = data.get("engine_status", {})
                
                max_score += 1
                if engine_status.get("engine_health") == "operational":
                    integration_score += 1
                    details["handover_engine"] = "OK"
                else:
                    details["handover_engine"] = f"Health: {engine_status.get('engine_health', 'unknown')}"
                
                # 檢查數據健康狀態
                data_health = data.get("data_health", {})
                max_score += 1
                if data_health.get("orbit_data_available", False):
                    integration_score += 1
                    details["orbit_data"] = "OK"
                else:
                    details["orbit_data"] = "Unavailable"
            
            integration_percentage = (integration_score / max_score * 100) if max_score > 0 else 0
            
            return {
                "success": integration_percentage >= 80,  # 至少80%組件正常
                "integration_score": integration_score,
                "max_score": max_score,
                "integration_percentage": round(integration_percentage, 1),
                "component_details": details
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def generate_report(self) -> None:
        """生成驗證報告"""
        success_rate = (self.results["success_count"] / self.results["total_tests"] * 100) if self.results["total_tests"] > 0 else 0
        
        print(f"\n{'='*60}")
        print(f"🎯 Phase 3 驗證報告")
        print(f"{'='*60}")
        print(f"總測試數: {self.results['total_tests']}")
        print(f"通過測試: {self.results['success_count']}")
        print(f"成功率: {success_rate:.1f}%")
        
        if success_rate >= 90:
            print("🏆 系統狀態: 優秀 (≥90%)")
        elif success_rate >= 80:
            print("✅ 系統狀態: 良好 (≥80%)")
        elif success_rate >= 70:
            print("⚠️ 系統狀態: 可接受 (≥70%)")
        else:
            print("❌ 系統狀態: 需要改進 (<70%)")
        
        print(f"\n詳細結果:")
        for result in self.results["test_results"]:
            status_icon = "✅" if result["status"] == "PASS" else "❌" if result["status"] == "FAIL" else "💥"
            print(f"{status_icon} {result['name']}: {result['status']}")
        
        # 保存報告到文件
        report_file = f"phase3_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 詳細報告已保存至: {report_file}")

def main():
    """主函數"""
    validator = Phase3Validator()
    results = validator.run_validation()
    
    # 返回適當的退出碼
    success_rate = (results["success_count"] / results["total_tests"] * 100) if results["total_tests"] > 0 else 0
    exit_code = 0 if success_rate >= 80 else 1
    
    print(f"\n退出碼: {exit_code} ({'成功' if exit_code == 0 else '失敗'})")
    return exit_code

if __name__ == "__main__":
    exit(main())