/**
 * 測試時間範圍漸進式衰退修復
 * 驗證不同時間範圍和採樣間隔的一致性
 */

const API_BASE = 'http://localhost:8080';

async function testTimeRangeFix() {
    console.log('🧪 測試時間範圍漸進式衰退修復...');
    
    const testScenarios = [
        {
            name: '2小時測試 - 7200秒間隔',
            duration_minutes: 120,
            sample_interval_seconds: 7200
        },
        {
            name: '12小時測試 - 7200秒間隔', 
            duration_minutes: 720,
            sample_interval_seconds: 7200
        },
        {
            name: '2小時測試 - 30秒間隔',
            duration_minutes: 120,
            sample_interval_seconds: 30
        }
    ];
    
    for (let i = 0; i < testScenarios.length; i++) {
        const scenario = testScenarios[i];
        console.log(`\n${i + 1}. ${scenario.name}`);
        
        try {
            // 唯一的場景名稱避免緩存衝突
            const uniqueId = Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            const scenarioName = `TimeRangeFix_${scenario.duration_minutes}min_${scenario.sample_interval_seconds}s_${uniqueId}`;
            
            // D2 預計算
            const precomputeResponse = await fetch(`${API_BASE}/api/satellite-data/d2/precompute`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    scenario_name: scenarioName,
                    constellation: 'starlink',
                    ue_position: {
                        latitude: 25.0330,
                        longitude: 121.5654,
                        altitude: 100
                    },
                    fixed_ref_position: {
                        latitude: 25.0330,
                        longitude: 121.5654,
                        altitude: 100
                    },
                    thresh1: -100,
                    thresh2: -110,
                    hysteresis: 3,
                    duration_minutes: scenario.duration_minutes,
                    sample_interval_seconds: scenario.sample_interval_seconds
                })
            });
            
            if (precomputeResponse.ok) {
                const precomputeData = await precomputeResponse.json();
                console.log(`   ✅ 預計算成功: ${precomputeData.measurements_generated} 個數據點`);
                
                // 獲取測量數據分析時間範圍
                const measurementResponse = await fetch(
                    `${API_BASE}/api/satellite-data/d2/measurements/${precomputeData.scenario_hash}?limit=1000`
                );
                
                if (measurementResponse.ok) {
                    const measurementData = await measurementResponse.json();
                    const measurements = measurementData.measurements;
                    
                    if (measurements.length >= 2) {
                        const firstTime = new Date(measurements[0].timestamp);
                        const lastTime = new Date(measurements[measurements.length - 1].timestamp);
                        const actualDurationMinutes = (lastTime - firstTime) / (1000 * 60);
                        const expectedDuration = scenario.duration_minutes;
                        
                        console.log(`   📊 時間範圍分析:`);
                        console.log(`      預期: ${expectedDuration} 分鐘`);
                        console.log(`      實際: ${actualDurationMinutes.toFixed(2)} 分鐘`);
                        console.log(`      差異: ${Math.abs(actualDurationMinutes - expectedDuration).toFixed(2)} 分鐘`);
                        console.log(`      準確性: ${((Math.min(actualDurationMinutes, expectedDuration) / Math.max(actualDurationMinutes, expectedDuration)) * 100).toFixed(1)}%`);
                        
                        // 檢查採樣間隔一致性
                        if (measurements.length >= 3) {
                            const interval1 = new Date(measurements[1].timestamp) - new Date(measurements[0].timestamp);
                            const interval2 = new Date(measurements[2].timestamp) - new Date(measurements[1].timestamp);
                            const avgInterval = (interval1 + interval2) / 2 / 1000; // 轉為秒
                            
                            console.log(`      預期間隔: ${scenario.sample_interval_seconds} 秒`);
                            console.log(`      實際間隔: ${avgInterval.toFixed(1)} 秒`);
                            console.log(`      間隔準確: ${Math.abs(avgInterval - scenario.sample_interval_seconds) < 5 ? '✅' : '❌'}`);
                        }
                        
                        const isTimeRangeCorrect = Math.abs(actualDurationMinutes - expectedDuration) < expectedDuration * 0.1; // 10% 容忍度
                        console.log(`   結果: ${isTimeRangeCorrect ? '✅ 時間範圍正確' : '❌ 時間範圍異常'}`);
                        
                    } else {
                        console.log('   ⚠️ 數據點不足，無法分析時間範圍');
                    }
                } else {
                    console.log('   ❌ 測量數據獲取失敗');
                }
            } else {
                console.log('   ❌ 預計算失敗:', await precomputeResponse.text());
            }
            
        } catch (error) {
            console.error(`   ❌ 測試失敗:`, error.message);
        }
        
        // 等待1秒避免請求過於頻繁
        await new Promise(resolve => setTimeout(resolve, 1000));
    }
    
    console.log('\n🎉 時間範圍測試完成！');
}

// 執行測試
testTimeRangeFix();