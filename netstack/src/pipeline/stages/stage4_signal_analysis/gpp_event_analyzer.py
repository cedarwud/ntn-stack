"""
3GPP事件分析器 - Stage 4模組化組件

職責：
1. 執行3GPP NTN標準事件分析
2. 識別A4/A5測量事件
3. 分析D2距離事件
4. 生成換手觸發建議
"""

import math
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class GPPEventAnalyzer:
    """3GPP事件分析器 - 基於3GPP NTN標準進行事件分析"""
    
    def __init__(self):
        """初始化3GPP事件分析器"""
        self.logger = logging.getLogger(f"{__name__}.GPPEventAnalyzer")
        
        # 3GPP NTN事件門檻 (基於標準文獻)
        self.event_thresholds = {
            # A4事件: 服務小區品質低於門檻
            "A4": {
                "threshold_dbm": -106.0,  # RSRP門檻
                "hysteresis_db": 2.0,     # 滯後
                "time_to_trigger_ms": 160 # 觸發時間
            },
            
            # A5事件: 服務小區品質低於門檻1且鄰區品質高於門檻2
            "A5": {
                "threshold1_dbm": -106.0,  # 服務小區門檻
                "threshold2_dbm": -106.0,  # 鄰區門檻
                "hysteresis_db": 2.0,      # 滯後
                "time_to_trigger_ms": 160  # 觸發時間
            },
            
            # D2事件: 距離變化
            "D2": {
                "distance_threshold_km": 1500.0,  # 距離門檻 (1500km)
                "min_distance_km": 1200.0,        # 最小距離 (1200km)
                "hysteresis_km": 50.0,            # 距離滯後
                "time_to_trigger_ms": 320          # 觸發時間
            }
        }
        
        # 分析統計
        self.analysis_statistics = {
            "satellites_analyzed": 0,
            "a4_events_detected": 0,
            "a5_events_detected": 0,
            "d2_events_detected": 0,
            "handover_candidates_identified": 0
        }
        
        self.logger.info("✅ 3GPP事件分析器初始化完成")
        self.logger.info(f"   A4門檻: {self.event_thresholds['A4']['threshold_dbm']} dBm")
        self.logger.info(f"   A5門檻: {self.event_thresholds['A5']['threshold1_dbm']} / {self.event_thresholds['A5']['threshold2_dbm']} dBm")
        self.logger.info(f"   D2距離門檻: {self.event_thresholds['D2']['distance_threshold_km']} km")
    
    def analyze_3gpp_events(self, signal_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        執行3GPP事件分析
        
        Args:
            signal_results: 信號品質計算結果
            
        Returns:
            包含3GPP事件分析結果的字典
        """
        self.logger.info("📊 開始3GPP NTN事件分析...")
        
        satellites = signal_results.get("satellites", [])
        
        event_results = {
            "satellites": [],
            "event_summary": {
                "total_satellites": len(satellites),
                "a4_events": 0,
                "a5_events": 0,
                "d2_events": 0,
                "handover_candidates": []
            },
            "constellation_events": {}
        }
        
        constellation_events = {}
        
        for satellite_signal in satellites:
            self.analysis_statistics["satellites_analyzed"] += 1
            
            try:
                satellite_events = self._analyze_single_satellite_events(satellite_signal)
                event_results["satellites"].append(satellite_events)
                
                # 統計事件
                a4_count = len(satellite_events["events"].get("A4", []))
                a5_count = len(satellite_events["events"].get("A5", []))
                d2_count = len(satellite_events["events"].get("D2", []))
                
                event_results["event_summary"]["a4_events"] += a4_count
                event_results["event_summary"]["a5_events"] += a5_count
                event_results["event_summary"]["d2_events"] += d2_count
                
                self.analysis_statistics["a4_events_detected"] += a4_count
                self.analysis_statistics["a5_events_detected"] += a5_count
                self.analysis_statistics["d2_events_detected"] += d2_count
                
                # 識別換手候選
                if satellite_events["handover_suitability"]["is_handover_candidate"]:
                    event_results["event_summary"]["handover_candidates"].append({
                        "satellite_id": satellite_events["satellite_id"],
                        "constellation": satellite_events["constellation"],
                        "suitability_score": satellite_events["handover_suitability"]["suitability_score"]
                    })
                    self.analysis_statistics["handover_candidates_identified"] += 1
                
                # 統計星座事件
                constellation = satellite_events["constellation"]
                if constellation not in constellation_events:
                    constellation_events[constellation] = {
                        "satellite_count": 0,
                        "total_a4_events": 0,
                        "total_a5_events": 0,
                        "total_d2_events": 0,
                        "handover_candidates": 0
                    }
                
                const_stats = constellation_events[constellation]
                const_stats["satellite_count"] += 1
                const_stats["total_a4_events"] += a4_count
                const_stats["total_a5_events"] += a5_count
                const_stats["total_d2_events"] += d2_count
                
                if satellite_events["handover_suitability"]["is_handover_candidate"]:
                    const_stats["handover_candidates"] += 1
                
            except Exception as e:
                self.logger.warning(f"衛星 {satellite_signal.get('satellite_id', 'unknown')} 事件分析失敗: {e}")
                continue
        
        event_results["constellation_events"] = constellation_events
        
        self.logger.info(f"✅ 3GPP事件分析完成:")
        self.logger.info(f"   A4事件: {event_results['event_summary']['a4_events']} 個")
        self.logger.info(f"   A5事件: {event_results['event_summary']['a5_events']} 個")  
        self.logger.info(f"   D2事件: {event_results['event_summary']['d2_events']} 個")
        self.logger.info(f"   換手候選: {len(event_results['event_summary']['handover_candidates'])} 顆衛星")
        
        return event_results
    
    def _analyze_single_satellite_events(self, satellite_signal: Dict[str, Any]) -> Dict[str, Any]:
        """分析單顆衛星的3GPP事件"""
        satellite_id = satellite_signal.get("satellite_id")
        constellation = satellite_signal.get("constellation")
        signal_timeseries = satellite_signal.get("signal_timeseries", [])
        signal_metrics = satellite_signal.get("signal_metrics", {})
        
        # 分析各種事件
        a4_events = self._detect_a4_events(signal_timeseries)
        a5_events = self._detect_a5_events(signal_timeseries)
        d2_events = self._detect_d2_events(signal_timeseries)
        
        # 評估換手適用性
        handover_suitability = self._assess_handover_suitability(
            signal_timeseries, signal_metrics, a4_events, a5_events, d2_events
        )
        
        return {
            "satellite_id": satellite_id,
            "constellation": constellation,
            "events": {
                "A4": a4_events,
                "A5": a5_events,
                "D2": d2_events
            },
            "event_statistics": {
                "total_a4_events": len(a4_events),
                "total_a5_events": len(a5_events),
                "total_d2_events": len(d2_events),
                "event_density": self._calculate_event_density(a4_events + a5_events + d2_events, len(signal_timeseries))
            },
            "handover_suitability": handover_suitability
        }
    
    def _detect_a4_events(self, signal_timeseries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """檢測A4事件 - 服務小區品質低於門檻"""
        a4_events = []
        threshold = self.event_thresholds["A4"]["threshold_dbm"]
        hysteresis = self.event_thresholds["A4"]["hysteresis_db"]
        
        in_a4_state = False
        a4_start_time = None
        
        for point in signal_timeseries:
            rsrp = point.get("rsrp_dbm", -140)
            timestamp = point.get("timestamp")
            
            # 檢查是否觸發A4事件
            if not in_a4_state and rsrp < threshold:
                # 進入A4狀態
                in_a4_state = True
                a4_start_time = timestamp
                
            elif in_a4_state and rsrp > (threshold + hysteresis):
                # 退出A4狀態
                if a4_start_time:
                    a4_events.append({
                        "event_type": "A4",
                        "start_time": a4_start_time,
                        "end_time": timestamp,
                        "trigger_rsrp_dbm": rsrp,
                        "threshold_dbm": threshold,
                        "duration_seconds": self._calculate_duration_seconds(a4_start_time, timestamp)
                    })
                
                in_a4_state = False
                a4_start_time = None
        
        # 處理未結束的A4事件
        if in_a4_state and a4_start_time:
            last_point = signal_timeseries[-1] if signal_timeseries else {}
            a4_events.append({
                "event_type": "A4", 
                "start_time": a4_start_time,
                "end_time": last_point.get("timestamp", a4_start_time),
                "trigger_rsrp_dbm": last_point.get("rsrp_dbm", -140),
                "threshold_dbm": threshold,
                "duration_seconds": self._calculate_duration_seconds(a4_start_time, last_point.get("timestamp", a4_start_time))
            })
        
        return a4_events
    
    def _detect_a5_events(self, signal_timeseries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """檢測A5事件 - 服務小區品質低於門檻且鄰區品質高於門檻"""
        # 簡化實現：基於信號品質變化檢測潛在的A5事件
        a5_events = []
        threshold1 = self.event_thresholds["A5"]["threshold1_dbm"]
        threshold2 = self.event_thresholds["A5"]["threshold2_dbm"]
        
        for i, point in enumerate(signal_timeseries):
            rsrp = point.get("rsrp_dbm", -140)
            timestamp = point.get("timestamp")
            elevation = point.get("elevation_deg", 0)
            
            # A5事件觸發條件：當前信號低於threshold1且仰角合理(表示可能有更好的鄰區)
            if rsrp < threshold1 and elevation > 15:  # 仰角>15度表示有好的幾何條件
                # 檢查是否有信號改善趨勢 (鄰區可能更好)
                if i < len(signal_timeseries) - 3:
                    future_rsrp = [signal_timeseries[j].get("rsrp_dbm", -140) for j in range(i+1, min(i+4, len(signal_timeseries)))]
                    avg_future_rsrp = sum(future_rsrp) / len(future_rsrp)
                    
                    if avg_future_rsrp > threshold2:  # 未來信號改善，可能有更好鄰區
                        a5_events.append({
                            "event_type": "A5",
                            "timestamp": timestamp,
                            "serving_rsrp_dbm": rsrp,
                            "threshold1_dbm": threshold1,
                            "threshold2_dbm": threshold2,
                            "elevation_deg": elevation,
                            "predicted_neighbor_rsrp_dbm": avg_future_rsrp
                        })
        
        return a5_events
    
    def _detect_d2_events(self, signal_timeseries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """檢測D2事件 - 距離變化超過門檻"""
        d2_events = []
        distance_threshold = self.event_thresholds["D2"]["distance_threshold_km"]
        min_distance = self.event_thresholds["D2"]["min_distance_km"]
        hysteresis = self.event_thresholds["D2"]["hysteresis_km"]
        
        prev_range = None
        
        for point in signal_timeseries:
            current_range = point.get("range_km", 0)
            timestamp = point.get("timestamp")
            
            if prev_range is not None:
                distance_change = abs(current_range - prev_range)
                
                # 檢查是否超過距離門檻
                if distance_change > distance_threshold:
                    d2_events.append({
                        "event_type": "D2",
                        "timestamp": timestamp,
                        "previous_range_km": prev_range,
                        "current_range_km": current_range,
                        "distance_change_km": distance_change,
                        "threshold_km": distance_threshold,
                        "exceeds_threshold": True
                    })
                
                # 檢查是否低於最小距離
                elif current_range < min_distance:
                    d2_events.append({
                        "event_type": "D2",
                        "timestamp": timestamp,
                        "current_range_km": current_range,
                        "min_distance_km": min_distance,
                        "below_minimum": True
                    })
            
            prev_range = current_range
        
        return d2_events
    
    def _assess_handover_suitability(self, signal_timeseries: List[Dict[str, Any]], 
                                   signal_metrics: Dict[str, Any],
                                   a4_events: List[Dict[str, Any]],
                                   a5_events: List[Dict[str, Any]],
                                   d2_events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """評估衛星換手適用性"""
        
        # 基於多個因素計算適用性分數
        suitability_score = 100.0
        suitability_factors = []
        
        # 因素1: 平均信號強度 (40%)
        avg_rsrp = signal_metrics.get("average_rsrp_dbm", -140)
        if avg_rsrp >= -85:
            signal_score = 40.0
            suitability_factors.append("優秀信號強度")
        elif avg_rsrp >= -95:
            signal_score = 32.0
            suitability_factors.append("良好信號強度")
        elif avg_rsrp >= -105:
            signal_score = 20.0
            suitability_factors.append("中等信號強度")
        else:
            signal_score = 5.0
            suitability_factors.append("信號強度不足")
        
        # 因素2: 信號穩定性 (25%)
        stability_score_raw = signal_metrics.get("signal_stability_score", 0)
        stability_score = (stability_score_raw / 100.0) * 25.0
        
        if stability_score_raw >= 80:
            suitability_factors.append("信號穩定")
        elif stability_score_raw >= 60:
            suitability_factors.append("信號較穩定")
        else:
            suitability_factors.append("信號不穩定")
        
        # 因素3: 事件頻率 (20%) - 事件越少越適合換手
        total_events = len(a4_events) + len(a5_events) + len(d2_events)
        total_points = len(signal_timeseries)
        
        if total_points > 0:
            event_rate = total_events / total_points
            if event_rate <= 0.1:
                event_score = 20.0
                suitability_factors.append("事件頻率低")
            elif event_rate <= 0.2:
                event_score = 15.0
                suitability_factors.append("事件頻率中等")
            else:
                event_score = 5.0
                suitability_factors.append("事件頻率高")
        else:
            event_score = 0.0
        
        # 因素4: 可見性 (15%)
        visible_points = signal_metrics.get("visible_points_count", 0)
        if total_points > 0:
            visibility_rate = visible_points / total_points
            visibility_score = visibility_rate * 15.0
            
            if visibility_rate >= 0.8:
                suitability_factors.append("高可見性")
            elif visibility_rate >= 0.5:
                suitability_factors.append("中等可見性")
            else:
                suitability_factors.append("低可見性")
        else:
            visibility_score = 0.0
        
        # 計算總分
        suitability_score = signal_score + stability_score + event_score + visibility_score
        
        # 判斷是否為換手候選
        is_handover_candidate = (
            suitability_score >= 60.0 and 
            avg_rsrp >= -105.0 and
            stability_score_raw >= 50.0
        )
        
        return {
            "is_handover_candidate": is_handover_candidate,
            "suitability_score": round(suitability_score, 2),
            "suitability_factors": suitability_factors,
            "detailed_scores": {
                "signal_strength_score": signal_score,
                "stability_score": stability_score,
                "event_frequency_score": event_score,
                "visibility_score": visibility_score
            }
        }
    
    def _calculate_event_density(self, events: List[Dict[str, Any]], total_points: int) -> float:
        """計算事件密度 (事件數/時間點數)"""
        if total_points == 0:
            return 0.0
        return len(events) / total_points
    
    def _calculate_duration_seconds(self, start_time: str, end_time: str) -> float:
        """計算時間間隔（秒）"""
        try:
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            return (end_dt - start_dt).total_seconds()
        except:
            return 0.0
    
    def generate_handover_recommendations(self, event_results: Dict[str, Any]) -> Dict[str, Any]:
        """生成換手建議"""
        handover_candidates = event_results.get("event_summary", {}).get("handover_candidates", [])
        
        # 按適用性分數排序
        sorted_candidates = sorted(
            handover_candidates, 
            key=lambda x: x.get("suitability_score", 0), 
            reverse=True
        )
        
        # 生成建議
        recommendations = {
            "top_handover_candidates": sorted_candidates[:10],  # 前10名
            "constellation_recommendations": {},
            "handover_strategy": self._generate_handover_strategy(sorted_candidates)
        }
        
        # 按星座分組建議
        constellation_groups = {}
        for candidate in sorted_candidates:
            constellation = candidate.get("constellation", "unknown")
            if constellation not in constellation_groups:
                constellation_groups[constellation] = []
            constellation_groups[constellation].append(candidate)
        
        for constellation, candidates in constellation_groups.items():
            recommendations["constellation_recommendations"][constellation] = {
                "candidate_count": len(candidates),
                "top_candidate": candidates[0] if candidates else None,
                "average_suitability": sum(c.get("suitability_score", 0) for c in candidates) / len(candidates) if candidates else 0
            }
        
        return recommendations
    
    def _generate_handover_strategy(self, candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成換手策略"""
        if not candidates:
            return {"strategy": "no_handover", "reason": "無合適換手候選"}
        
        top_candidate = candidates[0]
        top_score = top_candidate.get("suitability_score", 0)
        
        if top_score >= 80:
            strategy = "immediate_handover"
            reason = "發現高品質候選，建議立即換手"
        elif top_score >= 60:
            strategy = "conditional_handover"
            reason = "發現合適候選，建議在信號衰減時換手"
        else:
            strategy = "monitor_only"
            reason = "候選品質不足，僅監控"
        
        return {
            "strategy": strategy,
            "reason": reason,
            "primary_candidate": top_candidate,
            "backup_candidates": candidates[1:4]  # 備選方案
        }
    
    def get_analysis_statistics(self) -> Dict[str, Any]:
        """獲取分析統計信息"""
        return self.analysis_statistics.copy()