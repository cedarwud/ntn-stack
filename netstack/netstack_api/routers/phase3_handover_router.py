"""
Phase 3: 規則式換手決策 API 路由器

基於 D2/A4/A5 事件的換手決策引擎 API，支援：
- 即時換手狀態查詢
- 事件處理和決策生成  
- WebSocket 即時事件串流
- 性能監控和 KPI 統計
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Depends
from pydantic import BaseModel, Field
import structlog

# 導入 Phase 3 核心組件
try:
    from netstack.src.services.satellite.handover_event_detector import (
        RuleBasedHandoverEngine,
        HandoverDataAccess, 
        HandoverMetrics
    )
    PHASE3_AVAILABLE = True
except ImportError as e:
    PHASE3_AVAILABLE = False
    import traceback
    print(f"Phase 3 組件導入失敗: {e}")
    print(traceback.format_exc())

logger = structlog.get_logger(__name__)

# 創建路由器
router = APIRouter(prefix="/api/v1/handover", tags=["Phase 3 - 規則式換手決策"])

# 全域組件實例
handover_engine: Optional[RuleBasedHandoverEngine] = None
data_access: Optional[HandoverDataAccess] = None
metrics_system: Optional[HandoverMetrics] = None
websocket_connections: List[WebSocket] = []

# Pydantic 模型
class HandoverEvent(BaseModel):
    """換手事件模型"""
    type: str = Field(..., description="事件類型: D2, A4, A5")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    serving_satellite: Optional[Dict[str, Any]] = Field(None, description="服務衛星資訊")
    candidate_satellite: Optional[Dict[str, Any]] = Field(None, description="候選衛星資訊")
    recommended_target: Optional[Dict[str, Any]] = Field(None, description="推薦目標衛星")
    time_to_los_seconds: Optional[int] = Field(None, description="失去訊號時間（秒）")
    quality_advantage_db: Optional[float] = Field(None, description="品質優勢（dB）")
    handover_gain_db: Optional[float] = Field(None, description="換手增益（dB）")
    urgency: Optional[str] = Field("normal", description="緊急程度")

class HandoverResult(BaseModel):
    """換手執行結果模型"""
    success: bool = Field(..., description="執行是否成功")
    interruption_ms: int = Field(0, description="中斷時間（毫秒）")
    error_reason: Optional[str] = Field(None, description="失敗原因")
    completion_time: str = Field(default_factory=lambda: datetime.now().isoformat())

def get_initialized_components():
    """獲取初始化的組件"""
    global handover_engine, data_access, metrics_system
    
    if not PHASE3_AVAILABLE:
        raise HTTPException(
            status_code=503, 
            detail="Phase 3 組件不可用，請檢查相關模組"
        )
    
    # 懶初始化
    if handover_engine is None:
        try:
            handover_engine = RuleBasedHandoverEngine(scene_id="ntpu")
            data_access = HandoverDataAccess()
            metrics_system = HandoverMetrics()
            logger.info("Phase 3 組件初始化成功")
        except Exception as e:
            logger.error(f"Phase 3 組件初始化失敗: {e}")
            raise HTTPException(status_code=500, detail=f"組件初始化失敗: {str(e)}")
    
    return handover_engine, data_access, metrics_system

@router.get("/status")
async def get_handover_status():
    """獲取當前換手狀態"""
    start_time = time.time()
    
    try:
        engine, data_access, metrics = get_initialized_components()
        
        # 獲取引擎狀態
        engine_status = engine.get_current_status()
        
        # 獲取數據健康狀態
        data_health = data_access.get_data_health()
        
        # 獲取星座狀態
        constellation_status = data_access.get_constellation_status()
        
        # 獲取 KPI
        kpis = metrics.get_kpis()
        
        response_time = (time.time() - start_time) * 1000
        
        return {
            "status": "operational",
            "response_time_ms": round(response_time, 2),
            "engine_status": engine_status,
            "data_health": data_health,
            "constellation_status": constellation_status,
            "performance_kpis": kpis,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"獲取換手狀態失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/event")
async def process_handover_event(event: HandoverEvent):
    """處理換手事件"""
    start_time = time.time()
    
    try:
        engine, data_access, metrics = get_initialized_components()
        
        # 處理事件
        decision = engine.process_event(event.dict())
        
        # 記錄決策時間
        decision_time = (time.time() - start_time) * 1000
        
        if decision:
            # 記錄決策指標
            metrics.record_handover_decision(decision, decision_time)
            
            # 廣播到 WebSocket 連接
            await broadcast_to_websockets({
                "type": "handover_decision",
                "event": event.dict(),
                "decision": decision,
                "timestamp": datetime.now().isoformat()
            })
            
            return {
                "status": "decision_made",
                "decision": decision,
                "processing_time_ms": round(decision_time, 2),
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "status": "no_action_required",
                "reason": "事件條件不滿足換手要求",
                "processing_time_ms": round(decision_time, 2),
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"處理換手事件失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/result")
async def record_handover_result(
    decision_timestamp: str,
    result: HandoverResult
):
    """記錄換手執行結果"""
    try:
        engine, data_access, metrics = get_initialized_components()
        
        # 記錄執行結果
        metrics.record_handover_result(decision_timestamp, result.dict())
        
        # 如果換手完成，重置進行狀態
        if result.success:
            engine.reset_handover_progress()
        
        # 廣播結果
        await broadcast_to_websockets({
            "type": "handover_result",
            "decision_timestamp": decision_timestamp,
            "result": result.dict(),
            "timestamp": datetime.now().isoformat()
        })
        
        return {
            "status": "result_recorded",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"記錄換手結果失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/satellites/visible")
async def get_visible_satellites(
    timestamp: Optional[str] = None,
    use_cache: bool = True
):
    """獲取可見衛星列表"""
    try:
        engine, data_access, metrics = get_initialized_components()
        
        if timestamp is None:
            timestamp = datetime.now().isoformat()
        
        satellites = data_access.get_visible_satellites(timestamp, use_cache)
        
        return {
            "timestamp": timestamp,
            "visible_satellites": satellites,
            "count": len(satellites),
            "highest_elevation": max((s['elevation_deg'] for s in satellites), default=0)
        }
        
    except Exception as e:
        logger.error(f"獲取可見衛星失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/events/history")
async def get_handover_events(
    start_time: Optional[str] = None,
    end_time: Optional[str] = None
):
    """獲取換手事件歷史"""
    try:
        engine, data_access, metrics = get_initialized_components()
        
        events = data_access.get_handover_events(start_time, end_time)
        
        return {
            "query_range": {"start_time": start_time, "end_time": end_time},
            "events": events,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"獲取換手事件失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics/kpis")
async def get_handover_kpis():
    """獲取換手 KPI"""
    try:
        engine, data_access, metrics = get_initialized_components()
        
        kpis = metrics.get_kpis()
        detailed_stats = metrics.get_detailed_statistics()
        
        return {
            "kpis": kpis,
            "detailed_statistics": detailed_stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"獲取 KPI 失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics/performance")
async def get_performance_metrics():
    """獲取性能指標"""
    try:
        engine, data_access, metrics = get_initialized_components()
        
        detailed_stats = metrics.get_detailed_statistics()
        
        return {
            "performance_metrics": {
                "decision_latency_stats": {
                    "avg_ms": detailed_stats['kpis']['avg_decision_latency_ms'],
                    "recent_trend": detailed_stats['historical_trends']['decision_latency_trend'][-10:]
                },
                "interruption_stats": {
                    "avg_ms": detailed_stats['kpis']['avg_interruption_time_ms'],
                    "recent_trend": detailed_stats['historical_trends']['interruption_trend'][-10:]
                },
                "success_rate": detailed_stats['kpis']['handover_success_rate_percent'],
                "service_availability": detailed_stats['kpis']['service_availability_percent'],
                "performance_grade": detailed_stats['kpis']['performance_grade']
            },
            "system_health": detailed_stats['system_health'],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"獲取性能指標失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.websocket("/stream")
async def handover_event_stream(websocket: WebSocket):
    """即時事件串流"""
    await websocket.accept()
    websocket_connections.append(websocket)
    
    try:
        logger.info(f"WebSocket 連接建立，目前連線數: {len(websocket_connections)}")
        
        # 發送初始狀態
        try:
            engine, data_access, metrics = get_initialized_components()
            initial_status = {
                "type": "initial_status",
                "engine_status": engine.get_current_status(),
                "kpis": metrics.get_kpis(),
                "timestamp": datetime.now().isoformat()
            }
            await websocket.send_json(initial_status)
        except Exception as e:
            logger.error(f"發送初始狀態失敗: {e}")
        
        # 保持連接並定期發送心跳
        while True:
            try:
                # 等待來自客戶端的消息（如果有的話）
                await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
            except asyncio.TimeoutError:
                # 發送心跳
                await websocket.send_json({
                    "type": "heartbeat",
                    "timestamp": datetime.now().isoformat(),
                    "connections": len(websocket_connections)
                })
            except WebSocketDisconnect:
                break
                
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket 連接錯誤: {e}")
    finally:
        if websocket in websocket_connections:
            websocket_connections.remove(websocket)
        logger.info(f"WebSocket 連接關閉，剩餘連線數: {len(websocket_connections)}")

async def broadcast_to_websockets(message: Dict[str, Any]):
    """廣播消息到所有 WebSocket 連接"""
    if not websocket_connections:
        return
    
    disconnected = []
    for websocket in websocket_connections:
        try:
            await websocket.send_json(message)
        except Exception:
            disconnected.append(websocket)
    
    # 清理斷開的連接
    for ws in disconnected:
        if ws in websocket_connections:
            websocket_connections.remove(ws)

@router.get("/health")
async def health_check():
    """健康檢查端點"""
    try:
        if not PHASE3_AVAILABLE:
            return {
                "status": "unavailable",
                "reason": "Phase 3 組件不可用",
                "timestamp": datetime.now().isoformat()
            }
        
        engine, data_access, metrics = get_initialized_components()
        
        # 簡單的健康檢查
        engine_status = engine.get_current_status()
        data_health = data_access.get_data_health()
        
        all_healthy = (
            engine_status.get('engine_health') == 'operational' and
            data_health.get('orbit_data_available', False)
        )
        
        return {
            "status": "healthy" if all_healthy else "degraded",
            "components": {
                "handover_engine": engine_status.get('engine_health', 'unknown'),
                "data_access": "healthy" if data_health.get('orbit_data_available') else "degraded",
                "metrics_system": "healthy"
            },
            "websocket_connections": len(websocket_connections),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# 啟動時初始化組件
@router.on_event("startup")
async def startup_event():
    """路由器啟動事件"""
    logger.info("Phase 3 換手決策路由器啟動")
    try:
        get_initialized_components()
        logger.info("✅ Phase 3 組件預初始化成功")
    except Exception as e:
        logger.warning(f"⚠️ Phase 3 組件預初始化失敗: {e}")

@router.on_event("shutdown") 
async def shutdown_event():
    """路由器關閉事件"""
    logger.info("Phase 3 換手決策路由器關閉")
    
    # 關閉所有 WebSocket 連接
    for websocket in websocket_connections[:]:
        try:
            await websocket.close()
        except Exception:
            pass
    websocket_connections.clear()