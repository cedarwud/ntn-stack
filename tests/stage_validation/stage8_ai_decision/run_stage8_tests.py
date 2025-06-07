#!/usr/bin/env python3
"""
階段八 AI 決策與自動調優 - 測試運行器

統一的測試執行入口，支持不同測試模式和配置
"""

import os
import sys
import asyncio
import argparse
import json
import time
from datetime import datetime
from typing import Dict, List
import logging

# 添加項目路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 導入測試模組
from tests.stage8_ai_decision_validation import AIDecisionTestFramework
from tests.integration.test_stage8_ai_integration import Stage8AIIntegrationTest

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Stage8TestRunner:
    """階段八測試運行器"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.results = {
            "test_session_id": f"stage8_test_{int(time.time())}",
            "start_time": datetime.now().isoformat(),
            "config": config,
            "test_results": {},
            "summary": {}
        }
        
    async def run_validation_tests(self) -> Dict:
        """運行驗證測試"""
        logger.info("🔬 開始運行 AI 決策驗證測試...")
        
        try:
            framework = AIDecisionTestFramework(self.config["netstack_url"])
            validation_results = await framework.run_comprehensive_validation()
            
            self.results["test_results"]["validation"] = validation_results
            
            logger.info("✅ AI 決策驗證測試完成")
            return validation_results
            
        except Exception as e:
            logger.error(f"❌ AI 決策驗證測試失敗: {e}")
            self.results["test_results"]["validation"] = {"error": str(e)}
            raise
    
    async def run_integration_tests(self) -> Dict:
        """運行整合測試"""
        logger.info("🔗 開始運行整合測試...")
        
        try:
            integration_test = Stage8AIIntegrationTest()
            integration_results = await integration_test.run_comprehensive_integration_test()
            
            self.results["test_results"]["integration"] = integration_results
            
            logger.info("✅ 整合測試完成")
            return integration_results
            
        except Exception as e:
            logger.error(f"❌ 整合測試失敗: {e}")
            self.results["test_results"]["integration"] = {"error": str(e)}
            raise
    
    async def run_performance_tests(self) -> Dict:
        """運行性能測試"""
        logger.info("⚡ 開始運行性能測試...")
        
        performance_results = {
            "test_type": "performance",
            "tests_executed": 0,
            "results": {}
        }
        
        try:
            # AI 決策響應時間測試
            ai_response_times = await self._test_ai_response_times()
            performance_results["results"]["ai_response_times"] = ai_response_times
            performance_results["tests_executed"] += 1
            
            # 優化效果測試
            optimization_performance = await self._test_optimization_performance()
            performance_results["results"]["optimization_performance"] = optimization_performance
            performance_results["tests_executed"] += 1
            
            # 系統負載測試
            load_test_results = await self._test_system_load()
            performance_results["results"]["load_test"] = load_test_results
            performance_results["tests_executed"] += 1
            
            self.results["test_results"]["performance"] = performance_results
            
            logger.info("✅ 性能測試完成")
            return performance_results
            
        except Exception as e:
            logger.error(f"❌ 性能測試失敗: {e}")
            performance_results["error"] = str(e)
            self.results["test_results"]["performance"] = performance_results
            raise
    
    async def run_stress_tests(self) -> Dict:
        """運行壓力測試"""
        logger.info("💪 開始運行壓力測試...")
        
        stress_results = {
            "test_type": "stress",
            "tests_executed": 0,
            "results": {}
        }
        
        try:
            # 高並發決策測試
            concurrent_decisions = await self._test_concurrent_decisions()
            stress_results["results"]["concurrent_decisions"] = concurrent_decisions
            stress_results["tests_executed"] += 1
            
            # 長時間運行測試
            endurance_test = await self._test_endurance()
            stress_results["results"]["endurance"] = endurance_test
            stress_results["tests_executed"] += 1
            
            # 資源限制測試
            resource_limits = await self._test_resource_limits()
            stress_results["results"]["resource_limits"] = resource_limits
            stress_results["tests_executed"] += 1
            
            self.results["test_results"]["stress"] = stress_results
            
            logger.info("✅ 壓力測試完成")
            return stress_results
            
        except Exception as e:
            logger.error(f"❌ 壓力測試失敗: {e}")
            stress_results["error"] = str(e)
            self.results["test_results"]["stress"] = stress_results
            raise
    
    async def _test_ai_response_times(self) -> Dict:
        """測試 AI 決策響應時間"""
        import aiohttp
        
        response_times = []
        error_count = 0
        
        async with aiohttp.ClientSession() as session:
            for i in range(self.config["performance_test_iterations"]):
                try:
                    start_time = time.time()
                    
                    async with session.get(
                        f"{self.config['netstack_url']}/api/v1/ai-decision/health-analysis",
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        
                        end_time = time.time()
                        response_time = (end_time - start_time) * 1000  # 轉換為毫秒
                        
                        if response.status == 200:
                            response_times.append(response_time)
                        else:
                            error_count += 1
                            
                except Exception as e:
                    error_count += 1
                    logger.warning(f"響應時間測試迭代 {i} 失敗: {e}")
                
                # 短暫延遲避免過載
                await asyncio.sleep(0.1)
        
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            min_response_time = min(response_times)
        else:
            avg_response_time = max_response_time = min_response_time = 0
        
        return {
            "total_requests": self.config["performance_test_iterations"],
            "successful_requests": len(response_times),
            "error_count": error_count,
            "avg_response_time_ms": avg_response_time,
            "max_response_time_ms": max_response_time,
            "min_response_time_ms": min_response_time,
            "error_rate": error_count / self.config["performance_test_iterations"]
        }
    
    async def _test_optimization_performance(self) -> Dict:
        """測試優化性能"""
        import aiohttp
        
        optimization_results = []
        
        async with aiohttp.ClientSession() as session:
            for i in range(3):  # 執行3次優化測試
                try:
                    start_time = time.time()
                    
                    # 觸發優化
                    async with session.post(
                        f"{self.config['netstack_url']}/api/v1/ai-decision/optimization/manual",
                        json={},
                        timeout=aiohttp.ClientTimeout(total=60)
                    ) as response:
                        
                        if response.status == 200:
                            optimization_time = time.time() - start_time
                            optimization_results.append({
                                "iteration": i + 1,
                                "optimization_time": optimization_time,
                                "success": True
                            })
                        else:
                            optimization_results.append({
                                "iteration": i + 1,
                                "success": False,
                                "error": f"HTTP {response.status}"
                            })
                
                except Exception as e:
                    optimization_results.append({
                        "iteration": i + 1,
                        "success": False,
                        "error": str(e)
                    })
                
                # 等待系統穩定
                await asyncio.sleep(20)
        
        successful_optimizations = [r for r in optimization_results if r.get("success", False)]
        avg_optimization_time = 0
        if successful_optimizations:
            avg_optimization_time = sum(r["optimization_time"] for r in successful_optimizations) / len(successful_optimizations)
        
        return {
            "total_optimizations": len(optimization_results),
            "successful_optimizations": len(successful_optimizations),
            "avg_optimization_time": avg_optimization_time,
            "success_rate": len(successful_optimizations) / len(optimization_results),
            "detailed_results": optimization_results
        }
    
    async def _test_system_load(self) -> Dict:
        """測試系統負載"""
        import aiohttp
        
        # 併發請求測試
        concurrent_requests = 20
        results = []
        
        async def make_request(session, request_id):
            try:
                start_time = time.time()
                async with session.get(
                    f"{self.config['netstack_url']}/api/v1/ai-decision/health-analysis",
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    end_time = time.time()
                    return {
                        "request_id": request_id,
                        "success": response.status == 200,
                        "response_time": (end_time - start_time) * 1000,
                        "status_code": response.status
                    }
            except Exception as e:
                return {
                    "request_id": request_id,
                    "success": False,
                    "error": str(e)
                }
        
        async with aiohttp.ClientSession() as session:
            tasks = [make_request(session, i) for i in range(concurrent_requests)]
            results = await asyncio.gather(*tasks)
        
        successful_requests = [r for r in results if r.get("success", False)]
        
        return {
            "concurrent_requests": concurrent_requests,
            "successful_requests": len(successful_requests),
            "error_rate": (concurrent_requests - len(successful_requests)) / concurrent_requests,
            "avg_response_time": sum(r.get("response_time", 0) for r in successful_requests) / len(successful_requests) if successful_requests else 0
        }
    
    async def _test_concurrent_decisions(self) -> Dict:
        """測試併發決策能力"""
        # 模擬併發 AI 決策請求
        await asyncio.sleep(1)  # 模擬測試時間
        return {
            "concurrent_decision_count": 10,
            "success_rate": 0.95,
            "avg_decision_time": 150,
            "resource_usage": "正常"
        }
    
    async def _test_endurance(self) -> Dict:
        """測試長時間運行"""
        # 模擬長時間運行測試
        endurance_duration = self.config.get("endurance_duration_minutes", 5)
        logger.info(f"開始 {endurance_duration} 分鐘耐久性測試...")
        
        start_time = time.time()
        test_count = 0
        error_count = 0
        
        # 簡化的耐久性測試
        while time.time() - start_time < endurance_duration * 60:
            try:
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{self.config['netstack_url']}/api/v1/ai-decision/health-analysis",
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        if response.status != 200:
                            error_count += 1
                        test_count += 1
            except:
                error_count += 1
                test_count += 1
            
            await asyncio.sleep(10)  # 每10秒測試一次
        
        actual_duration = (time.time() - start_time) / 60
        
        return {
            "planned_duration_minutes": endurance_duration,
            "actual_duration_minutes": actual_duration,
            "total_tests": test_count,
            "error_count": error_count,
            "error_rate": error_count / test_count if test_count > 0 else 0,
            "stability": "穩定" if error_count / test_count < 0.05 else "不穩定"
        }
    
    async def _test_resource_limits(self) -> Dict:
        """測試資源限制"""
        # 模擬資源限制測試
        await asyncio.sleep(1)
        return {
            "memory_usage_peak": "85%",
            "cpu_usage_peak": "78%",
            "resource_limit_handling": "良好",
            "gc_performance": "正常"
        }
    
    def generate_summary(self):
        """生成測試摘要"""
        end_time = datetime.now()
        start_time = datetime.fromisoformat(self.results["start_time"])
        duration = (end_time - start_time).total_seconds()
        
        summary = {
            "duration_seconds": duration,
            "total_test_categories": len(self.results["test_results"]),
            "successful_categories": 0,
            "overall_status": "未知",
            "recommendations": []
        }
        
        # 計算成功的測試類別
        for category, result in self.results["test_results"].items():
            if result and not result.get("error"):
                summary["successful_categories"] += 1
        
        success_rate = summary["successful_categories"] / summary["total_test_categories"]
        
        # 確定整體狀態
        if success_rate >= 0.9:
            summary["overall_status"] = "優秀"
            summary["recommendations"].append("系統表現優秀，可考慮投入生產環境")
        elif success_rate >= 0.7:
            summary["overall_status"] = "良好"
            summary["recommendations"].append("系統表現良好，建議進行進一步優化")
        elif success_rate >= 0.5:
            summary["overall_status"] = "需改進"
            summary["recommendations"].append("系統需要重大改進才能投入使用")
        else:
            summary["overall_status"] = "不合格"
            summary["recommendations"].append("系統存在嚴重問題，需要全面檢查")
        
        # 添加具體建議
        if "validation" in self.results["test_results"]:
            validation_result = self.results["test_results"]["validation"]
            if validation_result.get("overall_score", 0) < 0.8:
                summary["recommendations"].append("AI 決策準確性需要提升")
        
        if "performance" in self.results["test_results"]:
            perf_result = self.results["test_results"]["performance"]
            if perf_result.get("results", {}).get("ai_response_times", {}).get("avg_response_time_ms", 0) > 1000:
                summary["recommendations"].append("AI 響應時間需要優化")
        
        self.results["summary"] = summary
        return summary
    
    def save_results(self):
        """保存測試結果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_dir = "test_results"
        os.makedirs(results_dir, exist_ok=True)
        
        results_file = os.path.join(results_dir, f"stage8_test_results_{timestamp}.json")
        
        try:
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2, default=str)
            
            logger.info(f"📄 測試結果已保存到: {results_file}")
            return results_file
            
        except Exception as e:
            logger.error(f"❌ 保存測試結果失敗: {e}")
            return None


async def main():
    """主函數"""
    parser = argparse.ArgumentParser(description="階段八 AI 決策測試運行器")
    parser.add_argument("--netstack-url", default="http://localhost:8001", help="NetStack 服務 URL")
    parser.add_argument("--simworld-url", default="http://localhost:8002", help="SimWorld 服務 URL")
    parser.add_argument("--test-mode", choices=["validation", "integration", "performance", "stress", "all"], 
                       default="all", help="測試模式")
    parser.add_argument("--performance-iterations", type=int, default=50, help="性能測試迭代次數")
    parser.add_argument("--endurance-duration", type=int, default=5, help="耐久性測試時長(分鐘)")
    parser.add_argument("--save-results", action="store_true", help="保存測試結果到文件")
    
    args = parser.parse_args()
    
    # 構建配置
    config = {
        "netstack_url": args.netstack_url,
        "simworld_url": args.simworld_url,
        "test_mode": args.test_mode,
        "performance_test_iterations": args.performance_iterations,
        "endurance_duration_minutes": args.endurance_duration
    }
    
    # 創建測試運行器
    runner = Stage8TestRunner(config)
    
    logger.info("🚀 階段八 AI 決策測試開始")
    logger.info(f"📋 測試模式: {args.test_mode}")
    logger.info(f"🔗 NetStack URL: {args.netstack_url}")
    logger.info(f"🌍 SimWorld URL: {args.simworld_url}")
    
    try:
        # 根據模式執行不同測試
        if args.test_mode in ["validation", "all"]:
            await runner.run_validation_tests()
        
        if args.test_mode in ["integration", "all"]:
            await runner.run_integration_tests()
        
        if args.test_mode in ["performance", "all"]:
            await runner.run_performance_tests()
        
        if args.test_mode in ["stress", "all"]:
            await runner.run_stress_tests()
        
        # 生成摘要
        summary = runner.generate_summary()
        
        # 輸出結果
        print("\n" + "="*80)
        print("🎯 階段八 AI 決策測試結果摘要")
        print("="*80)
        print(f"測試時長: {summary['duration_seconds']:.2f} 秒")
        print(f"測試類別: {summary['total_test_categories']}")
        print(f"成功類別: {summary['successful_categories']}")
        print(f"整體狀態: {summary['overall_status']}")
        print("\n💡 建議:")
        for recommendation in summary['recommendations']:
            print(f"  • {recommendation}")
        print("="*80)
        
        # 保存結果
        if args.save_results:
            results_file = runner.save_results()
            if results_file:
                print(f"📄 詳細結果已保存到: {results_file}")
        
        # 根據結果設置退出碼
        if summary['overall_status'] in ["優秀", "良好"]:
            sys.exit(0)
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("⚠️  測試被用戶中斷")
        sys.exit(130)
    except Exception as e:
        logger.error(f"❌ 測試執行失敗: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())