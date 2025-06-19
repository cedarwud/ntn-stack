import React, { useState, useEffect } from 'react';
import { runSystemTests, displayTestSummary, SystemTestResults } from './test-utils';

const Stage3QuickCheck: React.FC = () => {
  const [results, setResults] = useState<SystemTestResults | null>(null);
  const [isRunning, setIsRunning] = useState(false);

  const runQuickCheck = async () => {
    setIsRunning(true);
    
    try {
      const testResults = await runSystemTests(false); // 不包含性能測試的快速檢查
      setResults(testResults);
      displayTestSummary(testResults);
    } catch (error) {
      console.error('快速檢測失敗:', error);
    } finally {
      setIsRunning(false);
    }
  };

  useEffect(() => {
    // 自動執行快速檢測
    runQuickCheck();
  }, []);

  const getStatusColor = (success: boolean) => success ? '#10B981' : '#EF4444';
  const getStatusIcon = (success: boolean) => success ? '✅' : '❌';

  return (
    <div style={{ 
      padding: '20px', 
      fontFamily: 'monospace', 
      background: '#1a1a1a', 
      color: '#fff',
      borderRadius: '8px',
      margin: '20px'
    }}>
      <h2 style={{ color: '#60A5FA', marginBottom: '20px' }}>🚀 階段三快速檢測</h2>
      
      <div style={{ marginBottom: '20px' }}>
        <button 
          onClick={runQuickCheck} 
          disabled={isRunning}
          style={{
            background: isRunning ? '#6B7280' : '#3B82F6',
            color: 'white',
            border: 'none',
            padding: '10px 20px',
            borderRadius: '6px',
            cursor: isRunning ? 'not-allowed' : 'pointer',
            fontSize: '16px'
          }}
        >
          {isRunning ? '檢測中...' : '重新檢測'}
        </button>
      </div>

      {results && (
        <div>
          <div style={{ marginBottom: '20px' }}>
            <h3 style={{ color: '#F59E0B' }}>測試結果</h3>
            <div style={{ 
              background: '#374151', 
              padding: '15px', 
              borderRadius: '6px',
              marginBottom: '15px'
            }}>
              <div style={{ fontSize: '24px', fontWeight: 'bold' }}>
                總分: {results.overall_score}%
              </div>
              <div style={{ fontSize: '16px', opacity: 0.8 }}>
                通過: {results.passed_tests}/{results.total_tests} 項目
              </div>
            </div>
          </div>

          <div style={{ display: 'grid', gap: '10px' }}>
            <div style={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: '10px',
              padding: '10px',
              background: '#374151',
              borderRadius: '6px'
            }}>
              <span style={{ fontSize: '20px' }}>
                {getStatusIcon(results.netstack_core_sync.success)}
              </span>
              <span style={{ flex: 1 }}>NetStack 核心同步</span>
              <span style={{ 
                color: getStatusColor(results.netstack_core_sync.success),
                fontWeight: 'bold'
              }}>
                {results.netstack_core_sync.success ? '正常' : '異常'}
              </span>
            </div>

            <div style={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: '10px',
              padding: '10px',
              background: '#374151',
              borderRadius: '6px'
            }}>
              <span style={{ fontSize: '20px' }}>
                {getStatusIcon(results.simworld_satellites.success)}
              </span>
              <span style={{ flex: 1 }}>SimWorld 衛星數據</span>
              <span style={{ 
                color: getStatusColor(results.simworld_satellites.success),
                fontWeight: 'bold'
              }}>
                {results.simworld_satellites.success ? '正常' : '異常'}
              </span>
            </div>

            <div style={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: '10px',
              padding: '10px',
              background: '#374151',
              borderRadius: '6px'
            }}>
              <span style={{ fontSize: '20px' }}>
                {getStatusIcon(results.real_connections.success)}
              </span>
              <span style={{ flex: 1 }}>真實連接管理</span>
              <span style={{ 
                color: getStatusColor(results.real_connections.success),
                fontWeight: 'bold'
              }}>
                {results.real_connections.success ? '正常' : '異常'}
              </span>
            </div>

            <div style={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: '10px',
              padding: '10px',
              background: '#374151',
              borderRadius: '6px'
            }}>
              <span style={{ fontSize: '20px' }}>
                {getStatusIcon(results.ieee_algorithm.success)}
              </span>
              <span style={{ flex: 1 }}>IEEE INFOCOM 2024 演算法</span>
              <span style={{ 
                color: getStatusColor(results.ieee_algorithm.success),
                fontWeight: 'bold'
              }}>
                {results.ieee_algorithm.success ? '正常' : '異常'}
              </span>
            </div>
          </div>

          <div style={{ marginTop: '20px', fontSize: '14px', opacity: 0.7 }}>
            💡 提示: 檢查瀏覽器控制台以查看詳細的測試日誌
          </div>
        </div>
      )}

      {isRunning && (
        <div style={{ 
          textAlign: 'center', 
          padding: '40px',
          fontSize: '18px' 
        }}>
          <div>⏳ 正在執行快速檢測...</div>
          <div style={{ fontSize: '14px', marginTop: '10px', opacity: 0.7 }}>
            請稍候，正在測試各個系統組件
          </div>
        </div>
      )}
    </div>
  );
};

export default Stage3QuickCheck;