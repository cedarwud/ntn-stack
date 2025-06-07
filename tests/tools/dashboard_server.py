"""
互動式測試結果儀表板服務
Interactive Test Results Dashboard Server
"""

import json
import asyncio
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.utils import PlotlyJSONEncoder

# Web框架
from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_socketio import SocketIO, emit
import uvicorn
from fastapi import FastAPI, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from .visualization_config import ConfigManager, VisualizationConfig
from .test_data_collector import TestDataManager, TestSuite, PerformanceMetrics
from .visualization_engine import VisualizationEngine, ChartData
from .advanced_report_generator import AdvancedReportGenerator


class DashboardAPI:
    """儀表板API類"""
    
    def __init__(self, config: VisualizationConfig):
        self.config = config
        self.data_manager = TestDataManager()
        self.visualization_engine = VisualizationEngine(config)
        self.report_generator = AdvancedReportGenerator(config)
        self._cache = {}
        self._cache_timeout = 300  # 5分鐘緩存
    
    def get_dashboard_data(self, 
                          start_date: Optional[str] = None,
                          end_date: Optional[str] = None,
                          test_type: Optional[str] = None) -> Dict[str, Any]:
        """獲取儀表板數據"""
        
        # 解析日期
        if start_date:
            start_dt = datetime.fromisoformat(start_date)
        else:
            start_dt = datetime.now() - timedelta(days=7)
        
        if end_date:
            end_dt = datetime.fromisoformat(end_date)
        else:
            end_dt = datetime.now()
        
        # 檢查緩存
        cache_key = f"{start_dt}_{end_dt}_{test_type or 'all'}"
        if cache_key in self._cache:
            cached_data, cached_time = self._cache[cache_key]
            if (datetime.now() - cached_time).seconds < self._cache_timeout:
                return cached_data
        
        # 獲取測試數據
        test_data = self.data_manager.get_test_data(
            start_date=start_dt,
            end_date=end_dt,
            test_type=test_type
        )
        
        # 獲取性能數據
        performance_data = self.data_manager.get_performance_data(
            start_date=start_dt,
            end_date=end_dt
        )
        
        # 生成統計摘要
        summary = self._generate_dashboard_summary(test_data, performance_data)
        
        # 生成圖表數據
        charts = self._generate_dashboard_charts(test_data, performance_data)
        
        # 獲取最近的測試結果
        recent_tests = self._get_recent_test_results(test_data)
        
        dashboard_data = {
            'summary': summary,
            'charts': charts,
            'recent_tests': recent_tests,
            'last_updated': datetime.now().isoformat(),
            'filters': {
                'start_date': start_dt.isoformat(),
                'end_date': end_dt.isoformat(),
                'test_type': test_type
            }
        }
        
        # 更新緩存
        self._cache[cache_key] = (dashboard_data, datetime.now())
        
        return dashboard_data
    
    def _generate_dashboard_summary(self, test_data: pd.DataFrame, performance_data: pd.DataFrame) -> Dict[str, Any]:
        """生成儀表板摘要"""
        if test_data.empty:
            return {
                'total_tests': 0,
                'passed_tests': 0,
                'failed_tests': 0,
                'success_rate': 0,
                'avg_duration': 0,
                'total_suites': 0
            }
        
        total_tests = len(test_data)
        passed_tests = len(test_data[test_data['status'] == 'passed'])
        failed_tests = len(test_data[test_data['status'] == 'failed'])
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        avg_duration = test_data['duration'].mean() if 'duration' in test_data.columns else 0
        total_suites = test_data['suite_name'].nunique() if 'suite_name' in test_data.columns else 0
        
        # 性能摘要
        perf_summary = {}
        if not performance_data.empty:
            perf_summary = {
                'avg_response_time': performance_data['response_time'].mean(),
                'avg_throughput': performance_data['throughput'].mean(),
                'avg_error_rate': performance_data['error_rate'].mean()
            }
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'success_rate': round(success_rate, 2),
            'avg_duration': round(avg_duration, 2),
            'total_suites': total_suites,
            'performance': perf_summary
        }
    
    def _generate_dashboard_charts(self, test_data: pd.DataFrame, performance_data: pd.DataFrame) -> Dict[str, Any]:
        """生成儀表板圖表"""
        charts = {}
        
        if not test_data.empty:
            # 測試結果趨勢
            daily_results = self._get_daily_test_results(test_data)
            charts['test_trend'] = {
                'data': daily_results.to_dict('records'),
                'chart_type': 'line',
                'title': 'Daily Test Results Trend'
            }
            
            # 測試狀態分佈
            status_counts = test_data['status'].value_counts().to_dict()
            charts['status_distribution'] = {
                'data': [{'status': k, 'count': v} for k, v in status_counts.items()],
                'chart_type': 'pie',
                'title': 'Test Status Distribution'
            }
            
            # 測試套件比較
            suite_summary = test_data.groupby('suite_name').agg({
                'status': lambda x: (x == 'passed').sum() / len(x) * 100,
                'duration': 'mean'
            }).reset_index()
            suite_summary.columns = ['suite_name', 'success_rate', 'avg_duration']
            
            charts['suite_comparison'] = {
                'data': suite_summary.to_dict('records'),
                'chart_type': 'bar',
                'title': 'Test Suite Success Rate Comparison'
            }
        
        if not performance_data.empty:
            # 性能趨勢
            perf_trend = performance_data.groupby(performance_data['timestamp'].dt.date).agg({
                'response_time': 'mean',
                'throughput': 'mean',
                'error_rate': 'mean'
            }).reset_index()
            
            charts['performance_trend'] = {
                'data': perf_trend.to_dict('records'),
                'chart_type': 'line',
                'title': 'Performance Metrics Trend'
            }
        
        return charts
    
    def _get_daily_test_results(self, test_data: pd.DataFrame) -> pd.DataFrame:
        """獲取每日測試結果統計"""
        test_data['date'] = pd.to_datetime(test_data['timestamp']).dt.date
        
        daily_stats = test_data.groupby('date').agg({
            'status': [
                lambda x: (x == 'passed').sum(),
                lambda x: (x == 'failed').sum(),
                lambda x: len(x)
            ]
        }).reset_index()
        
        daily_stats.columns = ['date', 'passed', 'failed', 'total']
        daily_stats['success_rate'] = (daily_stats['passed'] / daily_stats['total']) * 100
        daily_stats['date'] = daily_stats['date'].astype(str)
        
        return daily_stats
    
    def _get_recent_test_results(self, test_data: pd.DataFrame, limit: int = 50) -> List[Dict[str, Any]]:
        """獲取最近的測試結果"""
        if test_data.empty:
            return []
        
        recent = test_data.sort_values('timestamp', ascending=False).head(limit)
        return recent.to_dict('records')
    
    def generate_real_time_chart(self, chart_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """生成實時圖表"""
        try:
            # 獲取最新數據
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=1)  # 最近1小時
            
            test_data = self.data_manager.get_test_data(
                start_date=start_time,
                end_date=end_time
            )
            
            if chart_type == 'real_time_status':
                # 實時測試狀態
                if not test_data.empty:
                    status_counts = test_data['status'].value_counts().to_dict()
                    return {
                        'success': True,
                        'data': [{'status': k, 'count': v} for k, v in status_counts.items()],
                        'timestamp': datetime.now().isoformat()
                    }
            
            elif chart_type == 'real_time_performance':
                # 實時性能數據
                performance_data = self.data_manager.get_performance_data(
                    start_date=start_time,
                    end_date=end_time
                )
                
                if not performance_data.empty:
                    latest = performance_data.iloc[-1]
                    return {
                        'success': True,
                        'data': {
                            'response_time': latest['response_time'],
                            'throughput': latest['throughput'],
                            'error_rate': latest['error_rate']
                        },
                        'timestamp': datetime.now().isoformat()
                    }
            
            return {'success': False, 'message': 'No data available'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}


# Flask應用
def create_flask_app(config: VisualizationConfig) -> Flask:
    """創建Flask應用"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'ntn-stack-dashboard-secret'
    
    # 創建SocketIO實例
    socketio = SocketIO(app, cors_allowed_origins="*")
    
    # 創建API實例
    dashboard_api = DashboardAPI(config)
    
    # 靜態文件和模板
    template_dir = str(Path(__file__).parent / "templates")
    static_dir = str(Path(__file__).parent / "static")
    
    Path(template_dir).mkdir(exist_ok=True)
    Path(static_dir).mkdir(exist_ok=True)
    
    # 創建默認模板
    _create_dashboard_template(template_dir)
    _create_dashboard_static_files(static_dir)
    
    @app.route('/')
    def dashboard():
        """主儀表板頁面"""
        return render_template('dashboard.html')
    
    @app.route('/api/dashboard')
    def api_dashboard_data():
        """獲取儀表板數據API"""
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        test_type = request.args.get('test_type')
        
        data = dashboard_api.get_dashboard_data(start_date, end_date, test_type)
        return jsonify(data)
    
    @app.route('/api/real-time/<chart_type>')
    def api_real_time_chart(chart_type):
        """實時圖表數據API"""
        params = request.args.to_dict()
        data = dashboard_api.generate_real_time_chart(chart_type, params)
        return jsonify(data)
    
    @app.route('/api/export/report')
    def api_export_report():
        """導出報告API"""
        format_type = request.args.get('format', 'html')
        
        # 獲取最近7天的數據
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        test_data = dashboard_api.data_manager.get_test_data(
            start_date=start_date,
            end_date=end_date
        )
        
        # 生成測試套件數據（簡化版本）
        test_suites = []  # 這裡需要從test_data構建TestSuite對象
        
        # 生成報告
        output_files = dashboard_api.report_generator.generate_and_export_report(
            test_suites=test_suites,
            formats=[format_type]
        )
        
        if format_type in output_files:
            file_path = output_files[format_type]
            directory = str(Path(file_path).parent)
            filename = Path(file_path).name
            return send_from_directory(directory, filename, as_attachment=True)
        else:
            return jsonify({'error': 'Report generation failed'}), 500
    
    # WebSocket事件
    @socketio.on('connect')
    def handle_connect():
        """客戶端連接"""
        print('Client connected')
        emit('connected', {'data': 'Connected to dashboard'})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """客戶端斷開連接"""
        print('Client disconnected')
    
    @socketio.on('request_real_time_data')
    def handle_real_time_request(data):
        """處理實時數據請求"""
        chart_type = data.get('chart_type', 'real_time_status')
        chart_data = dashboard_api.generate_real_time_chart(chart_type, data)
        emit('real_time_data', chart_data)
    
    # 啟動實時數據推送
    def background_task():
        """後台任務：定期推送實時數據"""
        while True:
            socketio.sleep(30)  # 每30秒推送一次
            
            # 推送實時測試狀態
            status_data = dashboard_api.generate_real_time_chart('real_time_status', {})
            socketio.emit('real_time_update', {
                'type': 'status',
                'data': status_data
            })
            
            # 推送實時性能數據
            perf_data = dashboard_api.generate_real_time_chart('real_time_performance', {})
            socketio.emit('real_time_update', {
                'type': 'performance',
                'data': perf_data
            })
    
    # 啟動後台任務
    socketio.start_background_task(background_task)
    
    app.socketio = socketio
    return app


def _create_dashboard_template(template_dir: str):
    """創建儀表板模板"""
    template_content = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NTN Stack Test Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <script src="https://cdn.socket.io/4.0.0/socket.io.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .dashboard-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .metric-card {
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }
        .metric-value {
            font-size: 2.5em;
            font-weight: bold;
            color: #333;
        }
        .metric-label {
            color: #666;
            margin-top: 5px;
        }
        .chart-container {
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        .status-passed { background-color: #28a745; }
        .status-failed { background-color: #dc3545; }
        .status-skipped { background-color: #6c757d; }
        .real-time-indicator {
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
    </style>
</head>
<body>
    <div class="container-fluid">
        <div class="row">
            <div class="col-12">
                <div class="dashboard-card">
                    <h1><i class="fas fa-chart-line"></i> NTN Stack Test Results Dashboard</h1>
                    <p class="mb-0">Real-time monitoring and analysis of test results</p>
                    <div class="real-time-indicator" style="float: right;">
                        <span class="badge bg-success">● LIVE</span>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- 控制面板 -->
        <div class="row mb-4">
            <div class="col-md-3">
                <label for="startDate">Start Date:</label>
                <input type="date" id="startDate" class="form-control">
            </div>
            <div class="col-md-3">
                <label for="endDate">End Date:</label>
                <input type="date" id="endDate" class="form-control">
            </div>
            <div class="col-md-3">
                <label for="testType">Test Type:</label>
                <select id="testType" class="form-control">
                    <option value="">All Types</option>
                    <option value="e2e">E2E Tests</option>
                    <option value="unit">Unit Tests</option>
                    <option value="integration">Integration Tests</option>
                    <option value="performance">Performance Tests</option>
                </select>
            </div>
            <div class="col-md-3">
                <label>&nbsp;</label>
                <button class="btn btn-primary form-control" onclick="updateDashboard()">Update</button>
            </div>
        </div>
        
        <!-- 關鍵指標 -->
        <div class="row" id="metricsRow">
            <!-- 動態生成指標卡片 -->
        </div>
        
        <!-- 圖表區域 -->
        <div class="row">
            <div class="col-md-6">
                <div class="chart-container">
                    <h4>Test Results Trend</h4>
                    <div id="trendChart" style="height: 400px;"></div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="chart-container">
                    <h4>Test Status Distribution</h4>
                    <div id="statusChart" style="height: 400px;"></div>
                </div>
            </div>
        </div>
        
        <div class="row">
            <div class="col-md-6">
                <div class="chart-container">
                    <h4>Test Suite Comparison</h4>
                    <div id="suiteChart" style="height: 400px;"></div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="chart-container">
                    <h4>Performance Metrics</h4>
                    <div id="performanceChart" style="height: 400px;"></div>
                </div>
            </div>
        </div>
        
        <!-- 最近測試結果 -->
        <div class="row">
            <div class="col-12">
                <div class="chart-container">
                    <h4>Recent Test Results</h4>
                    <div class="table-responsive">
                        <table class="table table-striped" id="recentTestsTable">
                            <thead>
                                <tr>
                                    <th>Test Name</th>
                                    <th>Status</th>
                                    <th>Duration</th>
                                    <th>Timestamp</th>
                                    <th>Suite</th>
                                </tr>
                            </thead>
                            <tbody>
                                <!-- 動態生成 -->
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // WebSocket連接
        const socket = io();
        
        socket.on('connect', function() {
            console.log('Connected to dashboard server');
        });
        
        socket.on('real_time_update', function(data) {
            console.log('Real-time update:', data);
            updateRealTimeData(data);
        });
        
        // 初始化儀表板
        document.addEventListener('DOMContentLoaded', function() {
            initializeDashboard();
            updateDashboard();
        });
        
        function initializeDashboard() {
            // 設置默認日期
            const endDate = new Date();
            const startDate = new Date();
            startDate.setDate(startDate.getDate() - 7);
            
            document.getElementById('endDate').value = endDate.toISOString().split('T')[0];
            document.getElementById('startDate').value = startDate.toISOString().split('T')[0];
        }
        
        function updateDashboard() {
            const startDate = document.getElementById('startDate').value;
            const endDate = document.getElementById('endDate').value;
            const testType = document.getElementById('testType').value;
            
            const params = new URLSearchParams();
            if (startDate) params.append('start_date', startDate);
            if (endDate) params.append('end_date', endDate);
            if (testType) params.append('test_type', testType);
            
            fetch(`/api/dashboard?${params}`)
                .then(response => response.json())
                .then(data => {
                    updateMetrics(data.summary);
                    updateCharts(data.charts);
                    updateRecentTests(data.recent_tests);
                })
                .catch(error => {
                    console.error('Error updating dashboard:', error);
                });
        }
        
        function updateMetrics(summary) {
            const metricsRow = document.getElementById('metricsRow');
            metricsRow.innerHTML = `
                <div class="col-md-2">
                    <div class="metric-card">
                        <div class="metric-value">${summary.total_tests}</div>
                        <div class="metric-label">Total Tests</div>
                    </div>
                </div>
                <div class="col-md-2">
                    <div class="metric-card">
                        <div class="metric-value">${summary.passed_tests}</div>
                        <div class="metric-label">Passed</div>
                    </div>
                </div>
                <div class="col-md-2">
                    <div class="metric-card">
                        <div class="metric-value">${summary.failed_tests}</div>
                        <div class="metric-label">Failed</div>
                    </div>
                </div>
                <div class="col-md-2">
                    <div class="metric-card">
                        <div class="metric-value">${summary.success_rate}%</div>
                        <div class="metric-label">Success Rate</div>
                    </div>
                </div>
                <div class="col-md-2">
                    <div class="metric-card">
                        <div class="metric-value">${summary.avg_duration}s</div>
                        <div class="metric-label">Avg Duration</div>
                    </div>
                </div>
                <div class="col-md-2">
                    <div class="metric-card">
                        <div class="metric-value">${summary.total_suites}</div>
                        <div class="metric-label">Test Suites</div>
                    </div>
                </div>
            `;
        }
        
        function updateCharts(charts) {
            // 更新趨勢圖
            if (charts.test_trend) {
                const trendData = charts.test_trend.data;
                const trace = {
                    x: trendData.map(d => d.date),
                    y: trendData.map(d => d.success_rate),
                    type: 'scatter',
                    mode: 'lines+markers',
                    name: 'Success Rate',
                    line: { color: '#007bff', width: 3 }
                };
                Plotly.newPlot('trendChart', [trace], {
                    title: 'Test Success Rate Trend',
                    xaxis: { title: 'Date' },
                    yaxis: { title: 'Success Rate (%)' }
                });
            }
            
            // 更新狀態分佈圖
            if (charts.status_distribution) {
                const statusData = charts.status_distribution.data;
                const trace = {
                    labels: statusData.map(d => d.status),
                    values: statusData.map(d => d.count),
                    type: 'pie',
                    hole: 0.4
                };
                Plotly.newPlot('statusChart', [trace], {
                    title: 'Test Status Distribution'
                });
            }
            
            // 更新測試套件比較
            if (charts.suite_comparison) {
                const suiteData = charts.suite_comparison.data;
                const trace = {
                    x: suiteData.map(d => d.suite_name),
                    y: suiteData.map(d => d.success_rate),
                    type: 'bar',
                    marker: { color: '#28a745' }
                };
                Plotly.newPlot('suiteChart', [trace], {
                    title: 'Test Suite Success Rate',
                    xaxis: { title: 'Test Suite' },
                    yaxis: { title: 'Success Rate (%)' }
                });
            }
        }
        
        function updateRecentTests(recentTests) {
            const tbody = document.querySelector('#recentTestsTable tbody');
            tbody.innerHTML = '';
            
            recentTests.slice(0, 20).forEach(test => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${test.test_name}</td>
                    <td><span class="status-indicator status-${test.status}"></span>${test.status}</td>
                    <td>${test.duration}s</td>
                    <td>${new Date(test.timestamp).toLocaleString()}</td>
                    <td>${test.suite_name || 'N/A'}</td>
                `;
                tbody.appendChild(row);
            });
        }
        
        function updateRealTimeData(data) {
            // 處理實時數據更新
            if (data.type === 'status' && data.data.success) {
                // 更新實時狀態數據
                console.log('Updating real-time status data');
            } else if (data.type === 'performance' && data.data.success) {
                // 更新實時性能數據
                console.log('Updating real-time performance data');
            }
        }
        
        // 導出報告
        function exportReport(format) {
            window.open(`/api/export/report?format=${format}`, '_blank');
        }
    </script>
</body>
</html>
    '''
    
    template_path = Path(template_dir) / "dashboard.html"
    with open(template_path, 'w', encoding='utf-8') as f:
        f.write(template_content)


def _create_dashboard_static_files(static_dir: str):
    """創建儀表板靜態文件"""
    # 創建CSS文件
    css_content = '''
/* 儀表板樣式 */
.dashboard-container {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.real-time-badge {
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0% { opacity: 1; }
    50% { opacity: 0.5; }
    100% { opacity: 1; }
}
    '''
    
    css_path = Path(static_dir) / "dashboard.css"
    with open(css_path, 'w', encoding='utf-8') as f:
        f.write(css_content)


class DashboardServer:
    """儀表板服務器主類"""
    
    def __init__(self, config_path: Optional[str] = None, port: int = 8050):
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.load_config()
        self.port = port
        self.app = None
    
    def create_app(self):
        """創建應用"""
        self.app = create_flask_app(self.config)
        return self.app
    
    def run(self, debug: bool = False, host: str = "0.0.0.0"):
        """運行儀表板服務器"""
        if not self.app:
            self.create_app()
        
        print(f"Starting NTN Stack Test Dashboard Server...")
        print(f"Dashboard URL: http://{host}:{self.port}")
        print(f"Debug mode: {debug}")
        
        self.app.socketio.run(
            self.app,
            host=host,
            port=self.port,
            debug=debug
        )


if __name__ == "__main__":
    # 運行儀表板服務器
    server = DashboardServer(port=8050)
    server.run(debug=True)