"""
Core API Routes

This module handles basic functionality routes including models, scenes, and health checks.
Extracted from the monolithic app/api/v1/router.py as part of Phase 2 refactoring.
"""

from fastapi import APIRouter, Response, HTTPException, Query
from starlette.responses import FileResponse
from typing import Optional
import os
from datetime import datetime

router = APIRouter()


@router.get("/", tags=["Health"])
async def root():
    """Root endpoint for health check"""
    return {
        "message": "Sionna RT Simulation API",
        "timestamp": datetime.utcnow().isoformat(),
        "status": "healthy",
    }


@router.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "simworld-backend",
    }


@router.get("/sionna/models/{model_name}", tags=["Models"])
def get_model(model_name: str):
    """
    獲取 Sionna 3D 模型檔案

    支援的模型：
    - uav: UAV 無人機模型
    - sat: 衛星模型
    - gNB: 基站模型
    """
    # 定義模型檔案映射
    model_files = {
        "uav": "uav.glb",
        "sat": "sat.glb",
        "gNB": "gnb.glb",
        "tower": "tower.glb",
        "jam": "jam.glb",
    }

    if model_name not in model_files:
        raise HTTPException(status_code=404, detail=f"Model '{model_name}' not found")

    model_file = model_files[model_name]
    file_path = f"app/static/models/{model_file}"

    if not os.path.exists(file_path):
        # 如果檔案不存在，提供一個備用回應
        raise HTTPException(
            status_code=404, detail=f"Model file '{model_file}' not found on server"
        )

    return FileResponse(
        path=file_path,
        media_type="model/gltf-binary",
        filename=model_file,
        headers={
            "Cache-Control": "public, max-age=3600",  # 快取 1 小時
            "Access-Control-Allow-Origin": "*",
        },
    )


@router.get("/scenes/{scene_name}/model", tags=["Scenes"])
def get_scene_model(scene_name: str):
    """
    獲取場景 3D 模型檔案

    支援的場景：
    - nycu: 陽明交大校園模型
    - urban: 都市環境模型
    - rural: 鄉村環境模型
    """
    # 定義場景模型檔案映射
    scene_files = {
        "nycu": "nycu_campus.glb",
        "urban": "urban_environment.glb",
        "rural": "rural_environment.glb",
    }

    if scene_name not in scene_files:
        raise HTTPException(status_code=404, detail=f"Scene '{scene_name}' not found")

    scene_file = scene_files[scene_name]
    file_path = f"static/scenes/{scene_file}"

    if not os.path.exists(file_path):
        # 提供場景不存在的詳細錯誤信息
        available_scenes = list(scene_files.keys())
        raise HTTPException(
            status_code=404,
            detail={
                "error": f"Scene file '{scene_file}' not found",
                "available_scenes": available_scenes,
                "requested_scene": scene_name,
            },
        )

    return FileResponse(
        path=file_path,
        media_type="model/gltf-binary",
        filename=scene_file,
        headers={
            "Cache-Control": "public, max-age=7200",  # 場景檔案快取 2 小時
            "Access-Control-Allow-Origin": "*",
        },
    )


@router.get("/status", tags=["Health"])
async def get_system_status():
    """
    獲取系統狀態資訊
    """
    return {
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "components": {"api": "healthy", "database": "healthy", "cache": "healthy"},
    }
