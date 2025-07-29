from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class SimulationParameters(BaseModel):
    """模擬參數模型，用於存儲模擬的輸入參數"""

    # 基本模擬參數
    simulation_type: str = Field(
        ..., description="模擬類型，如'cfr', 'sinr_map', 'doppler', 'channel_response'"
    )
    description: Optional[str] = Field(None, description="模擬描述")

    # 時間相關參數
    start_time: Optional[datetime] = Field(None, description="模擬開始時間")
    end_time: Optional[datetime] = Field(None, description="模擬結束時間")

    # SINR 地圖相關參數
    sinr_vmin: Optional[float] = Field(None, description="SINR 最小值 (dB)")
    sinr_vmax: Optional[float] = Field(None, description="SINR 最大值 (dB)")
    cell_size: Optional[float] = Field(None, description="Radio map 網格大小 (m)")
    samples_per_tx: Optional[int] = Field(None, description="每個發射器的採樣數量")

    # 其他 RF 參數
    carrier_frequency: Optional[float] = Field(None, description="載波頻率 (Hz)")
    bandwidth: Optional[float] = Field(None, description="頻寬 (Hz)")
    subcarriers: Optional[int] = Field(None, description="子載波數量")

    # 自定義參數
    custom_params: Optional[Dict[str, Any]] = Field(None, description="自定義參數")


class SimulationResult(BaseModel):
    """模擬結果模型，用於存儲模擬的輸出結果"""

    # 基本資訊
    simulation_id: str = Field(..., description="模擬 ID")
    simulation_type: str = Field(..., description="模擬類型")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="結果創建時間"
    )

    # 結果參數
    success: bool = Field(..., description="模擬是否成功")
    result_path: Optional[str] = Field(None, description="結果文件路徑")
    result_data: Optional[Dict[str, Any]] = Field(None, description="結果數據")

    # 錯誤訊息
    error_message: Optional[str] = Field(None, description="錯誤訊息，如果模擬失敗")


class SimulationImageRequest(BaseModel):
    """模擬圖像請求模型，用於 API 請求時的參數"""

    # 圖像類型
    image_type: str = Field(
        ..., description="圖像類型，如'cfr', 'sinr_map', 'doppler', 'channel_response'"
    )

    # 通用參數
    devices: Optional[List[int]] = Field(
        None, description="要包含在模擬中的設備 ID 列表"
    )

    # SINR 地圖相關參數
    sinr_vmin: float = Field(-40.0, description="SINR 最小值 (dB)")
    sinr_vmax: float = Field(0.0, description="SINR 最大值 (dB)")
    cell_size: float = Field(1.0, description="Radio map 網格大小 (m)")
    samples_per_tx: int = Field(10**7, description="每個發射器的採樣數量")
