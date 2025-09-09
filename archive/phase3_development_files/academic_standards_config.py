"""
學術標準配置系統
Academic Standards Configuration System

定義 Grade A/B/C 數據標準和檢查閾值
Based on Phase 2 specifications and CLAUDE.md academic standards
"""

from typing import Dict, Any, List, Tuple
from dataclasses import dataclass
from enum import Enum


class GradeLevel(Enum):
    """學術數據分級標準"""
    A = "A"  # 必須使用真實數據，零容忍
    B = "B"  # 基於標準模型，可接受
    C = "C"  # 嚴格禁止項目


class ValidationSeverity(Enum):
    """驗證嚴重程度"""
    BLOCKER = "BLOCKER"      # 阻斷性問題，必須修復
    CRITICAL = "CRITICAL"    # 嚴重問題，影響學術標準
    HIGH = "HIGH"           # 高優先級問題
    MEDIUM = "MEDIUM"       # 中等優先級問題
    LOW = "LOW"            # 低優先級問題


@dataclass
class AcademicStandardRule:
    """學術標準規則定義"""
    rule_id: str
    name: str
    description: str
    grade_level: GradeLevel
    severity: ValidationSeverity
    threshold: float
    unit: str
    enabled: bool = True


class AcademicStandardsConfig:
    """學術標準配置管理器"""
    
    def __init__(self):
        self._initialize_grade_a_requirements()
        self._initialize_grade_b_requirements()
        self._initialize_grade_c_forbidden_items()
        self._initialize_validation_rules()
    
    def _initialize_grade_a_requirements(self):
        """Grade A：必須使用真實數據 (絕不妥協)"""
        self.GRADE_A_REQUIREMENTS = {
            'eci_coordinates': {
                'zero_tolerance_threshold': 0.01,  # <1% 零值容忍
                'range_check': (-42000, 42000),    # km 範圍檢查  
                'mandatory_fields': ['x', 'y', 'z'],
                'description': 'ECI座標必須為非零真實值'
            },
            'orbital_parameters': {
                'tle_epoch_validation': True,      # TLE epoch 時間檢查
                'sgp4_calculation_integrity': True, # SGP4 計算完整性
                'time_base_enforcement': True,     # 強制TLE時間基準
                'description': '軌道參數必須基於真實TLE數據'
            },
            'physical_calculations': {
                'friis_formula_required': True,    # 必須使用Friis公式
                'doppler_calculation_required': True, # 都卜勒計算必需
                'spherical_trigonometry': True,    # 球面三角學精確計算
                'description': '基礎物理計算不得簡化'
            },
            'time_synchronization': {
                'gps_utc_standard': True,         # GPS/UTC標準時間
                'ntp_time_server': True,          # NTP時間伺服器
                'epoch_time_base': True,          # TLE epoch時間基準
                'description': '時間同步必須使用標準時間源'
            }
        }
    
    def _initialize_grade_b_requirements(self):
        """Grade B：基於標準模型 (可接受)"""
        self.GRADE_B_REQUIREMENTS = {
            'signal_propagation': {
                'atmospheric_attenuation': 'ITU-R P.618',
                'rain_attenuation': 'ITU-R P.837',
                'free_space_loss': '20*log10(4*pi*d/lambda)',
                'description': '信號傳播使用ITU-R標準模型'
            },
            'system_parameters': {
                'ntn_parameters': '3GPP TS 38.821',
                'satellite_eirp': 'Public Technical Documents',
                'user_equipment': 'Actual Hardware Specifications',
                'description': '系統參數基於公開標準文件'
            }
        }
    
    def _initialize_grade_c_forbidden_items(self):
        """Grade C：嚴格禁止 (零容忍)"""
        self.GRADE_C_FORBIDDEN = {
            'prohibited_practices': [
                'arbitrary_rsrp_values',           # 任意假設RSRP值
                'random_satellite_positions',      # 隨機產生衛星位置
                'unverified_simplified_formulas',  # 未經證實簡化公式
                'default_value_fallbacks',         # 預設值回退機制
                'non_physics_based_parameters',    # 無物理依據參數
                'mock_repository_usage',           # MockRepository使用
                'simulated_data_fallback',         # 模擬數據回退
                'algorithm_simplification'         # 演算法簡化
            ],
            'detection_patterns': {
                'mock_data_patterns': [
                    'MockRepository',
                    'random.normal()',
                    'np.random.',
                    '假設值',
                    'estimated',
                    'assumed',
                    'simplified'
                ],
                'forbidden_comments': [
                    '簡化',
                    'simplified',
                    'basic model',
                    '模擬實現',
                    'mock implementation'
                ]
            }
        }
    
    def _initialize_validation_rules(self):
        """初始化驗證規則集合"""
        self.validation_rules = [
            # ECI 座標零值檢測
            AcademicStandardRule(
                rule_id="ECI_ZERO_DETECTION",
                name="ECI座標零值檢測",
                description="檢測ECI座標中的零值，超過1%閾值即為違規",
                grade_level=GradeLevel.A,
                severity=ValidationSeverity.BLOCKER,
                threshold=0.01,
                unit="percentage"
            ),
            
            # TLE 時間基準檢查
            AcademicStandardRule(
                rule_id="TLE_EPOCH_TIME_BASE",
                name="TLE Epoch時間基準檢查",
                description="確保軌道計算使用TLE epoch時間，禁用datetime.now()",
                grade_level=GradeLevel.A,
                severity=ValidationSeverity.BLOCKER,
                threshold=0.0,
                unit="violations"
            ),
            
            # 座標範圍合理性檢查
            AcademicStandardRule(
                rule_id="COORDINATE_RANGE_CHECK",
                name="座標範圍合理性檢查",
                description="ECI座標必須在合理軌道範圍內(-42000, 42000) km",
                grade_level=GradeLevel.A,
                severity=ValidationSeverity.CRITICAL,
                threshold=42000.0,
                unit="kilometers"
            ),
            
            # SGP4 計算完整性檢查
            AcademicStandardRule(
                rule_id="SGP4_CALCULATION_INTEGRITY",
                name="SGP4計算完整性檢查",
                description="確保SGP4/SDP4計算流程完整執行，無跳過或簡化",
                grade_level=GradeLevel.A,
                severity=ValidationSeverity.CRITICAL,
                threshold=1.0,
                unit="completion_ratio"
            ),
            
            # 禁止模擬數據檢查
            AcademicStandardRule(
                rule_id="NO_SIMULATION_DATA",
                name="禁止模擬數據檢查",
                description="檢測並禁止使用MockRepository、random數據等模擬實現",
                grade_level=GradeLevel.C,
                severity=ValidationSeverity.BLOCKER,
                threshold=0.0,
                unit="violations"
            )
        ]
    
    def get_grade_a_requirements(self) -> Dict[str, Any]:
        """獲取Grade A要求"""
        return self.GRADE_A_REQUIREMENTS
    
    def get_grade_b_requirements(self) -> Dict[str, Any]:
        """獲取Grade B要求"""
        return self.GRADE_B_REQUIREMENTS
    
    def get_forbidden_items(self) -> Dict[str, Any]:
        """獲取禁止項目"""
        return self.GRADE_C_FORBIDDEN
    
    def get_validation_rules(self, grade_level: GradeLevel = None) -> List[AcademicStandardRule]:
        """獲取驗證規則"""
        if grade_level:
            return [rule for rule in self.validation_rules if rule.grade_level == grade_level]
        return self.validation_rules
    
    def get_rule_by_id(self, rule_id: str) -> AcademicStandardRule:
        """根據ID獲取特定規則"""
        for rule in self.validation_rules:
            if rule.rule_id == rule_id:
                return rule
        raise KeyError(f"Rule not found: {rule_id}")
    
    def validate_eci_coordinates_threshold(self, zero_percentage: float) -> bool:
        """驗證ECI座標零值百分比是否符合標準"""
        threshold = self.GRADE_A_REQUIREMENTS['eci_coordinates']['zero_tolerance_threshold']
        return zero_percentage <= threshold
    
    def is_forbidden_pattern(self, code_content: str) -> Tuple[bool, List[str]]:
        """檢查代碼是否包含禁止模式"""
        violations = []
        patterns = self.GRADE_C_FORBIDDEN['detection_patterns']['mock_data_patterns']
        comment_patterns = self.GRADE_C_FORBIDDEN['detection_patterns']['forbidden_comments']
        
        for pattern in patterns + comment_patterns:
            if pattern in code_content:
                violations.append(pattern)
        
        return len(violations) > 0, violations


# 全域配置實例
academic_standards_config = AcademicStandardsConfig()


# 配置常數導出
GRADE_A_REQUIREMENTS = academic_standards_config.get_grade_a_requirements()
GRADE_B_REQUIREMENTS = academic_standards_config.get_grade_b_requirements()  
FORBIDDEN_ITEMS = academic_standards_config.get_forbidden_items()
VALIDATION_RULES = academic_standards_config.get_validation_rules()


def get_academic_config() -> AcademicStandardsConfig:
    """獲取學術標準配置實例"""
    return academic_standards_config