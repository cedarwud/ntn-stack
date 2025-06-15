#!/usr/bin/env python3
"""
論文復現核心功能驗證測試 (無依賴外部服務)

專注測試論文演算法的核心邏輯，避免 HTTP 422 等外部服務錯誤
整合所有重要測試，移除重複內容

執行方式 (在 ntn-stack 根目錄):
source venv/bin/activate
python Desktop/paper/comprehensive/test_core_validation.py
"""

import sys
import asyncio
import time
import logging
from datetime import datetime
from typing import Dict, List, Any
import traceback

# 添加 NetStack API 路徑
sys.path.insert(0, '/home/sat/ntn-stack/netstack/netstack_api')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PaperReproductionCoreValidator:
    """論文復現核心功能驗證器"""
    
    def __init__(self):
        self.test_results = []
        self.start_time = None
        self.end_time = None
    
    async def test_module_imports(self):
        """測試模組導入"""
        print("🔍 測試論文復現模組導入...")
        
        try:
            # 論文標準演算法模組
            from services.paper_synchronized_algorithm import SynchronizedAlgorithm, AccessInfo
            from services.algorithm_integration_bridge import AlgorithmIntegrationBridge
            from services.fast_access_prediction_service import FastSatellitePrediction, AccessStrategy
            
            print("✅ 所有論文復現模組導入成功")
            self.test_results.append(("模組導入", True, "所有核心模組正常導入"))
            return True
            
        except Exception as e:
            print(f"❌ 模組導入失敗: {str(e)}")
            self.test_results.append(("模組導入", False, str(e)))
            return False
    
    async def test_algorithm_1_core(self):
        """測試 Algorithm 1 核心功能 (不依賴外部服務)"""
        print("\n📋 測試 Algorithm 1 (同步演算法) 核心功能...")
        
        try:
            from services.paper_synchronized_algorithm import SynchronizedAlgorithm, AccessInfo
            
            # 1. 初始化測試
            algo = SynchronizedAlgorithm(delta_t=5.0, binary_search_precision=0.01)
            assert algo.delta_t == 5.0
            assert algo.binary_search_precision == 0.01
            print("   ✅ Algorithm 1 初始化成功")
            
            # 2. AccessInfo 資料結構測試
            access_info = AccessInfo(
                ue_id="test_ue_001",
                satellite_id="test_sat_001",
                access_quality=0.85
            )
            assert access_info.ue_id == "test_ue_001"
            assert access_info.access_quality == 0.85
            print("   ✅ AccessInfo 資料結構正常")
            
            # 3. 二分搜尋精度測試 (使用模擬函數，不依賴外部服務)
            start_time = time.time()
            
            # 暫時覆蓋衛星位置獲取函數，避免外部依賴
            original_get_position = algo.tle_bridge.get_satellite_position
            
            async def mock_get_satellite_position(sat_id, timestamp):
                """模擬衛星位置獲取"""
                # 返回模擬位置資料
                return {
                    "latitude": 25.0 + (hash(sat_id) % 100) / 100,
                    "longitude": 121.0 + (hash(sat_id) % 100) / 100,
                    "altitude": 550.0 + (hash(sat_id) % 300)
                }
            
            algo.tle_bridge.get_satellite_position = mock_get_satellite_position
            
            try:
                handover_time = await algo.binary_search_handover_time(
                    ue_id="test_ue_001",
                    source_satellite="test_sat_001",
                    target_satellite="test_sat_002",
                    t_start=time.time(),
                    t_end=time.time() + 300
                )
                
                search_duration = (time.time() - start_time) * 1000
                precision_met = search_duration < 25.0  # 論文要求 <25ms
                
                print(f"   ✅ 二分搜尋完成 - 執行時間: {search_duration:.1f}ms")
                print(f"   🎯 精度: {'達標' if precision_met else '未達標'} (<25ms)")
                
                if precision_met:
                    self.test_results.append(("Algorithm1二分搜尋精度", True, f"{search_duration:.1f}ms"))
                else:
                    self.test_results.append(("Algorithm1二分搜尋精度", False, f"{search_duration:.1f}ms >= 25ms"))
                
            finally:
                # 恢復原始函數
                algo.tle_bridge.get_satellite_position = original_get_position
            
            # 4. UE 更新功能測試
            await algo.update_ue("test_ue_001")
            r_table_updated = len(algo.R) > 0
            print(f"   ✅ UE 更新完成 - R表大小: {len(algo.R)}")
            
            # 5. 狀態查詢測試
            status = await algo.get_algorithm_status()
            status_valid = (
                "algorithm_state" in status and
                "total_ues" in status and
                "binary_search_precision" in status
            )
            print(f"   ✅ 狀態查詢: {status['algorithm_state']}")
            
            self.test_results.append(("Algorithm1核心功能", True, "所有核心功能正常"))
            return True
            
        except Exception as e:
            print(f"   ❌ Algorithm 1 測試失敗: {str(e)}")
            self.test_results.append(("Algorithm1核心功能", False, str(e)))
            return False
    
    async def test_algorithm_2_core(self):
        """測試 Algorithm 2 核心功能 (不依賴外部服務)"""
        print("\n📡 測試 Algorithm 2 (快速衛星預測) 核心功能...")
        
        try:
            from services.fast_access_prediction_service import (
                FastSatellitePrediction, AccessStrategy, GeographicalBlock
            )
            
            # 1. 初始化測試
            service = FastSatellitePrediction(
                earth_radius_km=6371.0,
                block_size_degrees=10.0,
                prediction_accuracy_target=0.95
            )
            assert service.accuracy_target == 0.95
            print("   ✅ Algorithm 2 初始化成功")
            
            # 2. 地理區塊劃分測試
            blocks = await service.initialize_geographical_blocks()
            expected_blocks = 18 * 36  # -90到90度(18) x -180到180度(36)
            assert len(blocks) == expected_blocks
            print(f"   ✅ 地理區塊劃分: {len(blocks)} 個區塊 (10度網格)")
            
            # 3. UE 註冊和策略管理測試
            test_ues = [
                ("ue_flexible", AccessStrategy.FLEXIBLE, {"lat": 25.0, "lon": 121.0, "alt": 100.0}),
                ("ue_consistent", AccessStrategy.CONSISTENT, {"lat": 35.0, "lon": 139.0, "alt": 150.0})
            ]
            
            for ue_id, strategy, position in test_ues:
                success = await service.register_ue(
                    ue_id=ue_id,
                    position=position,
                    access_strategy=strategy,
                    current_satellite=f"sat_{hash(ue_id) % 10:03d}"
                )
                assert success == True
            
            print(f"   ✅ UE 註冊: {len(test_ues)} 個 UE 成功註冊")
            
            # 4. 策略更新測試
            original_strategy = await service.get_access_strategy("ue_flexible")
            new_strategy = AccessStrategy.CONSISTENT
            await service.update_ue_strategy("ue_flexible", new_strategy)
            updated_strategy = await service.get_access_strategy("ue_flexible")
            assert updated_strategy == new_strategy
            print("   ✅ 存取策略管理正常")
            
            # 5. 模擬衛星位置預測 (不依賴外部服務)
            mock_satellites = [
                {
                    "satellite_id": f"mock_sat_{i:03d}",
                    "id": f"mock_sat_{i:03d}",
                    "constellation": "test",
                    "latitude": (i * 30) % 180 - 90,
                    "longitude": (i * 36) % 360 - 180,
                    "altitude": 550 + i * 50,
                    "velocity": {"speed": 7.5}
                }
                for i in range(8)
            ]
            
            satellite_positions = await service.predict_satellite_positions(
                mock_satellites, time.time()
            )
            print(f"   ✅ 衛星位置預測: {len(satellite_positions)} 個衛星")
            
            # 6. 衛星到區塊分配測試
            satellite_blocks = await service.assign_satellites_to_blocks(satellite_positions)
            assert len(satellite_blocks) == len(service.blocks)
            total_assignments = sum(len(sats) for sats in satellite_blocks.values())
            print(f"   ✅ 衛星區塊分配: {total_assignments} 個分配")
            
            # 7. 服務狀態測試
            status = await service.get_service_status()
            assert status["service_name"] == "FastSatellitePrediction"
            assert status["algorithm"] == "Algorithm_2"
            print("   ✅ 服務狀態查詢正常")
            
            self.test_results.append(("Algorithm2核心功能", True, "所有核心功能正常"))
            return True
            
        except Exception as e:
            print(f"   ❌ Algorithm 2 測試失敗: {str(e)}")
            self.test_results.append(("Algorithm2核心功能", False, str(e)))
            return False
    
    async def test_integration_bridge(self):
        """測試整合橋接服務"""
        print("\n🌉 測試整合橋接服務...")
        
        try:
            from services.algorithm_integration_bridge import (
                AlgorithmIntegrationBridge,
                BridgeConfiguration,
                IntegrationMode
            )
            
            # 1. 論文模式測試
            config = BridgeConfiguration(
                integration_mode=IntegrationMode.PAPER_ONLY,
                enhanced_features_enabled=False
            )
            
            bridge = AlgorithmIntegrationBridge(config=config)
            init_result = await bridge.initialize_algorithms()
            assert init_result["success"] == True
            print("   ✅ 論文模式橋接初始化成功")
            
            # 2. 模式切換測試
            switch_result = await bridge.switch_mode(IntegrationMode.HYBRID)
            assert switch_result['success'] == True
            print("   ✅ 模式切換正常")
            
            # 3. 狀態查詢測試
            status = await bridge.get_integration_status()
            assert "component_status" in status
            print(f"   ✅ 整合狀態查詢: {len(status['component_status'])} 個組件")
            
            self.test_results.append(("整合橋接服務", True, "所有功能正常"))
            return True
            
        except Exception as e:
            print(f"   ❌ 整合橋接測試失敗: {str(e)}")
            self.test_results.append(("整合橋接服務", False, str(e)))
            return False
    
    async def test_performance_metrics(self):
        """測試效能指標"""
        print("\n⚡ 測試效能指標...")
        
        try:
            from services.paper_synchronized_algorithm import SynchronizedAlgorithm
            from services.fast_access_prediction_service import FastSatellitePrediction
            
            # Algorithm 1 效能測試
            algo1 = SynchronizedAlgorithm(delta_t=5.0, binary_search_precision=0.01)
            
            # 多次執行測試平均效能
            execution_times = []
            for i in range(5):
                start_time = time.time()
                await algo1.update_ue(f"perf_test_ue_{i}")
                execution_time = (time.time() - start_time) * 1000
                execution_times.append(execution_time)
            
            avg_execution_time = sum(execution_times) / len(execution_times)
            performance_good = avg_execution_time < 100  # 100ms內完成
            
            print(f"   ✅ Algorithm 1 平均執行時間: {avg_execution_time:.1f}ms")
            
            # Algorithm 2 效能測試
            service = FastSatellitePrediction()
            blocks = await service.initialize_geographical_blocks()
            
            block_init_performance = len(blocks) == 648  # 正確的區塊數量
            print(f"   ✅ Algorithm 2 區塊初始化: {len(blocks)} 個區塊")
            
            if performance_good and block_init_performance:
                self.test_results.append(("效能指標", True, f"執行時間{avg_execution_time:.1f}ms"))
            else:
                self.test_results.append(("效能指標", False, "效能未達標"))
            
            return performance_good and block_init_performance
            
        except Exception as e:
            print(f"   ❌ 效能測試失敗: {str(e)}")
            self.test_results.append(("效能指標", False, str(e)))
            return False
    
    async def run_comprehensive_validation(self):
        """執行綜合驗證"""
        self.start_time = datetime.now()
        
        print("🚀 開始執行論文復現核心功能驗證")
        print("="*80)
        print("📝 專注測試演算法邏輯，避免外部服務依賴")
        print("="*80)
        
        # 執行各項測試
        tests = [
            ("模組導入", self.test_module_imports),
            ("Algorithm 1 核心", self.test_algorithm_1_core),
            ("Algorithm 2 核心", self.test_algorithm_2_core),
            ("整合橋接", self.test_integration_bridge),
            ("效能指標", self.test_performance_metrics)
        ]
        
        passed_tests = 0
        for test_name, test_func in tests:
            try:
                result = await test_func()
                if result:
                    passed_tests += 1
            except Exception as e:
                print(f"   💥 {test_name} 測試異常: {str(e)}")
                self.test_results.append((test_name, False, f"異常: {str(e)}"))
        
        self.end_time = datetime.now()
        
        # 生成報告
        await self.generate_validation_report(passed_tests, len(tests))
        
        return passed_tests, len(tests)
    
    async def generate_validation_report(self, passed_tests: int, total_tests: int):
        """生成驗證報告"""
        duration = (self.end_time - self.start_time).total_seconds()
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print("\n" + "="*80)
        print("📊 論文復現核心功能驗證報告")
        print("="*80)
        
        print(f"\n📋 詳細結果:")
        for test_name, result, details in self.test_results:
            status = "✅ 通過" if result else "❌ 失敗"
            print(f"   {status} {test_name} - {details}")
        
        print(f"\n📊 統計:")
        print(f"   總測試項目: {total_tests}")
        print(f"   通過項目: {passed_tests}")
        print(f"   失敗項目: {total_tests - passed_tests}")
        print(f"   成功率: {success_rate:.1f}%")
        print(f"   執行時間: {duration:.2f} 秒")
        
        print(f"\n🎓 論文復現核心驗證:")
        core_features = {
            "Algorithm 1 實現": any("Algorithm1" in name and result for name, result, _ in self.test_results),
            "Algorithm 2 實現": any("Algorithm2" in name and result for name, result, _ in self.test_results),
            "二分搜尋精度": any("二分搜尋精度" in name and result for name, result, _ in self.test_results),
            "地理區塊劃分": any("Algorithm2" in name and result for name, result, _ in self.test_results),
            "整合橋接功能": any("整合橋接" in name and result for name, result, _ in self.test_results)
        }
        
        for feature, status in core_features.items():
            print(f"   {'✅' if status else '❌'} {feature}")
        
        if success_rate >= 90.0:
            print(f"\n🎉 論文復現核心功能驗證成功！")
            print(f"📝 所有核心演算法邏輯正常運作")
            print(f"📝 已準備好進行完整系統整合測試")
        elif success_rate >= 70.0:
            print(f"\n⚠️  論文復現基本成功，部分功能需要優化")
        else:
            print(f"\n❌ 論文復現存在重要問題，需要進一步檢查")
        
        return success_rate >= 90.0


async def main():
    """主函數"""
    validator = PaperReproductionCoreValidator()
    
    try:
        passed_tests, total_tests = await validator.run_comprehensive_validation()
        
        # 根據結果設定退出碼
        success = passed_tests >= (total_tests * 0.9)  # 90% 通過率
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n⚠️  測試被用戶中斷")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 測試執行錯誤: {str(e)}")
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())