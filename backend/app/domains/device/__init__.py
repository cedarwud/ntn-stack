"""
設備領域模組

包含設備相關的模型、服務、儲存庫和 API 實現。
主要處理設備的創建、查詢、更新和刪除等操作。
"""

from app.domains.device.models.device_model import Device, DeviceRole, DeviceBase
from app.domains.device.services.device_service import DeviceService
from app.domains.device.interfaces.device_repository import DeviceRepository
from app.domains.device.adapters.sqlmodel_device_repository import SQLModelDeviceRepository 