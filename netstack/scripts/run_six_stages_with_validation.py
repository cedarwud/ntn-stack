#!/usr/bin/env python3
"""
六階段數據處理系統 - 階段即時驗證版本
每個階段執行後立即驗證，失敗則停止後續處理
"""

import sys
import os
import json
import time
import logging
from datetime import datetime, timezone
from pathlib import Path

# 確保能找到模組
sys.path.insert(0, '/app')
sys.path.insert(0, '/app/src')

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 導入統一日誌管理器
try:
    from shared_core.unified_log_manager import UnifiedLogManager
    log_manager = None
except ImportError as e:
    print(f"⚠️ 無法導入統一日誌管理器: {e}")
    UnifiedLogManager = None
    log_manager = None

def validate_stage_immediately(stage_processor, processing_results, stage_num, stage_name):
    """
    階段執行後立即驗證
    
    Args:
        stage_processor: 階段處理器實例（包含驗證方法）
        processing_results: 處理結果
        stage_num: 階段編號
        stage_name: 階段名稱
        
    Returns:
        tuple: (validation_success, validation_message)
    """
    try:
        print(f"\n🔍 階段{stage_num}立即驗證檢查...")
        print("-" * 40)
        
        # 保存驗證快照（內含自動驗證）
        if hasattr(stage_processor, 'save_validation_snapshot'):
            validation_success = stage_processor.save_validation_snapshot(processing_results)
            
            if validation_success:
                print(f"✅ 階段{stage_num}驗證通過")
                return True, f"階段{stage_num}驗證成功"
            else:
                print(f"❌ 階段{stage_num}驗證快照生成失敗")
                return False, f"階段{stage_num}驗證快照生成失敗"
        else:
            # 如果沒有驗證方法，只做基本檢查
            if not processing_results:
                print(f"❌ 階段{stage_num}處理結果為空")
                return False, f"階段{stage_num}處理結果為空"
            
            print(f"⚠️ 階段{stage_num}無內建驗證，僅基本檢查通過")
            return True, f"階段{stage_num}基本檢查通過"
            
    except Exception as e:
        print(f"❌ 階段{stage_num}驗證異常: {e}")
        return False, f"階段{stage_num}驗證異常: {e}"

def check_validation_snapshot_quality(stage_num, data_dir="/app/data"):
    """
    檢查驗證快照的品質
    
    Args:
        stage_num: 階段編號
        data_dir: 數據目錄
        
    Returns:
        tuple: (quality_passed, quality_message)
    """
    try:
        validation_dir = Path(data_dir) / "validation_snapshots"
        snapshot_file = validation_dir / f"stage{stage_num}_validation.json"
        
        if not snapshot_file.exists():
            return False, f"階段{stage_num}驗證快照文件不存在"
        
        with open(snapshot_file, 'r', encoding='utf-8') as f:
            snapshot = json.load(f)
        
        # 檢查驗證狀態
        validation = snapshot.get('validation', {})
        passed = validation.get('passed', False)
        status = snapshot.get('status', 'unknown')
        
        if not passed or status != 'completed':
            # 提取失敗的檢查項目
            failed_checks = []
            all_checks = validation.get('allChecks', {})
            for check_name, check_result in all_checks.items():
                if not check_result:
                    failed_checks.append(check_name)
            
            failed_msg = f"階段{stage_num}品質驗證失敗: {', '.join(failed_checks)}" if failed_checks else f"階段{stage_num}品質驗證失敗"
            return False, failed_msg
        
        print(f"✅ 階段{stage_num}品質驗證通過")
        return True, f"階段{stage_num}品質驗證通過"
        
    except Exception as e:
        return False, f"階段{stage_num}品質檢查異常: {e}"

def run_all_stages_with_immediate_validation():
    """執行完整六階段處理流程 - 階段即時驗證版本"""
    
    # 🔧 新增：設置完整管道模式環境變量
    import os
    os.environ['PIPELINE_MODE'] = 'full'
    
    print('🚀 六階段數據處理系統 (階段即時驗證版本)')
    print('=' * 80)
    print(f'開始時間: {datetime.now(timezone.utc).isoformat()}')
    print('⚠️ 重要: 每個階段執行後立即驗證，失敗則停止後續處理')
    print('=' * 80)
    
    results = {}
    start_time = time.time()
    completed_stages = 0
    validation_failed_stage = None
    
    try:
        # 🗑️ 統一預處理清理：使用新的清理管理器
        print('\n🗑️ 統一預處理清理：清理所有階段舊輸出檔案')
        print('-' * 60)
        
        try:
            from shared_core.cleanup_manager import cleanup_all_stages
            cleaned_result = cleanup_all_stages()
            print(f'✅ 統一清理完成: {cleaned_result["files"]} 個檔案, {cleaned_result["directories"]} 個目錄已清理')
        except Exception as e:
            print(f'⚠️ 統一清理警告: {e}')
        
        # 階段一：TLE載入與SGP4計算
        print('\n📡 階段一：TLE載入與SGP4軌道計算')
        print('-' * 60)
        
        from stages.orbital_calculation_processor import Stage1TLEProcessor
        stage1 = Stage1TLEProcessor(
            tle_data_dir='/app/tle_data',
            output_dir='/app/data',
            sample_mode=False
        )
        
        results['stage1'] = stage1.process_tle_orbital_calculation()
        
        if not results['stage1']:
            print('❌ 階段一處理失敗')
            return False, 1, "階段一處理失敗"
        
        # 🔍 階段一立即驗證
        validation_success, validation_msg = validate_stage_immediately(
            stage1, results['stage1'], 1, "TLE載入與SGP4計算"
        )
        
        if not validation_success:
            print(f'❌ 階段一驗證失敗: {validation_msg}')
            print('🚫 停止後續階段處理，避免基於錯誤數據的無意義計算')
            return False, 1, validation_msg
        
        # 額外品質檢查
        quality_passed, quality_msg = check_validation_snapshot_quality(1)
        if not quality_passed:
            print(f'❌ 階段一品質檢查失敗: {quality_msg}')
            print('🚫 停止後續階段處理，避免基於低品質數據的計算')
            return False, 1, quality_msg
        
        completed_stages = 1
        print(f'✅ 階段一完成並驗證通過: {results["stage1"]["metadata"]["total_satellites"]} 顆衛星')
        
        # 階段二：智能衛星篩選
        print('\n🎯 階段二：智能衛星篩選')
        print('-' * 60)
        
        from stages.satellite_visibility_filter_processor import SatelliteVisibilityFilterProcessor
        stage2 = SatelliteVisibilityFilterProcessor(
            input_dir='/app/data',
            output_dir='/app/data'
        )
        
        results['stage2'] = stage2.process_intelligent_filtering(
            orbital_data=results['stage1'],
            save_output=True
        )
        
        if not results['stage2']:
            print('❌ 階段二處理失敗')
            return False, 2, "階段二處理失敗"
        
        # 🔍 階段二立即驗證
        validation_success, validation_msg = validate_stage_immediately(
            stage2, results['stage2'], 2, "智能衛星篩選"
        )
        
        if not validation_success:
            print(f'❌ 階段二驗證失敗: {validation_msg}')
            print('🚫 停止後續階段處理')
            return False, 2, validation_msg
        
        # 品質檢查
        quality_passed, quality_msg = check_validation_snapshot_quality(2)
        if not quality_passed:
            print(f'❌ 階段二品質檢查失敗: {quality_msg}')
            print('🚫 停止後續階段處理')
            return False, 2, quality_msg
        
        completed_stages = 2
        
        # 計算篩選後的衛星數量
        filtered_count = 0
        if 'constellations' in results['stage2']:
            for const_data in results['stage2']['constellations'].values():
                filtered_count += const_data.get('satellite_count', 0)
        elif 'metadata' in results['stage2']:
            filtered_count = results['stage2']['metadata'].get('total_satellites', 0)
        
        print(f'✅ 階段二完成並驗證通過: {filtered_count} 顆衛星通過篩選')
        
        # 階段三：信號品質分析
        print('\n📡 階段三：信號品質分析與3GPP事件')
        print('-' * 60)
        
        from stages.signal_analysis_processor import SignalQualityAnalysisProcessor
        stage3 = SignalQualityAnalysisProcessor(
            input_dir='/app/data',
            output_dir='/app/data'
        )
        
        results['stage3'] = stage3.process_signal_quality_analysis(
            filtering_data=results['stage2'],
            save_output=True
        )
        
        if not results['stage3']:
            print('❌ 階段三處理失敗')
            return False, 3, "階段三處理失敗"
        
        # 🔍 階段三立即驗證
        validation_success, validation_msg = validate_stage_immediately(
            stage3, results['stage3'], 3, "信號品質分析"
        )
        
        if not validation_success:
            print(f'❌ 階段三驗證失敗: {validation_msg}')
            print('🚫 停止後續階段處理')
            return False, 3, validation_msg
        
        # 品質檢查
        quality_passed, quality_msg = check_validation_snapshot_quality(3)
        if not quality_passed:
            print(f'❌ 階段三品質檢查失敗: {quality_msg}')
            print('🚫 停止後續階段處理')
            return False, 3, quality_msg
            
        completed_stages = 3
        
        event_count = 0
        if 'gpp_events' in results['stage3']:
            event_count = len(results['stage3']['gpp_events'].get('all_events', []))
        elif 'metadata' in results['stage3']:
            event_count = results['stage3']['metadata'].get('total_3gpp_events', 0)
        
        print(f'✅ 階段三完成並驗證通過: {event_count} 個3GPP事件')
        
        # 階段四：時間序列預處理
        print('\n⏰ 階段四：時間序列預處理')
        print('-' * 60)
        
        from stages.timeseries_preprocessing_processor import TimeseriesPreprocessingProcessor
        stage4 = TimeseriesPreprocessingProcessor(
            input_dir='/app/data',
            output_dir='/app/data'
        )
        
        results['stage4'] = stage4.process_timeseries_preprocessing(
            signal_file='/app/data/signal_quality_analysis_output.json',
            save_output=True
        )
        
        if not results['stage4']:
            print('❌ 階段四處理失敗')
            return False, 4, "階段四處理失敗"
        
        # 🔍 階段四立即驗證
        validation_success, validation_msg = validate_stage_immediately(
            stage4, results['stage4'], 4, "時間序列預處理"
        )
        
        if not validation_success:
            print(f'❌ 階段四驗證失敗: {validation_msg}')
            print('🚫 停止後續階段處理')
            return False, 4, validation_msg
        
        # 品質檢查
        quality_passed, quality_msg = check_validation_snapshot_quality(4)
        if not quality_passed:
            print(f'❌ 階段四品質檢查失敗: {quality_msg}')
            print('🚫 停止後續階段處理')
            return False, 4, quality_msg
            
        completed_stages = 4
        
        ts_count = 0
        if 'timeseries_data' in results['stage4']:
            ts_count = len(results['stage4']['timeseries_data'].get('satellites', []))
        elif 'metadata' in results['stage4']:
            ts_count = results['stage4']['metadata'].get('total_satellites', 0)
        
        print(f'✅ 階段四完成並驗證通過: {ts_count} 顆衛星時間序列')
        
        # 階段五：數據整合
        print('\n🔄 階段五：數據整合')
        print('-' * 60)
        
        import asyncio
        from stages.data_integration_processor import Stage5IntegrationProcessor, Stage5Config
        
        stage5_config = Stage5Config(
            input_enhanced_timeseries_dir='/app/data',
            output_data_integration_dir='/app/data',
            elevation_thresholds=[5, 10, 15]
        )
        
        stage5 = Stage5IntegrationProcessor(stage5_config)
        results['stage5'] = asyncio.run(stage5.process_enhanced_timeseries())
        
        if not results['stage5']:
            print('❌ 階段五處理失敗')
            return False, 5, "階段五處理失敗"
        
        # 🔍 階段五立即驗證
        validation_success, validation_msg = validate_stage_immediately(
            stage5, results['stage5'], 5, "數據整合"
        )
        
        if not validation_success:
            print(f'❌ 階段五驗證失敗: {validation_msg}')
            print('🚫 停止後續階段處理')
            return False, 5, validation_msg
        
        # 品質檢查
        quality_passed, quality_msg = check_validation_snapshot_quality(5)
        if not quality_passed:
            print(f'❌ 階段五品質檢查失敗: {quality_msg}')
            print('🚫 停止後續階段處理')
            return False, 5, quality_msg
            
        completed_stages = 5
        
        integrated_count = results['stage5'].get('metadata', {}).get('total_satellites', 0)
        print(f'✅ 階段五完成並驗證通過: {integrated_count} 顆衛星整合')
        
        # 階段六：動態池規劃
        print('\n🎯 階段六：動態池規劃')
        print('-' * 60)
        
        from stages.dynamic_pool_planner import EnhancedDynamicPoolPlanner
        
        stage6_config = {
            'input_dir': '/app/data',
            'output_dir': '/app/data'
        }
        stage6 = EnhancedDynamicPoolPlanner(stage6_config)
        
        results['stage6'] = stage6.process(
            input_data=results['stage5'],
            output_file='/app/data/enhanced_dynamic_pools_output.json'
        )
        
        if not results['stage6']:
            print('❌ 階段六處理失敗')
            return False, 6, "階段六處理失敗"
        
        # 🔍 階段六立即驗證
        validation_success, validation_msg = validate_stage_immediately(
            stage6, results['stage6'], 6, "動態池規劃"
        )
        
        if not validation_success:
            print(f'❌ 階段六驗證失敗: {validation_msg}')
            return False, 6, validation_msg
        
        # 品質檢查
        quality_passed, quality_msg = check_validation_snapshot_quality(6)
        if not quality_passed:
            print(f'❌ 階段六品質檢查失敗: {quality_msg}')
            return False, 6, quality_msg
            
        completed_stages = 6
        
        # 提取最終結果
        pool_data = results['stage6'].get('dynamic_satellite_pool', {})
        total_selected = pool_data.get('total_selected', 0)
        
        starlink_data = pool_data.get('starlink_satellites', 0)
        if isinstance(starlink_data, list):
            starlink_count = len(starlink_data)
        else:
            starlink_count = starlink_data
            
        oneweb_data = pool_data.get('oneweb_satellites', 0)
        if isinstance(oneweb_data, list):
            oneweb_count = len(oneweb_data)
        else:
            oneweb_count = oneweb_data
        
        print(f'✅ 階段六完成並驗證通過: 總計 {total_selected} 顆衛星')
        print(f'   - Starlink: {starlink_count} 顆')
        print(f'   - OneWeb: {oneweb_count} 顆')
        
        # 生成最終報告
        elapsed_time = time.time() - start_time
        print('\n' + '=' * 80)
        print('🎉 六階段處理與驗證完成總結')
        print('=' * 80)
        print(f'✅ 所有階段成功完成並驗證通過！')
        print(f'⏱️ 總耗時: {elapsed_time:.2f} 秒 ({elapsed_time/60:.2f} 分鐘)')
        print(f'📊 數據流程與驗證狀態:')
        print(f'   Stage 1: {results["stage1"]["metadata"]["total_satellites"]} 顆衛星載入 ✅')
        print(f'   Stage 2: {filtered_count} 顆衛星篩選 ✅')
        print(f'   Stage 3: {event_count} 個3GPP事件 ✅')
        print(f'   Stage 4: {ts_count} 顆衛星時間序列 ✅')
        print(f'   Stage 5: {integrated_count} 顆衛星整合 ✅')
        print(f'   Stage 6: {total_selected} 顆衛星最終選擇 ✅')
        print('🔍 品質保證: 所有階段都經過立即驗證')
        print('=' * 80)
        
        # 移除重複的報告生成 - 使用Docker日誌和驗證快照已足夠
        
        return True, completed_stages, "所有階段成功完成並驗證通過"
        
    except Exception as e:
        print(f'\n❌ 發生錯誤: {e}')
        import traceback
        traceback.print_exc()
        return False, completed_stages, f"執行異常: {e}"

def main():
    """主程序入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='六階段數據處理系統 - 階段即時驗證版本')
    parser.add_argument('--data-dir', default='/app/data', help='數據目錄')
    args = parser.parse_args()
    
    # 執行六階段處理
    success, completed_stages, message = run_all_stages_with_immediate_validation()
    
    print(f'\n📊 執行總結:')
    print(f'   成功狀態: {"✅ 成功" if success else "❌ 失敗"}')
    print(f'   完成階段: {completed_stages}/6')
    print(f'   結果信息: {message}')
    
    if success and completed_stages == 6:
        print('🎉 六階段處理與驗證完全成功！')
        return 0
    else:
        print(f'💥 在階段{completed_stages}發生問題: {message}')
        return 1

if __name__ == '__main__':
    sys.exit(main())