#!/usr/bin/env python3
"""
🧪 TDD整合機制測試腳本
=======================

用途：測試和驗證TDD整合自動化機制的完整功能

測試範圍：
1. TDD配置載入
2. 協調器初始化 
3. 後置鉤子觸發
4. 測試執行引擎
5. 結果整合器
6. 驗證快照增強
7. 故障處理機制

Author: Claude Code
Version: 5.0.0 (Phase 5.0 TDD整合自動化)
"""

import sys
import asyncio
from pathlib import Path
import json
from datetime import datetime, timezone

# 添加src路徑到sys.path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_tdd_configuration():
    """測試TDD配置載入"""
    print("🧪 測試 1: TDD配置載入")
    
    try:
        from src.shared.tdd_integration_coordinator import TDDConfigurationManager
        
        config_manager = TDDConfigurationManager()
        config = config_manager.load_config()
        
        print(f"   ✅ 配置載入成功")
        print(f"   📋 TDD整合啟用: {config.get('tdd_integration', {}).get('enabled', False)}")
        print(f"   📋 執行模式: {config.get('tdd_integration', {}).get('execution_mode', 'sync')}")
        print(f"   📋 可用階段數量: {len(config.get('stages', {}))}")
        
        # 測試階段配置
        stage1_config = config_manager.get_stage_config('stage1')
        print(f"   📋 Stage1 測試類型: {stage1_config.get('tests', [])}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 配置載入失敗: {e}")
        return False


def test_coordinator_initialization():
    """測試協調器初始化"""
    print("\n🧪 測試 2: TDD協調器初始化")
    
    try:
        from src.shared.tdd_integration_coordinator import get_tdd_coordinator
        
        coordinator = get_tdd_coordinator()
        print(f"   ✅ 協調器初始化成功")
        
        # 測試組件存在
        assert coordinator.config_manager is not None
        assert coordinator.test_engine is not None
        assert coordinator.results_integrator is not None
        assert coordinator.failure_handler is not None
        
        print(f"   ✅ 所有子組件初始化正常")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 協調器初始化失敗: {e}")
        return False


async def test_post_hook_execution():
    """測試後置鉤子執行"""
    print("\n🧪 測試 3: 後置鉤子執行")
    
    try:
        from src.shared.tdd_integration_coordinator import get_tdd_coordinator
        
        coordinator = get_tdd_coordinator()
        
        # 模擬階段結果
        stage_results = {
            "total_satellites": 8837,
            "processed_satellites": 8837,
            "execution_time": 3.5,
            "success_rate": 1.0
        }
        
        # 模擬驗證快照
        validation_snapshot = {
            "stage": 1,
            "stageName": "tle_loading",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "completed",
            "duration_seconds": 3.5,
            "validation": {"passed": True}
        }
        
        # 執行TDD測試
        results = await coordinator.execute_post_hook_tests(
            "stage1",
            stage_results,
            validation_snapshot,
            "development"
        )
        
        print(f"   ✅ 後置鉤子執行成功")
        print(f"   📊 品質分數: {results.overall_quality_score:.2f}")
        print(f"   ⏱️ 執行時間: {results.total_execution_time_ms}ms")
        print(f"   🧪 執行的測試類型: {list(results.test_results.keys())}")
        print(f"   🚦 關鍵問題: {len(results.critical_issues)}")
        print(f"   ⚠️ 警告數量: {len(results.warnings)}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 後置鉤子執行失敗: {e}")
        return False


def test_validation_snapshot_enhancement():
    """測試驗證快照增強"""
    print("\n🧪 測試 4: 驗證快照增強")
    
    try:
        from src.shared.tdd_integration_coordinator import get_tdd_coordinator, TDDIntegrationResults, ExecutionMode
        from datetime import datetime, timezone
        
        coordinator = get_tdd_coordinator()
        
        # 創建模擬TDD結果
        mock_tdd_results = TDDIntegrationResults(
            stage="stage1",
            execution_timestamp=datetime.now(timezone.utc),
            execution_mode=ExecutionMode.SYNC,
            total_execution_time_ms=1500,
            test_results={},
            overall_quality_score=0.95,
            critical_issues=[],
            warnings=["輕微性能問題"],
            recommendations=["考慮優化記憶體使用"],
            post_hook_triggered=True,
            validation_snapshot_enhanced=True
        )
        
        # 原始快照
        original_snapshot = {
            "stage": 1,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "validation": {"passed": True}
        }
        
        # 增強快照
        enhanced_snapshot = coordinator.enhance_validation_snapshot(
            original_snapshot, mock_tdd_results
        )
        
        print(f"   ✅ 驗證快照增強成功")
        print(f"   📋 包含TDD結果: {'tdd_integration' in enhanced_snapshot}")
        print(f"   📋 TDD啟用狀態: {enhanced_snapshot.get('tdd_integration', {}).get('enabled', False)}")
        print(f"   📋 執行模式: {enhanced_snapshot.get('tdd_integration', {}).get('execution_mode', 'unknown')}")
        print(f"   📋 品質分數: {enhanced_snapshot.get('tdd_integration', {}).get('overall_quality_score', 0)}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 驗證快照增強失敗: {e}")
        return False


def test_base_processor_integration():
    """測試BaseStageProcessor的TDD整合"""
    print("\n🧪 測試 5: BaseStageProcessor TDD整合")
    
    try:
        from src.shared.base_processor import BaseStageProcessor
        from unittest.mock import Mock
        
        # 創建一個測試用的處理器
        class TestProcessor(BaseStageProcessor):
            def validate_input(self, input_data):
                return True
            
            def process(self, input_data):
                return {
                    "data": {"test": "data"}, 
                    "metadata": {"test": True}
                }
            
            def validate_output(self, output_data):
                return True
            
            def save_results(self, results):
                return "/tmp/test_output.json"
            
            def extract_key_metrics(self, results):
                return {"test_metric": 1}
            
            def run_validation_checks(self, results):
                return {"passed": True}
        
        processor = TestProcessor(1, "test_stage")
        
        # 測試TDD狀態檢查
        print(f"   📋 TDD整合啟用: {processor.is_tdd_integration_enabled()}")
        
        tdd_status = processor.get_tdd_integration_status()
        print(f"   📋 TDD狀態: {tdd_status}")
        
        # 測試環境檢測
        environment = processor._detect_execution_environment()
        print(f"   📋 檢測到環境: {environment}")
        
        print(f"   ✅ BaseStageProcessor TDD整合正常")
        
        return True
        
    except Exception as e:
        print(f"   ❌ BaseStageProcessor TDD整合失敗: {e}")
        return False


def test_failure_handling():
    """測試故障處理機制"""
    print("\n🧪 測試 6: 故障處理機制")
    
    try:
        from src.shared.tdd_integration_coordinator import FailureHandler, TDDIntegrationResults, ExecutionMode
        from datetime import datetime, timezone
        
        failure_handler = FailureHandler()
        
        # 創建有失敗的TDD結果
        failed_results = TDDIntegrationResults(
            stage="stage1",
            execution_timestamp=datetime.now(timezone.utc),
            execution_mode=ExecutionMode.SYNC,
            total_execution_time_ms=2000,
            test_results={},
            overall_quality_score=0.3,
            critical_issues=["關鍵測試失敗"],
            warnings=["性能回歸", "合規問題"],
            recommendations=["立即修復"],
            post_hook_triggered=True,
            validation_snapshot_enhanced=False
        )
        
        # 處理失敗
        failure_action = failure_handler.handle_test_failures(
            failed_results, {"stage": 1}
        )
        
        print(f"   ✅ 故障處理執行成功")
        print(f"   🚦 處理動作: {failure_action.get('action', 'unknown')}")
        print(f"   📋 失敗原因: {failure_action.get('reason', 'unknown')}")
        print(f"   💡 建議數量: {len(failure_action.get('recovery_suggestions', []))}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 故障處理測試失敗: {e}")
        return False


def test_configuration_environments():
    """測試不同環境配置"""
    print("\n🧪 測試 7: 環境配置")
    
    try:
        from src.shared.tdd_integration_coordinator import TDDConfigurationManager, ExecutionMode
        
        config_manager = TDDConfigurationManager()
        
        environments = ["development", "testing", "production"]
        
        for env in environments:
            mode = config_manager.get_execution_mode(env)
            print(f"   📋 {env.ljust(11)} 環境執行模式: {mode.value}")
        
        print(f"   ✅ 環境配置測試成功")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 環境配置測試失敗: {e}")
        return False


async def main():
    """主測試函數"""
    print("🚀 TDD整合機制完整測試開始")
    print("=" * 50)
    
    test_results = []
    
    # 執行所有測試
    test_results.append(test_tdd_configuration())
    test_results.append(test_coordinator_initialization())
    test_results.append(await test_post_hook_execution())
    test_results.append(test_validation_snapshot_enhancement())
    test_results.append(test_base_processor_integration())
    test_results.append(test_failure_handling())
    test_results.append(test_configuration_environments())
    
    # 統計結果
    passed = sum(test_results)
    total = len(test_results)
    
    print("\n" + "=" * 50)
    print("📊 測試結果總結")
    print(f"   🧪 總測試數: {total}")
    print(f"   ✅ 通過測試: {passed}")
    print(f"   ❌ 失敗測試: {total - passed}")
    print(f"   📈 成功率: {passed/total*100:.1f}%")
    
    if passed == total:
        print("\n🎉 所有TDD整合測試通過！Phase 5.0 實現成功！")
        return 0
    else:
        print(f"\n⚠️ 有 {total - passed} 個測試失敗，需要修復")
        return 1


if __name__ == "__main__":
    # 執行測試
    exit_code = asyncio.run(main())
    sys.exit(exit_code)