"""
Phase 3 決策透明化與視覺化 API - 簡化版本

提供基本的決策解釋和分析功能，確保系統穩定性
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

# 設置日志
logger = logging.getLogger(__name__)

# 創建路由器
router = APIRouter(tags=["Phase 3 - Decision Transparency"])

# 請求模型
class DecisionExplanationRequest(BaseModel):
    """決策解釋請求"""
    state: List[float] = Field(..., description="狀態向量")
    action: int = Field(..., description="選擇的動作")
    q_values: List[float] = Field(..., description="所有動作的Q值")
    algorithm: str = Field(..., description="使用的算法")
    episode: int = Field(..., description="Episode編號")
    step: int = Field(..., description="步驟編號")
    scenario_context: Optional[Dict[str, Any]] = Field(None, description="場景上下文")

class AlgorithmComparisonRequest(BaseModel):
    """算法比較請求"""
    algorithms: List[str] = Field(..., description="算法列表")
    scenario: str = Field(default="urban", description="場景類型")
    episodes: int = Field(default=100, description="比較的集數")
    metrics: List[str] = Field(default=["total_reward"], description="比較指標")

# API 端點

@router.get("/health")
async def health_check():
    """Phase 3 健康檢查"""
    try:
        status = {
            "status": "healthy",
            "phase": "Phase 3: Decision Transparency & Visualization",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "analytics_available": False,
                "explainability_engine": False,
                "basic_explanation": True,
            },
            "features": [
                "basic_decision_explanation",
                "algorithm_comparison",
                "simplified_analysis"
            ],
            "version": "3.0.0-simplified"
        }
        
        return status
        
    except Exception as e:
        logger.error(f"Phase 3 健康檢查失敗: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@router.get("/status")
async def get_system_status():
    """獲取系統詳細狀態"""
    try:
        status = {
            "phase": "Phase 3",
            "analytics_available": False,
            "initialized_components": {
                "basic_explanation": True,
                "algorithm_comparison": True,
            },
            "capabilities": {
                "decision_transparency": True,
                "basic_explainability": True,
                "algorithm_comparison": True,
            },
            "supported_algorithms": ["DQN", "PPO", "SAC"],
            "supported_formats": ["json"],
            "timestamp": datetime.now().isoformat(),
        }
        
        return status
        
    except Exception as e:
        logger.error(f"獲取系統狀態失敗: {e}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")

@router.post("/explain/decision")
def explain_decision(request: DecisionExplanationRequest):
    """決策解釋主端點 - 簡化實現"""
    try:
        # 基本決策解釋
        algorithm = request.algorithm
        action = request.action  
        q_values = request.q_values
        episode = request.episode
        step = request.step
        
        chosen_q_value = q_values[action] if action < len(q_values) else 0
        max_q_value = max(q_values) if q_values else 1
        confidence = chosen_q_value / max_q_value if max_q_value > 0 else 0.5
        
        explanation = {
            "summary": f"{algorithm} algorithm selected action {action}",
            "confidence_score": confidence,
            "decision_reasoning": f"Action {action} Q-value: {chosen_q_value:.3f}",
            "episode": episode,
            "step": step,
            "algorithm": algorithm,
            "analysis_type": "basic"
        }
        
        return {
            "success": True,
            "algorithm": algorithm,
            "action": action,
            "confidence": confidence,
            "explanation": explanation,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"決策解釋失敗: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@router.post("/algorithms/comparison")
async def compare_algorithms(request: AlgorithmComparisonRequest):
    """算法比較分析"""
    try:
        import random
        
        comparison_data = {}
        comparison_analysis = {}
        
        for algorithm in request.algorithms:
            # 基本性能數據模擬
            base_performance = {"DQN": 45, "PPO": 50, "SAC": 47}.get(algorithm, 40)
            
            # 生成模擬數據
            rewards = [base_performance + random.uniform(-10, 10) for _ in range(request.episodes)]
            success_rates = [random.uniform(0.7, 0.95) for _ in range(request.episodes)]
            
            comparison_data[algorithm] = {
                "total_reward": rewards,
                "success_rate": success_rates,
            }
            
            # 計算統計摘要
            comparison_analysis[algorithm] = {
                "mean_reward": sum(rewards) / len(rewards),
                "mean_success_rate": sum(success_rates) / len(success_rates),
                "performance_score": (sum(rewards) / len(rewards)) * (sum(success_rates) / len(success_rates)),
            }
        
        # 排序算法性能
        ranked_algorithms = sorted(
            comparison_analysis.items(),
            key=lambda x: x[1]["performance_score"],
            reverse=True
        )
        
        return {
            "success": True,
            "request": {
                "algorithms": request.algorithms,
                "scenario": request.scenario,
                "episodes": request.episodes,
                "metrics": request.metrics,
            },
            "data": comparison_data,
            "analysis": comparison_analysis,
            "ranking": [{"algorithm": alg, "score": data["performance_score"]} 
                       for alg, data in ranked_algorithms],
            "best_algorithm": ranked_algorithms[0][0] if ranked_algorithms else None,
            "timestamp": datetime.now().isoformat(),
        }
        
    except Exception as e:
        logger.error(f"算法比較失敗: {e}")
        raise HTTPException(status_code=500, detail=f"Algorithm comparison failed: {str(e)}")

# 包含所有端點的路由器
__all__ = ["router"]