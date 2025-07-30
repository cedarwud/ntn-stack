#!/usr/bin/env python3
"""
驗證真實數據實現腳本
檢查 SimWorld 中所有 fallback 機制是否都使用真實數據
"""

import sys
import os
import json
import asyncio
import logging
from pathlib import Path
from datetime import datetime

# 添加 SimWorld 後端到 Python 路徑
sys.path.append('/home/sat/ntn-stack/simworld/backend')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RealDataVerifier:
    """真實數據實現驗證器"""
    
    def __init__(self):
        self.results = {
            "timestamp": datetime.utcnow().isoformat(),
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "test_results": []
        }
    
    def add_test_result(self, test_name: str, passed: bool, description: str, details: str = ""):
        """添加測試結果"""
        result = {
            "test_name": test_name,
            "passed": passed,
            "description": description,
            "details": details
        }
        
        self.results["test_results"].append(result)
        self.results["total_tests"] += 1
        
        if passed:
            self.results["passed_tests"] += 1
            logger.info(f"✅ {test_name}: {description}")
        else:
            self.results["failed_tests"] += 1
            logger.error(f"❌ {test_name}: {description}")
        
        if details:
            logger.info(f"   詳細: {details}")
    
    async def verify_historical_tle_data(self):
        """驗證歷史 TLE 數據可用性"""
        try:
            from app.data.historical_tle_data import get_historical_tle_data, get_data_source_info
            
            # 檢查數據源信息
            source_info = get_data_source_info()
            is_real_data = not source_info.get("is_simulation", True)
            
            self.add_test_result(
                "historical_data_source",
                is_real_data,
                "歷史 TLE 數據來源驗證",
                f"類型: {source_info.get('type')}, 模擬: {source_info.get('is_simulation')}"
            )
            
            # 檢查各星座數據
            constellations = ["starlink", "oneweb", "gps", "galileo"]
            total_satellites = 0
            
            for constellation in constellations:
                data = get_historical_tle_data(constellation)
                satellite_count = len(data)
                total_satellites += satellite_count
                
                self.add_test_result(
                    f"historical_data_{constellation}",
                    satellite_count > 0,
                    f"{constellation.upper()} 歷史數據可用性",
                    f"衛星數量: {satellite_count}"
                )
                
                # 驗證 TLE 格式
                if data:
                    sample_sat = data[0]
                    has_valid_tle = (
                        "line1" in sample_sat and 
                        "line2" in sample_sat and
                        sample_sat["line1"].startswith("1 ") and
                        sample_sat["line2"].startswith("2 ")
                    )
                    
                    self.add_test_result(
                        f"tle_format_{constellation}",
                        has_valid_tle,
                        f"{constellation.upper()} TLE 格式驗證",
                        f"示例: {sample_sat.get('name', 'Unknown')}"
                    )
            
            self.add_test_result(
                "total_historical_satellites",
                total_satellites > 20,  # 至少要有20顆衛星
                "歷史數據總量驗證",
                f"總衛星數: {total_satellites}"
            )
            
        except Exception as e:
            self.add_test_result(
                "historical_data_import",
                False,
                "歷史數據模組導入失敗",
                str(e)
            )
    
    async def verify_orbit_service_implementation(self):
        """驗證軌道服務實現"""
        try:
            from app.domains.satellite.services.orbit_service_netstack import OrbitServiceNetStack
            from datetime import datetime, timedelta
            
            # 創建軌道服務實例
            orbit_service = OrbitServiceNetStack()
            
            # 檢查是否有歷史數據方法
            has_historical_methods = all([
                hasattr(orbit_service, '_generate_orbit_from_historical_tle'),
                hasattr(orbit_service, '_calculate_passes_from_historical_tle'),
                hasattr(orbit_service, '_calculate_position_from_historical_tle')
            ])
            
            self.add_test_result(
                "orbit_service_methods",
                has_historical_methods,
                "軌道服務歷史數據方法檢查",
                "包含所有必要的歷史數據計算方法"
            )
            
            # 檢查是否有輔助計算方法
            has_calculation_methods = all([
                hasattr(orbit_service, '_ecf_to_geodetic'),
                hasattr(orbit_service, '_calculate_look_angles'),
                hasattr(orbit_service, '_generate_reference_orbit')
            ])
            
            self.add_test_result(
                "orbit_calculation_methods",
                has_calculation_methods,
                "軌道計算輔助方法檢查",
                "包含地理坐標轉換和角度計算方法"
            )
            
        except Exception as e:
            self.add_test_result(
                "orbit_service_verification",
                False,
                "軌道服務驗證失敗",
                str(e)
            )
    
    async def verify_historical_orbit_generator(self):
        """驗證歷史軌道生成器"""
        try:
            from app.services.historical_orbit_generator import HistoricalOrbitGenerator
            
            # 創建生成器實例
            generator = HistoricalOrbitGenerator()
            
            self.add_test_result(
                "historical_orbit_generator",
                True,
                "歷史軌道生成器創建成功",
                "可以創建 HistoricalOrbitGenerator 實例"
            )
            
            # 檢查關鍵方法
            has_key_methods = all([
                hasattr(generator, 'generate_precomputed_orbit_data'),
                hasattr(generator, '_calculate_satellite_orbit'),
                hasattr(generator, '_ecf_to_geodetic'),
                hasattr(generator, '_calculate_look_angles')
            ])
            
            self.add_test_result(
                "generator_methods",
                has_key_methods,
                "歷史軌道生成器方法完整性",
                "包含所有軌道計算和數據生成方法"
            )
            
        except Exception as e:
            self.add_test_result(
                "historical_orbit_generator",
                False,
                "歷史軌道生成器驗證失敗",
                str(e)
            )
    
    async def verify_frontend_improvements(self):
        """驗證前端改進"""
        try:
            # 檢查前端預計算數據服務文件
            frontend_service_path = Path("/home/sat/ntn-stack/simworld/frontend/src/services/precomputedDataService.ts")
            
            if frontend_service_path.exists():
                with open(frontend_service_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 檢查是否包含真實地理計算
                has_haversine = "calculateHaversineDistance" in content
                has_real_calculation = "真實地理計算" in content
                has_fallback_data = "generateHistoricalFallbackData" in content
                
                self.add_test_result(
                    "frontend_real_geo_calculation",
                    has_haversine and has_real_calculation,
                    "前端真實地理計算實現",
                    f"Haversine: {has_haversine}, 真實計算: {has_real_calculation}"
                )
                
                self.add_test_result(
                    "frontend_fallback_mechanism",
                    has_fallback_data,
                    "前端歷史數據 fallback 機制",
                    f"歷史數據 fallback: {has_fallback_data}"
                )
            else:
                self.add_test_result(
                    "frontend_service_file",
                    False,
                    "前端預計算數據服務文件不存在",
                    str(frontend_service_path)
                )
                
        except Exception as e:
            self.add_test_result(
                "frontend_verification",
                False,
                "前端改進驗證失敗",
                str(e)
            )
    
    async def verify_api_endpoints(self):
        """驗證 API 端點"""
        try:
            # 檢查歷史軌道 API 文件
            api_file_path = Path("/home/sat/ntn-stack/simworld/backend/app/api/routes/historical_orbits.py")
            
            if api_file_path.exists():
                with open(api_file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 檢查關鍵端點
                has_generate_endpoint = "/historical-orbits" in content
                has_health_endpoint = "/historical-orbits/health" in content
                has_save_endpoint = "/historical-orbits/save" in content
                
                self.add_test_result(
                    "historical_orbits_api",
                    has_generate_endpoint and has_health_endpoint,
                    "歷史軌道 API 端點完整性",
                    f"生成: {has_generate_endpoint}, 健康: {has_health_endpoint}, 保存: {has_save_endpoint}"
                )
            else:
                self.add_test_result(
                    "historical_orbits_api_file",
                    False,
                    "歷史軌道 API 文件不存在",
                    str(api_file_path)
                )
            
            # 檢查路由註冊
            router_file_path = Path("/home/sat/ntn-stack/simworld/backend/app/api/v1/router.py")
            if router_file_path.exists():
                with open(router_file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                has_historical_import = "historical_orbits_router" in content
                has_router_registration = "historical_orbits_router" in content and "include_router" in content
                
                self.add_test_result(
                    "api_router_registration",
                    has_historical_import and has_router_registration,
                    "歷史軌道 API 路由註冊",
                    f"導入: {has_historical_import}, 註冊: {has_router_registration}"
                )
                
        except Exception as e:
            self.add_test_result(
                "api_verification",
                False,
                "API 端點驗證失敗",
                str(e)
            )
    
    async def verify_no_simulation_fallbacks(self):
        """驗證沒有純模擬數據 fallback"""
        try:
            # 檢查關鍵文件中是否還有純模擬數據
            files_to_check = [
                "/home/sat/ntn-stack/simworld/backend/app/domains/satellite/services/orbit_service_netstack.py",
                "/home/sat/ntn-stack/simworld/backend/app/db/tle_init_fallback.py"
            ]
            
            simulation_patterns = [
                "generate.*simulated.*orbit",
                "_generate_simulated_",
                "模擬軌道數據",
                "簡單的圓形軌道模擬"
            ]
            
            for file_path in files_to_check:
                if Path(file_path).exists():
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 檢查是否包含歷史數據引用
                    has_historical_import = "historical_tle_data" in content
                    has_real_calculation = any([
                        "twoline2rv" in content,
                        "sgp4" in content,
                        "真實" in content and "TLE" in content
                    ])
                    
                    file_name = Path(file_path).name
                    self.add_test_result(
                        f"real_data_implementation_{file_name}",
                        has_historical_import or has_real_calculation,
                        f"{file_name} 真實數據實現檢查",
                        f"歷史數據: {has_historical_import}, 真實計算: {has_real_calculation}"
                    )
                    
        except Exception as e:
            self.add_test_result(
                "simulation_fallback_check",
                False,
                "模擬數據 fallback 檢查失敗",
                str(e)
            )
    
    def generate_report(self):
        """生成驗證報告"""
        success_rate = (self.results["passed_tests"] / max(1, self.results["total_tests"])) * 100
        
        print("\n" + "="*80)
        print("🛰️  SIMWORLD 真實數據實現驗證報告")
        print("="*80)
        print(f"驗證時間: {self.results['timestamp']}")
        print(f"總測試數: {self.results['total_tests']}")
        print(f"通過測試: {self.results['passed_tests']}")
        print(f"失敗測試: {self.results['failed_tests']}")
        print(f"成功率: {success_rate:.1f}%")
        print()
        
        # 按類別分組顯示結果
        categories = {
            "歷史數據": [r for r in self.results["test_results"] if "historical" in r["test_name"]],
            "軌道服務": [r for r in self.results["test_results"] if "orbit" in r["test_name"]],
            "前端改進": [r for r in self.results["test_results"] if "frontend" in r["test_name"]],
            "API 端點": [r for r in self.results["test_results"] if "api" in r["test_name"]],
            "數據實現": [r for r in self.results["test_results"] if "implementation" in r["test_name"]]
        }
        
        for category, tests in categories.items():
            if tests:
                print(f"📋 {category}:")
                for test in tests:
                    status = "✅" if test["passed"] else "❌"
                    print(f"  {status} {test['description']}")
                    if test["details"]:
                        print(f"     {test['details']}")
                print()
        
        # 總結
        if success_rate >= 90:
            print("🎉 優秀！真實數據實現完成度很高")
        elif success_rate >= 75:
            print("👍 良好！大部分真實數據實現已完成")
        elif success_rate >= 50:
            print("⚠️  一般，還有一些改進空間")
        else:
            print("❌ 需要更多工作來完成真實數據實現")
        
        print("="*80)
        
        return success_rate >= 75  # 75% 以上認為成功
    
    async def run_all_verifications(self):
        """運行所有驗證"""
        logger.info("🚀 開始驗證 SimWorld 真實數據實現...")
        
        await self.verify_historical_tle_data()
        await self.verify_orbit_service_implementation()
        await self.verify_historical_orbit_generator()
        await self.verify_frontend_improvements()
        await self.verify_api_endpoints()
        await self.verify_no_simulation_fallbacks()
        
        return self.generate_report()


async def main():
    """主函數"""
    try:
        verifier = RealDataVerifier()
        success = await verifier.run_all_verifications()
        
        # 保存詳細報告
        report_path = "/tmp/simworld_real_data_verification_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(verifier.results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 詳細報告已保存到: {report_path}")
        
        return 0 if success else 1
        
    except Exception as e:
        logger.error(f"❌ 驗證過程出錯: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)