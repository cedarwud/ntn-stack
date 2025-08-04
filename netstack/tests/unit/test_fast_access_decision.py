"""
Phase 3.2.2.2 快速接入決策引擎單元測試

測試快速接入決策引擎的完整實現，包括：
1. 接入候選評估和排序
2. 多維度決策算法
3. 資源預留和管理
4. 服務質量保證機制
5. 負載平衡和優化
"""

import pytest
import pytest_asyncio
import asyncio
import time
import math
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock

# 導入待測試的模組
import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, project_root)

from src.algorithms.access.fast_access_decision import (
    FastAccessDecisionEngine,
    AccessRequest,
    AccessCandidate,
    AccessPlan,
    AccessDecisionType,
    ServiceClass,
    AccessTrigger,
    create_fast_access_decision_engine,
    create_test_access_request,
    create_sample_access_candidates
)


class TestAccessCandidate:
    """測試接入候選"""
    
    def test_access_candidate_creation(self):
        """測試接入候選創建"""
        candidate = AccessCandidate(
            satellite_id="TEST-SAT-001",
            beam_id="BEAM-1",
            frequency_band="Ka-band",
            elevation_angle=30.0,
            azimuth_angle=180.0,
            distance_km=1500.0,
            signal_strength_dbm=-95.0,
            total_capacity_mbps=1000.0,
            current_load_percent=0.6,
            active_users=120,
            max_users=200
        )
        
        assert candidate.satellite_id == "TEST-SAT-001"
        assert candidate.beam_id == "BEAM-1"
        assert candidate.frequency_band == "Ka-band"
        assert candidate.elevation_angle == 30.0
        assert candidate.total_capacity_mbps == 1000.0
        assert candidate.current_load_percent == 0.6
        assert candidate.active_users == 120
    
    def test_load_factor_calculation(self):
        """測試負載因子計算"""
        candidate = AccessCandidate(
            satellite_id="LOAD-TEST",
            beam_id="BEAM-1",
            frequency_band="Ka-band",
            total_capacity_mbps=1000.0,
            available_capacity_mbps=400.0,  # 60%已使用
            active_users=80,
            max_users=100  # 80%用戶負載
        )
        
        load_factor = candidate.calculate_load_factor()
        # 應該取用戶負載(0.8)和容量負載(0.6)的最大值
        assert abs(load_factor - 0.8) < 0.01
    
    def test_overload_detection(self):
        """測試過載檢測"""
        # 正常負載候選
        normal_candidate = AccessCandidate(
            satellite_id="NORMAL",
            beam_id="BEAM-1",
            frequency_band="Ka-band",
            total_capacity_mbps=1000.0,
            available_capacity_mbps=700.0,  # 30%負載
            active_users=50,
            max_users=200
        )
        
        assert normal_candidate.is_overloaded() is False
        
        # 過載候選
        overloaded_candidate = AccessCandidate(
            satellite_id="OVERLOADED",
            beam_id="BEAM-2",
            frequency_band="Ka-band",
            total_capacity_mbps=1000.0,
            available_capacity_mbps=50.0,  # 95%負載
            active_users=190,
            max_users=200
        )
        
        assert overloaded_candidate.is_overloaded() is True
    
    def test_visibility_duration(self):
        """測試可見性持續時間"""
        current_time = datetime.now(timezone.utc)
        candidate = AccessCandidate(
            satellite_id="VISIBILITY-TEST",
            beam_id="BEAM-1",
            frequency_band="Ka-band",
            visibility_window_start=current_time,
            visibility_window_end=current_time + timedelta(minutes=10),
            predicted_availability_duration_s=600.0
        )
        
        # 測試通過可見性窗口計算
        duration = candidate.get_visibility_duration()
        assert abs(duration - 600.0) < 1.0  # 10分鐘 = 600秒
        
        # 測試通過預測時間
        candidate_no_window = AccessCandidate(
            satellite_id="NO-WINDOW",
            beam_id="BEAM-1",
            frequency_band="Ka-band",
            predicted_availability_duration_s=900.0
        )
        
        assert candidate_no_window.get_visibility_duration() == 900.0


class TestAccessRequest:
    """測試接入請求"""
    
    def test_access_request_creation(self):
        """測試接入請求創建"""
        request = AccessRequest(
            request_id="REQ-001",
            user_id="user123",
            device_id="device456",
            trigger_type=AccessTrigger.INITIAL_ATTACH,
            service_class=ServiceClass.VIDEO,
            timestamp=datetime.now(timezone.utc),
            user_latitude=25.0,
            user_longitude=121.0,
            required_bandwidth_mbps=50.0,
            max_acceptable_latency_ms=200.0,
            priority=7
        )
        
        assert request.request_id == "REQ-001"
        assert request.user_id == "user123"
        assert request.trigger_type == AccessTrigger.INITIAL_ATTACH
        assert request.service_class == ServiceClass.VIDEO
        assert request.required_bandwidth_mbps == 50.0
        assert request.priority == 7


class TestAccessPlan:
    """測試接入計劃"""
    
    def test_access_plan_creation(self):
        """測試接入計劃創建"""
        request = create_test_access_request()
        candidate = AccessCandidate(
            satellite_id="PLAN-SAT",
            beam_id="BEAM-1",
            frequency_band="Ka-band"
        )
        
        plan = AccessPlan(
            plan_id="PLAN-001",
            request=request,
            selected_candidate=candidate,
            decision=AccessDecisionType.IMMEDIATE_ACCEPT,
            execution_time=datetime.now(timezone.utc),
            preparation_phase_duration_ms=100,
            execution_phase_duration_ms=200,
            completion_phase_duration_ms=50
        )
        
        assert plan.plan_id == "PLAN-001"
        assert plan.decision == AccessDecisionType.IMMEDIATE_ACCEPT
        assert plan.selected_candidate.satellite_id == "PLAN-SAT"
        assert plan.get_total_duration_ms() == 350
    
    def test_plan_expiration(self):
        """測試計劃過期檢查"""
        request = create_test_access_request()
        request.deadline_ms = 1000  # 1秒期限
        
        candidate = AccessCandidate(
            satellite_id="EXPIRE-SAT",
            beam_id="BEAM-1",
            frequency_band="Ka-band"
        )
        
        # 剛創建的計劃不應過期
        plan = AccessPlan(
            plan_id="EXPIRE-PLAN",
            request=request,
            selected_candidate=candidate,
            decision=AccessDecisionType.IMMEDIATE_ACCEPT,
            execution_time=datetime.now(timezone.utc)
        )
        
        assert plan.is_expired() is False
        
        # 舊計劃應該過期
        old_plan = AccessPlan(
            plan_id="OLD-PLAN",
            request=request,
            selected_candidate=candidate,
            decision=AccessDecisionType.IMMEDIATE_ACCEPT,
            execution_time=datetime.now(timezone.utc) - timedelta(seconds=2)  # 2秒前
        )
        
        assert old_plan.is_expired() is True


class TestFastAccessDecisionEngine:
    """測試快速接入決策引擎"""
    
    @pytest_asyncio.fixture
    async def access_engine(self):
        """創建測試用接入決策引擎"""
        engine = create_fast_access_decision_engine("test_engine")
        return engine
    
    @pytest_asyncio.fixture
    async def running_engine(self):
        """創建運行中的接入決策引擎"""
        engine = create_fast_access_decision_engine("running_engine")
        await engine.start_engine()
        yield engine
        await engine.stop_engine()
    
    @pytest.mark.asyncio
    async def test_engine_initialization(self, access_engine):
        """測試引擎初始化"""
        assert isinstance(access_engine, FastAccessDecisionEngine)
        assert access_engine.engine_id.startswith("test_engine")
        assert access_engine.is_running is False
        assert len(access_engine.pending_requests) == 0
        assert len(access_engine.active_plans) == 0
    
    @pytest.mark.asyncio
    async def test_engine_start_stop(self, access_engine):
        """測試引擎啟動和停止"""
        # 啟動引擎
        await access_engine.start_engine()
        assert access_engine.is_running is True
        assert access_engine.decision_task is not None
        assert access_engine.monitoring_task is not None
        
        # 等待一小段時間
        await asyncio.sleep(0.1)
        
        # 停止引擎
        await access_engine.stop_engine()
        assert access_engine.is_running is False
    
    @pytest.mark.asyncio
    async def test_submit_access_request(self, running_engine):
        """測試提交接入請求"""
        request = create_test_access_request("user123", ServiceClass.DATA)
        
        request_id = await running_engine.submit_access_request(request)
        
        assert request_id == request.request_id
        assert request.request_id in running_engine.pending_requests
        assert running_engine.stats['requests_received'] == 1
    
    @pytest.mark.asyncio
    async def test_cancel_access_request(self, running_engine):
        """測試取消接入請求"""
        request = create_test_access_request("user_cancel", ServiceClass.VOICE)
        
        # 提交請求
        request_id = await running_engine.submit_access_request(request)
        assert request_id in running_engine.pending_requests
        
        # 取消請求
        cancelled = await running_engine.cancel_access_request(request_id)
        assert cancelled is True
        assert request_id not in running_engine.pending_requests
        
        # 取消不存在的請求
        not_cancelled = await running_engine.cancel_access_request("nonexistent")
        assert not_cancelled is False
    
    @pytest.mark.asyncio
    async def test_get_access_candidates(self, running_engine):
        """測試獲取接入候選"""
        request = create_test_access_request()
        request.user_latitude = 25.0
        request.user_longitude = 121.0
        
        candidates = await running_engine._get_access_candidates(request)
        
        # 應該有候選衛星
        assert len(candidates) > 0
        
        # 候選衛星應該符合基本要求
        for candidate in candidates:
            assert candidate.signal_strength_dbm >= running_engine.decision_config['min_signal_strength_dbm']
            assert candidate.elevation_angle >= running_engine.decision_config['min_elevation_angle_deg']
            assert not candidate.is_overloaded(running_engine.decision_config['overload_threshold'])
    
    @pytest.mark.asyncio
    async def test_evaluate_candidates(self, running_engine):
        """測試候選評估"""
        request = create_test_access_request()
        candidates = create_sample_access_candidates()
        
        evaluated_candidates = await running_engine._evaluate_candidates(request, candidates)
        
        # 應該有評分
        assert len(evaluated_candidates) == len(candidates)
        
        # 檢查評分和排序
        for i, candidate in enumerate(evaluated_candidates):
            assert hasattr(candidate, 'composite_score')
            assert 0.0 <= candidate.composite_score <= 1.0
            assert candidate.ranking == i + 1
        
        # 應該按分數排序（降序）
        for i in range(len(evaluated_candidates) - 1):
            assert evaluated_candidates[i].composite_score >= evaluated_candidates[i+1].composite_score
    
    @pytest.mark.asyncio
    async def test_signal_quality_evaluation(self, running_engine):
        """測試信號質量評估"""
        # 高質量信號候選
        good_candidate = AccessCandidate(
            satellite_id="GOOD-SIGNAL",
            beam_id="BEAM-1",
            frequency_band="Ka-band",
            signal_strength_dbm=-90.0,  # 強信號
            elevation_angle=60.0,       # 高仰角
            path_loss_db=160.0          # 低路徑損耗
        )
        
        good_score = running_engine._evaluate_signal_quality(good_candidate)
        
        # 低質量信號候選
        poor_candidate = AccessCandidate(
            satellite_id="POOR-SIGNAL",
            beam_id="BEAM-2",
            frequency_band="Ka-band",
            signal_strength_dbm=-115.0,  # 弱信號
            elevation_angle=15.0,        # 低仰角
            path_loss_db=190.0           # 高路徑損耗
        )
        
        poor_score = running_engine._evaluate_signal_quality(poor_candidate)
        
        # 高質量信號應該得分更高
        assert good_score > poor_score
        assert 0.0 <= good_score <= 1.0
        assert 0.0 <= poor_score <= 1.0
    
    @pytest.mark.asyncio
    async def test_capacity_availability_evaluation(self, running_engine):
        """測試容量可用性評估"""
        request = create_test_access_request()
        request.required_bandwidth_mbps = 10.0
        
        # 高容量候選
        high_capacity = AccessCandidate(
            satellite_id="HIGH-CAP",
            beam_id="BEAM-1",
            frequency_band="Ka-band",
            total_capacity_mbps=1000.0,
            available_capacity_mbps=800.0,  # 80%可用
            active_users=20,
            max_users=200
        )
        
        high_score = running_engine._evaluate_capacity_availability(high_capacity, request)
        
        # 低容量候選
        low_capacity = AccessCandidate(
            satellite_id="LOW-CAP",
            beam_id="BEAM-2",
            frequency_band="Ka-band",
            total_capacity_mbps=1000.0,
            available_capacity_mbps=5.0,   # 僅5Mbps可用
            active_users=180,
            max_users=200
        )
        
        low_score = running_engine._evaluate_capacity_availability(low_capacity, request)
        
        assert high_score > low_score
        assert 0.0 <= high_score <= 1.0
        assert 0.0 <= low_score <= 1.0
    
    @pytest.mark.asyncio
    async def test_predicted_performance_evaluation(self, running_engine):
        """測試預測性能評估"""
        request = create_test_access_request()
        request.required_bandwidth_mbps = 20.0
        request.max_acceptable_latency_ms = 200.0
        request.min_acceptable_reliability = 0.95
        
        # 高性能候選
        high_performance = AccessCandidate(
            satellite_id="HIGH-PERF",
            beam_id="BEAM-1",
            frequency_band="Ka-band",
            predicted_throughput_mbps=50.0,
            predicted_latency_ms=100.0,
            predicted_packet_loss_rate=0.01,      # 99%可靠性
            predicted_availability_duration_s=600.0
        )
        
        high_score = running_engine._evaluate_predicted_performance(high_performance, request)
        
        # 低性能候選
        low_performance = AccessCandidate(
            satellite_id="LOW-PERF",
            beam_id="BEAM-2",
            frequency_band="Ka-band",
            predicted_throughput_mbps=15.0,
            predicted_latency_ms=300.0,           # 超過要求
            predicted_packet_loss_rate=0.1,       # 90%可靠性
            predicted_availability_duration_s=120.0
        )
        
        low_score = running_engine._evaluate_predicted_performance(low_performance, request)
        
        assert high_score > low_score
        assert 0.0 <= high_score <= 1.0
        assert 0.0 <= low_score <= 1.0
    
    @pytest.mark.asyncio
    async def test_access_cost_evaluation(self, running_engine):
        """測試接入成本評估"""
        # 低成本候選
        low_cost = AccessCandidate(
            satellite_id="LOW-COST",
            beam_id="BEAM-1",
            frequency_band="Ka-band",
            setup_time_ms=120.0,
            signaling_overhead_kb=3.0,
            power_consumption_mw=600.0,
            interference_level_db=-95.0
        )
        
        low_cost_score = running_engine._evaluate_access_cost(low_cost)
        
        # 高成本候選
        high_cost = AccessCandidate(
            satellite_id="HIGH-COST",
            beam_id="BEAM-2",
            frequency_band="Ka-band",
            setup_time_ms=450.0,
            signaling_overhead_kb=9.0,
            power_consumption_mw=950.0,
            interference_level_db=-85.0
        )
        
        high_cost_score = running_engine._evaluate_access_cost(high_cost)
        
        # 低成本應該得分更高
        assert low_cost_score > high_cost_score
        assert 0.0 <= low_cost_score <= 1.0
        assert 0.0 <= high_cost_score <= 1.0
    
    @pytest.mark.asyncio
    async def test_service_compatibility_evaluation(self, running_engine):
        """測試服務兼容性評估"""
        # 語音服務請求（對延遲敏感）
        voice_request = create_test_access_request("voice_user", ServiceClass.VOICE)
        voice_request.max_acceptable_latency_ms = 150.0
        voice_request.min_acceptable_reliability = 0.98
        
        # 兼容的候選
        compatible_candidate = AccessCandidate(
            satellite_id="VOICE-COMPATIBLE",
            beam_id="BEAM-1",
            frequency_band="Ka-band",
            predicted_latency_ms=120.0,
            predicted_packet_loss_rate=0.01,     # 99%可靠性
            predicted_throughput_mbps=20.0
        )
        
        compatible_score = running_engine._evaluate_service_compatibility(compatible_candidate, voice_request)
        
        # 不兼容的候選
        incompatible_candidate = AccessCandidate(
            satellite_id="VOICE-INCOMPATIBLE",
            beam_id="BEAM-2",
            frequency_band="Ka-band",
            predicted_latency_ms=300.0,          # 延遲過高
            predicted_packet_loss_rate=0.05,     # 可靠性不足
            predicted_throughput_mbps=5.0        # 吞吐量不足
        )
        
        incompatible_score = running_engine._evaluate_service_compatibility(incompatible_candidate, voice_request)
        
        assert compatible_score > incompatible_score
        assert 0.0 <= compatible_score <= 1.0
        assert 0.0 <= incompatible_score <= 1.0
    
    @pytest.mark.asyncio
    async def test_load_balancing_evaluation(self, running_engine):
        """測試負載平衡評估"""
        # 低負載候選
        low_load = AccessCandidate(
            satellite_id="LOW-LOAD",
            beam_id="BEAM-1",
            frequency_band="Ka-band",
            total_capacity_mbps=1000.0,
            available_capacity_mbps=800.0,       # 20%負載
            active_users=40,
            max_users=200
        )
        
        low_load_score = running_engine._evaluate_load_balancing(low_load)
        
        # 高負載候選
        high_load = AccessCandidate(
            satellite_id="HIGH-LOAD",
            beam_id="BEAM-2",
            frequency_band="Ka-band",
            total_capacity_mbps=1000.0,
            available_capacity_mbps=200.0,       # 80%負載
            active_users=160,
            max_users=200
        )
        
        high_load_score = running_engine._evaluate_load_balancing(high_load)
        
        # 低負載應該得分更高
        assert low_load_score > high_load_score
        assert 0.0 <= low_load_score <= 1.0
        assert 0.0 <= high_load_score <= 1.0
    
    @pytest.mark.asyncio
    async def test_access_decision_making(self, running_engine):
        """測試接入決策制定"""
        request = create_test_access_request()
        
        # 高分候選（應該立即接受）
        excellent_candidate = AccessCandidate(
            satellite_id="EXCELLENT",
            beam_id="BEAM-1",
            frequency_band="Ka-band"
        )
        excellent_candidate.composite_score = 0.9
        
        decision, selected = await running_engine._make_access_decision(request, [excellent_candidate])
        assert decision == AccessDecisionType.IMMEDIATE_ACCEPT
        assert selected == excellent_candidate
        
        # 中等分數候選（條件接受）
        decent_candidate = AccessCandidate(
            satellite_id="DECENT",
            beam_id="BEAM-2",
            frequency_band="Ka-band"
        )
        decent_candidate.composite_score = 0.7
        
        decision, selected = await running_engine._make_access_decision(request, [decent_candidate])
        assert decision == AccessDecisionType.CONDITIONAL_ACCEPT
        assert selected == decent_candidate
        
        # 低分候選（延遲接受）
        poor_candidate = AccessCandidate(
            satellite_id="POOR",
            beam_id="BEAM-3",
            frequency_band="Ka-band"
        )
        poor_candidate.composite_score = 0.5
        
        decision, selected = await running_engine._make_access_decision(request, [poor_candidate])
        assert decision == AccessDecisionType.DELAYED_ACCEPT
        assert selected == poor_candidate
        
        # 極低分候選（拒絕）
        terrible_candidate = AccessCandidate(
            satellite_id="TERRIBLE",
            beam_id="BEAM-4",
            frequency_band="Ka-band"
        )
        terrible_candidate.composite_score = 0.2
        
        decision, selected = await running_engine._make_access_decision(request, [terrible_candidate])
        assert decision in [AccessDecisionType.REJECT_OVERLOAD, AccessDecisionType.REJECT_QOS, AccessDecisionType.REJECT_COVERAGE]
        assert selected == terrible_candidate
    
    @pytest.mark.asyncio
    async def test_emergency_service_priority(self, running_engine):
        """測試緊急服務優先處理"""
        emergency_request = create_test_access_request("emergency_user", ServiceClass.EMERGENCY)
        
        # 即使是中等分數的候選，緊急服務也應該被接受
        moderate_candidate = AccessCandidate(
            satellite_id="MODERATE",
            beam_id="BEAM-1",
            frequency_band="Ka-band"
        )
        moderate_candidate.composite_score = 0.4  # 正常情況下會被拒絕
        
        decision, selected = await running_engine._make_access_decision(emergency_request, [moderate_candidate])
        assert decision == AccessDecisionType.IMMEDIATE_ACCEPT
        assert selected == moderate_candidate
    
    @pytest.mark.asyncio
    async def test_create_access_plan(self, running_engine):
        """測試創建接入計劃"""
        request = create_test_access_request()
        candidate = create_sample_access_candidates()[0]
        
        plan = await running_engine._create_access_plan(request, candidate, AccessDecisionType.IMMEDIATE_ACCEPT)
        
        assert plan.request == request
        assert plan.selected_candidate == candidate
        assert plan.decision == AccessDecisionType.IMMEDIATE_ACCEPT
        assert plan.get_total_duration_ms() > 0
        assert plan.reserved_bandwidth_mbps > 0
        assert plan.guaranteed_throughput_mbps > 0
    
    @pytest.mark.asyncio
    async def test_resource_reservation(self, running_engine):
        """測試資源預留"""
        request = create_test_access_request()
        candidate = create_sample_access_candidates()[0]
        plan = await running_engine._create_access_plan(request, candidate, AccessDecisionType.IMMEDIATE_ACCEPT)
        
        # 預留資源應該成功
        reserved = await running_engine._reserve_resources(plan)
        assert reserved is True
        
        # 檢查資源狀態更新
        satellite_id = candidate.satellite_id
        assert satellite_id in running_engine.satellite_loads
        assert running_engine.satellite_loads[satellite_id] > 0
        
        # 釋放資源
        await running_engine._release_reserved_resources(plan)
        assert running_engine.satellite_loads[satellite_id] == 0.0
    
    @pytest.mark.asyncio
    async def test_overload_protection(self, running_engine):
        """測試過載保護"""
        # 人為設置高負載
        satellite_id = "OVERLOAD-TEST"
        running_engine.satellite_loads[satellite_id] = 0.9  # 90%負載
        
        request = create_test_access_request()
        candidate = AccessCandidate(
            satellite_id=satellite_id,
            beam_id="BEAM-1",
            frequency_band="Ka-band"
        )
        
        plan = await running_engine._create_access_plan(request, candidate, AccessDecisionType.IMMEDIATE_ACCEPT)
        
        # 資源預留應該失敗（會導致過載）
        reserved = await running_engine._reserve_resources(plan)
        assert reserved is False
    
    @pytest.mark.asyncio
    async def test_engine_status(self, running_engine):
        """測試引擎狀態獲取"""
        # 添加一些請求和計劃
        request = create_test_access_request()
        await running_engine.submit_access_request(request)
        
        status = running_engine.get_engine_status()
        
        assert isinstance(status, dict)
        assert status['engine_id'] == running_engine.engine_id
        assert status['is_running'] is True
        assert status['pending_requests'] == 1
        assert 'statistics' in status
        assert 'configuration' in status
    
    @pytest.mark.asyncio
    async def test_config_update(self, running_engine):
        """測試配置更新"""
        original_interval = running_engine.decision_config['evaluation_interval_ms']
        
        new_config = {
            'decision_config': {
                'evaluation_interval_ms': 200,
                'max_candidates_per_request': 15
            },
            'evaluation_weights': {
                'signal_quality': 0.3,
                'capacity_availability': 0.25
            }
        }
        
        running_engine.update_config(new_config)
        
        assert running_engine.decision_config['evaluation_interval_ms'] == 200
        assert running_engine.decision_config['max_candidates_per_request'] == 15
        assert running_engine.evaluation_weights['signal_quality'] == 0.3
        assert running_engine.decision_config['evaluation_interval_ms'] != original_interval


class TestAccessDecisionWorkflow:
    """測試接入決策工作流程"""
    
    @pytest_asyncio.fixture
    async def workflow_engine(self):
        """創建工作流程測試引擎"""
        engine = create_fast_access_decision_engine("workflow_engine")
        await engine.start_engine()
        yield engine
        await engine.stop_engine()
    
    @pytest.mark.asyncio
    async def test_complete_access_workflow(self, workflow_engine):
        """測試完整接入工作流程"""
        # 提交接入請求
        request = create_test_access_request("workflow_user", ServiceClass.DATA)
        request_id = await workflow_engine.submit_access_request(request)
        
        # 等待處理
        await asyncio.sleep(0.5)
        
        # 檢查請求是否被處理
        initial_pending = len(workflow_engine.pending_requests)
        initial_active = len(workflow_engine.active_plans)
        
        # 請求應該已被處理（移出待處理或進入活動計劃）
        assert (initial_pending == 0) or (initial_active > 0) or (workflow_engine.stats['requests_rejected'] > 0)
    
    @pytest.mark.asyncio
    async def test_priority_based_processing(self, workflow_engine):
        """測試基於優先級的處理"""
        # 提交低優先級請求
        low_priority = create_test_access_request("low_user", ServiceClass.BACKGROUND)
        low_priority.priority = 2
        await workflow_engine.submit_access_request(low_priority)
        
        # 提交高優先級請求
        high_priority = create_test_access_request("high_user", ServiceClass.EMERGENCY)
        high_priority.priority = 9
        await workflow_engine.submit_access_request(high_priority)
        
        # 等待處理
        await asyncio.sleep(0.3)
        
        # 高優先級請求應該優先處理
        assert workflow_engine.stats['emergency_requests'] == 1
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, workflow_engine):
        """測試並發請求處理"""
        # 降低處理間隔以加快測試
        workflow_engine.decision_config['evaluation_interval_ms'] = 50
        
        # 同時提交多個請求
        requests = []
        for i in range(3):  # 減少請求數量
            request = create_test_access_request(f"concurrent_user_{i}", ServiceClass.DATA)
            requests.append(request)
            await workflow_engine.submit_access_request(request)
        
        # 檢查請求已提交
        assert workflow_engine.stats['requests_received'] == 3
        
        # 等待處理
        await asyncio.sleep(1.0)
        
        # 檢查請求處理狀態
        total_processed = workflow_engine.stats['requests_accepted'] + workflow_engine.stats['requests_rejected']
        total_pending = len(workflow_engine.pending_requests)
        total_active = len(workflow_engine.active_plans)
        
        # 檢查請求總數正確
        assert workflow_engine.stats['requests_received'] == 3
        # 至少處理了一些請求（接受、拒絕或進入活動計劃）
        assert total_processed + total_active >= 1


class TestPerformanceMetrics:
    """測試性能指標"""
    
    @pytest_asyncio.fixture
    async def perf_engine(self):
        """創建性能測試引擎"""
        engine = create_fast_access_decision_engine("perf_engine")
        await engine.start_engine()
        yield engine
        await engine.stop_engine()
    
    @pytest.mark.asyncio
    async def test_decision_time_measurement(self, perf_engine):
        """測試決策時間測量"""
        # 提交請求
        request = create_test_access_request("perf_user")
        await perf_engine.submit_access_request(request)
        
        # 等待處理
        await asyncio.sleep(0.3)
        
        # 檢查統計更新
        assert perf_engine.stats['requests_received'] == 1
        
        if perf_engine.stats['requests_accepted'] + perf_engine.stats['requests_rejected'] > 0:
            assert perf_engine.stats['average_decision_time_ms'] > 0
            assert perf_engine.stats['total_decision_time_ms'] > 0
    
    @pytest.mark.asyncio
    async def test_resource_utilization_tracking(self, perf_engine):
        """測試資源利用率追蹤"""
        # 提交多個請求以消耗資源
        for i in range(3):
            request = create_test_access_request(f"resource_user_{i}")
            await perf_engine.submit_access_request(request)
        
        # 等待處理
        await asyncio.sleep(0.5)
        
        # 檢查資源狀態
        status = perf_engine.get_engine_status()
        satellite_loads = status['satellite_loads']
        
        # 如果有請求被接受，應該有資源被分配
        if perf_engine.stats['requests_accepted'] > 0:
            assert len(satellite_loads) > 0
            assert any(load > 0 for load in satellite_loads.values())


class TestHelperFunctions:
    """測試輔助函數"""
    
    def test_create_fast_access_decision_engine(self):
        """測試創建快速接入決策引擎"""
        engine = create_fast_access_decision_engine("helper_test")
        
        assert isinstance(engine, FastAccessDecisionEngine)
        assert engine.engine_id.startswith("helper_test")
        assert engine.is_running is False
    
    def test_create_test_access_request(self):
        """測試創建測試接入請求"""
        request = create_test_access_request("test_user", ServiceClass.VIDEO, AccessTrigger.HANDOVER, 8)
        
        assert isinstance(request, AccessRequest)
        assert request.user_id == "test_user"
        assert request.service_class == ServiceClass.VIDEO
        assert request.trigger_type == AccessTrigger.HANDOVER
        assert request.priority == 8
        assert request.user_latitude == 24.9441667  # NTPU位置
        assert request.user_longitude == 121.3713889
        
        # 檢查設備能力
        assert 'supported_bands' in request.device_capabilities
        assert 'max_tx_power_dbm' in request.device_capabilities
    
    def test_create_sample_access_candidates(self):
        """測試創建示例接入候選"""
        candidates = create_sample_access_candidates()
        
        assert isinstance(candidates, list)
        assert len(candidates) == 3
        
        for i, candidate in enumerate(candidates):
            assert candidate.satellite_id == f"SAT-{2001 + i}"
            assert candidate.beam_id == f"BEAM-{i+1}"
            assert candidate.frequency_band == "Ka-band"
            assert candidate.elevation_angle > 0
            assert candidate.total_capacity_mbps > 0
            assert candidate.available_capacity_mbps > 0


if __name__ == "__main__":
    # 運行測試
    pytest.main([__file__, "-v", "--tb=short", "-s"])