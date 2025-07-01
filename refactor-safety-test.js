#!/usr/bin/env node

/**
 * 階段二重構安全性測試腳本
 * 用於驗證 FullChartAnalysisDashboard 重構過程中功能正常
 */

const fs = require('fs');
const path = require('path');

console.log('🚀 階段二重構安全性測試腳本');
console.log('==========================================');

// 檢查關鍵檔案是否存在
const criticalFiles = [
  '/home/sat/ntn-stack/simworld/frontend/src/components/layout/FullChartAnalysisDashboard.tsx',
  '/home/sat/ntn-stack/simworld/frontend/src/components/layout/FullChartAnalysisDashboard.tsx.backup'
];

console.log('📁 檢查關鍵檔案...');
criticalFiles.forEach(file => {
  if (fs.existsSync(file)) {
    const stats = fs.statSync(file);
    const lines = fs.readFileSync(file, 'utf8').split('\n').length;
    console.log(`✅ ${path.basename(file)}: 存在 (${lines} 行)`);
  } else {
    console.log(`❌ ${path.basename(file)}: 不存在`);
  }
});

// 記錄當前狀態
const currentState = {
  timestamp: new Date().toISOString(),
  files: {}
};

criticalFiles.forEach(file => {
  if (fs.existsSync(file)) {
    const content = fs.readFileSync(file, 'utf8');
    currentState.files[path.basename(file)] = {
      lines: content.split('\n').length,
      size: content.length,
      checksum: require('crypto').createHash('md5').update(content).digest('hex')
    };
  }
});

// 保存狀態快照
fs.writeFileSync(
  '/home/sat/ntn-stack/refactor-state-snapshot.json', 
  JSON.stringify(currentState, null, 2)
);

console.log('📸 狀態快照已保存到 refactor-state-snapshot.json');

// 檢查重要的import和export
console.log('\n🔍 檢查重要的引用...');
const mainFile = '/home/sat/ntn-stack/simworld/frontend/src/components/layout/FullChartAnalysisDashboard.tsx';
if (fs.existsSync(mainFile)) {
  const content = fs.readFileSync(mainFile, 'utf8');
  
  // 檢查關鍵import
  const imports = [
    'GymnasiumRLMonitor',
    'OverviewTabContent',
    'IntegratedAnalysisTabContent',
    'EnhancedAlgorithmTabContent'
  ];
  
  imports.forEach(imp => {
    if (content.includes(imp)) {
      console.log(`✅ 發現引用: ${imp}`);
    } else {
      console.log(`⚠️  未發現引用: ${imp}`);
    }
  });
  
  // 檢查關鍵函數和變數
  const keyElements = [
    '_createMockData',
    'trainingMetrics',
    'rewardTrendData',
    'TabName'
  ];
  
  console.log('\n🔧 檢查關鍵元素...');
  keyElements.forEach(element => {
    if (content.includes(element)) {
      console.log(`✅ 發現元素: ${element}`);
    } else {
      console.log(`⚠️  未發現元素: ${element}`);
    }
  });
}

console.log('\n✅ 安全性檢查完成');
console.log('==========================================');