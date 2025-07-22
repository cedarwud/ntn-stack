/**
 * 深度分析2小時Starlink距離曲線模式
 * 找出為什麼只檢測到1個峰值的原因
 */

const API_BASE = 'http://localhost:8080';

async function analyze2HourCyclePattern() {
    console.log('📈 深度分析2小時Starlink距離曲線模式...');
    
    const uniqueId = Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    const scenarioName = `CyclePattern_2h_${uniqueId}`;
    
    try {
        // 生成2小時Starlink數據
        const precomputeResponse = await fetch(`${API_BASE}/api/satellite-data/d2/precompute`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                scenario_name: scenarioName,
                constellation: 'starlink',
                ue_position: { latitude: 25.0173, longitude: 121.4695, altitude: 100 },
                fixed_ref_position: { latitude: 25.0173, longitude: 121.4695, altitude: 100 },
                thresh1: -100,
                thresh2: -110,
                hysteresis: 3,
                duration_minutes: 120,
                sample_interval_seconds: 10
            })
        });
        
        if (!precomputeResponse.ok) {
            console.log('❌ 預計算失敗');
            return;
        }
        
        const precomputeData = await precomputeResponse.json();
        console.log(`✅ 預計算成功: ${precomputeData.measurements_generated} 個數據點`);
        
        const measurementResponse = await fetch(
            `${API_BASE}/api/satellite-data/d2/measurements/${precomputeData.scenario_hash}?limit=1000`
        );
        
        if (!measurementResponse.ok) {
            console.log('❌ 測量數據獲取失敗');
            return;
        }
        
        const measurementData = await measurementResponse.json();
        const measurements = measurementData.measurements;
        
        console.log(`📊 獲得 ${measurements.length} 個數據點`);
        
        // 提取距離數據
        const distances = measurements.map(m => m.satellite_distance / 1000); // 轉為km
        const timePoints = measurements.map((m, i) => i * 10 / 60); // 轉為分鐘
        
        console.log(`\n📏 距離統計:`);
        const minDist = Math.min(...distances);
        const maxDist = Math.max(...distances);
        const avgDist = distances.reduce((a, b) => a + b, 0) / distances.length;
        console.log(`   最小距離: ${minDist.toFixed(1)} km`);
        console.log(`   最大距離: ${maxDist.toFixed(1)} km`);
        console.log(`   平均距離: ${avgDist.toFixed(1)} km`);
        console.log(`   變化幅度: ${((maxDist - minDist) / minDist * 100).toFixed(1)}%`);
        
        // 更精細的極值檢測（使用滑動窗口）
        const windowSize = 5; // 5個數據點的窗口
        const peaks = [];
        const valleys = [];
        
        for (let i = windowSize; i < distances.length - windowSize; i++) {
            let isPeak = true;
            let isValley = true;
            
            // 檢查是否為局部最大值
            for (let j = i - windowSize; j <= i + windowSize; j++) {
                if (j !== i && distances[j] >= distances[i]) {
                    isPeak = false;
                }
                if (j !== i && distances[j] <= distances[i]) {
                    isValley = false;
                }
            }
            
            if (isPeak) {
                peaks.push({
                    index: i,
                    timeMinutes: timePoints[i],
                    distance: distances[i],
                    timestamp: measurements[i].timestamp
                });
            }
            
            if (isValley) {
                valleys.push({
                    index: i,
                    timeMinutes: timePoints[i], 
                    distance: distances[i],
                    timestamp: measurements[i].timestamp
                });
            }
        }
        
        console.log(`\n🏔️ 極值檢測結果 (滑動窗口法):`);
        console.log(`   峰值數量: ${peaks.length}`);
        console.log(`   谷值數量: ${valleys.length}`);
        
        // 列出所有極值
        if (peaks.length > 0) {
            console.log(`\n📍 峰值列表:`);
            peaks.forEach((peak, idx) => {
                const time = new Date(peak.timestamp);
                console.log(`   ${idx + 1}. ${time.toISOString().substr(11, 8)} (${peak.timeMinutes.toFixed(1)}min) - ${peak.distance.toFixed(1)}km`);
            });
        }
        
        if (valleys.length > 0) {
            console.log(`\n📍 谷值列表:`);
            valleys.forEach((valley, idx) => {
                const time = new Date(valley.timestamp);
                console.log(`   ${idx + 1}. ${time.toISOString().substr(11, 8)} (${valley.timeMinutes.toFixed(1)}min) - ${valley.distance.toFixed(1)}km`);
            });
        }
        
        // 分析距離變化趨勢
        console.log(`\n📈 距離變化趨勢分析:`);
        
        // 計算移動平均來平滑曲線
        const movingAvgWindow = 6; // 1分鐘移動平均
        const movingAvg = [];
        for (let i = movingAvgWindow; i < distances.length - movingAvgWindow; i++) {
            const sum = distances.slice(i - movingAvgWindow, i + movingAvgWindow + 1)
                .reduce((a, b) => a + b, 0);
            movingAvg.push(sum / (2 * movingAvgWindow + 1));
        }
        
        // 在移動平均上重新檢測週期
        const smoothedPeaks = [];
        const smoothedValleys = [];
        
        for (let i = 1; i < movingAvg.length - 1; i++) {
            if (movingAvg[i] > movingAvg[i-1] && movingAvg[i] > movingAvg[i+1]) {
                smoothedPeaks.push({
                    index: i + movingAvgWindow,
                    timeMinutes: timePoints[i + movingAvgWindow],
                    distance: movingAvg[i]
                });
            }
            if (movingAvg[i] < movingAvg[i-1] && movingAvg[i] < movingAvg[i+1]) {
                smoothedValleys.push({
                    index: i + movingAvgWindow,
                    timeMinutes: timePoints[i + movingAvgWindow],
                    distance: movingAvg[i]
                });
            }
        }
        
        console.log(`   移動平均後峰值: ${smoothedPeaks.length}`);
        console.log(`   移動平均後谷值: ${smoothedValleys.length}`);
        
        // 顯示數據樣本以分析模式
        console.log(`\n📝 距離數據樣本 (每10分鐘):`);
        for (let i = 0; i < Math.min(measurements.length, 121); i += 60) { // 每10分鐘採樣
            const m = measurements[i];
            const time = new Date(m.timestamp);
            const elapsedMinutes = i * 10 / 60;
            console.log(`   ${elapsedMinutes.toFixed(0)}min: ${time.toISOString().substr(11, 8)} - ${(m.satellite_distance/1000).toFixed(1)}km`);
        }
        
        // 判斷數據模式
        console.log(`\n💡 模式分析:`);
        
        const trend = distances[distances.length - 1] - distances[0];
        if (Math.abs(trend) > maxDist * 0.5) {
            if (trend > 0) {
                console.log(`   主要趨勢: 衛星遠離 (增加 ${(trend/1000).toFixed(1)}km)`);
            } else {
                console.log(`   主要趨勢: 衛星接近 (減少 ${(-trend/1000).toFixed(1)}km)`);
            }
            console.log(`   這可能解釋為什麼2小時內看不到完整的軌道週期`);
        } else {
            console.log(`   主要趨勢: 相對穩定 (變化 ${(trend/1000).toFixed(1)}km)`);
        }
        
        // 檢查是否為軌道週期的一部分
        const expectedPeriod = 95.6; // 分鐘
        const observationPeriod = 120; // 分鐘
        const theoreticalCycles = observationPeriod / expectedPeriod;
        
        console.log(`   理論週期數: ${theoreticalCycles.toFixed(2)}`);
        console.log(`   實際檢測: ${peaks.length} 峰值, ${valleys.length} 谷值`);
        
        if (peaks.length < theoreticalCycles) {
            console.log(`   ⚠️ 可能原因: 觀測到的是軌道週期的一部分，而非完整週期`);
            console.log(`   🛰️ 解釋: 衛星在2小時內主要表現為接近或遠離的單調趨勢`);
        }
        
    } catch (error) {
        console.error('❌ 分析失敗:', error.message);
    }
}

analyze2HourCyclePattern();