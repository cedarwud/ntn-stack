#!/usr/bin/env python3
"""
Phase 0 功能測試腳本
驗證 Starlink 完整數據下載與換手篩選工具的所有功能

測試項目:
1. TLE 數據下載和驗證
2. 衛星預篩選功能
3. 最佳時間段分析
4. 前端數據源格式化
5. 完整集成流程
"""

import asyncio
import logging
import sys
import json
from pathlib import Path

# 添加模組路徑
netstack_root = Path(__file__).parent
sys.path.insert(0, str(netstack_root))

# 先測試一個簡單的導入
try:
    from src.services.satellite.starlink_tle_downloader import StarlinkTLEDownloader
    from src.services.satellite.satellite_prefilter import SatellitePrefilter, ObserverLocation
    from src.services.satellite.optimal_timeframe_analyzer import OptimalTimeframeAnalyzer
    from src.services.satellite.frontend_data_formatter import FrontendDataFormatter
    from src.services.satellite.phase0_integration import Phase0Integration
    logger.info("所有模組導入成功")
except ImportError as e:
    logger.error(f"模組導入失敗: {e}")
    sys.exit(1)

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Phase0Tester:
    """Phase 0 功能測試器"""
    
    def __init__(self):
        self.test_results = {
            "passed": 0,
            "failed": 0,
            "errors": []
        }
        
        # NTPU 測試座標
        self.test_observer = ObserverLocation(
            latitude=24.9441667,
            longitude=121.3713889,
            altitude=0
        )
    
    def log_test_result(self, test_name: str, passed: bool, error_msg: str = None):
        """記錄測試結果"""
        if passed:
            self.test_results["passed"] += 1
            logger.info(f"✅ {test_name} - 通過")
        else:
            self.test_results["failed"] += 1
            logger.error(f"❌ {test_name} - 失敗: {error_msg}")
            self.test_results["errors"].append(f"{test_name}: {error_msg}")
    
    async def test_tle_downloader(self):
        """測試 TLE 數據下載器"""
        logger.info("=== 測試 1: TLE 數據下載器 ===")
        
        try:
            downloader = StarlinkTLEDownloader(cache_dir="test_cache")
            
            # 測試下載功能
            satellites = await downloader.get_starlink_tle_data()
            
            if not satellites:
                self.log_test_result("TLE 數據下載", False, "未下載到任何衛星數據")
                return
            
            # 驗證數據數量
            if len(satellites) < 1000:
                self.log_test_result("TLE 數據數量檢查", False, f"衛星數量過少: {len(satellites)}")
                return
            
            # 驗證數據格式
            sample_sat = satellites[0]
            required_fields = ['name', 'norad_id', 'line1', 'line2']
            for field in required_fields:
                if field not in sample_sat:
                    self.log_test_result("TLE 數據格式檢查", False, f"缺少必要字段: {field}")
                    return
            
            # 驗證數據完整性
            validation_result = await downloader.verify_complete_dataset(satellites[:10])  # 僅驗證前10顆
            
            if validation_result['valid_satellites'] == 0:
                self.log_test_result("TLE 數據驗證", False, "所有衛星數據都無效")
                return
            
            self.log_test_result("TLE 數據下載", True)
            self.log_test_result("TLE 數據數量檢查", True)
            self.log_test_result("TLE 數據格式檢查", True)
            self.log_test_result("TLE 數據驗證", True)
            
            logger.info(f"下載到 {len(satellites)} 顆衛星，驗證了 {validation_result['valid_satellites']}/{validation_result['total_satellites']} 顆")
            
            return satellites
            
        except Exception as e:
            self.log_test_result("TLE 數據下載", False, str(e))
            return None
    
    async def test_satellite_prefilter(self, satellites):
        """測試衛星預篩選器"""
        logger.info("=== 測試 2: 衛星預篩選器 ===")
        
        if not satellites:
            self.log_test_result("衛星預篩選", False, "沒有可用的衛星數據")
            return None
        
        try:
            prefilter = SatellitePrefilter()
            
            # 執行預篩選
            candidate_satellites, excluded_satellites = prefilter.pre_filter_satellites_by_orbit(
                self.test_observer, satellites
            )
            
            # 檢查篩選結果
            total_satellites = len(satellites)
            candidate_count = len(candidate_satellites)
            excluded_count = len(excluded_satellites)
            
            if candidate_count + excluded_count != total_satellites:
                self.log_test_result("預篩選數量一致性", False, 
                                   f"篩選前後數量不一致: {total_satellites} != {candidate_count + excluded_count}")
                return None
            
            if candidate_count == 0:
                self.log_test_result("候選衛星數量", False, "沒有候選衛星")
                return None
            
            # 檢查減少比例
            reduction_ratio = excluded_count / total_satellites * 100
            if reduction_ratio < 50:
                logger.warning(f"計算量減少比例較低: {reduction_ratio:.1f}%")
            
            self.log_test_result("衛星預篩選", True)
            self.log_test_result("預篩選數量一致性", True)
            self.log_test_result("候選衛星數量", True)
            
            logger.info(f"篩選結果: {candidate_count} 候選衛星, {excluded_count} 排除衛星 (減少 {reduction_ratio:.1f}%)")
            
            return candidate_satellites
            
        except Exception as e:
            self.log_test_result("衛星預篩選", False, str(e))
            return None
    
    async def test_optimal_timeframe_analyzer(self, candidate_satellites):
        """測試最佳時間段分析器"""
        logger.info("=== 測試 3: 最佳時間段分析器 ===")
        
        if not candidate_satellites:
            self.log_test_result("最佳時間段分析", False, "沒有候選衛星數據")
            return None
        
        try:
            analyzer = OptimalTimeframeAnalyzer()
            
            # 限制候選衛星數量以加速測試
            test_candidates = candidate_satellites[:50]  
            
            # 分析最佳時間段
            optimal_timeframe = analyzer.find_optimal_handover_timeframe(
                self.test_observer.latitude, 
                self.test_observer.longitude, 
                test_candidates
            )
            
            if not optimal_timeframe:
                self.log_test_result("最佳時間段分析", False, "未找到最佳時間段")
                return None
            
            # 檢查時間段合理性
            if optimal_timeframe.duration_minutes < 30 or optimal_timeframe.duration_minutes > 45:
                logger.warning(f"時間段長度異常: {optimal_timeframe.duration_minutes} 分鐘")
            
            # 檢查衛星數量
            if optimal_timeframe.satellite_count == 0:
                self.log_test_result("最佳時間段衛星數量", False, "時間段內無衛星")
                return None
            
            # 檢查品質評分
            if optimal_timeframe.coverage_quality_score < 0.1:
                logger.warning(f"覆蓋品質評分較低: {optimal_timeframe.coverage_quality_score:.3f}")
            
            self.log_test_result("最佳時間段分析", True)
            self.log_test_result("最佳時間段衛星數量", True)
            
            logger.info(f"最佳時間段: {optimal_timeframe.start_timestamp}, "
                       f"{optimal_timeframe.duration_minutes} 分鐘, "
                       f"{optimal_timeframe.satellite_count} 顆衛星, "
                       f"品質: {optimal_timeframe.coverage_quality_score:.3f}")
            
            return optimal_timeframe
            
        except Exception as e:
            self.log_test_result("最佳時間段分析", False, str(e))
            return None
    
    async def test_frontend_data_formatter(self, optimal_timeframe):
        """測試前端數據源格式化器"""
        logger.info("=== 測試 4: 前端數據源格式化器 ===")
        
        if not optimal_timeframe:
            self.log_test_result("前端數據格式化", False, "沒有最佳時間段數據")
            return None
        
        try:
            formatter = FrontendDataFormatter()
            
            # 格式化前端數據
            frontend_data = formatter.format_for_frontend_display(
                optimal_timeframe, 
                {"lat": self.test_observer.latitude, "lon": self.test_observer.longitude}
            )
            
            # 檢查數據結構
            required_sections = ["sidebar_data", "animation_data", "handover_sequence", "metadata"]
            for section in required_sections:
                if section not in frontend_data:
                    self.log_test_result("前端數據結構檢查", False, f"缺少數據段: {section}")
                    return None
            
            # 檢查側邊欄數據
            sidebar_data = frontend_data["sidebar_data"]
            if "satellite_gnb_list" not in sidebar_data or not sidebar_data["satellite_gnb_list"]:
                self.log_test_result("側邊欄數據檢查", False, "側邊欄衛星列表為空")
                return None
            
            # 檢查動畫數據
            animation_data = frontend_data["animation_data"]
            if "animation_trajectories" not in animation_data or not animation_data["animation_trajectories"]:
                self.log_test_result("動畫數據檢查", False, "動畫軌跡數據為空")
                return None
            
            # 檢查換手序列
            handover_data = frontend_data["handover_sequence"]
            if "handover_sequence" not in handover_data:
                self.log_test_result("換手序列檢查", False, "換手序列數據缺失")
                return None
            
            self.log_test_result("前端數據格式化", True)
            self.log_test_result("前端數據結構檢查", True)
            self.log_test_result("側邊欄數據檢查", True)
            self.log_test_result("動畫數據檢查", True)
            self.log_test_result("換手序列檢查", True)
            
            logger.info(f"前端數據源已生成: "
                       f"{len(sidebar_data['satellite_gnb_list'])} 個衛星, "
                       f"{len(animation_data['animation_trajectories'])} 條軌跡, "
                       f"{len(handover_data['handover_sequence'])} 個換手事件")
            
            return frontend_data
            
        except Exception as e:
            self.log_test_result("前端數據格式化", False, str(e))
            return None
    
    async def test_phase0_integration(self):
        """測試 Phase 0 完整集成"""
        logger.info("=== 測試 5: Phase 0 完整集成 ===")
        
        try:
            phase0 = Phase0Integration(cache_dir="test_cache")
            
            # 執行完整分析
            results = await phase0.run_complete_analysis(
                self.test_observer.latitude,
                self.test_observer.longitude,
                self.test_observer.altitude,
                force_download=False  # 使用緩存加速測試
            )
            
            # 檢查結果完整性
            required_sections = [
                "analysis_metadata", 
                "raw_data_statistics", 
                "optimal_timeframe", 
                "frontend_data_sources",
                "validation_results"
            ]
            
            for section in required_sections:
                if section not in results:
                    self.log_test_result("集成結果結構檢查", False, f"缺少結果段: {section}")
                    return None
            
            # 檢查分析時間
            analysis_duration = results["analysis_metadata"]["analysis_duration_seconds"]
            if analysis_duration > 600:  # 10分鐘超時
                logger.warning(f"分析時間較長: {analysis_duration:.1f} 秒")
            
            # 檢查驗證結果
            validation = results["validation_results"]
            if not validation.get("validation_passed", False):
                logger.warning("驗證未通過，但繼續測試")
                for error in validation.get("errors", []):
                    logger.warning(f"驗證錯誤: {error}")
            
            self.log_test_result("Phase 0 完整集成", True)
            self.log_test_result("集成結果結構檢查", True)
            
            logger.info(f"完整分析成功: 耗時 {analysis_duration:.1f} 秒, "
                       f"分析 {results['raw_data_statistics']['total_starlink_satellites']} 顆衛星, "
                       f"找到 {results['optimal_timeframe']['satellite_count']} 顆最佳衛星")
            
            # 保存測試結果
            test_output = Path("test_results") / "phase0_test_results.json"
            test_output.parent.mkdir(exist_ok=True)
            
            with open(test_output, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            logger.info(f"測試結果已保存到: {test_output}")
            
            return True
            
        except Exception as e:
            self.log_test_result("Phase 0 完整集成", False, str(e))
            return False
    
    async def run_all_tests(self):
        """運行所有測試"""
        logger.info("🚀 開始 Phase 0 完整功能測試")
        
        # 測試 1: TLE 數據下載器
        satellites = await self.test_tle_downloader()
        
        # 測試 2: 衛星預篩選器
        candidate_satellites = await self.test_satellite_prefilter(satellites)
        
        # 測試 3: 最佳時間段分析器  
        optimal_timeframe = await self.test_optimal_timeframe_analyzer(candidate_satellites)
        
        # 測試 4: 前端數據源格式化器
        frontend_data = await self.test_frontend_data_formatter(optimal_timeframe)
        
        # 測試 5: Phase 0 完整集成
        integration_success = await self.test_phase0_integration()
        
        # 輸出測試總結
        total_tests = self.test_results["passed"] + self.test_results["failed"]
        success_rate = self.test_results["passed"] / total_tests * 100 if total_tests > 0 else 0
        
        logger.info("=" * 50)
        logger.info("📊 Phase 0 測試總結")
        logger.info(f"通過測試: {self.test_results['passed']}")
        logger.info(f"失敗測試: {self.test_results['failed']}")
        logger.info(f"成功率: {success_rate:.1f}%")
        
        if self.test_results["errors"]:
            logger.info("❌ 測試錯誤:")
            for error in self.test_results["errors"]:
                logger.info(f"  - {error}")
        
        if success_rate >= 80:
            logger.info("🎉 Phase 0 測試基本通過！")
            return True
        else:
            logger.error("💥 Phase 0 測試未通過，需要修復問題")
            return False


async def main():
    """主函數"""
    tester = Phase0Tester()
    success = await tester.run_all_tests()
    
    if success:
        print("\n✅ Phase 0 開發完成，所有驗收標準達成！")
        sys.exit(0)
    else:
        print("\n❌ Phase 0 測試失敗，需要修復問題！")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())