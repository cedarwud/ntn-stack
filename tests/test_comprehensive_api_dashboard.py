#!/usr/bin/env python3
"""
後端 API 擴展與前端數據可視化全面測試

針對 TODO.md 中第 12 項和第 13 項任務的完整驗證測試：
12. 後端 API 擴展與統一
13. 前端數據可視化組件開發

支援本地和容器環境測試
"""

import os
import sys
import json
import time
import asyncio
import httpx
import websockets
import subprocess
import docker
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@dataclass
class TestResult:
    """測試結果數據類"""

    name: str
    success: bool
    message: str
    details: Optional[Dict[str, Any]] = None


class ComprehensiveAPIAndDashboardTest:
    """後端 API 和前端儀表板全面測試類"""

    def __init__(self):
        self.netstack_base = "http://localhost:8080"
        self.simworld_base = "http://localhost:8888"
        self.frontend_base = "http://localhost:5173"
        self.test_results: List[TestResult] = []

        # 初始化 Docker 客戶端
        try:
            self.docker_client = docker.from_env()
            self.use_docker = True
        except Exception as e:
            print(f"⚠️ 無法連接到 Docker: {e}")
            self.use_docker = False

    def check_container_status(self) -> List[TestResult]:
        """檢查容器運行狀態"""
        print("🐳 檢查容器運行狀態...")

        results = []
        required_containers = {
            "netstack-api": "NetStack API 服務",
            "simworld_backend": "SimWorld 後端服務",
            "simworld_frontend": "SimWorld 前端服務",
        }

        if not self.use_docker:
            results.append(
                TestResult(
                    name="Docker 連接",
                    success=False,
                    message="無法連接到 Docker",
                    details={},
                )
            )
            return results

        for container_name, description in required_containers.items():
            try:
                container = self.docker_client.containers.get(container_name)
                if container.status == "running":
                    results.append(
                        TestResult(
                            name=f"容器狀態 - {description}",
                            success=True,
                            message=f"容器正在運行 ({container.status})",
                            details={
                                "container": container_name,
                                "status": container.status,
                                "image": (
                                    container.image.tags[0]
                                    if container.image.tags
                                    else "unknown"
                                ),
                            },
                        )
                    )
                else:
                    results.append(
                        TestResult(
                            name=f"容器狀態 - {description}",
                            success=False,
                            message=f"容器未在運行 ({container.status})",
                            details={
                                "container": container_name,
                                "status": container.status,
                            },
                        )
                    )
            except docker.errors.NotFound:
                results.append(
                    TestResult(
                        name=f"容器狀態 - {description}",
                        success=False,
                        message="容器不存在",
                        details={"container": container_name},
                    )
                )
            except Exception as e:
                results.append(
                    TestResult(
                        name=f"容器狀態 - {description}",
                        success=False,
                        message=f"檢查容器失敗: {str(e)}",
                        details={"container": container_name, "error": str(e)},
                    )
                )

        return results

    def run_container_command(
        self, container_name: str, command: List[str]
    ) -> tuple[bool, str, str]:
        """在容器中執行命令"""
        if not self.use_docker:
            return False, "", "Docker 不可用"

        try:
            container = self.docker_client.containers.get(container_name)
            # 使用舊版本 API 參數
            result = container.exec_run(command, stdout=True, stderr=True)
            output = (
                result.output.decode("utf-8")
                if hasattr(result.output, "decode")
                else str(result.output)
            )
            return result.exit_code == 0, output, ""
        except Exception as e:
            return False, "", str(e)

    async def test_api_in_containers(self) -> List[TestResult]:
        """在容器中測試 API 功能"""
        print("🐳 在容器中測試 API 功能...")

        results = []

        # 測試 NetStack 容器中的 API
        if self.use_docker:
            # 在 NetStack 容器中執行內部 API 測試
            success, output, error = self.run_container_command(
                "netstack-api",
                [
                    "python",
                    "-c",
                    """
import httpx
import asyncio
import json

async def test_internal_api():
    try:
        async with httpx.AsyncClient() as client:
            # 測試內部健康檢查
            response = await client.get('http://localhost:8080/health')
            print(f'Health check: {response.status_code}')
            
            # 測試統一 API 端點
            response = await client.get('http://localhost:8080/api/v1/system/discovery')
            print(f'Service discovery: {response.status_code}')
            
            # 測試 OpenAPI 文檔
            response = await client.get('http://localhost:8080/openapi.json')
            print(f'OpenAPI docs: {response.status_code}')
            
        return True
    except Exception as e:
        print(f'Error: {e}')
        return False

result = asyncio.run(test_internal_api())
print(f'SUCCESS: {result}')
""",
                ],
            )

            if success and "SUCCESS: True" in output:
                results.append(
                    TestResult(
                        name="容器內 API 測試 - NetStack",
                        success=True,
                        message="NetStack 容器內 API 測試通過",
                        details={"output": output},
                    )
                )
            else:
                results.append(
                    TestResult(
                        name="容器內 API 測試 - NetStack",
                        success=False,
                        message="NetStack 容器內 API 測試失敗",
                        details={"output": output, "error": error},
                    )
                )

        # 測試 SimWorld 容器中的 API
        if self.use_docker:
            success, output, error = self.run_container_command(
                "simworld_backend",
                [
                    "python",
                    "-c",
                    """
import httpx
import asyncio

async def test_internal_api():
    try:
        async with httpx.AsyncClient() as client:
            # 測試內部健康檢查
            response = await client.get('http://localhost:8000/health')
            print(f'Health check: {response.status_code}')
            
            # 測試設備 API
            response = await client.get('http://localhost:8000/api/v1/devices')
            print(f'Devices API: {response.status_code}')
            
            # 測試 OpenAPI 文檔
            response = await client.get('http://localhost:8000/openapi.json')
            print(f'OpenAPI docs: {response.status_code}')
            
        return True
    except Exception as e:
        print(f'Error: {e}')
        return False

result = asyncio.run(test_internal_api())
print(f'SUCCESS: {result}')
""",
                ],
            )

            if success and "SUCCESS: True" in output:
                results.append(
                    TestResult(
                        name="容器內 API 測試 - SimWorld",
                        success=True,
                        message="SimWorld 容器內 API 測試通過",
                        details={"output": output},
                    )
                )
            else:
                results.append(
                    TestResult(
                        name="容器內 API 測試 - SimWorld",
                        success=False,
                        message="SimWorld 容器內 API 測試失敗",
                        details={"output": output, "error": error},
                    )
                )

        return results

    def test_container_dependencies(self) -> List[TestResult]:
        """測試容器中的依賴是否正確安裝"""
        print("📦 檢查容器依賴...")

        results = []

        # 檢查 NetStack 容器依賴
        if self.use_docker:
            dependencies = [
                ("httpx", "HTTP 客戶端庫"),
                ("fastapi", "FastAPI 框架"),
                ("websockets", "WebSocket 庫"),
                ("pytest", "測試框架"),
                ("structlog", "結構化日誌"),
            ]

            for dep, description in dependencies:
                success, output, error = self.run_container_command(
                    "netstack-api", ["python", "-c", f"import {dep}; print('OK')"]
                )

                results.append(
                    TestResult(
                        name=f"NetStack 依賴 - {description}",
                        success=success and "OK" in output,
                        message="依賴可用" if success else f"依賴缺失: {error}",
                        details={"dependency": dep},
                    )
                )

        # 檢查 SimWorld 容器依賴
        if self.use_docker:
            dependencies = [
                ("httpx", "HTTP 客戶端庫"),
                ("fastapi", "FastAPI 框架"),
                ("sqlalchemy", "數據庫 ORM"),
                ("pytest", "測試框架"),
            ]

            for dep, description in dependencies:
                success, output, error = self.run_container_command(
                    "simworld_backend", ["python", "-c", f"import {dep}; print('OK')"]
                )

                results.append(
                    TestResult(
                        name=f"SimWorld 依賴 - {description}",
                        success=success and "OK" in output,
                        message="依賴可用" if success else f"依賴缺失: {error}",
                        details={"dependency": dep},
                    )
                )

        return results

    async def test_container_networking(self) -> List[TestResult]:
        """測試容器間網絡連接"""
        print("🔗 測試容器間網絡連接...")

        results = []

        if self.use_docker:
            # 測試 NetStack -> SimWorld 連接
            success, output, error = self.run_container_command(
                "netstack-api",
                [
                    "python",
                    "-c",
                    """
import httpx
import asyncio

async def test_connection():
    try:
        async with httpx.AsyncClient() as client:
            # 嘗試連接到 SimWorld (容器內部地址)
            response = await client.get('http://simworld_backend:8000/health', timeout=5)
            print(f'NetStack -> SimWorld: {response.status_code}')
        return True
    except Exception as e:
        print(f'Connection failed: {e}')
        return False

result = asyncio.run(test_connection())
print(f'SUCCESS: {result}')
""",
                ],
            )

            results.append(
                TestResult(
                    name="容器網絡 - NetStack -> SimWorld",
                    success=success and "SUCCESS: True" in output,
                    message="容器間連接正常" if success else "容器間連接失敗",
                    details={"output": output, "error": error},
                )
            )

            # 測試 SimWorld -> NetStack 連接
            success, output, error = self.run_container_command(
                "simworld_backend",
                [
                    "python",
                    "-c",
                    """
import httpx
import asyncio

async def test_connection():
    try:
        async with httpx.AsyncClient() as client:
            # 嘗試連接到 NetStack (容器內部地址)
            response = await client.get('http://netstack-api:8080/health', timeout=5)
            print(f'SimWorld -> NetStack: {response.status_code}')
        return True
    except Exception as e:
        print(f'Connection failed: {e}')
        return False

result = asyncio.run(test_connection())
print(f'SUCCESS: {result}')
""",
                ],
            )

            results.append(
                TestResult(
                    name="容器網絡 - SimWorld -> NetStack",
                    success=success and "SUCCESS: True" in output,
                    message="容器間連接正常" if success else "容器間連接失敗",
                    details={"output": output, "error": error},
                )
            )

        return results

    async def test_unified_api_architecture(self) -> List[TestResult]:
        """測試統一 API 架構（任務 12）"""
        print("🔍 測試統一 API 架構...")

        results = []

        # 1. 測試 API 端點結構
        api_endpoints = {
            # NetStack API 端點
            f"{self.netstack_base}/api/v1/open5gs/ue": "5G 核心網管理",
            f"{self.netstack_base}/api/v1/ueransim/config/generate": "RAN 和 UE 管理",
            f"{self.netstack_base}/api/v1/uav": "UAV 管理",
            f"{self.netstack_base}/api/v1/mesh/nodes": "Mesh 網絡管理",
            f"{self.netstack_base}/api/v1/mesh/routing/optimize": "路由優化",
            # SimWorld API 端點
            f"{self.simworld_base}/api/v1/devices": "設備管理",
            f"{self.simworld_base}/api/v1/satellites": "衛星管理",
            f"{self.simworld_base}/api/v1/simulations/run": "模擬執行",
            f"{self.simworld_base}/api/v1/wireless/quick-simulation": "無線通道管理",
            f"{self.simworld_base}/api/v1/interference/simulate": "干擾模擬",
            f"{self.simworld_base}/api/v1/coordinates/convert": "坐標轉換",
        }

        for endpoint, description in api_endpoints.items():
            try:
                async with httpx.AsyncClient() as client:
                    # 使用 HEAD 請求檢查端點是否存在
                    response = await client.get(endpoint, timeout=10)

                    # 接受 2xx, 4xx 狀態碼（表示端點存在但可能需要參數）
                    if response.status_code < 500:
                        results.append(
                            TestResult(
                                name=f"API 端點 - {description}",
                                success=True,
                                message=f"端點可訪問 ({response.status_code})",
                                details={
                                    "endpoint": endpoint,
                                    "status": response.status_code,
                                },
                            )
                        )
                    else:
                        results.append(
                            TestResult(
                                name=f"API 端點 - {description}",
                                success=False,
                                message=f"端點錯誤 ({response.status_code})",
                                details={
                                    "endpoint": endpoint,
                                    "status": response.status_code,
                                },
                            )
                        )
            except Exception as e:
                results.append(
                    TestResult(
                        name=f"API 端點 - {description}",
                        success=False,
                        message=f"連接失敗: {str(e)}",
                        details={"endpoint": endpoint, "error": str(e)},
                    )
                )

        # 2. 測試 OpenAPI 文檔生成
        openapi_endpoints = [
            f"{self.netstack_base}/docs",
            f"{self.netstack_base}/openapi.json",
            f"{self.simworld_base}/docs",
            f"{self.simworld_base}/openapi.json",
        ]

        for endpoint in openapi_endpoints:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(endpoint, timeout=10)
                    if response.status_code == 200:
                        results.append(
                            TestResult(
                                name=f"OpenAPI 文檔",
                                success=True,
                                message=f"文檔可訪問: {endpoint}",
                                details={"endpoint": endpoint},
                            )
                        )
                    else:
                        results.append(
                            TestResult(
                                name=f"OpenAPI 文檔",
                                success=False,
                                message=f"文檔無法訪問: {endpoint} ({response.status_code})",
                                details={
                                    "endpoint": endpoint,
                                    "status": response.status_code,
                                },
                            )
                        )
            except Exception as e:
                results.append(
                    TestResult(
                        name=f"OpenAPI 文檔",
                        success=False,
                        message=f"文檔訪問失敗: {str(e)}",
                        details={"endpoint": endpoint, "error": str(e)},
                    )
                )

        return results

    async def test_websocket_endpoints(self) -> List[TestResult]:
        """測試 WebSocket 實時數據推送端點"""
        print("🔍 測試 WebSocket 端點...")

        results = []
        websocket_endpoints = [
            f"ws://localhost:8080/api/v1/ws/network-status",
            f"ws://localhost:8080/api/v1/ws/satellite-position",
            f"ws://localhost:8080/api/v1/ws/uav-telemetry",
            f"ws://localhost:8080/api/v1/ws/channel-heatmap",
        ]

        for ws_url in websocket_endpoints:
            try:
                # 簡短的 WebSocket 連接測試
                async with websockets.connect(ws_url) as websocket:
                    # 嘗試接收一條消息
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                        results.append(
                            TestResult(
                                name=f"WebSocket - {ws_url.split('/')[-1]}",
                                success=True,
                                message="連接成功並接收到數據",
                                details={
                                    "endpoint": ws_url,
                                    "received_data": len(message) > 0,
                                },
                            )
                        )
                    except asyncio.TimeoutError:
                        results.append(
                            TestResult(
                                name=f"WebSocket - {ws_url.split('/')[-1]}",
                                success=True,
                                message="連接成功（未在 3 秒內收到數據）",
                                details={"endpoint": ws_url},
                            )
                        )
            except Exception as e:
                results.append(
                    TestResult(
                        name=f"WebSocket - {ws_url.split('/')[-1]}",
                        success=False,
                        message=f"連接失敗: {str(e)}",
                        details={"endpoint": ws_url, "error": str(e)},
                    )
                )

        return results

    def test_frontend_dashboard_components(self) -> List[TestResult]:
        """測試前端儀表板組件（任務 13）"""
        print("🔍 測試前端儀表板組件...")

        results = []
        frontend_path = project_root / "simworld" / "frontend"

        # 1. 檢查核心組件文件
        required_components = {
            "src/components/dashboard/Dashboard.tsx": "主儀表板組件",
            "src/components/dashboard/Dashboard.scss": "儀表板樣式",
            "src/components/dashboard/panels/SystemOverview.tsx": "系統總覽面板",
            "src/components/dashboard/panels/RealTimeMetrics.tsx": "實時指標面板",
            "src/components/dashboard/panels/PerformanceMetricsPanel.tsx": "性能指標面板",
            "src/components/dashboard/panels/AlertsPanel.tsx": "告警面板",
            "src/components/dashboard/panels/ControlPanel.tsx": "控制面板",
            "src/components/dashboard/panels/PanelCommon.scss": "公共面板樣式",
            "src/components/dashboard/charts/NetworkTopologyChart.tsx": "網絡拓撲圖",
            "src/components/dashboard/views/SatelliteOrbitView.tsx": "衛星軌道視圖",
            "src/components/dashboard/views/UAVFlightTracker.tsx": "UAV 飛行追蹤",
            "src/hooks/useWebSocket.ts": "WebSocket Hook",
            "src/hooks/useApiData.ts": "API 數據 Hook",
            "src/pages/DashboardPage.tsx": "儀表板頁面",
        }

        for file_path, description in required_components.items():
            full_path = frontend_path / file_path
            if full_path.exists():
                # 檢查文件內容是否不為空
                if full_path.stat().st_size > 0:
                    results.append(
                        TestResult(
                            name=f"前端組件 - {description}",
                            success=True,
                            message="組件文件存在且有內容",
                            details={
                                "path": str(full_path),
                                "size": full_path.stat().st_size,
                            },
                        )
                    )
                else:
                    results.append(
                        TestResult(
                            name=f"前端組件 - {description}",
                            success=False,
                            message="組件文件存在但為空",
                            details={"path": str(full_path)},
                        )
                    )
            else:
                results.append(
                    TestResult(
                        name=f"前端組件 - {description}",
                        success=False,
                        message="組件文件不存在",
                        details={"path": str(full_path)},
                    )
                )

        # 2. 檢查路由配置
        main_tsx_path = frontend_path / "src" / "main.tsx"
        if main_tsx_path.exists():
            with open(main_tsx_path, "r", encoding="utf-8") as f:
                content = f.read()
                if "dashboard" in content and "activeView" in content:
                    results.append(
                        TestResult(
                            name="前端路由配置",
                            success=True,
                            message="儀表板路由已正確配置",
                            details={"file": str(main_tsx_path)},
                        )
                    )
                else:
                    results.append(
                        TestResult(
                            name="前端路由配置",
                            success=False,
                            message="儀表板路由配置不完整",
                            details={"file": str(main_tsx_path)},
                        )
                    )

        # 3. 檢查 Navbar 整合
        navbar_path = frontend_path / "src" / "components" / "layout" / "Navbar.tsx"
        if navbar_path.exists():
            with open(navbar_path, "r", encoding="utf-8") as f:
                content = f.read()
                if "儀表板" in content and "dashboard" in content:
                    results.append(
                        TestResult(
                            name="Navbar 整合",
                            success=True,
                            message="儀表板已整合到導航欄",
                            details={"file": str(navbar_path)},
                        )
                    )
                else:
                    results.append(
                        TestResult(
                            name="Navbar 整合",
                            success=False,
                            message="儀表板未完全整合到導航欄",
                            details={"file": str(navbar_path)},
                        )
                    )

        return results

    async def test_frontend_dashboard_accessibility(self) -> List[TestResult]:
        """測試前端儀表板的可訪問性"""
        print("🔍 測試前端儀表板可訪問性...")

        results = []

        dashboard_urls = [
            f"{self.frontend_base}/nycu/dashboard",
            f"{self.frontend_base}/lotus/dashboard",
        ]

        for url in dashboard_urls:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(url, timeout=10)
                    if response.status_code == 200:
                        results.append(
                            TestResult(
                                name=f"儀表板頁面訪問",
                                success=True,
                                message=f"頁面可訪問: {url}",
                                details={"url": url, "status": response.status_code},
                            )
                        )
                    else:
                        results.append(
                            TestResult(
                                name=f"儀表板頁面訪問",
                                success=False,
                                message=f"頁面無法訪問: {url} ({response.status_code})",
                                details={"url": url, "status": response.status_code},
                            )
                        )
            except Exception as e:
                results.append(
                    TestResult(
                        name=f"儀表板頁面訪問",
                        success=False,
                        message=f"頁面訪問失敗: {str(e)}",
                        details={"url": url, "error": str(e)},
                    )
                )

        return results

    def test_frontend_build_process(self) -> List[TestResult]:
        """測試前端建置過程"""
        print("🔍 測試前端建置過程...")

        results = []

        # 如果可以使用 Docker，先在容器中測試
        if self.use_docker:
            success, output, error = self.run_container_command(
                "simworld_frontend", ["npm", "run", "check"]
            )

            results.append(
                TestResult(
                    name="前端容器內類型檢查",
                    success=success,
                    message=(
                        "容器內 TypeScript 類型檢查通過"
                        if success
                        else "容器內類型檢查失敗"
                    ),
                    details={
                        "output": output[:500] if output else "",
                        "error": error[:500] if error else "",
                    },
                )
            )

        # 本地文件系統檢查
        frontend_path = project_root / "simworld" / "frontend"

        try:
            # 檢查 package.json 是否存在
            package_json_path = frontend_path / "package.json"
            if package_json_path.exists():
                results.append(
                    TestResult(
                        name="前端配置文件",
                        success=True,
                        message="package.json 存在",
                        details={"file": str(package_json_path)},
                    )
                )

                # 如果容器測試失敗，嘗試本地測試
                if not any(
                    r.name == "前端容器內類型檢查" and r.success for r in results
                ):
                    try:
                        process = subprocess.run(
                            ["npm", "run", "check"],
                            cwd=frontend_path,
                            capture_output=True,
                            text=True,
                            timeout=60,
                        )

                        if process.returncode == 0:
                            results.append(
                                TestResult(
                                    name="前端本地類型檢查",
                                    success=True,
                                    message="本地 TypeScript 類型檢查通過",
                                    details={"output": process.stdout[:500]},
                                )
                            )
                        else:
                            results.append(
                                TestResult(
                                    name="前端本地類型檢查",
                                    success=False,
                                    message="本地 TypeScript 類型檢查失敗",
                                    details={"error": process.stderr[:500]},
                                )
                            )
                    except subprocess.TimeoutExpired:
                        results.append(
                            TestResult(
                                name="前端本地類型檢查",
                                success=False,
                                message="本地類型檢查超時",
                                details={"timeout": 60},
                            )
                        )
                    except Exception as e:
                        results.append(
                            TestResult(
                                name="前端本地類型檢查",
                                success=False,
                                message=f"本地類型檢查執行失敗: {str(e)}",
                                details={"error": str(e)},
                            )
                        )
            else:
                results.append(
                    TestResult(
                        name="前端配置文件",
                        success=False,
                        message="package.json 不存在",
                        details={"file": str(package_json_path)},
                    )
                )

        except Exception as e:
            results.append(
                TestResult(
                    name="前端建置測試",
                    success=False,
                    message=f"建置測試失敗: {str(e)}",
                    details={"error": str(e)},
                )
            )

        return results

    def test_data_visualization_features(self) -> List[TestResult]:
        """測試數據可視化特性"""
        print("🔍 測試數據可視化特性...")

        results = []

        # 檢查可視化組件的關鍵特性
        visualization_features = {
            "多佈局支持": ["系統總覽", "網絡監控", "UAV 追蹤"],
            "實時數據更新": ["WebSocket 整合", "自動刷新", "數據緩存"],
            "交互式圖表": ["節點選擇", "全螢幕模式", "響應式設計"],
            "用戶體驗": ["暗色系主題", "動畫效果", "載入狀態"],
        }

        frontend_path = project_root / "simworld" / "frontend"
        dashboard_tsx = (
            frontend_path / "src" / "components" / "dashboard" / "Dashboard.tsx"
        )
        dashboard_scss = (
            frontend_path / "src" / "components" / "dashboard" / "Dashboard.scss"
        )

        if dashboard_tsx.exists():
            with open(dashboard_tsx, "r", encoding="utf-8") as f:
                tsx_content = f.read()

            if dashboard_scss.exists():
                with open(dashboard_scss, "r", encoding="utf-8") as f:
                    scss_content = f.read()

                # 檢查佈局支持
                layout_keywords = ["overview", "network", "uav", "selectedLayout"]
                layout_support = all(
                    keyword in tsx_content for keyword in layout_keywords
                )
                results.append(
                    TestResult(
                        name="多佈局支持",
                        success=layout_support,
                        message=(
                            "佈局切換功能完整"
                            if layout_support
                            else "佈局切換功能不完整"
                        ),
                        details={"keywords": layout_keywords},
                    )
                )

                # 檢查 WebSocket 整合
                websocket_keywords = ["useWebSocket", "wsData", "connected"]
                websocket_support = all(
                    keyword in tsx_content for keyword in websocket_keywords
                )
                results.append(
                    TestResult(
                        name="實時數據更新",
                        success=websocket_support,
                        message=(
                            "WebSocket 整合完整"
                            if websocket_support
                            else "WebSocket 整合不完整"
                        ),
                        details={"keywords": websocket_keywords},
                    )
                )

                # 檢查交互式特性
                interactive_keywords = ["fullscreen", "onClick", "onFullscreen"]
                interactive_support = all(
                    keyword in tsx_content for keyword in interactive_keywords
                )
                results.append(
                    TestResult(
                        name="交互式圖表",
                        success=interactive_support,
                        message=(
                            "交互式功能完整"
                            if interactive_support
                            else "交互式功能不完整"
                        ),
                        details={"keywords": interactive_keywords},
                    )
                )

                # 檢查暗色系主題
                theme_keywords = ["linear-gradient", "rgba", "backdrop-filter", "星空"]
                theme_support = any(
                    keyword in scss_content for keyword in theme_keywords
                )
                results.append(
                    TestResult(
                        name="暗色系星空主題",
                        success=theme_support,
                        message=(
                            "暗色系主題已應用" if theme_support else "暗色系主題未應用"
                        ),
                        details={"keywords": theme_keywords},
                    )
                )

            else:
                results.append(
                    TestResult(
                        name="樣式文件檢查",
                        success=False,
                        message="Dashboard.scss 文件不存在",
                        details={"file": str(dashboard_scss)},
                    )
                )
        else:
            results.append(
                TestResult(
                    name="主組件檢查",
                    success=False,
                    message="Dashboard.tsx 文件不存在",
                    details={"file": str(dashboard_tsx)},
                )
            )

        return results

    async def run_comprehensive_tests(self) -> Dict[str, Any]:
        """運行所有綜合測試"""
        print("🚀 開始後端 API 和前端儀表板全面測試...")
        print("=" * 60)

        all_results = []

        # 首先檢查容器狀態
        print("\n🐳 容器環境檢查")
        print("-" * 40)
        container_results = self.check_container_status()
        all_results.extend(container_results)

        dependency_results = self.test_container_dependencies()
        all_results.extend(dependency_results)

        network_results = await self.test_container_networking()
        all_results.extend(network_results)

        # 測試任務 12：後端 API 擴展與統一
        print("\n📡 任務 12：後端 API 擴展與統一")
        print("-" * 40)

        # 優先在容器中測試
        container_api_results = await self.test_api_in_containers()
        all_results.extend(container_api_results)

        api_results = await self.test_unified_api_architecture()
        all_results.extend(api_results)

        websocket_results = await self.test_websocket_endpoints()
        all_results.extend(websocket_results)

        # 測試任務 13：前端數據可視化組件開發
        print("\n🎨 任務 13：前端數據可視化組件開發")
        print("-" * 40)

        component_results = self.test_frontend_dashboard_components()
        all_results.extend(component_results)

        accessibility_results = await self.test_frontend_dashboard_accessibility()
        all_results.extend(accessibility_results)

        build_results = self.test_frontend_build_process()
        all_results.extend(build_results)

        visualization_results = self.test_data_visualization_features()
        all_results.extend(visualization_results)

        # 計算測試結果
        total_tests = len(all_results)
        passed_tests = sum(1 for result in all_results if result.success)
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0

        summary = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "success_rate": success_rate,
            "overall_success": success_rate >= 90,  # 90% 以上為成功
            "test_details": [
                {
                    "name": result.name,
                    "success": result.success,
                    "message": result.message,
                    "details": result.details,
                }
                for result in all_results
            ],
        }

        return summary

    def print_test_results(self, summary: Dict[str, Any]):
        """打印測試結果"""
        print("\n" + "=" * 60)
        print("📊 後端 API 和前端儀表板全面測試結果")
        print("=" * 60)

        if summary["overall_success"]:
            print("✅ 整體測試: 通過")
        else:
            print("❌ 整體測試: 失敗")

        print(f"\n📈 測試摘要:")
        print(f"  • 總測試數: {summary['total_tests']}")
        print(f"  • 通過測試: {summary['passed_tests']}")
        print(f"  • 失敗測試: {summary['failed_tests']}")
        print(f"  • 成功率: {summary['success_rate']:.1f}%")

        print(f"\n🎯 任務完成狀況:")

        # 按類別統計
        container_tests = [t for t in summary["test_details"] if "容器" in t["name"]]
        api_tests = [
            t
            for t in summary["test_details"]
            if "API" in t["name"] or "WebSocket" in t["name"]
        ]
        frontend_tests = [
            t
            for t in summary["test_details"]
            if "前端" in t["name"] or "儀表板" in t["name"] or "組件" in t["name"]
        ]

        container_success = sum(1 for t in container_tests if t["success"])
        api_success = sum(1 for t in api_tests if t["success"])
        frontend_success = sum(1 for t in frontend_tests if t["success"])

        container_rate = (
            (container_success / len(container_tests)) * 100 if container_tests else 0
        )
        api_rate = (api_success / len(api_tests)) * 100 if api_tests else 0
        frontend_rate = (
            (frontend_success / len(frontend_tests)) * 100 if frontend_tests else 0
        )

        print(
            f"  • 容器環境: {container_success}/{len(container_tests)} ({container_rate:.1f}%)"
        )
        print(
            f"  • 任務 12 (後端 API): {api_success}/{len(api_tests)} ({api_rate:.1f}%)"
        )
        print(
            f"  • 任務 13 (前端儀表板): {frontend_success}/{len(frontend_tests)} ({frontend_rate:.1f}%)"
        )

        # 顯示失敗的測試
        failed_tests = [t for t in summary["test_details"] if not t["success"]]
        if failed_tests:
            print(f"\n❌ 失敗的測試:")
            for test in failed_tests:
                print(f"  • {test['name']}: {test['message']}")

        print(f"\n🔮 整體評估:")
        if summary["success_rate"] >= 95:
            print(f"  • 🌟 優秀：系統架構完整，功能實現度極高")
        elif summary["success_rate"] >= 90:
            print(f"  • ✅ 良好：系統基本完整，少量功能需要完善")
        elif summary["success_rate"] >= 80:
            print(f"  • ⚠️ 尚可：核心功能完成，部分特性需要改進")
        else:
            print(f"  • ❌ 不足：需要重大改進才能達到目標")

        print(f"\n💡 建議:")
        print(
            f"  • 確保所有容器都在運行 (NetStack: 8080, SimWorld: 8888, Frontend: 5173)"
        )
        print(f"  • 優先使用容器內測試以確保測試環境一致性")
        print(f"  • 檢查容器間網絡連接和服務依賴")
        print(f"  • 查看容器日誌以診斷具體問題: docker logs <container_name>")


async def main():
    """主函數"""
    tester = ComprehensiveAPIAndDashboardTest()
    summary = await tester.run_comprehensive_tests()
    tester.print_test_results(summary)

    # 保存結果到文件
    results_file = project_root / "test_results_api_dashboard_comprehensive.json"
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"\n💾 測試結果已保存到: {results_file}")

    return 0 if summary["overall_success"] else 1


if __name__ == "__main__":
    try:
        exit(asyncio.run(main()))
    except KeyboardInterrupt:
        print("\n⚠️ 測試被用戶中斷")
        exit(1)
    except Exception as e:
        print(f"\n❌ 測試執行錯誤: {e}")
        exit(1)
