#!/usr/bin/env python3
"""
Phase 3: 運行時驗證框架整合測試
測試三個核心運行時檢查組件的功能和整合度

測試範圍:
1. RuntimeArchitectureChecker - 引擎類型和架構驗證
2. APIContractValidator - 數據格式和合約驗證  
3. ExecutionFlowChecker - 執行流程和依賴驗證
4. 六階段處理器整合驗證
"""

import os
import sys
import json
import logging
from pathlib import Path

# 添加必要路徑
sys.path.insert(0, '/app')
sys.path.insert(0, '/app/netstack')
sys.path.insert(0, '/app/netstack/src')

# 導入運行時檢查組件
from netstack.src.validation.runtime_architecture_checker import (
    RuntimeArchitectureChecker, 
    ArchitectureViolationError,
    check_runtime_architecture
)
from validation.api_contract_validator import (
    APIContractValidator,
    ContractViolationError, 
    validate_api_contract
)
from validation.execution_flow_checker import (
    ExecutionFlowChecker,
    FlowViolationError,
    check_execution_flow,
    validate_stage_completion
)

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RuntimeValidationFrameworkTester:
    """運行時驗證框架測試器"""
    
    def __init__(self):
        self.test_results = {
            "architecture_checker": {},
            "api_contract_validator": {},
            "execution_flow_checker": {},
            "integration_tests": {},
            "summary": {}
        }
        
    def test_architecture_checker(self):
        """測試 RuntimeArchitectureChecker"""
        logger.info("🔧 測試 RuntimeArchitectureChecker...")
        
        try:
            checker = RuntimeArchitectureChecker()
            
            # 測試 1: 正確的引擎類型檢查
            class MockSGP4Engine:
                def __init__(self):
                    self.__class__.__name__ = "SGP4OrbitalEngine"
            
            mock_engine = MockSGP4Engine()
            checker.check_engine_type("stage1", mock_engine)
            self.test_results["architecture_checker"]["engine_type_check"] = "PASS"
            logger.info("✅ 引擎類型檢查測試通過")
            
            # 測試 2: 錯誤引擎類型檢測
            class MockWrongEngine:
                def __init__(self):
                    self.__class__.__name__ = "CoordinateSpecificOrbitEngine"
            
            wrong_engine = MockWrongEngine()
            try:
                checker.check_engine_type("stage1", wrong_engine)
                self.test_results["architecture_checker"]["wrong_engine_detection"] = "FAIL"
                logger.error("❌ 錯誤引擎類型檢測失敗")
            except ArchitectureViolationError:
                self.test_results["architecture_checker"]["wrong_engine_detection"] = "PASS"  
                logger.info("✅ 錯誤引擎類型檢測測試通過")
            
            # 測試 3: 192點時間序列檢查
            test_output = {
                "satellites": [{
                    "position_timeseries": [{"time": i} for i in range(192)]
                }]
            }
            checker.check_output_format("stage1", test_output)
            self.test_results["architecture_checker"]["timeseries_format_check"] = "PASS"
            logger.info("✅ 192點時間序列檢查測試通過")
            
        except Exception as e:
            logger.error(f"❌ RuntimeArchitectureChecker 測試失敗: {e}")
            self.test_results["architecture_checker"]["overall"] = "FAIL"
            return False
            
        self.test_results["architecture_checker"]["overall"] = "PASS"
        return True
    
    def test_api_contract_validator(self):
        """測試 APIContractValidator"""
        logger.info("📋 測試 APIContractValidator...")
        
        try:
            validator = APIContractValidator()
            
            # 測試 1: Stage 1 正確輸出驗證
            valid_stage1_output = {
                "satellites": [{
                    "satellite_id": "TEST-1",
                    "constellation": "starlink", 
                    "position_timeseries": [
                        {
                            "time": i,
                            "elevation_deg": 45.0,
                            "is_visible": True
                        } for i in range(192)
                    ]
                }] * 8700,
                "metadata": {
                    "total_satellites": 8700,
                    "processing_timestamp": "2025-09-09T12:00:00Z",
                    "constellations": {
                        "starlink": {"satellite_count": 8000},
                        "oneweb": {"satellite_count": 700}
                    }
                }
            }
            
            validator.validate_stage1_output(valid_stage1_output)
            self.test_results["api_contract_validator"]["stage1_valid_output"] = "PASS"
            logger.info("✅ Stage 1 正確輸出驗證測試通過")
            
            # 測試 2: Stage 1 錯誤輸出檢測 (218點 vs 192點)
            invalid_stage1_output = valid_stage1_output.copy()
            invalid_stage1_output["satellites"][0]["position_timeseries"] = [{"time": i} for i in range(218)]
            
            try:
                validator.validate_stage1_output(invalid_stage1_output)
                self.test_results["api_contract_validator"]["stage1_invalid_detection"] = "FAIL"
                logger.error("❌ Stage 1 錯誤輸出檢測失敗")
            except ContractViolationError as e:
                self.test_results["api_contract_validator"]["stage1_invalid_detection"] = "PASS"
                logger.info("✅ Stage 1 錯誤輸出檢測測試通過")
            
            # 測試 3: Stage 2 輸出驗證
            valid_stage2_output = {
                "filtered_satellites": {
                    "starlink": [{"id": f"starlink-{i}"} for i in range(1000)],
                    "oneweb": [{"id": f"oneweb-{i}"} for i in range(100)]
                },
                "metadata": {
                    "filtering_rate": 0.15
                }
            }
            
            validator.validate_stage2_output(valid_stage2_output)
            self.test_results["api_contract_validator"]["stage2_valid_output"] = "PASS"
            logger.info("✅ Stage 2 正確輸出驗證測試通過")
            
        except Exception as e:
            logger.error(f"❌ APIContractValidator 測試失敗: {e}")
            self.test_results["api_contract_validator"]["overall"] = "FAIL"
            return False
            
        self.test_results["api_contract_validator"]["overall"] = "PASS"
        return True
    
    def test_execution_flow_checker(self):
        """測試 ExecutionFlowChecker"""
        logger.info("🔄 測試 ExecutionFlowChecker...")
        
        try:
            checker = ExecutionFlowChecker()
            
            # 測試 1: 正確的階段依賴檢查
            checker.check_stage_dependencies("stage2", ["stage1"])
            self.test_results["execution_flow_checker"]["dependency_check"] = "PASS"
            logger.info("✅ 階段依賴檢查測試通過")
            
            # 測試 2: 缺少依賴檢測
            try:
                checker.check_stage_dependencies("stage2", [])
                self.test_results["execution_flow_checker"]["missing_dependency_detection"] = "FAIL"
                logger.error("❌ 缺少依賴檢測失敗")
            except FlowViolationError:
                self.test_results["execution_flow_checker"]["missing_dependency_detection"] = "PASS"
                logger.info("✅ 缺少依賴檢測測試通過")
            
            # 測試 3: 執行順序檢查
            correct_order = ["stage1", "stage2", "stage3"]
            checker.check_data_chain_integrity(correct_order)
            self.test_results["execution_flow_checker"]["execution_order_check"] = "PASS"
            logger.info("✅ 執行順序檢查測試通過")
            
        except Exception as e:
            logger.error(f"❌ ExecutionFlowChecker 測試失敗: {e}")
            self.test_results["execution_flow_checker"]["overall"] = "FAIL"
            return False
            
        self.test_results["execution_flow_checker"]["overall"] = "PASS"
        return True
    
    def test_integration(self):
        """測試整合功能"""
        logger.info("🔗 測試整合功能...")
        
        try:
            # 測試整合便捷函數
            mock_engine = type('SGP4OrbitalEngine', (), {})()
            check_runtime_architecture("stage1", engine=mock_engine)
            self.test_results["integration_tests"]["convenience_functions"] = "PASS"
            logger.info("✅ 便捷函數整合測試通過")
            
            # 測試錯誤處理機制
            try:
                validate_stage_completion("stage2", [])  # 缺少stage1依賴
                self.test_results["integration_tests"]["error_handling"] = "FAIL"
                logger.error("❌ 錯誤處理機制測試失敗")
            except Exception:
                self.test_results["integration_tests"]["error_handling"] = "PASS"
                logger.info("✅ 錯誤處理機制測試通過")
                
        except Exception as e:
            logger.error(f"❌ 整合測試失敗: {e}")
            self.test_results["integration_tests"]["overall"] = "FAIL"
            return False
            
        self.test_results["integration_tests"]["overall"] = "PASS"
        return True
    
    def run_all_tests(self):
        """執行所有測試"""
        logger.info("🚀 開始運行時驗證框架整合測試")
        logger.info("=" * 60)
        
        test_methods = [
            self.test_architecture_checker,
            self.test_api_contract_validator, 
            self.test_execution_flow_checker,
            self.test_integration
        ]
        
        passed_tests = 0
        total_tests = len(test_methods)
        
        for test_method in test_methods:
            if test_method():
                passed_tests += 1
        
        # 生成測試摘要
        self.test_results["summary"] = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "pass_rate": f"{(passed_tests/total_tests)*100:.1f}%",
            "overall_status": "PASS" if passed_tests == total_tests else "FAIL"
        }
        
        logger.info("=" * 60)
        logger.info(f"📊 測試摘要:")
        logger.info(f"   總測試數: {total_tests}")
        logger.info(f"   通過測試: {passed_tests}")
        logger.info(f"   通過率: {self.test_results['summary']['pass_rate']}")
        logger.info(f"   整體狀態: {self.test_results['summary']['overall_status']}")
        
        # 保存測試結果
        test_results_file = Path("/app/data/runtime_validation_test_results.json")
        with open(test_results_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📄 測試結果已保存到: {test_results_file}")
        
        return self.test_results["summary"]["overall_status"] == "PASS"

def main():
    """主函數"""
    tester = RuntimeValidationFrameworkTester()
    success = tester.run_all_tests()
    
    if success:
        logger.info("🎉 所有運行時驗證框架測試通過!")
        return 0
    else:
        logger.error("💥 運行時驗證框架測試失敗!")
        return 1

if __name__ == "__main__":
    exit(main())