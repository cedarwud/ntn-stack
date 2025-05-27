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
    get_scene_xml_path,
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
async def get_cfr_plot(
    session: AsyncSession = Depends(get_session),
    scene: str = Query("nycu", description="場景名稱 (nycu, lotus)"),
):
    """產生並回傳通道頻率響應 (CFR) 圖"""
    logger.info(f"--- API Request: /cfr-plot?scene={scene} ---")

    try:
        success = await sionna_service.generate_cfr_plot(
            session=session, output_path=str(CFR_PLOT_IMAGE_PATH), scene_name=scene
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
    scene: str = Query("nycu", description="場景名稱 (nycu, lotus)"),
    sinr_vmin: float = Query(-40.0, description="SINR 最小值 (dB)"),
    sinr_vmax: float = Query(0.0, description="SINR 最大值 (dB)"),
    cell_size: float = Query(1.0, description="Radio map 網格大小 (m)"),
    samples_per_tx: int = Query(10**7, description="每個發射器的採樣數量"),
):
    """產生並回傳 SINR 地圖"""
    logger.info(
        f"--- API Request: /sinr-map?scene={scene}&sinr_vmin={sinr_vmin}&sinr_vmax={sinr_vmax}&cell_size={cell_size}&samples_per_tx={samples_per_tx} ---"
    )

    try:
        success = await sionna_service.generate_sinr_map(
            session=session,
            output_path=str(SINR_MAP_IMAGE_PATH),
            scene_name=scene,
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
async def get_doppler_plots(
    session: AsyncSession = Depends(get_session),
    scene: str = Query("nycu", description="場景名稱 (nycu, lotus)"),
):
    """產生並回傳延遲多普勒圖"""
    logger.info(f"--- API Request: /doppler-plots?scene={scene} ---")

    try:
        success = await sionna_service.generate_doppler_plots(
            session, str(DOPPLER_IMAGE_PATH), scene_name=scene
        )

        if not success:
            raise HTTPException(status_code=500, detail="產生延遲多普勒圖失敗")

        return create_image_response(str(DOPPLER_IMAGE_PATH), "delay_doppler.png")
    except Exception as e:
        logger.error(f"生成延遲多普勒圖時出錯: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"生成延遲多普勒圖時出錯: {str(e)}")


@router.get("/channel-response", response_description="通道響應圖")
async def get_channel_response(
    session: AsyncSession = Depends(get_session),
    scene: str = Query("nycu", description="場景名稱 (nycu, lotus)"),
):
    """產生並回傳通道響應圖，顯示 H_des、H_jam 和 H_all 的三維圖"""
    logger.info(f"--- API Request: /channel-response?scene={scene} ---")

    try:
        success = await sionna_service.generate_channel_response_plots(
            session,
            str(CHANNEL_RESPONSE_IMAGE_PATH),
            scene_name=scene,
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


@router.get("/scenes", response_description="獲取可用場景列表")
async def get_available_scenes():
    """獲取系統中所有可用場景的列表"""
    logger.info("--- API Request: /scenes (獲取可用場景列表) ---")

    try:
        from app.core.config import SCENE_DIR
        import os

        # 檢查場景目錄是否存在
        if not os.path.exists(SCENE_DIR):
            return {"scenes": [], "default": "NYCU"}

        # 獲取所有子目錄作為場景名稱
        scenes = []
        for item in os.listdir(SCENE_DIR):
            scene_path = os.path.join(SCENE_DIR, item)
            if os.path.isdir(scene_path):
                # 檢查是否有GLB模型文件
                if os.path.exists(os.path.join(scene_path, f"{item}.glb")):
                    scenes.append(
                        {
                            "name": item,
                            "has_model": True,
                            "has_xml": os.path.exists(
                                os.path.join(scene_path, f"{item}.xml")
                            ),
                        }
                    )

        # 當沒有場景時返回空列表
        if not scenes:
            return {"scenes": [], "default": "NYCU"}

        return {"scenes": scenes, "default": "NYCU"}
    except Exception as e:
        logger.error(f"獲取場景列表時出錯: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"獲取場景列表時出錯: {str(e)}")


@router.get("/scene/{scene_name}", response_description="獲取特定場景信息")
async def get_scene_info(scene_name: str):
    """獲取特定場景的詳細信息"""
    logger.info(f"--- API Request: /scene/{scene_name} (獲取場景信息) ---")

    try:
        from app.core.config import (
            get_scene_dir,
            get_scene_model_path,
            get_scene_xml_path,
        )
        import os

        scene_dir = get_scene_dir(scene_name)
        if not os.path.exists(scene_dir):
            raise HTTPException(status_code=404, detail=f"場景 {scene_name} 不存在")

        # 檢查場景文件
        model_path = get_scene_model_path(scene_name)
        xml_path = get_scene_xml_path(scene_name)

        # 獲取場景中的紋理文件
        textures = []
        textures_dir = os.path.join(scene_dir, "textures")
        if os.path.exists(textures_dir):
            textures = [
                f
                for f in os.listdir(textures_dir)
                if os.path.isfile(os.path.join(textures_dir, f))
            ]

        return {
            "name": scene_name,
            "has_model": os.path.exists(model_path),
            "has_xml": os.path.exists(xml_path),
            "textures": textures,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取場景 {scene_name} 信息時出錯: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"獲取場景信息時出錯: {str(e)}")


@router.get("/scene/{scene_name}/model", response_description="獲取場景模型文件")
async def get_scene_model(scene_name: str):
    """獲取特定場景的3D模型文件"""
    logger.info(f"--- API Request: /scene/{scene_name}/model (獲取場景模型) ---")

    try:
        from app.core.config import get_scene_model_path
        import os

        model_path = get_scene_model_path(scene_name)
        if not os.path.exists(model_path):
            raise HTTPException(
                status_code=404, detail=f"場景 {scene_name} 的模型不存在"
            )

        return StreamingResponse(
            open(model_path, "rb"),
            media_type="model/gltf-binary",
            headers={"Content-Disposition": f"attachment; filename={scene_name}.glb"},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取場景 {scene_name} 模型時出錯: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"獲取場景模型時出錯: {str(e)}")
