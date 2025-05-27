from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import DATABASE_URL
from app.db.base_class import Base  # noqa

# 重構後的領域模型引用
# 這些模型已被遷移到領域目錄中，不再需要從舊的db目錄導入

# 使用 async engine
# echo=False 可避免印出 SQL 指令，設為 True 可用於除錯
engine = create_async_engine(DATABASE_URL, echo=False, future=True)

# Async session maker
# expire_on_commit=False 可讓你在 commit 後仍能存取 session 中的物件
async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# SQLModel Base Class (如果需要自訂 Base，可以在這裡或 models.py 定義)
# from sqlmodel import SQLModel
# class CustomBase(SQLModel):
#     pass
