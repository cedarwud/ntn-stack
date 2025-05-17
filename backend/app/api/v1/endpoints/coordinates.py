from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging

# 導入新的服務
from app.services.coordinate_conversion_service import GlbConversionService, SatelliteCoordinateService

router = APIRouter()
logger = logging.getLogger(__name__)

# --- 轉換常數 ---
# GLB (0, 0) -> (真實): (24.786667 N, 120.996944 E)
# GLB (100, 100) -> (真實): (24.785833 N, 120.997778 E)

ORIGIN_LATITUDE = 24.786667  # 真實世界原點緯度
ORIGIN_LONGITUDE = 120.996944  # 真實世界原點經度

# GLB X 變化: 100 - 0 = 100
# GLB Y 變化: 100 - 0 = 100
# 真實緯度變化 (Lat): 24.785833 - 24.786667 = -0.000834 度
# 真實經度變化 (Lon): 120.997778 - 120.996944 = 0.000834 度

# 比例：
# GLB 的 Y 軸對應緯度變化
LATITUDE_SCALE_PER_GLB_Y = -0.00000834  # 度 / GLB Y 單位
# GLB 的 X 軸對應經度變化
LONGITUDE_SCALE_PER_GLB_X = 0.00000834   # 度 / GLB X 單位

# --- Pydantic 模型 ---

# GLB 和真實世界座標 (既有)
class GlbCoordinatesRequest(BaseModel):
    x: float
    y: float
    z: float | None = None  # 新增可選的 z

class RealWorldCoordinatesResponse(BaseModel):
    latitude: float
    longitude: float
    z: float | None = None  # 新增可選的 z

class RealWorldCoordinatesRequest(BaseModel):
    latitude: float
    longitude: float
    z: float | None = None  # 新增可選的 z

class GlbCoordinatesResponse(BaseModel):
    x: int
    y: int
    z: int | None = None  # 改為 int | None

# Skyfield 座標模型 (新增)
class GeodeticCoordsSkyfieldRequest(BaseModel):
    latitude_deg: float
    longitude_deg: float
    elevation_m: float

class EcefCoordsSkyfieldResponse(BaseModel):
    x_m: float
    y_m: float
    z_m: float

class EcefCoordsSkyfieldRequest(BaseModel):
    x_m: float
    y_m: float
    z_m: float

class GeodeticCoordsSkyfieldResponse(BaseModel):
    latitude_deg: float
    longitude_deg: float
    elevation_m: float

# --- API 端點 ---

# GLB 座標轉換 (使用服務層)
@router.post("/glb-to-real", response_model=RealWorldCoordinatesResponse, tags=["Coordinates Conversion"])
async def convert_glb_to_real(glb_coords: GlbCoordinatesRequest):
    """
    將 GLB 場景座標 (含可選 Z 軸) 轉換為真實世界經緯度座標 (Z 軸一對一透傳)。
    """
    try:
        lat, lon, z_val = GlbConversionService.to_real_world(glb_coords.x, glb_coords.y, glb_coords.z)
        return RealWorldCoordinatesResponse(latitude=lat, longitude=lon, z=z_val)
    except ValueError as ve:
        logger.error(f"GLB to Real conversion error: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error in GLB to Real conversion: {e}")
        raise HTTPException(status_code=500, detail="Coordinate conversion error")

@router.post("/real-to-glb", response_model=GlbCoordinatesResponse, tags=["Coordinates Conversion"])
async def convert_real_to_glb(real_coords: RealWorldCoordinatesRequest):
    """
    將真實世界經緯度座標 (含可選 Z 軸) 轉換為 GLB 場景座標 (Z 軸一對一透傳)。
    """
    try:
        x, y, z_val = GlbConversionService.to_glb(real_coords.latitude, real_coords.longitude, real_coords.z)
        return GlbCoordinatesResponse(x=x, y=y, z=z_val)
    except ValueError as ve:
        logger.error(f"Real to GLB conversion error: {ve}")
        raise HTTPException(status_code=400, detail=str(ve)) # Bad request if scale is bad
    except Exception as e:
        logger.error(f"Error in Real to GLB conversion: {e}")
        raise HTTPException(status_code=500, detail="Coordinate conversion error")

@router.get("/glb-conversion-parameters", tags=["Coordinates Conversion"])
async def get_glb_conversion_parameters():
    """
    獲取當前 GLB 使用的轉換參數。
    """
    try:
        return GlbConversionService.get_parameters()
    except Exception as e:
        logger.error(f"Error getting GLB conversion parameters: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving GLB parameters")

# Skyfield 衛星等級座標轉換 (新增，使用服務層)
@router.post("/geodetic-to-ecef", response_model=EcefCoordsSkyfieldResponse, tags=["Satellite Coordinates (Skyfield)"])
async def convert_geodetic_to_ecef(geo_coords: GeodeticCoordsSkyfieldRequest):
    """
    使用 Skyfield 將大地座標 (緯度, 經度, 高程) 轉換為 ECEF (地心地固) 座標。
    """
    try:
        x, y, z = SatelliteCoordinateService.geodetic_to_ecef(
            geo_coords.latitude_deg, 
            geo_coords.longitude_deg, 
            geo_coords.elevation_m
        )
        return EcefCoordsSkyfieldResponse(x_m=x, y_m=y, z_m=z)
    except RuntimeError as re: # Catch specific error from service if Skyfield failed to load
        logger.error(f"Skyfield Geodetic to ECEF conversion error: {re}")
        raise HTTPException(status_code=503, detail=str(re)) # Service Unavailable
    except Exception as e:
        logger.error(f"Error in Geodetic to ECEF conversion: {e}")
        raise HTTPException(status_code=500, detail="Satellite coordinate conversion error")

@router.post("/ecef-to-geodetic", response_model=GeodeticCoordsSkyfieldResponse, tags=["Satellite Coordinates (Skyfield)"])
async def convert_ecef_to_geodetic(ecef_coords: EcefCoordsSkyfieldRequest):
    """
    使用 Skyfield 將 ECEF (地心地固) 座標轉換為大地座標 (緯度, 經度, 高程)。
    """
    try:
        lat, lon, alt = SatelliteCoordinateService.ecef_to_geodetic(
            ecef_coords.x_m, 
            ecef_coords.y_m, 
            ecef_coords.z_m
        )
        return GeodeticCoordsSkyfieldResponse(latitude_deg=lat, longitude_deg=lon, elevation_m=alt)
    except RuntimeError as re:
        logger.error(f"Skyfield ECEF to Geodetic conversion error: {re}")
        raise HTTPException(status_code=503, detail=str(re))
    except Exception as e:
        logger.error(f"Error in ECEF to Geodetic conversion: {e}")
        raise HTTPException(status_code=500, detail="Satellite coordinate conversion error") 