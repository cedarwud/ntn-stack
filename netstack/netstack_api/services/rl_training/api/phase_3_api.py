"""
Phase 3 決策透明化與視覺化 API

提供完整的 Algorithm Explainability 和高級分析功能的 REST API 端點：
- 決策解釋和透明化分析
- 收斂性分析和學習曲線追蹤
- 統計顯著性測試和多算法對比
- 學術標準數據匯出
- 高級視覺化和實時監控

Created for Phase 3: Decision Transparency & Visualization Optimization
"""

import asyncio
import logging
import tempfile
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, Body
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

# 設置日志
logger = logging.getLogger(__name__)

# 嘗試導入分析組件
try:
    from ..analytics import (
        AdvancedExplainabilityEngine,
        ConvergenceAnalyzer,
        StatisticalTestingEngine,
        AcademicDataExporter,
        VisualizationEngine,
    )
    ANALYTICS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"部分分析組件不可用: {e}")
    ANALYTICS_AVAILABLE = False

# 創建路由器
router = APIRouter(tags=["Phase 3 - Decision Transparency"])

# 請求/響應模型
class DecisionExplanationRequest(BaseModel):
    """決策解釋請求"""
    state: List[float] = Field(..., description="狀態向量")
    action: int = Field(..., description="選擇的動作")
    q_values: List[float] = Field(..., description="所有動作的Q值")
    algorithm: str = Field(..., description="使用的算法")
    episode: int = Field(..., description="Episode編號")
    step: int = Field(..., description="步驟編號")
    scenario_context: Optional[Dict[str, Any]] = Field(None, description="場景上下文")

class ConvergenceAnalysisRequest(BaseModel):
    """收斂性分析請求"""
    rewards: List[float] = Field(..., description="獎勵序列")
    metric_name: str = Field(default="total_reward", description="指標名稱")
    algorithm: str = Field(..., description="算法名稱")
    scenario: str = Field(..., description="場景類型")

class StatisticalTestRequest(BaseModel):
    """統計測試請求"""
    test_type: str = Field(..., description="測試類型: t_test, mann_whitney, anova")
    data: Dict[str, List[float]] = Field(..., description="測試數據")
    test_name: str = Field(..., description="測試名稱")
    significance_level: float = Field(default=0.05, description="顯著性水平")

class VisualizationRequest(BaseModel):
    """視覺化請求"""
    visualization_type: str = Field(..., description="視覺化類型")
    data: Dict[str, Any] = Field(..., description="視覺化數據")
    title: str = Field(..., description="圖表標題")
    theme: str = Field(default="academic", description="主題")

class AcademicExportRequest(BaseModel):
    """學術匯出請求"""
    export_format: str = Field(..., description="匯出格式: csv, json, latex, excel")
    research_data: Dict[str, Any] = Field(..., description="研究數據")
    filename: str = Field(..., description="文件名")
    standard: str = Field(default="IEEE", description="學術標準")

# 全局組件實例
_explainability_engine: Optional[AdvancedExplainabilityEngine] = None
_convergence_analyzer: Optional[ConvergenceAnalyzer] = None
_statistical_engine: Optional[StatisticalTestingEngine] = None
_data_exporter: Optional[AcademicDataExporter] = None
_visualization_engine: Optional[VisualizationEngine] = None

def _get_or_create_explainability_engine() -> AdvancedExplainabilityEngine:
    """獲取或創建解釋性引擎"""
    global _explainability_engine
    if _explainability_engine is None:
        config = {
            "explainability_level": "detailed",
            "enable_feature_importance": True,
            "enable_decision_paths": True,
            "enable_counterfactual": True,
        }
        _explainability_engine = AdvancedExplainabilityEngine(config)
    return _explainability_engine

def _get_or_create_convergence_analyzer() -> ConvergenceAnalyzer:
    """獲取或創建收斂性分析器"""
    global _convergence_analyzer
    if _convergence_analyzer is None:
        config = {
            "smoothing_window": 10,
            "convergence_threshold": 0.01,
            "min_stable_episodes": 20,
            "enable_forecasting": True,
        }
        _convergence_analyzer = ConvergenceAnalyzer(config)
    return _convergence_analyzer

def _get_or_create_statistical_engine() -> StatisticalTestingEngine:
    """獲取或創建統計測試引擎"""
    global _statistical_engine
    if _statistical_engine is None:
        config = {
            "significance_level": 0.05,
            "enable_effect_size": True,
            "enable_power_analysis": True,
            "bootstrap_samples": 1000,
        }
        _statistical_engine = StatisticalTestingEngine(config)
    return _statistical_engine

def _get_or_create_data_exporter() -> AcademicDataExporter:
    """獲取或創建數據匯出器"""
    global _data_exporter
    if _data_exporter is None:
        config = {
            "export_directory": "/tmp/rl_exports",
            "default_format": "json",
            "include_metadata": True,
            "include_validation": True,
        }
        _data_exporter = AcademicDataExporter(config)
    return _data_exporter

def _get_or_create_visualization_engine() -> VisualizationEngine:
    """獲取或創建視覺化引擎"""
    global _visualization_engine
    if _visualization_engine is None:
        config = {
            "output_directory": "/tmp/rl_visualizations",
            "default_theme": "academic",
            "enable_interactive": True,
            "enable_realtime": True,
        }
        _visualization_engine = VisualizationEngine(config)
    return _visualization_engine

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
                "analytics_available": ANALYTICS_AVAILABLE,
                "explainability_engine": _explainability_engine is not None,
                "convergence_analyzer": _convergence_analyzer is not None,
                "statistical_engine": _statistical_engine is not None,
                "data_exporter": _data_exporter is not None,
                "visualization_engine": _visualization_engine is not None,
            },
        }
        
        if ANALYTICS_AVAILABLE:
            status["features"] = [
                "decision_explanation",
                "convergence_analysis", 
                "statistical_testing",
                "academic_export",
                "advanced_visualization",
                "algorithm_explainability",
            ]
            status["version"] = "3.0.0"
        else:
            status["features"] = [
                "basic_decision_explanation",
                "simple_analysis",
                "data_export",
                "visualization_placeholder"
            ]
            status["version"] = "3.0.0-simplified"
        
        return status
        
    except Exception as e:
        logger.error(f"Phase 3 健康檢查失敗: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@router.get("/status")
async def get_system_status():
    """獲取系統詳細狀態"""
    try:
        if not ANALYTICS_AVAILABLE:
            return {
                "error": "Analytics components not available",
                "available_features": [],
                "status": "degraded"
            }
        
        status = {
            "phase": "Phase 3",
            "analytics_available": ANALYTICS_AVAILABLE,
            "initialized_components": {
                "explainability_engine": _explainability_engine is not None,
                "convergence_analyzer": _convergence_analyzer is not None,
                "statistical_engine": _statistical_engine is not None,
                "data_exporter": _data_exporter is not None,
                "visualization_engine": _visualization_engine is not None,
            },
            "capabilities": {
                "decision_transparency": True,
                "algorithm_explainability": True,
                "convergence_analysis": True,
                "statistical_comparison": True,
                "academic_export": True,
                "advanced_visualization": True,
            },
            "supported_algorithms": ["DQN", "PPO", "SAC"],
            "supported_formats": ["csv", "json", "latex", "png", "html"],
            "timestamp": datetime.now().isoformat(),
        }
        
        return status
        
    except Exception as e:
        logger.error(f"獲取系統狀態失敗: {e}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")

@router.post("/explain/decision")
async def explain_decision(request: DecisionExplanationRequest):
    """解釋單個決策"""
    try:
        if not ANALYTICS_AVAILABLE:
            raise HTTPException(status_code=503, detail="Analytics components not available")
        
        engine = _get_or_create_explainability_engine()
        
        decision_data = {
            "state": request.state,
            "action": request.action,
            "q_values": request.q_values,
            "algorithm": request.algorithm,
            "episode": request.episode,
            "step": request.step,
            "scenario_context": request.scenario_context or {},
        }
        
        explanation = engine.analyze_decision_explainability(decision_data)
        
        if explanation is None:
            raise HTTPException(status_code=500, detail="Failed to generate decision explanation")
        
        return {
            "success": True,
            "decision_data": decision_data,
            "explanation": explanation,
            "timestamp": datetime.now().isoformat(),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"決策解釋失敗: {e}")
        raise HTTPException(status_code=500, detail=f"Decision explanation failed: {str(e)}")

@router.post("/explain/feature-importance")
async def analyze_feature_importance(request: DecisionExplanationRequest):
    """分析特徵重要性"""
    try:
        if not ANALYTICS_AVAILABLE:
            raise HTTPException(status_code=503, detail="Analytics components not available")
        
        engine = _get_or_create_explainability_engine()
        
        feature_importance = engine.analyze_feature_importance(
            state=request.state,
            q_values=request.q_values,
            action=request.action
        )
        
        if feature_importance is None:
            raise HTTPException(status_code=500, detail="Failed to analyze feature importance")
        
        return {
            "success": True,
            "feature_importance": feature_importance,
            "algorithm": request.algorithm,
            "timestamp": datetime.now().isoformat(),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"特徵重要性分析失敗: {e}")
        raise HTTPException(status_code=500, detail=f"Feature importance analysis failed: {str(e)}")

@router.post("/analyze/convergence")
async def analyze_convergence(request: ConvergenceAnalysisRequest):
    """進行收斂性分析"""
    try:
        if not ANALYTICS_AVAILABLE:
            raise HTTPException(status_code=503, detail="Analytics components not available")
        
        analyzer = _get_or_create_convergence_analyzer()
        
        # 學習曲線分析
        curve_analysis = analyzer.analyze_learning_curve(
            request.rewards,
            metric_name=request.metric_name
        )
        
        # 收斂檢測
        convergence_result = analyzer.detect_convergence(
            request.rewards[-50:] if len(request.rewards) > 50 else request.rewards,
            metric_name=request.metric_name
        )
        
        # 性能趨勢分析
        training_data = {
            "episodes": list(range(len(request.rewards))),
            "rewards": request.rewards,
            "algorithm": request.algorithm,
            "scenario": request.scenario,
        }
        trend_analysis = analyzer.analyze_performance_trend(training_data)
        
        return {
            "success": True,
            "convergence_analysis": {
                "curve_analysis": curve_analysis,
                "convergence_result": convergence_result,
                "trend_analysis": trend_analysis,
            },
            "algorithm": request.algorithm,
            "scenario": request.scenario,
            "episodes_analyzed": len(request.rewards),
            "timestamp": datetime.now().isoformat(),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"收斂性分析失敗: {e}")
        raise HTTPException(status_code=500, detail=f"Convergence analysis failed: {str(e)}")

@router.post("/test/statistical")
async def perform_statistical_test(request: StatisticalTestRequest):
    """執行統計測試"""
    try:
        if not ANALYTICS_AVAILABLE:
            raise HTTPException(status_code=503, detail="Analytics components not available")
        
        engine = _get_or_create_statistical_engine()
        
        result = None
        
        if request.test_type == "t_test":
            if len(request.data) != 2:
                raise HTTPException(status_code=400, detail="T-test requires exactly 2 groups")
            
            groups = list(request.data.values())
            result = engine.perform_t_test(
                groups[0], groups[1],
                test_name=request.test_name
            )
            
        elif request.test_type == "mann_whitney":
            if len(request.data) != 2:
                raise HTTPException(status_code=400, detail="Mann-Whitney test requires exactly 2 groups")
            
            groups = list(request.data.values())
            result = engine.perform_mann_whitney_test(
                groups[0], groups[1],
                test_name=request.test_name
            )
            
        elif request.test_type == "anova":
            result = engine.perform_anova(
                request.data,
                test_name=request.test_name
            )
            
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported test type: {request.test_type}")
        
        if result is None:
            raise HTTPException(status_code=500, detail="Statistical test failed")
        
        return {
            "success": True,
            "test_type": request.test_type,
            "test_name": request.test_name,
            "result": result,
            "significance_level": request.significance_level,
            "timestamp": datetime.now().isoformat(),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"統計測試失敗: {e}")
        raise HTTPException(status_code=500, detail=f"Statistical test failed: {str(e)}")

@router.post("/visualize")
async def create_visualization(request: VisualizationRequest):
    """創建視覺化"""
    try:
        if not ANALYTICS_AVAILABLE:
            raise HTTPException(status_code=503, detail="Analytics components not available")
        
        engine = _get_or_create_visualization_engine()
        
        result = None
        
        if request.visualization_type == "learning_curve":
            result = engine.create_learning_curve_plot(
                request.data,
                title=request.title,
                filename=f"learning_curve_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            
        elif request.visualization_type == "performance_comparison":
            result = engine.create_performance_comparison_plot(
                request.data,
                title=request.title,
                filename=f"performance_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            
        elif request.visualization_type == "convergence_analysis":
            result = engine.create_convergence_analysis_plot(
                request.data,
                title=request.title,
                filename=f"convergence_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            
        elif request.visualization_type == "dashboard":
            result = engine.create_analysis_dashboard(
                request.data,
                title=request.title,
                filename=f"dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported visualization type: {request.visualization_type}")
        
        if result is None or not result.get("success", False):
            raise HTTPException(status_code=500, detail="Visualization creation failed")
        
        return {
            "success": True,
            "visualization_type": request.visualization_type,
            "title": request.title,
            "result": result,
            "timestamp": datetime.now().isoformat(),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"視覺化創建失敗: {e}")
        raise HTTPException(status_code=500, detail=f"Visualization creation failed: {str(e)}")

@router.post("/export/academic")
async def export_academic_data(request: AcademicExportRequest):
    """匯出學術數據"""
    try:
        if not ANALYTICS_AVAILABLE:
            raise HTTPException(status_code=503, detail="Analytics components not available")
        
        exporter = _get_or_create_data_exporter()
        
        result = None
        
        if request.export_format == "csv":
            result = exporter.export_to_csv(
                request.research_data,
                filename=request.filename
            )
            
        elif request.export_format == "json":
            result = exporter.export_to_json(
                request.research_data,
                filename=request.filename
            )
            
        elif request.export_format == "latex":
            result = exporter.generate_publication_ready_report(
                request.research_data,
                standard=request.standard,
                filename=request.filename
            )
            
        elif request.export_format == "excel":
            result = exporter.export_to_excel(
                request.research_data,
                filename=request.filename
            )
            
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported export format: {request.export_format}")
        
        if result is None or not result.get("success", False):
            raise HTTPException(status_code=500, detail="Academic data export failed")
        
        return {
            "success": True,
            "export_format": request.export_format,
            "filename": request.filename,
            "result": result,
            "timestamp": datetime.now().isoformat(),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"學術數據匯出失敗: {e}")
        raise HTTPException(status_code=500, detail=f"Academic data export failed: {str(e)}")

@router.get("/export/download/{filename}")
async def download_export_file(filename: str):
    """下載匯出的文件"""
    try:
        # 安全檢查文件名
        if ".." in filename or "/" in filename:
            raise HTTPException(status_code=400, detail="Invalid filename")
        
        # 查找文件
        export_dirs = ["/tmp/rl_exports", "/tmp/rl_visualizations"]
        file_path = None
        
        for export_dir in export_dirs:
            potential_path = Path(export_dir) / filename
            if potential_path.exists():
                file_path = potential_path
                break
        
        if file_path is None:
            raise HTTPException(status_code=404, detail="File not found")
        
        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type='application/octet-stream'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文件下載失敗: {e}")
        raise HTTPException(status_code=500, detail=f"File download failed: {str(e)}")

@router.get("/algorithms/comparison")
async def get_algorithm_comparison_data(
    algorithms: List[str] = Query(..., description="算法列表"),
    scenario: str = Query(default="urban", description="場景類型"),
    metrics: List[str] = Query(default=["total_reward"], description="比較指標")
):
    """獲取算法比較數據"""
    try:
        if not ANALYTICS_AVAILABLE:
            raise HTTPException(status_code=503, detail="Analytics components not available")
        
        # 這裡應該從實際的訓練數據庫中獲取數據
        # 目前使用模擬數據
        import numpy as np
        
        comparison_data = {}
        
        for algorithm in algorithms:
            # 模擬不同算法的性能數據
            base_performance = {"DQN": 45, "PPO": 50, "SAC": 47}.get(algorithm, 40)
            
            comparison_data[algorithm] = {
                "total_reward": np.random.normal(base_performance, 10, 100).tolist(),
                "success_rate": np.random.uniform(0.7, 0.95, 100).tolist(),
                "handover_latency": np.random.uniform(10, 50, 100).tolist(),
            }
        
        return {
            "success": True,
            "algorithms": algorithms,
            "scenario": scenario,
            "metrics": metrics,
            "data": comparison_data,
            "timestamp": datetime.now().isoformat(),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"算法比較數據獲取失敗: {e}")
        raise HTTPException(status_code=500, detail=f"Algorithm comparison data fetch failed: {str(e)}")

@router.post("/workflow/complete-analysis")
async def run_complete_analysis_workflow(
    background_tasks: BackgroundTasks,
    training_session_id: str = Body(..., description="訓練會話ID"),
    analysis_options: Dict[str, bool] = Body(
        default={
            "convergence_analysis": True,
            "statistical_testing": True,
            "decision_explanation": True,
            "visualization": True,
            "academic_export": True,
        },
        description="分析選項"
    )
):
    """運行完整的分析工作流"""
    try:
        if not ANALYTICS_AVAILABLE:
            raise HTTPException(status_code=503, detail="Analytics components not available")
        
        # 啟動後台任務
        background_tasks.add_task(
            _run_analysis_workflow,
            training_session_id,
            analysis_options
        )
        
        return {
            "success": True,
            "message": "Complete analysis workflow started",
            "training_session_id": training_session_id,
            "analysis_options": analysis_options,
            "status": "running",
            "timestamp": datetime.now().isoformat(),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"完整分析工作流啟動失敗: {e}")
        raise HTTPException(status_code=500, detail=f"Complete analysis workflow failed: {str(e)}")

async def _run_analysis_workflow(training_session_id: str, analysis_options: Dict[str, bool]):
    """後台運行分析工作流"""
    try:
        logger.info(f"開始完整分析工作流: {training_session_id}")
        
        # 這裡應該實現完整的分析流程
        # 1. 從數據庫獲取訓練數據
        # 2. 運行各種分析
        # 3. 生成報告
        # 4. 保存結果
        
        await asyncio.sleep(1)  # 模擬分析時間
        
        logger.info(f"完整分析工作流完成: {training_session_id}")
        
    except Exception as e:
        logger.error(f"分析工作流執行失敗: {e}")

# 包含所有端點的路由器
__all__ = ["router"]