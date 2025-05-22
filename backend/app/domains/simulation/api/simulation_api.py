import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.core.config import (
    CFR_PLOT_IMAGE_PATH,
    SINR_MAP_IMAGE_PATH,
    DOPPLER_IMAGE_PATH,
    CHANNEL_RESPONSE_IMAGE_PATH,
)
from app.domains.simulation.models.simulation_model import (
    SimulationParameters,
    SimulationImageRequest,
)
from app.domains.simulation.services.sionna_service import sionna_service

logger = logging.getLogger(__name__)
router = APIRouter()


# 通用的圖像回應函數
def create_image_response(image_path: str, filename: str):
    """建立統一的圖像檔案串流回應"""
    logger.info(f"返回圖像，文件路徑: {image_path}")

    def iterfile():
        with open(image_path, "rb") as f:
            chunk = f.read(4096)
            while chunk:
                yield chunk
                chunk = f.read(4096)

    return StreamingResponse(
        iterfile(),
        media_type="image/png",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/scene-image", response_description="空場景圖像")
async def get_scene_image():
    """產生並回傳只包含基本場景的圖像 (無設備)"""
    logger.info("--- API Request: /scene-image (empty map) ---")

    try:
        output_path = "app/static/images/scene_empty.png"
        success = await sionna_service.generate_empty_scene_image(output_path)

        if not success:
            raise HTTPException(status_code=500, detail="無法產生空場景圖像")

        return create_image_response(output_path, "scene_empty.png")
    except Exception as e:
        logger.error(f"生成空場景圖像時出錯: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"生成場景圖像時出錯: {str(e)}")


@router.get("/cfr-plot", response_description="通道頻率響應圖")
async def get_cfr_plot(session: AsyncSession = Depends(get_session)):
    """產生並回傳通道頻率響應 (CFR) 圖"""
    logger.info("--- API Request: /cfr-plot ---")

    try:
        success = await sionna_service.generate_cfr_plot(
            session=session, output_path=str(CFR_PLOT_IMAGE_PATH)
        )

        if not success:
            raise HTTPException(status_code=500, detail="產生 CFR 圖失敗")

        return create_image_response(str(CFR_PLOT_IMAGE_PATH), "cfr_plot.png")
    except Exception as e:
        logger.error(f"生成 CFR 圖時出錯: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"生成 CFR 圖時出錯: {str(e)}")


@router.get("/sinr-map", response_description="SINR 地圖")
async def get_sinr_map(
    session: AsyncSession = Depends(get_session),
    sinr_vmin: float = Query(-40.0, description="SINR 最小值 (dB)"),
    sinr_vmax: float = Query(0.0, description="SINR 最大值 (dB)"),
    cell_size: float = Query(1.0, description="Radio map 網格大小 (m)"),
    samples_per_tx: int = Query(10**7, description="每個發射器的採樣數量"),
):
    """產生並回傳 SINR 地圖"""
    logger.info(
        f"--- API Request: /sinr-map?sinr_vmin={sinr_vmin}&sinr_vmax={sinr_vmax}&cell_size={cell_size}&samples_per_tx={samples_per_tx} ---"
    )

    try:
        success = await sionna_service.generate_sinr_map(
            session=session,
            output_path=str(SINR_MAP_IMAGE_PATH),
            sinr_vmin=sinr_vmin,
            sinr_vmax=sinr_vmax,
            cell_size=cell_size,
            samples_per_tx=samples_per_tx,
        )

        if not success:
            raise HTTPException(status_code=500, detail="產生 SINR 地圖失敗")

        return create_image_response(str(SINR_MAP_IMAGE_PATH), "sinr_map.png")
    except Exception as e:
        logger.error(f"生成 SINR 地圖時出錯: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"生成 SINR 地圖時出錯: {str(e)}")


@router.get("/doppler-plots", response_description="延遲多普勒圖")
async def get_doppler_plots(session: AsyncSession = Depends(get_session)):
    """產生並回傳延遲多普勒圖"""
    logger.info("--- API Request: /doppler-plots ---")

    try:
        success = await sionna_service.generate_doppler_plots(
            session, str(DOPPLER_IMAGE_PATH)
        )

        if not success:
            raise HTTPException(status_code=500, detail="產生延遲多普勒圖失敗")

        return create_image_response(str(DOPPLER_IMAGE_PATH), "delay_doppler.png")
    except Exception as e:
        logger.error(f"生成延遲多普勒圖時出錯: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"生成延遲多普勒圖時出錯: {str(e)}")


@router.get("/channel-response", response_description="通道響應圖")
async def get_channel_response(session: AsyncSession = Depends(get_session)):
    """產生並回傳通道響應圖，顯示 H_des、H_jam 和 H_all 的三維圖"""
    logger.info("--- API Request: /channel-response ---")

    try:
        success = await sionna_service.generate_channel_response_plots(
            session,
            str(CHANNEL_RESPONSE_IMAGE_PATH),
        )

        if not success:
            raise HTTPException(status_code=500, detail="產生通道響應圖失敗")

        return create_image_response(
            str(CHANNEL_RESPONSE_IMAGE_PATH), "channel_response_plots.png"
        )
    except Exception as e:
        logger.error(f"生成通道響應圖時出錯: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"生成通道響應圖時出錯: {str(e)}")


@router.post("/run", response_model=Dict[str, Any])
async def run_simulation(
    params: SimulationParameters, session: AsyncSession = Depends(get_session)
):
    """執行通用模擬"""
    logger.info(f"--- API Request: /run (type: {params.simulation_type}) ---")

    try:
        result = await sionna_service.run_simulation(session, params)

        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error_message", "模擬執行失敗"),
            )

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"執行模擬時出錯: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"執行模擬時出錯: {str(e)}",
        )
