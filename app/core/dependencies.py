"""
依賴注入模組
提供應用程式所需的各種依賴項
"""
from typing import AsyncGenerator, Optional
import logging
from fastapi import Depends, HTTPException, Header
from .config import settings

# 設定日誌
logger = logging.getLogger(__name__)


async def get_database():
    """
    獲取數據庫連接
    
    這是一個依賴項，用於注入數據庫連接
    後續需要實際的數據庫連接邏輯
    """
    # 暫時返回模擬的數據庫連接
    # 實際實現需要連接到 MongoDB
    try:
        # 這裡應該是實際的數據庫連接邏輯
        db_connection = {"type": "mongodb", "url": settings.mongodb_url}
        yield db_connection
    except Exception as e:
        logger.error(f"數據庫連接失敗: {str(e)}")
        raise HTTPException(status_code=503, detail="Database connection failed")
    finally:
        # 清理資源
        pass


async def get_redis():
    """
    獲取 Redis 連接
    
    這是一個依賴項，用於注入 Redis 連接
    """
    try:
        # 這裡應該是實際的 Redis 連接邏輯
        redis_connection = {"type": "redis", "url": settings.redis_url}
        yield redis_connection
    except Exception as e:
        logger.error(f"Redis連接失敗: {str(e)}")
        raise HTTPException(status_code=503, detail="Redis connection failed")
    finally:
        # 清理資源
        pass


async def get_current_user(
    authorization: Optional[str] = Header(None)
) -> Optional[dict]:
    """
    獲取當前用戶
    
    從請求頭中驗證用戶身份
    
    Args:
        authorization: Authorization 頭部
        
    Returns:
        dict: 用戶資訊，如果未認證則返回 None
    """
    if not authorization:
        return None
    
    try:
        # 這裡應該是實際的用戶驗證邏輯
        # 暫時返回模擬用戶
        if authorization.startswith("Bearer "):
            token = authorization.split(" ")[1]
            # 實際需要驗證 token
            return {
                "id": "user_001",
                "username": "admin",
                "roles": ["admin"]
            }
        return None
    except Exception as e:
        logger.error(f"用戶驗證失敗: {str(e)}")
        return None


async def require_authentication(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """
    要求用戶認證
    
    如果用戶未認證，拋出 401 錯誤
    
    Args:
        current_user: 當前用戶（通過依賴注入）
        
    Returns:
        dict: 認證的用戶資訊
        
    Raises:
        HTTPException: 如果用戶未認證
    """
    if not current_user:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return current_user


async def require_admin_role(
    current_user: dict = Depends(require_authentication)
) -> dict:
    """
    要求管理員角色
    
    如果用戶不是管理員，拋出 403 錯誤
    
    Args:
        current_user: 當前認證的用戶
        
    Returns:
        dict: 管理員用戶資訊
        
    Raises:
        HTTPException: 如果用戶不是管理員
    """
    if "admin" not in current_user.get("roles", []):
        raise HTTPException(
            status_code=403,
            detail="Admin role required"
        )
    return current_user


class ServiceContainer:
    """
    服務容器類
    管理應用程式中的各種服務實例
    """
    
    def __init__(self):
        self._services = {}
    
    def register(self, name: str, service):
        """註冊服務"""
        self._services[name] = service
        logger.info(f"服務已註冊: {name}")
    
    def get(self, name: str):
        """獲取服務"""
        if name not in self._services:
            raise ValueError(f"服務未註冊: {name}")
        return self._services[name]
    
    def exists(self, name: str) -> bool:
        """檢查服務是否存在"""
        return name in self._services


# 全域服務容器實例
service_container = ServiceContainer()


def get_service_container() -> ServiceContainer:
    """
    獲取服務容器
    
    這是一個依賴項，用於注入服務容器
    """
    return service_container