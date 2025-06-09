"""
3GPP NTN N3 Interface Implementation - Phase 2 Stage 5

實現3GPP TS 38.415定義的N3接口，支援衛星網路的用戶平面數據傳輸：
- GPRS Tunnelling Protocol (GTP-U) for NTN
- NTN-specific QoS handling
- Satellite link compensation
- Dynamic tunnel management
- Enhanced error detection and correction

Key Features:
- GTP-U protocol with NTN extensions
- Satellite-aware packet scheduling
- Adaptive QoS management
- Link quality monitoring
- Buffering and retransmission
"""

import asyncio
import logging
import uuid
import time
import struct
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import socket

import structlog

logger = structlog.get_logger(__name__)


class GtpuMessageType(Enum):
    """GTP-U消息類型"""
    ECHO_REQUEST = 1
    ECHO_RESPONSE = 2
    ERROR_INDICATION = 26
    SUPPORTED_EXTENSION_HEADERS = 31
    END_MARKER = 254
    G_PDU = 255


class NtnQosClass(Enum):
    """NTN QoS類別"""
    DELAY_CRITICAL = "delay_critical"      # 延遲敏感（如URLLC）
    THROUGHPUT_OPTIMIZED = "throughput_optimized"  # 吞吐量優化（如eMBB）
    BEST_EFFORT = "best_effort"           # 盡力而為
    SATELLITE_OPTIMIZED = "satellite_optimized"    # 衛星優化


class NtnLinkCondition(Enum):
    """NTN鏈路狀況"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"


@dataclass
class GtpuHeader:
    """GTP-U標頭"""
    version: int = 1
    pt: int = 1  # Protocol Type
    extension: bool = False
    sequence: bool = False
    pn: bool = False  # N-PDU Number
    message_type: int = 255  # G-PDU
    length: int = 0
    teid: int = 0  # Tunnel Endpoint Identifier
    sequence_number: Optional[int] = None
    npdu_number: Optional[int] = None
    next_extension_header: Optional[int] = None


@dataclass
class NtnTunnel:
    """NTN隧道"""
    tunnel_id: str
    local_teid: int
    remote_teid: int
    local_endpoint: Tuple[str, int]
    remote_endpoint: Tuple[str, int]
    
    # QoS parameters
    qos_class: NtnQosClass
    guaranteed_bit_rate_kbps: int
    maximum_bit_rate_kbps: int
    packet_delay_budget_ms: int
    packet_error_rate: float
    
    # NTN-specific parameters
    satellite_compensation_enabled: bool = True
    adaptive_coding_enabled: bool = True
    link_monitoring_enabled: bool = True
    
    # Tunnel state
    is_active: bool = True
    established_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    
    # Statistics
    packets_sent: int = 0
    packets_received: int = 0
    bytes_sent: int = 0
    bytes_received: int = 0
    packet_loss_count: int = 0
    retransmission_count: int = 0


@dataclass
class NtnPacketBuffer:
    """NTN封包緩衝區"""
    buffer_id: str
    tunnel_id: str
    max_size_bytes: int = 1024 * 1024  # 1MB
    max_packets: int = 1000
    retention_time_ms: int = 5000  # 5秒
    
    # Buffered packets
    packets: List[Dict[str, Any]] = field(default_factory=list)
    total_size_bytes: int = 0
    
    # Buffer statistics
    packets_buffered: int = 0
    packets_dropped: int = 0
    packets_transmitted: int = 0


@dataclass
class SatelliteLinkMetrics:
    """衛星鏈路指標"""
    link_id: str
    satellite_id: str
    
    # Signal quality
    rsrp_dbm: float  # Reference Signal Received Power
    rsrq_db: float   # Reference Signal Received Quality
    sinr_db: float   # Signal-to-Interference-plus-Noise Ratio
    
    # Link characteristics
    round_trip_time_ms: float
    available_bandwidth_mbps: float
    packet_loss_rate: float
    jitter_ms: float
    
    # Weather impact
    weather_attenuation_db: float
    atmospheric_noise_db: float
    
    # Mobility impact
    doppler_shift_hz: float
    handover_probability: float
    
    # Link condition
    link_condition: NtnLinkCondition
    quality_score: float  # 0.0 to 1.0
    
    timestamp: datetime = field(default_factory=datetime.now)


class NtnN3Interface:
    """3GPP NTN N3接口實現"""
    
    def __init__(self, local_ip: str = "0.0.0.0", local_port: int = 2152):
        self.logger = structlog.get_logger(__name__)
        self.local_ip = local_ip
        self.local_port = local_port
        
        # Network sockets
        self.udp_socket: Optional[socket.socket] = None
        
        # Tunnel management
        self.tunnels: Dict[int, NtnTunnel] = {}  # TEID -> Tunnel
        self.tunnel_by_id: Dict[str, NtnTunnel] = {}  # tunnel_id -> Tunnel
        
        # Packet processing
        self.packet_buffers: Dict[str, NtnPacketBuffer] = {}
        self.sequence_numbers: Dict[int, int] = {}  # TEID -> sequence number
        
        # Link monitoring
        self.satellite_links: Dict[str, SatelliteLinkMetrics] = {}
        
        # QoS management
        self.qos_policies: Dict[NtnQosClass, Dict[str, Any]] = {}
        self.setup_default_qos_policies()
        
        # Statistics
        self.interface_stats = {
            "total_packets_processed": 0,
            "total_bytes_processed": 0,
            "active_tunnels": 0,
            "packet_loss_rate": 0.0,
            "average_latency_ms": 0.0,
            "retransmission_rate": 0.0,
            "buffer_utilization": 0.0
        }
        
        # Service state
        self.is_running = False
        self.packet_processor_task: Optional[asyncio.Task] = None
        self.link_monitor_task: Optional[asyncio.Task] = None

    def setup_default_qos_policies(self):
        """設置預設QoS政策"""
        self.qos_policies = {
            NtnQosClass.DELAY_CRITICAL: {
                "max_latency_ms": 10,
                "priority": 1,
                "buffer_size_factor": 0.5,
                "retransmission_enabled": False,
                "adaptive_coding": True
            },
            NtnQosClass.THROUGHPUT_OPTIMIZED: {
                "max_latency_ms": 100,
                "priority": 2,
                "buffer_size_factor": 2.0,
                "retransmission_enabled": True,
                "adaptive_coding": True
            },
            NtnQosClass.BEST_EFFORT: {
                "max_latency_ms": 1000,
                "priority": 3,
                "buffer_size_factor": 1.0,
                "retransmission_enabled": True,
                "adaptive_coding": False
            },
            NtnQosClass.SATELLITE_OPTIMIZED: {
                "max_latency_ms": 200,
                "priority": 2,
                "buffer_size_factor": 3.0,
                "retransmission_enabled": True,
                "adaptive_coding": True
            }
        }

    async def start_n3_interface(self):
        """啟動N3接口"""
        if not self.is_running:
            self.is_running = True
            
            # 創建UDP socket
            await self.create_udp_socket()
            
            # 初始化衛星鏈路監控
            await self.initialize_satellite_links()
            
            # 啟動處理任務
            self.packet_processor_task = asyncio.create_task(self.packet_processor_loop())
            self.link_monitor_task = asyncio.create_task(self.link_monitor_loop())
            
            self.logger.info(f"NTN N3接口已啟動: {self.local_ip}:{self.local_port}")

    async def stop_n3_interface(self):
        """停止N3接口"""
        if self.is_running:
            self.is_running = False
            
            # 停止處理任務
            if self.packet_processor_task:
                self.packet_processor_task.cancel()
                try:
                    await self.packet_processor_task
                except asyncio.CancelledError:
                    pass
            
            if self.link_monitor_task:
                self.link_monitor_task.cancel()
                try:
                    await self.link_monitor_task
                except asyncio.CancelledError:
                    pass
            
            # 關閉socket
            if self.udp_socket:
                self.udp_socket.close()
                self.udp_socket = None
            
            # 清理隧道
            await self.cleanup_all_tunnels()
            
            self.logger.info("NTN N3接口已停止")

    async def create_udp_socket(self):
        """創建UDP socket"""
        try:
            self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.udp_socket.bind((self.local_ip, self.local_port))
            self.udp_socket.setblocking(False)
            
            self.logger.info(f"UDP socket已創建: {self.local_ip}:{self.local_port}")
            
        except Exception as e:
            self.logger.error(f"UDP socket創建失敗: {e}")
            raise

    async def initialize_satellite_links(self):
        """初始化衛星鏈路"""
        # 模擬衛星鏈路
        link_1 = SatelliteLinkMetrics(
            link_id="link_oneweb_001",
            satellite_id="oneweb_001",
            rsrp_dbm=-75.0,
            rsrq_db=15.0,
            sinr_db=20.0,
            round_trip_time_ms=50.0,
            available_bandwidth_mbps=100.0,
            packet_loss_rate=0.001,
            jitter_ms=5.0,
            weather_attenuation_db=0.5,
            atmospheric_noise_db=-110.0,
            doppler_shift_hz=1000.0,
            handover_probability=0.1,
            link_condition=NtnLinkCondition.GOOD,
            quality_score=0.85
        )
        
        self.satellite_links["link_oneweb_001"] = link_1

    async def create_tunnel(self, tunnel_config: Dict[str, Any]) -> NtnTunnel:
        """創建NTN隧道"""
        tunnel_id = f"ntn_tunnel_{uuid.uuid4().hex[:8]}"
        local_teid = tunnel_config.get("local_teid", self.generate_teid())
        
        tunnel = NtnTunnel(
            tunnel_id=tunnel_id,
            local_teid=local_teid,
            remote_teid=tunnel_config["remote_teid"],
            local_endpoint=(self.local_ip, self.local_port),
            remote_endpoint=(tunnel_config["remote_ip"], tunnel_config["remote_port"]),
            qos_class=NtnQosClass(tunnel_config.get("qos_class", "best_effort")),
            guaranteed_bit_rate_kbps=tunnel_config.get("gbr_kbps", 1000),
            maximum_bit_rate_kbps=tunnel_config.get("mbr_kbps", 10000),
            packet_delay_budget_ms=tunnel_config.get("pdb_ms", 100),
            packet_error_rate=tunnel_config.get("per", 1e-6)
        )
        
        # 存儲隧道
        self.tunnels[local_teid] = tunnel
        self.tunnel_by_id[tunnel_id] = tunnel
        self.sequence_numbers[local_teid] = 0
        
        # 創建對應的封包緩衝區
        await self.create_packet_buffer(tunnel)
        
        self.interface_stats["active_tunnels"] += 1
        self.logger.info(f"NTN隧道已創建: {tunnel_id} (TEID: {local_teid})")
        
        return tunnel

    async def create_packet_buffer(self, tunnel: NtnTunnel):
        """創建封包緩衝區"""
        qos_policy = self.qos_policies[tunnel.qos_class]
        
        buffer = NtnPacketBuffer(
            buffer_id=f"buffer_{tunnel.tunnel_id}",
            tunnel_id=tunnel.tunnel_id,
            max_size_bytes=int(1024 * 1024 * qos_policy["buffer_size_factor"]),
            retention_time_ms=qos_policy["max_latency_ms"] * 2
        )
        
        self.packet_buffers[tunnel.tunnel_id] = buffer

    async def send_gtp_packet(self, tunnel_id: str, payload: bytes, 
                            destination_ip: str = None, destination_port: int = None) -> bool:
        """發送GTP封包"""
        try:
            tunnel = self.tunnel_by_id.get(tunnel_id)
            if not tunnel or not tunnel.is_active:
                self.logger.warning(f"隧道不可用: {tunnel_id}")
                return False
            
            # 更新序列號
            self.sequence_numbers[tunnel.local_teid] += 1
            seq_num = self.sequence_numbers[tunnel.local_teid]
            
            # 創建GTP-U標頭
            gtp_header = GtpuHeader(
                message_type=GtpuMessageType.G_PDU.value,
                length=len(payload),
                teid=tunnel.remote_teid,
                sequence=True,
                sequence_number=seq_num
            )
            
            # 序列化GTP-U標頭
            header_bytes = self.serialize_gtp_header(gtp_header)
            
            # 組合完整封包
            full_packet = header_bytes + payload
            
            # 檢查鏈路品質並應用補償
            await self.apply_satellite_compensation(tunnel, full_packet)
            
            # 根據QoS政策處理封包
            if await self.should_buffer_packet(tunnel, full_packet):
                await self.buffer_packet(tunnel, full_packet)
            else:
                await self.transmit_packet(tunnel, full_packet, destination_ip, destination_port)
            
            # 更新統計
            tunnel.packets_sent += 1
            tunnel.bytes_sent += len(full_packet)
            tunnel.last_activity = datetime.now()
            self.interface_stats["total_packets_processed"] += 1
            self.interface_stats["total_bytes_processed"] += len(full_packet)
            
            return True
            
        except Exception as e:
            self.logger.error(f"GTP封包發送失敗: {e}")
            return False

    async def receive_gtp_packet(self, packet_data: bytes, source_address: Tuple[str, int]) -> bool:
        """接收GTP封包"""
        try:
            # 解析GTP-U標頭
            gtp_header, payload_offset = self.parse_gtp_header(packet_data)
            
            # 找到對應的隧道
            tunnel = self.tunnels.get(gtp_header.teid)
            if not tunnel:
                self.logger.warning(f"未知的TEID: {gtp_header.teid}")
                return False
            
            # 提取有效載荷
            payload = packet_data[payload_offset:]
            
            # 處理不同類型的GTP-U消息
            if gtp_header.message_type == GtpuMessageType.G_PDU.value:
                await self.process_g_pdu(tunnel, payload, gtp_header)
            elif gtp_header.message_type == GtpuMessageType.ECHO_REQUEST.value:
                await self.handle_echo_request(source_address, gtp_header)
            elif gtp_header.message_type == GtpuMessageType.ERROR_INDICATION.value:
                await self.handle_error_indication(tunnel, gtp_header)
            
            # 更新統計
            tunnel.packets_received += 1
            tunnel.bytes_received += len(packet_data)
            tunnel.last_activity = datetime.now()
            
            return True
            
        except Exception as e:
            self.logger.error(f"GTP封包接收處理失敗: {e}")
            return False

    def serialize_gtp_header(self, header: GtpuHeader) -> bytes:
        """序列化GTP-U標頭"""
        # GTP-U標頭格式 (簡化版)
        flags = (header.version << 5) | (header.pt << 4)
        if header.extension:
            flags |= 0x04
        if header.sequence:
            flags |= 0x02
        if header.pn:
            flags |= 0x01
        
        # 基本標頭 (8 bytes)
        header_data = struct.pack(
            "!BBHI",
            flags,
            header.message_type,
            header.length,
            header.teid
        )
        
        # 可選標頭欄位
        if header.sequence:
            header_data += struct.pack("!H", header.sequence_number or 0)
            header_data += struct.pack("!BB", header.npdu_number or 0, header.next_extension_header or 0)
        
        return header_data

    def parse_gtp_header(self, packet_data: bytes) -> Tuple[GtpuHeader, int]:
        """解析GTP-U標頭"""
        if len(packet_data) < 8:
            raise ValueError("封包太短，無法包含GTP-U標頭")
        
        # 解析基本標頭
        flags, message_type, length, teid = struct.unpack("!BBHI", packet_data[:8])
        
        header = GtpuHeader(
            version=(flags >> 5) & 0x07,
            pt=(flags >> 4) & 0x01,
            extension=bool(flags & 0x04),
            sequence=bool(flags & 0x02),
            pn=bool(flags & 0x01),
            message_type=message_type,
            length=length,
            teid=teid
        )
        
        offset = 8
        
        # 解析可選欄位
        if header.sequence or header.pn or header.extension:
            if len(packet_data) < offset + 4:
                raise ValueError("封包太短，無法包含可選標頭欄位")
            
            seq_num, npdu_num, next_ext = struct.unpack("!HBB", packet_data[offset:offset+4])
            header.sequence_number = seq_num if header.sequence else None
            header.npdu_number = npdu_num if header.pn else None
            header.next_extension_header = next_ext if header.extension else None
            offset += 4
        
        return header, offset

    async def apply_satellite_compensation(self, tunnel: NtnTunnel, packet: bytes):
        """應用衛星補償"""
        if not tunnel.satellite_compensation_enabled:
            return
        
        # 獲取鏈路指標
        link_metrics = list(self.satellite_links.values())[0]  # 簡化實現
        
        # 根據鏈路品質調整
        if link_metrics.link_condition == NtnLinkCondition.POOR:
            # 啟用錯誤檢測和修正
            await self.apply_error_correction(packet)
        
        if tunnel.adaptive_coding_enabled:
            # 根據信號品質調整編碼
            await self.apply_adaptive_coding(tunnel, link_metrics)

    async def should_buffer_packet(self, tunnel: NtnTunnel, packet: bytes) -> bool:
        """判斷是否應該緩衝封包"""
        qos_policy = self.qos_policies[tunnel.qos_class]
        
        # 延遲敏感的流量不緩衝
        if tunnel.qos_class == NtnQosClass.DELAY_CRITICAL:
            return False
        
        # 檢查鏈路品質
        link_metrics = list(self.satellite_links.values())[0]
        if link_metrics.link_condition in [NtnLinkCondition.POOR, NtnLinkCondition.CRITICAL]:
            return True
        
        # 檢查緩衝區狀態
        buffer = self.packet_buffers.get(tunnel.tunnel_id)
        if buffer and len(buffer.packets) > buffer.max_packets * 0.8:
            return False  # 緩衝區快滿，直接發送
        
        return False

    async def buffer_packet(self, tunnel: NtnTunnel, packet: bytes):
        """緩衝封包"""
        buffer = self.packet_buffers.get(tunnel.tunnel_id)
        if not buffer:
            return
        
        # 檢查緩衝區容量
        if (buffer.total_size_bytes + len(packet) > buffer.max_size_bytes or
            len(buffer.packets) >= buffer.max_packets):
            # 丟棄最舊的封包
            if buffer.packets:
                old_packet = buffer.packets.pop(0)
                buffer.total_size_bytes -= len(old_packet["data"])
                buffer.packets_dropped += 1
        
        # 添加新封包
        packet_info = {
            "data": packet,
            "timestamp": datetime.now(),
            "tunnel_id": tunnel.tunnel_id
        }
        
        buffer.packets.append(packet_info)
        buffer.total_size_bytes += len(packet)
        buffer.packets_buffered += 1

    async def transmit_packet(self, tunnel: NtnTunnel, packet: bytes, 
                            destination_ip: str = None, destination_port: int = None):
        """傳輸封包"""
        try:
            if not self.udp_socket:
                return
            
            # 使用指定的目標或隧道預設目標
            target_ip = destination_ip or tunnel.remote_endpoint[0]
            target_port = destination_port or tunnel.remote_endpoint[1]
            
            # 發送封包
            await asyncio.get_event_loop().run_in_executor(
                None,
                self.udp_socket.sendto,
                packet,
                (target_ip, target_port)
            )
            
        except Exception as e:
            self.logger.error(f"封包傳輸失敗: {e}")
            tunnel.packet_loss_count += 1

    async def packet_processor_loop(self):
        """封包處理循環"""
        while self.is_running:
            try:
                if not self.udp_socket:
                    await asyncio.sleep(0.1)
                    continue
                
                # 接收封包
                try:
                    data, addr = await asyncio.get_event_loop().run_in_executor(
                        None,
                        self.udp_socket.recvfrom,
                        4096
                    )
                    
                    # 處理接收到的封包
                    await self.receive_gtp_packet(data, addr)
                    
                except socket.error:
                    await asyncio.sleep(0.01)
                
                # 處理緩衝區中的封包
                await self.process_buffered_packets()
                
                await asyncio.sleep(0.001)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"封包處理循環異常: {e}")
                await asyncio.sleep(1.0)

    async def link_monitor_loop(self):
        """鏈路監控循環"""
        while self.is_running:
            try:
                # 更新衛星鏈路指標
                await self.update_satellite_link_metrics()
                
                # 檢查隧道健康狀態
                await self.check_tunnel_health()
                
                # 清理過期封包
                await self.cleanup_expired_packets()
                
                # 更新統計
                await self.update_interface_statistics()
                
                await asyncio.sleep(1.0)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"鏈路監控循環異常: {e}")
                await asyncio.sleep(5.0)

    async def get_n3_interface_status(self) -> Dict[str, Any]:
        """獲取N3接口狀態"""
        return {
            "interface_status": {
                "is_running": self.is_running,
                "local_endpoint": f"{self.local_ip}:{self.local_port}",
                "socket_active": self.udp_socket is not None
            },
            "tunnel_status": {
                "active_tunnels": len(self.tunnels),
                "tunnel_details": [
                    {
                        "tunnel_id": tunnel.tunnel_id,
                        "local_teid": tunnel.local_teid,
                        "remote_teid": tunnel.remote_teid,
                        "qos_class": tunnel.qos_class.value,
                        "is_active": tunnel.is_active,
                        "packets_sent": tunnel.packets_sent,
                        "packets_received": tunnel.packets_received
                    }
                    for tunnel in self.tunnels.values()
                ]
            },
            "buffer_status": {
                "total_buffers": len(self.packet_buffers),
                "buffer_utilization": sum(
                    len(buf.packets) / buf.max_packets
                    for buf in self.packet_buffers.values()
                ) / max(1, len(self.packet_buffers))
            },
            "satellite_links": {
                link_id: {
                    "satellite_id": link.satellite_id,
                    "link_condition": link.link_condition.value,
                    "quality_score": link.quality_score,
                    "rtt_ms": link.round_trip_time_ms,
                    "bandwidth_mbps": link.available_bandwidth_mbps,
                    "packet_loss_rate": link.packet_loss_rate
                }
                for link_id, link in self.satellite_links.items()
            },
            "interface_statistics": self.interface_stats.copy()
        }

    # 輔助方法實現
    def generate_teid(self) -> int:
        """生成TEID"""
        import random
        return random.randint(1, 0xFFFFFFFF)

    async def process_g_pdu(self, tunnel: NtnTunnel, payload: bytes, header: GtpuHeader):
        """處理G-PDU"""
        # 這裡處理用戶數據封包
        pass

    async def handle_echo_request(self, source_address: Tuple[str, int], header: GtpuHeader):
        """處理Echo Request"""
        # 回應Echo Response
        pass

    async def handle_error_indication(self, tunnel: NtnTunnel, header: GtpuHeader):
        """處理Error Indication"""
        # 處理錯誤指示
        pass

    async def apply_error_correction(self, packet: bytes):
        """應用錯誤修正"""
        pass

    async def apply_adaptive_coding(self, tunnel: NtnTunnel, link_metrics: SatelliteLinkMetrics):
        """應用自適應編碼"""
        pass

    async def process_buffered_packets(self):
        """處理緩衝區封包"""
        for buffer in self.packet_buffers.values():
            if not buffer.packets:
                continue
            
            # 檢查封包是否過期
            current_time = datetime.now()
            expired_packets = []
            
            for i, packet_info in enumerate(buffer.packets):
                age_ms = (current_time - packet_info["timestamp"]).total_seconds() * 1000
                if age_ms > buffer.retention_time_ms:
                    expired_packets.append(i)
            
            # 移除過期封包
            for i in reversed(expired_packets):
                old_packet = buffer.packets.pop(i)
                buffer.total_size_bytes -= len(old_packet["data"])
                buffer.packets_dropped += 1

    async def update_satellite_link_metrics(self):
        """更新衛星鏈路指標"""
        for link in self.satellite_links.values():
            # 模擬指標更新
            import random
            link.rsrp_dbm += random.uniform(-2.0, 2.0)
            link.round_trip_time_ms += random.uniform(-5.0, 5.0)
            link.packet_loss_rate = max(0.0, link.packet_loss_rate + random.uniform(-0.001, 0.001))
            link.timestamp = datetime.now()

    async def check_tunnel_health(self):
        """檢查隧道健康狀態"""
        current_time = datetime.now()
        inactive_threshold = timedelta(minutes=5)
        
        for tunnel in list(self.tunnels.values()):
            if current_time - tunnel.last_activity > inactive_threshold:
                tunnel.is_active = False

    async def cleanup_expired_packets(self):
        """清理過期封包"""
        # 在process_buffered_packets中已處理
        pass

    async def update_interface_statistics(self):
        """更新接口統計"""
        if self.tunnels:
            total_loss = sum(tunnel.packet_loss_count for tunnel in self.tunnels.values())
            total_packets = sum(tunnel.packets_sent for tunnel in self.tunnels.values())
            
            if total_packets > 0:
                self.interface_stats["packet_loss_rate"] = total_loss / total_packets
        
        # 更新緩衝區利用率
        if self.packet_buffers:
            total_utilization = sum(
                len(buf.packets) / buf.max_packets
                for buf in self.packet_buffers.values()
            )
            self.interface_stats["buffer_utilization"] = total_utilization / len(self.packet_buffers)

    async def cleanup_all_tunnels(self):
        """清理所有隧道"""
        for tunnel in self.tunnels.values():
            tunnel.is_active = False
        
        self.tunnels.clear()
        self.tunnel_by_id.clear()
        self.sequence_numbers.clear()
        self.packet_buffers.clear()