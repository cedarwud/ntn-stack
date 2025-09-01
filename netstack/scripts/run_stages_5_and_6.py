#!/usr/bin/env python3
"""
執行階段五和階段六
使用現有的階段四輸出數據
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

def run_stages_5_and_6():
    """執行階段5和階段6的處理流程"""
    
    print('🚀 六階段數據處理系統 - 階段5和6 (修復版)')
    print('=' * 80)
    print(f'開始時間: {datetime.now(timezone.utc).isoformat()}')
    print('=' * 80)
    
    results = {}
    start_time = time.time()
    
    try:
        # 檢查階段四的輸出文件
        print('\n📥 檢查階段四輸出數據')
        print('-' * 60)
        
        starlink_file = '/app/data/timeseries_preprocessing_outputs/starlink_enhanced.json'
        oneweb_file = '/app/data/timeseries_preprocessing_outputs/oneweb_enhanced.json'
        stats_file = '/app/data/timeseries_preprocessing_outputs/conversion_statistics.json'
        
        if not Path(starlink_file).exists():
            print(f'❌ Starlink 增強文件不存在: {starlink_file}')
            return False
            
        if not Path(oneweb_file).exists():
            print(f'❌ OneWeb 增強文件不存在: {oneweb_file}')
            return False
            
        # 載入統計信息
        with open(stats_file, 'r', encoding='utf-8') as f:
            stats = json.load(f)
        
        total_satellites = stats.get('successful_conversions', 0)
        print(f'✅ 階段四數據確認: {total_satellites} 顆衛星時間序列')
        
        # 構建階段四結果結構
        results['stage4'] = {
            'success': True,
            'conversion_statistics': stats,
            'output_files': {
                'starlink': starlink_file,
                'oneweb': oneweb_file
            }
        }
        
        # 階段五：數據整合
        print('\n🔄 階段五：數據整合')
        print('-' * 60)
        
        # 嘗試導入階段五處理器
        try:
            from stages.data_integration_processor import Stage5IntegrationProcessor, Stage5Config
            
            # 創建配置
            stage5_config = Stage5Config(
                input_enhanced_timeseries_dir='/app/data/timeseries_preprocessing_outputs',
                output_data_integration_dir='/app/data/data_integration_outputs',
                elevation_thresholds=[5, 10, 15]
            )
            
            stage5 = Stage5IntegrationProcessor(stage5_config)
            
            # 使用正確的方法名 (async method)
            import asyncio
            results['stage5'] = asyncio.run(stage5.process_enhanced_timeseries())
                
        except ImportError as e:
            print(f'❌ 階段五導入失敗: {e}')
            # 嘗試另一種導入方式
            try:
                from stages.data_integration_processor import DataIntegrationProcessor
                stage5 = DataIntegrationProcessor(
                    input_dir='/app/data/timeseries_preprocessing_outputs',
                    output_dir='/app/data/data_integration_outputs'
                )
                results['stage5'] = stage5.process_data_integration(save_output=True)
            except ImportError as e2:
                print(f'❌ 所有階段五導入嘗試失敗: {e2}')
                return False
        
        if not results['stage5'] or not results['stage5'].get('success', False):
            print('❌ 階段五失敗')
            return False
            
        integrated_count = results['stage5'].get('total_satellites', 
                                               results['stage5'].get('metadata', {}).get('total_satellites', 0))
        print(f'✅ 階段五完成: {integrated_count} 顆衛星整合')
        
        # 階段六：動態池規劃
        print('\n🎯 階段六：動態池規劃')
        print('-' * 60)
        
        try:
            from stages.enhanced_dynamic_pool_planner import EnhancedDynamicPoolPlanner
            
            # EnhancedDynamicPoolPlanner expects a config dict
            stage6_config = {
                'input_dir': '/app/data/data_integration_outputs',
                'output_dir': '/app/data/dynamic_pool_planning_outputs'
            }
            stage6 = EnhancedDynamicPoolPlanner(stage6_config)
            
            # 使用正確的方法名和參數
            results['stage6'] = stage6.process(input_data=results['stage5'])
                
        except ImportError as e:
            print(f'❌ 階段六導入失敗: {e}')
            # 嘗試另一種導入方式
            try:
                from stages.dynamic_pool_planner import DynamicPoolPlanner
                stage6 = DynamicPoolPlanner(
                    input_dir='/app/data/data_integration_outputs',
                    output_dir='/app/data/dynamic_pool_planning_outputs'
                )
                results['stage6'] = stage6.process_dynamic_pool_planning(save_output=True)
            except ImportError as e2:
                print(f'❌ 所有階段六導入嘗試失敗: {e2}')
                return False
        
        if not results['stage6'] or not results['stage6'].get('success', False):
            print('❌ 階段六失敗')
            return False
            
        # 提取最終結果
        pool_data = results['stage6'].get('dynamic_satellite_pool', 
                                        results['stage6'].get('satellite_pool', {}))
        total_selected = pool_data.get('total_selected', 
                                     len(pool_data.get('selected_satellites', [])))
        starlink_satellites = pool_data.get('starlink_satellites', [])
        oneweb_satellites = pool_data.get('oneweb_satellites', [])
        
        starlink_count = len(starlink_satellites)
        oneweb_count = len(oneweb_satellites)
        
        print(f'✅ 階段六完成: 總計 {total_selected} 顆衛星')
        print(f'   - Starlink: {starlink_count} 顆')
        print(f'   - OneWeb: {oneweb_count} 顆')
        
        # 生成最終報告
        elapsed_time = time.time() - start_time
        print('\n' + '=' * 80)
        print('📊 階段5-6處理完成總結')
        print('=' * 80)
        print(f'✅ 階段5-6成功完成！')
        print(f'⏱️ 總耗時: {elapsed_time:.2f} 秒')
        print(f'📊 數據流程:')
        print(f'   Stage 4: {total_satellites} 顆衛星時間序列（已有）')
        print(f'   Stage 5: {integrated_count} 顆衛星整合')
        print(f'   Stage 6: {total_selected} 顆衛星最終選擇')
        print(f'📋 最終衛星池組成:')
        print(f'   - Starlink: {starlink_count} 顆衛星')  
        print(f'   - OneWeb: {oneweb_count} 顆衛星')
        print('=' * 80)
        
        # 保存最終報告
        final_report = {
            'execution_time': datetime.now(timezone.utc).isoformat(),
            'processing_time_seconds': elapsed_time,
            'stages_completed': 2,  # 階段5-6
            'pipeline_summary': {
                'stage4_loaded': total_satellites,
                'stage5_integrated': integrated_count,
                'stage6_selected': total_selected
            },
            'final_satellite_pool': {
                'total': total_selected,
                'starlink': starlink_count,
                'oneweb': oneweb_count
            },
            'constellation_breakdown': {
                'starlink_satellites': starlink_count,
                'oneweb_satellites': oneweb_count
            },
            'success': True,
            'target_achieved': total_selected >= 156,  # 預期目標
            'target_comparison': {
                'expected_total': 156,
                'expected_starlink': 120,
                'expected_oneweb': 36,
                'actual_total': total_selected,
                'actual_starlink': starlink_count,
                'actual_oneweb': oneweb_count
            }
        }
        
        report_path = '/app/data/leo_optimization_stages_5_and_6_report.json'
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(final_report, f, indent=2, ensure_ascii=False)
        
        print(f'\n✅ 階段5-6報告已保存: {report_path}')
        
        # 驗證是否達到預期目標
        if total_selected >= 156:
            print(f'\n🎯 ✅ 目標達成！實際選擇 {total_selected} 顆衛星 ≥ 預期 156 顆')
        else:
            print(f'\n⚠️ 目標未達成：實際選擇 {total_selected} 顆衛星 < 預期 156 顆')
        
        return True
        
    except Exception as e:
        print(f'\n❌ 發生錯誤: {e}')
        import traceback
        traceback.print_exc()
        return False

def main():
    """主程序入口"""
    success = run_stages_5_and_6()
    
    if success:
        return 0
    else:
        return 1

if __name__ == '__main__':
    sys.exit(main())