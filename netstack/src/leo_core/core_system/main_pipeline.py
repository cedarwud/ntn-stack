# 🛰️ Phase 1 主管道執行器
"""
Phase 1 Main Pipeline - 完整核心系統執行流程
功能: 串接F1→F2→F3→A1完整流程，實現10-15/3-6顆衛星動態覆蓋
"""

import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path
import json
import sys
import os

# 添加當前路徑到系統路徑
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

from tle_data_loader.tle_loader_engine import TLELoaderEngine
from satellite_filter_engine.satellite_filter_engine_v2 import SatelliteFilterEngineV2  
from signal_analyzer.threegpp_event_processor import A4A5D2EventProcessor
from dynamic_pool_planner.simulated_annealing_optimizer import SimulatedAnnealingOptimizer

class LEOCorePipeline:
    """LEO 核心系統管道執行器"""
    
    def __init__(self, config: dict, output_dir: str = None):
        self.config = config
        self.logger = self._setup_logger()
        
        # 🎯 分層輸出策略實現 (跨平台兼容)
        import tempfile
        import os
        
        if output_dir:
            # 🔧 F3/A1永久數據目錄 - 添加跨平台檢測
            # 檢測是否在容器環境中（通過路徑和環境變量雙重檢測）
            is_container = (os.getenv('DOCKER_CONTAINER') == '1' or 
                          Path('/app').exists() or 
                          Path('/.dockerenv').exists())
            
            if is_container:
                # 容器環境：使用傳入的容器路徑
                self.output_dir = Path(output_dir)
            else:
                # 主機環境：檢測並轉換為本地路徑
                if output_dir.startswith('/app/data') or output_dir.startswith('/tmp/'):
                    # 容器路徑：轉換為主機項目目錄
                    project_root = Path.cwd().resolve()
                    self.output_dir = project_root / "data" / "leo_outputs"
                else:
                    # 已經是主機路徑：直接使用
                    self.output_dir = Path(output_dir)
            
            # F1/F2臨時輸出目錄 - 使用跨平台臨時目錄
            if is_container:
                # 容器環境：使用容器內臨時目錄
                self.temp_output_dir = Path("/tmp/leo_temporary_outputs")
            else:
                # 主機環境：使用系統臨時目錄 + 子目錄
                system_temp = Path(tempfile.gettempdir())
                self.temp_output_dir = system_temp / "leo_temporary_outputs"
        else:
            # 默認配置：使用跨平台默認路徑
            # 檢測是否在容器環境中（通過路徑和環境變量雙重檢測）
            is_container = (os.getenv('DOCKER_CONTAINER') == '1' or 
                          Path('/app').exists() or 
                          Path('/.dockerenv').exists())
            
            if is_container:
                # 容器環境：使用容器預設路徑
                default_output = '/app/data'
                self.temp_output_dir = Path("/tmp/leo_temporary_outputs")
            else:
                # 主機環境：使用項目目錄下的data子目錄
                project_root = Path.cwd().resolve()
                default_output = str(project_root / "data" / "leo_outputs")
                self.temp_output_dir = Path(tempfile.gettempdir()) / "leo_temporary_outputs"
            
            self.output_dir = Path(default_output)
        
        # 確保目錄存在
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_output_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"🎯 分層輸出策略:")
        self.logger.info(f"   F1/F2臨時數據: {self.temp_output_dir}")
        self.logger.info(f"   F3/A1永久數據: {self.output_dir}")
        
        # 管道統計
        self.pipeline_stats = {
            'start_time': None,
            'end_time': None,
            'total_duration_seconds': 0,
            'stages_completed': 0,
            'total_stages': 4,
            'stage_durations': {},
            'final_results': {}
        }
        
        # 階段組件
        self.tle_loader = None
        self.satellite_filter = None
        self.event_processor = None
        self.optimizer = None
    
    def _setup_logger(self):
        """設置日誌記錄器"""
        logger = logging.getLogger('LEOCorePipeline')
        logger.setLevel(logging.INFO)
        
        # 創建控制台處理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 創建格式器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        
        # 添加處理器到記錄器
        if not logger.handlers:
            logger.addHandler(console_handler)
        
        return logger
    
    async def execute_complete_pipeline(self):
        """執行完整的Phase 1管道"""
        
        # 初始化管道統計
        pipeline_start_time = datetime.now(timezone.utc)  # 🔧 修復：使用datetime一致性
        self.pipeline_stats = {
            'start_time': pipeline_start_time,  # 🔧 修復：存儲datetime對象
            'stages_completed': 0,
            'total_stages': 4,
            'stage_durations': {},
            'handover_events': []  # 初始化，供最終報告使用
        }
        
        try:
            self.logger.info("🚀 LEO核心系統管道執行開始")
            self.logger.info(f"   輸出目錄: {self.output_dir}")
            
            # Stage 1: TLE Loader - 載入全量衛星並計算軌道位置
            stage1_start = datetime.now(timezone.utc)
            self.logger.info("🛰️ Stage 1: TLE Loader 開始...")
            
            satellite_data, orbital_positions = await self._execute_stage1_tle_loading()
            
            stage1_duration = (datetime.now(timezone.utc) - stage1_start).total_seconds()
            self.pipeline_stats['stage_durations']['stage1_tle_loading'] = stage1_duration
            self.pipeline_stats['stages_completed'] += 1
            
            self.logger.info(f"✅ Stage 1完成 ({stage1_duration:.1f}秒)")
            
            # Stage 2: F2_Satellite_Filter - 篩選候選並使用全量軌道位置
            stage2_start = datetime.now(timezone.utc)
            self.logger.info("🔍 Stage 2: F2_Satellite_Filter 開始...")
            
            filtered_candidates, candidate_orbital_positions = await self._execute_stage2_satellite_filtering(satellite_data, orbital_positions)
            
            stage2_duration = (datetime.now(timezone.utc) - stage2_start).total_seconds()
            self.pipeline_stats['stage_durations']['stage2_filtering'] = stage2_duration
            self.pipeline_stats['stages_completed'] += 1
            
            self.logger.info(f"✅ Stage 2完成 ({stage2_duration:.1f}秒)")
            
            # Stage 3: F3_Signal_Analyzer - A4/A5/D2事件分析
            stage3_start = datetime.now(timezone.utc)
            self.logger.info("📊 Stage 3: F3_Signal_Analyzer 開始...")
            
            handover_events = await self._execute_stage3_signal_analysis(filtered_candidates, candidate_orbital_positions)
            
            stage3_duration = (datetime.now(timezone.utc) - stage3_start).total_seconds()
            self.pipeline_stats['stage_durations']['stage3_signal_analysis'] = stage3_duration
            self.pipeline_stats['stages_completed'] += 1
            
            # 將handover_events存儲到pipeline_stats中供最終報告使用
            self.pipeline_stats['handover_events'] = handover_events
            
            self.logger.info(f"✅ Stage 3完成 ({stage3_duration:.1f}秒)")
            
            # Stage 4: A1_Dynamic_Pool_Planner - 模擬退火最佳化
            stage4_start = datetime.now(timezone.utc)
            self.logger.info("🔥 Stage 4: A1_Dynamic_Pool_Planner 開始...")
            
            optimal_pools = await self._execute_stage4_pool_optimization(filtered_candidates, candidate_orbital_positions)
            
            stage4_duration = (datetime.now(timezone.utc) - stage4_start).total_seconds()
            self.pipeline_stats['stage_durations']['stage4_optimization'] = stage4_duration
            self.pipeline_stats['stages_completed'] += 1
            
            self.logger.info(f"✅ Stage 4完成 ({stage4_duration:.1f}秒)")
            
            # 生成最終報告 - 修復同步/異步不匹配問題
            self._generate_final_report(optimal_pools)
            
            # 🔧 修復：計算總時間時使用一致的datetime對象
            pipeline_end_time = datetime.now(timezone.utc)
            self.pipeline_stats['end_time'] = pipeline_end_time
            self.pipeline_stats['total_duration_seconds'] = (
                pipeline_end_time - pipeline_start_time
            ).total_seconds()
            
            self.logger.info("🎉 LEO核心系統管道執行完成!")
            self.logger.info(f"   總耗時: {self.pipeline_stats['total_duration_seconds']:.1f}秒")
            self.logger.info(f"   完成階段: {self.pipeline_stats['stages_completed']}/{self.pipeline_stats['total_stages']}")
            
            return optimal_pools
            
        except Exception as e:
            self.logger.error(f"❌ LEO核心系統管道執行失敗: {e}")
            raise
    
    async def _execute_stage1_tle_loading(self):
        """執行Stage 1: TLE數據載入"""
        
        # ✅ 修正：初始化TLE載入器，傳遞完整配置以支援sample_limits
        self.tle_loader = TLELoaderEngine(
            config=self.config.get('tle_loader', {}),
            full_config=self.config  # 傳遞完整配置以訪問satellite_filter.sample_limits
        )
        await self.tle_loader.initialize()
        
        # 載入全量衛星數據
        satellite_data = await self.tle_loader.load_full_satellite_data()
        
        # 記錄全量衛星數據
        if satellite_data.get('starlink'):
            self.logger.info(f"   Starlink衛星: {len(satellite_data['starlink'])}顆")
        if satellite_data.get('oneweb'):
            self.logger.info(f"   OneWeb衛星: {len(satellite_data['oneweb'])}顆")
        
        total_satellites = sum(len(sats) for sats in satellite_data.values())
        self.logger.info(f"📊 全量衛星總計: {total_satellites}顆")
        
        # ✅ 修正: 按照計劃，Stage 1應該計算全量衛星的軌道位置
        self.logger.info("🛰️ 開始計算全量衛星軌道位置...")
        
        # ✅ 收集**全量**衛星進行軌道計算 (按照原始架構修正)
        all_satellites = []
        for constellation_satellites in satellite_data.values():
            all_satellites.extend(constellation_satellites)
        
        if len(all_satellites) > 0:
            self.logger.info(f"📊 全量衛星構成：總計{len(all_satellites)}顆衛星")
            self.logger.info(f"   包含：{len(satellite_data.get('starlink', []))}顆Starlink + {len(satellite_data.get('oneweb', []))}顆OneWeb")
            self.logger.info(f"📊 計算全量{len(all_satellites)}顆衛星的軌道位置(200分鐘統一時間範圍)...")
            
            # 🔧 使用200分鐘統一時間範圍覆蓋雙星座軌道週期 (Starlink 96分鐘 + OneWeb 109分鐘)
            time_range = self.config.get('tle_loader', {}).get('calculation_params', {}).get('time_range_minutes', 200)
            orbital_positions = await self.tle_loader.calculate_orbital_positions(
                all_satellites, time_range_minutes=time_range
            )
            self.logger.info(f"✅ 全量軌道位置計算完成: {len(orbital_positions)}顆衛星")
        else:
            self.logger.warning("⚠️ 沒有衛星數據，跳過軌道位置計算")
            orbital_positions = {}
        
        # 導出Stage 1結果 - F1使用臨時目錄，改為有意義的檔名
        tle_loading_output = self.temp_output_dir / "tle_loading_and_orbit_calculation_results.json"
        await self.tle_loader.export_load_statistics(str(tle_loading_output))
        
        self.logger.info(f"📊 Stage 1統計: 載入{self.tle_loader.load_statistics['total_satellites']}顆衛星，計算{len(orbital_positions)}顆軌道")
        
        return satellite_data, orbital_positions
    
    async def _execute_stage2_satellite_filtering(self, satellite_data, orbital_positions):
        """執行Stage 2: 衛星篩選"""
        
        # 初始化篩選器 (v2 - 六階段篩選管線)
        self.satellite_filter = SatelliteFilterEngineV2(self.config.get('satellite_filter', {}))
        
        # ✅ 修正: 從有軌道數據的衛星中進行智能篩選
        self.logger.info(f"🔍 基於{len(orbital_positions)}顆衛星的軌道位置進行智能篩選")
        
        # 🔧 調整：僅從有軌道數據的衛星中篩選候選
        filtered_satellite_data = {}
        for constellation, satellites in satellite_data.items():
            # 只保留有軌道數據的衛星
            filtered_sats = [sat for sat in satellites if sat.satellite_id in orbital_positions]
            filtered_satellite_data[constellation] = filtered_sats
            self.logger.info(f"   {constellation}: {len(filtered_sats)}顆衛星有軌道數據")
        
        # ✅ 修復：全量模式使用適合的篩選策略
        total_satellites = sum(len(sats) for sats in filtered_satellite_data.values())
        
        if total_satellites >= 8000:  # 真正的全量模式
            self.logger.info(f"🌍 全量模式 ({total_satellites}顆 ≥ 8000)，使用寬鬆篩選避免過度篩選")
            # 修改篩選器配置為更寬鬆的參數
            original_config = self.satellite_filter.config.copy()
            
            # 調整為全量模式適用的寬鬆參數
            self.satellite_filter.config.update({
                'filtering_params': {
                    'geographic_threshold': 120.0,    # 放寬地理範圍
                    'min_score_threshold': 30.0,      # 降低評分門檻
                    'rsrp_threshold_dbm': -120.0,     # 放寬RSRP門檻
                    'max_candidates_per_constellation': 500  # 增加候選數上限
                }
            })
            
            # 使用開發模式篩選（較寬鬆）
            filtered_candidates = await self.satellite_filter.apply_development_filter(
                filtered_satellite_data, orbital_positions
            )
            
            # 恢復原始配置
            self.satellite_filter.config = original_config
            
        elif total_satellites <= 200:
            self.logger.info(f"🚀 開發模式 ({total_satellites}顆 ≤ 200)，使用寬鬆篩選")
            # 使用開發模式篩選
            filtered_candidates = await self.satellite_filter.apply_development_filter(
                filtered_satellite_data, orbital_positions
            )
        else:
            self.logger.info(f"🏭 生產模式 ({total_satellites}顆)，使用六階段篩選")
            # 應用六階段綜合篩選
            filtered_candidates = await self.satellite_filter.apply_comprehensive_filter(
                filtered_satellite_data, orbital_positions
            )
        
        # 從全量軌道位置中提取候選衛星的軌道數據
        candidate_orbital_positions = {}
        candidate_satellites = []
        for candidates in filtered_candidates.values():
            candidate_satellites.extend(candidates)
        
        self.logger.info(f"📊 篩選結果: {len(candidate_satellites)}顆候選衛星")
        
        # 提取候選衛星的軌道位置數據
        missing_orbital_data = []
        for candidate in candidate_satellites:
            satellite_id = candidate.satellite_id
            if satellite_id in orbital_positions:
                candidate_orbital_positions[satellite_id] = orbital_positions[satellite_id]
            else:
                missing_orbital_data.append(satellite_id)
        
        if missing_orbital_data:
            self.logger.warning(f"⚠️ {len(missing_orbital_data)}顆候選衛星缺少軌道數據: {missing_orbital_data[:5]}...")
        
        # 輸出調試信息
        self.logger.info(f"🔍 調試信息：")
        self.logger.info(f"   候選衛星數量: {len(candidate_satellites)}")
        self.logger.info(f"   有軌道數據的候選: {len(candidate_orbital_positions)}")
        if candidate_orbital_positions:
            sample_sat = list(candidate_orbital_positions.keys())[0]
            sample_positions = candidate_orbital_positions[sample_sat]
            self.logger.info(f"   樣本衛星 {sample_sat}: {len(sample_positions)}個位置點")
            if sample_positions:
                self.logger.info(f"   樣本位置: 仰角{sample_positions[0].elevation_deg:.1f}°")
        
        # 導出Stage 2結果 - F2使用臨時目錄 (1.1GB大文件)，改為有意義的檔名
        filtering_output = self.temp_output_dir / "satellite_filtering_and_candidate_selection_results.json"
        await self._export_stage2_enhanced_results(filtered_candidates, candidate_orbital_positions, str(filtering_output))
        
        total_candidates = sum(len(candidates) for candidates in filtered_candidates.values())
        self.logger.info(f"📊 Stage 2統計: 篩選出{total_candidates}顆候選衛星")
        
        return filtered_candidates, candidate_orbital_positions

    async def _export_stage2_enhanced_results(self, 
                                        filtered_candidates: dict, 
                                        orbital_positions: dict, 
                                        output_path: str):
        """導出Stage 2增強結果，包含軌道位置數據"""
        try:
            export_data = {
                'filter_statistics': {
                    'input_satellites': len(self.tle_loader.tle_database) if hasattr(self, 'tle_loader') else 0,
                    'final_candidates': sum(len(candidates) for candidates in filtered_candidates.values()),
                    'starlink_candidates': len(filtered_candidates.get('starlink', [])),
                    'oneweb_candidates': len(filtered_candidates.get('oneweb', [])),
                    'geographic_filtered': 0,
                    'constellation_filtered': 0,
                    'filter_stages': {}
                },
                'filter_timestamp': datetime.now(timezone.utc).isoformat(),
                'observer_coordinates': {
                    'latitude': 24.9441667,
                    'longitude': 121.3713889,
                    'location_name': 'NTPU'
                },
                'candidates': {},
                'orbital_positions': {}  # 新增：軌道位置數據
            }
            
            # 導出候選衛星詳細信息
            for constellation, candidates in filtered_candidates.items():
                export_data['candidates'][constellation] = []
                
                for candidate in candidates:
                    candidate_data = {
                        'satellite_id': candidate.satellite_id,
                        'total_score': round(candidate.total_score, 2),
                        'geographic_relevance_score': round(candidate.geographic_relevance_score, 2),
                        'orbital_characteristics_score': round(candidate.orbital_characteristics_score, 2),
                        'signal_quality_score': round(candidate.signal_quality_score, 2),
                        'temporal_distribution_score': round(candidate.temporal_distribution_score, 2),
                        'scoring_rationale': candidate.scoring_rationale,
                        'is_selected': candidate.is_selected
                    }
                    
                    # ✅ 新增：導出可見性分析數據
                    if hasattr(candidate, 'visibility_analysis') and candidate.visibility_analysis:
                        va = candidate.visibility_analysis
                        candidate_data['visibility_analysis'] = {
                            'total_visible_time_minutes': round(va.total_visible_time_minutes, 2),
                            'max_elevation_deg': round(va.max_elevation_deg, 2),
                            'visible_passes_count': va.visible_passes_count,
                            'avg_pass_duration_minutes': round(va.avg_pass_duration_minutes, 2),
                            'signal_strength_estimate_dbm': round(va.signal_strength_estimate_dbm, 2)
                        }
                        if va.best_elevation_time:
                            candidate_data['visibility_analysis']['best_elevation_time'] = va.best_elevation_time.isoformat() if hasattr(va.best_elevation_time, 'isoformat') else str(va.best_elevation_time)
                    
                    export_data['candidates'][constellation].append(candidate_data)
            
            # 導出軌道位置數據
            for satellite_id, positions in orbital_positions.items():
                export_data['orbital_positions'][satellite_id] = []
                for position in positions:
                    export_data['orbital_positions'][satellite_id].append({
                        'timestamp': position.timestamp.isoformat(),
                        'latitude_deg': round(position.latitude_deg, 6),
                        'longitude_deg': round(position.longitude_deg, 6),
                        'altitude_km': round(position.altitude_km, 2),
                        'elevation_deg': round(position.elevation_deg, 2),
                        'azimuth_deg': round(position.azimuth_deg, 2),
                        'distance_km': round(position.distance_km, 2),
                        'velocity_km_s': round(position.velocity_km_s, 3)
                    })
            
            with open(output_path, 'w') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
                
            self.logger.info(f"📊 Stage 2增強結果已導出至: {output_path}")
            self.logger.info(f"   包含軌道位置數據: {len(orbital_positions)}顆衛星")
            
        except Exception as e:
            self.logger.error(f"❌ Stage 2增強結果導出失敗: {e}")
            import traceback
            traceback.print_exc()
    
    async def _execute_stage3_signal_analysis(self, filtered_candidates, orbital_positions):
        """執行Stage 3: 信號分析和事件檢測"""
        
        # 初始化事件處理器
        self.event_processor = A4A5D2EventProcessor(self.config.get('event_processor', {}))
        
        # ✅ 修復：從filtered_candidates和orbital_positions生成SatelliteSignalData時間軸
        self.logger.info("🔄 開始生成衛星信號數據時間軸...")
        serving_timeline, neighbor_timelines = await self._generate_signal_timelines(
            filtered_candidates, orbital_positions
        )
        
        self.logger.info(f"📊 時間軸生成完成:")
        self.logger.info(f"   服務衛星時間軸: {len(serving_timeline)}個時間點")
        self.logger.info(f"   鄰居衛星數量: {len(neighbor_timelines)}")
        
        # 檢測換手事件
        handover_events = await self.event_processor.process_handover_events(
            serving_timeline, neighbor_timelines, time_range_minutes=200
        )
        
        # 匯出Stage 3結果 - F3使用永久目錄，改為有意義的檔名
        handover_analysis_output = self.output_dir / "handover_event_analysis_results.json"
        await self.event_processor.export_event_analysis(handover_events, str(handover_analysis_output))
        
        self.logger.info(f"📊 Stage 3統計: 檢測{len(handover_events)}個換手事件")
        
        return handover_events
    
    async def _generate_signal_timelines(self, filtered_candidates, orbital_positions):
        """✅ 關鍵修復：生成SatelliteSignalData時間軸"""
        from signal_analyzer.threegpp_event_processor import SatelliteSignalData
        import math
        
        self.logger.info("🔄 開始orbital_positions→SatelliteSignalData轉換...")
        
        # 1. 選擇服務衛星（從Starlink中選擇評分最高的）
        starlink_candidates = filtered_candidates.get('starlink', [])
        if not starlink_candidates:
            self.logger.warning("⚠️ 沒有Starlink候選衛星，使用OneWeb")
            starlink_candidates = filtered_candidates.get('oneweb', [])
        
        if not starlink_candidates:
            self.logger.error("❌ 沒有候選衛星可用於信號分析")
            return [], []
        
        # 選擇總評分最高的衛星作為服務衛星
        serving_satellite = max(starlink_candidates, key=lambda s: s.total_score)
        serving_satellite_id = serving_satellite.satellite_id
        
        self.logger.info(f"📡 選擇服務衛星: {serving_satellite_id} (評分: {serving_satellite.total_score:.2f})")
        
        # 2. 獲取服務衛星的軌道位置數據
        if serving_satellite_id not in orbital_positions:
            self.logger.error(f"❌ 服務衛星 {serving_satellite_id} 缺少軌道數據")
            return [], []
        
        serving_orbital_data = orbital_positions[serving_satellite_id]
        self.logger.info(f"📊 服務衛星軌道數據: {len(serving_orbital_data)}個時間點")
        
        # 3. 生成服務衛星時間軸
        serving_timeline = []
        for position in serving_orbital_data:
            # 計算信號參數
            signal_data = await self._create_satellite_signal_data(
                serving_satellite, position, "starlink" if "starlink" in serving_satellite_id.lower() else "oneweb"
            )
            serving_timeline.append(signal_data)
        
        # 4. 選擇鄰居衛星（排除服務衛星，選擇前10個評分最高的）
        all_candidates = []
        for constellation_candidates in filtered_candidates.values():
            all_candidates.extend(constellation_candidates)
        
        # 排除服務衛星，按評分排序
        neighbor_candidates = [c for c in all_candidates if c.satellite_id != serving_satellite_id]
        neighbor_candidates.sort(key=lambda s: s.total_score, reverse=True)
        neighbor_candidates = neighbor_candidates[:10]  # 限制鄰居數量
        
        self.logger.info(f"👥 選擇鄰居衛星數量: {len(neighbor_candidates)}")
        
        # 5. 生成鄰居衛星時間軸
        neighbor_timelines = []
        for neighbor_candidate in neighbor_candidates:
            neighbor_id = neighbor_candidate.satellite_id
            
            if neighbor_id not in orbital_positions:
                self.logger.warning(f"⚠️ 鄰居衛星 {neighbor_id} 缺少軌道數據")
                continue
            
            neighbor_orbital_data = orbital_positions[neighbor_id]
            neighbor_timeline = []
            
            constellation = "starlink" if "starlink" in neighbor_id.lower() else "oneweb"
            
            for position in neighbor_orbital_data:
                signal_data = await self._create_satellite_signal_data(
                    neighbor_candidate, position, constellation
                )
                neighbor_timeline.append(signal_data)
            
            neighbor_timelines.append(neighbor_timeline)
        
        self.logger.info(f"✅ 時間軸生成完成:")
        self.logger.info(f"   服務衛星時間軸: {len(serving_timeline)}個時間點")
        self.logger.info(f"   鄰居衛星數量: {len(neighbor_timelines)}")
        
        return serving_timeline, neighbor_timelines
    
    async def _create_satellite_signal_data(self, satellite_candidate, orbital_position, constellation):
        """創建SatelliteSignalData對象"""
        from signal_analyzer.threegpp_event_processor import SatelliteSignalData
        import math
        
        # 基本位置信息
        satellite_id = satellite_candidate.satellite_id
        timestamp = orbital_position.timestamp
        latitude = orbital_position.latitude_deg
        longitude = orbital_position.longitude_deg
        altitude_km = orbital_position.altitude_km
        elevation_deg = orbital_position.elevation_deg
        azimuth_deg = orbital_position.azimuth_deg
        distance_km = orbital_position.distance_km
        
        # 創建臨時SatelliteSignalData用於RSRP計算
        temp_signal_data = SatelliteSignalData(
            satellite_id=satellite_id,
            constellation=constellation,
            timestamp=timestamp,
            latitude=latitude,
            longitude=longitude,
            altitude_km=altitude_km,
            elevation_deg=elevation_deg,
            azimuth_deg=azimuth_deg,
            distance_km=distance_km,
            rsrp_dbm=0.0,  # 臨時值
            rsrq_db=0.0,   # 臨時值
            sinr_db=0.0,   # 臨時值
            path_loss_db=0.0,  # 臨時值
            doppler_shift_hz=0.0,  # 臨時值
            propagation_delay_ms=0.0   # 臨時值
        )
        
        # 使用事件處理器計算精確RSRP
        rsrp_dbm = await self.event_processor.calculate_precise_rsrp(temp_signal_data)
        
        # 計算其他信號參數
        # RSRQ: 基於仰角動態調整
        rsrq_db = -12.0 + (elevation_deg - 10) * 0.1  # -12dB基準，仰角越高越好
        
        # SINR: 基於仰角和距離
        sinr_db = 18.0 + (elevation_deg - 10) * 0.2 - (distance_km - 550) / 100  # 18dB基準
        
        # 自由空間路徑損耗
        frequency_ghz = 12.0 if constellation == "starlink" else 20.0  # Ku/Ka頻段
        path_loss_db = 20 * math.log10(distance_km) + 20 * math.log10(frequency_ghz) + 32.45
        
        # 多普勒頻移 (簡化計算)
        velocity_km_s = getattr(orbital_position, 'velocity_km_s', 7.8)  # LEO衛星典型速度
        doppler_shift_hz = frequency_ghz * 1e9 * velocity_km_s * 1000 / 299792458  # c = 光速
        
        # 傳播延遲
        propagation_delay_ms = distance_km / 299.792458  # 光速 km/ms
        
        # 創建完整的SatelliteSignalData
        signal_data = SatelliteSignalData(
            satellite_id=satellite_id,
            constellation=constellation,
            timestamp=timestamp,
            latitude=latitude,
            longitude=longitude,
            altitude_km=altitude_km,
            elevation_deg=elevation_deg,
            azimuth_deg=azimuth_deg,
            distance_km=distance_km,
            rsrp_dbm=rsrp_dbm,
            rsrq_db=rsrq_db,
            sinr_db=sinr_db,
            path_loss_db=path_loss_db,
            doppler_shift_hz=doppler_shift_hz,
            propagation_delay_ms=propagation_delay_ms
        )
        
        return signal_data
    
    async def _execute_stage4_pool_optimization(self, filtered_candidates, orbital_positions):
        """執行Stage 4: 動態池最佳化"""
        
        # 初始化最佳化器
        self.optimizer = SimulatedAnnealingOptimizer(self.config.get('optimizer', {}))
        
        # 準備候選數據
        starlink_candidates = filtered_candidates.get('starlink', [])
        oneweb_candidates = filtered_candidates.get('oneweb', [])
        
        # 執行模擬退火最佳化
        optimal_solution = await self.optimizer.optimize_satellite_pools(
            starlink_candidates, oneweb_candidates, orbital_positions
        )
        
        # 匯出Stage 4結果 - A1使用永久目錄，改為有意義的檔名
        pool_optimization_output = self.output_dir / "dynamic_satellite_pool_optimization_results.json"
        await self.optimizer.export_optimization_results(optimal_solution, str(pool_optimization_output))
        
        self.logger.info(f"📊 Stage 4統計: 最佳解包含{optimal_solution.get_total_satellites()}顆衛星")
        self.logger.info(f"   Starlink: {len(optimal_solution.starlink_satellites)}顆")
        self.logger.info(f"   OneWeb: {len(optimal_solution.oneweb_satellites)}顆")
        self.logger.info(f"   可見性合規: {optimal_solution.visibility_compliance:.1%}")
        
        return optimal_solution
    
    def _serialize_pipeline_stats(self):
        """序列化pipeline統計中的datetime對象為JSON兼容格式"""
        import numpy as np
        
        def serialize_value(value):
            """遞歸序列化各種數據類型"""
            if isinstance(value, datetime):
                return value.isoformat()
            elif isinstance(value, (np.bool_, bool)):
                return bool(value)  # 確保numpy boolean轉為Python boolean
            elif isinstance(value, (np.integer, np.int64, np.int32)):
                return int(value)  # 確保numpy整數轉為Python int
            elif isinstance(value, (np.floating, np.float64, np.float32)):
                return float(value)  # 確保numpy浮點數轉為Python float
            elif isinstance(value, dict):
                return {k: serialize_value(v) for k, v in value.items()}
            elif isinstance(value, (list, tuple)):
                return [serialize_value(item) for item in value]
            elif hasattr(value, 'tolist'):  # numpy arrays
                return value.tolist()
            else:
                return value
        
        serialized = {}
        for key, value in self.pipeline_stats.items():
            serialized[key] = serialize_value(value)
        return serialized
    
    def _generate_final_report(self, optimal_pools):
        """生成完整的執行報告"""
        
        # 🔧 修復：使用datetime一致性時間計算
        current_time = datetime.now(timezone.utc)
        total_duration = (current_time - self.pipeline_stats['start_time']).total_seconds()
        
        final_report = {
            "leo_optimization_completion_report": {
                "timestamp": current_time.isoformat(),
                "pipeline_statistics": {
                    "start_time": self.pipeline_stats['start_time'].isoformat(),
                    "end_time": None,  # 會在最後設定
                    "total_duration_seconds": 0,  # 會在最後計算
                    "stages_completed": self.pipeline_stats['stages_completed'],
                    "total_stages": self.pipeline_stats['total_stages'],
                    "stage_durations": self.pipeline_stats['stage_durations'],
                    "final_results": {}  # 向後兼容
                },
                "final_results": {
                    "optimal_satellite_pools": {
                        "starlink_count": len(optimal_pools.starlink_satellites),
                        "oneweb_count": len(optimal_pools.oneweb_satellites), 
                        "total_count": optimal_pools.get_total_satellites(),
                        "visibility_compliance": float(optimal_pools.visibility_compliance),
                        "temporal_distribution": float(optimal_pools.temporal_distribution),
                        "signal_quality": float(optimal_pools.signal_quality)
                    },
                    "handover_events": {
                        "total_events": len(self.pipeline_stats.get('handover_events', [])),
                        "a4_events": len([e for e in self.pipeline_stats.get('handover_events', []) if e.event_type == 'A4']),
                        "a5_events": len([e for e in self.pipeline_stats.get('handover_events', []) if e.event_type == 'A5']),
                        "d2_events": len([e for e in self.pipeline_stats.get('handover_events', []) if e.event_type == 'D2'])
                    },
                    "compliance_check": {
                        "starlink_target_met": 10 <= len(optimal_pools.starlink_satellites) <= 100,
                        "oneweb_target_met": 3 <= len(optimal_pools.oneweb_satellites) <= 50,
                        "visibility_compliance_ok": optimal_pools.visibility_compliance >= 0.70,
                        "temporal_distribution_ok": optimal_pools.temporal_distribution >= 0.50,
                        "frontend_ready": True
                    }
                }
            }
        }
        
        # 設定最終時間和持續時間
        final_report["leo_optimization_completion_report"]["pipeline_statistics"]["end_time"] = current_time.isoformat()
        final_report["leo_optimization_completion_report"]["pipeline_statistics"]["total_duration_seconds"] = total_duration
        
        # 儲存報告 - 使用新的功能描述性檔名
        final_report_path = self.output_dir / "leo_optimization_final_report.json"
        
        with open(final_report_path, 'w') as f:
            json.dump(final_report, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"📋 最終報告已生成: {final_report_path}")
        
        # 檢查目標達成狀況
        unmet_targets = []
        if not final_report["leo_optimization_completion_report"]["final_results"]["compliance_check"]["starlink_target_met"]:
            unmet_targets.append('starlink_pool_size_ok')
        if not final_report["leo_optimization_completion_report"]["final_results"]["compliance_check"]["oneweb_target_met"]:
            unmet_targets.append('oneweb_pool_size_ok')
        if not final_report["leo_optimization_completion_report"]["final_results"]["compliance_check"]["visibility_compliance_ok"]:
            unmet_targets.append('visibility_compliance_ok')
        if not final_report["leo_optimization_completion_report"]["final_results"]["compliance_check"]["temporal_distribution_ok"]:
            unmet_targets.append('temporal_distribution_ok')
        
        # 🔧 修復：添加signal_quality約束檢查
        signal_quality_ok = optimal_pools.signal_quality >= 0.50  # 假設信號品質閾值
        if not signal_quality_ok:
            unmet_targets.append('signal_quality_ok')
            
        if unmet_targets:
            self.logger.warning(f"⚠️ 未滿足的約束: {unmet_targets}")
        
        return final_report

def create_default_config():
    """創建預設配置"""
    return {
        'tle_loader': {
            'data_sources': {
                'starlink_tle_url': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=starlink',
                'oneweb_tle_url': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=oneweb'
            },
            'calculation_params': {
                'time_range_minutes': 200,
                'time_resolution_seconds': 30
            }
        },
        'satellite_filter': {
            # 🔥 移除預設sample_limits - 讓全量模式成為預設行為
            # sample_limits只在開發模式中明確添加
            'filtering_params': {
                'geographic_threshold': 60.0,
                'min_score_threshold': 70.0
            },
            'ntpu_coordinates': {
                'latitude': 24.9441667,
                'longitude': 121.3713889
            }
        },
        'event_processor': {
            'event_thresholds': {
                'a4_neighbor_threshold_dbm': -100.0,
                'a5_serving_threshold_dbm': -110.0,
                'd2_serving_distance_km': 5000.0
            },
            'signal_params': {
                'frequency_ghz': 12.0,
                'tx_power_dbm': 43.0
            }
        },
        'optimizer': {
            'optimization_params': {
                'max_iterations': 5000,
                'initial_temperature': 1000.0,
                'cooling_rate': 0.95
            },
            'targets': {
                'starlink_pool_size': 8085,  # ✅ 基於本地TLE數據實際值
                'oneweb_pool_size': 651,   # ✅ 基於本地TLE數據實際值
                'starlink_visible_range': (10, 15),
                'oneweb_visible_range': (3, 6)
            }
        }
    }

async def main():
    """Phase 1主管道執行入口"""
    
    print("🛰️ LEO衛星動態池規劃系統 - Phase 1執行器")
    print("=" * 60)
    
    # 創建配置
    config = create_default_config()
    
    # 初始化管道
    pipeline = LEOCorePipeline(config)
    
    try:
        # 執行完整管道
        optimal_pools = await pipeline.execute_complete_pipeline()
        
        print("\n🎉 Phase 1執行成功!")
        print(f"📊 最佳化結果:")
        print(f"   Starlink池: {len(optimal_pools.starlink_satellites)}顆")
        print(f"   OneWeb池: {len(optimal_pools.oneweb_satellites)}顆")
        print(f"   可見性合規: {optimal_pools.visibility_compliance:.1%}")
        print(f"   輸出目錄: {pipeline.output_dir}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Phase 1執行失敗: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())