import asyncio
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any

from ..core.algorithm_factory import get_algorithm

router = APIRouter()

# 這是一個全域變數，用來儲存目前正在運行的演算法實例。
# 在真實的多使用者、可擴展的應用中，這應該被一個更健壯的狀態管理器所取代，
# 例如 Redis、資料庫，或者一個專門的 Actor System (如 Ray)。
# 目前，為了簡化，我們只在記憶體中追蹤單一的訓練任務。
background_tasks: Dict[str, asyncio.Task] = {}
training_instances: Dict[str, Any] = {}


@router.post("/start/{algorithm}")
async def start_training(algorithm: str, background_tasks_param: BackgroundTasks):
    """
    啟動一個新的強化學習訓練任務。
    """
    if algorithm in background_tasks and not background_tasks[algorithm].done():
        raise HTTPException(
            status_code=409, detail=f"演算法 '{algorithm}' 的訓練任務已在執行中。"
        )

    try:
        # 在此處我們硬編碼環境名稱和設定，未來應從請求或設定檔中讀取。
        env_name = "CartPole-v1"
        config = {"total_episodes": 1000, "step_time": 0.1}

        trainer = get_algorithm(algorithm, env_name, config)
        training_instances[algorithm] = trainer

        # 使用 FastAPI 的 BackgroundTasks 來在背景執行訓練循環
        background_tasks_param.add_task(run_training_loop, algorithm, trainer)

        return {"message": f"演算法 '{algorithm}' 的訓練已啟動。"}

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"無法啟動訓練: {e}")


async def run_training_loop(algorithm: str, trainer: Any):
    """
    在背景運行的訓練循環。
    """
    try:
        # 由於 train() 方法不是 async，我們需要在執行器中運行它
        loop = asyncio.get_event_loop()
        task = loop.run_in_executor(None, trainer.train)
        background_tasks[algorithm] = task
        await task
    except asyncio.CancelledError:
        print(f"演算法 '{algorithm}' 的訓練任務被取消。")
    finally:
        if algorithm in background_tasks:
            del background_tasks[algorithm]
        if algorithm in training_instances:
            del training_instances[algorithm]


@router.get("/status/{algorithm}")
async def get_training_status(algorithm: str):
    """
    獲取指定演算法的訓練狀態。
    """
    # 支持的演算法列表
    supported_algorithms = ["dqn", "ppo", "sac"]
    
    if algorithm not in supported_algorithms:
        raise HTTPException(
            status_code=400, detail=f"不支援的演算法 '{algorithm}'。支援的演算法: {supported_algorithms}"
        )
    
    # 如果沒有訓練實例，返回未訓練狀態
    if algorithm not in training_instances:
        return {
            "algorithm": algorithm,
            "status": "not_running",
            "message": f"演算法 '{algorithm}' 目前沒有在訓練中",
            "is_training": False,
            "training_progress": None,
            "metrics": None
        }

    trainer = training_instances[algorithm]
    return trainer.get_status()


@router.post("/stop/{algorithm}")
async def stop_training(algorithm: str):
    """
    停止一個正在進行的訓練任務。
    """
    if algorithm not in background_tasks or background_tasks[algorithm].done():
        raise HTTPException(
            status_code=404, detail=f"找不到正在執行的演算法 '{algorithm}' 訓練任務。"
        )

    task = background_tasks[algorithm]
    task.cancel()

    trainer = training_instances.get(algorithm)
    if trainer:
        trainer.stop_training()

    return {"message": f"正在停止演算法 '{algorithm}' 的訓練任務..."}


@router.get("/performance-metrics")
async def get_training_performance_metrics():
    """獲取訓練性能指標 - 為前端 RL 監控系統提供"""
    try:
        # 收集所有算法的性能數據
        performance_data = {}
        active_algorithms = []
        
        for algorithm_name, trainer in training_instances.items():
            if trainer and hasattr(trainer, 'get_status'):
                status = trainer.get_status()
                performance_data[algorithm_name] = status
                
                # 檢查是否正在訓練
                if algorithm_name in background_tasks and not background_tasks[algorithm_name].done():
                    active_algorithms.append(algorithm_name)
        
        # 計算整體性能指標
        total_algorithms = len(performance_data)
        active_count = len(active_algorithms)
        
        # 計算平均指標
        avg_success_rate = 0.85  # 模擬成功率
        avg_throughput = active_count * 10  # 模擬吞吐量
        avg_response_time = 0.05  # 模擬響應時間
        
        return {
            "latency": avg_response_time * 1000,  # 轉換為毫秒
            "success_rate": avg_success_rate,
            "throughput": avg_throughput,
            "error_rate": 1 - avg_success_rate,
            "response_time": avg_response_time,
            "resource_utilization": {
                "cpu": 45.2,  # 模擬 CPU 使用率
                "memory": 68.5  # 模擬記憶體使用率
            },
            "active_algorithms": active_algorithms,
            "total_algorithms": total_algorithms,
            "algorithm_performance": performance_data,
            "timestamp": "2025-07-15T10:00:00Z"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取訓練性能指標失敗: {str(e)}")


@router.get("/status-summary")
async def get_training_status_summary():
    """獲取所有算法的訓練狀態摘要"""
    try:
        supported_algorithms = ["dqn", "ppo", "sac"]
        summary = {}
        
        for algorithm in supported_algorithms:
            if algorithm in training_instances:
                trainer = training_instances[algorithm]
                summary[algorithm] = trainer.get_status()
            else:
                summary[algorithm] = {
                    "algorithm": algorithm,
                    "status": "not_running",
                    "message": f"演算法 '{algorithm}' 目前沒有在訓練中",
                    "is_training": False,
                    "training_progress": None,
                    "metrics": None
                }
        
        # 計算整體統計
        total_algorithms = len(supported_algorithms)
        active_algorithms = [algo for algo in supported_algorithms 
                           if algo in background_tasks and not background_tasks[algo].done()]
        
        return {
            "algorithms": summary,
            "total_algorithms": total_algorithms,
            "active_algorithms": active_algorithms,
            "active_count": len(active_algorithms),
            "timestamp": "2025-07-15T10:00:00Z"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取訓練狀態摘要失敗: {str(e)}")
