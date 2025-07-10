#!/usr/bin/env python3
"""
NTN Stack 生產環境部署驗證器
Production Deployment Validator for NTN Stack Monitoring System - Stage 8

功能：
- 生產環境部署前檢查
- 系統配置驗證
- 安全標準檢查
- 效能基準驗證
- 高可用性確認
- 災難恢復準備檢查
"""

import os
import sys
import json
import yaml
import time
import logging
import subprocess
import asyncio
import aiohttp
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import psutil
import docker
import requests

# 🎨 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ProductionRequirement:
    """生產環境要求"""
    name: str
    description: str
    category: str
    severity: str  # critical, high, medium, low
    check_func: str
    expected_result: Any
    current_result: Any = None
    passed: bool = False
    message: str = ""

@dataclass
class ValidationResult:
    """驗證結果"""
    timestamp: datetime = field(default_factory=datetime.now)
    total_checks: int = 0
    passed_checks: int = 0
    failed_checks: int = 0
    critical_failures: int = 0
    high_priority_failures: int = 0
    requirements: List[ProductionRequirement] = field(default_factory=list)
    deployment_ready: bool = False
    recommendations: List[str] = field(default_factory=list)

class ProductionValidator:
    """生產環境驗證器"""
    
    def __init__(self, config_path: str = "monitoring/deployment/production_config.yml"):
        self.config_path = config_path
        self.config = self._load_config()
        self.docker_client = docker.from_env()
        self.requirements = self._initialize_requirements()
        
    def _load_config(self) -> Dict:
        """載入配置"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.warning(f"配置文件不存在: {self.config_path}，使用預設配置")
            return self._default_config()
    
    def _default_config(self) -> Dict:
        """預設配置"""
        return {
            "deployment": {
                "environment": "production",
                "min_cpu_cores": 4,
                "min_memory_gb": 8,
                "min_disk_space_gb": 100,
                "required_ports": [9090, 3000, 9093, 8000],
                "ssl_enabled": True,
                "backup_enabled": True
            },
            "monitoring": {
                "prometheus_retention": "90d",
                "alertmanager_enabled": True,
                "grafana_enabled": True,
                "metrics_endpoints": [
                    "http://localhost:9090/metrics",
                    "http://localhost:3000/metrics"
                ]
            },
            "security": {
                "authentication_required": True,
                "https_only": True,
                "audit_logging": True,
                "backup_encryption": True
            },
            "performance": {
                "max_response_time_ms": 200,
                "min_uptime_percent": 99.9,
                "max_memory_usage_percent": 80,
                "max_cpu_usage_percent": 70
            }
        }
    
    def _initialize_requirements(self) -> List[ProductionRequirement]:
        """初始化生產環境要求"""
        return [
            # 🖥️ 系統資源要求
            ProductionRequirement(
                name="CPU核心數檢查",
                description="確保系統有足夠的CPU核心",
                category="系統資源",
                severity="critical",
                check_func="check_cpu_cores",
                expected_result=self.config["deployment"]["min_cpu_cores"]
            ),
            ProductionRequirement(
                name="記憶體容量檢查",
                description="確保系統有足夠的記憶體",
                category="系統資源",
                severity="critical",
                check_func="check_memory",
                expected_result=self.config["deployment"]["min_memory_gb"]
            ),
            ProductionRequirement(
                name="磁碟空間檢查",
                description="確保有足夠的磁碟空間",
                category="系統資源",
                severity="critical",
                check_func="check_disk_space",
                expected_result=self.config["deployment"]["min_disk_space_gb"]
            ),
            
            # 🔧 服務配置要求
            ProductionRequirement(
                name="Docker服務檢查",
                description="確保Docker服務正常運行",
                category="服務配置",
                severity="critical",
                check_func="check_docker_service",
                expected_result=True
            ),
            ProductionRequirement(
                name="必要端口檢查",
                description="確保必要端口可用",
                category="服務配置",
                severity="high",
                check_func="check_required_ports",
                expected_result=self.config["deployment"]["required_ports"]
            ),
            ProductionRequirement(
                name="容器健康檢查",
                description="確保所有監控容器健康運行",
                category="服務配置",
                severity="critical",
                check_func="check_container_health",
                expected_result="healthy"
            ),
            
            # 🔐 安全配置要求
            ProductionRequirement(
                name="SSL憑證檢查",
                description="確保SSL憑證有效且未過期",
                category="安全配置",
                severity="critical",
                check_func="check_ssl_certificates",
                expected_result=True
            ),
            ProductionRequirement(
                name="認證配置檢查",
                description="確保認證機制正確配置",
                category="安全配置",
                severity="critical",
                check_func="check_authentication",
                expected_result=True
            ),
            ProductionRequirement(
                name="防火牆配置檢查",
                description="確保防火牆規則正確配置",
                category="安全配置",
                severity="high",
                check_func="check_firewall_rules",
                expected_result=True
            ),
            
            # 📊 監控配置要求
            ProductionRequirement(
                name="Prometheus配置檢查",
                description="確保Prometheus配置正確",
                category="監控配置",
                severity="critical",
                check_func="check_prometheus_config",
                expected_result=True
            ),
            ProductionRequirement(
                name="Grafana儀表板檢查",
                description="確保Grafana儀表板正常",
                category="監控配置",
                severity="high",
                check_func="check_grafana_dashboards",
                expected_result=True
            ),
            ProductionRequirement(
                name="警報規則檢查",
                description="確保警報規則正確配置",
                category="監控配置",
                severity="critical",
                check_func="check_alert_rules",
                expected_result=True
            ),
            
            # 💾 備份與恢復要求
            ProductionRequirement(
                name="備份配置檢查",
                description="確保備份機制正確配置",
                category="備份恢復",
                severity="critical",
                check_func="check_backup_config",
                expected_result=True
            ),
            ProductionRequirement(
                name="恢復程序檢查",
                description="確保災難恢復程序可用",
                category="備份恢復",
                severity="high",
                check_func="check_recovery_procedures",
                expected_result=True
            ),
            
            # ⚡ 效能要求
            ProductionRequirement(
                name="API響應時間檢查",
                description="確保API響應時間符合要求",
                category="效能指標",
                severity="high",
                check_func="check_api_response_time",
                expected_result=self.config["performance"]["max_response_time_ms"]
            ),
            ProductionRequirement(
                name="系統負載檢查",
                description="確保系統負載在合理範圍",
                category="效能指標",
                severity="medium",
                check_func="check_system_load",
                expected_result=True
            )
        ]
    
    async def run_validation(self) -> ValidationResult:
        """執行完整驗證"""
        logger.info("🚀 開始生產環境部署驗證...")
        
        result = ValidationResult()
        result.total_checks = len(self.requirements)
        
        for requirement in self.requirements:
            logger.info(f"🔍 檢查: {requirement.name}")
            
            try:
                # 動態調用檢查函數
                check_method = getattr(self, requirement.check_func)
                requirement.current_result = await check_method()
                
                # 評估結果
                requirement.passed = self._evaluate_requirement(requirement)
                
                if requirement.passed:
                    result.passed_checks += 1
                    logger.info(f"✅ {requirement.name} - 通過")
                else:
                    result.failed_checks += 1
                    if requirement.severity == "critical":
                        result.critical_failures += 1
                    elif requirement.severity == "high":
                        result.high_priority_failures += 1
                    logger.error(f"❌ {requirement.name} - 失敗: {requirement.message}")
                    
            except Exception as e:
                requirement.passed = False
                requirement.message = f"檢查異常: {str(e)}"
                result.failed_checks += 1
                if requirement.severity == "critical":
                    result.critical_failures += 1
                logger.error(f"💥 {requirement.name} - 異常: {str(e)}")
        
        result.requirements = self.requirements
        result.deployment_ready = result.critical_failures == 0
        result.recommendations = self._generate_recommendations(result)
        
        return result
    
    def _evaluate_requirement(self, requirement: ProductionRequirement) -> bool:
        """評估要求是否滿足"""
        if isinstance(requirement.expected_result, bool):
            return requirement.current_result == requirement.expected_result
        elif isinstance(requirement.expected_result, (int, float)):
            return requirement.current_result >= requirement.expected_result
        elif isinstance(requirement.expected_result, list):
            return all(item in requirement.current_result for item in requirement.expected_result)
        elif isinstance(requirement.expected_result, str):
            return requirement.current_result == requirement.expected_result
        else:
            return bool(requirement.current_result)
    
    # 🔧 檢查函數實作
    
    async def check_cpu_cores(self) -> int:
        """檢查CPU核心數"""
        return psutil.cpu_count(logical=False)
    
    async def check_memory(self) -> float:
        """檢查記憶體容量（GB）"""
        memory = psutil.virtual_memory()
        return memory.total / (1024**3)  # 轉換為GB
    
    async def check_disk_space(self) -> float:
        """檢查磁碟空間（GB）"""
        disk = psutil.disk_usage('/')
        return disk.free / (1024**3)  # 轉換為GB
    
    async def check_docker_service(self) -> bool:
        """檢查Docker服務"""
        try:
            self.docker_client.ping()
            return True
        except Exception:
            return False
    
    async def check_required_ports(self) -> List[int]:
        """檢查必要端口可用性"""
        import socket
        available_ports = []
        
        for port in self.config["deployment"]["required_ports"]:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', port))
            if result == 0:  # 端口開放
                available_ports.append(port)
            sock.close()
        
        return available_ports
    
    async def check_container_health(self) -> str:
        """檢查容器健康狀態"""
        try:
            containers = self.docker_client.containers.list()
            unhealthy_containers = []
            
            for container in containers:
                if container.attrs.get('State', {}).get('Health', {}).get('Status') == 'unhealthy':
                    unhealthy_containers.append(container.name)
            
            if unhealthy_containers:
                return f"unhealthy_containers: {unhealthy_containers}"
            return "healthy"
        except Exception as e:
            return f"error: {str(e)}"
    
    async def check_ssl_certificates(self) -> bool:
        """檢查SSL憑證"""
        try:
            import ssl
            import socket
            from datetime import datetime, timedelta
            
            # 檢查Grafana SSL憑證
            context = ssl.create_default_context()
            with socket.create_connection(('localhost', 3000), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname='localhost') as ssock:
                    cert = ssock.getpeercert()
                    # 檢查憑證是否在30天內過期
                    expiry_date = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                    if expiry_date < datetime.now() + timedelta(days=30):
                        return False
            
            return True
        except Exception:
            # 如果無法連接SSL，可能未啟用HTTPS
            return not self.config["security"]["https_only"]
    
    async def check_authentication(self) -> bool:
        """檢查認證配置"""
        try:
            # 檢查是否需要認證
            response = requests.get("http://localhost:9090/api/v1/query?query=up", timeout=5)
            if self.config["security"]["authentication_required"]:
                return response.status_code in [401, 403]  # 應該被拒絕
            else:
                return response.status_code == 200  # 應該可以訪問
        except Exception:
            return False
    
    async def check_firewall_rules(self) -> bool:
        """檢查防火牆規則"""
        try:
            # 檢查ufw狀態
            result = subprocess.run(['ufw', 'status'], capture_output=True, text=True)
            if result.returncode == 0:
                output = result.stdout
                # 檢查必要端口是否有規則
                required_ports = self.config["deployment"]["required_ports"]
                for port in required_ports:
                    if str(port) not in output:
                        return False
                return True
            return False  # ufw命令失敗
        except Exception:
            return False
    
    async def check_prometheus_config(self) -> bool:
        """檢查Prometheus配置"""
        try:
            response = requests.get("http://localhost:9090/api/v1/status/config", timeout=10)
            if response.status_code == 200:
                config_data = response.json()
                # 檢查關鍵配置項
                return 'data' in config_data and 'yaml' in config_data['data']
            return False
        except Exception:
            return False
    
    async def check_grafana_dashboards(self) -> bool:
        """檢查Grafana儀表板"""
        try:
            response = requests.get("http://localhost:3000/api/search?type=dash-db", timeout=10)
            if response.status_code == 200:
                dashboards = response.json()
                return len(dashboards) > 0  # 至少要有一個儀表板
            return False
        except Exception:
            return False
    
    async def check_alert_rules(self) -> bool:
        """檢查警報規則"""
        try:
            response = requests.get("http://localhost:9090/api/v1/rules", timeout=10)
            if response.status_code == 200:
                rules_data = response.json()
                groups = rules_data.get('data', {}).get('groups', [])
                return len(groups) > 0  # 至少要有一個警報組
            return False
        except Exception:
            return False
    
    async def check_backup_config(self) -> bool:
        """檢查備份配置"""
        # 檢查備份腳本是否存在
        backup_paths = [
            "/backup/ntn-stack",
            "monitoring/docs/operations_manual.md",
            "monitoring/security/setup_security.sh"
        ]
        
        for path in backup_paths:
            if not os.path.exists(path):
                return False
        
        return True
    
    async def check_recovery_procedures(self) -> bool:
        """檢查恢復程序"""
        # 檢查恢復文檔是否存在
        recovery_docs = [
            "monitoring/docs/troubleshooting_guide.md",
            "monitoring/docs/operations_manual.md"
        ]
        
        for doc in recovery_docs:
            if not os.path.exists(doc):
                return False
        
        return True
    
    async def check_api_response_time(self) -> float:
        """檢查API響應時間"""
        import time
        
        start_time = time.time()
        try:
            response = requests.get("http://localhost:9090/api/v1/query?query=up", timeout=5)
            if response.status_code == 200:
                response_time = (time.time() - start_time) * 1000  # 轉換為毫秒
                return response_time
            return float('inf')  # 如果請求失敗，返回無限大
        except Exception:
            return float('inf')
    
    async def check_system_load(self) -> bool:
        """檢查系統負載"""
        # 檢查CPU和記憶體使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        memory_percent = psutil.virtual_memory().percent
        
        cpu_ok = cpu_percent < self.config["performance"]["max_cpu_usage_percent"]
        memory_ok = memory_percent < self.config["performance"]["max_memory_usage_percent"]
        
        return cpu_ok and memory_ok
    
    def _generate_recommendations(self, result: ValidationResult) -> List[str]:
        """生成建議"""
        recommendations = []
        
        if result.critical_failures > 0:
            recommendations.append("🚨 發現關鍵問題，必須修復後才能部署到生產環境")
        
        if result.high_priority_failures > 0:
            recommendations.append("⚠️ 發現高優先級問題，建議修復後再部署")
        
        # 根據具體失敗項目生成建議
        for req in result.requirements:
            if not req.passed:
                if req.category == "系統資源":
                    recommendations.append(f"💻 升級系統資源: {req.name}")
                elif req.category == "安全配置":
                    recommendations.append(f"🔐 修復安全配置: {req.name}")
                elif req.category == "監控配置":
                    recommendations.append(f"📊 檢查監控配置: {req.name}")
                elif req.category == "備份恢復":
                    recommendations.append(f"💾 完善備份恢復: {req.name}")
        
        if result.deployment_ready:
            recommendations.append("✅ 系統已準備好部署到生產環境")
            recommendations.append("📋 建議執行最終部署檢查清單")
        
        return recommendations
    
    def generate_report(self, result: ValidationResult) -> str:
        """生成驗證報告"""
        report = f"""
# NTN Stack 生產環境部署驗證報告

**驗證時間**: {result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
**部署準備狀態**: {'✅ 準備就緒' if result.deployment_ready else '❌ 尚未準備'}

## 📊 驗證摘要

- **總檢查項目**: {result.total_checks}
- **通過檢查**: {result.passed_checks}
- **失敗檢查**: {result.failed_checks}
- **關鍵失敗**: {result.critical_failures}
- **高優先級失敗**: {result.high_priority_failures}

## 📋 詳細檢查結果

| 檢查項目 | 分類 | 嚴重度 | 狀態 | 預期結果 | 實際結果 | 訊息 |
|----------|------|--------|------|----------|----------|------|
"""
        
        for req in result.requirements:
            status_icon = "✅" if req.passed else "❌"
            report += f"| {req.name} | {req.category} | {req.severity} | {status_icon} | {req.expected_result} | {req.current_result} | {req.message} |\n"
        
        if result.recommendations:
            report += "\n## 💡 建議事項\n\n"
            for rec in result.recommendations:
                report += f"- {rec}\n"
        
        if not result.deployment_ready:
            report += "\n## ⚠️ 部署前必須修復的問題\n\n"
            critical_issues = [req for req in result.requirements if not req.passed and req.severity == "critical"]
            for issue in critical_issues:
                report += f"- **{issue.name}**: {issue.message}\n"
        
        report += f"""
## 📞 支援聯絡

- **技術支援**: tech-support@ntn-stack.com
- **運維團隊**: ops@ntn-stack.com
- **緊急聯絡**: +886-xxx-xxxxxx

---
*報告由NTN Stack生產環境驗證器自動生成*
"""
        
        return report

# 🚀 主執行函數
async def main():
    """主執行函數"""
    validator = ProductionValidator()
    
    print("🚀 開始NTN Stack生產環境部署驗證...")
    result = await validator.run_validation()
    
    # 生成報告
    report = validator.generate_report(result)
    
    # 儲存報告
    report_filename = f"production_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(report_filename, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n📋 驗證報告已儲存: {report_filename}")
    
    # 輸出摘要
    if result.deployment_ready:
        print("✅ 系統已準備好部署到生產環境！")
        return 0
    else:
        print(f"❌ 系統尚未準備好部署，發現 {result.critical_failures} 個關鍵問題")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))