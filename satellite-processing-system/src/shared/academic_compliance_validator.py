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
            "compliance_summary": {
                "grade_a_files": 0,
                "grade_b_files": 0,
                "grade_c_violations": 0,
                "overall_compliance": "Unknown"
            },
            "stage_results": {},
            "violation_details": []
        }

        # Grade C 禁止項目模式
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
                "patterns": [r'elevation_deg.*-90', r'get\("elevation_deg",\s*-90\)'],
                "context": "仰角硬編碼預設值",
                "severity": "High"
            },
            "random_generation": {
                "patterns": [r'random\.uniform', r'random\.choice', r'random\.sample', r'random\.randint', r'np\.random'],
                "context": "隨機數生成",
                "severity": "Critical"
            },
            "mock_data": {
                "patterns": [r'MockRepository', r'mock.*data', r'假設.*值', r'模擬.*值'],
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
            stages_dir = "/home/sat/ntn-stack/satellite-processing-system/src/stages"

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
        """驗證單個文件的合規性"""
        file_result = {
            "file_path": str(file_path),
            "violations": [],
            "good_practices": []
        }

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            self.validation_results["total_files_scanned"] += 1

            # 檢查禁止項目
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

        except Exception as e:
            self.logger.warning(f"無法讀取文件 {file_path}: {e}")

        return file_result

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
        """計算總體合規性"""
        total_critical = 0
        total_high = 0
        total_medium = 0
        grade_counts = {"A": 0, "B": 0, "C": 0}

        for stage_result in self.validation_results["stage_results"].values():
            total_critical += stage_result["critical_issues"]
            total_high += stage_result["high_issues"]
            total_medium += stage_result["medium_issues"]

            grade = stage_result["compliance_grade"]
            if grade in grade_counts:
                grade_counts[grade] += 1

        # 更新合規性摘要
        self.validation_results["compliance_summary"].update({
            "grade_a_files": grade_counts["A"],
            "grade_b_files": grade_counts["B"],
            "grade_c_violations": grade_counts["C"],
            "total_critical_issues": total_critical,
            "total_high_issues": total_high,
            "total_medium_issues": total_medium
        })

        # 🚨 修復：添加完整的整體合規等級邏輯
        if total_critical > 0:
            overall_grade = "C"
        elif total_high > 5:
            overall_grade = "C"
        elif grade_counts["C"] > 0:  # 有任何 C 等級階段
            overall_grade = "C"
        elif grade_counts["A"] >= 4:  # 至少4個階段達到A級
            overall_grade = "A"
        elif grade_counts["A"] + grade_counts["B"] >= 5:  # 至少5個階段達到A/B級
            overall_grade = "B"
        else:
            overall_grade = "C"

        self.validation_results["compliance_summary"]["overall_compliance"] = overall_grade

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
            output_path = "/home/sat/ntn-stack/satellite-processing-system/academic_compliance_validation_report.json"

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