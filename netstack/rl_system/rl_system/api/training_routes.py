import logging
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Dict, Any
from dataclasses import asdict

from ..core.algorithm_factory import AlgorithmFactory

# 確保演算法模組被加載，以便它們可以向工廠註冊
from ..algorithms import dqn_algorithm
from ..interfaces.rl_algorithm import TrainingConfig

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/rl/training", tags=["RL Training"])

# 模擬一個簡單的、內存中的任務狀態跟蹤器
# 在生產環境中，這應該由一個更穩健的系統（如 Redis, Celery）來處理
training_status_db: Dict[str, Any] = {}


@router.post("/start/{algorithm_name}")
async def start_training(
    algorithm_name: str, config: TrainingConfig, background_tasks: BackgroundTasks
):
    """
    異步啟動一個強化學習訓練任務。
    """
    logger.info(
        f"Received request to start training for algorithm: '{algorithm_name}' with config: {config}"
    )

    if training_status_db.get(algorithm_name) == "running":
        raise HTTPException(
            status_code=409,
            detail=f"Training for algorithm '{algorithm_name}' is already in progress.",
        )

    try:
        # 使用工廠創建算法實例
        # 這裡的 config 暫時為空，稍後可以擴展
        algorithm = AlgorithmFactory.create_algorithm(algorithm_name, {})

        # 定義要在背景運行的訓練函數
        async def training_task():
            logger.info(f"Background task started for algorithm '{algorithm_name}'.")
            training_status_db[algorithm_name] = "running"
            result = await algorithm.train(config)
            # 訓練完成後更新狀態
            training_status_db[algorithm_name] = {
                "status": "completed",
                "result": asdict(result),  # 使用 dataclasses.asdict
            }
            logger.info(
                f"Background task finished for algorithm '{algorithm_name}'. Result: {result}"
            )

        # 將訓練函數添加到背景任務
        background_tasks.add_task(training_task)

        # 立即返回，告知客戶端任務已開始
        return {
            "message": f"Training for '{algorithm_name}' started in the background."
        }

    except ValueError as e:
        logger.error(f"Failed to create algorithm '{algorithm_name}': {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="An internal server error occurred."
        )


@router.get("/status/{algorithm_name}")
async def get_training_status(algorithm_name: str):
    """
    獲取指定算法的訓練狀態。
    """
    status = training_status_db.get(algorithm_name, "not_found")
    if status == "not_found":
        raise HTTPException(
            status_code=404, detail=f"No training session found for '{algorithm_name}'."
        )

    return {"algorithm": algorithm_name, "status": status}
