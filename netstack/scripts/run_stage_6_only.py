#!/usr/bin/env python3
"""
只執行階段六，使用現有的階段五輸出檔案
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

def run_stage_6_only():
    """執行階段6的處理流程（檔案模式）"""
    
    print('🚀 六階段數據處理系統 - 僅階段6 (檔案模式)')
    print('=' * 80)
    print(f'開始時間: {datetime.now(timezone.utc).isoformat()}')
    print('=' * 80)
    
    start_time = time.time()
    
    try:
        # 檢查階段五的輸出文件
        print('\n📥 檢查階段五輸出數據')
        print('-' * 60)
        
        stage5_file = '/app/data/data_integration_outputs/data_integration_output.json'
        
        if not Path(stage5_file).exists():
            print(f'❌ 階段五輸出文件不存在: {stage5_file}')
            return False
        
        # 檢查文件大小
        file_size = Path(stage5_file).stat().st_size / (1024 * 1024)  # MB
        print(f'✅ 階段五數據文件確認: {file_size:.1f} MB')
        
        # 驗證文件內容
        with open(stage5_file, 'r', encoding='utf-8') as f:
            stage5_data = json.load(f)
        
        total_satellites = stage5_data.get('total_satellites', 0)
        print(f'✅ 階段五數據載入: {total_satellites} 顆衛星')
        
        # 階段六：動態池規劃（檔案模式）
        print('\n🎯 階段六：動態池規劃（檔案模式）')
        print('-' * 60)
        
        from stages.enhanced_dynamic_pool_planner import EnhancedDynamicPoolPlanner
        
        # EnhancedDynamicPoolPlanner expects a config dict
        stage6_config = {
            'input_dir': '/app/data/data_integration_outputs',
            'output_dir': '/app/data/dynamic_pool_planning_outputs'
        }
        stage6 = EnhancedDynamicPoolPlanner(stage6_config)
        
        # 使用檔案模式 - 傳入input_file參數
        output_file = '/app/data/dynamic_pool_planning_outputs/enhanced_dynamic_pools_output.json'
        results = stage6.process(
            input_file=stage5_file,  # 使用檔案模式
            input_data=None,         # 不使用記憶體模式
            output_file=output_file
        )
        
        if not results or not results.get('success', False):
            print('❌ 階段六失敗')
            print(f'錯誤信息: {results.get("error", "未知錯誤")}')
            return False
            
        # 提取最終結果
        if 'dynamic_satellite_pool' in results:
            pool_data = results['dynamic_satellite_pool']
        elif 'satellite_pool' in results:
            pool_data = results['satellite_pool'] 
        elif 'selected_satellites' in results:
            pool_data = {'selected_satellites': results['selected_satellites']}
        else:
            pool_data = results
            
        # 嘗試不同的計數方式
        total_selected = 0
        starlink_count = 0
        oneweb_count = 0
        
        if 'total_selected' in pool_data:
            total_selected = pool_data['total_selected']
            starlink_count = len(pool_data.get('starlink_satellites', []))
            oneweb_count = len(pool_data.get('oneweb_satellites', []))
        elif 'selected_satellites' in pool_data:
            all_satellites = pool_data['selected_satellites']
            total_selected = len(all_satellites)
            # 按星座分類計數
            for sat in all_satellites:
                constellation = sat.get('constellation', '').lower()
                if 'starlink' in constellation:
                    starlink_count += 1
                elif 'oneweb' in constellation:
                    oneweb_count += 1
        elif 'starlink' in pool_data and 'oneweb' in pool_data:
            starlink_sats = pool_data.get('starlink', {}).get('satellites', [])
            oneweb_sats = pool_data.get('oneweb', {}).get('satellites', [])
            starlink_count = len(starlink_sats)
            oneweb_count = len(oneweb_sats)
            total_selected = starlink_count + oneweb_count
        else:
            # 嘗試從結果中找到衛星計數
            for key in results.keys():
                if 'satellite' in key.lower() and isinstance(results[key], (list, dict)):
                    if isinstance(results[key], list):
                        total_selected = len(results[key])
                    elif isinstance(results[key], dict) and 'satellites' in results[key]:
                        total_selected = len(results[key]['satellites'])
                    break
        
        print(f'✅ 階段六完成: 總計 {total_selected} 顆衛星')
        print(f'   - Starlink: {starlink_count} 顆')
        print(f'   - OneWeb: {oneweb_count} 顆')
        
        # 生成最終報告
        elapsed_time = time.time() - start_time
        print('\n' + '=' * 80)
        print('📊 階段6處理完成總結')
        print('=' * 80)
        print(f'✅ 階段6成功完成！')
        print(f'⏱️ 總耗時: {elapsed_time:.2f} 秒')
        print(f'📊 數據流程:')
        print(f'   Stage 5: {total_satellites} 顆衛星（已有）')
        print(f'   Stage 6: {total_selected} 顆衛星最終選擇')
        print(f'📋 最終衛星池組成:')
        print(f'   - Starlink: {starlink_count} 顆衛星')  
        print(f'   - OneWeb: {oneweb_count} 顆衛星')
        
        # 驗證是否達到預期目標
        expected_total = 156
        expected_starlink = 120
        expected_oneweb = 36
        
        if total_selected >= expected_total:
            print(f'\n🎯 ✅ 目標達成！實際選擇 {total_selected} 顆衛星 ≥ 預期 {expected_total} 顆')
        else:
            print(f'\n⚠️ 目標部分達成：實際選擇 {total_selected} 顆衛星 < 預期 {expected_total} 顆')
        
        print(f'\n📊 與預期對比:')
        print(f'   - 總計: {total_selected}/{expected_total} ({total_selected/expected_total*100:.1f}%)')
        if starlink_count > 0:
            print(f'   - Starlink: {starlink_count}/{expected_starlink} ({starlink_count/expected_starlink*100:.1f}%)')
        if oneweb_count > 0:
            print(f'   - OneWeb: {oneweb_count}/{expected_oneweb} ({oneweb_count/expected_oneweb*100:.1f}%)')
        print('=' * 80)
        
        # 保存最終報告
        final_report = {
            'execution_time': datetime.now(timezone.utc).isoformat(),
            'processing_time_seconds': elapsed_time,
            'stage_completed': 6,
            'pipeline_summary': {
                'stage5_loaded': total_satellites,
                'stage6_selected': total_selected
            },
            'final_satellite_pool': {
                'total': total_selected,
                'starlink': starlink_count,
                'oneweb': oneweb_count
            },
            'target_comparison': {
                'expected_total': expected_total,
                'expected_starlink': expected_starlink,
                'expected_oneweb': expected_oneweb,
                'actual_total': total_selected,
                'actual_starlink': starlink_count,
                'actual_oneweb': oneweb_count,
                'target_achieved': total_selected >= expected_total
            },
            'success': True,
            'processing_mode': 'file_mode'
        }
        
        report_path = '/app/data/leo_optimization_stage_6_final_report.json'
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(final_report, f, indent=2, ensure_ascii=False)
        
        print(f'\n✅ 階段6最終報告已保存: {report_path}')
        
        return True
        
    except Exception as e:
        print(f'\n❌ 發生錯誤: {e}')
        import traceback
        traceback.print_exc()
        return False

def main():
    """主程序入口"""
    success = run_stage_6_only()
    
    if success:
        return 0
    else:
        return 1

if __name__ == '__main__':
    sys.exit(main())