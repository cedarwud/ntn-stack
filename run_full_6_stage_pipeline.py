#!/usr/bin/env python3
"""
完整六階段衛星數據處理流程
運行所有階段並獲得真實的衛星池大小
"""

import asyncio
import logging
import sys
import time
from pathlib import Path

# 添加模組路徑
sys.path.insert(0, str(Path(__file__).parent / "netstack" / "src"))

# 導入處理器
from stages.stage1_tle_processor import Stage1TLEProcessor
from stages.stage2_filter_processor import Stage2FilterProcessor  
from stages.stage3_signal_processor import Stage3SignalProcessor
from stages.stage5_integration_processor import Stage5IntegrationProcessor, Stage5Config

async def run_full_6_stage_pipeline():
    """運行完整的六階段處理流程"""
    
    # 設定日誌
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    total_start_time = time.time()
    
    logger.info("🚀 開始完整六階段衛星數據處理流程")
    logger.info("=" * 60)
    
    try:
        # ============== 階段一：TLE載入與SGP4計算 ==============
        logger.info("📡 階段一：TLE載入與SGP4計算")
        stage1_start = time.time()
        
        stage1_processor = Stage1TLEProcessor(
            tle_data_dir="/home/sat/ntn-stack/netstack/tle_data",
            output_dir="/tmp/satellite_data",
            sample_mode=False,  # 全量處理模式
            sample_size=50
        )
        
        stage1_results = stage1_processor.process_stage1()
        logger.info(f"✅ 階段一完成，耗時: {time.time() - stage1_start:.1f}秒")
        logger.info(f"   處理衛星數: {stage1_results.get('total_satellites', 0)}顆")
        
        # ============== 階段二：智能篩選 ==============  
        logger.info("🎯 階段二：智能篩選")
        stage2_start = time.time()
        
        stage2_processor = Stage2FilterProcessor(
            observer_lat=24.9441667,
            observer_lon=121.3713889,
            input_dir="/tmp/satellite_data",
            output_dir="/tmp/satellite_data"
        )
        
        # 傳遞階段一的記憶體數據
        stage2_results = stage2_processor.process_stage2(
            stage1_data=stage1_results
        )
        logger.info(f"✅ 階段二完成，耗時: {time.time() - stage2_start:.1f}秒")
        logger.info(f"   篩選後衛星數: {stage2_results.get('filtered_satellites_count', 0)}顆")
        
        # ============== 階段三：信號分析 ==============
        logger.info("📊 階段三：信號分析")
        stage3_start = time.time()
        
        stage3_processor = Stage3SignalProcessor(
            observer_lat=24.9441667,
            observer_lon=121.3713889,
            input_dir="/tmp/satellite_data",
            output_dir="/tmp/satellite_data"
        )
        
        # 傳遞階段二的記憶體數據
        stage3_results = stage3_processor.process_stage3(
            stage2_data=stage2_results
        )
        logger.info(f"✅ 階段三完成，耗時: {time.time() - stage3_start:.1f}秒")
        logger.info(f"   信號分析衛星數: {stage3_results.get('analyzed_satellites_count', 0)}顆")
        
        # ============== 階段四：時間序列預處理 ==============
        # 註：階段四通常整合在階段三中
        logger.info("📈 階段四：時間序列預處理（整合在階段三）")
        
        # ============== 階段五+六：數據整合與動態池規劃 ==============
        logger.info("🔧 階段五+六：數據整合與動態池規劃")
        stage5_start = time.time()
        
        # 設定階段五配置
        stage5_config = Stage5Config()
        stage5_config.input_enhanced_timeseries_dir = "/tmp/satellite_data/enhanced_timeseries"
        stage5_config.output_layered_dir = "/tmp/satellite_data/layered_phase0_enhanced"
        stage5_config.output_handover_scenarios_dir = "/tmp/satellite_data/handover_scenarios"
        stage5_config.output_signal_analysis_dir = "/tmp/satellite_data/signal_quality_analysis"
        stage5_config.output_processing_cache_dir = "/tmp/satellite_data/processing_cache"
        stage5_config.output_status_files_dir = "/tmp/satellite_data/status_files"
        
        stage5_processor = Stage5IntegrationProcessor(stage5_config)
        
        stage5_results = await stage5_processor.process_enhanced_timeseries()
        logger.info(f"✅ 階段五+六完成，耗時: {time.time() - stage5_start:.1f}秒")
        
        # ============== 結果分析 ==============
        logger.info("=" * 60)
        logger.info("🎯 六階段處理完成！結果分析：")
        
        total_time = time.time() - total_start_time
        logger.info(f"📊 總處理時間: {total_time:.1f} 秒")
        
        # 動態池結果分析
        dynamic_pools = stage5_results.get("dynamic_satellite_pools", {})
        if dynamic_pools and not isinstance(dynamic_pools, str):  # 確保不是錯誤訊息
            starlink_pool = dynamic_pools.get("starlink", {})
            oneweb_pool = dynamic_pools.get("oneweb", {})
            
            logger.info("🛰️ 動態衛星池結果：")
            logger.info(f"   Starlink: 估算 {starlink_pool.get('estimated_pool_size', '?')}顆 → 實際 {starlink_pool.get('actual_pool_size', '?')}顆")
            logger.info(f"   OneWeb:   估算 {oneweb_pool.get('estimated_pool_size', '?')}顆 → 實際 {oneweb_pool.get('actual_pool_size', '?')}顆")
            
            # 覆蓋統計
            if 'coverage_statistics' in starlink_pool:
                starlink_stats = starlink_pool['coverage_statistics']
                logger.info(f"   Starlink覆蓋率: {starlink_stats.get('target_met_ratio', 0)*100:.1f}%")
                logger.info(f"   平均可見衛星: {starlink_stats.get('avg_visible_satellites', 0):.1f}顆")
            
            if 'coverage_statistics' in oneweb_pool:
                oneweb_stats = oneweb_pool['coverage_statistics'] 
                logger.info(f"   OneWeb覆蓋率: {oneweb_stats.get('target_met_ratio', 0)*100:.1f}%")
                logger.info(f"   平均可見衛星: {oneweb_stats.get('avg_visible_satellites', 0):.1f}顆")
        
        else:
            logger.warning("⚠️ 動態池規劃結果異常")
            if isinstance(dynamic_pools, str):
                logger.error(f"   錯誤: {dynamic_pools}")
        
        # 處理階段統計
        logger.info("📈 各階段處理統計：")
        logger.info(f"   階段一: {stage1_results.get('total_satellites', 0)}顆衛星")
        logger.info(f"   階段二: {stage2_results.get('filtered_satellites_count', 0)}顆衛星")
        logger.info(f"   階段三: {stage3_results.get('analyzed_satellites_count', 0)}顆衛星")
        
        logger.info("=" * 60)
        logger.info("🎉 完整六階段處理流程執行完成！")
        
        return {
            "success": True,
            "total_time": total_time,
            "stage1": stage1_results,
            "stage2": stage2_results, 
            "stage3": stage3_results,
            "stage5": stage5_results,
            "dynamic_pools": dynamic_pools
        }
        
    except Exception as e:
        logger.error(f"❌ 六階段處理失敗: {e}")
        import traceback
        logger.error(f"詳細錯誤: {traceback.format_exc()}")
        return {
            "success": False,
            "error": str(e),
            "total_time": time.time() - total_start_time
        }

async def main():
    """主程式入口"""
    results = await run_full_6_stage_pipeline()
    
    if results["success"]:
        print(f"\n🎯 處理成功! 總耗時: {results['total_time']:.1f} 秒")
        
        # 顯示最終衛星池大小
        dynamic_pools = results.get("dynamic_pools", {})
        if dynamic_pools and isinstance(dynamic_pools, dict):
            starlink = dynamic_pools.get("starlink", {})
            oneweb = dynamic_pools.get("oneweb", {})
            
            print(f"🛰️ 最終衛星池:")
            print(f"   Starlink: {starlink.get('actual_pool_size', '?')} 顆")
            print(f"   OneWeb: {oneweb.get('actual_pool_size', '?')} 顆")
        
        return 0
    else:
        print(f"\n❌ 處理失敗: {results.get('error', '未知錯誤')}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)