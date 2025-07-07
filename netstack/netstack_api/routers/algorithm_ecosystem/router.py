"""
主路由器 - 重構後的簡化版本
只負責路由註冊，具體實現委派給端點模組
"""

import logging
from typing import Dict, List, Any
from fastapi import APIRouter, Depends, BackgroundTasks

from .schemas import *
from .dependencies import (
    get_algorithm_registry,
    get_environment_manager,
    get_handover_orchestrator,
    LifecycleManager
)
from .endpoints import AlgorithmEcosystemEndpoints

logger = logging.getLogger(__name__)

# 創建路由器
router = APIRouter(prefix="/api/v1/algorithm-ecosystem", tags=["Algorithm Ecosystem"])

# 端點實例
endpoints = AlgorithmEcosystemEndpoints()


# === 核心預測端點 ===

@router.post("/predict", response_model=HandoverDecisionResponse)
async def predict_handover(request: HandoverPredictionRequest):
    """換手預測"""
    return await endpoints.predict_handover(request)


# === 算法管理端點 ===

@router.get("/algorithms", response_model=List[AlgorithmInfoResponse])
async def list_algorithms():
    """列出所有可用算法"""
    return await endpoints.list_algorithms()


@router.post("/algorithms/register", response_model=OperationResponse)
async def register_algorithm(request: AlgorithmRegistrationRequest):
    """註冊新算法"""
    return await endpoints.register_algorithm(request)


@router.delete("/algorithms/{algorithm_name}", response_model=OperationResponse)
async def unregister_algorithm(algorithm_name: str):
    """註銷算法"""
    return await endpoints.unregister_algorithm(algorithm_name)


@router.post("/algorithms/{algorithm_name}/enable", response_model=OperationResponse)
async def enable_algorithm(algorithm_name: str):
    """啟用算法"""
    return await endpoints.enable_algorithm(algorithm_name)


@router.post("/algorithms/{algorithm_name}/disable", response_model=OperationResponse)
async def disable_algorithm(algorithm_name: str):
    """禁用算法"""
    return await endpoints.disable_algorithm(algorithm_name)


# === 協調器管理端點 ===

@router.get("/orchestrator/stats", response_model=StatsResponse)
async def get_orchestrator_stats():
    """獲取協調器統計信息"""
    return await endpoints.get_orchestrator_stats()


@router.put("/orchestrator/config", response_model=OperationResponse)
async def update_orchestrator_config(request: OrchestratorConfigRequest):
    """更新協調器配置"""
    return await endpoints.update_orchestrator_config(request)


# === 環境管理端點 ===

@router.get("/environment/stats", response_model=StatsResponse)
async def get_environment_stats():
    """獲取環境統計信息"""
    return await endpoints.get_environment_stats()


# === A/B測試端點 ===

@router.post("/ab-tests", response_model=OperationResponse)
async def set_ab_test_config(request: ABTestConfigRequest):
    """設置A/B測試配置"""
    return await endpoints.set_ab_test_config(request)


@router.get("/ab-tests/{test_id}/performance")
async def get_ab_test_performance(test_id: str):
    """獲取A/B測試性能數據"""
    return await endpoints.get_ab_test_performance(test_id)


# === 統計和監控端點 ===

@router.get("/registry/stats", response_model=StatsResponse)
async def get_registry_stats():
    """獲取註冊中心統計信息"""
    return await endpoints.get_registry_stats()


@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """健康檢查"""
    return await endpoints.health_check()


@router.post("/metrics/export")
async def export_metrics(request: MetricsExportRequest):
    """導出指標數據"""
    return await endpoints.export_metrics(request)


# === 生命週期事件 ===

@router.on_event("startup")
async def startup_event():
    """啟動事件處理"""
    await LifecycleManager.startup()


@router.on_event("shutdown")
async def shutdown_event():
    """關閉事件處理"""
    await LifecycleManager.shutdown()