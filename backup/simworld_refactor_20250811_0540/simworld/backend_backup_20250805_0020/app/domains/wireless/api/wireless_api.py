"""
Wireless Domain API
提供 Sionna 無線通道模擬和 UERANSIM 轉換的 API 端點
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
import logging

from ..models.channel_models import (
    ChannelSimulationRequest,
    SionnaChannelResponse,
    UERANSIMChannelParams,
    ChannelToRANConversionResult,
    BatchChannelConversionRequest,
    ChannelModelMetrics,
    ChannelUpdateEvent,
)
from ..services.sionna_channel_service import SionnaChannelSimulationService
from ..services.channel_conversion_service import ChannelToRANConversionService

logger = logging.getLogger(__name__)

router = APIRouter()

# 服務實例 (在實際部署中應該透過依賴注入)
sionna_service = SionnaChannelSimulationService()
conversion_service = ChannelToRANConversionService()


@router.post("/simulate", response_model=List[SionnaChannelResponse], tags=["通道模擬"])
async def simulate_wireless_channel(
    request: ChannelSimulationRequest, background_tasks: BackgroundTasks
) -> List[SionnaChannelResponse]:
    """
    執行 Sionna 無線通道模擬

    - **simulation_id**: 模擬識別碼
    - **environment_type**: 環境類型 (urban, suburban, rural, indoor, satellite)
    - **transmitters**: 發送端資訊列表
    - **receivers**: 接收端資訊列表
    - **carrier_frequency_hz**: 載波頻率
    - **bandwidth_hz**: 頻寬
    """
    try:
        logger.info(f"收到通道模擬請求: {request.simulation_id}")

        # 驗證請求參數
        if not request.transmitters:
            raise HTTPException(status_code=400, detail="至少需要一個發送端")
        if not request.receivers:
            raise HTTPException(status_code=400, detail="至少需要一個接收端")

        # 執行模擬
        results = await sionna_service.simulate_channel(request)

        # 背景任務：清理舊的模擬記錄
        background_tasks.add_task(sionna_service.cleanup_completed_simulations)

        logger.info(
            f"通道模擬完成: {request.simulation_id}, 產生 {len(results)} 個響應"
        )
        return results

    except Exception as e:
        logger.error(f"通道模擬失敗: {e}")
        raise HTTPException(status_code=500, detail=f"模擬失敗: {str(e)}")


@router.post(
    "/channel-to-ran", response_model=ChannelToRANConversionResult, tags=["通道轉換"]
)
async def convert_channel_to_ran(
    channel_response: SionnaChannelResponse,
    ue_id: str = Query(..., description="UE ID"),
    gnb_id: str = Query(..., description="gNodeB ID"),
    noise_figure_db: float = Query(7.0, description="噪音指數 (dB)"),
    antenna_gain_db: float = Query(15.0, description="天線增益 (dB)"),
) -> ChannelToRANConversionResult:
    """
    將 Sionna 通道響應轉換為 UERANSIM 可用的 RAN 參數

    這是核心的轉換端點，實現從物理層到協議層的參數映射：
    - 路徑損耗 → RSRP
    - 多路徑特性 → SINR, RSRQ
    - 通道品質 → CQI
    - 頻譜效率 → 吞吐量估計
    """
    try:
        logger.info(f"開始通道轉換: 通道 {channel_response.channel_id} → UE {ue_id}")

        result = await conversion_service.convert_channel_to_ran(
            channel_response=channel_response,
            ue_id=ue_id,
            gnb_id=gnb_id,
            noise_figure_db=noise_figure_db,
            antenna_gain_db=antenna_gain_db,
        )

        logger.info(f"通道轉換完成: {result.conversion_id}")
        return result

    except Exception as e:
        logger.error(f"通道轉換失敗: {e}")
        raise HTTPException(status_code=500, detail=f"轉換失敗: {str(e)}")


@router.post(
    "/batch-channel-to-ran",
    response_model=List[ChannelToRANConversionResult],
    tags=["通道轉換"],
)
async def batch_convert_channels_to_ran(
    request: BatchChannelConversionRequest,
) -> List[ChannelToRANConversionResult]:
    """
    批次轉換多個通道響應為 RAN 參數

    適用於大規模模擬或多個 UE 的同時處理
    """
    try:
        logger.info(
            f"開始批次轉換: {request.batch_id}, 通道數: {len(request.channels)}"
        )

        results = await conversion_service.batch_convert_channels(request)

        logger.info(f"批次轉換完成: {request.batch_id}, 成功: {len(results)}")
        return results

    except Exception as e:
        logger.error(f"批次轉換失敗: {e}")
        raise HTTPException(status_code=500, detail=f"批次轉換失敗: {str(e)}")


@router.get("/simulation/{simulation_id}/status", tags=["模擬管理"])
async def get_simulation_status(simulation_id: str) -> Dict[str, Any]:
    """獲取模擬狀態"""
    try:
        status = await sionna_service.get_simulation_status(simulation_id)

        if status is None:
            raise HTTPException(status_code=404, detail="找不到指定的模擬")

        return status

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取模擬狀態失敗: {e}")
        raise HTTPException(status_code=500, detail=f"狀態查詢失敗: {str(e)}")


@router.delete("/simulation/{simulation_id}", tags=["模擬管理"])
async def cancel_simulation(simulation_id: str) -> Dict[str, str]:
    """取消正在進行的模擬"""
    try:
        success = await sionna_service.cancel_simulation(simulation_id)

        if not success:
            raise HTTPException(status_code=404, detail="找不到指定的模擬或模擬已完成")

        return {"message": f"模擬 {simulation_id} 已取消", "status": "cancelled"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"取消模擬失敗: {e}")
        raise HTTPException(status_code=500, detail=f"取消失敗: {str(e)}")


@router.get("/metrics", response_model=ChannelModelMetrics, tags=["監控"])
async def get_channel_model_metrics() -> ChannelModelMetrics:
    """獲取通道模型效能指標"""
    try:
        metrics = await sionna_service.get_metrics()
        return metrics

    except Exception as e:
        logger.error(f"獲取指標失敗: {e}")
        raise HTTPException(status_code=500, detail=f"指標查詢失敗: {str(e)}")


@router.get(
    "/conversion/history",
    response_model=List[ChannelToRANConversionResult],
    tags=["轉換歷史"],
)
async def get_conversion_history(
    limit: int = Query(100, ge=1, le=1000, description="返回記錄數量"),
    since: Optional[datetime] = Query(None, description="起始時間"),
) -> List[ChannelToRANConversionResult]:
    """獲取轉換歷史記錄"""
    try:
        history = await conversion_service.get_conversion_history(
            limit=limit, since=since
        )
        return history

    except Exception as e:
        logger.error(f"獲取轉換歷史失敗: {e}")
        raise HTTPException(status_code=500, detail=f"歷史查詢失敗: {str(e)}")


@router.post(
    "/quick-simulation",
    response_model=List[ChannelToRANConversionResult],
    tags=["快速測試"],
)
async def quick_simulation_and_conversion(
    environment_type: str = Query("urban", description="環境類型"),
    frequency_ghz: float = Query(2.1, description="頻率 (GHz)"),
    bandwidth_mhz: float = Query(20, description="頻寬 (MHz)"),
    tx_position: List[float] = Query([0, 0, 30], description="發送端位置 [x,y,z]"),
    rx_position: List[float] = Query([1000, 0, 1.5], description="接收端位置 [x,y,z]"),
    ue_id: str = Query("ue_001", description="UE ID"),
    gnb_id: str = Query("gnb_001", description="gNodeB ID"),
) -> List[ChannelToRANConversionResult]:
    """
    快速執行通道模擬和轉換的完整流程

    適用於測試和演示，一次性完成從 Sionna 模擬到 UERANSIM 參數的轉換
    """
    try:
        # 建立模擬請求
        simulation_id = f"quick_{uuid.uuid4().hex[:8]}"
        simulation_request = ChannelSimulationRequest(
            simulation_id=simulation_id,
            environment_type=environment_type,
            carrier_frequency_hz=frequency_ghz * 1e9,
            bandwidth_hz=bandwidth_mhz * 1e6,
            transmitters=[{"position": tx_position}],
            receivers=[{"position": rx_position}],
        )

        # 執行模擬
        logger.info(f"執行快速模擬: {simulation_id}")
        channel_responses = await sionna_service.simulate_channel(simulation_request)

        # 轉換所有通道響應
        conversion_results = []
        for channel_response in channel_responses:
            result = await conversion_service.convert_channel_to_ran(
                channel_response=channel_response, ue_id=ue_id, gnb_id=gnb_id
            )
            # 添加環境類型到調試信息
            result.debug_info["environment_type"] = environment_type
            conversion_results.append(result)

        logger.info(
            f"快速模擬完成: {simulation_id}, 產生 {len(conversion_results)} 個轉換結果"
        )
        return conversion_results

    except Exception as e:
        logger.error(f"快速模擬失敗: {e}")
        raise HTTPException(status_code=500, detail=f"快速模擬失敗: {str(e)}")


@router.post(
    "/satellite-ntn-simulation",
    response_model=List[ChannelToRANConversionResult],
    tags=["衛星 NTN"],
)
async def satellite_ntn_simulation(
    satellite_altitude_km: float = Query(550, description="衛星高度 (km)"),
    ground_station_lat: float = Query(24.786667, description="地面站緯度"),
    ground_station_lon: float = Query(120.996944, description="地面站經度"),
    frequency_ghz: float = Query(20, description="頻率 (GHz)"),
    bandwidth_mhz: float = Query(100, description="頻寬 (MHz)"),
    ue_id: str = Query("ue_satellite", description="UE ID"),
    gnb_id: str = Query("gnb_satellite", description="gNodeB ID"),
) -> List[ChannelToRANConversionResult]:
    """
    衛星 NTN (Non-Terrestrial Network) 通道模擬

    專門針對衛星通信場景進行最佳化的模擬和轉換
    """
    try:
        simulation_id = f"ntn_{uuid.uuid4().hex[:8]}"

        # 計算衛星位置 (簡化為直接在地面站上方)
        satellite_position = [0, 0, satellite_altitude_km * 1000]  # 轉換為米
        ground_position = [0, 0, 0]  # 地面參考點

        simulation_request = ChannelSimulationRequest(
            simulation_id=simulation_id,
            environment_type="satellite",
            carrier_frequency_hz=frequency_ghz * 1e9,
            bandwidth_hz=bandwidth_mhz * 1e6,
            transmitters=[{"position": satellite_position}],
            receivers=[{"position": ground_position}],
            max_reflections=0,  # 衛星通信主要是直射路徑
            diffraction_enabled=False,
            scattering_enabled=False,
        )

        logger.info(f"執行衛星 NTN 模擬: {simulation_id}")
        channel_responses = await sionna_service.simulate_channel(simulation_request)

        # 轉換為 RAN 參數，考慮衛星通信的特殊性
        conversion_results = []
        for channel_response in channel_responses:
            result = await conversion_service.convert_channel_to_ran(
                channel_response=channel_response,
                ue_id=ue_id,
                gnb_id=gnb_id,
                noise_figure_db=3.0,  # 衛星接收機通常有更低的噪音指數
                antenna_gain_db=35.0,  # 衛星天線增益較高
            )
            # 添加環境類型到調試信息
            result.debug_info["environment_type"] = "satellite"
            conversion_results.append(result)

        logger.info(f"衛星 NTN 模擬完成: {simulation_id}")
        return conversion_results

    except Exception as e:
        logger.error(f"衛星 NTN 模擬失敗: {e}")
        raise HTTPException(status_code=500, detail=f"衛星模擬失敗: {str(e)}")


@router.get("/health", tags=["健康檢查"])
async def wireless_health_check() -> Dict[str, Any]:
    """無線模組健康檢查"""
    try:
        # 檢查服務狀態
        metrics = await sionna_service.get_metrics()

        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "sionna_simulation": {
                    "status": "active",
                    "gpu_available": sionna_service.gpu_available,
                    "active_simulations": len(sionna_service.active_simulations),
                },
                "channel_conversion": {
                    "status": "active",
                    "cache_size": len(conversion_service.conversion_cache),
                    "total_conversions": metrics.total_channels_processed,
                },
            },
            "metrics": {
                "total_channels_processed": metrics.total_channels_processed,
                "average_processing_time_ms": metrics.average_conversion_time_ms,
                "gpu_utilization": metrics.gpu_utilization,
                "memory_usage_mb": metrics.memory_usage_mb,
            },
        }

        return health_status

    except Exception as e:
        logger.error(f"健康檢查失敗: {e}")
        raise HTTPException(status_code=500, detail=f"健康檢查失敗: {str(e)}")


@router.get("/statistics", tags=["統計"])
async def get_wireless_statistics() -> Dict[str, Any]:
    """獲取無線統計信息"""
    try:
        # 獲取基本指標
        metrics = await sionna_service.get_metrics()

        # 獲取轉換歷史統計
        conversion_history = await conversion_service.get_conversion_history(limit=1000)

        # 計算統計信息
        total_conversions = len(conversion_history)
        successful_conversions = sum(
            1 for conv in conversion_history if conv.ran_parameters.cqi > 0
        )

        # 計算環境類型分佈
        environment_distribution = {}
        for conv in conversion_history:
            # 從調試信息中獲取環境類型，或使用默認值
            env_type = conv.debug_info.get("environment_type", "unknown")
            environment_distribution[env_type] = (
                environment_distribution.get(env_type, 0) + 1
            )

        # 計算 CQI 分佈
        cqi_distribution = {}
        for conv in conversion_history:
            cqi = conv.ran_parameters.cqi
            cqi_distribution[str(cqi)] = cqi_distribution.get(str(cqi), 0) + 1

        statistics = {
            "timestamp": datetime.utcnow().isoformat(),
            "summary": {
                "total_simulations": metrics.total_channels_processed,
                "total_conversions": total_conversions,
                "success_rate": (
                    successful_conversions / total_conversions
                    if total_conversions > 0
                    else 0.0
                ),
                "average_processing_time_ms": metrics.average_conversion_time_ms,
                "gpu_utilization": metrics.gpu_utilization,
                "memory_usage_mb": metrics.memory_usage_mb,
            },
            "distributions": {
                "environment_types": environment_distribution,
                "cqi_levels": cqi_distribution,
            },
            "performance": {
                "active_simulations": len(sionna_service.active_simulations),
                "cache_hit_rate": conversion_service.get_cache_hit_rate(),
                "average_sinr_db": (
                    sum(
                        conv.ran_parameters.sinr_db
                        for conv in conversion_history[-100:]
                    )
                    / min(100, len(conversion_history))
                    if conversion_history
                    else 0.0
                ),
                "average_throughput_mbps": (
                    sum(
                        conv.ran_parameters.throughput_mbps
                        for conv in conversion_history[-100:]
                    )
                    / min(100, len(conversion_history))
                    if conversion_history
                    else 0.0
                ),
            },
        }

        return statistics

    except Exception as e:
        logger.error(f"獲取統計信息失敗: {e}")
        raise HTTPException(status_code=500, detail=f"統計查詢失敗: {str(e)}")


@router.get("/channel-types", tags=["通道管理"])
async def get_supported_channel_types() -> Dict[str, Any]:
    """獲取支援的通道類型列表"""
    try:
        channel_types = {
            "supported_environments": [
                {
                    "type": "urban",
                    "description": "密集城市環境",
                    "typical_path_loss_db": 128.1,
                    "max_reflections": 3,
                    "frequency_range_ghz": [0.7, 6.0],
                    "use_cases": ["5G城市部署", "密集基站覆蓋"],
                },
                {
                    "type": "suburban",
                    "description": "郊區環境",
                    "typical_path_loss_db": 120.9,
                    "max_reflections": 2,
                    "frequency_range_ghz": [0.7, 6.0],
                    "use_cases": ["郊區覆蓋", "中密度部署"],
                },
                {
                    "type": "rural",
                    "description": "鄉村環境",
                    "typical_path_loss_db": 113.2,
                    "max_reflections": 1,
                    "frequency_range_ghz": [0.7, 6.0],
                    "use_cases": ["廣域覆蓋", "低密度部署"],
                },
                {
                    "type": "indoor",
                    "description": "室內環境",
                    "typical_path_loss_db": 89.5,
                    "max_reflections": 5,
                    "frequency_range_ghz": [2.4, 60.0],
                    "use_cases": ["室內覆蓋", "企業網路", "WiFi 6E"],
                },
                {
                    "type": "satellite",
                    "description": "衛星通信環境",
                    "typical_path_loss_db": 162.4,
                    "max_reflections": 0,
                    "frequency_range_ghz": [10.0, 30.0],
                    "use_cases": ["衛星通信", "NTN", "回程連線"],
                },
            ],
            "supported_features": [
                "多路徑傳播建模",
                "Ray tracing 支援",
                "GPU 加速計算",
                "3GPP 標準 CQI 映射",
                "動態通道更新",
                "批次處理支援",
            ],
            "frequency_bands": {
                "sub6_ghz": {"range": [0.7, 6.0], "description": "Sub-6GHz 頻段"},
                "mmwave": {"range": [24.0, 40.0], "description": "毫米波頻段"},
                "satellite": {"range": [10.0, 30.0], "description": "衛星通信頻段"},
            },
        }

        return channel_types

    except Exception as e:
        logger.error(f"獲取通道類型失敗: {e}")
        raise HTTPException(status_code=500, detail=f"通道類型查詢失敗: {str(e)}")


@router.post("/generate-ueransim-config", tags=["配置生成"])
async def generate_ueransim_config(
    gnb_id: str = Query(..., description="gNodeB ID"),
    position_x: float = Query(0.0, description="gNodeB X 位置 (m)"),
    position_y: float = Query(0.0, description="gNodeB Y 位置 (m)"),
    position_z: float = Query(30.0, description="gNodeB Z 位置 (m)"),
    frequency_mhz: int = Query(..., description="頻率 (MHz)"),
    bandwidth_mhz: int = Query(..., description="頻寬 (MHz)"),
    tx_power_dbm: float = Query(43.0, description="發射功率 (dBm)"),
    plmn: str = Query("00101", description="PLMN ID"),
    tac: int = Query(1, description="TAC"),
    cell_id: int = Query(1, description="Cell ID"),
) -> Dict[str, Any]:
    """
    生成 UERANSIM gNodeB 配置文件

    基於提供的參數生成完整的 UERANSIM 配置
    """
    try:
        logger.info(f"生成 UERANSIM 配置: gNodeB {gnb_id}")

        # 生成 gNodeB 配置
        gnb_config = {
            "mcc": plmn[:3],
            "mnc": plmn[3:],
            "nci": cell_id,
            "idLength": 32,
            "tac": tac,
            "linkIp": "127.0.0.1",
            "ngapIp": "127.0.0.1",
            "gtpIp": "127.0.0.1",
            "plmns": [{"mcc": plmn[:3], "mnc": plmn[3:], "sst": 1, "sd": "0x010203"}],
            "slices": [{"sst": 1, "sd": "0x010203", "default": True}],
            "amfConfigs": [{"address": "127.0.0.1", "port": 38412}],
        }

        # 添加無線參數
        radio_config = {
            "frequency": frequency_mhz,
            "bandwidth": bandwidth_mhz,
            "tx_power_dbm": tx_power_dbm,
            "position": {"x": position_x, "y": position_y, "z": position_z},
            "antenna": {
                "gain_db": 15.0,
                "height_m": position_z,
                "pattern": "omnidirectional",
            },
        }

        # 生成完整配置
        full_config = {
            "config_id": f"gnb_{gnb_id}_{uuid.uuid4().hex[:8]}",
            "gnb_id": gnb_id,
            "generated_at": datetime.utcnow().isoformat(),
            "config": {"gnb": gnb_config, "radio": radio_config},
            "config_yaml": f"""# UERANSIM gNodeB Configuration for {gnb_id}
# Generated at: {datetime.utcnow().isoformat()}

mcc: '{plmn[:3]}'
mnc: '{plmn[3:]}'
nci: {cell_id}
idLength: 32
tac: {tac}

linkIp: 127.0.0.1
ngapIp: 127.0.0.1  
gtpIp: 127.0.0.1

# List of AMF address information
amfConfigs:
  - address: 127.0.0.1
    port: 38412

# List of supported PLMNs
plmns:
  - mcc: '{plmn[:3]}'
    mnc: '{plmn[3:]}'
    sst: 1
    sd: 0x010203

# List of supported S-NSSAIs
slices:
  - sst: 1
    sd: 0x010203
    default: true

# Radio configuration
frequency: {frequency_mhz}
bandwidth: {bandwidth_mhz}
txPower: {tx_power_dbm}

# Position
position:
  x: {position_x}
  y: {position_y}
  z: {position_z}
""",
            "notes": [
                "此配置基於提供的 Sionna 通道模擬參數生成",
                "請根據實際部署環境調整 IP 地址",
                "建議在正式使用前進行功能測試",
            ],
        }

        logger.info(f"UERANSIM 配置生成完成: {full_config['config_id']}")
        return full_config

    except Exception as e:
        logger.error(f"生成 UERANSIM 配置失敗: {e}")
        raise HTTPException(status_code=500, detail=f"配置生成失敗: {str(e)}")
