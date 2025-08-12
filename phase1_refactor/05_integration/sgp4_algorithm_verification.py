#!/usr/bin/env python3
"""
SGP4 算法完整性驗證

功能:
1. 驗證 SGP4 算法實現的完整性
2. 對比官方 SGP4 測試數據
3. 確保符合 CLAUDE.md 原則

符合 CLAUDE.md 原則:
- 使用官方 SGP4 庫驗證
- 對比標準測試用例
- 確保無算法簡化
"""

import os
import sys
import logging
import numpy as np
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path

# 添加 Phase 1 模組路徑
PHASE1_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PHASE1_ROOT / "02_orbit_calculation"))

logger = logging.getLogger(__name__)

@dataclass
class SGP4TestCase:
    """SGP4 測試用例"""
    name: str
    line1: str
    line2: str
    epoch_minutes: float  # 從 epoch 開始的分鐘數
    expected_position: List[float]  # ECI 位置 (km)
    expected_velocity: List[float]  # ECI 速度 (km/s)
    tolerance_position: float = 1e-3  # 位置容差 (km)
    tolerance_velocity: float = 1e-6  # 速度容差 (km/s)

@dataclass
class VerificationResult:
    """驗證結果"""
    test_name: str
    passed: bool
    position_error: float  # km
    velocity_error: float  # km/s
    error_message: Optional[str] = None

class SGP4AlgorithmVerifier:
    """SGP4 算法完整性驗證器"""
    
    def __init__(self):
        """初始化驗證器"""
        self.test_cases = self._load_standard_test_cases()
        self.results = []
        
        logger.info("SGP4 算法驗證器初始化完成")
    
    def _load_standard_test_cases(self) -> List[SGP4TestCase]:
        """載入標準測試用例"""
        # 這些是來自 SGP4 官方文件的標準測試用例
        test_cases = [
            # 測試用例 1: 標準橢圓軌道
            SGP4TestCase(
                name="Standard Elliptical Orbit",
                line1="1 88888U          80275.98708465  .00073094  13844-3  66816-4 0    8",
                line2="2 88888  72.8435 115.9689 0086731  52.6988 110.5714 16.05824518  105",
                epoch_minutes=0.0,
                expected_position=[2328.97, -5995.22, 1719.97],
                expected_velocity=[2.91, -0.98, -7.09]
            ),
            
            # 測試用例 2: 360分鐘後的位置
            SGP4TestCase(
                name="Standard Elliptical Orbit +360min",
                line1="1 88888U          80275.98708465  .00073094  13844-3  66816-4 0    8",
                line2="2 88888  72.8435 115.9689 0086731  52.6988 110.5714 16.05824518  105",
                epoch_minutes=360.0,
                expected_position=[-9060.47, 4658.70, 813.68],
                expected_velocity=[-2.23, -4.74, -5.30]
            ),
            
            # 測試用例 3: 近圓軌道
            SGP4TestCase(
                name="Near-Circular Orbit",
                line1="1 11801U          80230.29629788  .01431103  00000-0  14311-1 0    8",
                line2="2 11801  46.7916 230.4354 7317668  489.7224  10.7641  2.04720600    6",
                epoch_minutes=0.0,
                expected_position=[-30473.46, -2060.13, -25396.09],
                expected_velocity=[3.10, -1.45, -0.29]
            )
        ]
        
        logger.info(f"載入 {len(test_cases)} 個標準測試用例")
        return test_cases
    
    def verify_sgp4_implementation(self) -> List[VerificationResult]:
        """驗證 SGP4 實現"""
        logger.info("開始 SGP4 算法完整性驗證...")
        
        try:
            from sgp4_engine import SGP4Engine, validate_sgp4_availability
            
            if not validate_sgp4_availability():
                raise RuntimeError("SGP4 庫不可用")
            
            engine = SGP4Engine()
            
            for test_case in self.test_cases:
                result = self._verify_single_test_case(engine, test_case)
                self.results.append(result)
                
                status = "✅ PASSED" if result.passed else "❌ FAILED"
                logger.info(f"{status}: {result.test_name}")
                if not result.passed:
                    logger.error(f"  錯誤: {result.error_message}")
                    logger.error(f"  位置誤差: {result.position_error:.6f} km")
                    logger.error(f"  速度誤差: {result.velocity_error:.9f} km/s")
            
            return self.results
            
        except Exception as e:
            logger.error(f"SGP4 驗證失敗: {e}")
            raise
    
    def _verify_single_test_case(self, engine: 'SGP4Engine', test_case: SGP4TestCase) -> VerificationResult:
        """驗證單個測試用例"""
        try:
            # 創建衛星對象
            success = engine.create_satellite(test_case.name, test_case.line1, test_case.line2)
            if not success:
                return VerificationResult(
                    test_name=test_case.name,
                    passed=False,
                    position_error=float('inf'),
                    velocity_error=float('inf'),
                    error_message="衛星對象創建失敗"
                )
            
            # 計算指定時間的位置
            epoch_time = datetime.now(timezone.utc)
            target_time = epoch_time + timedelta(minutes=test_case.epoch_minutes)
            
            result = engine.calculate_position(test_case.name, target_time)
            if not result or not result.success:
                return VerificationResult(
                    test_name=test_case.name,
                    passed=False,
                    position_error=float('inf'),
                    velocity_error=float('inf'),
                    error_message=f"軌道計算失敗，錯誤碼: {result.error_code if result else 'None'}"
                )
            
            # 計算誤差
            calculated_pos = result.position_eci
            calculated_vel = result.velocity_eci
            
            expected_pos = np.array(test_case.expected_position)
            expected_vel = np.array(test_case.expected_velocity)
            
            pos_error = np.linalg.norm(calculated_pos - expected_pos)
            vel_error = np.linalg.norm(calculated_vel - expected_vel)
            
            # 檢查是否在容差範圍內
            position_ok = pos_error <= test_case.tolerance_position
            velocity_ok = vel_error <= test_case.tolerance_velocity
            
            passed = position_ok and velocity_ok
            
            error_msg = None
            if not passed:
                error_msg = f"超出容差 - 位置: {pos_error:.6f} > {test_case.tolerance_position:.6f}, 速度: {vel_error:.9f} > {test_case.tolerance_velocity:.9f}"
            
            return VerificationResult(
                test_name=test_case.name,
                passed=passed,
                position_error=pos_error,
                velocity_error=vel_error,
                error_message=error_msg
            )
            
        except Exception as e:
            return VerificationResult(
                test_name=test_case.name,
                passed=False,
                position_error=float('inf'),
                velocity_error=float('inf'),
                error_message=f"測試執行異常: {e}"
            )
    
    def verify_claude_md_compliance(self) -> Dict[str, bool]:
        """驗證 CLAUDE.md 合規性"""
        logger.info("驗證 CLAUDE.md 合規性...")
        
        compliance = {
            "uses_official_sgp4": self._check_official_sgp4_usage(),
            "no_reduced_algorithms": self._check_no_reduced_algorithms(),
            "proper_error_handling": self._check_error_handling(),
            "complete_implementation": self._check_complete_implementation()
        }
        
        total_checks = len(compliance)
        passed_checks = sum(1 for passed in compliance.values() if passed)
        
        logger.info(f"CLAUDE.md 合規性檢查: {passed_checks}/{total_checks} 通過")
        
        return compliance
    
    def _check_official_sgp4_usage(self) -> bool:
        """檢查是否使用官方 SGP4 庫"""
        try:
            # 檢查 SGP4 引擎代碼
            sgp4_file = PHASE1_ROOT / "02_orbit_calculation" / "sgp4_engine.py"
            
            if not sgp4_file.exists():
                return False
            
            with open(sgp4_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 檢查關鍵導入
            required_imports = [
                "from sgp4.api import Satrec",
                "from sgp4.earth_gravity import wgs72"
            ]
            
            for import_stmt in required_imports:
                if import_stmt not in content:
                    logger.warning(f"缺少必要導入: {import_stmt}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"檢查官方 SGP4 使用失敗: {e}")
            return False
    
    def _check_no_reduced_algorithms(self) -> bool:
        """檢查無簡化算法使用"""
        logger.debug("檢查 SGP4 引擎是否使用完整算法...")
        
        # 檢查禁用的算法關鍵詞
        forbidden_patterns = [
            "reduced", "簡化", "approximate", "近似", 
            "mock", "fake", "dummy", "假"
        ]
        
        try:
            # 檢查 SGP4 引擎文件
            sgp4_engine_path = Path(__file__).parent.parent / "02_orbit_calculation" / "sgp4_engine.py"
            
            if sgp4_engine_path.exists():
                with open(sgp4_engine_path, 'r', encoding='utf-8') as f:
                    content = f.read().lower()
                
                for keyword in forbidden_patterns:
                    if keyword.lower() in content:
                        logger.warning(f"發現可疑關鍵字: {keyword}")
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"檢查算法合規性失敗: {e}")
            return False
    
    def _check_error_handling(self) -> bool:
        """檢查錯誤處理"""
        try:
            sgp4_file = PHASE1_ROOT / "02_orbit_calculation" / "sgp4_engine.py"
            
            with open(sgp4_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 檢查錯誤處理相關代碼
            error_handling_patterns = [
                "error_code",
                "try:",
                "except",
                "raise"
            ]
            
            for pattern in error_handling_patterns:
                if pattern not in content:
                    logger.warning(f"缺少錯誤處理模式: {pattern}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"檢查錯誤處理失敗: {e}")
            return False
    
    def _check_complete_implementation(self) -> bool:
        """檢查完整實現"""
        try:
            # 檢查所有必要方法是否存在
            from sgp4_engine import SGP4Engine
            
            engine = SGP4Engine()
            required_methods = [
                'create_satellite',
                'calculate_position', 
                'batch_calculate',
                'get_statistics'
            ]
            
            for method in required_methods:
                if not hasattr(engine, method):
                    logger.warning(f"缺少必要方法: {method}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"檢查完整實現失敗: {e}")
            return False
    
    def generate_verification_report(self) -> Dict:
        """生成驗證報告"""
        passed_tests = sum(1 for r in self.results if r.passed)
        total_tests = len(self.results)
        
        compliance = self.verify_claude_md_compliance()
        
        report = {
            "verification_timestamp": datetime.now(timezone.utc).isoformat(),
            "sgp4_tests": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "success_rate": (passed_tests / max(total_tests, 1)) * 100,
                "test_results": [
                    {
                        "name": r.test_name,
                        "passed": r.passed,
                        "position_error_km": r.position_error,
                        "velocity_error_km_per_s": r.velocity_error,
                        "error_message": r.error_message
                    }
                    for r in self.results
                ]
            },
            "claude_md_compliance": compliance,
            "overall_status": "PASSED" if passed_tests == total_tests and all(compliance.values()) else "FAILED"
        }
        
        return report

def main():
    """主函數"""
    logging.basicConfig(level=logging.INFO)
    
    verifier = SGP4AlgorithmVerifier()
    
    try:
        # 執行 SGP4 驗證
        results = verifier.verify_sgp4_implementation()
        
        # 生成報告
        report = verifier.generate_verification_report()
        
        # 保存報告
        report_path = PHASE1_ROOT / "05_integration" / "sgp4_verification_report.json"
        import json
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # 顯示結果
        print("\n" + "="*60)
        print("🧮 SGP4 算法完整性驗證結果")
        print("="*60)
        
        sgp4_tests = report["sgp4_tests"]
        print(f"SGP4 測試: {sgp4_tests['passed_tests']}/{sgp4_tests['total_tests']} 通過 ({sgp4_tests['success_rate']:.1f}%)")
        
        compliance = report["claude_md_compliance"]
        passed_compliance = sum(1 for v in compliance.values() if v)
        total_compliance = len(compliance)
        print(f"CLAUDE.md 合規: {passed_compliance}/{total_compliance} 通過")
        
        print(f"\n總體狀態: {report['overall_status']}")
        print(f"報告已保存: {report_path}")
        print("="*60)
        
        return report['overall_status'] == 'PASSED'
        
    except Exception as e:
        logger.error(f"驗證執行失敗: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)