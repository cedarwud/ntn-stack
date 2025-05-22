import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path

from app.domains.network.models.network_model import Subscriber, GNodeB, UE
from app.domains.network.services.platform_service import platform_service

logger = logging.getLogger(__name__)
router = APIRouter()

# --- 用戶管理 API ---


@router.get("/subscribers", response_model=List[Subscriber])
async def get_subscribers():
    """獲取所有註冊的用戶"""
    return await platform_service.get_subscribers()


@router.get("/subscribers/{imsi}", response_model=Subscriber)
async def get_subscriber(imsi: str = Path(..., description="用戶的 IMSI 識別碼")):
    """獲取特定 IMSI 的用戶信息"""
    subscriber = await platform_service.get_subscriber(imsi)
    if not subscriber:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"用戶 {imsi} 未找到"
        )
    return subscriber


@router.post("/subscribers", status_code=status.HTTP_201_CREATED)
async def create_subscriber(
    imsi: str = Query(..., description="用戶的 IMSI 識別碼"),
    key: str = Query(..., description="用戶的密鑰"),
    opc: str = Query(..., description="用戶的 OPC 值"),
    apn: str = Query("internet", description="接入點名稱"),
    sst: int = Query(1, description="切片服務類型"),
    sd: str = Query("0xffffff", description="切片區分符"),
):
    """創建新用戶"""
    success = await platform_service.create_subscriber(imsi, key, opc, apn, sst, sd)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"創建用戶 {imsi} 失敗",
        )
    return {"message": f"用戶 {imsi} 創建成功"}


@router.delete("/subscribers/{imsi}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subscriber(imsi: str = Path(..., description="用戶的 IMSI 識別碼")):
    """刪除用戶"""
    success = await platform_service.delete_subscriber(imsi)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"用戶 {imsi} 未找到或刪除失敗",
        )
    return None


# --- gNodeB 管理 API ---


@router.get("/gnbs", response_model=List[GNodeB])
async def get_gnbs():
    """獲取所有 gNodeB 信息"""
    return await platform_service.get_gnbs()


@router.post("/gnbs/{gnb_id}/start", status_code=status.HTTP_200_OK)
async def start_gnb(gnb_id: str = Path(..., description="gNodeB 識別碼")):
    """啟動指定的 gNodeB"""
    success = await platform_service.start_gnb(gnb_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"啟動 gNodeB {gnb_id} 失敗",
        )
    return {"message": f"gNodeB {gnb_id} 啟動成功"}


@router.post("/gnbs/{gnb_id}/stop", status_code=status.HTTP_200_OK)
async def stop_gnb(gnb_id: str = Path(..., description="gNodeB 識別碼")):
    """停止指定的 gNodeB"""
    success = await platform_service.stop_gnb(gnb_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"停止 gNodeB {gnb_id} 失敗",
        )
    return {"message": f"gNodeB {gnb_id} 已停止"}


@router.get("/gnbs/{gnb_id}/status", response_model=GNodeB)
async def get_gnb_status(gnb_id: str = Path(..., description="gNodeB 識別碼")):
    """獲取 gNodeB 的狀態信息"""
    return await platform_service.get_gnb_status(gnb_id)


# --- UE 管理 API ---


@router.get("/ues", response_model=List[UE])
async def get_ues():
    """獲取所有 UE 信息"""
    return await platform_service.get_ues()


@router.post("/ues/{ue_id}/start", status_code=status.HTTP_200_OK)
async def start_ue(ue_id: str = Path(..., description="UE 識別碼")):
    """啟動指定的 UE"""
    success = await platform_service.start_ue(ue_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"啟動 UE {ue_id} 失敗",
        )
    return {"message": f"UE {ue_id} 啟動成功"}


@router.post("/ues/{ue_id}/stop", status_code=status.HTTP_200_OK)
async def stop_ue(ue_id: str = Path(..., description="UE 識別碼")):
    """停止指定的 UE"""
    success = await platform_service.stop_ue(ue_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"停止 UE {ue_id} 失敗",
        )
    return {"message": f"UE {ue_id} 已停止"}


@router.get("/ues/{ue_id}/status", response_model=UE)
async def get_ue_status(ue_id: str = Path(..., description="UE 識別碼")):
    """獲取 UE 的狀態信息"""
    return await platform_service.get_ue_status(ue_id)
