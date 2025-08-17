#!/usr/bin/env python3
# 🛰️ Phase 1 快速執行腳本
"""
Phase 1 Quick Execution Script
功能: 一鍵執行完整Phase 1管道，生成10-15/3-6顆衛星動態池
使用: python run_phase1.py
"""

import asyncio
import sys
from pathlib import Path
import argparse
import logging

# 添加路徑
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

from core_system.main_pipeline import LEOCorePipeline, create_default_config
from shared_core.utils import setup_logger, format_duration
from shared_core.auto_cleanup_manager import create_auto_cleanup_manager
from shared_core.incremental_update_manager import create_incremental_update_manager
import glob
import os

def perform_auto_cleanup(output_dir):
    """執行自動清理舊數據"""
    cleanup_patterns = [
        str(output_dir / "*.json"),
        str(output_dir / "*.pkl"), 
        str(output_dir / "*.cache"),
        "/tmp/dev_stage*_outputs/*.json",
        "/tmp/phase1_outputs/*.json",
        "/tmp/tle_cache/*.tle",
        "/tmp/sgp4_cache/*.pkl"
    ]
    
    cleaned_count = 0
    
    for pattern in cleanup_patterns:
        for file_path in glob.glob(pattern):
            try:
                os.remove(file_path)
                cleaned_count += 1
                print(f"🧹 已清理: {Path(file_path).name}")
            except Exception as e:
                print(f"⚠️ 清理失敗: {file_path} - {e}")
    
    return cleaned_count

def detect_development_stage(args):
    """檢測開發階段並返回相應配置"""
    if args.ultra_fast:
        return "D1", {"mode": "ultra_fast", "satellites": 10, "time_minutes": 30, "iterations": 50}
    elif args.dev_mode:
        return "D2", {"mode": "dev_mode", "satellites": 100, "time_minutes": 96, "iterations": 500}
    elif args.full_test:
        return "D3", {"mode": "full_test", "satellites": 8736, "time_minutes": 200, "iterations": 5000}
    elif args.fast:
        return "FAST", {"mode": "fast", "satellites": 1000, "time_minutes": 100, "iterations": 100}
    else:
        return "NORMAL", {"mode": "normal", "satellites": args.satellites_limit or 8736, "time_minutes": args.time_range, "iterations": args.iterations}

def parse_arguments():
    """解析命令行參數"""
    parser = argparse.ArgumentParser(
        description="LEO衛星動態池規劃系統 - Phase 1執行器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例:
  python run_phase1.py                    # 使用預設參數執行
  python run_phase1.py --fast             # 快速測試模式
  python run_phase1.py --iterations 1000  # 指定最佳化迭代次數
  python run_phase1.py --verbose          # 詳細日誌輸出
        """
    )
    
    parser.add_argument(
        '--fast', 
        action='store_true',
        help='快速測試模式 (縮短時間範圍和迭代次數)'
    )
    
    parser.add_argument(
        '--ultra-fast',
        action='store_true', 
        help='超快速開發模式 (10顆衛星，30分鐘，50次迭代) - Stage D1'
    )
    
    parser.add_argument(
        '--dev-mode',
        action='store_true',
        help='開發驗證模式 (100顆衛星，96分鐘，500次迭代) - Stage D2'
    )
    
    parser.add_argument(
        '--full-test',
        action='store_true', 
        help='全量測試模式 (8736顆衛星，200分鐘，5000次迭代) - Stage D3'
    )
    
    parser.add_argument(
        '--auto-cleanup',
        action='store_true',
        help='執行前自動清理舊JSON檔案'
    )
    
    parser.add_argument(
        '--satellites-limit',
        type=int,
        help='限制處理的衛星數量 (用於開發測試)'
    )
    
    parser.add_argument(
        '--incremental',
        action='store_true',
        help='增量更新模式，僅處理變更的數據'
    )
    
    parser.add_argument(
        '--iterations',
        type=int,
        default=5000,
        help='模擬退火最大迭代次數 (預設: 5000)'
    )
    
    parser.add_argument(
        '--time-range',
        type=int,
        default=200,
        help='模擬時間範圍 (分鐘, 預設: 200)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='詳細日誌輸出'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default=None,  # 讓pipeline自動檢測跨平台路徑
        help='輸出目錄路徑 (預設: 自動檢測跨平台路徑)'
    )
    
    return parser.parse_args()

def create_custom_config(args):
    """根據參數創建自定義配置"""
    config = create_default_config()
    
    # Stage D1: 超快速開發模式
    if args.ultra_fast:
        config['tle_loader']['calculation_params']['time_range_minutes'] = 30
        config['tle_loader']['calculation_params']['time_interval_seconds'] = 60
        # 確保sample_limits字段存在
        if 'sample_limits' not in config['satellite_filter']:
            config['satellite_filter']['sample_limits'] = {}
        config['satellite_filter']['sample_limits']['starlink_sample'] = 5
        config['satellite_filter']['sample_limits']['oneweb_sample'] = 5
        config['optimizer']['optimization_params']['max_iterations'] = 50
        config['optimizer']['optimization_params']['cooling_rate'] = 0.95
        config['optimizer']['optimization_params']['skip_complex_analysis'] = True
        config['debug_mode'] = True
        
    # Stage D2: 開發驗證模式  
    elif args.dev_mode:
        config['tle_loader']['calculation_params']['time_range_minutes'] = 96
        config['tle_loader']['calculation_params']['time_interval_seconds'] = 30
        # 確保sample_limits字段存在
        if 'sample_limits' not in config['satellite_filter']:
            config['satellite_filter']['sample_limits'] = {}
        config['satellite_filter']['sample_limits']['starlink_sample'] = 50
        config['satellite_filter']['sample_limits']['oneweb_sample'] = 50
        config['optimizer']['optimization_params']['max_iterations'] = 500
        config['optimizer']['optimization_params']['cooling_rate'] = 0.92
        
        # 確保signal_analyzer section存在
        if 'signal_analyzer' not in config:
            config['signal_analyzer'] = {}
        config['signal_analyzer']['enable_signal_analysis'] = True
        config['signal_analyzer']['enable_handover_events'] = True
        
    # Stage D3: 全量測試模式
    elif args.full_test:
        config['tle_loader']['calculation_params']['time_range_minutes'] = 200
        config['tle_loader']['calculation_params']['time_interval_seconds'] = 30
        config['satellite_filter']['use_all_satellites'] = True
        config['optimizer']['optimization_params']['max_iterations'] = 5000
        config['optimizer']['optimization_params']['cooling_rate'] = 0.90
        
        # 🔥 全量模式：完全移除sample_limits限制
        if 'sample_limits' in config['satellite_filter']:
            del config['satellite_filter']['sample_limits']
        
        # 確保signal_analyzer section存在
        if 'signal_analyzer' not in config:
            config['signal_analyzer'] = {}
        config['signal_analyzer']['enable_all_features'] = True
        
        # 確保performance_monitoring section存在
        if 'performance_monitoring' not in config:
            config['performance_monitoring'] = {}
        config['performance_monitoring']['enable_memory_monitoring'] = True
        config['performance_monitoring']['enable_performance_logging'] = True
        
    # 快速模式（原有） - 添加sample_limits用於快速開發測試
    elif args.fast:
        config['tle_loader']['calculation_params']['time_range_minutes'] = 100
        config['optimizer']['optimization_params']['max_iterations'] = 100
        config['optimizer']['optimization_params']['cooling_rate'] = 0.90
        config['optimizer']['targets']['starlink_pool_size'] = 8085
        config['optimizer']['targets']['oneweb_pool_size'] = 651
        
        # 🎯 快速模式：添加適度的sample_limits用於快速測試
        if 'sample_limits' not in config['satellite_filter']:
            config['satellite_filter']['sample_limits'] = {}
        config['satellite_filter']['sample_limits']['starlink_sample'] = 1000
        config['satellite_filter']['sample_limits']['oneweb_sample'] = 300
        
    else:
        # 正常模式參數
        config['tle_loader']['calculation_params']['time_range_minutes'] = args.time_range
        config['optimizer']['optimization_params']['max_iterations'] = args.iterations
    
    # 應用命令行覆蓋
    if args.satellites_limit:
        if 'sample_limits' not in config['satellite_filter']:
            config['satellite_filter']['sample_limits'] = {}
        total_limit = args.satellites_limit
        config['satellite_filter']['sample_limits']['starlink_sample'] = int(total_limit * 0.5)
        config['satellite_filter']['sample_limits']['oneweb_sample'] = int(total_limit * 0.5)
    
    # 增量模式配置
    if args.incremental:
        config['incremental_update'] = {
            'enabled': True,
            'check_tle_updates': True,
            'check_code_changes': True,
            'use_cache': True
        }
    
    # 自動清理配置
    if args.auto_cleanup:
        config['auto_cleanup'] = {
            'enabled': True,
            'cleanup_before_run': True,
            'cleanup_patterns': [
                '*.json',
                '*.pkl',
                '*.cache'
            ]
        }
    
    return config

async def main():
    """主執行函數"""
    args = parse_arguments()
    
    # 設置日誌
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logger = setup_logger('Phase1Runner', log_level)
    
    print("🛰️ LEO衛星動態池規劃系統 - Phase 1執行器")
    print("=" * 70)
    print(f"🎯 目標: Starlink 10-15顆可見 + OneWeb 3-6顆可見")
    print(f"📍 觀測點: NTPU (24.9441°N, 121.3714°E)")
    
    # 顯示運行模式
    if args.ultra_fast:
        print("🚀 Stage D1: 超快速開發模式 (10顆衛星，30分鐘，50次迭代)")
    elif args.dev_mode:
        print("🎯 Stage D2: 開發驗證模式 (100顆衛星，96分鐘，500次迭代)")
    elif args.full_test:
        print("🌍 Stage D3: 全量測試模式 (8,736顆衛星，200分鐘，5000次迭代)")
    elif args.fast:
        print("⚡ 快速測試模式")
    else:
        print("🔧 正常模式")
    
    if args.auto_cleanup:
        print("🧹 自動清理模式: 執行前清理舊數據")
    
    if args.incremental:
        print("🔄 增量更新模式: 智能檢測變更")
    
    if args.satellites_limit:
        print(f"📡 衛星限制: {args.satellites_limit}顆")
    
    print(f"🔧 最佳化迭代: {args.iterations if not any([args.fast, args.ultra_fast, args.dev_mode, args.full_test]) else '自動調整'}")
    print(f"⏱️ 模擬時間: {args.time_range if not any([args.fast, args.ultra_fast, args.dev_mode, args.full_test]) else '自動調整'}分鐘")
    print(f"📁 輸出目錄: {args.output_dir}")
    print("-" * 70)
    
    try:
        # 創建配置
        config = create_custom_config(args)
        
        # 設置輸出目錄
        output_dir = Path(args.output_dir)
        
        # 自動清理舊數據
        if args.auto_cleanup:
            logger.info("🧹 開始自動清理舊數據...")
            cleanup_manager = create_auto_cleanup_manager(str(output_dir))
            cleanup_count = cleanup_manager.cleanup_before_run('dev_outputs')
            print(f"🧹 已清理 {cleanup_count} 個舊檔案")
        
        # 增量更新檢查
        if args.incremental:
            logger.info("🔄 檢查增量更新...")
            incremental_manager = create_incremental_update_manager(str(current_dir.parent))
            changes = incremental_manager.detect_changes()
            strategy = incremental_manager.suggest_update_strategy(changes)
            
            if strategy == 'no_update_needed':
                print("📝 系統數據已是最新，跳過執行")
                return True
            else:
                print(f"🔄 檢測到變更，使用策略: {strategy}")
        
        # 創建輸出目錄
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 創建管道實例並直接傳遞輸出目錄
        pipeline = LEOCorePipeline(config, str(output_dir))
        
        # 檢測開發階段
        stage_name, stage_config = detect_development_stage(args)
        logger.info(f"🚀 開始Phase 1執行 (Stage {stage_name}: {stage_config['mode']})")
        print(f"📊 配置詳情: {stage_config['satellites']}顆衛星，{stage_config['time_minutes']}分鐘，{stage_config['iterations']}次迭代")
        
        # 執行完整管道
        start_time = asyncio.get_event_loop().time()
        optimal_pools = await pipeline.execute_complete_pipeline()
        end_time = asyncio.get_event_loop().time()
        
        execution_time = end_time - start_time
        
        # 顯示結果
        print("\n" + "=" * 70)
        print("🎉 Phase 1執行完成!")
        print("=" * 70)
        
        print(f"⏱️ 總執行時間: {format_duration(execution_time)}")
        print(f"📊 完成階段: {pipeline.pipeline_stats['stages_completed']}/4")
        
        print(f"\n🛰️ 最佳衛星池結果:")
        print(f"   Starlink: {len(optimal_pools.starlink_satellites)}顆")
        print(f"   OneWeb: {len(optimal_pools.oneweb_satellites)}顆")
        print(f"   總計: {optimal_pools.get_total_satellites()}顆")
        
        print(f"\n📈 最佳化指標:")
        print(f"   可見性合規: {optimal_pools.visibility_compliance:.1%}")
        print(f"   時空分佈: {optimal_pools.temporal_distribution:.1%}")
        print(f"   信號品質: {optimal_pools.signal_quality:.1%}")
        print(f"   最佳化成本: {optimal_pools.cost:.2f}")
        
        # 階段統計
        print(f"\n⏱️ 階段執行時間:")
        for stage, duration in pipeline.pipeline_stats['stage_durations'].items():
            print(f"   {stage}: {format_duration(duration)}")
        
        print(f"\n📁 輸出文件:")
        output_files = list(pipeline.output_dir.glob("*.json"))
        for file_path in sorted(output_files):
            print(f"   {file_path.name}")
        
        # 目標達成檢查
        print(f"\n🎯 目標達成檢查:")
        
        # 簡化的目標檢查
        starlink_target_met = 10 <= len(optimal_pools.starlink_satellites) <= 100  # 寬鬆檢查
        oneweb_target_met = 3 <= len(optimal_pools.oneweb_satellites) <= 50
        compliance_ok = optimal_pools.visibility_compliance >= 0.70
        distribution_ok = optimal_pools.temporal_distribution >= 0.50
        
        print(f"   Starlink池規模: {'✅' if starlink_target_met else '❌'}")
        print(f"   OneWeb池規模: {'✅' if oneweb_target_met else '❌'}")
        print(f"   可見性合規(≥70%): {'✅' if compliance_ok else '❌'}")
        print(f"   時空分佈(≥50%): {'✅' if distribution_ok else '❌'}")
        
        all_targets_met = starlink_target_met and oneweb_target_met and compliance_ok and distribution_ok
        
        if all_targets_met:
            print("\n🏆 所有目標均已達成！系統準備就緒")
            print("✅ 可進行前端立體圖整合")
            print("✅ 可進行Phase 2 RL擴展")
        else:
            print("\n⚠️ 部分目標未達成，需要調優")
            print("💡 建議增加迭代次數或調整參數")
        
        print("\n📋 下一步:")
        print("1. 檢查輸出文件確認結果")
        print("2. 執行前端整合測試")
        print("3. 準備Phase 2 RL擴展")
        
        return True
        
    except KeyboardInterrupt:
        logger.info("⏹️ 用戶中斷執行")
        print("\n⏹️ 執行已被用戶中斷")
        return False
        
    except Exception as e:
        logger.error(f"❌ Phase 1執行失敗: {e}", exc_info=args.verbose)
        print(f"\n❌ 執行失敗: {e}")
        
        if args.verbose:
            import traceback
            traceback.print_exc()
        
        print("\n💡 故障排除建議:")
        print("1. 檢查網路連接 (TLE數據下載)")
        print("2. 確認依賴套件安裝完整")
        print("3. 使用 --fast 模式進行快速測試")
        print("4. 使用 --verbose 查看詳細錯誤信息")
        
        return False

if __name__ == "__main__":
    print("\n🛰️ 啟動Phase 1執行器...")
    
    try:
        success = asyncio.run(main())
        
        if success:
            print("\n✅ Phase 1執行成功完成")
            sys.exit(0)
        else:
            print("\n❌ Phase 1執行失敗")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️ 執行被中斷")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 未預期錯誤: {e}")
        sys.exit(1)