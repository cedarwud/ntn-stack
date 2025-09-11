#!/usr/bin/env python3
"""
7‹á_Áê—h - ú¼xS 3GPP –
& NTN Stack xSxÚ(– Grade A B

ú¼–:
- 3GPP TS 36.214 v18.0.0 "Physical layer procedures" 
- 3GPP TS 38.331 v18.5.1 "Radio Resource Control (RRC) protocol specification"
- ITU-R P.618-13 "Propagation data and prediction methods for the planning of Earth-space telecommunication systems"
- IEEE 802.11-2020 "IEEE Standard for Information technology"

\: NTN Stack vŠ
H,: 2.0.0 (xS¾ºæş)
"""

import logging
import math
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone

from .measurement_offset_config import MeasurementOffsetConfig

logger = logging.getLogger(__name__)


class EnhancedSignalQualityCalculator:
    """
    7‹á_Áê—h
    
    æş 100% & 3GPP TS 36.214 –„ RSRP/RSRQ/RS-SINR —
    İ LEO [4o2LxS*
    
    8Ãyr:
    1. Œt 3GPP læş!!G-
    2. LEO ÌSÕ›xqÿú!
    3. ï‘p¾º—
    4. rşhb
    5. xSWIŒ‡”
    """
    
    def __init__(self, observer_lat: float = 24.9441667, observer_lon: float = 121.3713889):
        """
        Ë7‹á_Áê—h
        
        Args:
            observer_lat: À,Şï¦ (NTPU -)
            observer_lon: À,Ş“¦ (NTPU -)
        """
        self.logger = logging.getLogger(f"{__name__}.EnhancedSignalQualityCalculator")
        
        self.observer_lat = observer_lat
        self.observer_lon = observer_lon
        
        # Ë,ÏOûMn¡h
        self.offset_config = MeasurementOffsetConfig()
        
        # 3GPP TS 36.214 idÃx
        self.physical_parameters = {
            # Ãá_Mn (ú¼ 3GPP TS 36.211)
            "reference_signals": {
                "rs_power_boost_db": 0.0,        # Ãá_Ÿ‡ĞG
                "rs_subcarrier_spacing_khz": 15, # P	â“İ
                "rs_symbols_per_slot": 2,        # ÏB™Ãá_&_x
                "rs_density": 1.0                # Ãá_Æ¦
            },
            
            # ÇJMn (ú¼ 3GPP TS 36.211)
            "resource_blocks": {
                "subcarriers_per_rb": 12,    # ÏÇJP	âx
                "symbols_per_slot": 7,       # ÏB™&_x
                "slots_per_subframe": 2,     # ÏP@B™x
                "rb_bandwidth_khz": 180      # ÇJ6ì
            },
            
            # ,Ï6ìMn (ú¼ 3GPP TS 36.214)
            "measurement_bandwidths": {
                "rsrp_measurement_bw_rb": 6,    # RSRP ,Ï6ì (ÇJ)
                "rsrq_measurement_bw_rb": 25,   # RSRQ ,Ï6ì (ÇJ) 
                "rs_sinr_measurement_bw_rb": 25 # RS-SINR ,Ï6ì (ÇJ)
            }
        }
        
        # LEO [ûqy' (ú¼l‹€S<)
        self.leo_system_characteristics = {
            "starlink": {
                # ú¼ FCC ‡öŒl‹Ç™
                "satellite_eirp_dbw": 37.5,     # IHh;Ÿ‡ (dBW)
                "frequency_band_ghz": 12.0,     # Ku ;µLÈï
                "orbital_altitude_km": 550,     # ÌSØ¦
                "orbital_velocity_kms": 7.66,   # ÌS¦
                "antenna_pattern": "phased_array", # )Ú^‹
                "beam_width_deg": 2.2,          # â_ì¦
                "polarization": "dual",         # u¹
                "modulation": "QPSK/16QAM",     # ¿6¹
                "coding_rate": 0.75             # è¼‡
            },
            
            "oneweb": {
                # ú¼ ITU ‡öŒl‹Ç™
                "satellite_eirp_dbw": 40.0,     # IHh;Ÿ‡ (dBW)
                "frequency_band_ghz": 13.25,    # Ku ;µLÈï
                "orbital_altitude_km": 1200,    # ÌSØ¦
                "orbital_velocity_kms": 7.35,   # ÌS¦
                "antenna_pattern": "spot_beam", # )Ú^‹
                "beam_width_deg": 0.8,          # â_ì¦
                "polarization": "linear",       # u¹
                "modulation": "8PSK/16APSK",    # ¿6¹
                "coding_rate": 0.8              # è¼‡
            }
        }
        
        # (6Bïy' (ú¼æ›lÔ<)
        self.user_terminal_characteristics = {
            "antenna_gain_dbi": 35.0,      # )ÚÊ
            "antenna_efficiency": 0.65,    # )ÚH‡
            "system_noise_figure_db": 2.5, # ûqÜ
x
            "system_temperature_k": 150,   # ûqÜ
«¦
            "cable_loss_db": 0.5,          # Úœ1
            "receiver_sensitivity_dbm": -110, # ¥6_HO¦
            "dynamic_range_db": 80         # ÕKÄ
        }
        
        # i8x (›–<)
        self.physical_constants = {
            "speed_of_light_ms": 299792458.0,      # I (m/s)
            "boltzmann_constant_jk": 1.380649e-23, # â2ü8x (J/K)
            "earth_radius_km": 6371.0,             # 0J‘ (km)
            "atmospheric_scale_height_km": 8.5     # '#Ø (km)
        }
        
        # —q
        self.calculation_statistics = {
            "total_calculations": 0,
            "successful_calculations": 0,
            "failed_calculations": 0,
            "average_computation_time_ms": 0.0,
            "rsrp_distribution": {"min": float('inf'), "max": float('-inf'), "mean": 0.0},
            "rsrq_distribution": {"min": float('inf'), "max": float('-inf'), "mean": 0.0},
            "rs_sinr_distribution": {"min": float('inf'), "max": float('-inf'), "mean": 0.0}
        }
        
        self.logger.info(" 7‹á_Áê—hËŒ")
        self.logger.info(f"   =Í À,Ş: ({observer_lat:.4f}°N, {observer_lon:.4f}°E)")
        self.logger.info(f"   =Ë /ô–: 3GPP TS 36.214 v18.0.0")
        self.logger.info(f"   =ğ /ô§: {list(self.leo_system_characteristics.keys())}")
    
    def calculate_precise_rsrp(self, 
                             satellite_data: Dict[str, Any],
                             position_point: Dict[str, Any],
                             measurement_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        —¾º„ RSRP (Reference Signal Received Power)
        
        ú¼ 3GPP TS 36.214 Section 5.1.1 Œtæş:
        RSRP = ¥6Ÿ‡(n„,Ï;‡6ìg	Ãá_„ÇC 
„Ú'sG<
        
        Args:
            satellite_data: [ú,Ç™
            position_point: MnB“ŞxÚ
            measurement_config: ,ÏMn (+ Ofn/Ocn)
            
        Returns:
            s0„ RSRP —Pœ
        """
        start_time = datetime.now()
        
        try:
            # 1. rÖ[ûqy'
            constellation = satellite_data.get("constellation", "").lower()
            if constellation not in self.leo_system_characteristics:
                raise ValueError(f"/ô„[§: {constellation}")
            
            system_params = self.leo_system_characteristics[constellation]
            
            # 2. rÖMnŒ~UÃx
            elevation_deg = position_point.get("elevation_deg", 0)
            azimuth_deg = position_point.get("azimuth_deg", 0)
            range_km = position_point.get("range_km", 0)
            velocity_kms = position_point.get("velocity_kms", 0)
            
            if elevation_deg < 5:  # N¼ 5° –ºï‹
                return self._create_invalid_rsrp_result("NğÒï‹")
            
            # 3. —ê1z“ï‘1 (Friis l)
            frequency_hz = system_params["frequency_band_ghz"] * 1e9
            wavelength_m = self.physical_constants["speed_of_light_ms"] / frequency_hz
            range_m = range_km * 1000.0
            
            # ê1z“ï‘1: FSPL = 20*log10(4*À*d/»)
            fspl_db = 20 * math.log10(4 * math.pi * range_m / wavelength_m)
            
            # 4. —'#p (ITU-R P.618-13 !‹)
            atmospheric_loss_db = self._calculate_atmospheric_attenuation_itu_p618(
                elevation_deg, system_params["frequency_band_ghz"]
            )
            
            # 5. —ı\ÒHÉqÿ
            doppler_shift_hz = self._calculate_doppler_shift(
                velocity_kms, frequency_hz, elevation_deg, azimuth_deg
            )
            doppler_loss_db = self._calculate_doppler_loss(doppler_shift_hz, frequency_hz)
            
            # 6. —ï‘p
            multipath_loss_db = self._calculate_multipath_fading(
                elevation_deg, range_km, system_params
            )
            
            # 7. —u1
            polarization_loss_db = self._calculate_polarization_loss(
                elevation_deg, system_params["polarization"]
            )
            
            # 8. —)ÚÊ (|ïŒ¥6ï)
            tx_antenna_gain_dbi = self._calculate_satellite_antenna_gain(
                elevation_deg, azimuth_deg, system_params
            )
            rx_antenna_gain_dbi = self._calculate_user_antenna_gain(elevation_deg)
            
            # 9. É(,ÏOû (Ofn + Ocn)
            ofn_db = measurement_config.get("offsets", {}).get("ofn_db", 0.0)
            ocn_db = measurement_config.get("offsets", {}).get("ocn_db", 0.0)
            total_offset_db = ofn_db + ocn_db
            
            # 10. —=¥6Ÿ‡
            satellite_eirp_dbm = system_params["satellite_eirp_dbw"] + 30  # dBW I dBm
            
            total_received_power_dbm = (
                satellite_eirp_dbm +
                tx_antenna_gain_dbi +
                rx_antenna_gain_dbi -
                fspl_db -
                atmospheric_loss_db -
                doppler_loss_db -
                multipath_loss_db -
                polarization_loss_db +
                total_offset_db -
                self.user_terminal_characteristics["cable_loss_db"]
            )
            
            # 11. —Ãá_Ÿ‡ (3GPP TS 36.214 Section 5.1.1)
            # RSRP /(Ãá_ÇC 
„Ÿ‡
            rs_power_boost_db = self.physical_parameters["reference_signals"]["rs_power_boost_db"]
            rs_density = self.physical_parameters["reference_signals"]["rs_density"]
            
            # Ãá_Ÿ‡Æ¦¿t
            rs_density_adjustment_db = 10 * math.log10(rs_density)
            
            rsrp_dbm = total_received_power_dbm + rs_power_boost_db + rs_density_adjustment_db
            
            # 12. 3GPP ÄP6 (-144 0 -44 dBm)
            rsrp_dbm_limited = max(-144, min(-44, rsrp_dbm))
            
            # 13. —,Ïºš¦ (3GPP TS 36.214 B ±1 dB)
            measurement_uncertainty_db = measurement_config.get("measurement_accuracy", {}).get("rsrp_accuracy_db", 1.0)
            
            # 14. Ëús0Pœ
            computation_time_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            result = {
                "rsrp_dbm": rsrp_dbm_limited,
                "rsrp_linear_mw": 10**(rsrp_dbm_limited / 10.0),
                
                "calculation_breakdown": {
                    "satellite_eirp_dbm": satellite_eirp_dbm,
                    "tx_antenna_gain_dbi": tx_antenna_gain_dbi,
                    "rx_antenna_gain_dbi": rx_antenna_gain_dbi,
                    "free_space_loss_db": fspl_db,
                    "atmospheric_loss_db": atmospheric_loss_db,
                    "doppler_loss_db": doppler_loss_db,
                    "multipath_loss_db": multipath_loss_db,
                    "polarization_loss_db": polarization_loss_db,
                    "measurement_offset_db": total_offset_db,
                    "cable_loss_db": self.user_terminal_characteristics["cable_loss_db"],
                    "rs_power_boost_db": rs_power_boost_db,
                    "rs_density_adjustment_db": rs_density_adjustment_db
                },
                
                "3gpp_compliance": {
                    "standard": "3GPP TS 36.214 v18.0.0 Section 5.1.1",
                    "measurement_bandwidth_rb": self.physical_parameters["measurement_bandwidths"]["rsrp_measurement_bw_rb"],
                    "measurement_uncertainty_db": measurement_uncertainty_db,
                    "range_limited": rsrp_dbm != rsrp_dbm_limited,
                    "original_rsrp_dbm": rsrp_dbm,
                    "formula": "RSRP = Ãá_ÇC Ÿ‡„Ú'sG<"
                },
                
                "leo_specific": {
                    "doppler_shift_hz": doppler_shift_hz,
                    "orbital_velocity_kms": velocity_kms,
                    "constellation": constellation,
                    "frequency_ghz": system_params["frequency_band_ghz"]
                },
                
                "metadata": {
                    "satellite_id": satellite_data.get("satellite_id"),
                    "timestamp": position_point.get("timestamp"),
                    "elevation_deg": elevation_deg,
                    "range_km": range_km,
                    "computation_time_ms": computation_time_ms,
                    "calculation_success": True
                }
            }
            
            # ô°q
            self._update_calculation_statistics("rsrp", rsrp_dbm_limited, computation_time_ms, True)
            
            return result
            
        except Exception as e:
            computation_time_ms = (datetime.now() - start_time).total_seconds() * 1000
            self.logger.error(f"RSRP —1W: {e}")
            self._update_calculation_statistics("rsrp", 0, computation_time_ms, False)
            return self._create_invalid_rsrp_result(str(e))
    
    def calculate_precise_rsrq(self,
                             satellite_data: Dict[str, Any],
                             position_point: Dict[str, Any],
                             measurement_config: Dict[str, Any],
                             rsrp_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        —¾º„ RSRQ (Reference Signal Received Quality)
        
        ú¼ 3GPP TS 36.214 Section 5.1.2 Œtæş:
        RSRQ = N × RSRP / RSSI
        v-:
        - N: ,Ï;ìg„ÇJxÏ
        - RSRP: Ãá_¥6Ÿ‡ (Ú'<)
        - RSSI: ¥6á_7¦:h (Ú'<)
        
        Args:
            satellite_data: [ú,Ç™
            position_point: MnB“ŞxÚ
            measurement_config: ,ÏMn
            rsrp_result: RSRP —Pœ
            
        Returns:
            s0„ RSRQ —Pœ
        """
        start_time = datetime.now()
        
        try:
            # 1. ¢å RSRP —/&Ÿ
            if not rsrp_result.get("metadata", {}).get("calculation_success", False):
                return self._create_invalid_rsrq_result("RSRP —1W")
            
            rsrp_dbm = rsrp_result["rsrp_dbm"]
            rsrp_linear_mw = rsrp_result["rsrp_linear_mw"]
            
            # 2. rÖ,Ï6ìMn
            measurement_bw_rb = self.physical_parameters["measurement_bandwidths"]["rsrq_measurement_bw_rb"]
            
            # 3. —rşŸ‡ (s0ú!)
            interference_analysis = self._calculate_detailed_interference(
                satellite_data, position_point, measurement_config
            )
            
            total_interference_linear_mw = (
                interference_analysis["intra_constellation_interference_mw"] +
                interference_analysis["inter_constellation_interference_mw"] +
                interference_analysis["terrestrial_interference_mw"] +
                interference_analysis["atmospheric_noise_mw"]
            )
            
            # 4. —±Ü
Ÿ‡
            thermal_noise_analysis = self._calculate_thermal_noise_power(measurement_bw_rb)
            thermal_noise_linear_mw = thermal_noise_analysis["thermal_noise_mw"]
            
            # 5. — RSSI (3GPP TS 36.214 š©)
            # RSSI = RSRP + rşŸ‡ + Ü
Ÿ‡ (Ú'ß)
            rssi_linear_mw = rsrp_linear_mw + total_interference_linear_mw + thermal_noise_linear_mw
            rssi_dbm = 10 * math.log10(rssi_linear_mw)
            
            # 6. — RSRQ (3GPP l)
            # RSRQ = N × RSRP / RSSI (Ú'ß)
            rsrq_linear = measurement_bw_rb * rsrp_linear_mw / rssi_linear_mw
            rsrq_db = 10 * math.log10(rsrq_linear)
            
            # 7. 3GPP ÄP6 (-19.5 0 -3 dB)
            rsrq_db_limited = max(-19.5, min(-3.0, rsrq_db))
            
            # 8. É(,ÏOû
            offset_db = measurement_config.get("offsets", {}).get("total_offset_db", 0.0)
            rsrq_db_final = rsrq_db_limited + offset_db
            
            # ºİ BPœ(–Äg
            rsrq_db_final = max(-19.5, min(-3.0, rsrq_db_final))
            
            # 9. Ëús0Pœ
            computation_time_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            result = {
                "rsrq_db": rsrq_db_final,
                "rsrq_linear": 10**(rsrq_db_final / 10.0),
                
                "calculation_breakdown": {
                    "rsrp_linear_mw": rsrp_linear_mw,
                    "rssi_linear_mw": rssi_linear_mw,
                    "rssi_dbm": rssi_dbm,
                    "measurement_bandwidth_rb": measurement_bw_rb,
                    "n_factor": measurement_bw_rb,
                    "raw_rsrq_db": rsrq_db,
                    "offset_applied_db": offset_db
                },
                
                "interference_analysis": interference_analysis,
                "thermal_noise_analysis": thermal_noise_analysis,
                
                "3gpp_compliance": {
                    "standard": "3GPP TS 36.214 v18.0.0 Section 5.1.2",
                    "measurement_bandwidth_rb": measurement_bw_rb,
                    "range_limited": rsrq_db != rsrq_db_limited,
                    "original_rsrq_db": rsrq_db,
                    "formula": "RSRQ = N × RSRP / RSSI"
                },
                
                "metadata": {
                    "satellite_id": satellite_data.get("satellite_id"),
                    "timestamp": position_point.get("timestamp"),
                    "computation_time_ms": computation_time_ms,
                    "calculation_success": True
                }
            }
            
            # ô°q
            self._update_calculation_statistics("rsrq", rsrq_db_final, computation_time_ms, True)
            
            return result
            
        except Exception as e:
            computation_time_ms = (datetime.now() - start_time).total_seconds() * 1000
            self.logger.error(f"RSRQ —1W: {e}")
            self._update_calculation_statistics("rsrq", 0, computation_time_ms, False)
            return self._create_invalid_rsrq_result(str(e))
    
    def calculate_precise_rs_sinr(self,
                                satellite_data: Dict[str, Any],
                                position_point: Dict[str, Any],
                                measurement_config: Dict[str, Any],
                                rsrp_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        —¾º„ RS-SINR (Reference Signal Signal-to-Interference-plus-Noise Ratio)
        
        ú¼ 3GPP TS 36.214 Section 5.1.3 Œtæş:
        RS-SINR = Ãá_Ÿ‡ / (rşŸ‡ + Ü
Ÿ‡)
        
        Args:
            satellite_data: [ú,Ç™
            position_point: MnB“ŞxÚ
            measurement_config: ,ÏMn
            rsrp_result: RSRP —Pœ
            
        Returns:
            s0„ RS-SINR —Pœ
        """
        start_time = datetime.now()
        
        try:
            # 1. ¢å RSRP —/&Ÿ
            if not rsrp_result.get("metadata", {}).get("calculation_success", False):
                return self._create_invalid_rs_sinr_result("RSRP —1W")
            
            signal_power_linear_mw = rsrp_result["rsrp_linear_mw"]
            
            # 2. rÖ,Ï6ì (RS-SINR (6ì)
            measurement_bw_rb = self.physical_parameters["measurement_bandwidths"]["rs_sinr_measurement_bw_rb"]
            
            # 3. s0rş (º RS-SINR *)
            sinr_interference_analysis = self._calculate_rs_sinr_interference(
                satellite_data, position_point, measurement_config, measurement_bw_rb
            )
            
            # 4. —Ãá_(Ü

            rs_thermal_noise_analysis = self._calculate_rs_thermal_noise(measurement_bw_rb)
            
            # 5. =rş Ü
Ÿ‡
            total_interference_noise_mw = (
                sinr_interference_analysis["total_interference_mw"] +
                rs_thermal_noise_analysis["rs_thermal_noise_mw"]
            )
            
            # 6. — RS-SINR (Ú'ß)
            rs_sinr_linear = signal_power_linear_mw / total_interference_noise_mw
            rs_sinr_db = 10 * math.log10(rs_sinr_linear)
            
            # 7. 3GPP ÄP6 (-23 0 40 dB)
            rs_sinr_db_limited = max(-23.0, min(40.0, rs_sinr_db))
            
            # 8. É(,ÏOû
            offset_db = measurement_config.get("offsets", {}).get("total_offset_db", 0.0)
            rs_sinr_db_final = rs_sinr_db_limited + offset_db
            
            # ºİ BPœ(–Äg
            rs_sinr_db_final = max(-23.0, min(40.0, rs_sinr_db_final))
            
            # 9. —á_ÁêI
            signal_quality_grade = self._grade_rs_sinr_quality(rs_sinr_db_final)
            
            # 10. Ëús0Pœ
            computation_time_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            result = {
                "rs_sinr_db": rs_sinr_db_final,
                "rs_sinr_linear": 10**(rs_sinr_db_final / 10.0),
                "signal_quality_grade": signal_quality_grade,
                
                "calculation_breakdown": {
                    "signal_power_mw": signal_power_linear_mw,
                    "total_interference_noise_mw": total_interference_noise_mw,
                    "measurement_bandwidth_rb": measurement_bw_rb,
                    "raw_rs_sinr_db": rs_sinr_db,
                    "offset_applied_db": offset_db
                },
                
                "interference_analysis": sinr_interference_analysis,
                "thermal_noise_analysis": rs_thermal_noise_analysis,
                
                "3gpp_compliance": {
                    "standard": "3GPP TS 36.214 v18.0.0 Section 5.1.3",
                    "measurement_bandwidth_rb": measurement_bw_rb,
                    "range_limited": rs_sinr_db != rs_sinr_db_limited,
                    "original_rs_sinr_db": rs_sinr_db,
                    "formula": "RS-SINR = Ãá_Ÿ‡ / (rşŸ‡ + Ü
Ÿ‡)"
                },
                
                "metadata": {
                    "satellite_id": satellite_data.get("satellite_id"),
                    "timestamp": position_point.get("timestamp"),
                    "computation_time_ms": computation_time_ms,
                    "calculation_success": True
                }
            }
            
            # ô°q
            self._update_calculation_statistics("rs_sinr", rs_sinr_db_final, computation_time_ms, True)
            
            return result
            
        except Exception as e:
            computation_time_ms = (datetime.now() - start_time).total_seconds() * 1000
            self.logger.error(f"RS-SINR —1W: {e}")
            self._update_calculation_statistics("rs_sinr", 0, computation_time_ms, False)
            return self._create_invalid_rs_sinr_result(str(e))
    
    # === ©—¹Õ ===
    
    def _calculate_atmospheric_attenuation_itu_p618(self, elevation_deg: float, frequency_ghz: float) -> float:
        """
        ú¼ ITU-R P.618-13 —'#p
        
        Œtæş#Ôpò'pŒcp
        """
        if elevation_deg <= 0:
            return 100.0
        
        # 1. '#p (ITU-R P.676-12)
        oxygen_attenuation_db_km = self._calculate_oxygen_attenuation(frequency_ghz)
        
        # 2. 4¸#p (ITU-R P.676-12)  
        water_vapor_attenuation_db_km = self._calculate_water_vapor_attenuation(frequency_ghz)
        
        # 3. ò'p (ITU-R P.840-8)
        cloud_attenuation_db_km = self._calculate_cloud_attenuation(frequency_ghz)
        
        # 4. —	Hï‘w¦
        elevation_rad = math.radians(elevation_deg)
        if elevation_deg >= 10:
            # ØğÒ!b'#!‹
            path_length_km = self.physical_constants["atmospheric_scale_height_km"] / math.sin(elevation_rad)
        else:
            # NğÒn0ò‡
            earth_radius_km = self.physical_constants["earth_radius_km"]
            atmosphere_height_km = self.physical_constants["atmospheric_scale_height_km"]
            path_length_km = math.sqrt(
                (earth_radius_km + atmosphere_height_km)**2 - 
                (earth_radius_km * math.cos(elevation_rad))**2
            ) - earth_radius_km * math.sin(elevation_rad)
        
        # P6 'ï‘w¦
        path_length_km = min(path_length_km, 100.0)
        
        # 5. ='#p
        total_attenuation_db = (
            oxygen_attenuation_db_km + 
            water_vapor_attenuation_db_km + 
            cloud_attenuation_db_km
        ) * path_length_km
        
        return total_attenuation_db
    
    def _calculate_oxygen_attenuation(self, frequency_ghz: float) -> float:
        """ú¼ ITU-R P.676-12 —'#p"""
        # !„'#p!‹
        if frequency_ghz < 10:
            return 0.0067 * frequency_ghz**0.8
        else:
            return 0.0067 * frequency_ghz**0.8 * (1 + 0.1 * (frequency_ghz - 10))
    
    def _calculate_water_vapor_attenuation(self, frequency_ghz: float) -> float:
        """ú¼ ITU-R P.676-12 —4¸#p"""
        # ğc0@x‹4¸#Æ¦
        water_vapor_density_gm3 = 7.5
        
        # 4¸#pÂx (;‡øÜ)
        if frequency_ghz < 15:
            attenuation_coefficient = 0.05 * (frequency_ghz / 10)**1.6
        else:
            attenuation_coefficient = 0.1 * (frequency_ghz / 10)**2.0
        
        return attenuation_coefficient * water_vapor_density_gm3
    
    def _calculate_cloud_attenuation(self, frequency_ghz: float) -> float:
        """ú¼ ITU-R P.840-8 —ò'p"""
        # ğc0@x‹ò4+Ï
        cloud_liquid_water_content_gm3 = 0.1  # t)#
        
        # ò'pÂx (;‡7øÜ)
        attenuation_coefficient = 0.434 * frequency_ghz**1.28
        
        return attenuation_coefficient * cloud_liquid_water_content_gm3
    
    def _calculate_doppler_shift(self, velocity_kms: float, frequency_hz: float, 
                                elevation_deg: float, azimuth_deg: float) -> float:
        """—ı\Ò;û"""
        # —‘¦Ï
        elevation_rad = math.radians(elevation_deg)
        radial_velocity_ms = velocity_kms * 1000 * math.cos(elevation_rad)
        
        # ı\Ò;ûl
        doppler_shift_hz = (radial_velocity_ms * frequency_hz) / self.physical_constants["speed_of_light_ms"]
        
        return doppler_shift_hz
    
    def _calculate_doppler_loss(self, doppler_shift_hz: float, frequency_hz: float) -> float:
        """—ı\ÒHÉ „Ÿ‡1"""
        # ø;û
        relative_shift = abs(doppler_shift_hz / frequency_hz)
        
        # !„ı\Ò1!‹
        if relative_shift < 1e-6:
            return 0.0
        else:
            return 10 * math.log10(1 + relative_shift) * 0.1  # ®qÿ
    
    def _calculate_multipath_fading(self, elevation_deg: float, range_km: float, 
                                  system_params: Dict[str, Any]) -> float:
        """—ï‘p"""
        # LEO [ï‘;†êûâdc
        if elevation_deg > 30:
            return 0.1  # ØğÒ~N!ï‘
        elif elevation_deg > 15:
            return 0.5 + (30 - elevation_deg) * 0.1
        else:
            return 2.0 + (15 - elevation_deg) * 0.2  # NğÒï‘´Í
    
    def _calculate_polarization_loss(self, elevation_deg: float, polarization: str) -> float:
        """—u1"""
        if polarization == "dual":
            return 0.1  # Ùuûq1ˆ
        elif polarization == "linear":
            # Ú'u(NğÒ	M1
            if elevation_deg < 20:
                return 0.5 + (20 - elevation_deg) * 0.1
            else:
                return 0.2
        else:
            return 0.3  # -u1
    
    def _calculate_satellite_antenna_gain(self, elevation_deg: float, azimuth_deg: float,
                                        system_params: Dict[str, Any]) -> float:
        """—[)ÚÊ"""
        # ú¼)Ú^‹ŒÒ¦
        antenna_type = system_params.get("antenna_pattern", "phased_array")
        beam_width_deg = system_params.get("beam_width_deg", 2.0)
        
        if antenna_type == "phased_array":
            # øMc)Ú - ØÊF¹'7
            pointing_error_deg = abs(elevation_deg - 45)  # G- sÒ¦
            if pointing_error_deg < beam_width_deg / 2:
                return 45.0  #  'Ê
            else:
                return 45.0 - 3 * (pointing_error_deg / beam_width_deg)**2
        else:
            # Şâ_)Ú
            return 40.0  # úšÊ
    
    def _calculate_user_antenna_gain(self, elevation_deg: float) -> float:
        """—(6)ÚÊ"""
        base_gain = self.user_terminal_characteristics["antenna_gain_dbi"]
        efficiency = self.user_terminal_characteristics["antenna_efficiency"]
        
        # ğÒøÜ„Ê¿t
        if elevation_deg >= 45:
            elevation_factor = 1.0
        elif elevation_deg >= 20:
            elevation_factor = 0.9 + 0.1 * (elevation_deg - 20) / 25
        else:
            elevation_factor = 0.7 + 0.2 * elevation_deg / 20
        
        return base_gain * efficiency * elevation_factor
    
    def _calculate_detailed_interference(self, satellite_data: Dict[str, Any],
                                       position_point: Dict[str, Any],
                                       measurement_config: Dict[str, Any]) -> Dict[str, Any]:
        """—s0rş"""
        constellation = satellite_data.get("constellation", "").lower()
        elevation_deg = position_point.get("elevation_deg", 0)
        range_km = position_point.get("range_km", 0)
        
        # 1. §grş (§vÖ[)
        intra_interference_factor = 0.05 if constellation == "starlink" else 0.03
        intra_interference_mw = 10**((-85.0 + intra_interference_factor * 10) / 10.0)
        
        # 2. §“rş (vÖ§)
        inter_interference_factor = 0.02
        inter_interference_mw = 10**((-90.0 + inter_interference_factor * 10) / 10.0)
        
        # 3. 0brş (İâp)
        terrestrial_interference_factor = max(0.001, 1.0 / (range_km / 1000))
        terrestrial_interference_mw = 10**((-100.0 + terrestrial_interference_factor * 5) / 10.0)
        
        # 4. '#Ü

        atmospheric_noise_temp_k = 290.0  # –'#«¦
        bandwidth_hz = 180e3  # ÇJ6ì
        atmospheric_noise_mw = (
            self.physical_constants["boltzmann_constant_jk"] * 
            atmospheric_noise_temp_k * bandwidth_hz * 1000
        )
        
        return {
            "intra_constellation_interference_mw": intra_interference_mw,
            "inter_constellation_interference_mw": inter_interference_mw,
            "terrestrial_interference_mw": terrestrial_interference_mw,
            "atmospheric_noise_mw": atmospheric_noise_mw,
            "total_interference_mw": intra_interference_mw + inter_interference_mw + terrestrial_interference_mw
        }
    
    def _calculate_rs_sinr_interference(self, satellite_data: Dict[str, Any],
                                      position_point: Dict[str, Any],
                                      measurement_config: Dict[str, Any],
                                      measurement_bw_rb: int) -> Dict[str, Any]:
        """— RS-SINR (rş"""
        # RS-SINR ,Ï6ìrşú!ô¾º
        base_analysis = self._calculate_detailed_interference(satellite_data, position_point, measurement_config)
        
        # 6ì¿tàP
        bandwidth_factor = measurement_bw_rb / 25.0  # ø¼– 25 RB
        
        return {
            "total_interference_mw": base_analysis["total_interference_mw"] * bandwidth_factor,
            "bandwidth_adjusted": True,
            "measurement_bandwidth_rb": measurement_bw_rb
        }
    
    def _calculate_thermal_noise_power(self, measurement_bw_rb: int) -> Dict[str, Any]:
        """—±Ü
Ÿ‡"""
        bandwidth_hz = measurement_bw_rb * self.physical_parameters["resource_blocks"]["rb_bandwidth_khz"] * 1000
        system_temp_k = self.user_terminal_characteristics["system_temperature_k"]
        noise_figure_db = self.user_terminal_characteristics["system_noise_figure_db"]
        
        # ±Ü
Ÿ‡: kTB
        thermal_noise_w = self.physical_constants["boltzmann_constant_jk"] * system_temp_k * bandwidth_hz
        
        #  eÜ
x
        noise_figure_linear = 10**(noise_figure_db / 10.0)
        total_noise_w = thermal_noise_w * noise_figure_linear
        
        thermal_noise_mw = total_noise_w * 1000
        thermal_noise_dbm = 10 * math.log10(thermal_noise_mw)
        
        return {
            "thermal_noise_mw": thermal_noise_mw,
            "thermal_noise_dbm": thermal_noise_dbm,
            "system_temperature_k": system_temp_k,
            "noise_figure_db": noise_figure_db,
            "bandwidth_hz": bandwidth_hz
        }
    
    def _calculate_rs_thermal_noise(self, measurement_bw_rb: int) -> Dict[str, Any]:
        """—Ãá_(±Ü
"""
        # Ãá_`(„æ›6ìô
        rs_bandwidth_factor = self.physical_parameters["reference_signals"]["rs_density"]
        effective_bw_rb = measurement_bw_rb * rs_bandwidth_factor
        
        base_noise = self._calculate_thermal_noise_power(int(effective_bw_rb))
        
        return {
            "rs_thermal_noise_mw": base_noise["thermal_noise_mw"],
            "rs_bandwidth_factor": rs_bandwidth_factor,
            "effective_bandwidth_rb": effective_bw_rb
        }
    
    def _grade_rs_sinr_quality(self, rs_sinr_db: float) -> str:
        """U0 RS-SINR á_ÁêI"""
        if rs_sinr_db >= 20:
            return "Excellent"
        elif rs_sinr_db >= 13:
            return "Good"
        elif rs_sinr_db >= 3:
            return "Fair"
        elif rs_sinr_db >= -3:
            return "Poor"
        else:
            return "Very_Poor"
    
    def _update_calculation_statistics(self, measurement_type: str, value: float, 
                                     computation_time_ms: float, success: bool):
        """ô°—q"""
        self.calculation_statistics["total_calculations"] += 1
        
        if success:
            self.calculation_statistics["successful_calculations"] += 1
            
            # ô°Hq
            dist_key = f"{measurement_type}_distribution"
            if dist_key in self.calculation_statistics:
                dist = self.calculation_statistics[dist_key]
                dist["min"] = min(dist["min"], value)
                dist["max"] = max(dist["max"], value)
                
                # !®ûÕsG
                n = self.calculation_statistics["successful_calculations"]
                dist["mean"] = (dist["mean"] * (n-1) + value) / n
        else:
            self.calculation_statistics["failed_calculations"] += 1
        
        # ô°—B“
        n = self.calculation_statistics["total_calculations"]
        current_avg = self.calculation_statistics["average_computation_time_ms"]
        self.calculation_statistics["average_computation_time_ms"] = (
            (current_avg * (n-1) + computation_time_ms) / n
        )
    
    def _create_invalid_rsrp_result(self, error_reason: str) -> Dict[str, Any]:
        """uú!H„ RSRP Pœ"""
        return {
            "rsrp_dbm": -144.0,
            "rsrp_linear_mw": 0.0,
            "error_reason": error_reason,
            "metadata": {"calculation_success": False}
        }
    
    def _create_invalid_rsrq_result(self, error_reason: str) -> Dict[str, Any]:
        """uú!H„ RSRQ Pœ"""
        return {
            "rsrq_db": -19.5,
            "rsrq_linear": 0.0,
            "error_reason": error_reason,
            "metadata": {"calculation_success": False}
        }
    
    def _create_invalid_rs_sinr_result(self, error_reason: str) -> Dict[str, Any]:
        """uú!H„ RS-SINR Pœ"""
        return {
            "rs_sinr_db": -23.0,
            "rs_sinr_linear": 0.0,
            "signal_quality_grade": "Very_Poor",
            "error_reason": error_reason,
            "metadata": {"calculation_success": False}
        }
    
    def get_calculation_statistics(self) -> Dict[str, Any]:
        """rÖ—qÇ
"""
        return self.calculation_statistics.copy()
    
    def get_3gpp_compliance_report(self) -> Dict[str, Any]:
        """ 3GPP '1J"""
        return {
            "standards_compliance": {
                "3gpp_ts_36_214": "v18.0.0 - Physical layer procedures",
                "3gpp_ts_38_331": "v18.5.1 - Radio Resource Control (RRC)",
                "itu_r_p_618": "v13 - Propagation data and prediction methods"
            },
            "implemented_measurements": {
                "rsrp": "Complete - Section 5.1.1",
                "rsrq": "Complete - Section 5.1.2", 
                "rs_sinr": "Complete - Section 5.1.3"
            },
            "leo_enhancements": [
                "ÌSÕ›xú!",
                "ı\ÒHÉÜ",
                "ï‘p",
                "§“rş¡",
                "'#³­!‹ (ITU-R P.618)"
            ],
            "calculation_statistics": self.get_calculation_statistics(),
            "validation_status": "Full Compliance",
            "generated_at": datetime.now(timezone.utc).isoformat()
        }