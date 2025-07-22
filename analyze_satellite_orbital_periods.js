/**
 * 分析真實衛星軌道週期
 * 驗證不同星座的實際軌道週期是否符合預期
 */

const API_BASE = 'http://localhost:8080';

async function analyzeSatelliteOrbitalPeriods() {
    console.log('🛰️ 分析真實衛星軌道週期...');
    
    const constellations = [
        { name: 'starlink', expectedPeriod: '約96分鐘 (LEO)' },
        { name: 'gps', expectedPeriod: '約12小時 (MEO)' },
        { name: 'oneweb', expectedPeriod: '約100分鐘 (LEO)' }
    ];
    
    for (const constellation of constellations) {
        console.log(`\n📡 分析 ${constellation.name.toUpperCase()} 星座:`);
        console.log(`   理論軌道週期: ${constellation.expectedPeriod}`);
        
        try {
            // 測試長時間段以觀察多個完整週期
            const uniqueId = Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            const scenarioName = `OrbitalAnalysis_${constellation.name}_${uniqueId}`;
            
            // 使用24小時觀察週期，30秒採樣
            const precomputeResponse = await fetch(`${API_BASE}/api/satellite-data/d2/precompute`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    scenario_name: scenarioName,
                    constellation: constellation.name,
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
                    duration_minutes: 1440, // 24小時
                    sample_interval_seconds: 60 // 1分鐘採樣
                })
            });
            
            if (precomputeResponse.ok) {
                const precomputeData = await precomputeResponse.json();
                console.log(`   ✅ 預計算成功: ${precomputeData.measurements_generated} 個數據點`);
                
                // 獲取測量數據
                const measurementResponse = await fetch(
                    `${API_BASE}/api/satellite-data/d2/measurements/${precomputeData.scenario_hash}?limit=1440`
                );
                
                if (measurementResponse.ok) {
                    const measurementData = await measurementResponse.json();
                    const measurements = measurementData.measurements;
                    
                    console.log(`   📊 獲得 ${measurements.length} 個數據點進行分析`);
                    
                    if (measurements.length >= 100) {
                        // 分析衛星距離變化模式
                        const distances = measurements.map(m => m.satellite_distance / 1000); // 轉為公里
                        const times = measurements.map((m, i) => i); // 時間索引（分鐘）
                        
                        // 尋找距離極值點來識別軌道週期
                        const peaks = [];
                        const valleys = [];
                        
                        for (let i = 1; i < distances.length - 1; i++) {
                            if (distances[i] > distances[i-1] && distances[i] > distances[i+1]) {
                                peaks.push({ index: i, time: i, distance: distances[i] });
                            }
                            if (distances[i] < distances[i-1] && distances[i] < distances[i+1]) {
                                valleys.push({ index: i, time: i, distance: distances[i] });
                            }
                        }
                        
                        console.log(`   🏔️ 發現 ${peaks.length} 個距離峰值, ${valleys.length} 個距離谷值`);
                        
                        // 計算峰值間隔（軌道週期）
                        if (peaks.length >= 2) {
                            const intervals = [];
                            for (let i = 1; i < peaks.length; i++) {
                                intervals.push(peaks[i].time - peaks[i-1].time);
                            }
                            const avgInterval = intervals.reduce((a, b) => a + b, 0) / intervals.length;
                            console.log(`   ⏱️ 平均軌道週期: ${avgInterval.toFixed(1)} 分鐘`);
                            
                            // 計算在不同時間段內的週期數
                            const cyclesIn2Hours = 120 / avgInterval;
                            const cyclesIn12Hours = 720 / avgInterval;
                            const cyclesIn24Hours = 1440 / avgInterval;
                            
                            console.log(`   📈 週期分析:`);
                            console.log(`      2小時內週期數: ${cyclesIn2Hours.toFixed(2)}`);
                            console.log(`      12小時內週期數: ${cyclesIn12Hours.toFixed(2)}`);
                            console.log(`      24小時內週期數: ${cyclesIn24Hours.toFixed(2)}`);
                            
                            // 分析距離範圍
                            const minDistance = Math.min(...distances);
                            const maxDistance = Math.max(...distances);
                            console.log(`   📏 距離範圍: ${minDistance.toFixed(0)} - ${maxDistance.toFixed(0)} km`);
                            console.log(`   📊 距離變化幅度: ${((maxDistance - minDistance) / minDistance * 100).toFixed(1)}%`);
                            
                            // 判斷軌道類型
                            let orbitType = '';
                            if (avgInterval < 120) {
                                orbitType = 'LEO (低地球軌道)';
                            } else if (avgInterval < 240) {
                                orbitType = 'MEO 下層';
                            } else if (avgInterval < 800) {
                                orbitType = 'MEO (中地球軌道)';
                            } else {
                                orbitType = 'GEO/高軌道';
                            }
                            console.log(`   🛰️ 軌道類型: ${orbitType}`);
                            
                        } else {
                            console.log('   ⚠️ 峰值點不足，無法計算軌道週期');
                        }
                        
                        // 顯示前幾個數據點的樣本
                        console.log(`   📝 前5個數據點樣本:`);
                        for (let i = 0; i < Math.min(5, measurements.length); i++) {
                            const m = measurements[i];
                            const time = new Date(m.timestamp);
                            console.log(`      ${i+1}. ${time.toISOString().substr(11, 8)} - ${(m.satellite_distance/1000).toFixed(1)}km`);
                        }
                        
                    } else {
                        console.log('   ⚠️ 數據點不足，無法進行週期分析');
                    }
                } else {
                    console.log('   ❌ 測量數據獲取失敗');
                }
            } else {
                console.log('   ❌ 預計算失敗:', await precomputeResponse.text());
            }
            
        } catch (error) {
            console.error(`   ❌ 分析失敗:`, error.message);
        }
        
        // 等待避免請求過於頻繁
        await new Promise(resolve => setTimeout(resolve, 1000));
    }
    
    console.log('\n🎉 衛星軌道週期分析完成！');
    console.log('\n💡 解釋：');
    console.log('- LEO衛星（如Starlink）：軌道週期約90-100分鐘');
    console.log('- MEO衛星（如GPS）：軌道週期約12小時');
    console.log('- 如果2小時只看到1個週期，可能該衛星軌道週期確實約為2小時');
    console.log('- 12小時看到2個週期表示軌道週期約為6小時，這在MEO範圍內是正常的');
}

// 執行分析
analyzeSatelliteOrbitalPeriods();