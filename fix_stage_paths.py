#!/usr/bin/env python
"""
修復六階段處理器的輸出路徑問題
將錯誤的 /app/data/leo_outputs/ 改為正確的 /app/data/
"""

import sys
import os

# 修復階段一的執行路徑
def fix_stage1():
    sys.path.append('/app')
    from src.stages.tle_orbital_calculation_processor import Stage1TLEProcessor
    
    print('🚀 執行階段一（修正路徑版本）：TLE載入與SGP4軌道計算')
    print('=' * 60)
    
    # 使用正確的路徑：/app/data 對應到主機的 /home/sat/ntn-stack/data/leo_outputs
    processor = Stage1TLEProcessor(
        tle_data_dir='/app/tle_data',
        output_dir='/app/data/tle_calculation_outputs',  # 修正的路徑
        sample_mode=False
    )
    
    # 執行完整的 TLE 軌道計算處理
    result = processor.process_tle_orbital_calculation()
    
    print('=' * 60)
    if result:
        print('✅ 階段一執行成功')
        print(f'處理時間戳: {result.get("metadata", {}).get("processing_timestamp")}')
        print(f'總衛星數: {result.get("metadata", {}).get("total_satellites")}')
        print(f'星座數量: {result.get("metadata", {}).get("total_constellations")}')
        
        # 檢查數據血統追蹤
        lineage = result.get('metadata', {}).get('data_lineage', {})
        if lineage:
            print('📊 數據血統追蹤:')
            print(f'  TLE日期: {lineage.get("tle_dates", {})}')
            print(f'  處理時間: {result["metadata"]["processing_timestamp"]}')
    else:
        print('❌ 階段一執行失敗')
    
    return result

# 修復階段二的執行路徑
def fix_stage2(stage1_result=None):
    sys.path.append('/app')
    from src.stages.intelligent_satellite_filter_processor import IntelligentSatelliteFilterProcessor
    
    print('\n🎯 執行階段二（修正路徑版本）：智能衛星篩選')
    print('=' * 60)
    
    processor = IntelligentSatelliteFilterProcessor(
        input_dir='/app/data',  # 修正的路徑
        output_dir='/app/data/intelligent_filtering_outputs'  # 修正的路徑
    )
    
    # 如果有 stage1 結果，使用記憶體傳遞；否則從檔案載入
    if stage1_result:
        result = processor.execute_refactored_intelligent_filtering(stage1_result)
    else:
        result = processor.process_intelligent_filtering()
    
    print('=' * 60)
    if result:
        print('✅ 階段二執行成功')
        print(f'篩選後衛星數: {result.get("metadata", {}).get("total_satellites_filtered")}')
    else:
        print('❌ 階段二執行失敗')
    
    return result

# 修復階段三的執行路徑
def fix_stage3(stage2_result=None):
    sys.path.append('/app')
    from src.stages.signal_quality_analysis_processor import SignalQualityAnalysisProcessor
    
    print('\n📡 執行階段三（修正路徑版本）：信號品質分析')
    print('=' * 60)
    
    processor = SignalQualityAnalysisProcessor(
        input_dir='/app/data',  # 修正的路徑
        output_dir='/app/data/signal_analysis_outputs'  # 修正的路徑
    )
    
    # 如果有 stage2 結果，使用記憶體傳遞；否則從檔案載入
    if stage2_result:
        result = processor.execute_signal_analysis(stage2_result)
    else:
        result = processor.process_signal_quality_analysis()
    
    print('=' * 60)
    if result:
        print('✅ 階段三執行成功')
    else:
        print('❌ 階段三執行失敗')
    
    return result

# 主執行函數
def main():
    print('🔧 開始修復並執行六階段數據處理')
    print('=' * 80)
    
    # 依序執行各階段
    stage1_result = fix_stage1()
    
    if stage1_result:
        stage2_result = fix_stage2(stage1_result)
        
        if stage2_result:
            stage3_result = fix_stage3(stage2_result)
            # 後續階段待實現...
    
    print('\n' + '=' * 80)
    print('🎉 階段處理完成')

if __name__ == '__main__':
    main()
