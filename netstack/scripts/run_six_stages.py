#!/usr/bin/env python
"""
六階段數據處理主執行器
在容器內執行: python /app/scripts/run_six_stages.py
"""

import sys
import os
import json
from datetime import datetime, timezone
from pathlib import Path

# 確保能找到模組
sys.path.insert(0, '/app')

def run_all_stages():
    """執行完整六階段處理流程"""
    from src.stages.tle_orbital_calculation_processor import Stage1TLEProcessor
    from src.stages.intelligent_satellite_filter_processor import IntelligentSatelliteFilterProcessor
    from src.stages.signal_quality_analysis_processor import SignalQualityAnalysisProcessor
    from src.stages.timeseries_preprocessing_processor import TimeseriesPreprocessingProcessor
    from src.stages.data_integration_processor import Stage5IntegrationProcessor as DataIntegrationProcessor
    from src.stages.enhanced_dynamic_pool_planner import EnhancedDynamicPoolPlanner
    
    print('🚀 六階段數據處理系統')
    print('=' * 80)
    print(f'開始時間: {datetime.now(timezone.utc).isoformat()}')
    print('=' * 80)
    
    results = {}
    
    # 階段一：TLE載入與SGP4計算
    print('\n📡 階段一：TLE載入與SGP4軌道計算')
    print('-' * 60)
    stage1 = Stage1TLEProcessor(
        tle_data_dir='/app/tle_data',
        output_dir='/app/data/tle_calculation_outputs',
        sample_mode=False
    )
    results['stage1'] = stage1.process_tle_orbital_calculation()
    
    if not results['stage1']:
        print('❌ 階段一失敗')
        return False
    print(f'✅ 階段一完成: {results["stage1"]["metadata"]["total_satellites"]} 顆衛星')
    
    # 階段二：智能衛星篩選  
    print('\n🎯 階段二：智能衛星篩選')
    print('-' * 60)
    stage2 = IntelligentSatelliteFilterProcessor(
        input_dir='/app/data',
        output_dir='/app/data/intelligent_filtering_outputs'
    )
    # 傳遞 orbital_data 作為關鍵字參數
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
    # 傳遞 filtered_data 作為字典數據
    results['stage3'] = stage3.process_signal_quality_analysis(filtered_data=results['stage2'])
    
    if not results['stage3']:
        print('❌ 階段三失敗')
        return False
    print(f'✅ 階段三完成')
    
    # 階段四：時間序列預處理
    print('\n⏰ 階段四：時間序列預處理')
    print('-' * 60)
    stage4 = TimeseriesPreprocessingProcessor(
        input_dir='/app/data',
        output_dir='/app/data/timeseries_preprocessing_outputs'
    )
    # 傳遞 signal_data 作為字典數據
    results['stage4'] = stage4.process_timeseries_preprocessing(signal_data=results['stage3'])
    
    if not results['stage4']:
        print('❌ 階段四失敗')
        return False
    print(f'✅ 階段四完成')
    
    # 階段五：數據整合
    print('\n🔄 階段五：數據整合')
    print('-' * 60)
    from src.stages.data_integration_processor import Stage5Config
    stage5_config = Stage5Config(
        input_enhanced_timeseries_dir='/app/data',
        output_data_integration_dir='/app/data/data_integration_outputs',
        elevation_thresholds=[5, 10, 15]
    )
    stage5 = DataIntegrationProcessor(stage5_config)
    # 傳遞 enhanced_data 作為字典數據
    results['stage5'] = stage5.process_data_integration(enhanced_data=results['stage4'])
    
    if not results['stage5']:
        print('❌ 階段五失敗')
        return False
    print(f'✅ 階段五完成')
    
    # 階段六：動態池規劃
    print('\n🎯 階段六：動態池規劃')
    print('-' * 60)
    stage6_config = {
        'input_dir': '/app/data',
        'output_dir': '/app/data/dynamic_pool_planning_outputs',
        'elevation_thresholds': [5, 10, 15],
        'pool_sizes': {'starlink': 120, 'oneweb': 36}
    }
    stage6 = EnhancedDynamicPoolPlanner(stage6_config)
    # 傳遞 integrated_data 作為字典數據
    results['stage6'] = stage6.plan_dynamic_pools(integrated_data=results['stage5'])
    
    if not results['stage6']:
        print('❌ 階段六失敗')
        return False
    print(f'✅ 階段六完成')
    
    return True

def verify_outputs():
    """驗證所有輸出檔案"""
    print('\n' + '=' * 80)
    print('📊 驗證輸出檔案：')
    print('=' * 80)
    
    outputs = {
        '階段一': '/app/data/tle_calculation_outputs/tle_orbital_calculation_output.json',
        '階段二': '/app/data/intelligent_filtering_outputs/intelligent_filtered_output.json',
        '階段三': '/app/data/signal_analysis_outputs/signal_event_analysis_output.json',
        '階段四-Starlink': '/app/data/timeseries_preprocessing_outputs/starlink_enhanced.json',
        '階段四-OneWeb': '/app/data/timeseries_preprocessing_outputs/oneweb_enhanced.json',
        '階段五': '/app/data/data_integration_outputs/integrated_data_output.json',
        '階段六': '/app/data/dynamic_pool_planning_outputs/enhanced_dynamic_pools_output.json'
    }
    
    all_valid = True
    for name, path in outputs.items():
        if Path(path).exists():
            size_mb = Path(path).stat().st_size / (1024**2)
            print(f'  ✅ {name}: {size_mb:.1f} MB')
            
            # 檢查JSON有效性
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                    if 'metadata' in data:
                        meta = data['metadata']
                        if 'processing_timestamp' in meta:
                            print(f'     時間: {meta["processing_timestamp"]}')
            except:
                print(f'     ⚠️ JSON解析失敗')
                all_valid = False
        else:
            print(f'  ❌ {name}: 不存在')
            all_valid = False
    
    return all_valid

def main():
    """主函數"""
    import argparse
    
    # 解析命令行參數
    parser = argparse.ArgumentParser(description='六階段數據處理系統')
    parser.add_argument('--data-dir', default='/app/data', 
                       help='數據輸出目錄 (預設: /app/data)')
    args = parser.parse_args()
    
    # 確保數據目錄存在
    os.makedirs(args.data_dir, exist_ok=True)
    
    try:
        # 執行六階段
        success = run_all_stages()
        
        if success:
            # 驗證輸出
            if verify_outputs():
                print('\n' + '=' * 80)
                print('🎉 六階段數據處理全部成功完成！')
                print('=' * 80)
                return 0
            else:
                print('\n⚠️ 部分輸出驗證失敗')
                return 1
        else:
            print('\n❌ 處理流程中斷')
            return 2
            
    except Exception as e:
        print(f'\n❌ 發生錯誤: {e}')
        import traceback
        traceback.print_exc()
        return 99

if __name__ == '__main__':
    exit(main())