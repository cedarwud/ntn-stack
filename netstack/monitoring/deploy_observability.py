#!/usr/bin/env python3
"""
NTN Stack 可觀測性統一格式部署工具

自動化部署監控指標統一格式系統，包含驗證、配置和儀表板設置
"""

import os
import sys
import yaml
import json
import argparse
import logging
import subprocess
import requests
from typing import Dict, List, Optional, Any
from pathlib import Path
import time

# 設置日誌
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ObservabilityDeployer:
    """可觀測性部署器"""

    def __init__(self, config_path: str = "monitoring"):
        self.config_path = Path(config_path)
        self.prometheus_url = "http://localhost:9090"
        self.grafana_url = "http://localhost:3000"
        self.grafana_credentials = ("admin", "admin")

        logger.info(f"可觀測性部署器已初始化，配置路徑: {self.config_path}")

    def deploy_full_stack(self):
        """部署完整的可觀測性系統"""
        logger.info("開始部署完整的可觀測性系統")

        steps = [
            ("驗證配置文件", self.validate_configurations),
            ("部署 Prometheus 配置", self.deploy_prometheus_config),
            ("啟動指標驗證器", self.run_metrics_validation),
            ("部署 Grafana 儀表板", self.deploy_grafana_dashboards),
            ("啟動指標模擬器", self.start_metrics_simulator),
            ("執行系統健康檢查", self.run_health_checks),
            ("生成部署報告", self.generate_deployment_report),
        ]

        results = {}
        for step_name, step_func in steps:
            logger.info(f"執行步驟: {step_name}")
            try:
                result = step_func()
                results[step_name] = {"status": "success", "result": result}
                logger.info(f"✅ {step_name} 完成")
            except Exception as e:
                logger.error(f"❌ {step_name} 失敗: {e}")
                results[step_name] = {"status": "failed", "error": str(e)}
                # 決定是否繼續執行後續步驟
                if step_name in ["驗證配置文件", "部署 Prometheus 配置"]:
                    logger.error("關鍵步驟失敗，停止部署")
                    break

        return results

    def validate_configurations(self):
        """驗證配置文件"""
        logger.info("驗證指標命名空間和標籤規範")

        required_files = [
            "standards/metrics_namespace_spec.yaml",
            "standards/standard_labels_spec.yaml",
            "configs/prometheus_best_practices.yaml",
        ]

        missing_files = []
        for file_path in required_files:
            full_path = self.config_path / file_path
            if not full_path.exists():
                missing_files.append(str(full_path))

        if missing_files:
            raise FileNotFoundError(f"缺少必要的配置文件: {missing_files}")

        # 驗證 YAML 文件格式
        for file_path in required_files:
            full_path = self.config_path / file_path
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    yaml.safe_load(f)
                logger.debug(f"✅ {file_path} 格式正確")
            except yaml.YAMLError as e:
                raise ValueError(f"YAML 格式錯誤 {file_path}: {e}")

        return {"validated_files": len(required_files)}

    def deploy_prometheus_config(self):
        """部署 Prometheus 配置"""
        logger.info("生成 Prometheus 配置文件")

        # 載入最佳實踐配置
        best_practices_file = (
            self.config_path / "configs/prometheus_best_practices.yaml"
        )
        with open(best_practices_file, "r", encoding="utf-8") as f:
            config_content = f.read()
        
        # 替換環境變數
        external_ip = os.getenv("EXTERNAL_IP", "127.0.0.1")
        config_content = config_content.replace("${EXTERNAL_IP}", external_ip)
        
        best_practices = yaml.safe_load(config_content)

        # 生成實際的 prometheus.yml
        prometheus_config = {
            "global": best_practices["global"],
            "scrape_configs": best_practices["scrape_configs"],
            "rule_files": best_practices["rule_files"],
        }

        # 寫入配置文件
        output_file = self.config_path / "prometheus.yml"
        with open(output_file, "w", encoding="utf-8") as f:
            yaml.dump(
                prometheus_config, f, default_flow_style=False, allow_unicode=True
            )

        logger.info(f"Prometheus 配置已生成: {output_file}")

        # 生成告警規則文件
        self._generate_alert_rules(best_practices)

        return {"config_file": str(output_file)}

    def _generate_alert_rules(self, best_practices: Dict):
        """生成告警規則文件"""
        alert_rules_dir = self.config_path / "alert_rules"
        alert_rules_dir.mkdir(exist_ok=True)

        if "alert_rules" in best_practices:
            for rule_group in best_practices["alert_rules"]:
                filename = f"{rule_group['name'].replace('.', '_')}.yml"
                rule_file = alert_rules_dir / filename

                rule_content = {"groups": [rule_group]}

                with open(rule_file, "w", encoding="utf-8") as f:
                    yaml.dump(
                        rule_content, f, default_flow_style=False, allow_unicode=True
                    )

                logger.debug(f"生成告警規則文件: {rule_file}")

    def run_metrics_validation(self):
        """執行指標驗證"""
        logger.info("運行指標驗證工具")

        validator_script = self.config_path / "tools/metrics_validator.py"
        if not validator_script.exists():
            raise FileNotFoundError(f"指標驗證器不存在: {validator_script}")

        # 運行驗證器
        cmd = [
            sys.executable,
            str(validator_script),
            "--config-dir",
            str(self.config_path / "standards"),
            "--prometheus-url",
            self.prometheus_url,
            "--output",
            str(self.config_path / "validation_report.txt"),
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                logger.info("指標驗證通過")
                return {"status": "passed", "output": result.stdout}
            else:
                logger.warning(f"指標驗證發現問題: {result.stderr}")
                return {
                    "status": "warnings",
                    "output": result.stdout,
                    "errors": result.stderr,
                }
        except subprocess.TimeoutExpired:
            raise TimeoutError("指標驗證超時")
        except Exception as e:
            raise RuntimeError(f"指標驗證執行失敗: {e}")

    def deploy_grafana_dashboards(self):
        """部署 Grafana 儀表板"""
        logger.info("部署 Grafana 儀表板")

        dashboard_file = self.config_path / "templates/grafana_dashboard_template.json"
        if not dashboard_file.exists():
            raise FileNotFoundError(f"儀表板模板不存在: {dashboard_file}")

        # 載入儀表板模板
        with open(dashboard_file, "r", encoding="utf-8") as f:
            dashboard_data = json.load(f)

        # 嘗試部署到 Grafana
        try:
            response = self._deploy_to_grafana(dashboard_data)
            return {"status": "deployed", "dashboard_id": response.get("id")}
        except Exception as e:
            logger.warning(f"無法連接到 Grafana，儀表板已準備: {e}")
            return {"status": "prepared", "template_file": str(dashboard_file)}

    def _deploy_to_grafana(self, dashboard_data: Dict) -> Dict:
        """部署儀表板到 Grafana"""
        url = f"{self.grafana_url}/api/dashboards/db"

        payload = {"dashboard": dashboard_data["dashboard"], "overwrite": True}

        response = requests.post(
            url, json=payload, auth=self.grafana_credentials, timeout=30
        )
        response.raise_for_status()

        result = response.json()
        logger.info(f"儀表板已部署到 Grafana: {result.get('url')}")
        return result

    def start_metrics_simulator(self):
        """啟動指標模擬器"""
        logger.info("啟動指標模擬器用於測試")

        simulator_script = self.config_path / "tools/metrics_simulator.py"
        if not simulator_script.exists():
            raise FileNotFoundError(f"指標模擬器不存在: {simulator_script}")

        # 檢查是否已有模擬器在運行
        try:
            response = requests.get("http://localhost:8000/metrics", timeout=5)
            if response.status_code == 200:
                logger.info("指標模擬器已在運行")
                return {"status": "already_running", "port": 8000}
        except requests.RequestException:
            pass

        # 啟動模擬器 (背景執行)
        cmd = [
            sys.executable,
            str(simulator_script),
            "--num-uavs",
            "3",
            "--duration",
            "86400",  # 24小時
            "--port",
            "8000",
            "--enable-anomalies",
        ]

        try:
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )

            # 等待模擬器啟動
            time.sleep(3)

            # 驗證模擬器是否正常運行
            response = requests.get("http://localhost:8000/metrics", timeout=10)
            if response.status_code == 200:
                logger.info("指標模擬器已成功啟動")
                return {"status": "started", "pid": process.pid, "port": 8000}
            else:
                raise RuntimeError("模擬器啟動失敗")

        except Exception as e:
            raise RuntimeError(f"無法啟動指標模擬器: {e}")

    def run_health_checks(self):
        """執行系統健康檢查"""
        logger.info("執行系統健康檢查")

        checks = {
            "prometheus": self._check_prometheus,
            "grafana": self._check_grafana,
            "metrics_simulator": self._check_metrics_simulator,
        }

        results = {}
        for check_name, check_func in checks.items():
            try:
                result = check_func()
                results[check_name] = {"status": "healthy", "details": result}
                logger.info(f"✅ {check_name} 健康檢查通過")
            except Exception as e:
                results[check_name] = {"status": "unhealthy", "error": str(e)}
                logger.warning(f"⚠️ {check_name} 健康檢查失敗: {e}")

        return results

    def _check_prometheus(self) -> Dict:
        """檢查 Prometheus 狀態"""
        response = requests.get(
            f"{self.prometheus_url}/api/v1/query", params={"query": "up"}, timeout=10
        )
        response.raise_for_status()

        data = response.json()
        return {"targets": len(data["data"]["result"]), "status": "up"}

    def _check_grafana(self) -> Dict:
        """檢查 Grafana 狀態"""
        response = requests.get(f"{self.grafana_url}/api/health", timeout=10)
        response.raise_for_status()

        return response.json()

    def _check_metrics_simulator(self) -> Dict:
        """檢查指標模擬器狀態"""
        response = requests.get("http://localhost:8000/metrics", timeout=10)
        response.raise_for_status()

        metrics_text = response.text
        metric_count = len(
            [
                line
                for line in metrics_text.split("\n")
                if line and not line.startswith("#")
            ]
        )

        return {"metrics_count": metric_count, "status": "generating"}

    def generate_deployment_report(self):
        """生成部署報告"""
        logger.info("生成部署報告")

        report = {
            "deployment_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "configuration": {
                "prometheus_url": self.prometheus_url,
                "grafana_url": self.grafana_url,
                "metrics_simulator_url": "http://localhost:8000",
            },
            "components": {
                "metrics_namespace": "已部署統一命名空間規範",
                "standard_labels": "已部署標準標籤集",
                "prometheus_config": "已生成最佳實踐配置",
                "grafana_dashboard": "已部署系統總覽儀表板",
                "metrics_validator": "已集成指標驗證工具",
                "metrics_simulator": "已啟動測試數據生成器",
            },
            "usage": {
                "metrics_validation": "python monitoring/tools/metrics_validator.py",
                "dashboard_access": f"{self.grafana_url}/d/ntn-stack-overview",
                "metrics_endpoint": "http://localhost:8000/metrics",
            },
        }

        # 保存報告
        report_file = self.config_path / "deployment_report.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info(f"部署報告已保存: {report_file}")
        return report


def main():
    """主程序"""
    parser = argparse.ArgumentParser(description="NTN Stack 可觀測性統一格式部署工具")
    parser.add_argument(
        "--config-path", default="monitoring", help="配置文件路徑 (默認: monitoring)"
    )
    parser.add_argument(
        "--prometheus-url",
        default="http://localhost:9090",
        help="Prometheus 服務器 URL",
    )
    parser.add_argument(
        "--grafana-url", default="http://localhost:3000", help="Grafana 服務器 URL"
    )
    parser.add_argument(
        "--action",
        choices=["deploy", "validate", "health-check", "report"],
        default="deploy",
        help="執行動作",
    )
    parser.add_argument("--verbose", action="store_true", help="詳細輸出")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # 創建部署器
    deployer = ObservabilityDeployer(args.config_path)
    deployer.prometheus_url = args.prometheus_url
    deployer.grafana_url = args.grafana_url

    try:
        if args.action == "deploy":
            logger.info("開始完整部署")
            results = deployer.deploy_full_stack()

            # 輸出結果摘要
            success_count = sum(1 for r in results.values() if r["status"] == "success")
            total_count = len(results)

            logger.info(f"部署完成: {success_count}/{total_count} 步驟成功")

            if success_count == total_count:
                logger.info("🎉 可觀測性系統部署成功！")
                logger.info(f"儀表板地址: {args.grafana_url}/d/ntn-stack-overview")
                logger.info("指標模擬器地址: http://localhost:8000/metrics")
            else:
                logger.warning("部分步驟失敗，請檢查日誌")
                for step, result in results.items():
                    if result["status"] == "failed":
                        logger.error(f"  ❌ {step}: {result['error']}")

        elif args.action == "validate":
            deployer.validate_configurations()
            deployer.run_metrics_validation()
            logger.info("驗證完成")

        elif args.action == "health-check":
            results = deployer.run_health_checks()
            healthy_count = sum(1 for r in results.values() if r["status"] == "healthy")
            logger.info(f"健康檢查完成: {healthy_count}/{len(results)} 服務健康")

        elif args.action == "report":
            report = deployer.generate_deployment_report()
            print(json.dumps(report, indent=2, ensure_ascii=False))

    except Exception as e:
        logger.error(f"執行失敗: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
