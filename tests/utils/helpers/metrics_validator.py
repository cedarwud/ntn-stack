#!/usr/bin/env python3
"""
NTN Stack 指標驗證工具

驗證 Prometheus 指標是否符合統一格式規範，確保指標命名、標籤使用的一致性
"""

import re
import yaml
import argparse
import requests
import logging
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path
import sys

# 設置日誌
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """驗證結果"""

    metric_name: str
    valid: bool
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]


@dataclass
class MetricInfo:
    """指標資訊"""

    name: str
    labels: Dict[str, str]
    value: float
    timestamp: Optional[float] = None


class MetricsValidator:
    """指標驗證器"""

    def __init__(self, config_dir: str = "monitoring/standards"):
        self.config_dir = Path(config_dir)
        self.namespace_spec = {}
        self.label_spec = {}
        self.validation_results: List[ValidationResult] = []

        # 載入規範文件
        self._load_specifications()

        # 編譯正則表達式
        self._compile_patterns()

    def _load_specifications(self):
        """載入指標規範"""
        try:
            # 載入命名空間規範
            namespace_file = self.config_dir / "metrics_namespace_spec.yaml"
            if namespace_file.exists():
                with open(namespace_file, "r", encoding="utf-8") as f:
                    self.namespace_spec = yaml.safe_load(f)
                logger.info(f"已載入命名空間規範: {namespace_file}")

            # 載入標籤規範
            label_file = self.config_dir / "standard_labels_spec.yaml"
            if label_file.exists():
                with open(label_file, "r", encoding="utf-8") as f:
                    self.label_spec = yaml.safe_load(f)
                logger.info(f"已載入標籤規範: {label_file}")

        except Exception as e:
            logger.error(f"載入規範文件失敗: {e}")
            sys.exit(1)

    def _compile_patterns(self):
        """編譯正則表達式模式"""
        # 有效的指標名稱模式
        self.metric_name_pattern = re.compile(r"^[a-z][a-z0-9_]*[a-z0-9]$")

        # 有效的標籤名稱模式
        self.label_name_pattern = re.compile(r"^[a-z][a-z0-9_]*[a-z0-9]$")

        # 有效的標籤值模式
        self.label_value_pattern = re.compile(r"^[a-zA-Z0-9_.-]+$")

        # 構建領域前綴模式
        if "domains" in self.namespace_spec:
            domain_prefixes = [
                domain["prefix"] for domain in self.namespace_spec["domains"].values()
            ]
            domain_pattern = "|".join(re.escape(prefix) for prefix in domain_prefixes)
            self.domain_pattern = re.compile(f"^({domain_pattern})")

    def validate_metric_name(self, metric_name: str) -> ValidationResult:
        """驗證指標名稱"""
        errors = []
        warnings = []
        suggestions = []

        # 基本格式檢查
        if not self.metric_name_pattern.match(metric_name):
            errors.append("指標名稱格式無效，應使用小寫字母、數字和底線")

        # 長度檢查
        if len(metric_name) > 50:
            warnings.append("指標名稱過長，建議少於 50 字符")

        # 領域前綴檢查
        if hasattr(self, "domain_pattern"):
            if not self.domain_pattern.match(metric_name):
                errors.append("指標名稱必須以有效的領域前綴開始")
                suggestions.append(
                    "使用以下前綴之一: "
                    + ", ".join(
                        d["prefix"] for d in self.namespace_spec["domains"].values()
                    )
                )

        # 命名規範檢查
        if self._check_naming_conventions(metric_name):
            warnings.extend(self._check_naming_conventions(metric_name))

        # 單位後綴檢查
        unit_suggestions = self._check_unit_suffix(metric_name)
        if unit_suggestions:
            suggestions.extend(unit_suggestions)

        return ValidationResult(
            metric_name=metric_name,
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
        )

    def validate_metric_labels(
        self, metric_name: str, labels: Dict[str, str]
    ) -> ValidationResult:
        """驗證指標標籤"""
        errors = []
        warnings = []
        suggestions = []

        # 檢查必要的公共標籤
        required_labels = self._get_required_labels()
        for label in required_labels:
            if label not in labels:
                warnings.append(f"缺少建議的公共標籤: {label}")

        # 驗證每個標籤
        for label_name, label_value in labels.items():
            # 標籤名稱格式檢查
            if not self.label_name_pattern.match(label_name):
                errors.append(f"標籤名稱 '{label_name}' 格式無效")

            # 標籤值格式檢查
            if not self.label_value_pattern.match(label_value):
                warnings.append(f"標籤值 '{label_value}' 包含特殊字符")

            # 檢查標籤定義
            label_validation = self._validate_label_definition(label_name, label_value)
            if label_validation:
                warnings.extend(label_validation)

        # 基數檢查
        cardinality_warnings = self._check_label_cardinality(labels)
        if cardinality_warnings:
            warnings.extend(cardinality_warnings)

        return ValidationResult(
            metric_name=metric_name,
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
        )

    def validate_prometheus_metrics(
        self, prometheus_url: str
    ) -> List[ValidationResult]:
        """驗證 Prometheus 中的指標"""
        results = []

        try:
            # 獲取指標列表
            response = requests.get(f"{prometheus_url}/api/v1/label/__name__/values")
            response.raise_for_status()

            metric_names = response.json()["data"]
            logger.info(f"從 Prometheus 獲取到 {len(metric_names)} 個指標")

            # 驗證每個指標
            for metric_name in metric_names:
                # 跳過內建指標
                if metric_name.startswith("prometheus_") or metric_name.startswith(
                    "go_"
                ):
                    continue

                # 驗證指標名稱
                name_result = self.validate_metric_name(metric_name)
                results.append(name_result)

                # 獲取指標的標籤資訊
                labels_info = self._get_metric_labels(prometheus_url, metric_name)
                if labels_info:
                    label_result = self.validate_metric_labels(metric_name, labels_info)
                    results.append(label_result)

        except Exception as e:
            logger.error(f"從 Prometheus 獲取指標失敗: {e}")

        return results

    def _get_metric_labels(
        self, prometheus_url: str, metric_name: str
    ) -> Dict[str, str]:
        """獲取指標的標籤資訊"""
        try:
            # 查詢指標的樣本以獲取標籤
            response = requests.get(
                f"{prometheus_url}/api/v1/query", params={"query": f"{metric_name}{{}}"}
            )
            response.raise_for_status()

            data = response.json()["data"]
            if data["result"]:
                # 返回第一個樣本的標籤
                return data["result"][0]["metric"]

        except Exception as e:
            logger.debug(f"獲取指標 {metric_name} 標籤失敗: {e}")

        return {}

    def _check_naming_conventions(self, metric_name: str) -> List[str]:
        """檢查命名慣例"""
        warnings = []

        # 檢查是否使用了駝峰命名法
        if re.search(r"[A-Z]", metric_name):
            warnings.append("不應使用大寫字母，建議使用底線分隔")

        # 檢查是否有連續底線
        if "__" in metric_name:
            warnings.append("避免使用連續底線")

        # 檢查是否以底線開始或結束
        if metric_name.startswith("_") or metric_name.endswith("_"):
            warnings.append("指標名稱不應以底線開始或結束")

        return warnings

    def _check_unit_suffix(self, metric_name: str) -> List[str]:
        """檢查單位後綴"""
        suggestions = []

        if "units" not in self.namespace_spec:
            return suggestions

        # 檢查是否包含時間相關詞彙但缺少時間單位
        time_keywords = ["latency", "duration", "time", "delay"]
        for keyword in time_keywords:
            if keyword in metric_name and not any(
                unit in metric_name for unit in ["_ms", "_seconds", "_us", "_ns"]
            ):
                suggestions.append(f"包含時間相關詞彙 '{keyword}' 但缺少時間單位後綴")

        # 檢查是否包含大小相關詞彙但缺少大小單位
        size_keywords = ["size", "bytes", "memory", "storage"]
        for keyword in size_keywords:
            if keyword in metric_name and not any(
                unit in metric_name for unit in ["_bytes", "_mb", "_gb", "_kb"]
            ):
                suggestions.append(f"包含大小相關詞彙 '{keyword}' 但缺少大小單位後綴")

        return suggestions

    def _get_required_labels(self) -> List[str]:
        """獲取必要的標籤列表"""
        if "common_labels" not in self.label_spec:
            return []

        required = []
        for label_name, label_config in self.label_spec["common_labels"].items():
            if label_config.get("required", False):
                required.append(label_name)

        return required

    def _validate_label_definition(
        self, label_name: str, label_value: str
    ) -> List[str]:
        """驗證標籤定義"""
        warnings = []

        # 查找標籤定義
        label_def = self._find_label_definition(label_name)
        if not label_def:
            warnings.append(f"標籤 '{label_name}' 未在標準規範中定義")
            return warnings

        # 檢查值是否在允許的範圍內
        if "values" in label_def and label_value not in label_def["values"]:
            warnings.append(f"標籤值 '{label_value}' 不在允許的值列表中")

        # 檢查值格式
        if "pattern" in label_def:
            pattern = re.compile(label_def["pattern"])
            if not pattern.match(label_value):
                warnings.append(f"標籤值 '{label_value}' 不符合格式要求")

        return warnings

    def _find_label_definition(self, label_name: str) -> Optional[Dict]:
        """查找標籤定義"""
        # 在所有標籤分類中搜索
        for category in self.label_spec.values():
            if isinstance(category, dict) and label_name in category:
                return category[label_name]
        return None

    def _check_label_cardinality(self, labels: Dict[str, str]) -> List[str]:
        """檢查標籤基數"""
        warnings = []

        # 檢查高基數標籤
        high_cardinality_patterns = [
            r".*_id$",  # ID 類標籤
            r".*timestamp.*",  # 時間戳
            r".*uuid.*",  # UUID
        ]

        for label_name in labels.keys():
            for pattern in high_cardinality_patterns:
                if re.match(pattern, label_name):
                    warnings.append(f"標籤 '{label_name}' 可能產生高基數問題")

        return warnings

    def generate_report(self, results: List[ValidationResult]) -> str:
        """生成驗證報告"""
        total_metrics = len(results)
        valid_metrics = sum(1 for r in results if r.valid)
        total_errors = sum(len(r.errors) for r in results)
        total_warnings = sum(len(r.warnings) for r in results)

        report = []
        report.append("# NTN Stack 指標驗證報告")
        report.append("=" * 50)
        report.append(f"總指標數: {total_metrics}")
        report.append(f"有效指標: {valid_metrics}")
        report.append(f"無效指標: {total_metrics - valid_metrics}")
        report.append(f"總錯誤數: {total_errors}")
        report.append(f"總警告數: {total_warnings}")
        report.append(f"合規率: {valid_metrics/total_metrics*100:.1f}%")
        report.append("")

        # 詳細結果
        if total_errors > 0:
            report.append("## 錯誤詳情")
            report.append("-" * 30)
            for result in results:
                if result.errors:
                    report.append(f"### {result.metric_name}")
                    for error in result.errors:
                        report.append(f"  ❌ {error}")
                    report.append("")

        if total_warnings > 0:
            report.append("## 警告詳情")
            report.append("-" * 30)
            for result in results:
                if result.warnings:
                    report.append(f"### {result.metric_name}")
                    for warning in result.warnings:
                        report.append(f"  ⚠️ {warning}")
                    report.append("")

        # 建議
        suggestions_count = sum(len(r.suggestions) for r in results)
        if suggestions_count > 0:
            report.append("## 改進建議")
            report.append("-" * 30)
            for result in results:
                if result.suggestions:
                    report.append(f"### {result.metric_name}")
                    for suggestion in result.suggestions:
                        report.append(f"  💡 {suggestion}")
                    report.append("")

        return "\n".join(report)


def main():
    """主程序"""
    parser = argparse.ArgumentParser(description="NTN Stack 指標驗證工具")
    parser.add_argument(
        "--prometheus-url",
        default="http://localhost:9090",
        help="Prometheus 服務器 URL",
    )
    parser.add_argument(
        "--config-dir", default="monitoring/standards", help="配置文件目錄"
    )
    parser.add_argument("--output", help="輸出報告文件路徑")
    parser.add_argument("--metric-name", help="驗證特定指標名稱")
    parser.add_argument("--verbose", action="store_true", help="詳細輸出")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # 創建驗證器
    validator = MetricsValidator(args.config_dir)

    results = []

    if args.metric_name:
        # 驗證單個指標
        result = validator.validate_metric_name(args.metric_name)
        results.append(result)
        logger.info(
            f"驗證指標 '{args.metric_name}': {'✅ 有效' if result.valid else '❌ 無效'}"
        )
    else:
        # 驗證 Prometheus 中的所有指標
        logger.info(f"連接到 Prometheus: {args.prometheus_url}")
        results = validator.validate_prometheus_metrics(args.prometheus_url)

    # 生成報告
    report = validator.generate_report(results)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report)
        logger.info(f"報告已保存到: {args.output}")
    else:
        print(report)

    # 根據驗證結果設置退出碼
    invalid_count = sum(1 for r in results if not r.valid)
    if invalid_count > 0:
        logger.error(f"發現 {invalid_count} 個無效指標")
        sys.exit(1)
    else:
        logger.info("所有指標驗證通過")
        sys.exit(0)


if __name__ == "__main__":
    main()
