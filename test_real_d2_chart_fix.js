#!/usr/bin/env node

/**
 * 測試 RealD2Chart 時間軸修復
 * 驗證真實數據模式下的時間範圍顯示
 */

console.log('🧪 RealD2Chart 時間軸修復測試');
console.log('=====================================');

// 模擬不同時間範圍的數據
const timeRanges = [
    { name: '2小時', minutes: 120, sampleInterval: 10 },
    { name: '6小時', minutes: 360, sampleInterval: 10 },
    { name: '12小時', minutes: 720, sampleInterval: 10 }
];

console.log('📊 預期數據點數量和時間軸範圍:');
console.log('採樣間隔: 10秒');
console.log('');

timeRanges.forEach(range => {
    const totalSeconds = range.minutes * 60;
    const expectedPoints = Math.floor(totalSeconds / range.sampleInterval);
    const maxXValue = (expectedPoints - 1) * range.sampleInterval;
    const maxXMinutes = maxXValue / 60;
    
    console.log(`${range.name.padEnd(8)}:`);
    console.log(`  - 總時間: ${totalSeconds} 秒 (${range.minutes} 分鐘)`);
    console.log(`  - 預期數據點: ${expectedPoints} 個`);
    console.log(`  - X軸範圍: 0-${maxXValue} 秒 (${maxXMinutes.toFixed(1)} 分鐘)`);
    console.log(`  - 修復前問題: 硬編碼 index * 10，但X軸範圍可能被截斷`);
    console.log(`  - 修復後效果: 動態使用 sampleIntervalSeconds = ${range.sampleInterval}`);
    console.log('');
});

console.log('🔧 修復內容:');
console.log('1. RealD2Chart 新增 sampleIntervalSeconds 參數');
console.log('2. 時間標籤計算: index * sampleIntervalSeconds');
console.log('3. 觸發區間計算: index * sampleIntervalSeconds');
console.log('4. EventD2Viewer 傳遞 selectedTimeRange.sampleIntervalSeconds');

console.log('');
console.log('🎯 關鍵差異:');
console.log('- PureD2Chart (模擬/歷史模式): 使用 5秒 間隔');
console.log('- RealD2Chart (真實數據模式): 使用 10秒 間隔');
console.log('- 兩者現在都支持動態時間範圍');

console.log('');
console.log('📝 測試步驟:');
console.log('1. 導航到 navbar > 換手事件 > d2 圖表');
console.log('2. 切換到"真實"模式 (使用 RealD2Chart)');
console.log('3. 測試不同時間範圍:');
timeRanges.forEach(range => {
    const totalSeconds = range.minutes * 60;
    const expectedPoints = Math.floor(totalSeconds / range.sampleInterval);
    const maxXValue = (expectedPoints - 1) * range.sampleInterval;
    console.log(`   - ${range.name}: X軸應顯示到 ${maxXValue} 秒`);
});

console.log('');
console.log('🔍 驗證方法:');
console.log('- 檢查 X軸 最大值是否正確顯示完整時間範圍');
console.log('- 確認 6小時 和 12小時 顯示不同的圖表');
console.log('- 觀察衛星距離曲線的完整軌道週期');

// 計算理論軌道週期數
const orbitalPeriod = 95.6; // 分鐘
console.log('');
console.log('🛰️ 理論軌道週期驗證:');
timeRanges.forEach(range => {
    const cycles = range.minutes / orbitalPeriod;
    console.log(`${range.name}: ${cycles.toFixed(2)} 個週期`);
});

console.log('');
console.log('⚠️ 注意事項:');
console.log('- 真實數據模式使用 RealD2Chart，採樣間隔 10秒');
console.log('- 模擬/歷史模式使用 PureD2Chart，採樣間隔 5秒');
console.log('- 兩種模式的時間軸刻度可能略有不同');

console.log('');
console.log('✅ 修復後預期:');
console.log('- 6小時模式: X軸顯示 0-21590秒 (約359.8分鐘)');
console.log('- 12小時模式: X軸顯示 0-43190秒 (約719.8分鐘)');
console.log('- 兩者顯示明顯不同的軌道週期數量');
