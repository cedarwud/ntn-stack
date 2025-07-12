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
