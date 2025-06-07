"""
測試結果可視化配置管理系統
Visualization Configuration Management System
"""

import json
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum


class ChartType(Enum):
    """支持的圖表類型"""
    LINE = "line"
    BAR = "bar"
    HEATMAP = "heatmap"
    SCATTER = "scatter"
    PIE = "pie"
    HISTOGRAM = "histogram"
    BOX = "box"
    VIOLIN = "violin"
    RADAR = "radar"
    WATERFALL = "waterfall"


class TestType(Enum):
    """測試類型"""
    E2E = "e2e"
    LOAD = "load"
    STRESS = "stress"
    PERFORMANCE = "performance"
    UNIT = "unit"
    INTEGRATION = "integration"
    REGRESSION = "regression"


@dataclass
class ChartConfig:
    """圖表配置"""
    chart_type: ChartType
    title: str
    x_axis: str
    y_axis: str
    color_scheme: str = "viridis"
    width: int = 800
    height: int = 600
    interactive: bool = True
    show_legend: bool = True
    show_grid: bool = True
    export_formats: List[str] = None

    def __post_init__(self):
        if self.export_formats is None:
            self.export_formats = ["png", "html", "svg"]


@dataclass
class DashboardConfig:
    """儀表板配置"""
    title: str = "NTN Stack Test Results Dashboard"
    theme: str = "light"
    auto_refresh: bool = True
    refresh_interval: int = 30  # seconds
    show_filters: bool = True
    show_export: bool = True
    charts_per_row: int = 2


@dataclass
class ReportConfig:
    """報告配置"""
    template: str = "default"
    format: str = "html"  # html, pdf
    include_charts: bool = True
    include_raw_data: bool = False
    include_summary: bool = True
    include_trends: bool = True
    logo_path: Optional[str] = None


@dataclass
class DataConfig:
    """數據配置"""
    source_paths: List[str]
    formats: List[str]  # json, xml, csv, junit
    retention_days: int = 30
    aggregation_rules: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.aggregation_rules is None:
            self.aggregation_rules = {
                "performance": "avg",
                "success_rate": "avg",
                "response_time": "p95"
            }


@dataclass
class VisualizationConfig:
    """完整的可視化配置"""
    dashboard: DashboardConfig
    report: ReportConfig
    data: DataConfig
    charts: Dict[str, ChartConfig]
    analysis: Dict[str, Any]
    
    def __post_init__(self):
        if not self.charts:
            self.charts = self._get_default_charts()
        if not self.analysis:
            self.analysis = self._get_default_analysis_config()

    def _get_default_charts(self) -> Dict[str, ChartConfig]:
        """獲取默認圖表配置"""
        return {
            "test_results_trend": ChartConfig(
                chart_type=ChartType.LINE,
                title="Test Results Trend",
                x_axis="timestamp",
                y_axis="success_rate"
            ),
            "performance_comparison": ChartConfig(
                chart_type=ChartType.BAR,
                title="Performance Comparison",
                x_axis="test_name",
                y_axis="response_time"
            ),
            "test_coverage_heatmap": ChartConfig(
                chart_type=ChartType.HEATMAP,
                title="Test Coverage Heatmap",
                x_axis="module",
                y_axis="test_type"
            ),
            "failure_distribution": ChartConfig(
                chart_type=ChartType.PIE,
                title="Failure Distribution",
                x_axis="error_type",
                y_axis="count"
            ),
            "performance_regression": ChartConfig(
                chart_type=ChartType.SCATTER,
                title="Performance Regression Analysis",
                x_axis="build_number",
                y_axis="response_time"
            )
        }

    def _get_default_analysis_config(self) -> Dict[str, Any]:
        """獲取默認分析配置"""
        return {
            "trend_analysis": {
                "enabled": True,
                "window_size": 10,
                "detect_anomalies": True
            },
            "regression_detection": {
                "enabled": True,
                "threshold": 0.1,  # 10% performance degradation
                "baseline_builds": 5
            },
            "failure_analysis": {
                "enabled": True,
                "categorize_errors": True,
                "root_cause_analysis": True
            },
            "coverage_analysis": {
                "enabled": True,
                "target_coverage": 0.8,
                "critical_paths": True
            }
        }


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = Path(config_path) if config_path else Path(__file__).parent / "visualization_config.yaml"
        self.config: Optional[VisualizationConfig] = None
        
    def load_config(self) -> VisualizationConfig:
        """加載配置"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    if self.config_path.suffix.lower() == '.json':
                        config_data = json.load(f)
                    else:
                        config_data = yaml.safe_load(f)
                
                self.config = self._dict_to_config(config_data)
            else:
                self.config = self._get_default_config()
                self.save_config()
        except Exception as e:
            print(f"Error loading config: {e}")
            self.config = self._get_default_config()
            
        return self.config
    
    def save_config(self):
        """保存配置"""
        if self.config:
            config_dict = self._config_to_dict(self.config)
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                if self.config_path.suffix.lower() == '.json':
                    json.dump(config_dict, f, indent=2, ensure_ascii=False)
                else:
                    yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)
    
    def _get_default_config(self) -> VisualizationConfig:
        """獲取默認配置"""
        return VisualizationConfig(
            dashboard=DashboardConfig(),
            report=ReportConfig(),
            data=DataConfig(
                source_paths=[
                    "/home/sat/ntn-stack/tests/reports",
                    "/home/sat/ntn-stack/tests/e2e/reports",
                    "/home/sat/ntn-stack/tests/performance/reports"
                ],
                formats=["json", "xml", "junit"]
            ),
            charts={},
            analysis={}
        )
    
    def _dict_to_config(self, config_dict: Dict[str, Any]) -> VisualizationConfig:
        """將字典轉換為配置對象"""
        # 處理charts轉換
        charts = {}
        for name, chart_data in config_dict.get("charts", {}).items():
            chart_data["chart_type"] = ChartType(chart_data["chart_type"])
            charts[name] = ChartConfig(**chart_data)
        
        # 處理其他配置
        dashboard = DashboardConfig(**config_dict.get("dashboard", {}))
        report = ReportConfig(**config_dict.get("report", {}))
        data = DataConfig(**config_dict.get("data", {}))
        analysis = config_dict.get("analysis", {})
        
        return VisualizationConfig(
            dashboard=dashboard,
            report=report,
            data=data,
            charts=charts,
            analysis=analysis
        )
    
    def _config_to_dict(self, config: VisualizationConfig) -> Dict[str, Any]:
        """將配置對象轉換為字典"""
        config_dict = asdict(config)
        
        # 處理枚舉類型
        for chart_name, chart_config in config_dict["charts"].items():
            chart_config["chart_type"] = chart_config["chart_type"].value
            
        return config_dict
    
    def update_chart_config(self, chart_name: str, chart_config: ChartConfig):
        """更新圖表配置"""
        if self.config:
            self.config.charts[chart_name] = chart_config
            self.save_config()
    
    def get_chart_config(self, chart_name: str) -> Optional[ChartConfig]:
        """獲取圖表配置"""
        if self.config:
            return self.config.charts.get(chart_name)
        return None
    
    def get_test_type_config(self, test_type: TestType) -> Dict[str, Any]:
        """獲取特定測試類型的配置"""
        if not self.config:
            return {}
            
        return {
            "charts": {k: v for k, v in self.config.charts.items() 
                      if test_type.value in k.lower()},
            "analysis": self.config.analysis,
            "dashboard": self.config.dashboard,
            "report": self.config.report
        }


# 預設配置實例
def create_default_config_file():
    """創建默認配置文件"""
    config_manager = ConfigManager()
    config_manager.load_config()
    print(f"Default configuration created at: {config_manager.config_path}")


if __name__ == "__main__":
    create_default_config_file()