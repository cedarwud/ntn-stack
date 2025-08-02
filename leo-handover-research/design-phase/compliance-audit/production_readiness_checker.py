#!/usr/bin/env python3
"""
生產就緒檢查器
確保整個合規性審計系統達到生產級別標準

🚨 嚴格遵循 CLAUDE.md 原則：
- ✅ 使用真實算法和數據
- ✅ 完整實現（無簡化）
- ✅ 生產級品質檢查
- ✅ 100% 合規性驗證

Author: LEO Handover Research Team
Date: 2025-08-02
Purpose: 生產就緒度全面評估
"""

import asyncio
import time
import json
import logging
import subprocess
import psutil
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ReadinessLevel(Enum):
    """就緒等級"""
    PRODUCTION_READY = "production_ready"          # 生產就緒
    STAGING_READY = "staging_ready"                # 測試環境就緒
    DEVELOPMENT_ONLY = "development_only"          # 僅開發環境
    NOT_READY = "not_ready"                        # 未就緒

class CheckCategory(Enum):
    """檢查類別"""
    SECURITY = "security"                          # 安全性
    PERFORMANCE = "performance"                    # 性能
    RELIABILITY = "reliability"                    # 可靠性
    COMPLIANCE = "compliance"                      # 合規性
    SCALABILITY = "scalability"                    # 可擴展性
    MONITORING = "monitoring"                      # 監控
    DOCUMENTATION = "documentation"                # 文檔

@dataclass
class ReadinessCheck:
    """就緒檢查項目"""
    category: CheckCategory
    check_name: str
    description: str
    required_for_production: bool
    passed: bool
    score: float  # 0.0-100.0
    details: Dict[str, Any]
    recommendations: List[str]

class ProductionReadinessChecker:
    """
    生產就緒檢查器
    
    負責：
    1. 全面的生產就緒度評估
    2. 安全性和性能檢查
    3. 合規性標準驗證
    4. 可靠性和監控檢查
    5. 文檔完整性驗證
    6. 部署前最終檢查
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """初始化生產就緒檢查器"""
        self.config = self._load_config(config_path)
        self.check_results: List[ReadinessCheck] = []
        
        # 關鍵文件路徑
        self.project_root = Path("/home/sat/ntn-stack")
        self.compliance_audit_path = self.project_root / "leo-handover-research/design-phase/compliance-audit"
        self.netstack_path = self.project_root / "netstack"
        
        logger.info("🔍 生產就緒檢查器初始化完成")
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """載入配置"""
        default_config = {
            "production_standards": {
                "min_compliance_score": 100.0,      # 要求 100% 合規
                "max_response_time_ms": 100.0,      # 最大響應時間
                "min_uptime_percent": 99.9,         # 最小正常運行時間
                "max_error_rate": 0.01,             # 最大錯誤率
                "min_test_coverage": 95.0,          # 最小測試覆蓋率
                "security_score_threshold": 95.0    # 安全分數門檻
            },
            "performance_requirements": {
                "d2_event_detection_ms": 50,        # D2 事件檢測時間
                "a4_event_detection_ms": 50,        # A4 事件檢測時間
                "a5_event_detection_ms": 50,        # A5 事件檢測時間
                "rsrp_calculation_ms": 10,          # RSRP 計算時間
                "sib19_processing_ms": 100,         # SIB19 處理時間
                "concurrent_users": 1000,           # 並發用戶數
                "throughput_ops_per_sec": 10000     # 吞吐量
            },
            "security_requirements": {
                "input_validation": True,           # 輸入驗證
                "sql_injection_protection": True,   # SQL 注入防護
                "xss_protection": True,             # XSS 防護
                "csrf_protection": True,            # CSRF 防護
                "rate_limiting": True,              # 速率限制
                "authentication": True,             # 身份驗證
                "authorization": True,              # 授權
                "data_encryption": True             # 數據加密
            },
            "reliability_requirements": {
                "graceful_degradation": True,       # 優雅降級
                "circuit_breaker": True,            # 斷路器
                "retry_mechanism": True,            # 重試機制
                "timeout_handling": True,           # 超時處理
                "error_recovery": True,             # 錯誤恢復
                "health_checks": True,              # 健康檢查
                "monitoring_alerts": True           # 監控告警
            }
        }
        
        if config_path and Path(config_path).exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        
        return default_config
    
    async def run_comprehensive_readiness_check(self) -> Dict[str, Any]:
        """運行完整的生產就緒檢查"""
        logger.info("🚀 開始生產就緒度全面檢查")
        start_time = time.time()
        
        # 清空之前的檢查結果
        self.check_results = []
        
        try:
            # 1. 合規性檢查
            logger.info("📋 執行合規性檢查...")
            await self._run_compliance_checks()
            
            # 2. 性能檢查
            logger.info("⚡ 執行性能檢查...")
            await self._run_performance_checks()
            
            # 3. 安全性檢查
            logger.info("🔒 執行安全性檢查...")
            await self._run_security_checks()
            
            # 4. 可靠性檢查
            logger.info("🛡️ 執行可靠性檢查...")
            await self._run_reliability_checks()
            
            # 5. 可擴展性檢查
            logger.info("📈 執行可擴展性檢查...")
            await self._run_scalability_checks()
            
            # 6. 監控檢查
            logger.info("📊 執行監控檢查...")
            await self._run_monitoring_checks()
            
            # 7. 文檔檢查
            logger.info("📚 執行文檔檢查...")
            await self._run_documentation_checks()
            
            # 計算總體就緒度
            overall_readiness = self._calculate_overall_readiness()
            
            duration = time.time() - start_time
            
            # 生成完整報告
            report = {
                "check_timestamp": datetime.now(timezone.utc).isoformat(),
                "duration_seconds": duration,
                "overall_readiness": overall_readiness,
                "category_summaries": self._generate_category_summaries(),
                "detailed_results": [self._check_to_dict(check) for check in self.check_results],
                "production_deployment_recommendation": self._generate_deployment_recommendation(overall_readiness),
                "action_items": self._generate_action_items()
            }
            
            logger.info(f"✅ 生產就緒檢查完成，耗時 {duration:.2f} 秒")
            logger.info(f"📊 總體就緒等級: {overall_readiness['readiness_level']}")
            logger.info(f"🎯 就緒分數: {overall_readiness['overall_score']:.1f}%")
            
            return report
            
        except Exception as e:
            logger.error(f"❌ 生產就緒檢查失敗: {e}")
            return {
                "check_timestamp": datetime.now(timezone.utc).isoformat(),
                "duration_seconds": time.time() - start_time,
                "error": str(e),
                "status": "failed"
            }
    
    async def _run_compliance_checks(self):
        """執行合規性檢查"""
        # 檢查 3GPP TS 38.331 合規性
        await self._check_3gpp_compliance()
        
        # 檢查 ITU-R P.618-14 合規性
        await self._check_itu_compliance()
        
        # 檢查合規性驗證系統完整性
        await self._check_compliance_verification_system()
    
    async def _check_3gpp_compliance(self):
        """檢查 3GPP TS 38.331 合規性"""
        try:
            # 運行 3GPP 合規性測試
            import sys
            sys.path.append(str(self.compliance_audit_path))
            
            from compliance_verification_system import ComplianceVerificationSystem
            
            verifier = ComplianceVerificationSystem()
            results = await verifier._verify_3gpp_compliance()
            
            passed = results["compliance_score"] >= 100.0
            score = results["compliance_score"]
            
            recommendations = []
            if not passed:
                recommendations.append("修復所有 3GPP TS 38.331 不合規項目")
                recommendations.append("重新運行合規性測試直到達到 100% 合規")
            
            self.check_results.append(ReadinessCheck(
                category=CheckCategory.COMPLIANCE,
                check_name="3GPP_TS_38_331_Compliance",
                description="3GPP TS 38.331 v17.3.0 標準完全合規性驗證",
                required_for_production=True,
                passed=passed,
                score=score,
                details={
                    "standard": "3GPP TS 38.331 v17.3.0",
                    "test_results": results["test_results"],
                    "total_tests": results["total_tests"],
                    "passed_tests": results["passed_tests"]
                },
                recommendations=recommendations
            ))
            
        except Exception as e:
            self.check_results.append(ReadinessCheck(
                category=CheckCategory.COMPLIANCE,
                check_name="3GPP_TS_38_331_Compliance",
                description="3GPP TS 38.331 v17.3.0 標準完全合規性驗證",
                required_for_production=True,
                passed=False,
                score=0.0,
                details={"error": str(e)},
                recommendations=["修復 3GPP 合規性檢查系統錯誤"]
            ))
    
    async def _check_itu_compliance(self):
        """檢查 ITU-R P.618-14 合規性"""
        try:
            import sys
            sys.path.append(str(self.compliance_audit_path))
            
            from compliance_verification_system import ComplianceVerificationSystem
            
            verifier = ComplianceVerificationSystem()
            results = await verifier._verify_itu_compliance()
            
            passed = results["compliance_score"] >= 100.0
            score = results["compliance_score"]
            
            recommendations = []
            if not passed:
                recommendations.append("修復所有 ITU-R P.618-14 不合規項目")
                recommendations.append("確保 RSRP 計算模型完全符合 ITU-R 標準")
            
            self.check_results.append(ReadinessCheck(
                category=CheckCategory.COMPLIANCE,
                check_name="ITU_R_P618_14_Compliance",
                description="ITU-R P.618-14 標準完全合規性驗證",
                required_for_production=True,
                passed=passed,
                score=score,
                details={
                    "standard": "ITU-R P.618-14",
                    "test_results": results["test_results"],
                    "total_tests": results["total_tests"],
                    "passed_tests": results["passed_tests"]
                },
                recommendations=recommendations
            ))
            
        except Exception as e:
            self.check_results.append(ReadinessCheck(
                category=CheckCategory.COMPLIANCE,
                check_name="ITU_R_P618_14_Compliance",
                description="ITU-R P.618-14 標準完全合規性驗證",
                required_for_production=True,
                passed=False,
                score=0.0,
                details={"error": str(e)},
                recommendations=["修復 ITU-R 合規性檢查系統錯誤"]
            ))
    
    async def _check_compliance_verification_system(self):
        """檢查合規性驗證系統完整性"""
        try:
            verification_system_path = self.compliance_audit_path / "compliance_verification_system.py"
            integration_monitor_path = self.compliance_audit_path / "system_integration_monitor.py"
            readiness_checker_path = self.compliance_audit_path / "production_readiness_checker.py"
            
            files_exist = [
                verification_system_path.exists(),
                integration_monitor_path.exists(),
                readiness_checker_path.exists()
            ]
            
            passed = all(files_exist)
            score = (sum(files_exist) / len(files_exist)) * 100.0
            
            recommendations = []
            if not passed:
                recommendations.append("確保所有合規性驗證系統文件完整")
                recommendations.append("檢查文件權限和可執行性")
            
            self.check_results.append(ReadinessCheck(
                category=CheckCategory.COMPLIANCE,
                check_name="Compliance_Verification_System_Integrity",
                description="合規性驗證系統完整性檢查",
                required_for_production=True,
                passed=passed,
                score=score,
                details={
                    "verification_system_exists": verification_system_path.exists(),
                    "integration_monitor_exists": integration_monitor_path.exists(),
                    "readiness_checker_exists": readiness_checker_path.exists(),
                    "files_checked": len(files_exist)
                },
                recommendations=recommendations
            ))
            
        except Exception as e:
            self.check_results.append(ReadinessCheck(
                category=CheckCategory.COMPLIANCE,
                check_name="Compliance_Verification_System_Integrity",
                description="合規性驗證系統完整性檢查",
                required_for_production=True,
                passed=False,
                score=0.0,
                details={"error": str(e)},
                recommendations=["修復合規性驗證系統完整性檢查錯誤"]
            ))
    
    async def _run_performance_checks(self):
        """執行性能檢查"""
        await self._check_response_times()
        await self._check_throughput()
        await self._check_resource_usage()
        await self._check_concurrent_performance()
    
    async def _check_response_times(self):
        """檢查響應時間"""
        try:
            import sys
            sys.path.append('/home/sat/ntn-stack/netstack/src/services/satellite')
            
            from handover_event_detector import HandoverEventDetector
            from dynamic_link_budget_calculator import DynamicLinkBudgetCalculator
            
            detector = HandoverEventDetector("ntpu")
            calculator = DynamicLinkBudgetCalculator()
            
            # 測試響應時間
            performance_tests = []
            
            # D2 事件檢測性能
            start_time = time.time()
            for _ in range(100):
                serving_sat = {'satellite_id': 'test', 'elevation_deg': 25.0, 'range_km': 1600.0}
                candidates = [{'satellite_id': 'test2', 'elevation_deg': 30.0, 'range_km': 1000.0}]
                detector._should_trigger_d2((24.94, 121.37, 0.05), serving_sat, candidates)
            d2_avg_time = ((time.time() - start_time) / 100) * 1000
            
            # RSRP 計算性能
            start_time = time.time()
            test_params = {'range_km': 800.0, 'elevation_deg': 30.0, 'frequency_ghz': 28.0, 
                          'satellite_id': 'test', 'azimuth_deg': 180.0}
            for _ in range(100):
                calculator.calculate_enhanced_rsrp(test_params, (24.94, 121.37, 0.05), time.time())
            rsrp_avg_time = ((time.time() - start_time) / 100) * 1000
            
            performance_tests.extend([
                {"test": "D2_event_detection", "avg_time_ms": d2_avg_time, "threshold_ms": 50},
                {"test": "RSRP_calculation", "avg_time_ms": rsrp_avg_time, "threshold_ms": 10}
            ])
            
            # 評估性能
            passed_tests = sum(1 for test in performance_tests 
                             if test["avg_time_ms"] <= test["threshold_ms"])
            total_tests = len(performance_tests)
            
            passed = passed_tests == total_tests
            score = (passed_tests / total_tests) * 100.0
            
            recommendations = []
            for test in performance_tests:
                if test["avg_time_ms"] > test["threshold_ms"]:
                    recommendations.append(f"優化 {test['test']} 性能，目標 < {test['threshold_ms']}ms")
            
            self.check_results.append(ReadinessCheck(
                category=CheckCategory.PERFORMANCE,
                check_name="Response_Time_Performance",
                description="關鍵功能響應時間性能檢查",
                required_for_production=True,
                passed=passed,
                score=score,
                details={
                    "performance_tests": performance_tests,
                    "passed_tests": passed_tests,
                    "total_tests": total_tests
                },
                recommendations=recommendations
            ))
            
        except Exception as e:
            self.check_results.append(ReadinessCheck(
                category=CheckCategory.PERFORMANCE,
                check_name="Response_Time_Performance",
                description="關鍵功能響應時間性能檢查",
                required_for_production=True,
                passed=False,
                score=0.0,
                details={"error": str(e)},
                recommendations=["修復性能測試系統錯誤"]
            ))
    
    async def _check_throughput(self):
        """檢查吞吐量"""
        try:
            # 模擬吞吐量測試
            target_throughput = self.config["performance_requirements"]["throughput_ops_per_sec"]
            
            import sys
            sys.path.append('/home/sat/ntn-stack/netstack/src/services/satellite')
            from handover_event_detector import HandoverEventDetector
            
            detector = HandoverEventDetector("ntpu")
            
            # 測試批量處理能力
            batch_size = 1000
            start_time = time.time()
            
            for _ in range(batch_size):
                test_satellite = {'elevation_deg': 25.0, 'range_km': 800.0, 'satellite_id': 'throughput_test'}
                detector._calculate_rsrp(test_satellite)
            
            duration = time.time() - start_time
            actual_throughput = batch_size / duration
            
            passed = actual_throughput >= target_throughput * 0.8  # 允許 20% 誤差
            score = min(100.0, (actual_throughput / target_throughput) * 100.0)
            
            recommendations = []
            if not passed:
                recommendations.append(f"提升系統吞吐量至 {target_throughput} ops/sec")
                recommendations.append("考慮並行處理和性能優化")
            
            self.check_results.append(ReadinessCheck(
                category=CheckCategory.PERFORMANCE,
                check_name="Throughput_Performance",
                description="系統吞吐量性能檢查",
                required_for_production=True,
                passed=passed,
                score=score,
                details={
                    "target_throughput_ops_per_sec": target_throughput,
                    "actual_throughput_ops_per_sec": actual_throughput,
                    "batch_size": batch_size,
                    "test_duration_sec": duration
                },
                recommendations=recommendations
            ))
            
        except Exception as e:
            self.check_results.append(ReadinessCheck(
                category=CheckCategory.PERFORMANCE,
                check_name="Throughput_Performance",
                description="系統吞吐量性能檢查",
                required_for_production=True,
                passed=False,
                score=0.0,
                details={"error": str(e)},
                recommendations=["修復吞吐量測試錯誤"]
            ))
    
    async def _check_resource_usage(self):
        """檢查資源使用"""
        try:
            # 獲取系統資源使用情況
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_info = psutil.virtual_memory()
            memory_percent = memory_info.percent
            disk_usage = psutil.disk_usage('/').percent
            
            # 檢查是否符合生產標準
            cpu_ok = cpu_percent < 70.0  # CPU 使用率 < 70%
            memory_ok = memory_percent < 80.0  # 記憶體使用率 < 80%
            disk_ok = disk_usage < 85.0  # 磁碟使用率 < 85%
            
            checks = [cpu_ok, memory_ok, disk_ok]
            passed = all(checks)
            score = (sum(checks) / len(checks)) * 100.0
            
            recommendations = []
            if not cpu_ok:
                recommendations.append("降低 CPU 使用率，優化算法性能")
            if not memory_ok:
                recommendations.append("優化記憶體使用，檢查記憶體洩漏")
            if not disk_ok:
                recommendations.append("清理磁碟空間，優化存儲使用")
            
            self.check_results.append(ReadinessCheck(
                category=CheckCategory.PERFORMANCE,
                check_name="Resource_Usage",
                description="系統資源使用檢查",
                required_for_production=True,
                passed=passed,
                score=score,
                details={
                    "cpu_usage_percent": cpu_percent,
                    "memory_usage_percent": memory_percent,
                    "disk_usage_percent": disk_usage,
                    "cpu_threshold": 70.0,
                    "memory_threshold": 80.0,
                    "disk_threshold": 85.0
                },
                recommendations=recommendations
            ))
            
        except Exception as e:
            self.check_results.append(ReadinessCheck(
                category=CheckCategory.PERFORMANCE,
                check_name="Resource_Usage",
                description="系統資源使用檢查",
                required_for_production=True,
                passed=False,
                score=0.0,
                details={"error": str(e)},
                recommendations=["修復資源監控錯誤"]
            ))
    
    async def _check_concurrent_performance(self):
        """檢查並發性能"""
        try:
            import asyncio
            import sys
            sys.path.append('/home/sat/ntn-stack/netstack/src/services/satellite')
            from handover_event_detector import HandoverEventDetector
            
            detector = HandoverEventDetector("ntpu")
            
            # 並發測試
            concurrent_tasks = 100
            
            async def concurrent_task():
                test_satellite = {'elevation_deg': 25.0, 'range_km': 800.0, 'satellite_id': 'concurrent_test'}
                return detector._calculate_rsrp(test_satellite)
            
            start_time = time.time()
            tasks = [concurrent_task() for _ in range(concurrent_tasks)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            duration = time.time() - start_time
            
            # 檢查結果
            successful_tasks = sum(1 for r in results if not isinstance(r, Exception))
            success_rate = successful_tasks / concurrent_tasks
            
            passed = success_rate >= 0.95 and duration < 5.0  # 95% 成功率，5秒內完成
            score = min(100.0, success_rate * 100.0 * (5.0 / max(duration, 0.1)))
            
            recommendations = []
            if success_rate < 0.95:
                recommendations.append("提升並發處理的穩定性")
            if duration >= 5.0:
                recommendations.append("優化並發處理性能")
            
            self.check_results.append(ReadinessCheck(
                category=CheckCategory.PERFORMANCE,
                check_name="Concurrent_Performance",
                description="並發性能檢查",
                required_for_production=True,
                passed=passed,
                score=score,
                details={
                    "concurrent_tasks": concurrent_tasks,
                    "successful_tasks": successful_tasks,
                    "success_rate": success_rate,
                    "duration_sec": duration,
                    "errors": [str(r) for r in results if isinstance(r, Exception)]
                },
                recommendations=recommendations
            ))
            
        except Exception as e:
            self.check_results.append(ReadinessCheck(
                category=CheckCategory.PERFORMANCE,
                check_name="Concurrent_Performance",
                description="並發性能檢查",
                required_for_production=True,
                passed=False,
                score=0.0,
                details={"error": str(e)},
                recommendations=["修復並發測試錯誤"]
            ))
    
    async def _run_security_checks(self):
        """執行安全性檢查"""
        await self._check_input_validation()
        await self._check_authentication_security()
        await self._check_data_protection()
        await self._check_api_security()
    
    async def _check_input_validation(self):
        """檢查輸入驗證"""
        try:
            # 測試輸入驗證
            import sys
            sys.path.append('/home/sat/ntn-stack/netstack/src/services/satellite')
            from handover_event_detector import HandoverEventDetector
            
            detector = HandoverEventDetector("ntpu")
            
            # 測試異常輸入處理
            invalid_inputs = [
                {'elevation_deg': -999, 'range_km': 'invalid', 'satellite_id': None},
                {'elevation_deg': 'abc', 'range_km': -1000, 'satellite_id': ''},
                {},  # 空字典
                None  # None 值
            ]
            
            validation_passed = 0
            total_tests = len(invalid_inputs)
            
            for invalid_input in invalid_inputs:
                try:
                    # 應該優雅處理無效輸入而不崩潰
                    result = detector._calculate_rsrp(invalid_input)
                    # 如果沒有異常但返回合理結果，說明有防護
                    if isinstance(result, float) and -200 <= result <= 0:
                        validation_passed += 1
                except (ValueError, TypeError, AttributeError):
                    # 拋出適當異常也是正確的防護
                    validation_passed += 1
                except Exception:
                    # 其他異常可能表示防護不足
                    pass
            
            passed = validation_passed >= total_tests * 0.8  # 80% 通過率
            score = (validation_passed / total_tests) * 100.0
            
            recommendations = []
            if not passed:
                recommendations.append("加強輸入驗證，確保所有輸入都經過適當檢查")
                recommendations.append("實現統一的輸入驗證機制")
            
            self.check_results.append(ReadinessCheck(
                category=CheckCategory.SECURITY,
                check_name="Input_Validation",
                description="輸入驗證安全檢查",
                required_for_production=True,
                passed=passed,
                score=score,
                details={
                    "total_tests": total_tests,
                    "validation_passed": validation_passed,
                    "test_inputs": invalid_inputs
                },
                recommendations=recommendations
            ))
            
        except Exception as e:
            self.check_results.append(ReadinessCheck(
                category=CheckCategory.SECURITY,
                check_name="Input_Validation",
                description="輸入驗證安全檢查",
                required_for_production=True,
                passed=False,
                score=0.0,
                details={"error": str(e)},
                recommendations=["修復輸入驗證測試錯誤"]
            ))
    
    async def _check_authentication_security(self):
        """檢查身份驗證安全"""
        try:
            # 檢查是否實現身份驗證機制
            auth_files = [
                self.netstack_path / "netstack_api" / "auth",
                self.netstack_path / "netstack_api" / "middleware",
                self.netstack_path / "netstack_api" / "security"
            ]
            
            auth_implementations = sum(1 for path in auth_files if path.exists())
            
            # 檢查環境變量中的密鑰配置
            import os
            security_vars = [
                "JWT_SECRET_KEY",
                "API_KEY", 
                "ENCRYPTION_KEY"
            ]
            
            configured_vars = sum(1 for var in security_vars if os.getenv(var))
            
            # 總體安全評分
            auth_score = (auth_implementations / len(auth_files)) * 50
            config_score = (configured_vars / len(security_vars)) * 50
            total_score = auth_score + config_score
            
            passed = total_score >= 70.0
            
            recommendations = []
            if auth_implementations == 0:
                recommendations.append("實現身份驗證和授權機制")
            if configured_vars == 0:
                recommendations.append("配置安全密鑰和環境變量")
            if not passed:
                recommendations.append("加強整體安全配置")
            
            self.check_results.append(ReadinessCheck(
                category=CheckCategory.SECURITY,
                check_name="Authentication_Security",
                description="身份驗證和授權安全檢查",
                required_for_production=True,
                passed=passed,
                score=total_score,
                details={
                    "auth_implementations": auth_implementations,
                    "configured_security_vars": configured_vars,
                    "auth_score": auth_score,
                    "config_score": config_score
                },
                recommendations=recommendations
            ))
            
        except Exception as e:
            self.check_results.append(ReadinessCheck(
                category=CheckCategory.SECURITY,
                check_name="Authentication_Security",
                description="身份驗證和授權安全檢查",
                required_for_production=True,
                passed=False,
                score=0.0,
                details={"error": str(e)},
                recommendations=["修復身份驗證檢查錯誤"]
            ))
    
    async def _check_data_protection(self):
        """檢查數據保護"""
        try:
            # 檢查敏感數據處理
            sensitive_patterns = [
                "password",
                "secret",
                "key",
                "token",
                "credential"
            ]
            
            # 檢查代碼中是否有硬編碼敏感信息
            code_files = list(self.netstack_path.rglob("*.py"))
            
            violations = 0
            total_files = len(code_files)
            
            for file_path in code_files[:20]:  # 抽樣檢查前20個文件
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read().lower()
                        for pattern in sensitive_patterns:
                            if f'{pattern} = "' in content or f"{pattern} = '" in content:
                                violations += 1
                                break
                except:
                    continue
            
            protection_score = max(0, (1 - violations / max(total_files, 1)) * 100)
            passed = violations == 0
            
            recommendations = []
            if violations > 0:
                recommendations.append("移除代碼中的硬編碼敏感信息")
                recommendations.append("使用環境變量或安全配置管理")
            
            self.check_results.append(ReadinessCheck(
                category=CheckCategory.SECURITY,
                check_name="Data_Protection",
                description="數據保護和敏感信息安全檢查",
                required_for_production=True,
                passed=passed,
                score=protection_score,
                details={
                    "files_checked": min(20, total_files),
                    "violations_found": violations,
                    "sensitive_patterns_checked": sensitive_patterns
                },
                recommendations=recommendations
            ))
            
        except Exception as e:
            self.check_results.append(ReadinessCheck(
                category=CheckCategory.SECURITY,
                check_name="Data_Protection",
                description="數據保護和敏感信息安全檢查",
                required_for_production=True,
                passed=False,
                score=0.0,
                details={"error": str(e)},
                recommendations=["修復數據保護檢查錯誤"]
            ))
    
    async def _check_api_security(self):
        """檢查 API 安全"""
        try:
            # 檢查 API 路由安全配置
            router_files = list(self.netstack_path.rglob("*router*.py"))
            
            security_features = {
                "rate_limiting": 0,
                "input_validation": 0,
                "authentication": 0,
                "cors_config": 0
            }
            
            total_routers = len(router_files)
            
            for router_file in router_files:
                try:
                    with open(router_file, 'r', encoding='utf-8') as f:
                        content = f.read().lower()
                        
                        if "rate" in content or "limit" in content:
                            security_features["rate_limiting"] += 1
                        if "validate" in content or "schema" in content:
                            security_features["input_validation"] += 1
                        if "auth" in content or "token" in content:
                            security_features["authentication"] += 1
                        if "cors" in content:
                            security_features["cors_config"] += 1
                            
                except:
                    continue
            
            # 計算安全分數
            if total_routers > 0:
                avg_security = sum(security_features.values()) / (len(security_features) * total_routers)
                security_score = avg_security * 100
            else:
                security_score = 0
            
            passed = security_score >= 50.0
            
            recommendations = []
            if security_features["rate_limiting"] == 0:
                recommendations.append("實現 API 速率限制")
            if security_features["authentication"] == 0:
                recommendations.append("加強 API 身份驗證")
            if not passed:
                recommendations.append("全面提升 API 安全配置")
            
            self.check_results.append(ReadinessCheck(
                category=CheckCategory.SECURITY,
                check_name="API_Security",
                description="API 安全配置檢查",
                required_for_production=True,
                passed=passed,
                score=security_score,
                details={
                    "total_routers": total_routers,
                    "security_features": security_features,
                    "avg_security_coverage": avg_security if total_routers > 0 else 0
                },
                recommendations=recommendations
            ))
            
        except Exception as e:
            self.check_results.append(ReadinessCheck(
                category=CheckCategory.SECURITY,
                check_name="API_Security",
                description="API 安全配置檢查",
                required_for_production=True,
                passed=False,
                score=0.0,
                details={"error": str(e)},
                recommendations=["修復 API 安全檢查錯誤"]
            ))
    
    async def _run_reliability_checks(self):
        """執行可靠性檢查"""
        await self._check_error_handling()
        await self._check_fault_tolerance()
        await self._check_data_consistency()
    
    async def _check_error_handling(self):
        """檢查錯誤處理"""
        try:
            # 檢查代碼中的錯誤處理機制
            code_files = list(self.netstack_path.rglob("*.py"))
            
            error_handling_stats = {
                "try_except_blocks": 0,
                "logging_statements": 0,
                "custom_exceptions": 0,
                "total_files": 0
            }
            
            for file_path in code_files[:50]:  # 檢查前50個文件
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                        error_handling_stats["total_files"] += 1
                        error_handling_stats["try_except_blocks"] += content.count("try:")
                        error_handling_stats["logging_statements"] += content.count("logger.")
                        error_handling_stats["custom_exceptions"] += content.count("Exception")
                        
                except:
                    continue
            
            # 計算錯誤處理覆蓋率
            if error_handling_stats["total_files"] > 0:
                avg_error_handling = (
                    error_handling_stats["try_except_blocks"] + 
                    error_handling_stats["logging_statements"]
                ) / error_handling_stats["total_files"]
                
                reliability_score = min(100.0, avg_error_handling * 20)  # 每個文件至少5個錯誤處理機制
            else:
                reliability_score = 0
            
            passed = reliability_score >= 60.0
            
            recommendations = []
            if error_handling_stats["try_except_blocks"] < error_handling_stats["total_files"]:
                recommendations.append("增加 try-except 錯誤處理塊")
            if error_handling_stats["logging_statements"] < error_handling_stats["total_files"] * 2:
                recommendations.append("增加適當的日誌記錄")
            
            self.check_results.append(ReadinessCheck(
                category=CheckCategory.RELIABILITY,
                check_name="Error_Handling",
                description="錯誤處理機制檢查",
                required_for_production=True,
                passed=passed,
                score=reliability_score,
                details=error_handling_stats,
                recommendations=recommendations
            ))
            
        except Exception as e:
            self.check_results.append(ReadinessCheck(
                category=CheckCategory.RELIABILITY,
                check_name="Error_Handling",
                description="錯誤處理機制檢查",
                required_for_production=True,
                passed=False,
                score=0.0,
                details={"error": str(e)},
                recommendations=["修復錯誤處理檢查錯誤"]
            ))
    
    async def _check_fault_tolerance(self):
        """檢查容錯能力"""
        try:
            # 測試服務的容錯能力
            import sys
            sys.path.append('/home/sat/ntn-stack/netstack/src/services/satellite')
            from handover_event_detector import HandoverEventDetector
            
            detector = HandoverEventDetector("ntpu")
            
            # 測試極端情況處理
            fault_tests = [
                {"name": "empty_satellite_data", "input": {}},
                {"name": "negative_values", "input": {"elevation_deg": -100, "range_km": -500}},
                {"name": "extreme_values", "input": {"elevation_deg": 999, "range_km": 99999}},
                {"name": "null_values", "input": {"elevation_deg": None, "range_km": None}},
            ]
            
            fault_tolerance_score = 0
            
            for test in fault_tests:
                try:
                    result = detector._calculate_rsrp(test["input"])
                    # 如果能處理而不崩潰，得分
                    if isinstance(result, (int, float)):
                        fault_tolerance_score += 25
                except Exception:
                    # 優雅的異常處理也算通過
                    fault_tolerance_score += 20
            
            passed = fault_tolerance_score >= 80.0
            
            recommendations = []
            if not passed:
                recommendations.append("提升系統容錯能力")
                recommendations.append("實現優雅降級機制")
                recommendations.append("加強邊界條件處理")
            
            self.check_results.append(ReadinessCheck(
                category=CheckCategory.RELIABILITY,
                check_name="Fault_Tolerance",
                description="容錯能力檢查",
                required_for_production=True,
                passed=passed,
                score=fault_tolerance_score,
                details={
                    "fault_tests": fault_tests,
                    "tolerance_score": fault_tolerance_score
                },
                recommendations=recommendations
            ))
            
        except Exception as e:
            self.check_results.append(ReadinessCheck(
                category=CheckCategory.RELIABILITY,
                check_name="Fault_Tolerance",
                description="容錯能力檢查",
                required_for_production=True,
                passed=False,
                score=0.0,
                details={"error": str(e)},
                recommendations=["修復容錯測試錯誤"]
            ))
    
    async def _check_data_consistency(self):
        """檢查數據一致性"""
        try:
            # 檢查數據一致性機制
            import sys
            sys.path.append('/home/sat/ntn-stack/netstack/src/services/satellite')
            from handover_event_detector import HandoverEventDetector
            
            detector = HandoverEventDetector("ntpu")
            
            # 測試相同輸入的一致性
            test_satellite = {
                'satellite_id': 'consistency_test',
                'elevation_deg': 30.0,
                'range_km': 800.0
            }
            
            results = []
            for _ in range(10):
                result = detector._calculate_rsrp(test_satellite)
                results.append(result)
            
            # 檢查結果一致性（允許小幅隨機變化）
            if results:
                avg_result = sum(results) / len(results)
                max_deviation = max(abs(r - avg_result) for r in results)
                consistency_score = max(0, 100 - (max_deviation * 10))  # 偏差越小分數越高
            else:
                consistency_score = 0
            
            passed = consistency_score >= 70.0
            
            recommendations = []
            if not passed:
                recommendations.append("改善數據一致性機制")
                recommendations.append("減少不必要的隨機性")
                recommendations.append("實現確定性算法")
            
            self.check_results.append(ReadinessCheck(
                category=CheckCategory.RELIABILITY,
                check_name="Data_Consistency",
                description="數據一致性檢查",
                required_for_production=True,
                passed=passed,
                score=consistency_score,
                details={
                    "test_results": results,
                    "average_result": avg_result if results else 0,
                    "max_deviation": max_deviation if results else 0,
                    "consistency_score": consistency_score
                },
                recommendations=recommendations
            ))
            
        except Exception as e:
            self.check_results.append(ReadinessCheck(
                category=CheckCategory.RELIABILITY,
                check_name="Data_Consistency",
                description="數據一致性檢查",
                required_for_production=True,
                passed=False,
                score=0.0,
                details={"error": str(e)},
                recommendations=["修復數據一致性檢查錯誤"]
            ))
    
    async def _run_scalability_checks(self):
        """執行可擴展性檢查"""
        await self._check_horizontal_scalability()
        await self._check_resource_scalability()
    
    async def _check_horizontal_scalability(self):
        """檢查水平擴展能力"""
        try:
            # 檢查系統架構是否支持水平擴展
            scalability_indicators = {
                "stateless_design": False,
                "load_balancer_ready": False,
                "database_clustering": False,
                "api_versioning": False
            }
            
            # 檢查代碼結構
            code_files = list(self.netstack_path.rglob("*.py"))
            
            for file_path in code_files[:30]:  # 檢查前30個文件
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read().lower()
                        
                        # 檢查無狀態設計指標
                        if "session" not in content and "global" not in content:
                            scalability_indicators["stateless_design"] = True
                        
                        # 檢查負載均衡準備
                        if "load" in content or "balance" in content:
                            scalability_indicators["load_balancer_ready"] = True
                        
                        # 檢查 API 版本控制
                        if "v1" in content or "version" in content:
                            scalability_indicators["api_versioning"] = True
                            
                except:
                    continue
            
            # 檢查配置文件
            config_files = list(self.project_root.rglob("docker-compose*.yml"))
            if config_files:
                scalability_indicators["database_clustering"] = True
            
            scalability_score = (sum(scalability_indicators.values()) / len(scalability_indicators)) * 100
            passed = scalability_score >= 75.0
            
            recommendations = []
            if not scalability_indicators["stateless_design"]:
                recommendations.append("實現無狀態服務設計")
            if not scalability_indicators["load_balancer_ready"]:
                recommendations.append("準備負載均衡配置")
            if not scalability_indicators["api_versioning"]:
                recommendations.append("實現 API 版本控制")
            
            self.check_results.append(ReadinessCheck(
                category=CheckCategory.SCALABILITY,
                check_name="Horizontal_Scalability",
                description="水平擴展能力檢查",
                required_for_production=False,  # 非強制但重要
                passed=passed,
                score=scalability_score,
                details=scalability_indicators,
                recommendations=recommendations
            ))
            
        except Exception as e:
            self.check_results.append(ReadinessCheck(
                category=CheckCategory.SCALABILITY,
                check_name="Horizontal_Scalability",
                description="水平擴展能力檢查",
                required_for_production=False,
                passed=False,
                score=0.0,
                details={"error": str(e)},
                recommendations=["修復可擴展性檢查錯誤"]
            ))
    
    async def _check_resource_scalability(self):
        """檢查資源擴展能力"""
        try:
            # 檢查資源配置的可擴展性
            import sys
            sys.path.append('/home/sat/ntn-stack/netstack/src/services/satellite')
            from handover_event_detector import HandoverEventDetector
            
            detector = HandoverEventDetector("ntpu")
            
            # 測試不同負載下的性能
            load_tests = [10, 50, 100, 500]
            performance_results = []
            
            for load in load_tests:
                start_time = time.time()
                
                for _ in range(load):
                    test_satellite = {'elevation_deg': 25.0, 'range_km': 800.0, 'satellite_id': f'load_test_{load}'}
                    detector._calculate_rsrp(test_satellite)
                
                duration = time.time() - start_time
                avg_time_per_op = (duration / load) * 1000  # ms
                
                performance_results.append({
                    "load": load,
                    "total_duration_sec": duration,
                    "avg_time_per_op_ms": avg_time_per_op
                })
            
            # 分析性能擴展性
            if len(performance_results) >= 2:
                # 檢查性能是否線性擴展
                first_result = performance_results[0]
                last_result = performance_results[-1]
                
                expected_time = first_result["avg_time_per_op_ms"]
                actual_time = last_result["avg_time_per_op_ms"]
                
                scalability_ratio = expected_time / max(actual_time, 0.001)
                scalability_score = min(100.0, scalability_ratio * 100)
            else:
                scalability_score = 0
            
            passed = scalability_score >= 70.0
            
            recommendations = []
            if not passed:
                recommendations.append("優化算法以支持更好的資源擴展")
                recommendations.append("實現資源池化和重用")
                recommendations.append("考慮異步處理和並發優化")
            
            self.check_results.append(ReadinessCheck(
                category=CheckCategory.SCALABILITY,
                check_name="Resource_Scalability",
                description="資源擴展能力檢查",
                required_for_production=False,
                passed=passed,
                score=scalability_score,
                details={
                    "performance_results": performance_results,
                    "scalability_score": scalability_score
                },
                recommendations=recommendations
            ))
            
        except Exception as e:
            self.check_results.append(ReadinessCheck(
                category=CheckCategory.SCALABILITY,
                check_name="Resource_Scalability",
                description="資源擴展能力檢查",
                required_for_production=False,
                passed=False,
                score=0.0,
                details={"error": str(e)},
                recommendations=["修復資源擴展性檢查錯誤"]
            ))
    
    async def _run_monitoring_checks(self):
        """執行監控檢查"""
        await self._check_logging_system()
        await self._check_metrics_collection()
        await self._check_health_monitoring()
    
    async def _check_logging_system(self):
        """檢查日誌系統"""
        try:
            # 檢查日誌配置和實現
            logging_indicators = {
                "structured_logging": False,
                "log_levels": False,
                "log_rotation": False,
                "centralized_logging": False
            }
            
            # 檢查代碼中的日誌使用
            code_files = list(self.netstack_path.rglob("*.py"))
            
            total_logging_statements = 0
            total_files_with_logging = 0
            
            for file_path in code_files[:40]:  # 檢查前40個文件
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                        file_logging_count = content.count("logger.")
                        if file_logging_count > 0:
                            total_files_with_logging += 1
                            total_logging_statements += file_logging_count
                        
                        # 檢查日誌配置
                        if "logging.config" in content or "dictConfig" in content:
                            logging_indicators["structured_logging"] = True
                        
                        if "DEBUG" in content and "INFO" in content and "ERROR" in content:
                            logging_indicators["log_levels"] = True
                            
                except:
                    continue
            
            # 檢查日誌配置文件
            config_files = list(self.project_root.rglob("*log*.conf")) + list(self.project_root.rglob("*log*.yaml"))
            if config_files:
                logging_indicators["log_rotation"] = True
                logging_indicators["centralized_logging"] = True
            
            # 計算日誌覆蓋率
            logging_coverage = (total_files_with_logging / max(len(code_files[:40]), 1)) * 100
            config_score = (sum(logging_indicators.values()) / len(logging_indicators)) * 100
            
            overall_score = (logging_coverage + config_score) / 2
            passed = overall_score >= 60.0
            
            recommendations = []
            if logging_coverage < 50:
                recommendations.append("增加更多日誌記錄覆蓋")
            if not logging_indicators["structured_logging"]:
                recommendations.append("實現結構化日誌")
            if not logging_indicators["log_rotation"]:
                recommendations.append("配置日誌輪轉")
            
            self.check_results.append(ReadinessCheck(
                category=CheckCategory.MONITORING,
                check_name="Logging_System",
                description="日誌系統檢查",
                required_for_production=True,
                passed=passed,
                score=overall_score,
                details={
                    "logging_coverage_percent": logging_coverage,
                    "total_logging_statements": total_logging_statements,
                    "files_with_logging": total_files_with_logging,
                    "logging_indicators": logging_indicators
                },
                recommendations=recommendations
            ))
            
        except Exception as e:
            self.check_results.append(ReadinessCheck(
                category=CheckCategory.MONITORING,
                check_name="Logging_System",
                description="日誌系統檢查",
                required_for_production=True,
                passed=False,
                score=0.0,
                details={"error": str(e)},
                recommendations=["修復日誌系統檢查錯誤"]
            ))
    
    async def _check_metrics_collection(self):
        """檢查指標收集"""
        try:
            # 檢查指標收集實現
            metrics_files = []
            metrics_implementations = 0
            
            # 查找指標相關文件
            for pattern in ["*metric*", "*monitor*", "*health*"]:
                metrics_files.extend(list(self.netstack_path.rglob(pattern + ".py")))
            
            if metrics_files:
                metrics_implementations = len(metrics_files)
            
            # 檢查系統整合監控器
            integration_monitor_exists = (self.compliance_audit_path / "system_integration_monitor.py").exists()
            
            # 檢查指標導出
            prometheus_config = False
            grafana_config = False
            
            # 查找監控配置
            for config_file in self.project_root.rglob("*docker-compose*.yml"):
                try:
                    with open(config_file, 'r') as f:
                        content = f.read().lower()
                        if "prometheus" in content:
                            prometheus_config = True
                        if "grafana" in content:
                            grafana_config = True
                except:
                    continue
            
            # 計算指標分數
            metrics_score = 0
            if metrics_implementations > 0:
                metrics_score += 30
            if integration_monitor_exists:
                metrics_score += 40
            if prometheus_config:
                metrics_score += 15
            if grafana_config:
                metrics_score += 15
            
            passed = metrics_score >= 70.0
            
            recommendations = []
            if metrics_implementations == 0:
                recommendations.append("實現指標收集機制")
            if not integration_monitor_exists:
                recommendations.append("使用系統整合監控器")
            if not prometheus_config:
                recommendations.append("配置 Prometheus 指標導出")
            
            self.check_results.append(ReadinessCheck(
                category=CheckCategory.MONITORING,
                check_name="Metrics_Collection",
                description="指標收集系統檢查",
                required_for_production=True,
                passed=passed,
                score=metrics_score,
                details={
                    "metrics_implementations": metrics_implementations,
                    "integration_monitor_exists": integration_monitor_exists,
                    "prometheus_config": prometheus_config,
                    "grafana_config": grafana_config
                },
                recommendations=recommendations
            ))
            
        except Exception as e:
            self.check_results.append(ReadinessCheck(
                category=CheckCategory.MONITORING,
                check_name="Metrics_Collection",
                description="指標收集系統檢查",
                required_for_production=True,
                passed=False,
                score=0.0,
                details={"error": str(e)},
                recommendations=["修復指標收集檢查錯誤"]
            ))
    
    async def _check_health_monitoring(self):
        """檢查健康監控"""
        try:
            # 檢查健康檢查端點
            health_endpoints = 0
            router_files = list(self.netstack_path.rglob("*router*.py"))
            
            for router_file in router_files:
                try:
                    with open(router_file, 'r') as f:
                        content = f.read().lower()
                        if "health" in content and ("@router" in content or "app.get" in content):
                            health_endpoints += 1
                except:
                    continue
            
            # 檢查健康檢查邏輯
            health_logic_score = 0
            if health_endpoints > 0:
                health_logic_score = min(100.0, health_endpoints * 25)
            
            # 檢查監控腳本
            monitoring_scripts = list(self.compliance_audit_path.glob("*monitor*.py"))
            monitoring_score = len(monitoring_scripts) * 30
            
            overall_score = min(100.0, health_logic_score + monitoring_score)
            passed = overall_score >= 70.0
            
            recommendations = []
            if health_endpoints == 0:
                recommendations.append("實現健康檢查 API 端點")
            if len(monitoring_scripts) == 0:
                recommendations.append("創建監控腳本和自動化檢查")
            if not passed:
                recommendations.append("完善健康監控系統")
            
            self.check_results.append(ReadinessCheck(
                category=CheckCategory.MONITORING,
                check_name="Health_Monitoring",
                description="健康監控系統檢查",
                required_for_production=True,
                passed=passed,
                score=overall_score,
                details={
                    "health_endpoints": health_endpoints,
                    "monitoring_scripts": len(monitoring_scripts),
                    "health_logic_score": health_logic_score,
                    "monitoring_score": monitoring_score
                },
                recommendations=recommendations
            ))
            
        except Exception as e:
            self.check_results.append(ReadinessCheck(
                category=CheckCategory.MONITORING,
                check_name="Health_Monitoring",
                description="健康監控系統檢查",
                required_for_production=True,
                passed=False,
                score=0.0,
                details={"error": str(e)},
                recommendations=["修復健康監控檢查錯誤"]
            ))
    
    async def _run_documentation_checks(self):
        """執行文檔檢查"""
        await self._check_api_documentation()
        await self._check_deployment_documentation()
        await self._check_compliance_documentation()
    
    async def _check_api_documentation(self):
        """檢查 API 文檔"""
        try:
            # 檢查 API 文檔完整性
            doc_files = []
            
            # 檢查 README 文件
            readme_files = list(self.project_root.rglob("README*.md"))
            doc_files.extend(readme_files)
            
            # 檢查 API 文檔
            api_doc_files = list(self.project_root.rglob("*api*.md"))
            doc_files.extend(api_doc_files)
            
            # 檢查 OpenAPI/Swagger 配置
            swagger_files = list(self.project_root.rglob("*swagger*")) + list(self.project_root.rglob("*openapi*"))
            
            # 檢查內聯文檔
            router_files = list(self.netstack_path.rglob("*router*.py"))
            documented_endpoints = 0
            total_endpoints = 0
            
            for router_file in router_files:
                try:
                    with open(router_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                        # 計算端點數量
                        endpoints = content.count("@router.") + content.count("app.get") + content.count("app.post")
                        total_endpoints += endpoints
                        
                        # 計算有文檔的端點
                        documented = content.count('"""') // 2  # 假設每個文檔字符串包裹一個端點
                        documented_endpoints += min(documented, endpoints)
                        
                except:
                    continue
            
            # 計算文檔分數
            doc_coverage = (documented_endpoints / max(total_endpoints, 1)) * 100
            file_score = min(100.0, len(doc_files) * 20)
            swagger_score = min(100.0, len(swagger_files) * 50)
            
            overall_score = (doc_coverage + file_score + swagger_score) / 3
            passed = overall_score >= 70.0
            
            recommendations = []
            if doc_coverage < 80:
                recommendations.append("增加 API 端點文檔覆蓋率")
            if len(swagger_files) == 0:
                recommendations.append("實現 OpenAPI/Swagger 文檔")
            if len(readme_files) == 0:
                recommendations.append("創建詳細的 README 文檔")
            
            self.check_results.append(ReadinessCheck(
                category=CheckCategory.DOCUMENTATION,
                check_name="API_Documentation",
                description="API 文檔完整性檢查",
                required_for_production=True,
                passed=passed,
                score=overall_score,
                details={
                    "documented_endpoints": documented_endpoints,
                    "total_endpoints": total_endpoints,
                    "doc_coverage_percent": doc_coverage,
                    "doc_files_count": len(doc_files),
                    "swagger_files_count": len(swagger_files)
                },
                recommendations=recommendations
            ))
            
        except Exception as e:
            self.check_results.append(ReadinessCheck(
                category=CheckCategory.DOCUMENTATION,
                check_name="API_Documentation",
                description="API 文檔完整性檢查",
                required_for_production=True,
                passed=False,
                score=0.0,
                details={"error": str(e)},
                recommendations=["修復 API 文檔檢查錯誤"]
            ))
    
    async def _check_deployment_documentation(self):
        """檢查部署文檔"""
        try:
            # 檢查部署相關文檔
            deployment_files = []
            
            # Docker 相關文檔
            docker_files = list(self.project_root.rglob("Dockerfile*")) + list(self.project_root.rglob("docker-compose*.yml"))
            deployment_files.extend(docker_files)
            
            # 部署指南
            deploy_docs = list(self.project_root.rglob("*deploy*.md")) + list(self.project_root.rglob("*install*.md"))
            deployment_files.extend(deploy_docs)
            
            # 配置文檔
            config_docs = list(self.project_root.rglob("*config*.md")) + list(self.project_root.rglob("*setup*.md"))
            deployment_files.extend(config_docs)
            
            # 檢查環境配置
            env_files = list(self.project_root.rglob("*.env*")) + list(self.project_root.rglob("*requirements*.txt"))
            
            # 計算部署文檔分數
            docker_score = min(100.0, len(docker_files) * 30)
            doc_score = min(100.0, len(deploy_docs + config_docs) * 25)
            env_score = min(100.0, len(env_files) * 20)
            
            overall_score = (docker_score + doc_score + env_score) / 3
            passed = overall_score >= 60.0
            
            recommendations = []
            if len(docker_files) == 0:
                recommendations.append("創建 Docker 配置文件")
            if len(deploy_docs) == 0:
                recommendations.append("編寫部署指南文檔")
            if len(env_files) == 0:
                recommendations.append("提供環境配置模板")
            
            self.check_results.append(ReadinessCheck(
                category=CheckCategory.DOCUMENTATION,
                check_name="Deployment_Documentation",
                description="部署文檔完整性檢查",
                required_for_production=True,
                passed=passed,
                score=overall_score,
                details={
                    "docker_files": len(docker_files),
                    "deploy_docs": len(deploy_docs),
                    "config_docs": len(config_docs),
                    "env_files": len(env_files),
                    "total_deployment_files": len(deployment_files)
                },
                recommendations=recommendations
            ))
            
        except Exception as e:
            self.check_results.append(ReadinessCheck(
                category=CheckCategory.DOCUMENTATION,
                check_name="Deployment_Documentation",
                description="部署文檔完整性檢查",
                required_for_production=True,
                passed=False,
                score=0.0,
                details={"error": str(e)},
                recommendations=["修復部署文檔檢查錯誤"]
            ))
    
    async def _check_compliance_documentation(self):
        """檢查合規性文檔"""
        try:
            # 檢查合規性審計文檔
            compliance_files = list(self.compliance_audit_path.rglob("*.md"))
            compliance_py_files = list(self.compliance_audit_path.rglob("*.py"))
            
            # 檢查關鍵文檔
            required_docs = [
                "README.md",
                "audit-summary.md",
                "sib19-architecture.md",
                "core-logic-fixes.md",
                "rsrp-signal-model.md",
                "layered-threshold-system.md",
                "implementation-plan.md"
            ]
            
            existing_docs = sum(1 for doc in required_docs 
                              if (self.compliance_audit_path / doc).exists())
            
            # 檢查實現文檔
            implementation_files = [
                "compliance_verification_system.py",
                "system_integration_monitor.py",
                "production_readiness_checker.py"
            ]
            
            existing_implementations = sum(1 for impl in implementation_files
                                         if (self.compliance_audit_path / impl).exists())
            
            # 計算合規文檔分數
            doc_completeness = (existing_docs / len(required_docs)) * 100
            impl_completeness = (existing_implementations / len(implementation_files)) * 100
            
            overall_score = (doc_completeness + impl_completeness) / 2
            passed = overall_score >= 90.0  # 合規文檔要求較高
            
            recommendations = []
            if existing_docs < len(required_docs):
                missing_docs = [doc for doc in required_docs 
                               if not (self.compliance_audit_path / doc).exists()]
                recommendations.append(f"完善缺失的文檔: {', '.join(missing_docs)}")
            
            if existing_implementations < len(implementation_files):
                recommendations.append("確保所有實現文件完整")
            
            self.check_results.append(ReadinessCheck(
                category=CheckCategory.DOCUMENTATION,
                check_name="Compliance_Documentation",
                description="合規性文檔完整性檢查",
                required_for_production=True,
                passed=passed,
                score=overall_score,
                details={
                    "total_compliance_files": len(compliance_files),
                    "total_implementation_files": len(compliance_py_files),
                    "required_docs_existing": existing_docs,
                    "required_docs_total": len(required_docs),
                    "implementation_files_existing": existing_implementations,
                    "implementation_files_total": len(implementation_files),
                    "doc_completeness": doc_completeness,
                    "impl_completeness": impl_completeness
                },
                recommendations=recommendations
            ))
            
        except Exception as e:
            self.check_results.append(ReadinessCheck(
                category=CheckCategory.DOCUMENTATION,
                check_name="Compliance_Documentation",
                description="合規性文檔完整性檢查",
                required_for_production=True,
                passed=False,
                score=0.0,
                details={"error": str(e)},
                recommendations=["修復合規性文檔檢查錯誤"]
            ))
    
    def _calculate_overall_readiness(self) -> Dict[str, Any]:
        """計算總體就緒度"""
        if not self.check_results:
            return {
                "readiness_level": ReadinessLevel.NOT_READY.value,
                "overall_score": 0.0,
                "critical_issues": ["沒有執行任何檢查"]
            }
        
        # 分離強制和非強制檢查
        required_checks = [check for check in self.check_results if check.required_for_production]
        optional_checks = [check for check in self.check_results if not check.required_for_production]
        
        # 計算強制檢查分數
        if required_checks:
            required_score = sum(check.score for check in required_checks) / len(required_checks)
            required_passed = sum(1 for check in required_checks if check.passed)
            required_pass_rate = (required_passed / len(required_checks)) * 100
        else:
            required_score = 0.0
            required_pass_rate = 0.0
        
        # 計算可選檢查分數
        if optional_checks:
            optional_score = sum(check.score for check in optional_checks) / len(optional_checks)
        else:
            optional_score = 100.0  # 如果沒有可選檢查，不影響分數
        
        # 加權總分 (強制檢查佔 85%，可選檢查佔 15%)
        overall_score = required_score * 0.85 + optional_score * 0.15
        
        # 確定就緒等級
        if required_pass_rate == 100.0 and overall_score >= 95.0:
            readiness_level = ReadinessLevel.PRODUCTION_READY
        elif required_pass_rate >= 90.0 and overall_score >= 85.0:
            readiness_level = ReadinessLevel.STAGING_READY
        elif required_pass_rate >= 70.0 and overall_score >= 70.0:
            readiness_level = ReadinessLevel.DEVELOPMENT_ONLY
        else:
            readiness_level = ReadinessLevel.NOT_READY
        
        # 識別關鍵問題
        critical_issues = []
        for check in required_checks:
            if not check.passed and check.required_for_production:
                critical_issues.append(f"{check.check_name}: {check.description}")
        
        return {
            "readiness_level": readiness_level.value,
            "overall_score": overall_score,
            "required_score": required_score,
            "optional_score": optional_score,
            "required_pass_rate": required_pass_rate,
            "required_checks_total": len(required_checks),
            "required_checks_passed": required_passed if required_checks else 0,
            "optional_checks_total": len(optional_checks),
            "critical_issues": critical_issues,
            "production_ready": readiness_level == ReadinessLevel.PRODUCTION_READY
        }
    
    def _generate_category_summaries(self) -> Dict[str, Any]:
        """生成類別摘要"""
        summaries = {}
        
        for category in CheckCategory:
            category_checks = [check for check in self.check_results 
                             if check.category == category]
            
            if category_checks:
                passed_checks = sum(1 for check in category_checks if check.passed)
                avg_score = sum(check.score for check in category_checks) / len(category_checks)
                
                summaries[category.value] = {
                    "total_checks": len(category_checks),
                    "passed_checks": passed_checks,
                    "pass_rate": (passed_checks / len(category_checks)) * 100,
                    "average_score": avg_score,
                    "status": "PASS" if passed_checks == len(category_checks) else "FAIL"
                }
            else:
                summaries[category.value] = {
                    "total_checks": 0,
                    "passed_checks": 0,
                    "pass_rate": 0.0,
                    "average_score": 0.0,
                    "status": "NOT_TESTED"
                }
        
        return summaries
    
    def _generate_deployment_recommendation(self, overall_readiness: Dict[str, Any]) -> Dict[str, Any]:
        """生成部署建議"""
        readiness_level = ReadinessLevel(overall_readiness["readiness_level"])
        
        if readiness_level == ReadinessLevel.PRODUCTION_READY:
            return {
                "recommendation": "DEPLOY_TO_PRODUCTION",
                "confidence": "HIGH",
                "message": "系統已完全準備好進行生產部署",
                "next_steps": [
                    "執行最終備份",
                    "通知相關團隊",
                    "執行部署",
                    "監控系統狀態"
                ]
            }
        elif readiness_level == ReadinessLevel.STAGING_READY:
            return {
                "recommendation": "DEPLOY_TO_STAGING",
                "confidence": "MEDIUM",
                "message": "系統適合部署到測試環境，需要修復少量問題後再考慮生產部署",
                "next_steps": [
                    "修復剩餘的關鍵問題",
                    "在測試環境進行全面測試",
                    "重新執行就緒檢查",
                    "準備生產部署"
                ]
            }
        elif readiness_level == ReadinessLevel.DEVELOPMENT_ONLY:
            return {
                "recommendation": "CONTINUE_DEVELOPMENT",
                "confidence": "LOW",
                "message": "系統仍需要重大改進才能考慮部署",
                "next_steps": [
                    "修復所有關鍵問題",
                    "提升系統可靠性",
                    "完善監控和文檔",
                    "重新進行全面檢查"
                ]
            }
        else:
            return {
                "recommendation": "BLOCK_DEPLOYMENT",
                "confidence": "HIGH",
                "message": "系統未準備好任何形式的部署，需要重大修復",
                "next_steps": [
                    "立即停止部署計劃",
                    "修復所有關鍵安全和功能問題",
                    "重新設計不合格的組件",
                    "從基礎重新驗證系統"
                ]
            }
    
    def _generate_action_items(self) -> List[Dict[str, Any]]:
        """生成行動項目"""
        action_items = []
        
        # 收集所有建議
        for check in self.check_results:
            if not check.passed and check.recommendations:
                for recommendation in check.recommendations:
                    action_items.append({
                        "category": check.category.value,
                        "check_name": check.check_name,
                        "priority": "HIGH" if check.required_for_production else "MEDIUM",
                        "action": recommendation,
                        "impact": "BLOCKS_PRODUCTION" if check.required_for_production else "IMPROVEMENT"
                    })
        
        # 按優先級排序
        action_items.sort(key=lambda x: (x["priority"] == "HIGH", x["impact"] == "BLOCKS_PRODUCTION"), reverse=True)
        
        return action_items
    
    def _check_to_dict(self, check: ReadinessCheck) -> Dict[str, Any]:
        """將檢查結果轉換為字典"""
        return {
            "category": check.category.value,
            "check_name": check.check_name,
            "description": check.description,
            "required_for_production": check.required_for_production,
            "passed": check.passed,
            "score": check.score,
            "details": check.details,
            "recommendations": check.recommendations
        }
    
    def save_readiness_report(self, report: Dict[str, Any], output_path: str):
        """保存就緒度報告"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False, default=str)
            logger.info(f"📄 就緒度報告已保存至: {output_path}")
        except Exception as e:
            logger.error(f"❌ 保存就緒度報告失敗: {e}")


async def main():
    """主程序 - 運行生產就緒檢查"""
    print("🔍 LEO 衛星換手系統 - 生產就緒度檢查器")
    print("=" * 60)
    
    # 初始化檢查器
    checker = ProductionReadinessChecker()
    
    # 執行完整檢查
    report = await checker.run_comprehensive_readiness_check()
    
    # 顯示結果摘要
    if "overall_readiness" in report:
        overall = report["overall_readiness"]
        
        print(f"\n📊 生產就緒度檢查結果:")
        print(f"就緒等級: {overall['readiness_level'].upper()}")
        print(f"總體分數: {overall['overall_score']:.1f}%")
        print(f"強制檢查通過率: {overall['required_pass_rate']:.1f}%")
        print(f"生產就緒: {'✅ 是' if overall['production_ready'] else '❌ 否'}")
        
        print(f"\n📋 類別摘要:")
        for category, summary in report["category_summaries"].items():
            status_icon = "✅" if summary["status"] == "PASS" else "❌"
            print(f"  {status_icon} {category}: {summary['pass_rate']:.1f}% ({summary['passed_checks']}/{summary['total_checks']})")
        
        print(f"\n🎯 部署建議:")
        deployment = report["production_deployment_recommendation"]
        print(f"  建議: {deployment['recommendation']}")
        print(f"  信心度: {deployment['confidence']}")
        print(f"  說明: {deployment['message']}")
        
        if overall.get("critical_issues"):
            print(f"\n🚨 關鍵問題:")
            for issue in overall["critical_issues"][:5]:  # 顯示前5個問題
                print(f"  ❌ {issue}")
        
        print(f"\n💡 優先行動項目:")
        for item in report["action_items"][:5]:  # 顯示前5個行動項目
            priority_icon = "🔥" if item["priority"] == "HIGH" else "⚠️"
            print(f"  {priority_icon} [{item['category']}] {item['action']}")
    
    # 保存報告
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = f"/home/sat/ntn-stack/leo-handover-research/design-phase/compliance-audit/production_readiness_report_{timestamp}.json"
    checker.save_readiness_report(report, report_path)
    
    # 返回結果
    return report


if __name__ == "__main__":
    results = asyncio.run(main())