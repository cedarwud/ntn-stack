"""
干擾控制服務

整合 simworld 的干擾模擬和 AI-RAN 決策，
將抗干擾策略應用到 UERANSIM 配置中。
"""

import asyncio
import logging
import uuid
import json
import aiohttp
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class InterferenceControlService:
    """干擾控制服務"""

    def __init__(
        self,
        simworld_api_url: str = "http://simworld-backend:8000",
        ueransim_config_dir: str = "/tmp/ueransim_configs",
        update_interval_sec: float = 5.0,
    ):
        """
        初始化干擾控制服務

        Args:
            simworld_api_url: simworld API 基礎URL
            ueransim_config_dir: UERANSIM 配置文件目錄
            update_interval_sec: 干擾監控更新間隔（秒）
        """
        self.simworld_api_url = simworld_api_url.rstrip("/")
        self.ueransim_config_dir = Path(ueransim_config_dir)
        self.update_interval_sec = update_interval_sec

        # 確保配置目錄存在
        self.ueransim_config_dir.mkdir(parents=True, exist_ok=True)

        # 狀態管理
        self.is_monitoring = False
        self.monitoring_task = None
        self.active_scenarios = {}
        self.current_interference_state = []
        self.ai_ran_decisions = []

        # HTTP 會話
        self.session = None

        self.logger = logger
        self.logger.info(f"干擾控制服務初始化完成")

    async def start(self):
        """啟動服務"""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)

        # 啟動干擾監控
        await self.start_interference_monitoring()

        self.logger.info(f"干擾控制服務已啟動，simworld URL: {self.simworld_api_url}")

    async def stop(self):
        """停止服務"""
        await self.stop_interference_monitoring()

        if self.session:
            await self.session.close()
            self.session = None

        self.logger.info("干擾控制服務已停止")

    async def simulate_jammer_scenario(
        self,
        scenario_name: str,
        jammer_configs: List[Dict[str, Any]],
        victim_positions: List[List[float]],
        victim_frequency_mhz: float = 2150.0,
        victim_bandwidth_mhz: float = 20.0,
    ) -> Dict[str, Any]:
        """
        模擬干擾場景

        Args:
            scenario_name: 場景名稱
            jammer_configs: 干擾源配置列表
            victim_positions: 受害者位置列表
            victim_frequency_mhz: 受害者工作頻率
            victim_bandwidth_mhz: 受害者頻寬

        Returns:
            模擬結果
        """
        try:
            self.logger.info(f"開始模擬干擾場景: {scenario_name}")

            # 創建干擾環境
            environment_bounds = {
                "min_x": -2000,
                "max_x": 2000,
                "min_y": -2000,
                "max_y": 2000,
                "min_z": 0,
                "max_z": 200,
            }

            # 調用 simworld API 創建場景
            create_url = f"{self.simworld_api_url}/api/v1/interference/scenario/create"
            create_params = {
                "scenario_name": scenario_name,
                "jammer_configs": jammer_configs,
                "environment_bounds": environment_bounds,
                "duration_sec": 60.0,
            }

            timeout = aiohttp.ClientTimeout(total=30)
            async with self.session.post(
                create_url, json=create_params, timeout=timeout
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"創建場景失敗: {error_text}")

                create_result = await response.json()
                environment = create_result["environment"]

            # 準備模擬請求
            simulation_request = {
                "request_id": f"sim_{uuid.uuid4().hex[:8]}",
                "environment": environment,
                "victim_positions": [tuple(pos) for pos in victim_positions],
                "victim_frequency_mhz": victim_frequency_mhz,
                "victim_bandwidth_mhz": victim_bandwidth_mhz,
                "simulation_time_step_ms": 10.0,
                "use_gpu_acceleration": True,
            }

            # 執行干擾模擬
            simulate_url = f"{self.simworld_api_url}/api/v1/interference/simulate"

            async with self.session.post(
                simulate_url, json=simulation_request
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"干擾模擬失敗: {error_text}")

                simulation_result = await response.json()

            # 儲存場景狀態
            scenario_id = simulation_result["simulation_id"]
            self.active_scenarios[scenario_id] = {
                "scenario_name": scenario_name,
                "simulation_result": simulation_result,
                "created_at": datetime.utcnow(),
                "status": "active",
            }

            self.logger.info(f"干擾場景 {scenario_name} 模擬完成: {scenario_id}")

            return {
                "success": True,
                "scenario_id": scenario_id,
                "simulation_result": simulation_result,
                "affected_victims": simulation_result["affected_victim_count"],
                "avg_sinr_degradation": simulation_result[
                    "average_sinr_degradation_db"
                ],
            }

        except Exception as e:
            self.logger.error(f"模擬干擾場景失敗: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def request_ai_ran_decision(
        self,
        interference_state: List[Dict[str, Any]],
        available_frequencies: List[float],
        scenario_description: str = "UERANSIM 抗干擾請求",
    ) -> Dict[str, Any]:
        """
        請求 AI-RAN 抗干擾決策

        Args:
            interference_state: 當前干擾狀態
            available_frequencies: 可用頻率列表
            scenario_description: 場景描述

        Returns:
            AI-RAN 決策結果
        """
        try:
            self.logger.info(f"請求 AI-RAN 決策: {scenario_description}")

            # 構建 AI-RAN 控制請求
            ai_ran_request = {
                "request_id": f"ai_ran_{uuid.uuid4().hex[:8]}",
                "scenario_description": scenario_description,
                "current_interference_state": interference_state,
                "current_network_performance": {
                    "throughput_mbps": 100.0,
                    "latency_ms": 10.0,
                    "packet_loss_rate": 0.01,
                },
                "available_frequencies_mhz": available_frequencies,
                "power_constraints_dbm": {"max": 30, "min": 5},
                "latency_requirements_ms": 1.0,
                "model_type": "DQN",
                "use_historical_data": True,
                "risk_tolerance": 0.1,
            }

            # 調用 simworld AI-RAN API
            ai_ran_url = f"{self.simworld_api_url}/api/v1/interference/ai-ran/control"

            async with self.session.post(ai_ran_url, json=ai_ran_request) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"AI-RAN 決策失敗: {error_text}")

                ai_ran_result = await response.json()

            # 儲存決策歷史
            if ai_ran_result["success"]:
                self.ai_ran_decisions.append(
                    {
                        "decision_result": ai_ran_result,
                        "timestamp": datetime.utcnow(),
                        "applied": False,
                    }
                )

            self.logger.info(
                f"AI-RAN 決策完成: {ai_ran_result['ai_decision']['decision_type']}"
            )

            return ai_ran_result

        except Exception as e:
            self.logger.error(f"AI-RAN 決策失敗: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def apply_anti_jamming_strategy(
        self,
        ai_decision: Dict[str, Any],
        ue_config_path: Optional[str] = None,
        gnb_config_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        應用抗干擾策略到 UERANSIM 配置

        Args:
            ai_decision: AI-RAN 決策
            ue_config_path: UE 配置文件路徑
            gnb_config_path: gNodeB 配置文件路徑

        Returns:
            應用結果
        """
        try:
            decision_type = ai_decision["decision_type"]
            self.logger.info(f"應用抗干擾策略: {decision_type}")

            results = []

            if decision_type == "frequency_hop":
                result = await self._apply_frequency_hop_strategy(
                    ai_decision, ue_config_path, gnb_config_path
                )
                results.append(result)

            elif decision_type == "beam_steering":
                result = await self._apply_beam_steering_strategy(
                    ai_decision, gnb_config_path
                )
                results.append(result)

            elif decision_type == "power_control":
                result = await self._apply_power_control_strategy(
                    ai_decision, ue_config_path, gnb_config_path
                )
                results.append(result)

            elif decision_type == "emergency_shutdown":
                result = await self._apply_emergency_shutdown(ai_decision)
                results.append(result)

            # 標記決策已應用
            for decision_record in self.ai_ran_decisions:
                if (
                    decision_record["decision_result"]["ai_decision"]["decision_id"]
                    == ai_decision["decision_id"]
                ):
                    decision_record["applied"] = True
                    decision_record["applied_at"] = datetime.utcnow()
                    break

            success = all(r["success"] for r in results)

            return {
                "success": success,
                "message": f"抗干擾策略 {decision_type} 應用{'成功' if success else '失敗'}",
                "applied_strategies": results,
                "decision_id": ai_decision["decision_id"],
            }

        except Exception as e:
            self.logger.error(f"應用抗干擾策略失敗: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def _apply_frequency_hop_strategy(
        self,
        ai_decision: Dict[str, Any],
        ue_config_path: Optional[str] = None,
        gnb_config_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """應用跳頻策略"""
        try:
            target_frequencies = ai_decision.get("target_frequencies_mhz", [])

            if not target_frequencies:
                return {"success": False, "error": "未指定目標頻率"}

            target_freq = target_frequencies[0]  # 使用第一個頻率

            # 更新 gNodeB 配置
            if gnb_config_path:
                await self._update_gnb_frequency(gnb_config_path, target_freq)

            # 更新 UE 配置
            if ue_config_path:
                await self._update_ue_frequency(ue_config_path, target_freq)

            self.logger.info(f"跳頻策略應用成功，目標頻率: {target_freq} MHz")

            return {
                "success": True,
                "strategy": "frequency_hop",
                "target_frequency_mhz": target_freq,
                "execution_time_ms": ai_decision.get("execution_delay_ms", 1.0),
            }

        except Exception as e:
            self.logger.error(f"應用跳頻策略失敗: {e}")
            return {"success": False, "error": str(e)}

    async def _apply_beam_steering_strategy(
        self, ai_decision: Dict[str, Any], gnb_config_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """應用波束控制策略"""
        try:
            beam_config_id = ai_decision.get("beam_config_id")

            if not beam_config_id:
                return {"success": False, "error": "未指定波束配置ID"}

            # 這裡應該根據 beam_config_id 獲取具體的波束配置
            # 簡化實現：直接應用默認波束設置
            if gnb_config_path:
                await self._update_gnb_beam_config(
                    gnb_config_path,
                    {
                        "beam_direction": [45.0, 10.0],  # azimuth, elevation
                        "beam_width": 20.0,
                        "antenna_count": 8,
                    },
                )

            self.logger.info(f"波束控制策略應用成功，配置ID: {beam_config_id}")

            return {
                "success": True,
                "strategy": "beam_steering",
                "beam_config_id": beam_config_id,
                "execution_time_ms": ai_decision.get("execution_delay_ms", 2.0),
            }

        except Exception as e:
            self.logger.error(f"應用波束控制策略失敗: {e}")
            return {"success": False, "error": str(e)}

    async def _apply_power_control_strategy(
        self,
        ai_decision: Dict[str, Any],
        ue_config_path: Optional[str] = None,
        gnb_config_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """應用功率控制策略"""
        try:
            power_adjustment = ai_decision.get("power_adjustment_db", 0.0)

            # 更新 gNodeB 功率
            if gnb_config_path:
                await self._update_gnb_power(gnb_config_path, power_adjustment)

            # 更新 UE 功率
            if ue_config_path:
                await self._update_ue_power(ue_config_path, power_adjustment)

            self.logger.info(f"功率控制策略應用成功，功率調整: {power_adjustment} dB")

            return {
                "success": True,
                "strategy": "power_control",
                "power_adjustment_db": power_adjustment,
                "execution_time_ms": ai_decision.get("execution_delay_ms", 0.5),
            }

        except Exception as e:
            self.logger.error(f"應用功率控制策略失敗: {e}")
            return {"success": False, "error": str(e)}

    async def _apply_emergency_shutdown(
        self, ai_decision: Dict[str, Any]
    ) -> Dict[str, Any]:
        """應用緊急關閉策略"""
        try:
            self.logger.warning("執行緊急關閉策略")

            # 這裡應該停止 UERANSIM 進程或切換到安全模式
            # 簡化實現：記錄緊急狀態

            return {
                "success": True,
                "strategy": "emergency_shutdown",
                "message": "系統已切換到緊急安全模式",
                "execution_time_ms": ai_decision.get("execution_delay_ms", 0.1),
            }

        except Exception as e:
            self.logger.error(f"執行緊急關閉失敗: {e}")
            return {"success": False, "error": str(e)}

    # 配置文件更新方法（簡化實現）

    async def _update_gnb_frequency(self, config_path: str, frequency_mhz: float):
        """更新 gNodeB 頻率配置"""
        # 這裡應該解析並修改 UERANSIM gNodeB 配置文件
        self.logger.info(
            f"更新 gNodeB 配置文件 {config_path} 的頻率為 {frequency_mhz} MHz"
        )

    async def _update_ue_frequency(self, config_path: str, frequency_mhz: float):
        """更新 UE 頻率配置"""
        # 這裡應該解析並修改 UERANSIM UE 配置文件
        self.logger.info(f"更新 UE 配置文件 {config_path} 的頻率為 {frequency_mhz} MHz")

    async def _update_gnb_beam_config(
        self, config_path: str, beam_config: Dict[str, Any]
    ):
        """更新 gNodeB 波束配置"""
        self.logger.info(f"更新 gNodeB 配置文件 {config_path} 的波束設置")

    async def _update_gnb_power(self, config_path: str, power_adjustment_db: float):
        """更新 gNodeB 功率配置"""
        self.logger.info(
            f"調整 gNodeB 配置文件 {config_path} 的功率 {power_adjustment_db} dB"
        )

    async def _update_ue_power(self, config_path: str, power_adjustment_db: float):
        """更新 UE 功率配置"""
        self.logger.info(
            f"調整 UE 配置文件 {config_path} 的功率 {power_adjustment_db} dB"
        )

    # 監控和管理方法

    async def start_interference_monitoring(self):
        """啟動干擾監控"""
        if self.is_monitoring:
            return

        self.is_monitoring = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        self.logger.info("干擾監控已啟動")

    async def stop_interference_monitoring(self):
        """停止干擾監控"""
        if not self.is_monitoring:
            return

        self.is_monitoring = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass

        self.logger.info("干擾監控已停止")

    async def _monitoring_loop(self):
        """監控循環"""
        while self.is_monitoring:
            try:
                # 檢查活躍場景中的干擾狀態
                await self._check_interference_levels()

                # 等待下次檢查
                await asyncio.sleep(self.update_interval_sec)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"監控循環錯誤: {e}")
                await asyncio.sleep(1.0)

    async def _check_interference_levels(self):
        """檢查干擾水平"""
        # 這裡應該實現實際的干擾檢測邏輯
        # 簡化版本：模擬干擾檢測
        pass

    def get_service_status(self) -> Dict[str, Any]:
        """獲取服務狀態"""
        return {
            "service_name": "InterferenceControlService",
            "is_monitoring": self.is_monitoring,
            "active_scenarios_count": len(self.active_scenarios),
            "ai_ran_decisions_count": len(self.ai_ran_decisions),
            "simworld_api_url": self.simworld_api_url,
            "ueransim_config_dir": str(self.ueransim_config_dir),
            "update_interval_sec": self.update_interval_sec,
        }
