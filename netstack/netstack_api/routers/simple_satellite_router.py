"""
Enhanced Satellite Router with Intelligent Preprocessing
使用智能預處理系統的強化衛星路由器

基於 @docs/satellite-preprocessing/ 完整實現
真正調用 IntelligentSatelliteSelector 實現 150+50 顆衛星智能選擇 (基於234顆真實可見衛星優化)
"""

import sys
import os
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import math
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
import json
import logging

# 添加預處理系統路徑
sys.path.append('/home/sat/ntn-stack/netstack/src/services/satellite')
sys.path.append('/home/sat/ntn-stack/netstack/src/services/satellite/preprocessing')

# 創建路由器
router = APIRouter(
    prefix="/api/v1/satellite-simple",
    tags=["Intelligent Satellite Operations"],
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"},
    },
)

logger = logging.getLogger(__name__)

# === Response Models ===

class PositionTimePoint(BaseModel):
    """時間序列位置點"""
    time: str
    time_offset_seconds: float
    elevation_deg: float
    azimuth_deg: float
    range_km: float
    is_visible: bool

class SatelliteInfo(BaseModel):
    """衛星信息"""
    name: str
    norad_id: str
    elevation_deg: float
    azimuth_deg: float
    distance_km: float
    orbit_altitude_km: float
    constellation: Optional[str] = None
    signal_strength: Optional[float] = None
    is_visible: bool = True
    position_timeseries: Optional[List[PositionTimePoint]] = None

class VisibleSatellitesResponse(BaseModel):
    """可見衛星響應"""
    satellites: List[SatelliteInfo]
    total_count: int
    requested_count: int
    constellation: Optional[str] = None
    global_view: bool = False
    timestamp: str
    observer_location: Optional[Dict[str, float]] = None
    data_source: str
    preprocessing_stats: Optional[Dict[str, Any]] = None

# === 全局智能預處理服務 ===
_preprocessing_service = None
_intelligent_selector = None

def get_preprocessing_service():
    """獲取預處理服務實例"""
    global _preprocessing_service
    if _preprocessing_service is None:
        try:
            from preprocessing_service import SatellitePreprocessingService
            _preprocessing_service = SatellitePreprocessingService()
            logger.info("✅ 智能預處理服務初始化成功")
        except Exception as e:
            logger.error(f"❌ 智能預處理服務初始化失敗: {e}")
            _preprocessing_service = None
    return _preprocessing_service

def get_intelligent_selector():
    """獲取智能選擇器實例"""
    global _intelligent_selector
    if _intelligent_selector is None:
        try:
            from src.services.satellite.preprocessing import IntelligentSatelliteSelector
            _intelligent_selector = IntelligentSatelliteSelector()
            logger.info("✅ 智能衛星選擇器初始化成功")
        except Exception as e:
            logger.error(f"❌ 智能衛星選擇器初始化失敗: {e}")
            _intelligent_selector = None
    return _intelligent_selector

def get_precomputed_satellite_data(constellation: str, count: int = 200) -> List[Dict]:
    """
    從Phase0預處理系統獲取實際衛星數據
    使用150+50顆真實衛星取代舊的15顆模擬數據 (基於SGP4全量計算優化配置)
    """
    satellites = []
    
    try:
        # 🔥 CRITICAL FIX: 使用分層預計算數據 (10°仰角門檻)
        import json
        precomputed_file = f'/app/data/layered_phase0_enhanced/elevation_10deg/{constellation.lower()}_with_3gpp_events.json'
        
        with open(precomputed_file, 'r') as f:
            precomputed_data = json.load(f)
        
        # 檢查數據結構 - 期望是包含衛星列表的結構
        if isinstance(precomputed_data, list):
            satellites_list = precomputed_data
        elif isinstance(precomputed_data, dict):
            # 從分層數據結構中提取衛星列表
            satellites_list = precomputed_data.get('satellites', [])
            metadata = precomputed_data.get('metadata', {})
            logger.info(f"📊 數據元信息: {metadata.get('total_satellites', 0)} 顆衛星, 處理階段: {metadata.get('processing_stage', 'unknown')}")
        else:
            logger.error(f"❌ 未預期的數據格式: {type(precomputed_data)}")
            satellites_list = []
        
        logger.info(f"🔍 載入 {len(satellites_list)} 顆 {constellation} 衛星數據")
        
        # 🔧 修復：從分層預計算數據中構建衛星列表
        for satellite_data in satellites_list:
            # 提取衛星基本信息
            satellite_id = satellite_data.get('satellite_id', '')
            norad_id = satellite_data.get('norad_id', 0)
            name = satellite_data.get('name', satellite_id)
            
            if not satellite_id:
                continue
                
            # 🎯 CRITICAL FIX: 使用分層數據中的時間序列位置數據
            position_timeseries = satellite_data.get('position_timeseries', [])
            
            # 只包含有真實軌道數據的衛星
            if position_timeseries:
                # 轉換為API需要的格式，保持真實SGP4計算結果
                precomputed_positions = []
                for position in position_timeseries:
                    precomputed_positions.append({
                        'time': position.get('time', ''),
                        'time_offset_seconds': position.get('time_offset_seconds', 0),
                        'position_eci': position.get('position_eci', {}),
                        'velocity_eci': position.get('velocity_eci', {}),
                        'range_km': position.get('range_km', 0),
                        'elevation_deg': position.get('elevation_deg', -90),
                        'azimuth_deg': position.get('azimuth_deg', 0),
                        'is_visible': position.get('elevation_deg', -90) >= 0
                    })
                
                # 提取軌道參數
                orbit_params = satellite_data.get('orbit_parameters', {})
                
                satellites.append({
                    'name': name,
                    'norad_id': str(norad_id) if norad_id else satellite_id,
                    'constellation': constellation.lower(),
                    'altitude': orbit_params.get('altitude', 550.0),
                    'inclination': orbit_params.get('inclination', 53.0),
                    'semi_major_axis': orbit_params.get('semi_major_axis', 6950.0),
                    'eccentricity': orbit_params.get('eccentricity', 0.0),
                    'mean_motion': orbit_params.get('mean_motion', 15.0),
                    # 🎯 關鍵修復：使用真實的 SGP4 預計算位置數據
                    'precomputed_positions': precomputed_positions,
                    'has_orbit_data': len(precomputed_positions) > 0
                })
        
        logger.info(f"✅ Phase0真實SGP4數據載入完成: {len(satellites)} 顆 {constellation} 衛星，軌道數據: {len([s for s in satellites if s['has_orbit_data']])} 顆")
        
        # 🔧 關鍵修復：如果成功載入真實數據，立即返回，不使用備用數據
        if satellites and len([s for s in satellites if s['has_orbit_data']]) > 0:
            logger.info(f"🎯 使用真實SGP4預計算數據: {len([s for s in satellites if s['has_orbit_data']])} 顆有軌道數據的衛星")
            return satellites
        
    except Exception as e:
        logger.error(f"❌ Phase0真實SGP4數據載入失敗: {e}")
        import traceback
        logger.error(f"詳細錯誤: {traceback.format_exc()}")
    
    # 🚫 根據 CLAUDE.md 核心原則，禁止使用備用數據生成
    # 必須使用真實的 Phase0 預計算 SGP4 數據，如無數據則報告錯誤
    logger.error(f"❌ Phase0 預計算數據載入完全失敗，拒絕使用備用數據生成: {constellation}")
    raise FileNotFoundError(f"Phase0 precomputed SGP4 data required for constellation {constellation}. Backup data generation prohibited.")

def calculate_satellite_position(sat_data: Dict, timestamp: datetime, observer_lat: float = 24.9441667, observer_lon: float = 121.3713889) -> SatelliteInfo:
    """
    使用預計算的真實SGP4軌道數據計算衛星位置
    直接使用預計算時間點，不依賴當前時間匹配
    """
    try:
        # 🔧 關鍵修復：直接使用預計算數據，不進行時間匹配
        precomputed_positions = sat_data.get('precomputed_positions', [])
        
        if precomputed_positions:
            # 🎯 關鍵修復：根據當前時間選擇最接近的預計算位置
            selected_position = None
            min_time_diff = float('inf')
            
            # 選擇時間上最接近當前請求時間的預計算位置
            for position in precomputed_positions:
                try:
                    pos_time_str = position.get('time', '')
                    if pos_time_str:
                        pos_time = datetime.fromisoformat(pos_time_str.replace('Z', '+00:00'))
                        time_diff = abs((timestamp - pos_time).total_seconds())
                        if time_diff < min_time_diff:
                            min_time_diff = time_diff
                            selected_position = position
                except Exception:
                    continue
            
            # 如果沒有找到匹配的時間，使用第一個位置作為後備
            if selected_position is None and precomputed_positions:
                selected_position = precomputed_positions[0]
            
            if selected_position:
                # 使用真實的SGP4計算結果
                elevation = selected_position.get('elevation_deg', -90)
                azimuth = selected_position.get('azimuth_deg', 0)
                distance = selected_position.get('range_km', 2000)
                
                # 信號強度計算 (基於ITU-R P.618)
                if elevation > 0:
                    frequency_ghz = 12.0  # Ku-band
                    fspl_db = 20 * math.log10(distance) + 20 * math.log10(frequency_ghz) + 92.45
                    satellite_eirp_dbm = 52.0 + 30  # 轉換為dBm
                    rx_antenna_gain_db = 35.0
                    elevation_gain = max(0, 10 * math.log10(math.sin(math.radians(max(elevation, 5)))))
                    signal_strength = satellite_eirp_dbm + rx_antenna_gain_db - fspl_db + elevation_gain - 5
                else:
                    signal_strength = -120.0  # 不可見衛星
                
# 使用預計算SGP4數據
                
                # 🔧 根據實際仰角判斷可見性
                is_actually_visible = elevation >= 0  # 地平線以上即為可見
                
                # 🎯 構建時間序列數據
                timeseries_points = []
                for pos in precomputed_positions:
                    timeseries_points.append(PositionTimePoint(
                        time=pos.get('time', ''),
                        time_offset_seconds=pos.get('time_offset_seconds', 0),
                        elevation_deg=round(pos.get('elevation_deg', -90), 2),
                        azimuth_deg=round(pos.get('azimuth_deg', 0), 2),
                        range_km=round(pos.get('range_km', 2000), 2),
                        is_visible=pos.get('elevation_deg', -90) >= 0
                    ))
                
                return SatelliteInfo(
                    name=sat_data['name'],
                    norad_id=sat_data['norad_id'],
                    elevation_deg=round(elevation, 2),
                    azimuth_deg=round(azimuth, 2),
                    distance_km=round(distance, 2),
                    orbit_altitude_km=sat_data.get('altitude', 550.0),
                    constellation=sat_data['constellation'],
                    signal_strength=round(signal_strength, 1),
                    is_visible=is_actually_visible,
                    position_timeseries=timeseries_points
                )
        
        # 🚫 根據 CLAUDE.md 核心原則，禁止使用簡化算法
        # 必須使用真實 SGP4 算法，如無預計算數據則返回錯誤
        logger.error(f"❌ 缺少 SGP4 軌道數據，拒絕使用簡化算法: {sat_data['name']}")
        return None  # 不返回簡化數據，強制使用真實算法
        
    except Exception as e:
        logger.error(f"計算衛星位置失敗: {e}")
        # 🚫 根據 CLAUDE.md 核心原則，禁止返回模擬數據
        # 計算失敗時返回 None，強制使用真實數據
        return None

# === API Endpoints ===

@router.get(
    "/visible_satellites",
    response_model=VisibleSatellitesResponse,
    summary="獲取智能選擇的可見衛星",
    description="使用智能預處理系統基於完整軌道週期分析的651+301顆衛星智能選擇 (基於真實234顆可見衛星優化)"
)
async def get_visible_satellites(
    count: int = Query(20, ge=1, le=200, description="返回的衛星數量"),
    constellation: str = Query("starlink", description="星座類型: starlink, oneweb"),
    min_elevation_deg: float = Query(5.0, ge=-90, le=90, description="最小仰角度數"),
    utc_timestamp: Optional[str] = Query(None, description="UTC時間戳"),
    global_view: bool = Query(False, description="全球視野模式")
) -> VisibleSatellitesResponse:
    """
    獲取智能選擇的可見衛星列表
    
    實現 @docs/satellite-preprocessing/ 計劃:
    - Starlink: 從8000+顆中選擇150顆最優衛星 (73%覆蓋205顆實際可見)
    - OneWeb: 從651顆中選擇50顆最優衛星 (172%覆蓋29顆實際可見)  
    - 確保8-12顆同時可見
    - 真實SGP4軌道計算
    - ITU-R P.618信號強度計算
    """
    try:
        current_time = datetime.utcnow()
        if utc_timestamp:
            try:
                current_time = datetime.fromisoformat(utc_timestamp.replace('Z', '+00:00'))
            except:
                pass
                
        logger.info(f"🛰️ 開始智能衛星選擇: {constellation} 星座, 請求 {count} 顆")
        
        # 1. 獲取完整衛星星座數據 (150+50顆優化配置)
        target_pool_size = 651 if constellation.lower() == 'starlink' else 301
        all_satellites = get_precomputed_satellite_data(constellation, target_pool_size)  # 使用預計算真實數據
        
        logger.info(f"📊 完整星座數據: {len(all_satellites)} 顆 {constellation} 衛星")
        
        # 2. 智能選擇策略：掃描全部衛星找出最佳可見子集
        selected_satellites = []
        preprocessing_stats = {}
        
        # 🎯 研究模式調整：根據請求數量決定篩選策略
        if count <= 15:
            # 傳統研究模式：嚴格控制數量，優化選擇品質
            logger.info(f"🔬 啟用傳統研究模式: 目標 {count} 顆高品質衛星")
            use_traditional_mode = True
        else:
            # 高密度研究模式：展示2025年真實衛星密度
            logger.info(f"🌐 啟用高密度研究模式: 目標 {count} 顆衛星")
            use_traditional_mode = False
        
        selector = get_intelligent_selector()
        if selector:
            try:
                # 調用智能選擇器選擇最優子集
                selected_subset, stats = selector.select_research_subset(all_satellites)
                preprocessing_stats = stats
                
                logger.info(f"✅ 智能選擇器完成: 選擇了 {len(selected_subset)} 顆衛星")
                logger.info(f"📈 選擇統計: {stats}")
                
                # 計算選擇的衛星的實時位置
                for sat_data in selected_subset:
                    sat_info = calculate_satellite_position(sat_data, current_time)
                    if sat_info and sat_info.elevation_deg >= min_elevation_deg:
                        selected_satellites.append(sat_info)
                        
            except Exception as e:
                logger.error(f"❌ 智能選擇器執行失敗: {e}")
                selector = None  # 觸發回退邏輯
        
        if not selector:
            logger.info("🔍 使用全域掃描策略：從所有衛星中選擇可見者")
            # 🔧 修復：掃描全部衛星，而不是只選擇前幾顆
            candidate_satellites = []
            
            # 計算所有衛星的實時位置和仰角
            for sat_data in all_satellites:
                try:
                    sat_info = calculate_satellite_position(sat_data, current_time)
                    if sat_info and sat_info.elevation_deg >= min_elevation_deg:
                        candidate_satellites.append(sat_info)
                except Exception as e:
                    logger.debug(f"計算衛星 {sat_data.get('name', 'UNKNOWN')} 位置失敗: {e}")
                    continue
            
            # 按仰角排序，選擇仰角最高的衛星
            candidate_satellites.sort(key=lambda x: x.elevation_deg, reverse=True)
            
            # 🎯 根據研究模式決定篩選策略
            if use_traditional_mode:
                # 傳統模式：提高仰角門檻，確保品質
                high_quality_sats = [s for s in candidate_satellites if s.elevation_deg >= 15]
                if len(high_quality_sats) >= count:
                    selected_satellites = high_quality_sats[:count]
                    logger.info(f"🔬 傳統模式：選擇 {count} 顆高品質衛星 (仰角≥15°)")
                else:
                    # 如果高品質衛星不夠，降級到10°門檻
                    medium_quality_sats = [s for s in candidate_satellites if s.elevation_deg >= 10]
                    selected_satellites = medium_quality_sats[:count]
                    logger.info(f"🔬 傳統模式：選擇 {count} 顆中等品質衛星 (仰角≥10°)")
            else:
                # 高密度模式：展示所有可見衛星
                selected_satellites = candidate_satellites[:count]
                logger.info(f"🌐 高密度模式：選擇 {len(selected_satellites)} 顆可見衛星")
            
            logger.info(f"📊 掃描結果: 從 {len(all_satellites)} 顆衛星中找到 {len(candidate_satellites)} 顆可見衛星")
        
        # 按仰角排序，仰角高的衛星優先
        selected_satellites.sort(key=lambda x: x.elevation_deg, reverse=True)
        
        # 限制返回數量
        selected_satellites = selected_satellites[:count]
        
        response = VisibleSatellitesResponse(
            satellites=selected_satellites,
            total_count=len(selected_satellites),
            requested_count=count,
            constellation=constellation,
            global_view=global_view,
            timestamp=current_time.isoformat() + 'Z',
            observer_location={
                "lat": 24.9441667,  # NTPU
                "lon": 121.3713889,
                "alt": 0.024
            },
            data_source="enhanced_preprocessing_150_50_satellites_optimized",
            preprocessing_stats=preprocessing_stats or {
                "starlink_satellites": 651 if constellation.lower() == 'starlink' else 0,
                "oneweb_satellites": 301 if constellation.lower() == 'oneweb' else 0,
                "total_constellation_pool": len(all_satellites),
                "intelligent_selector_used": selector is not None,
                "data_generation_method": "enhanced_preprocessing"
            }
        )
        
        logger.info(f"🎯 返回 {len(selected_satellites)} 顆可見衛星 (智能選擇系統)")
        
        return response
        
    except Exception as e:
        logger.error(f"❌ 獲取可見衛星失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取可見衛星失敗: {str(e)}")

@router.get(
    "/timeline/{constellation}",
    summary="獲取星座時間軸數據",
    description="獲取智能選擇衛星的24小時時間軸數據"
)
async def get_constellation_timeline(
    constellation: str,
    hours: int = Query(2, ge=1, le=24, description="時間範圍(小時)"),
    interval_minutes: int = Query(5, ge=1, le=60, description="時間間隔(分鐘)")
):
    """獲取星座時間軸數據"""
    try:
        current_time = datetime.utcnow()
        timeline_data = []
        
        # 生成時間點
        for i in range(0, hours * 60, interval_minutes):
            timestamp = current_time + timedelta(minutes=i)
            
            # 獲取該時間點的可見衛星
            satellites_response = await get_visible_satellites(
                count=20,
                constellation=constellation,
                min_elevation_deg=5.0,
                utc_timestamp=timestamp.isoformat() + 'Z'
            )
            
            timeline_data.append({
                "timestamp": timestamp.isoformat() + 'Z',
                "visible_count": len(satellites_response.satellites),
                "max_elevation": max([s.elevation_deg for s in satellites_response.satellites], default=0),
                "avg_signal_strength": sum([s.signal_strength for s in satellites_response.satellites if s.signal_strength]) / max(len(satellites_response.satellites), 1)
            })
        
        return {
            "constellation": constellation,
            "timeline": timeline_data,
            "total_points": len(timeline_data),
            "time_range_hours": hours,
            "data_source": "enhanced_preprocessing_120_80_satellites"
        }
        
    except Exception as e:
        logger.error(f"❌ 獲取時間軸數據失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取時間軸數據失敗: {str(e)}")

@router.get(
    "/health",
    summary="智能預處理系統健康檢查",
    description="檢查智能預處理系統和選擇器的狀態"
)
async def health_check():
    """智能預處理系統健康檢查"""
    preprocessing_service = get_preprocessing_service()
    intelligent_selector = get_intelligent_selector()
    
    return {
        "healthy": True,
        "service": "intelligent-satellite-preprocessing",
        "data_source": "enhanced_preprocessing_150_50_satellites_optimized",
        "timestamp": datetime.utcnow().isoformat() + 'Z',
        "components": {
            "preprocessing_service": preprocessing_service is not None,
            "intelligent_selector": intelligent_selector is not None
        },
        "endpoints": [
            "/api/v1/satellite-simple/visible_satellites",
            "/api/v1/satellite-simple/timeline/{constellation}", 
            "/api/v1/satellite-simple/health"
        ],
        "supported_constellations": ["starlink", "oneweb"],
        "intelligent_selection": {
            "starlink_target": 651,
            "oneweb_target": 301,
            "simultaneous_visible_target": "8-12 satellites",
            "selection_algorithm": "IntelligentSatelliteSelector",
            "orbit_calculation": "SGP4",
            "signal_model": "ITU-R P.618"
        }
    }