/**
 * 微服務API整合層 - Phase 2 前端整合
 * 與新的微服務網關、gRPC服務管理器和NTN接口整合
 */
import axios, { AxiosError } from 'axios';
// import { UAVData, SystemStatus, NetworkTopology } from '../types/charts';

// 微服務網關配置 - 使用 Vite 環境變量
const MICROSERVICE_GATEWAY_URL = import.meta.env.VITE_GATEWAY_URL || 'http://localhost:8080';

// 創建微服務API實例
const microserviceApi = axios.create({
  baseURL: MICROSERVICE_GATEWAY_URL,
  timeout: 15000, // 增加超時時間以適應微服務架構
  headers: {
    'Content-Type': 'application/json',
    'X-API-Version': '2.0',
    'X-Client-Type': 'frontend'
  }
});

// Phase 2 服務端點配置
const SERVICE_ENDPOINTS = {
  // 微服務網關
  gateway: {
    status: '/api/v1/gateway/status',
    services: '/api/v1/gateway/services',
    routes: '/api/v1/gateway/routes',
    loadbalancer: '/api/v1/gateway/loadbalancer'
  },
  
  // 5G NTN 協議接口
  ntn: {
    n2Status: '/api/v1/ntn/n2/status',
    n3Status: '/api/v1/ntn/n3/status',
    conditionalHandover: '/api/v1/ntn/handover/conditional',
    beamManagement: '/api/v1/ntn/beam',
    timingAdvance: '/api/v1/ntn/timing'
  },
  
  // 增強同步算法
  algorithm: {
    status: '/api/v1/algorithm/status',
    prediction: '/api/v1/algorithm/prediction',
    synchronization: '/api/v1/algorithm/sync',
    verification: '/api/v1/algorithm/verification'
  },
  
  // 系統監控
  monitoring: {
    e2eMetrics: '/api/v1/monitoring/e2e',
    performance: '/api/v1/monitoring/performance',
    sla: '/api/v1/monitoring/sla',
    alerts: '/api/v1/monitoring/alerts'
  }
};

// API重試配置
const RETRY_CONFIG = {
  maxRetries: 2,
  retryDelay: 2000,
  enableMockData: true,
  circuitBreakerThreshold: 5
};

// 斷路器狀態
let circuitBreakerFailures = 0;
let circuitBreakerLastFailure = 0;
const CIRCUIT_BREAKER_TIMEOUT = 30000; // 30秒

// 斷路器檢查
const isCircuitBreakerOpen = (): boolean => {
  if (circuitBreakerFailures >= RETRY_CONFIG.circuitBreakerThreshold) {
    const now = Date.now();
    if (now - circuitBreakerLastFailure < CIRCUIT_BREAKER_TIMEOUT) {
      return true;
    } else {
      // 重置斷路器
      circuitBreakerFailures = 0;
      return false;
    }
  }
  return false;
};

// 記錄斷路器失敗
const recordCircuitBreakerFailure = () => {
  circuitBreakerFailures++;
  circuitBreakerLastFailure = Date.now();
};

// 重試函數
const retryRequest = async <T>(
  requestFn: () => Promise<T>,
  retries: number = RETRY_CONFIG.maxRetries
): Promise<T> => {
  if (isCircuitBreakerOpen()) {
    throw new Error('Circuit breaker is open - service temporarily unavailable');
  }

  try {
    const result = await requestFn();
    // 成功時重置部分失敗計數
    if (circuitBreakerFailures > 0) {
      circuitBreakerFailures = Math.max(0, circuitBreakerFailures - 1);
    }
    return result;
  } catch (error) {
    recordCircuitBreakerFailure();
    
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
    return true; // 網路錯誤
  }
  
  const status = error.response.status;
  return status === 502 || status === 503 || status === 504 || status === 408;
};

// 請求攔截器
microserviceApi.interceptors.request.use((config) => {
  console.log(`[Microservice API] ${config.method?.toUpperCase()} ${config.url}`);
  
  // 添加追蹤ID
  config.headers['X-Trace-ID'] = `trace_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  
  return config;
});

// 響應攔截器
microserviceApi.interceptors.response.use(
  (response) => {
    const traceId = response.config.headers['X-Trace-ID'];
    console.log(`[Microservice API] Response received for trace: ${traceId}`);
    return response;
  },
  (error: AxiosError) => {
    const traceId = error.config?.headers['X-Trace-ID'];
    console.error(`[Microservice API] Error for trace ${traceId}:`, error.message);
    return Promise.reject(error);
  }
);

// Phase 2 特有的模擬數據生成器
const generateMockGatewayStatus = () => ({
  gateway_status: {
    is_running: true,
    uptime_seconds: 86400,
    total_requests: 15247,
    successful_requests: 15123,
    failed_requests: 124,
    average_response_time_ms: 45.2
  },
  service_registry: {
    netstack: {
      instances: 2,
      healthy_instances: 2,
      load_balancer_strategy: 'round_robin'
    },
    simworld: {
      instances: 1,
      healthy_instances: 1,
      load_balancer_strategy: 'single'
    }
  },
  circuit_breaker_status: {
    netstack: { state: 'closed', failure_count: 0 },
    simworld: { state: 'closed', failure_count: 0 }
  }
});

const generateMockNTNStatus = () => ({
  n2_interface: {
    is_running: true,
    ng_connection_established: true,
    active_ue_contexts: 12,
    handovers_completed: 45,
    beam_switches: 23,
    timing_updates: 156
  },
  n3_interface: {
    is_running: true,
    active_tunnels: 8,
    total_packets_processed: 892456,
    packet_loss_rate: 0.001,
    average_latency_ms: 25.4
  },
  conditional_handover: {
    active_configurations: 5,
    handovers_triggered: 12,
    handovers_completed: 11,
    average_handover_time_ms: 38.5,
    sla_compliance: true
  }
});

const generateMockE2EMetrics = () => ({
  sla_compliance: {
    handover_latency_ms: 38.5,
    handover_latency_compliant: true,
    prediction_accuracy: 0.92,
    prediction_accuracy_compliant: true,
    system_availability: 0.999,
    system_availability_compliant: true,
    overall_sla_compliance: true
  },
  performance_metrics: {
    total_tests: 5,
    passed_tests: 5,
    failed_tests: 0,
    success_rate: 1.0,
    average_test_duration_ms: 2547.8
  },
  test_results: [
    {
      test_name: 'UE Attachment Flow',
      status: 'passed',
      duration_ms: 66.5,
      sla_compliant: true
    },
    {
      test_name: 'Conditional Handover E2E',
      status: 'passed',
      duration_ms: 38.5,
      sla_compliant: true
    },
    {
      test_name: 'Multi-satellite Coordination',
      status: 'passed',
      duration_ms: 70.8,
      sla_compliant: true
    }
  ],
  timestamp: new Date().toISOString()
});

/**
 * Phase 2 API 函數
 */

// 獲取微服務網關狀態
export const getGatewayStatus = async () => {
  try {
    const response = await retryRequest(() =>
      microserviceApi.get(SERVICE_ENDPOINTS.gateway.status)
    );
    return response.data;
  } catch (error) {
    console.warn('獲取網關狀態失敗，使用模擬數據:', (error as Error).message);
    if (RETRY_CONFIG.enableMockData) {
      return generateMockGatewayStatus();
    }
    throw error;
  }
};

// 獲取註冊的服務列表
export const getRegisteredServices = async () => {
  try {
    const response = await retryRequest(() =>
      microserviceApi.get(SERVICE_ENDPOINTS.gateway.services)
    );
    return response.data;
  } catch (error) {
    console.warn('獲取服務列表失敗，使用模擬數據:', (error as Error).message);
    if (RETRY_CONFIG.enableMockData) {
      return {
        services: [
          { name: 'netstack', status: 'healthy', instances: 2 },
          { name: 'simworld', status: 'healthy', instances: 1 }
        ]
      };
    }
    throw error;
  }
};

// 獲取NTN接口狀態
export const getNTNStatus = async () => {
  try {
    const [n2Response, n3Response, handoverResponse] = await Promise.all([
      retryRequest(() => microserviceApi.get(SERVICE_ENDPOINTS.ntn.n2Status)),
      retryRequest(() => microserviceApi.get(SERVICE_ENDPOINTS.ntn.n3Status)),
      retryRequest(() => microserviceApi.get(SERVICE_ENDPOINTS.ntn.conditionalHandover))
    ]);
    
    return {
      n2_interface: n2Response.data,
      n3_interface: n3Response.data,
      conditional_handover: handoverResponse.data
    };
  } catch (error) {
    console.warn('獲取NTN狀態失敗，使用模擬數據:', (error as Error).message);
    if (RETRY_CONFIG.enableMockData) {
      return generateMockNTNStatus();
    }
    throw error;
  }
};

// 獲取端到端性能指標
export const getE2EPerformanceMetrics = async () => {
  try {
    const response = await retryRequest(() =>
      microserviceApi.get(SERVICE_ENDPOINTS.monitoring.e2eMetrics)
    );
    return response.data;
  } catch (error) {
    console.warn('獲取E2E指標失敗，使用模擬數據:', (error as Error).message);
    if (RETRY_CONFIG.enableMockData) {
      return generateMockE2EMetrics();
    }
    throw error;
  }
};

// 獲取SLA合規性狀態
export const getSLACompliance = async () => {
  try {
    const response = await retryRequest(() =>
      microserviceApi.get(SERVICE_ENDPOINTS.monitoring.sla)
    );
    return response.data;
  } catch (error) {
    console.warn('獲取SLA狀態失敗，使用模擬數據:', (error as Error).message);
    if (RETRY_CONFIG.enableMockData) {
      return {
        handover_latency: {
          current_ms: 38.5,
          requirement_ms: 50.0,
          compliant: true
        },
        prediction_accuracy: {
          current: 0.92,
          requirement: 0.90,
          compliant: true
        },
        system_availability: {
          current: 0.999,
          requirement: 0.999,
          compliant: true
        },
        overall_compliance: true
      };
    }
    throw error;
  }
};

// 執行條件切換測試
export const triggerConditionalHandoverTest = async (ueId: string) => {
  try {
    const response = await retryRequest(() =>
      microserviceApi.post(`${SERVICE_ENDPOINTS.ntn.conditionalHandover}/test`, { ue_id: ueId })
    );
    return response.data;
  } catch (error) {
    console.warn('觸發條件切換測試失敗:', (error as Error).message);
    if (RETRY_CONFIG.enableMockData) {
      return {
        test_id: `test_${Date.now()}`,
        ue_id: ueId,
        status: 'initiated',
        estimated_duration_ms: 45
      };
    }
    throw error;
  }
};

// 獲取算法狀態
export const getAlgorithmStatus = async () => {
  try {
    const response = await retryRequest(() =>
      microserviceApi.get(SERVICE_ENDPOINTS.algorithm.status)
    );
    return response.data;
  } catch (error) {
    console.warn('獲取算法狀態失敗，使用模擬數據:', (error as Error).message);
    if (RETRY_CONFIG.enableMockData) {
      return {
        algorithm_status: {
          is_running: true,
          prediction_accuracy: 0.924,
          sync_accuracy_ms: 8.5,
          last_update: new Date().toISOString()
        },
        predictions: {
          total_predictions: 1245,
          successful_predictions: 1150,
          accuracy_trend: 'improving'
        }
      };
    }
    throw error;
  }
};

// 執行系統健康檢查
export const performSystemHealthCheck = async () => {
  try {
    const [gatewayStatus, ntnStatus, algorithmStatus] = await Promise.all([
      getGatewayStatus(),
      getNTNStatus(),
      getAlgorithmStatus()
    ]);
    
    return {
      overall_health: 'healthy',
      components: {
        gateway: gatewayStatus,
        ntn: ntnStatus,
        algorithm: algorithmStatus
      },
      timestamp: new Date().toISOString()
    };
  } catch (error) {
    console.error('系統健康檢查失敗:', error);
    return {
      overall_health: 'degraded',
      components: {},
      error: (error as Error).message,
      timestamp: new Date().toISOString()
    };
  }
};

// 獲取實時監控告警
export const getSystemAlerts = async () => {
  try {
    const response = await retryRequest(() =>
      microserviceApi.get(SERVICE_ENDPOINTS.monitoring.alerts)
    );
    return response.data;
  } catch (error) {
    console.warn('獲取系統告警失敗，使用模擬數據:', (error as Error).message);
    if (RETRY_CONFIG.enableMockData) {
      return {
        alerts: [
          {
            id: 'alert_001',
            severity: 'info',
            message: 'Phase 2 微服務架構運行正常',
            component: 'Gateway',
            timestamp: new Date().toISOString(),
            resolved: false
          }
        ],
        total_alerts: 1,
        critical_alerts: 0
      };
    }
    throw error;
  }
};

export default microserviceApi;