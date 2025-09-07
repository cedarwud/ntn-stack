"""
六階段管道自動驗證引擎
實現 fail-fast 原則，在驗證失敗時立即停止後續階段執行
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ValidationResult(Enum):
    PASSED = "passed"
    FAILED = "failed"
    MISSING = "missing"

@dataclass
class StageValidationResult:
    stage: int
    stage_name: str
    result: ValidationResult
    passed_checks: int
    failed_checks: int
    total_checks: int
    critical_failures: List[str]
    error_message: Optional[str] = None

class PipelineValidationEngine:
    """
    六階段管道自動驗證引擎
    
    功能：
    1. 自動讀取各階段驗證快照
    2. 檢查關鍵驗證指標
    3. 實現 fail-fast 機制
    4. 提供詳細的錯誤報告
    """
    
    def __init__(self, data_dir: str = "/app/data"):
        self.data_dir = Path(data_dir)
        self.validation_dir = self.data_dir / "validation_snapshots"
        
        # 各階段的關鍵驗證規則
        self.stage_validation_rules = {
            1: {
                "name": "SGP4軌道計算與時間序列生成",
                "critical_checks": ["TLE文件存在性", "SGP4計算完整性", "軌道數據合理性"],
                "min_satellites": 8000,
                "required_constellations": ["starlink", "oneweb"]
            },
            2: {
                "name": "智能衛星篩選",
                "critical_checks": ["篩選算法完整性", "地理範圍覆蓋", "衛星數量合理性"],
                "min_satellites": 100,
                "max_satellites": 4000  # 調整為更合理的限制，約佔總數的45%
            },
            3: {
                "name": "信號品質分析與3GPP事件",
                "critical_checks": ["信號強度計算", "3GPP事件生成", "覆蓋區域驗證"],
                "min_events": 10
            },
            4: {
                "name": "時間序列預處理",
                "critical_checks": ["時間序列完整性", "數據格式轉換", "統計指標計算"],
                "min_satellites": 100
            },
            5: {
                "name": "數據整合與接口準備",
                "critical_checks": ["數據整合完整性", "API接口就緒", "格式標準化"],
                "min_satellites": 100
            },
            6: {
                "name": "動態池規劃與換手優化支援",
                "critical_checks": ["時空錯置驗證", "連續覆蓋保證", "換手場景豐富性", "強化學習數據準備"],
                "min_satellites": 50,
                "required_solution": True,
                "handover_requirements": {
                    "starlink_coverage": {"min": 10, "max": 15, "elevation_threshold": 5},
                    "oneweb_coverage": {"min": 3, "max": 6, "elevation_threshold": 10},
                    "min_handover_scenarios": 50,  # 最少換手場景數
                    "continuous_coverage_ratio": 0.95  # 95%連續覆蓋率
                }
            }
        }
        
        logger.info("✅ 六階段管道驗證引擎初始化完成")
    
    def validate_stage(self, stage_number: int) -> StageValidationResult:
        """驗證特定階段的輸出"""
        
        if stage_number not in self.stage_validation_rules:
            return StageValidationResult(
                stage=stage_number,
                stage_name="未知階段",
                result=ValidationResult.FAILED,
                passed_checks=0,
                failed_checks=1,
                total_checks=1,
                critical_failures=["階段配置不存在"],
                error_message=f"Stage {stage_number} 配置不存在"
            )
        
        rules = self.stage_validation_rules[stage_number]
        snapshot_path = self.validation_dir / f"stage{stage_number}_validation.json"
        
        # 檢查驗證快照是否存在
        if not snapshot_path.exists():
            return StageValidationResult(
                stage=stage_number,
                stage_name=rules["name"],
                result=ValidationResult.MISSING,
                passed_checks=0,
                failed_checks=1,
                total_checks=1,
                critical_failures=["驗證快照不存在"],
                error_message=f"驗證快照文件不存在: {snapshot_path}"
            )
        
        try:
            # 讀取驗證快照
            with open(snapshot_path, 'r', encoding='utf-8') as f:
                validation_data = json.load(f)
            
            return self._analyze_validation_snapshot(stage_number, validation_data, rules)
            
        except Exception as e:
            logger.error(f"讀取 Stage {stage_number} 驗證快照失敗: {e}")
            return StageValidationResult(
                stage=stage_number,
                stage_name=rules["name"],
                result=ValidationResult.FAILED,
                passed_checks=0,
                failed_checks=1,
                total_checks=1,
                critical_failures=["快照讀取失敗"],
                error_message=f"讀取驗證快照失敗: {e}"
            )
    
    def _analyze_validation_snapshot(self, stage_number: int, data: Dict[str, Any], rules: Dict[str, Any]) -> StageValidationResult:
        """分析驗證快照數據"""
        
        validation = data.get("validation", {})
        key_metrics = data.get("keyMetrics", {})
        
        # 基本驗證結果
        passed = validation.get("passed", False)
        total_checks = validation.get("totalChecks", 0)
        passed_checks = validation.get("passedChecks", 0)
        failed_checks = validation.get("failedChecks", 0)
        
        critical_failures = []
        
        # 檢查基本驗證狀態
        if not passed:
            critical_failures.append("基本驗證未通過")
        
        # 檢查關鍵驗證項目
        all_checks = validation.get("allChecks", {})
        for critical_check in rules.get("critical_checks", []):
            # 將中文檢查名稱對應到實際的檢查鍵
            check_key = self._map_critical_check_key(critical_check)
            if check_key and not all_checks.get(check_key, False):
                critical_failures.append(f"關鍵檢查失敗: {critical_check}")
        
        # 檢查衛星數量要求
        if "min_satellites" in rules:
            satellite_count = self._extract_satellite_count(key_metrics, stage_number)
            if satellite_count < rules["min_satellites"]:
                critical_failures.append(f"衛星數量不足: {satellite_count} < {rules['min_satellites']}")
        
        # 檢查最大衛星數量限制（Stage 2）
        if "max_satellites" in rules:
            satellite_count = self._extract_satellite_count(key_metrics, stage_number)
            if satellite_count > rules["max_satellites"]:
                critical_failures.append(f"衛星數量超出預期: {satellite_count} > {rules['max_satellites']}")
        
        # 檢查特定階段的要求
        if stage_number == 6 and rules.get("required_solution", False):
            if "final_solution" not in data:
                critical_failures.append("最終優化解決方案缺失")
            
            # 新增：檢查換手研究特定要求
            handover_reqs = rules.get("handover_requirements", {})
            if handover_reqs:
                # 檢查Starlink覆蓋數量
                starlink_count = key_metrics.get("starlink_count", 0) 
                starlink_req = handover_reqs.get("starlink_coverage", {})
                if not (starlink_req.get("min", 0) <= starlink_count <= starlink_req.get("max", 999)):
                    critical_failures.append(f"Starlink覆蓋數量不符: {starlink_count} (需要{starlink_req.get('min')}-{starlink_req.get('max')}顆)")
                
                # 檢查OneWeb覆蓋數量
                oneweb_count = key_metrics.get("oneweb_count", 0)
                oneweb_req = handover_reqs.get("oneweb_coverage", {})
                if not (oneweb_req.get("min", 0) <= oneweb_count <= oneweb_req.get("max", 999)):
                    critical_failures.append(f"OneWeb覆蓋數量不符: {oneweb_count} (需要{oneweb_req.get('min')}-{oneweb_req.get('max')}顆)")
                
                # 檢查換手場景豐富性
                handover_scenarios = key_metrics.get("handover_scenarios_count", 0)
                min_scenarios = handover_reqs.get("min_handover_scenarios", 50)
                if handover_scenarios < min_scenarios:
                    critical_failures.append(f"換手場景不足: {handover_scenarios} < {min_scenarios}")
                
                # 檢查連續覆蓋率
                coverage_ratio = key_metrics.get("continuous_coverage_ratio", 0.0)
                min_coverage = handover_reqs.get("continuous_coverage_ratio", 0.95)
                if coverage_ratio < min_coverage:
                    critical_failures.append(f"連續覆蓋率不達標: {coverage_ratio:.1%} < {min_coverage:.1%}")
        
        # 確定最終結果
        if critical_failures:
            result = ValidationResult.FAILED
        else:
            result = ValidationResult.PASSED
        
        return StageValidationResult(
            stage=stage_number,
            stage_name=rules["name"],
            result=result,
            passed_checks=passed_checks,
            failed_checks=failed_checks,
            total_checks=total_checks,
            critical_failures=critical_failures
        )
    
    def _map_critical_check_key(self, critical_check: str) -> Optional[str]:
        """將關鍵檢查名稱映射到實際的檢查鍵"""
        mapping = {
            # Stage 1
            "TLE文件存在性": "TLE文件存在性",
            "SGP4計算完整性": "SGP4計算完整性", 
            "軌道數據合理性": "軌道數據合理性",
            
            # Stage 2 - 修復映射以匹配實際的檢查項目名稱
            "篩選算法完整性": "篩選效果檢查",
            "地理範圍覆蓋": "地理篩選平衡性",
            "衛星數量合理性": "數據完整性檢查",
            
            # Stage 3 - 🔧 修復：與文檔和實際驗證快照一致
            "信號強度計算": "信號品質計算完整性",
            "3GPP事件生成": "3GPP事件處理檢查",
            "覆蓋區域驗證": "信號範圍合理性檢查",
            
            # Stage 4
            "時間序列完整性": "時間序列完整性",
            "數據格式轉換": "數據格式轉換",
            "統計指標計算": "統計計算",
            
            # Stage 5
            "數據整合完整性": "數據整合完整性",
            "API接口就緒": "API就緒檢查",
            "格式標準化": "格式標準化",
            
            # Stage 6 - 更新為換手優化支援
            "時空錯置驗證": "時空錯置驗證",
            "連續覆蓋保證": "連續覆蓋保證", 
            "換手場景豐富性": "換手場景豐富性",
            "強化學習數據準備": "強化學習數據準備"
        }
        return mapping.get(critical_check)
    
    def _extract_satellite_count(self, key_metrics: Dict[str, Any], stage_number: int) -> int:
        """從關鍵指標中提取衛星數量"""
        
        # Stage 1: 總衛星數
        if stage_number == 1:
            return key_metrics.get("總衛星數", key_metrics.get("total_satellites", 0))
        
        # Stage 2: 智能篩選後的輸出衛星數
        elif stage_number == 2:
            return key_metrics.get("輸出衛星", key_metrics.get("satellite_count", 0))
        
        # Stage 3-5: 處理後的衛星數
        elif stage_number in [3, 4, 5]:
            return key_metrics.get("處理衛星數", key_metrics.get("satellite_count", 0))
        
        # Stage 6: 最終池中的衛星數
        elif stage_number == 6:
            starlink = key_metrics.get("starlink_count", 0)
            oneweb = key_metrics.get("oneweb_count", 0)
            return starlink + oneweb
        
        return 0
    
    def validate_pipeline_execution(self, executed_stages: List[int]) -> bool:
        """驗證整個管道執行，實現 fail-fast 機制"""
        
        logger.info("🚀 開始管道驗證 (Fail-Fast 模式)")
        
        for stage in executed_stages:
            logger.info(f"📊 驗證 Stage {stage}...")
            
            result = self.validate_stage(stage)
            
            if result.result == ValidationResult.PASSED:
                logger.info(f"✅ Stage {stage} 驗證通過 ({result.passed_checks}/{result.total_checks})")
                
            elif result.result == ValidationResult.MISSING:
                logger.error(f"❌ Stage {stage} 驗證快照缺失")
                logger.error(f"   錯誤: {result.error_message}")
                return False
                
            else:  # FAILED
                logger.error(f"❌ Stage {stage} 驗證失敗 ({result.failed_checks}/{result.total_checks})")
                logger.error(f"   關鍵失敗: {', '.join(result.critical_failures)}")
                if result.error_message:
                    logger.error(f"   錯誤詳情: {result.error_message}")
                
                # Fail-Fast: 立即停止
                logger.error("🛑 驗證失敗，停止管道執行 (Fail-Fast)")
                return False
        
        logger.info("🎉 所有階段驗證通過！")
        return True
    
    def generate_validation_report(self, stages: List[int]) -> Dict[str, Any]:
        """生成詳細驗證報告"""
        
        report = {
            "validation_time": "2025-09-06T15:30:00",
            "total_stages": len(stages),
            "validation_engine_version": "1.0.0",
            "stages": []
        }
        
        all_passed = True
        
        for stage in stages:
            result = self.validate_stage(stage)
            
            stage_report = {
                "stage": stage,
                "stage_name": result.stage_name,
                "result": result.result.value,
                "passed_checks": result.passed_checks,
                "failed_checks": result.failed_checks,
                "total_checks": result.total_checks,
                "critical_failures": result.critical_failures
            }
            
            if result.error_message:
                stage_report["error_message"] = result.error_message
            
            report["stages"].append(stage_report)
            
            if result.result != ValidationResult.PASSED:
                all_passed = False
        
        report["overall_result"] = "PASSED" if all_passed else "FAILED"
        
        return report