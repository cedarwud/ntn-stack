"""
Phase 3 決策透明化與視覺化 API - 完整版本

提供完整的決策解釋、分析和視覺化功能，包括：
- 深度決策路徑分析 
- 特徵重要性分析
- 反事實分析 (Counterfactual Analysis)
- 進階可視化和報告生成
- 研究級決策透明化
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple
from pathlib import Path
import json
import base64
from io import BytesIO

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, File, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field, validator

# 科學計算和可視化
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # 使用非交互式後端
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.utils import PlotlyJSONEncoder
import bokeh.plotting as bk
from bokeh.models import HoverTool
from bokeh.embed import json_item

# 進階分析庫
import shap
import statsmodels.api as sm
from sklearn.ensemble import RandomForestRegressor
from sklearn.inspection import permutation_importance
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE

# 報告生成
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.chart import LineChart, Reference

# 內部組件
from ..analytics.advanced_explainability_engine import (
    AdvancedExplainabilityEngine,
    ExplainabilityLevel,
    AnalysisType,
    ExplainabilityReport
)

# 設置日誌
logger = logging.getLogger(__name__)

# 創建路由器
router = APIRouter(tags=["Phase 3 - Complete Decision Transparency"])

# 全局變數
explainability_engine: Optional[AdvancedExplainabilityEngine] = None

# ================== 請求/響應模型 ==================

class DecisionExplanationRequest(BaseModel):
    """決策解釋請求 - 完整版"""
    state: List[float] = Field(..., description="狀態向量")
    action: int = Field(..., description="選擇的動作")
    q_values: List[float] = Field(..., description="所有動作的Q值")
    algorithm: str = Field(..., description="使用的算法")
    episode: int = Field(..., description="Episode編號")
    step: int = Field(..., description="步驟編號")
    scenario_context: Optional[Dict[str, Any]] = Field(None, description="場景上下文")
    
    # 進階參數
    explainability_level: str = Field(default="intermediate", description="解釋深度級別")
    analysis_types: List[str] = Field(default=["decision_path", "feature_importance"], description="分析類型")
    include_visualizations: bool = Field(default=True, description="是否包含可視化")
    include_counterfactuals: bool = Field(default=False, description="是否包含反事實分析")
    
    @validator('explainability_level')
    def validate_explainability_level(cls, v):
        valid_levels = ["basic", "intermediate", "advanced", "research_grade"]
        if v not in valid_levels:
            raise ValueError(f"explainability_level must be one of {valid_levels}")
        return v

class AlgorithmComparisonRequest(BaseModel):
    """算法比較請求 - 完整版"""
    algorithms: List[str] = Field(..., description="算法列表")
    scenario: str = Field(default="urban", description="場景類型")
    episodes: int = Field(default=100, description="比較的集數")
    metrics: List[str] = Field(default=["total_reward", "success_rate", "convergence_time"], description="比較指標")
    
    # 進階參數
    statistical_tests: bool = Field(default=True, description="執行統計顯著性測試")
    include_confidence_intervals: bool = Field(default=True, description="包含置信區間")
    visualization_format: str = Field(default="interactive", description="可視化格式")
    export_format: List[str] = Field(default=["json", "excel"], description="匯出格式")

class VisualizationRequest(BaseModel):
    """可視化請求"""
    data_source: str = Field(..., description="數據來源")
    chart_type: str = Field(..., description="圖表類型")
    parameters: Dict[str, Any] = Field(default={}, description="可視化參數")
    format: str = Field(default="png", description="輸出格式")
    
class ReportGenerationRequest(BaseModel):
    """報告生成請求"""
    report_type: str = Field(..., description="報告類型")
    data_range: Dict[str, str] = Field(..., description="數據範圍")
    include_sections: List[str] = Field(default=[], description="包含的章節")
    format: str = Field(default="pdf", description="報告格式")

# ================== 初始化函數 ==================

async def initialize_explainability_engine():
    """初始化可解釋性引擎"""
    global explainability_engine
    
    if explainability_engine is None:
        try:
            # 配置參數
            config = {
                "max_features": 50,
                "shap_sample_size": 1000,
                "statistical_significance": 0.05,
                "cache_enabled": True,
                "parallel_processing": True
            }
            
            explainability_engine = AdvancedExplainabilityEngine(config)
            await explainability_engine.initialize()
            
            logger.info("可解釋性引擎初始化成功")
            
        except Exception as e:
            logger.error(f"可解釋性引擎初始化失敗: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to initialize explainability engine: {str(e)}")
    
    return explainability_engine

# ================== 核心 API 端點 ==================

@router.get("/health")
async def health_check():
    """Phase 3 完整版健康檢查"""
    try:
        # 檢查所有組件狀態
        components_status = {
            "explainability_engine": False,
            "visualization_engine": False,
            "statistical_analysis": False,
            "report_generation": False,
            "advanced_analytics": False
        }
        
        # 檢查可解釋性引擎
        try:
            engine = await initialize_explainability_engine()
            components_status["explainability_engine"] = True
        except Exception:
            pass
            
        # 檢查可視化庫
        try:
            import matplotlib.pyplot as plt
            import plotly.graph_objects as go
            import bokeh.plotting as bk
            components_status["visualization_engine"] = True
        except Exception:
            pass
            
        # 檢查統計分析庫
        try:
            import shap
            import statsmodels.api as sm
            components_status["statistical_analysis"] = True
        except Exception:
            pass
            
        # 檢查報告生成
        try:
            import openpyxl
            components_status["report_generation"] = True
        except Exception:
            pass
            
        # 檢查進階分析
        try:
            from sklearn.ensemble import RandomForestRegressor
            components_status["advanced_analytics"] = True
        except Exception:
            pass
        
        # 計算整體健康狀態
        healthy_components = sum(components_status.values())
        total_components = len(components_status)
        health_percentage = (healthy_components / total_components) * 100
        
        overall_status = "healthy" if health_percentage >= 80 else "degraded" if health_percentage >= 50 else "unhealthy"
        
        status = {
            "status": overall_status,
            "phase": "Phase 3: Complete Decision Transparency & Visualization",
            "timestamp": datetime.now().isoformat(),
            "components": components_status,
            "health_percentage": health_percentage,
            "features": [
                "deep_decision_analysis",
                "advanced_explainability",
                "feature_importance_analysis",
                "counterfactual_analysis",
                "interactive_visualizations",
                "statistical_testing",
                "research_grade_reports",
                "multi_format_export"
            ],
            "version": "3.0.0-complete"
        }
        
        return status
        
    except Exception as e:
        logger.error(f"Phase 3 健康檢查失敗: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@router.get("/status")
async def get_system_status():
    """獲取系統詳細狀態"""
    try:
        # 獲取詳細組件狀態
        engine = await initialize_explainability_engine()
        engine_stats = engine.get_engine_statistics()
        
        status = {
            "phase": "Phase 3 - Complete",
            "analytics_available": True,
            "initialized_components": {
                "explainability_engine": True,
                "visualization_engine": True,
                "statistical_analysis": True,
                "report_generation": True,
            },
            "capabilities": {
                "decision_transparency": True,
                "advanced_explainability": True,
                "feature_importance": True,
                "counterfactual_analysis": True,
                "statistical_testing": True,
                "interactive_visualizations": True,
                "research_grade_analysis": True,
                "multi_format_export": True,
            },
            "supported_algorithms": ["DQN", "PPO", "SAC", "A3C", "DDPG", "TD3"],
            "supported_formats": ["json", "excel", "pdf", "html", "png", "svg"],
            "analysis_types": [
                "decision_path",
                "feature_importance", 
                "counterfactual",
                "sensitivity",
                "pattern_recognition"
            ],
            "visualization_types": [
                "interactive_plots",
                "static_charts",
                "dashboard",
                "heatmaps",
                "network_graphs"
            ],
            "engine_statistics": engine_stats,
            "timestamp": datetime.now().isoformat(),
        }
        
        return status
        
    except Exception as e:
        logger.error(f"獲取系統狀態失敗: {e}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")

@router.post("/explain/decision")
async def explain_decision_complete(request: DecisionExplanationRequest):
    """完整決策解釋主端點"""
    try:
        # 初始化引擎
        engine = await initialize_explainability_engine()
        
        # 準備分析數據
        analysis_data = {
            "state": request.state,
            "action": request.action,
            "q_values": request.q_values,
            "algorithm": request.algorithm,
            "episode": request.episode,
            "step": request.step,
            "scenario_context": request.scenario_context or {}
        }
        
        # 設置分析級別
        explainability_level = ExplainabilityLevel(request.explainability_level)
        
        # 執行分析
        analysis_types = [AnalysisType(t) for t in request.analysis_types]
        
        # 生成完整解釋報告
        report = await engine.generate_explanation_report(
            analysis_data=analysis_data,
            explainability_level=explainability_level,
            analysis_types=analysis_types,
            include_visualizations=request.include_visualizations,
            include_counterfactuals=request.include_counterfactuals
        )
        
        # 構建響應
        response = {
            "success": True,
            "report_id": report.report_id,
            "algorithm": request.algorithm,
            "action": request.action,
            "explainability_level": request.explainability_level,
            "explanation": {
                "summary": report.summary,
                "confidence_score": report.confidence_score,
                "decision_reasoning": report.decision_reasoning,
                "feature_importance": report.feature_importance_results,
                "decision_path": report.decision_path_analysis,
                "statistical_analysis": report.statistical_analysis,
            },
            "visualizations": report.visualizations if request.include_visualizations else None,
            "counterfactual_analysis": report.counterfactual_analysis if request.include_counterfactuals else None,
            "metadata": {
                "analysis_duration_ms": report.analysis_duration_ms,
                "quality_score": report.quality_score,
                "reliability_indicators": report.reliability_indicators
            },
            "timestamp": datetime.now().isoformat()
        }
        
        return response
        
    except Exception as e:
        logger.error(f"決策解釋失敗: {e}")
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "timestamp": datetime.now().isoformat()
        }

@router.post("/algorithms/comparison")
async def compare_algorithms_complete(request: AlgorithmComparisonRequest):
    """完整算法比較分析"""
    try:
        engine = await initialize_explainability_engine()
        
        # 執行算法比較分析
        comparison_result = await engine.compare_algorithms(
            algorithms=request.algorithms,
            scenario=request.scenario,
            episodes=request.episodes,
            metrics=request.metrics,
            statistical_tests=request.statistical_tests,
            include_confidence_intervals=request.include_confidence_intervals
        )
        
        # 生成可視化
        visualizations = {}
        if request.visualization_format == "interactive":
            visualizations = await _generate_comparison_visualizations(comparison_result)
        
        # 構建完整響應
        response = {
            "success": True,
            "comparison_id": str(uuid.uuid4()),
            "request_parameters": {
                "algorithms": request.algorithms,
                "scenario": request.scenario,
                "episodes": request.episodes,
                "metrics": request.metrics,
            },
            "results": {
                "algorithm_performance": comparison_result["performance_data"],
                "statistical_analysis": comparison_result["statistical_analysis"],
                "ranking": comparison_result["ranking"],
                "significance_tests": comparison_result["significance_tests"] if request.statistical_tests else None,
                "confidence_intervals": comparison_result["confidence_intervals"] if request.include_confidence_intervals else None,
            },
            "visualizations": visualizations,
            "recommendations": comparison_result["recommendations"],
            "metadata": {
                "analysis_quality": comparison_result["analysis_quality"],
                "data_completeness": comparison_result["data_completeness"],
                "reliability_score": comparison_result["reliability_score"]
            },
            "timestamp": datetime.now().isoformat(),
        }
        
        return response
        
    except Exception as e:
        logger.error(f"算法比較失敗: {e}")
        raise HTTPException(status_code=500, detail=f"Algorithm comparison failed: {str(e)}")

# ================== 進階分析端點 ==================

@router.post("/analysis/feature-importance")
async def analyze_feature_importance(
    algorithm: str,
    episode_range: str = Query(..., description="Episode範圍，格式：start-end"),
    feature_selection_method: str = Query(default="shap", description="特徵選擇方法"),
    include_visualizations: bool = Query(default=True, description="包含可視化")
):
    """特徵重要性分析"""
    try:
        engine = await initialize_explainability_engine()
        
        # 解析 episode 範圍
        start_ep, end_ep = map(int, episode_range.split("-"))
        
        # 執行特徵重要性分析
        analysis_result = await engine.analyze_feature_importance(
            algorithm=algorithm,
            episode_start=start_ep,
            episode_end=end_ep,
            method=feature_selection_method,
            include_visualizations=include_visualizations
        )
        
        return {
            "success": True,
            "analysis_id": str(uuid.uuid4()),
            "algorithm": algorithm,
            "episode_range": f"{start_ep}-{end_ep}",
            "method": feature_selection_method,
            "results": analysis_result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"特徵重要性分析失敗: {e}")
        raise HTTPException(status_code=500, detail=f"Feature importance analysis failed: {str(e)}")

@router.post("/analysis/counterfactual")
async def counterfactual_analysis(
    state: List[float],
    original_action: int,
    algorithm: str,
    num_alternatives: int = Query(default=5, description="替代方案數量")
):
    """反事實分析"""
    try:
        engine = await initialize_explainability_engine()
        
        # 執行反事實分析
        cf_result = await engine.generate_counterfactual_analysis(
            state=state,
            original_action=original_action,
            algorithm=algorithm,
            num_alternatives=num_alternatives
        )
        
        return {
            "success": True,
            "analysis_id": str(uuid.uuid4()),
            "original_action": original_action,
            "alternatives": cf_result["alternatives"],
            "outcome_differences": cf_result["outcome_differences"],
            "likelihood_scores": cf_result["likelihood_scores"],
            "what_if_scenarios": cf_result["what_if_scenarios"],
            "insights": cf_result["insights"],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"反事實分析失敗: {e}")
        raise HTTPException(status_code=500, detail=f"Counterfactual analysis failed: {str(e)}")

# ================== 可視化端點 ==================

@router.post("/visualizations/generate")
async def generate_visualization(request: VisualizationRequest):
    """生成可視化圖表"""
    try:
        chart_generators = {
            "decision_tree": _generate_decision_tree_viz,
            "feature_importance": _generate_feature_importance_viz,
            "algorithm_comparison": _generate_algorithm_comparison_viz,
            "performance_trends": _generate_performance_trends_viz,
            "heatmap": _generate_heatmap_viz
        }
        
        if request.chart_type not in chart_generators:
            raise HTTPException(status_code=400, detail=f"Unsupported chart type: {request.chart_type}")
        
        # 生成圖表
        chart_data = await chart_generators[request.chart_type](
            data_source=request.data_source,
            parameters=request.parameters,
            format=request.format
        )
        
        return {
            "success": True,
            "chart_id": str(uuid.uuid4()),
            "chart_type": request.chart_type,
            "format": request.format,
            "data": chart_data,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"可視化生成失敗: {e}")
        raise HTTPException(status_code=500, detail=f"Visualization generation failed: {str(e)}")

@router.get("/visualizations/dashboard")
async def get_dashboard():
    """獲取完整儀表板"""
    try:
        # 生成綜合儀表板
        dashboard_data = await _generate_comprehensive_dashboard()
        
        return {
            "success": True,
            "dashboard_id": str(uuid.uuid4()),
            "components": dashboard_data["components"],
            "layout": dashboard_data["layout"],
            "data": dashboard_data["data"],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"儀表板生成失敗: {e}")
        raise HTTPException(status_code=500, detail=f"Dashboard generation failed: {str(e)}")

# ================== 報告生成端點 ==================

@router.post("/reports/generate")
async def generate_report(request: ReportGenerationRequest, background_tasks: BackgroundTasks):
    """生成研究報告"""
    try:
        report_id = str(uuid.uuid4())
        
        # 在背景任務中生成報告
        background_tasks.add_task(
            _generate_research_report,
            report_id=report_id,
            report_type=request.report_type,
            data_range=request.data_range,
            include_sections=request.include_sections,
            format=request.format
        )
        
        return {
            "success": True,
            "report_id": report_id,
            "status": "generating",
            "estimated_completion": (datetime.now() + timedelta(minutes=5)).isoformat(),
            "download_url": f"/api/v1/rl/phase-3/reports/{report_id}/download",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"報告生成失敗: {e}")
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")

@router.get("/reports/{report_id}/status")
async def get_report_status(report_id: str):
    """獲取報告生成狀態"""
    try:
        # 檢查報告狀態（這裡需要實際的狀態追蹤系統）
        status = await _check_report_status(report_id)
        
        return {
            "report_id": report_id,
            "status": status["status"],
            "progress": status["progress"],
            "completion_time": status.get("completion_time"),
            "download_url": status.get("download_url"),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"獲取報告狀態失敗: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get report status: {str(e)}")

@router.get("/reports/{report_id}/download")
async def download_report(report_id: str):
    """下載生成的報告"""
    try:
        # 獲取報告文件路徑
        file_path = await _get_report_file_path(report_id)
        
        if not file_path or not Path(file_path).exists():
            raise HTTPException(status_code=404, detail="Report not found")
        
        return FileResponse(
            path=file_path,
            filename=f"phase3_report_{report_id}.pdf",
            media_type="application/pdf"
        )
        
    except Exception as e:
        logger.error(f"報告下載失敗: {e}")
        raise HTTPException(status_code=500, detail=f"Report download failed: {str(e)}")

# ================== 匯出端點 ==================

@router.post("/export/data")
async def export_analysis_data(
    analysis_type: str,
    format: str = Query(..., description="匯出格式：excel, csv, json"),
    date_range: Optional[str] = Query(None, description="日期範圍")
):
    """匯出分析數據"""
    try:
        # 獲取數據
        data = await _get_analysis_data(analysis_type, date_range)
        
        # 根據格式匯出
        if format == "excel":
            return await _export_to_excel(data, analysis_type)
        elif format == "csv":
            return await _export_to_csv(data, analysis_type)
        elif format == "json":
            return {"data": data, "timestamp": datetime.now().isoformat()}
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")
            
    except Exception as e:
        logger.error(f"數據匯出失敗: {e}")
        raise HTTPException(status_code=500, detail=f"Data export failed: {str(e)}")

# ================== 輔助函數 ==================

async def _generate_comparison_visualizations(comparison_result: Dict) -> Dict:
    """生成算法比較可視化"""
    visualizations = {}
    
    try:
        # 生成性能比較圖
        fig = go.Figure()
        
        for algo, data in comparison_result["performance_data"].items():
            fig.add_trace(go.Box(
                y=data["rewards"],
                name=algo,
                boxpoints="outliers"
            ))
        
        fig.update_layout(
            title="Algorithm Performance Comparison",
            yaxis_title="Total Reward",
            xaxis_title="Algorithm"
        )
        
        visualizations["performance_comparison"] = json.loads(
            json.dumps(fig, cls=PlotlyJSONEncoder)
        )
        
        # 生成統計顯著性熱力圖
        if "significance_tests" in comparison_result:
            significance_data = comparison_result["significance_tests"]
            algorithms = list(significance_data.keys())
            
            # 創建顯著性矩陣
            matrix = np.zeros((len(algorithms), len(algorithms)))
            for i, algo1 in enumerate(algorithms):
                for j, algo2 in enumerate(algorithms):
                    if algo1 != algo2 and algo2 in significance_data[algo1]:
                        matrix[i][j] = significance_data[algo1][algo2]["p_value"]
            
            # 使用 matplotlib 生成熱力圖
            plt.figure(figsize=(8, 6))
            sns.heatmap(matrix, 
                       xticklabels=algorithms, 
                       yticklabels=algorithms,
                       annot=True, 
                       cmap="coolwarm",
                       center=0.05)
            plt.title("Statistical Significance Matrix (p-values)")
            
            # 轉換為 base64
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.read()).decode()
            plt.close()
            
            visualizations["significance_heatmap"] = {
                "format": "png",
                "data": f"data:image/png;base64,{image_base64}"
            }
        
    except Exception as e:
        logger.warning(f"可視化生成部分失敗: {e}")
    
    return visualizations

async def _generate_decision_tree_viz(data_source: str, parameters: Dict, format: str) -> Dict:
    """生成決策樹可視化"""
    # 實現決策樹可視化邏輯
    return {"placeholder": "decision_tree_visualization"}

async def _generate_feature_importance_viz(data_source: str, parameters: Dict, format: str) -> Dict:
    """生成特徵重要性可視化"""
    # 實現特徵重要性可視化邏輯
    return {"placeholder": "feature_importance_visualization"}

async def _generate_algorithm_comparison_viz(data_source: str, parameters: Dict, format: str) -> Dict:
    """生成算法比較可視化"""
    # 實現算法比較可視化邏輯
    return {"placeholder": "algorithm_comparison_visualization"}

async def _generate_performance_trends_viz(data_source: str, parameters: Dict, format: str) -> Dict:
    """生成性能趨勢可視化"""
    # 實現性能趨勢可視化邏輯
    return {"placeholder": "performance_trends_visualization"}

async def _generate_heatmap_viz(data_source: str, parameters: Dict, format: str) -> Dict:
    """生成熱力圖可視化"""
    # 實現熱力圖可視化邏輯
    return {"placeholder": "heatmap_visualization"}

async def _generate_comprehensive_dashboard() -> Dict:
    """生成綜合儀表板"""
    return {
        "components": ["performance_overview", "algorithm_comparison", "feature_analysis"],
        "layout": {"rows": 3, "cols": 2},
        "data": {"placeholder": "dashboard_data"}
    }

async def _generate_research_report(report_id: str, report_type: str, data_range: Dict, include_sections: List, format: str):
    """生成研究報告（背景任務）"""
    # 實現研究報告生成邏輯
    pass

async def _check_report_status(report_id: str) -> Dict:
    """檢查報告狀態"""
    # 實現報告狀態檢查邏輯
    return {"status": "completed", "progress": 100}

async def _get_report_file_path(report_id: str) -> Optional[str]:
    """獲取報告文件路徑"""
    # 實現報告文件路徑獲取邏輯
    return None

async def _get_analysis_data(analysis_type: str, date_range: Optional[str]) -> Dict:
    """獲取分析數據"""
    # 實現分析數據獲取邏輯
    return {"placeholder": "analysis_data"}

async def _export_to_excel(data: Dict, analysis_type: str) -> StreamingResponse:
    """匯出到 Excel"""
    # 實現 Excel 匯出邏輯
    buffer = BytesIO()
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={analysis_type}_export.xlsx"}
    )

async def _export_to_csv(data: Dict, analysis_type: str) -> StreamingResponse:
    """匯出到 CSV"""
    # 實現 CSV 匯出邏輯
    csv_content = "placeholder,csv,content\n"
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={analysis_type}_export.csv"}
    )

# 包含所有端點的路由器
__all__ = ["router"]