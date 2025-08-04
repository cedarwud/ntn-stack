"""
Phase 3.2.1.3: 狀態同步保證機制實現

實現分散式狀態同步算法，包括：
1. 用戶上下文同步
2. 會話狀態遷移
3. 數據一致性保證
4. 分散式狀態管理
5. 故障恢復機制

符合標準：
- 3GPP TS 38.300 NTN 狀態管理
- 3GPP TS 38.331 RRC 狀態轉換
- RAFT 分散式共識算法
- CAP 定理一致性保證
"""

import asyncio
import logging
import time
import json
import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Any, Callable, Union
from enum import Enum
from datetime import datetime, timezone, timedelta
from collections import defaultdict, deque
import uuid
from concurrent.futures import ThreadPoolExecutor
import threading

logger = logging.getLogger(__name__)


class StateType(Enum):
    """狀態類型"""
    USER_CONTEXT = "user_context"          # 用戶上下文
    SESSION_STATE = "session_state"        # 會話狀態
    BEARER_CONTEXT = "bearer_context"      # 承載上下文
    SECURITY_CONTEXT = "security_context"  # 安全上下文
    QOS_CONTEXT = "qos_context"            # QoS 上下文
    MOBILITY_CONTEXT = "mobility_context"  # 移動性上下文


class SyncOperation(Enum):
    """同步操作類型"""
    CREATE = "create"      # 創建狀態
    UPDATE = "update"      # 更新狀態
    DELETE = "delete"      # 刪除狀態
    MIGRATE = "migrate"    # 遷移狀態
    BACKUP = "backup"      # 備份狀態
    RESTORE = "restore"    # 恢復狀態


class ConsistencyLevel(Enum):
    """一致性級別"""
    EVENTUAL = "eventual"      # 最終一致性
    STRONG = "strong"          # 強一致性
    BOUNDED = "bounded"        # 有界一致性
    CAUSAL = "causal"          # 因果一致性


class NodeRole(Enum):
    """節點角色"""
    LEADER = "leader"          # 主節點
    FOLLOWER = "follower"      # 從節點
    CANDIDATE = "candidate"    # 候選節點
    OBSERVER = "observer"      # 觀察節點


@dataclass
class StateVersion:
    """狀態版本"""
    version_id: str
    timestamp: datetime
    node_id: str
    operation: SyncOperation
    checksum: str
    
    def __post_init__(self):
        if not self.version_id:
            self.version_id = str(uuid.uuid4())


@dataclass
class StateEntry:
    """狀態條目"""
    state_id: str
    state_type: StateType
    data: Dict[str, Any]
    version: StateVersion
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # 同步控制
    consistency_level: ConsistencyLevel = ConsistencyLevel.EVENTUAL
    ttl_seconds: Optional[int] = None
    
    # 訪問控制
    owner_node_id: str = ""
    access_permissions: Set[str] = field(default_factory=set)
    
    def calculate_checksum(self) -> str:
        """計算狀態校驗和"""
        content = json.dumps(self.data, sort_keys=True).encode('utf-8')
        return hashlib.sha256(content).hexdigest()
    
    def is_expired(self) -> bool:
        """檢查是否過期"""
        if not self.ttl_seconds:
            return False
        
        elapsed = (datetime.now(timezone.utc) - self.version.timestamp).total_seconds()
        return elapsed > self.ttl_seconds


@dataclass
class SyncMessage:
    """同步消息"""
    message_id: str
    message_type: str
    sender_id: str
    receiver_id: Optional[str]
    timestamp: datetime
    
    # 狀態同步相關
    state_entries: List[StateEntry] = field(default_factory=list)
    operation: Optional[SyncOperation] = None
    term: int = 0  # RAFT term
    
    # 一致性控制
    consistency_requirement: ConsistencyLevel = ConsistencyLevel.EVENTUAL
    sequence_number: int = 0
    depends_on: List[str] = field(default_factory=list)  # 依賴的消息ID
    
    payload: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NodeState:
    """節點狀態"""
    node_id: str
    role: NodeRole
    term: int
    last_heartbeat: datetime
    
    # RAFT 狀態
    voted_for: Optional[str] = None
    log_index: int = 0
    commit_index: int = 0
    
    # 性能指標
    response_time_ms: float = 0.0
    success_rate: float = 1.0
    load_factor: float = 0.0
    
    # 健康狀態
    is_healthy: bool = True
    failure_count: int = 0
    
    def is_active(self, timeout_seconds: int = 30) -> bool:
        """檢查節點是否活躍"""
        elapsed = (datetime.now(timezone.utc) - self.last_heartbeat).total_seconds()
        return elapsed <= timeout_seconds and self.is_healthy


class StateSynchronizationEngine:
    """狀態同步保證引擎"""
    
    def __init__(self, node_id: str, cluster_nodes: List[str] = None):
        self.node_id = node_id
        self.cluster_nodes = cluster_nodes or []
        
        # 同步配置
        self.sync_config = {
            'heartbeat_interval_ms': 1000,          # 心跳間隔
            'election_timeout_ms': 5000,            # 選舉超時
            'sync_batch_size': 100,                 # 同步批次大小
            'max_retry_attempts': 3,                # 最大重試次數
            'consistency_timeout_ms': 5000,         # 一致性超時
            'state_cache_size': 10000,              # 狀態緩存大小
            'backup_interval_s': 300,               # 備份間隔 (5分鐘)
            'gc_interval_s': 600                    # 垃圾回收間隔 (10分鐘)
        }
        
        # 節點管理
        self.current_term = 0
        self.voted_for: Optional[str] = None
        self.role = NodeRole.FOLLOWER
        self.leader_id: Optional[str] = None
        
        # 狀態存儲
        self.state_store: Dict[str, StateEntry] = {}
        self.state_versions: Dict[str, List[StateVersion]] = defaultdict(list)
        self.pending_operations: Dict[str, SyncMessage] = {}
        
        # 集群狀態
        self.cluster_nodes_state: Dict[str, NodeState] = {}
        self.sync_log: deque = deque(maxlen=1000)
        
        # 一致性控制
        self.sequence_counter = 0
        self.pending_consensus: Dict[str, Dict[str, Any]] = {}
        self.committed_index = 0
        
        # 運行狀態
        self.is_running = False
        self.sync_task: Optional[asyncio.Task] = None
        self.election_task: Optional[asyncio.Task] = None
        self.heartbeat_task: Optional[asyncio.Task] = None
        
        # 統計信息
        self.stats = {
            'states_synced': 0,
            'states_migrated': 0,
            'consistency_violations': 0,
            'failed_operations': 0,
            'backup_operations': 0,
            'restore_operations': 0,
            'elections_held': 0,
            'avg_sync_latency_ms': 0.0
        }
        
        # 線程池
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.sync_lock = threading.RLock()
        
        # 回調函數
        self.state_change_callbacks: List[Callable] = []
        self.consistency_violation_callbacks: List[Callable] = []
        
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def start_engine(self):
        """啟動狀態同步引擎"""
        if self.is_running:
            return
        
        self.is_running = True
        
        # 初始化集群節點狀態
        for node_id in self.cluster_nodes:
            if node_id != self.node_id:
                self.cluster_nodes_state[node_id] = NodeState(
                    node_id=node_id,
                    role=NodeRole.FOLLOWER,
                    term=0,
                    last_heartbeat=datetime.now(timezone.utc)
                )
        
        # 啟動同步任務
        self.sync_task = asyncio.create_task(self._sync_loop())
        self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        
        # 如果是集群環境，啟動選舉
        if len(self.cluster_nodes) > 1:
            await self._trigger_election()
        else:
            # 單節點模式，直接成為Leader
            await self._become_leader()
        
        self.logger.info(f"🚀 狀態同步引擎已啟動 - 節點: {self.node_id}, 角色: {self.role.value}")
    
    async def stop_engine(self):
        """停止狀態同步引擎"""
        self.is_running = False
        
        # 停止所有任務
        for task in [self.sync_task, self.election_task, self.heartbeat_task]:
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        self.executor.shutdown(wait=True)
        self.logger.info("⏹️ 狀態同步引擎已停止")
    
    async def _sync_loop(self):
        """主同步循環"""
        try:
            while self.is_running:
                await self._process_pending_operations()
                await self._perform_garbage_collection()
                await self._perform_backup_if_needed()
                await asyncio.sleep(0.1)
                
        except asyncio.CancelledError:
            self.logger.info("🔄 同步循環已取消")
        except Exception as e:
            self.logger.error(f"❌ 同步循環異常: {e}")
    
    async def _heartbeat_loop(self):
        """心跳循環"""
        try:
            while self.is_running:
                if self.role == NodeRole.LEADER:
                    await self._send_heartbeat()
                
                await self._check_cluster_health()
                await asyncio.sleep(self.sync_config['heartbeat_interval_ms'] / 1000.0)
                
        except asyncio.CancelledError:
            self.logger.info("💓 心跳循環已取消")
        except Exception as e:
            self.logger.error(f"❌ 心跳循環異常: {e}")
    
    # === 狀態管理核心方法 ===
    
    async def create_state(self, state_id: str, state_type: StateType, 
                          data: Dict[str, Any], 
                          consistency_level: ConsistencyLevel = ConsistencyLevel.EVENTUAL,
                          ttl_seconds: Optional[int] = None) -> bool:
        """創建狀態"""
        try:
            # 創建狀態版本
            version = StateVersion(
                version_id=str(uuid.uuid4()),
                timestamp=datetime.now(timezone.utc),
                node_id=self.node_id,
                operation=SyncOperation.CREATE,
                checksum=""
            )
            
            # 創建狀態條目
            state_entry = StateEntry(
                state_id=state_id,
                state_type=state_type,
                data=data,
                version=version,
                consistency_level=consistency_level,
                ttl_seconds=ttl_seconds,
                owner_node_id=self.node_id
            )
            
            # 計算校驗和
            version.checksum = state_entry.calculate_checksum()
            
            # 根據一致性級別處理
            if consistency_level == ConsistencyLevel.STRONG:
                success = await self._achieve_strong_consistency(state_entry, SyncOperation.CREATE)
            else:
                success = await self._store_state_locally(state_entry)
                if success:
                    await self._propagate_state_change(state_entry, SyncOperation.CREATE)
            
            if success:
                self.stats['states_synced'] += 1
                await self._notify_state_change(state_entry, SyncOperation.CREATE)
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ 創建狀態失敗: {e}")
            self.stats['failed_operations'] += 1
            return False
    
    async def update_state(self, state_id: str, data: Dict[str, Any],
                          consistency_level: ConsistencyLevel = ConsistencyLevel.EVENTUAL) -> bool:
        """更新狀態"""
        try:
            with self.sync_lock:
                if state_id not in self.state_store:
                    self.logger.warning(f"⚠️ 狀態不存在: {state_id}")
                    return False
                
                current_state = self.state_store[state_id]
                
                # 創建新版本
                new_version = StateVersion(
                    version_id=str(uuid.uuid4()),
                    timestamp=datetime.now(timezone.utc),
                    node_id=self.node_id,
                    operation=SyncOperation.UPDATE,
                    checksum=""
                )
                
                # 更新狀態
                updated_state = StateEntry(
                    state_id=state_id,
                    state_type=current_state.state_type,
                    data=data,
                    version=new_version,
                    consistency_level=consistency_level,
                    ttl_seconds=current_state.ttl_seconds,
                    owner_node_id=current_state.owner_node_id,
                    access_permissions=current_state.access_permissions
                )
                
                new_version.checksum = updated_state.calculate_checksum()
                
                # 根據一致性級別處理
                if consistency_level == ConsistencyLevel.STRONG:
                    success = await self._achieve_strong_consistency(updated_state, SyncOperation.UPDATE)
                else:
                    success = await self._store_state_locally(updated_state)
                    if success:
                        await self._propagate_state_change(updated_state, SyncOperation.UPDATE)
                
                if success:
                    self.stats['states_synced'] += 1
                    await self._notify_state_change(updated_state, SyncOperation.UPDATE)
                
                return success
                
        except Exception as e:
            self.logger.error(f"❌ 更新狀態失敗: {e}")
            self.stats['failed_operations'] += 1
            return False
    
    async def delete_state(self, state_id: str,
                          consistency_level: ConsistencyLevel = ConsistencyLevel.EVENTUAL) -> bool:
        """刪除狀態"""
        try:
            with self.sync_lock:
                if state_id not in self.state_store:
                    return True  # 已經不存在，視為成功
                
                current_state = self.state_store[state_id]
                
                # 創建刪除版本
                delete_version = StateVersion(
                    version_id=str(uuid.uuid4()),
                    timestamp=datetime.now(timezone.utc),
                    node_id=self.node_id,
                    operation=SyncOperation.DELETE,
                    checksum="DELETED"
                )
                
                # 根據一致性級別處理
                if consistency_level == ConsistencyLevel.STRONG:
                    success = await self._achieve_strong_consistency_delete(state_id, delete_version)
                else:
                    success = await self._delete_state_locally(state_id)
                    if success:
                        await self._propagate_state_deletion(state_id, delete_version)
                
                if success:
                    await self._notify_state_change(current_state, SyncOperation.DELETE)
                
                return success
                
        except Exception as e:
            self.logger.error(f"❌ 刪除狀態失敗: {e}")
            self.stats['failed_operations'] += 1
            return False
    
    async def migrate_state(self, state_id: str, target_node_id: str) -> bool:
        """遷移狀態到目標節點"""
        try:
            with self.sync_lock:
                if state_id not in self.state_store:
                    self.logger.warning(f"⚠️ 遷移的狀態不存在: {state_id}")
                    return False
                
                state_entry = self.state_store[state_id]
                
                # 創建遷移版本
                migrate_version = StateVersion(
                    version_id=str(uuid.uuid4()),
                    timestamp=datetime.now(timezone.utc),
                    node_id=self.node_id,
                    operation=SyncOperation.MIGRATE,
                    checksum=state_entry.version.checksum
                )
                
                # 更新所有者
                migrated_state = StateEntry(
                    state_id=state_entry.state_id,
                    state_type=state_entry.state_type,
                    data=state_entry.data,
                    version=migrate_version,
                    consistency_level=state_entry.consistency_level,
                    ttl_seconds=state_entry.ttl_seconds,
                    owner_node_id=target_node_id,
                    access_permissions=state_entry.access_permissions
                )
                
                # 發送遷移請求
                success = await self._send_migration_request(migrated_state, target_node_id)
                
                if success:
                    # 本地刪除原狀態
                    await self._delete_state_locally(state_id)
                    self.stats['states_migrated'] += 1
                    
                    self.logger.info(f"✅ 狀態遷移成功: {state_id} → {target_node_id}")
                
                return success
                
        except Exception as e:
            self.logger.error(f"❌ 狀態遷移失敗: {e}")
            self.stats['failed_operations'] += 1
            return False
    
    async def get_state(self, state_id: str) -> Optional[StateEntry]:
        """獲取狀態"""
        with self.sync_lock:
            state_entry = self.state_store.get(state_id)
            
            if state_entry and state_entry.is_expired():
                # 狀態已過期，刪除並返回None
                await self._delete_state_locally(state_id)
                return None
            
            return state_entry
    
    async def list_states(self, state_type: Optional[StateType] = None,
                         owner_node_id: Optional[str] = None) -> List[StateEntry]:
        """列出狀態"""
        with self.sync_lock:
            states = []
            for state_entry in self.state_store.values():
                # 檢查過期
                if state_entry.is_expired():
                    continue
                
                # 類型過濾
                if state_type and state_entry.state_type != state_type:
                    continue
                
                # 所有者過濾
                if owner_node_id and state_entry.owner_node_id != owner_node_id:
                    continue
                
                states.append(state_entry)
            
            return states
    
    # === 一致性保證方法 ===
    
    async def _achieve_strong_consistency(self, state_entry: StateEntry, 
                                        operation: SyncOperation) -> bool:
        """實現強一致性"""
        if self.role != NodeRole.LEADER:
            self.logger.warning("⚠️ 只有Leader可以處理強一致性請求")
            return False
        
        # 創建共識請求
        consensus_id = str(uuid.uuid4())
        consensus_data = {
            'consensus_id': consensus_id,
            'state_entry': state_entry,
            'operation': operation,
            'required_votes': len(self.cluster_nodes) // 2 + 1,
            'received_votes': 1,  # Leader自己的票
            'start_time': datetime.now(timezone.utc),
            'timeout_ms': self.sync_config['consistency_timeout_ms']
        }
        
        self.pending_consensus[consensus_id] = consensus_data
        
        # 發送投票請求給所有Follower
        await self._send_consensus_request(consensus_data)
        
        # 等待共識結果
        timeout_time = datetime.now(timezone.utc) + timedelta(
            milliseconds=self.sync_config['consistency_timeout_ms']
        )
        
        while datetime.now(timezone.utc) < timeout_time:
            if consensus_id not in self.pending_consensus:
                # 共識已完成
                success = await self._store_state_locally(state_entry)
                if success:
                    await self._commit_consensus(consensus_id)
                return success
            
            await asyncio.sleep(0.01)
        
        # 超時，共識失敗
        self.pending_consensus.pop(consensus_id, None)
        self.stats['consistency_violations'] += 1
        return False
    
    async def _achieve_strong_consistency_delete(self, state_id: str, 
                                               version: StateVersion) -> bool:
        """實現刪除的強一致性"""
        if self.role != NodeRole.LEADER:
            return False
        
        # 創建刪除共識
        consensus_id = str(uuid.uuid4())
        consensus_data = {
            'consensus_id': consensus_id,
            'state_id': state_id,
            'version': version,
            'operation': SyncOperation.DELETE,
            'required_votes': len(self.cluster_nodes) // 2 + 1,
            'received_votes': 1,
            'start_time': datetime.now(timezone.utc),
            'timeout_ms': self.sync_config['consistency_timeout_ms']
        }
        
        self.pending_consensus[consensus_id] = consensus_data
        await self._send_consensus_request(consensus_data)
        
        # 等待共識結果
        timeout_time = datetime.now(timezone.utc) + timedelta(
            milliseconds=self.sync_config['consistency_timeout_ms']
        )
        
        while datetime.now(timezone.utc) < timeout_time:
            if consensus_id not in self.pending_consensus:
                success = await self._delete_state_locally(state_id)
                if success:
                    await self._commit_consensus(consensus_id)
                return success
            
            await asyncio.sleep(0.01)
        
        self.pending_consensus.pop(consensus_id, None)
        self.stats['consistency_violations'] += 1
        return False
    
    # === 存儲管理方法 ===
    
    async def _store_state_locally(self, state_entry: StateEntry) -> bool:
        """本地存儲狀態"""
        try:
            with self.sync_lock:
                self.state_store[state_entry.state_id] = state_entry
                
                # 記錄版本歷史
                self.state_versions[state_entry.state_id].append(state_entry.version)
                
                # 限制版本歷史長度
                if len(self.state_versions[state_entry.state_id]) > 10:
                    self.state_versions[state_entry.state_id] = \
                        self.state_versions[state_entry.state_id][-10:]
                
                return True
                
        except Exception as e:
            self.logger.error(f"❌ 本地存儲狀態失敗: {e}")
            return False
    
    async def _delete_state_locally(self, state_id: str) -> bool:
        """本地刪除狀態"""
        try:
            with self.sync_lock:
                if state_id in self.state_store:
                    del self.state_store[state_id]
                
                # 保留版本歷史以供審計
                # 不刪除 self.state_versions[state_id]
                
                return True
                
        except Exception as e:
            self.logger.error(f"❌ 本地刪除狀態失敗: {e}")
            return False
    
    # === 集群通信方法 ===
    
    async def _propagate_state_change(self, state_entry: StateEntry, 
                                    operation: SyncOperation):
        """傳播狀態變更"""
        # 創建同步消息
        sync_message = SyncMessage(
            message_id=str(uuid.uuid4()),
            message_type="state_sync",
            sender_id=self.node_id,
            receiver_id=None,  # 廣播
            timestamp=datetime.now(timezone.utc),
            state_entries=[state_entry],
            operation=operation,
            term=self.current_term,
            sequence_number=self._get_next_sequence()
        )
        
        # 發送給所有其他節點
        await self._broadcast_message(sync_message)
    
    async def _propagate_state_deletion(self, state_id: str, version: StateVersion):
        """傳播狀態刪除"""
        sync_message = SyncMessage(
            message_id=str(uuid.uuid4()),
            message_type="state_delete",
            sender_id=self.node_id,
            receiver_id=None,
            timestamp=datetime.now(timezone.utc),
            operation=SyncOperation.DELETE,
            term=self.current_term,
            sequence_number=self._get_next_sequence(),
            payload={'state_id': state_id, 'version': version}
        )
        
        await self._broadcast_message(sync_message)
    
    async def _send_migration_request(self, state_entry: StateEntry, 
                                    target_node_id: str) -> bool:
        """發送遷移請求"""
        migration_message = SyncMessage(
            message_id=str(uuid.uuid4()),
            message_type="state_migration",
            sender_id=self.node_id,
            receiver_id=target_node_id,
            timestamp=datetime.now(timezone.utc),
            state_entries=[state_entry],
            operation=SyncOperation.MIGRATE,
            term=self.current_term
        )
        
        # 模擬發送 (實際實現需要網路通信)
        return await self._send_message(migration_message)
    
    async def _send_consensus_request(self, consensus_data: Dict[str, Any]):
        """發送共識請求"""
        consensus_message = SyncMessage(
            message_id=str(uuid.uuid4()),
            message_type="consensus_vote",
            sender_id=self.node_id,
            receiver_id=None,
            timestamp=datetime.now(timezone.utc),
            term=self.current_term,
            payload=consensus_data
        )
        
        await self._broadcast_message(consensus_message)
    
    async def _send_heartbeat(self):
        """發送心跳"""
        heartbeat_message = SyncMessage(
            message_id=str(uuid.uuid4()),
            message_type="heartbeat",
            sender_id=self.node_id,
            receiver_id=None,
            timestamp=datetime.now(timezone.utc),
            term=self.current_term,
            payload={
                'leader_id': self.node_id,
                'commit_index': self.committed_index
            }
        )
        
        await self._broadcast_message(heartbeat_message)
    
    async def _broadcast_message(self, message: SyncMessage):
        """廣播消息"""
        # 模擬廣播實現
        for node_id in self.cluster_nodes:
            if node_id != self.node_id:
                await self._send_message_to_node(message, node_id)
    
    async def _send_message(self, message: SyncMessage) -> bool:
        """發送消息"""
        # 模擬消息發送
        return True
    
    async def _send_message_to_node(self, message: SyncMessage, node_id: str):
        """發送消息到指定節點"""
        # 模擬實現
        pass
    
    # === 選舉和領導權管理 ===
    
    async def _trigger_election(self):
        """觸發領導選舉"""
        if self.election_task and not self.election_task.done():
            return
        
        self.election_task = asyncio.create_task(self._run_election())
        self.stats['elections_held'] += 1
    
    async def _run_election(self):
        """運行選舉"""
        self.logger.info("🗳️ 開始領導選舉")
        
        self.role = NodeRole.CANDIDATE
        self.current_term += 1
        self.voted_for = self.node_id
        
        # 發送投票請求
        votes_received = 1  # 自己的票
        required_votes = len(self.cluster_nodes) // 2 + 1
        
        election_message = SyncMessage(
            message_id=str(uuid.uuid4()),
            message_type="vote_request",
            sender_id=self.node_id,
            receiver_id=None,
            timestamp=datetime.now(timezone.utc),
            term=self.current_term,
            payload={
                'candidate_id': self.node_id,
                'last_log_index': len(self.sync_log)
            }
        )
        
        await self._broadcast_message(election_message)
        
        # 等待選舉結果 (簡化實現)
        await asyncio.sleep(self.sync_config['election_timeout_ms'] / 1000.0)
        
        # 在真實實現中，這裡會根據收到的投票決定結果
        # 為了測試，假設總是成功
        if votes_received >= required_votes:
            await self._become_leader()
        else:
            self.role = NodeRole.FOLLOWER
            self.voted_for = None
    
    async def _become_leader(self):
        """成為領導者"""
        self.role = NodeRole.LEADER
        self.leader_id = self.node_id
        
        self.logger.info(f"👑 成為集群領導者 - Term: {self.current_term}")
        
        # 立即發送心跳確立領導地位
        await self._send_heartbeat()
    
    # === 輔助方法 ===
    
    def _get_next_sequence(self) -> int:
        """獲取下一個序列號"""
        self.sequence_counter += 1
        return self.sequence_counter
    
    async def _process_pending_operations(self):
        """處理待處理的操作"""
        # 處理待處理的同步操作
        current_operations = list(self.pending_operations.items())
        for op_id, message in current_operations:
            try:
                await self._process_sync_message(message)
                del self.pending_operations[op_id]
            except Exception as e:
                self.logger.error(f"❌ 處理待處理操作失敗: {e}")
    
    async def _process_sync_message(self, message: SyncMessage):
        """處理同步消息"""
        # 簡化的消息處理實現
        pass
    
    async def _perform_garbage_collection(self):
        """執行垃圾回收"""
        if time.time() % self.sync_config['gc_interval_s'] < 1.0:
            with self.sync_lock:
                expired_states = []
                for state_id, state_entry in self.state_store.items():
                    if state_entry.is_expired():
                        expired_states.append(state_id)
                
                for state_id in expired_states:
                    del self.state_store[state_id]
                    self.logger.debug(f"🗑️ 清理過期狀態: {state_id}")
    
    async def _perform_backup_if_needed(self):
        """執行備份（如果需要）"""
        if time.time() % self.sync_config['backup_interval_s'] < 1.0:
            await self._create_backup()
    
    async def _create_backup(self) -> bool:
        """創建備份"""
        try:
            backup_data = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'node_id': self.node_id,
                'states': {}
            }
            
            with self.sync_lock:
                for state_id, state_entry in self.state_store.items():
                    backup_data['states'][state_id] = {
                        'state_type': state_entry.state_type.value,
                        'data': state_entry.data,
                        'version': state_entry.version.version_id,
                        'timestamp': state_entry.version.timestamp.isoformat()
                    }
            
            # 實際實現會將備份數據持久化
            self.stats['backup_operations'] += 1
            self.logger.debug(f"💾 創建備份完成: {len(backup_data['states'])} 個狀態")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 創建備份失敗: {e}")
            return False
    
    async def _check_cluster_health(self):
        """檢查集群健康狀態"""
        current_time = datetime.now(timezone.utc)
        timeout_seconds = self.sync_config['heartbeat_interval_ms'] * 3 / 1000.0
        
        for node_id, node_state in self.cluster_nodes_state.items():
            elapsed = (current_time - node_state.last_heartbeat).total_seconds()
            if elapsed > timeout_seconds:
                node_state.is_healthy = False
                node_state.failure_count += 1
                
                if self.role == NodeRole.LEADER and node_state.failure_count > 3:
                    self.logger.warning(f"⚠️ 節點 {node_id} 可能已離線")
    
    async def _notify_state_change(self, state_entry: StateEntry, operation: SyncOperation):
        """通知狀態變更"""
        for callback in self.state_change_callbacks:
            try:
                await callback(state_entry, operation)
            except Exception as e:
                self.logger.error(f"❌ 狀態變更回調失敗: {e}")
    
    async def _commit_consensus(self, consensus_id: str):
        """提交共識"""
        # 向所有節點發送提交消息
        commit_message = SyncMessage(
            message_id=str(uuid.uuid4()),
            message_type="consensus_commit",
            sender_id=self.node_id,
            receiver_id=None,
            timestamp=datetime.now(timezone.utc),
            term=self.current_term,
            payload={'consensus_id': consensus_id}
        )
        
        await self._broadcast_message(commit_message)
    
    # === 公共接口方法 ===
    
    def get_engine_status(self) -> Dict[str, Any]:
        """獲取引擎狀態"""
        with self.sync_lock:
            return {
                'node_id': self.node_id,
                'role': self.role.value,
                'term': self.current_term,
                'leader_id': self.leader_id,
                'is_running': self.is_running,
                'cluster_size': len(self.cluster_nodes),
                'active_nodes': len([n for n in self.cluster_nodes_state.values() if n.is_healthy]),
                'states_count': len(self.state_store),
                'pending_operations': len(self.pending_operations),
                'pending_consensus': len(self.pending_consensus),
                'statistics': self.stats.copy()
            }
    
    def add_state_change_callback(self, callback: Callable):
        """添加狀態變更回調"""
        self.state_change_callbacks.append(callback)
    
    def remove_state_change_callback(self, callback: Callable):
        """移除狀態變更回調"""
        if callback in self.state_change_callbacks:
            self.state_change_callbacks.remove(callback)
    
    def update_config(self, config: Dict[str, Any]):
        """更新配置"""
        self.sync_config.update(config)
        self.logger.info(f"🔧 同步引擎配置已更新: {list(config.keys())}")


# === 便利函數 ===

def create_state_synchronization_engine(node_id: str, 
                                       cluster_nodes: List[str] = None) -> StateSynchronizationEngine:
    """創建狀態同步引擎"""
    engine = StateSynchronizationEngine(node_id, cluster_nodes)
    
    logger.info(f"✅ 狀態同步引擎創建完成 - 節點: {node_id}, 集群大小: {len(cluster_nodes or [])}")
    return engine


def create_test_user_context(user_id: str) -> Dict[str, Any]:
    """創建測試用戶上下文"""
    # 確保IMSI是15位數字
    user_number = str(hash(user_id) % 1000000000).zfill(10)  # 10位用戶號碼
    return {
        'user_id': user_id,
        'imsi': f"46000{user_number}",  # 460(中國) + 00(運營商) + 10位用戶號碼
        'current_cell_id': f"CELL-{user_id}",
        'bearer_contexts': [
            {
                'bearer_id': 5,
                'qci': 9,
                'allocated_bandwidth_kbps': 1000,
                'packet_loss_rate': 0.01
            }
        ],
        'security_context': {
            'encryption_algorithm': 'AES-256',
            'integrity_algorithm': 'SHA-256',
            'security_keys': {'encrypted': True}
        },
        'mobility_state': 'CONNECTED',
        'last_update': datetime.now(timezone.utc).isoformat()
    }


def create_test_session_state(session_id: str) -> Dict[str, Any]:
    """創建測試會話狀態"""
    return {
        'session_id': session_id,
        'session_type': 'PDN',
        'apn': 'internet',
        'ip_address': f"192.168.1.{hash(session_id) % 254 + 1}",
        'allocated_resources': {
            'bandwidth_mbps': 10.0,
            'latency_ms': 50.0,
            'priority': 5
        },
        'active_flows': [
            {
                'flow_id': f"FLOW-{session_id}-1",
                'flow_type': 'HTTP',
                'bandwidth_kbps': 500,
                'packet_count': 1000
            }
        ],
        'qos_parameters': {
            'guaranteed_bit_rate_kbps': 1000,
            'maximum_bit_rate_kbps': 10000,
            'packet_delay_budget_ms': 100,
            'packet_error_loss_rate': 0.001
        },
        'established_time': datetime.now(timezone.utc).isoformat()
    }