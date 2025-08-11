/**
 * API服務統一導出
 * 將所有API服務模塊集中導出，方便在應用程序中使用
 */

// 導出設備API服務
export * from './deviceApi';
import deviceApi from './deviceApi';

// 衛星API服務已整合到 simworld-api.ts
// export * from './satelliteApi'; // 已廢棄
// import satelliteApi from './satelliteApi'; // 已廢棄

// 導出模擬API服務
export * from './simulationApi';
import simulationApi from './simulationApi';

// 導出座標API服務
export * from './coordinateApi';
import coordinateApi from './coordinateApi';

// 導出API路由
export { default as ApiRoutes } from '../config/apiRoutes';

// 導出統一API對象
const api = {
  device: deviceApi,
  // satellite: satelliteApi, // 已整合到 simworld-api.ts
  simulation: simulationApi,
  coordinate: coordinateApi
};

export default api; 