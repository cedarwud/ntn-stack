"""
動態衛星池API端點
提供階段6生成的優化衛星池數據
"""

from fastapi import APIRouter, HTTPException
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# 動態池數據文件路徑 (容器內路徑)
DYNAMIC_POOL_FILE = Path("/app/data/dynamic_pool_planning_outputs/enhanced_dynamic_pools_output.json")

@router.get("/api/satellite/dynamic-pool")
async def get_dynamic_pool():
    """
    獲取動態衛星池數據
    
    Returns:
        動態池配置，包含優化後的衛星ID列表
    """
    try:
        if not DYNAMIC_POOL_FILE.exists():
            logger.warning(f"動態池文件不存在: {DYNAMIC_POOL_FILE}")
            raise HTTPException(status_code=404, detail="動態池數據尚未生成")
        
        with open(DYNAMIC_POOL_FILE, 'r') as f:
            data = json.load(f)
        
        # 提取動態池數據
        pool_data = data.get('dynamic_satellite_pool', {})
        selection_details = pool_data.get('selection_details', {})
        
        # 解析衛星ID列表
        starlink_satellites = []
        oneweb_satellites = []
        
        # 從selection_details中提取衛星ID (處理數組格式)
        for satellite_info in selection_details:
            satellite_id = satellite_info.get('satellite_id', '')
            constellation = satellite_info.get('constellation', '')
            
            if constellation == 'starlink':
                starlink_satellites.append(satellite_id)
            elif constellation == 'oneweb':
                oneweb_satellites.append(satellite_id)
        
        # 構建正確的動態池數據結構
        formatted_pool_data = {
            "starlink_satellites": starlink_satellites,
            "oneweb_satellites": oneweb_satellites,
            "total_selected": len(starlink_satellites) + len(oneweb_satellites),
            "selection_details": selection_details
        }
        
        logger.info(f"返回動態池數據: Starlink {len(starlink_satellites)}顆, OneWeb {len(oneweb_satellites)}顆")
        
        return {
            "status": "success",
            "dynamic_satellite_pool": formatted_pool_data,
            "metadata": data.get('metadata', {}),
            "performance_metrics": data.get('performance_metrics', {})
        }
        
    except FileNotFoundError:
        logger.error("動態池文件未找到")
        raise HTTPException(status_code=404, detail="動態池數據文件未找到")
    except json.JSONDecodeError as e:
        logger.error(f"解析動態池文件失敗: {e}")
        raise HTTPException(status_code=500, detail="動態池數據格式錯誤")
    except Exception as e:
        logger.error(f"獲取動態池數據失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/satellite/pool-stats")
async def get_pool_statistics():
    """
    獲取動態池統計信息
    
    Returns:
        池的統計數據和覆蓋指標
    """
    try:
        if not DYNAMIC_POOL_FILE.exists():
            return {
                "status": "not_available",
                "message": "動態池尚未生成",
                "stats": None
            }
        
        with open(DYNAMIC_POOL_FILE, 'r') as f:
            data = json.load(f)
        
        pool_data = data.get('dynamic_satellite_pool', {})
        metrics = data.get('performance_metrics', {})
        optimization = data.get('optimization_results', {})
        
        stats = {
            "total_satellites": pool_data.get('total_selected', 0),
            "starlink_count": len(pool_data.get('starlink_satellites', [])),
            "oneweb_count": len(pool_data.get('oneweb_satellites', [])),
            "coverage_score": {
                "starlink": optimization.get('starlink_coverage_score', 0),
                "oneweb": optimization.get('oneweb_coverage_score', 0)
            },
            "processing_time_seconds": metrics.get('total_processing_time_seconds', 0),
            "generation_timestamp": data.get('metadata', {}).get('processing_timestamp', '')
        }
        
        return {
            "status": "success",
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"獲取池統計信息失敗: {e}")
        return {
            "status": "error",
            "message": str(e),
            "stats": None
        }