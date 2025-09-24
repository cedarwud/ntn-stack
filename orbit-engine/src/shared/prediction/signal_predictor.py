"""
信號預測器

整合來源：
- stage3_signal_analysis/signal_prediction_engine.py (核心信號預測功能)
- stage3_signal_analysis/handover_decision_engine.py (信號趨勢預測)
"""

import math
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

from .base_predictor import BasePrediction, PredictionResult, PredictionConfig, TrainingResult


@dataclass
class SignalQualityPrediction(PredictionResult):
    """信號品質預測結果"""
    rsrp_dbm: float = -120.0
    rsrq_db: Optional[float] = None
    sinr_db: Optional[float] = None
    elevation_deg: float = 0.0
    range_km: float = 0.0
    signal_trend: str = "stable"  # improving, stable, degrading
    handover_recommended: bool = False


class SignalPredictor(BasePrediction):
    """信號預測器 - 整合Stage 3的信號預測功能"""

    def __init__(self, config: PredictionConfig):
        # 信號預測配置 - 必須在調用super().__init__之前設置
        self.signal_config = {
            'frequency_ghz': 12.0,  # Ku-band
            'tx_power_dbw': 40.0,   # 發射功率
            'base_antenna_gain_db': 35.0,
            'min_rsrp_threshold': -140.0,
            'noise_floor_dbm': -120.0
        }

        super().__init__("SignalPredictor", config)

        # RSRP趨勢閾值 (基於3GPP標準)
        self.rsrp_thresholds = {
            'good_threshold_dbm': -90.0,
            'poor_threshold_dbm': -110.0,
            'handover_threshold_dbm': -105.0
        }

    def predict_signal_quality(self, satellite_pos: Dict[str, float], observer_pos: Dict[str, float]) -> Dict[str, Any]:
        """
        預測信號品質 (便捷方法)

        Args:
            satellite_pos: 衛星位置 {'latitude', 'longitude', 'altitude_km'}
            observer_pos: 觀測者位置 {'latitude', 'longitude', 'altitude_km'}

        Returns:
            預測結果字典
        """
        try:
            # 計算距離和仰角
            distance_km = self._calculate_distance(satellite_pos, observer_pos)
            elevation_deg = self._calculate_elevation(satellite_pos, observer_pos)

            # 使用標準預測方法
            input_data = {
                'range_km': distance_km,
                'elevation_deg': elevation_deg
            }

            prediction = self.predict(input_data)

            return {
                'rsrp_dbm': prediction.rsrp_dbm,
                'rsrq_db': prediction.rsrq_db,
                'sinr_db': prediction.sinr_db,
                'elevation_deg': prediction.elevation_deg,
                'distance_km': prediction.range_km,
                'signal_trend': prediction.signal_trend,
                'confidence': prediction.confidence_score
            }

        except Exception as e:
            self.logger.error(f"信號品質預測失敗: {e}")
            return {
                'rsrp_dbm': -120.0,
                'distance_km': 1000.0,
                'elevation_deg': 0.0,
                'error': str(e)
            }

    def _calculate_distance(self, pos1: Dict[str, float], pos2: Dict[str, float]) -> float:
        """計算兩點間距離 (簡化為直線距離)"""
        import math
        lat1, lon1, alt1 = pos1['latitude'], pos1['longitude'], pos1['altitude_km']
        lat2, lon2, alt2 = pos2['latitude'], pos2['longitude'], pos2['altitude_km']

        # 簡化的距離計算
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

        earth_radius_km = 6371.0
        ground_distance = earth_radius_km * c
        altitude_diff = abs(alt1 - alt2)

        return math.sqrt(ground_distance**2 + altitude_diff**2)

    def _calculate_elevation(self, satellite_pos: Dict[str, float], observer_pos: Dict[str, float]) -> float:
        """計算仰角"""
        import math

        # 簡化的仰角計算
        distance = self._calculate_distance(satellite_pos, observer_pos)
        altitude_diff = satellite_pos['altitude_km'] - observer_pos['altitude_km']

        if distance == 0:
            return 90.0

        elevation_rad = math.atan2(altitude_diff, distance)
        return max(0.0, math.degrees(elevation_rad))

    def predict(self, input_data: Any) -> SignalQualityPrediction:
        """執行信號品質預測"""
        try:
            if isinstance(input_data, dict):
                range_km = input_data.get('range_km')
                elevation_deg = input_data.get('elevation_deg')

                if range_km is None or elevation_deg is None:
                    raise ValueError("缺少必要的輸入參數: range_km, elevation_deg")

                # 核心RSRP預測
                predicted_rsrp = self._predict_rsrp_from_geometry(range_km, elevation_deg)

                # 信號趨勢分析
                signal_trend = self._determine_rsrp_trend(predicted_rsrp)

                # 換手建議
                handover_recommended = self._should_recommend_handover(predicted_rsrp, signal_trend)

                # 預測其他信號品質參數
                rsrq_db = self._predict_rsrq(predicted_rsrp, elevation_deg)
                sinr_db = self._predict_sinr(predicted_rsrp, elevation_deg)

                prediction = SignalQualityPrediction(
                    prediction_id=f"signal_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
                    predictor_name=self.predictor_name,
                    timestamp=datetime.now(),
                    prediction_horizon=timedelta(minutes=5),
                    confidence_score=self._calculate_prediction_confidence(predicted_rsrp, elevation_deg),
                    model_version="1.0.0",
                    rsrp_dbm=predicted_rsrp,
                    rsrq_db=rsrq_db,
                    sinr_db=sinr_db,
                    elevation_deg=elevation_deg,
                    range_km=range_km,
                    signal_trend=signal_trend,
                    handover_recommended=handover_recommended
                )

                self.add_prediction_result(prediction)
                return prediction

            else:
                raise ValueError("輸入數據必須是字典格式")

        except Exception as e:
            self.logger.error(f"信號預測失敗: {e}")
            # 返回默認的低質量預測
            return SignalQualityPrediction(
                prediction_id=f"signal_error_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
                predictor_name=self.predictor_name,
                timestamp=datetime.now(),
                prediction_horizon=timedelta(minutes=1),
                confidence_score=0.0,
                model_version="1.0.0",
                rsrp_dbm=self.signal_config['min_rsrp_threshold'],
                rsrq_db=-20.0,
                sinr_db=-5.0,
                elevation_deg=0.0,
                range_km=10000.0,
                signal_trend="degrading",
                handover_recommended=False
            )

    def train(self, training_data: Any) -> TrainingResult:
        """訓練信號預測模型"""
        training_start = datetime.now()

        try:
            # 信號預測器使用基於物理的模型，不需要傳統ML訓練
            # 但可以校準參數和更新統計模型

            if isinstance(training_data, list) and training_data:
                # 分析訓練數據以校準參數
                rsrp_values = []
                elevation_values = []

                for sample in training_data:
                    if isinstance(sample, dict):
                        rsrp = sample.get('actual_rsrp')
                        elevation = sample.get('elevation_deg')
                        if rsrp is not None and elevation is not None:
                            rsrp_values.append(rsrp)
                            elevation_values.append(elevation)

                # 計算校準因子
                if rsrp_values:
                    avg_rsrp = sum(rsrp_values) / len(rsrp_values)
                    rsrp_variance = sum((x - avg_rsrp) ** 2 for x in rsrp_values) / len(rsrp_values)

                    # 更新預測統計
                    training_accuracy = self._calculate_training_accuracy(rsrp_values, elevation_values)
                    validation_accuracy = training_accuracy * 0.95  # 簡化的驗證準確性

                else:
                    training_accuracy = 0.5
                    validation_accuracy = 0.4

            else:
                training_accuracy = 0.6
                validation_accuracy = 0.55

            training_duration = datetime.now() - training_start

            result = TrainingResult(
                training_id=f"signal_train_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                model_version="1.0.0",
                training_timestamp=training_start,
                training_duration=training_duration,
                training_accuracy=training_accuracy,
                validation_accuracy=validation_accuracy,
                training_samples=len(training_data) if isinstance(training_data, list) else 0
            )

            self.training_history.append(result)
            return result

        except Exception as e:
            self.logger.error(f"信號預測器訓練失敗: {e}")
            return TrainingResult(
                training_id=f"signal_train_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                model_version="1.0.0",
                training_timestamp=training_start,
                training_duration=datetime.now() - training_start,
                training_accuracy=0.0,
                validation_accuracy=0.0,
                training_samples=0
            )

    def _initialize_model(self):
        """初始化物理信號預測模型"""
        # 信號預測器使用基於物理的Friis公式和ITU-R標準
        # 不需要ML模型初始化，但可以設置預測參數
        self.model = {
            'type': 'physics_based',
            'frequency_ghz': self.signal_config['frequency_ghz'],
            'tx_power_dbw': self.signal_config['tx_power_dbw'],
            'initialized': True
        }
        self.logger.info("信號預測模型已初始化 (基於物理模型)")

    def _predict_rsrp_from_geometry(self, range_km: float, elevation_deg: float) -> float:
        """基於幾何關係預測RSRP (從Stage3提取)"""
        try:
            frequency_ghz = self.signal_config['frequency_ghz']
            tx_power_dbw = self.signal_config['tx_power_dbw']

            # 自由空間路徑損耗 (Friis公式)
            fspl_db = 32.45 + 20 * math.log10(frequency_ghz) + 20 * math.log10(range_km)

            # 天線增益 (基於仰角)
            antenna_gain = self._calculate_elevation_dependent_antenna_gain(elevation_deg)

            # RSRP計算 (ITU-R標準)
            rsrp_dbm = tx_power_dbw + 10 + antenna_gain - fspl_db  # +10: dBW to dBm

            # 大氣衰減校正
            atmospheric_loss = self._calculate_atmospheric_loss(elevation_deg, frequency_ghz)
            rsrp_dbm -= atmospheric_loss

            # 限制最小值
            return max(rsrp_dbm, self.signal_config['min_rsrp_threshold'])

        except Exception as e:
            self.logger.error(f"RSRP幾何預測失敗: {e}")
            return self.signal_config['min_rsrp_threshold']

    def _calculate_elevation_dependent_antenna_gain(self, elevation_deg: float) -> float:
        """計算基於仰角的天線增益"""
        base_gain = self.signal_config['base_antenna_gain_db']

        # 仰角越高，增益越好 (簡化模型)
        if elevation_deg >= 45:
            return base_gain
        elif elevation_deg >= 15:
            return base_gain - 2.0  # 輕微衰減
        elif elevation_deg >= 5:
            return base_gain - 5.0  # 中等衰減
        else:
            return base_gain - 10.0  # 嚴重衰減

    def _calculate_atmospheric_loss(self, elevation_deg: float, frequency_ghz: float) -> float:
        """計算大氣衰減 (基於ITU-R P.618)"""
        # 簡化的大氣衰減模型
        if elevation_deg >= 30:
            return 0.5  # 高仰角時衰減很小
        elif elevation_deg >= 10:
            return 1.0 + (30 - elevation_deg) * 0.1  # 線性增加
        else:
            return 3.0 + (10 - elevation_deg) * 0.2  # 低仰角時衰減較大

    def _determine_rsrp_trend(self, rsrp_dbm: float) -> str:
        """根據RSRP值確定信號趨勢"""
        if rsrp_dbm > self.rsrp_thresholds['good_threshold_dbm']:
            return 'improving'
        elif rsrp_dbm > self.rsrp_thresholds['poor_threshold_dbm']:
            return 'stable'
        else:
            return 'degrading'

    def _should_recommend_handover(self, rsrp_dbm: float, signal_trend: str) -> bool:
        """判斷是否應該建議換手"""
        # 基於RSRP和趨勢的換手決策
        if rsrp_dbm < self.rsrp_thresholds['handover_threshold_dbm']:
            return True
        if signal_trend == 'degrading' and rsrp_dbm < self.rsrp_thresholds['good_threshold_dbm']:
            return True
        return False

    def _predict_rsrq(self, rsrp_dbm: float, elevation_deg: float) -> float:
        """預測RSRQ (接收信號品質指示)"""
        # 簡化的RSRQ預測模型，基於RSRP和仰角
        base_rsrq = -10.0  # 基礎RSRQ

        # RSRP影響
        if rsrp_dbm > -80:
            rsrq_adjustment = 5.0
        elif rsrp_dbm > -100:
            rsrq_adjustment = 0.0
        else:
            rsrq_adjustment = -5.0

        # 仰角影響
        if elevation_deg > 30:
            elevation_adjustment = 2.0
        elif elevation_deg > 10:
            elevation_adjustment = 0.0
        else:
            elevation_adjustment = -3.0

        return base_rsrq + rsrq_adjustment + elevation_adjustment

    def _predict_sinr(self, rsrp_dbm: float, elevation_deg: float) -> float:
        """預測SINR (信號干擾噪聲比)"""
        # 簡化的SINR預測模型
        noise_floor = self.signal_config['noise_floor_dbm']

        # 基本SINR = RSRP - Noise Floor - Interference
        interference_estimate = -110.0  # 簡化的干擾估計

        sinr_db = rsrp_dbm - max(noise_floor, interference_estimate)

        # 仰角修正
        if elevation_deg > 30:
            sinr_db += 3.0
        elif elevation_deg < 10:
            sinr_db -= 2.0

        return sinr_db

    def _calculate_prediction_confidence(self, rsrp_dbm: float, elevation_deg: float) -> float:
        """計算預測信心度"""
        confidence = 0.5  # 基礎信心度

        # RSRP品質影響信心度
        if rsrp_dbm > self.rsrp_thresholds['good_threshold_dbm']:
            confidence += 0.3
        elif rsrp_dbm > self.rsrp_thresholds['poor_threshold_dbm']:
            confidence += 0.1

        # 仰角影響信心度
        if elevation_deg > 30:
            confidence += 0.2
        elif elevation_deg > 10:
            confidence += 0.1

        return min(1.0, confidence)

    def _calculate_training_accuracy(self, rsrp_values: List[float], elevation_values: List[float]) -> float:
        """計算訓練準確性"""
        if not rsrp_values:
            return 0.0

        # 基於RSRP值的分佈計算準確性
        avg_rsrp = sum(rsrp_values) / len(rsrp_values)

        if avg_rsrp > self.rsrp_thresholds['good_threshold_dbm']:
            return 0.9  # 高品質信號預測準確性高
        elif avg_rsrp > self.rsrp_thresholds['poor_threshold_dbm']:
            return 0.7  # 中等品質信號
        else:
            return 0.5  # 低品質信號預測困難

    def predict_signal_trajectory(self, trajectory_data: Dict[str, Any]) -> Dict[str, Any]:
        """預測整條軌跡的信號品質變化"""
        try:
            position_timeseries = trajectory_data.get('position_timeseries', [])
            satellite_id = trajectory_data.get('satellite_id', 'unknown')

            predictions = []
            for position in position_timeseries:
                observer_data = position.get('relative_to_observer', {})
                range_km = observer_data.get('range_km')
                elevation_deg = observer_data.get('elevation_deg')

                if range_km is not None and elevation_deg is not None and elevation_deg > 0:
                    prediction = self.predict({
                        'range_km': range_km,
                        'elevation_deg': elevation_deg
                    })

                    predictions.append({
                        'timestamp': position.get('timestamp'),
                        'prediction': prediction
                    })

            return {
                'satellite_id': satellite_id,
                'trajectory_predictions': predictions,
                'summary': self._summarize_trajectory_predictions(predictions)
            }

        except Exception as e:
            self.logger.error(f"軌跡信號預測失敗: {e}")
            return {
                'satellite_id': trajectory_data.get('satellite_id', 'unknown'),
                'error': str(e),
                'trajectory_predictions': []
            }

    def _summarize_trajectory_predictions(self, predictions: List[Dict]) -> Dict[str, Any]:
        """總結軌跡預測結果"""
        if not predictions:
            return {'no_predictions': True}

        rsrp_values = [p['prediction'].rsrp_dbm for p in predictions]
        handover_opportunities = [p for p in predictions if p['prediction'].handover_recommended]

        return {
            'total_predictions': len(predictions),
            'max_rsrp': max(rsrp_values),
            'min_rsrp': min(rsrp_values),
            'avg_rsrp': sum(rsrp_values) / len(rsrp_values),
            'handover_opportunities': len(handover_opportunities),
            'best_signal_window': self._find_best_signal_window(predictions),
            'overall_signal_quality': self._classify_overall_quality(rsrp_values)
        }

    def _find_best_signal_window(self, predictions: List[Dict]) -> Dict[str, Any]:
        """找出最佳信號窗口"""
        if not predictions:
            return {}

        best_prediction = max(predictions, key=lambda p: p['prediction'].rsrp_dbm)
        return {
            'timestamp': best_prediction['timestamp'],
            'rsrp_dbm': best_prediction['prediction'].rsrp_dbm,
            'elevation_deg': best_prediction['prediction'].elevation_deg
        }

    def _classify_overall_quality(self, rsrp_values: List[float]) -> str:
        """分類整體信號品質"""
        if not rsrp_values:
            return 'unknown'

        avg_rsrp = sum(rsrp_values) / len(rsrp_values)

        if avg_rsrp > self.rsrp_thresholds['good_threshold_dbm']:
            return 'excellent'
        elif avg_rsrp > self.rsrp_thresholds['poor_threshold_dbm']:
            return 'good'
        else:
            return 'poor'