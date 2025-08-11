import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Body, status
from datetime import datetime

from app.domains.system.models.system_models import (
    SystemResourceRequest,
    SystemResourcesResponse
)
from app.domains.system.services.system_resource_service import SystemResourceService

logger = logging.getLogger(__name__)
router = APIRouter()

# 創建服務實例
system_resource_service = SystemResourceService()


@router.post("/resources/real-time", response_model=SystemResourcesResponse)
async def get_real_time_system_resources(
    request: SystemResourceRequest = Body(default_factory=SystemResourceRequest)
):
    """
    獲取真實系統資源使用情況
    
    提供真實的系統資源監控，包括：
    - 真實CPU使用率 (基於psutil)
    - 真實記憶體使用率 (基於psutil)
    - Docker容器資源使用情況
    - GPU使用率 (nvidia-smi或智能估算)
    - 網路延遲測量
    - 磁碟和網路I/O速率
    
    這個API解決了效能指標板使用網路指標代理系統資源的問題。
    """
    try:
        logger.info("開始獲取真實系統資源數據")
        
        # 獲取真實系統資源數據
        resource_data = await system_resource_service.get_system_resources(request)
        
        response = SystemResourcesResponse(**resource_data)
        
        logger.info(f"系統資源獲取完成 - CPU: {response.overall_metrics.cpu_percentage}%, "
                   f"Memory: {response.overall_metrics.memory_percentage}%, "
                   f"GPU: {response.overall_metrics.gpu_percentage}%")
        
        return response
        
    except Exception as e:
        logger.error(f"獲取系統資源失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取系統資源失敗: {str(e)}"
        )


@router.get("/resources/containers")
async def get_container_resources(
    container_names: Optional[str] = None
):
    """
    獲取指定容器的資源使用情況
    
    Args:
        container_names: 容器名稱列表，用逗號分隔。如果不指定則返回所有容器
    """
    try:
        logger.info(f"獲取容器資源數據: {container_names}")
        
        include_containers = container_names.split(',') if container_names else None
        request = SystemResourceRequest(include_containers=include_containers)
        
        resource_data = await system_resource_service.get_system_resources(request)
        
        return {
            "container_metrics": resource_data["container_metrics"],
            "timestamp": resource_data["timestamp"]
        }
        
    except Exception as e:
        logger.error(f"獲取容器資源失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取容器資源失敗: {str(e)}"
        )


@router.get("/resources/summary")
async def get_system_summary():
    """
    獲取系統資源摘要
    
    提供快速的系統資源概覽，適用於儀表板顯示
    """
    try:
        logger.info("獲取系統資源摘要")
        
        request = SystemResourceRequest(
            include_gpu_metrics=True,
            include_network_latency=True
        )
        
        resource_data = await system_resource_service.get_system_resources(request)
        overall_metrics = resource_data["overall_metrics"]
        
        return {
            "cpu_percentage": overall_metrics.cpu_percentage,
            "memory_percentage": overall_metrics.memory_percentage,
            "gpu_percentage": overall_metrics.gpu_percentage,
            "network_latency_ms": overall_metrics.network_latency_ms,
            "memory_used_mb": overall_metrics.memory_used_mb,
            "memory_total_mb": overall_metrics.memory_total_mb,
            "disk_io_mbps": overall_metrics.disk_io_mbps,
            "network_io_mbps": overall_metrics.network_io_mbps,
            "timestamp": resource_data["timestamp"],
            "data_source": "real_system_metrics"
        }
        
    except Exception as e:
        logger.error(f"獲取系統摘要失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取系統摘要失敗: {str(e)}"
        )