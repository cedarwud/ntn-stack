"""
衛星星座配置測試 API 路由
提供星座配置創建、性能測試、結果分析等 REST API 端點
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import logging

from ..services.constellation_test_service import (
    constellation_test_service,
    ConstellationType,
    ConstellationConfig,
    HandoverTestResult,
    ConstellationPerformanceMetrics
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/constellation-test", tags=["constellation_test"])

# Request/Response 模型
class ConstellationConfigRequest(BaseModel):
    """星座配置請求"""
    constellation_type: str = Field(..., description="星座類型")
    satellite_count: int = Field(..., ge=1, description="衛星數量")
    orbital_params: Dict[str, float] = Field(..., description="軌道參數")
    coverage_requirements: Dict[str, float] = Field(..., description="覆蓋需求")

class HandoverTestRequest(BaseModel):
    """換手測試請求"""
    constellation_id: str = Field(..., description="星座配置ID")
    test_duration_hours: float = Field(24.0, ge=0.1, le=168.0, description="測試時長(小時)")
    ue_positions: Optional[List[List[float]]] = Field(None, description="UE位置列表 [[lat, lon], ...]")
    mobility_pattern: str = Field("stationary", description="移動模式")

class ConstellationComparisonRequest(BaseModel):
    """星座比較請求"""
    constellation_ids: List[str] = Field(..., min_items=2, description="要比較的星座ID列表")

class ConstellationConfigResponse(BaseModel):
    """星座配置響應"""
    constellation_id: str
    message: str
    config_summary: Dict[str, Any]

class HandoverTestResponse(BaseModel):
    """換手測試響應"""
    test_id: str
    constellation_id: str
    message: str
    estimated_completion_time: str

class TestResultResponse(BaseModel):
    """測試結果響應"""
    test_results: List[Dict[str, Any]]
    summary_statistics: Dict[str, Any]

class ConstellationComparisonResponse(BaseModel):
    """星座比較響應"""
    comparison_result: Dict[str, Any]
    performance_ranking: List[Dict[str, Any]]
    recommendations: List[str]

class ConstellationStatusResponse(BaseModel):
    """星座狀態響應"""
    constellation_status: Dict[str, Any]
    test_history: List[Dict[str, Any]]

@router.post("/create-configuration", response_model=ConstellationConfigResponse)
async def create_constellation_configuration(request: ConstellationConfigRequest):
    """
    創建衛星星座配置
    
    支持的星座類型:
    - leo_dense: 低軌高密度
    - leo_sparse: 低軌稀疏
    - meo_circular: 中軌圓形
    - hybrid_leo_meo: 混合軌道
    - walker_delta: Walker Delta星座
    - polar_coverage: 極地覆蓋
    """
    try:
        # 驗證星座類型
        try:
            constellation_type = ConstellationType(request.constellation_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"不支援的星座類型: {request.constellation_type}"
            )
        
        # 驗證軌道參數
        required_params = ["altitude", "inclination"]
        for param in required_params:
            if param not in request.orbital_params:
                raise HTTPException(
                    status_code=400,
                    detail=f"缺少必要的軌道參數: {param}"
                )
        
        # 創建星座配置
        constellation_id = await constellation_test_service.create_constellation_config(
            constellation_type=constellation_type,
            satellite_count=request.satellite_count,
            orbital_params=request.orbital_params,
            coverage_requirements=request.coverage_requirements
        )
        
        # 獲取配置摘要
        status = await constellation_test_service.get_constellation_status(constellation_id)
        
        logger.info(f"成功創建星座配置: {constellation_id}")
        
        return ConstellationConfigResponse(
            constellation_id=constellation_id,
            message="星座配置創建成功",
            config_summary={
                "constellation_type": request.constellation_type,
                "satellite_count": request.satellite_count,
                "altitude": request.orbital_params["altitude"],
                "inclination": request.orbital_params["inclination"],
                "created_at": status["config"]["created_at"]
            }
        )
        
    except Exception as e:
        logger.error(f"創建星座配置失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"創建星座配置失敗: {str(e)}")

@router.post("/run-handover-test", response_model=HandoverTestResponse)
async def run_handover_performance_test(
    request: HandoverTestRequest,
    background_tasks: BackgroundTasks
):
    """
    運行換手性能測試
    
    測試將在背景執行，可通過 test_id 查詢結果
    """
    try:
        # 驗證星座配置是否存在
        try:
            await constellation_test_service.get_constellation_status(request.constellation_id)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        
        # 轉換UE位置格式
        ue_positions = None
        if request.ue_positions:
            ue_positions = [(pos[0], pos[1]) for pos in request.ue_positions if len(pos) >= 2]
        
        # 在背景運行測試
        background_tasks.add_task(
            constellation_test_service.run_handover_performance_test,
            constellation_id=request.constellation_id,
            test_duration_hours=request.test_duration_hours,
            ue_positions=ue_positions,
            mobility_pattern=request.mobility_pattern
        )
        
        # 生成測試ID（預估）
        test_id = f"test_{request.constellation_id}_{int(datetime.now().timestamp())}"
        
        # 估算完成時間
        estimated_minutes = max(1, int(request.test_duration_hours * 0.1))  # 實際時間的10%
        completion_time = datetime.now().replace(microsecond=0) + \
                         datetime.timedelta(minutes=estimated_minutes)
        
        logger.info(f"開始運行換手測試: {test_id}, 星座: {request.constellation_id}")
        
        return HandoverTestResponse(
            test_id=test_id,
            constellation_id=request.constellation_id,
            message="換手性能測試已開始執行",
            estimated_completion_time=completion_time.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"啟動換手測試失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"啟動換手測試失敗: {str(e)}")

@router.get("/test-results/{constellation_id}", response_model=TestResultResponse)
async def get_test_results(constellation_id: str):
    """
    獲取指定星座的所有測試結果
    """
    try:
        # 驗證星座配置是否存在
        status = await constellation_test_service.get_constellation_status(constellation_id)
        
        if "latest_test_result" not in status or status["latest_test_result"] is None:
            return TestResultResponse(
                test_results=[],
                summary_statistics={
                    "total_tests": 0,
                    "message": "尚無測試結果"
                }
            )
        
        # 獲取所有測試結果
        test_results = constellation_test_service.test_results.get(constellation_id, [])
        
        # 計算摘要統計
        if test_results:
            total_handovers = sum(result.total_handovers for result in test_results)
            total_successful = sum(result.successful_handovers for result in test_results)
            avg_latency = sum(result.average_latency for result in test_results) / len(test_results)
            avg_success_rate = (total_successful / max(1, total_handovers)) * 100
            
            summary_stats = {
                "total_tests": len(test_results),
                "total_handovers": total_handovers,
                "overall_success_rate": round(avg_success_rate, 2),
                "average_latency": round(avg_latency, 2),
                "latest_test_time": test_results[-1].test_timestamp.isoformat(),
                "best_performance_test": max(
                    test_results, 
                    key=lambda x: x.successful_handovers / max(1, x.total_handovers)
                ).test_id
            }
        else:
            summary_stats = {"total_tests": 0, "message": "無測試結果"}
        
        logger.info(f"獲取測試結果: {constellation_id}, 共 {len(test_results)} 個測試")
        
        return TestResultResponse(
            test_results=[
                {
                    "test_id": result.test_id,
                    "test_timestamp": result.test_timestamp.isoformat(),
                    "total_handovers": result.total_handovers,
                    "successful_handovers": result.successful_handovers,
                    "success_rate": round((result.successful_handovers / max(1, result.total_handovers)) * 100, 2),
                    "average_latency": round(result.average_latency, 2),
                    "coverage_percentage": round(result.coverage_percentage, 2),
                    "packet_loss_rate": round(result.packet_loss_rate, 2)
                }
                for result in test_results
            ],
            summary_statistics=summary_stats
        )
        
    except Exception as e:
        logger.error(f"獲取測試結果失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"獲取測試結果失敗: {str(e)}")

@router.post("/compare-constellations", response_model=ConstellationComparisonResponse)
async def compare_constellation_performance(request: ConstellationComparisonRequest):
    """
    比較多個星座的性能
    
    提供詳細的性能對比分析和優化建議
    """
    try:
        # 驗證所有星座配置是否存在
        for constellation_id in request.constellation_ids:
            try:
                await constellation_test_service.get_constellation_status(constellation_id)
            except ValueError:
                raise HTTPException(
                    status_code=404,
                    detail=f"星座配置不存在: {constellation_id}"
                )
        
        # 執行性能比較
        comparison_result = await constellation_test_service.compare_constellation_performance(
            request.constellation_ids
        )
        
        logger.info(f"完成星座性能比較, 比較對象: {request.constellation_ids}")
        
        return ConstellationComparisonResponse(
            comparison_result=comparison_result,
            performance_ranking=comparison_result["performance_ranking"],
            recommendations=comparison_result["recommendations"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"星座性能比較失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"星座性能比較失敗: {str(e)}")

@router.get("/constellation-status/{constellation_id}", response_model=ConstellationStatusResponse)
async def get_constellation_status(constellation_id: str):
    """
    獲取指定星座的詳細狀態信息
    """
    try:
        status = await constellation_test_service.get_constellation_status(constellation_id)
        
        # 獲取測試歷史
        test_results = constellation_test_service.test_results.get(constellation_id, [])
        test_history = [
            {
                "test_id": result.test_id,
                "test_timestamp": result.test_timestamp.isoformat(),
                "success_rate": round((result.successful_handovers / max(1, result.total_handovers)) * 100, 2),
                "average_latency": round(result.average_latency, 2),
                "total_handovers": result.total_handovers
            }
            for result in test_results[-10:]  # 最近10次測試
        ]
        
        logger.info(f"獲取星座狀態: {constellation_id}")
        
        return ConstellationStatusResponse(
            constellation_status=status,
            test_history=test_history
        )
        
    except Exception as e:
        logger.error(f"獲取星座狀態失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"獲取星座狀態失敗: {str(e)}")

@router.get("/constellation-summaries")
async def get_all_constellation_summaries():
    """
    獲取所有星座的摘要信息
    """
    try:
        summaries = await constellation_test_service.get_all_constellation_summaries()
        
        logger.info(f"獲取星座摘要, 共 {len(summaries)} 個星座")
        
        return {
            "constellations": summaries,
            "total_count": len(summaries),
            "active_count": len([s for s in summaries if s["status"] == "active"]),
            "top_performer": summaries[0] if summaries else None
        }
        
    except Exception as e:
        logger.error(f"獲取星座摘要失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"獲取星座摘要失敗: {str(e)}")

@router.get("/predefined-constellations")
async def get_predefined_constellations():
    """
    獲取預定義的星座配置信息
    """
    try:
        summaries = await constellation_test_service.get_all_constellation_summaries()
        
        # 篩選預定義星座
        predefined = [
            s for s in summaries 
            if s["constellation_id"] in ["starlink_like", "oneweb_like", "walker_delta", "meo_hybrid"]
        ]
        
        constellation_types = {
            "leo_dense": {
                "name": "低軌高密度星座",
                "description": "適合高頻率換手場景，低延遲",
                "example": "Starlink"
            },
            "leo_sparse": {
                "name": "低軌稀疏星座", 
                "description": "平衡性能與成本，適中延遲",
                "example": "OneWeb"
            },
            "walker_delta": {
                "name": "Walker Delta星座",
                "description": "均勻覆蓋，規則軌道配置",
                "example": "GlobalStar"
            },
            "hybrid_leo_meo": {
                "name": "混合軌道星座",
                "description": "結合LEO和MEO優勢",
                "example": "Custom Hybrid"
            }
        }
        
        return {
            "predefined_constellations": predefined,
            "constellation_types": constellation_types,
            "recommendation": "建議先測試預定義配置，再根據需求自定義"
        }
        
    except Exception as e:
        logger.error(f"獲取預定義星座失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"獲取預定義星座失敗: {str(e)}")

@router.get("/export-results/{constellation_id}")
async def export_test_results(constellation_id: str, format: str = "json"):
    """
    導出指定星座的測試結果
    """
    try:
        export_data = await constellation_test_service.export_test_results(
            constellation_id, format
        )
        
        logger.info(f"導出測試結果: {constellation_id}, 格式: {format}")
        
        return {
            "constellation_id": constellation_id,
            "export_format": format,
            "export_data": export_data,
            "export_timestamp": datetime.now().isoformat()
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"導出測試結果失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"導出測試結果失敗: {str(e)}")

@router.delete("/constellation/{constellation_id}")
async def delete_constellation_configuration(constellation_id: str):
    """
    刪除星座配置及相關測試結果
    """
    try:
        # 檢查星座是否存在
        if constellation_id not in constellation_test_service.constellation_configs:
            raise HTTPException(status_code=404, detail=f"星座配置不存在: {constellation_id}")
        
        # 檢查是否為預定義星座
        predefined_ids = ["starlink_like", "oneweb_like", "walker_delta", "meo_hybrid"]
        if constellation_id in predefined_ids:
            raise HTTPException(status_code=400, detail="無法刪除預定義星座配置")
        
        # 刪除配置和相關數據
        del constellation_test_service.constellation_configs[constellation_id]
        
        if constellation_id in constellation_test_service.test_results:
            del constellation_test_service.test_results[constellation_id]
        
        if constellation_id in constellation_test_service.performance_metrics:
            del constellation_test_service.performance_metrics[constellation_id]
        
        logger.info(f"刪除星座配置: {constellation_id}")
        
        return {
            "message": f"星座配置 {constellation_id} 已成功刪除",
            "deleted_constellation_id": constellation_id,
            "deletion_timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"刪除星座配置失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"刪除星座配置失敗: {str(e)}")

@router.get("/health")
async def health_check():
    """
    服務健康檢查
    """
    try:
        constellation_count = len(constellation_test_service.constellation_configs)
        total_tests = sum(
            len(results) for results in constellation_test_service.test_results.values()
        )
        
        return {
            "status": "healthy",
            "service": "ConstellationTestService",
            "timestamp": datetime.now().isoformat(),
            "statistics": {
                "total_constellations": constellation_count,
                "total_tests_completed": total_tests,
                "service_uptime": "running"
            }
        }
        
    except Exception as e:
        logger.error(f"健康檢查失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"服務健康檢查失敗: {str(e)}")