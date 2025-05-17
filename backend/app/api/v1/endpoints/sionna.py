import logging
import os
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import sionna.rt as rt
from pathlib import Path
from typing import List, Optional

import numpy as np
from pydantic import BaseModel

from app.api.deps import get_session  # Import dependency
from app.services.sionna_simulation import (  # Import service functions
    generate_empty_scene_image,
    generate_cfr_plot,  # 新增: 導入剛添加的 CFR 繪圖函數
    generate_sinr_map,  # 新增: 導入 SINR 地圖生成函數
    generate_doppler_plots,  # 新增: 導入延遲多普勒圖生成函數
    generate_channel_response_plots,  # 新增: 導入通道響應圖生成函數
    verify_output_file,  # 新增: 導入文件驗證函數
)
from app.core.config import (  # Import constants
    STATIC_IMAGES_DIR,
    MODELS_DIR,
    CFR_PLOT_IMAGE_PATH,  # 新增: 導入 CFR 圖片路徑
    SINR_MAP_IMAGE_PATH,  # 新增: 導入 SINR 地圖路徑
    CHANNEL_RESPONSE_IMAGE_PATH,  # 新增: 導入通道響應圖路徑
    DOPPLER_IMAGE_PATH,  # 新增: 導入新的延遲多普勒圖路徑
)
from app.services import crud_device  # 新增: 導入 crud_device 以獲取設備資料
from app.db.models import DeviceRole  # 新增: 導入 DeviceRole 枚舉

# 新增: 導入 run_in_threadpool
from fastapi.concurrency import run_in_threadpool

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


@router.get("/models/{model_name}", tags=["Models"])
async def get_model_glb(model_name: str):
    """
    提供指定名稱的 3D 模型 GLB 檔案。
    """
    # **安全性**: 基本的檔名驗證，防止路徑遍歷
    if ".." in model_name or "/" in model_name or "\\" in model_name:
        logger.warning(f"請求了無效的模型名稱: {model_name}")
        raise HTTPException(status_code=400, detail="無效的模型檔案名稱。")

    # 確保 MODELS_DIR 是 Path 對象 (通常在 config.py 中定義)
    if not isinstance(MODELS_DIR, Path):
        logger.error(f"MODELS_DIR 設定錯誤，不是 Path 對象: {MODELS_DIR}")
        raise HTTPException(
            status_code=500, detail="伺服器配置錯誤: 模型儲存路徑無效。"
        )

    model_path = MODELS_DIR / f"{model_name}.glb"  # 假設所有模型都是 .glb

    logger.info(f"請求模型檔案: {model_path}")

    if not model_path.is_file():
        logger.error(f"模型檔案不存在: {model_path}")
        raise HTTPException(status_code=404, detail=f"找不到模型檔案: {model_name}.glb")

    return FileResponse(
        path=str(model_path),
        media_type="model/gltf-binary",
        filename=f"{model_name}.glb",
    )


@router.get("/scene-image-devices", tags=["Sionna Simulation"])
async def get_scene_image_devices_endpoint():
    """產生並回傳只包含基本場景的圖像 (無設備)"""
    logger.info("--- API Request: /scene-image-devices (empty map only) ---")

    temp_image_path = STATIC_IMAGES_DIR / "scene_with_devices.png"

    success = await run_in_threadpool(
        generate_empty_scene_image, output_path=str(temp_image_path)
    )

    if not success:
        logger.error("無法產生空場景圖像")
        raise HTTPException(status_code=500, detail="無法產生空場景圖像")

    return create_image_response(str(temp_image_path), "scene_with_devices.png")


@router.get("/cfr-plot", tags=["Sionna Simulation"])
async def get_cfr_plot_endpoint(session: AsyncSession = Depends(get_session)):
    """產生並回傳通道頻率響應 (CFR) 圖"""
    logger.info("--- API Request: /cfr-plot ---")

    success = await generate_cfr_plot(
        session=session, output_path=str(CFR_PLOT_IMAGE_PATH)
    )

    if not success:
        logger.error("產生 CFR 圖失敗")
        raise HTTPException(status_code=500, detail="產生 CFR 圖失敗")

    return create_image_response(str(CFR_PLOT_IMAGE_PATH), "cfr_plot.png")


@router.get("/sinr-map", tags=["Sionna Simulation"])
async def get_sinr_map_endpoint(
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

    success = await generate_sinr_map(
        session=session,
        output_path=str(SINR_MAP_IMAGE_PATH),
        sinr_vmin=sinr_vmin,
        sinr_vmax=sinr_vmax,
        cell_size=cell_size,
        samples_per_tx=samples_per_tx,
    )

    if not success:
        logger.error("產生 SINR 地圖失敗")
        raise HTTPException(status_code=500, detail="產生 SINR 地圖失敗")

    return create_image_response(str(SINR_MAP_IMAGE_PATH), "sinr_map.png")


@router.get("/doppler-plots", tags=["Sionna Simulation"])
async def get_doppler_plots_endpoint(session: AsyncSession = Depends(get_session)):
    """產生並回傳延遲多普勒圖"""
    logger.info("--- API Request: /doppler-plots ---")

    success = await generate_doppler_plots(session, str(DOPPLER_IMAGE_PATH))

    if not success:
        logger.error("產生延遲多普勒圖失敗")
        raise HTTPException(status_code=500, detail="產生延遲多普勒圖失敗")

    return create_image_response(str(DOPPLER_IMAGE_PATH), "delay_doppler.png")


@router.get("/channel-response-plots", tags=["Sionna Simulation"])
async def get_channel_response_plots(session: AsyncSession = Depends(get_session)):
    """產生並回傳通道響應圖，顯示 H_des、H_jam 和 H_all 的三維圖"""
    logger.info("--- API Request: /channel-response-plots ---")

    success = await generate_channel_response_plots(
        session,
        str(CHANNEL_RESPONSE_IMAGE_PATH),
    )

    if not success:
        logger.error("產生通道響應圖失敗")
        raise HTTPException(status_code=500, detail="產生通道響應圖失敗")

    return create_image_response(
        str(CHANNEL_RESPONSE_IMAGE_PATH), "channel_response_plots.png"
    )
