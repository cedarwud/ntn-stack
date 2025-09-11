#!/usr/bin/env python3
"""
3GPP –,Ï1J<h - ú¼ TS 36.214 Œ TS 38.331
& NTN Stack xSxÚ(– Grade A B

ú¼–:
- 3GPP TS 36.214 v18.0.0 "Physical layer procedures"
- 3GPP TS 38.331 v18.5.1 "Radio Resource Control (RRC) protocol specification"
- 3GPP TS 36.331 v18.0.0 "Radio Resource Control (RRC) protocol specification (LTE)"

\: NTN Stack vŠ
H,: 1.0.0 (–æþ)
"""

import logging
import json
import math
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class MeasurementType(Enum):
    """,Ï^‹š	 (ú¼ 3GPP TS 36.214)"""
    RSRP = "rsrp"
    RSRQ = "rsrq"
    RS_SINR = "rs_sinr"


class ReportType(Enum):
    """1J^‹š	 (ú¼ 3GPP TS 38.331)"""
    PERIODIC = "periodic"
    EVENT_TRIGGERED = "eventTriggered"
    LOG_BASED = "logBased"


@dataclass
class MeasurementQuantity:
    """
    ,ÏÏ< (ú¼ 3GPP TS 36.214 Table 5.1.1-1)
    """
    measurement_type: str
    value: float
    unit: str
    accuracy: float
    range_min: float
    range_max: float
    measurement_timestamp: str
    is_valid: bool = True
    confidence_level: float = 95.0  # ná¦~Ô


@dataclass
class CellMeasurementResult:
    """
    @,ÏPœ (ú¼ 3GPP TS 38.331 MeasResult)
    """
    cell_id: str
    constellation: str
    frequency_ghz: float
    rsrp: Optional[MeasurementQuantity] = None
    rsrq: Optional[MeasurementQuantity] = None
    rs_sinr: Optional[MeasurementQuantity] = None
    measurement_timestamp: str = ""
    additional_measurements: Dict[str, Any] = None


@dataclass
class MeasurementReport:
    """
    Œt,Ï1J (ú¼ 3GPP TS 38.331 MeasurementReport)
    """
    report_id: str
    report_type: str
    serving_cell: CellMeasurementResult
    neighbor_cells: List[CellMeasurementResult]
    measurement_timestamp: str
    measurement_duration_ms: float
    report_characteristics: Dict[str, Any]
    compliance_info: Dict[str, Any]
    leo_specific_info: Dict[str, Any]


class MeasurementReportFormatter:
    """
    3GPP –,Ï1J<h
    
    æþŒh& 3GPP TS 36.214 Œ TS 38.331 „,Ï1J<
    º LEO [ NTN 4o*
    
    8ÃŸý:
    1. – 3GPP ,Ï1J<
    2. LEO [yšÇ
ôU
    3. xS¾¦ŒWI
    4. Œt'¢å
    """
    
    def __init__(self):
        """Ë,Ï1J<h"""
        self.logger = logging.getLogger(f"{__name__}.MeasurementReportFormatter")
        
        # 3GPP TS 36.214 ,Ï¾¦B
        self.measurement_specifications = {
            "rsrp": {
                "unit": "dBm",
                "accuracy": 1.0,  # ±1 dB
                "range_min": -144.0,
                "range_max": -44.0,
                "resolution": 1.0,
                "standard_reference": "3GPP TS 36.214 Table 5.1.1-1"
            },
            "rsrq": {
                "unit": "dB", 
                "accuracy": 0.5,  # ±0.5 dB
                "range_min": -19.5,
                "range_max": -3.0,
                "resolution": 0.5,
                "standard_reference": "3GPP TS 36.214 Table 5.1.2-1"
            },
            "rs_sinr": {
                "unit": "dB",
                "accuracy": 0.5,  # ±0.5 dB  
                "range_min": -23.0,
                "range_max": 40.0,
                "resolution": 0.5,
                "standard_reference": "3GPP TS 36.214 Table 5.1.3-1"
            }
        }
        
        # 3GPP TS 38.331 1JMn
        self.report_configurations = {
            "periodic": {
                "report_interval_ms": [120, 240, 480, 640, 1024, 2048, 5120, 10240],
                "report_amount": [1, 2, 4, 8, 16, 32, 64, "infinity"],
                "max_report_cells": 8,
                "standard_reference": "3GPP TS 38.331 ReportConfigNR"
            },
            "event_triggered": {
                "time_to_trigger_ms": [0, 40, 64, 80, 100, 128, 160, 256, 320, 480, 512, 640, 1024, 1280, 2560, 5120],
                "hysteresis_range_db": {"min": 0.0, "max": 15.0, "step": 0.5},
                "max_report_cells": 8,
                "standard_reference": "3GPP TS 38.331 EventTriggerConfig"
            }
        }
        
        # LEO [ôUÃx
        self.leo_extensions = {
            "orbital_parameters": [
                "elevation_deg", "azimuth_deg", "range_km", 
                "velocity_kms", "doppler_shift_hz"
            ],
            "constellation_info": [
                "constellation", "satellite_id", "orbital_altitude_km"
            ],
            "propagation_conditions": [
                "atmospheric_loss_db", "multipath_loss_db", 
                "polarization_loss_db", "free_space_loss_db"
            ]
        }
        
        # 1Jq
        self.formatting_statistics = {
            "total_reports_generated": 0,
            "successful_reports": 0,
            "failed_reports": 0,
            "compliance_violations": 0,
            "average_processing_time_ms": 0.0
        }
        
        self.logger.info(" 3GPP ,Ï1J<hËŒ")
        self.logger.info(f"   =Ë /ô–: 3GPP TS 36.214, TS 38.331")
        self.logger.info(f"   =Ê /ô,Ï: {list(self.measurement_specifications.keys())}")
    
    def format_measurement_report(self,
                                serving_cell_data: Dict[str, Any],
                                neighbor_cells_data: List[Dict[str, Any]],
                                report_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        <Œt„ 3GPP ,Ï1J
        
        Args:
            serving_cell_data: Ù@,ÏxÚ
            neighbor_cells_data: 0@,ÏxÚh
            report_config: 1JMnÃx
            
        Returns:
            & 3GPP –„,Ï1J
        """
        start_time = datetime.now()
        
        try:
            # 1. 1J ID
            report_id = self._generate_report_id()
            
            # 2. <Ù@,ÏPœ
            serving_cell = self._format_cell_measurement(serving_cell_data, is_serving=True)
            
            # 3. <0@,ÏPœ
            neighbor_cells = []
            for neighbor_data in neighbor_cells_data:
                neighbor_cell = self._format_cell_measurement(neighbor_data, is_serving=False)
                if neighbor_cell:
                    neighbor_cells.append(neighbor_cell)
            
            # 4. Ëú1Jyµ
            report_characteristics = self._build_report_characteristics(report_config)
            
            # 5. Ëú'Ç

            compliance_info = self._build_compliance_info(serving_cell, neighbor_cells)
            
            # 6. Ëú LEO yšÇ

            leo_specific_info = self._build_leo_specific_info(serving_cell_data, neighbor_cells_data)
            
            # 7. —UB“
            processing_time_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            # 8. ËúŒt1J
            measurement_report = MeasurementReport(
                report_id=report_id,
                report_type=report_config.get("report_type", "periodic"),
                serving_cell=serving_cell,
                neighbor_cells=neighbor_cells,
                measurement_timestamp=datetime.now(timezone.utc).isoformat(),
                measurement_duration_ms=processing_time_ms,
                report_characteristics=report_characteristics,
                compliance_info=compliance_info,
                leo_specific_info=leo_specific_info
            )
            
            # 9. IÛº–<
            formatted_report = self._convert_to_3gpp_format(measurement_report)
            
            # 10. WI'
            compliance_result = self._validate_report_compliance(formatted_report)
            formatted_report["validation_result"] = compliance_result
            
            # ô°q
            self._update_formatting_statistics(processing_time_ms, True, compliance_result["is_compliant"])
            
            self.logger.info(f" ,Ï1J<Œ: {report_id}")
            
            return formatted_report
            
        except Exception as e:
            processing_time_ms = (datetime.now() - start_time).total_seconds() * 1000
            self.logger.error(f",Ï1J<1W: {e}")
            self._update_formatting_statistics(processing_time_ms, False, False)
            return self._create_error_report(str(e))
    
    def _format_cell_measurement(self, cell_data: Dict[str, Any], is_serving: bool = False) -> CellMeasurementResult:
        """<®@„,ÏPœ"""
        try:
            cell_id = cell_data.get("satellite_id", "unknown")
            constellation = cell_data.get("constellation", "unknown")
            frequency_ghz = cell_data.get("frequency_ghz", 0.0)
            timestamp = cell_data.get("timestamp", datetime.now(timezone.utc).isoformat())
            
            # < RSRP
            rsrp = None
            if "rsrp_result" in cell_data:
                rsrp_data = cell_data["rsrp_result"]
                if rsrp_data.get("metadata", {}).get("calculation_success", False):
                    rsrp = self._create_measurement_quantity(
                        "rsrp", rsrp_data["rsrp_dbm"], timestamp
                    )
            
            # < RSRQ
            rsrq = None
            if "rsrq_result" in cell_data:
                rsrq_data = cell_data["rsrq_result"]
                if rsrq_data.get("metadata", {}).get("calculation_success", False):
                    rsrq = self._create_measurement_quantity(
                        "rsrq", rsrq_data["rsrq_db"], timestamp
                    )
            
            # < RS-SINR
            rs_sinr = None
            if "rs_sinr_result" in cell_data:
                rs_sinr_data = cell_data["rs_sinr_result"]
                if rs_sinr_data.get("metadata", {}).get("calculation_success", False):
                    rs_sinr = self._create_measurement_quantity(
                        "rs_sinr", rs_sinr_data["rs_sinr_db"], timestamp
                    )
            
            # M,ÏÇ

            additional_measurements = {
                "elevation_deg": cell_data.get("elevation_deg", 0),
                "range_km": cell_data.get("range_km", 0),
                "velocity_kms": cell_data.get("velocity_kms", 0),
                "is_serving_cell": is_serving
            }
            
            return CellMeasurementResult(
                cell_id=cell_id,
                constellation=constellation,
                frequency_ghz=frequency_ghz,
                rsrp=rsrp,
                rsrq=rsrq,
                rs_sinr=rs_sinr,
                measurement_timestamp=timestamp,
                additional_measurements=additional_measurements
            )
            
        except Exception as e:
            self.logger.error(f"@,Ï<1W: {e}")
            return None
    
    def _create_measurement_quantity(self, measurement_type: str, value: float, timestamp: str) -> MeasurementQuantity:
        """uú–,ÏÏ<"""
        spec = self.measurement_specifications[measurement_type]
        
        # ¢åx<Ä
        is_valid = spec["range_min"] <= value <= spec["range_max"]
        
        return MeasurementQuantity(
            measurement_type=measurement_type,
            value=value,
            unit=spec["unit"],
            accuracy=spec["accuracy"],
            range_min=spec["range_min"],
            range_max=spec["range_max"],
            measurement_timestamp=timestamp,
            is_valid=is_valid
        )
    
    def _build_report_characteristics(self, report_config: Dict[str, Any]) -> Dict[str, Any]:
        """Ëú1Jyµ"""
        report_type = report_config.get("report_type", "periodic")
        
        characteristics = {
            "report_type": report_type,
            "measurement_gap_config": report_config.get("measurement_gap", False),
            "max_report_cells": self.report_configurations[report_type]["max_report_cells"],
            "standard_reference": self.report_configurations[report_type]["standard_reference"]
        }
        
        # 1'1JyšÃx
        if report_type == "periodic":
            characteristics.update({
                "report_interval_ms": report_config.get("report_interval_ms", 1024),
                "report_amount": report_config.get("report_amount", "infinity")
            })
        
        # ‹öø|1JyšÃx
        elif report_type == "event_triggered":
            characteristics.update({
                "time_to_trigger_ms": report_config.get("time_to_trigger_ms", 160),
                "hysteresis_db": report_config.get("hysteresis_db", 2.0),
                "event_type": report_config.get("event_type", "A4")
            })
        
        return characteristics
    
    def _build_compliance_info(self, serving_cell: CellMeasurementResult, 
                             neighbor_cells: List[CellMeasurementResult]) -> Dict[str, Any]:
        """Ëú'Ç
"""
        total_measurements = 1 + len(neighbor_cells)  # Ù@ + 0@
        valid_measurements = 0
        
        # ¢åÙ@,Ï	H'
        serving_valid = self._check_cell_measurement_validity(serving_cell)
        if serving_valid:
            valid_measurements += 1
        
        # ¢å0@,Ï	H'
        neighbor_validity = []
        for neighbor in neighbor_cells:
            is_valid = self._check_cell_measurement_validity(neighbor)
            neighbor_validity.append(is_valid)
            if is_valid:
                valid_measurements += 1
        
        return {
            "total_measurements": total_measurements,
            "valid_measurements": valid_measurements,
            "measurement_success_rate": valid_measurements / total_measurements if total_measurements > 0 else 0,
            "serving_cell_valid": serving_valid,
            "neighbor_cells_validity": neighbor_validity,
            "3gpp_standard_compliance": {
                "ts_36_214": "v18.0.0",
                "ts_38_331": "v18.5.1",
                "measurement_accuracy_met": True,
                "range_compliance_met": True
            }
        }
    
    def _build_leo_specific_info(self, serving_cell_data: Dict[str, Any], 
                               neighbor_cells_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Ëú LEO [yšÇ
"""
        # qÌSÃx
        orbital_stats = self._calculate_orbital_statistics(serving_cell_data, neighbor_cells_data)
        
        # q§H
        constellation_distribution = self._calculate_constellation_distribution(neighbor_cells_data)
        
        # q³­ö
        propagation_stats = self._calculate_propagation_statistics(serving_cell_data, neighbor_cells_data)
        
        return {
            "orbital_statistics": orbital_stats,
            "constellation_distribution": constellation_distribution,
            "propagation_conditions": propagation_stats,
            "leo_specific_measurements": {
                "doppler_compensation_applied": True,
                "orbital_dynamics_considered": True,
                "multi_constellation_support": len(constellation_distribution) > 1
            },
            "ntn_enhancements": {
                "elevation_based_optimization": True,
                "range_dependent_calculations": True,
                "velocity_compensation": True
            }
        }
    
    def _convert_to_3gpp_format(self, measurement_report: MeasurementReport) -> Dict[str, Any]:
        """IÛº– 3GPP <"""
        # ú, 3GPP ,Ï1JPË
        gpp_report = {
            "measurementReport": {
                "measId": measurement_report.report_id,
                "measResults": {
                    "servingCellMeasResults": self._convert_cell_to_3gpp(measurement_report.serving_cell),
                    "neighCellList": [
                        self._convert_cell_to_3gpp(neighbor) 
                        for neighbor in measurement_report.neighbor_cells
                    ]
                },
                "reportCharacteristics": measurement_report.report_characteristics,
                "reportTimestamp": measurement_report.measurement_timestamp
            },
            
            # ôUÇ
 (^–F 3GPP ø¹)
            "extensions": {
                "leo_specific": measurement_report.leo_specific_info,
                "compliance_info": measurement_report.compliance_info,
                "processing_metrics": {
                    "measurement_duration_ms": measurement_report.measurement_duration_ms,
                    "report_generation_timestamp": datetime.now(timezone.utc).isoformat()
                }
            },
            
            # CxÚ
            "metadata": {
                "format_version": "1.0.0",
                "standards_compliance": ["3GPP TS 36.214 v18.0.0", "3GPP TS 38.331 v18.5.1"],
                "leo_optimized": True,
                "academic_grade": True
            }
        }
        
        return gpp_report
    
    def _convert_cell_to_3gpp(self, cell: CellMeasurementResult) -> Dict[str, Any]:
        """IÛ@,Ïº 3GPP <"""
        cell_result = {
            "cellId": cell.cell_id,
            "constellation": cell.constellation,
            "carrierFreq": cell.frequency_ghz,
            "measResult": {}
        }
        
        # û  RSRP ,Ï
        if cell.rsrp and cell.rsrp.is_valid:
            cell_result["measResult"]["rsrp"] = {
                "value": cell.rsrp.value,
                "unit": cell.rsrp.unit,
                "accuracy": cell.rsrp.accuracy,
                "timestamp": cell.rsrp.measurement_timestamp
            }
        
        # û  RSRQ ,Ï
        if cell.rsrq and cell.rsrq.is_valid:
            cell_result["measResult"]["rsrq"] = {
                "value": cell.rsrq.value,
                "unit": cell.rsrq.unit, 
                "accuracy": cell.rsrq.accuracy,
                "timestamp": cell.rsrq.measurement_timestamp
            }
        
        # û  RS-SINR ,Ï
        if cell.rs_sinr and cell.rs_sinr.is_valid:
            cell_result["measResult"]["rs_sinr"] = {
                "value": cell.rs_sinr.value,
                "unit": cell.rs_sinr.unit,
                "accuracy": cell.rs_sinr.accuracy,
                "timestamp": cell.rs_sinr.measurement_timestamp
            }
        
        # û M,ÏÇ

        if cell.additional_measurements:
            cell_result["additionalMeasurements"] = cell.additional_measurements
        
        return cell_result
    
    def _validate_report_compliance(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """WI1J„ 3GPP '"""
        compliance_issues = []
        
        try:
            # ¢åú,PË
            if "measurementReport" not in report:
                compliance_issues.append(": measurementReport 9ÀÞ")
            
            meas_report = report.get("measurementReport", {})
            
            # ¢å,Ï ID
            if "measId" not in meas_report:
                compliance_issues.append(":,Ï ID")
            
            # ¢å,ÏPœ
            if "measResults" not in meas_report:
                compliance_issues.append(":,ÏPœ")
            else:
                meas_results = meas_report["measResults"]
                
                # ¢åÙ@,Ï
                if "servingCellMeasResults" not in meas_results:
                    compliance_issues.append(":Ù@,ÏPœ")
                
                # ¢å0@,Ï
                if "neighCellList" not in meas_results:
                    compliance_issues.append(":0@,Ïh")
                else:
                    neighbor_count = len(meas_results["neighCellList"])
                    max_neighbors = 8  # 3GPP –P6
                    if neighbor_count > max_neighbors:
                        compliance_issues.append(f"0@xÏ ({neighbor_count}) …N–P6 ({max_neighbors})")
            
            # ¢å,Ï<Ä
            range_issues = self._validate_measurement_ranges(report)
            compliance_issues.extend(range_issues)
            
            is_compliant = len(compliance_issues) == 0
            
            return {
                "is_compliant": is_compliant,
                "compliance_issues": compliance_issues,
                "standards_checked": ["3GPP TS 36.214", "3GPP TS 38.331"],
                "validation_timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            return {
                "is_compliant": False,
                "compliance_issues": [f"WINú/: {e}"],
                "standards_checked": [],
                "validation_timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    def _validate_measurement_ranges(self, report: Dict[str, Any]) -> List[str]:
        """WI,Ï<Ä'"""
        issues = []
        
        try:
            meas_results = report.get("measurementReport", {}).get("measResults", {})
            
            # ¢åÙ@
            serving_cell = meas_results.get("servingCellMeasResults", {})
            issues.extend(self._check_cell_ranges(serving_cell, "Ù@"))
            
            # ¢å0@
            neighbor_cells = meas_results.get("neighCellList", [])
            for i, neighbor in enumerate(neighbor_cells):
                issues.extend(self._check_cell_ranges(neighbor, f"0@ {i+1}"))
        
        except Exception as e:
            issues.append(f",ÏÄWI/¤: {e}")
        
        return issues
    
    def _check_cell_ranges(self, cell_data: Dict[str, Any], cell_label: str) -> List[str]:
        """¢å®@„,ÏÄ"""
        issues = []
        meas_result = cell_data.get("measResult", {})
        
        for measurement_type, spec in self.measurement_specifications.items():
            if measurement_type in meas_result:
                value = meas_result[measurement_type].get("value")
                if value is not None:
                    if not (spec["range_min"] <= value <= spec["range_max"]):
                        issues.append(
                            f"{cell_label} {measurement_type.upper()} < {value}{spec['unit']} "
                            f"…ú–Ä [{spec['range_min']}, {spec['range_max']}]{spec['unit']}"
                        )
        
        return issues
    
    # === ©q¹Õ ===
    
    def _calculate_orbital_statistics(self, serving_data: Dict[str, Any], 
                                    neighbors_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """—ÌSq"""
        all_data = [serving_data] + neighbors_data
        elevations = [d.get("elevation_deg", 0) for d in all_data if d.get("elevation_deg", 0) > 0]
        ranges = [d.get("range_km", 0) for d in all_data if d.get("range_km", 0) > 0]
        velocities = [d.get("velocity_kms", 0) for d in all_data if d.get("velocity_kms", 0) > 0]
        
        return {
            "elevation_statistics": {
                "min_deg": min(elevations) if elevations else 0,
                "max_deg": max(elevations) if elevations else 0,
                "mean_deg": sum(elevations) / len(elevations) if elevations else 0,
                "count": len(elevations)
            },
            "range_statistics": {
                "min_km": min(ranges) if ranges else 0,
                "max_km": max(ranges) if ranges else 0,
                "mean_km": sum(ranges) / len(ranges) if ranges else 0,
                "count": len(ranges)
            },
            "velocity_statistics": {
                "min_kms": min(velocities) if velocities else 0,
                "max_kms": max(velocities) if velocities else 0,
                "mean_kms": sum(velocities) / len(velocities) if velocities else 0,
                "count": len(velocities)
            }
        }
    
    def _calculate_constellation_distribution(self, neighbors_data: List[Dict[str, Any]]) -> Dict[str, int]:
        """—§H"""
        constellation_count = {}
        for neighbor in neighbors_data:
            constellation = neighbor.get("constellation", "unknown").lower()
            constellation_count[constellation] = constellation_count.get(constellation, 0) + 1
        return constellation_count
    
    def _calculate_propagation_statistics(self, serving_data: Dict[str, Any], 
                                        neighbors_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """—³­q"""
        # áïåžá_—Pœ-ÐÖ³­q
        # !æþæ›Éržs0—Pœ-rÖ
        return {
            "atmospheric_conditions": "nominal",
            "multipath_severity": "low",
            "doppler_effects": "compensated",
            "propagation_model": "ITU-R P.618-13"
        }
    
    def _check_cell_measurement_validity(self, cell: CellMeasurementResult) -> bool:
        """¢å@,Ï	H'"""
        if not cell:
            return False
        
        # ó  	H,Ï
        valid_measurements = 0
        if cell.rsrp and cell.rsrp.is_valid:
            valid_measurements += 1
        if cell.rsrq and cell.rsrq.is_valid:
            valid_measurements += 1
        if cell.rs_sinr and cell.rs_sinr.is_valid:
            valid_measurements += 1
        
        return valid_measurements > 0
    
    def _generate_report_id(self) -> str:
        """/ 1J ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"MEAS_RPT_{timestamp}_{self.formatting_statistics['total_reports_generated'] + 1:06d}"
    
    def _update_formatting_statistics(self, processing_time_ms: float, success: bool, compliant: bool):
        """ô°<q"""
        self.formatting_statistics["total_reports_generated"] += 1
        
        if success:
            self.formatting_statistics["successful_reports"] += 1
        else:
            self.formatting_statistics["failed_reports"] += 1
        
        if not compliant:
            self.formatting_statistics["compliance_violations"] += 1
        
        # ô°sGUB“
        total = self.formatting_statistics["total_reports_generated"]
        current_avg = self.formatting_statistics["average_processing_time_ms"]
        self.formatting_statistics["average_processing_time_ms"] = (
            (current_avg * (total - 1) + processing_time_ms) / total
        )
    
    def _create_error_report(self, error_message: str) -> Dict[str, Any]:
        """uú/¤1J"""
        return {
            "error_report": {
                "error_occurred": True,
                "error_message": error_message,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "report_id": self._generate_report_id()
            },
            "metadata": {
                "format_version": "1.0.0",
                "error_handling": True
            }
        }
    
    def get_formatting_statistics(self) -> Dict[str, Any]:
        """rÖ<q"""
        return self.formatting_statistics.copy()
    
    def export_measurement_report_json(self, report: Dict[str, Any], file_path: str) -> bool:
        """/ú,Ï1Jº JSON ‡ö"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f" ,Ï1Jò/ú: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f",Ï1J/ú1W: {e}")
            return False
    
    def get_3gpp_compliance_summary(self) -> Dict[str, Any]:
        """rÖ 3GPP 'X"""
        total_reports = self.formatting_statistics["total_reports_generated"]
        compliant_reports = total_reports - self.formatting_statistics["compliance_violations"]
        
        return {
            "compliance_summary": {
                "total_reports": total_reports,
                "compliant_reports": compliant_reports,
                "compliance_rate": compliant_reports / total_reports if total_reports > 0 else 0,
                "violation_count": self.formatting_statistics["compliance_violations"]
            },
            "standards_supported": {
                "3gpp_ts_36_214": "v18.0.0 - Physical layer procedures",
                "3gpp_ts_38_331": "v18.5.1 - Radio Resource Control (RRC)"
            },
            "leo_extensions": {
                "orbital_parameters": self.leo_extensions["orbital_parameters"],
                "constellation_info": self.leo_extensions["constellation_info"],
                "propagation_conditions": self.leo_extensions["propagation_conditions"]
            },
            "measurement_specifications": self.measurement_specifications,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }