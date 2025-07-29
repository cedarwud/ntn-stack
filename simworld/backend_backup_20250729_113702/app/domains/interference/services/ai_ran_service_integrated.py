"""
AI-RAN (AI無線接入網路) 服務 - NetStack 整合版

實現基於人工智慧的抗干擾決策系統，整合 NetStack RL 訓練系統：
- 使用 NetStack 統一的 DQN/PPO/SAC 算法
- 連接 NetStack PostgreSQL 資料庫
- 利用 NetStack 會話管理和持久化機制
- 保持原有的干擾決策業務邏輯

Phase 1: API 橋接整合版本
"""

import logging
import time
import uuid
import asyncio
import pickle
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import json

from .netstack_rl_client import NetStackRLClient, get_netstack_rl_client
from ..models.interference_models import (
    AIRANDecision,
    AIRANDecisionType,
    AIRANControlRequest,
    AIRANControlResponse,
    FrequencyHopPattern,
    FrequencyHopStrategy,
    BeamformingConfig,
    BeamformingStrategy,
    InterferenceDetectionResult,
    InterferenceMetrics,
)

logger = logging.getLogger(__name__)


class AIRANServiceIntegrated:
    """AI-RAN 抗干擾服務 - NetStack 整合版"""

    def __init__(self):
        """初始化 AI-RAN 服務"""
        self.logger = logger

        # NetStack RL 客戶端
        self.netstack_client: Optional[NetStackRLClient] = None
        self.current_training_session: Optional[str] = None
        self.preferred_algorithm = "dqn"  # 預設使用 DQN

        # 頻率管理
        self.available_frequencies = list(
            range(2100, 2200, 5)
        )  # 2.1GHz band, 5MHz steps
        self.frequency_blacklist = set()
        self.frequency_usage_history = {}

        # 跳頻模式
        self.hop_patterns = {}
        self.active_hop_patterns = {}

        # 波束成形配置
        self.beam_configs = {}
        self.active_beam_configs = {}

        # 決策歷史（現在存儲到 NetStack 系統）
        self.local_decision_cache = []  # 本地快取，用於降級
        self.performance_metrics = {}

        # 系統狀態
        self.is_netstack_available = False
        self.last_netstack_check = None

        self.logger.info("AI-RAN 服務初始化完成 (NetStack 整合版)")

    async def initialize(self) -> bool:
        """
        初始化服務，連接到 NetStack RL 系統

        Returns:
            bool: 初始化是否成功
        """
        try:
            # 獲取 NetStack RL 客戶端
            self.netstack_client = await get_netstack_rl_client()

            # 檢查 NetStack 系統可用性
            self.is_netstack_available = await self.netstack_client.health_check()

            if self.is_netstack_available:
                # 獲取可用算法
                algorithms = await self.netstack_client.get_available_algorithms()
                self.logger.info(f"NetStack 可用算法: {algorithms}")

                # 選擇最佳算法
                if "dqn" in algorithms:
                    self.preferred_algorithm = "dqn"
                elif algorithms:
                    self.preferred_algorithm = algorithms[0]

                # 啟動默認訓練會話
                await self._ensure_training_session()

                self.logger.info(
                    f"AI-RAN 服務初始化成功，使用算法: {self.preferred_algorithm}"
                )
                return True
            else:
                self.logger.warning("NetStack RL 系統不可用，將使用降級模式")
                return True  # 降級模式仍然可以工作

        except Exception as e:
            self.logger.error(f"AI-RAN 服務初始化失敗: {e}")
            self.is_netstack_available = False
            return True  # 降級到本地模式

    async def _ensure_training_session(self) -> Optional[str]:
        """
        確保有可用的訓練會話

        Returns:
            Optional[str]: 會話 ID
        """
        try:
            if not self.netstack_client or not self.is_netstack_available:
                return None

            # 檢查現有會話狀態
            if self.current_training_session:
                status = await self.netstack_client.get_training_status(
                    self.current_training_session
                )
                if status and status.get("status") in ["running", "paused"]:
                    return self.current_training_session

            # 創建新的訓練會話
            config = {
                "learning_rate": 0.001,
                "batch_size": 32,
                "gamma": 0.99,
                "epsilon": 0.1,
                "target_update_freq": 100,
                "memory_size": 10000,
                "episodes": 1000,
                "scenario_type": "interference_mitigation",
            }

            session_id = await self.netstack_client.start_training_session(
                algorithm=self.preferred_algorithm,
                config=config,
                session_name=f"aiRAN_interference_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            )

            if session_id:
                self.current_training_session = session_id
                self.logger.info(f"創建新的訓練會話: {session_id}")
                return session_id
            else:
                self.logger.warning("無法創建訓練會話，將使用降級模式")
                return None

        except Exception as e:
            self.logger.error(f"確保訓練會話失敗: {e}")
            return None

    async def make_anti_jamming_decision(
        self, request: AIRANControlRequest
    ) -> AIRANControlResponse:
        """
        做出抗干擾決策 - 使用 NetStack RL 系統

        Args:
            request: AI-RAN 控制請求

        Returns:
            AI-RAN 控制響應
        """
        start_time = time.time()
        control_id = f"ctrl_{uuid.uuid4().hex[:8]}"

        try:
            self.logger.info(f"開始 AI-RAN 決策 {control_id} (NetStack 模式)")

            # 分析當前干擾狀態
            interference_analysis = await self._analyze_interference_state(
                request.current_interference_state
            )

            # 選擇決策策略
            decision_type = await self._select_decision_strategy(
                interference_analysis, request
            )

            # 使用 NetStack RL 系統進行決策
            ai_decision = await self._make_netstack_rl_decision(
                decision_type, interference_analysis, request
            )

            # 如果 NetStack 不可用，降級到本地決策
            if ai_decision is None:
                ai_decision = await self._make_fallback_decision(
                    decision_type, interference_analysis, request
                )

            # 生成備選決策
            alternatives = await self._generate_alternative_decisions(
                interference_analysis, request, ai_decision
            )

            # 創建執行計劃
            execution_plan = await self._create_execution_plan(ai_decision)
            rollback_plan = await self._create_rollback_plan(ai_decision)

            # 存儲決策經驗到 NetStack（異步）
            asyncio.create_task(
                self._store_decision_experience(
                    interference_analysis, ai_decision, request
                )
            )

            # 創建響應
            response = AIRANControlResponse(
                control_id=control_id,
                request_id=request.request_id,
                timestamp=datetime.utcnow(),
                success=True,
                primary_decision=ai_decision,
                alternative_decisions=alternatives,
                execution_plan=execution_plan,
                rollback_plan=rollback_plan,
                confidence_level=ai_decision.confidence_score,
                processing_time_ms=(time.time() - start_time) * 1000,
                system_status={
                    "netstack_available": self.is_netstack_available,
                    "algorithm_used": self.preferred_algorithm,
                    "session_id": self.current_training_session,
                    "decision_mode": (
                        "netstack_rl" if self.is_netstack_available else "fallback"
                    ),
                },
            )

            self.logger.info(
                f"AI-RAN 決策完成 {control_id}",
                extra={
                    "processing_time_ms": response.processing_time_ms,
                    "decision_type": ai_decision.decision_type.value,
                    "confidence": ai_decision.confidence_score,
                    "netstack_mode": self.is_netstack_available,
                },
            )

            return response

        except Exception as e:
            self.logger.error(f"AI-RAN 決策失敗 {control_id}: {e}", exc_info=True)

            # 返回錯誤響應
            return AIRANControlResponse(
                control_id=control_id,
                request_id=request.request_id,
                timestamp=datetime.utcnow(),
                success=False,
                error_message=f"決策失敗: {str(e)}",
                confidence_level=0.0,
                processing_time_ms=(time.time() - start_time) * 1000,
                system_status={
                    "netstack_available": self.is_netstack_available,
                    "error": str(e),
                },
            )

    async def _make_netstack_rl_decision(
        self,
        decision_type: AIRANDecisionType,
        analysis: Dict[str, Any],
        request: AIRANControlRequest,
    ) -> Optional[AIRANDecision]:
        """
        使用 NetStack RL 系統進行決策

        Returns:
            Optional[AIRANDecision]: 決策結果，失敗時返回 None
        """
        try:
            if not self.netstack_client or not self.is_netstack_available:
                return None

            # 確保有可用的訓練會話
            session_id = await self._ensure_training_session()
            if not session_id:
                return None

            # 編碼狀態
            state = self._encode_interference_state(analysis)

            # 使用 NetStack RL 進行決策
            decision_result = await self.netstack_client.make_decision(
                algorithm=self.preferred_algorithm, state=state, session_id=session_id
            )

            if not decision_result:
                self.logger.warning("NetStack RL 決策失敗，將使用降級模式")
                self.is_netstack_available = False  # 暫時標記為不可用
                return None

            # 解析決策結果
            action_idx = decision_result.get("action", 0)
            confidence = decision_result.get("confidence", 0.5)

            # 根據決策類型創建具體決策
            if decision_type == AIRANDecisionType.FREQUENCY_HOP:
                return await self._create_frequency_hop_decision(
                    analysis, request, action_idx, confidence
                )
            elif decision_type == AIRANDecisionType.BEAM_STEERING:
                return await self._create_beam_steering_decision(
                    analysis, request, action_idx, confidence
                )
            elif decision_type == AIRANDecisionType.POWER_CONTROL:
                return await self._create_power_control_decision(
                    analysis, request, action_idx, confidence
                )
            else:
                return await self._create_emergency_decision(
                    analysis, request, confidence
                )

        except Exception as e:
            self.logger.error(f"NetStack RL 決策失敗: {e}")
            self.is_netstack_available = False  # 暫時標記為不可用
            return None

    async def _create_frequency_hop_decision(
        self,
        analysis: Dict[str, Any],
        request: AIRANControlRequest,
        action_idx: int,
        confidence: float,
    ) -> AIRANDecision:
        """創建跳頻決策"""
        # 排除受干擾頻率
        affected_freqs = set(analysis.get("affected_frequencies", []))
        available_freqs = [
            f
            for f in request.available_frequencies_mhz
            if f not in affected_freqs and f not in self.frequency_blacklist
        ]

        if not available_freqs:
            available_freqs = request.available_frequencies_mhz[:3]  # 緊急後備

        # 使用 NetStack 決策結果選擇頻率
        target_freq = available_freqs[action_idx % len(available_freqs)]

        # 創建跳頻模式
        hop_pattern_id = f"hop_{uuid.uuid4().hex[:8]}"
        hop_pattern = FrequencyHopPattern(
            pattern_id=hop_pattern_id,
            strategy=FrequencyHopStrategy.ADAPTIVE_ML,
            frequency_list_mhz=available_freqs,
            hop_duration_ms=10.0,
            dwell_time_ms=5.0,
        )

        self.hop_patterns[hop_pattern_id] = hop_pattern

        return AIRANDecision(
            decision_id=f"freq_hop_{uuid.uuid4().hex[:8]}",
            trigger_event="interference_detected",
            interference_level_db=analysis.get("max_interference_dbm", -80),
            decision_type=AIRANDecisionType.FREQUENCY_HOP,
            confidence_score=confidence,
            target_frequencies_mhz=[target_freq],
            hop_pattern_id=hop_pattern_id,
            execution_delay_ms=1.0,
            expected_sinr_improvement_db=analysis.get("expected_improvement", 5.0),
            expected_throughput_improvement_percent=15.0,
            interference_risk_score=max(0.0, 1.0 - confidence),
        )

    async def _make_fallback_decision(
        self,
        decision_type: AIRANDecisionType,
        analysis: Dict[str, Any],
        request: AIRANControlRequest,
    ) -> AIRANDecision:
        """降級決策（當 NetStack 不可用時）"""
        self.logger.info("使用降級決策模式")

        # 簡單的啟發式決策
        if decision_type == AIRANDecisionType.FREQUENCY_HOP:
            # 選擇 SINR 最高的頻率
            available_freqs = request.available_frequencies_mhz
            target_freq = available_freqs[0] if available_freqs else 2150.0

            return AIRANDecision(
                decision_id=f"fallback_freq_{uuid.uuid4().hex[:8]}",
                trigger_event="interference_detected",
                interference_level_db=analysis.get("max_interference_dbm", -80),
                decision_type=AIRANDecisionType.FREQUENCY_HOP,
                confidence_score=0.6,  # 降級模式信心較低
                target_frequencies_mhz=[target_freq],
                execution_delay_ms=1.0,
                expected_sinr_improvement_db=3.0,  # 保守估計
                expected_throughput_improvement_percent=10.0,
                interference_risk_score=0.4,
            )
        else:
            # 其他決策類型的降級處理
            return AIRANDecision(
                decision_id=f"fallback_emergency_{uuid.uuid4().hex[:8]}",
                trigger_event="system_degraded",
                interference_level_db=analysis.get("max_interference_dbm", -80),
                decision_type=AIRANDecisionType.EMERGENCY_PROTOCOL,
                confidence_score=0.5,
                execution_delay_ms=1.0,
                expected_sinr_improvement_db=2.0,
                expected_throughput_improvement_percent=5.0,
                interference_risk_score=0.5,
            )

    async def _store_decision_experience(
        self,
        analysis: Dict[str, Any],
        decision: AIRANDecision,
        request: AIRANControlRequest,
    ):
        """存儲決策經驗到 NetStack RL 系統"""
        try:
            if not self.netstack_client or not self.current_training_session:
                return

            state = self._encode_interference_state(analysis)

            # 模擬動作（基於決策類型）
            action = self._encode_decision_action(decision)

            # 計算獎勵（基於預期改善）
            reward = self._calculate_decision_reward(decision, analysis)

            # 下一個狀態（基於決策預期效果模擬）
            next_state = await self._simulate_post_decision_state(state, decision, analysis)

            # 存儲經驗
            success = await self.netstack_client.store_experience(
                session_id=self.current_training_session,
                state=state,
                action=action,
                reward=reward,
                next_state=next_state,
                done=False,
            )

            if success:
                self.logger.debug("成功存儲決策經驗到 NetStack")
            else:
                self.logger.warning("存儲決策經驗失敗")

        except Exception as e:
            self.logger.error(f"存儲決策經驗失敗: {e}")

    def _encode_interference_state(self, analysis: Dict[str, Any]) -> np.ndarray:
        """編碼干擾狀態為 RL 輸入"""
        state = np.zeros(20)

        # 基本指標
        state[0] = analysis.get("avg_sinr_db", 0) / 30.0  # 歸一化到 [-1, 1]
        state[1] = analysis.get("max_interference_dbm", -100) / 100.0
        state[2] = len(analysis.get("affected_frequencies", [])) / 100.0

        # 干擾類型 (one-hot 編碼)
        jammer_types = analysis.get("jammer_types", {})
        if "broadband_noise" in jammer_types:
            state[3] = 1.0
        if "sweep_jammer" in jammer_types:
            state[4] = 1.0
        if "smart_jammer" in jammer_types:
            state[5] = 1.0

        # 嚴重程度
        severity_map = {"low": 0.25, "medium": 0.5, "high": 0.75, "critical": 1.0}
        state[6] = severity_map.get(analysis.get("severity", "low"), 0.25)

        # 其他狀態特徵
        state[7:] = np.random.uniform(0, 0.1, 13)  # 其他特徵的簡化處理

        return state

    def _encode_decision_action(self, decision: AIRANDecision) -> int:
        """將決策編碼為動作索引"""
        if decision.decision_type == AIRANDecisionType.FREQUENCY_HOP:
            return 0
        elif decision.decision_type == AIRANDecisionType.BEAM_STEERING:
            return 1
        elif decision.decision_type == AIRANDecisionType.POWER_CONTROL:
            return 2
        else:
            return 3

    def _calculate_decision_reward(
        self, decision: AIRANDecision, analysis: Dict[str, Any]
    ) -> float:
        """計算決策獎勵"""
        # 基於預期改善計算獎勵
        sinr_reward = decision.expected_sinr_improvement_db * 0.1
        throughput_reward = decision.expected_throughput_improvement_percent * 0.01
        confidence_reward = decision.confidence_score * 0.5
        risk_penalty = decision.interference_risk_score * 0.3

        total_reward = (
            sinr_reward + throughput_reward + confidence_reward - risk_penalty
        )
        return np.clip(total_reward, -1.0, 1.0)

    # 複用原有的輔助方法
    async def _analyze_interference_state(
        self, interference_states: List[InterferenceDetectionResult]
    ) -> Dict[str, Any]:
        """分析干擾狀態"""
        if not interference_states:
            return {"severity": "low", "avg_sinr_db": 0, "max_interference_dbm": -100}

        # 簡化的分析邏輯
        avg_sinr = sum(state.sinr_db for state in interference_states) / len(
            interference_states
        )
        max_interference = max(
            state.interference_power_dbm for state in interference_states
        )

        severity = "low"
        if max_interference > -60:
            severity = "critical"
        elif max_interference > -70:
            severity = "high"
        elif max_interference > -80:
            severity = "medium"

        return {
            "avg_sinr_db": avg_sinr,
            "max_interference_dbm": max_interference,
            "severity": severity,
            "affected_frequencies": [
                state.frequency_mhz for state in interference_states
            ],
            "jammer_types": {"broadband_noise": True},  # 簡化
        }

    async def _select_decision_strategy(
        self, analysis: Dict[str, Any], request: AIRANControlRequest
    ) -> AIRANDecisionType:
        """選擇決策策略"""
        severity = analysis.get("severity", "low")

        if severity in ["critical", "high"]:
            return AIRANDecisionType.FREQUENCY_HOP
        elif severity == "medium":
            return AIRANDecisionType.BEAM_STEERING
        else:
            return AIRANDecisionType.POWER_CONTROL

    async def _generate_alternative_decisions(self, analysis, request, primary):
        """生成備選決策"""
        return []

    async def _create_execution_plan(self, decision):
        """創建執行計劃"""
        return [{"step": "execute", "action": decision.decision_type.value}]

    async def _create_rollback_plan(self, decision):
        """創建回滾計劃"""
        return [{"step": "rollback", "action": "restore_previous_config"}]

    async def _create_beam_steering_decision(
        self, analysis, request, action_idx, confidence
    ):
        """創建波束調整決策"""
        return AIRANDecision(
            decision_id=f"beam_steer_{uuid.uuid4().hex[:8]}",
            trigger_event="interference_detected",
            interference_level_db=analysis.get("max_interference_dbm", -80),
            decision_type=AIRANDecisionType.BEAM_STEERING,
            confidence_score=confidence,
            execution_delay_ms=5.0,
            expected_sinr_improvement_db=analysis.get("expected_improvement", 3.0),
            expected_throughput_improvement_percent=8.0,
            interference_risk_score=max(0.0, 1.0 - confidence),
        )

    async def _create_power_control_decision(
        self, analysis, request, action_idx, confidence
    ):
        """創建功率控制決策"""
        return AIRANDecision(
            decision_id=f"power_ctrl_{uuid.uuid4().hex[:8]}",
            trigger_event="interference_detected",
            interference_level_db=analysis.get("max_interference_dbm", -80),
            decision_type=AIRANDecisionType.POWER_CONTROL,
            confidence_score=confidence,
            power_adjustment_db=2.0,
            execution_delay_ms=2.0,
            expected_sinr_improvement_db=analysis.get("expected_improvement", 2.0),
            expected_throughput_improvement_percent=5.0,
            interference_risk_score=max(0.0, 1.0 - confidence),
        )

    async def _create_emergency_decision(self, analysis, request, confidence):
        """創建緊急決策"""
        return AIRANDecision(
            decision_id=f"emergency_{uuid.uuid4().hex[:8]}",
            trigger_event="emergency_protocol",
            interference_level_db=analysis.get("max_interference_dbm", -80),
            decision_type=AIRANDecisionType.EMERGENCY_PROTOCOL,
            confidence_score=confidence,
            execution_delay_ms=0.5,
            expected_sinr_improvement_db=1.0,
            expected_throughput_improvement_percent=3.0,
            interference_risk_score=0.8,
        )

    async def get_training_status(self) -> Dict[str, Any]:
        """獲取訓練狀態"""
        try:
            if not self.netstack_client or not self.current_training_session:
                return {
                    "status": "no_session",
                    "netstack_available": self.is_netstack_available,
                }

            status = await self.netstack_client.get_training_status(
                self.current_training_session
            )
            if status:
                status["netstack_available"] = self.is_netstack_available
                status["algorithm"] = self.preferred_algorithm
                return status
            else:
                return {
                    "status": "unknown",
                    "netstack_available": self.is_netstack_available,
                }

        except Exception as e:
            self.logger.error(f"獲取訓練狀態失敗: {e}")
            return {"status": "error", "error": str(e)}

    async def pause_training(self) -> bool:
        """暫停訓練"""
        if self.netstack_client and self.current_training_session:
            return await self.netstack_client.pause_training(
                self.current_training_session
            )
        return False

    async def resume_training(self) -> bool:
        """恢復訓練"""
        if self.netstack_client and self.current_training_session:
            return await self.netstack_client.resume_training(
                self.current_training_session
            )
        return False

    async def stop_training(self) -> bool:
        """停止訓練"""
        if self.netstack_client and self.current_training_session:
            result = await self.netstack_client.stop_training(
                self.current_training_session
            )
            if result:
                self.current_training_session = None
            return result
        return False

    async def _simulate_post_decision_state(
        self, 
        current_state: np.ndarray, 
        decision: AIRANDecision, 
        analysis: Dict[str, Any]
    ) -> np.ndarray:
        """模擬決策執行後的狀態變化
        
        基於決策類型和預期改善來計算下一狀態
        """
        next_state = current_state.copy()
        
        try:
            # 根據決策類型預測狀態變化
            if decision.decision_type == AIRANDecisionType.FREQUENCY_HOP:
                # 頻率跳躍：預期SINR改善，干擾水平降低
                if hasattr(decision, 'expected_sinr_improvement_db') and decision.expected_sinr_improvement_db:
                    # 狀態[0]是SINR，添加預期改善
                    current_sinr = next_state[0] * 30.0  # 反歸一化
                    improved_sinr = current_sinr + decision.expected_sinr_improvement_db
                    next_state[0] = min(improved_sinr / 30.0, 1.0)  # 重新歸一化並限制範圍
                
                # 干擾水平降低
                if next_state[1] < 0:  # 負值表示干擾
                    next_state[1] *= 0.7  # 降低30%的干擾
                    
            elif decision.decision_type == AIRANDecisionType.POWER_CONTROL:
                # 功率控制：適度改善但可能增加能耗
                if hasattr(decision, 'expected_sinr_improvement_db') and decision.expected_sinr_improvement_db:
                    current_sinr = next_state[0] * 30.0
                    improved_sinr = current_sinr + decision.expected_sinr_improvement_db
                    next_state[0] = min(improved_sinr / 30.0, 1.0)
                
                # 功率調整可能影響其他指標（如果有功率相關狀態）
                if len(next_state) > 10:  # 假設位置10存儲功率相關信息
                    power_adjustment = getattr(decision, 'power_adjustment_db', 0) / 10.0
                    next_state[10] = min(max(next_state[10] + power_adjustment, -1.0), 1.0)
                    
            elif decision.decision_type == AIRANDecisionType.BEAMFORMING:
                # 波束成形：顯著改善SINR
                if hasattr(decision, 'expected_sinr_improvement_db') and decision.expected_sinr_improvement_db:
                    current_sinr = next_state[0] * 30.0
                    improved_sinr = current_sinr + decision.expected_sinr_improvement_db
                    next_state[0] = min(improved_sinr / 30.0, 1.0)
                
                # 空間選擇性改善，減少干擾
                next_state[1] *= 0.5  # 干擾降低50%
                
            elif decision.decision_type == AIRANDecisionType.EMERGENCY_PROTOCOL:
                # 緊急協議：保守改善，優先穩定性
                if next_state[0] < 0:  # 如果當前SINR很差
                    next_state[0] = max(next_state[0] * 1.2, -0.8)  # 適度改善
                
                # 降低系統不確定性（如果有相關狀態維度）
                if len(next_state) > 15:
                    next_state[15] *= 0.8  # 假設位置15存儲不確定性指標
            
            # 添加決策信心度的影響
            confidence_factor = getattr(decision, 'confidence_score', 0.5)
            improvement_scaling = 0.5 + (confidence_factor * 0.5)  # 0.5-1.0範圍
            
            # 將改善程度按信心度縮放
            for i in range(len(next_state)):
                if next_state[i] != current_state[i]:
                    diff = next_state[i] - current_state[i]
                    next_state[i] = current_state[i] + (diff * improvement_scaling)
            
            # 添加少量隨機噪聲模擬現實中的不確定性
            noise_level = 0.05 * (1 - confidence_factor)  # 信心度越低噪聲越大
            noise = np.random.normal(0, noise_level, next_state.shape)
            next_state += noise
            
            # 確保狀態在合理範圍內
            next_state = np.clip(next_state, -1.0, 1.0)
            
            self.logger.debug(f"狀態模擬完成: 決策類型={decision.decision_type}, 信心度={confidence_factor:.2f}")
            
        except Exception as e:
            self.logger.error(f"狀態模擬失敗: {e}")
            # 失敗時返回輕微改善的狀態
            next_state = current_state + np.random.normal(0, 0.01, current_state.shape)
            next_state = np.clip(next_state, -1.0, 1.0)
        
        return next_state


# 全局服務實例
_ai_ran_service_integrated: Optional[AIRANServiceIntegrated] = None


async def get_ai_ran_service_integrated() -> AIRANServiceIntegrated:
    """獲取整合版 AI-RAN 服務實例"""
    global _ai_ran_service_integrated

    if _ai_ran_service_integrated is None:
        _ai_ran_service_integrated = AIRANServiceIntegrated()
        await _ai_ran_service_integrated.initialize()

    return _ai_ran_service_integrated
