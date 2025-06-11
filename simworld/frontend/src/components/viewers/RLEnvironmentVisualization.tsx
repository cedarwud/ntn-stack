import React, { useState, useEffect, useRef } from 'react';

interface EnvironmentInfo {
  name: string;
  observation_space: {
    shape: number[];
    dtype: string;
    low: number;
    high: number;
  };
  action_space: {
    shape: number[];
    dtype: string;
    low?: number;
    high?: number;
  };
  current_state?: number[];
  last_action?: number[];
  last_reward?: number;
  episode_steps?: number;
  total_episodes?: number;
}

interface RLEnvironmentVisualizationProps {
  environmentName: string;
}

const RLEnvironmentVisualization: React.FC<RLEnvironmentVisualizationProps> = ({
  environmentName
}) => {
  const [envInfo, setEnvInfo] = useState<EnvironmentInfo | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedDimension, setSelectedDimension] = useState(0);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    fetchEnvironmentInfo();
  }, [environmentName]);

  const fetchEnvironmentInfo = async () => {
    setIsLoading(true);
    try {
      // 模擬獲取環境信息
      const mockEnvInfo: EnvironmentInfo = {
        name: environmentName,
        observation_space: {
          shape: environmentName.includes('Interference') ? [20] : 
                environmentName.includes('Optimization') ? [15] : [37],
          dtype: 'float32',
          low: -10.0,
          high: 10.0
        },
        action_space: {
          shape: environmentName.includes('Interference') ? [4] :
                 environmentName.includes('Optimization') ? [6] : [16],
          dtype: 'float32',
          low: -1.0,
          high: 1.0
        },
        current_state: generateRandomState(
          environmentName.includes('Interference') ? 20 :
          environmentName.includes('Optimization') ? 15 : 37
        ),
        last_action: generateRandomAction(
          environmentName.includes('Interference') ? 4 :
          environmentName.includes('Optimization') ? 6 : 16
        ),
        last_reward: Math.random() * 20 - 5,
        episode_steps: Math.floor(Math.random() * 100) + 1,
        total_episodes: Math.floor(Math.random() * 1000) + 100
      };

      setEnvInfo(mockEnvInfo);
    } catch (error) {
      console.error('Failed to fetch environment info:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const generateRandomState = (size: number): number[] => {
    return Array.from({ length: size }, () => Math.random() * 20 - 10);
  };

  const generateRandomAction = (size: number): number[] => {
    return Array.from({ length: size }, () => Math.random() * 2 - 1);
  };

  // 繪製狀態空間可視化
  useEffect(() => {
    if (envInfo && envInfo.current_state && canvasRef.current) {
      const canvas = canvasRef.current;
      const ctx = canvas.getContext('2d');
      if (!ctx) return;

      const width = canvas.width;
      const height = canvas.height;

      // 清除畫布
      ctx.clearRect(0, 0, width, height);

      // 繪製狀態向量熱力圖
      const cellWidth = width / envInfo.current_state.length;
      const cellHeight = height * 0.6;

      envInfo.current_state.forEach((value, index) => {
        const x = index * cellWidth;
        const y = height * 0.2;
        
        // 正規化值到 0-1 範圍
        const normalizedValue = (value - envInfo.observation_space.low) / 
          (envInfo.observation_space.high - envInfo.observation_space.low);
        
        // 顏色映射：藍色(低) -> 綠色(中) -> 紅色(高)
        const hue = (1 - normalizedValue) * 240; // 240是藍色，0是紅色
        ctx.fillStyle = `hsl(${hue}, 70%, 50%)`;
        ctx.fillRect(x, y, cellWidth - 1, cellHeight);
        
        // 顯示數值
        ctx.fillStyle = 'white';
        ctx.font = '10px Arial';
        ctx.textAlign = 'center';
        ctx.fillText(
          value.toFixed(2), 
          x + cellWidth / 2, 
          y + cellHeight / 2 + 3
        );
        
        // 顯示維度標籤
        ctx.fillStyle = 'black';
        ctx.fillText(
          `S${index}`, 
          x + cellWidth / 2, 
          y - 5
        );
      });

      // 繪製動作向量
      if (envInfo.last_action) {
        const actionCellWidth = width / envInfo.last_action.length;
        const actionCellHeight = height * 0.15;
        const actionY = height * 0.85;

        envInfo.last_action.forEach((value, index) => {
          const x = index * actionCellWidth;
          
          // 正規化動作值
          const normalizedValue = (value - (envInfo.action_space.low || -1)) / 
            ((envInfo.action_space.high || 1) - (envInfo.action_space.low || -1));
          
          // 動作用綠色調
          const alpha = Math.abs(normalizedValue - 0.5) * 2;
          ctx.fillStyle = `rgba(34, 139, 34, ${alpha})`;
          ctx.fillRect(x, actionY, actionCellWidth - 1, actionCellHeight);
          
          ctx.fillStyle = 'white';
          ctx.font = '9px Arial';
          ctx.textAlign = 'center';
          ctx.fillText(
            value.toFixed(2), 
            x + actionCellWidth / 2, 
            actionY + actionCellHeight / 2 + 3
          );
          
          ctx.fillStyle = 'black';
          ctx.fillText(
            `A${index}`, 
            x + actionCellWidth / 2, 
            actionY - 5
          );
        });
      }

      // 添加標籤
      ctx.fillStyle = 'black';
      ctx.font = 'bold 14px Arial';
      ctx.textAlign = 'left';
      ctx.fillText('狀態空間 (State Space)', 10, 15);
      ctx.fillText('動作空間 (Action Space)', 10, height - 50);
    }
  }, [envInfo]);

  const getEnvironmentDescription = (name: string) => {
    if (name.includes('Interference')) {
      return {
        title: '干擾緩解環境',
        description: '用於訓練 AI 代理學習如何緩解無線通信干擾',
        stateFeatures: [
          'SINR 信號質量', 'RSRP 接收功率', '發射功率', '頻率', '帶寬',
          '干擾源數量', '干擾水平', '網路負載', '用戶數量', '時間因子'
        ],
        actionFeatures: [
          '功率控制', '頻率選擇', '波束方向', '展頻因子'
        ]
      };
    } else if (name.includes('Optimization')) {
      return {
        title: '網路優化環境',
        description: '用於訓練 AI 代理優化網路性能和資源配置',
        stateFeatures: [
          '吞吐量', '延遲', '封包遺失率', 'CPU 使用率', '記憶體使用率',
          '網路負載', '連接數', '帶寬利用率'
        ],
        actionFeatures: [
          '帶寬分配', 'QoS 優先級', '負載平衡', '快取策略', '路由優化', '資源調度'
        ]
      };
    } else {
      return {
        title: 'UAV 編隊環境',
        description: '用於訓練 AI 代理控制 UAV 編隊飛行和協調',
        stateFeatures: [
          'UAV 位置(xyz)', '速度向量', '加速度', '方向角', '編隊狀態',
          '通信質量', '電池電量', '任務進度', '環境條件'
        ],
        actionFeatures: [
          '推力控制', '方向控制', '高度調整', '速度調節',
          '編隊調整', '通信功率', '路徑規劃', '避障行為'
        ]
      };
    }
  };

  if (isLoading) {
    return (
      <div className="rl-env-visualization loading">
        <div className="loading-spinner">⏳ 載入環境信息中...</div>
      </div>
    );
  }

  if (!envInfo) {
    return (
      <div className="rl-env-visualization error">
        <div className="error-message">❌ 無法載入環境信息</div>
      </div>
    );
  }

  const envDesc = getEnvironmentDescription(envInfo.name);

  return (
    <div className="rl-env-visualization">
      <div className="env-header">
        <h2>🎮 {envDesc.title}</h2>
        <p className="env-description">{envDesc.description}</p>
        
        <div className="env-stats">
          <div className="stat-item">
            <span className="stat-label">觀察維度:</span>
            <span className="stat-value">{envInfo.observation_space.shape[0]}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">動作維度:</span>
            <span className="stat-value">{envInfo.action_space.shape[0]}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">當前集數:</span>
            <span className="stat-value">{envInfo.total_episodes}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">步驟數:</span>
            <span className="stat-value">{envInfo.episode_steps}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">最後獎勵:</span>
            <span className={`stat-value ${envInfo.last_reward! > 0 ? 'positive' : 'negative'}`}>
              {envInfo.last_reward?.toFixed(3)}
            </span>
          </div>
        </div>
      </div>

      <div className="visualization-container">
        <canvas
          ref={canvasRef}
          width={800}
          height={400}
          className="state-action-canvas"
        />
      </div>

      <div className="feature-explanation">
        <div className="feature-section">
          <h3>📊 狀態特徵說明</h3>
          <div className="feature-grid">
            {envDesc.stateFeatures.map((feature, index) => (
              <div key={index} className="feature-item">
                <span className="feature-index">S{index}</span>
                <span className="feature-name">{feature}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="feature-section">
          <h3>🎯 動作特徵說明</h3>
          <div className="feature-grid">
            {envDesc.actionFeatures.map((feature, index) => (
              <div key={index} className="feature-item">
                <span className="feature-index action">A{index}</span>
                <span className="feature-name">{feature}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="control-panel">
        <button onClick={fetchEnvironmentInfo} className="refresh-btn">
          🔄 刷新狀態
        </button>
        <button className="step-btn">
          ▶️ 執行一步
        </button>
        <button className="reset-btn">
          🔄 重置環境
        </button>
      </div>

      <style jsx>{`
        .rl-env-visualization {
          padding: 20px;
          background: #f8f9fa;
          border-radius: 12px;
          border: 1px solid #e9ecef;
        }

        .env-header {
          margin-bottom: 20px;
        }

        .env-header h2 {
          color: #333;
          margin: 0 0 10px 0;
          font-size: 24px;
        }

        .env-description {
          color: #666;
          margin-bottom: 15px;
          font-size: 14px;
        }

        .env-stats {
          display: flex;
          gap: 20px;
          flex-wrap: wrap;
        }

        .stat-item {
          display: flex;
          flex-direction: column;
          gap: 5px;
        }

        .stat-label {
          font-size: 12px;
          color: #666;
          font-weight: 500;
        }

        .stat-value {
          font-size: 16px;
          font-weight: 600;
          color: #333;
        }

        .stat-value.positive {
          color: #28a745;
        }

        .stat-value.negative {
          color: #dc3545;
        }

        .visualization-container {
          margin: 20px 0;
          text-align: center;
        }

        .state-action-canvas {
          border: 2px solid #dee2e6;
          border-radius: 8px;
          background: white;
          max-width: 100%;
          height: auto;
        }

        .feature-explanation {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 20px;
          margin: 20px 0;
        }

        .feature-section h3 {
          color: #333;
          margin: 0 0 15px 0;
          font-size: 18px;
        }

        .feature-grid {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .feature-item {
          display: flex;
          align-items: center;
          gap: 10px;
          padding: 8px 12px;
          background: white;
          border-radius: 6px;
          border: 1px solid #e9ecef;
        }

        .feature-index {
          background: #007bff;
          color: white;
          padding: 2px 8px;
          border-radius: 4px;
          font-size: 12px;
          font-weight: 600;
          min-width: 25px;
          text-align: center;
        }

        .feature-index.action {
          background: #28a745;
        }

        .feature-name {
          font-size: 14px;
          color: #333;
        }

        .control-panel {
          display: flex;
          gap: 10px;
          justify-content: center;
          margin-top: 20px;
        }

        .control-panel button {
          padding: 10px 20px;
          border: none;
          border-radius: 6px;
          cursor: pointer;
          font-weight: 500;
          transition: all 0.3s ease;
        }

        .refresh-btn {
          background: #007bff;
          color: white;
        }

        .step-btn {
          background: #28a745;
          color: white;
        }

        .reset-btn {
          background: #6c757d;
          color: white;
        }

        .control-panel button:hover {
          transform: translateY(-2px);
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }

        .loading, .error {
          display: flex;
          justify-content: center;
          align-items: center;
          height: 400px;
          font-size: 18px;
        }

        @media (max-width: 768px) {
          .feature-explanation {
            grid-template-columns: 1fr;
          }
          
          .env-stats {
            flex-direction: column;
            gap: 10px;
          }
          
          .control-panel {
            flex-direction: column;
            align-items: center;
          }
        }
      `}</style>
    </div>
  );
};

export default RLEnvironmentVisualization;