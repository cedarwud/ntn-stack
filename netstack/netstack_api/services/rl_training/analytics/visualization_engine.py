"""
Visualization Engine for RL Decision Analysis

提供強化學習決策分析的先進視覺化功能，包括：
- 實時決策過程視覺化
- 交互式性能分析儀表板
- 學習曲線和收斂性視覺化
- 算法比較視覺圖表
- 統計結果視覺化
- 3D 決策空間可視化
- 實時監控界面

此模組為 Phase 3 提供完整的視覺化解決方案。
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import asyncio
from collections import deque

# 嘗試導入視覺化庫，如不可用則優雅降級
try:
    import matplotlib.pyplot as plt
    import matplotlib.animation as animation
    from matplotlib.patches import Rectangle, Circle
    import seaborn as sns
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    logging.warning("matplotlib not available, static plot generation disabled")

try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    import plotly.offline as pyo
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    logging.warning("plotly not available, interactive plot generation disabled")

try:
    import bokeh.plotting as bk
    from bokeh.layouts import column, row
    from bokeh.models import ColumnDataSource, HoverTool
    BOKEH_AVAILABLE = True
except ImportError:
    BOKEH_AVAILABLE = False
    logging.warning("bokeh not available, dashboard generation disabled")

logger = logging.getLogger(__name__)

class VisualizationType(Enum):
    """視覺化類型"""
    LINE_CHART = "line_chart"
    BAR_CHART = "bar_chart"
    SCATTER_PLOT = "scatter_plot"
    BOX_PLOT = "box_plot"
    HEATMAP = "heatmap"
    HISTOGRAM = "histogram"
    VIOLIN_PLOT = "violin_plot"
    DASHBOARD = "dashboard"
    ANIMATION = "animation"
    REALTIME = "realtime"
    THREE_D = "3d_plot"

class PlotTheme(Enum):
    """繪圖主題"""
    ACADEMIC = "academic"
    PRESENTATION = "presentation"
    DARK = "dark"
    COLORBLIND_FRIENDLY = "colorblind"
    IEEE_STANDARD = "ieee"
    PUBLICATION_READY = "publication"

class ExportFormat(Enum):
    """匯出格式"""
    PNG = "png"
    PDF = "pdf"
    SVG = "svg"
    HTML = "html"
    JSON = "json"
    INTERACTIVE = "interactive"

@dataclass
class PlotConfig:
    """繪圖配置"""
    title: str
    width: int = 800
    height: int = 600
    theme: PlotTheme = PlotTheme.ACADEMIC
    color_palette: Optional[List[str]] = None
    font_size: int = 12
    dpi: int = 300
    show_grid: bool = True
    show_legend: bool = True
    legend_position: str = "upper right"
    background_color: str = "white"
    export_format: ExportFormat = ExportFormat.PNG

@dataclass
class VisualizationData:
    """視覺化數據結構"""
    data_id: str
    timestamp: datetime
    plot_type: VisualizationType
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    config: PlotConfig

@dataclass
class DashboardData:
    """儀表板數據"""
    dashboard_id: str
    title: str
    sections: List[Dict[str, Any]]
    layout_config: Dict[str, Any]
    update_frequency: float  # 秒
    data_sources: List[str]

@dataclass
class RealtimeVisualizationConfig:
    """實時視覺化配置"""
    buffer_size: int = 1000
    update_interval: float = 1.0  # 秒
    auto_scaling: bool = True
    show_confidence_bands: bool = True
    animation_speed: float = 1.0

class VisualizationEngine:
    """
    視覺化引擎
    
    提供全面的強化學習決策分析視覺化功能，支援靜態圖表、
    交互式儀表板和實時監控視覺化。
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化視覺化引擎
        
        Args:
            config: 配置參數
        """
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # 設置默認參數
        self.default_theme = PlotTheme(self.config.get('default_theme', 'academic'))
        self.output_directory = self.config.get('output_directory', './visualizations')
        self.enable_animations = self.config.get('enable_animations', True)
        self.enable_interactivity = self.config.get('enable_interactivity', True)
        
        # 顏色配置
        self.color_palettes = self._init_color_palettes()
        
        # 實時數據緩衝區
        self.realtime_buffers = {}
        self.active_dashboards = {}
        
        # 初始化繪圖後端
        self._init_plotting_backends()
        
        self.logger.info("Visualization Engine initialized")
    
    def _init_color_palettes(self) -> Dict[PlotTheme, List[str]]:
        """初始化顏色調色板"""
        palettes = {
            PlotTheme.ACADEMIC: ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b'],
            PlotTheme.PRESENTATION: ['#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6', '#34495e'],
            PlotTheme.DARK: ['#FF6B6B', '#4ECDC4', '#45B7D1', '#F9CA24', '#F0932B', '#EB4D4B'],
            PlotTheme.COLORBLIND_FRIENDLY: ['#1f77b4', '#ff7f0e', '#2ca02c', '#17becf', '#9467bd', '#8c564b'],
            PlotTheme.IEEE_STANDARD: ['#000080', '#800000', '#008000', '#800080', '#008080', '#808000'],
            PlotTheme.PUBLICATION_READY: ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#6A994E', '#774F38']
        }
        return palettes
    
    def _init_plotting_backends(self):
        """初始化繪圖後端"""
        self.backends = {
            'matplotlib': MATPLOTLIB_AVAILABLE,
            'plotly': PLOTLY_AVAILABLE,
            'bokeh': BOKEH_AVAILABLE
        }
        
        available_backends = [name for name, available in self.backends.items() if available]
        self.logger.info(f"Available plotting backends: {available_backends}")
        
        if MATPLOTLIB_AVAILABLE:
            plt.style.use('seaborn-v0_8' if hasattr(plt.style, 'seaborn-v0_8') else 'default')
    
    async def create_learning_curve_visualization(
        self,
        training_data: Dict[str, Any],
        config: Optional[PlotConfig] = None
    ) -> Dict[str, Any]:
        """
        創建學習曲線視覺化
        
        Args:
            training_data: 訓練數據，包含多個算法的學習曲線
            config: 繪圖配置
            
        Returns:
            視覺化結果和數據
        """
        plot_config = config or PlotConfig(title="Learning Curves Comparison")
        
        try:
            if PLOTLY_AVAILABLE and self.enable_interactivity:
                viz_result = await self._create_plotly_learning_curves(training_data, plot_config)
            elif MATPLOTLIB_AVAILABLE:
                viz_result = await self._create_matplotlib_learning_curves(training_data, plot_config)
            else:
                viz_result = await self._create_fallback_learning_curves(training_data, plot_config)
            
            self.logger.info("Learning curve visualization created successfully")
            return viz_result
            
        except Exception as e:
            self.logger.error(f"Error creating learning curve visualization: {e}")
            return self._create_error_visualization(str(e))
    
    async def _create_plotly_learning_curves(
        self,
        training_data: Dict[str, Any],
        config: PlotConfig
    ) -> Dict[str, Any]:
        """使用Plotly創建交互式學習曲線"""
        fig = go.Figure()
        
        colors = self.color_palettes[config.theme]
        
        for i, (algorithm, data) in enumerate(training_data.items()):
            if 'episodes' in data and 'rewards' in data:
                episodes = data['episodes']
                rewards = data['rewards']
                
                # 主要學習曲線
                fig.add_trace(go.Scatter(
                    x=episodes,
                    y=rewards,
                    mode='lines',
                    name=algorithm,
                    line=dict(color=colors[i % len(colors)], width=2),
                    hovertemplate=f"<b>{algorithm}</b><br>" +
                                  "Episode: %{x}<br>" +
                                  "Reward: %{y:.3f}<extra></extra>"
                ))
                
                # 添加置信區間（如果有）
                if 'confidence_upper' in data and 'confidence_lower' in data:
                    fig.add_trace(go.Scatter(
                        x=episodes + episodes[::-1],
                        y=data['confidence_upper'] + data['confidence_lower'][::-1],
                        fill='toself',
                        fillcolor=colors[i % len(colors)],
                        opacity=0.2,
                        line=dict(color='rgba(255,255,255,0)'),
                        showlegend=False,
                        name=f"{algorithm} CI"
                    ))
        
        # 更新佈局
        fig.update_layout(
            title=dict(text=config.title, font=dict(size=config.font_size + 4)),
            xaxis_title="Episode",
            yaxis_title="Cumulative Reward",
            font=dict(size=config.font_size),
            width=config.width,
            height=config.height,
            showlegend=config.show_legend,
            plot_bgcolor=config.background_color,
            hovermode='x unified'
        )
        
        if config.show_grid:
            fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
            fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
        
        # 生成HTML
        html_content = pyo.plot(fig, output_type='div', include_plotlyjs=True)
        
        return {
            'type': 'interactive_plot',
            'html_content': html_content,
            'figure_object': fig,
            'data_summary': self._summarize_learning_curve_data(training_data),
            'export_formats': ['html', 'png', 'pdf', 'svg']
        }
    
    async def _create_matplotlib_learning_curves(
        self,
        training_data: Dict[str, Any],
        config: PlotConfig
    ) -> Dict[str, Any]:
        """使用Matplotlib創建學習曲線"""
        fig, ax = plt.subplots(figsize=(config.width/100, config.height/100), dpi=config.dpi)
        
        colors = self.color_palettes[config.theme]
        
        for i, (algorithm, data) in enumerate(training_data.items()):
            if 'episodes' in data and 'rewards' in data:
                episodes = data['episodes']
                rewards = data['rewards']
                
                # 主要學習曲線
                ax.plot(episodes, rewards, 
                       label=algorithm, 
                       color=colors[i % len(colors)], 
                       linewidth=2)
                
                # 添加置信區間（如果有）
                if 'confidence_upper' in data and 'confidence_lower' in data:
                    ax.fill_between(episodes, 
                                   data['confidence_lower'], 
                                   data['confidence_upper'],
                                   alpha=0.2, 
                                   color=colors[i % len(colors)])
        
        # 設置圖表屬性
        ax.set_title(config.title, fontsize=config.font_size + 4, fontweight='bold')
        ax.set_xlabel('Episode', fontsize=config.font_size)
        ax.set_ylabel('Cumulative Reward', fontsize=config.font_size)
        
        if config.show_legend:
            ax.legend(fontsize=config.font_size - 2, loc=config.legend_position)
        
        if config.show_grid:
            ax.grid(True, alpha=0.3)
        
        # 保存圖片
        output_path = f"{self.output_directory}/learning_curves_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{config.export_format.value}"
        plt.savefig(output_path, dpi=config.dpi, bbox_inches='tight', 
                   facecolor=config.background_color)
        plt.close()
        
        return {
            'type': 'static_plot',
            'file_path': output_path,
            'data_summary': self._summarize_learning_curve_data(training_data),
            'export_formats': ['png', 'pdf', 'svg']
        }
    
    async def create_performance_comparison_visualization(
        self,
        comparison_data: Dict[str, Any],
        config: Optional[PlotConfig] = None
    ) -> Dict[str, Any]:
        """
        創建性能比較視覺化
        
        Args:
            comparison_data: 比較數據
            config: 繪圖配置
            
        Returns:
            視覺化結果
        """
        plot_config = config or PlotConfig(title="Algorithm Performance Comparison")
        
        try:
            if PLOTLY_AVAILABLE and self.enable_interactivity:
                viz_result = await self._create_plotly_performance_comparison(comparison_data, plot_config)
            elif MATPLOTLIB_AVAILABLE:
                viz_result = await self._create_matplotlib_performance_comparison(comparison_data, plot_config)
            else:
                viz_result = await self._create_fallback_performance_comparison(comparison_data, plot_config)
            
            self.logger.info("Performance comparison visualization created successfully")
            return viz_result
            
        except Exception as e:
            self.logger.error(f"Error creating performance comparison: {e}")
            return self._create_error_visualization(str(e))
    
    async def _create_plotly_performance_comparison(
        self,
        comparison_data: Dict[str, Any],
        config: PlotConfig
    ) -> Dict[str, Any]:
        """使用Plotly創建性能比較視覺化"""
        # 創建子圖
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Mean Performance', 'Performance Distribution', 
                          'Success Rate', 'Convergence Speed'),
            specs=[[{"type": "bar"}, {"type": "box"}],
                   [{"type": "bar"}, {"type": "bar"}]]
        )
        
        algorithms = list(comparison_data.keys())
        colors = self.color_palettes[config.theme]
        
        # 1. 平均性能條形圖
        mean_rewards = [comparison_data[alg].get('mean_reward', 0) for alg in algorithms]
        std_rewards = [comparison_data[alg].get('std_reward', 0) for alg in algorithms]
        
        fig.add_trace(
            go.Bar(x=algorithms, y=mean_rewards, 
                   error_y=dict(type='data', array=std_rewards),
                   marker_color=colors[:len(algorithms)],
                   name="Mean Reward"),
            row=1, col=1
        )
        
        # 2. 性能分布箱線圖
        for i, algorithm in enumerate(algorithms):
            if 'all_rewards' in comparison_data[algorithm]:
                fig.add_trace(
                    go.Box(y=comparison_data[algorithm]['all_rewards'],
                           name=algorithm,
                           marker_color=colors[i % len(colors)],
                           showlegend=False),
                    row=1, col=2
                )
        
        # 3. 成功率
        success_rates = [comparison_data[alg].get('success_rate', 0) * 100 for alg in algorithms]
        fig.add_trace(
            go.Bar(x=algorithms, y=success_rates,
                   marker_color=colors[:len(algorithms)],
                   name="Success Rate",
                   showlegend=False),
            row=2, col=1
        )
        
        # 4. 收斂速度
        convergence_episodes = [comparison_data[alg].get('convergence_episodes', 0) for alg in algorithms]
        fig.add_trace(
            go.Bar(x=algorithms, y=convergence_episodes,
                   marker_color=colors[:len(algorithms)],
                   name="Episodes to Convergence",
                   showlegend=False),
            row=2, col=2
        )
        
        # 更新佈局
        fig.update_layout(
            title=dict(text=config.title, font=dict(size=config.font_size + 4)),
            font=dict(size=config.font_size),
            width=config.width,
            height=config.height,
            showlegend=False
        )
        
        # 更新軸標籤
        fig.update_yaxes(title_text="Cumulative Reward", row=1, col=1)
        fig.update_yaxes(title_text="Reward Distribution", row=1, col=2)
        fig.update_yaxes(title_text="Success Rate (%)", row=2, col=1)
        fig.update_yaxes(title_text="Episodes", row=2, col=2)
        
        html_content = pyo.plot(fig, output_type='div', include_plotlyjs=True)
        
        return {
            'type': 'interactive_comparison',
            'html_content': html_content,
            'figure_object': fig,
            'data_summary': self._summarize_comparison_data(comparison_data)
        }
    
    async def create_statistical_visualization(
        self,
        statistical_results: Dict[str, Any],
        config: Optional[PlotConfig] = None
    ) -> Dict[str, Any]:
        """
        創建統計結果視覺化
        
        Args:
            statistical_results: 統計測試結果
            config: 繪圖配置
            
        Returns:
            視覺化結果
        """
        plot_config = config or PlotConfig(title="Statistical Analysis Results")
        
        try:
            if PLOTLY_AVAILABLE and self.enable_interactivity:
                viz_result = await self._create_plotly_statistical_viz(statistical_results, plot_config)
            elif MATPLOTLIB_AVAILABLE:
                viz_result = await self._create_matplotlib_statistical_viz(statistical_results, plot_config)
            else:
                viz_result = await self._create_fallback_statistical_viz(statistical_results, plot_config)
            
            self.logger.info("Statistical visualization created successfully")
            return viz_result
            
        except Exception as e:
            self.logger.error(f"Error creating statistical visualization: {e}")
            return self._create_error_visualization(str(e))
    
    async def _create_plotly_statistical_viz(
        self,
        statistical_results: Dict[str, Any],
        config: PlotConfig
    ) -> Dict[str, Any]:
        """使用Plotly創建統計視覺化"""
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('P-values', 'Effect Sizes'),
            specs=[[{"type": "bar"}, {"type": "bar"}]]
        )
        
        # 提取統計數據
        test_names = []
        p_values = []
        effect_sizes = []
        
        for test_name, result in statistical_results.items():
            if isinstance(result, dict):
                test_names.append(test_name)
                p_values.append(result.get('p_value', 1.0))
                effect_sizes.append(result.get('effect_size', 0.0))
        
        colors = self.color_palettes[config.theme]
        
        # P值條形圖
        p_value_colors = ['red' if p < 0.05 else 'blue' for p in p_values]
        fig.add_trace(
            go.Bar(x=test_names, y=p_values,
                   marker_color=p_value_colors,
                   name="P-values"),
            row=1, col=1
        )
        
        # 添加顯著性線
        fig.add_hline(y=0.05, line_dash="dash", line_color="red", 
                     annotation_text="α = 0.05", row=1, col=1)
        
        # 效應大小條形圖
        fig.add_trace(
            go.Bar(x=test_names, y=effect_sizes,
                   marker_color=colors[:len(test_names)],
                   name="Effect Sizes",
                   showlegend=False),
            row=1, col=2
        )
        
        # 更新佈局
        fig.update_layout(
            title=dict(text=config.title, font=dict(size=config.font_size + 4)),
            font=dict(size=config.font_size),
            width=config.width,
            height=config.height,
            showlegend=False
        )
        
        fig.update_yaxes(title_text="P-value", row=1, col=1)
        fig.update_yaxes(title_text="Effect Size", row=1, col=2)
        fig.update_xaxes(tickangle=45)
        
        html_content = pyo.plot(fig, output_type='div', include_plotlyjs=True)
        
        return {
            'type': 'statistical_visualization',
            'html_content': html_content,
            'figure_object': fig,
            'significance_summary': self._summarize_significance_results(statistical_results)
        }
    
    async def create_convergence_analysis_visualization(
        self,
        convergence_data: Dict[str, Any],
        config: Optional[PlotConfig] = None
    ) -> Dict[str, Any]:
        """
        創建收斂性分析視覺化
        
        Args:
            convergence_data: 收斂分析數據
            config: 繪圖配置
            
        Returns:
            視覺化結果
        """
        plot_config = config or PlotConfig(title="Convergence Analysis")
        
        try:
            if PLOTLY_AVAILABLE and self.enable_interactivity:
                viz_result = await self._create_plotly_convergence_viz(convergence_data, plot_config)
            elif MATPLOTLIB_AVAILABLE:
                viz_result = await self._create_matplotlib_convergence_viz(convergence_data, plot_config)
            else:
                viz_result = await self._create_fallback_convergence_viz(convergence_data, plot_config)
            
            self.logger.info("Convergence analysis visualization created successfully")
            return viz_result
            
        except Exception as e:
            self.logger.error(f"Error creating convergence visualization: {e}")
            return self._create_error_visualization(str(e))
    
    async def create_realtime_dashboard(
        self,
        dashboard_config: DashboardData
    ) -> Dict[str, Any]:
        """
        創建實時監控儀表板
        
        Args:
            dashboard_config: 儀表板配置
            
        Returns:
            儀表板設置結果
        """
        try:
            if BOKEH_AVAILABLE:
                dashboard_result = await self._create_bokeh_dashboard(dashboard_config)
            elif PLOTLY_AVAILABLE:
                dashboard_result = await self._create_plotly_dashboard(dashboard_config)
            else:
                dashboard_result = await self._create_fallback_dashboard(dashboard_config)
            
            # 註冊儀表板
            self.active_dashboards[dashboard_config.dashboard_id] = dashboard_result
            
            self.logger.info(f"Realtime dashboard created: {dashboard_config.dashboard_id}")
            return dashboard_result
            
        except Exception as e:
            self.logger.error(f"Error creating realtime dashboard: {e}")
            return self._create_error_visualization(str(e))
    
    async def _create_bokeh_dashboard(self, config: DashboardData) -> Dict[str, Any]:
        """使用Bokeh創建實時儀表板"""
        # 這裡會創建一個完整的Bokeh應用
        dashboard_elements = []
        
        for section in config.sections:
            section_type = section.get('type', 'line_chart')
            section_data = section.get('data', {})
            
            if section_type == 'performance_monitor':
                element = await self._create_bokeh_performance_monitor(section_data)
            elif section_type == 'learning_progress':
                element = await self._create_bokeh_learning_progress(section_data)
            elif section_type == 'decision_tracker':
                element = await self._create_bokeh_decision_tracker(section_data)
            else:
                element = await self._create_bokeh_generic_chart(section_data)
            
            dashboard_elements.append(element)
        
        # 組合佈局
        layout = column(*dashboard_elements)
        
        return {
            'type': 'bokeh_dashboard',
            'layout': layout,
            'dashboard_id': config.dashboard_id,
            'update_frequency': config.update_frequency,
            'status': 'active'
        }
    
    async def update_realtime_data(
        self,
        dashboard_id: str,
        data_update: Dict[str, Any]
    ) -> bool:
        """
        更新實時數據
        
        Args:
            dashboard_id: 儀表板ID
            data_update: 數據更新
            
        Returns:
            更新是否成功
        """
        try:
            if dashboard_id not in self.active_dashboards:
                self.logger.warning(f"Dashboard {dashboard_id} not found")
                return False
            
            dashboard = self.active_dashboards[dashboard_id]
            
            # 更新數據緩衝區
            if dashboard_id not in self.realtime_buffers:
                self.realtime_buffers[dashboard_id] = deque(maxlen=1000)
            
            self.realtime_buffers[dashboard_id].append({
                'timestamp': datetime.now(),
                'data': data_update
            })
            
            # 觸發儀表板更新
            await self._update_dashboard_display(dashboard_id, data_update)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating realtime data: {e}")
            return False
    
    async def export_visualization(
        self,
        viz_data: Dict[str, Any],
        export_format: ExportFormat,
        output_path: Optional[str] = None
    ) -> str:
        """
        匯出視覺化結果
        
        Args:
            viz_data: 視覺化數據
            export_format: 匯出格式
            output_path: 輸出路徑
            
        Returns:
            匯出檔案路徑
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            if output_path is None:
                output_path = f"{self.output_directory}/visualization_{timestamp}.{export_format.value}"
            
            if export_format == ExportFormat.HTML and 'html_content' in viz_data:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(viz_data['html_content'])
            
            elif export_format == ExportFormat.JSON:
                # 匯出視覺化配置和數據
                export_data = {
                    'visualization_type': viz_data.get('type', 'unknown'),
                    'creation_timestamp': timestamp,
                    'data_summary': viz_data.get('data_summary', {}),
                    'configuration': viz_data.get('config', {})
                }
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, default=str)
            
            elif export_format in [ExportFormat.PNG, ExportFormat.PDF, ExportFormat.SVG]:
                if 'figure_object' in viz_data and PLOTLY_AVAILABLE:
                    # Plotly圖表匯出
                    fig = viz_data['figure_object']
                    fig.write_image(output_path)
                elif 'file_path' in viz_data:
                    # 已存在的檔案
                    output_path = viz_data['file_path']
            
            self.logger.info(f"Visualization exported to: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error exporting visualization: {e}")
            return ""
    
    async def create_3d_decision_space_visualization(
        self,
        decision_data: Dict[str, Any],
        config: Optional[PlotConfig] = None
    ) -> Dict[str, Any]:
        """
        創建3D決策空間視覺化
        
        Args:
            decision_data: 決策空間數據
            config: 繪圖配置
            
        Returns:
            3D視覺化結果
        """
        plot_config = config or PlotConfig(title="3D Decision Space Analysis")
        
        try:
            if PLOTLY_AVAILABLE:
                viz_result = await self._create_plotly_3d_decision_space(decision_data, plot_config)
            else:
                viz_result = await self._create_fallback_3d_visualization(decision_data, plot_config)
            
            self.logger.info("3D decision space visualization created successfully")
            return viz_result
            
        except Exception as e:
            self.logger.error(f"Error creating 3D visualization: {e}")
            return self._create_error_visualization(str(e))
    
    async def _create_plotly_3d_decision_space(
        self,
        decision_data: Dict[str, Any],
        config: PlotConfig
    ) -> Dict[str, Any]:
        """使用Plotly創建3D決策空間"""
        fig = go.Figure()
        
        # 提取決策點數據
        states = decision_data.get('states', [])
        actions = decision_data.get('actions', [])
        rewards = decision_data.get('rewards', [])
        
        if len(states) > 0 and isinstance(states[0], (list, tuple)) and len(states[0]) >= 3:
            # 3D狀態空間
            x_coords = [state[0] for state in states]
            y_coords = [state[1] for state in states]
            z_coords = [state[2] for state in states]
            
            # 創建3D散點圖
            fig.add_trace(go.Scatter3d(
                x=x_coords,
                y=y_coords,
                z=z_coords,
                mode='markers',
                marker=dict(
                    size=5,
                    color=rewards,
                    colorscale='Viridis',
                    showscale=True,
                    colorbar=dict(title="Reward")
                ),
                text=[f"Action: {action}<br>Reward: {reward:.3f}" 
                      for action, reward in zip(actions, rewards)],
                hovertemplate="State: (%{x:.2f}, %{y:.2f}, %{z:.2f})<br>%{text}<extra></extra>",
                name="Decision Points"
            ))
            
            # 添加軌跡線
            fig.add_trace(go.Scatter3d(
                x=x_coords,
                y=y_coords,
                z=z_coords,
                mode='lines',
                line=dict(color='red', width=2),
                name="Decision Trajectory",
                showlegend=True
            ))
        
        # 更新佈局
        fig.update_layout(
            title=dict(text=config.title, font=dict(size=config.font_size + 4)),
            scene=dict(
                xaxis_title="State Dimension 1",
                yaxis_title="State Dimension 2",
                zaxis_title="State Dimension 3",
                camera=dict(
                    eye=dict(x=1.5, y=1.5, z=1.5)
                )
            ),
            width=config.width,
            height=config.height,
            font=dict(size=config.font_size)
        )
        
        html_content = pyo.plot(fig, output_type='div', include_plotlyjs=True)
        
        return {
            'type': '3d_decision_space',
            'html_content': html_content,
            'figure_object': fig,
            'data_summary': {
                'total_decisions': len(states),
                'state_dimensions': len(states[0]) if states else 0,
                'reward_range': [min(rewards), max(rewards)] if rewards else [0, 0]
            }
        }
    
    # 輔助方法
    def _summarize_learning_curve_data(self, training_data: Dict[str, Any]) -> Dict[str, Any]:
        """總結學習曲線數據"""
        summary = {
            'algorithms_count': len(training_data),
            'algorithms': list(training_data.keys()),
            'performance_summary': {}
        }
        
        for algorithm, data in training_data.items():
            if 'rewards' in data:
                rewards = data['rewards']
                summary['performance_summary'][algorithm] = {
                    'final_reward': rewards[-1] if rewards else 0,
                    'best_reward': max(rewards) if rewards else 0,
                    'avg_reward': np.mean(rewards) if rewards else 0,
                    'total_episodes': len(rewards)
                }
        
        return summary
    
    def _summarize_comparison_data(self, comparison_data: Dict[str, Any]) -> Dict[str, Any]:
        """總結比較數據"""
        algorithms = list(comparison_data.keys())
        
        best_algorithm = max(algorithms, 
                           key=lambda alg: comparison_data[alg].get('mean_reward', 0))
        
        return {
            'total_algorithms': len(algorithms),
            'best_algorithm': best_algorithm,
            'best_performance': comparison_data[best_algorithm].get('mean_reward', 0),
            'performance_range': [
                min(comparison_data[alg].get('mean_reward', 0) for alg in algorithms),
                max(comparison_data[alg].get('mean_reward', 0) for alg in algorithms)
            ]
        }
    
    def _summarize_significance_results(self, statistical_results: Dict[str, Any]) -> Dict[str, Any]:
        """總結顯著性結果"""
        significant_tests = []
        total_tests = 0
        
        for test_name, result in statistical_results.items():
            if isinstance(result, dict):
                total_tests += 1
                p_value = result.get('p_value', 1.0)
                if p_value < 0.05:
                    significant_tests.append(test_name)
        
        return {
            'total_tests': total_tests,
            'significant_tests': len(significant_tests),
            'significance_rate': len(significant_tests) / total_tests if total_tests > 0 else 0,
            'significant_comparisons': significant_tests
        }
    
    def _create_error_visualization(self, error_message: str) -> Dict[str, Any]:
        """創建錯誤視覺化"""
        return {
            'type': 'error',
            'error_message': error_message,
            'html_content': f"<div style='color: red; text-align: center;'><h3>Visualization Error</h3><p>{error_message}</p></div>",
            'data_summary': {'error': True}
        }
    
    async def _create_fallback_learning_curves(
        self,
        training_data: Dict[str, Any],
        config: PlotConfig
    ) -> Dict[str, Any]:
        """創建備用學習曲線視覺化"""
        # 簡化的文本格式輸出
        summary = self._summarize_learning_curve_data(training_data)
        
        text_output = f"Learning Curves Summary\\n"
        text_output += f"Total Algorithms: {summary['algorithms_count']}\\n\\n"
        
        for algorithm, perf in summary['performance_summary'].items():
            text_output += f"{algorithm}:\\n"
            text_output += f"  Final Reward: {perf['final_reward']:.3f}\\n"
            text_output += f"  Best Reward: {perf['best_reward']:.3f}\\n"
            text_output += f"  Average Reward: {perf['avg_reward']:.3f}\\n"
            text_output += f"  Total Episodes: {perf['total_episodes']}\\n\\n"
        
        return {
            'type': 'text_summary',
            'content': text_output,
            'data_summary': summary
        }
    
    async def _create_fallback_performance_comparison(
        self,
        comparison_data: Dict[str, Any],
        config: PlotConfig
    ) -> Dict[str, Any]:
        """創建備用性能比較視覺化"""
        summary = self._summarize_comparison_data(comparison_data)
        
        text_output = f"Performance Comparison Summary\\n"
        text_output += f"Best Algorithm: {summary['best_algorithm']}\\n"
        text_output += f"Best Performance: {summary['best_performance']:.3f}\\n\\n"
        
        for algorithm, data in comparison_data.items():
            text_output += f"{algorithm}: {data.get('mean_reward', 0):.3f}\\n"
        
        return {
            'type': 'text_summary',
            'content': text_output,
            'data_summary': summary
        }
    
    async def _update_dashboard_display(self, dashboard_id: str, data_update: Dict[str, Any]):
        """更新儀表板顯示"""
        # 此方法將在實際實現中處理儀表板的實時更新
        self.logger.debug(f"Updating dashboard {dashboard_id} with new data")
    
    async def get_dashboard_status(self, dashboard_id: str) -> Dict[str, Any]:
        """獲取儀表板狀態"""
        if dashboard_id in self.active_dashboards:
            dashboard = self.active_dashboards[dashboard_id]
            return {
                'dashboard_id': dashboard_id,
                'status': dashboard.get('status', 'unknown'),
                'type': dashboard.get('type', 'unknown'),
                'last_update': datetime.now().isoformat(),
                'data_points': len(self.realtime_buffers.get(dashboard_id, []))
            }
        else:
            return {
                'dashboard_id': dashboard_id,
                'status': 'not_found',
                'error': 'Dashboard not found'
            }
    
    async def cleanup_dashboards(self):
        """清理非活躍的儀表板"""
        # 清理邏輯
        cleanup_count = 0
        for dashboard_id in list(self.active_dashboards.keys()):
            # 實際實現中可以檢查儀表板是否仍在使用
            if dashboard_id in self.realtime_buffers:
                buffer = self.realtime_buffers[dashboard_id]
                if len(buffer) == 0:
                    del self.active_dashboards[dashboard_id]
                    del self.realtime_buffers[dashboard_id]
                    cleanup_count += 1
        
        self.logger.info(f"Cleaned up {cleanup_count} inactive dashboards")
        return cleanup_count

class RealtimeVisualizationService:
    """
    實時視覺化服務
    
    管理實時數據流和動態視覺化更新
    """
    
    def __init__(self, visualization_engine: VisualizationEngine):
        """
        初始化實時視覺化服務
        
        Args:
            visualization_engine: 視覺化引擎實例
        """
        self.viz_engine = visualization_engine
        self.active_streams = {}
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def start_realtime_stream(
        self,
        stream_id: str,
        config: RealtimeVisualizationConfig
    ) -> bool:
        """
        開始實時數據流
        
        Args:
            stream_id: 數據流ID
            config: 實時視覺化配置
            
        Returns:
            是否成功開始
        """
        try:
            stream_info = {
                'config': config,
                'start_time': datetime.now(),
                'status': 'active',
                'data_buffer': deque(maxlen=config.buffer_size)
            }
            
            self.active_streams[stream_id] = stream_info
            
            self.logger.info(f"Started realtime stream: {stream_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting realtime stream: {e}")
            return False
    
    async def push_realtime_data(
        self,
        stream_id: str,
        data: Dict[str, Any]
    ) -> bool:
        """
        推送實時數據
        
        Args:
            stream_id: 數據流ID
            data: 數據
            
        Returns:
            是否成功推送
        """
        try:
            if stream_id not in self.active_streams:
                self.logger.warning(f"Stream {stream_id} not found")
                return False
            
            stream = self.active_streams[stream_id]
            stream['data_buffer'].append({
                'timestamp': datetime.now(),
                'data': data
            })
            
            # 觸發視覺化更新
            await self._update_realtime_visualization(stream_id)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error pushing realtime data: {e}")
            return False
    
    async def _update_realtime_visualization(self, stream_id: str):
        """更新實時視覺化"""
        # 實際實現中將根據數據流更新相關的視覺化組件
        self.logger.debug(f"Updating realtime visualization for stream: {stream_id}")
    
    async def stop_realtime_stream(self, stream_id: str) -> bool:
        """
        停止實時數據流
        
        Args:
            stream_id: 數據流ID
            
        Returns:
            是否成功停止
        """
        try:
            if stream_id in self.active_streams:
                del self.active_streams[stream_id]
                self.logger.info(f"Stopped realtime stream: {stream_id}")
                return True
            else:
                self.logger.warning(f"Stream {stream_id} not found")
                return False
                
        except Exception as e:
            self.logger.error(f"Error stopping realtime stream: {e}")
            return False
    
    def get_active_streams(self) -> List[str]:
        """獲取活躍的數據流列表"""
        return list(self.active_streams.keys())