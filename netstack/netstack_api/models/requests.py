"""
NetStack API 請求模型

定義 API 端點的請求資料結構
"""

from typing import Optional
from pydantic import BaseModel, Field, validator


class SliceSwitchRequest(BaseModel):
    """Slice 切換請求"""
    
    imsi: str = Field(
        ...,
        description="UE 的 IMSI 號碼",
        example="999700000000001",
        min_length=15,
        max_length=15
    )
    
    target_slice: str = Field(
        ...,
        description="目標 Slice 類型",
        example="uRLLC"
    )
    
    @validator('imsi')
    def validate_imsi(cls, v):
        """驗證 IMSI 格式"""
        if not v.isdigit():
            raise ValueError('IMSI 必須為數字')
        if not v.startswith('999700'):
            raise ValueError('IMSI 必須以 999700 開頭')
        return v
    
    @validator('target_slice')
    def validate_target_slice(cls, v):
        """驗證目標 Slice"""
        allowed_slices = ['eMBB', 'uRLLC']
        if v not in allowed_slices:
            raise ValueError(f'目標 Slice 必須為 {allowed_slices} 之一')
        return v


class UERegistrationRequest(BaseModel):
    """UE 註冊請求"""
    
    imsi: str = Field(
        ...,
        description="UE 的 IMSI 號碼",
        example="999700000000001"
    )
    
    key: str = Field(
        ...,
        description="UE 的 K 金鑰",
        example="465B5CE8B199B49FAA5F0A2EE238A6BC"
    )
    
    opc: str = Field(
        ...,
        description="UE 的 OPc 值",
        example="E8ED289DEBA952E4283B54E88E6183CA"
    )
    
    apn: str = Field(
        default="internet",
        description="接入點名稱",
        example="internet"
    )
    
    slice_type: str = Field(
        ...,
        description="預設 Slice 類型",
        example="eMBB"
    )
    
    @validator('slice_type')
    def validate_slice_type(cls, v):
        """驗證 Slice 類型"""
        allowed_slices = ['eMBB', 'uRLLC']
        if v not in allowed_slices:
            raise ValueError(f'Slice 類型必須為 {allowed_slices} 之一')
        return v


class UEUpdateRequest(BaseModel):
    """UE 更新請求"""
    
    apn: Optional[str] = Field(
        None,
        description="接入點名稱",
        example="internet"
    )
    
    slice_type: Optional[str] = Field(
        None,
        description="Slice 類型",
        example="uRLLC"
    )
    
    @validator('slice_type')
    def validate_slice_type(cls, v):
        """驗證 Slice 類型"""
        if v is not None:
            allowed_slices = ['eMBB', 'uRLLC']
            if v not in allowed_slices:
                raise ValueError(f'Slice 類型必須為 {allowed_slices} 之一')
        return v 