"""
測試結果可視化引擎
Advanced Visualization Engine for Test Results
"""

import json
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import plotly.figure_factory as ff
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from pathlib import Path
import base64
from io import BytesIO

from .visualization_config import ChartConfig, ChartType, VisualizationConfig
from .test_data_collector import TestResult, TestSuite, PerformanceMetrics


@dataclass
class ChartData:
    """圖表數據結構"""
    title: str
    data: Dict[str, Any]
    config: ChartConfig
    figure: Optional[Any] = None
    html: Optional[str] = None
    image_base64: Optional[str] = None


class BaseChartGenerator:
    """基礎圖表生成器"""
    
    def __init__(self, config: ChartConfig):
        self.config = config
        
    def generate(self, data: pd.DataFrame) -> ChartData:
        """生成圖表"""
        raise NotImplementedError
        
    def save_chart(self, chart_data: ChartData, output_path: str, format: str = "html"):
        """保存圖表"""
        if format == "html" and chart_data.html:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(chart_data.html)
        elif format in ["png", "svg", "pdf"] and chart_data.figure:
            if hasattr(chart_data.figure, 'write_image'):
                chart_data.figure.write_image(output_path)
            else:
                chart_data.figure.savefig(output_path, format=format, dpi=300, bbox_inches='tight')


class LineChartGenerator(BaseChartGenerator):
    """折線圖生成器"""
    
    def generate(self, data: pd.DataFrame) -> ChartData:
        """生成折線圖"""
        fig = go.Figure()
        
        # 處理數據分組
        if 'category' in data.columns:
            for category in data['category'].unique():
                category_data = data[data['category'] == category]
                fig.add_trace(go.Scatter(
                    x=category_data[self.config.x_axis],
                    y=category_data[self.config.y_axis],
                    mode='lines+markers',
                    name=str(category),
                    line=dict(width=2),
                    marker=dict(size=6)
                ))
        else:
            fig.add_trace(go.Scatter(
                x=data[self.config.x_axis],
                y=data[self.config.y_axis],
                mode='lines+markers',
                name=self.config.y_axis,
                line=dict(width=2),
                marker=dict(size=6)
            ))
        
        # 更新布局
        fig.update_layout(
            title=self.config.title,
            xaxis_title=self.config.x_axis,
            yaxis_title=self.config.y_axis,
            width=self.config.width,
            height=self.config.height,
            showlegend=self.config.show_legend,
            template="plotly_white"
        )
        
        if self.config.show_grid:
            fig.update_xaxes(showgrid=True)
            fig.update_yaxes(showgrid=True)
        
        return ChartData(
            title=self.config.title,
            data=data.to_dict(),
            config=self.config,
            figure=fig,
            html=fig.to_html(include_plotlyjs=True)
        )


class BarChartGenerator(BaseChartGenerator):
    """柱狀圖生成器"""
    
    def generate(self, data: pd.DataFrame) -> ChartData:
        """生成柱狀圖"""
        fig = go.Figure()
        
        if 'category' in data.columns:
            # 分組柱狀圖
            for category in data['category'].unique():
                category_data = data[data['category'] == category]
                fig.add_trace(go.Bar(
                    x=category_data[self.config.x_axis],
                    y=category_data[self.config.y_axis],
                    name=str(category),
                    text=category_data[self.config.y_axis],
                    textposition='auto'
                ))
        else:
            # 單一柱狀圖
            fig.add_trace(go.Bar(
                x=data[self.config.x_axis],
                y=data[self.config.y_axis],
                text=data[self.config.y_axis],
                textposition='auto',
                marker_color=px.colors.qualitative.Set1
            ))
        
        fig.update_layout(
            title=self.config.title,
            xaxis_title=self.config.x_axis,
            yaxis_title=self.config.y_axis,
            width=self.config.width,
            height=self.config.height,
            showlegend=self.config.show_legend,
            template="plotly_white"
        )
        
        return ChartData(
            title=self.config.title,
            data=data.to_dict(),
            config=self.config,
            figure=fig,
            html=fig.to_html(include_plotlyjs=True)
        )


class HeatmapGenerator(BaseChartGenerator):
    """熱圖生成器"""
    
    def generate(self, data: pd.DataFrame) -> ChartData:
        """生成熱圖"""
        # 透視表格式化數據
        if 'value' in data.columns:
            pivot_data = data.pivot(
                index=self.config.y_axis,
                columns=self.config.x_axis,
                values='value'
            )
        else:
            pivot_data = data.pivot(
                index=self.config.y_axis,
                columns=self.config.x_axis
            )
        
        fig = go.Figure(data=go.Heatmap(
            z=pivot_data.values,
            x=pivot_data.columns,
            y=pivot_data.index,
            colorscale=self.config.color_scheme,
            text=pivot_data.values,
            texttemplate="%{text:.2f}",
            textfont={"size": 10},
            hoverongaps=False
        ))
        
        fig.update_layout(
            title=self.config.title,
            xaxis_title=self.config.x_axis,
            yaxis_title=self.config.y_axis,
            width=self.config.width,
            height=self.config.height,
            template="plotly_white"
        )
        
        return ChartData(
            title=self.config.title,
            data=data.to_dict(),
            config=self.config,
            figure=fig,
            html=fig.to_html(include_plotlyjs=True)
        )


class ScatterPlotGenerator(BaseChartGenerator):
    """散點圖生成器"""
    
    def generate(self, data: pd.DataFrame) -> ChartData:
        """生成散點圖"""
        fig = go.Figure()
        
        if 'category' in data.columns:
            for category in data['category'].unique():
                category_data = data[data['category'] == category]
                fig.add_trace(go.Scatter(
                    x=category_data[self.config.x_axis],
                    y=category_data[self.config.y_axis],
                    mode='markers',
                    name=str(category),
                    marker=dict(
                        size=8,
                        opacity=0.7
                    )
                ))
        else:
            fig.add_trace(go.Scatter(
                x=data[self.config.x_axis],
                y=data[self.config.y_axis],
                mode='markers',
                marker=dict(
                    size=8,
                    opacity=0.7,
                    color=data.index,
                    colorscale=self.config.color_scheme
                )
            ))
        
        # 添加趨勢線
        if len(data) > 1:
            z = np.polyfit(data[self.config.x_axis], data[self.config.y_axis], 1)
            p = np.poly1d(z)
            fig.add_trace(go.Scatter(
                x=data[self.config.x_axis],
                y=p(data[self.config.x_axis]),
                mode='lines',
                name='Trend Line',
                line=dict(dash='dash', color='red')
            ))
        
        fig.update_layout(
            title=self.config.title,
            xaxis_title=self.config.x_axis,
            yaxis_title=self.config.y_axis,
            width=self.config.width,
            height=self.config.height,
            showlegend=self.config.show_legend,
            template="plotly_white"
        )
        
        return ChartData(
            title=self.config.title,
            data=data.to_dict(),
            config=self.config,
            figure=fig,
            html=fig.to_html(include_plotlyjs=True)
        )


class PieChartGenerator(BaseChartGenerator):
    """餅圖生成器"""
    
    def generate(self, data: pd.DataFrame) -> ChartData:
        """生成餅圖"""
        fig = go.Figure(data=[go.Pie(
            labels=data[self.config.x_axis],
            values=data[self.config.y_axis],
            hole=0.3,
            textinfo='label+percent',
            textposition='outside'
        )])
        
        fig.update_layout(
            title=self.config.title,
            width=self.config.width,
            height=self.config.height,
            showlegend=self.config.show_legend,
            template="plotly_white"
        )
        
        return ChartData(
            title=self.config.title,
            data=data.to_dict(),
            config=self.config,
            figure=fig,
            html=fig.to_html(include_plotlyjs=True)
        )


class BoxPlotGenerator(BaseChartGenerator):
    """箱線圖生成器"""
    
    def generate(self, data: pd.DataFrame) -> ChartData:
        """生成箱線圖"""
        fig = go.Figure()
        
        if 'category' in data.columns:
            for category in data['category'].unique():
                category_data = data[data['category'] == category]
                fig.add_trace(go.Box(
                    y=category_data[self.config.y_axis],
                    name=str(category),
                    boxpoints='outliers'
                ))
        else:
            fig.add_trace(go.Box(
                y=data[self.config.y_axis],
                name=self.config.y_axis,
                boxpoints='outliers'
            ))
        
        fig.update_layout(
            title=self.config.title,
            xaxis_title=self.config.x_axis,
            yaxis_title=self.config.y_axis,
            width=self.config.width,
            height=self.config.height,
            showlegend=self.config.show_legend,
            template="plotly_white"
        )
        
        return ChartData(
            title=self.config.title,
            data=data.to_dict(),
            config=self.config,
            figure=fig,
            html=fig.to_html(include_plotlyjs=True)
        )


class RadarChartGenerator(BaseChartGenerator):
    """雷達圖生成器"""
    
    def generate(self, data: pd.DataFrame) -> ChartData:
        """生成雷達圖"""
        fig = go.Figure()
        
        if 'category' in data.columns:
            for category in data['category'].unique():
                category_data = data[data['category'] == category]
                fig.add_trace(go.Scatterpolar(
                    r=category_data[self.config.y_axis],
                    theta=category_data[self.config.x_axis],
                    fill='toself',
                    name=str(category)
                ))
        else:
            fig.add_trace(go.Scatterpolar(
                r=data[self.config.y_axis],
                theta=data[self.config.x_axis],
                fill='toself',
                name=self.config.y_axis
            ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, data[self.config.y_axis].max()]
                )
            ),
            title=self.config.title,
            width=self.config.width,
            height=self.config.height,
            showlegend=self.config.show_legend,
            template="plotly_white"
        )
        
        return ChartData(
            title=self.config.title,
            data=data.to_dict(),
            config=self.config,
            figure=fig,
            html=fig.to_html(include_plotlyjs=True)
        )


class VisualizationEngine:
    """可視化引擎主類"""
    
    def __init__(self, config: VisualizationConfig):
        self.config = config
        self.generators = {
            ChartType.LINE: LineChartGenerator,
            ChartType.BAR: BarChartGenerator,
            ChartType.HEATMAP: HeatmapGenerator,
            ChartType.SCATTER: ScatterPlotGenerator,
            ChartType.PIE: PieChartGenerator,
            ChartType.BOX: BoxPlotGenerator,
            ChartType.RADAR: RadarChartGenerator
        }
    
    def generate_chart(self, chart_name: str, data: pd.DataFrame) -> Optional[ChartData]:
        """生成指定圖表"""
        chart_config = self.config.charts.get(chart_name)
        if not chart_config:
            print(f"Chart config not found: {chart_name}")
            return None
        
        generator_class = self.generators.get(chart_config.chart_type)
        if not generator_class:
            print(f"Generator not found for chart type: {chart_config.chart_type}")
            return None
        
        generator = generator_class(chart_config)
        return generator.generate(data)
    
    def generate_test_results_overview(self, test_suites: List[TestSuite]) -> Dict[str, ChartData]:
        """生成測試結果概覽圖表"""
        charts = {}
        
        # 準備數據
        suite_data = []
        for suite in test_suites:
            suite_data.append({
                'name': suite.name,
                'timestamp': suite.timestamp,
                'success_rate': suite.success_rate,
                'total_tests': suite.total_tests,
                'passed': suite.passed,
                'failed': suite.failed,
                'duration': suite.duration
            })
        
        df = pd.DataFrame(suite_data)
        if df.empty:
            return charts
        
        # 成功率趨勢圖
        trend_data = df.copy()
        trend_data['category'] = 'Success Rate'
        charts['success_rate_trend'] = self.generate_chart('test_results_trend', trend_data)
        
        # 測試時間比較
        duration_data = df[['name', 'duration']].copy()
        duration_config = ChartConfig(
            chart_type=ChartType.BAR,
            title="Test Duration Comparison",
            x_axis='name',
            y_axis='duration'
        )
        generator = BarChartGenerator(duration_config)
        charts['duration_comparison'] = generator.generate(duration_data)
        
        # 測試結果分佈
        status_data = []
        for suite in test_suites:
            status_data.extend([
                {'status': 'Passed', 'count': suite.passed},
                {'status': 'Failed', 'count': suite.failed},
                {'status': 'Skipped', 'count': suite.skipped},
                {'status': 'Error', 'count': suite.errors}
            ])
        
        status_df = pd.DataFrame(status_data)
        status_summary = status_df.groupby('status')['count'].sum().reset_index()
        
        pie_config = ChartConfig(
            chart_type=ChartType.PIE,
            title="Test Results Distribution",
            x_axis='status',
            y_axis='count'
        )
        generator = PieChartGenerator(pie_config)
        charts['results_distribution'] = generator.generate(status_summary)
        
        return charts
    
    def generate_performance_charts(self, performance_data: List[PerformanceMetrics]) -> Dict[str, ChartData]:
        """生成性能圖表"""
        charts = {}
        
        if not performance_data:
            return charts
        
        # 準備性能數據
        perf_df = pd.DataFrame([
            {
                'test_name': perf.test_name,
                'timestamp': perf.timestamp,
                'response_time': perf.response_time,
                'throughput': perf.throughput,
                'error_rate': perf.error_rate,
                'cpu_usage': perf.cpu_usage,
                'memory_usage': perf.memory_usage
            }
            for perf in performance_data
        ])
        
        # 響應時間趨勢
        response_config = ChartConfig(
            chart_type=ChartType.LINE,
            title="Response Time Trend",
            x_axis='timestamp',
            y_axis='response_time'
        )
        generator = LineChartGenerator(response_config)
        charts['response_time_trend'] = generator.generate(perf_df)
        
        # 吞吐量 vs 響應時間散點圖
        scatter_config = ChartConfig(
            chart_type=ChartType.SCATTER,
            title="Throughput vs Response Time",
            x_axis='throughput',
            y_axis='response_time'
        )
        generator = ScatterPlotGenerator(scatter_config)
        charts['throughput_vs_response'] = generator.generate(perf_df)
        
        # 資源使用熱圖
        resource_data = perf_df[['test_name', 'cpu_usage', 'memory_usage']].melt(
            id_vars=['test_name'],
            var_name='resource_type',
            value_name='usage'
        )
        
        heatmap_config = ChartConfig(
            chart_type=ChartType.HEATMAP,
            title="Resource Usage Heatmap",
            x_axis='test_name',
            y_axis='resource_type'
        )
        generator = HeatmapGenerator(heatmap_config)
        charts['resource_usage_heatmap'] = generator.generate(resource_data)
        
        return charts
    
    def generate_failure_analysis_charts(self, test_results: List[TestResult]) -> Dict[str, ChartData]:
        """生成失敗分析圖表"""
        charts = {}
        
        # 失敗的測試結果
        failed_tests = [test for test in test_results if test.status in ['failed', 'error']]
        
        if not failed_tests:
            return charts
        
        # 失敗類型分佈
        failure_types = {}
        for test in failed_tests:
            failure_type = test.failure_type or 'Unknown'
            failure_types[failure_type] = failure_types.get(failure_type, 0) + 1
        
        failure_df = pd.DataFrame([
            {'failure_type': ft, 'count': count}
            for ft, count in failure_types.items()
        ])
        
        pie_config = ChartConfig(
            chart_type=ChartType.PIE,
            title="Failure Types Distribution",
            x_axis='failure_type',
            y_axis='count'
        )
        generator = PieChartGenerator(pie_config)
        charts['failure_types'] = generator.generate(failure_df)
        
        # 失敗測試時間分佈
        failure_times = [test.duration for test in failed_tests if test.duration > 0]
        if failure_times:
            time_df = pd.DataFrame({
                'duration': failure_times,
                'category': 'Failed Tests'
            })
            
            box_config = ChartConfig(
                chart_type=ChartType.BOX,
                title="Failed Test Duration Distribution",
                x_axis='category',
                y_axis='duration'
            )
            generator = BoxPlotGenerator(box_config)
            charts['failure_duration'] = generator.generate(time_df)
        
        return charts
    
    def generate_comprehensive_dashboard(self, 
                                       test_suites: List[TestSuite],
                                       performance_data: List[PerformanceMetrics]) -> Dict[str, ChartData]:
        """生成綜合儀表板"""
        charts = {}
        
        # 測試結果概覽
        overview_charts = self.generate_test_results_overview(test_suites)
        charts.update(overview_charts)
        
        # 性能圖表
        performance_charts = self.generate_performance_charts(performance_data)
        charts.update(performance_charts)
        
        # 失敗分析
        all_tests = []
        for suite in test_suites:
            all_tests.extend(suite.tests)
        
        failure_charts = self.generate_failure_analysis_charts(all_tests)
        charts.update(failure_charts)
        
        return charts
    
    def export_charts(self, charts: Dict[str, ChartData], output_dir: str):
        """導出圖表"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        for chart_name, chart_data in charts.items():
            if chart_data:
                for format in chart_data.config.export_formats:
                    file_path = output_path / f"{chart_name}.{format}"
                    generator = BaseChartGenerator(chart_data.config)
                    generator.save_chart(chart_data, str(file_path), format)


if __name__ == "__main__":
    # 示例使用
    from .visualization_config import ConfigManager
    
    config_manager = ConfigManager()
    config = config_manager.load_config()
    
    engine = VisualizationEngine(config)
    
    # 示例數據
    sample_data = pd.DataFrame({
        'timestamp': pd.date_range('2024-01-01', periods=10, freq='D'),
        'success_rate': np.random.uniform(80, 100, 10),
        'category': ['Test Suite A'] * 5 + ['Test Suite B'] * 5
    })
    
    chart = engine.generate_chart('test_results_trend', sample_data)
    if chart:
        print(f"Generated chart: {chart.title}")
        
        # 保存圖表
        output_dir = "/home/sat/ntn-stack/tests/reports/charts"
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        generator = BaseChartGenerator(chart.config)
        generator.save_chart(chart, f"{output_dir}/sample_chart.html")