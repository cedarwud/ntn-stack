"""
測試覆蓋率可視化分析器
Test Coverage Visualization Analyzer
"""

import json
import xml.etree.ElementTree as ET
import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from .visualization_config import ChartConfig, ChartType
from .visualization_engine import ChartData, BaseChartGenerator


@dataclass
class FileCoverage:
    """文件覆蓋率信息"""
    file_path: str
    file_name: str
    total_lines: int
    covered_lines: int
    coverage_percentage: float
    uncovered_lines: List[int]
    functions: List[Dict[str, Any]]
    branches: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.branches is None:
            self.branches = {'total': 0, 'covered': 0, 'percentage': 0.0}


@dataclass
class ModuleCoverage:
    """模組覆蓋率信息"""
    module_name: str
    module_path: str
    files: List[FileCoverage]
    total_lines: int
    covered_lines: int
    coverage_percentage: float
    function_coverage: float
    branch_coverage: float


@dataclass
class CoverageReport:
    """覆蓋率報告"""
    project_name: str
    generated_at: datetime
    overall_coverage: float
    line_coverage: float
    function_coverage: float
    branch_coverage: float
    modules: List[ModuleCoverage]
    summary_stats: Dict[str, Any]
    coverage_trends: Optional[List[Dict[str, Any]]] = None


@dataclass
class CoverageAnalysis:
    """覆蓋率分析結果"""
    coverage_distribution: Dict[str, int]
    low_coverage_files: List[FileCoverage]
    high_coverage_files: List[FileCoverage]
    uncovered_hotspots: List[Dict[str, Any]]
    coverage_gaps: List[Dict[str, Any]]
    improvement_suggestions: List[str]


class CoverageParser:
    """覆蓋率解析器"""
    
    def parse_coverage_xml(self, xml_path: str) -> CoverageReport:
        """解析XML格式的覆蓋率報告（如coverage.xml）"""
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            
            # 提取整體覆蓋率信息
            overall_coverage = 0.0
            line_rate = root.get('line-rate', '0')
            branch_rate = root.get('branch-rate', '0')
            
            overall_coverage = float(line_rate) * 100
            branch_coverage = float(branch_rate) * 100
            
            modules = []
            
            # 解析packages/classes
            packages = root.findall('.//package')
            for package in packages:
                package_name = package.get('name', 'unknown')
                
                # 解析classes/files
                classes = package.findall('.//class')
                files = []
                
                for cls in classes:
                    file_coverage = self._parse_class_coverage(cls)
                    if file_coverage:
                        files.append(file_coverage)
                
                if files:
                    module = self._create_module_coverage(package_name, files)
                    modules.append(module)
            
            # 計算統計信息
            summary_stats = self._calculate_summary_stats(modules)
            
            return CoverageReport(
                project_name=Path(xml_path).stem,
                generated_at=datetime.now(),
                overall_coverage=overall_coverage,
                line_coverage=overall_coverage,
                function_coverage=summary_stats.get('avg_function_coverage', 0.0),
                branch_coverage=branch_coverage,
                modules=modules,
                summary_stats=summary_stats
            )
            
        except Exception as e:
            print(f"Error parsing coverage XML {xml_path}: {e}")
            return self._create_empty_report()
    
    def parse_coverage_json(self, json_path: str) -> CoverageReport:
        """解析JSON格式的覆蓋率報告"""
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 解析totals
            totals = data.get('totals', {})
            overall_coverage = totals.get('percent_covered', 0.0)
            
            # 解析files
            files_data = data.get('files', {})
            modules = {}
            
            for file_path, file_data in files_data.items():
                module_name = self._get_module_name(file_path)
                
                file_coverage = FileCoverage(
                    file_path=file_path,
                    file_name=Path(file_path).name,
                    total_lines=file_data.get('summary', {}).get('num_statements', 0),
                    covered_lines=file_data.get('summary', {}).get('covered_lines', 0),
                    coverage_percentage=file_data.get('summary', {}).get('percent_covered', 0.0),
                    uncovered_lines=file_data.get('missing_lines', []),
                    functions=[]
                )
                
                if module_name not in modules:
                    modules[module_name] = []
                modules[module_name].append(file_coverage)
            
            # 創建模組覆蓋率
            module_list = []
            for module_name, files in modules.items():
                module = self._create_module_coverage(module_name, files)
                module_list.append(module)
            
            summary_stats = self._calculate_summary_stats(module_list)
            
            return CoverageReport(
                project_name=Path(json_path).stem,
                generated_at=datetime.now(),
                overall_coverage=overall_coverage,
                line_coverage=overall_coverage,
                function_coverage=summary_stats.get('avg_function_coverage', 0.0),
                branch_coverage=0.0,  # JSON格式通常不包含分支覆蓋率
                modules=module_list,
                summary_stats=summary_stats
            )
            
        except Exception as e:
            print(f"Error parsing coverage JSON {json_path}: {e}")
            return self._create_empty_report()
    
    def parse_lcov_report(self, lcov_path: str) -> CoverageReport:
        """解析LCOV格式的覆蓋率報告"""
        try:
            with open(lcov_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 解析LCOV格式
            records = content.split('end_of_record')
            modules = {}
            
            for record in records:
                if not record.strip():
                    continue
                
                lines = record.strip().split('\n')
                file_info = {}
                
                for line in lines:
                    if line.startswith('SF:'):
                        file_info['file_path'] = line[3:]
                    elif line.startswith('LF:'):
                        file_info['total_lines'] = int(line[3:])
                    elif line.startswith('LH:'):
                        file_info['covered_lines'] = int(line[3:])
                    elif line.startswith('BRF:'):
                        file_info['total_branches'] = int(line[4:])
                    elif line.startswith('BRH:'):
                        file_info['covered_branches'] = int(line[4:])
                
                if 'file_path' in file_info:
                    file_path = file_info['file_path']
                    module_name = self._get_module_name(file_path)
                    
                    total_lines = file_info.get('total_lines', 0)
                    covered_lines = file_info.get('covered_lines', 0)
                    coverage_percentage = (covered_lines / total_lines * 100) if total_lines > 0 else 0
                    
                    file_coverage = FileCoverage(
                        file_path=file_path,
                        file_name=Path(file_path).name,
                        total_lines=total_lines,
                        covered_lines=covered_lines,
                        coverage_percentage=coverage_percentage,
                        uncovered_lines=[],
                        functions=[],
                        branches={
                            'total': file_info.get('total_branches', 0),
                            'covered': file_info.get('covered_branches', 0),
                            'percentage': (file_info.get('covered_branches', 0) / 
                                         file_info.get('total_branches', 1) * 100) if file_info.get('total_branches', 0) > 0 else 0
                        }
                    )
                    
                    if module_name not in modules:
                        modules[module_name] = []
                    modules[module_name].append(file_coverage)
            
            # 創建模組覆蓋率
            module_list = []
            for module_name, files in modules.items():
                module = self._create_module_coverage(module_name, files)
                module_list.append(module)
            
            # 計算整體覆蓋率
            total_lines = sum(m.total_lines for m in module_list)
            total_covered = sum(m.covered_lines for m in module_list)
            overall_coverage = (total_covered / total_lines * 100) if total_lines > 0 else 0
            
            summary_stats = self._calculate_summary_stats(module_list)
            
            return CoverageReport(
                project_name=Path(lcov_path).stem,
                generated_at=datetime.now(),
                overall_coverage=overall_coverage,
                line_coverage=overall_coverage,
                function_coverage=summary_stats.get('avg_function_coverage', 0.0),
                branch_coverage=summary_stats.get('avg_branch_coverage', 0.0),
                modules=module_list,
                summary_stats=summary_stats
            )
            
        except Exception as e:
            print(f"Error parsing LCOV report {lcov_path}: {e}")
            return self._create_empty_report()
    
    def _parse_class_coverage(self, cls_element) -> Optional[FileCoverage]:
        """解析class元素的覆蓋率信息"""
        filename = cls_element.get('filename')
        if not filename:
            return None
        
        # 解析lines
        lines = cls_element.findall('.//line')
        total_lines = len(lines)
        covered_lines = len([line for line in lines if line.get('hits', '0') != '0'])
        uncovered_lines = [int(line.get('number', 0)) for line in lines if line.get('hits', '0') == '0']
        
        coverage_percentage = (covered_lines / total_lines * 100) if total_lines > 0 else 0
        
        # 解析methods/functions
        methods = cls_element.findall('.//method')
        functions = []
        for method in methods:
            func_info = {
                'name': method.get('name', 'unknown'),
                'signature': method.get('signature', ''),
                'line_rate': float(method.get('line-rate', 0))
            }
            functions.append(func_info)
        
        return FileCoverage(
            file_path=filename,
            file_name=Path(filename).name,
            total_lines=total_lines,
            covered_lines=covered_lines,
            coverage_percentage=coverage_percentage,
            uncovered_lines=uncovered_lines,
            functions=functions
        )
    
    def _get_module_name(self, file_path: str) -> str:
        """從文件路徑提取模組名"""
        path_parts = Path(file_path).parts
        
        # 嘗試找到主要的模組目錄
        for i, part in enumerate(path_parts):
            if part in ['src', 'lib', 'app', 'tests']:
                if i + 1 < len(path_parts):
                    return path_parts[i + 1]
        
        # 如果找不到，使用第一級目錄
        if len(path_parts) > 1:
            return path_parts[0]
        
        return 'unknown'
    
    def _create_module_coverage(self, module_name: str, files: List[FileCoverage]) -> ModuleCoverage:
        """創建模組覆蓋率信息"""
        total_lines = sum(f.total_lines for f in files)
        covered_lines = sum(f.covered_lines for f in files)
        coverage_percentage = (covered_lines / total_lines * 100) if total_lines > 0 else 0
        
        # 計算函數覆蓋率
        total_functions = sum(len(f.functions) for f in files)
        covered_functions = sum(
            sum(1 for func in f.functions if func.get('line_rate', 0) > 0)
            for f in files
        )
        function_coverage = (covered_functions / total_functions * 100) if total_functions > 0 else 0
        
        # 計算分支覆蓋率
        total_branches = sum(f.branches.get('total', 0) for f in files if f.branches)
        covered_branches = sum(f.branches.get('covered', 0) for f in files if f.branches)
        branch_coverage = (covered_branches / total_branches * 100) if total_branches > 0 else 0
        
        return ModuleCoverage(
            module_name=module_name,
            module_path='',
            files=files,
            total_lines=total_lines,
            covered_lines=covered_lines,
            coverage_percentage=coverage_percentage,
            function_coverage=function_coverage,
            branch_coverage=branch_coverage
        )
    
    def _calculate_summary_stats(self, modules: List[ModuleCoverage]) -> Dict[str, Any]:
        """計算摘要統計信息"""
        if not modules:
            return {}
        
        coverages = [m.coverage_percentage for m in modules]
        function_coverages = [m.function_coverage for m in modules if m.function_coverage > 0]
        branch_coverages = [m.branch_coverage for m in modules if m.branch_coverage > 0]
        
        return {
            'total_modules': len(modules),
            'total_files': sum(len(m.files) for m in modules),
            'avg_coverage': np.mean(coverages),
            'median_coverage': np.median(coverages),
            'min_coverage': np.min(coverages),
            'max_coverage': np.max(coverages),
            'std_coverage': np.std(coverages),
            'avg_function_coverage': np.mean(function_coverages) if function_coverages else 0,
            'avg_branch_coverage': np.mean(branch_coverages) if branch_coverages else 0,
            'low_coverage_modules': len([m for m in modules if m.coverage_percentage < 60]),
            'high_coverage_modules': len([m for m in modules if m.coverage_percentage >= 80])
        }
    
    def _create_empty_report(self) -> CoverageReport:
        """創建空的覆蓋率報告"""
        return CoverageReport(
            project_name="Unknown",
            generated_at=datetime.now(),
            overall_coverage=0.0,
            line_coverage=0.0,
            function_coverage=0.0,
            branch_coverage=0.0,
            modules=[],
            summary_stats={}
        )


class CoverageAnalyzer:
    """覆蓋率分析器"""
    
    def __init__(self):
        self.parser = CoverageParser()
    
    def analyze_coverage_report(self, coverage_report: CoverageReport) -> CoverageAnalysis:
        """分析覆蓋率報告"""
        
        # 覆蓋率分佈
        coverage_distribution = self._analyze_coverage_distribution(coverage_report)
        
        # 低覆蓋率和高覆蓋率文件
        all_files = []
        for module in coverage_report.modules:
            all_files.extend(module.files)
        
        low_coverage_files = [f for f in all_files if f.coverage_percentage < 60]
        high_coverage_files = [f for f in all_files if f.coverage_percentage >= 90]
        
        # 排序
        low_coverage_files.sort(key=lambda x: x.coverage_percentage)
        high_coverage_files.sort(key=lambda x: x.coverage_percentage, reverse=True)
        
        # 未覆蓋熱點
        uncovered_hotspots = self._find_uncovered_hotspots(all_files)
        
        # 覆蓋率差距
        coverage_gaps = self._identify_coverage_gaps(coverage_report)
        
        # 改進建議
        improvement_suggestions = self._generate_improvement_suggestions(coverage_report, all_files)
        
        return CoverageAnalysis(
            coverage_distribution=coverage_distribution,
            low_coverage_files=low_coverage_files[:20],  # 限制數量
            high_coverage_files=high_coverage_files[:20],
            uncovered_hotspots=uncovered_hotspots,
            coverage_gaps=coverage_gaps,
            improvement_suggestions=improvement_suggestions
        )
    
    def _analyze_coverage_distribution(self, coverage_report: CoverageReport) -> Dict[str, int]:
        """分析覆蓋率分佈"""
        distribution = {
            '0-20%': 0,
            '20-40%': 0,
            '40-60%': 0,
            '60-80%': 0,
            '80-100%': 0
        }
        
        for module in coverage_report.modules:
            for file in module.files:
                coverage = file.coverage_percentage
                if coverage < 20:
                    distribution['0-20%'] += 1
                elif coverage < 40:
                    distribution['20-40%'] += 1
                elif coverage < 60:
                    distribution['40-60%'] += 1
                elif coverage < 80:
                    distribution['60-80%'] += 1
                else:
                    distribution['80-100%'] += 1
        
        return distribution
    
    def _find_uncovered_hotspots(self, files: List[FileCoverage]) -> List[Dict[str, Any]]:
        """找出未覆蓋的熱點"""
        hotspots = []
        
        for file in files:
            if file.uncovered_lines and len(file.uncovered_lines) > 10:
                # 分析未覆蓋行的聚集
                uncovered_lines = sorted(file.uncovered_lines)
                clusters = []
                current_cluster = [uncovered_lines[0]]
                
                for i in range(1, len(uncovered_lines)):
                    if uncovered_lines[i] - uncovered_lines[i-1] <= 3:  # 行距小於等於3
                        current_cluster.append(uncovered_lines[i])
                    else:
                        if len(current_cluster) >= 5:  # 聚集大小至少5行
                            clusters.append(current_cluster)
                        current_cluster = [uncovered_lines[i]]
                
                if len(current_cluster) >= 5:
                    clusters.append(current_cluster)
                
                for cluster in clusters:
                    hotspot = {
                        'file_path': file.file_path,
                        'file_name': file.file_name,
                        'start_line': min(cluster),
                        'end_line': max(cluster),
                        'uncovered_lines_count': len(cluster),
                        'suggestion': f"Add tests for lines {min(cluster)}-{max(cluster)} in {file.file_name}"
                    }
                    hotspots.append(hotspot)
        
        # 按未覆蓋行數排序
        hotspots.sort(key=lambda x: x['uncovered_lines_count'], reverse=True)
        return hotspots[:10]  # 返回前10個熱點
    
    def _identify_coverage_gaps(self, coverage_report: CoverageReport) -> List[Dict[str, Any]]:
        """識別覆蓋率差距"""
        gaps = []
        
        # 模組間差距
        module_coverages = [(m.module_name, m.coverage_percentage) for m in coverage_report.modules]
        module_coverages.sort(key=lambda x: x[1])
        
        if len(module_coverages) > 1:
            lowest = module_coverages[0]
            highest = module_coverages[-1]
            
            if highest[1] - lowest[1] > 30:  # 差距超過30%
                gaps.append({
                    'type': 'module_gap',
                    'description': f"Large coverage gap between modules: {lowest[0]} ({lowest[1]:.1f}%) vs {highest[0]} ({highest[1]:.1f}%)",
                    'priority': 'high',
                    'recommendation': f"Focus testing efforts on {lowest[0]} module"
                })
        
        # 文件類型差距
        file_types = {}
        for module in coverage_report.modules:
            for file in module.files:
                ext = Path(file.file_path).suffix
                if ext not in file_types:
                    file_types[ext] = []
                file_types[ext].append(file.coverage_percentage)
        
        for ext, coverages in file_types.items():
            avg_coverage = np.mean(coverages)
            if avg_coverage < 50 and len(coverages) > 3:
                gaps.append({
                    'type': 'file_type_gap',
                    'description': f"Low coverage for {ext} files: {avg_coverage:.1f}% average",
                    'priority': 'medium',
                    'recommendation': f"Improve test coverage for {ext} files"
                })
        
        return gaps
    
    def _generate_improvement_suggestions(self, 
                                        coverage_report: CoverageReport,
                                        files: List[FileCoverage]) -> List[str]:
        """生成改進建議"""
        suggestions = []
        
        # 基於整體覆蓋率
        overall = coverage_report.overall_coverage
        if overall < 50:
            suggestions.append("🚨 Critical: Overall coverage is very low (<50%). Consider implementing a comprehensive testing strategy.")
        elif overall < 70:
            suggestions.append("⚠️  Warning: Overall coverage is below 70%. Focus on adding tests for core functionality.")
        elif overall < 85:
            suggestions.append("📈 Good: Coverage is decent. Target critical paths and edge cases to reach 85%+.")
        
        # 基於分支覆蓋率
        if coverage_report.branch_coverage < coverage_report.line_coverage - 20:
            suggestions.append("🔀 Branch coverage is significantly lower than line coverage. Add tests for conditional logic.")
        
        # 基於函數覆蓋率
        if coverage_report.function_coverage < 80:
            suggestions.append("🔧 Function coverage is low. Ensure all public methods have test cases.")
        
        # 基於模組差異
        if coverage_report.summary_stats.get('std_coverage', 0) > 25:
            suggestions.append("📊 High variance in module coverage. Balance testing efforts across modules.")
        
        # 基於未覆蓋文件數量
        uncovered_files = len([f for f in files if f.coverage_percentage == 0])
        if uncovered_files > 0:
            suggestions.append(f"📁 {uncovered_files} files have no test coverage. Start with the most critical ones.")
        
        # 基於低覆蓋率文件
        low_coverage_count = len([f for f in files if f.coverage_percentage < 60])
        total_files = len(files)
        if low_coverage_count / total_files > 0.3:
            suggestions.append("📝 More than 30% of files have low coverage. Implement systematic testing approach.")
        
        return suggestions


class CoverageVisualizer:
    """覆蓋率可視化器"""
    
    def generate_coverage_overview_chart(self, coverage_report: CoverageReport) -> ChartData:
        """生成覆蓋率概覽圖表"""
        
        # 準備數據
        metrics = ['Line Coverage', 'Function Coverage', 'Branch Coverage']
        values = [
            coverage_report.line_coverage,
            coverage_report.function_coverage,
            coverage_report.branch_coverage
        ]
        
        # 創建條形圖
        fig = go.Figure(data=[
            go.Bar(
                x=metrics,
                y=values,
                text=[f"{v:.1f}%" for v in values],
                textposition='auto',
                marker_color=['#2E86AB', '#A23B72', '#F18F01']
            )
        ])
        
        fig.update_layout(
            title=f"Coverage Overview - {coverage_report.project_name}",
            yaxis_title="Coverage Percentage",
            yaxis=dict(range=[0, 100]),
            template="plotly_white"
        )
        
        config = ChartConfig(
            chart_type=ChartType.BAR,
            title="Coverage Overview",
            x_axis="metrics",
            y_axis="coverage"
        )
        
        return ChartData(
            title="Coverage Overview",
            data={'metrics': metrics, 'values': values},
            config=config,
            figure=fig,
            html=fig.to_html(include_plotlyjs=True)
        )
    
    def generate_module_coverage_chart(self, coverage_report: CoverageReport) -> ChartData:
        """生成模組覆蓋率圖表"""
        
        modules = coverage_report.modules[:15]  # 限制顯示數量
        module_names = [m.module_name for m in modules]
        coverages = [m.coverage_percentage for m in modules]
        
        # 根據覆蓋率著色
        colors = []
        for coverage in coverages:
            if coverage >= 80:
                colors.append('#28a745')  # 綠色
            elif coverage >= 60:
                colors.append('#ffc107')  # 黃色
            else:
                colors.append('#dc3545')  # 紅色
        
        fig = go.Figure(data=[
            go.Bar(
                x=module_names,
                y=coverages,
                text=[f"{c:.1f}%" for c in coverages],
                textposition='auto',
                marker_color=colors
            )
        ])
        
        fig.update_layout(
            title="Module Coverage Distribution",
            xaxis_title="Modules",
            yaxis_title="Coverage Percentage",
            yaxis=dict(range=[0, 100]),
            template="plotly_white"
        )
        
        # 旋轉x軸標籤
        fig.update_xaxes(tickangle=45)
        
        config = ChartConfig(
            chart_type=ChartType.BAR,
            title="Module Coverage",
            x_axis="modules",
            y_axis="coverage"
        )
        
        return ChartData(
            title="Module Coverage Distribution",
            data={'modules': module_names, 'coverages': coverages},
            config=config,
            figure=fig,
            html=fig.to_html(include_plotlyjs=True)
        )
    
    def generate_coverage_distribution_chart(self, analysis: CoverageAnalysis) -> ChartData:
        """生成覆蓋率分佈圖表"""
        
        distribution = analysis.coverage_distribution
        ranges = list(distribution.keys())
        counts = list(distribution.values())
        
        fig = go.Figure(data=[
            go.Pie(
                labels=ranges,
                values=counts,
                hole=0.3,
                textinfo='label+percent',
                textposition='outside'
            )
        ])
        
        fig.update_layout(
            title="Coverage Distribution",
            template="plotly_white"
        )
        
        config = ChartConfig(
            chart_type=ChartType.PIE,
            title="Coverage Distribution",
            x_axis="ranges",
            y_axis="counts"
        )
        
        return ChartData(
            title="Coverage Distribution",
            data={'ranges': ranges, 'counts': counts},
            config=config,
            figure=fig,
            html=fig.to_html(include_plotlyjs=True)
        )
    
    def generate_coverage_heatmap(self, coverage_report: CoverageReport) -> ChartData:
        """生成覆蓋率熱圖"""
        
        # 準備熱圖數據
        heatmap_data = []
        modules = coverage_report.modules[:10]  # 限制模組數量
        
        for module in modules:
            files = module.files[:20]  # 限制文件數量
            for file in files:
                heatmap_data.append({
                    'module': module.module_name,
                    'file': file.file_name,
                    'coverage': file.coverage_percentage
                })
        
        if not heatmap_data:
            # 返回空圖表
            fig = go.Figure()
            fig.add_annotation(text="No data available", x=0.5, y=0.5, showarrow=False)
        else:
            df = pd.DataFrame(heatmap_data)
            pivot_df = df.pivot(index='file', columns='module', values='coverage').fillna(0)
            
            fig = go.Figure(data=go.Heatmap(
                z=pivot_df.values,
                x=pivot_df.columns,
                y=pivot_df.index,
                colorscale='RdYlGn',
                zmin=0,
                zmax=100,
                text=pivot_df.values,
                texttemplate="%{text:.1f}%",
                textfont={"size": 10},
                hoverongaps=False
            ))
        
        fig.update_layout(
            title="File Coverage Heatmap",
            xaxis_title="Modules",
            yaxis_title="Files",
            template="plotly_white"
        )
        
        config = ChartConfig(
            chart_type=ChartType.HEATMAP,
            title="Coverage Heatmap",
            x_axis="modules",
            y_axis="files"
        )
        
        return ChartData(
            title="File Coverage Heatmap",
            data={'heatmap_data': heatmap_data},
            config=config,
            figure=fig,
            html=fig.to_html(include_plotlyjs=True)
        )
    
    def generate_trend_chart(self, coverage_trends: List[Dict[str, Any]]) -> ChartData:
        """生成覆蓋率趨勢圖表"""
        
        if not coverage_trends:
            fig = go.Figure()
            fig.add_annotation(text="No trend data available", x=0.5, y=0.5, showarrow=False)
        else:
            dates = [item['date'] for item in coverage_trends]
            coverages = [item['coverage'] for item in coverage_trends]
            
            fig = go.Figure(data=go.Scatter(
                x=dates,
                y=coverages,
                mode='lines+markers',
                name='Coverage',
                line=dict(color='#007bff', width=3),
                marker=dict(size=6)
            ))
        
        fig.update_layout(
            title="Coverage Trend Over Time",
            xaxis_title="Date",
            yaxis_title="Coverage Percentage",
            yaxis=dict(range=[0, 100]),
            template="plotly_white"
        )
        
        config = ChartConfig(
            chart_type=ChartType.LINE,
            title="Coverage Trend",
            x_axis="date",
            y_axis="coverage"
        )
        
        return ChartData(
            title="Coverage Trend Over Time",
            data={'trends': coverage_trends},
            config=config,
            figure=fig,
            html=fig.to_html(include_plotlyjs=True)
        )


class CoverageReportGenerator:
    """覆蓋率報告生成器"""
    
    def __init__(self):
        self.parser = CoverageParser()
        self.analyzer = CoverageAnalyzer()
        self.visualizer = CoverageVisualizer()
    
    def process_coverage_files(self, coverage_paths: List[str]) -> List[CoverageReport]:
        """處理多個覆蓋率文件"""
        reports = []
        
        for path in coverage_paths:
            path_obj = Path(path)
            if not path_obj.exists():
                continue
            
            if path_obj.suffix.lower() == '.xml':
                report = self.parser.parse_coverage_xml(path)
            elif path_obj.suffix.lower() == '.json':
                report = self.parser.parse_coverage_json(path)
            elif path_obj.name.lower().startswith('lcov'):
                report = self.parser.parse_lcov_report(path)
            else:
                continue
            
            reports.append(report)
        
        return reports
    
    def generate_comprehensive_analysis(self, coverage_reports: List[CoverageReport]) -> Dict[str, Any]:
        """生成綜合覆蓋率分析"""
        if not coverage_reports:
            return {}
        
        # 合併多個報告（如果有的話）
        main_report = coverage_reports[0]  # 使用第一個作為主報告
        
        # 分析覆蓋率
        analysis = self.analyzer.analyze_coverage_report(main_report)
        
        # 生成圖表
        charts = {
            'overview': self.visualizer.generate_coverage_overview_chart(main_report),
            'module_coverage': self.visualizer.generate_module_coverage_chart(main_report),
            'distribution': self.visualizer.generate_coverage_distribution_chart(analysis),
            'heatmap': self.visualizer.generate_coverage_heatmap(main_report)
        }
        
        # 如果有趨勢數據，生成趨勢圖
        if main_report.coverage_trends:
            charts['trend'] = self.visualizer.generate_trend_chart(main_report.coverage_trends)
        
        return {
            'report': main_report,
            'analysis': analysis,
            'charts': charts,
            'summary': {
                'total_files': main_report.summary_stats.get('total_files', 0),
                'overall_coverage': main_report.overall_coverage,
                'critical_files': len(analysis.low_coverage_files),
                'improvement_suggestions': len(analysis.improvement_suggestions)
            }
        }


if __name__ == "__main__":
    # 示例使用
    generator = CoverageReportGenerator()
    
    # 處理覆蓋率文件
    coverage_paths = [
        "/home/sat/ntn-stack/tests/reports/coverage.xml",
        "/home/sat/ntn-stack/tests/reports/coverage.json"
    ]
    
    # 查找實際存在的覆蓋率文件
    existing_paths = []
    for search_dir in ["/home/sat/ntn-stack/tests/reports", "/home/sat/ntn-stack"]:
        search_path = Path(search_dir)
        if search_path.exists():
            for pattern in ["**/coverage.xml", "**/coverage.json", "**/lcov.info"]:
                existing_paths.extend(str(p) for p in search_path.glob(pattern))
    
    if existing_paths:
        print(f"Found coverage files: {existing_paths}")
        reports = generator.process_coverage_files(existing_paths)
        
        if reports:
            analysis = generator.generate_comprehensive_analysis(reports)
            print(f"Coverage analysis completed for {len(reports)} reports")
            print(f"Overall coverage: {analysis['summary']['overall_coverage']:.1f}%")
        else:
            print("No valid coverage reports found")
    else:
        print("No coverage files found. Creating sample analysis...")
        
        # 創建示例覆蓋率報告
        sample_files = [
            FileCoverage(
                file_path="src/main.py",
                file_name="main.py",
                total_lines=100,
                covered_lines=85,
                coverage_percentage=85.0,
                uncovered_lines=[10, 15, 20],
                functions=[]
            )
        ]
        
        sample_module = ModuleCoverage(
            module_name="main",
            module_path="src",
            files=sample_files,
            total_lines=100,
            covered_lines=85,
            coverage_percentage=85.0,
            function_coverage=90.0,
            branch_coverage=75.0
        )
        
        sample_report = CoverageReport(
            project_name="NTN Stack",
            generated_at=datetime.now(),
            overall_coverage=85.0,
            line_coverage=85.0,
            function_coverage=90.0,
            branch_coverage=75.0,
            modules=[sample_module],
            summary_stats={'total_files': 1}
        )
        
        analysis = generator.generate_comprehensive_analysis([sample_report])
        print(f"Sample analysis completed with {analysis['summary']['overall_coverage']:.1f}% coverage")