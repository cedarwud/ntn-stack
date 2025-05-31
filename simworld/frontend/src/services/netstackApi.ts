/**
 * NetStack API 服務層
 * 負責與 NetStack 後端 (port 8080) 交互，獲取網路狀態、UAV 數據等
 */
import axios, { AxiosError } from 'axios';
import { UAVData, SystemStatus, NetworkTopology } from '../types/charts';

// 創建 NetStack API 實例
const netstackApi = axios.create({
  baseURL: 'http://localhost:8080',
  timeout: 10000, // 10秒超時
  headers: {
    'Content-Type': 'application/json',
  }
});

// API 重試配置
const RETRY_CONFIG = {
  maxRetries: 1, // 減少重試次數
  retryDelay: 3000, // 增加重試延遲
  enableMockData: true, // 啟用模擬數據降級
};

// 重試函數
const retryRequest = async <T>(
  requestFn: () => Promise<T>,
  retries: number = RETRY_CONFIG.maxRetries
): Promise<T> => {
  try {
    return await requestFn();
  } catch (error) {
    if (retries > 0 && isRetryableError(error)) {
      console.log(`請求失敗，將在 ${RETRY_CONFIG.retryDelay}ms 後重試，剩餘重試次數: ${retries}`);
      await new Promise(resolve => setTimeout(resolve, RETRY_CONFIG.retryDelay));
      return retryRequest(requestFn, retries - 1);
    }
    throw error;
  }
};

// 判斷錯誤是否可重試
const isRetryableError = (error: any): boolean => {
  if (!error.response) {
    // 網路錯誤，可重試
    return true;
  }
  
  const status = error.response.status;
  // 只有 502, 503, 504 錯誤才重試
  return status === 502 || status === 503 || status === 504;
};

// 攔截請求，添加日志
netstackApi.interceptors.request.use((config) => {
  console.log(`NetStack API Request: ${config.method?.toUpperCase()} ${config.url}`);
  return config;
});

// 攔截響應，處理錯誤
netstackApi.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    // 不要在攔截器中打印錯誤，讓各個函數自己處理
    return Promise.reject(error);
  }
);

// 模擬數據生成器
const generateMockSystemStatus = (): SystemStatus => ({
  status: 'healthy',
  timestamp: new Date().toISOString(),
  components: {
    netstack: { 
      name: 'NetStack',
      healthy: true,
      status: 'running',
      version: '1.0.0',
      last_health_check: new Date().toISOString(),
      metrics: { cpu_usage: Math.floor(Math.random() * 30) + 10, memory_usage: Math.floor(Math.random() * 40) + 30, active_connections: Math.floor(Math.random() * 20) + 5 }
    },
    simworld: { 
      name: 'SimWorld',
      healthy: true,
      status: 'running',
      version: '1.0.0',
      last_health_check: new Date().toISOString(),
      metrics: { cpu_usage: Math.floor(Math.random() * 25) + 8, memory_usage: Math.floor(Math.random() * 35) + 25, active_connections: Math.floor(Math.random() * 15) + 3 }
    },
    database: { 
      name: 'Database',
      healthy: true,
      status: 'running',
      version: '1.0.0',
      last_health_check: new Date().toISOString(),
      metrics: { cpu_usage: Math.floor(Math.random() * 20) + 5, memory_usage: Math.floor(Math.random() * 30) + 15, active_connections: Math.floor(Math.random() * 10) + 1 }
    }
  },
  summary: {
    total_services: 3,
    healthy_services: 3,
    degraded_services: 0,
    last_updated: new Date().toISOString()
  }
});

const generateMockUAVData = (): { uavs: UAVData[]; total: number } => {
  const mockUAVs: UAVData[] = [
    {
      uav_id: 'UAV-001',
      name: 'SimUAV-Alpha',
      flight_status: 'flying',
      ue_connection_status: 'connected',
      current_position: { 
        latitude: 24.7881 + (Math.random() - 0.5) * 0.01, 
        longitude: 120.9974 + (Math.random() - 0.5) * 0.01, 
        altitude: 480 + Math.random() * 40,
        timestamp: new Date().toISOString(),
        speed: 12 + Math.random() * 8,
        heading: Math.random() * 360
      },
      target_position: {
        latitude: 24.7901,
        longitude: 120.9984,
        altitude: 500,
        timestamp: new Date().toISOString(),
        speed: 15.2,
        heading: 45
      },
      signal_quality: {
        rsrp_dbm: -95 + Math.random() * 20,
        rsrq_db: -15 + Math.random() * 8,
        sinr_db: 15 + Math.random() * 10,
        cqi: Math.floor(Math.random() * 10) + 8,
        throughput_mbps: 20 + Math.random() * 15,
        latency_ms: 10 + Math.random() * 15,
        packet_loss_rate: Math.random() * 0.5,
        jitter_ms: 1 + Math.random() * 3,
        link_budget_margin_db: 8 + Math.random() * 8,
        doppler_shift_hz: 100 + Math.random() * 100,
        beam_alignment_score: 0.8 + Math.random() * 0.2,
        interference_level_db: -100 + Math.random() * 10,
        timestamp: new Date().toISOString(),
        measurement_confidence: 0.85 + Math.random() * 0.15
      },
      last_update: new Date().toISOString()
    },
    {
      uav_id: 'UAV-002', 
      name: 'SimUAV-Beta',
      flight_status: 'flying',
      ue_connection_status: 'connected',
      current_position: { 
        latitude: 24.7901 + (Math.random() - 0.5) * 0.01, 
        longitude: 120.9984 + (Math.random() - 0.5) * 0.01, 
        altitude: 470 + Math.random() * 30,
        timestamp: new Date().toISOString(),
        speed: 10 + Math.random() * 6,
        heading: Math.random() * 360
      },
      signal_quality: {
        rsrp_dbm: -85 + Math.random() * 15,
        rsrq_db: -12 + Math.random() * 6,
        sinr_db: 18 + Math.random() * 8,
        cqi: Math.floor(Math.random() * 8) + 10,
        throughput_mbps: 25 + Math.random() * 12,
        latency_ms: 8 + Math.random() * 10,
        packet_loss_rate: Math.random() * 0.3,
        jitter_ms: 0.5 + Math.random() * 2,
        link_budget_margin_db: 10 + Math.random() * 10,
        doppler_shift_hz: 80 + Math.random() * 80,
        beam_alignment_score: 0.88 + Math.random() * 0.12,
        interference_level_db: -105 + Math.random() * 8,
        timestamp: new Date().toISOString(),
        measurement_confidence: 0.9 + Math.random() * 0.1
      },
      last_update: new Date().toISOString()
    }
  ];
  
  return { uavs: mockUAVs, total: mockUAVs.length };
};

/**
 * 獲取系統狀態
 */
export const getSystemStatus = async (): Promise<SystemStatus> => {
  try {
    const response = await retryRequest(() => 
      netstackApi.get<SystemStatus>('/api/v1/system/status')
    );
    return response.data;
  } catch (error) {
    console.warn('獲取系統狀態失敗，使用模擬數據:', (error as Error).message);
    
    if (RETRY_CONFIG.enableMockData) {
      return generateMockSystemStatus();
    }
    
    throw error;
  }
};

/**
 * 獲取 UAV 列表
 */
export const getUAVList = async (): Promise<{ uavs: UAVData[]; total: number }> => {
  try {
    const response = await retryRequest(() =>
      netstackApi.get<{ uavs: UAVData[]; total: number }>('/api/v1/uav')
    );
    return response.data;
  } catch (error) {
    console.warn('獲取 UAV 列表失敗，使用模擬數據:', (error as Error).message);
    
    if (RETRY_CONFIG.enableMockData) {
      return generateMockUAVData();
    }
    
    throw error;
  }
};

/**
 * 獲取特定 UAV 的詳細信息
 */
export const getUAVDetails = async (uavId: string): Promise<UAVData> => {
  try {
    const response = await retryRequest(() =>
      netstackApi.get<UAVData>(`/api/v1/uav/${uavId}`)
    );
    return response.data;
  } catch (error) {
    console.warn(`獲取 UAV ${uavId} 詳細信息失敗，使用模擬數據:`, (error as Error).message);
    
    if (RETRY_CONFIG.enableMockData) {
      const mockData = generateMockUAVData();
      const uav = mockData.uavs.find(u => u.uav_id === uavId);
      if (uav) {
        return uav;
      }
    }
    
    throw error;
  }
};

/**
 * 獲取 UAV 軌跡數據
 */
export const getUAVTrajectory = async (uavId?: string): Promise<any> => {
  try {
    const url = uavId ? `/api/v1/uav/trajectory/${uavId}` : '/api/v1/uav/trajectory';
    const response = await retryRequest(() => netstackApi.get(url));
    return response.data;
  } catch (error) {
    console.warn('獲取 UAV 軌跡失敗，使用模擬數據:', (error as Error).message);
    
    if (RETRY_CONFIG.enableMockData) {
      return {
        trajectories: [],
        timestamp: new Date().toISOString()
      };
    }
    
    throw error;
  }
};

/**
 * 獲取干擾數據
 */
export const getInterferenceStatus = async (): Promise<any> => {
  try {
    const response = await retryRequest(() => 
      netstackApi.get('/api/v1/interference/status')
    );
    return response.data;
  } catch (error) {
    console.warn('獲取干擾狀態失敗，使用模擬數據:', (error as Error).message);
    
    if (RETRY_CONFIG.enableMockData) {
      return {
        interference_level: 'low',
        sources: [],
        timestamp: new Date().toISOString()
      };
    }
    
    throw error;
  }
};

/**
 * 獲取 Mesh 網路拓撲
 */
export const getMeshTopology = async (): Promise<any> => {
  try {
    const response = await retryRequest(() =>
      netstackApi.get('/api/v1/mesh/topology')
    );
    return response.data;
  } catch (error) {
    console.warn('獲取 Mesh 拓撲失敗，使用模擬數據:', (error as Error).message);
    
    if (RETRY_CONFIG.enableMockData) {
      return {
        nodes: [
          { id: 'gateway-1', type: 'gateway', position: { x: 100, y: 100 }, status: 'active' },
          { id: 'mesh-1', type: 'mesh', position: { x: 200, y: 150 }, status: 'active' },
          { id: 'mesh-2', type: 'mesh', position: { x: 300, y: 100 }, status: 'active' },
          { id: 'uav-1', type: 'uav', position: { x: 250, y: 50 }, status: 'active' }
        ],
        links: [
          { source: 'gateway-1', target: 'mesh-1', strength: 0.8 },
          { source: 'mesh-1', target: 'mesh-2', strength: 0.7 },
          { source: 'mesh-1', target: 'uav-1', strength: 0.6 },
          { source: 'mesh-2', target: 'uav-1', strength: 0.5 }
        ],
        timestamp: new Date().toISOString()
      };
    }
    
    throw error;
  }
};

/**
 * 獲取 Mesh 節點列表
 */
export const getMeshNodes = async (): Promise<any> => {
  try {
    const response = await retryRequest(() =>
      netstackApi.get('/api/v1/mesh/nodes')
    );
    return response.data;
  } catch (error) {
    console.warn('獲取 Mesh 節點失敗，使用模擬數據:', (error as Error).message);
    
    if (RETRY_CONFIG.enableMockData) {
      return {
        nodes: [
          { id: 'mesh-1', name: 'Mesh Node 1', status: 'active', connections: 3 },
          { id: 'mesh-2', name: 'Mesh Node 2', status: 'active', connections: 2 }
        ],
        total: 2,
        timestamp: new Date().toISOString()
      };
    }
    
    throw error;
  }
};

/**
 * 獲取 OneWeb 星座狀態
 */
export const getOneWebStatus = async (): Promise<any> => {
  try {
    const response = await netstackApi.get('/api/v1/oneweb/constellation/status');
    return response.data;
  } catch (error) {
    console.error('獲取 OneWeb 狀態失敗:', error);
    throw error;
  }
};

/**
 * 獲取 Sionna 狀態
 */
export const getSionnaStatus = async (): Promise<any> => {
  try {
    const response = await netstackApi.get('/api/v1/sionna/status');
    return response.data;
  } catch (error) {
    console.error('獲取 Sionna 狀態失敗:', error);
    throw error;
  }
};

/**
 * 執行系統發現
 */
export const runSystemDiscovery = async (): Promise<any> => {
  try {
    const response = await netstackApi.get('/api/v1/system/discovery');
    return response.data;
  } catch (error) {
    console.error('執行系統發現失敗:', error);
    throw error;
  }
};

/**
 * 獲取 UAV-Mesh Failover 統計
 */
export const getUAVMeshStats = async (): Promise<any> => {
  try {
    const response = await netstackApi.get('/api/v1/uav-mesh-failover/stats');
    return response.data;
  } catch (error) {
    console.error('獲取 UAV-Mesh 統計失敗:', error);
    throw error;
  }
};

export default netstackApi; 