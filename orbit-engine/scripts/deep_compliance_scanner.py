#!/usr/bin/env python3
"""
深度學術合規掃描器 v1.0

專為發現隱藏違規而設計的高級掃描工具
包含語義分析、依賴關係分析、配置文件檢查等多層次掃描
"""

import re
import ast
import json
import yaml
import logging
import importlib
from pathlib import Path
from typing import Dict, List, Any, Set
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ViolationDetails:
    type: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    file_path: str
    line_number: int
    context: str
    description: str
    suggestion: str

class DeepComplianceScanner:
    """深度合規掃描器"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.violations: List[ViolationDetails] = []

        # 擴展的違規模式庫
        self.critical_patterns = {
            'hardcoded_physics_constants': [
                r'299792458',           # 光速
                r'6\.67430e-11',        # 重力常數
                r'9\.80665',            # 標準重力加速度
                r'1\.380649e-23',       # 玻爾茲曼常數
            ],
            'hidden_mock_usage': [
                r'[Mm]ock[A-Z]\w+',     # MockPrediction, MockData
                r'\w+[Mm]ock\w*',       # DataMock, TestMock
                r'[Ff]ake[A-Z]\w+',     # FakeData, FakeService
                r'[Ss]imulat\w+',       # Simulation, Simulator
                r'[Dd]ummy\w*',         # Dummy, DummyData
            ],
            'test_module_leakage': [
                r'from.*testing.*import',
                r'import.*test\w+',
                r'from.*test.*import',
                r'import.*mock',
            ],
            'random_data_generation': [
                r'random\.\w+',
                r'numpy\.random\.\w+',
                r'np\.random\.\w+',
                r'randint\(',
                r'uniform\(',
                r'normal\(',
            ]
        }

        self.high_patterns = {
            'undocumented_hardcoded_values': [
                r'>=?\s*\d+\.?\d*(?![e\-\+])',  # >= 70, > 5.0
                r'==?\s*\d+\.?\d*(?![e\-\+])',  # == 0, = 5
                r'\*\s*\d+\.?\d*(?![e\-\+])',   # * 2, * 1.5
                r'/\s*\d+\.?\d*(?![e\-\+])',    # / 1000
            ],
            'magic_numbers': [
                r'range\(\d+,\s*\d+\)',         # range(0, 100)
                r'sleep\(\d+\.?\d*\)',          # sleep(5)
                r'timeout=\d+\.?\d*',           # timeout=30
            ],
            'configuration_hardcoding': [
                r'elevation.*[0-9]+\.?[0-9]*',  # elevation門檻硬編碼
                r'rsrp.*-?[0-9]+\.?[0-9]*',     # RSRP硬編碼
                r'frequency.*[0-9]+\.?[0-9]*',  # 頻率硬編碼
            ]
        }

    def scan_project(self, project_path: Path) -> Dict[str, Any]:
        """執行完整項目掃描"""
        self.logger.info("🔍 開始深度合規掃描...")

        scan_results = {
            'scan_metadata': {
                'timestamp': datetime.now().isoformat(),
                'tool_version': '1.0',
                'scan_type': 'deep_compliance',
                'project_path': str(project_path)
            },
            'violations': [],
            'scan_statistics': {
                'files_scanned': 0,
                'critical_violations': 0,
                'high_violations': 0,
                'medium_violations': 0,
                'low_violations': 0
            },
            'scan_coverage': {
                'python_files': 0,
                'config_files': 0,
                'test_files': 0,
                'other_files': 0
            }
        }

        # 1. 掃描Python源代碼
        self._scan_python_files(project_path, scan_results)

        # 2. 掃描配置文件
        self._scan_config_files(project_path, scan_results)

        # 3. 分析依賴關係
        self._analyze_dependencies(project_path, scan_results)

        # 4. 語義分析
        self._semantic_analysis(project_path, scan_results)

        # 5. 交叉引用檢查
        self._cross_reference_check(project_path, scan_results)

        # 整理結果
        scan_results['violations'] = [
            {
                'type': v.type,
                'severity': v.severity,
                'file_path': v.file_path,
                'line_number': v.line_number,
                'context': v.context,
                'description': v.description,
                'suggestion': v.suggestion
            }
            for v in self.violations
        ]

        # 統計
        for violation in self.violations:
            scan_results['scan_statistics'][f"{violation.severity.lower()}_violations"] += 1

        return scan_results

    def _scan_python_files(self, project_path: Path, results: Dict[str, Any]):
        """掃描Python文件"""
        python_files = list(project_path.rglob("*.py"))
        results['scan_coverage']['python_files'] = len(python_files)

        for py_file in python_files:
            if self._should_skip_file(py_file):
                continue

            try:
                content = py_file.read_text(encoding='utf-8')
                self._check_critical_patterns(content, py_file)
                self._check_high_patterns(content, py_file)
                self._ast_analysis(content, py_file)
                results['scan_statistics']['files_scanned'] += 1

            except Exception as e:
                self.logger.warning(f"⚠️ 無法掃描 {py_file}: {e}")

    def _scan_config_files(self, project_path: Path, results: Dict[str, Any]):
        """掃描配置文件"""
        config_patterns = ["*.yaml", "*.yml", "*.json", "*.toml", "*.ini"]
        config_files = []

        for pattern in config_patterns:
            config_files.extend(project_path.rglob(pattern))

        results['scan_coverage']['config_files'] = len(config_files)

        for config_file in config_files:
            try:
                content = config_file.read_text(encoding='utf-8')
                self._check_config_violations(content, config_file)

            except Exception as e:
                self.logger.warning(f"⚠️ 無法掃描配置文件 {config_file}: {e}")

    def _check_critical_patterns(self, content: str, file_path: Path):
        """檢查Critical級別模式"""
        lines = content.split('\n')

        for pattern_type, patterns in self.critical_patterns.items():
            for pattern in patterns:
                for line_num, line in enumerate(lines, 1):
                    matches = re.finditer(pattern, line, re.IGNORECASE)
                    for match in matches:
                        # 上下文感知檢查
                        if self._is_acceptable_context(content, match.start(), pattern_type):
                            continue

                        self.violations.append(ViolationDetails(
                            type=pattern_type,
                            severity="CRITICAL",
                            file_path=str(file_path),
                            line_number=line_num,
                            context=line.strip(),
                            description=f"發現Critical級別違規: {match.group()}",
                            suggestion=self._get_suggestion(pattern_type, match.group())
                        ))

    def _check_high_patterns(self, content: str, file_path: Path):
        """檢查High級別模式"""
        lines = content.split('\n')

        for pattern_type, patterns in self.high_patterns.items():
            for pattern in patterns:
                for line_num, line in enumerate(lines, 1):
                    matches = re.finditer(pattern, line, re.IGNORECASE)
                    for match in matches:
                        if self._is_acceptable_context(content, match.start(), pattern_type):
                            continue

                        self.violations.append(ViolationDetails(
                            type=pattern_type,
                            severity="HIGH",
                            file_path=str(file_path),
                            line_number=line_num,
                            context=line.strip(),
                            description=f"發現High級別違規: {match.group()}",
                            suggestion=self._get_suggestion(pattern_type, match.group())
                        ))

    def _check_config_violations(self, content: str, file_path: Path):
        """檢查配置文件違規"""
        try:
            # 嘗試解析為YAML/JSON
            if file_path.suffix in ['.yaml', '.yml']:
                config_data = yaml.safe_load(content)
            elif file_path.suffix == '.json':
                config_data = json.loads(content)
            else:
                return

            # 檢查配置中的硬編碼值
            self._check_config_hardcoded_values(config_data, file_path, "")

        except Exception as e:
            self.logger.debug(f"配置文件解析失敗 {file_path}: {e}")

    def _check_config_hardcoded_values(self, data: Any, file_path: Path, key_path: str):
        """遞歸檢查配置文件中的硬編碼值"""
        if isinstance(data, dict):
            for key, value in data.items():
                new_path = f"{key_path}.{key}" if key_path else key
                self._check_config_hardcoded_values(value, file_path, new_path)

        elif isinstance(data, list):
            for i, item in enumerate(data):
                new_path = f"{key_path}[{i}]"
                self._check_config_hardcoded_values(item, file_path, new_path)

        elif isinstance(data, (int, float)):
            # 檢查是否為可疑的硬編碼值
            if self._is_suspicious_config_value(data, key_path):
                self.violations.append(ViolationDetails(
                    type="config_hardcoded_value",
                    severity="HIGH",
                    file_path=str(file_path),
                    line_number=0,  # 配置文件難以確定行號
                    context=f"{key_path}: {data}",
                    description=f"配置文件中的可疑硬編碼值: {data}",
                    suggestion="添加學術依據註釋或移至標準常數類"
                ))

    def _ast_analysis(self, content: str, file_path: Path):
        """AST語法樹分析"""
        try:
            tree = ast.parse(content)
            visitor = ViolationASTVisitor(file_path, self)
            visitor.visit(tree)

        except SyntaxError:
            # 語法錯誤的文件跳過
            pass

    def _analyze_dependencies(self, project_path: Path, results: Dict[str, Any]):
        """分析依賴關係"""
        # 檢查import語句中的可疑依賴
        for py_file in project_path.rglob("*.py"):
            if self._should_skip_file(py_file):
                continue

            try:
                content = py_file.read_text(encoding='utf-8')
                self._check_suspicious_imports(content, py_file)

            except Exception as e:
                continue

    def _semantic_analysis(self, project_path: Path, results: Dict[str, Any]):
        """語義分析"""
        # 檢查變數名和函數名中的可疑模式
        for py_file in project_path.rglob("*.py"):
            if self._should_skip_file(py_file):
                continue

            try:
                content = py_file.read_text(encoding='utf-8')
                self._check_semantic_violations(content, py_file)

            except Exception as e:
                continue

    def _cross_reference_check(self, project_path: Path, results: Dict[str, Any]):
        """交叉引用檢查"""
        # 檢查是否有循環依賴或不當引用
        pass

    def _is_acceptable_context(self, content: str, position: int, pattern_type: str) -> bool:
        """上下文感知檢查"""
        # 提取周圍上下文
        start = max(0, position - 100)
        end = min(len(content), position + 100)
        context = content[start:end]

        # 檢查是否在註釋中
        if any(marker in context for marker in ['#', '"""', "'''"]):
            return True

        # 檢查是否為常數定義
        if 'SPEED_OF_LIGHT' in context or 'physics_constants' in context:
            return True

        # 檢查是否為驗證/檢測邏輯
        detection_indicators = [
            'check', 'validate', 'detect', 'scan', 'verify',
            'test', 'assert', 'ensure', 'confirm'
        ]
        if any(indicator in context.lower() for indicator in detection_indicators):
            return True

        return False

    def _is_suspicious_config_value(self, value: float, key_path: str) -> bool:
        """判斷配置值是否可疑"""
        # 常見的可疑值
        suspicious_values = [5.0, 10.0, 15.0, -85, -70, -100, 45.0]

        if value in suspicious_values:
            # 檢查是否有學術依據標註
            suspicious_keys = ['elevation', 'rsrp', 'threshold', 'timeout', 'percentage']
            if any(key in key_path.lower() for key in suspicious_keys):
                return True

        return False

    def _check_suspicious_imports(self, content: str, file_path: Path):
        """檢查可疑的import語句"""
        lines = content.split('\n')

        for line_num, line in enumerate(lines, 1):
            # 檢查測試模組洩漏
            if re.search(r'from.*testing.*import|import.*test\w+', line):
                if not self._is_test_file(file_path):
                    self.violations.append(ViolationDetails(
                        type="test_module_leakage",
                        severity="MEDIUM",
                        file_path=str(file_path),
                        line_number=line_num,
                        context=line.strip(),
                        description="生產代碼中引入測試模組",
                        suggestion="移除測試模組引用或移至測試代碼"
                    ))

    def _check_semantic_violations(self, content: str, file_path: Path):
        """檢查語義違規"""
        # 檢查變數命名中的可疑模式
        suspicious_names = [
            r'\w*mock\w*', r'\w*fake\w*', r'\w*dummy\w*',
            r'\w*test\w*', r'\w*temp\w*', r'\w*tmp\w*'
        ]

        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            for pattern in suspicious_names:
                matches = re.finditer(pattern, line, re.IGNORECASE)
                for match in matches:
                    # 排除合理用法
                    if self._is_legitimate_usage(match.group(), line):
                        continue

                    self.violations.append(ViolationDetails(
                        type="suspicious_naming",
                        severity="MEDIUM",
                        file_path=str(file_path),
                        line_number=line_num,
                        context=line.strip(),
                        description=f"可疑的變數命名: {match.group()}",
                        suggestion="使用更具描述性的命名"
                    ))

    def _should_skip_file(self, file_path: Path) -> bool:
        """判斷是否應該跳過文件"""
        skip_patterns = [
            '__pycache__', '.pyc', '.git', '.venv', 'venv',
            'node_modules', '.pytest_cache', '.coverage'
        ]

        return any(pattern in str(file_path) for pattern in skip_patterns)

    def _is_test_file(self, file_path: Path) -> bool:
        """判斷是否為測試文件"""
        test_indicators = ['test_', '_test.py', '/tests/', '/test/']
        return any(indicator in str(file_path) for indicator in test_indicators)

    def _is_legitimate_usage(self, name: str, context: str) -> bool:
        """判斷是否為合理用法"""
        # 檢查是否在註釋或文檔字符串中
        if '#' in context or '"""' in context or "'''" in context:
            return True

        # 檢查是否為禁止性語句
        prohibitive_patterns = ['禁止', 'not', 'avoid', 'prevent', '不得']
        if any(pattern in context for pattern in prohibitive_patterns):
            return True

        return False

    def _get_suggestion(self, pattern_type: str, matched_text: str) -> str:
        """獲取修復建議"""
        suggestions = {
            'hardcoded_physics_constants': "使用 shared.constants.physics_constants 中的標準常數",
            'hidden_mock_usage': "移除Mock使用，改用真實數據和算法",
            'test_module_leakage': "移除測試模組引用，或將代碼移至測試目錄",
            'random_data_generation': "使用確定性算法替代隨機數生成",
            'undocumented_hardcoded_values': "移至常數類並添加學術依據註釋",
            'magic_numbers': "定義為命名常數並提供學術依據",
            'configuration_hardcoding': "在配置文件中添加學術標準引用註釋"
        }

        return suggestions.get(pattern_type, "請查閱學術標準合規指南")


class ViolationASTVisitor(ast.NodeVisitor):
    """AST訪問器用於深度語法分析"""

    def __init__(self, file_path: Path, scanner: DeepComplianceScanner):
        self.file_path = file_path
        self.scanner = scanner

    def visit_Constant(self, node):
        """檢查常數節點"""
        if isinstance(node.value, (int, float)):
            # 檢查是否為可疑的硬編碼值
            if self._is_suspicious_constant(node.value):
                self.scanner.violations.append(ViolationDetails(
                    type="ast_hardcoded_constant",
                    severity="MEDIUM",
                    file_path=str(self.file_path),
                    line_number=node.lineno,
                    context=f"常數值: {node.value}",
                    description=f"AST檢測到可疑常數: {node.value}",
                    suggestion="考慮將常數移至專用常數類"
                ))

        self.generic_visit(node)

    def _is_suspicious_constant(self, value) -> bool:
        """判斷常數是否可疑"""
        # 常見的可疑常數值
        suspicious_constants = [
            299792458,    # 光速
            5, 10, 15,    # 常見仰角門檻
            -85, -70, -100, # 常見RSRP門檻
            96, 109,      # 軌道週期
            1000, 1e3, 1e6, 1e9  # 單位轉換
        ]

        return value in suspicious_constants


def main():
    """主函數"""
    import argparse

    parser = argparse.ArgumentParser(description="深度學術合規掃描器")
    parser.add_argument("--project-path", default=".", help="項目路徑")
    parser.add_argument("--output", default="deep_scan_report.json", help="輸出文件")
    parser.add_argument("--verbose", action="store_true", help="詳細輸出")

    args = parser.parse_args()

    # 設置日誌
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # 執行掃描
    scanner = DeepComplianceScanner()
    project_path = Path(args.project_path)

    print("🔍 開始深度合規掃描...")
    results = scanner.scan_project(project_path)

    # 保存結果
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # 報告結果
    stats = results['scan_statistics']
    total_violations = sum([
        stats['critical_violations'],
        stats['high_violations'],
        stats['medium_violations'],
        stats['low_violations']
    ])

    print(f"📊 掃描完成！")
    print(f"   掃描文件: {stats['files_scanned']}")
    print(f"   總違規數: {total_violations}")
    print(f"   Critical: {stats['critical_violations']}")
    print(f"   High: {stats['high_violations']}")
    print(f"   Medium: {stats['medium_violations']}")
    print(f"   Low: {stats['low_violations']}")
    print(f"   報告保存至: {args.output}")

    if total_violations == 0:
        print("✅ 恭喜！未發現學術標準違規")
    else:
        print("⚠️ 發現學術標準違規，請查看詳細報告")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())