// api.ts - 集中管理 API 請求
import axios from 'axios';

// 創建一個 axios 實例，使用相對路徑
const api = axios.create({
  baseURL: '', // 不設置 baseURL，使用相對路徑
  timeout: 30000, // 30 秒超時
  headers: {
    'Content-Type': 'application/json',
  }
});

// 攔截請求，確保使用相對路徑
api.interceptors.request.use((config) => {
  // 確保 URL 不包含 Docker 容器名稱或絕對域名
  if (config.url) {
    // 移除容器名稱、IP地址和域名，僅保留路徑部分
    config.url = config.url.replace(/http(s)?:\/\/(fastapi_app|backend|localhost|120\.126\.151\.101)(:\d+)?/g, '');
  }
  
  // 確保 URL 以 / 開頭
  if (config.url && !config.url.startsWith('/')) {
    config.url = `/${config.url}`;
  }

  // 不設置 baseURL，使得所有請求都相對於當前頁面
  config.baseURL = '';
  
  // 輸出請求 URL 信息，方便調試
  console.log(`API Request to: ${config.url}`);
  
  return config;
});

// 攔截響應，處理錯誤
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      // 服務器返回了錯誤狀態碼
      console.error(`API 請求錯誤 (${error.response.status}): ${error.message}`);
      console.error('響應數據:', error.response.data);
    } else if (error.request) {
      // 請求已發送但沒有收到響應
      console.error('API 請求錯誤: 沒有收到響應');
      console.error('請求配置:', error.config);
    } else {
      // 請求設置時發生錯誤
      console.error('API 請求設置錯誤:', error.message);
    }
    
    return Promise.reject(error);
  }
);

export default api; 