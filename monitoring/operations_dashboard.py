import asyncio
import json
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import aiofiles
from datetime import datetime

# --- Configuration ---
LOG_FILE_PATH = os.getenv("LOG_FILE_PATH", "/tmp/operations.log")
DASHBOARD_HTML_PATH = "./dashboard.html"

# --- FastAPI App Initialization ---
app = FastAPI(
    title="NTN Stack Operations Dashboard",
    description="實時控制和監控AI決策引擎的後端服務",
    version="1.0.0",
)


# --- WebSocket Connection Manager ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()


# --- Utility Functions ---
async def write_log(message: str):
    """異步寫入日誌"""
    async with aiofiles.open(LOG_FILE_PATH, mode="a") as f:
        await f.write(
            f"{asyncio.to_thread(lambda: datetime.now().isoformat())} - {message}\n"
        )
    await manager.broadcast(json.dumps({"type": "log", "message": message}))


# --- API Endpoints ---
@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    """提供儀表板前端頁面"""
    try:
        async with aiofiles.open(DASHBOARD_HTML_PATH, mode="r") as f:
            content = await f.read()
        return HTMLResponse(content)
    except FileNotFoundError:
        return HTMLResponse(
            "<h1>儀表板文件 (dashboard.html) 未找到</h1>", status_code=404
        )


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket端點，處理前端的實時交互"""
    await manager.connect(websocket)
    await write_log("一個新的客戶端已連接")
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            action = message_data.get("action")
            payload = message_data.get("payload", {})

            await write_log(f"接收到指令: {action}，參數: {payload}")

            # 根據指令執行不同操作
            if action == "set_rl_mode":
                response = f"RL 模式已切換為: {payload.get('mode')}"
            elif action == "adjust_param":
                response = (
                    f"參數 {payload.get('param')} 已調整為: {payload.get('value')}"
                )
            elif action == "trigger_emergency_stop":
                response = "緊急停止指令已觸發！"
            else:
                response = f"未知的指令: {action}"

            await manager.send_personal_message(
                json.dumps({"type": "response", "message": response}), websocket
            )
            await write_log(response)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await write_log("一個客戶端已斷開連接")
    except Exception as e:
        error_message = f"處理指令時發生錯誤: {e}"
        await write_log(error_message)
        await manager.send_personal_message(
            json.dumps({"type": "error", "message": error_message}), websocket
        )


# --- Background Task ---
async def log_monitoring_task():
    """模擬一個後台任務，定期廣播日誌"""
    while True:
        await asyncio.sleep(15)
        log_message = "系統狀態檢查: 一切正常"
        await write_log(log_message)


@app.on_event("startup")
async def startup_event():
    # 啟動時清除舊日誌
    if os.path.exists(LOG_FILE_PATH):
        os.remove(LOG_FILE_PATH)
    asyncio.create_task(log_monitoring_task())


print("NTN 營運儀表板後端服務已啟動")
