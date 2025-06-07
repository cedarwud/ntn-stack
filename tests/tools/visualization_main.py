#!/usr/bin/env python3
"""
測試結果可視化分析工具主程序
Test Result Visualization Analysis Tool Main Program

這是一個綜合的測試結果可視化分析工具，實現階段七的要求。
包括數據收集、圖表生成、報告生成、儀表板服務和趨勢分析等功能。

使用方法:
    python visualization_main.py --help
    python visualization_main.py dashboard --port 8050
    python visualization_main.py generate-report --format html
    python visualization_main.py analyze-trends --days 30
"""

import argparse
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional

# 添加當前目錄到Python路徑
sys.path.insert(0, str(Path(__file__).parent))

from visualization_config import ConfigManager, VisualizationConfig
from test_data_collector import TestDataManager, TestResult, TestSuite, PerformanceMetrics
from visualization_engine import VisualizationEngine
from advanced_report_generator import AdvancedReportGenerator
from dashboard_server import DashboardServer
from test_analysis_engine import TestAnalysisEngine
from coverage_analyzer import CoverageReportGenerator


class VisualizationCLI:
    """可視化工具命令行界面"""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()
        self.data_manager = TestDataManager()
        
    def run_dashboard(self, port: int = 8050, debug: bool = False):
        """運行儀表板服務"""
        print("🚀 Starting NTN Stack Test Visualization Dashboard...")
        print(f"📊 Dashboard will be available at: http://localhost:{port}")
        print(f"🔧 Debug mode: {'Enabled' if debug else 'Disabled'}")
        
        server = DashboardServer(port=port)
        try:
            server.run(debug=debug)
        except KeyboardInterrupt:
            print("\n👋 Dashboard server stopped by user")
        except Exception as e:
            print(f"❌ Error starting dashboard: {e}")
    
    def generate_report(self, 
                       format_type: str = "html",
                       output_dir: Optional[str] = None,
                       days: int = 7):
        """生成測試報告"""
        print(f"📝 Generating {format_type.upper()} test report...")
        
        if output_dir is None:
            output_dir = "/home/sat/ntn-stack/tests/reports"
        
        # 獲取測試數據
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        print(f"📅 Analysis period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
        test_data = self.data_manager.get_test_data(
            start_date=start_date,
            end_date=end_date
        )
        
        performance_data = self.data_manager.get_performance_data(
            start_date=start_date,
            end_date=end_date
        )
        
        # 創建測試套件（簡化版本，實際應該從數據庫構建）
        test_suites = []
        if not test_data.empty:
            # 按suite_name分組創建TestSuite對象
            for suite_name in test_data['suite_name'].unique():
                suite_tests = test_data[test_data['suite_name'] == suite_name]
                
                # 統計結果
                total_tests = len(suite_tests)
                passed = len(suite_tests[suite_tests['status'] == 'passed'])
                failed = len(suite_tests[suite_tests['status'] == 'failed'])
                skipped = len(suite_tests[suite_tests['status'] == 'skipped'])
                errors = len(suite_tests[suite_tests['status'] == 'error'])
                duration = suite_tests['duration'].sum()
                
                # 創建TestResult對象
                test_results = [
                    TestResult(
                        test_name=row['test_name'],
                        test_type=row.get('test_type', 'unknown'),
                        status=row['status'],
                        duration=row['duration'],
                        timestamp=row['timestamp'],
                        error_message=row.get('error_message'),
                        failure_type=row.get('failure_type')
                    )
                    for _, row in suite_tests.iterrows()
                ]
                
                suite = TestSuite(
                    name=suite_name,
                    timestamp=suite_tests['timestamp'].min(),
                    total_tests=total_tests,
                    passed=passed,
                    failed=failed,
                    skipped=skipped,
                    errors=errors,
                    duration=duration,
                    success_rate=(passed / total_tests * 100) if total_tests > 0 else 0,
                    tests=test_results
                )
                
                test_suites.append(suite)
        
        # 處理性能數據
        perf_metrics = []
        if not performance_data.empty:
            perf_metrics = [
                PerformanceMetrics(
                    test_name=row['test_name'],
                    timestamp=row['timestamp'],
                    response_time=row['response_time'],
                    throughput=row['throughput'],
                    error_rate=row['error_rate'],
                    cpu_usage=row['cpu_usage'],
                    memory_usage=row['memory_usage'],
                    network_io=row.get('network_io', 0.0),
                    disk_io=row.get('disk_io', 0.0)
                )
                for _, row in performance_data.iterrows()
            ]
        
        # 生成報告
        report_generator = AdvancedReportGenerator(self.config)
        
        try:
            output_files = report_generator.generate_and_export_report(
                test_suites=test_suites,
                performance_data=perf_metrics,
                output_dir=output_dir,
                formats=[format_type]
            )
            
            print(f"✅ Report generated successfully:")
            for fmt, path in output_files.items():
                print(f"   📄 {fmt.upper()}: {path}")
                
        except Exception as e:
            print(f"❌ Error generating report: {e}")
    
    def analyze_trends(self, days: int = 30):
        """分析測試趨勢"""
        print(f"📈 Analyzing test trends for the last {days} days...")
        
        analysis_engine = TestAnalysisEngine(self.data_manager)
        
        try:
            report = analysis_engine.run_comprehensive_analysis(analysis_period_days=days)
            
            print(f"\n📊 Analysis Results:")
            print(f"   🏥 Health Score: {report.summary_metrics['health_score']}/100")
            print(f"   📋 Total Trends Analyzed: {report.summary_metrics['total_trends_analyzed']}")
            print(f"   🚨 Total Alerts: {report.summary_metrics['total_alerts']}")
            print(f"   🔴 Critical Alerts: {report.summary_metrics['critical_alerts']}")
            print(f"   📈 Improving Trends: {report.summary_metrics['improving_trends']}")
            print(f"   📉 Degrading Trends: {report.summary_metrics['degrading_trends']}")
            
            if report.recommendations:
                print(f"\n💡 Recommendations:")
                for i, rec in enumerate(report.recommendations, 1):
                    print(f"   {i}. {rec}")
            
            if report.regression_alerts:
                print(f"\n🚨 Regression Alerts:")
                for alert in report.regression_alerts[:5]:  # 顯示前5個
                    print(f"   {alert.severity.upper()}: {alert.description}")
            
            # 保存分析結果
            output_dir = Path("/home/sat/ntn-stack/tests/reports")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            analysis_file = output_dir / f"trend_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            import json
            from dataclasses import asdict
            
            analysis_data = {
                'generated_at': report.generated_at.isoformat(),
                'analysis_period': [
                    report.analysis_period[0].isoformat(),
                    report.analysis_period[1].isoformat()
                ],
                'summary_metrics': report.summary_metrics,
                'recommendations': report.recommendations,
                'alert_count': len(report.regression_alerts),
                'trend_count': len(report.trend_analyses)
            }
            
            with open(analysis_file, 'w', encoding='utf-8') as f:
                json.dump(analysis_data, f, indent=2, ensure_ascii=False)
            
            print(f"\n💾 Analysis results saved to: {analysis_file}")
            
        except Exception as e:
            print(f"❌ Error analyzing trends: {e}")
    
    def analyze_coverage(self, coverage_paths: Optional[List[str]] = None):
        """分析測試覆蓋率"""
        print("📊 Analyzing test coverage...")
        
        if coverage_paths is None:
            # 自動搜索覆蓋率文件
            search_dirs = [
                "/home/sat/ntn-stack/tests/reports",
                "/home/sat/ntn-stack",
                "/home/sat/ntn-stack/netstack",
                "/home/sat/ntn-stack/simworld"
            ]
            
            coverage_paths = []
            for search_dir in search_dirs:
                search_path = Path(search_dir)
                if search_path.exists():
                    patterns = ["**/coverage.xml", "**/coverage.json", "**/lcov.info", "**/.coverage"]
                    for pattern in patterns:
                        coverage_paths.extend(str(p) for p in search_path.glob(pattern))
        
        if not coverage_paths:
            print("⚠️  No coverage files found. Generating sample analysis...")
            self._generate_sample_coverage_analysis()
            return
        
        print(f"📁 Found {len(coverage_paths)} coverage files:")
        for path in coverage_paths:
            print(f"   📄 {path}")
        
        try:
            generator = CoverageReportGenerator()
            reports = generator.process_coverage_files(coverage_paths)
            
            if reports:
                analysis = generator.generate_comprehensive_analysis(reports)
                
                print(f"\n📊 Coverage Analysis Results:")
                print(f"   📈 Overall Coverage: {analysis['summary']['overall_coverage']:.1f}%")
                print(f"   📁 Total Files: {analysis['summary']['total_files']}")
                print(f"   🔴 Critical Files: {analysis['summary']['critical_files']}")
                print(f"   💡 Suggestions: {analysis['summary']['improvement_suggestions']}")
                
                # 顯示改進建議
                if analysis['analysis'].improvement_suggestions:
                    print(f"\n💡 Improvement Suggestions:")
                    for i, suggestion in enumerate(analysis['analysis'].improvement_suggestions, 1):
                        print(f"   {i}. {suggestion}")
                
                # 保存覆蓋率圖表
                output_dir = Path("/home/sat/ntn-stack/tests/reports/coverage")
                output_dir.mkdir(parents=True, exist_ok=True)
                
                for chart_name, chart_data in analysis['charts'].items():
                    if chart_data and chart_data.html:
                        chart_file = output_dir / f"{chart_name}.html"
                        with open(chart_file, 'w', encoding='utf-8') as f:
                            f.write(chart_data.html)
                        print(f"   📊 Chart saved: {chart_file}")
                
                print(f"\n💾 Coverage charts saved to: {output_dir}")
            else:
                print("❌ No valid coverage reports could be processed")
                
        except Exception as e:
            print(f"❌ Error analyzing coverage: {e}")
    
    def _generate_sample_coverage_analysis(self):
        """生成示例覆蓋率分析"""
        from coverage_analyzer import FileCoverage, ModuleCoverage, CoverageReport, CoverageReportGenerator
        
        # 創建示例數據
        sample_files = [
            FileCoverage(
                file_path="netstack/netstack_api/main.py",
                file_name="main.py",
                total_lines=150,
                covered_lines=135,
                coverage_percentage=90.0,
                uncovered_lines=[25, 30, 145],
                functions=[]
            ),
            FileCoverage(
                file_path="simworld/backend/app/main.py",
                file_name="main.py",
                total_lines=200,
                covered_lines=160,
                coverage_percentage=80.0,
                uncovered_lines=list(range(180, 200)),
                functions=[]
            )
        ]
        
        sample_module = ModuleCoverage(
            module_name="ntn_stack",
            module_path=".",
            files=sample_files,
            total_lines=350,
            covered_lines=295,
            coverage_percentage=84.3,
            function_coverage=88.0,
            branch_coverage=75.0
        )
        
        sample_report = CoverageReport(
            project_name="NTN Stack",
            generated_at=datetime.now(),
            overall_coverage=84.3,
            line_coverage=84.3,
            function_coverage=88.0,
            branch_coverage=75.0,
            modules=[sample_module],
            summary_stats={'total_files': 2, 'total_modules': 1}
        )
        
        generator = CoverageReportGenerator()
        analysis = generator.generate_comprehensive_analysis([sample_report])
        
        print(f"📊 Sample Coverage Analysis:")
        print(f"   📈 Overall Coverage: {analysis['summary']['overall_coverage']:.1f}%")
        print(f"   📁 Total Files: {analysis['summary']['total_files']}")
        
        # 保存示例圖表
        output_dir = Path("/home/sat/ntn-stack/tests/reports/coverage")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for chart_name, chart_data in analysis['charts'].items():
            if chart_data and chart_data.html:
                chart_file = output_dir / f"sample_{chart_name}.html"
                with open(chart_file, 'w', encoding='utf-8') as f:
                    f.write(chart_data.html)
                print(f"   📊 Sample chart: {chart_file}")
    
    def collect_data(self, source_paths: Optional[List[str]] = None):
        """收集測試數據"""
        print("📥 Collecting test data...")
        
        if source_paths is None:
            source_paths = [
                "/home/sat/ntn-stack/tests/reports",
                "/home/sat/ntn-stack/tests/e2e/reports",
                "/home/sat/ntn-stack/tests/performance/reports"
            ]
        
        total_suites = 0
        for path in source_paths:
            if Path(path).exists():
                print(f"📁 Scanning: {path}")
                test_suites = self.data_manager.collect_from_path(path)
                if test_suites:
                    self.data_manager.store_test_suites(test_suites)
                    total_suites += len(test_suites)
                    print(f"   ✅ Collected {len(test_suites)} test suites")
                else:
                    print(f"   ⚠️  No test data found")
            else:
                print(f"   ❌ Path not found: {path}")
        
        if total_suites > 0:
            print(f"\n✅ Total collected: {total_suites} test suites")
        else:
            print("\n⚠️  No test data collected. Make sure test reports exist in the specified paths.")
    
    def show_status(self):
        """顯示系統狀態"""
        print("📊 NTN Stack Test Visualization System Status")
        print("=" * 50)
        
        # 數據庫狀態
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
            
            test_data = self.data_manager.get_test_data(start_date=start_date, end_date=end_date)
            performance_data = self.data_manager.get_performance_data(start_date=start_date, end_date=end_date)
            
            print(f"📅 Data Status (Last 7 days):")
            print(f"   🧪 Test Records: {len(test_data)}")
            print(f"   ⚡ Performance Records: {len(performance_data)}")
            
            if not test_data.empty:
                success_rate = (test_data['status'] == 'passed').mean() * 100
                print(f"   📈 Success Rate: {success_rate:.1f}%")
                
                test_suites = test_data['suite_name'].nunique() if 'suite_name' in test_data.columns else 0
                print(f"   📦 Test Suites: {test_suites}")
        
        except Exception as e:
            print(f"   ❌ Database Error: {e}")
        
        # 配置狀態
        print(f"\n⚙️  Configuration:")
        print(f"   📁 Config File: {self.config_manager.config_path}")
        print(f"   📊 Charts Configured: {len(self.config.charts)}")
        print(f"   🎨 Dashboard Theme: {self.config.dashboard.theme}")
        
        # 輸出目錄狀態
        output_dirs = [
            "/home/sat/ntn-stack/tests/reports",
            "/home/sat/ntn-stack/tests/data"
        ]
        
        print(f"\n📁 Directory Status:")
        for dir_path in output_dirs:
            path = Path(dir_path)
            if path.exists():
                file_count = len(list(path.glob('*')))
                print(f"   ✅ {dir_path}: {file_count} files")
            else:
                print(f"   ❌ {dir_path}: Not found")
        
        print(f"\n🔧 System Information:")
        print(f"   🐍 Python: {sys.version.split()[0]}")
        print(f"   💻 Platform: {sys.platform}")
        print(f"   📂 Working Directory: {Path.cwd()}")


def main():
    """主函數"""
    parser = argparse.ArgumentParser(
        description="NTN Stack Test Result Visualization Analysis Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s dashboard --port 8050 --debug
  %(prog)s generate-report --format html --days 14
  %(prog)s analyze-trends --days 30
  %(prog)s analyze-coverage
  %(prog)s collect-data
  %(prog)s status
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # 儀表板命令
    dashboard_parser = subparsers.add_parser('dashboard', help='Start dashboard server')
    dashboard_parser.add_argument('--port', type=int, default=8050, help='Server port (default: 8050)')
    dashboard_parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    # 報告生成命令
    report_parser = subparsers.add_parser('generate-report', help='Generate test report')
    report_parser.add_argument('--format', choices=['html', 'pdf'], default='html', help='Report format')
    report_parser.add_argument('--output-dir', help='Output directory')
    report_parser.add_argument('--days', type=int, default=7, help='Analysis period in days')
    
    # 趨勢分析命令
    trends_parser = subparsers.add_parser('analyze-trends', help='Analyze test trends')
    trends_parser.add_argument('--days', type=int, default=30, help='Analysis period in days')
    
    # 覆蓋率分析命令
    coverage_parser = subparsers.add_parser('analyze-coverage', help='Analyze test coverage')
    coverage_parser.add_argument('--paths', nargs='*', help='Coverage file paths')
    
    # 數據收集命令
    collect_parser = subparsers.add_parser('collect-data', help='Collect test data')
    collect_parser.add_argument('--paths', nargs='*', help='Source paths to scan')
    
    # 狀態檢查命令
    subparsers.add_parser('status', help='Show system status')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    cli = VisualizationCLI()
    
    try:
        if args.command == 'dashboard':
            cli.run_dashboard(port=args.port, debug=args.debug)
        elif args.command == 'generate-report':
            cli.generate_report(
                format_type=args.format,
                output_dir=args.output_dir,
                days=args.days
            )
        elif args.command == 'analyze-trends':
            cli.analyze_trends(days=args.days)
        elif args.command == 'analyze-coverage':
            cli.analyze_coverage(coverage_paths=args.paths)
        elif args.command == 'collect-data':
            cli.collect_data(source_paths=args.paths)
        elif args.command == 'status':
            cli.show_status()
            
    except KeyboardInterrupt:
        print("\n👋 Operation cancelled by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())