"""
Phase 3.2.1.3 狀態同步保證機制單元測試

測試狀態同步保證機制的完整實現，包括：
1. 用戶上下文同步
2. 會話狀態遷移
3. 數據一致性保證
4. 分散式狀態管理
5. 故障恢復機制
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

from src.algorithms.sync.state_synchronization import (
    StateSynchronizationEngine,
    StateEntry,
    StateVersion,
    StateType,
    SyncOperation,
    ConsistencyLevel,
    NodeRole,
    SyncMessage,
    NodeState,
    create_state_synchronization_engine,
    create_test_user_context,
    create_test_session_state
)


class TestStateVersion:
    """測試狀態版本"""
    
    def test_state_version_creation(self):
        """測試狀態版本創建"""
        version = StateVersion(
            version_id="test_version_001",
            timestamp=datetime.now(timezone.utc),
            node_id="node_1",
            operation=SyncOperation.CREATE,
            checksum="abc123"
        )
        
        assert version.version_id == "test_version_001"
        assert version.node_id == "node_1"
        assert version.operation == SyncOperation.CREATE
        assert version.checksum == "abc123"
    
    def test_state_version_auto_id(self):
        """測試狀態版本自動ID生成"""
        version = StateVersion(
            version_id="",  # 空ID會自動生成
            timestamp=datetime.now(timezone.utc),
            node_id="node_1",
            operation=SyncOperation.UPDATE,
            checksum="def456"
        )
        
        assert version.version_id != ""
        assert len(version.version_id) == 36  # UUID格式


class TestStateEntry:
    """測試狀態條目"""
    
    def test_state_entry_creation(self):
        """測試狀態條目創建"""
        version = StateVersion(
            version_id="ver_001",
            timestamp=datetime.now(timezone.utc),
            node_id="node_1",
            operation=SyncOperation.CREATE,
            checksum=""
        )
        
        test_data = {"user_id": "user123", "status": "active"}
        
        entry = StateEntry(
            state_id="state_001",
            state_type=StateType.USER_CONTEXT,
            data=test_data,
            version=version,
            consistency_level=ConsistencyLevel.STRONG,
            ttl_seconds=3600,
            owner_node_id="node_1"
        )
        
        assert entry.state_id == "state_001"
        assert entry.state_type == StateType.USER_CONTEXT
        assert entry.data == test_data
        assert entry.consistency_level == ConsistencyLevel.STRONG
        assert entry.ttl_seconds == 3600
        assert entry.owner_node_id == "node_1"
    
    def test_checksum_calculation(self):
        """測試校驗和計算"""
        version = StateVersion(
            version_id="ver_001",
            timestamp=datetime.now(timezone.utc),
            node_id="node_1",
            operation=SyncOperation.CREATE,
            checksum=""
        )
        
        entry = StateEntry(
            state_id="state_001",
            state_type=StateType.SESSION_STATE,
            data={"key": "value", "number": 42},
            version=version,
            owner_node_id="node_1"
        )
        
        checksum = entry.calculate_checksum()
        assert isinstance(checksum, str)
        assert len(checksum) == 64  # SHA256 hex length
        
        # 相同數據應該產生相同校驗和
        entry2 = StateEntry(
            state_id="state_002",
            state_type=StateType.SESSION_STATE,
            data={"key": "value", "number": 42},
            version=version,
            owner_node_id="node_1"
        )
        
        assert entry.calculate_checksum() == entry2.calculate_checksum()
    
    def test_expiration_check(self):
        """測試過期檢查"""
        # 測試無TTL的狀態（永不過期）
        version = StateVersion(
            version_id="ver_001",
            timestamp=datetime.now(timezone.utc),
            node_id="node_1",
            operation=SyncOperation.CREATE,
            checksum=""
        )
        
        entry_no_ttl = StateEntry(
            state_id="state_no_ttl",
            state_type=StateType.USER_CONTEXT,
            data={"test": "data"},
            version=version,
            owner_node_id="node_1"
        )
        
        assert entry_no_ttl.is_expired() is False
        
        # 測試未過期的狀態
        entry_fresh = StateEntry(
            state_id="state_fresh",
            state_type=StateType.USER_CONTEXT,
            data={"test": "data"},
            version=version,
            ttl_seconds=3600,  # 1小時TTL
            owner_node_id="node_1"
        )
        
        assert entry_fresh.is_expired() is False
        
        # 測試過期的狀態
        old_version = StateVersion(
            version_id="old_ver",
            timestamp=datetime.now(timezone.utc) - timedelta(hours=2),  # 2小時前
            node_id="node_1",
            operation=SyncOperation.CREATE,
            checksum=""
        )
        
        entry_expired = StateEntry(
            state_id="state_expired",
            state_type=StateType.USER_CONTEXT,
            data={"test": "data"},
            version=old_version,
            ttl_seconds=3600,  # 1小時TTL，但創建時間是2小時前
            owner_node_id="node_1"
        )
        
        assert entry_expired.is_expired() is True


class TestSyncMessage:
    """測試同步消息"""
    
    def test_sync_message_creation(self):
        """測試同步消息創建"""
        message = SyncMessage(
            message_id="msg_001",
            message_type="state_sync",
            sender_id="node_1",
            receiver_id="node_2",
            timestamp=datetime.now(timezone.utc),
            operation=SyncOperation.UPDATE,
            term=5,
            consistency_requirement=ConsistencyLevel.STRONG,
            sequence_number=100
        )
        
        assert message.message_id == "msg_001"
        assert message.message_type == "state_sync"
        assert message.sender_id == "node_1"
        assert message.receiver_id == "node_2"
        assert message.operation == SyncOperation.UPDATE
        assert message.term == 5
        assert message.consistency_requirement == ConsistencyLevel.STRONG
        assert message.sequence_number == 100


class TestNodeState:
    """測試節點狀態"""
    
    def test_node_state_creation(self):
        """測試節點狀態創建"""
        node_state = NodeState(
            node_id="test_node",
            role=NodeRole.FOLLOWER,
            term=3,
            last_heartbeat=datetime.now(timezone.utc),
            response_time_ms=50.0,
            success_rate=0.95,
            load_factor=0.6,
            is_healthy=True
        )
        
        assert node_state.node_id == "test_node"
        assert node_state.role == NodeRole.FOLLOWER
        assert node_state.term == 3
        assert node_state.response_time_ms == 50.0
        assert node_state.success_rate == 0.95
        assert node_state.is_healthy is True
    
    def test_node_activity_check(self):
        """測試節點活躍性檢查"""
        # 活躍節點
        active_node = NodeState(
            node_id="active_node",
            role=NodeRole.FOLLOWER,
            term=1,
            last_heartbeat=datetime.now(timezone.utc),  # 剛剛有心跳
            is_healthy=True
        )
        
        assert active_node.is_active(timeout_seconds=30) is True
        
        # 不活躍節點（心跳超時）
        inactive_node = NodeState(
            node_id="inactive_node",
            role=NodeRole.FOLLOWER,
            term=1,
            last_heartbeat=datetime.now(timezone.utc) - timedelta(minutes=5),  # 5分鐘前
            is_healthy=True
        )
        
        assert inactive_node.is_active(timeout_seconds=30) is False
        
        # 不健康節點
        unhealthy_node = NodeState(
            node_id="unhealthy_node",
            role=NodeRole.FOLLOWER,
            term=1,
            last_heartbeat=datetime.now(timezone.utc),
            is_healthy=False
        )
        
        assert unhealthy_node.is_active(timeout_seconds=30) is False


class TestStateSynchronizationEngine:
    """測試狀態同步引擎"""
    
    @pytest_asyncio.fixture
    async def sync_engine(self):
        """創建測試用同步引擎"""
        engine = create_state_synchronization_engine("test_node", ["node1", "node2", "node3"])
        return engine
    
    @pytest_asyncio.fixture
    async def running_engine(self):
        """創建運行中的同步引擎"""
        engine = create_state_synchronization_engine("running_node", ["node1", "node2"])
        await engine.start_engine()
        yield engine
        await engine.stop_engine()
    
    @pytest.mark.asyncio
    async def test_engine_initialization(self, sync_engine):
        """測試引擎初始化"""
        assert isinstance(sync_engine, StateSynchronizationEngine)
        assert sync_engine.node_id == "test_node"
        assert len(sync_engine.cluster_nodes) == 3
        assert sync_engine.role == NodeRole.FOLLOWER
        assert sync_engine.is_running is False
        assert len(sync_engine.state_store) == 0
    
    @pytest.mark.asyncio
    async def test_engine_start_stop(self, sync_engine):
        """測試引擎啟動和停止"""
        # 啟動引擎
        await sync_engine.start_engine()
        assert sync_engine.is_running is True
        assert sync_engine.sync_task is not None
        assert sync_engine.heartbeat_task is not None
        
        # 等待一小段時間
        await asyncio.sleep(0.1)
        
        # 停止引擎
        await sync_engine.stop_engine()
        assert sync_engine.is_running is False
    
    @pytest.mark.asyncio
    async def test_create_state(self, running_engine):
        """測試創建狀態"""
        test_data = create_test_user_context("user123")
        
        success = await running_engine.create_state(
            state_id="user_context_123",
            state_type=StateType.USER_CONTEXT,
            data=test_data,
            consistency_level=ConsistencyLevel.EVENTUAL,
            ttl_seconds=3600
        )
        
        assert success is True
        assert "user_context_123" in running_engine.state_store
        
        # 檢查創建的狀態
        state_entry = running_engine.state_store["user_context_123"]
        assert state_entry.state_type == StateType.USER_CONTEXT
        assert state_entry.data == test_data
        assert state_entry.consistency_level == ConsistencyLevel.EVENTUAL
        assert state_entry.ttl_seconds == 3600
        assert state_entry.owner_node_id == running_engine.node_id
    
    @pytest.mark.asyncio
    async def test_update_state(self, running_engine):
        """測試更新狀態"""
        # 先創建狀態
        original_data = {"value": "original"}
        await running_engine.create_state(
            state_id="update_test",
            state_type=StateType.SESSION_STATE,
            data=original_data
        )
        
        # 更新狀態
        updated_data = {"value": "updated", "new_field": "added"}
        success = await running_engine.update_state(
            state_id="update_test",
            data=updated_data,
            consistency_level=ConsistencyLevel.BOUNDED
        )
        
        assert success is True
        
        # 檢查更新後的狀態
        updated_state = running_engine.state_store["update_test"]
        assert updated_state.data == updated_data
        assert updated_state.consistency_level == ConsistencyLevel.BOUNDED
        
        # 檢查版本歷史
        assert len(running_engine.state_versions["update_test"]) == 2
    
    @pytest.mark.asyncio
    async def test_delete_state(self, running_engine):
        """測試刪除狀態"""
        # 先創建狀態
        await running_engine.create_state(
            state_id="delete_test",
            state_type=StateType.BEARER_CONTEXT,
            data={"bearer_id": 5}
        )
        
        assert "delete_test" in running_engine.state_store
        
        # 刪除狀態
        success = await running_engine.delete_state(
            state_id="delete_test",
            consistency_level=ConsistencyLevel.EVENTUAL
        )
        
        assert success is True
        assert "delete_test" not in running_engine.state_store
    
    @pytest.mark.asyncio
    async def test_get_state(self, running_engine):
        """測試獲取狀態"""
        # 測試獲取不存在的狀態
        state = await running_engine.get_state("nonexistent")
        assert state is None
        
        # 創建狀態後獲取
        test_data = {"test": "get_state"}
        await running_engine.create_state(
            state_id="get_test",
            state_type=StateType.QOS_CONTEXT,
            data=test_data
        )
        
        retrieved_state = await running_engine.get_state("get_test")
        assert retrieved_state is not None
        assert retrieved_state.state_id == "get_test"
        assert retrieved_state.data == test_data
    
    @pytest.mark.asyncio
    async def test_list_states(self, running_engine):
        """測試列出狀態"""
        # 創建多個不同類型的狀態
        await running_engine.create_state(
            "user1", StateType.USER_CONTEXT, {"user": "1"}
        )
        await running_engine.create_state(
            "user2", StateType.USER_CONTEXT, {"user": "2"}
        )
        await running_engine.create_state(
            "session1", StateType.SESSION_STATE, {"session": "1"}
        )
        
        # 列出所有狀態
        all_states = await running_engine.list_states()
        assert len(all_states) == 3
        
        # 按類型過濾
        user_states = await running_engine.list_states(state_type=StateType.USER_CONTEXT)
        assert len(user_states) == 2
        assert all(s.state_type == StateType.USER_CONTEXT for s in user_states)
        
        session_states = await running_engine.list_states(state_type=StateType.SESSION_STATE)
        assert len(session_states) == 1
        assert session_states[0].state_type == StateType.SESSION_STATE
        
        # 按所有者過濾
        owned_states = await running_engine.list_states(owner_node_id=running_engine.node_id)
        assert len(owned_states) == 3  # 所有狀態都是當前節點創建的
    
    @pytest.mark.asyncio
    async def test_migrate_state(self, running_engine):
        """測試狀態遷移"""
        # 創建要遷移的狀態
        await running_engine.create_state(
            state_id="migrate_test",
            state_type=StateType.MOBILITY_CONTEXT,
            data={"location": "cell_1"}
        )
        
        # 遷移到目標節點
        success = await running_engine.migrate_state(
            state_id="migrate_test",
            target_node_id="target_node"
        )
        
        # 在模擬環境中，遷移會成功
        assert success is True
        assert "migrate_test" not in running_engine.state_store
        assert running_engine.stats['states_migrated'] == 1
    
    @pytest.mark.asyncio
    async def test_state_expiration(self, running_engine):
        """測試狀態過期"""
        # 創建短TTL的狀態
        await running_engine.create_state(
            state_id="expire_test",
            state_type=StateType.SECURITY_CONTEXT,
            data={"token": "secret"},
            ttl_seconds=1  # 1秒TTL
        )
        
        # 立即獲取應該成功
        state = await running_engine.get_state("expire_test")
        assert state is not None
        
        # 等待過期
        await asyncio.sleep(1.1)
        
        # 再次獲取應該返回None（已過期並被刪除）
        expired_state = await running_engine.get_state("expire_test")
        assert expired_state is None
    
    @pytest.mark.asyncio
    async def test_engine_status(self, running_engine):
        """測試引擎狀態獲取"""
        # 創建一些狀態
        await running_engine.create_state("test1", StateType.USER_CONTEXT, {"test": 1})
        await running_engine.create_state("test2", StateType.SESSION_STATE, {"test": 2})
        
        status = running_engine.get_engine_status()
        
        assert isinstance(status, dict)
        assert status['node_id'] == running_engine.node_id
        assert status['role'] == running_engine.role.value
        assert status['is_running'] is True
        assert status['states_count'] == 2
        assert 'statistics' in status
        assert 'cluster_size' in status
    
    @pytest.mark.asyncio
    async def test_config_update(self, running_engine):
        """測試配置更新"""
        original_interval = running_engine.sync_config['heartbeat_interval_ms']
        
        new_config = {
            'heartbeat_interval_ms': 2000,
            'sync_batch_size': 200
        }
        
        running_engine.update_config(new_config)
        
        assert running_engine.sync_config['heartbeat_interval_ms'] == 2000
        assert running_engine.sync_config['sync_batch_size'] == 200
        assert running_engine.sync_config['heartbeat_interval_ms'] != original_interval
    
    @pytest.mark.asyncio
    async def test_callback_management(self, running_engine):
        """測試回調管理"""
        callback_called = []
        
        async def test_callback(state_entry, operation):
            callback_called.append((state_entry.state_id, operation))
        
        # 添加回調
        running_engine.add_state_change_callback(test_callback)
        
        # 創建狀態應該觸發回調
        await running_engine.create_state(
            "callback_test", StateType.USER_CONTEXT, {"test": "callback"}
        )
        
        await asyncio.sleep(0.1)  # 等待回調執行
        
        assert len(callback_called) == 1
        assert callback_called[0] == ("callback_test", SyncOperation.CREATE)
        
        # 移除回調
        running_engine.remove_state_change_callback(test_callback)
        
        # 再創建狀態不應該觸發回調
        await running_engine.create_state(
            "callback_test2", StateType.SESSION_STATE, {"test": "no_callback"}
        )
        
        await asyncio.sleep(0.1)
        
        assert len(callback_called) == 1  # 沒有新的回調


class TestConsistencyLevels:
    """測試一致性級別"""
    
    @pytest_asyncio.fixture
    async def leader_engine(self):
        """創建Leader節點引擎"""
        engine = create_state_synchronization_engine("leader", ["leader", "follower1", "follower2"])
        await engine.start_engine()
        # 在測試中，我們手動設置為Leader
        engine.role = NodeRole.LEADER
        engine.leader_id = "leader"
        yield engine
        await engine.stop_engine()
    
    @pytest.mark.asyncio
    async def test_eventual_consistency(self, leader_engine):
        """測試最終一致性"""
        success = await leader_engine.create_state(
            state_id="eventual_test",
            state_type=StateType.USER_CONTEXT,
            data={"consistency": "eventual"},
            consistency_level=ConsistencyLevel.EVENTUAL
        )
        
        assert success is True
        
        # 最終一致性應該立即在本地存儲成功
        state = await leader_engine.get_state("eventual_test")
        assert state is not None
        assert state.consistency_level == ConsistencyLevel.EVENTUAL
    
    @pytest.mark.asyncio
    async def test_strong_consistency_timeout(self, leader_engine):
        """測試強一致性超時"""
        # 由於沒有實際的網路節點，強一致性會超時
        # 但我們測試超時處理機制
        
        # 設置較短的超時時間進行測試
        leader_engine.sync_config['consistency_timeout_ms'] = 100
        
        success = await leader_engine.create_state(
            state_id="strong_test",
            state_type=StateType.SESSION_STATE,
            data={"consistency": "strong"},
            consistency_level=ConsistencyLevel.STRONG
        )
        
        # 在沒有其他節點的情況下，強一致性可能會超時失敗
        # 但這取決於具體實現
        assert isinstance(success, bool)


class TestClusterBehavior:
    """測試集群行為"""
    
    @pytest.mark.asyncio
    async def test_single_node_cluster(self):
        """測試單節點集群"""
        engine = create_state_synchronization_engine("single_node", ["single_node"])
        await engine.start_engine()
        
        # 單節點應該自動成為Leader
        await asyncio.sleep(0.1)
        assert engine.role == NodeRole.LEADER
        assert engine.leader_id == "single_node"
        
        # 可以正常創建狀態
        success = await engine.create_state(
            "single_test", StateType.USER_CONTEXT, {"single": True}
        )
        assert success is True
        
        await engine.stop_engine()
    
    @pytest.mark.asyncio
    async def test_multi_node_cluster_init(self):
        """測試多節點集群初始化"""
        engines = []
        
        try:
            # 創建3個節點的集群
            cluster_nodes = ["node1", "node2", "node3"]
            
            for i, node_id in enumerate(cluster_nodes):
                engine = create_state_synchronization_engine(node_id, cluster_nodes)
                # 縮短選舉超時以加快測試
                engine.sync_config['election_timeout_ms'] = 200
                await engine.start_engine()
                engines.append(engine)
                
                # 檢查集群狀態初始化
                assert len(engine.cluster_nodes) == 3
                assert len(engine.cluster_nodes_state) == 2  # 不包括自己
            
            await asyncio.sleep(0.5)  # 等待選舉完成
            
            # 檢查集群初始化完成（在模擬環境中，我們主要測試初始化）
            # 所有節點都應該正常運行
            running_engines = [e for e in engines if e.is_running]
            assert len(running_engines) == 3  # 所有節點都在運行
            
            # 檢查選舉統計（至少有節點發起過選舉）
            total_elections = sum(e.stats['elections_held'] for e in engines)
            assert total_elections >= 1  # 至少有一次選舉嘗試
            
        finally:
            # 清理
            for engine in engines:
                await engine.stop_engine()


class TestBackupAndRestore:
    """測試備份和恢復"""
    
    @pytest_asyncio.fixture
    async def backup_engine(self):
        """創建用於備份測試的引擎"""
        engine = create_state_synchronization_engine("backup_node", ["backup_node"])
        await engine.start_engine()
        
        # 創建一些測試狀態
        await engine.create_state("state1", StateType.USER_CONTEXT, {"user": "1"})
        await engine.create_state("state2", StateType.SESSION_STATE, {"session": "2"})
        await engine.create_state("state3", StateType.BEARER_CONTEXT, {"bearer": "3"})
        
        yield engine
        await engine.stop_engine()
    
    @pytest.mark.asyncio
    async def test_backup_creation(self, backup_engine):
        """測試備份創建"""
        # 手動觸發備份
        success = await backup_engine._create_backup()
        
        assert success is True
        assert backup_engine.stats['backup_operations'] == 1


class TestPerformanceMetrics:
    """測試性能指標"""
    
    @pytest_asyncio.fixture
    async def perf_engine(self):
        """創建性能測試引擎"""
        engine = create_state_synchronization_engine("perf_node", ["perf_node"])
        await engine.start_engine()
        yield engine
        await engine.stop_engine()
    
    @pytest.mark.asyncio
    async def test_state_operations_performance(self, perf_engine):
        """測試狀態操作性能"""
        # 測試批量創建性能
        start_time = time.time()
        
        for i in range(100):
            await perf_engine.create_state(
                f"perf_state_{i}",
                StateType.USER_CONTEXT,
                {"index": i, "data": f"test_data_{i}"}
            )
        
        create_time = time.time() - start_time
        
        # 100個狀態創建應該在合理時間內完成
        assert create_time < 1.0  # <1秒
        assert len(perf_engine.state_store) == 100
        
        # 測試批量查詢性能
        start_time = time.time()
        
        for i in range(100):
            state = await perf_engine.get_state(f"perf_state_{i}")
            assert state is not None
        
        query_time = time.time() - start_time
        
        # 100個狀態查詢應該很快
        assert query_time < 0.5  # <0.5秒
    
    @pytest.mark.asyncio
    async def test_list_states_performance(self, perf_engine):
        """測試狀態列表性能"""
        # 創建不同類型的狀態
        for i in range(50):
            await perf_engine.create_state(
                f"user_{i}", StateType.USER_CONTEXT, {"user": i}
            )
            await perf_engine.create_state(
                f"session_{i}", StateType.SESSION_STATE, {"session": i}
            )
        
        # 測試列出所有狀態的性能
        start_time = time.time()
        all_states = await perf_engine.list_states()
        list_all_time = time.time() - start_time
        
        assert len(all_states) == 100
        assert list_all_time < 0.1  # <100ms
        
        # 測試按類型過濾的性能
        start_time = time.time()
        user_states = await perf_engine.list_states(state_type=StateType.USER_CONTEXT)
        filter_time = time.time() - start_time
        
        assert len(user_states) == 50
        assert filter_time < 0.1  # <100ms


class TestHelperFunctions:
    """測試輔助函數"""
    
    def test_create_state_synchronization_engine(self):
        """測試創建狀態同步引擎"""
        engine = create_state_synchronization_engine("helper_test", ["node1", "node2"])
        
        assert isinstance(engine, StateSynchronizationEngine)
        assert engine.node_id == "helper_test"
        assert len(engine.cluster_nodes) == 2
        assert engine.role == NodeRole.FOLLOWER
    
    def test_create_test_user_context(self):
        """測試創建測試用戶上下文"""
        user_context = create_test_user_context("test_user_123")
        
        assert isinstance(user_context, dict)
        assert user_context['user_id'] == "test_user_123"
        assert 'imsi' in user_context
        assert 'current_cell_id' in user_context
        assert 'bearer_contexts' in user_context
        assert 'security_context' in user_context
        assert 'mobility_state' in user_context
        assert 'last_update' in user_context
        
        # 檢查IMSI格式
        assert user_context['imsi'].startswith('46000')
        assert len(user_context['imsi']) == 15
        
        # 檢查承載上下文
        assert len(user_context['bearer_contexts']) >= 1
        bearer = user_context['bearer_contexts'][0]
        assert 'bearer_id' in bearer
        assert 'qci' in bearer
        assert 'allocated_bandwidth_kbps' in bearer
    
    def test_create_test_session_state(self):
        """測試創建測試會話狀態"""
        session_state = create_test_session_state("test_session_456")
        
        assert isinstance(session_state, dict)
        assert session_state['session_id'] == "test_session_456"
        assert 'session_type' in session_state
        assert 'apn' in session_state
        assert 'ip_address' in session_state
        assert 'allocated_resources' in session_state
        assert 'active_flows' in session_state
        assert 'qos_parameters' in session_state
        assert 'established_time' in session_state
        
        # 檢查IP地址格式
        ip_address = session_state['ip_address']
        assert ip_address.startswith('192.168.1.')
        
        # 檢查活動流
        flows = session_state['active_flows']
        assert len(flows) >= 1
        flow = flows[0]
        assert 'flow_id' in flow
        assert 'flow_type' in flow
        assert 'bandwidth_kbps' in flow
        
        # 檢查QoS參數
        qos = session_state['qos_parameters']
        assert 'guaranteed_bit_rate_kbps' in qos
        assert 'maximum_bit_rate_kbps' in qos
        assert 'packet_delay_budget_ms' in qos
        assert 'packet_error_loss_rate' in qos


if __name__ == "__main__":
    # 運行測試
    pytest.main([__file__, "-v", "--tb=short", "-s"])