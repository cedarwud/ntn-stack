#!/usr/bin/env python3
"""
Stage 4 Integration Test Suite: Sionna Wireless Channel and AI-RAN Anti-Interference Integration
This test suite verifies the complete functionality of Stage 4 development including:
- Sionna wireless channel model integration with UERANSIM
- AI-RAN anti-interference service optimization
- Real-time data exchange between services
- Wireless channel metrics collection
- Closed-loop interference control mechanism
- Frontend real-time visualization components
"""

import asyncio
import json
import pytest
import requests
import websockets
import time
import logging
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add project paths to Python path
sys.path.append('/home/sat/ntn-stack/netstack/netstack_api')
sys.path.append('/home/sat/ntn-stack/simworld/backend')

# Import services for testing
try:
    from services.sionna_integration_service import SionnaIntegrationService
    from services.ai_ran_anti_interference_service import AIRANAntiInterferenceService
    from services.ai_ran_optimizations import AIRANOptimizer
    from services.sionna_interference_integration import SionnaInterferenceIntegrationService
    from services.unified_metrics_collector import UnifiedMetricsCollector
    from services.closed_loop_interference_control import ClosedLoopInterferenceController
except ImportError as e:
    print(f"Warning: Could not import some services: {e}")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Stage4IntegrationTestSuite:
    """Comprehensive test suite for Stage 4 functionality"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.websocket_url = "ws://localhost:8080"
        self.test_results = {}
        self.performance_metrics = {}
        
    async def setup_test_environment(self):
        """Setup test environment and mock data"""
        logger.info("Setting up Stage 4 test environment...")
        
        # Mock test data
        self.test_ue_positions = [
            {"x": 100.0, "y": 200.0, "z": 10.0, "id": "ue_001"},
            {"x": 150.0, "y": 250.0, "z": 10.0, "id": "ue_002"},
            {"x": 200.0, "y": 300.0, "z": 10.0, "id": "ue_003"}
        ]
        
        self.test_gnb_positions = [
            {"x": 0.0, "y": 0.0, "z": 30.0, "id": "gnb_001"},
            {"x": 300.0, "y": 400.0, "z": 30.0, "id": "gnb_002"}
        ]
        
        self.test_interference_sources = [
            {
                "id": "interference_001",
                "type": "co_channel",
                "position": {"x": 50.0, "y": 100.0, "z": 15.0},
                "power_dbm": 20.0,
                "frequency_ghz": 2.1,
                "bandwidth_mhz": 20.0
            }
        ]
        
        logger.info("Test environment setup completed")

    # Test 1: Sionna Integration Service Testing
    async def test_sionna_integration_service(self) -> Dict[str, Any]:
        """Test Sionna wireless channel model integration with UERANSIM"""
        logger.info("Testing Sionna Integration Service...")
        test_result = {"passed": False, "details": {}, "errors": []}
        
        try:
            # Test 1.1: Channel simulation with interference
            response = await self._test_api_endpoint(
                "/api/sionna/channel-simulation-with-interference",
                method="POST",
                data={
                    "ue_positions": self.test_ue_positions,
                    "gnb_positions": self.test_gnb_positions,
                    "environment_type": "urban",
                    "frequency_ghz": 2.1,
                    "bandwidth_mhz": 20.0,
                    "interference_sources": self.test_interference_sources
                }
            )
            
            if response and response.get('status') == 'success':
                test_result["details"]["channel_simulation"] = "PASS"
                logger.info("✓ Channel simulation with interference: PASS")
            else:
                test_result["details"]["channel_simulation"] = "FAIL"
                test_result["errors"].append("Channel simulation failed")
            
            # Test 1.2: UERANSIM configuration writing
            config_test = await self._test_ueransim_config_generation()
            test_result["details"]["ueransim_config"] = "PASS" if config_test else "FAIL"
            
            # Test 1.3: Real-time channel parameter updates
            update_test = await self._test_realtime_parameter_updates()
            test_result["details"]["realtime_updates"] = "PASS" if update_test else "FAIL"
            
            test_result["passed"] = all(v == "PASS" for v in test_result["details"].values())
            
        except Exception as e:
            test_result["errors"].append(f"Sionna integration test error: {str(e)}")
            logger.error(f"Sionna integration test failed: {e}")
        
        self.test_results["sionna_integration"] = test_result
        return test_result
    
    # Test 2: AI-RAN Anti-Interference Service Testing
    async def test_airan_service(self) -> Dict[str, Any]:
        """Test AI-RAN anti-interference service optimization"""
        logger.info("Testing AI-RAN Anti-Interference Service...")
        test_result = {"passed": False, "details": {}, "errors": []}
        
        try:
            # Test 2.1: Neural network architecture validation
            nn_test = await self._test_neural_network_architecture()
            test_result["details"]["neural_network"] = "PASS" if nn_test else "FAIL"
            
            # Test 2.2: Fast inference mode testing
            inference_test = await self._test_fast_inference_mode()
            test_result["details"]["fast_inference"] = "PASS" if inference_test else "FAIL"
            
            # Test 2.3: Decision making effectiveness
            decision_test = await self._test_airan_decision_making()
            test_result["details"]["decision_making"] = "PASS" if decision_test else "FAIL"
            
            # Test 2.4: Performance optimization
            perf_test = await self._test_airan_performance_optimization()
            test_result["details"]["performance_optimization"] = "PASS" if perf_test else "FAIL"
            
            test_result["passed"] = all(v == "PASS" for v in test_result["details"].values())
            
        except Exception as e:
            test_result["errors"].append(f"AI-RAN service test error: {str(e)}")
            logger.error(f"AI-RAN service test failed: {e}")
        
        self.test_results["airan_service"] = test_result
        return test_result
    
    # Test 3: Real-time Data Exchange Testing
    async def test_realtime_data_exchange(self) -> Dict[str, Any]:
        """Test real-time data exchange between Sionna and interference control"""
        logger.info("Testing Real-time Data Exchange...")
        test_result = {"passed": False, "details": {}, "errors": []}
        
        try:
            # Test 3.1: Sionna-Interference integration service
            integration_test = await self._test_sionna_interference_integration()
            test_result["details"]["sionna_interference_integration"] = "PASS" if integration_test else "FAIL"
            
            # Test 3.2: Data fusion algorithms
            fusion_test = await self._test_data_fusion_algorithms()
            test_result["details"]["data_fusion"] = "PASS" if fusion_test else "FAIL"
            
            # Test 3.3: Real-time processing performance
            realtime_test = await self._test_realtime_processing_performance()
            test_result["details"]["realtime_processing"] = "PASS" if realtime_test else "FAIL"
            
            test_result["passed"] = all(v == "PASS" for v in test_result["details"].values())
            
        except Exception as e:
            test_result["errors"].append(f"Real-time data exchange test error: {str(e)}")
            logger.error(f"Real-time data exchange test failed: {e}")
        
        self.test_results["realtime_data_exchange"] = test_result
        return test_result
    
    # Test 4: Metrics Collection Testing
    async def test_metrics_collection(self) -> Dict[str, Any]:
        """Test wireless channel metrics collection"""
        logger.info("Testing Metrics Collection...")
        test_result = {"passed": False, "details": {}, "errors": []}
        
        try:
            # Test 4.1: Unified metrics collector enhancement
            collector_test = await self._test_unified_metrics_collector()
            test_result["details"]["unified_collector"] = "PASS" if collector_test else "FAIL"
            
            # Test 4.2: Sionna channel metrics
            sionna_metrics_test = await self._test_sionna_channel_metrics()
            test_result["details"]["sionna_metrics"] = "PASS" if sionna_metrics_test else "FAIL"
            
            # Test 4.3: AI-RAN decision metrics
            airan_metrics_test = await self._test_airan_decision_metrics()
            test_result["details"]["airan_metrics"] = "PASS" if airan_metrics_test else "FAIL"
            
            # Test 4.4: Interference control metrics
            interference_metrics_test = await self._test_interference_control_metrics()
            test_result["details"]["interference_metrics"] = "PASS" if interference_metrics_test else "FAIL"
            
            test_result["passed"] = all(v == "PASS" for v in test_result["details"].values())
            
        except Exception as e:
            test_result["errors"].append(f"Metrics collection test error: {str(e)}")
            logger.error(f"Metrics collection test failed: {e}")
        
        self.test_results["metrics_collection"] = test_result
        return test_result
    
    # Test 5: Closed-loop Control Testing
    async def test_closed_loop_control(self) -> Dict[str, Any]:
        """Test closed-loop interference control mechanism"""
        logger.info("Testing Closed-loop Control...")
        test_result = {"passed": False, "details": {}, "errors": []}
        
        try:
            # Test 5.1: Automated control loop
            control_loop_test = await self._test_automated_control_loop()
            test_result["details"]["control_loop"] = "PASS" if control_loop_test else "FAIL"
            
            # Test 5.2: Frequency hopping effectiveness
            freq_hop_test = await self._test_frequency_hopping()
            test_result["details"]["frequency_hopping"] = "PASS" if freq_hop_test else "FAIL"
            
            # Test 5.3: Adaptive learning
            adaptive_test = await self._test_adaptive_learning()
            test_result["details"]["adaptive_learning"] = "PASS" if adaptive_test else "FAIL"
            
            # Test 5.4: Response time measurement
            response_time_test = await self._test_response_time()
            test_result["details"]["response_time"] = "PASS" if response_time_test else "FAIL"
            
            test_result["passed"] = all(v == "PASS" for v in test_result["details"].values())
            
        except Exception as e:
            test_result["errors"].append(f"Closed-loop control test error: {str(e)}")
            logger.error(f"Closed-loop control test failed: {e}")
        
        self.test_results["closed_loop_control"] = test_result
        return test_result
    
    # Test 6: Frontend Integration Testing
    async def test_frontend_integration(self) -> Dict[str, Any]:
        """Test frontend real-time visualization components"""
        logger.info("Testing Frontend Integration...")
        test_result = {"passed": False, "details": {}, "errors": []}
        
        try:
            # Test 6.1: Enhanced SINR Viewer
            sinr_test = await self._test_sinr_viewer_enhancements()
            test_result["details"]["sinr_viewer"] = "PASS" if sinr_test else "FAIL"
            
            # Test 6.2: Enhanced Delay-Doppler Viewer
            delay_doppler_test = await self._test_delay_doppler_viewer_enhancements()
            test_result["details"]["delay_doppler_viewer"] = "PASS" if delay_doppler_test else "FAIL"
            
            # Test 6.3: Interference Visualization
            interference_viz_test = await self._test_interference_visualization()
            test_result["details"]["interference_visualization"] = "PASS" if interference_viz_test else "FAIL"
            
            # Test 6.4: AI-RAN Decision Visualization
            airan_viz_test = await self._test_airan_decision_visualization()
            test_result["details"]["airan_decision_visualization"] = "PASS" if airan_viz_test else "FAIL"
            
            # Test 6.5: Frequency Spectrum Visualization
            spectrum_test = await self._test_frequency_spectrum_visualization()
            test_result["details"]["frequency_spectrum"] = "PASS" if spectrum_test else "FAIL"
            
            # Test 6.6: Anti-interference Comparison Dashboard
            dashboard_test = await self._test_anti_interference_dashboard()
            test_result["details"]["comparison_dashboard"] = "PASS" if dashboard_test else "FAIL"
            
            test_result["passed"] = all(v == "PASS" for v in test_result["details"].values())
            
        except Exception as e:
            test_result["errors"].append(f"Frontend integration test error: {str(e)}")
            logger.error(f"Frontend integration test failed: {e}")
        
        self.test_results["frontend_integration"] = test_result
        return test_result
    
    # Test 7: Performance and Load Testing
    async def test_performance_and_load(self) -> Dict[str, Any]:
        """Test system performance under load"""
        logger.info("Testing Performance and Load...")
        test_result = {"passed": False, "details": {}, "errors": [], "metrics": {}}
        
        try:
            # Test 7.1: Concurrent interference detection
            concurrent_test, concurrent_metrics = await self._test_concurrent_interference_detection()
            test_result["details"]["concurrent_detection"] = "PASS" if concurrent_test else "FAIL"
            test_result["metrics"]["concurrent_detection"] = concurrent_metrics
            
            # Test 7.2: High-frequency decision making
            high_freq_test, high_freq_metrics = await self._test_high_frequency_decisions()
            test_result["details"]["high_frequency_decisions"] = "PASS" if high_freq_test else "FAIL"
            test_result["metrics"]["high_frequency_decisions"] = high_freq_metrics
            
            # Test 7.3: Memory usage optimization
            memory_test, memory_metrics = await self._test_memory_optimization()
            test_result["details"]["memory_optimization"] = "PASS" if memory_test else "FAIL"
            test_result["metrics"]["memory_optimization"] = memory_metrics
            
            # Test 7.4: WebSocket performance
            websocket_test, websocket_metrics = await self._test_websocket_performance()
            test_result["details"]["websocket_performance"] = "PASS" if websocket_test else "FAIL"
            test_result["metrics"]["websocket_performance"] = websocket_metrics
            
            test_result["passed"] = all(v == "PASS" for v in test_result["details"].values())
            
        except Exception as e:
            test_result["errors"].append(f"Performance test error: {str(e)}")
            logger.error(f"Performance test failed: {e}")
        
        self.test_results["performance_and_load"] = test_result
        return test_result
    
    # Helper Methods for Individual Tests
    async def _test_api_endpoint(self, endpoint: str, method: str = "GET", data: Optional[Dict] = None) -> Optional[Dict]:
        """Test API endpoint with retry logic"""
        try:
            url = f"{self.base_url}{endpoint}"
            if method == "GET":
                response = requests.get(url, timeout=10)
            elif method == "POST":
                response = requests.post(url, json=data, timeout=10)
            else:
                response = requests.request(method, url, json=data, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"API endpoint {endpoint} returned status {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"API endpoint test failed for {endpoint}: {e}")
            return None
    
    async def _test_ueransim_config_generation(self) -> bool:
        """Test UERANSIM configuration file generation"""
        try:
            # Mock test for config generation
            response = await self._test_api_endpoint(
                "/api/sionna/generate-ueransim-config",
                method="POST",
                data={
                    "scenario_id": "test_scenario",
                    "channel_params": {
                        "frequency_ghz": 2.1,
                        "bandwidth_mhz": 20.0,
                        "environment": "urban"
                    }
                }
            )
            return response is not None and response.get('config_generated', False)
        except Exception as e:
            logger.error(f"UERANSIM config test failed: {e}")
            return False
    
    async def _test_realtime_parameter_updates(self) -> bool:
        """Test real-time channel parameter updates"""
        try:
            # Test parameter update API
            response = await self._test_api_endpoint(
                "/api/sionna/update-channel-params",
                method="PUT",
                data={
                    "scenario_id": "test_scenario",
                    "updates": {
                        "frequency_ghz": 2.2,
                        "interference_level": 0.3
                    }
                }
            )
            return response is not None and response.get('updated', False)
        except Exception as e:
            logger.error(f"Real-time parameter update test failed: {e}")
            return False
    
    async def _test_neural_network_architecture(self) -> bool:
        """Test neural network architecture validation"""
        try:
            # Test NN architecture API
            response = await self._test_api_endpoint("/api/airan/network-architecture")
            if response:
                architecture = response.get('architecture', {})
                return (
                    'dueling_dqn' in architecture and
                    'attention_mechanism' in architecture and
                    'batch_normalization' in architecture
                )
            return False
        except Exception as e:
            logger.error(f"Neural network architecture test failed: {e}")
            return False
    
    async def _test_fast_inference_mode(self) -> bool:
        """Test AI-RAN fast inference mode"""
        try:
            start_time = time.time()
            response = await self._test_api_endpoint(
                "/api/airan/fast-inference",
                method="POST",
                data={
                    "interference_data": {
                        "sinr_values": [10.5, 8.2, 12.1, 6.8, 9.3],
                        "frequency_spectrum": [0.1, 0.3, 0.8, 0.2, 0.4],
                        "ue_positions": self.test_ue_positions[:2]
                    }
                }
            )
            inference_time = time.time() - start_time
            
            # Verify fast inference (should be under 100ms)
            return (
                response is not None and 
                response.get('decision_made', False) and
                inference_time < 0.1
            )
        except Exception as e:
            logger.error(f"Fast inference test failed: {e}")
            return False
    
    async def _test_airan_decision_making(self) -> bool:
        """Test AI-RAN decision making effectiveness"""
        try:
            response = await self._test_api_endpoint(
                "/api/airan/make-decision",
                method="POST",
                data={
                    "scenario": "interference_detected",
                    "context": {
                        "interference_level": 0.7,
                        "affected_ues": ["ue_001", "ue_002"],
                        "available_channels": [1800, 1900, 2100]
                    }
                }
            )
            
            if response:
                decision = response.get('decision', {})
                return (
                    decision.get('action') in ['frequency_hop', 'power_control', 'beamforming'] and
                    decision.get('confidence', 0) > 0.7
                )
            return False
        except Exception as e:
            logger.error(f"AI-RAN decision making test failed: {e}")
            return False
    
    async def _test_airan_performance_optimization(self) -> bool:
        """Test AI-RAN performance optimization features"""
        try:
            # Test batch processing
            response = await self._test_api_endpoint(
                "/api/airan/batch-process",
                method="POST",
                data={
                    "batch_size": 10,
                    "optimization_level": "high"
                }
            )
            return response is not None and response.get('batch_processed', False)
        except Exception as e:
            logger.error(f"AI-RAN performance optimization test failed: {e}")
            return False
    
    async def _test_sionna_interference_integration(self) -> bool:
        """Test Sionna-Interference integration service"""
        try:
            response = await self._test_api_endpoint(
                "/api/sionna-interference/integrated-detection",
                method="POST",
                data={
                    "scenario_id": "integration_test",
                    "ue_positions": self.test_ue_positions,
                    "gnb_positions": self.test_gnb_positions,
                    "interference_sources": self.test_interference_sources
                }
            )
            
            if response:
                result = response.get('integration_result', {})
                return (
                    result.get('interference_detected', False) and
                    'mitigation_applied' in result and
                    'performance_improvement' in result
                )
            return False
        except Exception as e:
            logger.error(f"Sionna-Interference integration test failed: {e}")
            return False
    
    async def _test_data_fusion_algorithms(self) -> bool:
        """Test data fusion algorithms"""
        try:
            response = await self._test_api_endpoint(
                "/api/data-fusion/process",
                method="POST",
                data={
                    "sionna_data": {"channel_response": [1.2, 0.8, 1.5]},
                    "interference_data": {"detected_sources": 2},
                    "ueransim_data": {"connection_quality": 0.85}
                }
            )
            return response is not None and response.get('fusion_completed', False)
        except Exception as e:
            logger.error(f"Data fusion test failed: {e}")
            return False
    
    async def _test_realtime_processing_performance(self) -> bool:
        """Test real-time processing performance"""
        try:
            start_time = time.time()
            response = await self._test_api_endpoint(
                "/api/realtime/process-stream",
                method="POST",
                data={"stream_data": {"samples": 1000, "rate": "1ms"}}
            )
            processing_time = time.time() - start_time
            
            # Should process in near real-time (under 50ms)
            return (
                response is not None and 
                response.get('processed', False) and
                processing_time < 0.05
            )
        except Exception as e:
            logger.error(f"Real-time processing test failed: {e}")
            return False
    
    async def _test_unified_metrics_collector(self) -> bool:
        """Test enhanced unified metrics collector"""
        try:
            response = await self._test_api_endpoint("/api/metrics/sionna-channels")
            if response:
                metrics = response.get('metrics', {})
                return (
                    'channel_response' in metrics and
                    'interference_levels' in metrics and
                    'ai_ran_decisions' in metrics
                )
            return False
        except Exception as e:
            logger.error(f"Unified metrics collector test failed: {e}")
            return False
    
    async def _test_sionna_channel_metrics(self) -> bool:
        """Test Sionna channel metrics collection"""
        try:
            response = await self._test_api_endpoint("/api/metrics/sionna/detailed")
            if response:
                metrics = response.get('sionna_metrics', {})
                return (
                    'path_loss' in metrics and
                    'delay_spread' in metrics and
                    'doppler_shift' in metrics and
                    'sinr_distribution' in metrics
                )
            return False
        except Exception as e:
            logger.error(f"Sionna channel metrics test failed: {e}")
            return False
    
    async def _test_airan_decision_metrics(self) -> bool:
        """Test AI-RAN decision metrics collection"""
        try:
            response = await self._test_api_endpoint("/api/metrics/airan/decisions")
            if response:
                metrics = response.get('airan_metrics', {})
                return (
                    'decision_count' in metrics and
                    'decision_effectiveness' in metrics and
                    'response_time' in metrics
                )
            return False
        except Exception as e:
            logger.error(f"AI-RAN decision metrics test failed: {e}")
            return False
    
    async def _test_interference_control_metrics(self) -> bool:
        """Test interference control metrics collection"""
        try:
            response = await self._test_api_endpoint("/api/metrics/interference/control")
            if response:
                metrics = response.get('interference_metrics', {})
                return (
                    'interference_events' in metrics and
                    'mitigation_success_rate' in metrics and
                    'frequency_hops' in metrics
                )
            return False
        except Exception as e:
            logger.error(f"Interference control metrics test failed: {e}")
            return False
    
    async def _test_automated_control_loop(self) -> bool:
        """Test automated closed-loop control"""
        try:
            response = await self._test_api_endpoint(
                "/api/closed-loop/start",
                method="POST",
                data={"scenario_id": "control_test", "auto_mode": True}
            )
            
            if response and response.get('control_loop_started', False):
                # Wait for control loop to process
                await asyncio.sleep(2)
                
                status_response = await self._test_api_endpoint("/api/closed-loop/status")
                return (
                    status_response is not None and 
                    status_response.get('status') == 'active' and
                    status_response.get('cycles_completed', 0) > 0
                )
            return False
        except Exception as e:
            logger.error(f"Automated control loop test failed: {e}")
            return False
    
    async def _test_frequency_hopping(self) -> bool:
        """Test frequency hopping effectiveness"""
        try:
            response = await self._test_api_endpoint(
                "/api/closed-loop/frequency-hop",
                method="POST",
                data={
                    "target_ue": "ue_001",
                    "interference_level": 0.8,
                    "available_channels": [1800, 1900, 2100, 2600]
                }
            )
            
            if response:
                hop_result = response.get('hop_result', {})
                return (
                    hop_result.get('hop_executed', False) and
                    hop_result.get('new_frequency') is not None and
                    hop_result.get('improvement_expected', 0) > 0
                )
            return False
        except Exception as e:
            logger.error(f"Frequency hopping test failed: {e}")
            return False
    
    async def _test_adaptive_learning(self) -> bool:
        """Test adaptive learning capabilities"""
        try:
            # Submit learning data
            response = await self._test_api_endpoint(
                "/api/closed-loop/learn",
                method="POST",
                data={
                    "decision_outcome": {
                        "action": "frequency_hop",
                        "effectiveness": 0.85,
                        "context": {"interference_level": 0.7}
                    }
                }
            )
            return response is not None and response.get('learning_applied', False)
        except Exception as e:
            logger.error(f"Adaptive learning test failed: {e}")
            return False
    
    async def _test_response_time(self) -> bool:
        """Test system response time to interference"""
        try:
            start_time = time.time()
            
            response = await self._test_api_endpoint(
                "/api/closed-loop/emergency-response",
                method="POST",
                data={
                    "emergency_type": "severe_interference",
                    "affected_ues": ["ue_001", "ue_002"]
                }
            )
            
            response_time = time.time() - start_time
            
            # Emergency response should be under 10ms
            return (
                response is not None and 
                response.get('emergency_handled', False) and
                response_time < 0.01
            )
        except Exception as e:
            logger.error(f"Response time test failed: {e}")
            return False
    
    async def _test_sinr_viewer_enhancements(self) -> bool:
        """Test enhanced SINR viewer component"""
        try:
            # Test WebSocket endpoint for SINR data
            response = await self._test_api_endpoint("/api/frontend/sinr-viewer/config")
            if response:
                config = response.get('config', {})
                return (
                    config.get('real_time_enabled', False) and
                    config.get('websocket_endpoint') is not None and
                    'performance_monitoring' in config
                )
            return False
        except Exception as e:
            logger.error(f"SINR viewer enhancement test failed: {e}")
            return False
    
    async def _test_delay_doppler_viewer_enhancements(self) -> bool:
        """Test enhanced Delay-Doppler viewer component"""
        try:
            response = await self._test_api_endpoint("/api/frontend/delay-doppler-viewer/config")
            if response:
                config = response.get('config', {})
                return (
                    config.get('real_time_enabled', False) and
                    'mobility_data_integration' in config and
                    'adaptive_resolution' in config
                )
            return False
        except Exception as e:
            logger.error(f"Delay-Doppler viewer enhancement test failed: {e}")
            return False
    
    async def _test_interference_visualization(self) -> bool:
        """Test 3D interference visualization component"""
        try:
            response = await self._test_api_endpoint("/api/frontend/interference-visualization/data")
            if response:
                viz_data = response.get('visualization_data', {})
                return (
                    'interference_sources' in viz_data and
                    'victim_devices' in viz_data and
                    'impact_ranges' in viz_data
                )
            return False
        except Exception as e:
            logger.error(f"Interference visualization test failed: {e}")
            return False
    
    async def _test_airan_decision_visualization(self) -> bool:
        """Test AI-RAN decision visualization component"""
        try:
            response = await self._test_api_endpoint("/api/frontend/airan-visualization/decisions")
            if response:
                decisions = response.get('decision_data', {})
                return (
                    'decision_flow' in decisions and
                    'neural_network_state' in decisions and
                    'performance_metrics' in decisions
                )
            return False
        except Exception as e:
            logger.error(f"AI-RAN decision visualization test failed: {e}")
            return False
    
    async def _test_frequency_spectrum_visualization(self) -> bool:
        """Test frequency spectrum visualization component"""
        try:
            response = await self._test_api_endpoint("/api/frontend/spectrum-visualization/data")
            if response:
                spectrum_data = response.get('spectrum_data', {})
                return (
                    'frequency_bands' in spectrum_data and
                    'occupancy_levels' in spectrum_data and
                    'interference_detection' in spectrum_data
                )
            return False
        except Exception as e:
            logger.error(f"Frequency spectrum visualization test failed: {e}")
            return False
    
    async def _test_anti_interference_dashboard(self) -> bool:
        """Test anti-interference comparison dashboard"""
        try:
            response = await self._test_api_endpoint("/api/frontend/anti-interference-dashboard/data")
            if response:
                dashboard_data = response.get('dashboard_data', {})
                return (
                    'metric_comparisons' in dashboard_data and
                    'airan_decisions' in dashboard_data and
                    'interference_events' in dashboard_data and
                    'summary_stats' in dashboard_data
                )
            return False
        except Exception as e:
            logger.error(f"Anti-interference dashboard test failed: {e}")
            return False
    
    async def _test_concurrent_interference_detection(self) -> tuple[bool, Dict[str, Any]]:
        """Test concurrent interference detection performance"""
        try:
            start_time = time.time()
            
            # Simulate multiple concurrent interference events
            tasks = []
            for i in range(10):
                task = self._test_api_endpoint(
                    "/api/interference/detect",
                    method="POST",
                    data={
                        "source_id": f"concurrent_test_{i}",
                        "interference_level": 0.5 + (i * 0.05)
                    }
                )
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            processing_time = time.time() - start_time
            
            successful_detections = sum(1 for r in results if isinstance(r, dict) and r.get('detected', False))
            
            metrics = {
                "total_requests": 10,
                "successful_detections": successful_detections,
                "total_processing_time": processing_time,
                "average_processing_time": processing_time / 10,
                "detection_rate": successful_detections / 10
            }
            
            # Success if >80% detection rate and average processing time <100ms
            success = (
                metrics["detection_rate"] > 0.8 and
                metrics["average_processing_time"] < 0.1
            )
            
            return success, metrics
            
        except Exception as e:
            logger.error(f"Concurrent interference detection test failed: {e}")
            return False, {"error": str(e)}
    
    async def _test_high_frequency_decisions(self) -> tuple[bool, Dict[str, Any]]:
        """Test high-frequency decision making performance"""
        try:
            start_time = time.time()
            decision_count = 0
            
            # Test rapid decision making for 5 seconds
            while time.time() - start_time < 5:
                response = await self._test_api_endpoint(
                    "/api/airan/rapid-decision",
                    method="POST",
                    data={"urgency": "high", "context": {"test": True}}
                )
                if response and response.get('decision_made', False):
                    decision_count += 1
                await asyncio.sleep(0.01)  # 10ms intervals
            
            total_time = time.time() - start_time
            decision_rate = decision_count / total_time
            
            metrics = {
                "total_decisions": decision_count,
                "total_time": total_time,
                "decisions_per_second": decision_rate,
                "average_decision_time": total_time / decision_count if decision_count > 0 else 0
            }
            
            # Success if >50 decisions per second
            success = decision_rate > 50
            
            return success, metrics
            
        except Exception as e:
            logger.error(f"High-frequency decisions test failed: {e}")
            return False, {"error": str(e)}
    
    async def _test_memory_optimization(self) -> tuple[bool, Dict[str, Any]]:
        """Test memory usage optimization"""
        try:
            # Get initial memory usage
            initial_response = await self._test_api_endpoint("/api/system/memory-usage")
            if not initial_response:
                return False, {"error": "Could not get initial memory usage"}
            
            initial_memory = initial_response.get('memory_mb', 0)
            
            # Trigger memory-intensive operations
            for i in range(5):
                await self._test_api_endpoint(
                    "/api/stress-test/memory",
                    method="POST",
                    data={"operation": "large_matrix_calculation", "size": 1000}
                )
            
            # Get final memory usage
            final_response = await self._test_api_endpoint("/api/system/memory-usage")
            if not final_response:
                return False, {"error": "Could not get final memory usage"}
            
            final_memory = final_response.get('memory_mb', 0)
            memory_increase = final_memory - initial_memory
            
            metrics = {
                "initial_memory_mb": initial_memory,
                "final_memory_mb": final_memory,
                "memory_increase_mb": memory_increase,
                "memory_increase_percent": (memory_increase / initial_memory * 100) if initial_memory > 0 else 0
            }
            
            # Success if memory increase is <20%
            success = metrics["memory_increase_percent"] < 20
            
            return success, metrics
            
        except Exception as e:
            logger.error(f"Memory optimization test failed: {e}")
            return False, {"error": str(e)}
    
    async def _test_websocket_performance(self) -> tuple[bool, Dict[str, Any]]:
        """Test WebSocket performance for real-time updates"""
        try:
            metrics = {
                "connections_tested": 0,
                "successful_connections": 0,
                "message_latencies": [],
                "average_latency": 0,
                "max_latency": 0
            }
            
            # Test multiple WebSocket connections
            websocket_endpoints = [
                f"{self.websocket_url}/ws/sionna-metrics",
                f"{self.websocket_url}/ws/airan-decisions",
                f"{self.websocket_url}/ws/interference-events",
                f"{self.websocket_url}/ws/anti-interference-metrics"
            ]
            
            for endpoint in websocket_endpoints:
                try:
                    async with websockets.connect(endpoint, ping_interval=None) as websocket:
                        metrics["connections_tested"] += 1
                        
                        # Send test message and measure latency
                        start_time = time.time()
                        await websocket.send(json.dumps({"type": "ping", "timestamp": start_time}))
                        
                        response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                        latency = time.time() - start_time
                        
                        metrics["successful_connections"] += 1
                        metrics["message_latencies"].append(latency)
                        
                except Exception as e:
                    logger.warning(f"WebSocket connection failed for {endpoint}: {e}")
            
            if metrics["message_latencies"]:
                metrics["average_latency"] = sum(metrics["message_latencies"]) / len(metrics["message_latencies"])
                metrics["max_latency"] = max(metrics["message_latencies"])
            
            # Success if >75% connections successful and average latency <50ms
            success = (
                metrics["successful_connections"] / metrics["connections_tested"] > 0.75 and
                metrics["average_latency"] < 0.05
            )
            
            return success, metrics
            
        except Exception as e:
            logger.error(f"WebSocket performance test failed: {e}")
            return False, {"error": str(e)}
    
    # Main Test Execution
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all Stage 4 integration tests"""
        logger.info("Starting Stage 4 Integration Test Suite...")
        
        await self.setup_test_environment()
        
        # Run all test categories
        test_categories = [
            ("Sionna Integration", self.test_sionna_integration_service),
            ("AI-RAN Service", self.test_airan_service),
            ("Real-time Data Exchange", self.test_realtime_data_exchange),
            ("Metrics Collection", self.test_metrics_collection),
            ("Closed-loop Control", self.test_closed_loop_control),
            ("Frontend Integration", self.test_frontend_integration),
            ("Performance and Load", self.test_performance_and_load)
        ]
        
        total_tests = 0
        passed_tests = 0
        
        for category_name, test_method in test_categories:
            logger.info(f"\n{'='*60}")
            logger.info(f"Running {category_name} Tests...")
            logger.info(f"{'='*60}")
            
            try:
                result = await test_method()
                category_passed = result.get("passed", False)
                category_test_count = len(result.get("details", {}))
                
                total_tests += category_test_count
                if category_passed:
                    passed_tests += category_test_count
                
                logger.info(f"{category_name}: {'PASS' if category_passed else 'FAIL'}")
                
                # Log detailed results
                for test_name, test_result in result.get("details", {}).items():
                    logger.info(f"  {test_name}: {test_result}")
                
                if result.get("errors"):
                    for error in result["errors"]:
                        logger.error(f"  Error: {error}")
                
            except Exception as e:
                logger.error(f"{category_name} tests failed with exception: {e}")
                self.test_results[category_name.lower().replace(" ", "_")] = {
                    "passed": False,
                    "errors": [str(e)]
                }
        
        # Generate summary report
        overall_success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        summary = {
            "stage": "Stage 4: Sionna Wireless Channel and AI-RAN Anti-Interference Integration",
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "success_rate": overall_success_rate,
            "overall_status": "PASS" if overall_success_rate >= 80 else "FAIL",
            "test_results": self.test_results,
            "performance_metrics": self.performance_metrics,
            "timestamp": time.time()
        }
        
        logger.info(f"\n{'='*80}")
        logger.info(f"STAGE 4 INTEGRATION TEST SUMMARY")
        logger.info(f"{'='*80}")
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed Tests: {passed_tests}")
        logger.info(f"Failed Tests: {total_tests - passed_tests}")
        logger.info(f"Success Rate: {overall_success_rate:.1f}%")
        logger.info(f"Overall Status: {summary['overall_status']}")
        logger.info(f"{'='*80}")
        
        return summary

# Test execution function
async def main():
    """Main function to run Stage 4 integration tests"""
    test_suite = Stage4IntegrationTestSuite()
    results = await test_suite.run_all_tests()
    
    # Save results to file
    results_file = "/home/sat/ntn-stack/tests/reports/stage4_integration_test_results.json"
    os.makedirs(os.path.dirname(results_file), exist_ok=True)
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Test results saved to: {results_file}")
    
    # Return exit code based on overall status
    return 0 if results["overall_status"] == "PASS" else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)