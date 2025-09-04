#!/usr/bin/env python3
"""
六階段數據處理統一執行腳本
修復多重實現問題後的標準版本
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

def run_all_stages():
    """執行完整六階段處理流程"""
    
    print('🚀 六階段數據處理系統 (最終修復版)')
    print('=' * 80)
    print(f'開始時間: {datetime.now(timezone.utc).isoformat()}')
    print('=' * 80)
    
    results = {}
    start_time = time.time()
    
    try:
        # 🗑️ 預處理：清理所有階段六舊輸出檔案
        print('\n🗑️ 預處理：清理階段六舊輸出檔案')
        print('-' * 60)
        
        try:
            from stages.dynamic_pool_planner import EnhancedDynamicPoolPlanner
            # 創建臨時實例進行清理
            temp_planner = EnhancedDynamicPoolPlanner({'cleanup_only': True})
            cleaned_count = temp_planner.cleanup_all_stage6_outputs()
            print(f'✅ 階段六清理完成: {cleaned_count} 項目已清理')
        except Exception as e:
            print(f'⚠️ 階段六清理警告: {e}')
            print('🔄 繼續執行六階段處理...')
        
        # 階段一：TLE載入與SGP4計算
        print('\n📡 階段一：TLE載入與SGP4軌道計算')
        print('-' * 60)
        
        from stages.orbital_calculation_processor import Stage1TLEProcessor
        stage1 = Stage1TLEProcessor(
            tle_data_dir='/app/tle_data',
            output_dir='/app/data/tle_calculation_outputs',
            sample_mode=False  # 全量處理模式
        )
        results['stage1'] = stage1.process_tle_orbital_calculation()
        
        if not results['stage1']:
            print('❌ 階段一失敗')
            return False
        print(f'✅ 階段一完成: {results["stage1"]["metadata"]["total_satellites"]} 顆衛星')
        
        # 階段二：智能衛星篩選
        print('\n🎯 階段二：智能衛星篩選')
        print('-' * 60)
        
        from stages.satellite_visibility_filter_processor import SatelliteVisibilityFilterProcessor
        stage2 = SatelliteVisibilityFilterProcessor(
            input_dir='/app/data',
            output_dir='/app/data/intelligent_filtering_outputs'
        )
        # 使用orbital_data參數
        results['stage2'] = stage2.process_intelligent_filtering(
            orbital_data=results['stage1'],
            save_output=True
        )
        
        if not results['stage2']:
            print('❌ 階段二失敗')
            return False
            
        # 計算篩選後的衛星數量
        filtered_count = 0
        if 'constellations' in results['stage2']:
            for const_data in results['stage2']['constellations'].values():
                filtered_count += const_data.get('satellite_count', 0)
        elif 'metadata' in results['stage2']:
            filtered_count = results['stage2']['metadata'].get('total_satellites', 0)
        
        print(f'✅ 階段二完成: {filtered_count} 顆衛星通過篩選')
        
        # 階段三：信號品質分析
        print('\n📡 階段三：信號品質分析與3GPP事件')
        print('-' * 60)
        
        from stages.signal_analysis_processor import SignalQualityAnalysisProcessor
        stage3 = SignalQualityAnalysisProcessor(
            input_dir='/app/data',
            output_dir='/app/data/signal_analysis_outputs'
        )
        # 使用filtering_data參數（注意：不是filtered_data）
        results['stage3'] = stage3.process_signal_quality_analysis(
            filtering_data=results['stage2'],  # 正確的參數名
            save_output=True
        )
        
        if not results['stage3']:
            print('❌ 階段三失敗')
            return False
            
        event_count = 0
        if 'gpp_events' in results['stage3']:
            event_count = len(results['stage3']['gpp_events'].get('all_events', []))
        elif 'metadata' in results['stage3']:
            event_count = results['stage3']['metadata'].get('total_3gpp_events', 0)
        
        print(f'✅ 階段三完成: {event_count} 個3GPP事件')
        
        # 階段四：時間序列預處理
        print('\n⏰ 階段四：時間序列預處理')
        print('-' * 60)
        
        from stages.timeseries_optimization_processor import TimeseriesPreprocessingProcessor
        stage4 = TimeseriesPreprocessingProcessor(
            input_dir='/app/data',
            output_dir='/app/data/timeseries_preprocessing_outputs'
        )
        
        # 使用默認輸入路徑（階段三已經保存檔案）
        results['stage4'] = stage4.process_timeseries_preprocessing(
            signal_file='/app/data/signal_analysis_outputs/signal_event_analysis_output.json',
            save_output=True
        )
        
        if not results['stage4']:
            print('❌ 階段四失敗')
            return False
            
        ts_count = 0
        if 'timeseries_data' in results['stage4']:
            ts_count = len(results['stage4']['timeseries_data'].get('satellites', []))
        elif 'metadata' in results['stage4']:
            ts_count = results['stage4']['metadata'].get('total_satellites', 0)
        
        print(f'✅ 階段四完成: {ts_count} 顆衛星時間序列')
        
        # 階段五：數據整合
        print('\n🔄 階段五：數據整合')
        print('-' * 60)
        
        import asyncio
        from stages.data_integration_processor import Stage5IntegrationProcessor, Stage5Config
        
        # 創建配置
        stage5_config = Stage5Config(
            input_enhanced_timeseries_dir='/app/data',
            output_data_integration_dir='/app/data/data_integration_outputs',
            elevation_thresholds=[5, 10, 15]
        )
        
        stage5 = Stage5IntegrationProcessor(stage5_config)
        # 使用async方法
        results['stage5'] = asyncio.run(stage5.process_enhanced_timeseries())
        
        if not results['stage5']:
            print('❌ 階段五失敗')
            return False
            
        integrated_count = results['stage5'].get('metadata', {}).get('total_satellites', 0)
        print(f'✅ 階段五完成: {integrated_count} 顆衛星整合')
        
        # 階段六：動態池規劃
        print('\n🎯 階段六：動態池規劃')
        print('-' * 60)
        
        from stages.dynamic_pool_planner import EnhancedDynamicPoolPlanner
        
        stage6_config = {
            'input_dir': '/app/data',
            'output_dir': '/app/data/dynamic_pool_planning_outputs'
        }
        stage6 = EnhancedDynamicPoolPlanner(stage6_config)
        
        # 使用process方法
        results['stage6'] = stage6.process(
            input_data=results['stage5'],
            output_file='/app/data/dynamic_pool_planning_outputs/enhanced_dynamic_pools_output.json'
        )
        
        if not results['stage6']:
            print('❌ 階段六失敗')
            return False
            
        # 提取最終結果
        pool_data = results['stage6'].get('dynamic_satellite_pool', {})
        total_selected = pool_data.get('total_selected', 0)
        
        # 處理可能是整數或列表的情況
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
        
        print(f'✅ 階段六完成: 總計 {total_selected} 顆衛星')
        print(f'   - Starlink: {starlink_count} 顆')
        print(f'   - OneWeb: {oneweb_count} 顆')
        
        # 生成最終報告
        elapsed_time = time.time() - start_time
        print('\n' + '=' * 80)
        print('📊 六階段處理完成總結')
        print('=' * 80)
        print(f'✅ 所有階段成功完成！')
        print(f'⏱️ 總耗時: {elapsed_time:.2f} 秒 ({elapsed_time/60:.2f} 分鐘)')
        print(f'📊 數據流程:')
        print(f'   Stage 1: {results["stage1"]["metadata"]["total_satellites"]} 顆衛星載入')
        print(f'   Stage 2: {filtered_count} 顆衛星篩選')
        print(f'   Stage 3: {event_count} 個3GPP事件')
        print(f'   Stage 4: {ts_count} 顆衛星時間序列')
        print(f'   Stage 5: {integrated_count} 顆衛星整合')
        print(f'   Stage 6: {total_selected} 顆衛星最終選擇')
        print('=' * 80)
        
        # 保存最終報告
        final_report = {
            'execution_time': datetime.now(timezone.utc).isoformat(),
            'processing_time_seconds': elapsed_time,
            'stages_completed': 6,
            'pipeline_summary': {
                'stage1_loaded': results['stage1']['metadata']['total_satellites'],
                'stage2_filtered': filtered_count,
                'stage3_events': event_count,
                'stage4_timeseries': ts_count,
                'stage5_integrated': integrated_count,
                'stage6_selected': total_selected
            },
            'final_satellite_pool': {
                'total': total_selected,
                'starlink': starlink_count,
                'oneweb': oneweb_count
            },
            'success': True
        }
        
        report_path = '/app/data/leo_optimization_final_report.json'
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(final_report, f, indent=2, ensure_ascii=False)
        
        print(f'\n✅ 最終報告已保存: {report_path}')
        
        return True
        
    except Exception as e:
        print(f'\n❌ 發生錯誤: {e}')
        import traceback
        traceback.print_exc()
        return False

def main():
    """主程序入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='六階段數據處理系統')
    parser.add_argument('--data-dir', default='/app/data', help='數據目錄')
    parser.add_argument('--skip-stage1', action='store_true', help='跳過階段一（如果已經完成）')
    parser.add_argument('--skip-stage2', action='store_true', help='跳過階段二（如果已經完成）')
    args = parser.parse_args()
    
    # 確保數據目錄存在
    data_dir = Path(args.data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # 執行六階段處理
    success = run_all_stages()
    
    if success:
        return 0
    else:
        return 1

if __name__ == '__main__':
    sys.exit(main())