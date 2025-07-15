/**
 * RL 監控系統測試頁面
 * 用於驗證所有組件功能
 */

import React, { useState } from 'react';
import RLMonitoringPanel from '../RLMonitoringPanel';
import APITestPanel from './APITestPanel';
import { BUILD_INFO } from '../index';

const TestPage: React.FC = () => {
  const [activeView, setActiveView] = useState<'monitoring' | 'api-test'>('monitoring');

  return (
    <div style={{ 
      minHeight: '100vh', 
      background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)',
      padding: '20px'
    }}>
      {/* 頁面標題 */}
      <div style={{ 
        textAlign: 'center', 
        marginBottom: '30px',
        color: '#fff'
      }}>
        <h1 style={{ margin: '0 0 10px 0', fontSize: '2rem' }}>
          🤖 RL 監控系統測試頁面
        </h1>
        <p style={{ margin: 0, opacity: 0.7 }}>
          {BUILD_INFO.description} v{BUILD_INFO.version}
        </p>
      </div>

      {/* 視圖切換按鈕 */}
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        marginBottom: '20px',
        gap: '10px'
      }}>
        <button
          onClick={() => setActiveView('monitoring')}
          style={{
            padding: '12px 24px',
            background: activeView === 'monitoring' ? '#00d4ff' : 'rgba(255,255,255,0.1)',
            color: '#fff',
            border: '1px solid ' + (activeView === 'monitoring' ? '#00d4ff' : 'rgba(255,255,255,0.2)'),
            borderRadius: '6px',
            cursor: 'pointer',
            transition: 'all 0.2s ease'
          }}
        >
          📊 監控面板
        </button>
        
        <button
          onClick={() => setActiveView('api-test')}
          style={{
            padding: '12px 24px',
            background: activeView === 'api-test' ? '#00ffa3' : 'rgba(255,255,255,0.1)',
            color: '#fff',
            border: '1px solid ' + (activeView === 'api-test' ? '#00ffa3' : 'rgba(255,255,255,0.2)'),
            borderRadius: '6px',
            cursor: 'pointer',
            transition: 'all 0.2s ease'
          }}
        >
          🔧 API 測試
        </button>
      </div>

      {/* 主要內容區域 */}
      <div style={{ 
        maxWidth: '1200px', 
        margin: '0 auto'
      }}>
        {activeView === 'monitoring' && (
          <div>
            <h2 style={{ color: '#fff', textAlign: 'center', marginBottom: '20px' }}>
              RL 監控面板測試
            </h2>
            <RLMonitoringPanel 
              mode="standalone"
              height="800px"
              refreshInterval={3000}
              onDataUpdate={(data) => {
                console.log('📊 監控數據更新:', data);
              }}
              onError={(error) => {
                console.error('❌ 監控錯誤:', error);
              }}
            />
          </div>
        )}

        {activeView === 'api-test' && (
          <div>
            <h2 style={{ color: '#fff', textAlign: 'center', marginBottom: '20px' }}>
              API 端點測試
            </h2>
            <APITestPanel />
          </div>
        )}
      </div>

      {/* 底部信息 */}
      <div style={{ 
        marginTop: '40px',
        textAlign: 'center',
        color: 'rgba(255,255,255,0.5)',
        fontSize: '14px'
      }}>
        <div>構建時間: {new Date(BUILD_INFO.build_date).toLocaleString()}</div>
        <div style={{ marginTop: '10px' }}>
          支持功能: {BUILD_INFO.features.join(' • ')}
        </div>
      </div>
    </div>
  );
};

export default TestPage;