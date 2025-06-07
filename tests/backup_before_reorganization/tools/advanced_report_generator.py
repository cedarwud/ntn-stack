"""
高級測試報告生成器
Advanced Test Report Generator with HTML and PDF support
"""

import json
import os
import base64
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from jinja2 import Template, Environment, FileSystemLoader
import pandas as pd
import numpy as np
from weasyprint import HTML, CSS
import plotly.io as pio

from visualization_config import VisualizationConfig, ReportConfig
from test_data_collector import TestResult, TestSuite, PerformanceMetrics, TestDataManager
from visualization_engine import VisualizationEngine, ChartData


@dataclass
class ReportSection:
    """報告段落"""
    title: str
    content: str
    charts: List[ChartData] = None
    tables: List[pd.DataFrame] = None
    
    def __post_init__(self):
        if self.charts is None:
            self.charts = []
        if self.tables is None:
            self.tables = []


@dataclass
class ReportSummary:
    """報告摘要"""
    total_test_suites: int
    total_tests: int
    total_passed: int
    total_failed: int
    total_skipped: int
    total_errors: int
    overall_success_rate: float
    total_duration: float
    report_period: str
    environment: str
    build_info: Dict[str, str]
    key_metrics: Dict[str, Any]


@dataclass
class TestReport:
    """完整測試報告"""
    title: str
    generated_at: datetime
    summary: ReportSummary
    sections: List[ReportSection]
    metadata: Dict[str, Any]


class HTMLTemplateManager:
    """HTML模板管理器"""
    
    def __init__(self, template_dir: Optional[str] = None):
        self.template_dir = template_dir or str(Path(__file__).parent / "templates")
        Path(self.template_dir).mkdir(parents=True, exist_ok=True)
        self.env = Environment(loader=FileSystemLoader(self.template_dir))
        self._create_default_templates()
    
    def _create_default_templates(self):
        """創建默認模板"""
        # 主報告模板
        main_template = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ report.title }}</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
        }
        .header {
            text-align: center;
            border-bottom: 3px solid #007bff;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .summary-card {
            background: linear-gradient(135deg, #007bff, #0056b3);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }
        .summary-card.success { background: linear-gradient(135deg, #28a745, #1e7e34); }
        .summary-card.warning { background: linear-gradient(135deg, #ffc107, #e0a800); }
        .summary-card.danger { background: linear-gradient(135deg, #dc3545, #c82333); }
        .summary-card h3 {
            margin: 0 0 10px 0;
            font-size: 2em;
        }
        .summary-card p {
            margin: 0;
            opacity: 0.9;
        }
        .section {
            margin-bottom: 40px;
            padding: 20px;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
        }
        .section h2 {
            color: #007bff;
            border-bottom: 2px solid #e0e0e0;
            padding-bottom: 10px;
        }
        .chart-container {
            margin: 20px 0;
            text-align: center;
        }
        .table-container {
            overflow-x: auto;
            margin: 20px 0;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 10px 0;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }
        th {
            background-color: #007bff;
            color: white;
        }
        tr:nth-child(even) {
            background-color: #f2f2f2;
        }
        .footer {
            text-align: center;
            padding-top: 20px;
            border-top: 1px solid #e0e0e0;
            color: #666;
        }
        .status-passed { color: #28a745; font-weight: bold; }
        .status-failed { color: #dc3545; font-weight: bold; }
        .status-skipped { color: #6c757d; font-weight: bold; }
        .status-error { color: #fd7e14; font-weight: bold; }
    </style>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{{ report.title }}</h1>
            <p>Generated on {{ report.generated_at.strftime('%Y-%m-%d %H:%M:%S') }}</p>
            <p>Report Period: {{ report.summary.report_period }}</p>
        </div>
        
        <div class="summary-grid">
            <div class="summary-card">
                <h3>{{ report.summary.total_test_suites }}</h3>
                <p>Test Suites</p>
            </div>
            <div class="summary-card">
                <h3>{{ report.summary.total_tests }}</h3>
                <p>Total Tests</p>
            </div>
            <div class="summary-card success">
                <h3>{{ report.summary.total_passed }}</h3>
                <p>Passed ({{ "%.1f"|format(report.summary.overall_success_rate) }}%)</p>
            </div>
            <div class="summary-card danger">
                <h3>{{ report.summary.total_failed }}</h3>
                <p>Failed</p>
            </div>
            <div class="summary-card warning">
                <h3>{{ report.summary.total_skipped }}</h3>
                <p>Skipped</p>
            </div>
            <div class="summary-card">
                <h3>{{ "%.2f"|format(report.summary.total_duration) }}s</h3>
                <p>Total Duration</p>
            </div>
        </div>
        
        {% for section in report.sections %}
        <div class="section">
            <h2>{{ section.title }}</h2>
            <div>{{ section.content|safe }}</div>
            
            {% for chart in section.charts %}
            <div class="chart-container">
                {{ chart.html|safe }}
            </div>
            {% endfor %}
            
            {% for table in section.tables %}
            <div class="table-container">
                {{ table.to_html(classes='table', escape=False)|safe }}
            </div>
            {% endfor %}
        </div>
        {% endfor %}
        
        <div class="footer">
            <p>Report generated by NTN Stack Test Visualization System</p>
            <p>{{ report.metadata.get('version', 'v1.0') }} | Environment: {{ report.summary.environment }}</p>
        </div>
    </div>
</body>
</html>
        '''
        
        template_path = Path(self.template_dir) / "main_report.html"
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(main_template)
    
    def render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """渲染模板"""
        template = self.env.get_template(template_name)
        return template.render(**context)


class AdvancedReportGenerator:
    """高級報告生成器"""
    
    def __init__(self, config: VisualizationConfig):
        self.config = config
        self.template_manager = HTMLTemplateManager()
        self.visualization_engine = VisualizationEngine(config)
        
    def generate_report(self,
                       test_suites: List[TestSuite],
                       performance_data: List[PerformanceMetrics] = None,
                       title: str = "NTN Stack Test Results Report",
                       period: str = "Last 7 Days") -> TestReport:
        """生成完整測試報告"""
        
        # 生成報告摘要
        summary = self._generate_summary(test_suites, period)
        
        # 生成報告段落
        sections = []
        
        # 1. 執行摘要
        sections.append(self._generate_executive_summary(test_suites, summary))
        
        # 2. 測試結果詳細分析
        sections.append(self._generate_test_results_analysis(test_suites))
        
        # 3. 性能分析
        if performance_data:
            sections.append(self._generate_performance_analysis(performance_data))
        
        # 4. 失敗分析
        sections.append(self._generate_failure_analysis(test_suites))
        
        # 5. 趨勢分析
        sections.append(self._generate_trend_analysis(test_suites))
        
        # 6. 建議和行動項目
        sections.append(self._generate_recommendations(test_suites, summary))
        
        return TestReport(
            title=title,
            generated_at=datetime.now(),
            summary=summary,
            sections=sections,
            metadata={
                'version': '1.0',
                'generator': 'NTN Stack Test Visualization System',
                'config': asdict(self.config.report)
            }
        )
    
    def _generate_summary(self, test_suites: List[TestSuite], period: str) -> ReportSummary:
        """生成報告摘要"""
        total_test_suites = len(test_suites)
        total_tests = sum(suite.total_tests for suite in test_suites)
        total_passed = sum(suite.passed for suite in test_suites)
        total_failed = sum(suite.failed for suite in test_suites)
        total_skipped = sum(suite.skipped for suite in test_suites)
        total_errors = sum(suite.errors for suite in test_suites)
        total_duration = sum(suite.duration for suite in test_suites)
        
        overall_success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        # 關鍵指標
        key_metrics = {
            'avg_test_duration': total_duration / total_tests if total_tests > 0 else 0,
            'failure_rate': (total_failed / total_tests * 100) if total_tests > 0 else 0,
            'error_rate': (total_errors / total_tests * 100) if total_tests > 0 else 0,
            'skip_rate': (total_skipped / total_tests * 100) if total_tests > 0 else 0
        }
        
        # 構建信息
        build_info = {
            'branch': 'main',
            'commit': 'latest',
            'build_number': 'auto'
        }
        
        return ReportSummary(
            total_test_suites=total_test_suites,
            total_tests=total_tests,
            total_passed=total_passed,
            total_failed=total_failed,
            total_skipped=total_skipped,
            total_errors=total_errors,
            overall_success_rate=overall_success_rate,
            total_duration=total_duration,
            report_period=period,
            environment='production',
            build_info=build_info,
            key_metrics=key_metrics
        )
    
    def _generate_executive_summary(self, test_suites: List[TestSuite], summary: ReportSummary) -> ReportSection:
        """生成執行摘要"""
        content = f"""
        <h3>測試執行概覽</h3>
        <p>本報告涵蓋了 {summary.report_period} 期間的測試執行結果。總計執行了 {summary.total_test_suites} 個測試套件，
        包含 {summary.total_tests} 個測試案例。</p>
        
        <h4>關鍵指標</h4>
        <ul>
            <li><strong>整體成功率:</strong> {summary.overall_success_rate:.1f}%</li>
            <li><strong>平均測試時間:</strong> {summary.key_metrics['avg_test_duration']:.2f} 秒</li>
            <li><strong>失敗率:</strong> {summary.key_metrics['failure_rate']:.1f}%</li>
            <li><strong>錯誤率:</strong> {summary.key_metrics['error_rate']:.1f}%</li>
        </ul>
        
        <h4>測試狀態分析</h4>
        <p>成功率 {summary.overall_success_rate:.1f}% 
        {'表現優秀' if summary.overall_success_rate >= 90 else '需要關注' if summary.overall_success_rate >= 80 else '需要緊急處理'}。
        </p>
        """
        
        # 生成總覽圖表
        charts = self.visualization_engine.generate_test_results_overview(test_suites)
        
        return ReportSection(
            title="執行摘要",
            content=content,
            charts=list(charts.values())
        )
    
    def _generate_test_results_analysis(self, test_suites: List[TestSuite]) -> ReportSection:
        """生成測試結果詳細分析"""
        content = """
        <h3>測試結果詳細分析</h3>
        <p>以下是各測試套件的詳細執行結果分析。</p>
        """
        
        # 創建測試套件詳細表格
        suite_data = []
        for suite in test_suites:
            suite_data.append({
                '測試套件': suite.name,
                '執行時間': suite.timestamp.strftime('%Y-%m-%d %H:%M'),
                '總測試數': suite.total_tests,
                '通過': suite.passed,
                '失敗': suite.failed,
                '跳過': suite.skipped,
                '錯誤': suite.errors,
                '成功率': f"{suite.success_rate:.1f}%",
                '執行時間(秒)': f"{suite.duration:.2f}"
            })
        
        suite_df = pd.DataFrame(suite_data)
        
        # 添加狀態顏色格式
        def color_status(val):
            if isinstance(val, str) and '%' in val:
                rate = float(val.replace('%', ''))
                if rate >= 90:
                    return 'class="status-passed"'
                elif rate >= 80:
                    return 'class="status-skipped"'
                else:
                    return 'class="status-failed"'
            return ''
        
        return ReportSection(
            title="測試結果詳細分析",
            content=content,
            tables=[suite_df]
        )
    
    def _generate_performance_analysis(self, performance_data: List[PerformanceMetrics]) -> ReportSection:
        """生成性能分析"""
        content = """
        <h3>性能指標分析</h3>
        <p>以下是系統性能指標的詳細分析，包括響應時間、吞吐量和資源使用情況。</p>
        """
        
        # 生成性能圖表
        charts = self.visualization_engine.generate_performance_charts(performance_data)
        
        # 性能統計表
        perf_stats = []
        if performance_data:
            response_times = [p.response_time for p in performance_data]
            throughputs = [p.throughput for p in performance_data]
            error_rates = [p.error_rate for p in performance_data]
            
            perf_stats.append({
                '指標': '響應時間 (ms)',
                '平均值': f"{np.mean(response_times):.2f}",
                '最小值': f"{np.min(response_times):.2f}",
                '最大值': f"{np.max(response_times):.2f}",
                '標準差': f"{np.std(response_times):.2f}"
            })
            
            perf_stats.append({
                '指標': '吞吐量 (req/s)',
                '平均值': f"{np.mean(throughputs):.2f}",
                '最小值': f"{np.min(throughputs):.2f}",
                '最大值': f"{np.max(throughputs):.2f}",
                '標準差': f"{np.std(throughputs):.2f}"
            })
            
            perf_stats.append({
                '指標': '錯誤率 (%)',
                '平均值': f"{np.mean(error_rates):.2f}",
                '最小值': f"{np.min(error_rates):.2f}",
                '最大值': f"{np.max(error_rates):.2f}",
                '標準差': f"{np.std(error_rates):.2f}"
            })
        
        perf_df = pd.DataFrame(perf_stats)
        
        return ReportSection(
            title="性能分析",
            content=content,
            charts=list(charts.values()),
            tables=[perf_df] if perf_stats else []
        )
    
    def _generate_failure_analysis(self, test_suites: List[TestSuite]) -> ReportSection:
        """生成失敗分析"""
        content = """
        <h3>失敗案例分析</h3>
        <p>對測試失敗案例進行深入分析，識別常見問題和根本原因。</p>
        """
        
        # 收集所有失敗的測試
        all_tests = []
        for suite in test_suites:
            all_tests.extend(suite.tests)
        
        # 生成失敗分析圖表
        charts = self.visualization_engine.generate_failure_analysis_charts(all_tests)
        
        # 失敗詳細表格
        failed_tests = [test for test in all_tests if test.status in ['failed', 'error']]
        if failed_tests:
            failure_data = []
            for test in failed_tests[:20]:  # 只顯示前20個
                failure_data.append({
                    '測試名稱': test.test_name,
                    '狀態': test.status,
                    '失敗類型': test.failure_type or 'Unknown',
                    '錯誤信息': (test.error_message or '')[:100] + '...' if test.error_message and len(test.error_message) > 100 else test.error_message or '',
                    '執行時間': f"{test.duration:.2f}s",
                    '時間戳': test.timestamp.strftime('%Y-%m-%d %H:%M')
                })
            
            failure_df = pd.DataFrame(failure_data)
        else:
            failure_df = pd.DataFrame([{'信息': '沒有失敗的測試案例'}])
        
        return ReportSection(
            title="失敗分析",
            content=content,
            charts=list(charts.values()),
            tables=[failure_df]
        )
    
    def _generate_trend_analysis(self, test_suites: List[TestSuite]) -> ReportSection:
        """生成趨勢分析"""
        content = """
        <h3>測試趨勢分析</h3>
        <p>分析測試結果的歷史趨勢，識別性能回歸和改進。</p>
        """
        
        # 按時間排序測試套件
        sorted_suites = sorted(test_suites, key=lambda x: x.timestamp)
        
        # 趨勢數據
        trend_data = []
        for suite in sorted_suites:
            trend_data.append({
                '日期': suite.timestamp.strftime('%Y-%m-%d'),
                '成功率': suite.success_rate,
                '測試數量': suite.total_tests,
                '執行時間': suite.duration,
                '測試套件': suite.name
            })
        
        trend_df = pd.DataFrame(trend_data)
        
        return ReportSection(
            title="趨勢分析",
            content=content,
            tables=[trend_df]
        )
    
    def _generate_recommendations(self, test_suites: List[TestSuite], summary: ReportSummary) -> ReportSection:
        """生成建議和行動項目"""
        recommendations = []
        
        # 基於測試結果生成建議
        if summary.overall_success_rate < 80:
            recommendations.append("🔴 緊急：整體測試成功率低於80%，需要立即調查和修復失敗的測試案例")
        elif summary.overall_success_rate < 90:
            recommendations.append("🟡 警告：測試成功率低於90%，建議檢查失敗案例並改進測試穩定性")
        else:
            recommendations.append("🟢 良好：測試成功率超過90%，繼續保持當前的質量標準")
        
        if summary.key_metrics['avg_test_duration'] > 60:
            recommendations.append("⏰ 性能：平均測試時間較長，考慮優化測試執行速度")
        
        if summary.key_metrics['failure_rate'] > 10:
            recommendations.append("🔍 質量：失敗率較高，需要加強代碼質量和測試用例設計")
        
        # 基於測試套件數量的建議
        if len(test_suites) < 5:
            recommendations.append("📊 覆蓋：測試套件數量較少，考慮增加更多測試覆蓋")
        
        content = f"""
        <h3>建議和行動項目</h3>
        <p>基於當前測試結果分析，提供以下改進建議：</p>
        <ul>
        {''.join(f'<li>{rec}</li>' for rec in recommendations)}
        </ul>
        
        <h4>後續行動計劃</h4>
        <ol>
            <li>優先處理失敗率最高的測試套件</li>
            <li>分析性能瓶頸並進行優化</li>
            <li>增強測試自動化和監控</li>
            <li>定期回顧和更新測試策略</li>
        </ol>
        """
        
        return ReportSection(
            title="建議和行動項目",
            content=content
        )
    
    def export_html_report(self, report: TestReport, output_path: str):
        """導出HTML報告"""
        html_content = self.template_manager.render_template(
            "main_report.html",
            {"report": report}
        )
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def export_pdf_report(self, report: TestReport, output_path: str):
        """導出PDF報告"""
        # 首先生成HTML
        html_path = output_path.replace('.pdf', '.html')
        self.export_html_report(report, html_path)
        
        # 轉換為PDF
        try:
            HTML(filename=html_path).write_pdf(output_path)
        except Exception as e:
            print(f"Error generating PDF: {e}")
            print("PDF generation requires weasyprint. Install with: pip install weasyprint")
    
    def generate_and_export_report(self,
                                 test_suites: List[TestSuite],
                                 performance_data: List[PerformanceMetrics] = None,
                                 output_dir: str = "/home/sat/ntn-stack/tests/reports",
                                 formats: List[str] = None) -> Dict[str, str]:
        """生成並導出報告"""
        if formats is None:
            formats = ["html"]
        
        # 生成報告
        report = self.generate_report(test_suites, performance_data)
        
        # 導出報告
        output_files = {}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for format in formats:
            filename = f"test_report_{timestamp}.{format}"
            output_path = str(Path(output_dir) / filename)
            
            if format == "html":
                self.export_html_report(report, output_path)
            elif format == "pdf":
                self.export_pdf_report(report, output_path)
            
            output_files[format] = output_path
        
        return output_files


if __name__ == "__main__":
    # 示例使用
    from visualization_config import ConfigManager
    from test_data_collector import TestDataManager
    
    # 加載配置
    config_manager = ConfigManager()
    config = config_manager.load_config()
    
    # 創建報告生成器
    report_generator = AdvancedReportGenerator(config)
    
    # 獲取測試數據
    data_manager = TestDataManager()
    test_data = data_manager.get_test_data(
        start_date=datetime.now() - timedelta(days=7)
    )
    
    # 示例測試套件（如果沒有真實數據）
    if test_data.empty:
        from datetime import datetime
        sample_suite = TestSuite(
            name="Sample Test Suite",
            timestamp=datetime.now(),
            total_tests=100,
            passed=85,
            failed=10,
            skipped=5,
            errors=0,
            duration=120.5,
            success_rate=85.0,
            tests=[]
        )
        test_suites = [sample_suite]
    else:
        # 從真實數據創建測試套件
        test_suites = []
    
    # 生成並導出報告
    output_files = report_generator.generate_and_export_report(
        test_suites=test_suites,
        formats=["html"]
    )
    
    print("Report generated:")
    for format, path in output_files.items():
        print(f"  {format.upper()}: {path}")