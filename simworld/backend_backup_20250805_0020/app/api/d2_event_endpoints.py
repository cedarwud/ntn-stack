"""
D2 Event API endpoints for serving enhanced satellite data
"""

from fastapi import APIRouter, HTTPException
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/d2-events", tags=["d2-events"])

# Data directory path
DATA_DIR = Path("/app/data")
if not DATA_DIR.exists():
    # Fallback to local development path
    DATA_DIR = Path(__file__).parent.parent.parent.parent.parent / "data"

@router.get("/data/{constellation}")
async def get_d2_event_data(constellation: str):
    """
    Get enhanced D2 event data for a specific constellation
    
    Args:
        constellation: Name of constellation (starlink or oneweb)
        
    Returns:
        Enhanced satellite data with MRL calculations and D2 events
    """
    if constellation not in ["starlink", "oneweb"]:
        raise HTTPException(status_code=400, detail="Invalid constellation. Must be 'starlink' or 'oneweb'")
    
    try:
        # Try enhanced data first
        enhanced_file = DATA_DIR / f"{constellation}_120min_d2_enhanced.json"
        
        if enhanced_file.exists():
            logger.info(f"Loading enhanced D2 data from: {enhanced_file}")
            with open(enhanced_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        
        # Fallback to regular timeseries data
        timeseries_file = DATA_DIR / f"{constellation}_120min_timeseries.json"
        
        if timeseries_file.exists():
            logger.warning(f"Enhanced data not found, using regular timeseries: {timeseries_file}")
            with open(timeseries_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Add placeholder for missing D2 fields
            data['d2_events'] = []
            data['metadata']['d2_enhancement'] = {
                "status": "not_available",
                "message": "D2 enhancement not yet processed for this data"
            }
            
            return data
        
        raise HTTPException(status_code=404, detail=f"No data found for constellation: {constellation}")
        
    except Exception as e:
        logger.error(f"Error loading D2 event data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_d2_status():
    """Get status of D2 event data availability"""
    status = {
        "available_constellations": [],
        "enhanced_data": {},
        "data_directory": str(DATA_DIR)
    }
    
    for constellation in ["starlink", "oneweb"]:
        enhanced_file = DATA_DIR / f"{constellation}_120min_d2_enhanced.json"
        timeseries_file = DATA_DIR / f"{constellation}_120min_timeseries.json"
        
        if enhanced_file.exists():
            status["available_constellations"].append(constellation)
            status["enhanced_data"][constellation] = {
                "available": True,
                "file_size_mb": enhanced_file.stat().st_size / 1024 / 1024,
                "last_modified": enhanced_file.stat().st_mtime
            }
        elif timeseries_file.exists():
            status["available_constellations"].append(constellation)
            status["enhanced_data"][constellation] = {
                "available": False,
                "timeseries_available": True
            }
    
    return status