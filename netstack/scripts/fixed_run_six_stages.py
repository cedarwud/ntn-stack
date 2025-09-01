#!/usr/bin/env python3
"""
修復版六階段數據處理主控制器
解決了階段二參數傳遞問題
"""

import os
import sys
import json
import time
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

# 添加模塊路徑
sys.path.append('/app')
sys.path.append('/app/src')

# 導入各階段處理器（使用正確的類名）
from stages.tle_orbital_calculation_processor import Stage1TLEProcessor as TLEOrbitalCalculationProcessor
from stages.intelligent_satellite_filter_processor import IntelligentSatelliteFilterProcessor
from stages.signal_quality_analysis_processor import SignalQualityAnalysisProcessor
from stages.timeseries_preprocessing_processor import TimeseriesPreprocessingProcessor
from stages.data_integration_processor import Stage5IntegrationProcessor as DataIntegrationProcessor
from stages.enhanced_dynamic_pool_planner import EnhancedDynamicPoolPlanner as DynamicPoolPlanningProcessor

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_all_stages() -> bool:
    """執行完整的六階段處理流程（修復版）"""
    
    results = {}
    
    # 階段一：TLE載入與SGP4軌道計算
    print('\n📡 階段一：TLE載入與SGP4軌道計算')
    print('-' * 60)
    stage1 = TLEOrbitalCalculationProcessor(
        tle_dir='/app/tle_data',
        output_dir='/app/data/tle_calculation_outputs'
    )
    results['stage1'] = stage1.process_tle_orbital_calculation()
    
    if not results['stage1']:
        print('❌ 階段一失敗')
        return False
    print(f'✅ 階段一完成: {results["stage1"]["metadata"]["total_satellites"]} 顆衛星')
    
    # 階段二：智能衛星篩選（修復：使用 orbital_data 關鍵字參數）
    print('\n🎯 階段二：智能衛星篩選')
    print('-' * 60)
    stage2 = IntelligentSatelliteFilterProcessor(
        input_dir='/app/data',
        output_dir='/app/data/intelligent_filtering_outputs'
    )
    # 關鍵修復：使用 orbital_data 關鍵字參數
    results['stage2'] = stage2.process_intelligent_filtering(orbital_data=results['stage1'])
    
    if not results['stage2']:
        print('❌ 階段二失敗')
        return False
    filtered_count = sum(
        c.get('satellite_count', 0) 
        for c in results['stage2'].get('constellations', {}).values()
    )
    print(f'✅ 階段二完成: {filtered_count} 顆衛星通過篩選')
    
    # 階段三：信號品質分析
    print('\n📡 階段三：信號品質分析與3GPP事件')
    print('-' * 60)
    stage3 = SignalQualityAnalysisProcessor(
        input_dir='/app/data',
        output_dir='/app/data/signal_analysis_outputs'
    )
    # 修復：使用 filtered_data 關鍵字參數
    results['stage3'] = stage3.process_signal_quality_analysis(filtered_data=results['stage2'])
    
    if not results['stage3']:
        print('❌ 階段三失敗')
        return False
    event_count = len(results['stage3'].get('gpp_events', {}).get('all_events', []))
    print(f'✅ 階段三完成: {event_count} 個3GPP事件')
    
    # 階段四：時間序列預處理
    print('\n⏰ 階段四：時間序列預處理')
    print('-' * 60)
    stage4 = TimeseriesPreprocessingProcessor(
        input_dir='/app/data',
        output_dir='/app/data/timeseries_preprocessing_outputs'
    )
    # 修復：使用 signal_data 關鍵字參數
    results['stage4'] = stage4.process_timeseries_preprocessing(signal_data=results['stage3'])
    
    if not results['stage4']:
        print('❌ 階段四失敗')
        return False
    ts_count = len(results['stage4'].get('timeseries_data', {}).get('satellites', []))
    print(f'✅ 階段四完成: {ts_count} 顆衛星時間序列')
    
    # 階段五：數據整合
    print('\n🔗 階段五：數據整合')
    print('-' * 60)
    stage5 = DataIntegrationProcessor(
        input_dir='/app/data',
        output_dir='/app/data/data_integration_outputs'
    )
    # 修復：使用 timeseries_data 關鍵字參數
    results['stage5'] = stage5.process_data_integration(timeseries_data=results['stage4'])
    
    if not results['stage5']:
        print('❌ 階段五失敗')
        return False
    integrated_count = results['stage5'].get('metadata', {}).get('total_satellites', 0)
    print(f'✅ 階段五完成: {integrated_count} 顆衛星整合')
    
    # 階段六：動態池規劃
    print('\n🎯 階段六：動態衛星池規劃')
    print('-' * 60)
    stage6 = DynamicPoolPlanningProcessor(
        input_dir='/app/data',
        output_dir='/app/data/dynamic_pool_planning_outputs'
    )
    # 修復：使用 integrated_data 關鍵字參數
    results['stage6'] = stage6.process_dynamic_pool_planning(integrated_data=results['stage5'])
    
    if not results['stage6']:
        print('❌ 階段六失敗')
        return False
    
    # 顯示最終結果
    pool_data = results['stage6'].get('dynamic_satellite_pool', {})
    total_selected = pool_data.get('total_selected', 0)
    starlink_count = len(pool_data.get('starlink_satellites', []))
    oneweb_count = len(pool_data.get('oneweb_satellites', []))
    
    print(f'✅ 階段六完成: 總計 {total_selected} 顆衛星')
    print(f'   - Starlink: {starlink_count} 顆')
    print(f'   - OneWeb: {oneweb_count} 顆')
    
    # 生成最終報告
    print('\n📊 生成最終報告...')
    final_report = {
        'execution_time': datetime.now(timezone.utc).isoformat(),
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
    
    # 保存最終報告
    report_path = '/app/data/leo_optimization_final_report.json'
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(final_report, f, indent=2, ensure_ascii=False)
    
    print(f'✅ 最終報告已保存: {report_path}')
    
    return True

def main():
    """主程序入口"""
    print('\n🚀 六階段數據處理系統（修復版）')
    print('=' * 80)
    print(f'開始時間: {datetime.now(timezone.utc).isoformat()}')
    print('=' * 80)
    
    start_time = time.time()
    
    try:
        success = run_all_stages()
        
        if success:
            elapsed = time.time() - start_time
            print('\n' + '=' * 80)
            print(f'✅ 六階段處理成功完成！')
            print(f'總耗時: {elapsed:.2f} 秒 ({elapsed/60:.2f} 分鐘)')
            print('=' * 80)
            return 0
        else:
            print('\n❌ 六階段處理失敗')
            return 1
            
    except Exception as e:
        print(f'\n❌ 發生錯誤: {e}')
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())