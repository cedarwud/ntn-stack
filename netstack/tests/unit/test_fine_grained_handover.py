"""
Phase 3.2.1.2 精細化切換決策引擎單元測試

測試精細化切換決策引擎的完整實現，包括：
1. 微秒級切換時序控制
2. 多目標優化決策算法
3. 動態負載平衡機制
4. 用戶服務質量保證
5. 資源利用率優化
"""

import pytest
import pytest_asyncio
import asyncio
import time
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock

# 導入待測試的模組
import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, project_root)

from src.algorithms.handover.fine_grained_decision import (
    FineGrainedHandoverDecisionEngine,
    SatelliteCandidate,
    HandoverRequest,
    HandoverPlan,
    HandoverTrigger,
    HandoverDecision,
    OptimizationObjective,
    create_fine_grained_handover_engine,
    create_test_handover_request
)


class TestSatelliteCandidate:
    """測試候選衛星"""
    
    def test_satellite_candidate_creation(self):
        """測試候選衛星創建"""
        candidate = SatelliteCandidate(
            satellite_id="TEST-SAT-001",
            signal_strength_dbm=-85.0,
            elevation_angle=45.0,
            azimuth_angle=180.0,
            distance_km=1500.0,
            velocity_kmh=27000.0,
            doppler_shift_hz=15000.0,
            available_bandwidth_mbps=100.0,
            current_load_percent=60.0,
            user_count=500,
            beam_capacity_percent=70.0,
            predicted_throughput_mbps=50.0,
            predicted_latency_ms=80.0,
            predicted_reliability=0.95,
            predicted_availability_duration_s=1200.0,
            handover_delay_ms=30.0,
            signaling_overhead_kb=10.0,
            resource_preparation_ms=20.0
        )
        
        assert candidate.satellite_id == "TEST-SAT-001"
        assert candidate.signal_strength_dbm == -85.0
        assert candidate.elevation_angle == 45.0
        assert candidate.available_bandwidth_mbps == 100.0
        assert candidate.predicted_throughput_mbps == 50.0
    
    def test_candidate_overall_score_calculation(self):
        """測試候選衛星綜合評分計算"""
        # 高質量候選衛星
        good_candidate = SatelliteCandidate(
            satellite_id="GOOD-SAT",
            signal_strength_dbm=-70.0,  # 強信號
            elevation_angle=80.0,       # 高仰角
            azimuth_angle=180.0,
            distance_km=1200.0,
            velocity_kmh=27000.0,
            doppler_shift_hz=10000.0,
            available_bandwidth_mbps=150.0,
            current_load_percent=30.0,  # 低負載
            user_count=200,
            beam_capacity_percent=40.0,
            predicted_throughput_mbps=80.0,  # 高吞吐量
            predicted_latency_ms=50.0,       # 低延遲
            predicted_reliability=0.98,      # 高可靠性
            predicted_availability_duration_s=1800.0,
            handover_delay_ms=25.0,          # 低切換延遲
            signaling_overhead_kb=8.0,
            resource_preparation_ms=15.0
        )
        
        weights = {
            'signal_strength': 0.3, 'elevation': 0.2, 'load': 0.15,
            'throughput': 0.15, 'latency': 0.1, 'reliability': 0.05,
            'availability': 0.03, 'handover_cost': 0.02
        }
        
        score = good_candidate.calculate_overall_score(weights)
        assert 0.8 <= score <= 1.0  # 高質量候選衛星應該得高分
        
        # 低質量候選衛星
        bad_candidate = SatelliteCandidate(
            satellite_id="BAD-SAT",
            signal_strength_dbm=-110.0,  # 弱信號
            elevation_angle=10.0,        # 低仰角
            azimuth_angle=180.0,
            distance_km=2000.0,
            velocity_kmh=28000.0,
            doppler_shift_hz=40000.0,
            available_bandwidth_mbps=20.0,
            current_load_percent=90.0,   # 高負載
            user_count=1500,
            beam_capacity_percent=95.0,
            predicted_throughput_mbps=5.0,   # 低吞吐量
            predicted_latency_ms=500.0,      # 高延遲
            predicted_reliability=0.80,      # 低可靠性
            predicted_availability_duration_s=300.0,
            handover_delay_ms=100.0,         # 高切換延遲
            signaling_overhead_kb=25.0,
            resource_preparation_ms=80.0
        )
        
        score = bad_candidate.calculate_overall_score(weights)
        assert 0.0 <= score <= 0.4  # 低質量候選衛星應該得低分


class TestHandoverRequest:
    """測試切換請求"""
    
    def test_handover_request_creation(self):
        """測試切換請求創建"""
        request = HandoverRequest(
            request_id="test_req_001",
            user_id="user_123",
            current_satellite_id="SAT-CURRENT",
            trigger_type=HandoverTrigger.SIGNAL_STRENGTH,
            priority=7,
            timestamp=datetime.now(timezone.utc),
            service_type="video",
            required_bandwidth_mbps=25.0,
            max_acceptable_latency_ms=200.0,
            min_acceptable_reliability=0.99,
            current_signal_strength_dbm=-90.0,
            current_throughput_mbps=15.0,
            current_latency_ms=180.0
        )
        
        assert request.request_id == "test_req_001"
        assert request.user_id == "user_123"
        assert request.trigger_type == HandoverTrigger.SIGNAL_STRENGTH
        assert request.priority == 7
        assert request.service_type == "video"
        assert request.required_bandwidth_mbps == 25.0
    
    def test_emergency_priority_request(self):
        """測試緊急優先級請求"""
        emergency_request = create_test_handover_request(
            "emergency_user", "SAT-FAIL", 
            HandoverTrigger.EMERGENCY, 
            priority=10
        )
        
        assert emergency_request.priority == 10
        assert emergency_request.trigger_type == HandoverTrigger.EMERGENCY


class TestHandoverPlan:
    """測試切換計劃"""
    
    def test_handover_plan_creation(self):
        """測試切換計劃創建"""
        request = create_test_handover_request("test_user", "SAT-OLD")
        target = SatelliteCandidate(
            satellite_id="SAT-NEW",
            signal_strength_dbm=-80.0,
            elevation_angle=60.0,
            azimuth_angle=90.0,
            distance_km=1400.0,
            velocity_kmh=27500.0,
            doppler_shift_hz=12000.0,
            available_bandwidth_mbps=120.0,
            current_load_percent=45.0,
            user_count=300,
            beam_capacity_percent=55.0,
            predicted_throughput_mbps=60.0,
            predicted_latency_ms=70.0,
            predicted_reliability=0.96,
            predicted_availability_duration_s=1500.0,
            handover_delay_ms=35.0,
            signaling_overhead_kb=12.0,
            resource_preparation_ms=25.0
        )
        
        plan = HandoverPlan(
            plan_id="test_plan_001",
            request=request,
            target_satellite=target,
            decision=HandoverDecision.EXECUTE_SCHEDULED,
            execution_time=datetime.now(timezone.utc) + timedelta(seconds=2),
            preparation_phase_duration_ms=25,
            execution_phase_duration_ms=35,
            completion_phase_duration_ms=10,
            optimization_objectives=[OptimizationObjective.MINIMIZE_INTERRUPTION],
            expected_improvement={'signal_strength_db': 15.0},
            reserved_resources={'bandwidth_mbps': 10.0}
        )
        
        assert plan.plan_id == "test_plan_001"
        assert plan.target_satellite.satellite_id == "SAT-NEW"
        assert plan.decision == HandoverDecision.EXECUTE_SCHEDULED
        assert plan.get_total_duration_ms() == 70  # 25+35+10


class TestFineGrainedHandoverDecisionEngine:
    """測試精細化切換決策引擎"""
    
    @pytest_asyncio.fixture
    async def handover_engine(self):
        """創建測試用切換決策引擎"""
        engine = create_fine_grained_handover_engine("test_engine")
        return engine
    
    @pytest.mark.asyncio
    async def test_engine_initialization(self, handover_engine):
        """測試引擎初始化"""
        assert isinstance(handover_engine, FineGrainedHandoverDecisionEngine)
        assert handover_engine.engine_id == "test_engine"
        assert handover_engine.is_running is False
        assert len(handover_engine.pending_requests) == 0
        assert len(handover_engine.active_plans) == 0
    
    @pytest.mark.asyncio
    async def test_engine_start_stop(self, handover_engine):
        """測試引擎啟動和停止"""
        # 啟動引擎
        await handover_engine.start_engine()
        assert handover_engine.is_running is True
        assert handover_engine.decision_task is not None
        
        # 等待一小段時間
        await asyncio.sleep(0.1)
        
        # 停止引擎
        await handover_engine.stop_engine()
        assert handover_engine.is_running is False
    
    @pytest.mark.asyncio
    async def test_submit_handover_request(self, handover_engine):
        """測試提交切換請求"""
        request = create_test_handover_request("test_user", "SAT-001")
        
        request_id = await handover_engine.submit_handover_request(request)
        
        assert request_id == request.request_id
        assert request_id in handover_engine.pending_requests
        assert handover_engine.pending_requests[request_id] == request
    
    @pytest.mark.asyncio
    async def test_emergency_request_processing(self, handover_engine):
        """測試緊急請求處理"""
        # 創建緊急請求
        emergency_request = create_test_handover_request(
            "emergency_user", "SAT-FAIL", 
            HandoverTrigger.EMERGENCY, 
            priority=9
        )
        
        # 模擬候選衛星生成
        original_method = handover_engine._generate_mock_candidates
        async def mock_generate_candidates(current_sat):
            return [SatelliteCandidate(
                satellite_id="EMERGENCY-SAT",
                signal_strength_dbm=-75.0,
                elevation_angle=70.0,
                azimuth_angle=45.0,
                distance_km=1300.0,
                velocity_kmh=27000.0,
                doppler_shift_hz=8000.0,
                available_bandwidth_mbps=100.0,
                current_load_percent=40.0,
                user_count=250,
                beam_capacity_percent=50.0,
                predicted_throughput_mbps=70.0,
                predicted_latency_ms=60.0,
                predicted_reliability=0.97,
                predicted_availability_duration_s=1800.0,
                handover_delay_ms=20.0,
                signaling_overhead_kb=8.0,
                resource_preparation_ms=15.0
            )]
        
        handover_engine._generate_mock_candidates = mock_generate_candidates
        
        # 提交緊急請求
        await handover_engine.submit_handover_request(emergency_request)
        
        # 緊急請求應該被立即處理
        await asyncio.sleep(0.1)  # 等待處理完成
        
        assert handover_engine.stats['emergency_handovers'] >= 1
        
        # 恢復原方法
        handover_engine._generate_mock_candidates = original_method
    
    @pytest.mark.asyncio
    async def test_handover_decision_making(self, handover_engine):
        """測試切換決策制定"""
        request = create_test_handover_request("decision_user", "SAT-OLD")
        
        # 制定決策
        plan = await handover_engine._make_handover_decision(request)
        
        # 應該能夠制定出切換計劃
        if plan:  # 可能因為候選衛星評分過低而返回None
            assert isinstance(plan, HandoverPlan)
            assert plan.request == request
            assert plan.target_satellite is not None
            assert plan.decision in [HandoverDecision.EXECUTE_IMMEDIATELY, 
                                   HandoverDecision.EXECUTE_SCHEDULED]
    
    @pytest.mark.asyncio
    async def test_candidate_evaluation(self, handover_engine):
        """測試候選衛星評估"""
        request = create_test_handover_request("eval_user", "SAT-CURRENT")
        
        # 創建測試候選衛星
        candidate = SatelliteCandidate(
            satellite_id="TEST-CANDIDATE",
            signal_strength_dbm=-80.0,
            elevation_angle=50.0,
            azimuth_angle=120.0,
            distance_km=1500.0,
            velocity_kmh=27200.0,
            doppler_shift_hz=10000.0,
            available_bandwidth_mbps=80.0,
            current_load_percent=50.0,
            user_count=400,
            beam_capacity_percent=60.0,
            predicted_throughput_mbps=50.0,
            predicted_latency_ms=100.0,
            predicted_reliability=0.95,
            predicted_availability_duration_s=1200.0,
            handover_delay_ms=40.0,
            signaling_overhead_kb=15.0,
            resource_preparation_ms=30.0
        )
        
        weights = handover_engine.optimization_weights
        evaluated_candidate, score = await handover_engine._evaluate_candidate(candidate, request, weights)
        
        assert evaluated_candidate == candidate
        assert 0.0 <= score <= 1.0
        assert isinstance(score, float)
    
    @pytest.mark.asyncio
    async def test_handover_plan_execution(self, handover_engine):
        """測試切換計劃執行"""
        request = create_test_handover_request("exec_user", "SAT-EXEC")
        target = SatelliteCandidate(
            satellite_id="SAT-TARGET",
            signal_strength_dbm=-75.0,
            elevation_angle=65.0,
            azimuth_angle=200.0,
            distance_km=1300.0,
            velocity_kmh=27100.0,
            doppler_shift_hz=5000.0,
            available_bandwidth_mbps=90.0,
            current_load_percent=35.0,
            user_count=280,
            beam_capacity_percent=45.0,
            predicted_throughput_mbps=65.0,
            predicted_latency_ms=75.0,
            predicted_reliability=0.97,
            predicted_availability_duration_s=1600.0,
            handover_delay_ms=30.0,
            signaling_overhead_kb=10.0,
            resource_preparation_ms=20.0
        )
        
        plan = HandoverPlan(
            plan_id="exec_test_plan",
            request=request,
            target_satellite=target,
            decision=HandoverDecision.EXECUTE_IMMEDIATELY,
            execution_time=datetime.now(timezone.utc),
            preparation_phase_duration_ms=20,
            execution_phase_duration_ms=30,
            completion_phase_duration_ms=10,
            optimization_objectives=[OptimizationObjective.MINIMIZE_INTERRUPTION],
            expected_improvement={'signal_strength_db': 20.0},
            reserved_resources={'bandwidth_mbps': 10.0}
        )
        
        # 執行切換計劃
        await handover_engine._execute_handover_plan(plan)
        
        # 檢查統計信息更新
        assert handover_engine.stats['handovers_executed'] >= 1
        assert len(handover_engine.completed_handovers) >= 1
    
    @pytest.mark.asyncio
    async def test_request_cancellation(self, handover_engine):
        """測試切換請求取消"""
        request = create_test_handover_request("cancel_user", "SAT-CANCEL")
        
        # 提交請求
        request_id = await handover_engine.submit_handover_request(request)
        assert request_id in handover_engine.pending_requests
        
        # 取消請求
        cancelled = await handover_engine.cancel_handover_request(request_id)
        assert cancelled is True
        assert request_id not in handover_engine.pending_requests
    
    @pytest.mark.asyncio
    async def test_config_update(self, handover_engine):
        """測試配置更新"""
        original_delay = handover_engine.decision_config['max_handover_delay_ms']
        
        new_config = {
            'decision_config': {'max_handover_delay_ms': 100},
            'optimization_weights': {'signal_strength': 0.4}
        }
        
        handover_engine.update_config(new_config)
        
        assert handover_engine.decision_config['max_handover_delay_ms'] == 100
        assert handover_engine.optimization_weights['signal_strength'] == 0.4
        assert handover_engine.decision_config['max_handover_delay_ms'] != original_delay
    
    @pytest.mark.asyncio
    async def test_engine_status_retrieval(self, handover_engine):
        """測試引擎狀態獲取"""
        status = handover_engine.get_engine_status()
        
        assert isinstance(status, dict)
        assert status['engine_id'] == "test_engine"
        assert 'is_running' in status
        assert 'pending_requests' in status
        assert 'active_plans' in status
        assert 'statistics' in status
        assert 'configuration' in status
    
    @pytest.mark.asyncio
    async def test_service_type_optimization(self, handover_engine):
        """測試不同服務類型的優化"""
        # 語音服務請求
        voice_request = HandoverRequest(
            request_id="voice_req",
            user_id="voice_user",
            current_satellite_id="SAT-VOICE",
            trigger_type=HandoverTrigger.SERVICE_QUALITY,
            priority=6,
            timestamp=datetime.now(timezone.utc),
            service_type="voice",
            required_bandwidth_mbps=1.0,
            max_acceptable_latency_ms=150.0,
            min_acceptable_reliability=0.99
        )
        
        # 檢查語音服務的權重配置
        voice_weights = handover_engine.service_weights['voice']
        assert voice_weights['latency'] > handover_engine.optimization_weights['latency']
        assert voice_weights['reliability'] > handover_engine.optimization_weights['reliability']
        
        # 視頻服務請求
        video_request = HandoverRequest(
            request_id="video_req",
            user_id="video_user",
            current_satellite_id="SAT-VIDEO",
            trigger_type=HandoverTrigger.LOAD_BALANCING,
            priority=5,
            timestamp=datetime.now(timezone.utc),
            service_type="video",
            required_bandwidth_mbps=20.0,
            max_acceptable_latency_ms=300.0,
            min_acceptable_reliability=0.95
        )
        
        # 檢查視頻服務的權重配置
        video_weights = handover_engine.service_weights['video']
        assert video_weights['throughput'] > handover_engine.optimization_weights['throughput']


class TestDecisionEngineIntegration:
    """決策引擎整合測試"""
    
    @pytest_asyncio.fixture
    async def running_engine(self):
        """創建運行中的決策引擎"""
        engine = create_fine_grained_handover_engine("integration_engine")
        await engine.start_engine()
        yield engine
        await engine.stop_engine()
    
    @pytest.mark.asyncio
    async def test_full_handover_workflow(self, running_engine):
        """測試完整的切換工作流程"""
        # 1. 提交多個切換請求
        requests = []
        for i in range(3):
            request = create_test_handover_request(f"workflow_user_{i}", f"SAT-{i:03d}")
            request.priority = 5 + i  # 不同優先級
            requests.append(request)
            await running_engine.submit_handover_request(request)
        
        # 2. 等待處理
        await asyncio.sleep(0.5)
        
        # 3. 檢查處理結果
        assert running_engine.stats['decisions_made'] >= 3
        assert len(running_engine.pending_requests) == 0  # 所有請求都應該被處理
    
    @pytest.mark.asyncio
    async def test_concurrent_handovers(self, running_engine):
        """測試並發切換處理"""
        # 同時提交多個高優先級請求
        tasks = []
        for i in range(5):
            request = create_test_handover_request(f"concurrent_user_{i}", f"SAT-CONCURRENT-{i}")
            request.priority = 8  # 高優先級
            task = running_engine.submit_handover_request(request)
            tasks.append(task)
        
        # 並發提交
        await asyncio.gather(*tasks)
        
        # 等待處理
        await asyncio.sleep(0.3)
        
        # 檢查並發限制
        max_concurrent = running_engine.decision_config['max_concurrent_handovers']
        assert len(running_engine.active_plans) <= max_concurrent
    
    @pytest.mark.asyncio
    async def test_load_balancing_scenario(self, running_engine):
        """測試負載平衡場景"""
        # 模擬負載平衡觸發的切換
        load_balance_request = create_test_handover_request(
            "load_balance_user", "SAT-OVERLOADED",
            HandoverTrigger.LOAD_BALANCING, 
            priority=6
        )
        
        await running_engine.submit_handover_request(load_balance_request)
        
        # 等待處理
        await asyncio.sleep(0.2)
        
        # 檢查決策制定
        assert running_engine.stats['decisions_made'] >= 1


class TestPerformanceMetrics:
    """性能指標測試"""
    
    @pytest_asyncio.fixture
    async def perf_engine(self):
        """創建性能測試用引擎"""
        engine = create_fine_grained_handover_engine("perf_engine")
        return engine
    
    @pytest.mark.asyncio
    async def test_decision_making_performance(self, perf_engine):
        """測試決策制定性能"""
        request = create_test_handover_request("perf_user", "SAT-PERF")
        
        start_time = time.time()
        plan = await perf_engine._make_handover_decision(request)
        decision_time = (time.time() - start_time) * 1000  # ms
        
        # 決策制定應該在50ms內完成
        assert decision_time < 50.0
    
    @pytest.mark.asyncio
    async def test_candidate_evaluation_performance(self, perf_engine):
        """測試候選衛星評估性能"""
        request = create_test_handover_request("eval_perf_user", "SAT-EVAL")
        
        # 創建多個候選衛星
        candidates = []
        for i in range(10):
            candidate = SatelliteCandidate(
                satellite_id=f"PERF-SAT-{i}",
                signal_strength_dbm=-80.0 - i,
                elevation_angle=45.0 + i * 3,
                azimuth_angle=i * 36,
                distance_km=1500.0 + i * 100,
                velocity_kmh=27000.0 + i * 100,
                doppler_shift_hz=10000.0 + i * 1000,
                available_bandwidth_mbps=80.0 + i * 5,
                current_load_percent=40.0 + i * 3,
                user_count=300 + i * 20,
                beam_capacity_percent=50.0 + i * 2,
                predicted_throughput_mbps=50.0 + i * 3,
                predicted_latency_ms=80.0 + i * 5,
                predicted_reliability=0.95 - i * 0.01,
                predicted_availability_duration_s=1200.0 + i * 60,
                handover_delay_ms=30.0 + i * 2,
                signaling_overhead_kb=10.0 + i,
                resource_preparation_ms=20.0 + i * 2
            )
            candidates.append(candidate)
        
        weights = perf_engine.optimization_weights
        
        start_time = time.time()
        
        # 並行評估所有候選衛星
        evaluation_tasks = [
            perf_engine._evaluate_candidate(candidate, request, weights)
            for candidate in candidates
        ]
        results = await asyncio.gather(*evaluation_tasks)
        
        eval_time = (time.time() - start_time) * 1000  # ms
        
        # 10個候選衛星的評估應該在30ms內完成
        assert eval_time < 30.0
        assert len(results) == 10
    
    @pytest.mark.asyncio
    async def test_handover_execution_performance(self, perf_engine):
        """測試切換執行性能"""
        request = create_test_handover_request("exec_perf_user", "SAT-EXEC")
        target = SatelliteCandidate(
            satellite_id="PERF-TARGET",
            signal_strength_dbm=-70.0,
            elevation_angle=60.0,
            azimuth_angle=150.0,
            distance_km=1200.0,
            velocity_kmh=27000.0,
            doppler_shift_hz=8000.0,
            available_bandwidth_mbps=100.0,
            current_load_percent=30.0,
            user_count=200,
            beam_capacity_percent=40.0,
            predicted_throughput_mbps=70.0,
            predicted_latency_ms=60.0,
            predicted_reliability=0.98,
            predicted_availability_duration_s=1800.0,
            handover_delay_ms=25.0,
            signaling_overhead_kb=8.0,
            resource_preparation_ms=15.0
        )
        
        plan = HandoverPlan(
            plan_id="perf_exec_plan",
            request=request,
            target_satellite=target,
            decision=HandoverDecision.EXECUTE_IMMEDIATELY,
            execution_time=datetime.now(timezone.utc),
            preparation_phase_duration_ms=15,
            execution_phase_duration_ms=25,
            completion_phase_duration_ms=10,
            optimization_objectives=[OptimizationObjective.MINIMIZE_INTERRUPTION],
            expected_improvement={'signal_strength_db': 25.0},
            reserved_resources={'bandwidth_mbps': 10.0}
        )
        
        start_time = time.time()
        await perf_engine._execute_handover_plan(plan)
        execution_time = (time.time() - start_time) * 1000  # ms
        
        # 切換執行時間應該接近計劃的總時間（50ms + 一些開銷）
        expected_time = plan.get_total_duration_ms()
        assert execution_time < expected_time + 20  # 允許20ms誤差


class TestHelperFunctions:
    """測試輔助函數"""
    
    def test_create_fine_grained_handover_engine(self):
        """測試創建精細化切換決策引擎"""
        engine = create_fine_grained_handover_engine("helper_test_engine")
        
        assert isinstance(engine, FineGrainedHandoverDecisionEngine)
        assert engine.engine_id == "helper_test_engine"
        assert engine.is_running is False
    
    def test_create_test_handover_request(self):
        """測試創建測試切換請求"""
        request = create_test_handover_request(
            "helper_user", "SAT-HELPER", 
            HandoverTrigger.PREDICTED_OUTAGE, 
            priority=7
        )
        
        assert isinstance(request, HandoverRequest)
        assert request.user_id == "helper_user"
        assert request.current_satellite_id == "SAT-HELPER"
        assert request.trigger_type == HandoverTrigger.PREDICTED_OUTAGE
        assert request.priority == 7
        assert request.service_type == "data"
        assert request.required_bandwidth_mbps == 10.0


if __name__ == "__main__":
    # 運行測試
    pytest.main([__file__, "-v", "--tb=short", "-s"])