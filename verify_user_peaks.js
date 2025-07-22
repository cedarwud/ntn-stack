/**
 * 驗證用戶觀察到的2個峰值
 * 分析2h和10h的峰值特徵
 */

const API_BASE = 'http://localhost:8080';

async function verifyUserPeaks() {
    console.log('🔍 驗證用戶觀察的2個峰值...');
    
    try {
        const config = {
            scenario_name: `VerifyPeaks_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            constellation: 'starlink',
            ue_position: { latitude: 25.0173, longitude: 121.4695, altitude: 100 },
            fixed_ref_position: { latitude: 25.0173, longitude: 121.4695, altitude: 100 },
            thresh1: -100,
            thresh2: -110,
            hysteresis: 3,
            duration_minutes: 720,
            sample_interval_seconds: 10
        };
        
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
        
        console.log(`✅ 獲得 ${measurements.length} 個數據點`);
        
        // 尋找真正的全局極值
        const distances = measurements.map(m => m.satellite_distance / 1000);
        const maxDist = Math.max(...distances);
        const minDist = Math.min(...distances);
        
        // 找到最大值的位置
        const globalMaxIndices = [];
        for (let i = 0; i < distances.length; i++) {
            if (distances[i] === maxDist) {
                globalMaxIndices.push(i);
            }
        }
        
        // 找到接近最大值的其他峰值（在90%以上）
        const highPeaks = [];
        const threshold = maxDist * 0.85; // 85%閾值
        
        for (let i = 360; i < distances.length - 360; i++) { // 1小時窗口
            const currentDist = distances[i];
            
            if (currentDist >= threshold) {
                // 檢查是否在局部範圍內是最高的
                let isLocalMax = true;
                for (let j = i - 360; j <= i + 360; j++) {
                    if (j !== i && distances[j] > currentDist) {
                        isLocalMax = false;
                        break;
                    }
                }
                
                if (isLocalMax) {
                    const timeHours = i * 10 / 3600;
                    highPeaks.push({
                        index: i,
                        timeHours: timeHours,
                        distance: currentDist,
                        timestamp: measurements[i].timestamp
                    });
                }
            }
        }
        
        // 去重相近的峰值
        const uniquePeaks = [];
        for (const peak of highPeaks) {
            const isDuplicate = uniquePeaks.some(existing => 
                Math.abs(existing.timeHours - peak.timeHours) < 0.5
            );
            if (!isDuplicate) {
                uniquePeaks.push(peak);
            }
        }
        
        console.log(`\n🏔️ 高峰值檢測 (≥${threshold.toFixed(0)}km):`);
        console.log(`   全局最大值: ${maxDist.toFixed(1)} km`);
        console.log(`   檢測到 ${uniquePeaks.length} 個高峰值:`);
        
        uniquePeaks.forEach((peak, idx) => {
            const time = new Date(peak.timestamp);
            console.log(`   ${idx + 1}. ${time.toISOString().substr(11, 8)} (${peak.timeHours.toFixed(1)}h) - ${peak.distance.toFixed(1)}km`);
        });
        
        // 分析用戶觀察的2個峰值理論
        if (uniquePeaks.length >= 2) {
            console.log(`\n🎯 用戶觀察分析:`);
            console.log(`   檢測到的高峰值數量: ${uniquePeaks.length}`);
            
            if (uniquePeaks.length === 2) {
                const interval = (uniquePeaks[1].timeHours - uniquePeaks[0].timeHours) * 60;
                console.log(`   ✅ 正好2個高峰值！與用戶觀察匹配`);
                console.log(`   峰值間隔: ${interval.toFixed(1)} 分鐘 = ${(interval/60).toFixed(1)} 小時`);
                console.log(`   這表示軌道週期約: ${interval.toFixed(1)} 分鐘`);
                
                // 檢查是否符合Starlink理論週期
                const theoreticalPeriod = 95.6; // 分鐘
                const cycles = interval / theoreticalPeriod;
                console.log(`   理論軌道週期: ${theoreticalPeriod} 分鐘`);
                console.log(`   峰值間隔包含: ${cycles.toFixed(1)} 個軌道週期`);
                
                if (Math.abs(cycles - Math.round(cycles)) < 0.2) {
                    console.log(`   ✅ 符合整數個軌道週期！`);
                } else {
                    console.log(`   ⚠️ 不是整數個軌道週期，可能是軌道相位關係`);
                }
            } else {
                console.log(`   檢測到 ${uniquePeaks.length} 個高峰值，與用戶觀察的2個不完全匹配`);
                console.log(`   可能原因:`);
                console.log(`   - 圖表分辨率影響視覺判斷`);
                console.log(`   - 不同的峰值顯著性標準`);
                console.log(`   - 軌道幾何關係造成的視覺效果`);
            }
        }
        
        // 檢查距離變化的週期性
        console.log(`\n📊 距離變化週期性分析:`);
        const hourlyDistances = [];
        for (let hour = 0; hour < 12; hour++) {
            const index = Math.floor(hour * 360);
            if (index < measurements.length) {
                hourlyDistances.push({
                    hour: hour,
                    distance: measurements[index].satellite_distance / 1000,
                    timestamp: measurements[index].timestamp
                });
            }
        }
        
        // 找到每小時數據中的相對極值
        const hourlyPeaks = [];
        const hourlyValleys = [];
        
        for (let i = 1; i < hourlyDistances.length - 1; i++) {
            const prev = hourlyDistances[i-1].distance;
            const curr = hourlyDistances[i].distance;
            const next = hourlyDistances[i+1].distance;
            
            if (curr > prev && curr > next) {
                hourlyPeaks.push(hourlyDistances[i]);
            }
            if (curr < prev && curr < next) {
                hourlyValleys.push(hourlyDistances[i]);
            }
        }
        
        console.log(`   每小時採樣峰值: ${hourlyPeaks.length} 個`);
        hourlyPeaks.forEach((peak, idx) => {
            const time = new Date(peak.timestamp);
            console.log(`   ${idx + 1}. ${peak.hour}h: ${time.toISOString().substr(11, 8)} - ${peak.distance.toFixed(1)}km`);
        });
        
        console.log(`   每小時採樣谷值: ${hourlyValleys.length} 個`);
        hourlyValleys.forEach((valley, idx) => {
            const time = new Date(valley.timestamp);
            console.log(`   ${idx + 1}. ${valley.hour}h: ${time.toISOString().substr(11, 8)} - ${valley.distance.toFixed(1)}km`);
        });
        
        // 最終結論
        console.log(`\n💡 結論:`);
        if (uniquePeaks.length === 2) {
            console.log(`   ✅ 系統檢測到2個顯著高峰值，與用戶觀察匹配`);
            console.log(`   ✅ 這表明12小時內確實有2個主要的距離峰值`);
            console.log(`   ✅ 用戶的視覺觀察是準確的`);
        } else {
            console.log(`   📊 系統檢測結果與用戶觀察存在差異`);
            console.log(`   🔍 需要調整峰值檢測標準或了解圖表顯示差異`);
        }
        
    } catch (error) {
        console.error('❌ 驗證失敗:', error.message);
    }
}

verifyUserPeaks();