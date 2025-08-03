"""
Phase 3.1.1 NTN RRC Procedures 單元測試

測試 3GPP NTN-specific RRC procedures 的完整實現，包括：
1. RRC Connection Establishment
2. RRC Reconfiguration
3. RRC Connection Release  
4. Timing Advance handling
5. Doppler compensation
6. Measurement processing
"""

import pytest
import pytest_asyncio
import asyncio
import time
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

# 導入待測試的模組
import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, project_root)

from src.protocols.rrc.ntn_procedures import (
    NTNRRCProcessor,
    RRCMessage,
    RRCMessageType,
    RRCState,
    NTNTimingAdvance,
    NTNTimingAdvanceType,
    DopplerCompensation,
    NTNConnectionContext,
    create_ntn_rrc_processor,
    create_test_rrc_setup_request,
    create_test_measurement_report
)


class TestNTNTimingAdvance:
    """測試 NTN 時間提前量"""
    
    def test_timing_advance_creation(self):
        """測試時間提前量創建"""
        ta = NTNTimingAdvance(
            ta_type=NTNTimingAdvanceType.DEDICATED_TA,
            ta_value=250000.0,  # 250ms
            ta_validity_time=30,
            satellite_id="STARLINK-1007",
            reference_time=datetime.now(timezone.utc)
        )
        
        assert ta.ta_type == NTNTimingAdvanceType.DEDICATED_TA
        assert ta.ta_value == 250000.0
        assert ta.ta_validity_time == 30
        assert ta.satellite_id == "STARLINK-1007"
        assert ta.is_valid() is True
    
    def test_timing_advance_validity(self):
        """測試時間提前量有效性檢查"""
        # 創建過期的時間提前量
        expired_ta = NTNTimingAdvance(
            ta_type=NTNTimingAdvanceType.COMMON_TA,
            ta_value=100000.0,
            ta_validity_time=1,  # 1秒有效期
            satellite_id="STARLINK-1008",
            reference_time=datetime.now(timezone.utc) - timedelta(seconds=2)
        )
        
        assert expired_ta.is_valid() is False
        
        # 創建有效的時間提前量
        valid_ta = NTNTimingAdvance(
            ta_type=NTNTimingAdvanceType.DEDICATED_TA,
            ta_value=200000.0,
            ta_validity_time=60,
            satellite_id="STARLINK-1008",
            reference_time=datetime.now(timezone.utc)
        )
        
        assert valid_ta.is_valid() is True
    
    def test_timing_advance_types(self):
        """測試不同類型的時間提前量"""
        ta_types = [
            NTNTimingAdvanceType.COMMON_TA,
            NTNTimingAdvanceType.DEDICATED_TA,
            NTNTimingAdvanceType.REFERENCE_TA
        ]
        
        for ta_type in ta_types:
            ta = NTNTimingAdvance(
                ta_type=ta_type,
                ta_value=150000.0,
                ta_validity_time=30,
                satellite_id="TEST-SAT",
                reference_time=datetime.now(timezone.utc)
            )
            assert ta.ta_type == ta_type


class TestDopplerCompensation:
    """測試都卜勒補償"""
    
    def test_doppler_compensation_creation(self):
        """測試都卜勒補償創建"""
        doppler = DopplerCompensation(
            frequency_offset_hz=1500.0,
            compensation_factor=0.001,
            update_period_ms=5000,
            satellite_id="STARLINK-1007",
            ephemeris_time=datetime.now(timezone.utc)
        )
        
        assert doppler.frequency_offset_hz == 1500.0
        assert doppler.compensation_factor == 0.001
        assert doppler.update_period_ms == 5000
        assert doppler.satellite_id == "STARLINK-1007"
    
    def test_doppler_compensation_calculation(self):
        """測試都卜勒補償計算"""
        ephemeris_time = datetime.now(timezone.utc)
        doppler = DopplerCompensation(
            frequency_offset_hz=1000.0,
            compensation_factor=0.002,
            update_period_ms=1000,
            satellite_id="TEST-SAT",
            ephemeris_time=ephemeris_time
        )
        
        # 測試當前時間的補償
        current_time = ephemeris_time
        compensation = doppler.calculate_compensation(current_time)
        assert compensation == 1000.0  # 無時間差，補償值等於基礎偏移
        
        # 測試1小時後的補償
        future_time = ephemeris_time + timedelta(hours=1)
        future_compensation = doppler.calculate_compensation(future_time)
        expected = 1000.0 * (1 + 0.002)  # 1小時的變化
        assert abs(future_compensation - expected) < 0.1


class TestRRCMessage:
    """測試 RRC 消息"""
    
    def test_rrc_message_creation(self):
        """測試 RRC 消息創建"""
        message = RRCMessage(
            message_type=RRCMessageType.RRC_SETUP_REQUEST,
            message_id="test_msg_001",
            cell_identity="STARLINK-1007",
            ue_identity="UE-12345",
            payload={"test_key": "test_value"}
        )
        
        assert message.message_type == RRCMessageType.RRC_SETUP_REQUEST
        assert message.message_id == "test_msg_001"
        assert message.cell_identity == "STARLINK-1007"
        assert message.ue_identity == "UE-12345"
        assert message.payload["test_key"] == "test_value"
        assert isinstance(message.timestamp, datetime)
    
    def test_rrc_message_types(self):
        """測試所有 RRC 消息類型"""
        message_types = [
            RRCMessageType.RRC_SETUP_REQUEST,
            RRCMessageType.RRC_SETUP,
            RRCMessageType.RRC_SETUP_COMPLETE,
            RRCMessageType.RRC_RECONFIGURATION,
            RRCMessageType.RRC_RECONFIGURATION_COMPLETE,
            RRCMessageType.RRC_RELEASE,
            RRCMessageType.MEASUREMENT_REPORT,
            RRCMessageType.NTN_TIMING_ADVANCE_COMMAND,
            RRCMessageType.NTN_DOPPLER_COMPENSATION
        ]
        
        for msg_type in message_types:
            message = RRCMessage(
                message_type=msg_type,
                message_id=f"test_{msg_type.value}"
            )
            assert message.message_type == msg_type


class TestNTNConnectionContext:
    """測試 NTN 連接上下文"""
    
    def test_connection_context_creation(self):
        """測試連接上下文創建"""
        context = NTNConnectionContext(
            ue_identity="UE-12345",
            serving_satellite_id="STARLINK-1007",
            current_state=RRCState.RRC_CONNECTED,
            connection_established_time=datetime.now(timezone.utc),
            last_activity_time=datetime.now(timezone.utc)
        )
        
        assert context.ue_identity == "UE-12345"
        assert context.serving_satellite_id == "STARLINK-1007"
        assert context.current_state == RRCState.RRC_CONNECTED
        assert len(context.neighbor_satellites) == 0
        assert len(context.measurement_config) == 0
    
    def test_connection_context_activity_update(self):
        """測試活動時間更新"""
        context = NTNConnectionContext(
            ue_identity="UE-TEST",
            serving_satellite_id="TEST-SAT",
            current_state=RRCState.RRC_CONNECTED,
            connection_established_time=datetime.now(timezone.utc),
            last_activity_time=datetime.now(timezone.utc) - timedelta(minutes=1)
        )
        
        old_activity_time = context.last_activity_time
        context.update_activity()
        
        assert context.last_activity_time > old_activity_time
    
    def test_timing_advance_validity_check(self):
        """測試時間提前量有效性檢查"""
        context = NTNConnectionContext(
            ue_identity="UE-TEST",
            serving_satellite_id="TEST-SAT",
            current_state=RRCState.RRC_CONNECTED,
            connection_established_time=datetime.now(timezone.utc),
            last_activity_time=datetime.now(timezone.utc)
        )
        
        # 沒有時間提前量
        assert context.is_timing_advance_valid() is False
        
        # 添加有效的時間提前量
        context.timing_advance = NTNTimingAdvance(
            ta_type=NTNTimingAdvanceType.DEDICATED_TA,
            ta_value=250000.0,
            ta_validity_time=60,
            satellite_id="TEST-SAT",
            reference_time=datetime.now(timezone.utc)
        )
        
        assert context.is_timing_advance_valid() is True


class TestNTNRRCProcessor:
    """測試 NTN RRC 處理器"""
    
    @pytest_asyncio.fixture
    async def processor(self):
        """創建測試用的 RRC 處理器"""
        return await create_ntn_rrc_processor()
    
    @pytest.mark.asyncio
    async def test_processor_initialization(self, processor):
        """測試處理器初始化"""
        assert isinstance(processor, NTNRRCProcessor)
        assert len(processor.active_connections) == 0
        assert len(processor.satellite_info) > 0
        assert 'measurement_period_ms' in processor.measurement_config
    
    @pytest.mark.asyncio
    async def test_rrc_setup_request_processing(self, processor):
        """測試 RRC Setup Request 處理"""
        # 創建測試請求
        setup_request = create_test_rrc_setup_request("UE-TEST-001")
        
        # 處理請求
        response = await processor.process_rrc_setup_request(setup_request)
        
        # 驗證響應
        assert response.message_type == RRCMessageType.RRC_SETUP
        assert response.ue_identity == "UE-TEST-001"
        assert 'serving_satellite_id' in response.payload
        assert 'timing_advance' in response.payload
        assert 'doppler_compensation' in response.payload
        assert 'measurement_config' in response.payload
        
        # 驗證連接上下文已創建
        assert "UE-TEST-001" in processor.active_connections
        context = processor.active_connections["UE-TEST-001"]
        assert context.current_state == RRCState.RRC_CONNECTED
        assert context.timing_advance is not None
        assert context.doppler_compensation is not None
    
    @pytest.mark.asyncio
    async def test_rrc_setup_request_missing_ue_identity(self, processor):
        """測試缺少 UE identity 的 RRC Setup Request"""
        setup_request = RRCMessage(
            message_type=RRCMessageType.RRC_SETUP_REQUEST,
            message_id="test_invalid",
            payload={}  # 缺少 ue_identity
        )
        
        response = await processor.process_rrc_setup_request(setup_request)
        
        # 應該返回拒絕響應
        assert 'setup_result' in response.payload
        assert response.payload['setup_result'] == 'rejected'
        assert 'rejection_reason' in response.payload
    
    @pytest.mark.asyncio
    async def test_rrc_reconfiguration_processing(self, processor):
        """測試 RRC Reconfiguration 處理"""
        # 先建立連接
        setup_request = create_test_rrc_setup_request("UE-TEST-002")
        await processor.process_rrc_setup_request(setup_request)
        
        # 創建重配置請求
        reconfig_request = {
            'ue_identity': 'UE-TEST-002',
            'target_satellite_id': 'STARLINK-1008',
            'measurement_config': {
                'rsrp_threshold_dbm': -115
            },
            'neighbor_satellites': ['STARLINK-1009', 'ONEWEB-0001']
        }
        
        # 處理重配置
        response = await processor.process_rrc_reconfiguration(reconfig_request)
        
        # 驗證響應
        assert response.message_type == RRCMessageType.RRC_RECONFIGURATION
        assert response.ue_identity == "UE-TEST-002"
        assert response.payload['reconfiguration_complete'] is True
        
        # 驗證上下文已更新
        context = processor.active_connections["UE-TEST-002"]
        assert context.serving_satellite_id == "STARLINK-1008"
        assert context.measurement_config['rsrp_threshold_dbm'] == -115
        assert len(context.neighbor_satellites) == 2
    
    @pytest.mark.asyncio
    async def test_rrc_reconfiguration_invalid_ue(self, processor):
        """測試無效 UE 的 RRC Reconfiguration"""
        reconfig_request = {
            'ue_identity': 'INVALID-UE'
        }
        
        response = await processor.process_rrc_reconfiguration(reconfig_request)
        
        assert 'error' in response.payload
        assert response.payload['error'] is True
    
    @pytest.mark.asyncio
    async def test_rrc_release_processing(self, processor):
        """測試 RRC Release 處理"""
        # 先建立連接
        setup_request = create_test_rrc_setup_request("UE-TEST-003")
        await processor.process_rrc_setup_request(setup_request)
        
        assert "UE-TEST-003" in processor.active_connections
        
        # 釋放連接
        release_request = {
            'ue_identity': 'UE-TEST-003',
            'cause': 'user_request'
        }
        
        response = await processor.process_rrc_release(release_request)
        
        # 驗證響應
        assert response.message_type == RRCMessageType.RRC_RELEASE
        assert response.ue_identity == "UE-TEST-003"
        assert response.payload['connection_released'] is True
        assert response.payload['release_cause'] == 'user_request'
        
        # 驗證連接已清理
        assert "UE-TEST-003" not in processor.active_connections
    
    @pytest.mark.asyncio
    async def test_measurement_report_processing(self, processor):
        """測試測量報告處理"""
        # 先建立連接
        setup_request = create_test_rrc_setup_request("UE-TEST-004")
        await processor.process_rrc_setup_request(setup_request)
        
        # 創建測量報告
        measurements = [
            {
                'satellite_id': 'STARLINK-1007',
                'rsrp_dbm': -100,
                'sinr_db': 10
            },
            {
                'satellite_id': 'STARLINK-1008',
                'rsrp_dbm': -95,  # 更好的信號
                'sinr_db': 12
            }
        ]
        
        measurement_report = create_test_measurement_report("UE-TEST-004", measurements)
        
        # 處理測量報告
        response = await processor.process_measurement_report(measurement_report)
        
        # 由於鄰近衛星信號更好，應該觸發切換
        if response:
            assert response.message_type == RRCMessageType.RRC_RECONFIGURATION
            assert 'mobility_control_info' in response.payload
            assert response.payload['mobility_control_info']['target_satellite_id'] == 'STARLINK-1008'
    
    @pytest.mark.asyncio
    async def test_timing_advance_update(self, processor):
        """測試時間提前量更新"""
        # 先建立連接
        setup_request = create_test_rrc_setup_request("UE-TEST-005")
        await processor.process_rrc_setup_request(setup_request)
        
        context = processor.active_connections["UE-TEST-005"]
        
        # 模擬時間提前量過期
        context.timing_advance.ta_validity_time = 1
        context.timing_advance.reference_time = datetime.now(timezone.utc) - timedelta(seconds=2)
        
        assert context.is_timing_advance_valid() is False
        
        # 更新時間提前量
        response = await processor.update_timing_advance("UE-TEST-005")
        
        # 驗證響應
        assert response is not None
        assert response.message_type == RRCMessageType.NTN_TIMING_ADVANCE_COMMAND
        assert response.ue_identity == "UE-TEST-005"
        assert 'timing_advance' in response.payload
        
        # 驗證時間提前量已更新
        assert context.is_timing_advance_valid() is True
    
    @pytest.mark.asyncio
    async def test_timing_advance_update_not_needed(self, processor):
        """測試不需要更新時間提前量的情況"""
        # 先建立連接
        setup_request = create_test_rrc_setup_request("UE-TEST-006")
        await processor.process_rrc_setup_request(setup_request)
        
        # 時間提前量仍有效，不需要更新
        response = await processor.update_timing_advance("UE-TEST-006")
        assert response is None
    
    @pytest.mark.asyncio
    async def test_get_active_connections(self, processor):
        """測試獲取活動連接"""
        # 建立多個連接
        for i in range(3):
            setup_request = create_test_rrc_setup_request(f"UE-TEST-{i:03d}")
            await processor.process_rrc_setup_request(setup_request)
        
        # 獲取活動連接
        connections = processor.get_active_connections()
        
        assert len(connections) == 3
        for ue_id, conn_info in connections.items():
            assert 'serving_satellite_id' in conn_info
            assert 'current_state' in conn_info
            assert 'connection_duration' in conn_info
            assert 'timing_advance_valid' in conn_info
            assert conn_info['current_state'] == RRCState.RRC_CONNECTED.value
    
    @pytest.mark.asyncio
    async def test_get_connection_statistics(self, processor):
        """測試獲取連接統計"""
        # 建立連接
        setup_request = create_test_rrc_setup_request("UE-STATS-001")
        await processor.process_rrc_setup_request(setup_request)
        
        # 獲取統計信息
        stats = processor.get_connection_statistics()
        
        assert 'total_active_connections' in stats
        assert 'unique_satellites_in_use' in stats
        assert 'satellites_in_use' in stats
        assert 'average_connection_age' in stats
        
        assert stats['total_active_connections'] == 1
        assert stats['unique_satellites_in_use'] >= 1
        assert len(stats['satellites_in_use']) >= 1
        assert stats['average_connection_age'] >= 0


class TestRRCProcedureIntegration:
    """測試 RRC 程序整合"""
    
    @pytest_asyncio.fixture
    async def processor(self):
        """創建測試用的 RRC 處理器"""
        return await create_ntn_rrc_processor()
    
    @pytest.mark.asyncio
    async def test_complete_connection_lifecycle(self, processor):
        """測試完整的連接生命週期"""
        ue_identity = "UE-LIFECYCLE-001"
        
        # 1. RRC Setup
        setup_request = create_test_rrc_setup_request(ue_identity)
        setup_response = await processor.process_rrc_setup_request(setup_request)
        
        assert setup_response.message_type == RRCMessageType.RRC_SETUP
        assert ue_identity in processor.active_connections
        
        # 2. RRC Reconfiguration
        reconfig_request = {
            'ue_identity': ue_identity,
            'measurement_config': {'rsrp_threshold_dbm': -108}
        }
        reconfig_response = await processor.process_rrc_reconfiguration(reconfig_request)
        
        assert reconfig_response.payload['reconfiguration_complete'] is True
        
        # 3. 測量報告處理
        measurements = [
            {'satellite_id': processor.active_connections[ue_identity].serving_satellite_id, 'rsrp_dbm': -105}
        ]
        measurement_report = create_test_measurement_report(ue_identity, measurements)
        await processor.process_measurement_report(measurement_report)
        
        # 4. RRC Release
        release_request = {'ue_identity': ue_identity}
        release_response = await processor.process_rrc_release(release_request)
        
        assert release_response.payload['connection_released'] is True
        assert ue_identity not in processor.active_connections
    
    @pytest.mark.asyncio
    async def test_satellite_handover_scenario(self, processor):
        """測試衛星切換場景"""
        ue_identity = "UE-HANDOVER-001"
        
        # 建立初始連接
        setup_request = create_test_rrc_setup_request(ue_identity)
        await processor.process_rrc_setup_request(setup_request)
        
        initial_satellite = processor.active_connections[ue_identity].serving_satellite_id
        
        # 創建觸發切換的測量報告
        measurements = [
            {
                'satellite_id': initial_satellite,
                'rsrp_dbm': -110  # 弱信號
            },
            {
                'satellite_id': 'STARLINK-1008',
                'rsrp_dbm': -102  # 強信號，觸發切換
            }
        ]
        
        measurement_report = create_test_measurement_report(ue_identity, measurements)
        handover_command = await processor.process_measurement_report(measurement_report)
        
        # 驗證切換命令
        if handover_command:
            assert handover_command.message_type == RRCMessageType.RRC_RECONFIGURATION
            assert 'mobility_control_info' in handover_command.payload
            
            # 執行切換
            reconfig_request = {
                'ue_identity': ue_identity,
                'target_satellite_id': 'STARLINK-1008'
            }
            
            await processor.process_rrc_reconfiguration(reconfig_request)
            
            # 驗證切換完成
            final_satellite = processor.active_connections[ue_identity].serving_satellite_id
            assert final_satellite == 'STARLINK-1008'
            assert final_satellite != initial_satellite
    
    @pytest.mark.asyncio
    async def test_concurrent_connections(self, processor):
        """測試併發連接處理"""
        ue_identities = [f"UE-CONCURRENT-{i:03d}" for i in range(5)]
        
        # 併發建立連接
        setup_tasks = []
        for ue_id in ue_identities:
            setup_request = create_test_rrc_setup_request(ue_id)
            task = processor.process_rrc_setup_request(setup_request)
            setup_tasks.append(task)
        
        responses = await asyncio.gather(*setup_tasks)
        
        # 驗證所有連接都成功建立
        assert len(responses) == 5
        for i, response in enumerate(responses):
            assert response.message_type == RRCMessageType.RRC_SETUP
            assert response.ue_identity == ue_identities[i]
        
        # 驗證所有連接都在活動列表中
        assert len(processor.active_connections) == 5
        for ue_id in ue_identities:
            assert ue_id in processor.active_connections


class TestHelperFunctions:
    """測試輔助函數"""
    
    @pytest.mark.asyncio
    async def test_create_ntn_rrc_processor(self):
        """測試創建 NTN RRC 處理器"""
        processor = await create_ntn_rrc_processor()
        
        assert isinstance(processor, NTNRRCProcessor)
        assert len(processor.satellite_info) > 0
        assert 'STARLINK-1007' in processor.satellite_info
        assert 'STARLINK-1008' in processor.satellite_info
        assert 'ONEWEB-0001' in processor.satellite_info
    
    def test_create_test_rrc_setup_request(self):
        """測試創建測試 RRC Setup Request"""
        ue_identity = "TEST-UE-123"
        request = create_test_rrc_setup_request(ue_identity)
        
        assert request.message_type == RRCMessageType.RRC_SETUP_REQUEST
        assert request.payload['ue_identity'] == ue_identity
        assert 'establishment_cause' in request.payload
        assert 'selected_plmn_identity' in request.payload
    
    def test_create_test_measurement_report(self):
        """測試創建測量報告"""
        ue_identity = "TEST-UE-456"
        measurements = [
            {'satellite_id': 'SAT-1', 'rsrp_dbm': -100},
            {'satellite_id': 'SAT-2', 'rsrp_dbm': -105}
        ]
        
        report = create_test_measurement_report(ue_identity, measurements)
        
        assert report['ue_identity'] == ue_identity
        assert len(report['measurements']) == 2
        assert 'measurement_id' in report
        assert 'report_timestamp' in report


# 性能測試
class TestRRCProcedurePerformance:
    """測試 RRC 程序性能"""
    
    @pytest_asyncio.fixture
    async def processor(self):
        """創建測試用的 RRC 處理器"""
        return await create_ntn_rrc_processor()
    
    @pytest.mark.asyncio
    async def test_setup_request_processing_time(self, processor):
        """測試 RRC Setup Request 處理時間"""
        setup_request = create_test_rrc_setup_request("UE-PERF-001")
        
        start_time = time.time()
        response = await processor.process_rrc_setup_request(setup_request)
        processing_time = time.time() - start_time
        
        # RRC Setup 處理應該在 50ms 內完成
        assert processing_time < 0.05
        assert response.message_type == RRCMessageType.RRC_SETUP
    
    @pytest.mark.asyncio
    async def test_measurement_report_processing_time(self, processor):
        """測試測量報告處理時間"""
        # 先建立連接
        setup_request = create_test_rrc_setup_request("UE-PERF-002")
        await processor.process_rrc_setup_request(setup_request)
        
        # 創建大量測量數據
        measurements = [
            {'satellite_id': f'SAT-{i}', 'rsrp_dbm': -100 - i}
            for i in range(50)
        ]
        
        measurement_report = create_test_measurement_report("UE-PERF-002", measurements)
        
        start_time = time.time()
        await processor.process_measurement_report(measurement_report)
        processing_time = time.time() - start_time
        
        # 測量報告處理應該在 20ms 內完成
        assert processing_time < 0.02


if __name__ == "__main__":
    # 運行測試
    pytest.main([__file__, "-v", "--tb=short", "-s"])