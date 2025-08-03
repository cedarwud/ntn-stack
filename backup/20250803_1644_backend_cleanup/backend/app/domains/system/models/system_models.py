from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field as PydanticField


class SystemResourceMetrics(BaseModel):
    """系統資源指標"""
    
    cpu_percentage: float = PydanticField(description="CPU使用率百分比")
    memory_percentage: float = PydanticField(description="記憶體使用率百分比") 
    memory_used_mb: float = PydanticField(description="已使用記憶體 (MB)")
    memory_total_mb: float = PydanticField(description="總記憶體 (MB)")
    gpu_percentage: float = PydanticField(description="GPU使用率百分比")
    network_latency_ms: float = PydanticField(description="網路延遲 (毫秒)")
    disk_io_mbps: float = PydanticField(description="磁碟I/O速度 (MB/s)")
    network_io_mbps: float = PydanticField(description="網路I/O速度 (MB/s)")


class ContainerResourceData(BaseModel):
    """容器資源數據"""
    
    container_name: str = PydanticField(description="容器名稱")
    cpu_percentage: float = PydanticField(description="CPU使用率百分比")
    memory_percentage: float = PydanticField(description="記憶體使用率百分比")
    memory_used_mb: float = PydanticField(description="已使用記憶體 (MB)")
    memory_limit_mb: float = PydanticField(description="記憶體限制 (MB)")
    network_rx_mb: float = PydanticField(description="網路接收 (MB)")
    network_tx_mb: float = PydanticField(description="網路傳送 (MB)")
    block_io_read_mb: float = PydanticField(description="磁碟讀取 (MB)")
    block_io_write_mb: float = PydanticField(description="磁碟寫入 (MB)")


class SystemResourcesResponse(BaseModel):
    """系統資源響應"""
    
    overall_metrics: SystemResourceMetrics = PydanticField(description="整體系統指標")
    container_metrics: Dict[str, ContainerResourceData] = PydanticField(description="各容器指標")
    host_info: Dict[str, Any] = PydanticField(description="主機資訊")
    calculation_metadata: Dict[str, Any] = PydanticField(description="計算元數據")
    timestamp: datetime = PydanticField(description="時間戳")


class SystemResourceRequest(BaseModel):
    """系統資源請求"""
    
    include_containers: Optional[list] = PydanticField(default=None, description="包含的容器列表")
    include_gpu_metrics: bool = PydanticField(default=True, description="是否包含GPU指標")
    include_network_latency: bool = PydanticField(default=True, description="是否包含網路延遲")