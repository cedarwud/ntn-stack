"""
RF Simulation Domain API - 統一的無線通道和干擾模擬API

整合原本的 wireless 和 interference 領域功能：
- Sionna 無線通道模擬
- 干擾源模擬和檢測
- AI-RAN 抗干擾控制
- UERANSIM 參數轉換

Phase 2 重構：簡化領域架構，合併相關功能
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
import logging

# Import wireless domain models and services
from ...wireless.models.channel_models import (
    ChannelSimulationRequest,
    SionnaChannelResponse,
    UERANSIMChannelParams,
    ChannelToRANConversionResult,
    BatchChannelConversionRequest,
    ChannelModelMetrics,
    ChannelUpdateEvent,
)
from ...wireless.services.sionna_channel_service import SionnaChannelSimulationService
from ...wireless.services.channel_conversion_service import ChannelToRANConversionService

# Import interference domain models and services
from ...interference.models.interference_models import (
    InterferenceSimulationRequest,
    InterferenceSimulationResponse,
    AIRANControlRequest,
    AIRANControlResponse,
    JammerType,
    InterferenceEnvironment,
    InterferenceDetectionResult,
    InterferenceMetrics,
    JammerSource,
    InterferencePattern,
)
from ...interference.services.interference_simulation_service import InterferenceSimulationService
from ...interference.services.ai_ran_service import AIRANService
from ...interference.services.ai_ran_service_integrated import (
    AIRANServiceIntegrated,
    get_ai_ran_service_integrated,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# 統一的服務實例管理
sionna_service = SionnaChannelSimulationService()
conversion_service = ChannelToRANConversionService()
interference_service = InterferenceSimulationService()
ai_ran_service = AIRANService()

# ============================================================================
# 無線通道模擬端點 (原 wireless domain)
# ============================================================================

@router.post("/channel/simulate", response_model=List[SionnaChannelResponse], tags=["通道模擬"])
async def simulate_wireless_channel(
    request: ChannelSimulationRequest, background_tasks: BackgroundTasks
) -> List[SionnaChannelResponse]:
    """
    執行 Sionna 無線通道模擬
    
    支持環境類型：urban, suburban, rural, indoor, satellite
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
        
        logger.info(f"通道模擬完成: {request.simulation_id}, 產生 {len(results)} 個響應")
        return results
        
    except Exception as e:
        logger.error(f"通道模擬失敗: {e}")
        raise HTTPException(status_code=500, detail=f"模擬失敗: {str(e)}")


@router.post("/channel/convert-to-ran", response_model=ChannelToRANConversionResult, tags=["通道轉換"])
async def convert_channel_to_ran(
    channel_response: SionnaChannelResponse,
    ue_id: str = Query(..., description="UE ID"),
    gnb_id: str = Query(..., description="gNodeB ID"),
    noise_figure_db: float = Query(7.0, description="噪音指數 (dB)"),
    antenna_gain_db: float = Query(15.0, description="天線增益 (dB)"),
) -> ChannelToRANConversionResult:
    """
    將 Sionna 通道響應轉換為 UERANSIM 可用的 RAN 參數
    
    實現從物理層到協議層的參數映射：
    - 路徑損耗 → RSRP
    - 多路徑特性 → SINR, RSRQ
    - 通道品質 → CQI
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


@router.post("/channel/quick-simulation", response_model=List[ChannelToRANConversionResult], tags=["快速測試"])
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
            result.debug_info["environment_type"] = environment_type
            conversion_results.append(result)
        
        logger.info(f"快速模擬完成: {simulation_id}, 產生 {len(conversion_results)} 個轉換結果")
        return conversion_results
        
    except Exception as e:
        logger.error(f"快速模擬失敗: {e}")
        raise HTTPException(status_code=500, detail=f"快速模擬失敗: {str(e)}")


@router.post("/channel/satellite-ntn", response_model=List[ChannelToRANConversionResult], tags=["衛星 NTN"])
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
            result.debug_info["environment_type"] = "satellite"
            conversion_results.append(result)
        
        logger.info(f"衛星 NTN 模擬完成: {simulation_id}")
        return conversion_results
        
    except Exception as e:
        logger.error(f"衛星 NTN 模擬失敗: {e}")
        raise HTTPException(status_code=500, detail=f"衛星模擬失敗: {str(e)}")

# ============================================================================
# 干擾模擬和抗干擾端點 (原 interference domain)
# ============================================================================

@router.post("/interference/simulate", response_model=InterferenceSimulationResponse, tags=["干擾模擬"])
async def simulate_interference(
    request: InterferenceSimulationRequest, background_tasks: BackgroundTasks
) -> InterferenceSimulationResponse:
    """
    執行干擾模擬
    
    使用 Sionna 進行 GPU 加速的多類型干擾源模擬，
    支持寬帶噪聲、掃頻、智能干擾等多種干擾場景。
    """
    try:
        logger.info(f"收到干擾模擬請求: {request.request_id}")
        
        # 執行干擾模擬
        response = await interference_service.simulate_interference(request)
        
        # 在背景更新歷史數據
        if response.success:
            background_tasks.add_task(_update_simulation_history, request, response)
        
        return response
        
    except Exception as e:
        logger.error(f"干擾模擬API失敗: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"模擬失敗: {str(e)}")


@router.post("/interference/ai-ran/control", response_model=AIRANControlResponse, tags=["AI-RAN 抗干擾"])
async def ai_ran_control(
    request: AIRANControlRequest, background_tasks: BackgroundTasks
) -> AIRANControlResponse:
    """
    AI-RAN 抗干擾控制 (原版)
    
    基於本地 DQN 的抗干擾決策，保留作為後備系統。
    """
    try:
        logger.info(f"收到 AI-RAN 控制請求 (原版): {request.request_id}")
        
        # 執行 AI-RAN 決策
        response = await ai_ran_service.make_anti_jamming_decision(request)
        
        # 在背景訓練 AI 模型
        if response.success and ai_ran_service.ai_available:
            background_tasks.add_task(_train_ai_model, request, response)
        
        return response
        
    except Exception as e:
        logger.error(f"AI-RAN 控制API失敗: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"控制失敗: {str(e)}")


@router.post("/interference/ai-ran/control-netstack", response_model=AIRANControlResponse, tags=["AI-RAN 抗干擾"])
async def ai_ran_control_integrated(
    request: AIRANControlRequest, background_tasks: BackgroundTasks
) -> AIRANControlResponse:
    """
    AI-RAN 抗干擾控制 (NetStack 整合版)
    
    基於 NetStack RL 系統的智能抗干擾決策，支持：
    - 多算法支援 (DQN/PPO/SAC)
    - NetStack PostgreSQL 資料庫整合
    - 統一的會話管理和持久化
    - 毫秒級實時決策響應
    - 自動降級到本地模式
    """
    try:
        logger.info(f"收到 AI-RAN 控制請求 (整合版): {request.request_id}")
        
        # 獲取整合服務
        integrated_service = await get_ai_ran_service_integrated()
        
        # 執行 NetStack 整合決策
        response = await integrated_service.make_anti_jamming_decision(request)
        
        # 記錄使用的系統模式
        system_status = getattr(response, "system_status", {}) or {}
        logger.info(f"決策完成，模式: {system_status.get('decision_mode', 'unknown')}")
        
        return response
        
    except Exception as e:
        logger.error(f"AI-RAN 整合控制API失敗: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"整合控制失敗: {str(e)}")


@router.get("/interference/scenarios/presets", tags=["干擾場景"])
async def get_preset_scenarios():
    """
    獲取預設干擾場景
    
    返回常用的干擾測試場景配置
    """
    presets = {
        "urban_broadband_interference": {
            "name": "都市寬帶干擾",
            "description": "模擬都市環境中的寬帶噪聲干擾",
            "jammer_configs": [
                {
                    "type": "broadband_noise",
                    "position": [500, 0, 10],
                    "power_dbm": 30,
                    "frequency_band": {"center_freq_mhz": 2150, "bandwidth_mhz": 50},
                }
            ],
            "environment_bounds": {
                "min_x": -1000, "max_x": 1000,
                "min_y": -1000, "max_y": 1000,
                "min_z": 0, "max_z": 100,
            },
        },
        "military_sweep_jamming": {
            "name": "軍用掃頻干擾",
            "description": "模擬軍事環境中的掃頻干擾攻擊",
            "jammer_configs": [
                {
                    "type": "sweep_jammer",
                    "position": [800, 300, 20],
                    "power_dbm": 40,
                    "frequency_band": {"center_freq_mhz": 2150, "bandwidth_mhz": 100},
                    "sweep_rate_mhz_per_sec": 2000,
                }
            ],
            "environment_bounds": {
                "min_x": -2000, "max_x": 2000,
                "min_y": -2000, "max_y": 2000,
                "min_z": 0, "max_z": 200,
            },
        },
        "smart_adaptive_jamming": {
            "name": "智能自適應干擾",
            "description": "模擬AI驅動的智能干擾攻擊",
            "jammer_configs": [
                {
                    "type": "smart_jammer",
                    "position": [1000, -500, 30],
                    "power_dbm": 35,
                    "frequency_band": {"center_freq_mhz": 2150, "bandwidth_mhz": 20},
                    "learning_enabled": True,
                    "target_protocols": ["5G-NR", "LTE"],
                }
            ],
            "environment_bounds": {
                "min_x": -1500, "max_x": 1500,
                "min_y": -1500, "max_y": 1500,
                "min_z": 0, "max_z": 150,
            },
        },
    }
    
    return {"success": True, "presets": presets, "count": len(presets)}


# ============================================================================
# 統一的健康檢查和監控端點
# ============================================================================

@router.get("/health", tags=["健康檢查"])
async def rf_simulation_health_check() -> Dict[str, Any]:
    """RF 模擬系統統一健康檢查"""
    try:
        # 檢查無線通道服務
        channel_metrics = await sionna_service.get_metrics()
        
        # 檢查干擾模擬服務
        interference_metrics = await interference_service.get_simulation_metrics(3600.0)
        
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "sionna_channel_simulation": {
                    "status": "active",
                    "gpu_available": sionna_service.gpu_available,
                    "active_simulations": len(sionna_service.active_simulations),
                },
                "channel_conversion": {
                    "status": "active",
                    "cache_size": len(conversion_service.conversion_cache),
                    "total_conversions": channel_metrics.total_channels_processed,
                },
                "interference_simulation": {
                    "status": "active",
                    "service_status": interference_service.get_service_status(),
                },
                "ai_ran_control": {
                    "status": "active",
                    "ai_available": ai_ran_service.ai_available,
                },
            },
            "metrics": {
                "total_channels_processed": channel_metrics.total_channels_processed,
                "average_processing_time_ms": channel_metrics.average_conversion_time_ms,
                "gpu_utilization": channel_metrics.gpu_utilization,
                "memory_usage_mb": channel_metrics.memory_usage_mb,
                "total_interference_simulations": interference_metrics.total_simulations,
                "total_ai_ran_decisions": interference_metrics.total_ai_decisions,
            },
        }
        
        return health_status
        
    except Exception as e:
        logger.error(f"健康檢查失敗: {e}")
        raise HTTPException(status_code=500, detail=f"健康檢查失敗: {str(e)}")


@router.get("/metrics", tags=["系統監控"])
async def get_rf_simulation_metrics() -> Dict[str, Any]:
    """獲取 RF 模擬系統統一指標"""
    try:
        # 獲取無線通道指標
        channel_metrics = await sionna_service.get_metrics()
        conversion_history = await conversion_service.get_conversion_history(limit=1000)
        
        # 獲取干擾系統指標
        interference_metrics = await interference_service.get_simulation_metrics(3600.0)
        
        # 統一指標格式
        unified_metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "channel_simulation": {
                "total_simulations": channel_metrics.total_channels_processed,
                "total_conversions": len(conversion_history),
                "average_processing_time_ms": channel_metrics.average_conversion_time_ms,
                "gpu_utilization": channel_metrics.gpu_utilization,
                "memory_usage_mb": channel_metrics.memory_usage_mb,
                "cache_hit_rate": conversion_service.get_cache_hit_rate(),
            },
            "interference_simulation": {
                "total_simulations": interference_metrics.total_simulations,
                "total_ai_decisions": interference_metrics.total_ai_decisions,
                "average_detection_time_ms": interference_metrics.average_detection_time_ms,
                "success_rate": interference_metrics.success_rate,
            },
            "system_performance": {
                "active_channel_simulations": len(sionna_service.active_simulations),
                "active_interference_simulations": len(interference_service.active_simulations),
                "ai_ran_available": ai_ran_service.ai_available,
            },
        }
        
        return {"success": True, "metrics": unified_metrics}
        
    except Exception as e:
        logger.error(f"獲取指標失敗: {e}")
        raise HTTPException(status_code=500, detail=f"指標獲取失敗: {str(e)}")


# ============================================================================
# 背景任務
# ============================================================================

async def _update_simulation_history(
    request: InterferenceSimulationRequest, response: InterferenceSimulationResponse
):
    """更新模擬歷史（背景任務）"""
    try:
        logger.info(f"模擬歷史已更新: {response.simulation_id}")
    except Exception as e:
        logger.error(f"更新模擬歷史失敗: {e}")


async def _train_ai_model(request: AIRANControlRequest, response: AIRANControlResponse):
    """訓練AI模型（背景任務）"""
    try:
        logger.info(f"AI模型訓練任務已提交: {response.control_id}")
    except Exception as e:
        logger.error(f"AI模型訓練失敗: {e}")