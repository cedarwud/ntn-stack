from typing import Dict, List, Optional, Any
import logging
import subprocess
import os
import json
import asyncio
import re

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ueransim_service")

# 配置常數
UERANSIM_GNB_CONFIG_DIR = "/etc/ueransim/gnb_configs"
UERANSIM_UE_CONFIG_DIR = "/etc/ueransim/ue_configs"
UERANSIM_GNB_CMD = "nr-gnb"
UERANSIM_UE_CMD = "nr-ue"


class UERANSIMService:
    """與UERANSIM交互的服務類"""

    def __init__(
        self,
        gnb_config_dir: str = UERANSIM_GNB_CONFIG_DIR,
        ue_config_dir: str = UERANSIM_UE_CONFIG_DIR,
    ):
        """初始化UERANSIM服務

        Args:
            gnb_config_dir: gNodeB配置目錄
            ue_config_dir: UE配置目錄
        """
        self.gnb_config_dir = gnb_config_dir
        self.ue_config_dir = ue_config_dir
        self.running_gnbs = {}
        self.running_ues = {}

    async def get_gnbs(self) -> List[Dict[str, Any]]:
        """獲取所有gNodeB配置

        Returns:
            gNodeB配置列表
        """
        gnbs = []
        try:
            for filename in os.listdir(self.gnb_config_dir):
                if filename.endswith(".yaml") or filename.endswith(".yml"):
                    gnb_id = filename.split(".")[0]
                    config_path = os.path.join(self.gnb_config_dir, filename)
                    running = gnb_id in self.running_gnbs

                    gnbs.append(
                        {"id": gnb_id, "config_path": config_path, "running": running}
                    )
        except Exception as e:
            logger.error(f"獲取gNodeB列表失敗: {str(e)}")

        return gnbs

    async def get_ues(self) -> List[Dict[str, Any]]:
        """獲取所有UE配置

        Returns:
            UE配置列表
        """
        ues = []
        try:
            for filename in os.listdir(self.ue_config_dir):
                if filename.endswith(".yaml") or filename.endswith(".yml"):
                    ue_id = filename.split(".")[0]
                    config_path = os.path.join(self.ue_config_dir, filename)
                    running = ue_id in self.running_ues

                    ues.append(
                        {"id": ue_id, "config_path": config_path, "running": running}
                    )
        except Exception as e:
            logger.error(f"獲取UE列表失敗: {str(e)}")

        return ues

    async def start_gnb(self, gnb_id: str) -> bool:
        """啟動gNodeB

        Args:
            gnb_id: gNodeB的ID

        Returns:
            啟動是否成功
        """
        if gnb_id in self.running_gnbs:
            logger.info(f"gNodeB {gnb_id} 已在運行中")
            return True

        config_path = os.path.join(self.gnb_config_dir, f"{gnb_id}.yaml")
        if not os.path.exists(config_path):
            logger.error(f"gNodeB配置文件不存在: {config_path}")
            return False

        try:
            # 啟動gNodeB進程
            process = await asyncio.create_subprocess_exec(
                UERANSIM_GNB_CMD,
                "-c",
                config_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            self.running_gnbs[gnb_id] = process
            logger.info(f"gNodeB {gnb_id} 啟動成功，進程ID: {process.pid}")
            return True
        except Exception as e:
            logger.error(f"啟動gNodeB {gnb_id} 失敗: {str(e)}")
            return False

    async def stop_gnb(self, gnb_id: str) -> bool:
        """停止gNodeB

        Args:
            gnb_id: gNodeB的ID

        Returns:
            停止是否成功
        """
        if gnb_id not in self.running_gnbs:
            logger.info(f"gNodeB {gnb_id} 未在運行")
            return True

        try:
            process = self.running_gnbs[gnb_id]
            process.terminate()
            await process.wait()
            del self.running_gnbs[gnb_id]
            logger.info(f"gNodeB {gnb_id} 已停止")
            return True
        except Exception as e:
            logger.error(f"停止gNodeB {gnb_id} 失敗: {str(e)}")
            return False

    async def start_ue(self, ue_id: str) -> bool:
        """啟動UE

        Args:
            ue_id: UE的ID

        Returns:
            啟動是否成功
        """
        if ue_id in self.running_ues:
            logger.info(f"UE {ue_id} 已在運行中")
            return True

        config_path = os.path.join(self.ue_config_dir, f"{ue_id}.yaml")
        if not os.path.exists(config_path):
            logger.error(f"UE配置文件不存在: {config_path}")
            return False

        try:
            # 啟動UE進程
            process = await asyncio.create_subprocess_exec(
                UERANSIM_UE_CMD,
                "-c",
                config_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            self.running_ues[ue_id] = process
            logger.info(f"UE {ue_id} 啟動成功，進程ID: {process.pid}")
            return True
        except Exception as e:
            logger.error(f"啟動UE {ue_id} 失敗: {str(e)}")
            return False

    async def stop_ue(self, ue_id: str) -> bool:
        """停止UE

        Args:
            ue_id: UE的ID

        Returns:
            停止是否成功
        """
        if ue_id not in self.running_ues:
            logger.info(f"UE {ue_id} 未在運行")
            return True

        try:
            process = self.running_ues[ue_id]
            process.terminate()
            await process.wait()
            del self.running_ues[ue_id]
            logger.info(f"UE {ue_id} 已停止")
            return True
        except Exception as e:
            logger.error(f"停止UE {ue_id} 失敗: {str(e)}")
            return False

    async def get_gnb_status(self, gnb_id: str) -> Dict[str, Any]:
        """獲取gNodeB的運行狀態

        Args:
            gnb_id: gNodeB的ID

        Returns:
            gNodeB狀態信息
        """
        status = {
            "id": gnb_id,
            "running": gnb_id in self.running_gnbs,
            "uptime": None,
            "connected_ues": 0,
        }

        if gnb_id in self.running_gnbs:
            # 這裡可以添加獲取更多詳細狀態的邏輯
            # 例如通過檢查進程輸出或調用UERANSIM的狀態API
            pass

        return status

    async def get_ue_status(self, ue_id: str) -> Dict[str, Any]:
        """獲取UE的運行狀態

        Args:
            ue_id: UE的ID

        Returns:
            UE狀態信息
        """
        status = {
            "id": ue_id,
            "running": ue_id in self.running_ues,
            "connected": False,
            "signal_strength": None,
            "ip_address": None,
        }

        if ue_id in self.running_ues:
            # 獲取UE的IP地址
            try:
                result = await asyncio.create_subprocess_shell(
                    f"ip addr show uesimtun0",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, _ = await result.communicate()
                output = stdout.decode()

                # 解析IP地址
                ip_match = re.search(r"inet\s+(\d+\.\d+\.\d+\.\d+)", output)
                if ip_match:
                    status["ip_address"] = ip_match.group(1)
                    status["connected"] = True
            except Exception as e:
                logger.error(f"獲取UE {ue_id} IP地址失敗: {str(e)}")

        return status
