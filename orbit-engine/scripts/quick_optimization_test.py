#!/usr/bin/env python3
"""
快速優化測試腳本 - 驗證修復後的並行處理是否正常工作
"""

import os
import sys
import time
import json

# 添加項目根目錄到路徑
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(project_root, 'src'))

from stages.stage2_orbital_computing.optimized_stage2_processor import OptimizedStage2Processor

def create_mock_stage1_data():
    """創建最小測試數據 - 模擬Stage1的實際輸出格式"""
    return {
        'stage': 'data_loading',
        'tle_data': [
            {
                'name': 'STARLINK-1008',
                'constellation': 'starlink',
                'tle_line1': '1 44714U 19074B   25264.18859944 -.00000585  00000+0 -20394-4 0  9999',
                'tle_line2': '2 44714  53.0523 227.5398 0001426  93.8814 266.2338 15.06398391323207',
                'line1': '1 44714U 19074B   25264.18859944 -.00000585  00000+0 -20394-4 0  9999',
                'line2': '2 44714  53.0523 227.5398 0001426  93.8814 266.2338 15.06398391323207',
                'norad_id': '44714',
                'satellite_id': '44714',
                'source_file': '/orbit-engine/data/tle_data/starlink/tle/starlink_20250921.tle',
                'epoch_datetime': '2025-09-21T04:31:34.991616+00:00',
                'epoch_year_full': 2025,
                'epoch_day_decimal': 264.18859944,
                'epoch_precision_seconds': 0.000864,
                'time_reference_standard': 'tle_epoch_utc',
                'time_quality_grade': 'A+'
            },
            {
                'name': 'STARLINK-1009',
                'constellation': 'starlink',
                'tle_line1': '1 44715U 19074C   25264.18859944 -.00000585  00000+0 -20394-4 0  9998',
                'tle_line2': '2 44715  53.0523 227.5398 0001426  94.8814 266.2338 15.06398391323208',
                'line1': '1 44715U 19074C   25264.18859944 -.00000585  00000+0 -20394-4 0  9998',
                'line2': '2 44715  53.0523 227.5398 0001426  94.8814 266.2338 15.06398391323208',
                'norad_id': '44715',
                'satellite_id': '44715',
                'source_file': '/orbit-engine/data/tle_data/starlink/tle/starlink_20250921.tle',
                'epoch_datetime': '2025-09-21T04:31:34.991616+00:00',
                'epoch_year_full': 2025,
                'epoch_day_decimal': 264.18859944,
                'epoch_precision_seconds': 0.000864,
                'time_reference_standard': 'tle_epoch_utc',
                'time_quality_grade': 'A+'
            }
        ],
        'metadata': {
            'satellites_loaded': 2,
            'processing_time': 0.1,
            'stage': 'data_loading'
        }
    }

def test_optimization():
    """測試優化處理器"""
    print("🚀 開始快速優化測試...")

    # 創建測試數據
    mock_data = create_mock_stage1_data()
    print(f"📊 測試數據: {len(mock_data['tle_data'])}顆衛星")

    try:
        # 創建優化處理器
        print("⚙️ 初始化優化處理器...")
        processor = OptimizedStage2Processor(enable_optimization=True)

        # 執行處理
        print("🔥 開始執行並行處理...")
        start_time = time.time()

        result = processor.execute(mock_data)

        execution_time = time.time() - start_time

        # 詳細調試信息
        print(f"🔍 詳細調試 - 完整結果結構:")
        if result:
            print(f"  - 結果類型: {type(result)}")
            if isinstance(result, dict):
                print(f"  - 結果鍵: {list(result.keys())}")

                # 檢查各種可能的數據字段
                for key in ['data', 'satellites', 'orbital_results', 'integrated_results']:
                    if key in result:
                        data = result[key]
                        print(f"  - {key}: {type(data)}, 長度: {len(data) if hasattr(data, '__len__') else 'N/A'}")
                        if data and hasattr(data, 'keys'):
                            sample_key = list(data.keys())[0]
                            print(f"    - 樣本鍵: {sample_key}")
                            print(f"    - 樣本類型: {type(data[sample_key])}")
        else:
            print("⚠️ 結果完全為空")

        # 檢查結果
        success = result.get('status') == 'success' if 'status' in result else 'error' not in str(result)

        print(f"✅ 處理完成:")
        print(f"   ⏱️ 執行時間: {execution_time:.3f}秒")
        print(f"   📊 處理狀態: {'成功' if success else '失敗'}")

        # 檢查優化指標
        if 'optimization_metrics' in result:
            metrics = result['optimization_metrics']
            print(f"   🚀 GPU使用: {metrics.get('hardware_utilization', {}).get('gpu_available', False)}")
            print(f"   💻 CPU並行: {metrics.get('performance_breakdown', {}).get('cpu_parallel_used', False)}")

            if 'performance_breakdown' in metrics:
                perf = metrics['performance_breakdown']
                print(f"   📈 SGP4計算: {perf.get('sgp4_calculation_time', 0):.3f}秒")
                print(f"   🌐 座標轉換: {perf.get('coordinate_conversion_time', 0):.3f}秒")
                print(f"   👁️ 可見性分析: {perf.get('visibility_analysis_time', 0):.3f}秒")

        return success, execution_time

    except Exception as e:
        print(f"❌ 優化處理器測試失敗: {e}")
        import traceback
        print("📋 完整錯誤跟踪:")
        traceback.print_exc()

        # 額外調試信息
        print("\n🔍 詳細錯誤分析:")
        print(f"  - 錯誤類型: {type(e).__name__}")
        print(f"  - 錯誤訊息: {str(e)}")

        return False, 0

if __name__ == '__main__':
    success, time_taken = test_optimization()

    print(f"\n{'='*50}")
    print(f"🎯 測試結果:")
    print(f"   狀態: {'✅ 成功' if success else '❌ 失敗'}")
    print(f"   時間: {time_taken:.3f}秒")
    print(f"{'='*50}")

    if success:
        print("🎉 優化處理器修復成功！可以正常執行並行計算")
    else:
        print("⚠️ 優化處理器仍有問題，需要進一步調試")