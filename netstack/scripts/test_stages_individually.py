#!/usr/bin/env python3
"""
逐步測試每個階段，找出問題所在
"""

import sys
import os
import json
from pathlib import Path

sys.path.insert(0, '/app')
sys.path.insert(0, '/app/src')

def test_stage3():
    """測試階段三"""
    print("\n🔍 測試階段三：信號品質分析")
    print("-" * 60)
    
    try:
        # 載入階段二的輸出
        stage2_file = Path('/app/data/intelligent_filtering_outputs/intelligent_filtered_output.json')
        if not stage2_file.exists():
            print("❌ 階段二輸出文件不存在")
            return False
            
        with open(stage2_file, 'r') as f:
            stage2_data = json.load(f)
        
        print(f"✅ 載入階段二數據：{stage2_data['metadata'].get('total_satellites', 0)} 顆衛星")
        
        # 執行階段三
        from stages.signal_quality_analysis_processor import SignalQualityAnalysisProcessor
        
        stage3 = SignalQualityAnalysisProcessor(
            input_dir='/app/data',
            output_dir='/app/data/signal_analysis_outputs'
        )
        
        print("🚀 開始執行階段三...")
        result = stage3.process_signal_quality_analysis(
            filtered_data=stage2_data,
            save_output=True
        )
        
        if result:
            event_count = len(result.get('gpp_events', {}).get('all_events', []))
            print(f"✅ 階段三成功：{event_count} 個3GPP事件")
            return True
        else:
            print("❌ 階段三執行失敗")
            return False
            
    except Exception as e:
        print(f"❌ 階段三錯誤：{e}")
        import traceback
        traceback.print_exc()
        return False

def test_stage4():
    """測試階段四"""
    print("\n🔍 測試階段四：時間序列預處理")
    print("-" * 60)
    
    try:
        # 載入階段三的輸出
        stage3_file = Path('/app/data/signal_analysis_outputs/signal_event_analysis_output.json')
        if not stage3_file.exists():
            print("❌ 階段三輸出文件不存在")
            return False
            
        with open(stage3_file, 'r') as f:
            stage3_data = json.load(f)
        
        print(f"✅ 載入階段三數據")
        
        # 執行階段四
        from stages.timeseries_preprocessing_processor import TimeseriesPreprocessingProcessor
        
        stage4 = TimeseriesPreprocessingProcessor(
            input_dir='/app/data',
            output_dir='/app/data/timeseries_preprocessing_outputs'
        )
        
        print("🚀 開始執行階段四...")
        result = stage4.process_timeseries_preprocessing(
            signal_data=stage3_data,
            save_output=True
        )
        
        if result:
            ts_count = len(result.get('timeseries_data', {}).get('satellites', []))
            print(f"✅ 階段四成功：{ts_count} 顆衛星時間序列")
            return True
        else:
            print("❌ 階段四執行失敗")
            return False
            
    except Exception as e:
        print(f"❌ 階段四錯誤：{e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主測試流程"""
    print("🔍 六階段處理診斷測試")
    print("=" * 80)
    
    # 檢查現有輸出
    print("\n📊 檢查現有輸出文件：")
    stages = {
        'Stage 1': '/app/data/tle_calculation_outputs/tle_orbital_calculation_output.json',
        'Stage 2': '/app/data/intelligent_filtering_outputs/intelligent_filtered_output.json',
        'Stage 3': '/app/data/signal_analysis_outputs/signal_event_analysis_output.json',
        'Stage 4': '/app/data/timeseries_preprocessing_outputs/enhanced_timeseries_output.json',
        'Stage 5': '/app/data/data_integration_outputs/data_integration_output.json',
        'Stage 6': '/app/data/dynamic_pool_planning_outputs/enhanced_dynamic_pools_output.json'
    }
    
    for stage, path in stages.items():
        p = Path(path)
        if p.exists():
            size = p.stat().st_size / (1024 * 1024)  # MB
            print(f"  ✅ {stage}: {size:.1f} MB")
        else:
            print(f"  ❌ {stage}: 不存在")
    
    # 測試階段三
    if not Path(stages['Stage 3']).exists():
        if not test_stage3():
            print("\n⚠️ 階段三失敗，停止測試")
            return 1
    
    # 測試階段四
    if not Path(stages['Stage 4']).exists():
        if not test_stage4():
            print("\n⚠️ 階段四失敗，停止測試")
            return 1
    
    print("\n✅ 診斷測試完成")
    return 0

if __name__ == '__main__':
    sys.exit(main())