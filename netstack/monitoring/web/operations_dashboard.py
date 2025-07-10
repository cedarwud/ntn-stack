#!/usr/bin/env python3
"""
NTN Stack - Stage 8: 營運管理 Web 介面
AI 決策系統管理儀表板

提供以下功能：
1. RL 算法啟停控制面板
2. 決策參數實時調優介面  
3. 訓練會話管理和監控
4. 系統配置熱更新介面
5. 緊急處理機制操作界面
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

import aiofiles
from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field

from ..operations.decision_system_manager import DecisionSystemManager, SystemState, AlertSeverity
from ..metrics.ai_decision_metrics import (
    record_decision_result, update_system_health, 
    get_all_metrics, export_metrics_to_prometheus
)

# 設定日誌
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# FastAPI 應用初始化
app = FastAPI(
    title="NTN Stack Operations Dashboard",
    description="AI 決策系統營運管理儀表板",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 靜態文件和模板設定
static_path = Path(__file__).parent / "static"
templates_path = Path(__file__).parent / "templates"
static_path.mkdir(exist_ok=True)
templates_path.mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
templates = Jinja2Templates(directory=str(templates_path))

# 全域管理器實例
decision_manager = DecisionSystemManager()

# WebSocket 連接管理
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket 連接建立，當前連接數: {len(self.active_connections)}")
        
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket 連接斷開，當前連接數: {len(self.active_connections)}")
        
    async def broadcast(self, message: dict):
        """向所有連接的客戶端廣播消息"""
        if not self.active_connections:
            return
            
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"WebSocket 廣播失敗: {e}")
                disconnected.append(connection)
                
        # 清理斷開的連接
        for conn in disconnected:
            self.disconnect(conn)

manager = ConnectionManager()

# 數據模型定義
class RLAlgorithmRequest(BaseModel):
    algorithm: str = Field(..., description="RL 算法名稱 (DQN, PPO, SAC)")
    parameters: Optional[Dict[str, Any]] = Field(default={}, description="算法參數")

class ParameterUpdateRequest(BaseModel):
    component: str = Field(..., description="組件名稱")
    parameters: Dict[str, Any] = Field(..., description="參數字典")
    hot_reload: bool = Field(default=True, description="是否熱更新")

class EmergencyModeRequest(BaseModel):
    trigger_reason: str = Field(..., description="觸發原因")
    severity: AlertSeverity = Field(default=AlertSeverity.CRITICAL, description="告警級別")

class ManualDecisionRequest(BaseModel):
    decision_type: str = Field(..., description="決策類型")
    parameters: Dict[str, Any] = Field(..., description="決策參數")
    duration_minutes: int = Field(default=30, description="手動決策持續時間（分鐘）")

# 首頁路由
@app.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    """營運管理儀表板首頁"""
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "title": "NTN Stack 營運管理中心",
        "current_time": datetime.now().isoformat()
    })

# 系統狀態 API
@app.get("/api/system/status")
async def get_system_status():
    """獲取系統整體狀態"""
    try:
        health_check = await decision_manager.comprehensive_health_check()
        rl_status = await decision_manager.get_rl_algorithm_status()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "system_state": decision_manager.current_state.value,
            "health_score": health_check.health_score,
            "components_status": health_check.components,
            "rl_algorithms": rl_status,
            "uptime": "計算中...",  # TODO: 實現運行時間計算
            "total_decisions": "從指標獲取",  # TODO: 從指標系統獲取
            "current_load": health_check.performance.cpu_usage
        }
    except Exception as e:
        logger.error(f"獲取系統狀態失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# RL 算法管理 API
@app.post("/api/rl/start")
async def start_rl_algorithm(request: RLAlgorithmRequest, background_tasks: BackgroundTasks):
    """啟動 RL 算法"""
    try:
        result = await decision_manager.start_rl_algorithm(
            algorithm=request.algorithm,
            parameters=request.parameters
        )
        
        # 廣播狀態更新
        background_tasks.add_task(
            manager.broadcast, 
            {
                "type": "rl_algorithm_started",
                "algorithm": request.algorithm,
                "timestamp": datetime.now().isoformat(),
                "success": result
            }
        )
        
        return {"success": result, "message": f"RL 算法 {request.algorithm} 啟動成功"}
    except Exception as e:
        logger.error(f"啟動 RL 算法失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/rl/stop")
async def stop_rl_algorithm(request: RLAlgorithmRequest, background_tasks: BackgroundTasks):
    """停止 RL 算法"""
    try:
        result = await decision_manager.stop_rl_algorithm(
            algorithm=request.algorithm,
            save_model=True
        )
        
        # 廣播狀態更新
        background_tasks.add_task(
            manager.broadcast, 
            {
                "type": "rl_algorithm_stopped",
                "algorithm": request.algorithm,
                "timestamp": datetime.now().isoformat(),
                "success": result
            }
        )
        
        return {"success": result, "message": f"RL 算法 {request.algorithm} 停止成功"}
    except Exception as e:
        logger.error(f"停止 RL 算法失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/rl/status")
async def get_rl_status():
    """獲取所有 RL 算法狀態"""
    try:
        status = await decision_manager.get_rl_algorithm_status()
        return status
    except Exception as e:
        logger.error(f"獲取 RL 狀態失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 參數管理 API
@app.post("/api/parameters/update")
async def update_parameters(request: ParameterUpdateRequest, background_tasks: BackgroundTasks):
    """更新系統參數"""
    try:
        result = await decision_manager.update_decision_parameters(
            parameters=request.parameters,
            hot_reload=request.hot_reload
        )
        
        # 廣播參數更新通知
        background_tasks.add_task(
            manager.broadcast,
            {
                "type": "parameters_updated",
                "component": request.component,
                "parameters": request.parameters,
                "hot_reload": request.hot_reload,
                "timestamp": datetime.now().isoformat(),
                "success": result
            }
        )
        
        return {"success": result, "message": "參數更新成功"}
    except Exception as e:
        logger.error(f"更新參數失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/parameters/rollback")
async def rollback_parameters(background_tasks: BackgroundTasks):
    """回滾參數到前一個版本"""
    try:
        result = await decision_manager.rollback_parameters()
        
        background_tasks.add_task(
            manager.broadcast,
            {
                "type": "parameters_rollback",
                "timestamp": datetime.now().isoformat(),
                "success": result
            }
        )
        
        return {"success": result, "message": "參數回滾成功"}
    except Exception as e:
        logger.error(f"參數回滾失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 緊急處理 API
@app.post("/api/emergency/trigger")
async def trigger_emergency_mode(request: EmergencyModeRequest, background_tasks: BackgroundTasks):
    """觸發緊急模式"""
    try:
        result = await decision_manager.trigger_emergency_mode(
            reason=request.trigger_reason,
            severity=request.severity
        )
        
        # 立即廣播緊急狀態
        background_tasks.add_task(
            manager.broadcast,
            {
                "type": "emergency_triggered",
                "reason": request.trigger_reason,
                "severity": request.severity.value,
                "timestamp": datetime.now().isoformat(),
                "success": result
            }
        )
        
        return {"success": result, "message": "緊急模式已觸發", "severity": request.severity.value}
    except Exception as e:
        logger.error(f"觸發緊急模式失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/emergency/exit")
async def exit_emergency_mode(background_tasks: BackgroundTasks):
    """退出緊急模式"""
    try:
        result = await decision_manager.exit_emergency_mode()
        
        background_tasks.add_task(
            manager.broadcast,
            {
                "type": "emergency_exited",
                "timestamp": datetime.now().isoformat(),
                "success": result
            }
        )
        
        return {"success": result, "message": "已退出緊急模式"}
    except Exception as e:
        logger.error(f"退出緊急模式失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 手動決策覆蓋 API
@app.post("/api/manual-decision")
async def manual_decision_override(request: ManualDecisionRequest, background_tasks: BackgroundTasks):
    """手動決策覆蓋"""
    try:
        result = await decision_manager.manual_decision_override(
            decision_type=request.decision_type,
            decision_data=request.parameters,
            duration_minutes=request.duration_minutes
        )
        
        background_tasks.add_task(
            manager.broadcast,
            {
                "type": "manual_decision_override",
                "decision_type": request.decision_type,
                "parameters": request.parameters,
                "duration_minutes": request.duration_minutes,
                "timestamp": datetime.now().isoformat(),
                "success": result
            }
        )
        
        return {"success": result, "message": f"手動決策覆蓋已生效，持續 {request.duration_minutes} 分鐘"}
    except Exception as e:
        logger.error(f"手動決策覆蓋失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 性能分析 API
@app.get("/api/performance/trends")
async def get_performance_trends():
    """獲取性能趨勢分析"""
    try:
        trends = await decision_manager.get_performance_trends()
        return trends
    except Exception as e:
        logger.error(f"獲取性能趨勢失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/metrics/export")
async def export_prometheus_metrics():
    """導出 Prometheus 格式指標"""
    try:
        metrics_data = export_metrics_to_prometheus()
        return JSONResponse(
            content={"metrics": metrics_data},
            headers={"Content-Type": "application/json"}
        )
    except Exception as e:
        logger.error(f"導出指標失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket 端點
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 端點，用於實時狀態推送"""
    await manager.connect(websocket)
    try:
        while True:
            # 等待客戶端消息（心跳檢測）
            data = await websocket.receive_text()
            
            # 處理心跳或其他客戶端請求
            if data == "ping":
                await websocket.send_text("pong")
            elif data == "status":
                # 發送當前系統狀態
                try:
                    status = await get_system_status()
                    await websocket.send_text(json.dumps({
                        "type": "status_update",
                        "data": status,
                        "timestamp": datetime.now().isoformat()
                    }))
                except Exception as e:
                    logger.error(f"發送狀態更新失敗: {e}")
                    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket 錯誤: {e}")
        manager.disconnect(websocket)

# 後台任務：定期狀態廣播
@app.on_event("startup")
async def startup_event():
    """應用啟動時的初始化"""
    logger.info("營運管理儀表板啟動中...")
    
    # 初始化決策系統管理器
    await decision_manager.initialize()
    
    # 啟動定期狀態廣播任務
    asyncio.create_task(periodic_status_broadcast())
    
    logger.info("營運管理儀表板啟動完成")

async def periodic_status_broadcast():
    """定期廣播系統狀態（每30秒）"""
    while True:
        try:
            await asyncio.sleep(30)  # 30秒間隔
            
            if manager.active_connections:
                status = await get_system_status()
                await manager.broadcast({
                    "type": "periodic_status_update",
                    "data": status,
                    "timestamp": datetime.now().isoformat()
                })
                
        except Exception as e:
            logger.error(f"定期狀態廣播失敗: {e}")

# 健康檢查端點
@app.get("/health")
async def health_check():
    """應用健康檢查端點"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "operations-dashboard",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "operations_dashboard:app",
        host="0.0.0.0",
        port=8090,
        reload=True,
        log_level="info"
    )