"""
NetStack API 回應模型

定義 API 端點的回應資料結構
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """健康檢查回應"""

    overall_status: str = Field(..., description="整體健康狀態", example="healthy")

    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="檢查時間 (ISO 8601 格式)",
    )

    services: Dict[str, Dict[str, Any]] = Field(
        ...,
        description="各服務健康狀態",
        example={
            "mongodb": {"status": "healthy", "response_time": 0.05},
            "redis": {"status": "healthy", "response_time": 0.02},
            "open5gs": {"status": "healthy", "services_count": 11},
        },
    )

    version: str = Field(default="1.0.0", description="API 版本")


class SliceInfo(BaseModel):
    """Slice 資訊"""

    sst: int = Field(..., description="Slice/Service Type", example=1)

    sd: str = Field(..., description="Slice Differentiator", example="0x111111")

    slice_type: str = Field(..., description="Slice 類型名稱", example="eMBB")


class UEInfoResponse(BaseModel):
    """UE 資訊回應"""

    imsi: str = Field(..., description="UE 的 IMSI 號碼", example="999700000000001")

    apn: str = Field(..., description="接入點名稱", example="internet")

    slice: SliceInfo = Field(..., description="目前 Slice 資訊")

    status: str = Field(..., description="UE 狀態", example="registered")

    ip_address: Optional[str] = Field(
        None, description="分配的 IP 位址", example="10.45.0.2"
    )

    last_seen: Optional[str] = Field(None, description="最後活動時間 (ISO 8601 格式)")

    created_at: str = Field(..., description="註冊時間 (ISO 8601 格式)")


class UEStatsResponse(BaseModel):
    """UE 統計資訊回應"""

    imsi: str = Field(..., description="UE 的 IMSI 號碼", example="999700000000001")

    connection_time: int = Field(..., description="連線時間 (秒)", example=3600)

    bytes_uploaded: int = Field(default=0, description="上傳位元組數", example=1024000)

    bytes_downloaded: int = Field(
        default=0, description="下載位元組數", example=5120000
    )

    rtt_ms: Optional[float] = Field(None, description="往返延遲 (毫秒)", example=45.2)

    slice_switches: int = Field(default=0, description="Slice 切換次數", example=2)

    last_rtt_test: Optional[str] = Field(
        None, description="最後 RTT 測試時間 (ISO 8601 格式)"
    )


class SliceSwitchResponse(BaseModel):
    """Slice 切換回應"""

    imsi: str = Field(..., description="UE 的 IMSI 號碼", example="999700000000001")

    previous_slice: SliceInfo = Field(..., description="切換前的 Slice")

    new_slice: SliceInfo = Field(..., description="切換後的 Slice")

    switch_time: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="切換時間 (ISO 8601 格式)",
    )

    success: bool = Field(..., description="切換是否成功", example=True)

    message: str = Field(..., description="切換結果訊息", example="Slice 切換成功")


class ErrorResponse(BaseModel):
    """錯誤回應"""

    error: str = Field(..., description="錯誤類型", example="ValidationError")

    message: str = Field(..., description="錯誤訊息", example="IMSI 格式不正確")

    status_code: int = Field(..., description="HTTP 狀態碼", example=400)

    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="錯誤發生時間 (ISO 8601 格式)",
    )


class SliceTypeResponse(BaseModel):
    """Slice 類型回應"""

    name: str = Field(..., description="Slice 名稱", example="eMBB")

    sst: int = Field(..., description="Slice/Service Type", example=1)

    sd: str = Field(..., description="Slice Differentiator", example="0x111111")

    description: str = Field(..., description="Slice 描述", example="增強型行動寬頻")

    characteristics: Dict[str, str] = Field(
        ...,
        description="Slice 特性",
        example={"latency": "~100ms", "bandwidth": "高", "reliability": "99%"},
    )


class SliceTypesResponse(BaseModel):
    """Slice 類型列表回應"""

    slice_types: List[SliceTypeResponse] = Field(
        ..., description="支援的 Slice 類型列表"
    )
