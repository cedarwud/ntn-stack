#!/usr/bin/env python3
"""
從階段四開始執行六階段數據處理
使用現有的階段三輸出數據
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

def run_stages_4_to_6():
    """執行階段4到階段6的處理流程"""
    
    print('🚀 六階段數據處理系統 - 階段4到6 (修復版)')
    print('=' * 80)
    print(f'開始時間: {datetime.now(timezone.utc).isoformat()}')
    print('=' * 80)
    
    results = {}
    start_time = time.time()
    
    try:
        # 載入階段三的輸出
        print('\n📥 載入階段三輸出數據')
        print('-' * 60)
        
        stage3_file = '/app/data/signal_analysis_outputs/signal_event_analysis_output.json'
        with open(stage3_file, 'r', encoding='utf-8') as f:
            results['stage3'] = json.load(f)
        
        stage3_satellites = results['stage3']['metadata'].get('satellites_count', 0)
        print(f'✅ 階段三數據載入完成: {stage3_satellites} 顆衛星')
        
        # 階段四：時間序列預處理
        print('\n⏰ 階段四：時間序列預處理')
        print('-' * 60)
        
        from stages.timeseries_preprocessing_processor import TimeseriesPreprocessingProcessor
        stage4 = TimeseriesPreprocessingProcessor(
            input_dir='/app/data',
            output_dir='/app/data/timeseries_preprocessing_outputs'
        )
        
        # Stage 4 loads from file, specify correct path
        results['stage4'] = stage4.process_timeseries_preprocessing(
            signal_file='/app/data/signal_analysis_outputs/signal_event_analysis_output.json',
            save_output=True
        )
        
        if not results['stage4']:
            print('❌ 階段四失敗')
            return False
            
        ts_count = 0
        if 'conversion_statistics' in results['stage4']:
            ts_count = results['stage4']['conversion_statistics'].get('successful_conversions', 0)
        elif 'constellation_data' in results['stage4']:
            starlink_processed = results['stage4']['constellation_data']['starlink'].get('satellites_processed', 0)
            oneweb_processed = results['stage4']['constellation_data']['oneweb'].get('satellites_processed', 0)
            ts_count = starlink_processed + oneweb_processed
        
        print(f'✅ 階段四完成: {ts_count} 顆衛星時間序列')
        
        # 階段五：數據整合
        print('\n🔄 階段五：數據整合')
        print('-' * 60)
        
        # 嘗試兩種導入方式
        try:
            from stages.data_integration_processor import Stage5IntegrationProcessor, Stage5Config
            
            # 創建配置
            stage5_config = Stage5Config(
                input_enhanced_timeseries_dir='/app/data',
                output_data_integration_dir='/app/data/data_integration_outputs',
                elevation_thresholds=[5, 10, 15]
            )
            
            stage5 = Stage5IntegrationProcessor(stage5_config)
            # 使用enhanced_data參數（根據原始程式碼）
            results['stage5'] = stage5.process_data_integration(
                enhanced_data=results['stage4'],
                save_output=True
            )
        except ImportError:
            # 如果上面的導入失敗，嘗試另一種方式
            from stages.data_integration_processor import Stage5IntegrationProcessor
            
            stage5 = Stage5IntegrationProcessor(
                input_dir='/app/data',
                output_dir='/app/data/data_integration_outputs'
            )
            # 使用timeseries_data參數
            results['stage5'] = stage5.process_data_integration(
                timeseries_data=results['stage4'],
                save_output=True
            )
        
        if not results['stage5']:
            print('❌ 階段五失敗')
            return False
            
        integrated_count = results['stage5'].get('metadata', {}).get('total_satellites', 0)
        print(f'✅ 階段五完成: {integrated_count} 顆衛星整合')
        
        # 階段六：動態池規劃
        print('\n🎯 階段六：動態池規劃')
        print('-' * 60)
        
        from stages.enhanced_dynamic_pool_planner import EnhancedDynamicPoolPlanner
        
        stage6 = EnhancedDynamicPoolPlanner(
            input_dir='/app/data',
            output_dir='/app/data/dynamic_pool_planning_outputs'
        )
        
        # 使用process_dynamic_pool_planning方法
        results['stage6'] = stage6.process_dynamic_pool_planning(
            integrated_data=results['stage5'],
            save_output=True
        )
        
        if not results['stage6']:
            print('❌ 階段六失敗')
            return False
            
        # 提取最終結果
        pool_data = results['stage6'].get('dynamic_satellite_pool', {})
        total_selected = pool_data.get('total_selected', 0)
        starlink_count = len(pool_data.get('starlink_satellites', []))
        oneweb_count = len(pool_data.get('oneweb_satellites', []))
        
        print(f'✅ 階段六完成: 總計 {total_selected} 顆衛星')
        print(f'   - Starlink: {starlink_count} 顆')
        print(f'   - OneWeb: {oneweb_count} 顆')
        
        # 生成最終報告
        elapsed_time = time.time() - start_time
        print('\n' + '=' * 80)
        print('📊 階段4-6處理完成總結')
        print('=' * 80)
        print(f'✅ 階段4-6成功完成！')
        print(f'⏱️ 總耗時: {elapsed_time:.2f} 秒 ({elapsed_time/60:.2f} 分鐘)')
        print(f'📊 數據流程:')
        print(f'   Stage 3: {stage3_satellites} 顆衛星（已有）')
        print(f'   Stage 4: {ts_count} 顆衛星時間序列')
        print(f'   Stage 5: {integrated_count} 顆衛星整合')
        print(f'   Stage 6: {total_selected} 顆衛星最終選擇')
        print('=' * 80)
        
        # 保存最終報告
        final_report = {
            'execution_time': datetime.now(timezone.utc).isoformat(),
            'processing_time_seconds': elapsed_time,
            'stages_completed': 3,  # 階段4-6
            'pipeline_summary': {
                'stage3_loaded': stage3_satellites,
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
        
        report_path = '/app/data/leo_optimization_stages_4_to_6_report.json'
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(final_report, f, indent=2, ensure_ascii=False)
        
        print(f'\n✅ 階段4-6報告已保存: {report_path}')
        
        return True
        
    except Exception as e:
        print(f'\n❌ 發生錯誤: {e}')
        import traceback
        traceback.print_exc()
        return False

def main():
    """主程序入口"""
    success = run_stages_4_to_6()
    
    if success:
        return 0
    else:
        return 1

if __name__ == '__main__':
    sys.exit(main())