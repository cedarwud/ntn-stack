/**
 * API服務統一導出
 * 將所有API服務模塊集中導出，方便在應用程序中使用
 */

// 導出設備API服務
export * from './deviceApi';
import deviceApi from './deviceApi';

// 導出衛星API服務
export * from './satelliteApi';
import satelliteApi from './satelliteApi';

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
  satellite: satelliteApi,
  simulation: simulationApi,
  coordinate: coordinateApi
};

export default api; 