#!/usr/bin/env python3
"""
全階段實現狀況驗證腳本

根據 DR.md 檢查所有 8 個階段的實現狀況
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple
import json
import logging

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StageValidator:
    """階段驗證器"""
    
    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        
        # 定義每個階段的核心組件
        self.stage_requirements = {
            "stage1": {
                "name": "5G Core Network & Basic Services Integration",
                "status_claimed": "已完成",
                "key_components": [
                    "netstack/compose/core.yaml",
                    "netstack/netstack_api/services/ue_service.py",
                    "netstack/netstack_api/services/slice_service.py",
                    "netstack/netstack_api/services/health_service.py",
                    "netstack/config/prometheus.yml"
                ],
                "api_endpoints": [
                    "/api/v1/ue/status",
                    "/api/v1/slices/",
                    "/health"
                ]
            },
            "stage2": {
                "name": "Satellite Orbit Computation & Multi-Domain Integration",
                "status_claimed": "已完成",
                "key_components": [
                    "simworld/backend/app/domains/satellite/services/orbit_service.py",
                    "simworld/backend/app/domains/satellite/services/tle_service.py",
                    "simworld/backend/app/domains/coordinates/services/coordinate_service.py",
                    "simworld/frontend/src/components/scenes/satellite/SatelliteManager.tsx"
                ],
                "api_endpoints": [
                    "/api/v1/satellites/",
                    "/api/v1/coordinates/",
                    "/api/v1/orbit/"
                ]
            },
            "stage3": {
                "name": "NTN gNodeB Mapping & Advanced Network Functions",
                "status_claimed": "已完成", 
                "key_components": [
                    "netstack/netstack_api/services/satellite_gnb_mapping_service.py",
                    "netstack/netstack_api/services/oneweb_satellite_gnb_service.py",
                    "netstack/netstack_api/services/uav_ue_service.py",
                    "netstack/netstack_api/services/mesh_bridge_service.py"
                ],
                "api_endpoints": [
                    "/api/v1/satellite-gnb/",
                    "/api/v1/oneweb/",
                    "/api/v1/uav/",
                    "/api/v1/mesh/"
                ]
            },
            "stage4": {
                "name": "Sionna Channel & AI-RAN Anti-Interference Integration",
                "status_claimed": "待實現",
                "key_components": [
                    "netstack/netstack_api/services/sionna_integration_service.py",
                    "netstack/netstack_api/services/ai_ran_anti_interference_service.py",
                    "netstack/netstack_api/services/interference_control_service.py",
                    "simworld/frontend/src/components/viewers/InterferenceVisualization.tsx",
                    "simworld/frontend/src/components/viewers/SINRViewer.tsx"
                ],
                "api_endpoints": [
                    "/api/v1/sionna/",
                    "/api/v1/interference/",
                    "/api/v1/ai-ran/"
                ]
            },
            "stage5": {
                "name": "UAV Swarm Coordination & Mesh Network Optimization",
                "status_claimed": "待實現",
                "key_components": [
                    "netstack/netstack_api/services/uav_swarm_coordination_service.py",
                    "netstack/netstack_api/services/uav_mesh_failover_service.py",
                    "netstack/netstack_api/services/uav_formation_management_service.py",
                    "simworld/frontend/src/components/viewers/UAVSwarmCoordinationViewer.tsx"
                ],
                "api_endpoints": [
                    "/api/v1/uav/swarm/",
                    "/api/v1/uav/formation/",
                    "/api/v1/mesh/optimization/"
                ]
            },
            "stage6": {
                "name": "Satellite Handover Prediction & Synchronization Algorithm",
                "status_claimed": "待實現",
                "key_components": [
                    "netstack/netstack_api/services/handover_prediction_service.py",
                    "netstack/netstack_api/services/satellite_handover_service.py",
                    "netstack/netstack_api/services/event_bus_service.py"
                ],
                "api_endpoints": [
                    "/api/v1/handover/",
                    "/api/v1/handover/prediction/",
                    "/api/v1/events/"
                ]
            },
            "stage7": {
                "name": "End-to-End Performance Optimization & Testing Framework Enhancement",
                "status_claimed": "待實現",
                "key_components": [
                    "netstack/netstack_api/services/enhanced_performance_optimizer.py",
                    "tests/e2e/e2e_test_framework.py",
                    "tests/performance/load_tests.py",
                    "tests/performance/stress_tests.py",
                    "tests/e2e/E2E_INTEGRATION_TESTING_SUMMARY.md"
                ],
                "api_endpoints": [
                    "/api/v1/performance/",
                    "/api/v1/optimization/"
                ]
            },
            "stage8": {
                "name": "Advanced AI Decision Making & Automated Optimization",
                "status_claimed": "待實現",
                "key_components": [
                    "netstack/netstack_api/services/ai_decision_engine.py",
                    "netstack/netstack_api/services/auto_optimization_service.py",
                    "netstack/netstack_api/services/predictive_maintenance_service.py",
                    "netstack/netstack_api/routers/ai_decision_router.py",
                    "simworld/frontend/src/components/viewers/AIDecisionVisualization.tsx",
                    "simworld/frontend/src/components/dashboard/MLModelMonitoringDashboard.tsx",
                    "tests/stage8_ai_decision_validation.py"
                ],
                "api_endpoints": [
                    "/api/v1/ai-decision/",
                    "/api/v1/ai-decision/health-analysis",
                    "/api/v1/ai-decision/optimization/",
                    "/api/v1/ai-decision/maintenance/"
                ]
            }
        }
    
    def check_file_exists(self, file_path: str) -> Tuple[bool, str]:
        """檢查檔案是否存在"""
        full_path = self.project_root / file_path
        exists = full_path.exists()
        
        if exists:
            # 檢查檔案大小來判斷是否為實質性實現
            size = full_path.stat().st_size
            if size < 500:  # 小於 500 bytes 可能只是空檔案或佔位符
                return False, f"檔案過小 ({size} bytes)"
            else:
                return True, f"存在 ({size} bytes)"
        else:
            return False, "檔案不存在"
    
    def validate_stage_implementation(self, stage_id: str) -> Dict:
        """驗證單個階段的實現狀況"""
        stage = self.stage_requirements[stage_id]
        
        results = {
            "stage_id": stage_id,
            "name": stage["name"],
            "status_claimed": stage["status_claimed"],
            "components_checked": len(stage["key_components"]),
            "components_found": 0,
            "components_details": {},
            "endpoints_count": len(stage["api_endpoints"]),
            "implementation_percentage": 0,
            "actual_status": "未知"
        }
        
        # 檢查關鍵組件
        for component in stage["key_components"]:
            exists, detail = self.check_file_exists(component)
            results["components_details"][component] = {
                "exists": exists,
                "detail": detail
            }
            if exists:
                results["components_found"] += 1
        
        # 計算實現百分比
        if results["components_checked"] > 0:
            results["implementation_percentage"] = (results["components_found"] / results["components_checked"]) * 100
        
        # 判斷實際狀態
        if results["implementation_percentage"] >= 90:
            results["actual_status"] = "完全實現"
        elif results["implementation_percentage"] >= 70:
            results["actual_status"] = "大部分實現"
        elif results["implementation_percentage"] >= 50:
            results["actual_status"] = "部分實現"
        elif results["implementation_percentage"] >= 20:
            results["actual_status"] = "初步實現"
        else:
            results["actual_status"] = "未實現"
        
        return results
    
    def validate_all_stages(self) -> Dict:
        """驗證所有階段"""
        logger.info("🔍 開始驗證所有階段的實現狀況...")
        
        validation_results = {
            "validation_timestamp": str(Path.cwd()),
            "project_root": str(self.project_root),
            "stages": {},
            "summary": {
                "total_stages": len(self.stage_requirements),
                "fully_implemented": 0,
                "mostly_implemented": 0,
                "partially_implemented": 0,
                "not_implemented": 0,
                "status_discrepancies": []
            }
        }
        
        for stage_id in sorted(self.stage_requirements.keys()):
            logger.info(f"   🔍 驗證 {stage_id}...")
            stage_result = self.validate_stage_implementation(stage_id)
            validation_results["stages"][stage_id] = stage_result
            
            # 統計摘要
            if stage_result["actual_status"] == "完全實現":
                validation_results["summary"]["fully_implemented"] += 1
            elif stage_result["actual_status"] == "大部分實現":
                validation_results["summary"]["mostly_implemented"] += 1
            elif stage_result["actual_status"] in ["部分實現", "初步實現"]:
                validation_results["summary"]["partially_implemented"] += 1
            else:
                validation_results["summary"]["not_implemented"] += 1
            
            # 檢查狀態差異
            claimed = stage_result["status_claimed"]
            actual = stage_result["actual_status"]
            
            if claimed == "已完成" and actual != "完全實現":
                validation_results["summary"]["status_discrepancies"].append({
                    "stage": stage_id,
                    "claimed": claimed,
                    "actual": actual,
                    "percentage": stage_result["implementation_percentage"]
                })
            elif claimed == "待實現" and actual in ["完全實現", "大部分實現"]:
                validation_results["summary"]["status_discrepancies"].append({
                    "stage": stage_id,
                    "claimed": claimed,
                    "actual": actual,
                    "percentage": stage_result["implementation_percentage"]
                })
        
        return validation_results
    
    def generate_validation_report(self, results: Dict):
        """生成驗證報告"""
        logger.info("📊 生成驗證報告...")
        
        report_path = self.project_root / "STAGE_VALIDATION_REPORT.md"
        
        # 生成詳細報告
        report_lines = [
            "# NTN Stack 階段實現狀況驗證報告",
            "",
            f"**驗證時間**: {results['validation_timestamp']}",
            f"**專案根目錄**: {results['project_root']}",
            "",
            "## 📊 總體摘要",
            "",
            f"- **總階段數**: {results['summary']['total_stages']}",
            f"- **完全實現**: {results['summary']['fully_implemented']} 階段",
            f"- **大部分實現**: {results['summary']['mostly_implemented']} 階段", 
            f"- **部分實現**: {results['summary']['partially_implemented']} 階段",
            f"- **未實現**: {results['summary']['not_implemented']} 階段",
            "",
            "## ⚠️ 狀態差異分析",
            ""
        ]
        
        if results['summary']['status_discrepancies']:
            report_lines.append("發現以下階段的聲明狀態與實際實現不符：")
            report_lines.append("")
            for discrepancy in results['summary']['status_discrepancies']:
                report_lines.append(f"- **{discrepancy['stage']}**: 聲明「{discrepancy['claimed']}」，實際「{discrepancy['actual']}」({discrepancy['percentage']:.1f}%)")
        else:
            report_lines.append("✅ 所有階段的聲明狀態與實際實現一致")
        
        report_lines.extend([
            "",
            "## 📋 各階段詳細狀況",
            ""
        ])
        
        # 各階段詳細信息
        for stage_id, stage_result in results['stages'].items():
            status_emoji = {
                "完全實現": "✅",
                "大部分實現": "🔄", 
                "部分實現": "⚠️",
                "初步實現": "⚠️",
                "未實現": "❌"
            }.get(stage_result["actual_status"], "❓")
            
            report_lines.extend([
                f"### {status_emoji} {stage_id.upper()}: {stage_result['name']}",
                "",
                f"- **聲明狀態**: {stage_result['status_claimed']}",
                f"- **實際狀態**: {stage_result['actual_status']}",
                f"- **實現程度**: {stage_result['implementation_percentage']:.1f}%",
                f"- **檢查組件**: {stage_result['components_found']}/{stage_result['components_checked']}",
                "",
                "**組件檢查詳情**:",
                ""
            ])
            
            for component, details in stage_result['components_details'].items():
                status_icon = "✅" if details['exists'] else "❌"
                report_lines.append(f"- {status_icon} `{component}` - {details['detail']}")
            
            report_lines.append("")
        
        # 寫入報告
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))
        
        logger.info(f"✅ 驗證報告已生成: {report_path}")
        
        return report_path
    
    def print_summary(self, results: Dict):
        """打印摘要到控制台"""
        print("\n" + "="*80)
        print("🎯 NTN STACK 階段實現狀況驗證摘要")
        print("="*80)
        
        summary = results['summary']
        total = summary['total_stages']
        
        print(f"📊 總階段數: {total}")
        print(f"✅ 完全實現: {summary['fully_implemented']} ({summary['fully_implemented']/total*100:.1f}%)")
        print(f"🔄 大部分實現: {summary['mostly_implemented']} ({summary['mostly_implemented']/total*100:.1f}%)")
        print(f"⚠️  部分實現: {summary['partially_implemented']} ({summary['partially_implemented']/total*100:.1f}%)")
        print(f"❌ 未實現: {summary['not_implemented']} ({summary['not_implemented']/total*100:.1f}%)")
        
        print("\n📋 各階段狀況:")
        for stage_id, stage_result in results['stages'].items():
            status_emoji = {
                "完全實現": "✅",
                "大部分實現": "🔄", 
                "部分實現": "⚠️",
                "初步實現": "⚠️",
                "未實現": "❌"
            }.get(stage_result["actual_status"], "❓")
            
            print(f"  {status_emoji} {stage_id.upper()}: {stage_result['actual_status']} ({stage_result['implementation_percentage']:.1f}%)")
        
        if summary['status_discrepancies']:
            print("\n⚠️  發現狀態差異:")
            for discrepancy in summary['status_discrepancies']:
                print(f"  • {discrepancy['stage']}: 聲明「{discrepancy['claimed']}」→ 實際「{discrepancy['actual']}」")
        
        # 總體結論
        fully_plus_mostly = summary['fully_implemented'] + summary['mostly_implemented']
        if fully_plus_mostly >= 7:
            print("\n🎉 結論: 專案實現程度優秀！大部分階段已完成")
        elif fully_plus_mostly >= 5:
            print("\n👍 結論: 專案實現程度良好，主要功能已具備")
        elif fully_plus_mostly >= 3:
            print("\n⚠️  結論: 專案實現程度中等，需要進一步完善")
        else:
            print("\n❌ 結論: 專案實現程度偏低，需要大量開發工作")
        
        print("="*80)
    
    def run_validation(self):
        """執行完整驗證"""
        results = self.validate_all_stages()
        report_path = self.generate_validation_report(results)
        self.print_summary(results)
        
        return results, report_path

def main():
    """主函數"""
    import argparse
    
    parser = argparse.ArgumentParser(description="NTN Stack 階段實現驗證工具")
    parser.add_argument("--project-root", default="/home/sat/ntn-stack", 
                       help="專案根目錄路徑")
    parser.add_argument("--output-json", help="輸出 JSON 格式結果到指定檔案")
    
    args = parser.parse_args()
    
    project_root = Path(args.project_root)
    if not project_root.exists():
        logger.error(f"❌ 專案目錄不存在: {project_root}")
        return 1
    
    validator = StageValidator(project_root)
    
    try:
        results, report_path = validator.run_validation()
        
        # 輸出 JSON 結果（如果指定）
        if args.output_json:
            with open(args.output_json, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            logger.info(f"📄 JSON 結果已輸出到: {args.output_json}")
        
        print(f"\n📄 詳細報告: {report_path}")
        
        # 根據實現程度設置退出碼
        summary = results['summary']
        fully_plus_mostly = summary['fully_implemented'] + summary['mostly_implemented']
        
        if fully_plus_mostly >= 6:
            return 0  # 成功
        elif fully_plus_mostly >= 4:
            return 1  # 警告
        else:
            return 2  # 失敗
            
    except Exception as e:
        logger.error(f"❌ 驗證過程發生錯誤: {e}")
        return 3

if __name__ == "__main__":
    exit(main())