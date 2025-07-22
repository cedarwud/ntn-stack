/**
 * 測試前端實際接收和顯示的數據
 * 模擬 unifiedD2DataService.getD2Data() 的完整流程
 */

const API_BASE = 'http://localhost:8080';

async function testFrontendDataDisplay() {
    console.log('🖥️ 測試前端實際數據顯示邏輯...');
    
    // 模擬前端的 D2ScenarioConfig
    const frontendConfig = {
        scenario_name: `D2_starlink_720min_10s_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        constellation: 'starlink',
        ue_position: {
            latitude: 25.0173,  // referenceLocation 中正紀念堂
            longitude: 121.4695,
            altitude: 100
        },
        fixed_ref_position: {
            latitude: 25.0173,  // referenceLocation 中正紀念堂  
            longitude: 121.4695,
            altitude: 100
        },
        thresh1: -100,  // params.Thresh1
        thresh2: -110,  // params.Thresh2
        hysteresis: 3,  // params.Hys
        duration_minutes: 720,  // 12小時
        sample_interval_seconds: 10  // selectedTimeRange.sampleIntervalSeconds
    };
    
    console.log('📋 前端配置:');
    console.log(`   星座: ${frontendConfig.constellation}`);
    console.log(`   時間範圍: ${frontendConfig.duration_minutes} 分鐘`);
    console.log(`   採樣間隔: ${frontendConfig.sample_interval_seconds} 秒`);
    
    try {
        // Step 1: 預計算 (模擬 unifiedD2DataService 的流程)
        console.log('\n🔄 Step 1: 預計算...');
        const precomputeResponse = await fetch(`${API_BASE}/api/satellite-data/d2/precompute`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(frontendConfig)
        });
        
        if (!precomputeResponse.ok) {
            throw new Error(`預計算失敗: ${precomputeResponse.status}`);
        }
        
        const precomputeData = await precomputeResponse.json();
        console.log(`   ✅ 預計算成功: ${precomputeData.measurements_generated} 個數據點`);
        console.log(`   🔑 Scenario Hash: ${precomputeData.scenario_hash}`);
        
        // Step 2: 獲取測量數據 (模擬前端獲取全部數據)
        console.log('\n📊 Step 2: 獲取測量數據...');
        const measurementResponse = await fetch(
            `${API_BASE}/api/satellite-data/d2/measurements/${precomputeData.scenario_hash}?limit=10000`
        );
        
        if (!measurementResponse.ok) {
            throw new Error(`測量數據獲取失敗: ${measurementResponse.status}`);
        }
        
        const measurementData = await measurementResponse.json();
        const measurements = measurementData.measurements;
        
        console.log(`   ✅ 獲得 ${measurements.length} 個測量數據點`);
        
        // Step 3: 轉換為前端格式 (模擬 convertToRealD2DataPoints)
        console.log('\n🔄 Step 3: 轉換為前端數據格式...');
        
        const realD2DataPoints = measurements.map((measurement, index) => ({
            timestamp: measurement.timestamp,
            satelliteDistance: measurement.satellite_distance, // 米
            groundDistance: measurement.ground_distance, // 米
            satelliteInfo: {
                noradId: measurement.norad_id,
                name: measurement.satellite_id,
                latitude: measurement.satellite_position.latitude,
                longitude: measurement.satellite_position.longitude,
                altitude: measurement.satellite_position.altitude,
            },
            triggerConditionMet: measurement.trigger_condition_met,
            d2EventDetails: {
                thresh1: frontendConfig.thresh1,
                thresh2: frontendConfig.thresh2,
                hysteresis: frontendConfig.hysteresis,
                enteringCondition: false, // 簡化
                leavingCondition: false   // 簡化
            }
        }));
        
        console.log(`   ✅ 轉換完成: ${realD2DataPoints.length} 個前端數據點`);
        
        // Step 4: 模擬前端圖表時間軸計算
        console.log('\n📈 Step 4: 前端圖表時間軸分析...');
        
        // 前端的時間標籤計算 (RealD2Chart.tsx line 159)
        const frontendLabels = realD2DataPoints.map((_, index) => index * 10); // 假設每10秒
        const satelliteDistanceData = realD2DataPoints.map(point => point.satelliteDistance / 1000); // 轉為km
        
        console.log(`   時間軸範圍: 0 - ${frontendLabels[frontendLabels.length - 1]} 秒`);
        console.log(`   時間軸範圍: 0 - ${(frontendLabels[frontendLabels.length - 1] / 3600).toFixed(1)} 小時`);
        
        // Step 5: 目視峰值分析 (模擬用戶在圖表上看到的)
        console.log('\n👁️ Step 5: 目視峰值分析...');
        
        const distances = satelliteDistanceData;
        const times = frontendLabels;
        
        // 統計信息
        const minDist = Math.min(...distances);
        const maxDist = Math.max(...distances);
        const avgDist = distances.reduce((a, b) => a + b, 0) / distances.length;
        
        console.log(`   距離統計:`);
        console.log(`      最小: ${minDist.toFixed(1)} km`);
        console.log(`      最大: ${maxDist.toFixed(1)} km`);
        console.log(`      平均: ${avgDist.toFixed(1)} km`);
        console.log(`      變化: ${((maxDist - minDist) / minDist * 100).toFixed(1)}%`);
        
        // 簡單峰值檢測 (用戶眼中的明顯峰值)
        const visualPeaks = [];
        const threshold = (maxDist - minDist) * 0.1; // 10%變化閾值
        
        for (let i = 5; i < distances.length - 5; i++) {
            let isPeak = true;
            const currentDist = distances[i];
            
            // 檢查是否比前後5個點都高
            for (let j = i - 5; j <= i + 5; j++) {
                if (j !== i && distances[j] >= currentDist - threshold) {
                    isPeak = false;
                    break;
                }
            }
            
            if (isPeak && currentDist > avgDist) {
                visualPeaks.push({
                    index: i,
                    timeSeconds: times[i],
                    timeHours: times[i] / 3600,
                    distance: currentDist,
                    timestamp: realD2DataPoints[i].timestamp
                });
            }
        }
        
        console.log(`\n🏔️ 視覺上明顯的峰值 (用戶在圖表上會看到): ${visualPeaks.length} 個`);
        
        if (visualPeaks.length > 0) {
            visualPeaks.forEach((peak, idx) => {
                const time = new Date(peak.timestamp);
                console.log(`   ${idx + 1}. ${time.toISOString().substr(11, 8)} (${peak.timeHours.toFixed(1)}h) - ${peak.distance.toFixed(1)}km`);
            });
            
            // 計算峰值間隔
            if (visualPeaks.length >= 2) {
                const intervals = [];
                for (let i = 1; i < visualPeaks.length; i++) {
                    intervals.push((visualPeaks[i].timeSeconds - visualPeaks[i-1].timeSeconds) / 60); // 分鐘
                }
                const avgInterval = intervals.reduce((a, b) => a + b, 0) / intervals.length;
                console.log(`\n⏱️ 峰值間隔分析:`);
                console.log(`   間隔序列: ${intervals.map(i => i.toFixed(1)).join(', ')} 分鐘`);
                console.log(`   平均間隔: ${avgInterval.toFixed(1)} 分鐘`);
                console.log(`   軌道週期: ${avgInterval.toFixed(1)} 分鐘`);
            }
        } else {
            console.log(`   ⚠️ 沒有檢測到明顯的峰值`);
            
            // 顯示距離變化趨勢
            console.log(`\n📊 距離變化採樣 (每小時):`);
            const hourlyStep = Math.floor(distances.length / 12); // 12小時，每小時一個點
            for (let i = 0; i < 12 && i * hourlyStep < distances.length; i++) {
                const idx = i * hourlyStep;
                const time = new Date(realD2DataPoints[idx].timestamp);
                console.log(`   ${i}h: ${time.toISOString().substr(11, 8)} - ${distances[idx].toFixed(1)}km`);
            }
        }
        
        // Step 6: 與我的後端測試對比
        console.log(`\n🔬 與後端測試對比:`);
        console.log(`   前端目視峰值: ${visualPeaks.length} 個`);
        console.log(`   後端算法檢測: 8 個 (之前測試結果)`);
        console.log(`   用戶觀察: 2 個 (您的反饋)`);
        
        if (visualPeaks.length !== 8) {
            console.log(`   ❗ 差異原因可能是:`);
            console.log(`      1. 峰值檢測算法敏感度不同`);
            console.log(`      2. 圖表顯示解析度限制`);
            console.log(`      3. 視覺上不明顯的小峰值`);
            console.log(`      4. 前端數據處理差異`);
        }
        
    } catch (error) {
        console.error('❌ 測試失敗:', error.message);
    }
}

testFrontendDataDisplay();