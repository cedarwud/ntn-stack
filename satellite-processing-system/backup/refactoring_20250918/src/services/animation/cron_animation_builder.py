#!/usr/bin/env python3
"""
Pure Cron動畫建構器

支援Pure Cron驅動架構的動畫數據建構器，
為前端提供60 FPS流暢動畫數據。

實現架構：
- CronAnimationBuilder: 核心動畫建構器
- 衛星軌跡建構 (build_satellite_tracks)
- 信號時間線建構 (build_signal_timelines)
- 換手序列建構 (build_handover_sequences)

符合文檔: @satellite-processing-system/docs/stages/stage4-timeseries.md
"""

import logging
import numpy as np
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Tuple
import json
from pathlib import Path

class CronAnimationBuilder:
    """
    Pure Cron動畫建構器
    
    根據階段四文檔規範實現：
    - 定時觸發：每6小時自動更新
    - 無依賴啟動：容器啟動時數據立即可用
    - 增量更新：僅在TLE變更時重新計算
    
    前端動畫需求：
    - 時間軸控制：支援1x-60x倍速播放
    - 衛星軌跡：平滑的軌道動畫路徑  
    - 信號變化：即時信號強度視覺化
    - 換手事件：動態換手決策展示
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化動畫建構器
        
        Args:
            config: 建構器配置參數
        """
        self.logger = logging.getLogger(f"{__name__}.CronAnimationBuilder")
        
        # 配置處理
        self.config = config or {}
        
        # 動畫參數配置
        self.animation_config = {
            "target_fps": 60,                    # 60 FPS目標幀率
            "time_resolution_sec": 30,           # 30秒時間解析度
            "orbital_period_min": 96,            # 96分鐘軌道週期
            "total_frames": 192,                 # 總幀數 (96*60/30)
            "smooth_interpolation": True,        # 平滑插值
            "track_precision": 3                 # 軌跡座標精度
        }
        
        # Pure Cron架構配置
        self.cron_config = {
            "update_interval_hours": 6,          # 6小時更新間隔
            "incremental_update": True,          # 增量更新
            "cache_enabled": True,               # 快取啟用
            "startup_data_ready": True           # 啟動時數據就緒
        }
        
        # 處理統計
        self.build_stats = {
            "tracks_built": 0,
            "timelines_built": 0,
            "sequences_built": 0,
            "build_time_seconds": 0.0
        }
        
        self.logger.info("✅ CronAnimationBuilder 初始化完成")
        self.logger.info(f"   目標FPS: {self.animation_config['target_fps']}")
        self.logger.info(f"   總幀數: {self.animation_config['total_frames']}")
    
    def build_satellite_tracks(self, timeseries_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        建構衛星軌跡數據
        
        為前端動畫提供平滑的軌道路徑數據，支援：
        - 60 FPS流暢渲染
        - 1x-60x倍速播放控制
        - 軌跡平滑插值
        - 可見性狀態追蹤
        
        Args:
            timeseries_data: 時間序列數據
            
        Returns:
            Dict[str, Any]: 軌跡建構結果
        """
        self.logger.info("🛰️ 建構衛星軌跡數據...")
        start_time = datetime.now(timezone.utc)
        
        try:
            built_tracks = {}
            total_satellites = 0
            
            # 處理各星座軌跡
            for constellation, data in timeseries_data.items():
                if constellation == "metadata":
                    continue
                    
                satellites = data.get("satellites", [])
                self.logger.info(f"處理 {constellation} 星座軌跡: {len(satellites)} 顆衛星")
                
                constellation_tracks = self._build_constellation_tracks(
                    constellation, satellites
                )
                built_tracks[constellation] = constellation_tracks
                total_satellites += len(satellites)
            
            # 計算統計
            end_time = datetime.now(timezone.utc)
            build_duration = (end_time - start_time).total_seconds()
            self.build_stats["tracks_built"] = total_satellites
            self.build_stats["build_time_seconds"] += build_duration
            
            result = {
                "metadata": {
                    "component": "satellite_tracks",
                    "total_satellites": total_satellites,
                    "total_frames": self.animation_config["total_frames"],
                    "target_fps": self.animation_config["target_fps"],
                    "build_timestamp": end_time.isoformat(),
                    "build_duration_seconds": build_duration,
                    "smooth_interpolation_enabled": self.animation_config["smooth_interpolation"]
                },
                "tracks": built_tracks
            }
            
            self.logger.info(f"✅ 軌跡建構完成: {total_satellites} 顆衛星, {build_duration:.2f}秒")
            return result
            
        except Exception as e:
            self.logger.error(f"軌跡建構失敗: {e}")
            raise RuntimeError(f"衛星軌跡建構失敗: {e}")
    
    def build_signal_timelines(self, timeseries_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        建構信號時間線數據
        
        為前端提供即時信號強度視覺化數據：
        - RSRP信號強度變化
        - 視覺化顏色映射
        - 信號品質等級
        - 時間同步標記
        
        Args:
            timeseries_data: 時間序列數據
            
        Returns:
            Dict[str, Any]: 信號時間線結果
        """
        self.logger.info("📡 建構信號時間線數據...")
        start_time = datetime.now(timezone.utc)
        
        try:
            built_timelines = {}
            total_timelines = 0
            
            # 處理各星座信號時間線
            for constellation, data in timeseries_data.items():
                if constellation == "metadata":
                    continue
                    
                satellites = data.get("satellites", [])
                self.logger.info(f"處理 {constellation} 星座信號: {len(satellites)} 條時間線")
                
                constellation_timelines = self._build_constellation_signal_timelines(
                    constellation, satellites
                )
                built_timelines[constellation] = constellation_timelines
                total_timelines += len(satellites)
            
            # 計算統計
            end_time = datetime.now(timezone.utc)
            build_duration = (end_time - start_time).total_seconds()
            self.build_stats["timelines_built"] = total_timelines
            self.build_stats["build_time_seconds"] += build_duration
            
            result = {
                "metadata": {
                    "component": "signal_timelines",
                    "total_timelines": total_timelines,
                    "total_frames": self.animation_config["total_frames"],
                    "signal_unit": "dBm",
                    "build_timestamp": end_time.isoformat(),
                    "build_duration_seconds": build_duration,
                    "quality_levels": ["excellent", "good", "fair", "poor"]
                },
                "timelines": built_timelines
            }
            
            self.logger.info(f"✅ 信號時間線建構完成: {total_timelines} 條時間線, {build_duration:.2f}秒")
            return result
            
        except Exception as e:
            self.logger.error(f"信號時間線建構失敗: {e}")
            raise RuntimeError(f"信號時間線建構失敗: {e}")
    
    def build_handover_sequences(self, timeseries_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        建構換手序列數據
        
        為前端提供動態換手決策展示：
        - 換手觸發事件
        - 候選衛星追蹤
        - 決策過程視覺化
        - 換手成功率統計
        
        Args:
            timeseries_data: 時間序列數據
            
        Returns:
            Dict[str, Any]: 換手序列結果
        """
        self.logger.info("🔄 建構換手序列數據...")
        start_time = datetime.now(timezone.utc)
        
        try:
            built_sequences = {}
            total_sequences = 0
            
            # 處理各星座換手序列
            for constellation, data in timeseries_data.items():
                if constellation == "metadata":
                    continue
                    
                satellites = data.get("satellites", [])
                self.logger.info(f"處理 {constellation} 星座換手: {len(satellites)} 顆衛星")
                
                constellation_sequences = self._build_constellation_handover_sequences(
                    constellation, satellites
                )
                built_sequences[constellation] = constellation_sequences
                total_sequences += len(constellation_sequences.get("sequences", []))
            
            # 計算統計
            end_time = datetime.now(timezone.utc)
            build_duration = (end_time - start_time).total_seconds()
            self.build_stats["sequences_built"] = total_sequences
            self.build_stats["build_time_seconds"] += build_duration
            
            result = {
                "metadata": {
                    "component": "handover_sequences",
                    "total_sequences": total_sequences,
                    "total_frames": self.animation_config["total_frames"],
                    "build_timestamp": end_time.isoformat(),
                    "build_duration_seconds": build_duration,
                    "supported_events": ["A4", "A5", "D2"],
                    "handover_success_rate": self._calculate_handover_success_rate(built_sequences)
                },
                "sequences": built_sequences
            }
            
            self.logger.info(f"✅ 換手序列建構完成: {total_sequences} 個序列, {build_duration:.2f}秒")
            return result
            
        except Exception as e:
            self.logger.error(f"換手序列建構失敗: {e}")
            raise RuntimeError(f"換手序列建構失敗: {e}")
    
    def build_complete_animation_data(self, timeseries_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        建構完整動畫數據 (主要方法)
        
        整合軌跡、信號時間線和換手序列，
        生成前端動畫所需的完整數據結構。
        
        Args:
            timeseries_data: 完整時間序列數據
            
        Returns:
            Dict[str, Any]: 完整動畫數據
        """
        self.logger.info("🎬 建構完整動畫數據...")
        overall_start = datetime.now(timezone.utc)
        
        try:
            # Step 1: 建構衛星軌跡
            tracks_data = self.build_satellite_tracks(timeseries_data)
            
            # Step 2: 建構信號時間線
            timelines_data = self.build_signal_timelines(timeseries_data)
            
            # Step 3: 建構換手序列
            sequences_data = self.build_handover_sequences(timeseries_data)
            
            # 整合完整動畫數據
            overall_end = datetime.now(timezone.utc)
            total_duration = (overall_end - overall_start).total_seconds()
            
            complete_animation_data = {
                "metadata": {
                    "stage": "stage4_animation_build",
                    "component": "complete_animation_data",
                    "build_timestamp": overall_end.isoformat(),
                    "total_build_duration_seconds": total_duration,
                    "animation_fps": self.animation_config["target_fps"],
                    "total_frames": self.animation_config["total_frames"],
                    "orbital_period_min": self.animation_config["orbital_period_min"],
                    "cron_architecture": "pure_cron_driven",
                    "ready_for_frontend": True
                },
                "animation_components": {
                    "satellite_tracks": tracks_data,
                    "signal_timelines": timelines_data,
                    "handover_sequences": sequences_data
                },
                "build_statistics": self.build_stats
            }
            
            self.logger.info(f"✅ 完整動畫數據建構完成: 總時間 {total_duration:.2f}秒")
            return complete_animation_data
            
        except Exception as e:
            self.logger.error(f"完整動畫數據建構失敗: {e}")
            raise RuntimeError(f"動畫數據建構失敗: {e}")
    
    def get_build_statistics(self) -> Dict[str, Any]:
        """獲取建構統計信息"""
        return {
            "tracks_built": self.build_stats["tracks_built"],
            "timelines_built": self.build_stats["timelines_built"], 
            "sequences_built": self.build_stats["sequences_built"],
            "total_build_time_seconds": self.build_stats["build_time_seconds"],
            "average_build_time_per_satellite": (
                self.build_stats["build_time_seconds"] / max(1, self.build_stats["tracks_built"])
            )
        }
    
    # ==================== 私有方法 ====================
    
    def _build_constellation_tracks(self, constellation: str, satellites: List[Dict[str, Any]]) -> Dict[str, Any]:
        """建構星座軌跡數據"""
        constellation_tracks = {
            "constellation": constellation,
            "satellite_count": len(satellites),
            "tracks": []
        }
        
        for satellite in satellites:
            track_data = self._build_single_satellite_track(satellite)
            constellation_tracks["tracks"].append(track_data)
        
        return constellation_tracks
    
    def _build_single_satellite_track(self, satellite: Dict[str, Any]) -> Dict[str, Any]:
        """建構單顆衛星軌跡"""
        satellite_name = satellite.get("satellite_name", "unknown")
        track_points = satellite.get("track_points", [])
        
        # 為60 FPS動畫優化軌跡點
        optimized_track = self._optimize_track_for_animation(track_points)
        
        return {
            "satellite_name": satellite_name,
            "satellite_id": satellite.get("satellite_id", 0),
            "total_frames": len(optimized_track),
            "track_data": optimized_track,
            "animation_metadata": {
                "smooth_interpolated": True,
                "fps_optimized": True,
                "coordinate_precision": self.animation_config["track_precision"]
            }
        }
    
    def _optimize_track_for_animation(self, track_points: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """為動畫優化軌跡點"""
        if not track_points:
            return []
        
        optimized_track = []
        
        # 應用平滑插值演算法
        if self.animation_config["smooth_interpolation"]:
            optimized_track = self._apply_smooth_interpolation(track_points)
        else:
            optimized_track = track_points.copy()
        
        # 為每個點添加動畫元數據
        for i, point in enumerate(optimized_track):
            point["frame_number"] = i
            point["progress_ratio"] = i / max(1, len(optimized_track) - 1)
            point["animation_ready"] = True
        
        return optimized_track
    
    def _apply_smooth_interpolation(self, points: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """應用平滑插值演算法"""
        if len(points) < 3:
            return points
        
        smoothed_points = []
        
        for i, point in enumerate(points):
            # 基本平滑：使用相鄰點的平均值
            if i == 0 or i == len(points) - 1:
                smoothed_points.append(point.copy())
            else:
                prev_point = points[i-1]
                next_point = points[i+1]
                
                smoothed_point = point.copy()
                
                # 位置平滑
                if all(k in point for k in ["lat", "lon"]):
                    smoothed_point["lat"] = round(
                        (prev_point["lat"] + point["lat"] + next_point["lat"]) / 3,
                        self.animation_config["track_precision"]
                    )
                    smoothed_point["lon"] = round(
                        (prev_point["lon"] + point["lon"] + next_point["lon"]) / 3,
                        self.animation_config["track_precision"]
                    )
                
                # 仰角平滑
                if all(k in point for k in ["elevation_deg"]):
                    smoothed_point["elevation_deg"] = round(
                        (prev_point["elevation_deg"] + point["elevation_deg"] + next_point["elevation_deg"]) / 3,
                        1
                    )
                
                smoothed_points.append(smoothed_point)
        
        return smoothed_points
    
    def _build_constellation_signal_timelines(self, constellation: str, satellites: List[Dict[str, Any]]) -> Dict[str, Any]:
        """建構星座信號時間線"""
        constellation_timelines = {
            "constellation": constellation,
            "satellite_count": len(satellites),
            "timelines": []
        }
        
        for satellite in satellites:
            timeline_data = self._build_single_satellite_timeline(satellite)
            constellation_timelines["timelines"].append(timeline_data)
        
        return constellation_timelines
    
    def _build_single_satellite_timeline(self, satellite: Dict[str, Any]) -> Dict[str, Any]:
        """建構單顆衛星信號時間線"""
        satellite_name = satellite.get("satellite_name", "unknown")
        signal_timeline = satellite.get("signal_timeline", [])
        
        # 為視覺化增強信號數據
        enhanced_timeline = self._enhance_signal_for_visualization(signal_timeline)
        
        return {
            "satellite_name": satellite_name,
            "satellite_id": satellite.get("satellite_id", 0),
            "total_frames": len(enhanced_timeline),
            "signal_data": enhanced_timeline,
            "timeline_metadata": {
                "signal_unit": "dBm",
                "visualization_enhanced": True,
                "color_mapping_applied": True
            }
        }
    
    def _enhance_signal_for_visualization(self, signal_timeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """為視覺化增強信號數據"""
        enhanced_timeline = []
        
        for i, signal_point in enumerate(signal_timeline):
            enhanced_point = signal_point.copy()
            
            # 添加動畫幀編號
            enhanced_point["frame_number"] = i
            
            # 增強顏色映射
            rsrp_dbm = signal_point.get("rsrp_dbm", -120)
            enhanced_point["quality_level"] = self._get_signal_quality_level(rsrp_dbm)
            enhanced_point["animation_color"] = self._get_animation_color(rsrp_dbm)
            
            # 添加視覺化效果參數
            enhanced_point["opacity"] = max(0.3, min(1.0, (rsrp_dbm + 120) / 50))
            enhanced_point["scale"] = max(0.5, min(2.0, (rsrp_dbm + 90) / 40))
            
            enhanced_timeline.append(enhanced_point)
        
        return enhanced_timeline
    
    def _get_signal_quality_level(self, rsrp_dbm: float) -> str:
        """獲取信號品質等級"""
        if rsrp_dbm > -70:
            return "excellent"
        elif rsrp_dbm > -85:
            return "good" 
        elif rsrp_dbm > -100:
            return "fair"
        else:
            return "poor"
    
    def _get_animation_color(self, rsrp_dbm: float) -> str:
        """獲取動畫顏色"""
        if rsrp_dbm > -70:
            return "#00FF00"  # 綠色 - 優秀
        elif rsrp_dbm > -85:
            return "#FFFF00"  # 黃色 - 良好
        elif rsrp_dbm > -100:
            return "#FFA500"  # 橙色 - 一般
        else:
            return "#FF0000"  # 紅色 - 較差
    
    def _build_constellation_handover_sequences(self, constellation: str, satellites: List[Dict[str, Any]]) -> Dict[str, Any]:
        """建構星座換手序列"""
        constellation_sequences = {
            "constellation": constellation,
            "satellite_count": len(satellites),
            "sequences": []
        }
        
        # 分析衛星間的換手機會
        handover_sequences = self._analyze_handover_opportunities(satellites)
        constellation_sequences["sequences"] = handover_sequences
        
        return constellation_sequences
    
    def _analyze_handover_opportunities(self, satellites: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """分析換手機會"""
        sequences = []
        
        # 簡化的換手分析 - 基於仰角變化檢測換手時機
        for i, satellite in enumerate(satellites):
            track_points = satellite.get("track_points", [])
            
            if len(track_points) < 10:
                continue
            
            # 檢測仰角峰值 (可能的換手時機)
            elevation_changes = self._detect_elevation_peaks(track_points)
            
            if elevation_changes:
                handover_sequence = {
                    "source_satellite": satellite.get("satellite_name", "unknown"),
                    "source_satellite_id": satellite.get("satellite_id", 0),
                    "handover_events": elevation_changes,
                    "total_handovers": len(elevation_changes),
                    "success_probability": self._calculate_handover_success_probability(elevation_changes)
                }
                sequences.append(handover_sequence)
        
        return sequences
    
    def _detect_elevation_peaks(self, track_points: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """檢測仰角峰值"""
        peaks = []
        
        if len(track_points) < 3:
            return peaks
        
        for i in range(1, len(track_points) - 1):
            prev_elev = track_points[i-1].get("elevation_deg", 0)
            curr_elev = track_points[i].get("elevation_deg", 0)
            next_elev = track_points[i+1].get("elevation_deg", 0)
            
            # 檢測局部最大值 (峰值)
            if curr_elev > prev_elev and curr_elev > next_elev and curr_elev > 30:
                peak_event = {
                    "frame_number": i,
                    "time": track_points[i].get("time", 0),
                    "peak_elevation_deg": curr_elev,
                    "handover_type": "elevation_based",
                    "recommended": curr_elev > 45
                }
                peaks.append(peak_event)
        
        return peaks
    
    def _calculate_handover_success_probability(self, handover_events: List[Dict[str, Any]]) -> float:
        """計算換手成功機率"""
        if not handover_events:
            return 0.0
        
        # 基於仰角計算成功機率
        high_elevation_events = sum(1 for event in handover_events 
                                  if event.get("peak_elevation_deg", 0) > 45)
        
        return min(0.95, high_elevation_events / len(handover_events) * 0.8 + 0.2)
    
    def _calculate_handover_success_rate(self, sequences_data: Dict[str, Any]) -> float:
        """計算整體換手成功率"""
        total_probability = 0.0
        total_sequences = 0
        
        for constellation_data in sequences_data.values():
            sequences = constellation_data.get("sequences", [])
            for sequence in sequences:
                total_probability += sequence.get("success_probability", 0.0)
                total_sequences += 1
        
        return total_probability / max(1, total_sequences)