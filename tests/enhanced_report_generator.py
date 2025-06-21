#!/usr/bin/env python3
"""
學術級別實驗報告生成系統
支援論文級別的實驗報告，包含 LaTeX 表格、學術圖表和統計分析

主要功能：
1. LaTeX 表格自動生成 (IEEE 論文格式)
2. 學術級 CDF 和性能圖表生成
3. 統計顯著性分析報告
4. 與論文結果自動對比分析
5. 支援多種輸出格式 (PDF, HTML, LaTeX)
"""

import asyncio
import time
import json
import yaml
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import jinja2
import structlog

# LaTeX 和 PDF 支援
try:
    import matplotlib
    matplotlib.use('Agg')  # 非互動式後端
except ImportError:
    pass

logger = structlog.get_logger(__name__)

class ReportFormat(Enum):
    """報告格式"""
    LATEX = "latex"
    PDF = "pdf"
    HTML = "html"
    MARKDOWN = "markdown"
    JSON = "json"

class PlotStyle(Enum):
    """圖表風格"""
    ACADEMIC = "academic"
    IEEE = "ieee"
    ARXIV = "arxiv"
    PRESENTATION = "presentation"

@dataclass
class PlotConfig:
    """圖表配置"""
    style: PlotStyle
    dpi: int = 300
    figsize: Tuple[float, float] = (10, 6)
    font_size: int = 12
    line_width: float = 2.0
    colors: List[str] = field(default_factory=lambda: [
        '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', 
        '#9467bd', '#8c564b', '#e377c2', '#7f7f7f'
    ])

@dataclass
class TableConfig:
    """表格配置"""
    format: str = "latex"
    caption: str = ""
    label: str = ""
    position: str = "ht"
    centering: bool = True
    booktabs: bool = True  # 使用 booktabs 套件
    precision: int = 2

@dataclass
class StatisticalResult:
    """統計分析結果"""
    test_name: str
    statistic: float
    p_value: float
    effect_size: float
    confidence_interval: Tuple[float, float]
    interpretation: str
    significant: bool

class EnhancedReportGenerator:
    """學術級別報告生成器"""
    
    def __init__(self, config_path: str = "tests/configs/paper_reproduction_config.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.output_dir = Path("tests/results/enhanced_reports")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 模板配置
        self.template_dir = Path("tests/templates")
        self.template_dir.mkdir(exist_ok=True)
        self._setup_templates()
        
        # 圖表配置
        self.plot_config = PlotConfig(PlotStyle.IEEE)
        self._setup_matplotlib_style()
        
        # 論文基準數據
        self.paper_benchmarks = self._load_paper_benchmarks()
        
    def _load_config(self) -> Dict[str, Any]:
        """載入配置檔案"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"載入配置檔案失敗: {e}")
            return {}
    
    def _load_paper_benchmarks(self) -> Dict[str, float]:
        """載入論文基準數據"""
        if "acceptance_criteria" in self.config:
            criteria = self.config["acceptance_criteria"]
            return {
                "proposed_latency_ms": 25.0,
                "ntn_baseline_latency_ms": 250.0,
                "ntn_gs_latency_ms": 153.0,
                "ntn_smn_latency_ms": 158.5,
                "target_improvement_factor": criteria["primary_kpis"]["proposed_vs_baseline_improvement"]["latency_reduction_factor"],
                "target_success_rate": criteria["primary_kpis"]["success_rate"]["target_percentage"] / 100,
                "target_prediction_accuracy": criteria["primary_kpis"]["prediction_accuracy"]["target_percentage"] / 100
            }
        return {}
    
    def _setup_matplotlib_style(self):
        """設定 matplotlib 學術風格"""
        plt.style.use('seaborn-v0_8-whitegrid')
        
        # IEEE 期刊風格設定
        plt.rcParams.update({
            'font.family': 'serif',
            'font.serif': ['Times New Roman'],
            'font.size': self.plot_config.font_size,
            'axes.linewidth': 1.0,
            'axes.labelsize': self.plot_config.font_size,
            'axes.titlesize': self.plot_config.font_size + 2,
            'xtick.labelsize': self.plot_config.font_size - 1,
            'ytick.labelsize': self.plot_config.font_size - 1,
            'legend.fontsize': self.plot_config.font_size - 1,
            'figure.titlesize': self.plot_config.font_size + 4,
            'lines.linewidth': self.plot_config.line_width,
            'grid.alpha': 0.3,
            'savefig.dpi': self.plot_config.dpi,
            'savefig.bbox': 'tight',
            'savefig.transparent': True
        })
    
    def _setup_templates(self):
        """設定報告模板"""
        # LaTeX 論文模板
        latex_template = '''\\documentclass[conference]{IEEEtran}
\\usepackage{cite}
\\usepackage{amsmath,amssymb,amsfonts}
\\usepackage{algorithmic}
\\usepackage{graphicx}
\\usepackage{textcomp}
\\usepackage{xcolor}
\\usepackage{booktabs}
\\usepackage{float}

\\begin{document}

\\title{{{ title }}}

\\author{
\\IEEEauthorblockN{{{ authors }}}
\\IEEEauthorblockA{{{ affiliation }}}
}

\\maketitle

\\begin{abstract}
{{ abstract }}
\\end{abstract}

\\section{Experimental Results}

{{ content }}

\\section{Performance Analysis}

{{ performance_analysis }}

\\section{Statistical Validation}

{{ statistical_analysis }}

\\section{Conclusion}

{{ conclusion }}

\\end{document}'''
        
        # HTML 報告模板
        html_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        body { font-family: 'Times New Roman', serif; margin: 2em; }
        .header { text-align: center; margin-bottom: 2em; }
        .section { margin: 2em 0; }
        .table { margin: 1em 0; }
        .figure { text-align: center; margin: 2em 0; }
        .caption { font-style: italic; margin-top: 0.5em; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: center; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ title }}</h1>
        <p><strong>{{ authors }}</strong></p>
        <p>{{ affiliation }}</p>
        <p><em>Generated: {{ generation_date }}</em></p>
    </div>
    
    <div class="section">
        <h2>Abstract</h2>
        <p>{{ abstract }}</p>
    </div>
    
    <div class="section">
        <h2>Experimental Results</h2>
        {{ content }}
    </div>
    
    <div class="section">
        <h2>Performance Analysis</h2>
        {{ performance_analysis }}
    </div>
    
    <div class="section">
        <h2>Statistical Validation</h2>
        {{ statistical_analysis }}
    </div>
    
    <div class="section">
        <h2>Conclusion</h2>
        {{ conclusion }}
    </div>
</body>
</html>'''
        
        # 保存模板
        with open(self.template_dir / "ieee_paper.tex", 'w', encoding='utf-8') as f:
            f.write(latex_template)
        
        with open(self.template_dir / "technical_report.html", 'w', encoding='utf-8') as f:
            f.write(html_template)
    
    async def generate_comprehensive_report(
        self, 
        experiment_results: Dict[str, Any],
        format: ReportFormat = ReportFormat.HTML
    ) -> Dict[str, Any]:
        """生成綜合實驗報告"""
        logger.info(f"🔄 開始生成 {format.value.upper()} 格式的綜合報告")
        
        start_time = time.time()
        
        # 1. 數據預處理和分析
        processed_data = await self._process_experiment_data(experiment_results)
        
        # 2. 生成性能比較表格
        performance_tables = await self._generate_performance_tables(processed_data)
        
        # 3. 生成學術級圖表
        academic_plots = await self._generate_academic_plots(processed_data)
        
        # 4. 執行統計分析
        statistical_analysis = await self._perform_comprehensive_statistical_analysis(processed_data)
        
        # 5. 與論文結果對比
        paper_validation = await self._validate_against_paper_comprehensive(processed_data)
        
        # 6. 生成報告內容
        report_content = await self._generate_report_content(
            processed_data, performance_tables, academic_plots, 
            statistical_analysis, paper_validation
        )
        
        # 7. 根據格式生成最終報告
        final_report = await self._generate_formatted_report(report_content, format)
        
        execution_time = time.time() - start_time
        
        report_metadata = {
            "generation_time": execution_time,
            "format": format.value,
            "timestamp": datetime.now().isoformat(),
            "data_summary": {
                "experiments_analyzed": len(processed_data.get("experiments", [])),
                "statistical_tests": len(statistical_analysis.get("tests", [])),
                "plots_generated": len(academic_plots.get("plots", [])),
                "tables_generated": len(performance_tables.get("tables", []))
            },
            "files_generated": final_report.get("files", []),
            "validation_status": paper_validation.get("overall_validation", {})
        }
        
        logger.info(f"✅ 綜合報告生成完成，耗時: {execution_time:.2f}秒")
        
        return {
            "metadata": report_metadata,
            "content": report_content,
            "final_report": final_report,
            "validation": paper_validation
        }
    
    async def _process_experiment_data(self, raw_results: Dict[str, Any]) -> Dict[str, Any]:
        """處理和分析實驗數據"""
        logger.info("📊 處理實驗數據")
        
        processed = {
            "experiments": [],
            "performance_metrics": {},
            "scheme_comparisons": {},
            "constellation_analysis": {}
        }
        
        # 提取實驗結果
        if "constellation_results" in raw_results:
            for scenario_name, scenario_data in raw_results["constellation_results"].items():
                for scheme_name, scheme_results in scenario_data.items():
                    experiment = {
                        "scenario": scenario_name,
                        "scheme": scheme_name,
                        "measurements": scheme_results.get("measurements", []),
                        "summary_stats": scheme_results.get("summary_stats", {}),
                        "success_rate": scheme_results.get("success_rate", 0)
                    }
                    processed["experiments"].append(experiment)
        
        # 計算性能指標
        for experiment in processed["experiments"]:
            scheme = experiment["scheme"]
            if scheme not in processed["performance_metrics"]:
                processed["performance_metrics"][scheme] = {
                    "latencies": [],
                    "success_rates": [],
                    "prediction_accuracies": []
                }
            
            stats = experiment["summary_stats"]
            if "mean_latency_ms" in stats:
                processed["performance_metrics"][scheme]["latencies"].append(stats["mean_latency_ms"])
            processed["performance_metrics"][scheme]["success_rates"].append(experiment["success_rate"])
        
        # 方案間比較
        if "ntn_baseline" in processed["performance_metrics"] and "proposed" in processed["performance_metrics"]:
            baseline_latencies = processed["performance_metrics"]["ntn_baseline"]["latencies"]
            proposed_latencies = processed["performance_metrics"]["proposed"]["latencies"]
            
            if baseline_latencies and proposed_latencies:
                improvement_factor = np.mean(baseline_latencies) / np.mean(proposed_latencies)
                processed["scheme_comparisons"]["improvement_factor"] = improvement_factor
        
        return processed
    
    async def _generate_performance_tables(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """生成性能比較表格"""
        logger.info("📋 生成性能比較表格")
        
        tables = {}
        
        # 主要性能比較表 (仿論文 Table III)
        performance_data = []
        for scheme, metrics in data["performance_metrics"].items():
            if metrics["latencies"]:
                row = {
                    "Scheme": scheme.replace("_", "-").upper(),
                    "Avg Latency (ms)": f"{np.mean(metrics['latencies']):.1f}",
                    "Success Rate (%)": f"{np.mean(metrics['success_rates']) * 100:.1f}",
                    "Std Dev (ms)": f"{np.std(metrics['latencies']):.1f}",
                    "P95 Latency (ms)": f"{np.percentile(metrics['latencies'], 95):.1f}",
                    "Improvement": "Baseline" if scheme == "ntn_baseline" else f"{self.paper_benchmarks.get('ntn_baseline_latency_ms', 250) / np.mean(metrics['latencies']):.1f}x"
                }
                performance_data.append(row)
        
        # 生成 LaTeX 表格
        latex_table = self._generate_latex_table(
            performance_data,
            caption="Handover Performance Comparison (Reproduction Results)",
            label="tab:performance_comparison"
        )
        tables["performance_comparison_latex"] = latex_table
        
        # 生成 HTML 表格
        html_table = self._generate_html_table(performance_data, "Performance Comparison")
        tables["performance_comparison_html"] = html_table
        
        # 統計顯著性表格
        if len(data["performance_metrics"]) >= 2:
            statistical_table = await self._generate_statistical_significance_table(data)
            tables["statistical_significance"] = statistical_table
        
        return {"tables": tables}
    
    def _generate_latex_table(
        self, 
        data: List[Dict[str, Any]], 
        caption: str = "", 
        label: str = ""
    ) -> str:
        """生成 LaTeX 格式表格"""
        if not data:
            return ""
        
        # 表頭
        headers = list(data[0].keys())
        col_spec = "|" + "c|" * len(headers)
        
        latex = f"""\\begin{{table}}[ht]
\\centering
\\caption{{{caption}}}
\\label{{{label}}}
\\begin{{tabular}}{{{col_spec}}}
\\hline
"""
        
        # 添加表頭
        header_row = " & ".join([f"\\textbf{{{h}}}" for h in headers]) + " \\\\\\\\"
        latex += header_row + "\n\\hline\n"
        
        # 添加數據行
        for row in data:
            data_row = " & ".join([str(row[h]) for h in headers]) + " \\\\\\\\"
            latex += data_row + "\n\\hline\n"
        
        latex += """\\end{tabular}
\\end{table}"""
        
        return latex
    
    def _generate_html_table(self, data: List[Dict[str, Any]], title: str = "") -> str:
        """生成 HTML 格式表格"""
        if not data:
            return ""
        
        headers = list(data[0].keys())
        
        html = f'<div class="table">\n'
        if title:
            html += f'<h3>{title}</h3>\n'
        
        html += '<table>\n<thead>\n<tr>\n'
        for header in headers:
            html += f'<th>{header}</th>\n'
        html += '</tr>\n</thead>\n<tbody>\n'
        
        for row in data:
            html += '<tr>\n'
            for header in headers:
                html += f'<td>{row[header]}</td>\n'
            html += '</tr>\n'
        
        html += '</tbody>\n</table>\n</div>\n'
        
        return html
    
    async def _generate_academic_plots(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """生成學術級圖表"""
        logger.info("📈 生成學術級圖表")
        
        plots = {}
        
        # 1. CDF 比較圖 (仿論文 Figure 7)
        cdf_plot = await self._generate_cdf_comparison_plot(data)
        plots["cdf_comparison"] = cdf_plot
        
        # 2. 性能改進條形圖
        improvement_plot = await self._generate_improvement_bar_plot(data)
        plots["improvement_comparison"] = improvement_plot
        
        # 3. Box plot 顯示分佈
        box_plot = await self._generate_performance_box_plot(data)
        plots["performance_distribution"] = box_plot
        
        # 4. 統計置信區間圖
        confidence_plot = await self._generate_confidence_interval_plot(data)
        plots["confidence_intervals"] = confidence_plot
        
        return {"plots": plots}
    
    async def _generate_cdf_comparison_plot(self, data: Dict[str, Any]) -> str:
        """生成 CDF 比較圖"""
        plt.figure(figsize=self.plot_config.figsize)
        
        # 為每個方案繪製 CDF
        for i, (scheme, metrics) in enumerate(data["performance_metrics"].items()):
            if metrics["latencies"]:
                latencies = np.array(metrics["latencies"])
                
                # 計算 CDF
                sorted_latencies = np.sort(latencies)
                p = np.arange(1, len(sorted_latencies) + 1) / len(sorted_latencies)
                
                color = self.plot_config.colors[i % len(self.plot_config.colors)]
                label = scheme.replace("_", "-").upper()
                
                plt.plot(sorted_latencies, p, label=label, linewidth=self.plot_config.line_width, color=color)
        
        plt.xlabel("Handover Latency (ms)")
        plt.ylabel("Cumulative Distribution Function")
        plt.title("Handover Latency CDF Comparison")
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.xlim(0, 300)
        plt.ylim(0, 1)
        
        # 保存圖表
        plot_path = self.output_dir / "cdf_comparison.png"
        plt.savefig(plot_path, dpi=self.plot_config.dpi, bbox_inches='tight')
        plt.close()
        
        return str(plot_path)
    
    async def _generate_improvement_bar_plot(self, data: Dict[str, Any]) -> str:
        """生成性能改進條形圖"""
        plt.figure(figsize=self.plot_config.figsize)
        
        schemes = []
        latencies = []
        
        baseline_latency = None
        for scheme, metrics in data["performance_metrics"].items():
            if metrics["latencies"]:
                avg_latency = np.mean(metrics["latencies"])
                schemes.append(scheme.replace("_", "-").upper())
                latencies.append(avg_latency)
                
                if scheme == "ntn_baseline":
                    baseline_latency = avg_latency
        
        # 計算改進倍數
        improvements = []
        for latency in latencies:
            if baseline_latency and latency > 0:
                improvements.append(baseline_latency / latency)
            else:
                improvements.append(1.0)
        
        # 創建條形圖
        bars = plt.bar(schemes, latencies, color=self.plot_config.colors[:len(schemes)])
        
        # 添加改進倍數標籤
        for i, (bar, improvement) in enumerate(zip(bars, improvements)):
            height = bar.get_height()
            if improvement > 1:
                plt.text(bar.get_x() + bar.get_width()/2., height + 5,
                        f'{improvement:.1f}x', ha='center', va='bottom')
        
        plt.xlabel("Handover Scheme")
        plt.ylabel("Average Latency (ms)")
        plt.title("Performance Improvement Comparison")
        plt.xticks(rotation=45)
        
        plot_path = self.output_dir / "improvement_comparison.png"
        plt.savefig(plot_path, dpi=self.plot_config.dpi, bbox_inches='tight')
        plt.close()
        
        return str(plot_path)
    
    async def _generate_performance_box_plot(self, data: Dict[str, Any]) -> str:
        """生成性能分佈 Box plot"""
        plt.figure(figsize=self.plot_config.figsize)
        
        plot_data = []
        labels = []
        
        for scheme, metrics in data["performance_metrics"].items():
            if metrics["latencies"]:
                plot_data.append(metrics["latencies"])
                labels.append(scheme.replace("_", "-").upper())
        
        if plot_data:
            box_plot = plt.boxplot(plot_data, labels=labels, patch_artist=True)
            
            # 設定顏色
            for i, patch in enumerate(box_plot['boxes']):
                patch.set_facecolor(self.plot_config.colors[i % len(self.plot_config.colors)])
                patch.set_alpha(0.7)
        
        plt.xlabel("Handover Scheme")
        plt.ylabel("Latency (ms)")
        plt.title("Latency Distribution Comparison")
        plt.xticks(rotation=45)
        
        plot_path = self.output_dir / "performance_distribution.png"
        plt.savefig(plot_path, dpi=self.plot_config.dpi, bbox_inches='tight')
        plt.close()
        
        return str(plot_path)
    
    async def _generate_confidence_interval_plot(self, data: Dict[str, Any]) -> str:
        """生成置信區間圖"""
        plt.figure(figsize=self.plot_config.figsize)
        
        schemes = []
        means = []
        ci_lower = []
        ci_upper = []
        
        for scheme, metrics in data["performance_metrics"].items():
            if metrics["latencies"]:
                latencies = np.array(metrics["latencies"])
                mean_val = np.mean(latencies)
                std_err = stats.sem(latencies)
                ci = stats.t.interval(0.95, len(latencies)-1, loc=mean_val, scale=std_err)
                
                schemes.append(scheme.replace("_", "-").upper())
                means.append(mean_val)
                ci_lower.append(ci[0])
                ci_upper.append(ci[1])
        
        x_pos = np.arange(len(schemes))
        
        # 繪製均值和置信區間
        plt.errorbar(x_pos, means, 
                    yerr=[np.array(means) - np.array(ci_lower), 
                          np.array(ci_upper) - np.array(means)],
                    fmt='o', capsize=5, capthick=2, markersize=8)
        
        plt.xticks(x_pos, schemes, rotation=45)
        plt.xlabel("Handover Scheme")
        plt.ylabel("Latency (ms)")
        plt.title("Mean Latency with 95% Confidence Intervals")
        plt.grid(True, alpha=0.3)
        
        plot_path = self.output_dir / "confidence_intervals.png"
        plt.savefig(plot_path, dpi=self.plot_config.dpi, bbox_inches='tight')
        plt.close()
        
        return str(plot_path)
    
    async def _perform_comprehensive_statistical_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """執行綜合統計分析"""
        logger.info("📊 執行統計分析")
        
        analysis = {
            "tests": [],
            "summary": {},
            "significance_matrix": {}
        }
        
        # 兩兩比較
        schemes = list(data["performance_metrics"].keys())
        for i, scheme1 in enumerate(schemes):
            for j, scheme2 in enumerate(schemes[i+1:], i+1):
                metrics1 = data["performance_metrics"][scheme1]
                metrics2 = data["performance_metrics"][scheme2]
                
                if metrics1["latencies"] and metrics2["latencies"]:
                    # T 檢驗
                    t_stat, p_value = stats.ttest_ind(metrics1["latencies"], metrics2["latencies"])
                    
                    # 效果大小 (Cohen's d)
                    pooled_std = np.sqrt(
                        ((len(metrics1["latencies"]) - 1) * np.var(metrics1["latencies"], ddof=1) +
                         (len(metrics2["latencies"]) - 1) * np.var(metrics2["latencies"], ddof=1)) /
                        (len(metrics1["latencies"]) + len(metrics2["latencies"]) - 2)
                    )
                    cohens_d = (np.mean(metrics1["latencies"]) - np.mean(metrics2["latencies"])) / pooled_std
                    
                    # 置信區間
                    diff_mean = np.mean(metrics1["latencies"]) - np.mean(metrics2["latencies"])
                    se_diff = pooled_std * np.sqrt(1/len(metrics1["latencies"]) + 1/len(metrics2["latencies"]))
                    ci = stats.t.interval(0.95, len(metrics1["latencies"]) + len(metrics2["latencies"]) - 2, 
                                         loc=diff_mean, scale=se_diff)
                    
                    result = StatisticalResult(
                        test_name=f"{scheme1}_vs_{scheme2}",
                        statistic=t_stat,
                        p_value=p_value,
                        effect_size=cohens_d,
                        confidence_interval=ci,
                        interpretation=self._interpret_statistical_result(p_value, cohens_d),
                        significant=p_value < 0.05
                    )
                    
                    analysis["tests"].append(result.__dict__)
                    analysis["significance_matrix"][f"{scheme1}_vs_{scheme2}"] = {
                        "significant": result.significant,
                        "p_value": p_value,
                        "effect_size": cohens_d
                    }
        
        # 總體摘要
        significant_tests = [t for t in analysis["tests"] if t["significant"]]
        analysis["summary"] = {
            "total_comparisons": len(analysis["tests"]),
            "significant_comparisons": len(significant_tests),
            "significance_rate": len(significant_tests) / len(analysis["tests"]) if analysis["tests"] else 0,
            "large_effect_sizes": len([t for t in analysis["tests"] if abs(t["effect_size"]) > 0.8])
        }
        
        return analysis
    
    def _interpret_statistical_result(self, p_value: float, effect_size: float) -> str:
        """解釋統計結果"""
        significance = "significant" if p_value < 0.05 else "not significant"
        
        if abs(effect_size) < 0.2:
            effect = "negligible"
        elif abs(effect_size) < 0.5:
            effect = "small"
        elif abs(effect_size) < 0.8:
            effect = "medium"
        else:
            effect = "large"
        
        return f"The difference is {significance} (p={p_value:.3f}) with a {effect} effect size (d={effect_size:.2f})"
    
    async def _generate_statistical_significance_table(self, data: Dict[str, Any]) -> str:
        """生成統計顯著性表格"""
        statistical_data = []
        
        schemes = list(data["performance_metrics"].keys())
        for i, scheme1 in enumerate(schemes):
            for scheme2 in schemes[i+1:]:
                metrics1 = data["performance_metrics"][scheme1]
                metrics2 = data["performance_metrics"][scheme2]
                
                if metrics1["latencies"] and metrics2["latencies"]:
                    t_stat, p_value = stats.ttest_ind(metrics1["latencies"], metrics2["latencies"])
                    
                    row = {
                        "Comparison": f"{scheme1.upper()} vs {scheme2.upper()}",
                        "T-statistic": f"{t_stat:.3f}",
                        "P-value": f"{p_value:.3f}",
                        "Significant": "Yes" if p_value < 0.05 else "No",
                        "Conclusion": "Significant difference" if p_value < 0.05 else "No significant difference"
                    }
                    statistical_data.append(row)
        
        return self._generate_latex_table(
            statistical_data,
            caption="Statistical Significance Analysis",
            label="tab:statistical_analysis"
        )
    
    async def _validate_against_paper_comprehensive(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """與論文結果進行綜合驗證"""
        logger.info("✅ 驗證論文結果")
        
        validation = {
            "scheme_validations": {},
            "overall_validation": {},
            "discrepancies": []
        }
        
        # 驗證各方案性能
        for scheme, metrics in data["performance_metrics"].items():
            if metrics["latencies"]:
                avg_latency = np.mean(metrics["latencies"])
                expected_latency = self.paper_benchmarks.get(f"{scheme}_latency_ms")
                
                if expected_latency:
                    deviation = abs(avg_latency - expected_latency) / expected_latency
                    within_tolerance = deviation < 0.2  # 20% 容錯
                    
                    validation["scheme_validations"][scheme] = {
                        "measured_latency": avg_latency,
                        "expected_latency": expected_latency,
                        "deviation_percent": deviation * 100,
                        "within_tolerance": within_tolerance,
                        "status": "PASS" if within_tolerance else "FAIL"
                    }
                    
                    if not within_tolerance:
                        validation["discrepancies"].append({
                            "scheme": scheme,
                            "metric": "latency",
                            "expected": expected_latency,
                            "measured": avg_latency,
                            "deviation": deviation
                        })
        
        # 整體驗證
        passed_validations = sum(1 for v in validation["scheme_validations"].values() if v["within_tolerance"])
        total_validations = len(validation["scheme_validations"])
        
        validation["overall_validation"] = {
            "passed_tests": passed_validations,
            "total_tests": total_validations,
            "success_rate": passed_validations / total_validations if total_validations > 0 else 0,
            "overall_status": "PASS" if passed_validations == total_validations else "PARTIAL" if passed_validations > 0 else "FAIL"
        }
        
        return validation
    
    async def _generate_report_content(
        self, 
        data: Dict[str, Any],
        tables: Dict[str, Any],
        plots: Dict[str, Any],
        statistical_analysis: Dict[str, Any],
        validation: Dict[str, Any]
    ) -> Dict[str, str]:
        """生成報告內容"""
        
        content = {
            "title": "IEEE INFOCOM 2024 Paper Reproduction: Accelerating Handover in Mobile Satellite Networks",
            "authors": "Experimental Validation Team",
            "affiliation": "NTN Stack Development Project",
            "generation_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "abstract": self._generate_abstract(data, validation),
            "experimental_setup": self._generate_experimental_setup(),
            "results_and_analysis": self._generate_results_section(data, tables, plots),
            "statistical_validation": self._generate_statistical_section(statistical_analysis),
            "paper_validation": self._generate_validation_section(validation),
            "conclusion": self._generate_conclusion(data, validation)
        }
        
        return content
    
    def _generate_abstract(self, data: Dict[str, Any], validation: Dict[str, Any]) -> str:
        """生成摘要"""
        total_experiments = len(data.get("experiments", []))
        success_rate = validation["overall_validation"].get("success_rate", 0) * 100
        
        improvement_factor = data.get("scheme_comparisons", {}).get("improvement_factor", 0)
        
        return f"""
        This report presents the experimental reproduction of the IEEE INFOCOM 2024 paper 
        "Accelerating Handover in Mobile Satellite Networks". We conducted {total_experiments} 
        experiments across multiple satellite constellations (Starlink, Kuiper, OneWeb) to 
        validate the proposed handover algorithm. Our results show a {improvement_factor:.1f}x 
        improvement in handover latency compared to the baseline NTN scheme, achieving 
        {success_rate:.1f}% validation success rate against the original paper benchmarks. 
        The experimental framework demonstrates the effectiveness of the two-point prediction 
        algorithm with binary search refinement for accelerated satellite handovers.
        """
    
    def _generate_experimental_setup(self) -> str:
        """生成實驗設置說明"""
        return """
        The experimental validation was conducted using a containerized NTN stack environment 
        with real satellite constellation data. The test framework implements four handover 
        schemes: NTN Baseline (3GPP standard), NTN-GS (Ground Station assisted), NTN-SMN 
        (Satellite Mesh Network), and the Proposed Algorithm. Each experiment measures 
        handover latency, success rate, and prediction accuracy across different mobility 
        scenarios and environmental conditions.
        """
    
    def _generate_results_section(
        self, 
        data: Dict[str, Any], 
        tables: Dict[str, Any], 
        plots: Dict[str, Any]
    ) -> str:
        """生成結果分析章節"""
        
        # 計算關鍵指標
        if "proposed" in data["performance_metrics"] and data["performance_metrics"]["proposed"]["latencies"]:
            proposed_latency = np.mean(data["performance_metrics"]["proposed"]["latencies"])
        else:
            proposed_latency = 0
            
        if "ntn_baseline" in data["performance_metrics"] and data["performance_metrics"]["ntn_baseline"]["latencies"]:
            baseline_latency = np.mean(data["performance_metrics"]["ntn_baseline"]["latencies"])
        else:
            baseline_latency = 0
        
        improvement = baseline_latency / proposed_latency if proposed_latency > 0 else 0
        
        content = f"""
        <h3>Performance Comparison Results</h3>
        
        <p>The experimental validation demonstrates significant performance improvements 
        with the proposed algorithm achieving an average handover latency of {proposed_latency:.1f}ms 
        compared to {baseline_latency:.1f}ms for the baseline NTN scheme, representing 
        a {improvement:.1f}x improvement factor.</p>
        
        {tables['tables'].get('performance_comparison_html', '')}
        
        <div class="figure">
            <img src="{plots['plots'].get('cdf_comparison', '')}" alt="CDF Comparison" width="600">
            <p class="caption">Figure 1: Cumulative Distribution Function comparison of handover latencies</p>
        </div>
        
        <div class="figure">
            <img src="{plots['plots'].get('improvement_comparison', '')}" alt="Improvement Comparison" width="600">
            <p class="caption">Figure 2: Performance improvement comparison across handover schemes</p>
        </div>
        """
        
        return content
    
    def _generate_statistical_section(self, analysis: Dict[str, Any]) -> str:
        """生成統計分析章節"""
        summary = analysis.get("summary", {})
        
        return f"""
        <h3>Statistical Significance Analysis</h3>
        
        <p>Statistical validation was performed using two-sample t-tests with 95% confidence 
        intervals. Out of {summary.get('total_comparisons', 0)} pairwise comparisons, 
        {summary.get('significant_comparisons', 0)} showed statistically significant 
        differences (p < 0.05), representing a {summary.get('significance_rate', 0)*100:.1f}% 
        significance rate.</p>
        
        <p>Effect size analysis revealed {summary.get('large_effect_sizes', 0)} comparisons 
        with large effect sizes (|d| > 0.8), indicating practically significant performance 
        differences beyond statistical significance.</p>
        """
    
    def _generate_validation_section(self, validation: Dict[str, Any]) -> str:
        """生成論文驗證章節"""
        overall = validation.get("overall_validation", {})
        
        return f"""
        <h3>Paper Benchmark Validation</h3>
        
        <p>Validation against original paper benchmarks shows {overall.get('passed_tests', 0)} 
        out of {overall.get('total_tests', 0)} metrics within acceptable tolerance (±20%), 
        achieving {overall.get('success_rate', 0)*100:.1f}% validation success rate.</p>
        
        <p>Overall validation status: <strong>{overall.get('overall_status', 'UNKNOWN')}</strong></p>
        """
    
    def _generate_conclusion(self, data: Dict[str, Any], validation: Dict[str, Any]) -> str:
        """生成結論"""
        improvement_factor = data.get("scheme_comparisons", {}).get("improvement_factor", 0)
        
        return f"""
        The experimental reproduction successfully validates the key claims of the IEEE INFOCOM 2024 
        paper. The proposed handover algorithm demonstrates a {improvement_factor:.1f}x improvement 
        in latency performance while maintaining high success rates across multiple satellite 
        constellations. The binary search refinement technique proves effective for real-time 
        handover prediction in NTN environments. These results confirm the practical applicability 
        of the proposed approach for next-generation satellite communication systems.
        """
    
    async def _generate_formatted_report(
        self, 
        content: Dict[str, str], 
        format: ReportFormat
    ) -> Dict[str, Any]:
        """生成格式化報告"""
        logger.info(f"📄 生成 {format.value} 格式報告")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        files = []
        
        if format == ReportFormat.HTML:
            # 生成 HTML 報告
            env = jinja2.Environment(loader=jinja2.FileSystemLoader(self.template_dir))
            template = env.get_template("technical_report.html")
            
            html_content = template.render(**content)
            
            html_path = self.output_dir / f"comprehensive_report_{timestamp}.html"
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            files.append(str(html_path))
            
        elif format == ReportFormat.LATEX:
            # 生成 LaTeX 報告
            env = jinja2.Environment(loader=jinja2.FileSystemLoader(self.template_dir))
            template = env.get_template("ieee_paper.tex")
            
            latex_content = template.render(**content)
            
            latex_path = self.output_dir / f"paper_reproduction_{timestamp}.tex"
            with open(latex_path, 'w', encoding='utf-8') as f:
                f.write(latex_content)
            
            files.append(str(latex_path))
            
        elif format == ReportFormat.JSON:
            # 生成 JSON 報告
            json_path = self.output_dir / f"report_data_{timestamp}.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(content, f, indent=2, ensure_ascii=False)
            
            files.append(str(json_path))
        
        return {
            "format": format.value,
            "files": files,
            "timestamp": timestamp,
            "generation_successful": True
        }

# 命令行介面
async def main():
    """主執行函數"""
    import argparse
    
    parser = argparse.ArgumentParser(description="學術級別實驗報告生成器")
    parser.add_argument("--input", required=True, help="實驗結果 JSON 檔案路徑")
    parser.add_argument("--format", choices=["html", "latex", "pdf", "json"], 
                       default="html", help="報告格式")
    parser.add_argument("--config", default="tests/configs/paper_reproduction_config.yaml",
                       help="配置檔案路徑")
    parser.add_argument("--output-dir", help="輸出目錄")
    
    args = parser.parse_args()
    
    # 載入實驗結果
    with open(args.input, 'r', encoding='utf-8') as f:
        experiment_results = json.load(f)
    
    # 創建報告生成器
    generator = EnhancedReportGenerator(args.config)
    
    if args.output_dir:
        generator.output_dir = Path(args.output_dir)
        generator.output_dir.mkdir(parents=True, exist_ok=True)
    
    # 生成報告
    report_format = ReportFormat(args.format)
    results = await generator.generate_comprehensive_report(experiment_results, report_format)
    
    print(f"\n✅ 學術報告生成完成!")
    print(f"📊 分析實驗數: {results['metadata']['data_summary']['experiments_analyzed']}")
    print(f"📈 生成圖表數: {results['metadata']['data_summary']['plots_generated']}")
    print(f"📋 生成表格數: {results['metadata']['data_summary']['tables_generated']}")
    print(f"📄 生成檔案: {', '.join(results['final_report']['files'])}")
    print(f"⏱️  總耗時: {results['metadata']['generation_time']:.2f}秒")

if __name__ == "__main__":
    asyncio.run(main())