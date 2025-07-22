/**
 * 重現用戶具體場景：Starlink 2小時 vs 12小時的週期問題
 * 驗證前端實際使用的配置是否正確
 */

const API_BASE = 'http://localhost:8080';

async function testUserScenario() {
    console.log('🔍 重現用戶場景：Starlink 2小時 vs 12小時');
    
    const scenarios = [
        {
            name: 'Starlink 2小時 (用戶配置)',
            constellation: 'starlink',
            duration_minutes: 120,
            sample_interval_seconds: 10, // 前端預設值
            expectedCycles: '1-1.3個週期'
        },
        {
            name: 'Starlink 12小時 (用戶配置)', 
            constellation: 'starlink',
            duration_minutes: 720,
            sample_interval_seconds: 10, // 前端預設值
            expectedCycles: '6-8個週期'
        }
    ];
    
    for (const scenario of scenarios) {
        console.log(`\n📊 測試: ${scenario.name}`);
        console.log(`   預期週期數: ${scenario.expectedCycles}`);
        
        try {
            const uniqueId = Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            const scenarioName = `UserScenario_${scenario.constellation}_${scenario.duration_minutes}min_${uniqueId}`;
            
            // 使用與前端完全相同的配置
            const requestBody = {
                scenario_name: scenarioName,
                constellation: scenario.constellation,
                ue_position: {
                    latitude: 25.0173,  // 中正紀念堂
                    longitude: 121.4695,
                    altitude: 100
                },
                fixed_ref_position: {
                    latitude: 25.0173,  // 中正紀念堂  
                    longitude: 121.4695,
                    altitude: 100
                },
                thresh1: -100,
                thresh2: -110, 
                hysteresis: 3,
                duration_minutes: scenario.duration_minutes,
                sample_interval_seconds: scenario.sample_interval_seconds
            };
            
            console.log(`   ⚙️ 配置: ${scenario.duration_minutes}分鐘, ${scenario.sample_interval_seconds}秒間隔`);
            
            // 預計算
            const precomputeResponse = await fetch(`${API_BASE}/api/satellite-data/d2/precompute`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestBody)
            });
            
            if (precomputeResponse.ok) {
                const precomputeData = await precomputeResponse.json();
                console.log(`   ✅ 預計算成功: ${precomputeData.measurements_generated} 個數據點`);
                
                // 獲取所有測量數據
                const measurementResponse = await fetch(
                    `${API_BASE}/api/satellite-data/d2/measurements/${precomputeData.scenario_hash}?limit=10000`
                );
                
                if (measurementResponse.ok) {
                    const measurementData = await measurementResponse.json();
                    const measurements = measurementData.measurements;
                    
                    console.log(`   📊 實際數據點: ${measurements.length}`);
                    
                    if (measurements.length >= 10) {
                        // 分析完整時間範圍
                        const firstTime = new Date(measurements[0].timestamp);
                        const lastTime = new Date(measurements[measurements.length - 1].timestamp);
                        const actualDurationMinutes = (lastTime.getTime() - firstTime.getTime()) / (1000 * 60);
                        
                        console.log(`   ⏰ 實際時間範圍: ${actualDurationMinutes.toFixed(2)} 分鐘`);
                        console.log(`   📅 開始時間: ${firstTime.toISOString()}`);
                        console.log(`   📅 結束時間: ${lastTime.toISOString()}`);
                        
                        // 分析距離變化週期
                        const distances = measurements.map(m => m.satellite_distance / 1000);
                        
                        // 尋找極值點分析週期
                        const peaks = [];
                        const valleys = [];
                        
                        for (let i = 1; i < distances.length - 1; i++) {
                            if (distances[i] > distances[i-1] && distances[i] > distances[i+1]) {
                                peaks.push({
                                    index: i,
                                    timeMinutes: i * scenario.sample_interval_seconds / 60,
                                    distance: distances[i],
                                    timestamp: measurements[i].timestamp
                                });
                            }
                            if (distances[i] < distances[i-1] && distances[i] < distances[i+1]) {
                                valleys.push({
                                    index: i,
                                    timeMinutes: i * scenario.sample_interval_seconds / 60,
                                    distance: distances[i],
                                    timestamp: measurements[i].timestamp
                                });
                            }
                        }
                        
                        console.log(`   🏔️ 發現 ${peaks.length} 個峰值, ${valleys.length} 個谷值`);
                        
                        // 計算週期
                        if (peaks.length >= 2) {
                            const intervals = [];
                            for (let i = 1; i < peaks.length; i++) {
                                intervals.push(peaks[i].timeMinutes - peaks[i-1].timeMinutes);
                            }
                            const avgPeriod = intervals.reduce((a, b) => a + b, 0) / intervals.length;
                            const totalCycles = actualDurationMinutes / avgPeriod;
                            
                            console.log(`   📈 分析結果:`);
                            console.log(`      平均軌道週期: ${avgPeriod.toFixed(1)} 分鐘`);
                            console.log(`      實際週期數: ${totalCycles.toFixed(2)}`);
                            console.log(`      峰值間隔: ${intervals.map(i => i.toFixed(1)).join(', ')} 分鐘`);
                            
                            // 列出所有峰值時間
                            console.log(`   📍 峰值時間點:`);
                            peaks.forEach((peak, idx) => {
                                const time = new Date(peak.timestamp);
                                console.log(`      ${idx + 1}. ${time.toISOString().substr(11, 8)} (${peak.timeMinutes.toFixed(1)}min) - ${peak.distance.toFixed(0)}km`);
                            });
                            
                        } else {
                            console.log(`   ⚠️ 峰值不足，無法分析週期 (只有 ${peaks.length} 個峰值)`);
                            
                            // 如果峰值不足，顯示距離變化趨勢
                            const minDist = Math.min(...distances);
                            const maxDist = Math.max(...distances);
                            const range = maxDist - minDist;
                            console.log(`   📏 距離範圍: ${minDist.toFixed(0)} - ${maxDist.toFixed(0)} km (變化 ${range.toFixed(0)} km)`);
                            
                            // 顯示前幾個和後幾個數據點
                            console.log(`   📝 前5個數據點:`);
                            for (let i = 0; i < Math.min(5, measurements.length); i++) {
                                const m = measurements[i];
                                const time = new Date(m.timestamp);
                                console.log(`      ${i+1}. ${time.toISOString().substr(11, 8)} - ${(m.satellite_distance/1000).toFixed(1)}km`);
                            }
                            
                            if (measurements.length > 10) {
                                console.log(`   📝 後5個數據點:`);
                                for (let i = Math.max(0, measurements.length - 5); i < measurements.length; i++) {
                                    const m = measurements[i];
                                    const time = new Date(m.timestamp);
                                    console.log(`      ${i+1}. ${time.toISOString().substr(11, 8)} - ${(m.satellite_distance/1000).toFixed(1)}km`);
                                }
                            }
                        }
                        
                    } else {
                        console.log('   ⚠️ 數據點不足進行週期分析');
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
        
        // 等待避免請求過於頻繁
        await new Promise(resolve => setTimeout(resolve, 1000));
    }
    
    console.log('\n🔍 用戶場景測試完成');
}

// 執行測試
testUserScenario();