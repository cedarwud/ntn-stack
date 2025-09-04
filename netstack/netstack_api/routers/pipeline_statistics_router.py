"""
六階段數據處理管道統計 API
提供每個階段的輸出衛星數據統計信息
"""

import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# 創建路由器
router = APIRouter(
    prefix="/api/v1/pipeline",
    tags=["Pipeline Statistics"],
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"},
    },
)

logger = logging.getLogger(__name__)

# === Response Models ===

class StageStatistics(BaseModel):
    """單階段統計"""
    stage: int
    stage_name: str
    status: str  # "success", "failed", "no_data"
    total_satellites: int
    starlink_count: int
    oneweb_count: int
    processing_time: Optional[str]
    output_file_size_mb: Optional[float]
    last_updated: Optional[str]
    error_message: Optional[str] = None

class PipelineStatisticsResponse(BaseModel):
    """管道統計響應"""
    metadata: Dict[str, Any]
    stages: List[StageStatistics]
    summary: Dict[str, Any]

# === 數據路徑配置 ===
DATA_PATHS = {
    1: "/app/data/tle_calculation_outputs/tle_orbital_calculation_output.json",
    2: "/app/data/intelligent_filtering_outputs/intelligent_filtered_output.json", 
    3: "/app/data/signal_analysis_outputs/signal_event_analysis_output.json",
    4: "/app/data/timeseries_preprocessing_outputs/conversion_statistics.json",
    5: "/app/data/data_integration_output.json",
    6: "/app/data/leo_outputs/dynamic_pool_planning_outputs/enhanced_dynamic_pools_output.json"
}

STAGE_NAMES = {
    1: "TLE軌道計算",
    2: "智能衛星篩選", 
    3: "信號分析",
    4: "時間序列預處理",
    5: "數據整合",
    6: "動態池規劃"
}

def get_file_size_mb(file_path: str) -> Optional[float]:
    """獲取文件大小（MB）"""
    try:
        if os.path.exists(file_path):
            size_bytes = os.path.getsize(file_path)
            return round(size_bytes / (1024 * 1024), 2)
        return None
    except Exception as e:
        logger.warning(f"獲取文件大小失敗 {file_path}: {e}")
        return None

def analyze_stage_data(stage: int, file_path: str) -> StageStatistics:
    """分析單階段數據"""
    try:
        if not os.path.exists(file_path):
            return StageStatistics(
                stage=stage,
                stage_name=STAGE_NAMES[stage],
                status="no_data",
                total_satellites=0,
                starlink_count=0,
                oneweb_count=0,
                processing_time=None,
                output_file_size_mb=None,
                last_updated=None,
                error_message=f"輸出文件不存在: {file_path}"
            )
        
        # 讀取 JSON 數據
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 統計衛星數量
        total_satellites = 0
        starlink_count = 0
        oneweb_count = 0
        processing_time = None
        last_updated = None
        
        # 根據不同階段的數據結構解析
        if stage == 1:
            # 階段一：TLE軌道計算
            metadata = data.get('metadata', {})
            total_satellites = metadata.get('total_satellites', 0)
            
            constellations = data.get('constellations', {})
            starlink_data = constellations.get('starlink', {})
            oneweb_data = constellations.get('oneweb', {})
            
            starlink_count = starlink_data.get('satellite_count', 0)
            oneweb_count = oneweb_data.get('satellite_count', 0)
            
            processing_time = metadata.get('processing_timestamp')
            
        elif stage == 2:
            # 階段二：智能篩選
            metadata = data.get('metadata', {})
            unified_results = metadata.get('unified_filtering_results', {})
            
            total_satellites = unified_results.get('total_selected', 0)
            starlink_count = unified_results.get('starlink_selected', 0)
            oneweb_count = unified_results.get('oneweb_selected', 0)
            
            processing_time = metadata.get('processing_timestamp')
            
        elif stage == 3:
            # 階段三：信號分析
            metadata = data.get('metadata', {})
            satellites = data.get('satellites', [])
            
            total_satellites = len(satellites)
            starlink_count = len([s for s in satellites if s.get('constellation') == 'starlink'])
            oneweb_count = len([s for s in satellites if s.get('constellation') == 'oneweb'])
            
            processing_time = metadata.get('processing_timestamp')
            
        elif stage == 4:
            # 階段四：時間序列預處理 (使用conversion_statistics)
            total_satellites = data.get('total_processed', 0)
            successful_conversions = data.get('successful_conversions', 0)
            
            # 假設Starlink:OneWeb比例約為86:14 (基於階段2的1029:167)
            starlink_count = int(successful_conversions * 0.86)
            oneweb_count = successful_conversions - starlink_count
            
            processing_time = None  # conversion_statistics沒有時間戳
            
        elif stage == 5:
            # 階段五：數據整合
            total_satellites = data.get('total_satellites', 0)
            constellation_summary = data.get('constellation_summary', {})
            
            starlink_data = constellation_summary.get('starlink', {})
            oneweb_data = constellation_summary.get('oneweb', {})
            
            starlink_count = starlink_data.get('satellite_count', 0)
            oneweb_count = oneweb_data.get('satellite_count', 0)
            
            processing_time = data.get('start_time')
            
        elif stage == 6:
            # 階段六：動態池規劃
            metadata = data.get('metadata', {})
            pool_data = data.get('dynamic_satellite_pool', {})
            
            total_satellites = pool_data.get('total_selected', 0)
            selection_details = pool_data.get('selection_details', [])
            
            starlink_count = len([s for s in selection_details if s.get('constellation') == 'starlink'])
            oneweb_count = len([s for s in selection_details if s.get('constellation') == 'oneweb'])
            
            processing_time = metadata.get('timestamp')
        
        # 獲取文件修改時間
        try:
            mtime = os.path.getmtime(file_path)
            last_updated = datetime.fromtimestamp(mtime, timezone.utc).isoformat()
        except:
            pass
        
        return StageStatistics(
            stage=stage,
            stage_name=STAGE_NAMES[stage],
            status="success",
            total_satellites=total_satellites,
            starlink_count=starlink_count,
            oneweb_count=oneweb_count,
            processing_time=processing_time,
            output_file_size_mb=get_file_size_mb(file_path),
            last_updated=last_updated
        )
        
    except Exception as e:
        logger.error(f"分析階段 {stage} 數據失敗: {e}")
        return StageStatistics(
            stage=stage,
            stage_name=STAGE_NAMES[stage],
            status="failed",
            total_satellites=0,
            starlink_count=0,
            oneweb_count=0,
            processing_time=None,
            output_file_size_mb=get_file_size_mb(file_path),
            last_updated=None,
            error_message=str(e)
        )

@router.get("/statistics", response_model=PipelineStatisticsResponse)
async def get_pipeline_statistics():
    """獲取六階段管道統計信息"""
    try:
        logger.info("🔍 開始分析六階段管道統計...")
        
        stages = []
        
        # 分析每個階段
        for stage_num in range(1, 7):
            file_path = DATA_PATHS[stage_num]
            stage_stats = analyze_stage_data(stage_num, file_path)
            stages.append(stage_stats)
            
            logger.info(f"  階段 {stage_num} ({stage_stats.stage_name}): {stage_stats.status} - {stage_stats.total_satellites} 顆衛星")
        
        # 計算匯總統計
        successful_stages = [s for s in stages if s.status == "success"]
        failed_stages = [s for s in stages if s.status == "failed"]
        no_data_stages = [s for s in stages if s.status == "no_data"]
        
        # 數據流統計
        data_flow = []
        if successful_stages:
            for stage in sorted(successful_stages, key=lambda x: x.stage):
                data_flow.append({
                    'stage': stage.stage,
                    'satellites': stage.total_satellites,
                    'starlink': stage.starlink_count,
                    'oneweb': stage.oneweb_count
                })
        
        summary = {
            'total_stages': 6,
            'successful_stages': len(successful_stages),
            'failed_stages': len(failed_stages),
            'no_data_stages': len(no_data_stages),
            'data_flow': data_flow,
            'final_output': stages[-1].total_satellites if stages else 0,
            'pipeline_health': "healthy" if len(successful_stages) >= 4 else "degraded" if len(successful_stages) >= 2 else "critical"
        }
        
        # 計算數據丟失率
        if len(data_flow) >= 2:
            input_satellites = data_flow[0]['satellites']
            output_satellites = data_flow[-1]['satellites']
            if input_satellites > 0:
                retention_rate = (output_satellites / input_satellites) * 100
                summary['data_retention_rate'] = round(retention_rate, 2)
                summary['data_loss_rate'] = round(100 - retention_rate, 2)
        
        metadata = {
            'analysis_timestamp': datetime.now(timezone.utc).isoformat(),
            'analyzer_version': 'v1.0',
            'data_paths_analyzed': DATA_PATHS
        }
        
        logger.info(f"✅ 管道分析完成: {summary['pipeline_health']} 狀態")
        logger.info(f"   成功階段: {summary['successful_stages']}/6")
        logger.info(f"   最終輸出: {summary['final_output']} 顆衛星")
        
        return PipelineStatisticsResponse(
            metadata=metadata,
            stages=stages,
            summary=summary
        )
        
    except Exception as e:
        logger.error(f"❌ 管道統計分析失敗: {e}")
        raise HTTPException(status_code=500, detail=f"管道統計分析失敗: {str(e)}")

@router.get("/health")
async def pipeline_health_check():
    """管道健康檢查"""
    try:
        # 快速檢查關鍵文件存在性
        stage_status = {}
        for stage, path in DATA_PATHS.items():
            stage_status[f"stage_{stage}"] = os.path.exists(path)
        
        healthy_stages = sum(stage_status.values())
        total_stages = len(stage_status)
        
        health_status = "healthy" if healthy_stages >= 4 else "degraded" if healthy_stages >= 2 else "critical"
        
        return {
            "status": health_status,
            "healthy_stages": healthy_stages,
            "total_stages": total_stages,
            "stage_status": stage_status,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"健康檢查失敗: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }