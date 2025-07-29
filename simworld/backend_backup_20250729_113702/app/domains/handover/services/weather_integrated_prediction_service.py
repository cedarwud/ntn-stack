"""
Weather-Integrated Prediction Service Implementation
實作整合天氣資訊的預測算法
考慮大氣條件對信號傳播的影響以提升預測準確率
"""

import asyncio
import time
import math
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import logging
import random

logger = logging.getLogger(__name__)


class WeatherCondition(str, Enum):
    """天氣條件類型"""
    CLEAR = "clear"              # 晴朗
    PARTLY_CLOUDY = "partly_cloudy"  # 部分多雲
    CLOUDY = "cloudy"            # 多雲
    OVERCAST = "overcast"        # 陰天
    LIGHT_RAIN = "light_rain"    # 小雨
    MODERATE_RAIN = "moderate_rain"  # 中雨
    HEAVY_RAIN = "heavy_rain"    # 大雨
    THUNDERSTORM = "thunderstorm"    # 雷暴
    SNOW = "snow"                # 雪
    FOG = "fog"                  # 霧


@dataclass
class WeatherData:
    """天氣數據"""
    condition: WeatherCondition
    temperature_celsius: float
    humidity_percent: float
    pressure_hpa: float
    wind_speed_kmh: float
    visibility_km: float
    cloud_coverage_percent: float
    precipitation_rate_mmh: float  # 降雨率 mm/h
    timestamp: float


@dataclass
class AtmosphericLossProfile:
    """大氣損耗概況"""
    rain_attenuation_db: float      # 雨衰
    cloud_attenuation_db: float     # 雲層衰減
    atmospheric_absorption_db: float # 大氣吸收
    scintillation_db: float         # 電離層閃爍
    total_atmospheric_loss_db: float
    confidence_factor: float        # 預測信心係數 (0-1)


@dataclass
class WeatherAdjustedSatelliteScore:
    """天氣調整後的衛星評分"""
    satellite_id: str
    base_score: float
    weather_adjusted_score: float
    atmospheric_loss: AtmosphericLossProfile
    adjusted_signal_strength_dbm: float
    weather_risk_factor: float      # 天氣風險因子 (0-1)


class WeatherIntegratedPredictionService:
    """天氣整合預測服務"""
    
    def __init__(self):
        # 天氣影響參數配置
        self.weather_impact_coefficients = self._initialize_weather_coefficients()
        self.frequency_ghz = 20.0  # Ka 頻段 20 GHz
        
        # 預測歷史和準確率追蹤
        self.prediction_history: List[Dict] = []
        self.weather_prediction_cache: Dict[str, WeatherData] = {}
        
        # 動態調整參數
        self.base_accuracy_target = 0.95
        self.weather_adjustment_enabled = True
    
    def _initialize_weather_coefficients(self) -> Dict[WeatherCondition, Dict]:
        """初始化天氣影響係數"""
        return {
            WeatherCondition.CLEAR: {
                "rain_attenuation_factor": 0.0,
                "cloud_attenuation_factor": 0.1,
                "atmospheric_absorption": 0.2,
                "scintillation_factor": 0.1,
                "reliability_multiplier": 1.0
            },
            WeatherCondition.PARTLY_CLOUDY: {
                "rain_attenuation_factor": 0.0,
                "cloud_attenuation_factor": 0.3,
                "atmospheric_absorption": 0.3,
                "scintillation_factor": 0.2,
                "reliability_multiplier": 0.95
            },
            WeatherCondition.CLOUDY: {
                "rain_attenuation_factor": 0.0,
                "cloud_attenuation_factor": 0.6,
                "atmospheric_absorption": 0.4,
                "scintillation_factor": 0.3,
                "reliability_multiplier": 0.9
            },
            WeatherCondition.LIGHT_RAIN: {
                "rain_attenuation_factor": 0.5,
                "cloud_attenuation_factor": 0.8,
                "atmospheric_absorption": 0.6,
                "scintillation_factor": 0.4,
                "reliability_multiplier": 0.85
            },
            WeatherCondition.MODERATE_RAIN: {
                "rain_attenuation_factor": 2.0,
                "cloud_attenuation_factor": 1.2,
                "atmospheric_absorption": 0.8,
                "scintillation_factor": 0.6,
                "reliability_multiplier": 0.75
            },
            WeatherCondition.HEAVY_RAIN: {
                "rain_attenuation_factor": 8.0,
                "cloud_attenuation_factor": 1.8,
                "atmospheric_absorption": 1.2,
                "scintillation_factor": 1.0,
                "reliability_multiplier": 0.6
            },
            WeatherCondition.THUNDERSTORM: {
                "rain_attenuation_factor": 15.0,
                "cloud_attenuation_factor": 2.5,
                "atmospheric_absorption": 1.8,
                "scintillation_factor": 2.0,
                "reliability_multiplier": 0.4
            },
            WeatherCondition.SNOW: {
                "rain_attenuation_factor": 1.0,
                "cloud_attenuation_factor": 1.0,
                "atmospheric_absorption": 0.7,
                "scintillation_factor": 0.5,
                "reliability_multiplier": 0.8
            },
            WeatherCondition.FOG: {
                "rain_attenuation_factor": 0.2,
                "cloud_attenuation_factor": 1.5,
                "atmospheric_absorption": 1.0,
                "scintillation_factor": 0.8,
                "reliability_multiplier": 0.7
            }
        }
    
    async def get_weather_conditions(self, ue_position: Tuple[float, float, float]) -> WeatherData:
        """
        獲取指定位置的天氣條件
        在實際系統中應整合真實的天氣 API
        """
        lat, lon, alt = ue_position
        cache_key = f"{lat:.3f}_{lon:.3f}"
        
        # 檢查快取
        if cache_key in self.weather_prediction_cache:
            cached_weather = self.weather_prediction_cache[cache_key]
            # 如果快取數據不超過 10 分鐘，直接使用
            if time.time() - cached_weather.timestamp < 600:
                return cached_weather
        
        # 生成模擬天氣數據 (在生產環境中應替換為真實 API)
        weather_data = await self._generate_simulated_weather(ue_position)
        
        # 快取天氣數據
        self.weather_prediction_cache[cache_key] = weather_data
        
        logger.info(f"獲取天氣數據: {weather_data.condition.value}, 溫度: {weather_data.temperature_celsius}°C, 降雨: {weather_data.precipitation_rate_mmh}mm/h")
        
        return weather_data
    
    async def _generate_simulated_weather(self, ue_position: Tuple[float, float, float]) -> WeatherData:
        """生成模擬天氣數據"""
        lat, lon, alt = ue_position
        
        # 基於位置和時間生成偽隨機但一致的天氣
        current_time = time.time()
        seed_value = int(lat * 1000) + int(lon * 1000) + int(current_time / 3600)  # 每小時變化
        random.seed(seed_value)
        
        # 天氣條件概率分佈
        weather_probabilities = [
            (WeatherCondition.CLEAR, 0.4),
            (WeatherCondition.PARTLY_CLOUDY, 0.25),
            (WeatherCondition.CLOUDY, 0.15),
            (WeatherCondition.LIGHT_RAIN, 0.1),
            (WeatherCondition.MODERATE_RAIN, 0.05),
            (WeatherCondition.HEAVY_RAIN, 0.02),
            (WeatherCondition.THUNDERSTORM, 0.01),
            (WeatherCondition.SNOW, 0.01),
            (WeatherCondition.FOG, 0.01)
        ]
        
        # 選擇天氣條件
        rand_val = random.random()
        cumulative_prob = 0
        selected_condition = WeatherCondition.CLEAR
        
        for condition, prob in weather_probabilities:
            cumulative_prob += prob
            if rand_val <= cumulative_prob:
                selected_condition = condition
                break
        
        # 根據天氣條件生成相關參數
        if selected_condition in [WeatherCondition.CLEAR, WeatherCondition.PARTLY_CLOUDY]:
            temperature = random.uniform(20, 30)
            humidity = random.uniform(40, 70)
            precipitation = 0.0
            visibility = random.uniform(15, 25)
            cloud_coverage = random.uniform(0, 40) if selected_condition == WeatherCondition.PARTLY_CLOUDY else random.uniform(0, 10)
        elif selected_condition == WeatherCondition.CLOUDY:
            temperature = random.uniform(15, 25)
            humidity = random.uniform(60, 80)
            precipitation = 0.0
            visibility = random.uniform(10, 20)
            cloud_coverage = random.uniform(50, 80)
        elif selected_condition == WeatherCondition.LIGHT_RAIN:
            temperature = random.uniform(12, 22)
            humidity = random.uniform(75, 90)
            precipitation = random.uniform(0.5, 2.0)
            visibility = random.uniform(5, 15)
            cloud_coverage = random.uniform(70, 90)
        elif selected_condition == WeatherCondition.MODERATE_RAIN:
            temperature = random.uniform(10, 20)
            humidity = random.uniform(80, 95)
            precipitation = random.uniform(2.0, 8.0)
            visibility = random.uniform(2, 8)
            cloud_coverage = random.uniform(80, 95)
        else:  # 極端天氣
            temperature = random.uniform(5, 18)
            humidity = random.uniform(85, 100)
            precipitation = random.uniform(8.0, 25.0)
            visibility = random.uniform(0.5, 5)
            cloud_coverage = random.uniform(90, 100)
        
        return WeatherData(
            condition=selected_condition,
            temperature_celsius=temperature,
            humidity_percent=humidity,
            pressure_hpa=random.uniform(1000, 1020),
            wind_speed_kmh=random.uniform(5, 20),
            visibility_km=visibility,
            cloud_coverage_percent=cloud_coverage,
            precipitation_rate_mmh=precipitation,
            timestamp=current_time
        )
    
    def calculate_atmospheric_loss(self, weather_data: WeatherData, elevation_deg: float) -> AtmosphericLossProfile:
        """
        計算大氣損耗概況
        基於天氣條件和衛星仰角
        """
        coeffs = self.weather_impact_coefficients[weather_data.condition]
        
        # 計算雨衰 (ITU-R P.838 模型簡化版)
        if weather_data.precipitation_rate_mmh > 0:
            # 雨衰係數 (dB/km) at 20 GHz
            rain_specific_attenuation = coeffs["rain_attenuation_factor"] * (weather_data.precipitation_rate_mmh ** 0.75)
            # 路徑長度修正 (考慮仰角)
            path_length_factor = 1.0 / math.sin(math.radians(max(elevation_deg, 5)))
            rain_attenuation_db = rain_specific_attenuation * path_length_factor * 2.0  # 假設 2km 雨層厚度
        else:
            rain_attenuation_db = 0.0
        
        # 雲層衰減
        cloud_attenuation_db = coeffs["cloud_attenuation_factor"] * (weather_data.cloud_coverage_percent / 100.0) * 0.5
        
        # 大氣吸收 (氧氣和水蒸氣)
        atmospheric_absorption_db = coeffs["atmospheric_absorption"] * (1.0 + weather_data.humidity_percent / 100.0)
        
        # 電離層閃爍效應
        scintillation_db = coeffs["scintillation_factor"] * (1.0 / math.sin(math.radians(max(elevation_deg, 10))))
        
        # 總大氣損耗
        total_loss = rain_attenuation_db + cloud_attenuation_db + atmospheric_absorption_db + scintillation_db
        
        # 信心係數 (基於天氣穩定性)
        confidence_factor = coeffs["reliability_multiplier"]
        
        return AtmosphericLossProfile(
            rain_attenuation_db=rain_attenuation_db,
            cloud_attenuation_db=cloud_attenuation_db,
            atmospheric_absorption_db=atmospheric_absorption_db,
            scintillation_db=scintillation_db,
            total_atmospheric_loss_db=total_loss,
            confidence_factor=confidence_factor
        )
    
    async def calculate_weather_adjusted_satellite_scores(
        self,
        satellite_candidates: List[Dict],
        ue_position: Tuple[float, float, float]
    ) -> List[WeatherAdjustedSatelliteScore]:
        """
        計算天氣調整後的衛星評分
        """
        # 獲取當前天氣條件
        weather_data = await self.get_weather_conditions(ue_position)
        
        adjusted_scores = []
        
        for candidate in satellite_candidates:
            # 獲取基礎評分 (來自約束式選擇服務)
            base_score = candidate.get('base_score', 0.8)
            elevation_deg = candidate.get('elevation_deg', 30.0)
            base_signal_strength = candidate.get('signal_strength_dbm', -80.0)
            
            # 計算大氣損耗
            atmospheric_loss = self.calculate_atmospheric_loss(weather_data, elevation_deg)
            
            # 調整信號強度
            adjusted_signal_strength = base_signal_strength - atmospheric_loss.total_atmospheric_loss_db
            
            # 計算天氣風險因子
            weather_risk = 1.0 - atmospheric_loss.confidence_factor
            
            # 調整評分 (考慮天氣影響)
            score_adjustment_factor = atmospheric_loss.confidence_factor
            if adjusted_signal_strength < -100.0:  # 信號強度過低的懲罰
                score_adjustment_factor *= 0.5
            
            weather_adjusted_score = base_score * score_adjustment_factor
            
            adjusted_scores.append(WeatherAdjustedSatelliteScore(
                satellite_id=candidate.get('satellite_id', 'unknown'),
                base_score=base_score,
                weather_adjusted_score=weather_adjusted_score,
                atmospheric_loss=atmospheric_loss,
                adjusted_signal_strength_dbm=adjusted_signal_strength,
                weather_risk_factor=weather_risk
            ))
        
        # 按調整後的評分排序
        adjusted_scores.sort(key=lambda x: x.weather_adjusted_score, reverse=True)
        
        logger.info(f"天氣調整完成: {weather_data.condition.value} 條件下調整了 {len(adjusted_scores)} 個候選衛星")
        
        return adjusted_scores
    
    async def predict_with_weather_integration(
        self,
        ue_id: str,
        ue_position: Tuple[float, float, float],
        satellite_candidates: List[Dict],
        future_time_horizon_sec: int = 300
    ) -> Dict:
        """
        整合天氣資訊的預測算法
        預測未來一段時間內的最佳衛星選擇
        """
        try:
            logger.info(f"為 UE {ue_id} 執行天氣整合預測，預測時間範圍: {future_time_horizon_sec} 秒")
            
            # 獲取當前天氣調整後的評分
            current_scores = await self.calculate_weather_adjusted_satellite_scores(
                satellite_candidates, ue_position
            )
            
            if not current_scores:
                return {
                    "success": False,
                    "error": "沒有可用的衛星候選者"
                }
            
            # 選擇最佳衛星
            best_satellite = current_scores[0]
            
            # 預測未來天氣變化對信號的影響
            future_weather_impact = await self._predict_future_weather_impact(
                ue_position, future_time_horizon_sec
            )
            
            # 計算預測信心度
            prediction_confidence = self._calculate_prediction_confidence(
                best_satellite, future_weather_impact
            )
            
            # 建立預測結果
            prediction_result = {
                "success": True,
                "ue_id": ue_id,
                "selected_satellite": {
                    "satellite_id": best_satellite.satellite_id,
                    "base_score": best_satellite.base_score,
                    "weather_adjusted_score": best_satellite.weather_adjusted_score,
                    "adjusted_signal_strength_dbm": best_satellite.adjusted_signal_strength_dbm,
                    "weather_risk_factor": best_satellite.weather_risk_factor
                },
                "atmospheric_conditions": {
                    "total_loss_db": best_satellite.atmospheric_loss.total_atmospheric_loss_db,
                    "rain_attenuation_db": best_satellite.atmospheric_loss.rain_attenuation_db,
                    "cloud_attenuation_db": best_satellite.atmospheric_loss.cloud_attenuation_db,
                    "confidence_factor": best_satellite.atmospheric_loss.confidence_factor
                },
                "prediction_confidence": prediction_confidence,
                "future_weather_outlook": future_weather_impact,
                "timestamp": time.time()
            }
            
            # 記錄預測歷史
            await self._record_weather_prediction(ue_id, prediction_result)
            
            return prediction_result
            
        except Exception as e:
            logger.error(f"天氣整合預測失敗: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _predict_future_weather_impact(
        self,
        ue_position: Tuple[float, float, float],
        time_horizon_sec: int
    ) -> Dict:
        """預測未來天氣變化的影響"""
        # 簡化的未來天氣預測 (在實際系統中應使用氣象預報 API)
        current_weather = await self.get_weather_conditions(ue_position)
        
        # 基於當前天氣條件預測未來趨勢
        future_impact = {
            "stability_forecast": "stable",  # stable, improving, deteriorating
            "estimated_signal_variation_db": 2.0,
            "risk_of_severe_weather": 0.1,
            "recommended_backup_satellites": 2
        }
        
        # 如果當前是惡劣天氣，預測可能的改善
        if current_weather.condition in [WeatherCondition.HEAVY_RAIN, WeatherCondition.THUNDERSTORM]:
            future_impact["stability_forecast"] = "improving"
            future_impact["estimated_signal_variation_db"] = 8.0
            future_impact["recommended_backup_satellites"] = 3
        elif current_weather.condition == WeatherCondition.CLEAR and current_weather.cloud_coverage_percent > 70:
            future_impact["stability_forecast"] = "deteriorating"
            future_impact["estimated_signal_variation_db"] = 4.0
            future_impact["risk_of_severe_weather"] = 0.3
        
        return future_impact
    
    def _calculate_prediction_confidence(
        self,
        best_satellite: WeatherAdjustedSatelliteScore,
        future_weather_impact: Dict
    ) -> float:
        """計算預測信心度"""
        base_confidence = 0.9
        
        # 基於天氣風險調整
        weather_penalty = best_satellite.weather_risk_factor * 0.3
        
        # 基於未來天氣穩定性調整
        if future_weather_impact["stability_forecast"] == "deteriorating":
            weather_penalty += 0.2
        elif future_weather_impact["stability_forecast"] == "improving":
            weather_penalty -= 0.1
        
        # 基於信號強度調整
        if best_satellite.adjusted_signal_strength_dbm < -90:
            signal_penalty = 0.2
        else:
            signal_penalty = 0.0
        
        final_confidence = max(0.1, base_confidence - weather_penalty - signal_penalty)
        
        return final_confidence
    
    async def _record_weather_prediction(self, ue_id: str, prediction_result: Dict):
        """記錄天氣預測歷史"""
        history_entry = {
            "timestamp": time.time(),
            "ue_id": ue_id,
            "prediction": prediction_result,
            "weather_condition": prediction_result.get("atmospheric_conditions", {}),
            "confidence": prediction_result.get("prediction_confidence", 0.0)
        }
        
        self.prediction_history.append(history_entry)
        
        # 保持歷史記錄在合理範圍內
        if len(self.prediction_history) > 500:
            self.prediction_history = self.prediction_history[-250:]
    
    def get_weather_prediction_statistics(self) -> Dict:
        """獲取天氣預測統計"""
        if not self.prediction_history:
            return {
                "total_predictions": 0,
                "average_confidence": 0.0,
                "weather_distribution": {},
                "accuracy_by_weather": {}
            }
        
        total_predictions = len(self.prediction_history)
        avg_confidence = sum(entry["confidence"] for entry in self.prediction_history) / total_predictions
        
        # 天氣條件分佈統計 (簡化版)
        weather_distribution = {}
        for entry in self.prediction_history[-100:]:  # 最近 100 次預測
            # 模擬天氣統計
            weather_type = "clear" if entry["confidence"] > 0.8 else "adverse"
            weather_distribution[weather_type] = weather_distribution.get(weather_type, 0) + 1
        
        return {
            "total_predictions": total_predictions,
            "average_confidence": round(avg_confidence, 3),
            "weather_distribution": weather_distribution,
            "recent_predictions": len(self.prediction_history[-50:]) if self.prediction_history else 0,
            "cache_size": len(self.weather_prediction_cache)
        }
    
    def enable_weather_adjustment(self, enabled: bool):
        """啟用/禁用天氣調整"""
        self.weather_adjustment_enabled = enabled
        logger.info(f"天氣調整已{'啟用' if enabled else '禁用'}")
    
    def update_weather_coefficients(self, condition: WeatherCondition, coefficients: Dict):
        """更新特定天氣條件的影響係數"""
        if condition in self.weather_impact_coefficients:
            self.weather_impact_coefficients[condition].update(coefficients)
            logger.info(f"已更新 {condition.value} 的天氣係數")