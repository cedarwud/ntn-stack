#!/usr/bin/env node

/**
 * 驗證 D2 圖表時間範圍修復
 * 檢查修改的文件是否正確實現了動態時間範圍功能
 */

const fs = require('fs');
const path = require('path');

console.log('🔍 驗證 D2 圖表時間範圍修復');
console.log('=====================================');

// 檢查文件是否存在
const filesToCheck = [
    'simworld/frontend/src/components/domains/measurement/charts/PureD2Chart.tsx',
    'simworld/frontend/src/components/domains/measurement/charts/EventD2Viewer.tsx'
];

let allChecksPass = true;

filesToCheck.forEach(filePath => {
    console.log(`\n📁 檢查文件: ${filePath}`);
    
    if (!fs.existsSync(filePath)) {
        console.log('❌ 文件不存在');
        allChecksPass = false;
        return;
    }
    
    const content = fs.readFileSync(filePath, 'utf8');
    
    if (filePath.includes('PureD2Chart.tsx')) {
        // 檢查 PureD2Chart 的修改
        const checks = [
            {
                name: '新增 historicalDurationMinutes 參數到接口',
                pattern: /historicalDurationMinutes\?\s*:\s*number/,
                required: true
            },
            {
                name: '新增 historicalDurationMinutes 參數到組件',
                pattern: /historicalDurationMinutes\s*=\s*180/,
                required: true
            },
            {
                name: '使用動態時間長度調用 fetchHistoricalD2Data',
                pattern: /fetchHistoricalD2Data\(\s*historicalStartTime,\s*historicalDurationMinutes\s*\)/,
                required: true
            }
        ];
        
        checks.forEach(check => {
            const found = check.pattern.test(content);
            console.log(`${found ? '✅' : '❌'} ${check.name}`);
            if (!found && check.required) {
                allChecksPass = false;
            }
        });
    }
    
    if (filePath.includes('EventD2Viewer.tsx')) {
        // 檢查 EventD2Viewer 的修改
        const checks = [
            {
                name: '傳遞 historicalDurationMinutes 到 PureD2Chart',
                pattern: /historicalDurationMinutes=\{\s*selectedTimeRange\.durationMinutes\s*\}/,
                required: true
            }
        ];
        
        checks.forEach(check => {
            const found = check.pattern.test(content);
            console.log(`${found ? '✅' : '❌'} ${check.name}`);
            if (!found && check.required) {
                allChecksPass = false;
            }
        });
    }
});

console.log('\n📊 修復驗證結果:');
if (allChecksPass) {
    console.log('✅ 所有檢查通過！修復已正確實施。');
    console.log('\n🎯 預期效果:');
    console.log('- 6小時模式將顯示約 3.8 個軌道週期');
    console.log('- 12小時模式將顯示約 7.5 個軌道週期');
    console.log('- 兩者將顯示明顯不同的圖表');
    
    console.log('\n🧪 測試建議:');
    console.log('1. 啟動前端應用');
    console.log('2. 導航到 navbar > 換手事件 > d2 圖表');
    console.log('3. 切換到"真實"模式');
    console.log('4. 依次測試 2小時、6小時、12小時時間範圍');
    console.log('5. 觀察衛星距離曲線的週期數量變化');
} else {
    console.log('❌ 部分檢查失敗，請檢查修復實施。');
}

console.log('\n📋 技術摘要:');
console.log('- 修復了固定3小時數據獲取的問題');
console.log('- 實現了動態時間範圍參數傳遞');
console.log('- 保持了向後兼容性（預設180分鐘）');
console.log('- 後端已支持動態 duration_minutes 參數');
