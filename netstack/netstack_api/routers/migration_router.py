"""
AI Decision Engine Migration API Router
=======================================

階段6：新舊系統串接與安全切換管理API
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field
import structlog

from ..services.ai_decision_integration.migration import (
    get_feature_flag_manager,
    get_api_proxy,
    FeatureStatus,
    MigrationStep
)
from ..services.ai_decision_integration.migration.orchestrator import (
    get_migration_orchestrator,
    MigrationPhase
)

logger = structlog.get_logger(__name__)

# 創建路由器
router = APIRouter(
    prefix="/api/migration",
    tags=["AI Decision Migration"],
)

# Pydantic 模型
class FeatureFlagUpdate(BaseModel):
    """特性開關更新請求"""
    feature_name: str = Field(..., description="特性名稱")
    enabled: bool = Field(..., description="是否啟用")
    percentage: float = Field(100.0, ge=0.0, le=100.0, description="啟用百分比")
    updated_by: str = Field("admin", description="更新者")

class MigrationStepRequest(BaseModel):
    """遷移步驟請求"""
    step_name: str = Field(..., description="步驟名稱")
    force: bool = Field(False, description="強制執行")

class ProxyTestRequest(BaseModel):
    """代理測試請求"""
    test_data: Dict[str, Any] = Field(..., description="測試數據")
    user_id: Optional[str] = Field(None, description="用戶ID")
    force_new_api: Optional[bool] = Field(None, description="強制使用新API")

# --- 特性開關管理 ---

@router.get("/feature-flags")
async def get_feature_flags():
    """獲取所有特性開關狀態"""
    try:
        manager = get_feature_flag_manager()
        status = manager.get_migration_status()
        return {
            "success": True,
            "feature_flags": status["feature_flags"],
            "migration_steps": status["migration_steps"]
        }
    except Exception as e:
        logger.error("Failed to get feature flags", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/feature-flags/update")
async def update_feature_flag(request: FeatureFlagUpdate):
    """更新特性開關"""
    try:
        manager = get_feature_flag_manager()
        
        if request.enabled:
            success = await manager.enable_feature(
                request.feature_name,
                request.percentage,
                request.updated_by
            )
        else:
            success = await manager.disable_feature(
                request.feature_name,
                request.updated_by
            )
        
        if not success:
            raise HTTPException(
                status_code=400, 
                detail=f"Failed to update feature: {request.feature_name}"
            )
        
        return {
            "success": True,
            "message": f"Feature {request.feature_name} updated successfully",
            "feature_name": request.feature_name,
            "enabled": request.enabled,
            "percentage": request.percentage if request.enabled else 0.0
        }
        
    except Exception as e:
        logger.error("Failed to update feature flag", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/feature-flags/{feature_name}/rollback")
async def rollback_feature_flag(
    feature_name: str,
    updated_by: str = "admin"
):
    """回滾特性開關"""
    try:
        manager = get_feature_flag_manager()
        success = await manager.rollback_feature(feature_name, updated_by)
        
        if not success:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to rollback feature: {feature_name}"
            )
        
        return {
            "success": True,
            "message": f"Feature {feature_name} rolled back successfully",
            "feature_name": feature_name,
            "action": "rollback",
            "updated_by": updated_by
        }
        
    except Exception as e:
        logger.error("Failed to rollback feature flag", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/feature-flags/{feature_name}/metrics")
async def get_feature_metrics(feature_name: str):
    """獲取特性開關指標"""
    try:
        manager = get_feature_flag_manager()
        metrics = await manager.get_feature_metrics(feature_name)
        
        return {
            "success": True,
            "metrics": metrics
        }
        
    except Exception as e:
        logger.error("Failed to get feature metrics", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

# --- 遷移步驟管理 ---

@router.post("/migration-steps/execute")
async def execute_migration_step(request: MigrationStepRequest):
    """執行遷移步驟"""
    try:
        manager = get_feature_flag_manager()
        
        logger.info(f"Starting migration step: {request.step_name}")
        
        result = await manager.execute_migration_step(request.step_name)
        
        if result["success"]:
            logger.info(f"Migration step completed: {request.step_name}")
            return {
                "success": True,
                "message": f"Migration step {request.step_name} completed successfully",
                "result": result
            }
        else:
            logger.error(f"Migration step failed: {request.step_name}", error=result.get("error"))
            return {
                "success": False,
                "message": f"Migration step {request.step_name} failed",
                "error": result.get("error"),
                "details": result.get("details")
            }
        
    except Exception as e:
        logger.error("Failed to execute migration step", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/migration-steps")
async def get_migration_steps():
    """獲取所有遷移步驟"""
    try:
        manager = get_feature_flag_manager()
        status = manager.get_migration_status()
        
        return {
            "success": True,
            "migration_steps": status["migration_steps"]
        }
        
    except Exception as e:
        logger.error("Failed to get migration steps", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/migration-steps/auto-execute")
async def auto_execute_migration():
    """自動執行完整遷移流程"""
    try:
        manager = get_feature_flag_manager()
        
        # 獲取所有步驟
        status = manager.get_migration_status()
        steps = status["migration_steps"]
        
        results = []
        
        for step in steps:
            step_name = step["step_name"]
            logger.info(f"Auto-executing migration step: {step_name}")
            
            result = await manager.execute_migration_step(step_name)
            results.append({
                "step_name": step_name,
                "success": result["success"],
                "error": result.get("error"),
                "execution_time": datetime.utcnow().isoformat()
            })
            
            if not result["success"]:
                logger.error(f"Auto-migration failed at step: {step_name}")
                break
        
        all_success = all(r["success"] for r in results)
        
        return {
            "success": all_success,
            "message": "Auto-migration completed" if all_success else "Auto-migration failed",
            "results": results,
            "total_steps": len(steps),
            "completed_steps": len([r for r in results if r["success"]])
        }
        
    except Exception as e:
        logger.error("Failed to auto-execute migration", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

# --- API代理管理 ---

@router.get("/proxy/status")
async def get_proxy_status():
    """獲取代理狀態"""
    try:
        proxy = get_api_proxy()
        health = await proxy.health_check()
        
        return {
            "success": True,
            "proxy_status": health
        }
        
    except Exception as e:
        logger.error("Failed to get proxy status", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/proxy/test")
async def test_proxy(request: ProxyTestRequest):
    """測試代理功能"""
    try:
        proxy = get_api_proxy()
        
        # 創建模擬FastAPI請求
        mock_request = type('MockRequest', (), {
            'headers': {'X-User-ID': request.user_id} if request.user_id else {},
            'client': type('MockClient', (), {'host': '127.0.0.1'})()
        })()
        
        # 測試代理
        if request.force_new_api is not None:
            # 暫時修改決策邏輯進行測試
            original_method = proxy._should_use_new_api
            proxy._should_use_new_api = lambda user_id: request.force_new_api
        
        result = await proxy.proxy_comprehensive_decision(request.test_data, mock_request)
        
        if request.force_new_api is not None:
            proxy._should_use_new_api = original_method
        
        return {
            "success": True,
            "test_result": result,
            "proxy_metrics": proxy._get_metrics_summary()
        }
        
    except Exception as e:
        logger.error("Failed to test proxy", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/proxy/metrics")
async def get_proxy_metrics():
    """獲取代理指標"""
    try:
        proxy = get_api_proxy()
        metrics = proxy._get_metrics_summary()
        
        return {
            "success": True,
            "metrics": metrics
        }
        
    except Exception as e:
        logger.error("Failed to get proxy metrics", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

# --- 整合測試 ---

@router.post("/integration-test")
async def run_integration_test():
    """運行整合測試"""
    try:
        logger.info("Starting integration test")
        
        # 測試數據
        test_data = {
            "context": {
                "system_metrics": {
                    "latency_ms": 45.0,
                    "throughput_mbps": 75.0,
                    "coverage_percentage": 82.0,
                    "power_consumption_w": 120.0,
                    "sinr_db": 18.0,
                    "packet_loss_rate": 0.02,
                    "handover_success_rate": 0.95,
                    "interference_level_db": -85.0,
                    "resource_utilization": 0.65,
                    "cost_efficiency": 8.5
                },
                "network_state": {
                    "active_connections": 1250,
                    "cpu_utilization": 65.0,
                    "memory_utilization": 70.0
                },
                "interference_data": {
                    "interference_level": -85.0,
                    "sources": ["terrestrial", "inter_beam"]
                },
                "optimization_objectives": [
                    {
                        "name": "latency",
                        "weight": 0.3,
                        "is_maximize": False
                    },
                    {
                        "name": "throughput",
                        "weight": 0.4,
                        "is_maximize": True
                    }
                ]
            },
            "urgent_mode": False
        }
        
        # 測試新舊API
        proxy = get_api_proxy()
        mock_request = type('MockRequest', (), {
            'headers': {'X-User-ID': 'integration_test'},
            'client': type('MockClient', (), {'host': '127.0.0.1'})()
        })()
        
        # 測試舊API
        proxy._should_use_new_api = lambda user_id: False
        old_result = await proxy.proxy_comprehensive_decision(test_data, mock_request)
        
        # 測試新API
        proxy._should_use_new_api = lambda user_id: True
        new_result = await proxy.proxy_comprehensive_decision(test_data, mock_request)
        
        # 恢復原始邏輯
        proxy._should_use_new_api = proxy._should_use_new_api.__func__
        
        return {
            "success": True,
            "message": "Integration test completed",
            "results": {
                "old_api_result": old_result,
                "new_api_result": new_result,
                "compatibility_check": {
                    "both_success": old_result.get("success") and new_result.get("success"),
                    "response_structure_similar": "decision_id" in old_result and "success" in new_result
                }
            },
            "proxy_metrics": proxy._get_metrics_summary()
        }
        
    except Exception as e:
        logger.error("Integration test failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

# --- 系統監控 ---

@router.get("/system-status")
async def get_system_status():
    """獲取系統完整狀態"""
    try:
        manager = get_feature_flag_manager()
        proxy = get_api_proxy()
        
        # 獲取特性開關狀態
        migration_status = manager.get_migration_status()
        
        # 獲取代理狀態
        proxy_health = await proxy.health_check()
        
        # 計算遷移進度
        feature_flags = migration_status["feature_flags"]
        enabled_features = sum(1 for flag in feature_flags.values() 
                             if flag["status"] in ["enabled", "testing"])
        total_features = len(feature_flags)
        migration_progress = (enabled_features / total_features) * 100 if total_features > 0 else 0
        
        return {
            "success": True,
            "system_status": {
                "migration_progress": round(migration_progress, 1),
                "enabled_features": enabled_features,
                "total_features": total_features,
                "feature_flags": feature_flags,
                "proxy_health": proxy_health,
                "migration_steps": migration_status["migration_steps"]
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to get system status", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/emergency-rollback")
async def emergency_rollback():
    """緊急回滾所有功能"""
    try:
        manager = get_feature_flag_manager()
        
        # 獲取所有特性開關
        status = manager.get_migration_status()
        feature_flags = status["feature_flags"]
        
        rollback_results = []
        
        for feature_name, flag_info in feature_flags.items():
            if flag_info["status"] != "disabled":
                success = await manager.rollback_feature(feature_name, "emergency_rollback")
                rollback_results.append({
                    "feature_name": feature_name,
                    "success": success,
                    "previous_status": flag_info["status"]
                })
        
        return {
            "success": True,
            "message": "Emergency rollback completed",
            "rollback_results": rollback_results,
            "rollback_count": len(rollback_results),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Emergency rollback failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

# --- 協調器管理 ---

@router.post("/orchestrator/full-migration")
async def execute_full_migration():
    """執行完整遷移流程"""
    try:
        orchestrator = get_migration_orchestrator()
        
        logger.info("Starting full migration process")
        
        results = await orchestrator.execute_full_migration()
        
        all_success = all(r.success for r in results)
        
        return {
            "success": all_success,
            "message": "Full migration completed" if all_success else "Migration failed",
            "results": [
                {
                    "phase": r.phase.value,
                    "success": r.success,
                    "completed_steps": r.completed_steps,
                    "failed_steps": r.failed_steps,
                    "error_message": r.error_message,
                    "duration": str(r.duration) if r.duration else None
                }
                for r in results
            ],
            "total_phases": len(results),
            "completed_phases": len([r for r in results if r.success])
        }
        
    except Exception as e:
        logger.error("Full migration execution failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/orchestrator/execute-phase")
async def execute_migration_phase(phase: str):
    """執行特定遷移階段"""
    try:
        orchestrator = get_migration_orchestrator()
        
        # 驗證階段名稱
        try:
            migration_phase = MigrationPhase(phase)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid phase: {phase}. Valid phases: {[p.value for p in MigrationPhase]}"
            )
        
        logger.info(f"Executing migration phase: {phase}")
        
        result = await orchestrator.execute_phase(migration_phase)
        
        return {
            "success": result.success,
            "message": f"Phase {phase} completed" if result.success else f"Phase {phase} failed",
            "phase": result.phase.value,
            "completed_steps": result.completed_steps,
            "failed_steps": result.failed_steps,
            "error_message": result.error_message,
            "duration": str(result.duration) if result.duration else None,
            "metrics": result.metrics
        }
        
    except Exception as e:
        logger.error("Migration phase execution failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/orchestrator/rollback-to-phase")
async def rollback_to_phase(target_phase: str):
    """回滾到指定階段"""
    try:
        orchestrator = get_migration_orchestrator()
        
        # 驗證階段名稱
        try:
            migration_phase = MigrationPhase(target_phase)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid phase: {target_phase}. Valid phases: {[p.value for p in MigrationPhase]}"
            )
        
        logger.info(f"Rolling back to phase: {target_phase}")
        
        await orchestrator.rollback_to_phase(migration_phase)
        
        return {
            "success": True,
            "message": f"Successfully rolled back to phase: {target_phase}",
            "current_phase": target_phase,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Rollback to phase failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/orchestrator/status")
async def get_orchestrator_status():
    """獲取協調器狀態"""
    try:
        orchestrator = get_migration_orchestrator()
        status = orchestrator.get_migration_status()
        
        return {
            "success": True,
            "orchestrator_status": status
        }
        
    except Exception as e:
        logger.error("Failed to get orchestrator status", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))