/**
 * 壓力測試：模擬用戶操作以驗證不再出現漸進式時間範圍衰退
 * 模擬多次切換星座和時間範圍，確保每次都能獲得正確的時間區間
 */

const API_BASE = 'http://localhost:8080';

async function stressTestProgressiveDegradation() {
    console.log('🚀 開始壓力測試：模擬漸進式時間範圍衰退場景...');
    
    const operations = [
        { constellation: 'starlink', duration_minutes: 720, sample_interval_seconds: 7200, name: 'Starlink 12小時' },
        { constellation: 'starlink', duration_minutes: 120, sample_interval_seconds: 7200, name: 'Starlink 2小時' },
        { constellation: 'gps', duration_minutes: 720, sample_interval_seconds: 7200, name: 'GPS 12小時' },
        { constellation: 'gps', duration_minutes: 120, sample_interval_seconds: 7200, name: 'GPS 2小時' },
        { constellation: 'oneweb', duration_minutes: 720, sample_interval_seconds: 7200, name: 'OneWeb 12小時' },
        { constellation: 'oneweb', duration_minutes: 120, sample_interval_seconds: 7200, name: 'OneWeb 2小時' },
        { constellation: 'starlink', duration_minutes: 720, sample_interval_seconds: 7200, name: 'Starlink 12小時 (重測)' },
        { constellation: 'starlink', duration_minutes: 120, sample_interval_seconds: 30, name: 'Starlink 2小時高頻' },
        { constellation: 'starlink', duration_minutes: 720, sample_interval_seconds: 30, name: 'Starlink 12小時高頻' }
    ];
    
    console.log(`將執行 ${operations.length} 次操作，模擬用戶頻繁切換場景...`);
    
    for (let i = 0; i < operations.length; i++) {
        const op = operations[i];
        console.log(`\n📋 操作 ${i + 1}/${operations.length}: ${op.name}`);
        
        try {
            // 生成唯一場景名稱
            const uniqueId = Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            const scenarioName = `StressTest_${op.constellation}_${op.duration_minutes}min_${uniqueId}`;
            
            console.log(`   ⏱️  預期時間範圍: ${op.duration_minutes} 分鐘, 間隔: ${op.sample_interval_seconds} 秒`);
            
            // 執行 D2 預計算
            const startTime = Date.now();
            const precomputeResponse = await fetch(`${API_BASE}/api/satellite-data/d2/precompute`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    scenario_name: scenarioName,
                    constellation: op.constellation,
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
                    duration_minutes: op.duration_minutes,
                    sample_interval_seconds: op.sample_interval_seconds
                })
            });
            
            if (precomputeResponse.ok) {
                const precomputeData = await precomputeResponse.json();
                const computeTime = Date.now() - startTime;
                console.log(`   ✅ 預計算成功 (${computeTime}ms): ${precomputeData.measurements_generated} 個數據點`);
                
                // 獲取部分測量數據進行驗證
                const measurementResponse = await fetch(
                    `${API_BASE}/api/satellite-data/d2/measurements/${precomputeData.scenario_hash}?limit=100`
                );
                
                if (measurementResponse.ok) {
                    const measurementData = await measurementResponse.json();
                    const measurements = measurementData.measurements;
                    
                    if (measurements.length >= 2) {
                        const firstTime = new Date(measurements[0].timestamp);
                        const lastTime = new Date(measurements[Math.min(measurements.length - 1, 99)].timestamp);
                        const sampledDuration = (lastTime - firstTime) / (1000 * 60);
                        
                        // 預測完整持續時間
                        const totalPoints = precomputeData.measurements_generated;
                        const sampledPoints = measurements.length;
                        const projectedDuration = sampledPoints >= 2 ? (sampledDuration / (sampledPoints - 1)) * (totalPoints - 1) : sampledDuration;
                        
                        const durationAccuracy = op.duration_minutes > 0 ? (Math.min(projectedDuration, op.duration_minutes) / Math.max(projectedDuration, op.duration_minutes)) * 100 : 100;
                        
                        console.log(`   📊 時間範圍驗證:`);
                        console.log(`      預期持續時間: ${op.duration_minutes} 分鐘`);
                        console.log(`      推算持續時間: ${projectedDuration.toFixed(2)} 分鐘`);
                        console.log(`      準確性: ${durationAccuracy.toFixed(1)}%`);
                        
                        // 檢查採樣間隔
                        if (measurements.length >= 3) {
                            const interval1 = new Date(measurements[1].timestamp) - new Date(measurements[0].timestamp);
                            const interval2 = new Date(measurements[2].timestamp) - new Date(measurements[1].timestamp);
                            const avgInterval = (interval1 + interval2) / 2 / 1000;
                            const intervalAccuracy = Math.abs(avgInterval - op.sample_interval_seconds) / op.sample_interval_seconds * 100;
                            
                            console.log(`      預期採樣間隔: ${op.sample_interval_seconds} 秒`);
                            console.log(`      實際採樣間隔: ${avgInterval.toFixed(1)} 秒`);
                            console.log(`      間隔誤差: ${intervalAccuracy.toFixed(1)}%`);
                        }
                        
                        // 判斷結果
                        const isSuccess = durationAccuracy >= 95 && Math.abs(projectedDuration - op.duration_minutes) < op.duration_minutes * 0.1;
                        console.log(`   結果: ${isSuccess ? '✅ 成功' : '❌ 異常'} - ${isSuccess ? '時間範圍正確' : '時間範圍偏差過大'}`);
                        
                        if (!isSuccess) {
                            console.log(`   ⚠️  檢測到時間範圍異常！可能的漸進式衰退`);
                        }
                        
                    } else {
                        console.log('   ⚠️ 數據點不足，無法驗證時間範圍');
                    }
                } else {
                    console.log('   ❌ 測量數據獲取失敗');
                }
            } else {
                const errorText = await precomputeResponse.text();
                console.log('   ❌ 預計算失敗:', errorText);
            }
            
        } catch (error) {
            console.error(`   ❌ 操作失敗:`, error.message);
        }
        
        // 短暫等待模擬用戶操作間隔
        await new Promise(resolve => setTimeout(resolve, 500));
    }
    
    console.log('\n🎉 壓力測試完成！');
    console.log('✅ 如果所有操作都顯示「成功」，則表示漸進式時間範圍衰退問題已解決');
}

// 執行壓力測試
stressTestProgressiveDegradation();