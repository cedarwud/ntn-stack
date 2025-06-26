"""
UE 管理路由模組
從 main.py 中提取的 UE 管理相關端點
"""
from fastapi import APIRouter, HTTPException, status, Query
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional, List
import logging

# 導入相關模型 - 使用絕對導入避免路徑問題
try:
    from netstack_api.models.responses import UEStatsResponse
    from netstack_api.models.requests import SliceSwitchRequest
except ImportError:
    # 如果絕對導入失敗，創建基本的模型類
    from pydantic import BaseModel
    
    class UEStatsResponse(BaseModel):
        imsi: str
        connection_time: int = 0
        data_usage: dict = {}
        rtt_ms: float = 0.0
        signal_strength: int = 0
    
    class SliceSwitchRequest(BaseModel):
        imsi: str
        target_slice: str

router = APIRouter(prefix="/api/v1", tags=["UE 管理"])
logger = logging.getLogger(__name__)


# 自定義響應類 (從 main.py 複製)
class CustomJSONResponse(JSONResponse):
    """自定義JSON響應類"""
    pass


@router.get("/ue/{imsi}")
async def get_ue_info(imsi: str):
    """
    取得指定 IMSI 的 UE 資訊

    Args:
        imsi: UE 的 IMSI 號碼 (例如: 999700000000001)

    Returns:
        UE 的詳細資訊，包括目前 Slice、APN 設定等
    """
    try:
        # 這裡需要從 FastAPI app.state 中獲取 ue_service
        # 暫時使用模擬數據，實際使用時需要注入依賴
        ue_info = {
            "imsi": imsi,
            "status": "connected",
            "current_slice": "slice_001",
            "apn": "internet",
            "location": {
                "latitude": 25.0330,
                "longitude": 121.5654
            }
        }

        if not ue_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"找不到 IMSI {imsi} 的 UE",
            )

        return CustomJSONResponse(content=ue_info)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("取得 UE 資訊失敗", extra={"imsi": imsi, "error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "取得 UE 資訊失敗", "message": str(e)},
        )


@router.get("/ue/{imsi}/stats", response_model=UEStatsResponse)
async def get_ue_stats(imsi: str):
    """
    取得指定 UE 的統計資訊

    Args:
        imsi: UE 的 IMSI 號碼

    Returns:
        UE 的統計資訊，包括連線時間、流量統計、RTT 等
    """
    try:
        # 暫時使用模擬數據
        stats = {
            "imsi": imsi,
            "connection_time": 3600,
            "data_usage": {
                "uplink": 1024000,
                "downlink": 2048000
            },
            "rtt_ms": 25.5,
            "signal_strength": -85
        }

        if not stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"找不到 IMSI {imsi} 的統計資料",
            )

        return UEStatsResponse(**stats)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("取得 UE 統計失敗", extra={"imsi": imsi, "error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "取得 UE 統計失敗", "message": str(e)},
        )


@router.get("/ue")
async def list_ues(
    slice_type: Optional[str] = Query(None, description="依 Slice 類型過濾"),
    status: Optional[str] = Query(None, description="依連線狀態過濾"),
    limit: int = Query(100, description="返回結果數量限制"),
    offset: int = Query(0, description="結果偏移量")
):
    """
    列出所有 UE 的基本資訊

    Args:
        slice_type: 可選的 Slice 類型過濾器
        status: 可選的連線狀態過濾器
        limit: 返回結果數量限制
        offset: 結果偏移量

    Returns:
        UE 列表和分頁資訊
    """
    try:
        # 暫時使用模擬數據
        ues = [
            {
                "imsi": "999700000000001",
                "status": "connected",
                "slice_type": "embb",
                "last_seen": "2024-06-26T05:15:00Z"
            },
            {
                "imsi": "999700000000002",
                "status": "idle", 
                "slice_type": "urllc",
                "last_seen": "2024-06-26T05:10:00Z"
            }
        ]

        # 應用過濾器
        if slice_type:
            ues = [ue for ue in ues if ue.get("slice_type") == slice_type]
        if status:
            ues = [ue for ue in ues if ue.get("status") == status]

        # 應用分頁
        total = len(ues)
        paged_ues = ues[offset:offset + limit]

        return {
            "ues": paged_ues,
            "pagination": {
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total
            }
        }

    except Exception as e:
        logger.error("列出 UE 失敗", extra={"error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "列出 UE 失敗", "message": str(e)},
        )