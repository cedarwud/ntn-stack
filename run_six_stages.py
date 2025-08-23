#!/usr/bin/env python
"""
執行完整六階段數據處理流程（修正路徑版本）
確保所有輸出正確保存到掛載的 volume
"""

import sys
import os
import json
from datetime import datetime, timezone
from pathlib import Path

def run_stage1():
    """階段一：TLE載入與SGP4軌道計算"""
    sys.path.append('/app')
    from src.stages.tle_orbital_calculation_processor import Stage1TLEProcessor
    
    print('🚀 執行階段一：TLE載入與SGP4軌道計算')
    print('=' * 60)
    
    processor = Stage1TLEProcessor(
        tle_data_dir='/app/tle_data',
        output_dir='/app/data/tle_calculation_outputs',  # 正確路徑
        sample_mode=False
    )
    
    result = processor.process_tle_orbital_calculation()
    
    if result:
        print(f'✅ 階段一完成: {result.get("metadata", {}).get("total_satellites")} 顆衛星')
        # 驗證檔案確實存在
        output_file = Path('/app/data/tle_calculation_outputs/tle_orbital_calculation_output.json')
        if output_file.exists():
            file_size = output_file.stat().st_size / (1024**3)  # GB
            print(f'  檔案大小: {file_size:.2f} GB')
    else:
        print('❌ 階段一執行失敗')
        return None
    
    return result

def run_stage2(stage1_result=None):
    """階段二：智能衛星篩選"""
    sys.path.append('/app')
    from src.stages.intelligent_satellite_filter_processor import IntelligentSatelliteFilterProcessor
    
    print('\n🎯 執行階段二：智能衛星篩選')
    print('=' * 60)
    
    processor = IntelligentSatelliteFilterProcessor(
        input_dir='/app/data',
        output_dir='/app/data/intelligent_filtering_outputs'
    )
    
    # 使用正確的方法名稱
    if stage1_result:
        result = processor.execute_refactored_intelligent_filtering(stage1_result)
        processor.save_intelligent_filtering_output(result)
    else:
        result = processor.process_intelligent_filtering()
    
    if result:
        total_filtered = sum(
            const_data.get('satellite_count', 0) 
            for const_data in result.get('constellations', {}).values()
        )
        print(f'✅ 階段二完成: {total_filtered} 顆衛星通過篩選')
    else:
        print('❌ 階段二執行失敗')
        return None
    
    return result

def run_stage3(stage2_result=None):
    """階段三：信號品質分析"""
    sys.path.append('/app')
    from src.stages.signal_quality_analysis_processor import SignalQualityAnalysisProcessor
    
    print('\n📡 執行階段三：信號品質分析')
    print('=' * 60)
    
    processor = SignalQualityAnalysisProcessor(
        input_dir='/app/data',
        output_dir='/app/data/signal_analysis_outputs'
    )
    
    # 使用正確的方法名稱
    result = processor.process_signal_quality_analysis(stage2_result)
    
    if result:
        print(f'✅ 階段三完成')
        # 檢查3GPP事件
        events = result.get('metadata', {}).get('total_3gpp_events', 0)
        print(f'  3GPP事件數: {events}')
    else:
        print('❌ 階段三執行失敗')
        return None
    
    return result

def run_stage4(stage3_result=None):
    """階段四：時間序列預處理"""
    sys.path.append('/app')
    from src.stages.timeseries_preprocessing_processor import TimeseriesPreprocessingProcessor
    
    print('\n⏰ 執行階段四：時間序列預處理')
    print('=' * 60)
    
    processor = TimeseriesPreprocessingProcessor(
        input_dir='/app/data',
        output_dir='/app/data/timeseries_preprocessing_outputs'
    )
    
    result = processor.process_timeseries_preprocessing(stage3_result)
    
    if result:
        print(f'✅ 階段四完成')
        # 檢查輸出檔案
        output_files = [
            '/app/data/timeseries_preprocessing_outputs/starlink_enhanced.json',
            '/app/data/timeseries_preprocessing_outputs/oneweb_enhanced.json'
        ]
        for file_path in output_files:
            if Path(file_path).exists():
                print(f'  ✓ {Path(file_path).name} 已生成')
    else:
        print('❌ 階段四執行失敗')
        return None
    
    return result

def run_stage5(stage4_result=None):
    """階段五：數據整合"""
    sys.path.append('/app')
    from src.stages.data_integration_processor import DataIntegrationProcessor
    
    print('\n🔄 執行階段五：數據整合')
    print('=' * 60)
    
    processor = DataIntegrationProcessor(
        input_dir='/app/data',
        output_dir='/app/data/data_integration_outputs'
    )
    
    result = processor.process_data_integration(stage4_result)
    
    if result:
        print(f'✅ 階段五完成')
    else:
        print('❌ 階段五執行失敗')
        return None
    
    return result

def run_stage6(stage5_result=None):
    """階段六：動態池規劃"""
    sys.path.append('/app')
    from src.stages.enhanced_dynamic_pool_planner import EnhancedDynamicPoolPlanner
    
    print('\n🎯 執行階段六：動態池規劃')
    print('=' * 60)
    
    processor = EnhancedDynamicPoolPlanner(
        input_dir='/app/data',
        output_dir='/app/data/dynamic_pool_planning_outputs'
    )
    
    result = processor.plan_dynamic_pools(stage5_result)
    
    if result:
        print(f'✅ 階段六完成')
        # 檢查動態池數量
        pools = result.get('dynamic_pools', [])
        print(f'  動態池數量: {len(pools)}')
    else:
        print('❌ 階段六執行失敗')
        return None
    
    return result

def verify_outputs():
    """驗證所有階段的輸出"""
    print('\n' + '=' * 80)
    print('📊 驗證六階段輸出結果：')
    print('=' * 80)
    
    stages = [
        ('階段一', '/app/data/tle_calculation_outputs/tle_orbital_calculation_output.json'),
        ('階段二', '/app/data/intelligent_filtering_outputs/intelligent_filtered_output.json'),
        ('階段三', '/app/data/signal_analysis_outputs/signal_event_analysis_output.json'),
        ('階段四', '/app/data/timeseries_preprocessing_outputs/starlink_enhanced.json'),
        ('階段五', '/app/data/data_integration_outputs/integrated_data_output.json'),
        ('階段六', '/app/data/dynamic_pool_planning_outputs/enhanced_dynamic_pools_output.json')
    ]
    
    all_success = True
    for stage_name, file_path in stages:
        path = Path(file_path)
        if path.exists():
            file_size = path.stat().st_size / (1024**2)  # MB
            print(f'  ✅ {stage_name}: {file_size:.1f} MB')
            
            # 檢查JSON內容
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    metadata = data.get('metadata', {})
                    if 'processing_timestamp' in metadata:
                        print(f'     處理時間: {metadata["processing_timestamp"]}')
                    if 'total_satellites' in metadata:
                        print(f'     衛星數量: {metadata["total_satellites"]}')
                    elif 'total_satellites_filtered' in metadata:
                        print(f'     篩選衛星: {metadata["total_satellites_filtered"]}')
            except Exception as e:
                print(f'     ⚠️ 無法讀取JSON: {e}')
        else:
            print(f'  ❌ {stage_name}: 檔案不存在')
            all_success = False
    
    return all_success

def main():
    """主執行函數"""
    print('🔧 六階段數據處理系統 - 完整執行')
    print('=' * 80)
    print(f'執行時間: {datetime.now(timezone.utc).isoformat()}')
    print('=' * 80)
    
    try:
        # 執行六個階段
        stage1_result = run_stage1()
        if not stage1_result:
            print('❌ 階段一失敗，停止執行')
            return 1
        
        stage2_result = run_stage2(stage1_result)
        if not stage2_result:
            print('❌ 階段二失敗，停止執行')
            return 2
        
        stage3_result = run_stage3(stage2_result)
        if not stage3_result:
            print('❌ 階段三失敗，停止執行')
            return 3
        
        stage4_result = run_stage4(stage3_result)
        if not stage4_result:
            print('❌ 階段四失敗，停止執行')
            return 4
        
        stage5_result = run_stage5(stage4_result)
        if not stage5_result:
            print('❌ 階段五失敗，停止執行')
            return 5
        
        stage6_result = run_stage6(stage5_result)
        if not stage6_result:
            print('❌ 階段六失敗，停止執行')
            return 6
        
        # 驗證所有輸出
        if verify_outputs():
            print('\n' + '=' * 80)
            print('🎉 六階段數據處理全部完成！')
            print('=' * 80)
            return 0
        else:
            print('\n⚠️ 部分階段輸出驗證失敗')
            return 7
            
    except Exception as e:
        print(f'\n❌ 執行過程中發生錯誤: {e}')
        import traceback
        traceback.print_exc()
        return 99

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)