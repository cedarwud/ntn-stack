/**
 * 機器學習模型監控儀表板
 * 
 * 階段八：進階 AI 智慧決策與自動化調優
 * 提供機器學習模型訓練、評估和性能監控的全面視圖
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
import './MLModelMonitoringDashboard.scss';

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

interface ModelMetrics {
  accuracy: number;
  precision: number;
  recall: number;
  f1_score: number;
  loss: number;
  training_time: number;
  inference_time: number;
  memory_usage: number;
}

interface TrainingProgress {
  epoch: number;
  loss: number;
  val_loss: number;
  accuracy: number;
  val_accuracy: number;
  learning_rate: number;
  timestamp: string;
}

interface ModelInfo {
  model_id: string;
  model_name: string;
  model_type: string;
  version: string;
  status: 'training' | 'trained' | 'deployed' | 'failed';
  created_at: string;
  last_updated: string;
  metrics: ModelMetrics;
  training_progress: TrainingProgress[];
  hyperparameters: Record<string, any>;
  dataset_info: {
    training_samples: number;
    validation_samples: number;
    test_samples: number;
    features: number;
  };
}

interface PredictionStats {
  total_predictions: number;
  successful_predictions: number;
  failed_predictions: number;
  average_confidence: number;
  prediction_distribution: Record<string, number>;
  recent_predictions: Array<{
    timestamp: string;
    input: any;
    prediction: any;
    confidence: number;
    actual?: any;
    correct?: boolean;
  }>;
}

interface MLModelMonitoringDashboardProps {
  refreshInterval?: number;
  enableRealTime?: boolean;
}

const MLModelMonitoringDashboard: React.FC<MLModelMonitoringDashboardProps> = ({
  refreshInterval = 10000,
  enableRealTime = true
}) => {
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [selectedModel, setSelectedModel] = useState<ModelInfo | null>(null);
  const [predictionStats, setPredictionStats] = useState<PredictionStats | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'training' | 'performance' | 'predictions'>('overview');
  const [isLoading, setIsLoading] = useState(false);
  const [isTraining, setIsTraining] = useState(false);

  // 獲取模型列表
  const fetchModels = useCallback(async () => {
    try {
      setIsLoading(true);
      
      // 獲取 AI-RAN 模型狀態
      const aiRanResponse = await fetch('/api/v1/ai-decision/ai-ran/status');
      const aiRanData = await aiRanResponse.json();
      
      // 獲取自動優化服務狀態
      const optimizationResponse = await fetch('/api/v1/ai-decision/optimization/status');
      const optimizationData = await optimizationResponse.json();
      
      // 模擬模型信息（實際應用中會從後端API獲取）
      const mockModels: ModelInfo[] = [
        {
          model_id: 'ai-ran-dqn',
          model_name: 'AI-RAN DQN 模型',
          model_type: 'Deep Q-Network',
          version: '1.2.0',
          status: aiRanData.model_loaded ? 'deployed' : 'failed',
          created_at: '2024-01-15T10:00:00Z',
          last_updated: '2024-01-20T15:30:00Z',
          metrics: {
            accuracy: 0.89,
            precision: 0.87,
            recall: 0.91,
            f1_score: 0.89,
            loss: 0.15,
            training_time: 3600,
            inference_time: 12,
            memory_usage: 256
          },
          training_progress: generateMockTrainingProgress(),
          hyperparameters: {
            learning_rate: 0.001,
            batch_size: 32,
            hidden_layers: 3,
            neurons_per_layer: 256,
            dropout_rate: 0.1,
            epsilon: aiRanData.epsilon || 0.1
          },
          dataset_info: {
            training_samples: 10000,
            validation_samples: 2000,
            test_samples: 1000,
            features: 20
          }
        },
        {
          model_id: 'optimization-rf',
          model_name: '系統優化隨機森林',
          model_type: 'Random Forest',
          version: '2.1.0',
          status: optimizationData.ml_engine_trained ? 'deployed' : 'training',
          created_at: '2024-01-18T09:00:00Z',
          last_updated: '2024-01-22T11:45:00Z',
          metrics: {
            accuracy: 0.94,
            precision: 0.92,
            recall: 0.96,
            f1_score: 0.94,
            loss: 0.08,
            training_time: 1200,
            inference_time: 5,
            memory_usage: 128
          },
          training_progress: generateMockTrainingProgress(),
          hyperparameters: {
            n_estimators: 100,
            max_depth: 10,
            min_samples_split: 2,
            min_samples_leaf: 1,
            random_state: 42
          },
          dataset_info: {
            training_samples: 5000,
            validation_samples: 1000,
            test_samples: 500,
            features: 12
          }
        },
        {
          model_id: 'predictive-maintenance',
          model_name: '預測性維護模型',
          model_type: 'Isolation Forest',
          version: '1.0.0',
          status: 'trained',
          created_at: '2024-01-20T14:00:00Z',
          last_updated: '2024-01-22T16:20:00Z',
          metrics: {
            accuracy: 0.91,
            precision: 0.88,
            recall: 0.93,
            f1_score: 0.90,
            loss: 0.12,
            training_time: 800,
            inference_time: 8,
            memory_usage: 96
          },
          training_progress: generateMockTrainingProgress(),
          hyperparameters: {
            contamination: 0.1,
            n_estimators: 100,
            max_samples: 'auto',
            random_state: 42
          },
          dataset_info: {
            training_samples: 3000,
            validation_samples: 600,
            test_samples: 300,
            features: 10
          }
        }
      ];
      
      setModels(mockModels);
      
      if (!selectedModel && mockModels.length > 0) {
        setSelectedModel(mockModels[0]);
      }
      
    } catch (error) {
      console.error('獲取模型信息失敗:', error);
    } finally {
      setIsLoading(false);
    }
  }, [selectedModel]);

  // 獲取預測統計
  const fetchPredictionStats = useCallback(async (modelId: string) => {
    try {
      // 模擬預測統計數據
      const mockStats: PredictionStats = {
        total_predictions: 15420,
        successful_predictions: 14891,
        failed_predictions: 529,
        average_confidence: 0.87,
        prediction_distribution: {
          'interference_mitigation': 3500,
          'performance_optimization': 4200,
          'predictive_maintenance': 2800,
          'resource_allocation': 2920,
          'other': 2000
        },
        recent_predictions: generateMockRecentPredictions()
      };
      
      setPredictionStats(mockStats);
    } catch (error) {
      console.error('獲取預測統計失敗:', error);
    }
  }, []);

  // 訓練模型
  const handleTrainModel = async (modelId: string) => {
    try {
      setIsTraining(true);
      
      if (modelId === 'ai-ran-dqn') {
        const response = await fetch('/api/v1/ai-decision/ai-ran/train', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            training_episodes: 1000,
            save_interval: 100
          })
        });
        
        if (response.ok) {
          alert('AI-RAN 模型訓練已啟動');
        }
      } else {
        // 其他模型的訓練邏輯
        setTimeout(() => {
          alert(`${modelId} 模型訓練完成`);
          fetchModels();
        }, 3000);
      }
      
    } catch (error) {
      console.error('訓練模型失敗:', error);
      alert('訓練模型失敗');
    } finally {
      setIsTraining(false);
    }
  };

  useEffect(() => {
    fetchModels();
    
    if (enableRealTime) {
      const interval = setInterval(fetchModels, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [fetchModels, enableRealTime, refreshInterval]);

  useEffect(() => {
    if (selectedModel) {
      fetchPredictionStats(selectedModel.model_id);
    }
  }, [selectedModel, fetchPredictionStats]);

  // 訓練進度圖表
  const trainingProgressData = {
    labels: selectedModel?.training_progress.map(p => `Epoch ${p.epoch}`) || [],
    datasets: [
      {
        label: '訓練損失',
        data: selectedModel?.training_progress.map(p => p.loss) || [],
        borderColor: 'rgba(255, 99, 132, 1)',
        backgroundColor: 'rgba(255, 99, 132, 0.2)',
        tension: 0.1,
      },
      {
        label: '驗證損失',
        data: selectedModel?.training_progress.map(p => p.val_loss) || [],
        borderColor: 'rgba(54, 162, 235, 1)',
        backgroundColor: 'rgba(54, 162, 235, 0.2)',
        tension: 0.1,
      },
    ],
  };

  // 模型性能指標圖表
  const performanceMetricsData = {
    labels: ['準確率', '精確率', '召回率', 'F1分數'],
    datasets: [
      {
        data: selectedModel ? [
          selectedModel.metrics.accuracy * 100,
          selectedModel.metrics.precision * 100,
          selectedModel.metrics.recall * 100,
          selectedModel.metrics.f1_score * 100
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

  // 預測分布圖表
  const predictionDistributionData = {
    labels: Object.keys(predictionStats?.prediction_distribution || {}),
    datasets: [
      {
        data: Object.values(predictionStats?.prediction_distribution || {}),
        backgroundColor: [
          'rgba(255, 99, 132, 0.6)',
          'rgba(54, 162, 235, 0.6)',
          'rgba(255, 205, 86, 0.6)',
          'rgba(75, 192, 192, 0.6)',
          'rgba(153, 102, 255, 0.6)',
        ],
        borderWidth: 1,
      },
    ],
  };

  const renderOverviewTab = () => (
    <div className="ml-overview">
      <div className="models-grid">
        {models.map(model => (
          <div 
            key={model.model_id}
            className={`model-card ${selectedModel?.model_id === model.model_id ? 'selected' : ''}`}
            onClick={() => setSelectedModel(model)}
          >
            <div className="model-header">
              <h4>{model.model_name}</h4>
              <span className={`status ${model.status}`}>
                {model.status === 'deployed' ? '已部署' :
                 model.status === 'trained' ? '已訓練' :
                 model.status === 'training' ? '訓練中' : '失敗'}
              </span>
            </div>
            <div className="model-info">
              <p>類型: {model.model_type}</p>
              <p>版本: {model.version}</p>
              <p>準確率: {(model.metrics.accuracy * 100).toFixed(1)}%</p>
            </div>
            <div className="model-actions">
              <button 
                onClick={(e) => {
                  e.stopPropagation();
                  handleTrainModel(model.model_id);
                }}
                disabled={isTraining || model.status === 'training'}
                className="train-button"
              >
                {model.status === 'training' ? '訓練中...' : '重新訓練'}
              </button>
            </div>
          </div>
        ))}
      </div>

      {selectedModel && (
        <div className="model-details">
          <div className="detail-section">
            <h4>模型詳情</h4>
            <div className="details-grid">
              <div className="detail-item">
                <label>模型ID:</label>
                <span>{selectedModel.model_id}</span>
              </div>
              <div className="detail-item">
                <label>創建時間:</label>
                <span>{new Date(selectedModel.created_at).toLocaleString()}</span>
              </div>
              <div className="detail-item">
                <label>最後更新:</label>
                <span>{new Date(selectedModel.last_updated).toLocaleString()}</span>
              </div>
              <div className="detail-item">
                <label>訓練樣本:</label>
                <span>{selectedModel.dataset_info.training_samples.toLocaleString()}</span>
              </div>
            </div>
          </div>

          <div className="metrics-section">
            <h4>性能指標</h4>
            <div className="metrics-grid">
              <div className="metric-item">
                <label>準確率</label>
                <span>{(selectedModel.metrics.accuracy * 100).toFixed(1)}%</span>
              </div>
              <div className="metric-item">
                <label>精確率</label>
                <span>{(selectedModel.metrics.precision * 100).toFixed(1)}%</span>
              </div>
              <div className="metric-item">
                <label>召回率</label>
                <span>{(selectedModel.metrics.recall * 100).toFixed(1)}%</span>
              </div>
              <div className="metric-item">
                <label>F1分數</label>
                <span>{(selectedModel.metrics.f1_score * 100).toFixed(1)}%</span>
              </div>
              <div className="metric-item">
                <label>推理時間</label>
                <span>{selectedModel.metrics.inference_time}ms</span>
              </div>
              <div className="metric-item">
                <label>記憶體使用</label>
                <span>{selectedModel.metrics.memory_usage}MB</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  const renderTrainingTab = () => (
    <div className="ml-training">
      {selectedModel && (
        <>
          <div className="training-progress-chart">
            <h4>訓練進度</h4>
            <Line
              data={trainingProgressData}
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
                      text: '損失值',
                    },
                  },
                },
              }}
            />
          </div>

          <div className="hyperparameters-section">
            <h4>超參數配置</h4>
            <div className="hyperparameters-grid">
              {Object.entries(selectedModel.hyperparameters).map(([key, value]) => (
                <div key={key} className="hyperparameter-item">
                  <label>{key}:</label>
                  <span>{typeof value === 'number' ? value.toFixed(4) : String(value)}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="dataset-info-section">
            <h4>數據集信息</h4>
            <div className="dataset-grid">
              <div className="dataset-item">
                <label>訓練樣本:</label>
                <span>{selectedModel.dataset_info.training_samples.toLocaleString()}</span>
              </div>
              <div className="dataset-item">
                <label>驗證樣本:</label>
                <span>{selectedModel.dataset_info.validation_samples.toLocaleString()}</span>
              </div>
              <div className="dataset-item">
                <label>測試樣本:</label>
                <span>{selectedModel.dataset_info.test_samples.toLocaleString()}</span>
              </div>
              <div className="dataset-item">
                <label>特徵數量:</label>
                <span>{selectedModel.dataset_info.features}</span>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );

  const renderPerformanceTab = () => (
    <div className="ml-performance">
      {selectedModel && (
        <>
          <div className="performance-metrics-chart">
            <h4>性能指標對比</h4>
            <Bar
              data={performanceMetricsData}
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
                    title: {
                      display: true,
                      text: '百分比 (%)',
                    },
                  },
                },
              }}
            />
          </div>

          <div className="performance-comparison">
            <h4>性能對比</h4>
            <div className="comparison-table">
              <div className="table-header">
                <span>指標</span>
                <span>當前值</span>
                <span>目標值</span>
                <span>狀態</span>
              </div>
              <div className="table-row">
                <span>準確率</span>
                <span>{(selectedModel.metrics.accuracy * 100).toFixed(1)}%</span>
                <span>90%</span>
                <span className={selectedModel.metrics.accuracy >= 0.9 ? 'good' : 'warning'}>
                  {selectedModel.metrics.accuracy >= 0.9 ? '✓ 達標' : '⚠ 未達標'}
                </span>
              </div>
              <div className="table-row">
                <span>推理時間</span>
                <span>{selectedModel.metrics.inference_time}ms</span>
                <span>&lt;50ms</span>
                <span className={selectedModel.metrics.inference_time < 50 ? 'good' : 'warning'}>
                  {selectedModel.metrics.inference_time < 50 ? '✓ 達標' : '⚠ 未達標'}
                </span>
              </div>
              <div className="table-row">
                <span>記憶體使用</span>
                <span>{selectedModel.metrics.memory_usage}MB</span>
                <span>&lt;512MB</span>
                <span className={selectedModel.metrics.memory_usage < 512 ? 'good' : 'warning'}>
                  {selectedModel.metrics.memory_usage < 512 ? '✓ 達標' : '⚠ 未達標'}
                </span>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );

  const renderPredictionsTab = () => (
    <div className="ml-predictions">
      {predictionStats && (
        <>
          <div className="prediction-stats">
            <div className="stats-grid">
              <div className="stat-card">
                <h4>總預測次數</h4>
                <span className="stat-value">{predictionStats.total_predictions.toLocaleString()}</span>
              </div>
              <div className="stat-card">
                <h4>成功率</h4>
                <span className="stat-value">
                  {((predictionStats.successful_predictions / predictionStats.total_predictions) * 100).toFixed(1)}%
                </span>
              </div>
              <div className="stat-card">
                <h4>平均信心度</h4>
                <span className="stat-value">{(predictionStats.average_confidence * 100).toFixed(1)}%</span>
              </div>
            </div>
          </div>

          <div className="prediction-distribution">
            <h4>預測分布</h4>
            <Doughnut
              data={predictionDistributionData}
              options={{
                responsive: true,
                plugins: {
                  legend: {
                    position: 'right',
                  },
                },
              }}
            />
          </div>

          <div className="recent-predictions">
            <h4>最近預測</h4>
            <div className="predictions-list">
              {predictionStats.recent_predictions.slice(0, 10).map((prediction, index) => (
                <div key={index} className="prediction-item">
                  <div className="prediction-time">
                    {new Date(prediction.timestamp).toLocaleString()}
                  </div>
                  <div className="prediction-confidence">
                    信心度: {(prediction.confidence * 100).toFixed(1)}%
                  </div>
                  {prediction.correct !== undefined && (
                    <div className={`prediction-result ${prediction.correct ? 'correct' : 'incorrect'}`}>
                      {prediction.correct ? '✓ 正確' : '✗ 錯誤'}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );

  return (
    <div className="ml-model-monitoring-dashboard">
      <div className="dashboard-header">
        <h2>機器學習模型監控</h2>
        <div className="header-controls">
          <div className="refresh-indicator">
            {enableRealTime && (
              <span className={`indicator ${isLoading ? 'loading' : 'active'}`}>
                實時監控
              </span>
            )}
          </div>
          <button onClick={fetchModels} disabled={isLoading} className="refresh-button">
            🔄 刷新
          </button>
        </div>
      </div>

      <div className="dashboard-tabs">
        <button
          className={`tab ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          模型總覽
        </button>
        <button
          className={`tab ${activeTab === 'training' ? 'active' : ''}`}
          onClick={() => setActiveTab('training')}
        >
          訓練監控
        </button>
        <button
          className={`tab ${activeTab === 'performance' ? 'active' : ''}`}
          onClick={() => setActiveTab('performance')}
        >
          性能分析
        </button>
        <button
          className={`tab ${activeTab === 'predictions' ? 'active' : ''}`}
          onClick={() => setActiveTab('predictions')}
        >
          預測統計
        </button>
      </div>

      <div className="dashboard-content">
        {activeTab === 'overview' && renderOverviewTab()}
        {activeTab === 'training' && renderTrainingTab()}
        {activeTab === 'performance' && renderPerformanceTab()}
        {activeTab === 'predictions' && renderPredictionsTab()}
      </div>
    </div>
  );
};

// 輔助函數
function generateMockTrainingProgress(): TrainingProgress[] {
  const progress = [];
  for (let epoch = 1; epoch <= 100; epoch++) {
    progress.push({
      epoch,
      loss: Math.max(0.01, 1.0 - (epoch * 0.01) + Math.random() * 0.1),
      val_loss: Math.max(0.02, 1.1 - (epoch * 0.01) + Math.random() * 0.15),
      accuracy: Math.min(0.99, epoch * 0.01 + Math.random() * 0.05),
      val_accuracy: Math.min(0.98, epoch * 0.009 + Math.random() * 0.05),
      learning_rate: 0.001 * Math.pow(0.95, Math.floor(epoch / 20)),
      timestamp: new Date(Date.now() - (100 - epoch) * 3600000).toISOString()
    });
  }
  return progress;
}

function generateMockRecentPredictions() {
  const predictions = [];
  for (let i = 0; i < 20; i++) {
    predictions.push({
      timestamp: new Date(Date.now() - i * 300000).toISOString(),
      input: { feature1: Math.random(), feature2: Math.random() },
      prediction: Math.random() > 0.5 ? 'optimize' : 'maintain',
      confidence: 0.7 + Math.random() * 0.3,
      actual: Math.random() > 0.5 ? 'optimize' : 'maintain',
      correct: Math.random() > 0.15
    });
  }
  return predictions;
}

export default MLModelMonitoringDashboard;