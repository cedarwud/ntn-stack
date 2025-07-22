#!/usr/bin/env node

/**
 * 測試 D2 圖表時間範圍修復
 * 驗證 6小時和12小時是否能正確顯示不同的週期數
 */

console.log('🧪 D2 圖表時間範圍修復測試');
console.log('=====================================');

// 模擬 LEO 衛星軌道週期
const LEO_ORBITAL_PERIOD_MINUTES = 95.6; // Starlink 典型軌道週期

// 測試不同時間範圍的週期數計算
const timeRanges = [
    { name: '5分鐘', minutes: 5 },
    { name: '15分鐘', minutes: 15 },
    { name: '30分鐘', minutes: 30 },
    { name: '1小時', minutes: 60 },
    { name: '2小時', minutes: 120 },
    { name: '6小時', minutes: 360 },
    { name: '12小時', minutes: 720 }
];

console.log('📊 理論週期數計算:');
console.log('軌道週期:', LEO_ORBITAL_PERIOD_MINUTES, '分鐘');
console.log('');

timeRanges.forEach(range => {
    const cycles = range.minutes / LEO_ORBITAL_PERIOD_MINUTES;
    const completeCycles = Math.floor(cycles);
    const partialCycle = (cycles - completeCycles).toFixed(2);
    
    console.log(`${range.name.padEnd(8)} (${range.minutes.toString().padStart(3)}分鐘): ${cycles.toFixed(2)} 週期 = ${completeCycles} 完整 + ${partialCycle} 部分`);
});

console.log('');
console.log('🔧 修復前的問題:');
console.log('- 6小時和12小時都只顯示 3小時(180分鐘) = 1.88 週期');
console.log('- 這導致兩者顯示相同的圖表');

console.log('');
console.log('✅ 修復後的預期結果:');
console.log('- 6小時應顯示: 3.77 週期');
console.log('- 12小時應顯示: 7.53 週期');
console.log('- 兩者應該顯示明顯不同的圖表');

console.log('');
console.log('🎯 修復內容:');
console.log('1. PureD2Chart 新增 historicalDurationMinutes 參數');
console.log('2. EventD2Viewer 傳遞 selectedTimeRange.durationMinutes');
console.log('3. fetchHistoricalD2Data 使用動態時間長度而非固定180分鐘');

console.log('');
console.log('📝 測試步驟:');
console.log('1. 啟動前端應用');
console.log('2. 導航到 navbar > 換手事件 > d2 圖表');
console.log('3. 切換到"真實"模式');
console.log('4. 測試不同時間範圍:');
timeRanges.slice(4).forEach(range => {
    const cycles = range.minutes / LEO_ORBITAL_PERIOD_MINUTES;
    console.log(`   - ${range.name}: 應顯示約 ${cycles.toFixed(1)} 個週期`);
});

console.log('');
console.log('🔍 驗證方法:');
console.log('- 觀察圖表中衛星距離曲線的波峰波谷數量');
console.log('- 6小時應比2小時多約2.5個週期');
console.log('- 12小時應比6小時多約3.8個週期');
