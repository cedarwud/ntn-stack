#!/usr/bin/env python
"""
重置數據庫腳本 - 容器內版本
此腳本在Docker容器內運行，用於重置數據庫中的設備數據
"""
import asyncio
from sqlalchemy import text
from app.db.base import engine
from app.db.lifespan import seed_initial_data
from app.db.base import async_session_maker
from app.db.models import Device


async def reset_db():
    # 刪除所有設備數據
    try:
        async with engine.begin() as conn:
            # 使用text()函數創建可執行的SQL語句
            await conn.execute(text("DELETE FROM device"))
            print("已刪除所有設備數據")
    except Exception as e:
        print(f"刪除數據時出錯: {e}")
        return

    # 重新初始化
    try:
        async with async_session_maker() as session:
            await seed_initial_data(session)
            print("已重新初始化設備數據")
    except Exception as e:
        print(f"初始化數據時出錯: {e}")


if __name__ == "__main__":
    asyncio.run(reset_db())
