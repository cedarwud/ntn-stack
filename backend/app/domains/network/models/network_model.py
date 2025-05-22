from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from sqlmodel import SQLModel, Relationship, Column, JSON
from enum import Enum


class SubscriberStatus(str, Enum):
    """用戶狀態枚舉"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class NetworkSliceType(int, Enum):
    """網路切片類型枚舉"""

    EMBB = 1  # 增強型行動寬頻
    URLLC = 2  # 超可靠低延遲通信
    MMTC = 3  # 大規模機器類型通信


class Subscriber(BaseModel):
    """5G網路用戶模型"""

    # 基本識別資訊
    imsi: str = Field(..., description="國際移動用戶識別碼(IMSI)")
    key: str = Field(..., description="用戶驗證密鑰")
    opc: str = Field(..., description="運營商認證碼")
    status: SubscriberStatus = Field(
        default=SubscriberStatus.ACTIVE, description="用戶狀態"
    )

    # 訂閱資料
    apn: str = Field(default="internet", description="接入點名稱")
    sst: int = Field(default=1, description="切片服務類型")
    sd: str = Field(default="0xffffff", description="切片區分符")

    # 時間相關
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="創建時間"
    )
    updated_at: Optional[datetime] = Field(None, description="最後更新時間")


class GNodeBStatus(str, Enum):
    """gNodeB狀態枚舉"""

    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
    UNKNOWN = "unknown"


class UEStatus(str, Enum):
    """UE狀態枚舉"""

    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    REGISTERING = "registering"
    ERROR = "error"
    UNKNOWN = "unknown"


class GNodeB(BaseModel):
    """5G基站模型"""

    # 基本資訊
    id: str = Field(..., description="基站ID")
    name: Optional[str] = Field(None, description="基站名稱")
    status: GNodeBStatus = Field(default=GNodeBStatus.UNKNOWN, description="基站狀態")

    # 網路配置
    mcc: str = Field(..., description="移動國家代碼")
    mnc: str = Field(..., description="移動網路代碼")
    tac: str = Field(..., description="跟蹤區域碼")
    nci: str = Field(..., description="NR小區識別碼")

    # 其他配置
    amf_addr: Optional[str] = Field(None, description="接入和移動管理功能地址")
    gnb_addr: Optional[str] = Field(None, description="gNodeB IP地址")

    # 詳細資訊（存儲為JSON格式）
    config: Optional[Dict[str, Any]] = Field(None, description="完整配置")


class UE(BaseModel):
    """用戶終端設備模型"""

    # 基本資訊
    id: str = Field(..., description="UE ID")
    name: Optional[str] = Field(None, description="UE名稱")
    imsi: str = Field(..., description="國際移動用戶識別碼")
    status: UEStatus = Field(default=UEStatus.UNKNOWN, description="UE狀態")

    # 網路配置
    mcc: str = Field(..., description="移動國家代碼")
    mnc: str = Field(..., description="移動網路代碼")
    key: str = Field(..., description="用戶驗證密鑰")
    opc: str = Field(..., description="運營商認證碼")

    # 其他資訊
    apn: str = Field(default="internet", description="接入點名稱")
    sst: int = Field(default=1, description="切片服務類型")
    sd: str = Field(default="0xffffff", description="切片區分符")
    connected_gnb: Optional[str] = Field(None, description="連接的gNodeB ID")
    ip_addr: Optional[str] = Field(None, description="分配的IP地址")

    # 詳細資訊（存儲為JSON格式）
    config: Optional[Dict[str, Any]] = Field(None, description="完整配置")
