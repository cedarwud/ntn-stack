"""
閉環干擾檢測與頻率跳變控制機制
實現階段四：干擾檢測與頻率跳變的閉環控制機制
"""

import asyncio
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass
from enum import Enum
import numpy as np
import structlog

logger = structlog.get_logger(__name__)


class FrequencyState(Enum):
    """頻率狀態"""
    CLEAN = "clean"
    MODERATE_INTERFERENCE = "moderate_interference"
    SEVERE_INTERFERENCE = "severe_interference"
    UNKNOWN = "unknown"


class ControlAction(Enum):
    """控制動作"""
    MAINTAIN = "maintain"
    FREQUENCY_HOP = "frequency_hop"
    POWER_ADJUST = "power_adjust"
    BEAM_FORMING = "beam_forming"
    EMERGENCY_SWITCH = "emergency_switch"


@dataclass
class FrequencyChannel:
    """頻率通道"""
    frequency_mhz: float
    bandwidth_mhz: float
    state: FrequencyState
    interference_level_db: float
    last_updated: datetime
    usage_history: List[float]  # SINR 歷史
    occupation_time: float  # 佔用時間（秒）
    switch_count: int  # 切換次數
    
    def update_state(self, new_interference_level: float, sinr_db: float):
        """更新頻率狀態"""
        self.interference_level_db = new_interference_level
        self.usage_history.append(sinr_db)
        if len(self.usage_history) > 100:  # 保留最近 100 個記錄
            self.usage_history.pop(0)
        self.last_updated = datetime.utcnow()
        
        # 更新狀態
        if new_interference_level < -100:
            self.state = FrequencyState.CLEAN
        elif new_interference_level < -85:
            self.state = FrequencyState.MODERATE_INTERFERENCE
        else:
            self.state = FrequencyState.SEVERE_INTERFERENCE

    def get_average_sinr(self) -> float:
        """獲取平均 SINR"""
        return np.mean(self.usage_history) if self.usage_history else 0.0

    def get_stability_score(self) -> float:
        """獲取穩定性評分（0-1）"""
        if len(self.usage_history) < 5:
            return 0.5
        variance = np.var(self.usage_history)
        return max(0.0, min(1.0, 1.0 - variance / 100.0))


@dataclass
class ControlDecision:
    """控制決策"""
    decision_id: str
    timestamp: datetime
    current_frequency: float
    target_frequency: Optional[float]
    action: ControlAction
    confidence: float
    reasoning: str
    expected_improvement: float
    execution_delay_ms: int


class ClosedLoopInterferenceController:
    """閉環干擾控制器"""

    def __init__(
        self,
        interference_threshold_db: float = -85.0,
        sinr_threshold_db: float = 5.0,
        control_interval_ms: int = 500,  # 500ms 控制週期
        frequency_range: Tuple[float, float] = (2100.0, 2500.0),
        frequency_step_mhz: float = 5.0,
        max_hops_per_minute: int = 10,
    ):
        self.interference_threshold_db = interference_threshold_db
        self.sinr_threshold_db = sinr_threshold_db
        self.control_interval_ms = control_interval_ms
        self.frequency_range = frequency_range
        self.frequency_step_mhz = frequency_step_mhz
        self.max_hops_per_minute = max_hops_per_minute

        self.logger = logger.bind(service="closed_loop_interference_controller")

        # 頻率通道管理
        self.frequency_channels: Dict[float, FrequencyChannel] = {}
        self._initialize_frequency_channels()

        # 控制狀態
        self.current_frequency = 2150.0  # 默認頻率
        self.current_sinr_db = 15.0
        self.control_enabled = False
        self.last_hop_time = datetime.utcnow()
        self.hop_count_last_minute = 0

        # 決策歷史
        self.decision_history: List[ControlDecision] = []
        self.control_statistics = {
            "total_decisions": 0,
            "frequency_hops": 0,
            "successful_mitigations": 0,
            "false_positives": 0,
            "average_sinr_improvement": 0.0,
            "control_loop_latency_ms": 0.0,
        }

        # 學習參數
        self.adaptation_rate = 0.1
        self.confidence_threshold = 0.7
        self.stability_weight = 0.3

        # 控制任務
        self.control_task: Optional[asyncio.Task] = None
        self.is_running = False

    def _initialize_frequency_channels(self):
        """初始化頻率通道"""
        freq = self.frequency_range[0]
        while freq <= self.frequency_range[1]:
            self.frequency_channels[freq] = FrequencyChannel(
                frequency_mhz=freq,
                bandwidth_mhz=20.0,
                state=FrequencyState.UNKNOWN,
                interference_level_db=-120.0,
                last_updated=datetime.utcnow(),
                usage_history=[],
                occupation_time=0.0,
                switch_count=0,
            )
            freq += self.frequency_step_mhz

        self.logger.info(f"初始化了 {len(self.frequency_channels)} 個頻率通道")

    async def start_control_loop(self):
        """啟動控制循環"""
        if self.is_running:
            self.logger.warning("控制循環已在運行")
            return

        self.logger.info("🚀 啟動閉環干擾控制循環")
        self.is_running = True
        self.control_enabled = True
        self.control_task = asyncio.create_task(self._control_loop())

    async def stop_control_loop(self):
        """停止控制循環"""
        if not self.is_running:
            return

        self.logger.info("🛑 停止閉環干擾控制循環")
        self.is_running = False
        self.control_enabled = False

        if self.control_task:
            self.control_task.cancel()
            try:
                await self.control_task
            except asyncio.CancelledError:
                pass

    async def _control_loop(self):
        """主控制循環"""
        while self.is_running:
            try:
                loop_start_time = time.time()

                # 步驟 1：感知（測量當前狀態）
                current_state = await self._sense_environment()

                # 步驟 2：決策（分析並制定控制策略）
                decision = await self._make_control_decision(current_state)

                # 步驟 3：執行（應用控制動作）
                if decision and self.control_enabled:
                    execution_result = await self._execute_control_action(decision)
                    await self._update_control_statistics(decision, execution_result)

                # 步驟 4：學習（更新控制參數）
                await self._adaptive_learning(current_state, decision)

                # 計算控制循環延遲
                loop_time_ms = (time.time() - loop_start_time) * 1000
                self._update_loop_latency(loop_time_ms)

                # 等待下一個控制週期
                sleep_time = max(0, (self.control_interval_ms - loop_time_ms) / 1000)
                await asyncio.sleep(sleep_time)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error("控制循環異常", error=str(e))
                await asyncio.sleep(1.0)

    async def _sense_environment(self) -> Dict[str, Any]:
        """感知環境狀態"""
        try:
            # 模擬從各種傳感器和監測點收集數據
            current_state = {
                "timestamp": datetime.utcnow().isoformat(),
                "current_frequency": self.current_frequency,
                "current_sinr_db": self.current_sinr_db,
                "interference_measurements": {},
                "network_performance": {},
                "environment_factors": {},
            }

            # 測量所有頻率通道的干擾水平
            for freq, channel in self.frequency_channels.items():
                # 模擬干擾測量（實際中會從 Sionna 和干擾檢測器獲取）
                interference_level = await self._measure_interference_level(freq)
                sinr_value = await self._measure_sinr(freq)
                
                channel.update_state(interference_level, sinr_value)
                
                current_state["interference_measurements"][freq] = {
                    "interference_level_db": interference_level,
                    "sinr_db": sinr_value,
                    "channel_state": channel.state.value,
                    "stability_score": channel.get_stability_score(),
                }

            # 測量網路性能
            current_state["network_performance"] = {
                "throughput_mbps": await self._measure_throughput(),
                "latency_ms": await self._measure_latency(),
                "packet_loss_rate": await self._measure_packet_loss(),
                "ue_count": await self._get_active_ue_count(),
            }

            # 環境因素
            current_state["environment_factors"] = {
                "mobility_level": await self._assess_mobility(),
                "traffic_load": await self._assess_traffic_load(),
                "time_of_day": datetime.utcnow().hour,
            }

            return current_state

        except Exception as e:
            self.logger.error("環境感知失敗", error=str(e))
            return {"error": str(e)}

    async def _measure_interference_level(self, frequency: float) -> float:
        """測量指定頻率的干擾水平"""
        # 模擬干擾測量
        base_interference = -120.0
        if frequency == self.current_frequency:
            # 當前頻率可能有更多干擾
            noise = np.random.normal(0, 10)
            return base_interference + 20 + noise
        else:
            # 其他頻率的基礎干擾
            noise = np.random.normal(0, 5)
            return base_interference + noise

    async def _measure_sinr(self, frequency: float) -> float:
        """測量指定頻率的 SINR"""
        # 模擬 SINR 測量
        if frequency == self.current_frequency:
            return self.current_sinr_db + np.random.normal(0, 2)
        else:
            # 估算其他頻率的 SINR
            channel = self.frequency_channels[frequency]
            if channel.usage_history:
                return channel.get_average_sinr() + np.random.normal(0, 3)
            else:
                return 10.0 + np.random.normal(0, 5)

    async def _measure_throughput(self) -> float:
        """測量吞吐量"""
        # 基於當前 SINR 估算吞吐量
        sinr_linear = 10 ** (self.current_sinr_db / 10)
        bandwidth_hz = 20e6
        capacity = bandwidth_hz * np.log2(1 + sinr_linear)
        return capacity / 1e6 * np.random.uniform(0.7, 1.0)  # Mbps

    async def _measure_latency(self) -> float:
        """測量延遲"""
        base_latency = 30.0
        sinr_factor = max(1.0, (20 - self.current_sinr_db) / 10)
        return base_latency * sinr_factor + np.random.uniform(0, 10)

    async def _measure_packet_loss(self) -> float:
        """測量丟包率"""
        if self.current_sinr_db > 15:
            return np.random.uniform(0, 0.01)
        elif self.current_sinr_db > 5:
            return np.random.uniform(0.01, 0.05)
        else:
            return np.random.uniform(0.05, 0.2)

    async def _get_active_ue_count(self) -> int:
        """獲取活躍 UE 數量"""
        return np.random.randint(5, 20)

    async def _assess_mobility(self) -> str:
        """評估移動性水平"""
        return np.random.choice(["low", "medium", "high"], p=[0.5, 0.3, 0.2])

    async def _assess_traffic_load(self) -> str:
        """評估流量負載"""
        hour = datetime.utcnow().hour
        if 9 <= hour <= 17:
            return np.random.choice(["medium", "high"], p=[0.3, 0.7])
        else:
            return np.random.choice(["low", "medium"], p=[0.7, 0.3])

    async def _make_control_decision(self, current_state: Dict[str, Any]) -> Optional[ControlDecision]:
        """制定控制決策"""
        try:
            decision_id = f"decision_{uuid.uuid4().hex[:8]}"
            current_freq = current_state["current_frequency"]
            current_sinr = current_state["current_sinr_db"]

            # 分析當前狀態
            interference_analysis = self._analyze_interference_situation(current_state)
            performance_analysis = self._analyze_performance_degradation(current_state)
            
            # 決策邏輯
            action, target_freq, confidence, reasoning = await self._decide_action(
                current_state, interference_analysis, performance_analysis
            )

            # 估算改善效果
            expected_improvement = self._estimate_improvement(action, target_freq, current_state)

            decision = ControlDecision(
                decision_id=decision_id,
                timestamp=datetime.utcnow(),
                current_frequency=current_freq,
                target_frequency=target_freq,
                action=action,
                confidence=confidence,
                reasoning=reasoning,
                expected_improvement=expected_improvement,
                execution_delay_ms=self._estimate_execution_delay(action),
            )

            # 記錄決策
            self.decision_history.append(decision)
            if len(self.decision_history) > 1000:  # 保留最近 1000 個決策
                self.decision_history.pop(0)

            self.control_statistics["total_decisions"] += 1

            self.logger.debug(
                "控制決策",
                decision_id=decision_id,
                action=action.value,
                confidence=confidence,
                reasoning=reasoning
            )

            return decision

        except Exception as e:
            self.logger.error("控制決策失敗", error=str(e))
            return None

    def _analyze_interference_situation(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """分析干擾情況"""
        current_freq = state["current_frequency"]
        measurements = state["interference_measurements"]
        
        current_interference = measurements.get(current_freq, {}).get("interference_level_db", -120)
        current_sinr = measurements.get(current_freq, {}).get("sinr_db", 0)
        
        # 評估干擾嚴重程度
        if current_interference > -70:
            severity = "critical"
        elif current_interference > -85:
            severity = "moderate"
        else:
            severity = "low"
        
        # 分析干擾趨勢
        channel = self.frequency_channels[current_freq]
        trend = "stable"
        if len(channel.usage_history) >= 5:
            recent_avg = np.mean(channel.usage_history[-5:])
            older_avg = np.mean(channel.usage_history[-10:-5]) if len(channel.usage_history) >= 10 else recent_avg
            if recent_avg < older_avg - 3:
                trend = "degrading"
            elif recent_avg > older_avg + 3:
                trend = "improving"

        return {
            "severity": severity,
            "trend": trend,
            "current_interference_db": current_interference,
            "current_sinr_db": current_sinr,
            "requires_action": severity in ["critical", "moderate"] or trend == "degrading"
        }

    def _analyze_performance_degradation(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """分析性能下降"""
        performance = state["network_performance"]
        
        throughput = performance.get("throughput_mbps", 0)
        latency = performance.get("latency_ms", 100)
        packet_loss = performance.get("packet_loss_rate", 0)
        
        # 評估性能下降程度
        degradation_score = 0
        if throughput < 10:
            degradation_score += 3
        elif throughput < 20:
            degradation_score += 1
            
        if latency > 100:
            degradation_score += 2
        elif latency > 50:
            degradation_score += 1
            
        if packet_loss > 0.1:
            degradation_score += 3
        elif packet_loss > 0.05:
            degradation_score += 2
        elif packet_loss > 0.01:
            degradation_score += 1

        severity = "low"
        if degradation_score >= 6:
            severity = "critical"
        elif degradation_score >= 3:
            severity = "moderate"

        return {
            "severity": severity,
            "degradation_score": degradation_score,
            "throughput_mbps": throughput,
            "latency_ms": latency,
            "packet_loss_rate": packet_loss,
            "requires_action": degradation_score >= 3
        }

    async def _decide_action(
        self, current_state: Dict, interference_analysis: Dict, performance_analysis: Dict
    ) -> Tuple[ControlAction, Optional[float], float, str]:
        """決定控制動作"""
        
        # 檢查是否需要採取行動
        if not (interference_analysis["requires_action"] or performance_analysis["requires_action"]):
            return ControlAction.MAINTAIN, None, 0.9, "狀態正常，維持當前配置"

        # 檢查頻率跳變限制
        current_time = datetime.utcnow()
        if (current_time - self.last_hop_time).total_seconds() < 60:
            self.hop_count_last_minute += 1
        else:
            self.hop_count_last_minute = 0
            
        if self.hop_count_last_minute >= self.max_hops_per_minute:
            return ControlAction.POWER_ADJUST, None, 0.6, "頻率跳變次數已達上限，調整功率"

        # 尋找最佳替代頻率
        best_frequency = self._find_best_alternative_frequency(current_state)
        
        if best_frequency is None:
            return ControlAction.BEAM_FORMING, None, 0.7, "無可用替代頻率，使用波束賦形"

        # 評估頻率跳變的收益
        current_freq = current_state["current_frequency"]
        current_quality = self._evaluate_frequency_quality(current_freq, current_state)
        target_quality = self._evaluate_frequency_quality(best_frequency, current_state)
        
        improvement = target_quality - current_quality
        confidence = min(0.95, 0.5 + improvement / 10)  # 基於改善程度計算置信度

        if improvement > 5 and confidence > self.confidence_threshold:
            action = ControlAction.FREQUENCY_HOP
            reasoning = f"切換到 {best_frequency:.1f} MHz，預期改善 {improvement:.1f} dB"
        elif interference_analysis["severity"] == "critical":
            action = ControlAction.EMERGENCY_SWITCH
            reasoning = f"緊急切換到 {best_frequency:.1f} MHz，避免嚴重干擾"
            confidence = 0.95
        else:
            action = ControlAction.POWER_ADJUST
            best_frequency = None
            reasoning = "改善不足，調整發射功率"
            confidence = 0.6

        return action, best_frequency, confidence, reasoning

    def _find_best_alternative_frequency(self, current_state: Dict) -> Optional[float]:
        """尋找最佳替代頻率"""
        current_freq = current_state["current_frequency"]
        measurements = current_state["interference_measurements"]
        
        candidates = []
        for freq, channel in self.frequency_channels.items():
            if freq == current_freq:
                continue
                
            quality_score = self._evaluate_frequency_quality(freq, current_state)
            stability_score = channel.get_stability_score()
            usage_penalty = min(1.0, channel.switch_count / 10)  # 懲罰頻繁切換的頻率
            
            overall_score = quality_score + stability_score * self.stability_weight - usage_penalty
            
            candidates.append((freq, overall_score))
        
        if not candidates:
            return None
            
        # 選擇得分最高的頻率
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0][0]

    def _evaluate_frequency_quality(self, frequency: float, current_state: Dict) -> float:
        """評估頻率質量"""
        measurements = current_state["interference_measurements"]
        freq_data = measurements.get(frequency, {})
        
        interference_level = freq_data.get("interference_level_db", -120)
        sinr = freq_data.get("sinr_db", 0)
        
        # 質量評分（0-100）
        interference_score = max(0, min(100, (interference_level + 120) * 2))
        sinr_score = max(0, min(100, sinr * 3))
        
        return (interference_score + sinr_score) / 2

    def _estimate_improvement(self, action: ControlAction, target_freq: Optional[float], current_state: Dict) -> float:
        """估算改善效果"""
        if action == ControlAction.MAINTAIN:
            return 0.0
        elif action == ControlAction.FREQUENCY_HOP and target_freq:
            current_quality = self._evaluate_frequency_quality(current_state["current_frequency"], current_state)
            target_quality = self._evaluate_frequency_quality(target_freq, current_state)
            return target_quality - current_quality
        elif action == ControlAction.POWER_ADJUST:
            return 2.0  # 功率調整預期改善 2dB
        elif action == ControlAction.BEAM_FORMING:
            return 5.0  # 波束賦形預期改善 5dB
        else:
            return 3.0

    def _estimate_execution_delay(self, action: ControlAction) -> int:
        """估算執行延遲（毫秒）"""
        delays = {
            ControlAction.MAINTAIN: 0,
            ControlAction.FREQUENCY_HOP: 50,
            ControlAction.POWER_ADJUST: 10,
            ControlAction.BEAM_FORMING: 100,
            ControlAction.EMERGENCY_SWITCH: 20,
        }
        return delays.get(action, 50)

    async def _execute_control_action(self, decision: ControlDecision) -> Dict[str, Any]:
        """執行控制動作"""
        try:
            execution_start = time.time()
            
            if decision.action == ControlAction.MAINTAIN:
                result = {"success": True, "message": "維持當前配置"}
                
            elif decision.action in [ControlAction.FREQUENCY_HOP, ControlAction.EMERGENCY_SWITCH]:
                result = await self._execute_frequency_hop(decision.target_frequency)
                
            elif decision.action == ControlAction.POWER_ADJUST:
                result = await self._execute_power_adjustment()
                
            elif decision.action == ControlAction.BEAM_FORMING:
                result = await self._execute_beam_forming()
                
            else:
                result = {"success": False, "error": f"未知動作: {decision.action}"}

            execution_time = (time.time() - execution_start) * 1000
            result["execution_time_ms"] = execution_time
            result["decision_id"] = decision.decision_id

            self.logger.info(
                "控制動作執行",
                action=decision.action.value,
                success=result.get("success", False),
                execution_time_ms=execution_time
            )

            return result

        except Exception as e:
            self.logger.error("控制動作執行失敗", error=str(e))
            return {"success": False, "error": str(e)}

    async def _execute_frequency_hop(self, target_frequency: float) -> Dict[str, Any]:
        """執行頻率跳變"""
        try:
            if target_frequency not in self.frequency_channels:
                return {"success": False, "error": f"無效頻率: {target_frequency}"}

            old_frequency = self.current_frequency
            
            # 模擬頻率切換延遲
            await asyncio.sleep(0.05)  # 50ms 切換時間
            
            # 更新當前頻率
            self.current_frequency = target_frequency
            self.last_hop_time = datetime.utcnow()
            
            # 更新頻率通道統計
            self.frequency_channels[old_frequency].occupation_time += (
                datetime.utcnow() - self.frequency_channels[old_frequency].last_updated
            ).total_seconds()
            self.frequency_channels[target_frequency].switch_count += 1
            
            # 更新 SINR（模擬改善）
            improvement = np.random.uniform(3, 8)
            self.current_sinr_db += improvement
            
            self.control_statistics["frequency_hops"] += 1
            
            return {
                "success": True,
                "old_frequency": old_frequency,
                "new_frequency": target_frequency,
                "sinr_improvement_db": improvement,
                "message": f"成功切換到 {target_frequency:.1f} MHz"
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _execute_power_adjustment(self) -> Dict[str, Any]:
        """執行功率調整"""
        try:
            # 模擬功率調整
            await asyncio.sleep(0.01)  # 10ms 調整時間
            
            adjustment_db = np.random.uniform(1, 3)
            self.current_sinr_db += adjustment_db
            
            return {
                "success": True,
                "power_adjustment_db": adjustment_db,
                "message": f"功率調整 +{adjustment_db:.1f} dB"
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _execute_beam_forming(self) -> Dict[str, Any]:
        """執行波束賦形"""
        try:
            # 模擬波束賦形調整
            await asyncio.sleep(0.1)  # 100ms 調整時間
            
            improvement_db = np.random.uniform(4, 8)
            self.current_sinr_db += improvement_db
            
            return {
                "success": True,
                "beam_forming_gain_db": improvement_db,
                "message": f"波束賦形增益 +{improvement_db:.1f} dB"
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _update_control_statistics(self, decision: ControlDecision, execution_result: Dict):
        """更新控制統計"""
        try:
            if execution_result.get("success", False):
                if decision.action in [ControlAction.FREQUENCY_HOP, ControlAction.EMERGENCY_SWITCH]:
                    self.control_statistics["successful_mitigations"] += 1
                    
                    # 更新平均 SINR 改善
                    improvement = execution_result.get("sinr_improvement_db", 0)
                    current_avg = self.control_statistics["average_sinr_improvement"]
                    count = self.control_statistics["successful_mitigations"]
                    self.control_statistics["average_sinr_improvement"] = (
                        current_avg * (count - 1) + improvement
                    ) / count

        except Exception as e:
            self.logger.error("更新控制統計失敗", error=str(e))

    async def _adaptive_learning(self, current_state: Dict, decision: Optional[ControlDecision]):
        """自適應學習"""
        try:
            if not decision:
                return

            # 簡單的參數自適應
            if decision.action == ControlAction.FREQUENCY_HOP:
                # 如果頻率跳變過於頻繁，提高閾值
                if self.hop_count_last_minute > 5:
                    self.interference_threshold_db -= 2  # 更嚴格的閾值
                else:
                    self.interference_threshold_db += 0.5  # 放鬆閾值
                    
                # 限制閾值範圍
                self.interference_threshold_db = max(-100, min(-70, self.interference_threshold_db))

            # 調整置信度閾值
            if decision.confidence > 0.8 and current_state.get("current_sinr_db", 0) > 15:
                self.confidence_threshold = max(0.6, self.confidence_threshold - 0.01)
            elif decision.confidence < 0.6:
                self.confidence_threshold = min(0.9, self.confidence_threshold + 0.01)

        except Exception as e:
            self.logger.error("自適應學習失敗", error=str(e))

    def _update_loop_latency(self, latency_ms: float):
        """更新控制循環延遲統計"""
        current_avg = self.control_statistics["control_loop_latency_ms"]
        count = self.control_statistics["total_decisions"]
        
        if count <= 1:
            self.control_statistics["control_loop_latency_ms"] = latency_ms
        else:
            self.control_statistics["control_loop_latency_ms"] = (
                current_avg * (count - 1) + latency_ms
            ) / count

    # === 公共 API 方法 ===

    async def get_controller_status(self) -> Dict[str, Any]:
        """獲取控制器狀態"""
        return {
            "controller_name": "閉環干擾控制器",
            "is_running": self.is_running,
            "control_enabled": self.control_enabled,
            "current_frequency_mhz": self.current_frequency,
            "current_sinr_db": self.current_sinr_db,
            "control_interval_ms": self.control_interval_ms,
            "interference_threshold_db": self.interference_threshold_db,
            "sinr_threshold_db": self.sinr_threshold_db,
            "max_hops_per_minute": self.max_hops_per_minute,
            "hop_count_last_minute": self.hop_count_last_minute,
            "confidence_threshold": self.confidence_threshold,
            "total_frequency_channels": len(self.frequency_channels),
            "statistics": self.control_statistics,
        }

    async def get_frequency_channel_status(self) -> Dict[str, Any]:
        """獲取頻率通道狀態"""
        channel_status = {}
        for freq, channel in self.frequency_channels.items():
            channel_status[freq] = {
                "frequency_mhz": freq,
                "state": channel.state.value,
                "interference_level_db": channel.interference_level_db,
                "average_sinr_db": channel.get_average_sinr(),
                "stability_score": channel.get_stability_score(),
                "switch_count": channel.switch_count,
                "occupation_time_sec": channel.occupation_time,
                "last_updated": channel.last_updated.isoformat(),
                "is_current": freq == self.current_frequency,
            }
        return channel_status

    async def get_decision_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """獲取決策歷史"""
        recent_decisions = self.decision_history[-limit:]
        return [
            {
                "decision_id": d.decision_id,
                "timestamp": d.timestamp.isoformat(),
                "current_frequency": d.current_frequency,
                "target_frequency": d.target_frequency,
                "action": d.action.value,
                "confidence": d.confidence,
                "reasoning": d.reasoning,
                "expected_improvement": d.expected_improvement,
                "execution_delay_ms": d.execution_delay_ms,
            }
            for d in recent_decisions
        ]

    async def manual_frequency_override(self, target_frequency: float, reason: str = "手動設置") -> Dict[str, Any]:
        """手動頻率覆蓋"""
        try:
            if target_frequency not in self.frequency_channels:
                return {"success": False, "error": f"無效頻率: {target_frequency}"}

            old_frequency = self.current_frequency
            
            # 創建手動決策
            manual_decision = ControlDecision(
                decision_id=f"manual_{uuid.uuid4().hex[:8]}",
                timestamp=datetime.utcnow(),
                current_frequency=old_frequency,
                target_frequency=target_frequency,
                action=ControlAction.FREQUENCY_HOP,
                confidence=1.0,
                reasoning=f"手動覆蓋: {reason}",
                expected_improvement=0.0,
                execution_delay_ms=50,
            )

            # 執行頻率切換
            result = await self._execute_frequency_hop(target_frequency)
            
            if result.get("success"):
                self.decision_history.append(manual_decision)
                self.logger.info(f"手動頻率覆蓋成功: {old_frequency} -> {target_frequency}")
            
            return result

        except Exception as e:
            self.logger.error("手動頻率覆蓋失敗", error=str(e))
            return {"success": False, "error": str(e)}

    async def update_control_parameters(self, **kwargs) -> Dict[str, Any]:
        """更新控制參數"""
        try:
            updated_params = []
            
            if "interference_threshold_db" in kwargs:
                self.interference_threshold_db = kwargs["interference_threshold_db"]
                updated_params.append("interference_threshold_db")
                
            if "sinr_threshold_db" in kwargs:
                self.sinr_threshold_db = kwargs["sinr_threshold_db"]
                updated_params.append("sinr_threshold_db")
                
            if "control_interval_ms" in kwargs:
                self.control_interval_ms = kwargs["control_interval_ms"]
                updated_params.append("control_interval_ms")
                
            if "max_hops_per_minute" in kwargs:
                self.max_hops_per_minute = kwargs["max_hops_per_minute"]
                updated_params.append("max_hops_per_minute")
                
            if "confidence_threshold" in kwargs:
                self.confidence_threshold = kwargs["confidence_threshold"]
                updated_params.append("confidence_threshold")

            self.logger.info(f"控制參數已更新: {updated_params}")
            
            return {
                "success": True,
                "updated_parameters": updated_params,
                "current_parameters": {
                    "interference_threshold_db": self.interference_threshold_db,
                    "sinr_threshold_db": self.sinr_threshold_db,
                    "control_interval_ms": self.control_interval_ms,
                    "max_hops_per_minute": self.max_hops_per_minute,
                    "confidence_threshold": self.confidence_threshold,
                }
            }

        except Exception as e:
            self.logger.error("更新控制參數失敗", error=str(e))
            return {"success": False, "error": str(e)}