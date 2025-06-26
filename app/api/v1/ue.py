"""UE 管理路由模組"""
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, Optional
from datetime import datetime

router = APIRouter(prefix="/ue", tags=["UE 管理"])


@router.get("/{imsi}")
async def get_ue_info(imsi: str) -> Dict[str, Any]:
    """獲取UE資訊"""
    return {
        "imsi": imsi,
        "status": "connected",
        "last_seen": datetime.utcnow().isoformat(),
        "message": "重構後的UE API"
    }


@router.get("/")
async def list_ues(
    status: Optional[str] = Query(None),
    limit: int = Query(100),
    offset: int = Query(0)
) -> Dict[str, Any]:
    """獲取UE列表"""
    return {
        "ues": [
            {"imsi": "001010000000001", "status": "connected"},
            {"imsi": "001010000000002", "status": "idle"}
        ],
        "total": 2,
        "message": "重構後的UE列表API"
    }