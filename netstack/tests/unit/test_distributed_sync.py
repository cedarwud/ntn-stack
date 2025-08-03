"""
Phase 3.2.1.1 分散式時間同步協議單元測試

測試多衛星分散式時間同步協議的完整實現，包括：
1. Berkeley 算法適應版本測試
2. 拜占庭容錯機制測試
3. 主節點選舉算法測試
4. 分層同步架構測試
5. 網路分區容錯測試
6. 同步精度監控測試
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

from src.algorithms.sync.distributed_sync import (
    DistributedSyncAlgorithm,
    SyncMessage,
    PeerNode,
    SyncRole,
    SyncState,
    MessageType,
    create_distributed_sync_algorithm,
    create_test_sync_network
)


class TestSyncMessage:
    """測試同步消息"""
    
    def test_sync_message_creation(self):
        """測試同步消息創建"""
        msg = SyncMessage(
            message_id="test_msg_001",
            message_type=MessageType.SYNC_REQUEST,
            sender_id="node_1",
            receiver_id="node_2",
            timestamp=datetime.now(timezone.utc),
            priority=100,
            clock_accuracy=50000
        )
        
        assert msg.message_id == "test_msg_001"
        assert msg.message_type == MessageType.SYNC_REQUEST
        assert msg.sender_id == "node_1"
        assert msg.receiver_id == "node_2"
        assert msg.priority == 100
        assert msg.clock_accuracy == 50000
    
    def test_sync_message_to_dict(self):
        """測試同步消息轉換為字典"""
        current_time = datetime.now(timezone.utc)
        msg = SyncMessage(
            message_id="test_dict",
            message_type=MessageType.TIME_ANNOUNCE,
            sender_id="master_node",
            receiver_id=None,
            timestamp=current_time,
            origin_timestamp=current_time,
            payload={'test_data': 'value'}
        )
        
        msg_dict = msg.to_dict()
        
        assert isinstance(msg_dict, dict)
        assert msg_dict['message_id'] == "test_dict"
        assert msg_dict['message_type'] == "time_announce"
        assert msg_dict['sender_id'] == "master_node"
        assert msg_dict['receiver_id'] is None
        assert 'timestamp' in msg_dict
        assert 'origin_timestamp' in msg_dict
        assert msg_dict['payload'] == {'test_data': 'value'}


class TestPeerNode:
    """測試對等節點"""
    
    def test_peer_node_creation(self):
        """測試對等節點創建"""
        peer = PeerNode(
            node_id="test_peer",
            role=SyncRole.SLAVE,
            last_seen=datetime.now(timezone.utc)
        )
        
        assert peer.node_id == "test_peer"
        assert peer.role == SyncRole.SLAVE
        assert peer.reliability_score == 1.0
        assert peer.priority == 128
        assert len(peer.offset_history) == 0
    
    def test_peer_node_metrics_update(self):
        """測試對等節點指標更新"""
        peer = PeerNode(
            node_id="metrics_test_peer",
            role=SyncRole.SLAVE,
            last_seen=datetime.now(timezone.utc)
        )
        
        # 添加測試數據
        for i in range(10):
            offset = 0.001 + i * 0.0001  # 1ms + 變化
            delay = 0.05 + i * 0.001     # 50ms + 變化
            jitter = 0.001               # 1ms 抖動
            peer.update_metrics(offset, delay, jitter)
        
        assert len(peer.offset_history) == 10
        assert len(peer.delay_history) == 10
        assert len(peer.jitter_history) == 10
        assert peer.response_time_avg > 50  # 平均響應時間 > 50ms
        assert 0 < peer.reliability_score <= 1.0
    
    def test_peer_node_statistics(self):
        """測試對等節點統計功能"""
        peer = PeerNode(
            node_id="stats_peer",
            role=SyncRole.SLAVE,
            last_seen=datetime.now(timezone.utc)
        )
        
        # 添加一致性數據
        for _ in range(20):
            peer.update_metrics(0.001, 0.05, 0.0001)  # 穩定的指標
        
        avg_offset = peer.get_avg_offset()
        offset_stdev = peer.get_offset_stdev()
        
        assert abs(avg_offset - 0.001) < 0.0001  # 平均偏移接近 1ms
        assert offset_stdev < 0.0001             # 標準差很小
        assert peer.reliability_score > 0.9     # 高可靠性
    
    def test_peer_node_master_suitability(self):
        """測試對等節點主節點適合性判斷"""
        # 高質量節點
        good_peer = PeerNode(
            node_id="good_peer",
            role=SyncRole.CANDIDATE,
            last_seen=datetime.now(timezone.utc)
        )
        good_peer.reliability_score = 0.95
        good_peer.response_time_avg = 100  # 100ms
        good_peer.packet_loss_rate = 0.01  # 1%
        good_peer.clock_accuracy = 50000   # 50µs
        
        assert good_peer.is_suitable_master() is True
        
        # 低質量節點
        bad_peer = PeerNode(
            node_id="bad_peer",
            role=SyncRole.SLAVE,
            last_seen=datetime.now(timezone.utc)
        )
        bad_peer.reliability_score = 0.5   # 低可靠性
        bad_peer.response_time_avg = 800   # 800ms 響應時間
        bad_peer.packet_loss_rate = 0.2    # 20% 丟包率
        bad_peer.clock_accuracy = 500000   # 500µs
        
        assert bad_peer.is_suitable_master() is False


class TestDistributedSyncAlgorithm:
    """測試分散式同步算法"""
    
    @pytest_asyncio.fixture
    async def sync_algorithm(self):
        """創建測試用同步算法"""
        algorithm = create_distributed_sync_algorithm("test_node", SyncRole.SLAVE)
        
        # 設置測試用消息回調
        async def mock_send_callback(message):
            pass  # 模擬發送
        
        algorithm.set_message_callback(mock_send_callback)
        return algorithm
    
    @pytest.mark.asyncio
    async def test_algorithm_initialization(self, sync_algorithm):
        """測試算法初始化"""
        assert isinstance(sync_algorithm, DistributedSyncAlgorithm)
        assert sync_algorithm.node_id == "test_node"
        assert sync_algorithm.role == SyncRole.SLAVE
        assert sync_algorithm.state == SyncState.INITIALIZING
        assert len(sync_algorithm.peers) == 0
        assert sync_algorithm.master_node_id is None
    
    @pytest.mark.asyncio
    async def test_algorithm_start_stop(self, sync_algorithm):
        """測試算法啟動和停止"""
        # 啟動算法
        await sync_algorithm.start_algorithm()
        assert sync_algorithm.is_running is True
        assert sync_algorithm.sync_task is not None
        
        # 等待一小段時間
        await asyncio.sleep(0.1)
        
        # 停止算法
        await sync_algorithm.stop_algorithm()
        assert sync_algorithm.is_running is False
    
    @pytest.mark.asyncio
    async def test_priority_calculation(self, sync_algorithm):
        """測試優先級計算"""
        # 設置高精度時鐘
        sync_algorithm.sync_accuracy = 10000  # 10µs
        priority = sync_algorithm._calculate_priority()
        
        assert isinstance(priority, int)
        assert 1 <= priority <= 255
        
        # 主節點角色應該有更高優先級 (更低數值)
        sync_algorithm.role = SyncRole.MASTER
        master_priority = sync_algorithm._calculate_priority()
        
        assert master_priority < priority  # 數值更低 = 優先級更高
    
    @pytest.mark.asyncio
    async def test_peer_management(self, sync_algorithm):
        """測試對等節點管理"""
        current_time = datetime.now(timezone.utc)
        
        # 模擬接收來自其他節點的消息
        test_message = SyncMessage(
            message_id="peer_test",
            message_type=MessageType.HEARTBEAT,
            sender_id="peer_node_1",
            receiver_id=None,
            timestamp=current_time,
            priority=120,
            clock_accuracy=100000,
            payload={'role': 'slave', 'state': 'synchronized'}
        )
        
        await sync_algorithm.receive_message(test_message)
        
        # 檢查是否正確添加了對等節點
        assert "peer_node_1" in sync_algorithm.peers
        peer = sync_algorithm.peers["peer_node_1"]
        assert peer.node_id == "peer_node_1"
        assert peer.priority == 120
        assert peer.clock_accuracy == 100000
    
    @pytest.mark.asyncio
    async def test_message_routing(self, sync_algorithm):
        """測試消息路由"""
        sent_messages = []
        
        async def capture_send_callback(message):
            sent_messages.append(message)
        
        sync_algorithm.set_message_callback(capture_send_callback)
        
        # 測試心跳消息發送
        await sync_algorithm._send_heartbeat()
        
        assert len(sent_messages) == 1
        assert sent_messages[0].message_type == MessageType.HEARTBEAT
        assert sent_messages[0].sender_id == "test_node"
    
    @pytest.mark.asyncio
    async def test_time_adjustment(self, sync_algorithm):
        """測試時間調整"""
        initial_offset = sync_algorithm.local_offset
        
        # 模擬 100µs 的時間偏移
        test_offset = 100000  # 100µs in ns
        await sync_algorithm._adjust_local_time(test_offset)
        
        # 檢查偏移是否被調整 (使用平滑調整)
        assert abs(sync_algorithm.local_offset - initial_offset) > 0
        assert sync_algorithm.sync_accuracy == abs(test_offset)
        assert sync_algorithm.state in [SyncState.SYNCHRONIZED, SyncState.SYNCING]
    
    @pytest.mark.asyncio
    async def test_master_election_trigger(self, sync_algorithm):
        """測試主節點選舉觸發"""
        # 設置為候選節點
        sync_algorithm.role = SyncRole.CANDIDATE
        
        # 觸發選舉
        await sync_algorithm._trigger_master_election()
        
        # 檢查是否啟動了選舉任務
        assert sync_algorithm.election_task is not None
        assert sync_algorithm.stats['master_elections'] > 0
        
        # 等待選舉完成
        if sync_algorithm.election_task:
            try:
                await asyncio.wait_for(sync_algorithm.election_task, timeout=1.0)
            except asyncio.TimeoutError:
                sync_algorithm.election_task.cancel()
    
    @pytest.mark.asyncio
    async def test_sync_status_retrieval(self, sync_algorithm):
        """測試同步狀態獲取"""
        # 添加一些測試對等節點
        sync_algorithm.peers["peer1"] = PeerNode(
            node_id="peer1",
            role=SyncRole.SLAVE,
            last_seen=datetime.now(timezone.utc)
        )
        
        status = sync_algorithm.get_sync_status()
        
        assert isinstance(status, dict)
        assert status['node_id'] == "test_node"
        assert status['role'] == SyncRole.SLAVE.value
        assert status['state'] == sync_algorithm.state.value
        assert status['peers_count'] == 1
        assert 'peers' in status
        assert 'statistics' in status
        assert 'is_synchronized' in status
    
    @pytest.mark.asyncio
    async def test_config_update(self, sync_algorithm):
        """測試配置更新"""
        original_interval = sync_algorithm.sync_config['sync_interval']
        
        new_config = {
            'sync_interval': 2.0,
            'max_offset_threshold': 2e6
        }
        
        sync_algorithm.update_config(new_config)
        
        assert sync_algorithm.sync_config['sync_interval'] == 2.0
        assert sync_algorithm.sync_config['max_offset_threshold'] == 2e6
        assert sync_algorithm.sync_config['sync_interval'] != original_interval


class TestMasterElection:
    """測試主節點選舉"""
    
    @pytest_asyncio.fixture
    async def election_network(self):
        """創建選舉測試網路"""
        nodes = []
        sent_messages = []
        
        # 創建 3 個候選節點
        for i in range(3):
            node = create_distributed_sync_algorithm(f"candidate_{i}", SyncRole.CANDIDATE)
            
            # 設置不同的時鐘精度
            node.sync_accuracy = 10000 * (i + 1)  # 10µs, 20µs, 30µs
            
            # 共享消息發送回調
            async def create_send_callback(node_id):
                async def send_callback(message):
                    sent_messages.append((node_id, message))
                return send_callback
            
            node.set_message_callback(await create_send_callback(f"candidate_{i}"))
            nodes.append(node)
        
        return nodes, sent_messages
    
    @pytest.mark.asyncio
    async def test_priority_based_election(self, election_network):
        """測試基於優先級的選舉"""
        nodes, sent_messages = election_network
        
        # 手動計算每個節點的優先級
        priorities = []
        for node in nodes:
            priority = node._calculate_priority()
            priorities.append((node.node_id, priority))
        
        # 按優先級排序
        priorities.sort(key=lambda x: x[1])
        expected_winner = priorities[0][0]  # 優先級最高 (數值最低)
        
        # 執行選舉
        for node in nodes:
            await node._run_master_election()
        
        # 檢查是否產生了選舉消息
        election_messages = [
            (sender, msg) for sender, msg in sent_messages 
            if msg.message_type == MessageType.MASTER_ELECTION
        ]
        
        assert len(election_messages) == 3  # 每個節點都發送選舉消息
        
        # 驗證選舉消息包含正確的優先級信息
        for sender, msg in election_messages:
            assert msg.message_type == MessageType.MASTER_ELECTION
            assert msg.priority > 0
            assert msg.clock_accuracy > 0
    
    @pytest.mark.asyncio
    async def test_master_announcement(self, election_network):
        """測試主節點公告"""
        nodes, sent_messages = election_network
        
        # 手動設置第一個節點為主節點
        master_node = nodes[0]
        await master_node._become_master()
        
        # 檢查角色變更
        assert master_node.role == SyncRole.MASTER
        assert master_node.master_node_id == master_node.node_id
        assert master_node.state == SyncState.SYNCHRONIZED
        
        # 檢查是否發送了心跳公告
        heartbeat_messages = [
            (sender, msg) for sender, msg in sent_messages 
            if msg.message_type == MessageType.HEARTBEAT
        ]
        
        assert len(heartbeat_messages) >= 1  # 至少有一個心跳消息


class TestSyncNetwork:
    """測試同步網路"""
    
    @pytest.mark.asyncio
    async def test_network_creation(self):
        """測試同步網路創建"""
        network = create_test_sync_network(5)
        
        assert len(network) == 5
        assert network[0].role == SyncRole.MASTER
        
        for i in range(1, 5):
            assert network[i].role == SyncRole.SLAVE
            assert network[i].node_id == f"slave_node_{i}"
    
    @pytest.mark.asyncio
    async def test_network_message_flow(self):
        """測試網路消息流"""
        network = create_test_sync_network(3)
        all_messages = []
        
        # 設置消息收集器
        for node in network:
            async def create_collector(node_id):
                async def collect_messages(message):
                    all_messages.append((node_id, message))
                return collect_messages
            
            node.set_message_callback(await create_collector(node.node_id))
        
        # 啟動所有節點
        for node in network:
            await node.start_algorithm()
        
        # 運行一段時間
        await asyncio.sleep(0.5)
        
        # 停止所有節點
        for node in network:
            await node.stop_algorithm()
        
        # 檢查是否有消息交換
        assert len(all_messages) > 0
        
        # 檢查主節點是否發送了時間公告
        time_announces = [
            (sender, msg) for sender, msg in all_messages 
            if msg.message_type == MessageType.TIME_ANNOUNCE
        ]
        
        assert len(time_announces) > 0  # 主節點應該發送時間公告


class TestByzantineFaultTolerance:
    """測試拜占庭容錯"""
    
    @pytest.mark.asyncio
    async def test_faulty_node_detection(self):
        """測試故障節點檢測"""
        algorithm = create_distributed_sync_algorithm("test_node", SyncRole.SLAVE)
        
        # 添加一個對等節點
        faulty_peer = PeerNode(
            node_id="faulty_node",
            role=SyncRole.SLAVE,
            last_seen=datetime.now(timezone.utc) - timedelta(seconds=10)  # 10秒前
        )
        algorithm.peers["faulty_node"] = faulty_peer
        
        # 執行清理
        await algorithm._cleanup_expired_peers()
        
        # 檢查故障節點是否被移除
        assert "faulty_node" not in algorithm.peers
    
    @pytest.mark.asyncio
    async def test_conflicting_masters(self):
        """測試衝突主節點處理"""
        algorithm = create_distributed_sync_algorithm("test_node", SyncRole.MASTER)
        algorithm.master_node_id = algorithm.node_id
        
        sent_messages = []
        async def capture_callback(message):
            sent_messages.append(message)
        
        algorithm.set_message_callback(capture_callback)
        
        # 模擬另一個節點聲稱是主節點
        conflicting_message = SyncMessage(
            message_id="conflict_test",
            message_type=MessageType.HEARTBEAT,
            sender_id="conflicting_master",
            receiver_id=None,
            timestamp=datetime.now(timezone.utc),
            payload={'role': 'master'}
        )
        
        await algorithm.receive_message(conflicting_message)
        
        # 應該觸發重新選舉
        assert algorithm.stats['master_elections'] > 0


class TestPerformanceMetrics:
    """測試性能指標"""
    
    @pytest.mark.asyncio
    async def test_message_processing_performance(self):
        """測試消息處理性能"""
        algorithm = create_distributed_sync_algorithm("perf_test", SyncRole.MASTER)
        
        async def null_callback(message):
            pass
        
        algorithm.set_message_callback(null_callback)
        
        # 測試大量消息處理
        messages = []
        for i in range(100):
            msg = SyncMessage(
                message_id=f"perf_msg_{i}",
                message_type=MessageType.HEARTBEAT,
                sender_id=f"sender_{i % 10}",
                receiver_id=None,
                timestamp=datetime.now(timezone.utc)
            )
            messages.append(msg)
        
        start_time = time.time()
        
        for msg in messages:
            await algorithm.receive_message(msg)
        
        processing_time = time.time() - start_time
        
        # 處理 100 條消息應該在 1 秒內完成
        assert processing_time < 1.0
        assert algorithm.stats['messages_received'] == 100
    
    @pytest.mark.asyncio
    async def test_sync_cycle_performance(self):
        """測試同步週期性能"""
        algorithm = create_distributed_sync_algorithm("cycle_perf_test", SyncRole.MASTER)
        
        async def null_callback(message):
            pass
        
        algorithm.set_message_callback(null_callback)
        
        # 測試同步週期執行時間
        start_time = time.time()
        
        for _ in range(10):
            await algorithm._perform_sync_cycle()
        
        cycle_time = time.time() - start_time
        
        # 10 個同步週期應該在合理時間內完成
        assert cycle_time < 1.0  # <1 秒
        assert algorithm.stats['sync_cycles_completed'] == 10


class TestHelperFunctions:
    """測試輔助函數"""
    
    def test_create_distributed_sync_algorithm(self):
        """測試創建分散式同步算法"""
        algorithm = create_distributed_sync_algorithm("helper_test", SyncRole.CANDIDATE)
        
        assert isinstance(algorithm, DistributedSyncAlgorithm)
        assert algorithm.node_id == "helper_test"
        assert algorithm.role == SyncRole.CANDIDATE
    
    def test_create_test_sync_network(self):
        """測試創建測試同步網路"""
        network = create_test_sync_network(7)
        
        assert len(network) == 7
        assert network[0].role == SyncRole.MASTER
        assert network[0].node_id == "master_node"
        
        for i in range(1, 7):
            assert network[i].role == SyncRole.SLAVE
            assert network[i].node_id == f"slave_node_{i}"


if __name__ == "__main__":
    # 運行測試
    pytest.main([__file__, "-v", "--tb=short", "-s"])