#!/usr/bin/env python3
"""
測試 SimWorld 本地 Docker Volume 整合
驗證所有 fallback 機制是否都使用 Docker Volume 本地數據架構
"""

import sys
import os
import json
import logging
from pathlib import Path
from datetime import datetime

# 添加 SimWorld 後端到 Python 路徑
sys.path.append('/home/sat/ntn-stack/simworld/backend')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DockerVolumeIntegrationTester:
    """Docker Volume 整合測試器"""
    
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
    
    def test_docker_volume_paths(self):
        """測試 Docker Volume 路徑配置"""
        print("🐳 測試 Docker Volume 路徑配置...")
        print("=" * 60)
        
        # 預期的 Docker Volume 路徑
        expected_paths = [
            ("/app/data", "NetStack 預計算數據"),
            ("/app/netstack/tle_data", "NetStack TLE 原始數據"),
            ("/app/public/data", "前端公共數據")
        ]
        
        for path_str, description in expected_paths:
            path = Path(path_str)
            exists = path.exists()
            
            self.add_test_result(
                f"docker_volume_path_{path.name}",
                exists,
                f"{description} 路徑檢查",
                f"路徑: {path_str}, 存在: {exists}"
            )
            
            if exists:
                # 檢查路徑內容
                try:
                    contents = list(path.iterdir())
                    self.add_test_result(
                        f"docker_volume_content_{path.name}",
                        len(contents) > 0,
                        f"{description} 內容檢查",
                        f"文件/目錄數量: {len(contents)}"
                    )
                except:
                    self.add_test_result(
                        f"docker_volume_content_{path.name}",
                        False,
                        f"{description} 內容檢查失敗",
                        "無法讀取目錄內容"
                    )
    
    def test_local_volume_service(self):
        """測試本地 Volume 數據服務"""
        print("\n📊 測試本地 Volume 數據服務...")
        print("=" * 60)
        
        try:
            from app.services.local_volume_data_service import get_local_volume_service
            
            service = get_local_volume_service()
            
            self.add_test_result(
                "local_volume_service_creation",
                True,
                "本地 Volume 服務創建成功",
                "服務實例化正常"
            )
            
            # 測試數據可用性檢查
            data_available = service.is_data_available()
            self.add_test_result(
                "local_volume_data_availability",
                data_available,
                "本地數據可用性檢查",
                f"數據可用: {data_available}"
            )
            
            # 測試數據新鮮度檢查
            try:
                import asyncio
                freshness = asyncio.run(service.check_data_freshness())
                has_freshness_info = "precomputed_data" in freshness
                
                self.add_test_result(
                    "local_volume_freshness_check",
                    has_freshness_info,
                    "數據新鮮度檢查功能",
                    f"新鮮度信息: {bool(freshness.get('data_ready'))}"
                )
            except Exception as e:
                self.add_test_result(
                    "local_volume_freshness_check",
                    False,
                    "數據新鮮度檢查失敗",
                    str(e)
                )
            
        except Exception as e:
            self.add_test_result(
                "local_volume_service_import",
                False,
                "本地 Volume 服務導入失敗",
                str(e)
            )
    
    def test_orbit_service_integration(self):
        """測試軌道服務整合"""
        print("\n🛰️ 測試軌道服務 Docker Volume 整合...")
        print("=" * 60)
        
        try:
            # 檢查 orbit_service_netstack.py 是否使用本地數據
            orbit_service_path = Path("/home/sat/ntn-stack/simworld/backend/app/domains/satellite/services/orbit_service_netstack.py")
            
            if orbit_service_path.exists():
                with open(orbit_service_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 檢查是否包含本地 Volume 調用
                has_local_volume_call = "_fetch_latest_tle_from_local_volume" in content
                has_deprecated_celestrak = "_fetch_latest_tle_from_celestrak_deprecated" in content
                no_direct_celestrak = "_fetch_latest_tle_from_celestrak(" not in content.replace("_fetch_latest_tle_from_celestrak_deprecated", "")
                
                self.add_test_result(
                    "orbit_service_local_volume_integration",
                    has_local_volume_call,
                    "軌道服務本地 Volume 整合",
                    f"本地 Volume 調用: {has_local_volume_call}"
                )
                
                self.add_test_result(
                    "orbit_service_celestrak_deprecation",
                    has_deprecated_celestrak,
                    "Celestrak API 調用已廢棄",
                    f"廢棄標記: {has_deprecated_celestrak}"
                )
                
                # 檢查是否有本地數據服務導入
                has_local_service_import = "local_volume_data_service" in content
                
                self.add_test_result(
                    "orbit_service_local_service_import",
                    has_local_service_import,
                    "軌道服務本地數據服務導入",
                    f"導入本地服務: {has_local_service_import}"
                )
            else:
                self.add_test_result(
                    "orbit_service_file_check",
                    False,
                    "軌道服務文件不存在",
                    str(orbit_service_path)
                )
        
        except Exception as e:
            self.add_test_result(
                "orbit_service_integration_check",
                False,
                "軌道服務整合檢查失敗",
                str(e)
            )
    
    def test_tle_fallback_integration(self):
        """測試 TLE Fallback 整合"""
        print("\n📡 測試 TLE Fallback Docker Volume 整合...")
        print("=" * 60)
        
        try:
            # 檢查 tle_init_fallback.py 是否使用本地數據
            fallback_path = Path("/home/sat/ntn-stack/simworld/backend/app/db/tle_init_fallback.py")
            
            if fallback_path.exists():
                with open(fallback_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 檢查是否包含衛星數據架構相關內容
                has_architecture_reference = "satellite_data_architecture.md" in content
                has_docker_volume_priority = "Docker Volume 本地數據" in content
                has_local_volume_function = "_load_from_docker_volume" in content
                no_celestrak_priority = "CelesTrak 下載最新" not in content
                
                self.add_test_result(
                    "tle_fallback_architecture_reference",
                    has_architecture_reference,
                    "TLE Fallback 架構文檔引用",
                    f"架構引用: {has_architecture_reference}"
                )
                
                self.add_test_result(
                    "tle_fallback_docker_volume_priority",
                    has_docker_volume_priority,
                    "TLE Fallback Docker Volume 優先級",
                    f"本地數據優先: {has_docker_volume_priority}"
                )
                
                self.add_test_result(
                    "tle_fallback_local_volume_function",
                    has_local_volume_function,
                    "TLE Fallback 本地 Volume 載入函數",
                    f"本地載入函數: {has_local_volume_function}"
                )
                
                self.add_test_result(
                    "tle_fallback_no_celestrak_priority",
                    no_celestrak_priority,
                    "TLE Fallback 移除 Celestrak 優先級",
                    f"不再優先 Celestrak: {no_celestrak_priority}"
                )
            else:
                self.add_test_result(
                    "tle_fallback_file_check",
                    False,
                    "TLE Fallback 文件不存在",
                    str(fallback_path)
                )
        
        except Exception as e:
            self.add_test_result(
                "tle_fallback_integration_check",
                False,
                "TLE Fallback 整合檢查失敗",
                str(e)
            )
    
    def test_frontend_volume_configuration(self):
        """測試前端 Volume 配置"""
        print("\n🎨 測試前端 Docker Volume 配置...")
        print("=" * 60)
        
        try:
            # 檢查前端預計算數據服務
            frontend_service_path = Path("/home/sat/ntn-stack/simworld/frontend/src/services/precomputedDataService.ts")
            
            if frontend_service_path.exists():
                with open(frontend_service_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 檢查是否使用正確的 Docker Volume 路徑
                uses_data_path = "/data/" in content
                has_volume_priority = "phase0_precomputed_orbits.json" in content
                no_external_api_calls = "http://localhost" not in content and "https://api" not in content
                
                self.add_test_result(
                    "frontend_data_path_usage",
                    uses_data_path,
                    "前端使用 Docker Volume 數據路徑",
                    f"使用 /data/ 路徑: {uses_data_path}"
                )
                
                self.add_test_result(
                    "frontend_volume_priority",
                    has_volume_priority,
                    "前端 Volume 數據優先級",
                    f"優先本地數據: {has_volume_priority}"
                )
                
                self.add_test_result(
                    "frontend_no_external_api",
                    no_external_api_calls,
                    "前端無外部 API 調用",
                    f"無外部 API: {no_external_api_calls}"
                )
            else:
                self.add_test_result(
                    "frontend_service_file_check",
                    False,
                    "前端服務文件不存在",
                    str(frontend_service_path)
                )
        
        except Exception as e:
            self.add_test_result(
                "frontend_volume_configuration_check",
                False,
                "前端 Volume 配置檢查失敗",
                str(e)
            )
    
    def test_docker_compose_configuration(self):
        """測試 Docker Compose 配置"""
        print("\n🐳 測試 Docker Compose Volume 配置...")
        print("=" * 60)
        
        try:
            # 檢查 docker-compose.yml
            compose_path = Path("/home/sat/ntn-stack/simworld/docker-compose.yml")
            
            if compose_path.exists():
                with open(compose_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 檢查 Volume 掛載配置
                has_netstack_tle_mount = "../netstack/tle_data:/app/netstack/tle_data" in content
                has_satellite_data_volume = "satellite_precomputed_data:/app/public/data" in content
                has_external_volume = "external: true" in content and "compose_satellite_precomputed_data" in content
                
                self.add_test_result(
                    "docker_compose_netstack_tle_mount",
                    has_netstack_tle_mount,
                    "Docker Compose NetStack TLE 掛載",
                    f"TLE 數據掛載: {has_netstack_tle_mount}"
                )
                
                self.add_test_result(
                    "docker_compose_satellite_data_volume",
                    has_satellite_data_volume,
                    "Docker Compose 衛星數據 Volume",
                    f"衛星數據 Volume: {has_satellite_data_volume}"
                )
                
                self.add_test_result(
                    "docker_compose_external_volume",
                    has_external_volume,
                    "Docker Compose 外部 Volume 配置",
                    f"外部 Volume: {has_external_volume}"
                )
            else:
                self.add_test_result(
                    "docker_compose_file_check",
                    False,
                    "Docker Compose 文件不存在",
                    str(compose_path)
                )
        
        except Exception as e:
            self.add_test_result(
                "docker_compose_configuration_check",
                False,
                "Docker Compose 配置檢查失敗",
                str(e)
            )
    
    def generate_report(self):
        """生成測試報告"""
        success_rate = (self.results["passed_tests"] / max(1, self.results["total_tests"])) * 100
        
        print("\n" + "="*80)
        print("🐳 SIMWORLD DOCKER VOLUME 整合測試報告")
        print("="*80)
        print(f"測試時間: {self.results['timestamp']}")
        print(f"總測試數: {self.results['total_tests']}")
        print(f"通過測試: {self.results['passed_tests']}")
        print(f"失敗測試: {self.results['failed_tests']}")
        print(f"成功率: {success_rate:.1f}%")
        print()
        
        # 按類別分組顯示結果
        categories = {
            "Docker Volume 路徑": [r for r in self.results["test_results"] if "docker_volume_path" in r["test_name"]],
            "本地數據服務": [r for r in self.results["test_results"] if "local_volume" in r["test_name"]],
            "軌道服務整合": [r for r in self.results["test_results"] if "orbit_service" in r["test_name"]],
            "TLE Fallback 整合": [r for r in self.results["test_results"] if "tle_fallback" in r["test_name"]],
            "前端配置": [r for r in self.results["test_results"] if "frontend" in r["test_name"]],
            "Docker Compose": [r for r in self.results["test_results"] if "docker_compose" in r["test_name"]]
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
        
        # 架構合規性評估
        print("📊 衛星數據架構合規性評估:")
        architecture_compliance_tests = [
            r for r in self.results["test_results"] 
            if any(keyword in r["test_name"] for keyword in ["docker_volume", "local_volume", "no_external", "architecture"])
        ]
        
        compliance_rate = (sum(1 for t in architecture_compliance_tests if t["passed"]) / max(1, len(architecture_compliance_tests))) * 100
        
        print(f"   架構合規測試: {len(architecture_compliance_tests)}")
        print(f"   合規率: {compliance_rate:.1f}%")
        
        if compliance_rate >= 90:
            print("   🎉 優秀！完全符合衛星數據架構要求")
        elif compliance_rate >= 75:
            print("   👍 良好！大部分符合架構要求")
        else:
            print("   ⚠️  需要更多工作以符合架構要求")
        
        print("="*80)
        
        return success_rate >= 75
    
    def run_all_tests(self):
        """運行所有測試"""
        logger.info("🚀 開始 SimWorld Docker Volume 整合測試...")
        
        self.test_docker_volume_paths()
        self.test_local_volume_service()
        self.test_orbit_service_integration()
        self.test_tle_fallback_integration()
        self.test_frontend_volume_configuration()
        self.test_docker_compose_configuration()
        
        return self.generate_report()


def main():
    """主函數"""
    try:
        print("🐳 SimWorld Docker Volume 整合測試")
        print("=" * 80)
        print("根據 @docs/satellite_data_architecture.md 驗證整合狀況")
        print()
        
        tester = DockerVolumeIntegrationTester()
        success = tester.run_all_tests()
        
        # 保存詳細報告
        report_path = "/tmp/simworld_docker_volume_integration_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(tester.results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 詳細報告已保存到: {report_path}")
        
        return 0 if success else 1
        
    except Exception as e:
        logger.error(f"❌ 測試過程出錯: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)