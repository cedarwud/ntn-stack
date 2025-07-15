/**
 * API 測試面板組件
 * 用於驗證 API 端點整合狀況
 */

import React, { useState } from 'react';
import { apiTester, APITestSummary } from '../utils/apiTester';

const APITestPanel: React.FC = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [testResults, setTestResults] = useState<APITestSummary | null>(null);
  const [healthStatus, setHealthStatus] = useState<any>(null);

  const runAPITests = async () => {
    setIsLoading(true);
    try {
      console.log('🚀 開始 API 整合測試...');
      
      // 測試所有 API 端點
      const summary = await apiTester.testAll();
      setTestResults(summary);
      
      // 輸出格式化結果到控制台
      console.log(apiTester.formatResults(summary));
      
      // 測試系統健康檢查
      const health = await apiTester.healthCheck();
      setHealthStatus(health);
      
      console.log('🏥 系統健康檢查結果:', health);
      
    } catch (error) {
      console.error('❌ API 測試失敗:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const testPhase3APIs = async () => {
    console.log('🔬 測試 Phase 3 API...');
    try {
      const phase3Results = await apiTester.testPhase3();
      console.log('Phase 3 API 測試結果:', phase3Results);
    } catch (error) {
      console.error('Phase 3 API 測試失敗:', error);
    }
  };

  return (
    <div style={{ 
      padding: '20px', 
      background: '#1a1a2e', 
      color: '#fff', 
      borderRadius: '8px',
      maxWidth: '800px',
      margin: '20px auto' 
    }}>
      <h2>🔧 RL 監控 API 測試面板</h2>
      <p>用於驗證所有 API 端點的連通性和響應狀況</p>
      
      <div style={{ marginBottom: '20px' }}>
        <button
          onClick={runAPITests}
          disabled={isLoading}
          style={{
            padding: '12px 24px',
            background: isLoading ? '#666' : '#00d4ff',
            color: '#fff',
            border: 'none',
            borderRadius: '6px',
            cursor: isLoading ? 'not-allowed' : 'pointer',
            marginRight: '10px'
          }}
        >
          {isLoading ? '🔄 測試中...' : '🚀 運行完整 API 測試'}
        </button>
        
        <button
          onClick={testPhase3APIs}
          style={{
            padding: '12px 24px',
            background: '#00ffa3',
            color: '#fff',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer'
          }}
        >
          🔬 測試 Phase 3 API
        </button>
      </div>

      {/* 健康檢查結果 */}
      {healthStatus && (
        <div style={{ 
          marginBottom: '20px', 
          padding: '15px', 
          background: 'rgba(255,255,255,0.1)',
          borderRadius: '6px'
        }}>
          <h3>🏥 系統健康狀態</h3>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span>總體狀態:</span>
            <span style={{ 
              color: healthStatus.overall === 'healthy' ? '#00ffa3' : 
                     healthStatus.overall === 'degraded' ? '#ffa500' : '#ff6b6b'
            }}>
              {healthStatus.overall === 'healthy' ? '🟢' : 
               healthStatus.overall === 'degraded' ? '🟡' : '🔴'}
              {healthStatus.overall.toUpperCase()}
            </span>
          </div>
          
          <div style={{ marginTop: '10px' }}>
            <h4>服務狀態:</h4>
            {Object.entries(healthStatus.services).map(([service, status]) => (
              <div key={service} style={{ marginLeft: '10px' }}>
                <span>{status === 'up' ? '🟢' : '🔴'}</span>
                <span style={{ marginLeft: '5px' }}>{service}: {status as string}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* API 測試結果 */}
      {testResults && (
        <div style={{ 
          padding: '15px', 
          background: 'rgba(255,255,255,0.1)',
          borderRadius: '6px'
        }}>
          <h3>📊 API 測試結果</h3>
          
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(4, 1fr)', 
            gap: '15px',
            marginBottom: '20px'
          }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#00ffa3' }}>
                {testResults.totalEndpoints}
              </div>
              <div style={{ fontSize: '12px', opacity: 0.7 }}>總端點數</div>
            </div>
            
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#00ffa3' }}>
                {testResults.successCount}
              </div>
              <div style={{ fontSize: '12px', opacity: 0.7 }}>成功</div>
            </div>
            
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#ff6b6b' }}>
                {testResults.errorCount}
              </div>
              <div style={{ fontSize: '12px', opacity: 0.7 }}>失敗</div>
            </div>
            
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#00d4ff' }}>
                {testResults.successRate.toFixed(1)}%
              </div>
              <div style={{ fontSize: '12px', opacity: 0.7 }}>成功率</div>
            </div>
          </div>

          <div style={{ 
            marginBottom: '15px',
            textAlign: 'center',
            fontSize: '14px',
            opacity: 0.8
          }}>
            平均響應時間: {testResults.avgResponseTime.toFixed(2)}ms
          </div>

          {/* 詳細結果列表 */}
          <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
            {testResults.results.map((result, index) => (
              <div 
                key={index}
                style={{ 
                  display: 'flex', 
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '8px 12px',
                  marginBottom: '5px',
                  background: result.status === 'success' 
                    ? 'rgba(0, 255, 163, 0.1)' 
                    : 'rgba(255, 107, 107, 0.1)',
                  borderRadius: '4px',
                  fontSize: '14px'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span>{result.status === 'success' ? '✅' : '❌'}</span>
                  <span>{result.endpoint}</span>
                </div>
                
                <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
                  <span style={{ opacity: 0.7 }}>
                    {result.responseTime.toFixed(2)}ms
                  </span>
                  {result.error && (
                    <span style={{ 
                      color: '#ff6b6b', 
                      fontSize: '12px',
                      maxWidth: '200px',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis'
                    }}>
                      {result.error}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div style={{ 
        marginTop: '20px', 
        fontSize: '12px', 
        opacity: 0.6,
        textAlign: 'center'
      }}>
        💡 打開瀏覽器控制台查看詳細的測試日誌和格式化結果
      </div>
    </div>
  );
};

export default APITestPanel;