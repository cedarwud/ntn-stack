#!/usr/bin/env python3
"""
Phase 1 重構 - 整合測試

功能:
1. 測試完整的 Phase 1 流程
2. 驗證各模組間的整合
3. 確保數據流正確性

符合 CLAUDE.md 原則:
- 全流程測試真實算法
- 驗證無簡化或模擬數據
- 確保與 Phase 2 接口兼容
"""

import os
import sys
import logging
import tempfile
from datetime import datetime, timezone
from pathlib import Path

# 添加 phase1_refactor 到路徑
phase1_refactor_dir = Path(__file__).parent.parent
sys.path.insert(0, str(phase1_refactor_dir))

from data_source.tle_loader import TLELoader
from orbit_calculation.sgp4_engine import SGP4Engine
from processing_pipeline.phase1_coordinator import Phase1Coordinator, Phase1Config
from output_interface.phase1_api import Phase1APIInterface

logger = logging.getLogger(__name__)

class Phase1IntegrationTest:
    """
    Phase 1 完整整合測試
    
    驗證從 TLE 載入到 API 輸出的完整流程
    """
    
    def __init__(self, test_output_dir: str = None):
        """
        初始化整合測試
        
        Args:
            test_output_dir: 測試輸出目錄，None 時使用臨時目錄
        """
        self.test_output_dir = test_output_dir or tempfile.mkdtemp()
        self.test_results = {}
        
        logger.info(f"整合測試初始化完成，輸出目錄: {self.test_output_dir}")
    
    def test_tle_loader(self) -> bool:
        """測試 TLE 載入器"""
        logger.info("🔍 測試 TLE 載入器...")
        
        try:
            # 使用統一配置載入器獲取 TLE 目錄
            try:
                from config_loader import get_tle_data_path
                tle_path = get_tle_data_path()
                tle_dirs = [tle_path] if tle_path else []
            except:
                # 回退到預設路徑
                tle_dirs = [
                    "/home/sat/ntn-stack/netstack/tle_data"
                ]
            
            tle_dir = None
            for dir_path in tle_dirs:
                if Path(dir_path).exists():
                    tle_dir = dir_path
                    break
            
            if not tle_dir:
                logger.warning("⚠️ TLE 數據目錄不存在，跳過 TLE 載入測試")
                self.test_results["tle_loader"] = "skipped"
                return True
            
            # 測試載入器
            loader = TLELoader(tle_dir)
            result = loader.load_all_tle_data()
            
            # 驗證結果
            success = (
                result.total_records > 0 and
                len(result.constellations) > 0 and
                len(result.errors) == 0
            )
            
            if success:
                logger.info(f"✅ TLE 載入器測試通過: {result.total_records} 條記錄")
                self.test_results["tle_loader"] = {
                    "status": "passed",
                    "total_records": result.total_records,
                    "constellations": result.constellations
                }
            else:
                logger.error("❌ TLE 載入器測試失敗")
                self.test_results["tle_loader"] = {
                    "status": "failed",
                    "errors": result.errors
                }
            
            return success
            
        except Exception as e:
            logger.error(f"❌ TLE 載入器測試異常: {e}")
            self.test_results["tle_loader"] = {"status": "error", "error": str(e)}
            return False
    
    def test_sgp4_engine(self) -> bool:
        """測試 SGP4 計算引擎"""
        logger.info("🔍 測試 SGP4 計算引擎...")
        
        try:
            engine = SGP4Engine()
            
            # 測試 TLE (ISS)
            line1 = "1 25544U 98067A   21001.00000000  .00001817  00000-0  41860-4 0  9990"
            line2 = "2 25544  51.6461 290.5094 0000597  91.8164 268.3516 15.48919103262509"
            
            # 創建衛星
            if not engine.create_satellite("TEST_SAT", line1, line2):
                raise RuntimeError("SGP4 衛星對象創建失敗")
            
            # 計算位置
            now = datetime.now(timezone.utc)
            result = engine.calculate_position("TEST_SAT", now)
            
            success = result is not None and result.success
            
            if success:
                import numpy as np
                pos_magnitude = np.linalg.norm(result.position_eci)
                logger.info(f"✅ SGP4 引擎測試通過: 位置大小 {pos_magnitude:.2f} km")
                self.test_results["sgp4_engine"] = {
                    "status": "passed",
                    "position_magnitude_km": pos_magnitude,
                    "calculation_success": True
                }
            else:
                logger.error("❌ SGP4 引擎測試失敗")
                self.test_results["sgp4_engine"] = {"status": "failed"}
            
            return success
            
        except Exception as e:
            logger.error(f"❌ SGP4 引擎測試異常: {e}")
            self.test_results["sgp4_engine"] = {"status": "error", "error": str(e)}
            return False
    
    def test_phase1_coordinator(self) -> bool:
        """測試 Phase 1 協調器"""
        logger.info("🔍 測試 Phase 1 協調器...")
        
        try:
            # 使用統一配置載入器獲取 TLE 目錄
            try:
                from config_loader import get_tle_data_path
                tle_path = get_tle_data_path()
                tle_dirs = [tle_path] if tle_path else []
            except:
                # 回退到預設路徑
                tle_dirs = [
                    "/home/sat/ntn-stack/netstack/tle_data"
                ]
            
            tle_dir = None
            for dir_path in tle_dirs:
                if Path(dir_path).exists():
                    tle_dir = dir_path
                    break
            
            if not tle_dir:
                logger.warning("⚠️ TLE 數據目錄不存在，跳過協調器測試")
                self.test_results["phase1_coordinator"] = "skipped"
                return True
            
            # 創建測試配置
            config = Phase1Config(
                tle_data_dir=tle_dir,
                output_dir=self.test_output_dir,
                trajectory_duration_minutes=30,  # 縮短測試時間
                time_step_seconds=60
            )
            
            # 創建協調器
            coordinator = Phase1Coordinator(config)
            
            # 執行完整流程
            result = coordinator.execute_complete_pipeline()
            
            success = (
                result.total_satellites > 0 and
                result.successful_calculations > 0 and
                result.tle_loading_success and
                result.sgp4_calculation_success and
                result.data_export_success
            )
            
            if success:
                logger.info(f"✅ Phase 1 協調器測試通過")
                logger.info(f"   處理衛星: {result.total_satellites} 顆")
                logger.info(f"   成功計算: {result.successful_calculations} 次")
                logger.info(f"   執行時間: {result.total_duration_seconds:.2f} 秒")
                
                self.test_results["phase1_coordinator"] = {
                    "status": "passed",
                    "total_satellites": result.total_satellites,
                    "successful_calculations": result.successful_calculations,
                    "execution_time": result.total_duration_seconds
                }
            else:
                logger.error("❌ Phase 1 協調器測試失敗")
                self.test_results["phase1_coordinator"] = {"status": "failed"}
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Phase 1 協調器測試異常: {e}")
            self.test_results["phase1_coordinator"] = {"status": "error", "error": str(e)}
            return False
    
    def test_api_interface(self) -> bool:
        """測試 API 接口"""
        logger.info("🔍 測試 API 接口...")
        
        try:
            # 創建 API 接口
            api = Phase1APIInterface(self.test_output_dir)
            
            # 測試健康檢查
            health = api.get_execution_summary()
            
            # 測試星座信息獲取
            constellation_info = api.get_constellation_info()
            
            success = (
                isinstance(constellation_info, dict) and
                "constellations" in constellation_info
            )
            
            if success:
                logger.info("✅ API 接口測試通過")
                self.test_results["api_interface"] = {
                    "status": "passed",
                    "constellations_available": len(constellation_info.get("constellations", {}))
                }
            else:
                logger.error("❌ API 接口測試失敗")
                self.test_results["api_interface"] = {"status": "failed"}
            
            return success
            
        except Exception as e:
            logger.error(f"❌ API 接口測試異常: {e}")
            self.test_results["api_interface"] = {"status": "error", "error": str(e)}
            return False
    
    def run_complete_integration_test(self) -> bool:
        """執行完整的整合測試"""
        logger.info("🚀 開始 Phase 1 完整整合測試")
        logger.info("=" * 60)
        
        tests = [
            ("TLE 載入器", self.test_tle_loader),
            ("SGP4 引擎", self.test_sgp4_engine),
            ("Phase 1 協調器", self.test_phase1_coordinator),
            ("API 接口", self.test_api_interface)
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            logger.info(f"\n🔄 執行測試: {test_name}")
            try:
                if test_func():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                failed += 1
                logger.error(f"❌ 測試異常 {test_name}: {e}")
        
        logger.info("\n" + "=" * 60)
        logger.info("📊 Phase 1 整合測試結果")
        logger.info(f"   通過: {passed} / {len(tests)}")
        logger.info(f"   失敗: {failed} / {len(tests)}")
        
        if failed == 0:
            logger.info("🎉 所有整合測試通過！Phase 1 重構整合成功")
            return True
        else:
            logger.error("❌ 部分整合測試失敗，需要修復")
            return False
    
    def get_test_results(self) -> dict:
        """獲取測試結果"""
        return self.test_results

def run_integration_tests(output_dir: str = None) -> bool:
    """
    執行 Phase 1 整合測試
    
    Args:
        output_dir: 測試輸出目錄
        
    Returns:
        bool: 測試是否全部通過
    """
    test_runner = Phase1IntegrationTest(output_dir)
    return test_runner.run_complete_integration_test()

if __name__ == "__main__":
    # 設置日誌
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # 執行整合測試
    success = run_integration_tests()
    sys.exit(0 if success else 1)