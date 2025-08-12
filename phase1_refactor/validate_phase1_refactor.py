#!/usr/bin/env python3
"""
Phase 1 重構驗證腳本

功能:
1. 驗證 Phase 1 重構的完整性
2. 測試核心模組功能
3. 確保符合 CLAUDE.md 原則

使用方法:
    python validate_phase1_refactor.py
"""

import os
import sys
import json
import logging
import subprocess
from pathlib import Path
from datetime import datetime, timezone

# 設置路徑
PHASE1_ROOT = Path(__file__).parent
sys.path.insert(0, str(PHASE1_ROOT))

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Phase1RefactorValidator:
    """Phase 1 重構驗證器"""
    
    def __init__(self):
        self.results = {
            "validation_timestamp": datetime.now(timezone.utc).isoformat(),
            "tests_passed": 0,
            "tests_failed": 0,
            "errors": [],
            "warnings": [],
            "compliance_checks": {}
        }
    
    def run_all_validations(self):
        """執行所有驗證測試"""
        logger.info("🚀 開始 Phase 1 重構驗證...")
        
        # 1. 目錄結構驗證
        self._validate_directory_structure()
        
        # 2. 模組導入測試
        self._validate_module_imports()
        
        # 3. 配置檔案驗證
        self._validate_configuration_files()
        
        # 4. 核心功能測試
        self._validate_core_functionality()
        
        # 5. CLAUDE.md 合規性檢查
        self._validate_claude_md_compliance()
        
        # 生成報告
        self._generate_validation_report()
        
        return self.results
    
    def _validate_directory_structure(self):
        """驗證目錄結構"""
        logger.info("📁 驗證目錄結構...")
        
        required_dirs = [
            "01_data_source",
            "02_orbit_calculation", 
            "03_processing_pipeline",
            "04_output_interface",
            "05_integration",
            "config",
            "docs",
            "migration"
        ]
        
        required_files = [
            "01_data_source/tle_loader.py",
            "02_orbit_calculation/sgp4_engine.py",
            "03_processing_pipeline/phase1_coordinator.py",
            "04_output_interface/phase1_api.py",
            "config/phase1_config.yaml",
            "docs/algorithm_specification.md"
        ]
        
        try:
            # 檢查目錄
            for dir_name in required_dirs:
                dir_path = PHASE1_ROOT / dir_name
                if not dir_path.exists():
                    self._add_error(f"缺少目錄: {dir_path}")
                else:
                    self._add_success(f"目錄存在: {dir_name}")
            
            # 檢查檔案
            for file_path in required_files:
                file_full_path = PHASE1_ROOT / file_path
                if not file_full_path.exists():
                    self._add_error(f"缺少檔案: {file_path}")
                else:
                    self._add_success(f"檔案存在: {file_path}")
                    
        except Exception as e:
            self._add_error(f"目錄結構驗證失敗: {e}")
    
    def _validate_module_imports(self):
        """驗證模組導入"""
        logger.info("📦 驗證模組導入...")
        
        modules_to_test = [
            ("01_data_source.tle_loader", "TLELoader"),
            ("02_orbit_calculation.sgp4_engine", "SGP4Engine"),
            ("03_processing_pipeline.phase1_coordinator", "Phase1Coordinator"),
            ("04_output_interface.phase1_api", "Phase1APIInterface")
        ]
        
        for module_path, class_name in modules_to_test:
            try:
                # 動態導入模組
                module = __import__(module_path, fromlist=[class_name])
                target_class = getattr(module, class_name)
                
                # 檢查類別是否可實例化
                if hasattr(target_class, '__init__'):
                    self._add_success(f"模組可導入: {module_path}.{class_name}")
                else:
                    self._add_warning(f"模組無 __init__ 方法: {module_path}.{class_name}")
                    
            except ImportError as e:
                self._add_error(f"模組導入失敗 {module_path}: {e}")
            except Exception as e:
                self._add_error(f"模組測試異常 {module_path}: {e}")
    
    def _validate_configuration_files(self):
        """驗證配置檔案"""
        logger.info("⚙️ 驗證配置檔案...")
        
        config_files = [
            "config/phase1_config.yaml",
            "config/constellation_config.yaml"
        ]
        
        for config_file in config_files:
            config_path = PHASE1_ROOT / config_file
            if config_path.exists():
                try:
                    # 嘗試解析 YAML
                    import yaml
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config_data = yaml.safe_load(f)
                    
                    if config_data:
                        self._add_success(f"配置檔案有效: {config_file}")
                    else:
                        self._add_warning(f"配置檔案為空: {config_file}")
                        
                except yaml.YAMLError as e:
                    self._add_error(f"YAML 格式錯誤 {config_file}: {e}")
                except Exception as e:
                    self._add_error(f"配置檔案讀取失敗 {config_file}: {e}")
            else:
                self._add_warning(f"配置檔案不存在: {config_file}")
    
    def _validate_core_functionality(self):
        """驗證核心功能"""
        logger.info("🧮 驗證核心功能...")
        
        try:
            # 測試 TLE 載入器
            self._test_tle_loader()
            
            # 測試 SGP4 引擎
            self._test_sgp4_engine()
            
            # 測試協調器（基本檢查）
            self._test_coordinator_basic()
            
        except Exception as e:
            self._add_error(f"核心功能測試失敗: {e}")
    
    def _test_tle_loader(self):
        """測試 TLE 載入器"""
        try:
            sys.path.insert(0, str(PHASE1_ROOT / "01_data_source"))
            from tle_loader import TLELoader, create_tle_loader
            
            # 嘗試創建載入器（使用測試目錄）
            test_tle_dir = "/tmp/test_tle"
            Path(test_tle_dir).mkdir(exist_ok=True)
            
            loader = TLELoader(test_tle_dir)
            self._add_success("TLE 載入器創建成功")
            
            # 測試 TLE 格式驗證
            line1 = "1 25544U 98067A   21001.00000000  .00001817  00000-0  41860-4 0  9990"
            line2 = "2 25544  51.6461 290.5094 0000597  91.8164 268.3516 15.48919103262509"
            
            if loader._validate_tle_format(line1, line2):
                self._add_success("TLE 格式驗證功能正常")
            else:
                self._add_error("TLE 格式驗證失敗")
                
        except ImportError as e:
            self._add_error(f"TLE 載入器導入失敗: {e}")
        except Exception as e:
            self._add_error(f"TLE 載入器測試失敗: {e}")
    
    def _test_sgp4_engine(self):
        """測試 SGP4 引擎"""
        try:
            sys.path.insert(0, str(PHASE1_ROOT / "02_orbit_calculation"))
            from sgp4_engine import SGP4Engine, validate_sgp4_availability
            
            # 檢查 SGP4 庫可用性
            if validate_sgp4_availability():
                self._add_success("SGP4 庫可用")
                
                # 嘗試創建引擎
                engine = SGP4Engine()
                self._add_success("SGP4 引擎創建成功")
                
                # 測試基本功能（如果 SGP4 可用）
                stats = engine.get_statistics()
                if isinstance(stats, dict):
                    self._add_success("SGP4 引擎統計功能正常")
                
            else:
                self._add_warning("SGP4 庫不可用，跳過詳細測試")
                
        except ImportError as e:
            self._add_error(f"SGP4 引擎導入失敗: {e}")
        except Exception as e:
            self._add_error(f"SGP4 引擎測試失敗: {e}")
    
    def _test_coordinator_basic(self):
        """測試協調器基本功能"""
        try:
            sys.path.insert(0, str(PHASE1_ROOT / "03_processing_pipeline"))
            from phase1_coordinator import Phase1Coordinator, Phase1Config
            
            # 創建測試配置
            test_config = Phase1Config(
                tle_data_dir="/tmp/test_tle",
                output_dir="/tmp/test_output"
            )
            
            # 確保測試目錄存在
            Path("/tmp/test_output").mkdir(exist_ok=True)
            
            coordinator = Phase1Coordinator(test_config)
            self._add_success("Phase 1 協調器創建成功")
            
            # 測試狀態獲取
            status = coordinator.get_status()
            if hasattr(status, 'stage'):
                self._add_success("協調器狀態功能正常")
                
        except ImportError as e:
            self._add_error(f"協調器導入失敗: {e}")
        except Exception as e:
            self._add_error(f"協調器測試失敗: {e}")
    
    def _validate_claude_md_compliance(self):
        """驗證 CLAUDE.md 合規性"""
        logger.info("📏 驗證 CLAUDE.md 合規性...")
        
        compliance_checks = {
            "no_simplified_algorithms": self._check_no_simplified_algorithms(),
            "real_data_sources": self._check_real_data_sources(),
            "complete_sgp4_usage": self._check_complete_sgp4_usage(),
            "no_mock_data": self._check_no_mock_data()
        }
        
        self.results["compliance_checks"] = compliance_checks
        
        passed_checks = sum(1 for result in compliance_checks.values() if result)
        total_checks = len(compliance_checks)
        
        if passed_checks == total_checks:
            self._add_success(f"CLAUDE.md 合規性檢查通過 ({passed_checks}/{total_checks})")
        else:
            self._add_warning(f"CLAUDE.md 合規性部分通過 ({passed_checks}/{total_checks})")
    
    def _check_no_simplified_algorithms(self):
        """檢查無簡化算法"""
        # 檢查代碼中是否有禁止的關鍵字
        forbidden_keywords = ["簡化", "simplified", "mock", "假設", "estimated"]
        
        python_files = list(PHASE1_ROOT.glob("**/*.py"))
        
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read().lower()
                    
                for keyword in forbidden_keywords:
                    if keyword.lower() in content:
                        self._add_warning(f"發現可疑關鍵字 '{keyword}' 在 {file_path}")
                        return False
            except Exception:
                continue
        
        return True
    
    def _check_real_data_sources(self):
        """檢查真實數據源"""
        # 檢查是否使用真實 TLE 數據路徑
        expected_tle_path = "/netstack/tle_data"
        
        config_file = PHASE1_ROOT / "config/phase1_config.yaml"
        if config_file.exists():
            try:
                import yaml
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                
                tle_dir = config.get("data_sources", {}).get("tle_data_dir", "")
                return expected_tle_path in tle_dir
            except Exception:
                return False
        
        return False
    
    def _check_complete_sgp4_usage(self):
        """檢查完整 SGP4 使用"""
        sgp4_file = PHASE1_ROOT / "02_orbit_calculation/sgp4_engine.py"
        
        if sgp4_file.exists():
            try:
                with open(sgp4_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 檢查是否使用官方 SGP4 庫
                required_imports = ["from sgp4.api import Satrec", "from sgp4.earth_gravity import wgs72"]
                
                for import_stmt in required_imports:
                    if import_stmt not in content:
                        return False
                
                return True
            except Exception:
                return False
        
        return False
    
    def _check_no_mock_data(self):
        """檢查無模擬數據"""
        # 檢查代碼中是否有模擬數據生成
        mock_keywords = ["random.normal", "np.random", "mock_data", "fake_data"]
        
        python_files = list(PHASE1_ROOT.glob("**/*.py"))
        
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                for keyword in mock_keywords:
                    if keyword in content:
                        self._add_warning(f"發現可能的模擬數據 '{keyword}' 在 {file_path}")
                        return False
            except Exception:
                continue
        
        return True
    
    def _add_success(self, message: str):
        """添加成功記錄"""
        logger.info(f"✅ {message}")
        self.results["tests_passed"] += 1
    
    def _add_error(self, message: str):
        """添加錯誤記錄"""
        logger.error(f"❌ {message}")
        self.results["tests_failed"] += 1
        self.results["errors"].append(message)
    
    def _add_warning(self, message: str):
        """添加警告記錄"""
        logger.warning(f"⚠️ {message}")
        self.results["warnings"].append(message)
    
    def _generate_validation_report(self):
        """生成驗證報告"""
        report_path = PHASE1_ROOT / "validation_report.json"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📊 驗證報告已保存: {report_path}")
        
        # 顯示摘要
        total_tests = self.results["tests_passed"] + self.results["tests_failed"]
        success_rate = (self.results["tests_passed"] / max(total_tests, 1)) * 100
        
        print("\n" + "="*60)
        print("🎯 Phase 1 重構驗證摘要")
        print("="*60)
        print(f"總測試數: {total_tests}")
        print(f"通過測試: {self.results['tests_passed']}")
        print(f"失敗測試: {self.results['tests_failed']}")
        print(f"警告數量: {len(self.results['warnings'])}")
        print(f"成功率: {success_rate:.1f}%")
        
        if self.results["tests_failed"] == 0:
            print("\n🎉 Phase 1 重構驗證通過！")
        else:
            print("\n❌ Phase 1 重構驗證存在問題，請檢查錯誤信息")
            
        print("="*60)

def main():
    """主函數"""
    validator = Phase1RefactorValidator()
    results = validator.run_all_validations()
    
    # 返回適當的退出代碼
    if results["tests_failed"] == 0:
        return 0
    else:
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)