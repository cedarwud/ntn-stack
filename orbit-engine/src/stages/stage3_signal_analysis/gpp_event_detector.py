"""
3GPP Event Detector for Stage 3 Signal Analysis

Implements 3GPP NTN standard event detection according to documentation requirements:
- A4 Event: Neighbor satellite signal better than threshold
- A5 Event: Serving satellite worse AND neighbor satellite better
- D2 Event: Distance-based handover trigger

Based on 3GPP TS 38.331 and 3GPP TS 38.821 (NTN specifications)
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone


class GPPEventDetector:
    """
    3GPP Event Detector for NTN satellite handover events.

    Implements standard 3GPP measurement events adapted for NTN scenarios:
    - A4: Neighbor becomes better than threshold
    - A5: Serving becomes worse than threshold1 AND neighbor becomes better than threshold2
    - D2: Distance-based handover (NTN-specific)
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize GPP Event Detector with 3GPP standard thresholds."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = config or {}

        # 3GPP Event Thresholds (from documentation)
        self.thresholds = {
            'a4_threshold_dbm': self.config.get('a4_threshold_dbm', -100),      # A4 event threshold
            'a5_threshold1_dbm': self.config.get('a5_threshold1_dbm', -110),    # A5 serving threshold
            'a5_threshold2_dbm': self.config.get('a5_threshold2_dbm', -95),     # A5 neighbor threshold
            'd2_distance_km': self.config.get('d2_distance_km', 1500),          # D2 distance threshold
            'hysteresis_db': self.config.get('hysteresis_db', 2.0),             # Hysteresis value
            'time_to_trigger_ms': self.config.get('time_to_trigger_ms', 320)    # Time to trigger
        }

        # Event counters for monitoring
        self.event_stats = {
            'a4_events_detected': 0,
            'a5_events_detected': 0,
            'd2_events_detected': 0,
            'total_satellites_evaluated': 0
        }

        self.logger.info("3GPP Event Detector initialized with NTN thresholds")

    def detect_a4_events(self, satellites: Dict[str, Any], threshold_dbm: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        Detect A4 events: Neighbor satellite becomes better than threshold.

        3GPP Definition: Neighbor becomes offset better than threshold

        Args:
            satellites: Dictionary of satellite data with signal quality
            threshold_dbm: Optional custom threshold (uses config default if None)

        Returns:
            List of A4 event detections
        """
        threshold = threshold_dbm or self.thresholds['a4_threshold_dbm']
        a4_events = []

        try:
            for satellite_id, satellite_data in satellites.items():
                self.event_stats['total_satellites_evaluated'] += 1

                # Extract signal quality
                signal_analysis = satellite_data.get('signal_analysis', {})
                signal_stats = signal_analysis.get('signal_statistics', {})
                rsrp_dbm = signal_stats.get('average_rsrp', -999)

                # Check A4 condition: RSRP > threshold + hysteresis
                if rsrp_dbm > (threshold + self.thresholds['hysteresis_db']):
                    a4_event = {
                        'event_type': 'A4',
                        'satellite_id': satellite_id,
                        'rsrp_dbm': rsrp_dbm,
                        'threshold_dbm': threshold,
                        'margin_db': rsrp_dbm - threshold,
                        'timestamp': datetime.now(timezone.utc).isoformat(),
                        'description': f'Neighbor {satellite_id} better than threshold'
                    }

                    a4_events.append(a4_event)
                    self.event_stats['a4_events_detected'] += 1

                    self.logger.debug(f"A4 event: {satellite_id} RSRP={rsrp_dbm:.1f}dBm > {threshold:.1f}dBm")

            return a4_events

        except Exception as e:
            self.logger.error(f"A4 event detection failed: {e}")
            return []

    def detect_a5_events(self, serving_satellite: Dict[str, Any],
                        neighbor_satellites: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detect A5 events: Serving satellite worse than threshold1 AND neighbor better than threshold2.

        3GPP Definition: Serving becomes worse than threshold1 AND neighbor becomes better than threshold2

        Args:
            serving_satellite: Current serving satellite data
            neighbor_satellites: Dictionary of neighbor satellite data

        Returns:
            List of A5 event detections
        """
        a5_events = []

        try:
            # Extract serving satellite signal quality
            serving_signal = serving_satellite.get('signal_analysis', {}).get('signal_statistics', {})
            serving_rsrp = serving_signal.get('average_rsrp', -999)
            serving_id = serving_satellite.get('satellite_id', 'unknown')

            # Check serving condition: RSRP < threshold1 - hysteresis
            threshold1 = self.thresholds['a5_threshold1_dbm']
            threshold2 = self.thresholds['a5_threshold2_dbm']

            if serving_rsrp < (threshold1 - self.thresholds['hysteresis_db']):

                # Check neighbor satellites for threshold2 condition
                for neighbor_id, neighbor_data in neighbor_satellites.items():
                    neighbor_signal = neighbor_data.get('signal_analysis', {}).get('signal_statistics', {})
                    neighbor_rsrp = neighbor_signal.get('average_rsrp', -999)

                    # Check neighbor condition: RSRP > threshold2 + hysteresis
                    if neighbor_rsrp > (threshold2 + self.thresholds['hysteresis_db']):
                        a5_event = {
                            'event_type': 'A5',
                            'serving_satellite_id': serving_id,
                            'neighbor_satellite_id': neighbor_id,
                            'serving_rsrp_dbm': serving_rsrp,
                            'neighbor_rsrp_dbm': neighbor_rsrp,
                            'threshold1_dbm': threshold1,
                            'threshold2_dbm': threshold2,
                            'rsrp_difference_db': neighbor_rsrp - serving_rsrp,
                            'timestamp': datetime.now(timezone.utc).isoformat(),
                            'description': f'Serving {serving_id} poor, neighbor {neighbor_id} good'
                        }

                        a5_events.append(a5_event)
                        self.event_stats['a5_events_detected'] += 1

                        self.logger.debug(f"A5 event: serving={serving_rsrp:.1f}dBm, neighbor={neighbor_rsrp:.1f}dBm")

            return a5_events

        except Exception as e:
            self.logger.error(f"A5 event detection failed: {e}")
            return []

    def detect_d2_events(self, satellites: Dict[str, Any],
                        distance_threshold_km: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        Detect D2 events: Distance-based handover trigger (NTN-specific).

        NTN-specific event for satellite handover based on distance criteria.

        Args:
            satellites: Dictionary of satellite data with orbital information
            distance_threshold_km: Optional custom distance threshold

        Returns:
            List of D2 event detections
        """
        threshold_km = distance_threshold_km or self.thresholds['d2_distance_km']
        d2_events = []

        try:
            for satellite_id, satellite_data in satellites.items():
                # Extract orbital data
                satellite_orbit = satellite_data.get('satellite_data', {})
                orbital_data = satellite_orbit.get('orbital_data', {})
                distance_km = orbital_data.get('distance_km', 0)
                elevation_deg = orbital_data.get('elevation_deg', 0)

                # D2 condition: Distance exceeds threshold OR elevation very low
                distance_exceeded = distance_km > threshold_km
                low_elevation = elevation_deg < 5.0  # Very low elevation trigger

                if distance_exceeded or low_elevation:
                    d2_event = {
                        'event_type': 'D2',
                        'satellite_id': satellite_id,
                        'distance_km': distance_km,
                        'elevation_deg': elevation_deg,
                        'distance_threshold_km': threshold_km,
                        'trigger_reason': 'distance_exceeded' if distance_exceeded else 'low_elevation',
                        'timestamp': datetime.now(timezone.utc).isoformat(),
                        'description': f'Distance/elevation handover trigger for {satellite_id}'
                    }

                    d2_events.append(d2_event)
                    self.event_stats['d2_events_detected'] += 1

                    self.logger.debug(f"D2 event: {satellite_id} dist={distance_km:.1f}km, elev={elevation_deg:.1f}°")

            return d2_events

        except Exception as e:
            self.logger.error(f"D2 event detection failed: {e}")
            return []

    def analyze_all_gpp_events(self, satellites_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze all 3GPP events for the given satellite data.

        Args:
            satellites_data: Complete satellite analysis data

        Returns:
            Comprehensive 3GPP event analysis results
        """
        try:
            analysis_start = datetime.now(timezone.utc)

            # Detect A4 events (all satellites as potential neighbors)
            a4_events = self.detect_a4_events(satellites_data)

            # For A5 events, we need to determine serving vs neighbors
            # For this implementation, we'll use the best signal satellite as serving
            serving_satellite = self._identify_serving_satellite(satellites_data)
            neighbor_satellites = {k: v for k, v in satellites_data.items()
                                 if k != serving_satellite.get('satellite_id')}

            a5_events = self.detect_a5_events(serving_satellite, neighbor_satellites) if serving_satellite else []

            # Detect D2 events
            d2_events = self.detect_d2_events(satellites_data)

            # Compile comprehensive results
            all_events = a4_events + a5_events + d2_events

            results = {
                'analysis_timestamp': analysis_start.isoformat(),
                'total_satellites_analyzed': len(satellites_data),
                'event_summary': {
                    'total_events': len(all_events),
                    'a4_events': len(a4_events),
                    'a5_events': len(a5_events),
                    'd2_events': len(d2_events)
                },
                'events_by_type': {
                    'A4': a4_events,
                    'A5': a5_events,
                    'D2': d2_events
                },
                'all_events': all_events,
                'thresholds_used': self.thresholds.copy(),
                'cumulative_stats': self.event_stats.copy()
            }

            self.logger.info(f"3GPP event analysis: {len(all_events)} total events detected")

            return results

        except Exception as e:
            self.logger.error(f"Complete 3GPP event analysis failed: {e}")
            return {
                'error': str(e),
                'analysis_timestamp': datetime.now(timezone.utc).isoformat()
            }

    def _identify_serving_satellite(self, satellites_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Identify the serving satellite (typically the one with best signal quality).

        Args:
            satellites_data: Dictionary of satellite data

        Returns:
            Serving satellite data or None if no suitable satellite found
        """
        try:
            best_satellite = None
            best_rsrp = -999.0

            for satellite_id, satellite_data in satellites_data.items():
                signal_analysis = satellite_data.get('signal_analysis', {})
                signal_stats = signal_analysis.get('signal_statistics', {})
                rsrp = signal_stats.get('average_rsrp', -999)

                if rsrp > best_rsrp:
                    best_rsrp = rsrp
                    best_satellite = satellite_data
                    best_satellite['satellite_id'] = satellite_id

            return best_satellite

        except Exception as e:
            self.logger.error(f"Serving satellite identification failed: {e}")
            return None

    def get_event_statistics(self) -> Dict[str, Any]:
        """
        Get cumulative event detection statistics.

        Returns:
            Dictionary containing event statistics
        """
        return {
            'cumulative_stats': self.event_stats.copy(),
            'thresholds': self.thresholds.copy(),
            'last_updated': datetime.now(timezone.utc).isoformat()
        }

    def reset_statistics(self):
        """Reset cumulative event statistics."""
        for key in self.event_stats:
            self.event_stats[key] = 0
        self.logger.info("Event statistics reset")