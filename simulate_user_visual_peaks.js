/**
 * 模擬用戶在圖表上目視觀察到的峰值
 * 使用更寬鬆的標準來匹配人眼在圖表上的觀察
 */

const API_BASE = 'http://localhost:8080';

async function simulateUserVisualPeaks() {
    console.log('👁️ 模擬用戶目視觀察峰值...');
    
    try {
        // 使用與前端完全相同的配置
        const config = {
            scenario_name: `VisualPeaks_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            constellation: 'starlink',
            ue_position: { latitude: 25.0173, longitude: 121.4695, altitude: 100 },
            fixed_ref_position: { latitude: 25.0173, longitude: 121.4695, altitude: 100 },
            thresh1: -100,
            thresh2: -110,
            hysteresis: 3,
            duration_minutes: 720, // 12小時
            sample_interval_seconds: 10
        };
        
        // 獲取數據
        const precomputeResponse = await fetch(`${API_BASE}/api/satellite-data/d2/precompute`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });
        
        const precomputeData = await precomputeResponse.json();
        const measurementResponse = await fetch(
            `${API_BASE}/api/satellite-data/d2/measurements/${precomputeData.scenario_hash}?limit=10000`
        );
        
        const measurementData = await measurementResponse.json();
        const measurements = measurementData.measurements;
        
        console.log(`✅ 獲得 ${measurements.length} 個數據點進行分析`);
        
        // 提取距離數據
        const distances = measurements.map(m => m.satellite_distance / 1000); // km
        const times = measurements.map((m, i) => i * 10 / 3600); // 小時
        
        // 使用移動平均平滑數據（模擬用戶眼中的平滑曲線）
        const windowSize = 30; // 5分鐘移動平均
        const smoothedDistances = [];
        
        for (let i = windowSize; i < distances.length - windowSize; i++) {
            const sum = distances.slice(i - windowSize, i + windowSize + 1)
                .reduce((a, b) => a + b, 0);
            smoothedDistances.push(sum / (2 * windowSize + 1));
        }
        
        console.log(`📊 距離統計 (平滑後):`);
        const minDist = Math.min(...smoothedDistances);
        const maxDist = Math.max(...smoothedDistances);
        const avgDist = smoothedDistances.reduce((a, b) => a + b, 0) / smoothedDistances.length;
        
        console.log(`   最小: ${minDist.toFixed(1)} km`);
        console.log(`   最大: ${maxDist.toFixed(1)} km`);
        console.log(`   平均: ${avgDist.toFixed(1)} km`);
        console.log(`   變化幅度: ${((maxDist - minDist) / minDist * 100).toFixed(1)}%`);
        
        // 檢測顯著的局部極值 (用戶眼中的明顯峰值/谷值)
        const significantPeaks = [];
        const significantValleys = [];
        const minHeight = (maxDist - minDist) * 0.15; // 至少15%的變化才算顯著
        
        for (let i = 60; i < smoothedDistances.length - 60; i++) { // 更大的窗口
            let isPeak = true;
            let isValley = true;
            const currentDist = smoothedDistances[i];
            
            // 檢查60個點的範圍內是否為極值 (約10分鐘範圍)
            for (let j = i - 60; j <= i + 60; j++) {
                if (j !== i) {
                    if (smoothedDistances[j] >= currentDist - minHeight) {
                        isPeak = false;
                    }
                    if (smoothedDistances[j] <= currentDist + minHeight) {
                        isValley = false;
                    }
                }
            }
            
            const adjustedIndex = i + windowSize;
            const timeHours = adjustedIndex * 10 / 3600;
            
            if (isPeak && currentDist > avgDist + minHeight) {
                significantPeaks.push({
                    index: adjustedIndex,
                    timeHours: timeHours,
                    distance: currentDist,
                    timestamp: measurements[adjustedIndex].timestamp
                });
            }
            
            if (isValley && currentDist < avgDist - minHeight) {
                significantValleys.push({
                    index: adjustedIndex,
                    timeHours: timeHours,
                    distance: currentDist,
                    timestamp: measurements[adjustedIndex].timestamp
                });
            }
        }
        
        console.log(`\n🏔️ 顯著峰值 (用戶圖表上會明顯看到): ${significantPeaks.length} 個`);
        significantPeaks.forEach((peak, idx) => {
            const time = new Date(peak.timestamp);
            console.log(`   ${idx + 1}. ${time.toISOString().substr(11, 8)} (${peak.timeHours.toFixed(1)}h) - ${peak.distance.toFixed(1)}km`);
        });
        
        console.log(`\n🏔️ 顯著谷值: ${significantValleys.length} 個`);
        significantValleys.forEach((valley, idx) => {
            const time = new Date(valley.timestamp);
            console.log(`   ${idx + 1}. ${time.toISOString().substr(11, 8)} (${valley.timeHours.toFixed(1)}h) - ${valley.distance.toFixed(1)}km`);
        });
        
        // 合併峰值和谷值來計算總的"週期特徵"
        const allExtrema = [...significantPeaks, ...significantValleys]
            .sort((a, b) => a.timeHours - b.timeHours);
        
        console.log(`\n📈 總的極值點 (峰值+谷值): ${allExtrema.length} 個`);
        
        if (allExtrema.length >= 2) {
            const intervals = [];
            for (let i = 1; i < allExtrema.length; i++) {
                intervals.push((allExtrema[i].timeHours - allExtrema[i-1].timeHours) * 60); // 分鐘
            }
            const avgInterval = intervals.reduce((a, b) => a + b, 0) / intervals.length;
            
            console.log(`⏱️ 極值間隔分析:`);
            console.log(`   間隔序列: ${intervals.map(i => i.toFixed(1)).join(', ')} 分鐘`);
            console.log(`   平均間隔: ${avgInterval.toFixed(1)} 分鐘`);
            console.log(`   推算軌道週期: ${(avgInterval * 2).toFixed(1)} 分鐘`); // 峰值到峰值是兩個間隔
        }
        
        // 特別針對您的觀察：2個峰值
        console.log(`\n🎯 針對用戶觀察分析:`);
        console.log(`   用戶看到: 2個峰值`);
        console.log(`   系統檢測: ${significantPeaks.length}個顯著峰值`);
        
        if (significantPeaks.length === 2) {
            console.log(`   ✅ 完全匹配！用戶觀察準確`);
            const interval = (significantPeaks[1].timeHours - significantPeaks[0].timeHours) * 60;
            console.log(`   峰值間隔: ${interval.toFixed(1)} 分鐘`);
            console.log(`   軌道週期: ${interval.toFixed(1)} 分鐘`);
        } else {
            console.log(`   差異原因可能是:`);
            console.log(`   - 圖表視覺解析度不同`);
            console.log(`   - 峰值顯著性標準不同`);
            console.log(`   - 不同的衛星軌道週期`);
        }
        
        // 生成簡化的時間序列用於視覺化理解
        console.log(`\n📊 簡化時間序列 (每小時採樣):`);
        for (let hour = 0; hour < 12; hour++) {
            const index = Math.floor(hour * 360); // 每小時360個10秒間隔的點
            if (index < measurements.length) {
                const distance = measurements[index].satellite_distance / 1000;
                const time = new Date(measurements[index].timestamp);
                const marker = significantPeaks.some(p => Math.abs(p.timeHours - hour) < 0.5) ? '🏔️' : 
                             significantValleys.some(v => Math.abs(v.timeHours - hour) < 0.5) ? '🏞️' : '   ';
                console.log(`   ${hour.toString().padStart(2)}h: ${time.toISOString().substr(11, 8)} - ${distance.toFixed(1).padStart(8)}km ${marker}`);
            }
        }
        
    } catch (error) {
        console.error('❌ 分析失敗:', error.message);
    }
}

simulateUserVisualPeaks();