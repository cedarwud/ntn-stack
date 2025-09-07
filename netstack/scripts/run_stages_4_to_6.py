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
            output_dir='/app/data'
        )
        
        # Stage 4 loads from file, specify correct path
        results['stage4'] = stage4.process_timeseries_preprocessing(
            signal_file='/app/data/signal_event_analysis_output.json',
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
                input_enhanced_timeseries_dir='/app/data/timeseries_preprocessing_outputs',
                output_data_integration_dir='/app/data',
                elevation_thresholds=[5, 10, 15]
            )
            
            stage5 = Stage5IntegrationProcessor(stage5_config)
            # 使用enhanced_data參數（根據原始程式碼）
            import asyncio
            results['stage5'] = asyncio.run(stage5.process_enhanced_timeseries())
        except ImportError:
            # 如果上面的導入失敗，嘗試另一種方式
            from stages.data_integration_processor import Stage5IntegrationProcessor
            
            stage5 = Stage5IntegrationProcessor(
                input_dir='/app/data',
                output_dir='/app/data'
            )
            # 使用timeseries_data參數
            import asyncio
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
        
        # 🔧 修復：使用正確的config字典構造方式
        stage6_config = {
            'input_dir': '/app/data',
            'output_dir': '/app/data',
            'save_pool_data': True,
            'save_optimization_results': True
        }
        stage6 = EnhancedDynamicPoolPlanner(stage6_config)
        
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
        print(f'⏱️  總處理時間: {elapsed_time:.2f}秒')
        print(f'📊 最終結果:')
        print(f'   - 階段4: {ts_count} 顆衛星時間序列轉換')
        print(f'   - 階段5: {integrated_count} 顆衛星數據整合')
        print(f'   - 階段6: {total_selected} 顆衛星動態池規劃')
        
        print('\n🎯 後續可執行動作:')
        print('   1. 檢查驗證快照: ls -la /app/data/validation_snapshots/')
        print('   2. 查看池規劃結果: cat /app/data/stage6_dynamic_pool_output.json')
        print('   3. SimWorld可視化: 檢查 /home/sat/ntn-stack/data/simworld_outputs/')
        
        return True
        
    except Exception as e:
        logger.exception(f'階段4-6處理時發生錯誤: {e}')
        print(f'❌ 處理失敗: {e}')
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