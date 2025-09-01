#!/usr/bin/env python3
"""
簡化版六階段處理腳本 - 直接調用正確的類和方法
"""

import os
import sys
import json
import time
from datetime import datetime, timezone

# 添加模塊路徑
sys.path.append('/app')
sys.path.append('/app/src')

print('\n🚀 六階段數據處理系統（簡化版）')
print('=' * 80)
print(f'開始時間: {datetime.now(timezone.utc).isoformat()}')
print('=' * 80)

start_time = time.time()

try:
    # 階段一：TLE載入與SGP4軌道計算
    print('\n📡 階段一：TLE載入與SGP4軌道計算')
    print('-' * 60)
    
    from stages.tle_orbital_calculation_processor import Stage1TLEProcessor
    stage1 = Stage1TLEProcessor(
        tle_data_dir='/app/tle_data',
        output_dir='/app/data/tle_calculation_outputs'
    )
    stage1_result = stage1.process_tle_orbital_calculation()
    
    if stage1_result:
        print(f'✅ 階段一完成: {stage1_result["metadata"]["total_satellites"]} 顆衛星')
    else:
        print('❌ 階段一失敗')
        sys.exit(1)
    
    # 階段二：智能衛星篩選
    print('\n🎯 階段二：智能衛星篩選')
    print('-' * 60)
    
    from stages.intelligent_satellite_filter_processor import IntelligentSatelliteFilterProcessor
    stage2 = IntelligentSatelliteFilterProcessor(
        input_dir='/app/data',
        output_dir='/app/data/intelligent_filtering_outputs'
    )
    stage2_result = stage2.process_intelligent_filtering(orbital_data=stage1_result)
    
    if stage2_result:
        filtered_count = sum(
            c.get('satellite_count', 0) 
            for c in stage2_result.get('constellations', {}).values()
        )
        print(f'✅ 階段二完成: {filtered_count} 顆衛星通過篩選')
    else:
        print('❌ 階段二失敗')
        sys.exit(1)
    
    # 階段三：信號品質分析
    print('\n📡 階段三：信號品質分析與3GPP事件')
    print('-' * 60)
    
    from stages.signal_quality_analysis_processor import SignalQualityAnalysisProcessor
    stage3 = SignalQualityAnalysisProcessor(
        input_dir='/app/data',
        output_dir='/app/data/signal_analysis_outputs'
    )
    stage3_result = stage3.process_signal_quality_analysis(filtered_data=stage2_result)
    
    if stage3_result:
        event_count = len(stage3_result.get('gpp_events', {}).get('all_events', []))
        print(f'✅ 階段三完成: {event_count} 個3GPP事件')
    else:
        print('❌ 階段三失敗')
        sys.exit(1)
    
    # 階段四：時間序列預處理
    print('\n⏰ 階段四：時間序列預處理')
    print('-' * 60)
    
    from stages.timeseries_preprocessing_processor import TimeseriesPreprocessingProcessor
    stage4 = TimeseriesPreprocessingProcessor(
        input_dir='/app/data',
        output_dir='/app/data/timeseries_preprocessing_outputs'
    )
    stage4_result = stage4.process_timeseries_preprocessing(signal_data=stage3_result)
    
    if stage4_result:
        ts_count = len(stage4_result.get('timeseries_data', {}).get('satellites', []))
        print(f'✅ 階段四完成: {ts_count} 顆衛星時間序列')
    else:
        print('❌ 階段四失敗')
        sys.exit(1)
    
    # 階段五：數據整合
    print('\n🔗 階段五：數據整合')
    print('-' * 60)
    
    from stages.data_integration_processor import Stage5IntegrationProcessor
    stage5 = Stage5IntegrationProcessor(
        input_dir='/app/data',
        output_dir='/app/data/data_integration_outputs'
    )
    stage5_result = stage5.process_data_integration(timeseries_data=stage4_result)
    
    if stage5_result:
        integrated_count = stage5_result.get('metadata', {}).get('total_satellites', 0)
        print(f'✅ 階段五完成: {integrated_count} 顆衛星整合')
    else:
        print('❌ 階段五失敗')
        sys.exit(1)
    
    # 階段六：動態池規劃
    print('\n🎯 階段六：動態衛星池規劃')
    print('-' * 60)
    
    from stages.enhanced_dynamic_pool_planner import EnhancedDynamicPoolPlanner
    stage6 = EnhancedDynamicPoolPlanner(
        input_dir='/app/data',
        output_dir='/app/data/dynamic_pool_planning_outputs'
    )
    stage6_result = stage6.process_dynamic_pool_planning(integrated_data=stage5_result)
    
    if stage6_result:
        pool_data = stage6_result.get('dynamic_satellite_pool', {})
        total_selected = pool_data.get('total_selected', 0)
        starlink_count = len(pool_data.get('starlink_satellites', []))
        oneweb_count = len(pool_data.get('oneweb_satellites', []))
        
        print(f'✅ 階段六完成: 總計 {total_selected} 顆衛星')
        print(f'   - Starlink: {starlink_count} 顆')
        print(f'   - OneWeb: {oneweb_count} 顆')
    else:
        print('❌ 階段六失敗')
        sys.exit(1)
    
    # 生成最終報告
    print('\n📊 生成最終報告...')
    final_report = {
        'execution_time': datetime.now(timezone.utc).isoformat(),
        'stages_completed': 6,
        'pipeline_summary': {
            'stage1_loaded': stage1_result['metadata']['total_satellites'],
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
    
    # 保存最終報告
    report_path = '/app/data/leo_optimization_final_report.json'
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(final_report, f, indent=2, ensure_ascii=False)
    
    print(f'✅ 最終報告已保存: {report_path}')
    
    elapsed = time.time() - start_time
    print('\n' + '=' * 80)
    print(f'✅ 六階段處理成功完成！')
    print(f'總耗時: {elapsed:.2f} 秒 ({elapsed/60:.2f} 分鐘)')
    print('=' * 80)
    
except Exception as e:
    print(f'\n❌ 發生錯誤: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)