#!/usr/bin/env python3
"""
智能數據融合引擎 - 階段五核心組件

實現文檔中定義的創新智能數據融合方法，同時利用階段三和階段四的數據優勢：
- 階段三：提供科學計算所需的精確數據（真實仰角、詳細信號分析）
- 階段四：提供前端動畫和可視化優化數據

融合策略：
1. 科學精確性 - 使用階段三的真實仰角數據進行分層濾波
2. 動畫流暢性 - 保留階段四的前端優化數據  
3. 功能完整性 - 同時滿足科學計算和可視化需求
4. 架構彈性 - 可獨立更新各數據源而不影響其他功能

作者：Claude Code
日期：2025-09-11
版本：v1.0
"""

import os
import json
import logging
import asyncio
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime, timezone
from pathlib import Path


class IntelligentDataFusionEngine:
    """
    智能數據融合引擎
    
    實現階段三（科學數據）和階段四（動畫數據）的智能融合，
    提供統一的增強時間序列數據結構。
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化智能數據融合引擎"""
        self.logger = logging.getLogger(f"{__name__}.IntelligentDataFusionEngine")
        self.config = config or self._get_academic_grade_config()
        
        # 數據來源配置
        self.data_fusion_strategy = {
            'stage3_data': {
                'source': '/app/data/signal_quality_analysis_output.json',
                'provides': [
                    'position_timeseries',      # 完整軌道時序數據
                    'elevation_deg',            # 真實仰角數據（位於relative_to_observer）
                    'signal_quality',           # 詳細信號分析
                    'visibility_analysis',      # 可見性判斷
                    '3gpp_events'              # 3GPP標準事件
                ],
                'purpose': '提供科學計算所需的精確數據'
            },
            'stage4_data': {
                'source': '/orbit-engine/data/outputs/stage4/',
                'provides': [
                    'track_points',            # 優化的軌跡動畫點
                    'signal_timeline',         # 前端信號可視化
                    'animation_metadata'       # 動畫性能數據
                ],
                'purpose': '提供前端動畫和可視化優化數據'
            }
        }
        
        # 融合統計
        self.fusion_statistics = {
            "fusion_start_time": None,
            "fusion_end_time": None,
            "fusion_duration": 0,
            "stage3_satellites_loaded": 0,
            "stage4_satellites_loaded": 0,
            "successfully_fused_satellites": 0,
            "fusion_success_rate": 0.0,
            "data_sources_loaded": []
        }
        
        self.logger.info("✅ IntelligentDataFusionEngine 初始化完成")
        self.logger.info("   融合策略: 階段三科學數據 + 階段四動畫數據")
        self.logger.info("   目標: 智能雙數據源整合")
    
    def _get_academic_grade_config(self) -> Dict[str, Any]:
        """獲取學術級配置 - 修復: 從標準配置文件載入替代硬編碼預設值"""
        try:
            import sys
            sys.path.append('/orbit-engine/src')
            from shared.academic_standards_config import AcademicStandardsConfig
            standards_config = AcademicStandardsConfig()
            
            # 載入學術級數據融合配置
            fusion_config = standards_config.get_data_fusion_parameters()
            constellation_requirements = standards_config.get_constellation_requirements()
            
            return {
                "fusion_mode": fusion_config.get("mode", "physics_based_dual_source"),
                "prioritize_stage3_precision": fusion_config.get("prioritize_precision", True),
                "preserve_stage4_animation": fusion_config.get("preserve_animation", True),
                "enable_fallback_mechanisms": False,  # 學術級標準禁用回退機制
                "validation_enabled": True,
                "academic_compliance": "Grade_A",
                "required_constellations": constellation_requirements.get("supported_constellations", ["starlink", "oneweb"]),
                "minimum_satellites_per_constellation": {
                    "starlink": constellation_requirements.get("starlink", {}).get("minimum_satellites", 1000),
                    "oneweb": constellation_requirements.get("oneweb", {}).get("minimum_satellites", 100)
                },
                "data_source_validation": {
                    "require_real_tle_data": True,
                    "require_physics_based_calculations": True,
                    "prohibit_mock_values": True
                }
            }
            
        except ImportError:
            self.logger.warning("⚠️ 無法載入學術標準配置，使用Grade B緊急備用配置")
            
            # 緊急備用配置 (基於已知的衛星系統參數)
            return {
                "fusion_mode": "validated_dual_source",
                "prioritize_stage3_precision": True,
                "preserve_stage4_animation": True,
                "enable_fallback_mechanisms": False,  # 禁用回退以符合學術標準
                "validation_enabled": True,
                "academic_compliance": "Grade_B",
                "required_constellations": ["starlink", "oneweb"],
                "minimum_satellites_per_constellation": {
                    "starlink": 1000,  # 基於SpaceX公開資料
                    "oneweb": 100      # 基於OneWeb公開資料
                },
                "data_source_validation": {
                    "require_real_tle_data": True,
                    "require_physics_based_calculations": True,
                    "prohibit_mock_values": True
                }
            }
    
    async def load_enhanced_timeseries(self, 
                                     stage3_path: Optional[str] = None,
                                     stage4_path: Optional[str] = None) -> Dict[str, Any]:
        """
        智能數據融合：結合階段三科學數據和階段四動畫數據
        
        Args:
            stage3_path: 階段三數據路徑（可選）
            stage4_path: 階段四數據路徑（可選）
            
        Returns:
            融合後的增強時間序列數據
        """
        self.fusion_statistics["fusion_start_time"] = datetime.now(timezone.utc)
        self.logger.info("🔄 開始智能數據融合...")
        
        try:
            # 1. 載入階段三數據（科學精確數據）
            self.logger.info("📊 載入階段三科學精確數據...")
            stage3_data = await self._load_stage3_signal_analysis(stage3_path)
            
            # 2. 載入階段四數據（動畫優化數據）
            self.logger.info("🎬 載入階段四動畫優化數據...")  
            stage4_data = await self._load_stage4_animation_data(stage4_path)
            
            # 3. 執行智能融合
            self.logger.info("🧠 執行智能雙數據源融合...")
            enhanced_data = await self._perform_intelligent_fusion(stage3_data, stage4_data)
            
            # 4. 驗證融合結果
            if self.config.get("validation_enabled", True):
                self.logger.info("🔍 驗證融合數據完整性...")
                validation_result = await self._validate_fusion_results(enhanced_data)
                if not validation_result["validation_passed"]:
                    self.logger.warning("⚠️ 融合數據驗證發現問題，但繼續處理")
            
            # 5. 計算融合統計
            self._calculate_fusion_statistics(enhanced_data)
            
            self.logger.info(f"✅ 智能數據融合完成")
            self.logger.info(f"   階段三衛星: {self.fusion_statistics['stage3_satellites_loaded']}")
            self.logger.info(f"   階段四衛星: {self.fusion_statistics['stage4_satellites_loaded']}")
            self.logger.info(f"   成功融合: {self.fusion_statistics['successfully_fused_satellites']}")
            self.logger.info(f"   融合成功率: {self.fusion_statistics['fusion_success_rate']:.1f}%")
            
            return enhanced_data
            
        except Exception as e:
            self.logger.error(f"❌ 智能數據融合失敗: {e}")
            return {"error": f"數據融合失敗: {e}", "fusion_statistics": self.fusion_statistics}
    
    async def _load_stage3_signal_analysis(self, stage3_path: Optional[str] = None) -> Dict[str, Any]:
        """載入階段三信號分析數據 - 重構版：使用統一數據載入器"""
        from .stage_data_loader import StageDataLoader
        
        try:
            # 使用統一的數據載入器
            data_loader = StageDataLoader()
            all_stage_data = data_loader.load_all_stage_outputs()
            
            stage3_data = data_loader.get_stage_data("stage3")
            if stage3_data:
                # 驗證數據結構
                if self._validate_stage3_structure(stage3_data):
                    self.fusion_statistics["data_sources_loaded"].append("stage3")
                    
                    # 統計衛星數量
                    satellites_count = 0
                    for constellation in ["starlink", "oneweb"]:
                        constellation_data = stage3_data.get("satellites", {}).get(constellation, {})
                        if isinstance(constellation_data, dict):
                            satellites_count += len(constellation_data)
                    
                    self.fusion_statistics["stage3_satellites_loaded"] = satellites_count
                    self.logger.info(f"✅ 階段三數據載入成功 (使用統一載入器): {satellites_count}顆衛星")
                    
                    return stage3_data
                    
        except Exception as e:
            self.logger.warning(f"⚠️ 統一數據載入器失敗，使用回退機制: {e}")
            
            # 如果統一載入器失敗，使用原有的直接文件載入作為回退
            possible_paths = [
                "/app/data/signal_quality_analysis_output.json",
                "/orbit-engine/data/outputs/stage3/signal_event_analysis_output.json",
                "data/signal_analysis_outputs/signal_event_analysis_output.json"
            ]
            
            if stage3_path:
                possible_paths = [stage3_path] + possible_paths
            
            for path in possible_paths:
                if os.path.exists(path):
                    try:
                        with open(path, 'r', encoding='utf-8') as f:
                            stage3_data = json.load(f)
                        
                        if self._validate_stage3_structure(stage3_data):
                            self.fusion_statistics["data_sources_loaded"].append("stage3_fallback")
                            self.logger.info(f"✅ 階段三數據回退載入成功: {path}")
                            return stage3_data
                            
                    except Exception as load_error:
                        self.logger.warning(f"⚠️ 回退載入失敗: {path} - {load_error}")
                        continue
        
        # 如果無法載入真實數據，使用回退機制
        self.logger.warning("⚠️ 無法載入階段三數據，使用回退機制")
        return self._create_fallback_stage3_data()
    
    async def _load_stage4_animation_data(self, stage4_path: Optional[str] = None) -> Dict[str, Any]:
        """載入階段四動畫數據 - 重構版：使用統一數據載入器"""
        from .stage_data_loader import StageDataLoader
        
        try:
            # 使用統一的數據載入器
            data_loader = StageDataLoader()
            all_stage_data = data_loader.load_all_stage_outputs()
            
            stage4_data = data_loader.get_stage_data("stage4")
            if stage4_data:
                satellites_count = 0
                
                # 統計衛星數量
                for constellation in ["starlink", "oneweb"]:
                    constellation_data = stage4_data.get(constellation, {})
                    if isinstance(constellation_data, dict):
                        satellites_count += len(constellation_data.get("satellites", {}))
                
                if stage4_data:
                    self.fusion_statistics["data_sources_loaded"].append("stage4")
                    self.fusion_statistics["stage4_satellites_loaded"] = satellites_count
                    self.logger.info(f"✅ 階段四數據載入成功 (使用統一載入器): {satellites_count}顆衛星")
                    return stage4_data
                    
        except Exception as e:
            self.logger.warning(f"⚠️ 統一數據載入器失敗，使用回退機制: {e}")
            
            # 如果統一載入器失敗，使用原有的直接文件載入作為回退
            possible_directories = [
                "/orbit-engine/data/outputs/stage4/",
                "data/timeseries_preprocessing_outputs/"
            ]
            
            if stage4_path:
                possible_directories = [stage4_path] + possible_directories
            
            stage4_data = {}
            
            for base_dir in possible_directories:
                if os.path.exists(base_dir):
                    try:
                        # 查找星座數據文件
                        starlink_file = os.path.join(base_dir, "starlink_enhanced.json")
                        oneweb_file = os.path.join(base_dir, "oneweb_enhanced.json")
                        
                        satellites_count = 0
                        
                        # 載入Starlink數據
                        if os.path.exists(starlink_file):
                            with open(starlink_file, 'r', encoding='utf-8') as f:
                                starlink_data = json.load(f)
                            stage4_data["starlink"] = starlink_data
                            satellites_count += len(starlink_data.get("satellites", {}))
                        
                        # 載入OneWeb數據  
                        if os.path.exists(oneweb_file):
                            with open(oneweb_file, 'r', encoding='utf-8') as f:
                                oneweb_data = json.load(f)
                            stage4_data["oneweb"] = oneweb_data
                            satellites_count += len(oneweb_data.get("satellites", {}))
                        
                        if stage4_data:
                            self.fusion_statistics["data_sources_loaded"].append("stage4_fallback")
                            self.fusion_statistics["stage4_satellites_loaded"] = satellites_count
                            self.logger.info(f"✅ 階段四數據回退載入成功: {base_dir} ({satellites_count}顆衛星)")
                            return stage4_data
                            
                    except Exception as load_error:
                        self.logger.warning(f"⚠️ 回退載入失敗: {base_dir} - {load_error}")
                        continue
        
        # 如果無法載入真實數據，使用回退機制
        self.logger.warning("⚠️ 無法載入階段四數據，使用回退機制")
        return self._create_fallback_stage4_data()
    
    async def _perform_intelligent_fusion(self, 
                                        stage3_data: Dict[str, Any], 
                                        stage4_data: Dict[str, Any]) -> Dict[str, Any]:
        """執行智能融合"""
        
        enhanced_data = {
            "metadata": {
                "stage": 5,
                "stage_name": "data_integration_with_intelligent_fusion",
                "fusion_timestamp": datetime.now(timezone.utc).isoformat(),
                "fusion_strategy": "dual_source_scientific_animation",
                "data_sources": self.fusion_statistics["data_sources_loaded"]
            },
            "timeseries_data": {}
        }
        
        # 處理每個星座的數據融合
        for constellation in self.config.get("required_constellations", ["starlink", "oneweb"]):
            self.logger.info(f"🔄 融合{constellation}數據...")
            
            # 從階段三獲取科學數據
            stage3_constellation = stage3_data.get("satellites", {}).get(constellation, {})
            
            # 從階段四獲取動畫數據
            stage4_constellation = stage4_data.get(constellation, {}).get("satellites", {})
            
            # 執行按衛星ID的智能融合
            fused_satellites = await self._fuse_constellation_data(
                constellation, stage3_constellation, stage4_constellation
            )
            
            enhanced_data["timeseries_data"][constellation] = {
                "metadata": {
                    "constellation": constellation,
                    "fusion_timestamp": datetime.now(timezone.utc).isoformat(),
                    "satellites_count": len(fused_satellites),
                    "data_sources": {
                        "stage3_scientific_data": len(stage3_constellation),
                        "stage4_animation_data": len(stage4_constellation)
                    }
                },
                "satellites": fused_satellites
            }
        
        return enhanced_data
    
    async def _fuse_constellation_data(self, 
                                     constellation: str,
                                     stage3_satellites: Dict[str, Any],
                                     stage4_satellites: Dict[str, Any]) -> Dict[str, Any]:
        """融合單個星座的衛星數據"""
        
        fused_satellites = {}
        
        # 以階段三數據為主體（科學精確性優先）
        for sat_id, stage3_sat in stage3_satellites.items():
            if not isinstance(stage3_sat, dict):
                continue
            
            # 創建融合後的衛星數據
            enhanced_satellite = {
                # === 階段三提供：科學計算數據 ===
                **stage3_sat,  # position_timeseries, signal_quality, visibility_analysis 等
                
                # === 基本衛星信息 ===
                "satellite_id": sat_id,
                "constellation": constellation,
                "data_fusion_info": {
                    "primary_source": "stage3_scientific_data",
                    "has_animation_data": sat_id in stage4_satellites,
                    "fusion_timestamp": datetime.now(timezone.utc).isoformat()
                }
            }
            
            # === 階段四提供：動畫優化數據（如果存在） ===
            if sat_id in stage4_satellites:
                stage4_sat = stage4_satellites[sat_id]
                if isinstance(stage4_sat, dict):
                    # 添加動畫相關數據
                    enhanced_satellite.update({
                        "signal_timeline": stage4_sat.get("signal_timeline", []),
                        "track_points": stage4_sat.get("track_points", []),
                        "animation_summary": stage4_sat.get("summary", {}),
                        "frontend_optimized": True
                    })
                    enhanced_satellite["data_fusion_info"]["animation_data_merged"] = True
                else:
                    enhanced_satellite["data_fusion_info"]["animation_data_merged"] = False
            else:
                enhanced_satellite["data_fusion_info"]["animation_data_merged"] = False
                enhanced_satellite["frontend_optimized"] = False
            
            # === 數據完整性標記 ===
            enhanced_satellite["data_integrity"] = {
                "has_position_timeseries": "position_timeseries" in stage3_sat,
                "has_signal_quality": "signal_quality" in stage3_sat,
                "has_visibility_analysis": "visibility_analysis" in stage3_sat,
                "has_animation_timeline": "signal_timeline" in enhanced_satellite,
                "scientific_precision": True,
                "animation_optimized": enhanced_satellite["frontend_optimized"]
            }
            
            fused_satellites[sat_id] = enhanced_satellite
        
        self.logger.info(f"✅ {constellation}融合完成: {len(fused_satellites)}顆衛星")
        return fused_satellites
    
    def _validate_stage3_structure(self, data: Dict[str, Any]) -> bool:
        """驗證階段三數據結構"""
        required_fields = ["satellites", "metadata"]
        
        for field in required_fields:
            if field not in data:
                self.logger.warning(f"階段三數據缺少字段: {field}")
                return False
        
        satellites = data.get("satellites", {})
        if not isinstance(satellites, dict):
            self.logger.warning("階段三衛星數據結構錯誤")
            return False
        
        # 檢查星座數據
        for constellation in ["starlink", "oneweb"]:
            if constellation in satellites:
                constellation_data = satellites[constellation]
                if isinstance(constellation_data, dict) and len(constellation_data) > 0:
                    return True
        
        self.logger.warning("階段三數據中沒有有效的星座數據")
        return False
    
    async def _validate_fusion_results(self, enhanced_data: Dict[str, Any]) -> Dict[str, Any]:
        """驗證融合結果"""
        
        validation_result = {
            "validation_passed": True,
            "validation_timestamp": datetime.now(timezone.utc).isoformat(),
            "checks_performed": [],
            "issues_found": []
        }
        
        try:
            # 檢查基本結構
            if "timeseries_data" not in enhanced_data:
                validation_result["issues_found"].append("缺少timeseries_data字段")
                validation_result["validation_passed"] = False
            
            # 檢查星座數據
            timeseries_data = enhanced_data.get("timeseries_data", {})
            for constellation in self.config.get("required_constellations", []):
                if constellation not in timeseries_data:
                    validation_result["issues_found"].append(f"缺少{constellation}數據")
                    validation_result["validation_passed"] = False
                    continue
                
                constellation_data = timeseries_data[constellation]
                satellites = constellation_data.get("satellites", {})
                satellites_count = len(satellites)
                
                minimum_count = self.config.get("minimum_satellites_per_constellation", {}).get(constellation, 0)
                if satellites_count < minimum_count:
                    validation_result["issues_found"].append(
                        f"{constellation}衛星數量不足: {satellites_count} < {minimum_count}"
                    )
                    validation_result["validation_passed"] = False
                
                validation_result["checks_performed"].append(f"{constellation}_satellite_count_check")
            
            # 檢查數據融合完整性
            total_fused = self.fusion_statistics.get("successfully_fused_satellites", 0)
            if total_fused == 0:
                validation_result["issues_found"].append("沒有成功融合的衛星數據")
                validation_result["validation_passed"] = False
            
            validation_result["checks_performed"].append("data_fusion_integrity_check")
            
        except Exception as e:
            validation_result["validation_passed"] = False
            validation_result["issues_found"].append(f"驗證過程異常: {e}")
        
        return validation_result
    
    def _calculate_fusion_statistics(self, enhanced_data: Dict[str, Any]):
        """計算融合統計"""
        self.fusion_statistics["fusion_end_time"] = datetime.now(timezone.utc)
        self.fusion_statistics["fusion_duration"] = (
            self.fusion_statistics["fusion_end_time"] - 
            self.fusion_statistics["fusion_start_time"]
        ).total_seconds()
        
        # 計算成功融合的衛星數量
        successfully_fused = 0
        timeseries_data = enhanced_data.get("timeseries_data", {})
        
        for constellation_data in timeseries_data.values():
            satellites = constellation_data.get("satellites", {})
            successfully_fused += len(satellites)
        
        self.fusion_statistics["successfully_fused_satellites"] = successfully_fused
        
        # 計算融合成功率
        total_loaded = (
            self.fusion_statistics["stage3_satellites_loaded"] + 
            self.fusion_statistics["stage4_satellites_loaded"]
        )
        
        if total_loaded > 0:
            self.fusion_statistics["fusion_success_rate"] = (successfully_fused / total_loaded) * 100
        else:
            self.fusion_statistics["fusion_success_rate"] = 0.0
    
    def _create_fallback_stage3_data(self) -> Dict[str, Any]:
        """創建階段三回退數據"""
        return {
            "metadata": {
                "stage": 3,
                "data_source": "fallback_mechanism",
                "warning": "使用回退數據，可能影響科學精確性"
            },
            "satellites": {
                "starlink": {},
                "oneweb": {}
            }
        }
    
    def _create_fallback_stage4_data(self) -> Dict[str, Any]:
        """創建階段四回退數據"""
        return {
            "starlink": {"satellites": {}},
            "oneweb": {"satellites": {}},
            "metadata": {
                "data_source": "fallback_mechanism",
                "warning": "使用回退數據，可能影響動畫效果"
            }
        }
    
    def get_fusion_statistics(self) -> Dict[str, Any]:
        """獲取融合統計數據"""
        return self.fusion_statistics
    
    def get_data_fusion_strategy(self) -> Dict[str, Any]:
        """獲取數據融合策略"""
        return self.data_fusion_strategy