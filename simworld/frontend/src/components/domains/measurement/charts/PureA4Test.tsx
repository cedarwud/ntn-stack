/**
 * Pure A4 Chart Test Page
 * 測試新的純粹實現是否正常工作
 */

import React from 'react';
import PureA4Chart from './PureA4Chart';

export const PureA4Test: React.FC = () => {
  return (
    <div style={{ 
      padding: '20px', 
      backgroundColor: '#1a1a1a', 
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      gap: '20px'
    }}>
      <h1 style={{ color: 'white', marginBottom: '20px' }}>
        Pure A4 Chart Test - 完全對照 chart.html
      </h1>
      
      <div style={{ 
        backgroundColor: '#2a2a2a', 
        padding: '20px', 
        borderRadius: '8px',
        boxShadow: '0 4px 8px rgba(0,0,0,0.3)'
      }}>
        <PureA4Chart width={800} height={400} />
      </div>
      
      <div style={{ 
        color: 'white', 
        textAlign: 'center',
        maxWidth: '600px'
      }}>
        <h3>測試重點：</h3>
        <ul style={{ textAlign: 'left', lineHeight: '1.6' }}>
          <li>✅ 使用原生 Chart.js/auto</li>
          <li>✅ 使用 chart.html 的確切數據 (48個點)</li>
          <li>✅ 使用 chart.html 的確切配置 (tension: 0.3)</li>
          <li>✅ 拋棄 react-chartjs-2</li>
          <li>✅ 應該達到完全平滑的效果</li>
        </ul>
      </div>
    </div>
  );
};

export default PureA4Test;