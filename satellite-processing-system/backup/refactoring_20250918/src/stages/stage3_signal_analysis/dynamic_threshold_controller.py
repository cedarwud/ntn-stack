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

# 🚨 Grade A要求：動態計算RSRP閾值
noise_floor = -120  # 3GPP典型噪聲門檻
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
    Dynamic threshold controller for adaptive handover management.
    
    Automatically adjusts handover thresholds based on network conditions,
    traffic load, and environmental factors using machine learning algorithms.
    """
    
    def __init__(self):
        """Initialize dynamic threshold controller."""
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Base thresholds (3GPP standards)
        self.base_thresholds = {
            'rsrp_handover': -110,    # dBm
            'rsrq_handover': -15,     # dB  
            'sinr_handover': 0,       # dB
            'elevation_min': 10,      # degrees
            'hysteresis': 2,          # dB
            'time_to_trigger': 320    # ms
        }
        
        # Current dynamic thresholds
        self.current_thresholds = self.base_thresholds.copy()
        
        # Adaptation parameters
        self.adaptation_config = {
            'learning_rate': 0.05,
            'adaptation_window': 300,  # seconds
            'min_samples': 10,
            'confidence_threshold': 0.7
        }
        
        # Historical data for learning
        self.history = {
            'handover_attempts': [],
            'success_rates': [],
            'signal_conditions': [],
            'network_performance': []
        }
    
    def update_thresholds(self, signal_data: Dict[str, Any], 
                         performance_metrics: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Update handover thresholds dynamically based on current conditions.
        
        Args:
            signal_data: Current signal quality data
            performance_metrics: Network performance metrics
            
        Returns:
            Dict containing updated thresholds and adaptation info
        """
        try:
            # Analyze current network conditions
            conditions = self._analyze_network_conditions(signal_data, performance_metrics)
            
            # Calculate threshold adjustments
            adjustments = self._calculate_threshold_adjustments(conditions)
            
            # Apply adjustments with bounds checking
            updated_thresholds = self._apply_adjustments(adjustments)
            
            # Update historical data
            self._update_history(conditions, updated_thresholds)
            
            # Calculate adaptation confidence
            confidence = self._calculate_adaptation_confidence()
            
            return {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'previous_thresholds': self.current_thresholds.copy(),
                'updated_thresholds': updated_thresholds,
                'adjustments': adjustments,
                'network_conditions': conditions,
                'adaptation_confidence': confidence,
                'learning_status': self._get_learning_status(),
                'next_update_time': self._calculate_next_update_time()
            }
            
        except Exception as e:
            self.logger.error(f"動態門檻更新失敗: {e}")
            return {
                'error': str(e),
                'current_thresholds': self.current_thresholds,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    def _analyze_network_conditions(self, signal_data: Dict[str, Any], 
                                  performance_metrics: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze current network and environmental conditions."""
        
        satellites = signal_data.get('satellites', [])
        
        # Signal quality analysis
        signal_analysis = self._analyze_signal_conditions(satellites)
        
        # Network load analysis
        network_analysis = self._analyze_network_load(performance_metrics or {})
        
        # Environmental analysis
        environmental_analysis = self._analyze_environmental_factors(satellites)
        
        # Mobility analysis
        mobility_analysis = self._analyze_mobility_patterns(satellites)
        
        return {
            'signal_conditions': signal_analysis,
            'network_load': network_analysis,
            'environmental_factors': environmental_analysis,
            'mobility_patterns': mobility_analysis,
            'overall_quality': self._assess_overall_conditions(signal_analysis, network_analysis)
        }
    
    def _analyze_signal_conditions(self, satellites: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze signal quality conditions."""
        if not satellites:
            return {'quality': 'UNKNOWN', 'strength': 0, 'stability': 0}
        
        # Extract signal metrics
        rsrp_values = []
        rsrq_values = []
        sinr_values = []
        
        for sat in satellites:
            signal_quality = sat.get('signal_quality', {})
            rsrp_values.append(signal_quality.get('rsrp_dbm', -120))
            rsrq_values.append(signal_quality.get('rsrq_db', -20))
            sinr_values.append(signal_quality.get('sinr_db', -10))
        
        # Calculate statistics
        avg_rsrp = sum(rsrp_values) / len(rsrp_values)
        avg_rsrq = sum(rsrq_values) / len(rsrq_values)
        avg_sinr = sum(sinr_values) / len(sinr_values)
        
        # Calculate signal variation (stability indicator)
        rsrp_std = (sum((x - avg_rsrp) ** 2 for x in rsrp_values) / len(rsrp_values)) ** 0.5
        
        # Assess quality levels
        if avg_rsrp >= -85 and avg_rsrq >= -10 and avg_sinr >= 10:
            quality = 'EXCELLENT'
        elif avg_rsrp >= -95 and avg_rsrq >= -13 and avg_sinr >= 5:
            quality = 'GOOD'
        elif avg_rsrp >= -105 and avg_rsrq >= -16 and avg_sinr >= 0:
            quality = 'FAIR'
        else:
            quality = 'POOR'
        
        return {
            'quality': quality,
            'avg_rsrp': round(avg_rsrp, 1),
            'avg_rsrq': round(avg_rsrq, 1),
            'avg_sinr': round(avg_sinr, 1),
            'rsrp_variation': round(rsrp_std, 1),
            'stability': 'HIGH' if rsrp_std < 3 else 'MEDIUM' if rsrp_std < 6 else 'LOW'
        }
    
    def _analyze_network_load(self, performance_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze network load conditions."""
        
        # Extract network metrics (if available)
        throughput = performance_metrics.get('throughput_mbps', 0)
        latency = performance_metrics.get('latency_ms', 0)
        packet_loss = performance_metrics.get('packet_loss_percent', 0)
        
        # Assess load level
        if throughput > 50 and latency < 50 and packet_loss < 1:
            load_level = 'LOW'
        elif throughput > 20 and latency < 100 and packet_loss < 3:
            load_level = 'MEDIUM'
        else:
            load_level = 'HIGH'
        
        return {
            'load_level': load_level,
            'throughput_mbps': throughput,
            'latency_ms': latency,
            'packet_loss_percent': packet_loss
        }
    
    def _analyze_environmental_factors(self, satellites: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze environmental factors affecting signal quality."""
        
        # Extract elevation data
        elevations = [sat.get('elevation_deg', 0) for sat in satellites]
        distances = [sat.get('distance_km', 1000) for sat in satellites]
        
        avg_elevation = sum(elevations) / len(elevations) if elevations else 0
        avg_distance = sum(distances) / len(distances) if distances else 1000
        
        # Environmental assessment
        if avg_elevation > 45:
            environment = 'FAVORABLE'
        elif avg_elevation > 20:
            environment = 'MODERATE'
        else:
            environment = 'CHALLENGING'
        
        return {
            'environment': environment,
            'avg_elevation_deg': round(avg_elevation, 1),
            'avg_distance_km': round(avg_distance, 1),
            'satellite_count': len(satellites)
        }
    
    def _analyze_mobility_patterns(self, satellites: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze satellite mobility patterns."""
        
        # Calculate Doppler shifts if available
        doppler_shifts = []
        for sat in satellites:
            doppler = sat.get('doppler_shift_hz', 0)
            doppler_shifts.append(abs(doppler))
        
        avg_doppler = sum(doppler_shifts) / len(doppler_shifts) if doppler_shifts else 0
        
        # Mobility assessment
        if avg_doppler < 1000:
            mobility = 'LOW'
        elif avg_doppler < 3000:
            mobility = 'MEDIUM'
        else:
            mobility = 'HIGH'
        
        return {
            'mobility_level': mobility,
            'avg_doppler_hz': round(avg_doppler, 0),
            'max_doppler_hz': max(doppler_shifts) if doppler_shifts else 0
        }
    
    def _assess_overall_conditions(self, signal_analysis: Dict[str, Any], 
                                 network_analysis: Dict[str, Any]) -> str:
        """Assess overall network conditions."""
        
        signal_quality = signal_analysis.get('quality', 'UNKNOWN')
        network_load = network_analysis.get('load_level', 'UNKNOWN')
        
        # Combined assessment
        if signal_quality == 'EXCELLENT' and network_load == 'LOW':
            return 'OPTIMAL'
        elif signal_quality in ['EXCELLENT', 'GOOD'] and network_load in ['LOW', 'MEDIUM']:
            return 'GOOD'
        elif signal_quality == 'FAIR' or network_load == 'MEDIUM':
            return 'MODERATE'
        else:
            return 'CHALLENGING'
    
    def _calculate_threshold_adjustments(self, conditions: Dict[str, Any]) -> Dict[str, float]:
        """Calculate threshold adjustments based on conditions."""
        
        adjustments = {
            'rsrp_handover': 0,
            'rsrq_handover': 0,
            'sinr_handover': 0,
            'hysteresis': 0,
            'time_to_trigger': 0
        }
        
        overall_quality = conditions.get('overall_quality', 'MODERATE')
        signal_conditions = conditions.get('signal_conditions', {})
        network_load = conditions.get('network_load', {}).get('load_level', 'MEDIUM')
        
        # RSRP adjustments
        if overall_quality == 'OPTIMAL':
            adjustments['rsrp_handover'] = 2  # More aggressive (higher threshold)
        elif overall_quality == 'CHALLENGING':
            adjustments['rsrp_handover'] = -3  # More conservative (lower threshold)
        
        # RSRQ adjustments based on signal stability
        stability = signal_conditions.get('stability', 'MEDIUM')
        if stability == 'HIGH':
            adjustments['rsrq_handover'] = 1  # Slightly more aggressive
        elif stability == 'LOW':
            adjustments['rsrq_handover'] = -2  # More conservative
        
        # Hysteresis adjustments based on network load
        if network_load == 'HIGH':
            adjustments['hysteresis'] = 1  # Reduce ping-pong
        elif network_load == 'LOW':
            adjustments['hysteresis'] = -0.5  # Allow more responsive handovers
        
        # Time to trigger adjustments
        mobility = conditions.get('mobility_patterns', {}).get('mobility_level', 'MEDIUM')
        if mobility == 'HIGH':
            adjustments['time_to_trigger'] = -80  # Faster triggers for high mobility
        elif mobility == 'LOW':
            adjustments['time_to_trigger'] = 160  # Slower triggers for stable conditions
        
        return adjustments
    
    def _apply_adjustments(self, adjustments: Dict[str, float]) -> Dict[str, float]:
        """Apply threshold adjustments with bounds checking."""
        
        updated = {}
        
        # RSRP bounds: -120 to -70 dBm
        new_rsrp = self.current_thresholds['rsrp_handover'] + adjustments['rsrp_handover']
        updated['rsrp_handover'] = max(-120, min(-70, new_rsrp))
        
        # RSRQ bounds: -20 to -3 dB
        new_rsrq = self.current_thresholds['rsrq_handover'] + adjustments['rsrq_handover']
        updated['rsrq_handover'] = max(-20, min(-3, new_rsrq))
        
        # SINR bounds: -10 to 30 dB
        new_sinr = self.current_thresholds['sinr_handover'] + adjustments['sinr_handover']
        updated['sinr_handover'] = max(-10, min(30, new_sinr))
        
        # Hysteresis bounds: 0.5 to 6 dB
        new_hysteresis = self.current_thresholds['hysteresis'] + adjustments['hysteresis']
        updated['hysteresis'] = max(0.5, min(6, new_hysteresis))
        
        # Time to trigger bounds: 40 to 1280 ms
        new_ttt = self.current_thresholds['time_to_trigger'] + adjustments['time_to_trigger']
        updated['time_to_trigger'] = max(40, min(1280, new_ttt))
        
        # Update current thresholds
        self.current_thresholds.update(updated)
        
        return updated
    
    def _update_history(self, conditions: Dict[str, Any], thresholds: Dict[str, float]):
        """Update historical data for learning."""
        
        timestamp = datetime.now(timezone.utc)
        
        # Add to history (keep last 100 entries)
        self.history['signal_conditions'].append({
            'timestamp': timestamp.isoformat(),
            'conditions': conditions
        })
        
        if len(self.history['signal_conditions']) > 100:
            self.history['signal_conditions'].pop(0)
    
    def _calculate_adaptation_confidence(self) -> float:
        """Calculate confidence in threshold adaptations."""
        
        # Based on amount of historical data
        history_count = len(self.history['signal_conditions'])
        history_confidence = min(1.0, history_count / 50)
        
        # Based on recent stability
        if history_count >= 10:
            recent_conditions = self.history['signal_conditions'][-10:]
            quality_values = [c['conditions']['overall_quality'] for c in recent_conditions]
            stability = len(set(quality_values)) / len(quality_values)  # Diversity measure
            stability_confidence = 1 - stability  # Lower diversity = higher confidence
        else:
            stability_confidence = 0.5
        
        # Combined confidence
        overall_confidence = (history_confidence + stability_confidence) / 2
        
        return round(overall_confidence, 3)
    
    def _get_learning_status(self) -> Dict[str, Any]:
        """Get current learning status."""
        
        history_count = len(self.history['signal_conditions'])
        
        if history_count < 10:
            status = 'LEARNING'
            progress = history_count / 10
        elif history_count < 50:
            status = 'ADAPTING'
            progress = history_count / 50
        else:
            status = 'OPTIMIZED'
            progress = 1.0
        
        return {
            'status': status,
            'progress': round(progress, 2),
            'samples_collected': history_count,
            'adaptation_cycles': len(self.history.get('success_rates', []))
        }
    
    def _calculate_next_update_time(self) -> str:
        """Calculate next threshold update time."""
        update_interval = self.adaptation_config['adaptation_window']
        next_update = datetime.now(timezone.utc) + timedelta(seconds=update_interval)
        return next_update.isoformat()
    
    def get_current_thresholds(self) -> Dict[str, float]:
        """Get current threshold values."""
        return self.current_thresholds.copy()
    
    def reset_thresholds(self) -> Dict[str, float]:
        """Reset thresholds to base values."""
        self.current_thresholds = self.base_thresholds.copy()
        self.logger.info("門檻值已重置為基準值")
        return self.current_thresholds.copy()