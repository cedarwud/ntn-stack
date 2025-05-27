from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from .base import async_session_maker


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """獲取異步資料庫會話的協程函數

    用作依賴注入，為服務提供資料庫會話

    Yields:
        AsyncSession: 異步SQLAlchemy會話對象
    """
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()
