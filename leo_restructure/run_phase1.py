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

from phase1_core_system.main_pipeline import Phase1Pipeline, create_default_config
from shared_core.utils import setup_logger, format_duration

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
        default='/tmp/phase1_outputs',
        help='輸出目錄路徑 (預設: /tmp/phase1_outputs)'
    )
    
    return parser.parse_args()

def create_custom_config(args):
    """根據參數創建自定義配置"""
    config = create_default_config()
    
    # 快速模式調整
    if args.fast:
        config['tle_loader']['calculation_params']['time_range_minutes'] = 100
        config['optimizer']['optimization_params']['max_iterations'] = 100
        config['optimizer']['optimization_params']['cooling_rate'] = 0.90
        config['optimizer']['targets']['starlink_pool_size'] = 8085  # 全量Starlink衛星
        config['optimizer']['targets']['oneweb_pool_size'] = 651   # 全量OneWeb衛星
    else:
        # 正常模式參數
        config['tle_loader']['calculation_params']['time_range_minutes'] = args.time_range
        config['optimizer']['optimization_params']['max_iterations'] = args.iterations
    
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
    
    if args.fast:
        print("⚡ 快速測試模式")
    
    print(f"🔧 最佳化迭代: {args.iterations if not args.fast else 100}")
    print(f"⏱️ 模擬時間: {args.time_range if not args.fast else 100}分鐘")
    print(f"📁 輸出目錄: {args.output_dir}")
    print("-" * 70)
    
    try:
        # 創建配置
        config = create_custom_config(args)
        
        # 創建管道實例
        pipeline = Phase1Pipeline(config)
        
        # 修改輸出目錄
        pipeline.output_dir = Path(args.output_dir)
        pipeline.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"🚀 開始Phase 1執行 ({'快速模式' if args.fast else '正常模式'})")
        
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