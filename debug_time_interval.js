/**
 * 調試前端時間間隔假設問題
 */

const API_BASE = 'http://localhost:8080';

async function debugTimeInterval() {
    console.log('🔍 調試前端時間間隔假設問題...');
    
    const uniqueId = Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    const scenarioName = `TimeIntervalDebug_${uniqueId}`;
    
    try {
        // 測試與前端相同的配置
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
                sample_interval_seconds: 10 // 前端設定
            })
        });
        
        if (precomputeResponse.ok) {
            const precomputeData = await precomputeResponse.json();
            console.log(`✅ 預計算成功: ${precomputeData.measurements_generated} 個數據點`);
            
            const measurementResponse = await fetch(
                `${API_BASE}/api/satellite-data/d2/measurements/${precomputeData.scenario_hash}?limit=20`
            );
            
            if (measurementResponse.ok) {
                const measurementData = await measurementResponse.json();
                const measurements = measurementData.measurements;
                
                console.log(`\n📊 時間間隔分析 (前${measurements.length}個數據點):`);
                
                for (let i = 0; i < Math.min(10, measurements.length); i++) {
                    const m = measurements[i];
                    const time = new Date(m.timestamp);
                    
                    // 計算與第一個數據點的時間差
                    if (i === 0) {
                        console.log(`${i+1}. ${time.toISOString()} (基準時間) - 距離: ${(m.satellite_distance/1000).toFixed(1)}km`);
                    } else {
                        const firstTime = new Date(measurements[0].timestamp);
                        const intervalSeconds = (time.getTime() - firstTime.getTime()) / 1000;
                        const expectedInterval = i * 10; // 前端假設的間隔
                        const difference = intervalSeconds - expectedInterval;
                        
                        console.log(`${i+1}. ${time.toISOString()} (+${intervalSeconds}s, 預期+${expectedInterval}s, 差異${difference}s) - 距離: ${(m.satellite_distance/1000).toFixed(1)}km`);
                    }
                }
                
                // 檢查實際採樣間隔
                if (measurements.length >= 2) {
                    const actualIntervals = [];
                    for (let i = 1; i < Math.min(5, measurements.length); i++) {
                        const current = new Date(measurements[i].timestamp);
                        const previous = new Date(measurements[i-1].timestamp);
                        const interval = (current.getTime() - previous.getTime()) / 1000;
                        actualIntervals.push(interval);
                    }
                    
                    const avgInterval = actualIntervals.reduce((a, b) => a + b, 0) / actualIntervals.length;
                    console.log(`\n⏱️ 實際採樣間隔分析:`);
                    console.log(`   間隔序列: ${actualIntervals.join(', ')} 秒`);
                    console.log(`   平均間隔: ${avgInterval.toFixed(1)} 秒`);
                    console.log(`   前端假設: 10 秒`);
                    console.log(`   差異: ${Math.abs(avgInterval - 10).toFixed(1)} 秒`);
                    
                    if (Math.abs(avgInterval - 10) > 1) {
                        console.log(`   ⚠️ 警告：實際間隔與前端假設不符！這會導致時間軸錯誤`);
                    } else {
                        console.log(`   ✅ 間隔符合前端假設`);
                    }
                }
                
            } else {
                console.log('❌ 測量數據獲取失敗');
            }
        } else {
            console.log('❌ 預計算失敗');
        }
        
    } catch (error) {
        console.error('❌ 調試失敗:', error.message);
    }
}

debugTimeInterval();