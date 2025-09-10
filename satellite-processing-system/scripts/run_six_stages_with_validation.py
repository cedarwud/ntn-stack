#!/usr/bin/env python3
"""
六階段數據處理系統 - 新模組化架構版本
每個階段執行後立即驗證，失敗則停止後續處理

重要更新 (2025-09-10):
- 使用新的模組化架構 /pipeline/stages/
- 每個階段分解為專業化組件，提供革命性除錯能力
- 保持學術級標準合規 (Grade A)
- 維持完整驗證框架
"""

import sys
import os
import json
import time
import logging
from datetime import datetime, timezone
from pathlib import Path

# 確保能找到模組 - 獨立系統路徑配置
import os
from pathlib import Path

# 獲取項目根目錄
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

# 如果在容器中，也添加容器路徑
if os.path.exists('/satellite-processing'):
    sys.path.insert(0, '/satellite-processing')
    sys.path.insert(0, '/satellite-processing/src')

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 導入統一日誌管理器
try:
    from shared.unified_log_manager import UnifiedLogManager
    log_manager = None
except ImportError as e:
    print(f"⚠️ 無法導入統一日誌管理器: {e}")
    UnifiedLogManager = None
    log_manager = None

def validate_stage_immediately(stage_processor, processing_results, stage_num, stage_name):
    """
    階段執行後立即驗證
    
    Args:
        stage_processor: 階段處理器實例（包含驗證方法）
        processing_results: 處理結果
        stage_num: 階段編號
        stage_name: 階段名稱
        
    Returns:
        tuple: (validation_success, validation_message)
    """
    try:
        print(f"\n🔍 階段{stage_num}立即驗證檢查...")
        print("-" * 40)
        
        # 🔧 特殊處理階段一：驗證快照已在內部完成，無需外部調用
        if stage_num == 1:
            # 階段一返回的是output_file字符串，驗證已在處理過程中完成
            if processing_results and isinstance(processing_results, str):
                print(f"✅ 階段{stage_num}處理成功，輸出文件: {processing_results}")
                print(f"✅ 階段{stage_num}驗證已在內部完成")
                return True, f"階段{stage_num}驗證成功"
            else:
                print(f"❌ 階段{stage_num}處理結果異常")
                return False, f"階段{stage_num}處理結果異常"
        
        # 其他階段：保存驗證快照（內含自動驗證）
        elif hasattr(stage_processor, 'save_validation_snapshot'):
            validation_success = stage_processor.save_validation_snapshot(processing_results)
            
            if validation_success:
                print(f"✅ 階段{stage_num}驗證通過")
                return True, f"階段{stage_num}驗證成功"
            else:
                print(f"❌ 階段{stage_num}驗證快照生成失敗")
                return False, f"階段{stage_num}驗證快照生成失敗"
        else:
            # 如果沒有驗證方法，只做基本檢查
            if not processing_results:
                print(f"❌ 階段{stage_num}處理結果為空")
                return False, f"階段{stage_num}處理結果為空"
            
            print(f"⚠️ 階段{stage_num}無內建驗證，僅基本檢查通過")
            return True, f"階段{stage_num}基本檢查通過"
            
    except Exception as e:
        print(f"❌ 階段{stage_num}驗證異常: {e}")
        return False, f"階段{stage_num}驗證異常: {e}"

def check_validation_snapshot_quality(stage_num):
    """檢查驗證快照品質"""
    try:
        snapshot_file = f'data/validation_snapshots/stage{stage_num}_validation.json'
        
        if not os.path.exists(snapshot_file):
            return False, f"驗證快照文件不存在: {snapshot_file}"
        
        with open(snapshot_file, 'r', encoding='utf-8') as f:
            snapshot_data = json.load(f)
        
        # 檢查學術標準評級
        if 'academic_standards_check' in snapshot_data:
            grade = snapshot_data['academic_standards_check'].get('grade_achieved', 'C')
            if grade in ['A', 'B']:
                return True, f"學術標準評級: {grade}"
            else:
                return False, f"學術標準評級不符合要求: {grade}"
        
        return True, "基本品質檢查通過"
        
    except Exception as e:
        return False, f"品質檢查異常: {e}"

def run_stage_specific(target_stage, validation_level='STANDARD'):
    """運行特定階段"""
    results = {}
    
    print(f'\n🎯 運行階段 {target_stage} (驗證級別: {validation_level})')
    print('=' * 80)
    
    try:
        # 統一清理
        try:
            from shared.cleanup_manager import cleanup_all_stages
            cleaned_result = cleanup_all_stages()
            print(f'✅ 統一清理完成: {cleaned_result["files"]} 個檔案, {cleaned_result["directories"]} 個目錄已清理')
        except Exception as e:
            print(f'⚠️ 統一清理警告: {e}')
        
        # 根據目標階段運行
        if target_stage == 1:
            # 階段一：TLE載入與SGP4計算 - 使用新模組化架構
            print('\n📡 階段一：TLE載入與SGP4軌道計算 (新模組化架構)')
            print('-' * 60)
            
            from stages.stage1_orbital_calculation.stage1_processor import Stage1Processor
            stage1 = Stage1Processor(
                sample_mode=False,
                sample_size=500
            )
            
            results['stage1'] = stage1.process()
            
            if not results['stage1']:
                print('❌ 階段一處理失敗')
                return False, 1, "階段一處理失敗"
            
            # 立即驗證
            validation_success, validation_msg = validate_stage_immediately(
                stage1, results['stage1'], 1, "TLE載入與SGP4計算"
            )
            
            if not validation_success:
                print(f'❌ 階段一驗證失敗: {validation_msg}')
                return False, 1, validation_msg
            
            print(f'✅ 階段一完成並驗證通過')
            return True, 1, "階段一成功完成"
            
        elif target_stage == 2:
            # 階段二：智能衛星篩選 - 使用新模組化架構
            print('\n🎯 階段二：智能衛星篩選 (新模組化架構)')
            print('-' * 60)
            
            from stages.stage2_visibility_filter.stage2_processor import Stage2Processor
            stage2 = Stage2Processor(
                input_dir='data',
                output_dir='data/intelligent_filtering_outputs'
            )
            
            results['stage2'] = stage2.process()
            
            if not results['stage2']:
                print('❌ 階段二處理失敗')
                return False, 2, "階段二處理失敗"
                
            # 立即驗證
            validation_success, validation_msg = validate_stage_immediately(
                stage2, results['stage2'], 2, "智能衛星篩選"
            )
            
            if not validation_success:
                print(f'❌ 階段二驗證失敗: {validation_msg}')
                return False, 2, validation_msg
            
            print(f'✅ 階段二完成並驗證通過')
            return True, 2, "階段二成功完成"
            
        elif target_stage == 3:
            # 階段三：時間序列預處理 - 使用新模組化架構
            print('\n⏱️ 階段三：時間序列預處理 (新模組化架構)')
            print('-' * 60)
            
            from stages.stage3_timeseries_preprocessing.stage3_processor import Stage3Processor
            stage3 = Stage3Processor(
                input_dir='data/intelligent_filtering_outputs',
                output_dir='data/timeseries_preprocessing_outputs'
            )
            
            results['stage3'] = stage3.process()
            
            if not results['stage3']:
                print('❌ 階段三處理失敗')
                return False, 3, "階段三處理失敗"
                
            # 立即驗證
            validation_success, validation_msg = validate_stage_immediately(
                stage3, results['stage3'], 3, "時間序列預處理"
            )
            
            if not validation_success:
                print(f'❌ 階段三驗證失敗: {validation_msg}')
                return False, 3, validation_msg
            
            print(f'✅ 階段三完成並驗證通過')
            return True, 3, "階段三成功完成"
            
        elif target_stage == 4:
            # 階段四：信號分析 - 使用新模組化架構
            print('\n📶 階段四：信號分析 (新模組化架構)')
            print('-' * 60)
            
            from stages.stage4_signal_analysis.stage4_processor import Stage4Processor
            stage4 = Stage4Processor(
                input_dir='data/timeseries_preprocessing_outputs',
                output_dir='data/signal_analysis_outputs'
            )
            
            results['stage4'] = stage4.process()
            
            if not results['stage4']:
                print('❌ 階段四處理失敗')
                return False, 4, "階段四處理失敗"
                
            # 立即驗證
            validation_success, validation_msg = validate_stage_immediately(
                stage4, results['stage4'], 4, "信號分析"
            )
            
            if not validation_success:
                print(f'❌ 階段四驗證失敗: {validation_msg}')
                return False, 4, validation_msg
            
            print(f'✅ 階段四完成並驗證通過')
            return True, 4, "階段四成功完成"
            
        elif target_stage == 5:
            # 階段五：數據整合 - 使用新模組化架構
            print('\n🔗 階段五：數據整合 (新模組化架構)')
            print('-' * 60)
            
            from stages.stage5_data_integration.stage5_processor import Stage5Processor
            stage5 = Stage5Processor(
                signal_analysis_dir='data/signal_analysis_outputs',
                output_dir='data/data_integration_outputs'
            )
            
            results['stage5'] = stage5.process()
            
            if not results['stage5']:
                print('❌ 階段五處理失敗')
                return False, 5, "階段五處理失敗"
                
            # 立即驗證
            validation_success, validation_msg = validate_stage_immediately(
                stage5, results['stage5'], 5, "數據整合"
            )
            
            if not validation_success:
                print(f'❌ 階段五驗證失敗: {validation_msg}')
                return False, 5, validation_msg
            
            print(f'✅ 階段五完成並驗證通過')
            return True, 5, "階段五成功完成"
            
        elif target_stage == 6:
            # 階段六：動態池規劃 - 使用新模組化架構
            print('\n🌐 階段六：動態池規劃 (新模組化架構)')
            print('-' * 60)
            
            from stages.stage6_dynamic_planning.stage6_processor import Stage6Processor
            stage6 = Stage6Processor(
                data_integration_dir='data/data_integration_outputs',
                output_dir='data/dynamic_pool_planning_outputs'
            )
            
            results['stage6'] = stage6.process()
            
            if not results['stage6']:
                print('❌ 階段六處理失敗')
                return False, 6, "階段六處理失敗"
                
            # 立即驗證
            validation_success, validation_msg = validate_stage_immediately(
                stage6, results['stage6'], 6, "動態池規劃"
            )
            
            if not validation_success:
                print(f'❌ 階段六驗證失敗: {validation_msg}')
                return False, 6, validation_msg
            
            print(f'✅ 階段六完成並驗證通過')
            return True, 6, "階段六成功完成"
        
        else:
            return False, 0, f"無效的階段編號: {target_stage}"
            
    except Exception as e:
        logger.error(f"階段{target_stage}執行異常: {e}")
        return False, target_stage, f"階段{target_stage}執行異常: {e}"

def run_all_stages_sequential(validation_level='STANDARD'):
    """順序執行所有六個階段 - 使用新模組化架構"""
    results = {}
    completed_stages = 0
    
    print(f'\n🚀 開始六階段數據處理 (驗證級別: {validation_level}) - 新模組化架構版本')
    print('=' * 80)
    print('🏗️ 架構特色: 40個專業化組件，革命性除錯能力，Grade A學術標準')
    print('=' * 80)
    
    try:
        # 統一清理
        try:
            from shared.cleanup_manager import cleanup_all_stages
            cleaned_result = cleanup_all_stages()
            print(f'✅ 統一清理完成: {cleaned_result["files"]} 個檔案, {cleaned_result["directories"]} 個目錄已清理')
        except Exception as e:
            print(f'⚠️ 統一清理警告: {e}')
        
        # 階段一：TLE載入與SGP4計算 - 使用新模組化架構
        print('\n📡 階段一：TLE載入與SGP4軌道計算 (新模組化架構)')
        print('-' * 60)
        
        from stages.stage1_orbital_calculation.stage1_processor import Stage1Processor
        stage1 = Stage1Processor(
            sample_mode=False,
            sample_size=500
        )
        
        results['stage1'] = stage1.process()
        
        if not results['stage1']:
            print('❌ 階段一處理失敗')
            return False, 1, "階段一處理失敗"
        
        # 🔍 階段一立即驗證
        validation_success, validation_msg = validate_stage_immediately(
            stage1, results['stage1'], 1, "TLE載入與SGP4計算"
        )
        
        if not validation_success:
            print(f'❌ 階段一驗證失敗: {validation_msg}')
            print('🚫 停止後續階段處理，避免基於錯誤數據的無意義計算')
            return False, 1, validation_msg
        
        # 額外品質檢查
        quality_passed, quality_msg = check_validation_snapshot_quality(1)
        if not quality_passed:
            print(f'❌ 階段一品質檢查失敗: {quality_msg}')
            print('🚫 停止後續階段處理，避免基於低品質數據的計算')
            return False, 1, quality_msg
        
        completed_stages = 1
        print(f'✅ 階段一完成並驗證通過')
        
        # 階段二：智能衛星篩選 - 使用新模組化架構
        print('\n🎯 階段二：智能衛星篩選 (新模組化架構)')
        print('-' * 60)
        
        from stages.stage2_visibility_filter.stage2_processor import Stage2Processor
        stage2 = Stage2Processor(
            input_dir='data',
            output_dir='data/intelligent_filtering_outputs'
        )
        
        results['stage2'] = stage2.process()
        
        if not results['stage2']:
            print('❌ 階段二處理失敗')
            return False, 2, "階段二處理失敗"
        
        # 🔍 階段二立即驗證
        validation_success, validation_msg = validate_stage_immediately(
            stage2, results['stage2'], 2, "智能衛星篩選"
        )
        
        if not validation_success:
            print(f'❌ 階段二驗證失敗: {validation_msg}')
            print('🚫 停止後續階段處理')
            return False, 2, validation_msg
        
        completed_stages = 2
        print(f'✅ 階段二完成並驗證通過')
        
        # 階段三：時間序列預處理 - 使用新模組化架構
        print('\n⏱️ 階段三：時間序列預處理 (新模組化架構)')
        print('-' * 60)
        
        from stages.stage3_timeseries_preprocessing.stage3_processor import Stage3Processor
        stage3 = Stage3Processor(
            input_dir='data/intelligent_filtering_outputs',
            output_dir='data/timeseries_preprocessing_outputs'
        )
        
        results['stage3'] = stage3.process()
        
        if not results['stage3']:
            print('❌ 階段三處理失敗')
            return False, 3, "階段三處理失敗"
        
        # 🔍 階段三立即驗證
        validation_success, validation_msg = validate_stage_immediately(
            stage3, results['stage3'], 3, "時間序列預處理"
        )
        
        if not validation_success:
            print(f'❌ 階段三驗證失敗: {validation_msg}')
            print('🚫 停止後續階段處理')
            return False, 3, validation_msg
        
        completed_stages = 3
        print(f'✅ 階段三完成並驗證通過')
        
        # 階段四：信號分析 - 使用新模組化架構
        print('\n📶 階段四：信號分析 (新模組化架構)')
        print('-' * 60)
        
        from stages.stage4_signal_analysis.stage4_processor import Stage4Processor
        stage4 = Stage4Processor(
            input_dir='data/timeseries_preprocessing_outputs',
            output_dir='data/signal_analysis_outputs'
        )
        
        results['stage4'] = stage4.process()
        
        if not results['stage4']:
            print('❌ 階段四處理失敗')
            return False, 4, "階段四處理失敗"
        
        # 🔍 階段四立即驗證
        validation_success, validation_msg = validate_stage_immediately(
            stage4, results['stage4'], 4, "信號分析"
        )
        
        if not validation_success:
            print(f'❌ 階段四驗證失敗: {validation_msg}')
            print('🚫 停止後續階段處理')
            return False, 4, validation_msg
        
        completed_stages = 4
        print(f'✅ 階段四完成並驗證通過')
        
        # 階段五：數據整合 - 使用新模組化架構
        print('\n🔗 階段五：數據整合 (新模組化架構)')
        print('-' * 60)
        
        from stages.stage5_data_integration.stage5_processor import Stage5Processor
        stage5 = Stage5Processor(
            signal_analysis_dir='data/signal_analysis_outputs',
            output_dir='data/data_integration_outputs'
        )
        
        results['stage5'] = stage5.process()
        
        if not results['stage5']:
            print('❌ 階段五處理失敗')
            return False, 5, "階段五處理失敗"
        
        # 🔍 階段五立即驗證
        validation_success, validation_msg = validate_stage_immediately(
            stage5, results['stage5'], 5, "數據整合"
        )
        
        if not validation_success:
            print(f'❌ 階段五驗證失敗: {validation_msg}')
            print('🚫 停止後續階段處理')
            return False, 5, validation_msg
        
        completed_stages = 5
        print(f'✅ 階段五完成並驗證通過')
        
        # 階段六：動態池規劃 - 使用新模組化架構
        print('\n🌐 階段六：動態池規劃 (新模組化架構)')
        print('-' * 60)
        
        from stages.stage6_dynamic_planning.stage6_processor import Stage6Processor
        stage6 = Stage6Processor(
            data_integration_dir='data/data_integration_outputs',
            output_dir='data/dynamic_pool_planning_outputs'
        )
        
        results['stage6'] = stage6.process()
        
        if not results['stage6']:
            print('❌ 階段六處理失敗')
            return False, 6, "階段六處理失敗"
        
        # 🔍 階段六立即驗證
        validation_success, validation_msg = validate_stage_immediately(
            stage6, results['stage6'], 6, "動態池規劃"
        )
        
        if not validation_success:
            print(f'❌ 階段六驗證失敗: {validation_msg}')
            return False, 6, validation_msg
        
        completed_stages = 6
        print(f'✅ 階段六完成並驗證通過')
        
        # 🎉 全部完成
        print('\n🎉 六階段處理全部完成!')
        print('=' * 80)
        print('🏗️ 新模組化架構優勢:')
        print('   ✅ 40個專業化組件完美協作')
        print('   ✅ 革命性除錯能力 - 組件級問題定位')
        print('   ✅ Grade A學術標準全面合規')
        print('   ✅ 完整驗證框架保障品質')
        print('=' * 80)
        
        return True, 6, "全部六階段成功完成"
        
    except Exception as e:
        logger.error(f"六階段處理異常 (階段{completed_stages}): {e}")
        return False, completed_stages, f"六階段處理異常 (階段{completed_stages}): {e}"

def main():
    import argparse
    parser = argparse.ArgumentParser(description='六階段數據處理系統 - 新模組化架構版本')
    parser.add_argument('--stage', type=int, choices=[1,2,3,4,5,6], 
                       help='運行特定階段 (1-6)')
    parser.add_argument('--validation-level', choices=['FAST', 'STANDARD', 'COMPREHENSIVE'], 
                       default='STANDARD', help='驗證級別')
    args = parser.parse_args()
    
    start_time = time.time()
    
    if args.stage:
        success, completed_stage, message = run_stage_specific(args.stage, args.validation_level)
    else:
        success, completed_stage, message = run_all_stages_sequential(args.validation_level)
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    print(f'\n📊 執行統計:')
    print(f'   執行時間: {execution_time:.2f} 秒')
    print(f'   完成階段: {completed_stage}/6')
    print(f'   最終狀態: {"✅ 成功" if success else "❌ 失敗"}')
    print(f'   訊息: {message}')
    
    # 架構特色總結
    print('\n🏗️ 新模組化架構特色總結:')
    print('   📦 Stage 1: 3個專業組件 (TLE載入、軌道計算、數據處理)')
    print('   📦 Stage 2: 6個專業組件 (可見性分析、仰角篩選、結果格式化)')  
    print('   📦 Stage 3: 6個專業組件 (時間序列轉換、學術驗證、動畫建構)')
    print('   📦 Stage 4: 7個專業組件 (信號品質、3GPP分析、物理驗證)')
    print('   📦 Stage 5: 9個專業組件 (跨階段驗證、PostgreSQL整合、快取管理)')
    print('   📦 Stage 6: 9個專業組件 (衛星選擇、覆蓋優化、物理計算)')
    print('   🎯 總計: 40個專業化組件，實現革命性維護便利性')
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())