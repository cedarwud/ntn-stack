/**
 * Pure A4 Chart Component
 * 完全對照 chart.html 的實現方式
 * 使用原生 Chart.js，拋棄 react-chartjs-2
 */

import React, { useEffect, useRef } from 'react';
import { Chart } from 'chart.js/auto';

// 完全對照 chart.html 的數據點
const dataPoints = [
  {x:1.48, y:-51.66}, {x:3.65, y:-51.93}, {x:5.82, y:-52.45}, {x:7.99, y:-53.18},
  {x:10.17, y:-54.13}, {x:12.34, y:-55.38}, {x:14.51, y:-56.90}, {x:16.68, y:-58.82},
  {x:18.66, y:-61.08}, {x:20.24, y:-63.51}, {x:21.32, y:-66.04}, {x:22.02, y:-68.77},
  {x:22.21, y:-71.47}, {x:22.81, y:-74.17}, {x:23.79, y:-76.41}, {x:25.40, y:-78.89},
  {x:27.35, y:-81.11}, {x:29.72, y:-83.25}, {x:31.40, y:-84.45}, {x:35.25, y:-86.75},
  {x:37.42, y:-87.36}, {x:39.59, y:-87.94}, {x:41.76, y:-88.32}, {x:43.94, y:-88.58},
  {x:46.11, y:-88.42}, {x:48.28, y:-88.26}, {x:50.45, y:-88.02}, {x:52.63, y:-87.73},
  {x:54.80, y:-87.32}, {x:56.97, y:-86.84}, {x:58.65, y:-86.46}, {x:61.51, y:-85.47},
  {x:63.69, y:-84.75}, {x:65.86, y:-83.84}, {x:67.83, y:-82.90}, {x:70.20, y:-81.45},
  {x:72.37, y:-79.85}, {x:74.38, y:-77.70}, {x:75.53, y:-75.79}, {x:76.13, y:-71.29},
  {x:77.31, y:-68.42}, {x:78.99, y:-65.89}, {x:81.06, y:-63.81}, {x:83.24, y:-62.15},
  {x:85.41, y:-60.98}, {x:87.58, y:-60.17}, {x:89.75, y:-59.67}, {x:91.23, y:-59.54}
];

interface PureA4ChartProps {
  width?: number;
  height?: number;
  threshold?: number;
  hysteresis?: number;
  showThresholdLines?: boolean;
  isDarkTheme?: boolean;
  onThemeToggle?: () => void;
}

export const PureA4Chart: React.FC<PureA4ChartProps> = ({
  width: _width = 800,
  height: _height = 400,
  threshold = -70,
  hysteresis = 3,
  showThresholdLines = true,
  isDarkTheme = true,
  onThemeToggle
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const chartRef = useRef<Chart | null>(null);

  // 主題配色方案
  const colors = {
    dark: {
      rsrpLine: '#007bff',           // 藍色 RSRP 線
      thresholdLine: '#E74C3C',      // 紅色主閾值線
      hysteresisLine: 'rgba(231, 76, 60, 0.6)', // 淺紅色遲滯線
      title: '#E74C3C',             // 紅色標題
      text: 'white',                // 白色文字
      grid: 'rgba(255, 255, 255, 0.1)', // 淺色網格
      background: 'transparent'      // 透明背景
    },
    light: {
      rsrpLine: '#0066CC',           // 參考 Event-A4.jpg 的藍色曲線
      thresholdLine: '#D32F2F',      // 參考 Event-A4.jpg 的紅色虛線
      hysteresisLine: '#D32F2F',     // 參考 Event-A4.jpg，改為實線紅色
      title: '#D32F2F',             // 紅色標題
      text: '#333333',              // 深灰色文字
      grid: 'rgba(0, 0, 0, 0.1)',   // 淺灰色網格
      background: 'white'           // 白色背景
    }
  };

  const currentTheme = isDarkTheme ? colors.dark : colors.light;

  // 初始化圖表
  useEffect(() => {
    if (!canvasRef.current) return;

    // 銷毀舊的圖表
    if (chartRef.current) {
      chartRef.current.destroy();
      chartRef.current = null;
    }

    const ctx = canvasRef.current.getContext('2d');
    if (!ctx) return;

    // 準備數據集
    const datasets = [
      {
        label: 'Neighbor Cell RSRP',
        data: dataPoints,
        borderColor: currentTheme.rsrpLine,
        backgroundColor: 'transparent',
        fill: false,
        tension: 0.3,
        pointRadius: 0
      }
    ];

    // 如果需要顯示閾值線，添加閾值線數據集
    if (showThresholdLines) {
      const thresholdData = dataPoints.map(point => ({ x: point.x, y: threshold }));
      const upperThresholdData = dataPoints.map(point => ({ x: point.x, y: threshold + hysteresis }));
      const lowerThresholdData = dataPoints.map(point => ({ x: point.x, y: threshold - hysteresis }));
      
      datasets.push(
        {
          label: 'a4-Threshold',
          data: thresholdData,
          borderColor: currentTheme.thresholdLine,
          backgroundColor: 'transparent',
          borderDash: [10, 5],
          borderWidth: 2,
          fill: false,
          tension: 0,
          pointRadius: 0
        },
        {
          label: 'Threshold + Hys',
          data: upperThresholdData,
          borderColor: currentTheme.hysteresisLine,
          backgroundColor: 'transparent',
          borderDash: [5, 3],
          borderWidth: 3,
          fill: false,
          tension: 0,
          pointRadius: 0
        },
        {
          label: 'Threshold - Hys',
          data: lowerThresholdData,
          borderColor: currentTheme.hysteresisLine,
          backgroundColor: 'transparent',
          borderDash: [5, 3],
          borderWidth: 3,
          fill: false,
          tension: 0,
          pointRadius: 0
        }
      );
    }

    try {
      chartRef.current = new Chart(ctx, {
        type: 'line',
        data: {
          datasets: datasets
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { 
              display: showThresholdLines,
              position: 'bottom',
              labels: {
                color: currentTheme.text,
                font: { size: 12 }
              }
            },
            title: {
              display: false
            }
          },
          scales: {
            x: {
              type: 'linear',
              title: { 
                display: true, 
                text: 'Time (s)',
                color: currentTheme.text,
                font: { size: 14 }
              },
              ticks: {
                color: currentTheme.text
              },
              grid: { color: currentTheme.grid },
              min: 0,
              max: 95
            },
            y: {
              title: { 
                display: true, 
                text: 'RSRP (dBm)',
                color: currentTheme.text,
                font: { size: 14 }
              },
              ticks: {
                color: currentTheme.text
              },
              grid: { color: currentTheme.grid },
              min: -100,
              max: -50,
              reverse: true
            }
          }
        }
      });
    } catch (error) {
      console.error('Chart creation failed:', error);
    }

    // 清理函數
    return () => {
      if (chartRef.current) {
        chartRef.current.destroy();
        chartRef.current = null;
      }
    };
  }, [isDarkTheme, threshold, hysteresis, showThresholdLines, currentTheme]); // 添加依賴項以便主題和參數變化時重建



  return (
    <div style={{ 
      width: '100%', 
      height: '100%', 
      minHeight: '300px', // 最小高度
      maxHeight: '80vh', // 最大高度為視窗的80%
      position: 'relative',
      backgroundColor: currentTheme.background,
      borderRadius: '8px' // 添加圓角
    }}>
      <canvas 
        ref={canvasRef}
        style={{ width: '100%', height: '100%' }}
      />
    </div>
  );
};

export default PureA4Chart;