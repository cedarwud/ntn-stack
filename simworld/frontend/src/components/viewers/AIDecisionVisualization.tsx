/**
 * AI 決策過程透明化可視化組件
 * 
 * 階段八：進階 AI 智慧決策與自動化調優
 * 提供 AI 決策過程的透明化展示，包括決策邏輯、信心度和效果預測
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
  RadialLinearScale,
} from 'chart.js';
import { Line, Bar, Doughnut, Radar } from 'react-chartjs-2';
import './AIDecisionVisualization.scss';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  RadialLinearScale,
  Title,
  Tooltip,
  Legend
);

interface DecisionStep {
  step: string;
  description: string;
  confidence: number;
  duration_ms: number;
  result: any;
  importance: number;
}

interface AIDecisionData {
  decision_id: string;
  timestamp: string;
  decision_mode: 'fast' | 'comprehensive';
  confidence_score: number;
  expected_improvements: Record<string, number>;
  decision_steps: DecisionStep[];
  health_analysis: {
    health_score: number;
    risk_level: string;
    anomaly_detected: boolean;
    recommendations: string[];
  };
  learning_prediction: {
    predicted_improvement: number;
    confidence: number;
    detailed_predictions: Record<string, number>;
  };
  comprehensive_decision: {
    actions: Array<{
      type: string;
      confidence: number;
      expected_improvement?: number;
    }>;
    priority_level: number;
    implementation_order: number[];
  };
}

interface AIDecisionVisualizationProps {
  decisionData?: AIDecisionData;
  realTimeMode?: boolean;
  onDecisionUpdate?: (decision: AIDecisionData) => void;
}

const AIDecisionVisualization: React.FC<AIDecisionVisualizationProps> = ({
  decisionData,
  realTimeMode = false,
  onDecisionUpdate
}) => {
  const [currentDecision, setCurrentDecision] = useState<AIDecisionData | null>(decisionData || null);
  const [decisionHistory, setDecisionHistory] = useState<AIDecisionData[]>([]);
  const [activeTab, setActiveTab] = useState<'overview' | 'steps' | 'prediction' | 'health'>('overview');
  const [isLoading, setIsLoading] = useState(false);

  // 模擬實時數據更新
  useEffect(() => {
    if (realTimeMode) {
      const interval = setInterval(() => {
        fetchLatestDecision();
      }, 5000);

      return () => clearInterval(interval);
    }
  }, [realTimeMode]);

  const fetchLatestDecision = useCallback(async () => {
    try {
      setIsLoading(true);
      const response = await fetch('/api/v1/ai-decision/decision-history?limit=1');
      const data = await response.json();
      
      if (data.success && data.decisions.length > 0) {
        const latestDecision = data.decisions[0];
        setCurrentDecision(latestDecision);
        setDecisionHistory(prev => [latestDecision, ...prev.slice(0, 9)]); // 保留最近10個決策
        
        if (onDecisionUpdate) {
          onDecisionUpdate(latestDecision);
        }
      }
    } catch (error) {
      console.error('獲取最新決策失敗:', error);
    } finally {
      setIsLoading(false);
    }
  }, [onDecisionUpdate]);

  // 決策信心度圖表
  const confidenceChartData = {
    labels: ['整體信心度', '健康分析', '學習預測', '決策執行'],
    datasets: [
      {
        label: '信心度',
        data: currentDecision ? [
          currentDecision.confidence_score * 100,
          currentDecision.health_analysis.health_score * 100,
          currentDecision.learning_prediction.confidence * 100,
          Math.min(...currentDecision.comprehensive_decision.actions.map(a => a.confidence * 100))
        ] : [0, 0, 0, 0],
        backgroundColor: [
          'rgba(75, 192, 192, 0.6)',
          'rgba(255, 99, 132, 0.6)',
          'rgba(54, 162, 235, 0.6)',
          'rgba(255, 205, 86, 0.6)',
        ],
        borderColor: [
          'rgba(75, 192, 192, 1)',
          'rgba(255, 99, 132, 1)',
          'rgba(54, 162, 235, 1)',
          'rgba(255, 205, 86, 1)',
        ],
        borderWidth: 2,
      },
    ],
  };

  // 決策步驟時間線圖表
  const stepsTimelineData = {
    labels: currentDecision?.decision_steps.map(step => step.step) || [],
    datasets: [
      {
        label: '執行時間 (ms)',
        data: currentDecision?.decision_steps.map(step => step.duration_ms) || [],
        backgroundColor: 'rgba(54, 162, 235, 0.6)',
        borderColor: 'rgba(54, 162, 235, 1)',
        borderWidth: 1,
      },
      {
        label: '信心度 (%)',
        data: currentDecision?.decision_steps.map(step => step.confidence * 100) || [],
        backgroundColor: 'rgba(255, 99, 132, 0.6)',
        borderColor: 'rgba(255, 99, 132, 1)',
        borderWidth: 1,
        yAxisID: 'y1',
      },
    ],
  };

  // 預期改善雷達圖
  const improvementRadarData = {
    labels: ['延遲', '吞吐量', '覆蓋率', '功耗', '穩定性'],
    datasets: [
      {
        label: '預期改善 (%)',
        data: currentDecision ? [
          (currentDecision.expected_improvements.latency || 0) * 100,
          (currentDecision.expected_improvements.throughput || 0) * 100,
          (currentDecision.expected_improvements.coverage || 0) * 100,
          (currentDecision.expected_improvements.power || 0) * 100,
          (currentDecision.expected_improvements.stability || 0) * 100,
        ] : [0, 0, 0, 0, 0],
        backgroundColor: 'rgba(75, 192, 192, 0.2)',
        borderColor: 'rgba(75, 192, 192, 1)',
        pointBackgroundColor: 'rgba(75, 192, 192, 1)',
        pointBorderColor: '#fff',
        pointHoverBackgroundColor: '#fff',
        pointHoverBorderColor: 'rgba(75, 192, 192, 1)',
      },
    ],
  };

  const renderOverviewTab = () => (
    <div className="ai-decision-overview">
      <div className="decision-summary">
        <div className="summary-card">
          <h4>決策摘要</h4>
          <div className="summary-stats">
            <div className="stat">
              <label>決策ID:</label>
              <span>{currentDecision?.decision_id}</span>
            </div>
            <div className="stat">
              <label>決策模式:</label>
              <span className={`mode ${currentDecision?.decision_mode}`}>
                {currentDecision?.decision_mode === 'fast' ? '快速模式' : '綜合模式'}
              </span>
            </div>
            <div className="stat">
              <label>整體信心度:</label>
              <span className="confidence">{((currentDecision?.confidence_score || 0) * 100).toFixed(1)}%</span>
            </div>
            <div className="stat">
              <label>優先級:</label>
              <span className={`priority priority-${currentDecision?.comprehensive_decision.priority_level}`}>
                {currentDecision?.comprehensive_decision.priority_level === 3 ? '高' : 
                 currentDecision?.comprehensive_decision.priority_level === 2 ? '中' : '低'}
              </span>
            </div>
          </div>
        </div>

        <div className="confidence-chart">
          <h4>各模塊信心度</h4>
          <Bar 
            data={confidenceChartData}
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
                  max: 100,
                  ticks: {
                    callback: function(value) {
                      return value + '%';
                    }
                  }
                },
              },
            }}
          />
        </div>
      </div>

      <div className="actions-overview">
        <h4>建議行動</h4>
        <div className="actions-list">
          {currentDecision?.comprehensive_decision.actions.map((action, index) => (
            <div key={index} className="action-item">
              <div className="action-type">{action.type}</div>
              <div className="action-confidence">
                信心度: {(action.confidence * 100).toFixed(1)}%
              </div>
              {action.expected_improvement && (
                <div className="action-improvement">
                  預期改善: +{(action.expected_improvement * 100).toFixed(1)}%
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      <div className="improvement-radar">
        <h4>預期改善分析</h4>
        <Radar
          data={improvementRadarData}
          options={{
            responsive: true,
            scales: {
              r: {
                beginAtZero: true,
                max: 20,
                ticks: {
                  callback: function(value) {
                    return value + '%';
                  }
                }
              },
            },
          }}
        />
      </div>
    </div>
  );

  const renderStepsTab = () => (
    <div className="ai-decision-steps">
      <div className="steps-timeline">
        <h4>決策步驟時間線</h4>
        <Bar
          data={stepsTimelineData}
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
                  text: '執行時間 (ms)',
                },
              },
              y1: {
                type: 'linear',
                display: true,
                position: 'right',
                title: {
                  display: true,
                  text: '信心度 (%)',
                },
                grid: {
                  drawOnChartArea: false,
                },
                max: 100,
              },
            },
          }}
        />
      </div>

      <div className="steps-details">
        <h4>詳細步驟</h4>
        <div className="steps-list">
          {currentDecision?.decision_steps.map((step, index) => (
            <div key={index} className="step-item">
              <div className="step-header">
                <span className="step-number">{index + 1}</span>
                <h5>{step.step}</h5>
                <span className={`confidence confidence-${Math.floor(step.confidence * 5)}`}>
                  {(step.confidence * 100).toFixed(1)}%
                </span>
              </div>
              <p className="step-description">{step.description}</p>
              <div className="step-metrics">
                <span>執行時間: {step.duration_ms}ms</span>
                <span>重要性: {(step.importance * 100).toFixed(0)}%</span>
              </div>
              {step.result && (
                <div className="step-result">
                  <pre>{JSON.stringify(step.result, null, 2)}</pre>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  const renderPredictionTab = () => (
    <div className="ai-decision-prediction">
      <div className="prediction-summary">
        <h4>學習預測分析</h4>
        <div className="prediction-stats">
          <div className="stat-card">
            <label>預測改善:</label>
            <span className="value positive">
              +{((currentDecision?.learning_prediction.predicted_improvement || 0) * 100).toFixed(1)}%
            </span>
          </div>
          <div className="stat-card">
            <label>預測信心度:</label>
            <span className="value">
              {((currentDecision?.learning_prediction.confidence || 0) * 100).toFixed(1)}%
            </span>
          </div>
        </div>
      </div>

      <div className="detailed-predictions">
        <h4>詳細預測</h4>
        <div className="predictions-grid">
          {Object.entries(currentDecision?.learning_prediction.detailed_predictions || {}).map(([key, value]) => (
            <div key={key} className="prediction-item">
              <label>{key}:</label>
              <div className="prediction-value">
                <span className={value > 0 ? 'positive' : value < 0 ? 'negative' : 'neutral'}>
                  {value > 0 ? '+' : ''}{(value * 100).toFixed(1)}%
                </span>
                <div className="prediction-bar">
                  <div 
                    className="prediction-fill"
                    style={{ 
                      width: `${Math.abs(value) * 100}%`,
                      backgroundColor: value > 0 ? '#4caf50' : value < 0 ? '#f44336' : '#9e9e9e'
                    }}
                  />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="prediction-history">
        <h4>預測準確性歷史</h4>
        {decisionHistory.length > 0 && (
          <Line
            data={{
              labels: decisionHistory.map((_, index) => `T-${index}`).reverse(),
              datasets: [
                {
                  label: '預測改善',
                  data: decisionHistory.map(d => d.learning_prediction.predicted_improvement * 100).reverse(),
                  borderColor: 'rgba(75, 192, 192, 1)',
                  backgroundColor: 'rgba(75, 192, 192, 0.2)',
                  tension: 0.1,
                },
                {
                  label: '預測信心度',
                  data: decisionHistory.map(d => d.learning_prediction.confidence * 100).reverse(),
                  borderColor: 'rgba(255, 99, 132, 1)',
                  backgroundColor: 'rgba(255, 99, 132, 0.2)',
                  tension: 0.1,
                },
              ],
            }}
            options={{
              responsive: true,
              plugins: {
                legend: {
                  position: 'top',
                },
              },
              scales: {
                y: {
                  beginAtZero: true,
                  title: {
                    display: true,
                    text: '百分比 (%)',
                  },
                },
              },
            }}
          />
        )}
      </div>
    </div>
  );

  const renderHealthTab = () => (
    <div className="ai-decision-health">
      <div className="health-overview">
        <h4>系統健康分析</h4>
        <div className="health-score">
          <div className="score-circle">
            <Doughnut
              data={{
                datasets: [
                  {
                    data: [
                      (currentDecision?.health_analysis.health_score || 0) * 100,
                      100 - ((currentDecision?.health_analysis.health_score || 0) * 100)
                    ],
                    backgroundColor: [
                      currentDecision?.health_analysis.health_score > 0.8 ? '#4caf50' :
                      currentDecision?.health_analysis.health_score > 0.6 ? '#ff9800' : '#f44336',
                      '#e0e0e0'
                    ],
                    borderWidth: 0,
                  },
                ],
              }}
              options={{
                cutout: '70%',
                plugins: {
                  legend: {
                    display: false,
                  },
                },
              }}
            />
            <div className="score-text">
              <span className="score-value">
                {((currentDecision?.health_analysis.health_score || 0) * 100).toFixed(0)}
              </span>
              <span className="score-label">健康分數</span>
            </div>
          </div>
        </div>

        <div className="health-status">
          <div className="status-item">
            <label>風險等級:</label>
            <span className={`risk-level ${currentDecision?.health_analysis.risk_level}`}>
              {currentDecision?.health_analysis.risk_level === 'high' ? '高風險' :
               currentDecision?.health_analysis.risk_level === 'medium' ? '中風險' :
               currentDecision?.health_analysis.risk_level === 'low' ? '低風險' : '最小風險'}
            </span>
          </div>
          <div className="status-item">
            <label>異常檢測:</label>
            <span className={`anomaly ${currentDecision?.health_analysis.anomaly_detected ? 'detected' : 'normal'}`}>
              {currentDecision?.health_analysis.anomaly_detected ? '檢測到異常' : '正常'}
            </span>
          </div>
        </div>
      </div>

      <div className="health-recommendations">
        <h4>維護建議</h4>
        <div className="recommendations-list">
          {currentDecision?.health_analysis.recommendations.map((recommendation, index) => (
            <div key={index} className="recommendation-item">
              <span className="recommendation-icon">💡</span>
              <span className="recommendation-text">{recommendation}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  if (!currentDecision) {
    return (
      <div className="ai-decision-visualization loading">
        <div className="loading-message">
          {isLoading ? '加載中...' : '無決策數據'}
        </div>
        {realTimeMode && (
          <button onClick={fetchLatestDecision} disabled={isLoading}>
            刷新數據
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="ai-decision-visualization">
      <div className="visualization-header">
        <h3>AI 決策透明化展示</h3>
        <div className="header-controls">
          <div className="real-time-indicator">
            {realTimeMode && (
              <span className={`indicator ${isLoading ? 'loading' : 'active'}`}>
                實時模式
              </span>
            )}
          </div>
          <button 
            className="refresh-button"
            onClick={fetchLatestDecision}
            disabled={isLoading}
          >
            🔄 刷新
          </button>
        </div>
      </div>

      <div className="visualization-tabs">
        <button
          className={`tab ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          總覽
        </button>
        <button
          className={`tab ${activeTab === 'steps' ? 'active' : ''}`}
          onClick={() => setActiveTab('steps')}
        >
          決策步驟
        </button>
        <button
          className={`tab ${activeTab === 'prediction' ? 'active' : ''}`}
          onClick={() => setActiveTab('prediction')}
        >
          學習預測
        </button>
        <button
          className={`tab ${activeTab === 'health' ? 'active' : ''}`}
          onClick={() => setActiveTab('health')}
        >
          健康分析
        </button>
      </div>

      <div className="visualization-content">
        {activeTab === 'overview' && renderOverviewTab()}
        {activeTab === 'steps' && renderStepsTab()}
        {activeTab === 'prediction' && renderPredictionTab()}
        {activeTab === 'health' && renderHealthTab()}
      </div>

      {decisionHistory.length > 0 && (
        <div className="decision-history-summary">
          <h4>最近決策記錄</h4>
          <div className="history-list">
            {decisionHistory.slice(0, 5).map((decision, index) => (
              <div 
                key={decision.decision_id} 
                className={`history-item ${decision.decision_id === currentDecision.decision_id ? 'current' : ''}`}
                onClick={() => setCurrentDecision(decision)}
              >
                <span className="history-time">
                  {new Date(decision.timestamp).toLocaleTimeString()}
                </span>
                <span className="history-confidence">
                  {(decision.confidence_score * 100).toFixed(0)}%
                </span>
                <span className="history-mode">{decision.decision_mode}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default AIDecisionVisualization;