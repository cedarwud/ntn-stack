#!/usr/bin/env python3
"""
Test Cleanup Utility
Identifies and removes obsolete, redundant, and duplicate test files
"""

import os
import shutil
import json
import logging
from pathlib import Path
from typing import List, Dict, Set
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestCleanupAnalyzer:
    def __init__(self, old_tests_path: str):
        self.old_tests_path = Path(old_tests_path)
        self.obsolete_files = []
        self.redundant_files = []
        self.consolidation_groups = {}
        self.migration_plan = {}
        
    def analyze_obsolete_files(self) -> List[str]:
        """Identify files that are clearly obsolete or temporary."""
        obsolete_patterns = [
            # Stage-based tests (likely temporary)
            "**/stage*_*.py",
            "**/run_stage*_*.py", 
            "**/stage*_*.sh",
            
            # Simple/basic tests that are likely superseded
            "**/simple_*.py",
            "**/basic_*.py",
            "**/quick_*.py",
            
            # Temporary or experimental files
            "**/temp_*.py",
            "**/test_temp*.py",
            "**/experimental_*.py",
            
            # Old backup files
            "**/*_backup.py",
            "**/*_old.py",
            "**/*.bak",
        ]
        
        obsolete_files = []
        for pattern in obsolete_patterns:
            obsolete_files.extend(self.old_tests_path.glob(pattern))
        
        # Additional checks for specific files
        specific_obsolete = [
            "stage4_quick_test.py",
            "stage4_container_test.py", 
            "run_stage4_comprehensive_testing.py",
            "run_stage4_docker.sh",
            "simple_api_test.py",
            "integration/run_stage8_tests.py"
        ]
        
        for file_name in specific_obsolete:
            file_path = self.old_tests_path / file_name
            if file_path.exists():
                obsolete_files.append(file_path)
        
        self.obsolete_files = [str(f) for f in obsolete_files]
        return self.obsolete_files
    
    def analyze_redundant_files(self) -> Dict[str, List[str]]:
        """Group files that appear to be redundant."""
        redundant_groups = {
            "health_checks": [
                "unit/simworld/test_health_check.py",
                "unit/netstack/test_api_health.py",
                "integration/simplified_e2e_test.py"  # Contains health checks
            ],
            
            "api_integration": [
                "real_api_integration_test.py",
                "integration/api/test_api_integration.py",
                "simple_api_test.py"
            ],
            
            "uav_connection": [
                "e2e/scenarios/test_uav_satellite_connection.py",
                "integration/services/test_uav_satellite_connection_quality.py"
            ],
            
            "failover_tests": [
                "e2e/scenarios/test_satellite_mesh_failover.py",
                "integration/services/test_failover.py",
                "integration/services/test_uav_mesh_failover_integration.py"
            ],
            
            "connectivity_tests": [
                "integration/services/test_connectivity.py",
                "integration/simplified_e2e_test.py",
                "real_api_integration_test.py"
            ]
        }
        
        # Filter to only include files that actually exist
        existing_redundant_groups = {}
        for group_name, files in redundant_groups.items():
            existing_files = []
            for file_path in files:
                full_path = self.old_tests_path / file_path
                if full_path.exists():
                    existing_files.append(str(full_path))
            
            if len(existing_files) > 1:  # Only groups with multiple existing files
                existing_redundant_groups[group_name] = existing_files
        
        self.redundant_files = existing_redundant_groups
        return self.redundant_files
    
    def create_migration_plan(self) -> Dict[str, Dict]:
        """Create a plan for migrating valuable tests to new structure."""
        migration_plan = {
            # Keep the best file from each redundant group
            "health_checks": {
                "keep": "unit/netstack/test_api_health.py",
                "migrate_to": "reorganized/integration/netstack/test_health_monitoring.py",
                "action": "consolidate_health_checks"
            },
            
            "api_integration": {
                "keep": "integration/api/test_api_integration.py", 
                "migrate_to": "reorganized/integration/backend/test_api_integration.py",
                "action": "enhance_with_real_api_features"
            },
            
            "uav_connection": {
                "keep": "e2e/scenarios/test_uav_satellite_connection.py",
                "migrate_to": "reorganized/e2e/backend/test_uav_satellite_scenarios.py",
                "action": "merge_connection_quality_tests"
            },
            
            "failover_tests": {
                "keep": "e2e/scenarios/test_satellite_mesh_failover.py",
                "migrate_to": "reorganized/e2e/backend/test_failover_scenarios.py", 
                "action": "consolidate_all_failover_tests"
            }
        }
        
        # Add files that should be migrated as-is
        preserve_and_migrate = {
            "gymnasium/test_dqn_training.py": "reorganized/unit/backend/test_rl_training.py",
            "gymnasium/test_real_data_integration.py": "reorganized/integration/backend/test_rl_data_integration.py",
            "e2e/scenarios/test_interference_avoidance.py": "reorganized/e2e/backend/test_interference_scenarios.py",
            "performance/test_load_performance.py": "reorganized/performance/backend/test_load_performance.py",
            "unit/deployment/test_basic_functionality.py": "reorganized/unit/backend/test_deployment.py"
        }
        
        for old_path, new_path in preserve_and_migrate.items():
            old_full_path = self.old_tests_path / old_path
            if old_full_path.exists():
                migration_plan[f"preserve_{old_path.replace('/', '_')}"] = {
                    "keep": old_path,
                    "migrate_to": new_path,
                    "action": "migrate_as_is"
                }
        
        self.migration_plan = migration_plan
        return migration_plan
    
    def generate_cleanup_report(self) -> Dict:
        """Generate comprehensive cleanup report."""
        obsolete_files = self.analyze_obsolete_files()
        redundant_groups = self.analyze_redundant_files()
        migration_plan = self.create_migration_plan()
        
        # Calculate statistics
        total_obsolete = len(obsolete_files)
        total_redundant = sum(len(files) for files in redundant_groups.values())
        total_to_migrate = len(migration_plan)
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "analysis_summary": {
                "total_obsolete_files": total_obsolete,
                "total_redundant_files": total_redundant,
                "redundant_groups": len(redundant_groups),
                "migration_items": total_to_migrate,
                "estimated_reduction": total_obsolete + total_redundant - total_to_migrate
            },
            "obsolete_files": obsolete_files,
            "redundant_groups": redundant_groups,
            "migration_plan": migration_plan,
            "recommendations": self._generate_recommendations()
        }
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = [
            "Remove all stage-based test files as they appear to be temporary development artifacts",
            "Consolidate health check tests into a single comprehensive test suite",
            "Merge API integration tests to eliminate duplication while preserving functionality",
            "Create unified failover test scenarios combining E2E and integration approaches",
            "Migrate valuable RL and performance tests to new structure with better organization",
            "Consider creating test templates to prevent future duplication",
            "Implement naming conventions to clearly distinguish test purposes",
            "Add documentation for each test category to prevent overlap"
        ]
        return recommendations
    
    def execute_cleanup(self, dry_run: bool = True) -> Dict:
        """Execute the cleanup plan."""
        cleanup_results = {
            "dry_run": dry_run,
            "actions_taken": [],
            "files_removed": [],
            "files_migrated": [],
            "errors": []
        }
        
        if dry_run:
            logger.info("DRY RUN MODE - No files will be actually modified")
        
        # Remove obsolete files
        for file_path in self.obsolete_files:
            try:
                if dry_run:
                    logger.info(f"[DRY RUN] Would remove obsolete file: {file_path}")
                    cleanup_results["actions_taken"].append(f"Would remove: {file_path}")
                else:
                    os.remove(file_path)
                    logger.info(f"Removed obsolete file: {file_path}")
                    cleanup_results["files_removed"].append(file_path)
            except Exception as e:
                error_msg = f"Error removing {file_path}: {e}"
                logger.error(error_msg)
                cleanup_results["errors"].append(error_msg)
        
        # Handle redundant files (remove all but the "keep" file from each group)
        for group_name, group_data in self.migration_plan.items():
            if "keep" in group_data and group_name in self.redundant_files:
                files_to_remove = [f for f in self.redundant_files[group_name] 
                                 if not f.endswith(group_data["keep"])]
                
                for file_path in files_to_remove:
                    try:
                        if dry_run:
                            logger.info(f"[DRY RUN] Would remove redundant file: {file_path}")
                            cleanup_results["actions_taken"].append(f"Would remove redundant: {file_path}")
                        else:
                            os.remove(file_path)
                            logger.info(f"Removed redundant file: {file_path}")
                            cleanup_results["files_removed"].append(file_path)
                    except Exception as e:
                        error_msg = f"Error removing {file_path}: {e}"
                        logger.error(error_msg)
                        cleanup_results["errors"].append(error_msg)
        
        return cleanup_results

def main():
    """Main function to run the cleanup analysis."""
    old_tests_path = os.path.join(os.path.dirname(__file__), "..", "..", "..")
    
    analyzer = TestCleanupAnalyzer(old_tests_path)
    
    # Generate comprehensive report
    report = analyzer.generate_cleanup_report()
    
    # Save report
    report_path = os.path.join(old_tests_path, "cleanup_analysis_report.json")
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    # Print summary
    print("\n" + "="*60)
    print("🧪 TEST CLEANUP ANALYSIS REPORT")
    print("="*60)
    print(f"📊 Analysis Summary:")
    print(f"   • Obsolete files found: {report['analysis_summary']['total_obsolete_files']}")
    print(f"   • Redundant files found: {report['analysis_summary']['total_redundant_files']}")
    print(f"   • Redundant groups: {report['analysis_summary']['redundant_groups']}")
    print(f"   • Migration items: {report['analysis_summary']['migration_items']}")
    print(f"   • Estimated file reduction: {report['analysis_summary']['estimated_reduction']}")
    
    print(f"\n🗑️ Obsolete Files to Remove:")
    for file_path in report['obsolete_files']:
        print(f"   • {file_path}")
    
    print(f"\n🔄 Redundant Groups Found:")
    for group_name, files in report['redundant_groups'].items():
        print(f"   • {group_name}: {len(files)} files")
        for file_path in files:
            print(f"     - {file_path}")
    
    print(f"\n📋 Key Recommendations:")
    for i, rec in enumerate(report['recommendations'], 1):
        print(f"   {i}. {rec}")
    
    print(f"\n📄 Full report saved to: {report_path}")
    print("\n" + "="*60)
    
    # Ask for confirmation to execute cleanup
    response = input("\n🤔 Execute cleanup? (y/N): ").strip().lower()
    if response == 'y':
        print("\n🧹 Executing cleanup...")
        cleanup_results = analyzer.execute_cleanup(dry_run=False)
        print(f"✅ Cleanup completed. Removed {len(cleanup_results['files_removed'])} files.")
        if cleanup_results['errors']:
            print(f"⚠️ {len(cleanup_results['errors'])} errors occurred:")
            for error in cleanup_results['errors']:
                print(f"   • {error}")
    else:
        print("\n🔍 Running dry run to show what would be done...")
        cleanup_results = analyzer.execute_cleanup(dry_run=True)
        print("✅ Dry run completed. Use 'y' to execute actual cleanup.")

if __name__ == "__main__":
    main()