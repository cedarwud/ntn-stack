#!/usr/bin/env node

/**
 * 測試 X 軸範圍修復
 * 驗證不同時間範圍的 X 軸最大值計算
 */

console.log('🧪 X 軸範圍修復測試');
console.log('=====================================');

// 模擬不同時間範圍的數據點數量
const timeRanges = [
    { name: '2小時', minutes: 120, expectedPoints: 120 * 60 / 5 }, // 5秒間隔
    { name: '6小時', minutes: 360, expectedPoints: 360 * 60 / 5 },
    { name: '12小時', minutes: 720, expectedPoints: 720 * 60 / 5 }
];

console.log('📊 預期數據點數量和 X 軸範圍:');
console.log('採樣間隔: 5秒');
console.log('');

timeRanges.forEach(range => {
    const maxXValue = (range.expectedPoints - 1) * 5; // X軸最大值（秒）
    const maxXMinutes = maxXValue / 60; // 轉換為分鐘
    
    console.log(`${range.name.padEnd(8)}:`);
    console.log(`  - 預期數據點: ${range.expectedPoints.toFixed(0)} 個`);
    console.log(`  - X軸最大值: ${maxXValue} 秒 (${maxXMinutes.toFixed(1)} 分鐘)`);
    console.log(`  - 修復前問題: 固定顯示到 95 秒`);
    console.log(`  - 修復後效果: 顯示到 ${maxXValue} 秒`);
    console.log('');
});

console.log('🔧 修復內容:');
console.log('1. 歷史數據 X 軸從 index 改為 index * 5（實際時間秒數）');
console.log('2. X 軸最大值從固定 95 秒改為動態計算');
console.log('3. 歷史數據類型使用 (totalCount - 1) * 5 計算最大值');

console.log('');
console.log('📝 預期結果:');
console.log('- 2小時: X軸顯示 0-7195 秒 (約119.9分鐘)');
console.log('- 6小時: X軸顯示 0-21595 秒 (約359.9分鐘)');
console.log('- 12小時: X軸顯示 0-43195 秒 (約719.9分鐘)');

console.log('');
console.log('🎯 驗證方法:');
console.log('1. 切換到真實數據模式');
console.log('2. 選擇不同時間範圍');
console.log('3. 檢查 X 軸最大值是否正確顯示完整時間範圍');
console.log('4. 確認可以看到完整的軌道週期數量');

// 計算理論軌道週期數
const orbitalPeriod = 95.6; // 分鐘
console.log('');
console.log('🛰️ 理論軌道週期驗證:');
timeRanges.forEach(range => {
    const cycles = range.minutes / orbitalPeriod;
    console.log(`${range.name}: ${cycles.toFixed(2)} 個週期`);
});

console.log('');
console.log('✅ 修復後應該能看到:');
console.log('- 6小時: 約3.8個完整的衛星軌道週期');
console.log('- 12小時: 約7.5個完整的衛星軌道週期');
console.log('- 兩者顯示明顯不同的圖表模式');
