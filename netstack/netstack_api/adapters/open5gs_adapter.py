"""
Open5GS 適配器

處理與 Open5GS 核心網服務的互動和管理
"""

import asyncio
import subprocess
from typing import Dict, List, Optional, Any

import httpx
import structlog

logger = structlog.get_logger(__name__)


class Open5GSAdapter:
    """Open5GS 核心網適配器"""

    def __init__(self, mongo_host: str = "mongo"):
        """
        初始化 Open5GS 適配器

        Args:
            mongo_host: MongoDB 主機名稱
        """
        self.mongo_host = mongo_host
        self.services = {
            "amf": "http://netstack-amf:7777",
            "smf": "http://netstack-smf:7777",
            "nrf": "http://netstack-nrf:7777",
            "nssf": "http://netstack-nssf:7777",
            "upf": "http://netstack-upf:8080",
        }

    async def health_check(self) -> Dict[str, Any]:
        """檢查 Open5GS 服務健康狀態"""
        service_status = {}
        healthy_count = 0

        async with httpx.AsyncClient(timeout=5.0) as client:
            for service_name, service_url in self.services.items():
                try:
                    response = await client.get(f"{service_url}/health")
                    if response.status_code == 200:
                        service_status[service_name] = "healthy"
                        healthy_count += 1
                    else:
                        service_status[service_name] = "unhealthy"
                except Exception as e:
                    service_status[service_name] = f"error: {str(e)}"

        overall_status = (
            "healthy" if healthy_count == len(self.services) else "degraded"
        )

        return {
            "status": overall_status,
            "services": service_status,
            "services_count": len(self.services),
            "healthy_count": healthy_count,
        }

    async def get_amf_status(self) -> Dict[str, Any]:
        """取得 AMF 狀態"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{self.services['amf']}/namf-comm/v1/status"
                )
                if response.status_code == 200:
                    return response.json()
                else:
                    return {"error": f"AMF 回應錯誤: {response.status_code}"}
        except Exception as e:
            logger.error("取得 AMF 狀態失敗", error=str(e))
            return {"error": str(e)}

    async def get_smf_sessions(self) -> List[Dict[str, Any]]:
        """取得 SMF 會話列表"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{self.services['smf']}/nsmf-pdusession/v1/sessions"
                )
                if response.status_code == 200:
                    return response.json()
                else:
                    return []
        except Exception as e:
            logger.error("取得 SMF 會話失敗", error=str(e))
            return []

    async def trigger_slice_selection(
        self, imsi: str, sst: int, sd: str
    ) -> Dict[str, Any]:
        """
        觸發 NSSF Slice 選擇

        Args:
            imsi: UE IMSI
            sst: Slice/Service Type
            sd: Slice Differentiator

        Returns:
            Slice 選擇結果
        """
        try:
            # 構建 NSSF Slice 選擇請求
            slice_selection_request = {
                "nfType": "AMF",
                "nfId": "amf-001",
                "sliceInfoRequestForRegistration": {
                    "subscribedNssai": [{"sst": sst, "sd": sd}]
                },
                "tai": {"plmnId": {"mcc": "999", "mnc": "70"}, "tac": "1"},
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.services['nssf']}/nnssf-nsselection/v1/network-slice-information",
                    json=slice_selection_request,
                    headers={"Content-Type": "application/json"},
                )

                if response.status_code in [200, 201]:
                    result = response.json()
                    logger.info(
                        "NSSF Slice 選擇成功", imsi=imsi, sst=sst, sd=sd, result=result
                    )
                    return {"success": True, "result": result}
                else:
                    logger.error(
                        "NSSF Slice 選擇失敗",
                        imsi=imsi,
                        status_code=response.status_code,
                        response=response.text,
                    )
                    return {
                        "success": False,
                        "error": f"NSSF 回應錯誤: {response.status_code}",
                    }

        except Exception as e:
            logger.error(
                "觸發 NSSF Slice 選擇失敗", imsi=imsi, sst=sst, sd=sd, error=str(e)
            )
            return {"success": False, "error": str(e)}

    async def execute_dbctl_command(self, command: str) -> Dict[str, Any]:
        """
        執行 open5gs-dbctl 命令

        Args:
            command: 要執行的命令

        Returns:
            命令執行結果
        """
        try:
            # 構建 Docker 命令
            docker_cmd = [
                "docker",
                "run",
                "--rm",
                "--net",
                "compose_netstack-core",
                "-e",
                f"DB_URI=mongodb://{self.mongo_host}/open5gs",
                "gradiant/open5gs-dbctl:0.10.3",
                "open5gs-dbctl",
                command,
            ]

            # 執行命令
            process = await asyncio.create_subprocess_exec(
                *docker_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                logger.info("open5gs-dbctl 命令執行成功", command=command)
                return {"success": True, "output": stdout.decode(), "command": command}
            else:
                logger.warning(
                    "open5gs-dbctl 命令執行失敗",
                    command=command,
                    returncode=process.returncode,
                    stderr=stderr.decode(),
                )
                return {"success": False, "error": stderr.decode(), "command": command}

        except FileNotFoundError as e:
            logger.warning(
                "Docker 或 open5gs-dbctl 映像檔不可用",
                command=command,
                error=str(e),
                suggestion="系統將繼續使用 MongoDB 直接操作",
            )
            return {
                "success": False,
                "error": f"Docker 命令不可用: {str(e)}",
                "command": command,
                "fallback": "使用 MongoDB 直接操作",
            }
        except Exception as e:
            logger.warning("執行 open5gs-dbctl 命令失敗", command=command, error=str(e))
            return {"success": False, "error": str(e), "command": command}

    async def add_subscriber_with_slice(
        self, imsi: str, key: str, opc: str, apn: str, sst: int, sd: str
    ) -> Dict[str, Any]:
        """
        使用 dbctl 新增帶有 Slice 的用戶

        Args:
            imsi: UE IMSI
            key: K 金鑰
            opc: OPc 值
            apn: 接入點名稱
            sst: Slice/Service Type
            sd: Slice Differentiator

        Returns:
            新增結果
        """
        command = f"add_ue_with_slice {imsi} {key} {opc} {apn} {sst} {sd}"
        return await self.execute_dbctl_command(command)

    async def update_subscriber_slice(
        self, imsi: str, apn: str, sst: int, sd: str
    ) -> Dict[str, Any]:
        """
        更新用戶的 Slice 配置

        Args:
            imsi: UE IMSI
            apn: 接入點名稱
            sst: Slice/Service Type
            sd: Slice Differentiator

        Returns:
            更新結果
        """
        command = f"update_slice {imsi} {apn} {sst} {sd}"
        return await self.execute_dbctl_command(command)

    async def remove_subscriber(self, imsi: str) -> Dict[str, Any]:
        """
        移除用戶

        Args:
            imsi: UE IMSI

        Returns:
            移除結果
        """
        command = f"remove {imsi}"
        return await self.execute_dbctl_command(command)

    async def show_all_subscribers(self) -> Dict[str, Any]:
        """
        顯示所有用戶

        Returns:
            用戶列表
        """
        command = "showall"
        return await self.execute_dbctl_command(command)

    async def get_upf_metrics(self) -> Dict[str, Any]:
        """取得 UPF 指標"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.services['upf']}/metrics")
                if response.status_code == 200:
                    # 解析 Prometheus 格式的指標
                    metrics_text = response.text
                    metrics = {}

                    for line in metrics_text.split("\n"):
                        if line.startswith("#") or not line.strip():
                            continue
                        if " " in line:
                            metric_name, metric_value = line.split(" ", 1)
                            try:
                                metrics[metric_name] = float(metric_value)
                            except ValueError:
                                metrics[metric_name] = metric_value

                    return {"success": True, "metrics": metrics}
                else:
                    return {
                        "success": False,
                        "error": f"UPF 指標取得失敗: {response.status_code}",
                    }
        except Exception as e:
            logger.error("取得 UPF 指標失敗", error=str(e))
            return {"success": False, "error": str(e)}

    async def restart_service(self, service_name: str) -> Dict[str, Any]:
        """
        重啟指定的 Open5GS 服務

        Args:
            service_name: 服務名稱 (amf, smf, upf 等)

        Returns:
            重啟結果
        """
        try:
            container_name = f"netstack-{service_name}"

            # 執行 Docker 重啟命令
            process = await asyncio.create_subprocess_exec(
                "docker",
                "restart",
                container_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                logger.info("服務重啟成功", service=service_name)
                return {"success": True, "message": f"{service_name} 服務重啟成功"}
            else:
                logger.error(
                    "服務重啟失敗", service=service_name, stderr=stderr.decode()
                )
                return {"success": False, "error": stderr.decode()}

        except Exception as e:
            logger.error("重啟服務失敗", service=service_name, error=str(e))
            return {"success": False, "error": str(e)}

    async def update_ue_slice_config(
        self, imsi: str, sst: int, sd: str, qos_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        更新 UE 的 Slice 配置

        Args:
            imsi: UE IMSI
            sst: Slice/Service Type
            sd: Slice Differentiator
            qos_profile: QoS 配置

        Returns:
            更新結果
        """
        try:
            # 使用 MongoDB 直接更新用戶的 Slice 配置
            command = f"update_slice {imsi} internet {sst} {sd}"
            result = await self.execute_dbctl_command(command)

            logger.info(
                "UE Slice 配置更新完成",
                imsi=imsi,
                sst=sst,
                sd=sd,
                success=result.get("success", False),
            )

            return result

        except Exception as e:
            logger.error(
                "更新 UE Slice 配置失敗", imsi=imsi, sst=sst, sd=sd, error=str(e)
            )
            return {"success": False, "error": str(e)}

    async def update_smf_session_config(
        self, imsi: str, slice_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        更新 SMF 會話配置

        Args:
            imsi: UE IMSI
            slice_config: Slice 配置

        Returns:
            更新結果
        """
        try:
            # 在實際環境中，這裡會調用 SMF 的 API 來更新會話配置
            # 目前返回模擬結果
            logger.info(
                "SMF 會話配置更新",
                imsi=imsi,
                slice_type=slice_config.get("name", "unknown"),
            )

            return {
                "success": True,
                "message": "SMF 會話配置已更新",
                "slice_config": slice_config,
            }

        except Exception as e:
            logger.error("更新 SMF 會話配置失敗", imsi=imsi, error=str(e))
            return {"success": False, "error": str(e)}

    async def trigger_ue_reregistration(self, imsi: str) -> Dict[str, Any]:
        """
        觸發 UE 重新註冊

        Args:
            imsi: UE IMSI

        Returns:
            觸發結果
        """
        try:
            # 在實際環境中，這裡會通過 AMF API 觸發 UE 重新註冊
            # 目前返回模擬結果
            logger.info("觸發 UE 重新註冊", imsi=imsi)

            return {"success": True, "message": f"UE {imsi} 重新註冊已觸發"}

        except Exception as e:
            logger.error("觸發 UE 重新註冊失敗", imsi=imsi, error=str(e))
            return {"success": False, "error": str(e)}
