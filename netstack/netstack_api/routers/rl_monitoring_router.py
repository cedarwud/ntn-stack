"""
RL 訓練監控路由器

提供強化學習訓練過程的實時監控和管理 API 端點
"""

import sys
import os
import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import subprocess
import psutil

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, Path as PathParam
from pydantic import BaseModel, Field
import structlog

# 添加路徑以便導入
# 路徑配置已在容器內設定，無需手動添加
# sys.path.append('/home/sat/ntn-stack')
# sys.path.append('/home/sat/ntn-stack/netstack')

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/api/v1/rl", tags=["RL Training Monitoring"])

# 全局狀態管理
training_sessions: Dict[str, Dict[str, Any]] = {}
active_processes: Dict[str, subprocess.Popen] = {}


# Pydantic 模型定義
class TrainingConfig(BaseModel):
    """RL 訓練配置"""
    algorithm: str = Field(..., description="算法類型", pattern="^(dqn|ppo|sac)$")
    episodes: int = Field(1000, description="訓練回合數", ge=100, le=10000)
    learning_rate: float = Field(3e-4, description="學習率", gt=0, le=1)
    batch_size: int = Field(64, description="批次大小", ge=16, le=512)
    buffer_size: int = Field(100000, description="經驗回放緩衝區大小", ge=1000)
    environment_config: Dict[str, Any] = Field(
        default_factory=lambda: {
            "num_ues": 5,
            "num_satellites": 10,
            "simulation_time": 100.0
        },
        description="環境配置"
    )
    save_frequency: int = Field(100, description="模型保存頻率", ge=10)
    evaluation_frequency: int = Field(50, description="評估頻率", ge=10)


class TrainingStatus(BaseModel):
    """訓練狀態"""
    session_id: str
    algorithm: str
    status: str  # idle, running, paused, completed, failed
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    current_episode: int = 0
    total_episodes: int = 0
    current_reward: float = 0.0
    average_reward: float = 0.0
    best_reward: float = float('-inf')
    success_rate: float = 0.0
    training_time_seconds: float = 0.0
    config: Dict[str, Any] = {}
    metrics_history: List[Dict[str, Any]] = []
    error_message: Optional[str] = None


class ModelInfo(BaseModel):
    """模型資訊"""
    model_id: str
    algorithm: str
    creation_time: datetime
    file_size_mb: float
    performance_metrics: Dict[str, float]
    config: Dict[str, Any]


class AlgorithmComparisonRequest(BaseModel):
    """算法對比請求"""
    algorithms: List[str] = Field(..., description="要對比的算法列表")
    test_scenarios: int = Field(100, description="測試場景數量", ge=10, le=1000)
    environment_config: Dict[str, Any] = Field(
        default_factory=lambda: {
            "num_ues": 5,
            "num_satellites": 10
        }
    )


# API 端點實現

@router.get("/status")
async def get_system_status():
    """獲取 RL 系統整體狀態"""
    try:
        # 檢查系統資源
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # 檢查可用模型
        model_dir = Path("/app/models")
        available_models = []
        
        if model_dir.exists():
            for model_file in model_dir.glob("*.zip"):
                try:
                    file_stat = model_file.stat()
                    available_models.append({
                        "name": model_file.stem,
                        "size_mb": round(file_stat.st_size / 1024 / 1024, 2),
                        "created": datetime.fromtimestamp(file_stat.st_ctime).isoformat()
                    })
                except Exception as e:
                    logger.warning(f"無法讀取模型文件 {model_file}: {e}")
        
        # 檢查活躍訓練會話
        active_sessions = len([s for s in training_sessions.values() if s.get('status') == 'running'])
        
        return {
            "status": "ready",
            "system_resources": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": disk.percent,
                "available_memory_gb": round(memory.available / 1024**3, 2)
            },
            "available_models": available_models,
            "active_training_sessions": active_sessions,
            "total_sessions": len(training_sessions),
            "supported_algorithms": ["dqn", "ppo", "sac"],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"獲取系統狀態失敗: {e}")
        raise HTTPException(status_code=500, detail=f"系統狀態檢查失敗: {str(e)}")


@router.post("/training/start")
async def start_training(
    config: TrainingConfig,
    background_tasks: BackgroundTasks,
    session_name: Optional[str] = Query(None, description="訓練會話名稱")
):
    """啟動 RL 訓練"""
    try:
        # 生成會話 ID
        session_id = session_name or f"{config.algorithm}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if session_id in training_sessions and training_sessions[session_id].get('status') == 'running':
            raise HTTPException(status_code=400, detail=f"訓練會話 {session_id} 已在運行")
        
        # 創建訓練狀態
        training_sessions[session_id] = {
            "session_id": session_id,
            "algorithm": config.algorithm,
            "status": "starting",
            "start_time": datetime.now(),
            "current_episode": 0,
            "total_episodes": config.episodes,
            "current_reward": 0.0,
            "average_reward": 0.0,
            "best_reward": float('-inf'),
            "success_rate": 0.0,
            "training_time_seconds": 0.0,
            "config": config.dict(),
            "metrics_history": [],
            "error_message": None
        }
        
        # 啟動背景訓練任務
        background_tasks.add_task(run_training_session, session_id, config)
        
        logger.info(f"啟動 RL 訓練會話: {session_id}")
        
        return {
            "message": f"RL 訓練會話 {session_id} 已啟動",
            "session_id": session_id,
            "algorithm": config.algorithm,
            "estimated_duration_minutes": config.episodes / 10,  # 粗估
            "status": "starting"
        }
        
    except Exception as e:
        logger.error(f"啟動訓練失敗: {e}")
        raise HTTPException(status_code=500, detail=f"啟動訓練失敗: {str(e)}")


@router.get("/training/{session_id}/status")
async def get_training_status(session_id: str = PathParam(..., description="訓練會話 ID")):
    """獲取指定訓練會話的狀態"""
    if session_id not in training_sessions:
        raise HTTPException(status_code=404, detail=f"未找到訓練會話: {session_id}")
    
    session = training_sessions[session_id]
    
    # 計算進度
    progress = 0.0
    if session['total_episodes'] > 0:
        progress = min(session['current_episode'] / session['total_episodes'], 1.0)
    
    # 計算訓練時間
    training_time = 0.0
    if session.get('start_time'):
        if session['status'] == 'running':
            training_time = (datetime.now() - session['start_time']).total_seconds()
        elif session.get('end_time'):
            training_time = (session['end_time'] - session['start_time']).total_seconds()
    
    # 估算剩餘時間
    estimated_remaining = None
    if session['status'] == 'running' and progress > 0.01:
        avg_time_per_episode = training_time / max(session['current_episode'], 1)
        remaining_episodes = session['total_episodes'] - session['current_episode']
        estimated_remaining = remaining_episodes * avg_time_per_episode
    
    return TrainingStatus(
        session_id=session_id,
        algorithm=session['algorithm'],
        status=session['status'],
        start_time=session.get('start_time'),
        end_time=session.get('end_time'),
        current_episode=session['current_episode'],
        total_episodes=session['total_episodes'],
        current_reward=session['current_reward'],
        average_reward=session['average_reward'],
        best_reward=session['best_reward'],
        success_rate=session['success_rate'],
        training_time_seconds=training_time,
        config=session['config'],
        metrics_history=session['metrics_history'][-50:],  # 只返回最近50個指標
        error_message=session.get('error_message')
    ).dict() | {
        "progress_percent": round(progress * 100, 2),
        "estimated_remaining_seconds": estimated_remaining
    }


@router.get("/training/sessions")
async def list_training_sessions(
    status: Optional[str] = Query(None, description="過濾狀態"),
    algorithm: Optional[str] = Query(None, description="過濾算法"),
    limit: int = Query(50, description="返回數量限制", ge=1, le=100)
):
    """列出訓練會話"""
    sessions = list(training_sessions.values())
    
    # 過濾
    if status:
        sessions = [s for s in sessions if s.get('status') == status]
    if algorithm:
        sessions = [s for s in sessions if s.get('algorithm') == algorithm]
    
    # 排序（最新的在前）
    sessions.sort(key=lambda x: x.get('start_time', datetime.min), reverse=True)
    
    # 限制數量
    sessions = sessions[:limit]
    
    # 簡化返回的資料
    simplified_sessions = []
    for session in sessions:
        simplified_sessions.append({
            "session_id": session['session_id'],
            "algorithm": session['algorithm'],
            "status": session['status'],
            "start_time": session.get('start_time'),
            "progress": round(session['current_episode'] / max(session['total_episodes'], 1) * 100, 1),
            "current_reward": session['current_reward'],
            "average_reward": session['average_reward']
        })
    
    return {
        "sessions": simplified_sessions,
        "total_count": len(training_sessions),
        "filtered_count": len(simplified_sessions)
    }


@router.post("/training/{session_id}/stop")
async def stop_training(session_id: str = PathParam(..., description="訓練會話 ID")):
    """停止訓練會話"""
    if session_id not in training_sessions:
        raise HTTPException(status_code=404, detail=f"未找到訓練會話: {session_id}")
    
    session = training_sessions[session_id]
    
    if session['status'] not in ['running', 'starting']:
        raise HTTPException(status_code=400, detail=f"會話 {session_id} 無法停止，當前狀態: {session['status']}")
    
    try:
        # 終止進程
        if session_id in active_processes:
            process = active_processes[session_id]
            if process.poll() is None:  # 進程仍在運行
                process.terminate()
                await asyncio.sleep(2)
                if process.poll() is None:
                    process.kill()
            del active_processes[session_id]
        
        # 更新狀態
        session['status'] = 'stopped'
        session['end_time'] = datetime.now()
        
        logger.info(f"已停止訓練會話: {session_id}")
        
        return {
            "message": f"訓練會話 {session_id} 已停止",
            "session_id": session_id,
            "final_episode": session['current_episode'],
            "final_reward": session['current_reward']
        }
        
    except Exception as e:
        logger.error(f"停止訓練會話失敗: {e}")
        session['status'] = 'error'
        session['error_message'] = str(e)
        raise HTTPException(status_code=500, detail=f"停止訓練失敗: {str(e)}")


@router.get("/models")
async def list_models():
    """列出可用的訓練模型"""
    try:
        model_dir = Path("/app/models")
        models = []
        
        if model_dir.exists():
            for model_file in model_dir.glob("*.zip"):
                try:
                    file_stat = model_file.stat()
                    
                    # 嘗試從文件名解析算法類型
                    algorithm = "unknown"
                    if "dqn" in model_file.name.lower():
                        algorithm = "dqn"
                    elif "ppo" in model_file.name.lower():
                        algorithm = "ppo"
                    elif "sac" in model_file.name.lower():
                        algorithm = "sac"
                    
                    models.append(ModelInfo(
                        model_id=model_file.stem,
                        algorithm=algorithm,
                        creation_time=datetime.fromtimestamp(file_stat.st_ctime),
                        file_size_mb=round(file_stat.st_size / 1024 / 1024, 2),
                        performance_metrics={},  # 需要額外的元數據文件
                        config={}
                    ))
                    
                except Exception as e:
                    logger.warning(f"處理模型文件 {model_file} 時出錯: {e}")
        
        return {
            "models": [model.dict() for model in models],
            "total_count": len(models),
            "model_directory": str(model_dir)
        }
        
    except Exception as e:
        logger.error(f"列出模型失敗: {e}")
        raise HTTPException(status_code=500, detail=f"列出模型失敗: {str(e)}")


@router.post("/compare")
async def start_algorithm_comparison(
    request: AlgorithmComparisonRequest,
    background_tasks: BackgroundTasks
):
    """啟動算法對比評估"""
    try:
        comparison_id = f"comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 驗證算法列表
        valid_algorithms = ["dqn", "ppo", "sac", "infocom2024", "simple_threshold", "random"]
        invalid_algorithms = [algo for algo in request.algorithms if algo not in valid_algorithms]
        
        if invalid_algorithms:
            raise HTTPException(
                status_code=400, 
                detail=f"不支援的算法: {invalid_algorithms}. 支援的算法: {valid_algorithms}"
            )
        
        # 創建對比任務狀態
        comparison_status = {
            "comparison_id": comparison_id,
            "status": "starting",
            "algorithms": request.algorithms,
            "test_scenarios": request.test_scenarios,
            "start_time": datetime.now(),
            "progress": 0,
            "results": {},
            "error_message": None
        }
        
        # 存儲狀態（使用全局字典或數據庫）
        # 這裡簡化為內存存儲
        if not hasattr(start_algorithm_comparison, '_comparisons'):
            start_algorithm_comparison._comparisons = {}
        start_algorithm_comparison._comparisons[comparison_id] = comparison_status
        
        # 啟動背景任務
        background_tasks.add_task(run_algorithm_comparison, comparison_id, request)
        
        return {
            "message": "算法對比評估已啟動",
            "comparison_id": comparison_id,
            "algorithms": request.algorithms,
            "test_scenarios": request.test_scenarios,
            "estimated_duration_minutes": len(request.algorithms) * 5
        }
        
    except Exception as e:
        logger.error(f"啟動算法對比失敗: {e}")
        raise HTTPException(status_code=500, detail=f"啟動算法對比失敗: {str(e)}")


@router.get("/compare/{comparison_id}/status")
async def get_comparison_status(comparison_id: str = PathParam(..., description="對比任務 ID")):
    """獲取算法對比狀態"""
    if not hasattr(start_algorithm_comparison, '_comparisons'):
        raise HTTPException(status_code=404, detail="未找到對比任務")
    
    comparisons = start_algorithm_comparison._comparisons
    
    if comparison_id not in comparisons:
        raise HTTPException(status_code=404, detail=f"未找到對比任務: {comparison_id}")
    
    comparison = comparisons[comparison_id]
    
    # 計算進度
    total_algorithms = len(comparison['algorithms'])
    completed_algorithms = len([algo for algo, result in comparison['results'].items() if result is not None])
    progress = (completed_algorithms / total_algorithms) * 100 if total_algorithms > 0 else 0
    
    return {
        "comparison_id": comparison_id,
        "status": comparison['status'],
        "progress_percent": round(progress, 1),
        "algorithms": comparison['algorithms'],
        "completed_algorithms": list(comparison['results'].keys()),
        "start_time": comparison['start_time'],
        "results": comparison['results'],
        "error_message": comparison.get('error_message')
    }


# 背景任務函數

async def run_training_session(session_id: str, config: TrainingConfig):
    """運行 RL 訓練會話的背景任務"""
    session = training_sessions[session_id]
    
    try:
        session['status'] = 'running'
        
        # 構建訓練命令
        script_path = f"/app/scripts/rl_training/train_{config.algorithm}.py"
        
        cmd = [
            "docker", "exec", "simworld_backend",
            "python", script_path,
            "--episodes", str(config.episodes),
            "--learning-rate", str(config.learning_rate),
            "--batch-size", str(config.batch_size),
            "--session-id", session_id
        ]
        
        # 啟動訓練進程
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        active_processes[session_id] = process
        
        # 監控訓練進度
        while process.poll() is None:
            try:
                # 模擬從進程輸出讀取進度資訊
                # 實際實現中應該解析訓練腳本的輸出
                await asyncio.sleep(5)
                
                # 更新模擬進度
                session['current_episode'] = min(session['current_episode'] + 5, config.episodes)
                session['current_reward'] = session['current_reward'] + (0.1 if session['current_episode'] % 10 == 0 else 0)
                session['average_reward'] = session['current_reward'] / max(session['current_episode'], 1)
                
                if session['current_episode'] >= config.episodes:
                    break
                    
            except Exception as e:
                logger.error(f"訓練監控錯誤: {e}")
                break
        
        # 檢查進程結果
        return_code = process.wait()
        
        if return_code == 0:
            session['status'] = 'completed'
            logger.info(f"訓練會話 {session_id} 成功完成")
        else:
            session['status'] = 'failed'
            stderr_output = process.stderr.read() if process.stderr else "未知錯誤"
            session['error_message'] = stderr_output
            logger.error(f"訓練會話 {session_id} 失敗: {stderr_output}")
        
    except Exception as e:
        session['status'] = 'error'
        session['error_message'] = str(e)
        logger.error(f"訓練會話 {session_id} 異常: {e}")
    
    finally:
        session['end_time'] = datetime.now()
        if session_id in active_processes:
            del active_processes[session_id]


async def run_algorithm_comparison(comparison_id: str, request: AlgorithmComparisonRequest):
    """運行算法對比評估的背景任務"""
    if not hasattr(start_algorithm_comparison, '_comparisons'):
        return
    
    comparison = start_algorithm_comparison._comparisons[comparison_id]
    
    try:
        comparison['status'] = 'running'
        
        # 這裡調用實際的算法對比腳本
        # 實際實現應該調用我們之前創建的 algorithm_comparison.py
        
        for algorithm in request.algorithms:
            try:
                # 模擬算法評估
                await asyncio.sleep(2)  # 模擬評估時間
                
                # 模擬評估結果
                comparison['results'][algorithm] = {
                    "average_latency": 20.0 + len(algorithm),  # 模擬數據
                    "success_rate": 0.9 + 0.01 * len(algorithm),
                    "average_decision_time": 1.0 + 0.1 * len(algorithm),
                    "test_scenarios": request.test_scenarios
                }
                
            except Exception as e:
                comparison['results'][algorithm] = {
                    "error": str(e)
                }
        
        comparison['status'] = 'completed'
        
    except Exception as e:
        comparison['status'] = 'failed'
        comparison['error_message'] = str(e)
        logger.error(f"算法對比 {comparison_id} 失敗: {e}")


# 初始化
@router.on_event("startup")
async def startup_event():
    """路由器啟動事件"""
    logger.info("RL 監控路由器已啟動")
    
    # 創建必要的目錄 (使用容器內的路徑)
    try:
        model_dir = Path("/app/models")
        model_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"模型目錄已創建: {model_dir}")
        
        results_dir = Path("/app/results")
        results_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"結果目錄已創建: {results_dir}")
    except Exception as e:
        logger.warning(f"無法創建目錄: {e}，將使用臨時目錄")