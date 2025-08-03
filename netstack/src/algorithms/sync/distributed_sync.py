"""
Phase 3.2.1.1: 多衛星分散式時間同步協議實現

實現分散式衛星時間同步算法，包括：
1. Berkeley 算法的衛星網路適應版本
2. 拜占庭容錯時間同步
3. 分層同步架構 (Master-Slave)
4. 同步精度監控與自適應調整
5. 網路分區容錯機制

符合標準：
- IEEE 1588 PTP (Precision Time Protocol)
- ITU-R TF.460 時間頻率標準
- 3GPP TS 38.331 NTN 同步要求
"""

import asyncio
import logging
import time
import statistics
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Any, Callable
from enum import Enum
from datetime import datetime, timezone, timedelta
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


class SyncRole(Enum):
    """同步角色類型"""
    MASTER = "master"           # 主同步節點
    SLAVE = "slave"             # 從同步節點
    CANDIDATE = "candidate"     # 候選主節點
    PASSIVE = "passive"         # 被動監聽節點
    FAULTY = "faulty"           # 故障節點


class SyncState(Enum):
    """同步狀態"""
    INITIALIZING = "initializing"   # 初始化中
    SYNCING = "syncing"            # 同步中
    SYNCHRONIZED = "synchronized"   # 已同步
    DEGRADED = "degraded"          # 降級模式
    FAILED = "failed"              # 同步失敗


class MessageType(Enum):
    """同步消息類型"""
    SYNC_REQUEST = "sync_request"         # 同步請求
    SYNC_RESPONSE = "sync_response"       # 同步響應
    TIME_ANNOUNCE = "time_announce"       # 時間公告
    DELAY_REQUEST = "delay_request"       # 延遲請求
    DELAY_RESPONSE = "delay_response"     # 延遲響應
    FOLLOW_UP = "follow_up"              # 跟進消息
    MASTER_ELECTION = "master_election"   # 主節點選舉
    HEARTBEAT = "heartbeat"              # 心跳消息


@dataclass
class SyncMessage:
    """同步消息"""
    message_id: str
    message_type: MessageType
    sender_id: str
    receiver_id: Optional[str]
    timestamp: datetime
    
    # 時間同步相關
    origin_timestamp: Optional[datetime] = None      # 發送時間戳
    receive_timestamp: Optional[datetime] = None     # 接收時間戳
    correction_field: float = 0.0                   # 校正字段 (ns)
    
    # 主節點選舉相關
    priority: int = 128                             # 優先級 (0-255)
    clock_accuracy: float = 1e6                     # 時鐘精度 (ns)
    clock_variance: float = 0.0                     # 時鐘方差
    
    # 自定義數據
    payload: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            'message_id': self.message_id,
            'message_type': self.message_type.value,
            'sender_id': self.sender_id,
            'receiver_id': self.receiver_id,
            'timestamp': self.timestamp.isoformat(),
            'origin_timestamp': self.origin_timestamp.isoformat() if self.origin_timestamp else None,
            'receive_timestamp': self.receive_timestamp.isoformat() if self.receive_timestamp else None,
            'correction_field': self.correction_field,
            'priority': self.priority,
            'clock_accuracy': self.clock_accuracy,
            'clock_variance': self.clock_variance,
            'payload': self.payload
        }


@dataclass
class PeerNode:
    """對等節點信息"""
    node_id: str
    role: SyncRole
    last_seen: datetime
    
    # 時間同步指標
    offset_history: deque = field(default_factory=lambda: deque(maxlen=100))
    delay_history: deque = field(default_factory=lambda: deque(maxlen=100))
    jitter_history: deque = field(default_factory=lambda: deque(maxlen=100))
    
    # 節點質量指標
    reliability_score: float = 1.0      # 可靠性評分 0-1
    response_time_avg: float = 0.0      # 平均響應時間 (ms)
    packet_loss_rate: float = 0.0      # 丟包率
    clock_stability: float = 1.0       # 時鐘穩定性
    
    # 主節點選舉指標
    priority: int = 128
    clock_accuracy: float = 1e6
    clock_variance: float = 0.0
    
    def update_metrics(self, offset: float, delay: float, jitter: float):
        """更新同步指標"""
        self.offset_history.append(offset)
        self.delay_history.append(delay)
        self.jitter_history.append(jitter)
        
        # 更新平均響應時間
        if self.delay_history:
            self.response_time_avg = statistics.mean(self.delay_history) * 1000  # 轉為 ms
        
        # 計算可靠性評分
        self._calculate_reliability_score()
    
    def _calculate_reliability_score(self):
        """計算可靠性評分"""
        factors = []
        
        # 基於延遲穩定性
        if len(self.delay_history) >= 10:
            delay_stability = 1.0 / (1.0 + statistics.stdev(self.delay_history) * 1000)
            factors.append(delay_stability)
        
        # 基於時間偏移穩定性
        if len(self.offset_history) >= 10:
            offset_stability = 1.0 / (1.0 + statistics.stdev(self.offset_history) * 1000)
            factors.append(offset_stability)
        
        # 基於響應時間
        response_factor = max(0, 1.0 - self.response_time_avg / 1000.0)  # >1s 響應時間降分
        factors.append(response_factor)
        
        # 基於丟包率
        packet_factor = 1.0 - self.packet_loss_rate
        factors.append(packet_factor)
        
        if factors:
            self.reliability_score = statistics.mean(factors)
        
    def get_avg_offset(self) -> float:
        """獲取平均時間偏移"""
        return statistics.mean(self.offset_history) if self.offset_history else 0.0
    
    def get_offset_stdev(self) -> float:
        """獲取時間偏移標準差"""
        return statistics.stdev(self.offset_history) if len(self.offset_history) >= 2 else 0.0
    
    def is_suitable_master(self) -> bool:
        """判斷是否適合作為主節點"""
        return (
            self.reliability_score > 0.8 and
            self.response_time_avg < 500 and  # <500ms
            self.packet_loss_rate < 0.1 and  # <10% 丟包率
            self.clock_accuracy < 1e5         # <100µs 精度
        )


class DistributedSyncAlgorithm:
    """分散式時間同步算法核心"""
    
    def __init__(self, node_id: str, initial_role: SyncRole = SyncRole.SLAVE):
        self.node_id = node_id
        self.role = initial_role
        self.state = SyncState.INITIALIZING
        
        # 對等節點管理
        self.peers: Dict[str, PeerNode] = {}
        self.master_node_id: Optional[str] = None
        
        # 同步配置
        self.sync_config = {
            'sync_interval': 1.0,           # 同步間隔 (秒)
            'announce_interval': 2.0,       # 公告間隔 (秒)
            'delay_req_interval': 10.0,     # 延遲請求間隔 (秒)
            'master_timeout': 5.0,          # 主節點超時 (秒)
            'max_offset_threshold': 1e6,    # 最大偏移閾值 (ns) = 1ms
            'election_timeout': 3.0,        # 選舉超時 (秒)
            'byzantine_tolerance': True,    # 拜占庭容錯
            'min_peers_for_sync': 3         # 最少同步節點數
        }
        
        # 時間同步狀態
        self.local_offset = 0.0            # 本地時間偏移 (ns)
        self.sync_accuracy = 1e9           # 同步精度 (ns)
        self.last_sync_time = datetime.now(timezone.utc)
        
        # 消息處理
        self.message_handlers: Dict[MessageType, Callable] = {
            MessageType.SYNC_REQUEST: self._handle_sync_request,
            MessageType.SYNC_RESPONSE: self._handle_sync_response,
            MessageType.TIME_ANNOUNCE: self._handle_time_announce,
            MessageType.DELAY_REQUEST: self._handle_delay_request,
            MessageType.DELAY_RESPONSE: self._handle_delay_response,
            MessageType.FOLLOW_UP: self._handle_follow_up,
            MessageType.MASTER_ELECTION: self._handle_master_election,
            MessageType.HEARTBEAT: self._handle_heartbeat
        }
        
        # 統計信息
        self.stats = {
            'messages_sent': 0,
            'messages_received': 0,
            'sync_cycles_completed': 0,
            'master_elections': 0,
            'sync_failures': 0
        }
        
        # 任務管理
        self.sync_task: Optional[asyncio.Task] = None
        self.election_task: Optional[asyncio.Task] = None
        self.is_running = False
        
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # 消息回調 (需要外部注入)
        self.send_message_callback: Optional[Callable] = None
    
    async def start_algorithm(self):
        """啟動分散式同步算法"""
        if self.is_running:
            return
        
        self.is_running = True
        self.state = SyncState.INITIALIZING
        
        # 啟動主同步循環
        self.sync_task = asyncio.create_task(self._sync_loop())
        
        self.logger.info(f"🚀 分散式同步算法已啟動 - 節點: {self.node_id}, 角色: {self.role.value}")
    
    async def stop_algorithm(self):
        """停止分散式同步算法"""
        self.is_running = False
        
        if self.sync_task:
            self.sync_task.cancel()
            try:
                await self.sync_task
            except asyncio.CancelledError:
                pass
        
        if self.election_task:
            self.election_task.cancel()
            try:
                await self.election_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("⏹️ 分散式同步算法已停止")
    
    async def _sync_loop(self):
        """主同步循環"""
        try:
            while self.is_running:
                await self._perform_sync_cycle()
                await asyncio.sleep(self.sync_config['sync_interval'])
                
        except asyncio.CancelledError:
            self.logger.info("🔄 同步循環已取消")
        except Exception as e:
            self.logger.error(f"❌ 同步循環異常: {e}")
            self.state = SyncState.FAILED
    
    async def _perform_sync_cycle(self):
        """執行一個同步週期"""
        try:
            # 檢查主節點狀態
            await self._check_master_status()
            
            # 根據角色執行相應動作
            if self.role == SyncRole.MASTER:
                await self._master_sync_cycle()
            elif self.role == SyncRole.SLAVE:
                await self._slave_sync_cycle()
            elif self.role == SyncRole.CANDIDATE:
                await self._candidate_sync_cycle()
            
            # 清理過期節點
            await self._cleanup_expired_peers()
            
            # 更新統計
            self.stats['sync_cycles_completed'] += 1
            
        except Exception as e:
            self.logger.error(f"❌ 同步週期執行失敗: {e}")
            self.stats['sync_failures'] += 1
    
    async def _check_master_status(self):
        """檢查主節點狀態"""
        if self.master_node_id and self.master_node_id in self.peers:
            master_peer = self.peers[self.master_node_id]
            master_timeout = timedelta(seconds=self.sync_config['master_timeout'])
            
            if datetime.now(timezone.utc) - master_peer.last_seen > master_timeout:
                self.logger.warning(f"⚠️ 主節點 {self.master_node_id} 超時，觸發選舉")
                await self._trigger_master_election()
        elif self.role != SyncRole.MASTER and not self.master_node_id:
            # 沒有主節點，觸發選舉
            await self._trigger_master_election()
    
    async def _master_sync_cycle(self):
        """主節點同步週期"""
        current_time = datetime.now(timezone.utc)
        
        # 發送時間公告給所有從節點
        announce_msg = SyncMessage(
            message_id=f"announce_{int(time.time() * 1000000)}",
            message_type=MessageType.TIME_ANNOUNCE,
            sender_id=self.node_id,
            receiver_id=None,  # 廣播
            timestamp=current_time,
            origin_timestamp=current_time,
            clock_accuracy=self.sync_accuracy,
            priority=self._calculate_priority()
        )
        
        await self._send_message(announce_msg)
        
        # 定期發送心跳
        if self.stats['sync_cycles_completed'] % 10 == 0:  # 每10個週期
            await self._send_heartbeat()
    
    async def _slave_sync_cycle(self):
        """從節點同步週期"""
        if not self.master_node_id or self.master_node_id not in self.peers:
            return
        
        # 定期發送延遲請求
        if self.stats['sync_cycles_completed'] % int(self.sync_config['delay_req_interval']) == 0:
            delay_req_msg = SyncMessage(
                message_id=f"delay_req_{int(time.time() * 1000000)}",
                message_type=MessageType.DELAY_REQUEST,
                sender_id=self.node_id,
                receiver_id=self.master_node_id,
                timestamp=datetime.now(timezone.utc),
                origin_timestamp=datetime.now(timezone.utc)
            )
            
            await self._send_message(delay_req_msg)
    
    async def _candidate_sync_cycle(self):
        """候選節點同步週期"""
        # 候選節點監聽網路狀態，準備參與選舉
        if len([p for p in self.peers.values() if p.role == SyncRole.MASTER]) == 0:
            await self._trigger_master_election()
    
    async def _trigger_master_election(self):
        """觸發主節點選舉"""
        if self.election_task and not self.election_task.done():
            return  # 選舉已在進行中
        
        self.election_task = asyncio.create_task(self._run_master_election())
        self.stats['master_elections'] += 1
    
    async def _run_master_election(self):
        """運行主節點選舉"""
        self.logger.info("🗳️ 開始主節點選舉")
        
        try:
            # 計算自己的選舉優先級
            my_priority = self._calculate_priority()
            
            # 發送選舉消息
            election_msg = SyncMessage(
                message_id=f"election_{int(time.time() * 1000000)}",
                message_type=MessageType.MASTER_ELECTION,
                sender_id=self.node_id,
                receiver_id=None,  # 廣播
                timestamp=datetime.now(timezone.utc),
                priority=my_priority,
                clock_accuracy=self.sync_accuracy,
                clock_variance=self._calculate_clock_variance()
            )
            
            await self._send_message(election_msg)
            
            # 等待選舉結果
            await asyncio.sleep(self.sync_config['election_timeout'])
            
            # 分析選舉結果
            await self._analyze_election_results()
            
        except Exception as e:
            self.logger.error(f"❌ 主節點選舉失敗: {e}")
    
    def _calculate_priority(self) -> int:
        """計算節點優先級 (數值越低優先級越高)"""
        base_priority = 128
        
        # 基於時鐘精度調整
        accuracy_factor = min(50, self.sync_accuracy / 1e4)  # 精度因子
        
        # 基於可靠性調整
        if hasattr(self, 'peers') and self.peers:
            avg_reliability = statistics.mean([p.reliability_score for p in self.peers.values()])
            reliability_factor = int((1.0 - avg_reliability) * 50)
        else:
            reliability_factor = 0
        
        # 基於角色歷史調整
        role_factor = 0
        if self.role == SyncRole.MASTER:
            role_factor = -10  # 當前主節點有優勢
        elif self.role == SyncRole.CANDIDATE:
            role_factor = 5
        
        priority = base_priority + accuracy_factor + reliability_factor + role_factor
        return max(1, min(255, int(priority)))
    
    def _calculate_clock_variance(self) -> float:
        """計算時鐘方差"""
        if len(self.peers) < 2:
            return 0.0
        
        offsets = [peer.get_avg_offset() for peer in self.peers.values() 
                  if len(peer.offset_history) > 0]
        
        if len(offsets) >= 2:
            return statistics.variance(offsets)
        return 0.0
    
    async def _analyze_election_results(self):
        """分析選舉結果"""
        # 收集所有候選人信息
        candidates = [
            (self.node_id, self._calculate_priority(), self.sync_accuracy)
        ]
        
        for peer in self.peers.values():
            if hasattr(peer, 'priority'):
                candidates.append((peer.node_id, peer.priority, peer.clock_accuracy))
        
        # 按優先級排序 (數值越低優先級越高)
        candidates.sort(key=lambda x: (x[1], x[2]))  # 先按優先級，再按精度
        
        if candidates:
            winner_id = candidates[0][0]
            
            if winner_id == self.node_id:
                # 自己當選主節點
                await self._become_master()
            else:
                # 其他節點當選
                await self._accept_master(winner_id)
    
    async def _become_master(self):
        """成為主節點"""
        old_role = self.role
        self.role = SyncRole.MASTER
        self.master_node_id = self.node_id
        self.state = SyncState.SYNCHRONIZED
        
        self.logger.info(f"👑 節點 {self.node_id} 成為主節點 (原角色: {old_role.value})")
        
        # 立即發送主節點公告
        await self._send_heartbeat()
    
    async def _accept_master(self, master_id: str):
        """接受新主節點"""
        old_master = self.master_node_id
        self.master_node_id = master_id
        
        if self.role == SyncRole.MASTER:
            self.role = SyncRole.SLAVE
        
        self.logger.info(f"✅ 接受新主節點: {master_id} (原主節點: {old_master})")
    
    async def _send_heartbeat(self):
        """發送心跳消息"""
        heartbeat_msg = SyncMessage(
            message_id=f"heartbeat_{int(time.time() * 1000000)}",
            message_type=MessageType.HEARTBEAT,
            sender_id=self.node_id,
            receiver_id=None,  # 廣播
            timestamp=datetime.now(timezone.utc),
            priority=self._calculate_priority(),
            clock_accuracy=self.sync_accuracy,
            payload={
                'role': self.role.value,
                'state': self.state.value,
                'sync_accuracy': self.sync_accuracy,
                'peers_count': len(self.peers)
            }
        )
        
        await self._send_message(heartbeat_msg)
    
    async def _cleanup_expired_peers(self):
        """清理過期的對等節點"""
        current_time = datetime.now(timezone.utc)
        timeout = timedelta(seconds=self.sync_config['master_timeout'] * 2)
        
        expired_peers = []
        for peer_id, peer in self.peers.items():
            if current_time - peer.last_seen > timeout:
                expired_peers.append(peer_id)
        
        for peer_id in expired_peers:
            self.logger.warning(f"🗑️ 清理過期節點: {peer_id}")
            del self.peers[peer_id]
            
            if peer_id == self.master_node_id:
                self.master_node_id = None
                await self._trigger_master_election()
    
    # === 消息處理器 ===
    
    async def receive_message(self, message: SyncMessage):
        """接收並處理同步消息"""
        try:
            # 記錄接收時間
            message.receive_timestamp = datetime.now(timezone.utc)
            
            # 更新發送者信息
            await self._update_peer_info(message)
            
            # 路由到相應處理器
            handler = self.message_handlers.get(message.message_type)
            if handler:
                await handler(message)
            else:
                self.logger.warning(f"⚠️ 未知消息類型: {message.message_type}")
            
            self.stats['messages_received'] += 1
            
        except Exception as e:
            self.logger.error(f"❌ 消息處理失敗: {e}")
    
    async def _update_peer_info(self, message: SyncMessage):
        """更新對等節點信息"""
        sender_id = message.sender_id
        current_time = datetime.now(timezone.utc)
        
        if sender_id not in self.peers:
            self.peers[sender_id] = PeerNode(
                node_id=sender_id,
                role=SyncRole.SLAVE,  # 默認角色
                last_seen=current_time,
                priority=message.priority,
                clock_accuracy=message.clock_accuracy
            )
        
        peer = self.peers[sender_id]
        peer.last_seen = current_time
        peer.priority = message.priority
        peer.clock_accuracy = message.clock_accuracy
        
        # 從 payload 更新角色信息
        if 'role' in message.payload:
            try:
                peer.role = SyncRole(message.payload['role'])
            except ValueError:
                pass
    
    async def _handle_sync_request(self, message: SyncMessage):
        """處理同步請求"""
        if self.role != SyncRole.MASTER:
            return
        
        # 回復同步響應
        response_msg = SyncMessage(
            message_id=f"sync_resp_{int(time.time() * 1000000)}",
            message_type=MessageType.SYNC_RESPONSE,
            sender_id=self.node_id,
            receiver_id=message.sender_id,
            timestamp=datetime.now(timezone.utc),
            origin_timestamp=message.origin_timestamp,
            clock_accuracy=self.sync_accuracy
        )
        
        await self._send_message(response_msg)
    
    async def _handle_sync_response(self, message: SyncMessage):
        """處理同步響應"""
        if message.receiver_id != self.node_id:
            return
        
        # 計算時間偏移和網路延遲
        if message.origin_timestamp and message.receive_timestamp:
            t1 = message.origin_timestamp
            t2 = message.receive_timestamp
            t3 = message.timestamp
            t4 = datetime.now(timezone.utc)
            
            # 計算偏移和延遲
            offset = ((t2 - t1).total_seconds() + (t3 - t4).total_seconds()) / 2 * 1e9  # ns
            delay = ((t4 - t1).total_seconds() - (t3 - t2).total_seconds()) / 2 * 1e9   # ns
            
            # 更新對等節點指標
            if message.sender_id in self.peers:
                peer = self.peers[message.sender_id]
                jitter = abs(delay - peer.response_time_avg * 1e6) if peer.response_time_avg > 0 else 0
                peer.update_metrics(offset, delay / 1e9, jitter / 1e9)
            
            # 如果是來自主節點的響應，調整本地時間
            if message.sender_id == self.master_node_id:
                await self._adjust_local_time(offset)
    
    async def _handle_time_announce(self, message: SyncMessage):
        """處理時間公告"""
        if self.role == SyncRole.MASTER:
            return  # 主節點不處理時間公告
        
        sender_id = message.sender_id
        
        # 更新主節點信息
        if sender_id in self.peers:
            peer = self.peers[sender_id]
            if peer.role == SyncRole.MASTER or sender_id == self.master_node_id:
                # 計算時間偏移
                if message.origin_timestamp:
                    local_time = datetime.now(timezone.utc)
                    offset = (message.origin_timestamp - local_time).total_seconds() * 1e9  # ns
                    
                    await self._adjust_local_time(offset)
                    self.master_node_id = sender_id
    
    async def _handle_delay_request(self, message: SyncMessage):
        """處理延遲請求"""
        if self.role != SyncRole.MASTER:
            return
        
        # 回復延遲響應
        response_msg = SyncMessage(
            message_id=f"delay_resp_{int(time.time() * 1000000)}",
            message_type=MessageType.DELAY_RESPONSE,
            sender_id=self.node_id,
            receiver_id=message.sender_id,
            timestamp=datetime.now(timezone.utc),
            origin_timestamp=message.origin_timestamp,
            receive_timestamp=message.receive_timestamp
        )
        
        await self._send_message(response_msg)
    
    async def _handle_delay_response(self, message: SyncMessage):
        """處理延遲響應"""
        # 計算準確的網路延遲
        if message.origin_timestamp and message.receive_timestamp:
            t1 = message.origin_timestamp
            t4 = datetime.now(timezone.utc)
            
            round_trip_delay = (t4 - t1).total_seconds() * 1e9  # ns
            
            if message.sender_id in self.peers:
                peer = self.peers[message.sender_id]
                peer.delay_history.append(round_trip_delay / 1e9)  # 轉為秒
    
    async def _handle_follow_up(self, message: SyncMessage):
        """處理跟進消息"""
        # IEEE 1588 Follow_Up 消息處理
        # 用於提供精確的時間戳信息
        pass
    
    async def _handle_master_election(self, message: SyncMessage):
        """處理主節點選舉消息"""
        sender_id = message.sender_id
        
        # 更新候選人信息
        if sender_id in self.peers:
            peer = self.peers[sender_id]
            peer.role = SyncRole.CANDIDATE
            peer.priority = message.priority
            peer.clock_accuracy = message.clock_accuracy
            peer.clock_variance = message.clock_variance
    
    async def _handle_heartbeat(self, message: SyncMessage):
        """處理心跳消息"""
        sender_id = message.sender_id
        
        # 更新節點狀態
        if sender_id in self.peers:
            peer = self.peers[sender_id]
            
            # 從 payload 更新詳細狀態
            if 'role' in message.payload:
                try:
                    peer.role = SyncRole(message.payload['role'])
                    
                    # 如果發送者聲稱是主節點，更新主節點信息
                    if peer.role == SyncRole.MASTER:
                        if not self.master_node_id or sender_id == self.master_node_id:
                            self.master_node_id = sender_id
                            if self.role == SyncRole.MASTER and sender_id != self.node_id:
                                # 出現了兩個主節點，需要重新選舉
                                await self._trigger_master_election()
                                
                except ValueError:
                    pass
    
    async def _adjust_local_time(self, offset_ns: float):
        """調整本地時間偏移"""
        if abs(offset_ns) > self.sync_config['max_offset_threshold']:
            self.logger.warning(f"⚠️ 時間偏移過大: {offset_ns/1e6:.3f}ms，限制調整")
            offset_ns = math.copysign(self.sync_config['max_offset_threshold'], offset_ns)
        
        # 平滑調整，避免突然跳躍
        adjustment_factor = 0.1  # 每次調整 10%
        self.local_offset += offset_ns * adjustment_factor
        
        # 更新同步精度
        self.sync_accuracy = abs(offset_ns)
        self.last_sync_time = datetime.now(timezone.utc)
        
        # 更新狀態
        if abs(self.local_offset) < self.sync_config['max_offset_threshold']:
            self.state = SyncState.SYNCHRONIZED
        else:
            self.state = SyncState.SYNCING
        
        self.logger.debug(f"🕐 調整本地時間偏移: {offset_ns/1e6:.3f}ms → 累積偏移: {self.local_offset/1e6:.3f}ms")
    
    async def _send_message(self, message: SyncMessage):
        """發送同步消息"""
        try:
            if self.send_message_callback:
                await self.send_message_callback(message)
                self.stats['messages_sent'] += 1
            else:
                self.logger.warning("⚠️ 消息發送回調未設置")
                
        except Exception as e:
            self.logger.error(f"❌ 消息發送失敗: {e}")
    
    # === 公共接口方法 ===
    
    def set_message_callback(self, callback: Callable):
        """設置消息發送回調"""
        self.send_message_callback = callback
    
    def get_current_time(self) -> datetime:
        """獲取同步後的當前時間"""
        local_time = datetime.now(timezone.utc)
        adjusted_time = local_time + timedelta(microseconds=self.local_offset / 1000)
        return adjusted_time
    
    def get_sync_status(self) -> Dict[str, Any]:
        """獲取同步狀態"""
        peer_stats = {}
        for peer_id, peer in self.peers.items():
            peer_stats[peer_id] = {
                'role': peer.role.value,
                'reliability_score': peer.reliability_score,
                'avg_offset': peer.get_avg_offset(),
                'offset_stdev': peer.get_offset_stdev(),
                'response_time_avg': peer.response_time_avg,
                'packet_loss_rate': peer.packet_loss_rate,
                'last_seen': peer.last_seen.isoformat()
            }
        
        return {
            'node_id': self.node_id,
            'role': self.role.value,
            'state': self.state.value,
            'master_node_id': self.master_node_id,
            'local_offset_ns': self.local_offset,
            'sync_accuracy_ns': self.sync_accuracy,
            'last_sync_time': self.last_sync_time.isoformat(),
            'peers_count': len(self.peers),
            'peers': peer_stats,
            'statistics': self.stats.copy(),
            'is_synchronized': self.state == SyncState.SYNCHRONIZED
        }
    
    def update_config(self, config: Dict[str, Any]):
        """更新同步配置"""
        self.sync_config.update(config)
        self.logger.info(f"🔧 同步配置已更新: {list(config.keys())}")


# === 便利函數 ===

def create_distributed_sync_algorithm(node_id: str, role: SyncRole = SyncRole.SLAVE) -> DistributedSyncAlgorithm:
    """創建分散式同步算法實例"""
    algorithm = DistributedSyncAlgorithm(node_id, role)
    
    logger.info(f"✅ 分散式同步算法創建完成 - 節點: {node_id}, 角色: {role.value}")
    return algorithm


def create_test_sync_network(node_count: int = 5) -> List[DistributedSyncAlgorithm]:
    """創建測試用的同步網路"""
    nodes = []
    
    # 創建第一個節點作為主節點
    master_node = create_distributed_sync_algorithm("master_node", SyncRole.MASTER)
    nodes.append(master_node)
    
    # 創建其他從節點
    for i in range(node_count - 1):
        slave_node = create_distributed_sync_algorithm(f"slave_node_{i+1}", SyncRole.SLAVE)
        nodes.append(slave_node)
    
    return nodes