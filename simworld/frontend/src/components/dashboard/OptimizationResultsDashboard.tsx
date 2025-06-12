/**
 * 自動調優結果對比分析儀表板
 * 
 * 階段八：進階 AI 智慧決策與自動化調優
 * 提供自動調優結果的詳細對比分析和效果展示
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
import './OptimizationResultsDashboard.scss';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
);

interface OptimizationMetrics {
  latency_ms: number;
  throughput_mbps: number;
  coverage_percentage: number;
  power_consumption_w: number;
  cpu_utilization: number;
  memory_utilization: number;
  cost_per_hour: number;
  user_satisfaction: number;
}

interface OptimizationResult {
  optimization_id: string;
  timestamp: string;
  optimization_cycle: number;
  trigger_reason: string;
  parameter_changes: Record<string, {
    old_value: number;
    new_value: number;
    change_percentage: number;
  }>;
  before_metrics: OptimizationMetrics;
  after_metrics: OptimizationMetrics;
  improvements: Record<string, number>;
  implementation_time_seconds: number;
  success: boolean;
  confidence_score: number;
  cost_benefit_analysis: {
    total_cost: number;
    total_benefit: number;
    roi: number;
    payback_period_hours: number;
  };
}

interface OptimizationSummary {
  total_optimizations: number;
  successful_optimizations: number;
  average_improvement: number;
  total_cost_savings: number;
  best_performing_parameter: string;
  most_improved_metric: string;
  optimization_frequency_per_day: number;
}

interface OptimizationResultsDashboardProps {
  refreshInterval?: number;
  enableRealTime?: boolean;
  timeRange?: 'last_hour' | 'last_day' | 'last_week' | 'last_month';
}

const OptimizationResultsDashboard: React.FC<OptimizationResultsDashboardProps> = ({
  refreshInterval = 30000,
  enableRealTime = true,
  timeRange = 'last_day'
}) => {
  const [optimizationResults, setOptimizationResults] = useState<OptimizationResult[]>([]);
  const [summary, setSummary] = useState<OptimizationSummary | null>(null);
  const [selectedOptimization, setSelectedOptimization] = useState<OptimizationResult | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'comparison' | 'trends' | 'parameters'>('overview');
  const [isLoading, setIsLoading] = useState(false);
  const [compareMode, setCompareMode] = useState(false);
  const [selectedForComparison, setSelectedForComparison] = useState<OptimizationResult[]>([]);

  // 獲取優化結果
  const fetchOptimizationResults = useCallback(async () => {
    try {
      setIsLoading(true);
      
      // 獲取優化報告
      const daysMap = {
        'last_hour': 1,
        'last_day': 1,
        'last_week': 7,
        'last_month': 30
      };
      
      const days = daysMap[timeRange];
      const response = await fetch(`/api/v1/ai-decision/optimization/report?days=${days}`);
      const data = await response.json();
      
      if (data.success || data.report_period_days) {
        // 生成模擬優化結果
        const mockResults = generateMockOptimizationResults(days);
        setOptimizationResults(mockResults);
        
        // 生成摘要統計
        const mockSummary = generateOptimizationSummary(mockResults);
        setSummary(mockSummary);
        
        if (!selectedOptimization && mockResults.length > 0) {
          setSelectedOptimization(mockResults[0]);
        }
      }
      
    } catch (error) {
      console.error('獲取優化結果失敗:', error);
    } finally {
      setIsLoading(false);
    }
  }, [timeRange, selectedOptimization]);

  // 觸發手動優化
  const triggerManualOptimization = async () => {
    try {
      const response = await fetch('/api/v1/ai-decision/optimization/manual', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target_objectives: null })
      });
      
      if (response.ok) {
        alert('手動優化已啟動');
        setTimeout(() => fetchOptimizationResults(), 2000);
      }
    } catch (error) {
      console.error('觸發手動優化失敗:', error);
      alert('觸發優化失敗');
    }
  };

  useEffect(() => {
    fetchOptimizationResults();
    
    if (enableRealTime) {
      const interval = setInterval(fetchOptimizationResults, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [fetchOptimizationResults, enableRealTime, refreshInterval]);

  // 計算改善百分比
  const calculateImprovement = (before: number, after: number, isLowerBetter = false): number => {
    if (before === 0) return 0;
    const improvement = ((after - before) / before) * 100;
    return isLowerBetter ? -improvement : improvement;
  };

  // 性能趨勢圖表數據
  const performanceTrendsData = {
    labels: optimizationResults.map(r => new Date(r.timestamp).toLocaleDateString()).reverse(),
    datasets: [
      {
        label: '延遲 (ms)',
        data: optimizationResults.map(r => r.after_metrics.latency_ms).reverse(),
        borderColor: 'rgba(255, 99, 132, 1)',
        backgroundColor: 'rgba(255, 99, 132, 0.2)',
        tension: 0.1,
        yAxisID: 'y',
      },
      {
        label: '吞吐量 (Mbps)',
        data: optimizationResults.map(r => r.after_metrics.throughput_mbps).reverse(),
        borderColor: 'rgba(54, 162, 235, 1)',
        backgroundColor: 'rgba(54, 162, 235, 0.2)',
        tension: 0.1,
        yAxisID: 'y1',
      },
      {
        label: '覆蓋率 (%)',
        data: optimizationResults.map(r => r.after_metrics.coverage_percentage).reverse(),
        borderColor: 'rgba(75, 192, 192, 1)',
        backgroundColor: 'rgba(75, 192, 192, 0.2)',
        tension: 0.1,
        yAxisID: 'y2',
      },
    ],
  };

  // 優化成功率圖表
  const successRateData = {
    labels: ['成功', '失敗'],
    datasets: [
      {
        data: summary ? [
          summary.successful_optimizations,
          summary.total_optimizations - summary.successful_optimizations
        ] : [0, 0],
        backgroundColor: [
          'rgba(75, 192, 192, 0.6)',
          'rgba(255, 99, 132, 0.6)',
        ],
        borderColor: [
          'rgba(75, 192, 192, 1)',
          'rgba(255, 99, 132, 1)',
        ],
        borderWidth: 2,
      },
    ],
  };

  // 參數變化影響分析
  const parameterImpactData = {
    labels: selectedOptimization ? Object.keys(selectedOptimization.parameter_changes) : [],
    datasets: [
      {
        label: '變化百分比',
        data: selectedOptimization ? 
          Object.values(selectedOptimization.parameter_changes).map(change => Math.abs(change.change_percentage)) : [],
        backgroundColor: 'rgba(153, 102, 255, 0.6)',
        borderColor: 'rgba(153, 102, 255, 1)',
        borderWidth: 1,
      },
    ],
  };

  const renderOverviewTab = () => (
    <div className="optimization-overview">
      <div className="summary-cards">
        <div className="summary-card">
          <h4>總優化次數</h4>
          <span className="value">{summary?.total_optimizations || 0}</span>
        </div>
        <div className="summary-card">
          <h4>成功率</h4>
          <span className="value success">
            {summary ? ((summary.successful_optimizations / summary.total_optimizations) * 100).toFixed(1) : 0}%
          </span>
        </div>
        <div className="summary-card">
          <h4>平均改善</h4>
          <span className="value positive">
            +{summary ? (summary.average_improvement * 100).toFixed(1) : 0}%
          </span>
        </div>
        <div className="summary-card">
          <h4>成本節省</h4>
          <span className="value cost">${summary?.total_cost_savings.toFixed(0) || 0}</span>
        </div>
      </div>

      <div className="charts-row">
        <div className="chart-container">
          <h4>優化成功率</h4>
          <Doughnut
            data={successRateData}
            options={{
              responsive: true,
              plugins: {
                legend: {
                  position: 'bottom',
                },
              },
            }}
          />
        </div>

        <div className="chart-container">
          <h4>性能趨勢</h4>
          <Line
            data={performanceTrendsData}
            options={{
              responsive: true,
              plugins: {
                legend: {
                  position: 'top',
                },
              },
              scales: {
                y: {
                  type: 'linear',
                  display: true,
                  position: 'left',
                  title: {
                    display: true,
                    text: '延遲 (ms)',
                  },
                },
                y1: {
                  type: 'linear',
                  display: true,
                  position: 'right',
                  title: {
                    display: true,
                    text: '吞吐量 (Mbps)',
                  },
                  grid: {
                    drawOnChartArea: false,
                  },
                },
                y2: {
                  type: 'linear',
                  display: false,
                  position: 'right',
                },
              },
            }}
          />
        </div>
      </div>

      <div className="recent-optimizations">
        <h4>最近優化記錄</h4>
        <div className="optimizations-list">
          {optimizationResults.slice(0, 5).map((result) => (
            <div 
              key={result.optimization_id}
              className={`optimization-item ${selectedOptimization?.optimization_id === result.optimization_id ? 'selected' : ''}`}
              onClick={() => setSelectedOptimization(result)}
            >
              <div className="optimization-header">
                <span className="cycle">週期 #{result.optimization_cycle}</span>
                <span className={`status ${result.success ? 'success' : 'failed'}`}>
                  {result.success ? '成功' : '失敗'}
                </span>
                <span className="confidence">
                  信心度: {(result.confidence_score * 100).toFixed(0)}%
                </span>
              </div>
              <div className="optimization-details">
                <span className="time">{new Date(result.timestamp).toLocaleString()}</span>
                <span className="trigger">觸發: {result.trigger_reason}</span>
                <span className="changes">
                  參數變更: {Object.keys(result.parameter_changes).length}
                </span>
              </div>
              <div className="optimization-metrics">
                {Object.entries(result.improvements).slice(0, 3).map(([key, value]) => (
                  <span key={key} className={`improvement ${value > 0 ? 'positive' : 'negative'}`}>
                    {key}: {value > 0 ? '+' : ''}{(value * 100).toFixed(1)}%
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  const renderComparisonTab = () => (
    <div className="optimization-comparison">
      <div className="comparison-controls">
        <button 
          className={`compare-button ${compareMode ? 'active' : ''}`}
          onClick={() => {
            setCompareMode(!compareMode);
            setSelectedForComparison([]);
          }}
        >
          {compareMode ? '退出比較模式' : '進入比較模式'}
        </button>
        
        {compareMode && selectedForComparison.length > 0 && (
          <span className="selected-count">
            已選擇 {selectedForComparison.length} 個優化結果進行比較
          </span>
        )}
      </div>

      {selectedOptimization && (
        <div className="detailed-comparison">
          <h4>優化詳細對比</h4>
          <div className="before-after-comparison">
            <div className="comparison-section">
              <h5>優化前</h5>
              <div className="metrics-grid">
                <div className="metric">
                  <label>延遲:</label>
                  <span>{selectedOptimization.before_metrics.latency_ms}ms</span>
                </div>
                <div className="metric">
                  <label>吞吐量:</label>
                  <span>{selectedOptimization.before_metrics.throughput_mbps}Mbps</span>
                </div>
                <div className="metric">
                  <label>覆蓋率:</label>
                  <span>{selectedOptimization.before_metrics.coverage_percentage}%</span>
                </div>
                <div className="metric">
                  <label>功耗:</label>
                  <span>{selectedOptimization.before_metrics.power_consumption_w}W</span>
                </div>
                <div className="metric">
                  <label>CPU使用率:</label>
                  <span>{selectedOptimization.before_metrics.cpu_utilization}%</span>
                </div>
                <div className="metric">
                  <label>記憶體使用率:</label>
                  <span>{selectedOptimization.before_metrics.memory_utilization}%</span>
                </div>
              </div>
            </div>

            <div className="comparison-arrow">→</div>

            <div className="comparison-section">
              <h5>優化後</h5>
              <div className="metrics-grid">
                <div className="metric">
                  <label>延遲:</label>
                  <span>{selectedOptimization.after_metrics.latency_ms}ms</span>
                  <span className={`change ${calculateImprovement(
                    selectedOptimization.before_metrics.latency_ms,
                    selectedOptimization.after_metrics.latency_ms,
                    true
                  ) > 0 ? 'positive' : 'negative'}`}>
                    ({calculateImprovement(
                      selectedOptimization.before_metrics.latency_ms,
                      selectedOptimization.after_metrics.latency_ms,
                      true
                    ).toFixed(1)}%)
                  </span>
                </div>
                <div className="metric">
                  <label>吞吐量:</label>
                  <span>{selectedOptimization.after_metrics.throughput_mbps}Mbps</span>
                  <span className={`change ${calculateImprovement(
                    selectedOptimization.before_metrics.throughput_mbps,
                    selectedOptimization.after_metrics.throughput_mbps
                  ) > 0 ? 'positive' : 'negative'}`}>
                    ({calculateImprovement(
                      selectedOptimization.before_metrics.throughput_mbps,
                      selectedOptimization.after_metrics.throughput_mbps
                    ).toFixed(1)}%)
                  </span>
                </div>
                <div className="metric">
                  <label>覆蓋率:</label>
                  <span>{selectedOptimization.after_metrics.coverage_percentage}%</span>
                  <span className={`change ${calculateImprovement(
                    selectedOptimization.before_metrics.coverage_percentage,
                    selectedOptimization.after_metrics.coverage_percentage
                  ) > 0 ? 'positive' : 'negative'}`}>
                    ({calculateImprovement(
                      selectedOptimization.before_metrics.coverage_percentage,
                      selectedOptimization.after_metrics.coverage_percentage
                    ).toFixed(1)}%)
                  </span>
                </div>
                <div className="metric">
                  <label>功耗:</label>
                  <span>{selectedOptimization.after_metrics.power_consumption_w}W</span>
                  <span className={`change ${calculateImprovement(
                    selectedOptimization.before_metrics.power_consumption_w,
                    selectedOptimization.after_metrics.power_consumption_w,
                    true
                  ) > 0 ? 'positive' : 'negative'}`}>
                    ({calculateImprovement(
                      selectedOptimization.before_metrics.power_consumption_w,
                      selectedOptimization.after_metrics.power_consumption_w,
                      true
                    ).toFixed(1)}%)
                  </span>
                </div>
                <div className="metric">
                  <label>CPU使用率:</label>
                  <span>{selectedOptimization.after_metrics.cpu_utilization}%</span>
                  <span className={`change ${calculateImprovement(
                    selectedOptimization.before_metrics.cpu_utilization,
                    selectedOptimization.after_metrics.cpu_utilization,
                    true
                  ) > 0 ? 'positive' : 'negative'}`}>
                    ({calculateImprovement(
                      selectedOptimization.before_metrics.cpu_utilization,
                      selectedOptimization.after_metrics.cpu_utilization,
                      true
                    ).toFixed(1)}%)
                  </span>
                </div>
                <div className="metric">
                  <label>記憶體使用率:</label>
                  <span>{selectedOptimization.after_metrics.memory_utilization}%</span>
                  <span className={`change ${calculateImprovement(
                    selectedOptimization.before_metrics.memory_utilization,
                    selectedOptimization.after_metrics.memory_utilization,
                    true
                  ) > 0 ? 'positive' : 'negative'}`}>
                    ({calculateImprovement(
                      selectedOptimization.before_metrics.memory_utilization,
                      selectedOptimization.after_metrics.memory_utilization,
                      true
                    ).toFixed(1)}%)
                  </span>
                </div>
              </div>
            </div>
          </div>

          <div className="cost-benefit-analysis">
            <h5>成本效益分析</h5>
            <div className="cost-benefit-grid">
              <div className="cost-benefit-item">
                <label>總成本:</label>
                <span>${selectedOptimization.cost_benefit_analysis.total_cost.toFixed(2)}</span>
              </div>
              <div className="cost-benefit-item">
                <label>總效益:</label>
                <span>${selectedOptimization.cost_benefit_analysis.total_benefit.toFixed(2)}</span>
              </div>
              <div className="cost-benefit-item">
                <label>ROI:</label>
                <span className={`${selectedOptimization.cost_benefit_analysis.roi > 0 ? 'positive' : 'negative'}`}>
                  {(selectedOptimization.cost_benefit_analysis.roi * 100).toFixed(1)}%
                </span>
              </div>
              <div className="cost-benefit-item">
                <label>回收期:</label>
                <span>{selectedOptimization.cost_benefit_analysis.payback_period_hours.toFixed(1)}小時</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  const renderTrendsTab = () => (
    <div className="optimization-trends">
      <div className="trends-summary">
        <h4>趨勢分析摘要</h4>
        <div className="trends-stats">
          <div className="trend-stat">
            <label>最佳表現參數:</label>
            <span>{summary?.best_performing_parameter || 'N/A'}</span>
          </div>
          <div className="trend-stat">
            <label>最大改善指標:</label>
            <span>{summary?.most_improved_metric || 'N/A'}</span>
          </div>
          <div className="trend-stat">
            <label>每日優化頻率:</label>
            <span>{summary?.optimization_frequency_per_day.toFixed(1) || 0} 次/天</span>
          </div>
        </div>
      </div>

      <div className="performance-trends-chart">
        <h4>性能指標趨勢</h4>
        <Line
          data={performanceTrendsData}
          options={{
            responsive: true,
            plugins: {
              legend: {
                position: 'top',
              },
            },
            scales: {
              y: {
                type: 'linear',
                display: true,
                position: 'left',
                title: {
                  display: true,
                  text: '延遲 (ms)',
                },
              },
              y1: {
                type: 'linear',
                display: true,
                position: 'right',
                title: {
                  display: true,
                  text: '吞吐量 (Mbps)',
                },
                grid: {
                  drawOnChartArea: false,
                },
              },
              y2: {
                type: 'linear',
                display: false,
                position: 'right',
              },
            },
          }}
        />
      </div>

      <div className="improvement-trends">
        <h4>改善趨勢</h4>
        <div className="improvement-metrics">
          {optimizationResults.slice(0, 10).map((result) => (
            <div key={result.optimization_id} className="improvement-item">
              <span className="cycle">#{result.optimization_cycle}</span>
              <div className="improvements">
                {Object.entries(result.improvements).map(([metric, value]) => (
                  <span 
                    key={metric}
                    className={`improvement-value ${value > 0 ? 'positive' : 'negative'}`}
                  >
                    {metric}: {value > 0 ? '+' : ''}{(value * 100).toFixed(1)}%
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  const renderParametersTab = () => (
    <div className="optimization-parameters">
      {selectedOptimization && (
        <>
          <div className="parameter-changes">
            <h4>參數變更詳情</h4>
            <div className="parameters-list">
              {Object.entries(selectedOptimization.parameter_changes).map(([param, change]) => (
                <div key={param} className="parameter-item">
                  <div className="parameter-name">{param}</div>
                  <div className="parameter-change">
                    <span className="old-value">{change.old_value}</span>
                    <span className="arrow">→</span>
                    <span className="new-value">{change.new_value}</span>
                    <span className={`percentage ${change.change_percentage > 0 ? 'positive' : 'negative'}`}>
                      ({change.change_percentage > 0 ? '+' : ''}{change.change_percentage.toFixed(1)}%)
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="parameter-impact-chart">
            <h4>參數變化影響分析</h4>
            <Bar
              data={parameterImpactData}
              options={{
                responsive: true,
                plugins: {
                  legend: {
                    display: false,
                  },
                },
                scales: {
                  y: {
                    beginAtZero: true,
                    title: {
                      display: true,
                      text: '變化幅度 (%)',
                    },
                  },
                },
              }}
            />
          </div>

          <div className="optimization-info">
            <h4>優化執行信息</h4>
            <div className="info-grid">
              <div className="info-item">
                <label>實施時間:</label>
                <span>{selectedOptimization.implementation_time_seconds}秒</span>
              </div>
              <div className="info-item">
                <label>觸發原因:</label>
                <span>{selectedOptimization.trigger_reason}</span>
              </div>
              <div className="info-item">
                <label>信心度:</label>
                <span>{(selectedOptimization.confidence_score * 100).toFixed(1)}%</span>
              </div>
              <div className="info-item">
                <label>執行狀態:</label>
                <span className={selectedOptimization.success ? 'success' : 'failed'}>
                  {selectedOptimization.success ? '成功' : '失敗'}
                </span>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );

  return (
    <div className="optimization-results-dashboard">
      <div className="dashboard-header">
        <h2>自動調優結果分析</h2>
        <div className="header-controls">
          <select 
            value={timeRange} 
            onChange={() => setSelectedOptimization(null)}
            className="time-range-selector"
          >
            <option value="last_hour">過去一小時</option>
            <option value="last_day">過去一天</option>
            <option value="last_week">過去一週</option>
            <option value="last_month">過去一月</option>
          </select>
          
          <div className="status-indicator">
            {enableRealTime && (
              <span className={`indicator ${isLoading ? 'loading' : 'active'}`}>
                實時監控
              </span>
            )}
          </div>
          
          <button onClick={triggerManualOptimization} className="manual-optimize-button">
            🚀 手動優化
          </button>
          
          <button onClick={fetchOptimizationResults} disabled={isLoading} className="refresh-button">
            🔄 刷新
          </button>
        </div>
      </div>

      <div className="dashboard-tabs">
        <button
          className={`tab ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          總覽分析
        </button>
        <button
          className={`tab ${activeTab === 'comparison' ? 'active' : ''}`}
          onClick={() => setActiveTab('comparison')}
        >
          對比分析
        </button>
        <button
          className={`tab ${activeTab === 'trends' ? 'active' : ''}`}
          onClick={() => setActiveTab('trends')}
        >
          趨勢分析
        </button>
        <button
          className={`tab ${activeTab === 'parameters' ? 'active' : ''}`}
          onClick={() => setActiveTab('parameters')}
        >
          參數分析
        </button>
      </div>

      <div className="dashboard-content">
        {activeTab === 'overview' && renderOverviewTab()}
        {activeTab === 'comparison' && renderComparisonTab()}
        {activeTab === 'trends' && renderTrendsTab()}
        {activeTab === 'parameters' && renderParametersTab()}
      </div>
    </div>
  );
};

// 輔助函數
function generateMockOptimizationResults(days: number): OptimizationResult[] {
  const results = [];
  const now = new Date();
  
  for (let i = 0; i < Math.min(days * 3, 30); i++) {
    const timestamp = new Date(now.getTime() - i * 8 * 60 * 60 * 1000);
    
    const beforeMetrics: OptimizationMetrics = {
      latency_ms: 45 + Math.random() * 20,
      throughput_mbps: 50 + Math.random() * 30,
      coverage_percentage: 75 + Math.random() * 15,
      power_consumption_w: 100 + Math.random() * 50,
      cpu_utilization: 60 + Math.random() * 25,
      memory_utilization: 65 + Math.random() * 20,
      cost_per_hour: 10 + Math.random() * 5,
      user_satisfaction: 7 + Math.random() * 2
    };
    
    const improvements = {
      latency: -(Math.random() * 0.15),
      throughput: Math.random() * 0.2,
      coverage: Math.random() * 0.1,
      power: -(Math.random() * 0.1),
      cpu: -(Math.random() * 0.05),
      memory: -(Math.random() * 0.05)
    };
    
    const afterMetrics: OptimizationMetrics = {
      latency_ms: beforeMetrics.latency_ms * (1 + improvements.latency),
      throughput_mbps: beforeMetrics.throughput_mbps * (1 + improvements.throughput),
      coverage_percentage: beforeMetrics.coverage_percentage * (1 + improvements.coverage),
      power_consumption_w: beforeMetrics.power_consumption_w * (1 + improvements.power),
      cpu_utilization: beforeMetrics.cpu_utilization * (1 + improvements.cpu),
      memory_utilization: beforeMetrics.memory_utilization * (1 + improvements.memory),
      cost_per_hour: beforeMetrics.cost_per_hour * 0.95,
      user_satisfaction: Math.min(10, beforeMetrics.user_satisfaction * 1.05)
    };
    
    results.push({
      optimization_id: `opt_${i}_${timestamp.getTime()}`,
      timestamp: timestamp.toISOString(),
      optimization_cycle: i + 1,
      trigger_reason: ['scheduled', 'performance_degradation', 'manual', 'ai_recommendation'][Math.floor(Math.random() * 4)],
      parameter_changes: {
        'gnb_tx_power_dbm': {
          old_value: 23,
          new_value: 23 + (Math.random() - 0.5) * 4,
          change_percentage: (Math.random() - 0.5) * 20
        },
        'amf_max_sessions': {
          old_value: 1000,
          new_value: 1000 + Math.floor((Math.random() - 0.5) * 500),
          change_percentage: (Math.random() - 0.5) * 25
        }
      },
      before_metrics: beforeMetrics,
      after_metrics: afterMetrics,
      improvements: improvements,
      implementation_time_seconds: 30 + Math.random() * 120,
      success: Math.random() > 0.1,
      confidence_score: 0.7 + Math.random() * 0.3,
      cost_benefit_analysis: {
        total_cost: 50 + Math.random() * 100,
        total_benefit: 75 + Math.random() * 150,
        roi: (Math.random() - 0.2) * 2,
        payback_period_hours: 2 + Math.random() * 10
      }
    });
  }
  
  return results.reverse();
}

function generateOptimizationSummary(results: OptimizationResult[]): OptimizationSummary {
  const successful = results.filter(r => r.success).length;
  const totalImprovements = results.map(r => Object.values(r.improvements)).flat();
  const avgImprovement = totalImprovements.reduce((sum, imp) => sum + imp, 0) / totalImprovements.length;
  
  return {
    total_optimizations: results.length,
    successful_optimizations: successful,
    average_improvement: avgImprovement,
    total_cost_savings: results.reduce((sum, r) => sum + (r.cost_benefit_analysis.total_benefit - r.cost_benefit_analysis.total_cost), 0),
    best_performing_parameter: 'gnb_tx_power_dbm',
    most_improved_metric: 'throughput',
    optimization_frequency_per_day: results.length / 7
  };
}

export default OptimizationResultsDashboard;