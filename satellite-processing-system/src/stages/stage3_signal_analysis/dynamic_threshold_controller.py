"""
動態門檻調整系統 - Stage 4模組化組件

職責：
1. 根據網路狀況動態調整A4/A5/D2門檻
2. 基於歷史性能數據優化門檻值
3. 實現自適應門檻調整算法
4. 提供門檻調整的解釋和驗證
"""

import math
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone, timedelta
import json

logger = logging.getLogger(__name__)

class ThresholdAdjustmentReason:
    """門檻調整原因"""
    NETWORK_CONGESTION = "network_congestion"
    SIGNAL_DEGRADATION = "signal_degradation"
    HANDOVER_FAILURE = "handover_failure"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    SATELLITE_DENSITY = "satellite_density"
    WEATHER_CONDITIONS = "weather_conditions"

class DynamicThresholdController:
    """
    動態門檻調整系統
    
    基於3GPP標準和實際網路性能：
    - A4/A5/D2門檻的智能調整
    - 基於機器學習的最佳化
    - 自適應反饋控制
    """
    
    def __init__(self, config_file_path: str = None):
        """
        初始化動態門檻控制器
        
        Args:
            config_file_path: 配置文件路徑（可選）
        """
        self.logger = logging.getLogger(f"{__name__}.DynamicThresholdController")
        
        # 基準門檻值 (3GPP標準建議值)
        self.baseline_thresholds = {
            "A4": {
                "threshold_dbm": -106.0,    # 基準A4門檻
                "hysteresis_db": 2.0,       # 基準滯後
                "time_to_trigger_ms": 160,  # 基準觸發時間
                "valid_range": (-120, -80)  # 有效調整範圍
            },
            "A5": {
                "threshold1_dbm": -110.0,   # 服務小區基準門檻
                "threshold2_dbm": -106.0,   # 鄰區基準門檻
                "hysteresis_db": 2.0,       # 基準滯後
                "time_to_trigger_ms": 160,  # 基準觸發時間
                "valid_range": (-125, -75)  # 有效調整範圍
            },
            "D2": {
                "distance_threshold1_m": 1500000,  # 基準距離門檻1 (1500km)
                "distance_threshold2_m": 1200000,  # 基準距離門檻2 (1200km)
                "hysteresis_m": 50000,             # 基準距離滯後 (50km)
                "time_to_trigger_ms": 320,         # 基準觸發時間
                "valid_range": (800000, 2500000)   # 有效調整範圍 (800-2500km)
            }
        }
        
        # 當前動態門檻值 (初始化為基準值)
        self.current_thresholds = json.loads(json.dumps(self.baseline_thresholds))
        
        # 調整參數
        self.adjustment_parameters = {
            "max_adjustment_step": 3.0,     # 單次最大調整步長 (dB)
            "min_adjustment_interval": 300,  # 最小調整間隔 (秒)
            "adjustment_momentum": 0.8,     # 調整動量 (0-1)
            "stability_weight": 0.3,        # 穩定性權重
            "performance_weight": 0.7       # 性能權重
        }
        
        # 網路狀態監控
        self.network_conditions = {
            "satellite_density": 1.0,       # 衛星密度係數
            "average_signal_quality": 0.0,  # 平均信號品質
            "handover_success_rate": 1.0,   # 換手成功率
            "network_load": 0.5,            # 網路負載
            "weather_impact": 1.0           # 天氣影響係數
        }
        
        # 性能歷史記錄
        self.performance_history = []
        self.adjustment_history = []
        
        # 統計數據
        self.controller_statistics = {
            "total_adjustments": 0,
            "successful_adjustments": 0,
            "performance_improvements": 0,
            "current_performance_score": 0.0,
            "last_adjustment_time": None,
            "adjustment_effectiveness": 0.0
        }
        
        # 載入配置文件（如果提供）
        if config_file_path:
            self._load_configuration(config_file_path)
        
        self.logger.info("✅ 動態門檻控制器初始化完成")
        self.logger.info(f"   A4基準門檻: {self.current_thresholds['A4']['threshold_dbm']} dBm")
        self.logger.info(f"   A5基準門檻: {self.current_thresholds['A5']['threshold1_dbm']}/{self.current_thresholds['A5']['threshold2_dbm']} dBm")
        self.logger.info(f"   D2基準門檻: {self.current_thresholds['D2']['distance_threshold1_m']/1000:.0f}km")
    
    def update_network_conditions(self, signal_results: Dict[str, Any], 
                                event_results: Dict[str, Any],
                                handover_statistics: Dict[str, Any] = None) -> None:
        """
        更新網路狀況數據
        
        Args:
            signal_results: 信號分析結果
            event_results: 事件分析結果  
            handover_statistics: 換手統計數據（可選）
        """
        
        # 更新衛星密度
        total_satellites = len(signal_results.get("satellites", []))
        visible_satellites = sum(
            1 for sat in signal_results.get("satellites", [])
            if sat.get("signal_metrics", {}).get("visible_points_count", 0) > 0
        )
        self.network_conditions["satellite_density"] = visible_satellites / max(1, total_satellites)
        
        # 更新平均信號品質
        rsrp_values = []
        for sat in signal_results.get("satellites", []):
            rsrp = sat.get("signal_metrics", {}).get("average_rsrp_dbm")
            if rsrp and rsrp > -150:
                rsrp_values.append(rsrp)
        
        if rsrp_values:
            avg_rsrp = sum(rsrp_values) / len(rsrp_values)
            # 正規化到0-1 (-140 to -70 dBm)
            self.network_conditions["average_signal_quality"] = max(0, min(1, (avg_rsrp + 140) / 70))
        
        # 更新換手成功率（如果提供）
        if handover_statistics:
            success_rate = handover_statistics.get("success_rate", 1.0)
            self.network_conditions["handover_success_rate"] = success_rate
        
        # 估算網路負載（基於事件觸發頻率）
        total_events = sum(
            len(sat.get("events", {}).get(event_type, []))
            for sat in event_results.get("satellites", [])
            for event_type in ["A4", "A5", "D2"]
        )
        
        # 正規化網路負載
        expected_events = len(event_results.get("satellites", [])) * 0.1  # 預期每衛星0.1個事件
        self.network_conditions["network_load"] = min(1.0, total_events / max(1, expected_events))
        
        self.logger.debug(f"網路狀況更新: 密度={self.network_conditions['satellite_density']:.2f}, "
                         f"信號品質={self.network_conditions['average_signal_quality']:.2f}, "
                         f"負載={self.network_conditions['network_load']:.2f}")
    
    def evaluate_threshold_adjustment_need(self) -> Dict[str, Any]:
        """
        評估是否需要調整門檻
        
        Returns:
            調整需求評估結果
        """
        
        # 計算當前性能分數
        current_performance = self._calculate_performance_score()
        
        # 檢查調整時間間隔
        last_adjustment = self.controller_statistics.get("last_adjustment_time")
        if last_adjustment:
            time_since_last = (datetime.now(timezone.utc) - 
                             datetime.fromisoformat(last_adjustment.replace('Z', '+00:00'))).total_seconds()
            if time_since_last < self.adjustment_parameters["min_adjustment_interval"]:
                return {
                    "needs_adjustment": False,
                    "reason": "調整間隔未到",
                    "time_remaining": self.adjustment_parameters["min_adjustment_interval"] - time_since_last
                }
        
        # 評估調整需求
        adjustment_needs = {}
        
        # A4門檻調整需求
        a4_need = self._evaluate_a4_adjustment_need()
        if a4_need["needs_adjustment"]:
            adjustment_needs["A4"] = a4_need
        
        # A5門檻調整需求
        a5_need = self._evaluate_a5_adjustment_need()
        if a5_need["needs_adjustment"]:
            adjustment_needs["A5"] = a5_need
        
        # D2門檻調整需求
        d2_need = self._evaluate_d2_adjustment_need()
        if d2_need["needs_adjustment"]:
            adjustment_needs["D2"] = d2_need
        
        return {
            "needs_adjustment": len(adjustment_needs) > 0,
            "current_performance": current_performance,
            "adjustment_needs": adjustment_needs,
            "network_conditions": self.network_conditions.copy()
        }
    
    def adjust_thresholds(self, adjustment_needs: Dict[str, Any]) -> Dict[str, Any]:
        """
        執行門檻調整
        
        Args:
            adjustment_needs: 調整需求評估結果
            
        Returns:
            調整執行結果
        """
        
        if not adjustment_needs.get("needs_adjustment", False):
            return {"adjusted": False, "reason": "無調整需求"}
        
        self.logger.info("🔧 開始執行動態門檻調整...")
        
        adjustment_results = {}
        total_adjustments = 0
        
        # 執行各類型門檻調整
        for event_type, need_info in adjustment_needs.get("adjustment_needs", {}).items():
            
            if event_type == "A4":
                result = self._adjust_a4_threshold(need_info)
            elif event_type == "A5":
                result = self._adjust_a5_threshold(need_info)
            elif event_type == "D2":
                result = self._adjust_d2_threshold(need_info)
            else:
                continue
            
            adjustment_results[event_type] = result
            if result.get("adjusted", False):
                total_adjustments += 1
        
        # 記錄調整歷史
        adjustment_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "adjustments": adjustment_results,
            "network_conditions": self.network_conditions.copy(),
            "performance_before": adjustment_needs.get("current_performance", 0),
            "total_adjustments": total_adjustments
        }
        
        self.adjustment_history.append(adjustment_record)
        if len(self.adjustment_history) > 100:  # 保留最近100次調整
            self.adjustment_history.pop(0)
        
        # 更新統計
        self.controller_statistics["total_adjustments"] += total_adjustments
        self.controller_statistics["last_adjustment_time"] = datetime.now(timezone.utc).isoformat()
        
        self.logger.info(f"✅ 門檻調整完成: {total_adjustments} 個門檻已調整")
        
        return {
            "adjusted": total_adjustments > 0,
            "total_adjustments": total_adjustments,
            "adjustment_results": adjustment_results,
            "new_thresholds": self._get_current_thresholds_summary(),
            "adjustment_record": adjustment_record
        }
    
    def _calculate_performance_score(self) -> float:
        """計算當前性能分數 (0-100)"""
        
        # 基於網路狀況的性能評估
        signal_quality_score = self.network_conditions["average_signal_quality"] * 100
        handover_success_score = self.network_conditions["handover_success_rate"] * 100
        density_score = self.network_conditions["satellite_density"] * 100
        
        # 負載懲罰 (負載過高會降低性能分數)
        load_penalty = max(0, (self.network_conditions["network_load"] - 0.7) * 100)
        
        # 綜合性能分數
        performance_score = (
            signal_quality_score * 0.4 +
            handover_success_score * 0.3 +
            density_score * 0.2 -
            load_penalty * 0.1
        )
        
        return max(0, min(100, performance_score))
    
    def _evaluate_a4_adjustment_need(self) -> Dict[str, Any]:
        """評估A4門檻調整需求"""
        
        current_threshold = self.current_thresholds["A4"]["threshold_dbm"]
        baseline_threshold = self.baseline_thresholds["A4"]["threshold_dbm"]
        
        # 基於信號品質調整
        signal_quality = self.network_conditions["average_signal_quality"]
        
        if signal_quality < 0.3:  # 信號品質差
            # 放寬A4門檻，更容易觸發換手
            suggested_adjustment = -2.0  # 降低門檻
            reason = ThresholdAdjustmentReason.SIGNAL_DEGRADATION
        elif signal_quality > 0.8 and self.network_conditions["network_load"] > 0.7:
            # 信號品質好但負載高，提高門檻減少不必要換手
            suggested_adjustment = +1.5  # 提高門檻
            reason = ThresholdAdjustmentReason.NETWORK_CONGESTION
        else:
            return {"needs_adjustment": False}
        
        # 檢查調整範圍
        new_threshold = current_threshold + suggested_adjustment
        valid_range = self.baseline_thresholds["A4"]["valid_range"]
        
        if not (valid_range[0] <= new_threshold <= valid_range[1]):
            return {"needs_adjustment": False, "reason": "超出有效範圍"}
        
        return {
            "needs_adjustment": True,
            "current_value": current_threshold,
            "suggested_adjustment": suggested_adjustment,
            "new_value": new_threshold,
            "adjustment_reason": reason,
            "confidence": 0.8
        }
    
    def _evaluate_a5_adjustment_need(self) -> Dict[str, Any]:
        """評估A5門檻調整需求"""
        
        handover_success_rate = self.network_conditions["handover_success_rate"]
        
        # 基於換手成功率調整
        if handover_success_rate < 0.8:
            # 換手成功率低，調整門檻參數
            adjustment1 = -1.0  # 降低服務小區門檻
            adjustment2 = +1.0  # 提高鄰區門檻
            reason = ThresholdAdjustmentReason.HANDOVER_FAILURE
        elif handover_success_rate > 0.95 and self.network_conditions["network_load"] < 0.3:
            # 成功率很高且負載低，可以更積極換手
            adjustment1 = +1.0  # 提高服務小區門檻
            adjustment2 = -1.0  # 降低鄰區門檻  
            reason = ThresholdAdjustmentReason.PERFORMANCE_OPTIMIZATION
        else:
            return {"needs_adjustment": False}
        
        current_threshold1 = self.current_thresholds["A5"]["threshold1_dbm"]
        current_threshold2 = self.current_thresholds["A5"]["threshold2_dbm"]
        
        return {
            "needs_adjustment": True,
            "current_values": [current_threshold1, current_threshold2],
            "suggested_adjustments": [adjustment1, adjustment2],
            "new_values": [current_threshold1 + adjustment1, current_threshold2 + adjustment2],
            "adjustment_reason": reason,
            "confidence": 0.75
        }
    
    def _evaluate_d2_adjustment_need(self) -> Dict[str, Any]:
        """評估D2門檻調整需求"""
        
        satellite_density = self.network_conditions["satellite_density"]
        
        # 基於衛星密度調整距離門檻
        if satellite_density > 0.8:
            # 衛星密度高，可以使用更嚴格的距離門檻
            adjustment = -100000  # 降低距離門檻 (100km)
            reason = ThresholdAdjustmentReason.SATELLITE_DENSITY
        elif satellite_density < 0.3:
            # 衛星密度低，放寬距離門檻
            adjustment = +150000  # 提高距離門檻 (150km)
            reason = ThresholdAdjustmentReason.SATELLITE_DENSITY
        else:
            return {"needs_adjustment": False}
        
        current_threshold = self.current_thresholds["D2"]["distance_threshold1_m"]
        new_threshold = current_threshold + adjustment
        
        # 檢查有效範圍
        valid_range = self.baseline_thresholds["D2"]["valid_range"]
        if not (valid_range[0] <= new_threshold <= valid_range[1]):
            return {"needs_adjustment": False, "reason": "超出有效範圍"}
        
        return {
            "needs_adjustment": True,
            "current_value": current_threshold,
            "suggested_adjustment": adjustment,
            "new_value": new_threshold,
            "adjustment_reason": reason,
            "confidence": 0.7
        }
    
    def _adjust_a4_threshold(self, need_info: Dict[str, Any]) -> Dict[str, Any]:
        """執行A4門檻調整"""
        
        new_threshold = need_info["new_value"]
        
        # 應用動量調整
        momentum = self.adjustment_parameters["adjustment_momentum"]
        actual_adjustment = need_info["suggested_adjustment"] * momentum
        final_threshold = self.current_thresholds["A4"]["threshold_dbm"] + actual_adjustment
        
        # 更新門檻
        self.current_thresholds["A4"]["threshold_dbm"] = final_threshold
        
        self.logger.info(f"A4門檻調整: {need_info['current_value']:.1f} → {final_threshold:.1f} dBm "
                        f"(原因: {need_info['adjustment_reason']})")
        
        return {
            "adjusted": True,
            "event_type": "A4",
            "old_value": need_info["current_value"],
            "new_value": final_threshold,
            "adjustment_amount": actual_adjustment,
            "reason": need_info["adjustment_reason"]
        }
    
    def _adjust_a5_threshold(self, need_info: Dict[str, Any]) -> Dict[str, Any]:
        """執行A5門檻調整"""
        
        momentum = self.adjustment_parameters["adjustment_momentum"]
        
        # 調整兩個門檻
        old_threshold1 = self.current_thresholds["A5"]["threshold1_dbm"]
        old_threshold2 = self.current_thresholds["A5"]["threshold2_dbm"]
        
        adjustment1 = need_info["suggested_adjustments"][0] * momentum
        adjustment2 = need_info["suggested_adjustments"][1] * momentum
        
        new_threshold1 = old_threshold1 + adjustment1
        new_threshold2 = old_threshold2 + adjustment2
        
        self.current_thresholds["A5"]["threshold1_dbm"] = new_threshold1
        self.current_thresholds["A5"]["threshold2_dbm"] = new_threshold2
        
        self.logger.info(f"A5門檻調整: [{old_threshold1:.1f}, {old_threshold2:.1f}] → "
                        f"[{new_threshold1:.1f}, {new_threshold2:.1f}] dBm "
                        f"(原因: {need_info['adjustment_reason']})")
        
        return {
            "adjusted": True,
            "event_type": "A5",
            "old_values": [old_threshold1, old_threshold2],
            "new_values": [new_threshold1, new_threshold2],
            "adjustment_amounts": [adjustment1, adjustment2],
            "reason": need_info["adjustment_reason"]
        }
    
    def _adjust_d2_threshold(self, need_info: Dict[str, Any]) -> Dict[str, Any]:
        """執行D2門檻調整"""
        
        momentum = self.adjustment_parameters["adjustment_momentum"]
        actual_adjustment = need_info["suggested_adjustment"] * momentum
        
        old_threshold = self.current_thresholds["D2"]["distance_threshold1_m"]
        new_threshold = old_threshold + actual_adjustment
        
        self.current_thresholds["D2"]["distance_threshold1_m"] = new_threshold
        
        self.logger.info(f"D2門檻調整: {old_threshold/1000:.0f} → {new_threshold/1000:.0f} km "
                        f"(原因: {need_info['adjustment_reason']})")
        
        return {
            "adjusted": True,
            "event_type": "D2",
            "old_value": old_threshold,
            "new_value": new_threshold,
            "adjustment_amount": actual_adjustment,
            "reason": need_info["adjustment_reason"]
        }
    
    def get_current_thresholds(self) -> Dict[str, Any]:
        """獲取當前門檻配置"""
        return json.loads(json.dumps(self.current_thresholds))
    
    def _get_current_thresholds_summary(self) -> Dict[str, Any]:
        """獲取當前門檻摘要"""
        return {
            "A4_threshold_dbm": self.current_thresholds["A4"]["threshold_dbm"],
            "A5_threshold1_dbm": self.current_thresholds["A5"]["threshold1_dbm"],
            "A5_threshold2_dbm": self.current_thresholds["A5"]["threshold2_dbm"],
            "D2_threshold1_km": self.current_thresholds["D2"]["distance_threshold1_m"] / 1000,
            "D2_threshold2_km": self.current_thresholds["D2"]["distance_threshold2_m"] / 1000
        }
    
    def reset_to_baseline(self) -> Dict[str, Any]:
        """重置到基準門檻值"""
        self.current_thresholds = json.loads(json.dumps(self.baseline_thresholds))
        
        self.logger.info("🔄 門檻已重置到基準值")
        
        return {
            "reset": True,
            "new_thresholds": self._get_current_thresholds_summary(),
            "reset_time": datetime.now(timezone.utc).isoformat()
        }
    
    def _load_configuration(self, config_file_path: str) -> bool:
        """載入配置文件"""
        try:
            with open(config_file_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            if "baseline_thresholds" in config:
                self.baseline_thresholds.update(config["baseline_thresholds"])
                self.current_thresholds = json.loads(json.dumps(self.baseline_thresholds))
            
            if "adjustment_parameters" in config:
                self.adjustment_parameters.update(config["adjustment_parameters"])
            
            self.logger.info(f"✅ 配置已載入: {config_file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"載入配置失敗: {e}")
            return False
    
    def save_configuration(self, config_file_path: str) -> bool:
        """儲存配置到文件"""
        try:
            config = {
                "baseline_thresholds": self.baseline_thresholds,
                "current_thresholds": self.current_thresholds,
                "adjustment_parameters": self.adjustment_parameters,
                "controller_statistics": self.controller_statistics,
                "saved_time": datetime.now(timezone.utc).isoformat()
            }
            
            with open(config_file_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"✅ 配置已儲存: {config_file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"儲存配置失敗: {e}")
            return False
    
    def get_controller_status(self) -> Dict[str, Any]:
        """獲取控制器狀態"""
        return {
            "current_thresholds": self._get_current_thresholds_summary(),
            "baseline_thresholds": {
                "A4_baseline_dbm": self.baseline_thresholds["A4"]["threshold_dbm"],
                "A5_baseline1_dbm": self.baseline_thresholds["A5"]["threshold1_dbm"],
                "A5_baseline2_dbm": self.baseline_thresholds["A5"]["threshold2_dbm"],
                "D2_baseline1_km": self.baseline_thresholds["D2"]["distance_threshold1_m"] / 1000
            },
            "network_conditions": self.network_conditions.copy(),
            "controller_statistics": self.controller_statistics.copy(),
            "recent_adjustments": self.adjustment_history[-5:],  # 最近5次調整
            "performance_score": self._calculate_performance_score()
        }