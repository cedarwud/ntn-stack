# backend/app/api/v1/router.py
from fastapi import APIRouter

# 從 endpoints 目錄導入 sionna 和 devices 路由
from app.api.v1.endpoints import sionna, devices, coordinates

api_router = APIRouter()

# 包含現有的 sionna 路由
api_router.include_router(sionna.router, prefix="/sionna", tags=["Sionna Simulation"])

# 添加 devices 路由 - 用於處理所有類型的設備，包括干擾源
# 整合了之前的 jammers 端點功能到 devices 中
# 同時提供了兩種訪問模式：
# 1. /devices/jammer/* - 專門用於處理干擾源
# 2. /devices/* - 處理所有設備，可以通過查詢參數和路徑參數指定設備類型
api_router.include_router(devices.router, prefix="/devices", tags=["Devices"])

# 新增 coordinates 路由
api_router.include_router(coordinates.router, prefix="/coordinates", tags=["Coordinates Conversion"])

# 註：兩種路由模式（devices 和 jammers）底層調用的是同一套 CRUD 函數
# 這樣做的主要原因是保持 API 的向後兼容性，同時也使前端代碼更清晰
# 未來可以考慮完全整合為一套 API，讓前端通過查詢參數指定設備類型
