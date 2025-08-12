#!/usr/bin/env python3
"""
Phase 1 數據提供者實現

功能:
1. 實現 Phase1DataProvider 接口
2. 整合 SGP4 引擎和 TLE 載入器
3. 提供高效的軌道數據查詢服務

符合 CLAUDE.md 原則:
- 使用真實的 SGP4 計算結果
- 提供完整的軌道數據
- 確保數據準確性和一致性
"""

import logging
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Any
import numpy as np
import uuid

# 添加 Phase 1 模組路徑
PHASE1_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PHASE1_ROOT / "01_data_source"))
sys.path.insert(0, str(PHASE1_ROOT / "02_orbit_calculation"))
sys.path.insert(0, str(PHASE1_ROOT / "04_output_interface"))

from phase2_interface import (
    Phase1DataProvider, Phase1OrbitData, Phase1DataBatch, 
    Phase1QueryRequest, Phase1QueryResponse, DataFormat, CoordinateSystem
)

logger = logging.getLogger(__name__)

class SGP4Phase1DataProvider(Phase1DataProvider):
    """基於 SGP4 的 Phase 1 數據提供者"""
    
    def __init__(self, tle_data_path: str = ""):
        """
        初始化數據提供者
        
        Args:
            tle_data_path: TLE 數據路徑，為空時使用統一配置
        """
        if not tle_data_path:
            # 使用統一配置載入器
            try:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                config_dir = os.path.join(os.path.dirname(current_dir), 'config')
                if config_dir not in sys.path:
                    sys.path.insert(0, config_dir)
                
                from config_loader import get_tle_data_path
                tle_data_path = get_tle_data_path()
                logger.info("✅ 數據提供者使用統一配置載入器")
            except Exception as e:
                logger.warning(f"⚠️ 統一配置載入失敗，使用預設路徑: {e}")
                # 回退到智能路徑解析
                from pathlib import Path
                current_file = Path(__file__)
                project_root = current_file.parent.parent.parent
                tle_data_path = str(project_root / "netstack" / "tle_data")
                
        self.tle_data_path = tle_data_path
        self.tle_loader = None
        self.sgp4_engine = None
        self.satellite_catalog = {}
        self.data_coverage_info = {}
        self.last_data_load = None
        
        # 初始化核心組件
        self._initialize_components()
        
        logger.info("✅ SGP4 Phase 1 數據提供者初始化完成")
    
    def _initialize_components(self):
        """初始化核心組件"""
        try:
            # 載入 TLE 數據載入器
            from tle_loader import create_tle_loader
            self.tle_loader = create_tle_loader(self.tle_data_path)
            
            # 載入 SGP4 引擎
            from sgp4_engine import create_sgp4_engine, validate_sgp4_availability
            
            if not validate_sgp4_availability():
                raise RuntimeError("SGP4 庫不可用")
            
            self.sgp4_engine = create_sgp4_engine()
            
            # 載入衛星數據
            self._load_satellite_data()
            
            logger.info("核心組件初始化完成")
            
        except Exception as e:
            logger.error(f"核心組件初始化失敗: {e}")
            raise
    
    def _load_satellite_data(self):
        """載入衛星數據"""
        try:
            logger.info("開始載入衛星數據...")
            
            # 載入 TLE 數據
            tle_result = self.tle_loader.load_all_tle_data()
            
            if tle_result.total_records == 0:
                logger.warning("未找到任何 TLE 數據")
                return
            
            # 創建衛星對象並建立目錄
            successful_satellites = 0
            constellation_stats = {}
            
            for record in tle_result.records:
                satellite_id = record.satellite_id
                
                # 創建 SGP4 衛星對象
                success = self.sgp4_engine.create_satellite(
                    satellite_id, record.line1, record.line2
                )
                
                if success:
                    self.satellite_catalog[satellite_id] = {
                        'satellite_id': satellite_id,
                        'satellite_name': record.satellite_name,
                        'constellation': record.constellation,
                        'line1': record.line1,
                        'line2': record.line2,
                        'epoch': record.epoch,
                        'loaded_time': datetime.now(timezone.utc)
                    }
                    
                    successful_satellites += 1
                    
                    # 統計星座信息
                    if record.constellation not in constellation_stats:
                        constellation_stats[record.constellation] = 0
                    constellation_stats[record.constellation] += 1
            
            # 更新數據覆蓋信息
            self.data_coverage_info = {
                'total_satellites': successful_satellites,
                'total_tle_records': tle_result.total_records,
                'constellation_distribution': constellation_stats,
                'data_load_time': datetime.now(timezone.utc),
                'data_source_path': self.tle_data_path,
                'sgp4_engine_stats': self.sgp4_engine.get_statistics()
            }
            
            self.last_data_load = datetime.now(timezone.utc)
            
            logger.info(f"衛星數據載入完成: {successful_satellites}/{tle_result.total_records} 成功載入")
            logger.info(f"星座分布: {constellation_stats}")
            
        except Exception as e:
            logger.error(f"載入衛星數據失敗: {e}")
            raise
    
    def query_orbit_data(self, request: Phase1QueryRequest) -> Phase1QueryResponse:
        """查詢軌道數據"""
        start_time = datetime.now(timezone.utc)
        
        try:
            logger.info(f"處理軌道數據查詢: {request.request_id}")
            
            # 確定查詢的衛星列表
            target_satellites = self._determine_target_satellites(request)
            
            if not target_satellites:
                return Phase1QueryResponse(
                    request_id=request.request_id,
                    response_time=datetime.now(timezone.utc),
                    success=False,
                    total_matches=0,
                    returned_records=0,
                    has_more_data=False,
                    error_message="沒有符合條件的衛星"
                )
            
            # 確定查詢時間點
            time_points = self._determine_time_points(request)
            
            # 執行批量軌道計算
            orbit_results = []
            calculation_errors = []
            
            for satellite_id in target_satellites[:request.max_records // len(time_points)]:
                for time_point in time_points:
                    orbit_data = self._calculate_satellite_orbit(
                        satellite_id, time_point, request.coordinate_system
                    )
                    
                    if orbit_data:
                        orbit_results.append(orbit_data)
                    else:
                        calculation_errors.append(f"計算失敗: {satellite_id} at {time_point}")
                    
                    # 檢查記錄數限制
                    if len(orbit_results) >= request.max_records:
                        break
                
                if len(orbit_results) >= request.max_records:
                    break
            
            # 創建數據批次
            data_batch = self._create_data_batch(
                orbit_results, request, start_time
            )
            
            # 計算是否有更多數據
            total_possible = len(target_satellites) * len(time_points)
            has_more = len(orbit_results) < total_possible
            
            response = Phase1QueryResponse(
                request_id=request.request_id,
                response_time=datetime.now(timezone.utc),
                success=True,
                total_matches=total_possible,
                returned_records=len(orbit_results),
                has_more_data=has_more,
                data_batch=data_batch,
                error_message=None if not calculation_errors else f"{len(calculation_errors)} 計算錯誤"
            )
            
            query_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            logger.info(f"軌道數據查詢完成: {len(orbit_results)} 記錄, 耗時 {query_time:.2f}s")
            
            return response
            
        except Exception as e:
            logger.error(f"軌道數據查詢失敗 {request.request_id}: {e}")
            return Phase1QueryResponse(
                request_id=request.request_id,
                response_time=datetime.now(timezone.utc),
                success=False,
                total_matches=0,
                returned_records=0,
                has_more_data=False,
                error_message=f"查詢執行異常: {e}"
            )
    
    def _determine_target_satellites(self, request: Phase1QueryRequest) -> List[str]:
        """確定目標衛星列表"""
        target_satellites = []
        
        # 如果指定了衛星 ID
        if request.satellite_ids:
            for satellite_id in request.satellite_ids:
                if satellite_id in self.satellite_catalog:
                    target_satellites.append(satellite_id)
        
        # 如果指定了星座
        elif request.constellations:
            for satellite_id, info in self.satellite_catalog.items():
                if info['constellation'] in request.constellations:
                    target_satellites.append(satellite_id)
        
        # 否則返回所有衛星
        else:
            target_satellites = list(self.satellite_catalog.keys())
        
        return target_satellites
    
    def _determine_time_points(self, request: Phase1QueryRequest) -> List[datetime]:
        """確定查詢時間點"""
        if request.time_range_start and request.time_range_end:
            # 使用指定時間範圍
            time_points = []
            current_time = request.time_range_start
            time_step = timedelta(minutes=1)  # 1分鐘間隔
            
            while current_time <= request.time_range_end and len(time_points) < 10:
                time_points.append(current_time)
                current_time += time_step
            
            return time_points
        else:
            # 使用當前時間
            return [datetime.now(timezone.utc)]
    
    def _calculate_satellite_orbit(self, 
                                 satellite_id: str, 
                                 timestamp: datetime,
                                 coordinate_system: CoordinateSystem) -> Optional[Phase1OrbitData]:
        """計算單顆衛星軌道"""
        try:
            # 使用 SGP4 引擎計算
            result = self.sgp4_engine.calculate_position(satellite_id, timestamp)
            
            if not result or not result.success:
                return None
            
            # 獲取衛星信息
            satellite_info = self.satellite_catalog.get(satellite_id, {})
            
            # 創建 Phase1OrbitData
            orbit_data = Phase1OrbitData(
                satellite_id=satellite_id,
                constellation=satellite_info.get('constellation', 'unknown'),
                timestamp=timestamp,
                position_eci=result.position_eci.tolist(),
                velocity_eci=result.velocity_eci.tolist(),
                position_teme=result.position_teme.tolist(),
                velocity_teme=result.velocity_teme.tolist(),
                calculation_quality=1.0 if result.error_code == 0 else 0.5,
                error_code=result.error_code,
                metadata={
                    'satellite_name': satellite_info.get('satellite_name', ''),
                    'tle_epoch': satellite_info.get('epoch', '').isoformat() if satellite_info.get('epoch') else '',
                    'coordinate_system_requested': coordinate_system.value
                }
            )
            
            return orbit_data
            
        except Exception as e:
            logger.error(f"計算衛星軌道失敗 {satellite_id}: {e}")
            return None
    
    def _create_data_batch(self, 
                         orbit_results: List[Phase1OrbitData],
                         request: Phase1QueryRequest,
                         generation_start_time: datetime) -> Phase1DataBatch:
        """創建數據批次"""
        
        # 計算時間範圍
        if orbit_results:
            timestamps = [orbit.timestamp for orbit in orbit_results]
            time_range_start = min(timestamps)
            time_range_end = max(timestamps)
        else:
            time_range_start = time_range_end = datetime.now(timezone.utc)
        
        # 計算品質指標
        quality_scores = [orbit.calculation_quality for orbit in orbit_results]
        quality_metrics = {
            'average_quality': float(np.mean(quality_scores)) if quality_scores else 0.0,
            'min_quality': float(np.min(quality_scores)) if quality_scores else 0.0,
            'max_quality': float(np.max(quality_scores)) if quality_scores else 0.0,
            'successful_calculations': sum(1 for orbit in orbit_results if orbit.error_code == 0),
            'failed_calculations': sum(1 for orbit in orbit_results if orbit.error_code != 0)
        }
        
        # 統計衛星和星座
        unique_satellites = set(orbit.satellite_id for orbit in orbit_results)
        unique_constellations = set(orbit.constellation for orbit in orbit_results)
        
        batch = Phase1DataBatch(
            batch_id=str(uuid.uuid4()),
            generation_time=generation_start_time,
            time_range_start=time_range_start,
            time_range_end=time_range_end,
            satellite_count=len(unique_satellites),
            total_records=len(orbit_results),
            data_format=request.data_format,
            coordinate_systems=[request.coordinate_system],
            orbit_data=orbit_results,
            quality_metrics=quality_metrics,
            version="1.0"
        )
        
        return batch
    
    def get_available_satellites(self) -> List[str]:
        """獲取可用衛星列表"""
        return list(self.satellite_catalog.keys())
    
    def get_data_coverage(self) -> Dict[str, Any]:
        """獲取數據覆蓋範圍"""
        coverage = self.data_coverage_info.copy()
        
        # 添加即時統計
        if self.sgp4_engine:
            coverage['current_engine_stats'] = self.sgp4_engine.get_statistics()
        
        coverage['last_update'] = self.last_data_load.isoformat() if self.last_data_load else None
        
        return coverage
    
    def validate_data_integrity(self) -> bool:
        """驗證數據完整性"""
        try:
            # 檢查核心組件
            if not self.tle_loader or not self.sgp4_engine:
                return False
            
            # 檢查衛星目錄
            if not self.satellite_catalog:
                return False
            
            # 檢查 SGP4 引擎統計
            stats = self.sgp4_engine.get_statistics()
            if stats['cached_satellites'] == 0:
                return False
            
            # 抽樣測試幾顆衛星的計算
            test_satellites = list(self.satellite_catalog.keys())[:3]
            test_time = datetime.now(timezone.utc)
            
            successful_tests = 0
            for satellite_id in test_satellites:
                result = self.sgp4_engine.calculate_position(satellite_id, test_time)
                if result and result.success:
                    successful_tests += 1
            
            # 至少50%的測試衛星應該計算成功
            integrity_ok = (successful_tests / len(test_satellites)) >= 0.5
            
            logger.info(f"數據完整性驗證: {successful_tests}/{len(test_satellites)} 測試通過")
            return integrity_ok
            
        except Exception as e:
            logger.error(f"數據完整性驗證失敗: {e}")
            return False
    
    def refresh_data(self):
        """刷新數據"""
        try:
            logger.info("開始刷新數據...")
            
            # 清除現有緩存
            if self.sgp4_engine:
                self.sgp4_engine.clear_cache()
            
            self.satellite_catalog.clear()
            
            # 重新載入數據
            self._load_satellite_data()
            
            logger.info("數據刷新完成")
            
        except Exception as e:
            logger.error(f"數據刷新失敗: {e}")
            raise

# 便利函數
def create_sgp4_data_provider(tle_data_path: str = "") -> SGP4Phase1DataProvider:
    """創建 SGP4 數據提供者"""
    return SGP4Phase1DataProvider(tle_data_path)

if __name__ == "__main__":
    # 測試用例
    logging.basicConfig(level=logging.INFO)
    
    try:
        print("SGP4 Phase 1 數據提供者測試")
        print("=" * 40)
        
        # 創建數據提供者
        provider = create_sgp4_data_provider()
        
        # 測試獲取可用衛星
        satellites = provider.get_available_satellites()
        print(f"可用衛星數量: {len(satellites)}")
        
        # 測試數據覆蓋範圍
        coverage = provider.get_data_coverage()
        print(f"數據覆蓋: {coverage.get('total_satellites', 0)} 顆衛星")
        
        # 測試數據完整性
        integrity = provider.validate_data_integrity()
        print(f"數據完整性: {'✅ 通過' if integrity else '❌ 失敗'}")
        
        # 測試查詢功能
        from phase2_interface import Phase1QueryRequest, CoordinateSystem, DataFormat
        
        test_request = Phase1QueryRequest(
            request_id="test_001",
            timestamp=datetime.now(timezone.utc),
            satellite_ids=satellites[:3] if satellites else None,
            coordinate_system=CoordinateSystem.ECI,
            data_format=DataFormat.JSON,
            max_records=10
        )
        
        response = provider.query_orbit_data(test_request)
        print(f"查詢測試: {'✅ 成功' if response.success else '❌ 失敗'}")
        if response.success:
            print(f"  返回記錄數: {response.returned_records}")
        
        print("✅ SGP4 Phase 1 數據提供者測試完成")
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()