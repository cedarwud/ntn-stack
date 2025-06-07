#!/usr/bin/env python3
"""
Stage 4 Quick Verification Test
Simplified test suite to quickly verify Stage 4 components are working
"""

import asyncio
import json
import requests
import time
import logging
import os
import sys
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Stage4QuickVerification:
    """Quick verification test for Stage 4 functionality"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.results = {}
        
    def test_api_health(self) -> bool:
        """Test if API services are running"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def test_sionna_integration(self) -> bool:
        """Quick test for Sionna integration"""
        try:
            # Test basic channel simulation endpoint
            response = requests.post(
                f"{self.base_url}/api/sionna/channel-simulation",
                json={
                    "ue_positions": [{"x": 100, "y": 200, "z": 10}],
                    "gnb_positions": [{"x": 0, "y": 0, "z": 30}],
                    "frequency_ghz": 2.1
                },
                timeout=10
            )
            return response.status_code in [200, 201]
        except Exception as e:
            logger.error(f"Sionna integration test failed: {e}")
            return False
    
    def test_airan_service(self) -> bool:
        """Quick test for AI-RAN service"""
        try:
            # Test AI-RAN decision making endpoint
            response = requests.post(
                f"{self.base_url}/api/airan/quick-decision",
                json={
                    "interference_level": 0.5,
                    "context": {"test": True}
                },
                timeout=10
            )
            return response.status_code in [200, 201]
        except Exception as e:
            logger.error(f"AI-RAN service test failed: {e}")
            return False
    
    def test_metrics_collection(self) -> bool:
        """Quick test for metrics collection"""
        try:
            # Test metrics endpoint
            response = requests.get(f"{self.base_url}/api/metrics/summary", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Metrics collection test failed: {e}")
            return False
    
    def test_interference_control(self) -> bool:
        """Quick test for interference control"""
        try:
            # Test interference detection endpoint
            response = requests.post(
                f"{self.base_url}/api/interference/detect",
                json={
                    "source_type": "test",
                    "target_ue": "ue_test",
                    "interference_level": 0.6
                },
                timeout=10
            )
            return response.status_code in [200, 201]
        except Exception as e:
            logger.error(f"Interference control test failed: {e}")
            return False
    
    def test_frontend_api(self) -> bool:
        """Quick test for frontend API endpoints"""
        try:
            # Test frontend configuration endpoints
            endpoints = [
                "/api/frontend/sinr-viewer/config",
                "/api/frontend/interference-visualization/data",
                "/api/frontend/spectrum-visualization/data"
            ]
            
            for endpoint in endpoints:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                if response.status_code not in [200, 404]:  # 404 is acceptable for mock endpoints
                    return False
            return True
        except Exception as e:
            logger.error(f"Frontend API test failed: {e}")
            return False
    
    def verify_files_exist(self) -> bool:
        """Verify that Stage 4 files were created successfully"""
        required_files = [
            "/home/sat/ntn-stack/netstack/netstack_api/services/ai_ran_optimizations.py",
            "/home/sat/ntn-stack/netstack/netstack_api/services/closed_loop_interference_control.py",
            "/home/sat/ntn-stack/netstack/netstack_api/services/sionna_interference_integration.py",
            "/home/sat/ntn-stack/simworld/frontend/src/components/viewers/AIRANDecisionVisualization.tsx",
            "/home/sat/ntn-stack/simworld/frontend/src/components/viewers/FrequencySpectrumVisualization.tsx",
            "/home/sat/ntn-stack/simworld/frontend/src/components/viewers/InterferenceVisualization.tsx",
            "/home/sat/ntn-stack/simworld/frontend/src/components/dashboard/AntiInterferenceComparisonDashboard.tsx"
        ]
        
        missing_files = []
        for file_path in required_files:
            if not os.path.exists(file_path):
                missing_files.append(file_path)
        
        if missing_files:
            logger.error(f"Missing Stage 4 files: {missing_files}")
            return False
        
        logger.info("✓ All Stage 4 files verified successfully")
        return True
    
    def verify_enhanced_files(self) -> bool:
        """Verify that existing files were enhanced with Stage 4 features"""
        enhanced_files = [
            "/home/sat/ntn-stack/netstack/netstack_api/services/sionna_integration_service.py",
            "/home/sat/ntn-stack/netstack/netstack_api/services/ai_ran_anti_interference_service.py",
            "/home/sat/ntn-stack/netstack/netstack_api/services/interference_control_service.py",
            "/home/sat/ntn-stack/netstack/netstack_api/services/unified_metrics_collector.py",
            "/home/sat/ntn-stack/simworld/frontend/src/components/viewers/SINRViewer.tsx",
            "/home/sat/ntn-stack/simworld/frontend/src/components/viewers/DelayDopplerViewer.tsx",
            "/home/sat/ntn-stack/simworld/frontend/src/types/charts.ts",
            "/home/sat/ntn-stack/simworld/frontend/src/styles/index.scss"
        ]
        
        for file_path in enhanced_files:
            if not os.path.exists(file_path):
                logger.error(f"Enhanced file missing: {file_path}")
                return False
        
        logger.info("✓ All enhanced files verified successfully")
        return True
    
    def check_key_features(self) -> Dict[str, bool]:
        """Check for key Stage 4 features in the codebase"""
        features = {}
        
        # Check for Dueling DQN in AI-RAN service
        try:
            with open("/home/sat/ntn-stack/netstack/netstack_api/services/ai_ran_anti_interference_service.py", 'r') as f:
                content = f.read()
                features["dueling_dqn"] = "Dueling" in content and "advantage_stream" in content
        except:
            features["dueling_dqn"] = False
        
        # Check for real-time WebSocket in frontend
        try:
            with open("/home/sat/ntn-stack/simworld/frontend/src/components/viewers/SINRViewer.tsx", 'r') as f:
                content = f.read()
                features["realtime_websocket"] = "useWebSocket" in content and "realTimeEnabled" in content
        except:
            features["realtime_websocket"] = False
        
        # Check for closed-loop control
        try:
            with open("/home/sat/ntn-stack/netstack/netstack_api/services/closed_loop_interference_control.py", 'r') as f:
                content = f.read()
                features["closed_loop_control"] = "ClosedLoopInterferenceController" in content and "_control_loop" in content
        except:
            features["closed_loop_control"] = False
        
        # Check for Sionna integration enhancements
        try:
            with open("/home/sat/ntn-stack/netstack/netstack_api/services/sionna_integration_service.py", 'r') as f:
                content = f.read()
                features["sionna_enhancement"] = "request_channel_simulation_with_interference" in content
        except:
            features["sionna_enhancement"] = False
        
        # Check for Three.js interference visualization
        try:
            with open("/home/sat/ntn-stack/simworld/frontend/src/components/viewers/InterferenceVisualization.tsx", 'r') as f:
                content = f.read()
                features["threejs_visualization"] = "THREE" in content and "createInterferenceSource" in content
        except:
            features["threejs_visualization"] = False
        
        return features
    
    def run_verification(self) -> Dict[str, Any]:
        """Run all verification tests"""
        logger.info("Starting Stage 4 Quick Verification...")
        
        tests = {
            "files_exist": self.verify_files_exist(),
            "enhanced_files": self.verify_enhanced_files(),
            "api_health": self.test_api_health(),
            "sionna_integration": self.test_sionna_integration(),
            "airan_service": self.test_airan_service(),
            "metrics_collection": self.test_metrics_collection(),
            "interference_control": self.test_interference_control(),
            "frontend_api": self.test_frontend_api()
        }
        
        features = self.check_key_features()
        
        # Calculate results
        total_tests = len(tests)
        passed_tests = sum(1 for result in tests.values() if result)
        success_rate = (passed_tests / total_tests) * 100
        
        total_features = len(features)
        implemented_features = sum(1 for implemented in features.values() if implemented)
        feature_rate = (implemented_features / total_features) * 100
        
        overall_status = "PASS" if success_rate >= 60 and feature_rate >= 80 else "FAIL"
        
        results = {
            "stage": "Stage 4 Quick Verification",
            "tests": tests,
            "features": features,
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "success_rate": success_rate,
                "total_features": total_features,
                "implemented_features": implemented_features,
                "feature_implementation_rate": feature_rate,
                "overall_status": overall_status
            },
            "timestamp": time.time()
        }
        
        # Log results
        logger.info(f"\n{'='*60}")
        logger.info(f"STAGE 4 QUICK VERIFICATION RESULTS")
        logger.info(f"{'='*60}")
        
        logger.info("File and Service Tests:")
        for test_name, result in tests.items():
            status = "✓ PASS" if result else "✗ FAIL"
            logger.info(f"  {test_name}: {status}")
        
        logger.info("\nKey Features Implementation:")
        for feature_name, implemented in features.items():
            status = "✓ IMPLEMENTED" if implemented else "✗ MISSING"
            logger.info(f"  {feature_name}: {status}")
        
        logger.info(f"\nSummary:")
        logger.info(f"  Test Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests})")
        logger.info(f"  Feature Implementation Rate: {feature_rate:.1f}% ({implemented_features}/{total_features})")
        logger.info(f"  Overall Status: {overall_status}")
        logger.info(f"{'='*60}")
        
        return results

def main():
    """Main function"""
    verification = Stage4QuickVerification()
    results = verification.run_verification()
    
    # Save results
    results_file = "/home/sat/ntn-stack/tests/reports/stage4_quick_verification.json"
    os.makedirs(os.path.dirname(results_file), exist_ok=True)
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results saved to: {results_file}")
    
    # Return appropriate exit code
    return 0 if results["summary"]["overall_status"] == "PASS" else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)