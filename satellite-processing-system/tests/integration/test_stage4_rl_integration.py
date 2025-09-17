#!/usr/bin/env python3
"""
🧪 Stage4 RL預處理引擎整合測試

驗證 RL 預處理引擎是否正確整合到 TimeseriesPreprocessingProcessor
"""

import sys
import os
import json
from datetime import datetime, timezone
from pathlib import Path

# 添加專案路徑
sys.path.append('/home/sat/ntn-stack/satellite-processing-system/src')

def test_rl_preprocessing_engine_import():
    """測試RL預處理引擎導入"""
    print("🔍 測試RL預處理引擎導入...")

    try:
        from stages.stage4_timeseries_preprocessing.rl_preprocessing_engine import (
            RLPreprocessingEngine, RLState, RLAction, ActionType
        )
        print("✅ RL預處理引擎導入成功")
        return True
    except Exception as e:
        print(f"❌ RL預處理引擎導入失敗: {e}")
        return False

def test_timeseries_processor_integration():
    """測試時間序列處理器整合"""
    print("🔍 測試時間序列處理器整合...")

    try:
        from stages.stage4_timeseries_preprocessing.timeseries_preprocessing_processor import (
            TimeseriesPreprocessingProcessor
        )

        # 創建處理器實例
        config = {
            "rl_preprocessing": {
                "state_dim": 20,
                "discrete_actions": 5,
                "continuous_dim": 3
            }
        }

        processor = TimeseriesPreprocessingProcessor(config)

        # 驗證RL引擎是否正確初始化
        if hasattr(processor, 'rl_preprocessing_engine'):
            print("✅ RL預處理引擎已正確整合到時間序列處理器")
            print(f"   狀態維度: {processor.rl_preprocessing_engine.state_config['state_dim']}")
            print(f"   離散動作: {processor.rl_preprocessing_engine.action_config['discrete_actions']}")
            return True
        else:
            print("❌ RL預處理引擎未找到在時間序列處理器中")
            return False

    except Exception as e:
        print(f"❌ 時間序列處理器整合測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_rl_methods_accessibility():
    """測試RL方法可訪問性"""
    print("🔍 測試RL方法可訪問性...")

    try:
        from stages.stage4_timeseries_preprocessing.timeseries_preprocessing_processor import (
            TimeseriesPreprocessingProcessor
        )

        processor = TimeseriesPreprocessingProcessor()

        # 驗證關鍵方法是否存在
        methods_to_check = [
            'generate_rl_training_data',
            '_create_training_episodes'
        ]

        for method_name in methods_to_check:
            if hasattr(processor, method_name):
                print(f"✅ 方法 {method_name} 可訪問")
            else:
                print(f"❌ 方法 {method_name} 不存在")
                return False

        # 測試RL引擎方法
        rl_engine = processor.rl_preprocessing_engine
        engine_methods = [
            'generate_training_states',
            'define_action_space',
            'calculate_reward_functions',
            'create_experience_buffer'
        ]

        for method_name in engine_methods:
            if hasattr(rl_engine, method_name):
                print(f"✅ RL引擎方法 {method_name} 可訪問")
            else:
                print(f"❌ RL引擎方法 {method_name} 不存在")
                return False

        return True

    except Exception as e:
        print(f"❌ RL方法可訪問性測試失敗: {e}")
        return False

def test_rl_functionality_basic():
    """基本RL功能測試"""
    print("🔍 測試基本RL功能...")

    try:
        from stages.stage4_timeseries_preprocessing.rl_preprocessing_engine import (
            RLPreprocessingEngine
        )

        # 創建RL引擎
        engine = RLPreprocessingEngine()

        # 測試動作空間定義
        discrete_actions = engine.define_action_space("discrete")
        continuous_actions = engine.define_action_space("continuous")

        print(f"✅ 離散動作空間定義成功: {discrete_actions['action_space_definition']['num_actions']} 個動作")
        print(f"✅ 連續動作空間定義成功: {continuous_actions['action_space_definition']['dimensions']} 維")

        # 測試狀態生成（使用模擬數據）
        mock_timeseries_data = {
            'signal_analysis': {
                'satellites': [{
                    'signal_timeseries': [{
                        'rsrp_dbm': -85.0,
                        'elevation_deg': 30.0,
                        'range_km': 1200.0,
                        'timestamp': datetime.now(timezone.utc).isoformat()
                    }]
                }]
            }
        }

        training_states = engine.generate_training_states(mock_timeseries_data, {})
        states_count = len(training_states.get('training_states', []))

        print(f"✅ 訓練狀態生成成功: {states_count} 個狀態")

        return True

    except Exception as e:
        print(f"❌ 基本RL功能測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主測試函數"""
    print("🚀 開始 Stage4 RL預處理引擎整合測試")
    print("=" * 50)

    tests = [
        ("RL預處理引擎導入", test_rl_preprocessing_engine_import),
        ("時間序列處理器整合", test_timeseries_processor_integration),
        ("RL方法可訪問性", test_rl_methods_accessibility),
        ("基本RL功能", test_rl_functionality_basic)
    ]

    passed_tests = 0
    total_tests = len(tests)

    for test_name, test_func in tests:
        print(f"\n📋 執行測試: {test_name}")
        if test_func():
            passed_tests += 1
        print("-" * 30)

    print(f"\n📊 測試結果摘要:")
    print(f"   總測試數: {total_tests}")
    print(f"   通過測試: {passed_tests}")
    print(f"   失敗測試: {total_tests - passed_tests}")
    print(f"   成功率: {(passed_tests/total_tests*100):.1f}%")

    if passed_tests == total_tests:
        print("\n🎉 所有Stage4 RL預處理引擎整合測試均通過！")
        return 0
    else:
        print(f"\n⚠️ 有 {total_tests - passed_tests} 個測試失敗，需要進一步檢查")
        return 1

if __name__ == "__main__":
    exit(main())