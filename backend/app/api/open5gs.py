from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any, Optional

from app.services.open5gs_service import Open5GSService

router = APIRouter()
open5gs_service = Open5GSService()


@router.get("/subscribers", response_model=List[Dict[str, Any]])
async def get_subscribers():
    """獲取所有註冊的用戶"""
    return await open5gs_service.get_subscribers()


@router.get("/subscribers/{imsi}", response_model=Dict[str, Any])
async def get_subscriber(imsi: str):
    """獲取特定IMSI的用戶信息"""
    subscriber = await open5gs_service.get_subscriber_by_imsi(imsi)
    if not subscriber:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"用戶 {imsi} 未找到"
        )
    return subscriber


@router.post("/subscribers", status_code=status.HTTP_201_CREATED)
async def create_subscriber(
    imsi: str,
    key: str,
    opc: str,
    apn: str = "internet",
    sst: int = 1,
    sd: str = "0xffffff",
):
    """創建新用戶"""
    success = await open5gs_service.add_subscriber(imsi, key, opc, apn, sst, sd)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"創建用戶 {imsi} 失敗",
        )
    return {"message": f"用戶 {imsi} 創建成功"}


@router.delete("/subscribers/{imsi}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subscriber(imsi: str):
    """刪除用戶"""
    success = await open5gs_service.remove_subscriber(imsi)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"用戶 {imsi} 未找到或刪除失敗",
        )
    return None
