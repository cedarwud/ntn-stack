#!/usr/bin/env python
"""
檢查設備數據腳本
此腳本用於查詢和顯示數據庫中的設備數據
"""
import asyncio
from sqlalchemy import select
from app.db.base import async_session_maker
from app.db.models import Device


async def check_devices():
    async with async_session_maker() as session:
        result = await session.execute(select(Device))
        devices = result.scalars().all()
        print(f"共找到 {len(devices)} 個設備:")
        for device in devices:
            print(
                f"- {device.name}: 位置 ({device.position_x}, {device.position_y}, {device.position_z}), 方向 ({device.orientation_x:.2f}, {device.orientation_y:.2f}, {device.orientation_z:.2f}), 角色: {device.role}, 功率: {device.power_dbm}dBm"
            )


if __name__ == "__main__":
    asyncio.run(check_devices())
