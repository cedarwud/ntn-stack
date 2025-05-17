import logging
from skyfield.api import load, wgs84, Distance
# from skyfield.positionlib import Geocentric # Not strictly needed for these direct conversions
# from skyfield.framelib import itrs # Not strictly needed for these direct conversions

logger = logging.getLogger(__name__)

# --- GLB Coordinate Conversion Constants ---
ORIGIN_LATITUDE_GLB = 24.786667  # 真實世界原點緯度 (GLB (0,0) 對應點)
ORIGIN_LONGITUDE_GLB = 120.996944  # 真實世界原點經度 (GLB (0,0) 對應點)
# GLB (100, 100) -> (真實): (24.785833 N, 120.997778 E)
# GLB X 變化 (dx_glb): 100 - 0 = 100
# GLB Y 變化 (dy_glb): 100 - 0 = 100
# 真實緯度變化 (dlat_real): 24.785833 - 24.786667 = -0.000834 度
# 真實經度變化 (dlon_real): 120.997778 - 120.996944 = 0.000834 度
LATITUDE_SCALE_PER_GLB_Y = -0.000834 / 100  # 度 / GLB Y 單位
LONGITUDE_SCALE_PER_GLB_X = 0.000834 / 100   # 度 / GLB X 單位

class GlbConversionService:
    @staticmethod
    def to_real_world(glb_x: float, glb_y: float, glb_z: float | None = None) -> tuple[float, float, float | None]:
        """將 GLB 場景座標 (含可選 Z 軸) 轉換為真實世界經緯度座標 (含可選 Z 軸)。"""
        real_latitude = ORIGIN_LATITUDE_GLB + (glb_y * LATITUDE_SCALE_PER_GLB_Y)
        real_longitude = ORIGIN_LONGITUDE_GLB + (glb_x * LONGITUDE_SCALE_PER_GLB_X)
        logger.info(f"Service: Converted GLB (X:{glb_x}, Y:{glb_y}, Z:{glb_z}) to Real (Lat:{real_latitude}, Lon:{real_longitude}, Z:{glb_z})")
        return real_latitude, real_longitude, glb_z # Z 軸直接透傳

    @staticmethod
    def to_glb(latitude: float, longitude: float, z_input: float | None = None) -> tuple[int, int, int | None]:
        """將真實世界經緯度座標 (含可選 Z 軸) 轉換為 GLB 場景座標 (X, Y, Z 均四捨五入為整數)。"""
        if LATITUDE_SCALE_PER_GLB_Y == 0:
            logger.error("GLB Latitude Scale factor is zero.")
            raise ValueError("Invalid GLB latitude scale factor configuration")
        if LONGITUDE_SCALE_PER_GLB_X == 0:
            logger.error("GLB Longitude Scale factor is zero.")
            raise ValueError("Invalid GLB longitude scale factor configuration")
        
        glb_y_float = (latitude - ORIGIN_LATITUDE_GLB) / LATITUDE_SCALE_PER_GLB_Y
        glb_x_float = (longitude - ORIGIN_LONGITUDE_GLB) / LONGITUDE_SCALE_PER_GLB_X

        # 四捨五入邏輯 (0.5 則進位)
        glb_x_rounded = int(glb_x_float + 0.5) if glb_x_float >= 0 else int(glb_x_float - 0.5)
        glb_y_rounded = int(glb_y_float + 0.5) if glb_y_float >= 0 else int(glb_y_float - 0.5)
        
        glb_z_rounded: int | None = None
        if z_input is not None:
            glb_z_rounded = int(z_input + 0.5) if z_input >= 0 else int(z_input - 0.5)

        logger.info(f"Service: Converted Real (Lat:{latitude}, Lon:{longitude}, Z_in:{z_input}) to GLB (X_float:{glb_x_float:.2f}, Y_float:{glb_y_float:.2f}, Z_in_float:{z_input}) -> (X_rounded:{glb_x_rounded}, Y_rounded:{glb_y_rounded}, Z_rounded:{glb_z_rounded})")
        return glb_x_rounded, glb_y_rounded, glb_z_rounded

    @staticmethod
    def get_parameters() -> dict:
        """獲取 GLB 轉換參數。"""
        return {
            "origin_latitude_glb": ORIGIN_LATITUDE_GLB,
            "origin_longitude_glb": ORIGIN_LONGITUDE_GLB,
            "latitude_scale_per_glb_y": LATITUDE_SCALE_PER_GLB_Y,
            "longitude_scale_per_glb_x": LONGITUDE_SCALE_PER_GLB_X
        }

# --- Satellite Coordinate Conversion (Skyfield) ---
# Skyfield 的 timescale 對於座標參考框架的轉換至關重要
# 使用 builtin=True 通常可以避免首次運行時下載大型星曆文件，對於 WGS84 轉換足夠
try:
    ts = load.timescale(builtin=True)
except Exception as e:
    logger.error(f"Skyfield timescale failed to load: {e}. Satellite coordinate conversions will not be available.")
    ts = None

class SatelliteCoordinateService:
    @staticmethod
    def geodetic_to_ecef(latitude_deg: float, longitude_deg: float, elevation_m: float) -> tuple[float, float, float]:
        """將大地座標 (緯度, 經度, 高程) 轉換為 ECEF (地心地固) 座標 (X, Y, Z 米)。"""
        if ts is None:
            logger.error("Skyfield timescale not initialized. Cannot perform geodetic_to_ecef conversion.")
            raise RuntimeError("Skyfield timescale not initialized. Satellite conversions unavailable.")
        
        # 使用 wgs84.latlon 建立地球表面上的點
        earth_location = wgs84.latlon(
            latitude_degrees=latitude_deg,
            longitude_degrees=longitude_deg,
            elevation_m=elevation_m
        )
        # .itrs_xyz.m 屬性提供 ITRS 框架下的 ECEF 座標 (單位：米)
        # ITRS (International Terrestrial Reference System) 被 Skyfield 用作 ECEF 的實現
        x_m, y_m, z_m = earth_location.itrs_xyz.m
        logger.info(f"Service: Converted Geodetic (Lat:{latitude_deg}, Lon:{longitude_deg}, El:{elevation_m}m) to ECEF (X:{x_m}m, Y:{y_m}m, Z:{z_m}m)")
        return x_m, y_m, z_m

    @staticmethod
    def ecef_to_geodetic(x_m: float, y_m: float, z_m: float) -> tuple[float, float, float]:
        """將 ECEF 座標 (X, Y, Z 米) 轉換為大地座標 (緯度, 經度, 高程)。"""
        if ts is None:
            logger.error("Skyfield timescale not initialized. Cannot perform ecef_to_geodetic conversion.")
            raise RuntimeError("Skyfield timescale not initialized. Satellite conversions unavailable.")

        # 建立一個 Skyfield Distance 物件，表示 ECEF 座標向量 (單位：米)
        position_vector_itrs_m = Distance(m=[x_m, y_m, z_m])
        
        # 使用 wgs84.geographic_position_of() 將此 ITRS 向量轉換為大地座標
        geopoint = wgs84.geographic_position_of(position_vector_itrs_m)
        
        latitude_deg = geopoint.latitude.degrees
        longitude_deg = geopoint.longitude.degrees
        elevation_m = geopoint.elevation.m
        logger.info(f"Service: Converted ECEF (X:{x_m}m, Y:{y_m}m, Z:{z_m}m) to Geodetic (Lat:{latitude_deg}, Lon:{longitude_deg}, El:{elevation_m}m)")
        return latitude_deg, longitude_deg, elevation_m 