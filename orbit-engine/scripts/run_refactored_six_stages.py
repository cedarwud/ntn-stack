#!/usr/bin/env python3
"""
六階段數據處理系統 - 重構版本
使用新的共享模組架構和統一處理器接口

重構更新 (2025-09-21):
- 使用重構後的處理器架構
- 統一的 BaseProcessor 接口
- 共享監控、預測、驗證模組
- 簡化的數據流傳遞
- 標準化的錯誤處理

執行環境:
- 容器內執行: docker exec orbit-engine-dev python /app/scripts/run_refactored_six_stages.py
- 主機執行: cd orbit-engine-system && python scripts/run_refactored_six_stages.py
"""

import sys
import os
import json
import time
import logging
from datetime import datetime, timezone
from pathlib import Path

# 確保能找到模組
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

# 如果在容器中，也添加容器路徑
if os.path.exists('/orbit-engine'):
    sys.path.insert(0, '/orbit-engine')
    sys.path.insert(0, '/orbit-engine/src')

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def validate_processing_result(result, stage_name):
    """驗證處理結果"""
    if not result:
        return False, f"{stage_name}處理結果為空"

    if not hasattr(result, 'status'):
        return False, f"{stage_name}處理結果格式錯誤"

    from shared.interfaces import ProcessingStatus
    if result.status != ProcessingStatus.SUCCESS:
        error_message = result.metadata.get('message', '未知錯誤')
        return False, f"{stage_name}處理失敗: {error_message}"

    return True, f"{stage_name}處理成功"


def run_all_stages_sequential():
    """順序執行所有六個階段 - 重構版本"""
    print('\n🚀 開始六階段數據處理 - 重構版本')
    print('=' * 80)
    print('🏗️ 架構特色: 共享模組、統一接口、簡化維護')
    print('=' * 80)

    stage_results = {}

    try:
        # Stage 1: 數據載入層
        print('\n📡 Stage 1: 數據載入層處理器')
        print('-' * 60)

        from stages.stage1_orbital_calculation.stage1_data_loading_processor import create_stage1_processor
        stage1_processor = create_stage1_processor()

        stage1_result = stage1_processor.process(None)
        validation_success, validation_msg = validate_processing_result(stage1_result, "Stage 1")

        if not validation_success:
            print(f'❌ Stage 1失敗: {validation_msg}')
            return False, 1, validation_msg

        stage_results['stage1'] = stage1_result.data
        print(f'✅ Stage 1完成: {validation_msg}')

        # Stage 2: 軌道計算層
        print('\n🎯 Stage 2: 軌道計算層處理器')
        print('-' * 60)

        from stages.stage2_visibility_filter.stage2_orbital_computing_processor import create_stage2_processor
        stage2_processor = create_stage2_processor()

        stage2_result = stage2_processor.process(stage1_result.data)
        validation_success, validation_msg = validate_processing_result(stage2_result, "Stage 2")

        if not validation_success:
            print(f'❌ Stage 2失敗: {validation_msg}')
            return False, 2, validation_msg

        stage_results['stage2'] = stage2_result.data
        print(f'✅ Stage 2完成: {validation_msg}')

        # Stage 3: 信號分析層
        print('\n📶 Stage 3: 信號分析層處理器')
        print('-' * 60)

        from stages.stage3_signal_analysis.stage3_signal_analysis_processor import create_stage3_processor
        stage3_processor = create_stage3_processor()

        stage3_result = stage3_processor.process(stage2_result.data)
        validation_success, validation_msg = validate_processing_result(stage3_result, "Stage 3")

        if not validation_success:
            print(f'❌ Stage 3失敗: {validation_msg}')
            return False, 3, validation_msg

        stage_results['stage3'] = stage3_result.data
        print(f'✅ Stage 3完成: {validation_msg}')

        # Stage 4: 優化決策層
        print('\n⏱️ Stage 4: 優化決策層處理器')
        print('-' * 60)

        from stages.stage4_timeseries_preprocessing.timeseries_preprocessing_processor import create_stage4_processor
        stage4_processor = create_stage4_processor()

        stage4_result = stage4_processor.process(stage3_result.data)
        validation_success, validation_msg = validate_processing_result(stage4_result, "Stage 4")

        if not validation_success:
            print(f'❌ Stage 4失敗: {validation_msg}')
            return False, 4, validation_msg

        stage_results['stage4'] = stage4_result.data
        print(f'✅ Stage 4完成: {validation_msg}')

        # Stage 5: 數據整合層
        print('\n🔗 Stage 5: 數據整合層處理器')
        print('-' * 60)

        from stages.stage5_data_integration.data_integration_processor import create_stage5_processor
        stage5_processor = create_stage5_processor()

        stage5_result = stage5_processor.process(stage4_result.data)
        validation_success, validation_msg = validate_processing_result(stage5_result, "Stage 5")

        if not validation_success:
            print(f'❌ Stage 5失敗: {validation_msg}')
            return False, 5, validation_msg

        stage_results['stage5'] = stage5_result.data
        print(f'✅ Stage 5完成: {validation_msg}')

        # Stage 6: 持久化API層
        print('\n🌐 Stage 6: 持久化API層處理器')
        print('-' * 60)

        from stages.stage6_dynamic_pool_planning.stage6_persistence_processor import create_stage6_processor
        stage6_processor = create_stage6_processor()

        stage6_result = stage6_processor.process(stage5_result.data)
        validation_success, validation_msg = validate_processing_result(stage6_result, "Stage 6")

        if not validation_success:
            print(f'❌ Stage 6失敗: {validation_msg}')
            return False, 6, validation_msg

        stage_results['stage6'] = stage6_result.data
        print(f'✅ Stage 6完成: {validation_msg}')

        # 生成處理摘要
        print('\n🎉 六階段處理全部完成!')
        print('=' * 80)

        # 提取關鍵指標
        summary = {}
        for stage_name, processor in [
            ('stage1', stage1_processor),
            ('stage2', stage2_processor),
            ('stage3', stage3_processor),
            ('stage4', stage4_processor),
            ('stage5', stage5_processor),
            ('stage6', stage6_processor)
        ]:
            try:
                summary[stage_name] = processor.extract_key_metrics()
            except Exception as e:
                logger.warning(f"無法提取{stage_name}關鍵指標: {e}")
                summary[stage_name] = {"error": str(e)}

        print('📊 處理摘要:')
        for stage_name, metrics in summary.items():
            if 'error' not in metrics:
                print(f'   {stage_name}: {metrics}')
            else:
                print(f'   {stage_name}: 指標提取失敗')

        print('🏗️ 重構架構優勢:')
        print('   ✅ 統一的 BaseProcessor 接口')
        print('   ✅ 共享監控和預測模組')
        print('   ✅ 標準化的數據流傳遞')
        print('   ✅ 簡化的錯誤處理機制')
        print('   ✅ 模組化驗證框架')
        print('=' * 80)

        return True, 6, "全部六階段成功完成"

    except Exception as e:
        logger.error(f"六階段處理異常: {e}")
        return False, 0, f"六階段處理異常: {e}"


def run_stage_specific(target_stage):
    """運行特定階段"""
    print(f'\n🎯 運行階段 {target_stage} - 重構版本')
    print('=' * 80)

    try:
        if target_stage == 1:
            print('\n📡 Stage 1: 數據載入層處理器')
            from stages.stage1_orbital_calculation.stage1_data_loading_processor import create_stage1_processor
            processor = create_stage1_processor()
            result = processor.process(None)

        elif target_stage == 2:
            print('\n🎯 Stage 2: 軌道計算層處理器')
            # 需要從 Stage 1 輸出載入數據
            print('⚠️ Stage 2 需要 Stage 1 的輸出數據，建議運行完整管道')
            return False, 2, "Stage 2 需要 Stage 1 的輸出數據"

        elif target_stage == 3:
            print('\n📶 Stage 3: 信號分析層處理器')
            print('⚠️ Stage 3 需要 Stage 2 的輸出數據，建議運行完整管道')
            return False, 3, "Stage 3 需要 Stage 2 的輸出數據"

        elif target_stage == 4:
            print('\n⏱️ Stage 4: 優化決策層處理器')
            print('⚠️ Stage 4 需要 Stage 3 的輸出數據，建議運行完整管道')
            return False, 4, "Stage 4 需要 Stage 3 的輸出數據"

        elif target_stage == 5:
            print('\n🔗 Stage 5: 數據整合層處理器')
            print('⚠️ Stage 5 需要 Stage 4 的輸出數據，建議運行完整管道')
            return False, 5, "Stage 5 需要 Stage 4 的輸出數據"

        elif target_stage == 6:
            print('\n🌐 Stage 6: 持久化API層處理器')
            print('⚠️ Stage 6 需要 Stage 5 的輸出數據，建議運行完整管道')
            return False, 6, "Stage 6 需要 Stage 5 的輸出數據"
        else:
            return False, 0, f"無效的階段編號: {target_stage}"

        # 驗證結果
        validation_success, validation_msg = validate_processing_result(result, f"Stage {target_stage}")

        if not validation_success:
            print(f'❌ Stage {target_stage}失敗: {validation_msg}')
            return False, target_stage, validation_msg

        print(f'✅ Stage {target_stage}完成: {validation_msg}')
        return True, target_stage, f"Stage {target_stage}成功完成"

    except Exception as e:
        logger.error(f"Stage {target_stage}執行異常: {e}")
        return False, target_stage, f"Stage {target_stage}執行異常: {e}"


def main():
    import argparse
    parser = argparse.ArgumentParser(description='六階段數據處理系統 - 重構版本')
    parser.add_argument('--stage', type=int, choices=[1,2,3,4,5,6],
                       help='運行特定階段 (1-6)')
    args = parser.parse_args()

    start_time = time.time()

    if args.stage:
        success, completed_stage, message = run_stage_specific(args.stage)
    else:
        success, completed_stage, message = run_all_stages_sequential()

    end_time = time.time()
    execution_time = end_time - start_time

    print(f'\n📊 執行統計:')
    print(f'   執行時間: {execution_time:.2f} 秒')
    print(f'   完成階段: {completed_stage}/6')
    print(f'   最終狀態: {"✅ 成功" if success else "❌ 失敗"}')
    print(f'   訊息: {message}')

    print('\n🏗️ 重構架構特色總結:')
    print('   📦 Stage 1: 數據載入層 - TLE數據載入與預處理')
    print('   📦 Stage 2: 軌道計算層 - SGP4計算與可見性過濾')
    print('   📦 Stage 3: 信號分析層 - 信號品質計算與3GPP事件檢測')
    print('   📦 Stage 4: 優化決策層 - 換手決策與動態池規劃')
    print('   📦 Stage 5: 數據整合層 - 多階段數據整合與格式化')
    print('   📦 Stage 6: 持久化API層 - 數據存儲與API輸出')
    print('   🎯 架構優勢: 統一接口、共享模組、簡化維護')

    return 0 if success else 1


if __name__ == "__main__":
    exit(main())