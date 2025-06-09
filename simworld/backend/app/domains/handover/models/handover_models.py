from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field as PydanticField
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import Integer, Float, String, DateTime, Text, Enum as SQLEnum


class HandoverStatus(str, Enum):
    """換手狀態枚舉"""
    IDLE = "idle"
    PREDICTING = "predicting"
    HANDOVER = "handover"
    COMPLETE = "complete"
    FAILED = "failed"


class HandoverTriggerType(str, Enum):
    """換手觸發類型"""
    MANUAL = "manual"
    AUTOMATIC = "automatic"
    PREDICTED = "predicted"
    EMERGENCY = "emergency"


# 預測資料表 (R table) - 根據 IEEE INFOCOM 2024 論文
class HandoverPredictionTable(SQLModel, table=True):
    """
    換手預測記錄表 (R table)
    根據 IEEE INFOCOM 2024 論文的 Fine-Grained Synchronized Algorithm
    """
    __tablename__ = "handover_prediction_table"

    id: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer, primary_key=True, autoincrement=True),
        description="主鍵 ID"
    )
    
    # 基本標識
    ue_id: int = Field(index=True, description="UE 設備 ID")
    prediction_id: str = Field(index=True, description="預測批次 ID")
    
    # 時間點 - T 和 T+Δt
    current_time: datetime = Field(description="當前時間 T")
    future_time: datetime = Field(description="預測時間 T+Δt")
    delta_t_seconds: int = Field(description="時間間隔 Δt (秒)")
    
    # 衛星選擇結果
    current_satellite_id: str = Field(description="當前最佳衛星 ID (AT)")
    future_satellite_id: str = Field(description="預測最佳衛星 ID (AT+Δt)")
    
    # 換手決策
    handover_required: bool = Field(default=False, description="是否需要換手")
    handover_trigger_time: Optional[datetime] = Field(
        default=None, 
        description="換手觸發時間 Tp (如需換手)"
    )
    
    # Binary Search Refinement 結果
    binary_search_iterations: int = Field(default=0, description="Binary Search 迭代次數")
    precision_achieved: float = Field(default=0.0, description="達到的精度 (秒)")
    search_details: Optional[str] = Field(default=None, description="搜索過程詳細資訊 JSON")
    
    # 預測置信度和品質
    prediction_confidence: float = Field(description="預測置信度 (0-1)")
    signal_quality_current: float = Field(description="當前衛星信號品質")
    signal_quality_future: float = Field(description="預測衛星信號品質")
    
    # 創建和更新時間
    created_at: datetime = Field(default_factory=datetime.utcnow, description="創建時間")
    updated_at: Optional[datetime] = Field(default=None, description="更新時間")


# Binary Search 迭代記錄
class BinarySearchIteration(BaseModel):
    """Binary Search Refinement 迭代記錄"""
    
    iteration: int = PydanticField(description="迭代次數")
    start_time: float = PydanticField(description="搜索開始時間 (timestamp)")
    end_time: float = PydanticField(description="搜索結束時間 (timestamp)")
    mid_time: float = PydanticField(description="中點時間 (timestamp)")
    satellite: str = PydanticField(description="中點時間選中的衛星")
    precision: float = PydanticField(description="當前精度 (秒)")
    completed: bool = PydanticField(description="是否完成")


# 簡化的預測記錄 (用於服務層)
class HandoverPredictionRecord(BaseModel):
    """換手預測記錄 (用於內存快取)"""
    
    ue_id: str = PydanticField(description="UE 設備 ID")
    current_satellite: str = PydanticField(description="當前最佳衛星 (AT)")
    predicted_satellite: str = PydanticField(description="預測最佳衛星 (AT+Δt)")
    handover_time: Optional[float] = PydanticField(default=None, description="換手觸發時間 Tp")
    prediction_confidence: float = PydanticField(description="預測置信度")
    last_updated: datetime = PydanticField(description="最後更新時間")


# 手動換手請求
class ManualHandoverRequest(SQLModel, table=True):
    """手動換手請求記錄"""
    __tablename__ = "manual_handover_request"

    id: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer, primary_key=True, autoincrement=True),
        description="主鍵 ID"
    )
    
    ue_id: int = Field(index=True, description="UE 設備 ID")
    from_satellite_id: str = Field(description="源衛星 ID")
    to_satellite_id: str = Field(description="目標衛星 ID")
    
    trigger_type: HandoverTriggerType = Field(
        default=HandoverTriggerType.MANUAL,
        sa_column=Column(SQLEnum(HandoverTriggerType)),
        description="觸發類型"
    )
    
    status: HandoverStatus = Field(
        default=HandoverStatus.IDLE,
        sa_column=Column(SQLEnum(HandoverStatus)),
        description="換手狀態"
    )
    
    # 換手執行數據
    request_time: datetime = Field(default_factory=datetime.utcnow, description="請求時間")
    start_time: Optional[datetime] = Field(default=None, description="開始時間")
    completion_time: Optional[datetime] = Field(default=None, description="完成時間")
    duration_seconds: Optional[float] = Field(default=None, description="持續時間 (秒)")
    
    # 結果和元數據
    success: Optional[bool] = Field(default=None, description="是否成功")
    error_message: Optional[str] = Field(default=None, description="錯誤訊息")
    extra_data: Optional[str] = Field(default=None, description="額外資料 JSON")


# API 請求/響應模型
class HandoverPredictionRequest(BaseModel):
    """換手預測請求"""
    
    ue_id: int = PydanticField(description="UE 設備 ID")
    delta_t_seconds: int = PydanticField(default=5, description="預測時間間隔 (秒)")
    precision_threshold: float = PydanticField(default=0.1, description="精度閾值 (秒)")


class HandoverPredictionResponse(BaseModel):
    """換手預測響應"""
    
    prediction_id: str = PydanticField(description="預測批次 ID")
    ue_id: int = PydanticField(description="UE 設備 ID")
    
    # 時間資訊
    current_time: float = PydanticField(description="當前時間 T (timestamp)")
    future_time: float = PydanticField(description="預測時間 T+Δt (timestamp)")
    delta_t_seconds: int = PydanticField(description="時間間隔 Δt")
    
    # 衛星選擇結果
    current_satellite: Dict[str, Any] = PydanticField(description="當前最佳衛星資訊")
    future_satellite: Dict[str, Any] = PydanticField(description="預測最佳衛星資訊")
    
    # 換手決策
    handover_required: bool = PydanticField(description="是否需要換手")
    handover_trigger_time: Optional[float] = PydanticField(
        default=None, 
        description="換手觸發時間 Tp (timestamp)"
    )
    
    # Binary Search 結果
    binary_search_result: Optional[Dict[str, Any]] = PydanticField(
        default=None, 
        description="Binary Search 精細化結果"
    )
    
    # 預測品質
    prediction_confidence: float = PydanticField(description="預測置信度")
    accuracy_percentage: float = PydanticField(description="預測準確率百分比")


class ManualHandoverTriggerRequest(BaseModel):
    """手動換手觸發請求"""
    
    ue_id: int = PydanticField(description="UE 設備 ID")
    target_satellite_id: str = PydanticField(description="目標衛星 ID")
    trigger_type: HandoverTriggerType = PydanticField(
        default=HandoverTriggerType.MANUAL,
        description="觸發類型"
    )


class ManualHandoverResponse(BaseModel):
    """手動換手響應"""
    
    handover_id: int = PydanticField(description="換手請求 ID")
    ue_id: int = PydanticField(description="UE 設備 ID")
    from_satellite_id: str = PydanticField(description="源衛星 ID")
    to_satellite_id: str = PydanticField(description="目標衛星 ID")
    
    status: HandoverStatus = PydanticField(description="當前狀態")
    request_time: datetime = PydanticField(description="請求時間")
    
    # 執行結果 (異步更新)
    start_time: Optional[datetime] = PydanticField(default=None, description="開始時間")
    completion_time: Optional[datetime] = PydanticField(default=None, description="完成時間")
    success: Optional[bool] = PydanticField(default=None, description="是否成功")
    error_message: Optional[str] = PydanticField(default=None, description="錯誤訊息")


class HandoverStatusResponse(BaseModel):
    """換手狀態查詢響應"""
    
    handover_id: int = PydanticField(description="換手請求 ID")
    status: HandoverStatus = PydanticField(description="當前狀態")
    progress_percentage: Optional[float] = PydanticField(
        default=None, 
        description="進度百分比 (0-100)"
    )
    estimated_completion_time: Optional[datetime] = PydanticField(
        default=None, 
        description="預計完成時間"
    )