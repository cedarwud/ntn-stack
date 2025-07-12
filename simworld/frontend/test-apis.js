// 測試現有API端點的可用性
const testAPIs = async () => {
  const endpoints = [
    '/api/v1/health',
    '/api/v1/status', 
    '/api/v1/performance/metrics/real-time',
    '/api/v1/satellite-ops/visible_satellites?count=10&min_elevation_deg=-10&observer_lat=0&observer_lon=0&observer_alt=0&global_view=true'
  ];

  for (const endpoint of endpoints) {
    try {
      const response = await fetch(`http://localhost:8888${endpoint}`);
      const data = await response.json();
      console.log(`✅ ${endpoint}:`, data);
    } catch (error) {
      console.error(`❌ ${endpoint}:`, error.message);
    }
  }
};

// 在瀏覽器控制台運行：testAPIs();
