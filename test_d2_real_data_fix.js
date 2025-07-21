/**
 * 測試 D2 真實數據切換功能修復
 * 驗證 API 端點是否正常工作
 */

const API_BASE = 'http://localhost:8080';

async function testD2RealDataAPI() {
    console.log('🧪 開始測試 D2 真實數據 API...');
    
    try {
        // 1. 測試 TLE 更新
        console.log('1. 測試 TLE 更新...');
        const tleResponse = await fetch(`${API_BASE}/api/satellite-data/tle/update`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                constellation: 'starlink',
                force_update: false
            })
        });
        
        if (tleResponse.ok) {
            const tleData = await tleResponse.json();
            console.log('✅ TLE 更新成功:', tleData);
        } else {
            console.log('⚠️ TLE 更新響應:', tleResponse.status, await tleResponse.text());
        }
        
        // 2. 測試 D2 預計算
        console.log('2. 測試 D2 預計算...');
        const precomputeResponse = await fetch(`${API_BASE}/api/satellite-data/d2/precompute`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                scenario_name: 'EventD2Viewer_RealData_Test',
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
                duration_minutes: 60,
                sample_interval_seconds: 30
            })
        });
        
        if (precomputeResponse.ok) {
            const precomputeData = await precomputeResponse.json();
            console.log('✅ D2 預計算成功:', precomputeData);
            
            // 3. 測試獲取測量數據
            console.log('3. 測試獲取測量數據...');
            const measurementResponse = await fetch(
                `${API_BASE}/api/satellite-data/d2/measurements/${precomputeData.scenario_hash}?limit=100`
            );
            
            if (measurementResponse.ok) {
                const measurementData = await measurementResponse.json();
                console.log('✅ 測量數據獲取成功:', {
                    scenario_hash: measurementData.scenario_hash,
                    measurement_count: measurementData.measurement_count,
                    sample_measurements: measurementData.measurements.slice(0, 3)
                });
            } else {
                console.log('❌ 測量數據獲取失敗:', measurementResponse.status, await measurementResponse.text());
            }
            
        } else {
            console.log('❌ D2 預計算失敗:', precomputeResponse.status, await precomputeResponse.text());
        }
        
        // 4. 測試健康檢查
        console.log('4. 測試健康檢查...');
        const healthResponse = await fetch(`${API_BASE}/health`);
        if (healthResponse.ok) {
            const healthData = await healthResponse.json();
            console.log('✅ 健康檢查成功:', healthData);
        } else {
            console.log('❌ 健康檢查失敗:', healthResponse.status);
        }
        
        console.log('🎉 所有測試完成！');
        
    } catch (error) {
        console.error('❌ 測試過程中發生錯誤:', error);
    }
}

// 執行測試
testD2RealDataAPI();
