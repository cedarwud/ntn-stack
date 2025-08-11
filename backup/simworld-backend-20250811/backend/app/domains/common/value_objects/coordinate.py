from pydantic import Field
from typing import Optional

from app.domains.common.models.base_model import ValueObject


class Coordinate(ValueObject):
    """座標值對象，表示空間位置"""

    latitude: float = Field(..., description="緯度")
    longitude: float = Field(..., description="經度")
    altitude: Optional[float] = Field(None, description="海拔高度（米）")

    def distance_to(self, other: "Coordinate") -> float:
        """計算到另一座標的大圓距離（公里）

        Args:
            other: 另一座標

        Returns:
            兩點間大圓距離，單位為公里
        """
        # 簡化實現，實際應使用更精確的計算方法
        # 這裡可以實現球面三角法或Haversine公式
        # 由於這是一個示例，這裡只返回一個占位值
        return 0.0

    @classmethod
    def from_degrees(
        cls, lat_deg: float, lon_deg: float, alt: Optional[float] = None
    ) -> "Coordinate":
        """從角度創建座標

        Args:
            lat_deg: 緯度（度）
            lon_deg: 經度（度）
            alt: 海拔高度（米）

        Returns:
            座標對象
        """
        return cls(latitude=lat_deg, longitude=lon_deg, altitude=alt)
