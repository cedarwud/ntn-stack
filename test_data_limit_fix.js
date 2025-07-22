#!/usr/bin/env node

/**
 * 測試數據點限制修復
 * 驗證不同時間範圍的數據點數量限制計算
 */

console.log('🧪 數據點限制修復測試');
console.log('=====================================');

// 模擬不同時間範圍的配置
const timeRanges = [
    { name: '2小時', minutes: 120, sampleInterval: 10 },
    { name: '6小時', minutes: 360, sampleInterval: 10 },
    { name: '12小時', minutes: 720, sampleInterval: 10 }
];

console.log('📊 數據點數量和限制計算:');
console.log('採樣間隔: 10秒');
console.log('');

timeRanges.forEach(range => {
    const totalSeconds = range.minutes * 60;
    const expectedDataPoints = Math.ceil(totalSeconds / range.sampleInterval);
    const limit = Math.max(1000, expectedDataPoints + 100); // 修復後的邏輯
    const maxTimeSeconds = (limit - 1) * range.sampleInterval;
    const maxTimeMinutes = maxTimeSeconds / 60;
    
    console.log(`${range.name.padEnd(8)}:`);
    console.log(`  - 總時間: ${totalSeconds} 秒 (${range.minutes} 分鐘)`);
    console.log(`  - 預期數據點: ${expectedDataPoints} 個`);
    console.log(`  - 修復前限制: 1000 個 (固定)`);
    console.log(`  - 修復後限制: ${limit} 個 (動態)`);
    console.log(`  - 實際可顯示時間: ${maxTimeSeconds} 秒 (${maxTimeMinutes.toFixed(1)} 分鐘)`);
    
    if (expectedDataPoints > 1000) {
        console.log(`  - ⚠️ 修復前問題: 數據被截斷到 ${(1000 * range.sampleInterval / 60).toFixed(1)} 分鐘`);
        console.log(`  - ✅ 修復後效果: 完整顯示 ${range.minutes} 分鐘數據`);
    } else {
        console.log(`  - ✅ 無截斷問題: 數據點數量在限制內`);
    }
    console.log('');
});

console.log('🔧 修復內容:');
console.log('1. unifiedD2DataService.getD2Data() 動態計算數據點限制');
console.log('2. 根據 duration_minutes 和 sample_interval_seconds 計算預期數據點數');
console.log('3. 設定限制為 Math.max(1000, expectedDataPoints + 100)');
console.log('4. 傳遞動態限制給 getCachedD2Measurements()');

console.log('');
console.log('🎯 關鍵修復邏輯:');
console.log('```typescript');
console.log('const totalSeconds = config.duration_minutes * 60');
console.log('const expectedDataPoints = Math.ceil(totalSeconds / config.sample_interval_seconds)');
console.log('const limit = Math.max(1000, expectedDataPoints + 100)');
console.log('const measurements = await this.getCachedD2Measurements(hash, limit)');
console.log('```');

console.log('');
console.log('📝 修復前後對比:');
console.log('| 時間範圍 | 預期數據點 | 修復前限制 | 修復後限制 | 顯示時間 |');
console.log('|---------|-----------|-----------|-----------|----------|');
timeRanges.forEach(range => {
    const totalSeconds = range.minutes * 60;
    const expectedDataPoints = Math.ceil(totalSeconds / range.sampleInterval);
    const oldLimit = 1000;
    const newLimit = Math.max(1000, expectedDataPoints + 100);
    const oldMaxTime = (oldLimit * range.sampleInterval / 60).toFixed(1);
    const newMaxTime = range.minutes;
    
    console.log(`| ${range.name.padEnd(7)} | ${expectedDataPoints.toString().padStart(9)} | ${oldLimit.toString().padStart(9)} | ${newLimit.toString().padStart(9)} | ${range.minutes}分鐘 |`);
});

console.log('');
console.log('🔍 驗證方法:');
console.log('1. 導航到 navbar > 換手事件 > d2 圖表');
console.log('2. 切換到"真實"模式');
console.log('3. 測試不同時間範圍，檢查瀏覽器控制台日誌:');
console.log('   - 查找 "計算數據點限制" 日誌');
console.log('   - 確認 "成功載入 X 個數據點" 的數量');
console.log('4. 觀察 X軸 時間範圍是否正確顯示完整時間');

console.log('');
console.log('📊 預期結果:');
timeRanges.forEach(range => {
    const expectedDataPoints = Math.ceil(range.minutes * 60 / range.sampleInterval);
    const maxTimeSeconds = (expectedDataPoints - 1) * range.sampleInterval;
    console.log(`- ${range.name}: 載入約 ${expectedDataPoints} 個數據點，X軸顯示到 ${maxTimeSeconds} 秒`);
});

console.log('');
console.log('✅ 修復後，6小時和12小時應該顯示明顯不同的圖表！');
