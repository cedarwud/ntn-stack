// 測試衛星數據流和渲染的調試腳本
const http = require('http');

// 1. 測試衛星數據API
console.log('🔍 測試衛星數據API...');

const testAPI = () => {
  return new Promise((resolve) => {
    const options = {
      hostname: 'localhost',
      port: 8080,
      path: '/api/v1/satellite-simple/visible_satellites?count=5&min_elevation_deg=5&observer_lat=24.9441667&observer_lon=121.3713889&constellation=starlink&utc_timestamp=2025-08-18T10:00:00Z&global_view=false',
      method: 'GET'
    };

    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => data += chunk);
      res.on('end', () => {
        try {
          const result = JSON.parse(data);
          console.log('✅ API測試成功:', {
            衛星數量: result.satellites?.length || 0,
            第一顆衛星: result.satellites?.[0] ? {
              name: result.satellites[0].name,
              hasTimeseries: !!result.satellites[0].position_timeseries?.length,
              timeseriesLength: result.satellites[0].position_timeseries?.length
            } : null
          });
          resolve(result);
        } catch (e) {
          console.error('❌ API解析錯誤:', e.message);
          resolve(null);
        }
      });
    });

    req.on('error', (e) => {
      console.error('❌ API請求錯誤:', e.message);
      resolve(null);
    });

    req.end();
  });
};

// 2. 測試前端資源
const testFrontend = () => {
  return new Promise((resolve) => {
    const options = {
      hostname: 'localhost',
      port: 5173,
      path: '/',
      method: 'GET'
    };

    const req = http.request(options, (res) => {
      console.log('✅ 前端狀態:', res.statusCode);
      resolve(res.statusCode === 200);
    });

    req.on('error', (e) => {
      console.error('❌ 前端連接錯誤:', e.message);
      resolve(false);
    });

    req.end();
  });
};

// 3. 測試衛星模型文件
const testSatelliteModel = () => {
  return new Promise((resolve) => {
    const options = {
      hostname: 'localhost',
      port: 8888,
      path: '/static/models/sat.glb',
      method: 'HEAD'
    };

    const req = http.request(options, (res) => {
      console.log('✅ 衛星模型檢查:', {
        狀態碼: res.statusCode,
        文件大小: res.headers['content-length'],
        內容類型: res.headers['content-type']
      });
      resolve(res.statusCode === 200);
    });

    req.on('error', (e) => {
      console.error('❌ 衛星模型錯誤:', e.message);
      resolve(false);
    });

    req.end();
  });
};

// 執行所有測試
async function runTests() {
  console.log('🚀 開始衛星顯示問題診斷...\n');

  const apiResult = await testAPI();
  const frontendOK = await testFrontend();
  const modelOK = await testSatelliteModel();

  console.log('\n📊 診斷結果總結:');
  console.log('- API數據:', apiResult ? '✅ 正常' : '❌ 異常');
  console.log('- 前端服務:', frontendOK ? '✅ 正常' : '❌ 異常');
  console.log('- 衛星模型:', modelOK ? '✅ 正常' : '❌ 異常');

  if (apiResult && frontendOK && modelOK) {
    console.log('\n🎯 基礎設施正常，問題可能在於：');
    console.log('1. SatelliteDataBridge 數據同步');
    console.log('2. DynamicSatelliteRenderer 渲染邏輯');
    console.log('3. 衛星位置計算或可見性判斷');
  }
}

runTests().catch(console.error);