"""
學術級數據合規性驗證器
Academic Data Compliance Validator

驗證所有六個階段是否符合學術級數據標準
檢查是否存在硬編碼、隨機數生成等違規行為
"""

import os
import re
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple
from datetime import datetime, timezone

class AcademicComplianceValidator:
    """學術級數據合規性驗證器"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.validation_results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_files_scanned": 0,
            "total_violations": 0,  # 🔧 修復：添加缺少的字段
            "overall_grade": "Unknown",  # 🔧 修復：添加整體等級字段
            "overall_compliance_score": 0.0,  # 🔧 修復：添加合規分數字段
            "compliance_summary": {
                "grade_a_files": 0,
                "grade_b_files": 0,
                "grade_c_violations": 0,
                "overall_compliance": "Unknown"
            },
            "stage_results": {},
            "violation_details": []
        }

        # Grade C 禁止項目模式 - 🔧 修復：改進mock檢測邏輯
        self.prohibited_patterns = {
            "hardcoded_rsrp": {
                "patterns": [
                    r'rsrp.*-85\b', r'RSRP.*-85\b', r'= -85\b.*rsrp', r'= -85\b.*RSRP',
                    r'rsrp.*-88\b', r'RSRP.*-88\b', r'= -88\b.*rsrp', r'= -88\b.*RSRP',
                    r'rsrp.*-90\b', r'RSRP.*-90\b', r'= -90\b.*rsrp', r'= -90\b.*RSRP',
                    r'threshold.*-85\b', r'threshold.*-88\b', r'threshold.*-90\b',
                    r'-85.*dBm', r'-88.*dBm', r'-90.*dBm',
                    r'base_rsrp.*-85', r'base_rsrp.*-88', r'base_rsrp.*-90'
                ],
                "context": "RSRP硬編碼值",
                "severity": "Critical"
            },
            "hardcoded_elevation": {
                # 🔧 修復：更精確的仰角硬編碼檢測，排除合理的sentinel值
                "patterns": [
                    r'elevation_threshold.*=.*\d+',     # 仰角門檻硬編碼
                    r'min_elevation.*=.*\d+',           # 最小仰角硬編碼
                    r'max_elevation.*=.*\d+',           # 最大仰角硬編碼
                    r'default_elevation.*=.*\d+',       # 預設仰角硬編碼
                    r'get\("elevation_deg",\s*-90\)'    # 字典取值硬編碼
                ],
                "context": "仰角硬編碼預設值",
                "severity": "High"
            },
            "random_generation": {
                "patterns": [r'random\.uniform', r'random\.choice', r'random\.sample', r'random\.randint', r'np\.random'],
                "context": "隨機數生成",
                "severity": "Critical"
            },
            "mock_data": {
                # 🔧 修復：更精確的mock檢測模式，排除檢測邏輯
                "patterns": [
                    r'MockRepository\(\)',      # Mock類實例化
                    r'MockPrediction\(\)',      # Mock類實例化
                    r'mock_repository\s*=',     # Mock對象賦值
                    r'mock_prediction\s*=',     # Mock對象賦值
                    r'假設.*值\s*=',            # 中文假設值
                    r'模擬.*值\s*='             # 中文模擬值
                ],
                "context": "模擬數據使用",
                "severity": "Critical"
            },
            "hardcoded_coordinates": {
                "patterns": [r'25\.0.*121\.5', r'longitude.*121\.5', r'latitude.*25\.0'],
                "context": "硬編碼座標",
                "severity": "Medium"
            }
        }

        # Grade A/B 良好實踐模式
        self.good_practices = {
            "standard_references": [
                "ITU-R", "3GPP", "IEEE", "SpaceX_Technical_Specs", "OneWeb_Technical_Specs"
            ],
            "physics_based": [
                "Friis", "path_loss", "atmospheric_attenuation", "SGP4", "orbital_mechanics"
            ],
            "academic_compliance": [
                "academic_standards_config", "elevation_standards"
            ]
        }

    def validate_all_stages(self, stages_dir: str = None) -> Dict[str, Any]:
        """驗證所有六個階段的合規性"""
        if stages_dir is None:
            stages_dir = "/home/sat/ntn-stack/orbit-engine-system/src/stages"

        stages_path = Path(stages_dir)
        if not stages_path.exists():
            self.logger.error(f"階段目錄不存在: {stages_path}")
            return self.validation_results

        self.logger.info("🔍 開始學術級數據合規性驗證...")

        # 驗證每個階段
        for stage_num in range(1, 7):
            stage_dir = stages_path / f"stage{stage_num}_*"
            stage_dirs = list(stages_path.glob(f"stage{stage_num}_*"))

            if stage_dirs:
                stage_path = stage_dirs[0]  # 取第一個匹配的目錄
                self.logger.info(f"🔍 驗證 Stage {stage_num}: {stage_path.name}")
                stage_result = self._validate_stage(stage_path, stage_num)
                self.validation_results["stage_results"][f"stage_{stage_num}"] = stage_result
            else:
                self.logger.warning(f"未找到 Stage {stage_num} 目錄")

        # 計算總體合規性
        self._calculate_overall_compliance()

        self.logger.info("✅ 學術級數據合規性驗證完成")
        return self.validation_results

    def _validate_stage(self, stage_path: Path, stage_num: int) -> Dict[str, Any]:
        """驗證單個階段的合規性"""
        stage_result = {
            "stage_number": stage_num,
            "stage_path": str(stage_path),
            "files_scanned": 0,
            "violations": [],
            "good_practices": [],
            "compliance_grade": "Unknown",
            "critical_issues": 0,
            "high_issues": 0,
            "medium_issues": 0
        }

        # 掃描Python文件
        python_files = list(stage_path.glob("*.py"))
        for py_file in python_files:
            file_result = self._validate_file(py_file)
            stage_result["files_scanned"] += 1
            stage_result["violations"].extend(file_result["violations"])
            stage_result["good_practices"].extend(file_result["good_practices"])

        # 統計問題嚴重度
        for violation in stage_result["violations"]:
            severity = violation.get("severity", "Medium")
            if severity == "Critical":
                stage_result["critical_issues"] += 1
            elif severity == "High":
                stage_result["high_issues"] += 1
            else:
                stage_result["medium_issues"] += 1

        # 決定階段合規等級
        stage_result["compliance_grade"] = self._determine_compliance_grade(stage_result)

        return stage_result

    def _validate_file(self, file_path: Path) -> Dict[str, Any]:
        """
        驗證單個文件的合規性
        🎓 Grade A學術標準：深度檢查算法實現、數據來源、時間基準使用
        """
        file_result = {
            "file_path": str(file_path),
            "violations": [],
            "good_practices": [],
            "academic_grade": "A+",
            "critical_issues": [],
            "detailed_analysis": {}
        }

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            self.validation_results["total_files_scanned"] += 1

            # 🚨 Grade A 關鍵檢查：時間基準合規性
            self._check_time_reference_compliance(content, file_path, file_result)
            
            # 🚨 Grade A 關鍵檢查：Mock數據檢測
            self._check_mock_data_usage(content, file_path, file_result)
            
            # 🚨 Grade A 關鍵檢查：簡化算法檢測
            self._check_simplified_algorithms(content, file_path, file_result)
            
            # 🚨 Grade A 關鍵檢查：硬編碼參數檢測
            self._check_hardcoded_parameters(content, file_path, file_result)
            
            # 🚨 Grade A 關鍵檢查：數據來源驗證
            self._check_data_source_compliance(content, file_path, file_result)

            # 檢查原有禁止項目
            for violation_type, config in self.prohibited_patterns.items():
                for pattern in config["patterns"]:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        violation = {
                            "type": violation_type,
                            "file": file_path.name,
                            "line": line_num,
                            "context": config["context"],
                            "severity": config["severity"],
                            "matched_text": match.group(),
                            "description": f"在文件 {file_path.name}:{line_num} 發現{config['context']}"
                        }
                        file_result["violations"].append(violation)
                        self.validation_results["violation_details"].append(violation)

            # 檢查良好實踐
            for practice_type, keywords in self.good_practices.items():
                for keyword in keywords:
                    if keyword in content:
                        file_result["good_practices"].append({
                            "type": practice_type,
                            "keyword": keyword,
                            "file": file_path.name
                        })
            
            # 計算文件的學術等級
            file_result["academic_grade"] = self._calculate_file_academic_grade(file_result)

        except Exception as e:
            self.logger.warning(f"無法讀取文件 {file_path}: {e}")

        return file_result

    def _check_time_reference_compliance(self, content: str, file_path: Path, file_result: Dict) -> None:
        """
        檢查時間基準合規性
        🎓 Grade A標準：禁止使用當前時間作為軌道計算基準
        """
        time_violations = []
        
        # 檢查datetime.now()的使用
        datetime_now_pattern = r'datetime\.now\s*\(\s*\)'
        matches = re.finditer(datetime_now_pattern, content)
        for match in matches:
            line_num = content[:match.start()].count('\n') + 1
            context_lines = content.split('\n')[max(0, line_num-2):line_num+1]
            
            # 檢查是否用於軌道計算或數據評估
            context_text = '\n'.join(context_lines).lower()
            if any(keyword in context_text for keyword in ['age_days', 'epoch', 'orbital', 'calculation', 'freshness', 'quality']):
                time_violations.append({
                    "type": "time_reference_violation",
                    "severity": "CRITICAL",
                    "line": line_num,
                    "matched_text": match.group(),
                    "context": "使用當前時間進行軌道計算或數據評估",
                    "description": f"❌ 在 {file_path.name}:{line_num} 發現使用datetime.now()進行軌道相關計算",
                    "fix_suggestion": "使用TLE epoch時間作為計算基準"
                })
        
        if time_violations:
            file_result["critical_issues"].extend(time_violations)
            file_result["violations"].extend(time_violations)

    def _check_mock_data_usage(self, content: str, file_path: Path, file_result: Dict) -> None:
        """
        檢查Mock數據使用
        🎓 Grade A標準：禁止使用模擬或假數據，但允許檢測和防止mock數據
        """
        mock_violations = []
        
        # 檢查真正的Mock數據使用模式
        mock_usage_patterns = [
            r'class\s+Mock\w+.*:',  # Mock類定義
            r'def\s+mock_\w+.*:',   # Mock函數定義
            r'MockPrediction\(\)',  # Mock類實例化
            r'MockRepository\(\)',  # Mock類實例化
            r'fake_data\s*=',       # 假數據賦值
            r'simulated_data\s*=',  # 模擬數據賦值
            r'random\.normal\(',    # 隨機數據生成
            r'np\.random\.',        # NumPy隨機數據
            r'假設.*=\s*\d+',       # 中文假設賦值 (整數)
            # 🔧 修復：移除過於寬泛的estimated模式，避免誤報精度常數
            # r'estimated.*=\s*\d',   # 這會誤報estimated_accuracy = 1e-6
            r'assumed.*=\s*\d+'     # 假定值賦值 (整數)
        ]
        
        # 檢測邏輯的豁免模式 (這些是允許的，因為是在檢測mock數據)
        detection_patterns = [
            r'mock_data_count',     # 計算mock數據數量
            r'check.*mock',         # 檢查mock
            r'detect.*mock',        # 檢測mock
            r'validate.*mock',      # 驗證mock
            r'if.*mock.*in',        # 檢查是否包含mock
            r'mock.*ratio',         # mock比例計算
            r'authentic_data_ratio' # 真實數據比例
        ]
        
        lines = content.split('\n')
        
        for pattern in mock_usage_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                line_content = lines[line_num - 1] if line_num <= len(lines) else ""
                
                # 檢查是否是檢測邏輯（豁免）
                is_detection_logic = any(
                    re.search(exempt_pattern, line_content, re.IGNORECASE) 
                    for exempt_pattern in detection_patterns
                )
                
                # 檢查上下文是否是驗證或檢測相關
                context_lines = lines[max(0, line_num-3):min(len(lines), line_num+3)]
                context_text = ' '.join(context_lines).lower()
                is_validation_context = any(keyword in context_text for keyword in [
                    'validate', 'check', 'detect', 'verify', 'authenticity', 
                    'compliance', 'validation', '驗證', '檢查', '檢測'
                ])
                
                # 只有在非檢測邏輯且非驗證上下文時才報告違反
                if not is_detection_logic and not is_validation_context:
                    mock_violations.append({
                        "type": "mock_data_violation",
                        "severity": "CRITICAL",
                        "line": line_num,
                        "matched_text": match.group(),
                        "context": "使用模擬或假數據",
                        "description": f"❌ 在 {file_path.name}:{line_num} 發現Mock數據使用",
                        "fix_suggestion": "使用真實數據源（TLE、3GPP標準、ITU-R模型）"
                    })
        
        if mock_violations:
            file_result["critical_issues"].extend(mock_violations)
            file_result["violations"].extend(mock_violations)

    def _check_simplified_algorithms(self, content: str, file_path: Path, file_result: Dict) -> None:
        """
        檢查簡化算法使用
        🎓 Grade A標準：禁止使用簡化或近似算法
        """
        simplified_violations = []
        
        # 檢查簡化算法關鍵詞
        simplified_patterns = [
            r'使用.*簡化.*算法',         # 實際使用簡化算法
            r'採用.*簡化.*算法',         # 採用簡化算法
            r'implemented.*simplified.*algorithm',  # 英文：實現了簡化算法
            r'using.*simplified.*algorithm',       # 英文：使用簡化算法
            r'approximate.*calculation',
            r'rough.*estimate',
            r'基本模型',
            r'basic.*model',
            r'linear.*approximation',
            r'假設.*為常數',
            r'固定.*值'
        ]
        
        # 豁免模式：這些是說明文檔或禁止條款，不是實際使用
        exemption_patterns = [
            r'禁止.*簡化.*算法',         # 禁止使用簡化算法
            r'❌.*簡化.*算法',          # ❌ 禁止任何簡化算法
            r'不得.*簡化.*算法',         # 不得使用簡化算法
            r'avoid.*simplified.*algorithm',  # 避免簡化算法
            r'prohibit.*simplified.*algorithm', # 禁止簡化算法
            r'forbidden.*models',        # 禁止模型列表
            r'禁用的.*模式',             # 禁用的模式列表
            r'".*approximation"',        # 字符串字面值定義
            r'\[.*approximation.*\]'     # 列表中的項目
        ]
        
        lines = content.split('\n')
        
        for pattern in simplified_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                line_content = lines[line_num - 1] if line_num <= len(lines) else ""
                
                # 檢查是否是豁免情況（文檔說明或禁止條款）
                is_exemption = any(
                    re.search(exempt_pattern, line_content, re.IGNORECASE) 
                    for exempt_pattern in exemption_patterns
                )
                
                # 只有在非豁免情況下才報告違反
                if not is_exemption:
                    simplified_violations.append({
                        "type": "simplified_algorithm_violation",
                        "severity": "HIGH",
                        "line": line_num,
                        "matched_text": match.group(),
                        "context": "使用簡化算法",
                        "description": f"⚠️ 在 {file_path.name}:{line_num} 發現簡化算法",
                        "fix_suggestion": "使用完整的標準算法實現（SGP4、ITU-R、3GPP）"
                    })
        
        if simplified_violations:
            file_result["violations"].extend(simplified_violations)

    def _check_hardcoded_parameters(self, content: str, file_path: Path, file_result: Dict) -> None:
        """
        檢查硬編碼參數
        🎓 Grade A標準：參數應來自官方標準或配置文件
        """
        hardcoded_violations = []
        
        # 檢查可疑的硬編碼數值
        hardcoded_patterns = [
            r'= -\d+\.?\d*\s*#.*dBm',  # 硬編碼的功率值
            r'= \d+\.?\d*\s*#.*elevation',  # 硬編碼的仰角
            r'= \d+\.?\d*\s*#.*frequency',  # 硬編碼的頻率
            r'預設值.*=',
            r'default.*= \d',
            r'固定.*= \d'
        ]
        
        for pattern in hardcoded_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                
                # 排除配置文件中的合理預設值
                if not any(keyword in file_path.name.lower() for keyword in ['config', 'settings', 'constants']):
                    hardcoded_violations.append({
                        "type": "hardcoded_parameter_violation",
                        "severity": "MEDIUM",
                        "line": line_num,
                        "matched_text": match.group(),
                        "context": "使用硬編碼參數",
                        "description": f"⚠️ 在 {file_path.name}:{line_num} 發現硬編碼參數",
                        "fix_suggestion": "從配置文件或標準文檔中載入參數"
                    })
        
        if hardcoded_violations:
            file_result["violations"].extend(hardcoded_violations)

    def _check_data_source_compliance(self, content: str, file_path: Path, file_result: Dict) -> None:
        """
        檢查數據來源合規性
        🎓 Grade A標準：必須使用官方或權威數據源
        """
        data_source_issues = []
        
        # 檢查良好的數據源
        good_sources = [
            'space-track.org', 'itu-r', '3gpp', 'ieee', 'skyfield',
            'sgp4', 'noaa', 'ntp.org', 'celestrak', 'norad'
        ]
        
        # 檢查可疑的數據源
        suspicious_sources = [
            'random', 'fake', 'mock', 'test_data', 'dummy',
            '隨機', '模擬', '測試數據'
        ]
        
        good_source_found = any(source in content.lower() for source in good_sources)
        suspicious_source_found = any(source in content.lower() for source in suspicious_sources)
        
        if suspicious_source_found and not good_source_found:
            data_source_issues.append({
                "type": "data_source_violation",
                "severity": "HIGH",
                "line": 0,
                "matched_text": "suspicious data sources",
                "context": "使用可疑數據源",
                "description": f"⚠️ {file_path.name} 可能使用非官方數據源",
                "fix_suggestion": "使用官方數據源（Space-Track、ITU-R、3GPP等）"
            })
        
        if data_source_issues:
            file_result["violations"].extend(data_source_issues)

    def _calculate_file_academic_grade(self, file_result: Dict) -> str:
        """
        計算文件的學術等級
        🎓 基於違反類型和嚴重程度評分
        """
        critical_count = len(file_result["critical_issues"])
        total_violations = len(file_result["violations"])
        
        if critical_count > 0:
            return "F"  # 有關鍵問題直接不合格
        elif total_violations == 0:
            return "A+"
        elif total_violations <= 2:
            return "A"
        elif total_violations <= 5:
            return "B"
        else:
            return "C"

    def _determine_compliance_grade(self, stage_result: Dict[str, Any]) -> str:
        """確定階段的合規等級"""
        critical_issues = stage_result["critical_issues"]
        high_issues = stage_result["high_issues"]
        medium_issues = stage_result["medium_issues"]
        good_practices = len(stage_result["good_practices"])

        # Critical 問題直接定為 Grade C
        if critical_issues > 0:
            return "C"

        # High 問題較多也是 Grade C
        if high_issues > 2:
            return "C"

        # 🚨 修復：添加 Grade A 評判邏輯
        # Grade A: 無任何問題 + 豐富的良好實踐
        if critical_issues == 0 and high_issues == 0 and medium_issues == 0 and good_practices >= 2:
            return "A"

        # Grade B: 無Critical/High問題 + 有良好實踐
        if critical_issues == 0 and high_issues == 0 and good_practices > 0:
            return "B"

        # 中等問題但有良好實踐可能是 Grade B
        if medium_issues > 0 and good_practices > 0 and critical_issues == 0 and high_issues == 0:
            return "B"

        # 其他情況
        return "C"

    def _calculate_overall_compliance(self):
        """
        計算總體合規性
        🎓 Grade A 學術標準：基於關鍵問題數量和整體違反情況評估
        """
        total_critical = 0
        total_high = 0
        total_medium = 0
        grade_counts = {"A+": 0, "A": 0, "B": 0, "C": 0, "F": 0}
        
        # 計算總違反數
        self.validation_results["total_violations"] = len(self.validation_results["violation_details"])
        
        # 統計各階段結果
        stage_count = 0
        for stage_name, stage_result in self.validation_results["stage_results"].items():
            # 處理不同的數據結構
            if isinstance(stage_result, dict):
                stage_count += 1
                critical_issues = stage_result.get("critical_issues", 0)
                high_issues = stage_result.get("high_issues", 0) 
                medium_issues = stage_result.get("medium_issues", 0)
                
                # 如果是列表形式的critical_issues
                if isinstance(critical_issues, list):
                    critical_issues = len(critical_issues)
                if isinstance(high_issues, list):
                    high_issues = len(high_issues)
                if isinstance(medium_issues, list):
                    medium_issues = len(medium_issues)
                
                total_critical += critical_issues
                total_high += high_issues
                total_medium += medium_issues

                grade = stage_result.get("compliance_grade", "C")
                if grade in grade_counts:
                    grade_counts[grade] += 1
                else:
                    grade_counts["C"] += 1

        # 更新合規性摘要
        self.validation_results["compliance_summary"].update({
            "grade_a_files": grade_counts["A"] + grade_counts["A+"],
            "grade_b_files": grade_counts["B"], 
            "grade_c_violations": grade_counts["C"],
            "grade_f_violations": grade_counts["F"],
            "total_critical_issues": total_critical,
            "total_high_issues": total_high,
            "total_medium_issues": total_medium
        })

        # 🎓 計算整體學術等級 - 修復單階段檢查邏輯
        if total_critical > 0:
            overall_grade = "F"  # 有關鍵問題直接不合格
            compliance_score = max(0, 60 - total_critical * 10)
        elif grade_counts["F"] > 0:
            overall_grade = "F"
            compliance_score = 50
        elif total_high > 5:
            overall_grade = "C"
            compliance_score = max(60, 80 - total_high * 3)
        elif stage_count == 1:  # 🔧 修復：單階段檢查邏輯
            # 對於單階段檢查，直接基於該階段的表現
            if grade_counts["A+"] > 0:
                overall_grade = "A+"
                compliance_score = max(95, 100 - total_medium)
            elif grade_counts["A"] > 0:
                overall_grade = "A"
                compliance_score = max(90, 95 - total_medium)
            elif grade_counts["B"] > 0:
                overall_grade = "B"
                compliance_score = max(80, 90 - total_high * 2 - total_medium)
            else:
                overall_grade = "C"
                compliance_score = 65
        elif grade_counts["C"] > stage_count / 2:  # 超過一半階段C等級
            overall_grade = "C"
            compliance_score = 70
        elif grade_counts["A"] + grade_counts["A+"] >= stage_count * 0.7:  # 70%以上階段達到A級
            overall_grade = "A"
            compliance_score = max(85, 100 - total_high - total_medium)
        elif grade_counts["A"] + grade_counts["A+"] + grade_counts["B"] >= stage_count * 0.8:  # 80%以上階段達到A/B級
            overall_grade = "B"
            compliance_score = max(75, 90 - total_high * 2 - total_medium)
        else:
            overall_grade = "C"
            compliance_score = 65

        # 更新結果
        self.validation_results["overall_grade"] = overall_grade
        self.validation_results["overall_compliance_score"] = compliance_score
        self.validation_results["compliance_summary"]["overall_compliance"] = overall_grade

        self.logger.info(f"📊 學術標準評估完成: {overall_grade} ({compliance_score:.1f}/100)")
        self.logger.info(f"🚨 關鍵問題: {total_critical}, ⚠️ 高風險: {total_high}, 📝 中等: {total_medium}")

    def generate_compliance_report(self) -> str:
        """生成合規性報告"""
        report = []
        report.append("# 學術級數據合規性驗證報告")
        report.append("# Academic Data Compliance Validation Report")
        report.append("")
        report.append(f"**驗證時間**: {self.validation_results['timestamp']}")
        report.append(f"**掃描文件數**: {self.validation_results['total_files_scanned']}")
        report.append("")

        # 總體合規性
        summary = self.validation_results["compliance_summary"]
        report.append("## 總體合規性摘要")
        report.append(f"- **總體合規等級**: {summary['overall_compliance']}")
        report.append(f"- Grade A 檔案: {summary['grade_a_files']}")
        report.append(f"- Grade B 檔案: {summary['grade_b_files']}")
        report.append(f"- Grade C 違規: {summary['grade_c_violations']}")
        report.append(f"- 嚴重問題總數: {summary.get('total_critical_issues', 0)}")
        report.append("")

        # 各階段詳情
        report.append("## 各階段合規性詳情")
        for stage_name, stage_result in self.validation_results["stage_results"].items():
            report.append(f"### {stage_name.upper()}")
            report.append(f"- **合規等級**: {stage_result['compliance_grade']}")
            report.append(f"- **掃描文件數**: {stage_result['files_scanned']}")
            report.append(f"- **嚴重問題**: {stage_result['critical_issues']}")
            report.append(f"- **高級問題**: {stage_result['high_issues']}")
            report.append(f"- **中等問題**: {stage_result['medium_issues']}")
            report.append("")

        # 主要違規詳情
        if self.validation_results["violation_details"]:
            report.append("## 主要違規詳情")
            for violation in self.validation_results["violation_details"][:20]:  # 只顯示前20個
                report.append(f"- **{violation['severity']}**: {violation['description']}")
                report.append(f"  - 文件: {violation['file']}")
                report.append(f"  - 行號: {violation['line']}")
                report.append(f"  - 匹配文本: `{violation['matched_text']}`")
                report.append("")

        return "\n".join(report)

    def save_validation_results(self, output_path: str = None):
        """保存驗證結果"""
        if output_path is None:
            output_path = "/home/sat/ntn-stack/orbit-engine-system/academic_compliance_validation_report.json"

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(self.validation_results, f, indent=2, ensure_ascii=False)

            self.logger.info(f"驗證結果已保存至: {output_path}")

            # 同時保存報告
            report_path = output_path.replace('.json', '.md')
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(self.generate_compliance_report())

            self.logger.info(f"合規性報告已保存至: {report_path}")

        except Exception as e:
            self.logger.error(f"保存驗證結果失敗: {e}")

# 全域實例
COMPLIANCE_VALIDATOR = AcademicComplianceValidator()