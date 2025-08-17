#!/usr/bin/env python3
"""
LEO F1→F2→F3→A1 系統 - API 輸出接口

功能:
1. 提供 F1→F2→F3→A1 數據的統一 API 接口
2. 替代原有的舊六階段系統
3. 支援動態衛星池優化數據查詢

符合 CLAUDE.md 原則:
- 提供真實的 SGP4 計算結果
- 明確標識數據來源為 "leo_f1_f2_f3_a1_system"
- 支援完整的 8,715 顆衛星數據
"""

import os
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Query

logger = logging.getLogger(__name__)

# LEO F1→F2→F3→A1 API 路由器
router = APIRouter(
    prefix="/api/v1/leo-orbit",
    tags=["LEO F1→F2→F3→A1 Satellite Data"]
)

class LEOOrbitAPIInterface:
    """
    LEO F1→F2→F3→A1 API 接口類
    
    負責提供 F1→F2→F3→A1 軌道數據的 REST API
    支援多種查詢方式和數據格式
    """
    
    def __init__(self, data_dir: str = "/app/data"):
        """
        初始化 API 接口
        
        Args:
            data_dir: F1→F2→F3→A1 數據輸出目錄
        """
        self.data_dir = Path(data_dir)
        self.orbit_database = None
        self.summary_data = None
        
        # 載入 LEO 數據
        self._load_leo_data()
        
        logger.info(f"✅ LEO F1→F2→F3→A1 API 接口初始化完成: {self.data_dir}")
    
    def _load_leo_data(self):
        """載入 F1→F2→F3→A1 生成的數據"""
        try:
            # 載入軌道數據庫
            orbit_db_path = self.data_dir / "tle_loading_and_orbit_calculation_results.json"
            if orbit_db_path.exists():
                with open(orbit_db_path, 'r', encoding='utf-8') as f:
                    self.orbit_database = json.load(f)
                logger.info("✅ LEO 軌道數據庫已載入")
            
            # 載入執行摘要
            summary_path = self.data_dir / "leo_optimization_final_report.json"
            if summary_path.exists():
                with open(summary_path, 'r', encoding='utf-8') as f:
                    self.summary_data = json.load(f)
                logger.info("✅ LEO 執行摘要已載入")
                
        except Exception as e:
            logger.warning(f"載入 LEO 數據時出現問題: {e}")
    
    def get_satellite_orbits(self, constellation: str, count: int = 200) -> List[Dict]:
        """
        獲取衛星軌道數據
        
        取代原有的 get_enhanced_satellite_data() 函數
        
        Args:
            constellation: 星座名稱 ("starlink" 或 "oneweb")
            count: 返回數量限制
            
        Returns:
            List[Dict]: 衛星軌道數據列表
        """
        if not self.orbit_database:
            raise HTTPException(status_code=503, detail="LEO 數據尚未準備就緒")
        
        constellations = self.orbit_database.get("constellations", {})
        
        if constellation not in constellations:
            available = list(constellations.keys())
            raise HTTPException(
                status_code=404, 
                detail=f"星座 '{constellation}' 不存在。可用星座: {available}"
            )
        
        constellation_data = constellations[constellation]
        satellites = constellation_data.get("satellites", {})
        
        # 轉換為 API 響應格式
        results = []
        for satellite_id, satellite_info in list(satellites.items())[:count]:
            # 取最新的位置數據
            positions = satellite_info.get("positions", [])
            if positions:
                latest_position = positions[0]  # 假設按時間排序
                
                result = {
                    "satellite_id": satellite_id,
                    "satellite_name": satellite_info.get("satellite_name", ""),
                    "constellation": constellation,
                    "timestamp": latest_position.get("timestamp", ""),
                    "position": {
                        "x": latest_position["position_eci"][0],
                        "y": latest_position["position_eci"][1], 
                        "z": latest_position["position_eci"][2]
                    },
                    "velocity": {
                        "vx": latest_position["velocity_eci"][0],
                        "vy": latest_position["velocity_eci"][1],
                        "vz": latest_position["velocity_eci"][2]
                    },
                    "data_source": "leo_f1_f2_f3_a1_system",
                    "algorithm": "complete_sgp4_algorithm"
                }
                results.append(result)
        
        logger.info(f"返回 {len(results)} 條 {constellation} 軌道數據")
        return results
    
    def get_constellation_info(self) -> Dict[str, Any]:
        """
        獲取所有星座的統計信息
        
        Returns:
            Dict: 星座統計信息
        """
        if not self.orbit_database:
            return {"error": "LEO 數據尚未準備就緒"}
        
        constellations_info = {}
        constellations = self.orbit_database.get("constellations", {})
        
        for constellation_name, constellation_data in constellations.items():
            constellations_info[constellation_name] = {
                "total_satellites": constellation_data.get("total_satellites", 0),
                "available_satellites": len(constellation_data.get("satellites", {})),
                "data_source": "leo_f1_f2_f3_a1_system"
            }
        
        result = {
            "generation_timestamp": self.orbit_database.get("generation_timestamp", ""),
            "algorithm": self.orbit_database.get("algorithm", "complete_sgp4_algorithm"),
            "constellations": constellations_info,
            "total_satellites": sum(info["total_satellites"] for info in constellations_info.values())
        }
        
        return result
    
    def get_satellite_trajectory(self, satellite_id: str, 
                               constellation: str) -> Dict[str, Any]:
        """
        獲取單顆衛星的完整軌跡
        
        Args:
            satellite_id: 衛星 ID
            constellation: 星座名稱
            
        Returns:
            Dict: 衛星軌跡數據
        """
        if not self.orbit_database:
            raise HTTPException(status_code=503, detail="LEO 數據尚未準備就緒")
        
        constellations = self.orbit_database.get("constellations", {})
        
        if constellation not in constellations:
            raise HTTPException(status_code=404, detail=f"星座 '{constellation}' 不存在")
        
        satellites = constellations[constellation].get("satellites", {})
        
        if satellite_id not in satellites:
            raise HTTPException(status_code=404, detail=f"衛星 '{satellite_id}' 不存在")
        
        satellite_info = satellites[satellite_id]
        
        return {
            "satellite_id": satellite_id,
            "satellite_name": satellite_info.get("satellite_name", ""),
            "constellation": constellation,
            "tle_epoch": satellite_info.get("tle_epoch", ""),
            "positions": satellite_info.get("positions", []),
            "total_positions": satellite_info.get("total_positions", 0),
            "data_source": "leo_f1_f2_f3_a1_system",
            "computation_parameters": self.orbit_database.get("computation_parameters", {})
        }
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """
        獲取 LEO F1→F2→F3→A1 執行摘要
        
        Returns:
            Dict: 執行摘要信息
        """
        if not self.summary_data:
            return {"error": "執行摘要數據不可用"}
        
        return self.summary_data

# 全局 API 接口實例
leo_orbit_api = None

def get_leo_orbit_api() -> LEOOrbitAPIInterface:
    """獲取 LEO 軌道 API 接口實例"""
    global leo_orbit_api
    if leo_orbit_api is None:
        leo_orbit_api = LEOOrbitAPIInterface()
    return leo_orbit_api

# FastAPI 路由定義
@router.get("/satellite_orbits")
def get_satellite_orbits_endpoint(
    constellation: str = Query(..., description="星座名稱"),
    count: int = Query(200, ge=1, le=10000, description="返回數量")
):
    """獲取衛星軌道數據 API 端點"""
    api = get_leo_orbit_api()
    return api.get_satellite_orbits(constellation, count)

@router.get("/constellations/info")
def get_constellations_info_endpoint():
    """獲取星座統計信息 API 端點"""
    api = get_leo_orbit_api()
    return api.get_constellation_info()

@router.get("/satellite/{satellite_id}/trajectory")
def get_satellite_trajectory_endpoint(
    satellite_id: str,
    constellation: str = Query(..., description="星座名稱")
):
    """獲取單顆衛星軌跡 API 端點"""
    api = get_leo_orbit_api()
    return api.get_satellite_trajectory(satellite_id, constellation)

@router.get("/execution/summary")
def get_execution_summary_endpoint():
    """獲取執行摘要 API 端點"""
    api = get_leo_orbit_api()
    return api.get_execution_summary()

@router.get("/health")
def leo_orbit_health_check():
    """LEO 軌道健康檢查"""
    api = get_leo_orbit_api()
    
    status = "healthy" if api.orbit_database else "no_data"
    
    return {
        "status": status,
        "service": "LEO F1→F2→F3→A1 Satellite Orbit Data",
        "algorithm": "complete_sgp4_algorithm",
        "data_available": api.orbit_database is not None,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

if __name__ == "__main__":
    # 測試用例
    try:
        api = LEOOrbitAPIInterface()
        info = api.get_constellation_info()
        print("✅ LEO F1→F2→F3→A1 API 測試成功")
        print(f"   可用星座: {list(info.get('constellations', {}).keys())}")
        print(f"   總衛星數: {info.get('total_satellites', 0)}")
    except Exception as e:
        print(f"❌ LEO F1→F2→F3→A1 API 測試失敗: {e}")