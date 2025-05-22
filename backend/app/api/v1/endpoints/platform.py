from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any, Optional

from app.domains.integration.dependencies import (
    get_open5gs_adapter,
    get_ueransim_adapter,
)
from app.domains.integration.open5gs.adapter import Open5GSAdapter
from app.domains.integration.ueransim.adapter import UERANSIMAdapter

router = APIRouter()

# --- Open5GS 相關端點 ---


@router.get("/open5gs/subscribers", response_model=List[Dict[str, Any]])
async def get_subscribers(open5gs: Open5GSAdapter = Depends(get_open5gs_adapter)):
    """獲取所有註冊的用戶"""
    return await open5gs.get_subscribers()


@router.get("/open5gs/subscribers/{imsi}", response_model=Dict[str, Any])
async def get_subscriber(
    imsi: str, open5gs: Open5GSAdapter = Depends(get_open5gs_adapter)
):
    """獲取特定IMSI的用戶信息"""
    subscriber = await open5gs.get_subscriber_by_imsi(imsi)
    if not subscriber:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"用戶 {imsi} 未找到"
        )
    return subscriber


@router.post("/open5gs/subscribers", status_code=status.HTTP_201_CREATED)
async def create_subscriber(
    imsi: str,
    key: str,
    opc: str,
    apn: str = "internet",
    sst: int = 1,
    sd: str = "0xffffff",
    open5gs: Open5GSAdapter = Depends(get_open5gs_adapter),
):
    """創建新用戶"""
    success = await open5gs.add_subscriber(imsi, key, opc, apn, sst, sd)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"創建用戶 {imsi} 失敗",
        )
    return {"message": f"用戶 {imsi} 創建成功"}


@router.delete("/open5gs/subscribers/{imsi}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subscriber(
    imsi: str, open5gs: Open5GSAdapter = Depends(get_open5gs_adapter)
):
    """刪除用戶"""
    success = await open5gs.remove_subscriber(imsi)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"用戶 {imsi} 未找到或刪除失敗",
        )
    return None


# --- UERANSIM 相關端點 ---


@router.get("/ueransim/gnbs", response_model=List[Dict[str, Any]])
async def get_gnbs(ueransim: UERANSIMAdapter = Depends(get_ueransim_adapter)):
    """獲取所有gNodeB信息"""
    return await ueransim.get_gnbs()


@router.get("/ueransim/ues", response_model=List[Dict[str, Any]])
async def get_ues(ueransim: UERANSIMAdapter = Depends(get_ueransim_adapter)):
    """獲取所有UE信息"""
    return await ueransim.get_ues()


@router.post("/ueransim/gnbs/{gnb_id}/start", status_code=status.HTTP_200_OK)
async def start_gnb(
    gnb_id: str, ueransim: UERANSIMAdapter = Depends(get_ueransim_adapter)
):
    """啟動指定的gNodeB"""
    success = await ueransim.start_gnb(gnb_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"啟動gNodeB {gnb_id} 失敗",
        )
    return {"message": f"gNodeB {gnb_id} 啟動成功"}


@router.post("/ueransim/gnbs/{gnb_id}/stop", status_code=status.HTTP_200_OK)
async def stop_gnb(
    gnb_id: str, ueransim: UERANSIMAdapter = Depends(get_ueransim_adapter)
):
    """停止指定的gNodeB"""
    success = await ueransim.stop_gnb(gnb_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"停止gNodeB {gnb_id} 失敗",
        )
    return {"message": f"gNodeB {gnb_id} 已停止"}


@router.post("/ueransim/ues/{ue_id}/start", status_code=status.HTTP_200_OK)
async def start_ue(
    ue_id: str, ueransim: UERANSIMAdapter = Depends(get_ueransim_adapter)
):
    """啟動指定的UE"""
    success = await ueransim.start_ue(ue_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"啟動UE {ue_id} 失敗",
        )
    return {"message": f"UE {ue_id} 啟動成功"}


@router.post("/ueransim/ues/{ue_id}/stop", status_code=status.HTTP_200_OK)
async def stop_ue(
    ue_id: str, ueransim: UERANSIMAdapter = Depends(get_ueransim_adapter)
):
    """停止指定的UE"""
    success = await ueransim.stop_ue(ue_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"停止UE {ue_id} 失敗",
        )
    return {"message": f"UE {ue_id} 已停止"}


@router.get("/ueransim/gnbs/{gnb_id}/status", response_model=Dict[str, Any])
async def get_gnb_status(
    gnb_id: str, ueransim: UERANSIMAdapter = Depends(get_ueransim_adapter)
):
    """獲取gNodeB的狀態信息"""
    return await ueransim.get_gnb_status(gnb_id)


@router.get("/ueransim/ues/{ue_id}/status", response_model=Dict[str, Any])
async def get_ue_status(
    ue_id: str, ueransim: UERANSIMAdapter = Depends(get_ueransim_adapter)
):
    """獲取UE的狀態信息"""
    return await ueransim.get_ue_status(ue_id)
