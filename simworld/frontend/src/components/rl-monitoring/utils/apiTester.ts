/**
 * API 端點整合測試工具
 * 實現 @tr.md 任務 1.2 - 整合現有 API 端點
 */

import { apiClient } from '../../../services/api-client';

export interface APITestResult {
  endpoint: string;
  status: 'success' | 'error';
  statusCode?: number;
  responseTime: number;
  data?: any;
  error?: string;
}

export interface APITestSummary {
  totalEndpoints: number;
  successCount: number;
  errorCount: number;
  successRate: number;
  avgResponseTime: number;
  results: APITestResult[];
}

/**
 * API 端點配置
 */
const API_ENDPOINTS = [
  // 基礎 RL API
  { name: 'RL Health Check', path: '/api/v1/rl/health', method: 'GET' },
  { name: 'RL Status', path: '/api/v1/rl/status', method: 'GET' },
  { name: 'RL Algorithms', path: '/api/v1/rl/algorithms', method: 'GET' },
  { name: 'Training Status Summary', path: '/api/v1/rl/training/status-summary', method: 'GET' },
  { name: 'Training Sessions', path: '/api/v1/rl/training/sessions', method: 'GET' },
  { name: 'Performance Metrics', path: '/api/v1/rl/training/performance-metrics', method: 'GET' },
  
  // Phase 3 API (可能不存在)
  { name: 'Phase 3 Health', path: '/api/v1/rl/phase-3/health', method: 'GET', optional: true },
  
  // 系統相關 API
  { name: 'AI Decision Engine Health', path: '/api/v2/decision/health', method: 'GET' },
  { name: 'AI Decision Engine Status', path: '/api/v2/decision/status', method: 'GET' },
  { name: 'Algorithm Performance Comparison', path: '/api/algorithm-performance/four-way-comparison', method: 'GET' }
];

/**
 * 測試單個 API 端點
 */
async function testSingleEndpoint(endpoint: typeof API_ENDPOINTS[0]): Promise<APITestResult> {
  const startTime = Date.now();
  
  try {
    let response: any;
    
    // 使用現有的 apiClient 方法
    switch (endpoint.path) {
      case '/api/v1/rl/training/status-summary':
        response = await apiClient.getTrainingStatusSummary();
        break;
      case '/api/v1/rl/training/sessions':
        response = await apiClient.getRLTrainingSessions();
        break;
      case '/api/v1/rl/training/performance-metrics':
        response = await apiClient.getTrainingPerformanceMetrics();
        break;
      case '/api/v2/decision/health':
        response = await apiClient.getAIDecisionEngineHealth();
        break;
      case '/api/v2/decision/status':
        response = await apiClient.getAIDecisionEngineStatus();
        break;
      default:
        // 使用通用 fetch
        const fetchResponse = await fetch(`http://localhost:8080${endpoint.path}`);
        response = await fetchResponse.json();
        break;
    }
    
    const endTime = Date.now();
    const responseTime = endTime - startTime;
    
    return {
      endpoint: endpoint.name,
      status: 'success',
      statusCode: 200,
      responseTime,
      data: response
    };
    
  } catch (error) {
    const endTime = Date.now();
    const responseTime = endTime - startTime;
    
    return {
      endpoint: endpoint.name,
      status: 'error',
      responseTime,
      error: error instanceof Error ? error.message : String(error)
    };
  }
}

/**
 * 測試所有 API 端點
 */
export async function testAllAPIEndpoints(): Promise<APITestSummary> {
  console.log('🔍 開始 API 端點連通性測試...');
  
  const results: APITestResult[] = [];
  
  // 並行測試所有端點
  const testPromises = API_ENDPOINTS.map(endpoint => testSingleEndpoint(endpoint));
  const testResults = await Promise.allSettled(testPromises);
  
  testResults.forEach((result, index) => {
    if (result.status === 'fulfilled') {
      results.push(result.value);
    } else {
      results.push({
        endpoint: API_ENDPOINTS[index].name,
        status: 'error',
        responseTime: 0,
        error: result.reason?.message || 'Unknown error'
      });
    }
  });
  
  // 計算統計信息
  const successCount = results.filter(r => r.status === 'success').length;
  const errorCount = results.filter(r => r.status === 'error').length;
  const successRate = (successCount / results.length) * 100;
  const avgResponseTime = results.reduce((sum, r) => sum + r.responseTime, 0) / results.length;
  
  const summary: APITestSummary = {
    totalEndpoints: results.length,
    successCount,
    errorCount,
    successRate,
    avgResponseTime,
    results
  };
  
  // 輸出測試結果
  console.log('📊 API 測試結果摘要:');
  console.log(`✅ 成功: ${successCount}/${results.length} (${successRate.toFixed(1)}%)`);
  console.log(`❌ 失敗: ${errorCount}`);
  console.log(`⏱️ 平均響應時間: ${avgResponseTime.toFixed(2)}ms`);
  
  // 輸出詳細結果
  results.forEach(result => {
    const status = result.status === 'success' ? '✅' : '❌';
    console.log(`${status} ${result.endpoint}: ${result.responseTime.toFixed(2)}ms`);
    if (result.error) {
      console.log(`   Error: ${result.error}`);
    }
  });
  
  return summary;
}

/**
 * 測試 Phase 3 視覺化 API
 */
export async function testPhase3APIs(): Promise<APITestResult[]> {
  const phase3Endpoints = [
    {
      name: 'Phase 3 Visualization Generate',
      test: async () => {
        const response = await fetch('/api/v1/rl/phase-3/visualizations/generate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            visualization_type: 'feature_importance',
            data_source: 'current_training',
            format: 'plotly'
          })
        });
        return await response.json();
      }
    },
    {
      name: 'Phase 3 Decision Explanation',
      test: async () => {
        const response = await fetch('/api/v1/rl/phase-3/explain/decision', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            algorithm: 'current_active',
            include_reasoning: true
          })
        });
        return await response.json();
      }
    },
    {
      name: 'Phase 3 Algorithm Comparison',
      test: async () => {
        const response = await fetch('/api/v1/rl/phase-3/algorithms/comparison', {
          method: 'GET'
        });
        return await response.json();
      }
    }
  ];
  
  const results: APITestResult[] = [];
  
  for (const endpoint of phase3Endpoints) {
    const startTime = Date.now();
    try {
      const data = await endpoint.test();
      const endTime = Date.now();
      
      results.push({
        endpoint: endpoint.name,
        status: 'success',
        responseTime: endTime - startTime,
        data
      });
    } catch (error) {
      const endTime = Date.now();
      
      results.push({
        endpoint: endpoint.name,
        status: 'error',
        responseTime: endTime - startTime,
        error: error instanceof Error ? error.message : String(error)
      });
    }
  }
  
  return results;
}

/**
 * 健康檢查所有關鍵服務
 */
export async function healthCheckAllServices(): Promise<{
  overall: 'healthy' | 'degraded' | 'critical';
  services: Record<string, 'up' | 'down' | 'degraded'>;
  details: any;
}> {
  try {
    // 測試關鍵服務
    const [rlHealth, aiHealth] = await Promise.allSettled([
      fetch('/api/v1/rl/health').then(r => r.json()),
      fetch('/api/v2/decision/health').then(r => r.json())
    ]);
    
    const services: Record<string, 'up' | 'down' | 'degraded'> = {};
    
    // RL 服務狀態
    if (rlHealth.status === 'fulfilled' && rlHealth.value.status === 'healthy') {
      services.rl_service = 'up';
    } else {
      services.rl_service = 'down';
    }
    
    // AI 決策引擎狀態
    if (aiHealth.status === 'fulfilled') {
      services.ai_decision_engine = 'up';
    } else {
      services.ai_decision_engine = 'down';
    }
    
    // 計算總體健康狀態
    const downServices = Object.values(services).filter(status => status === 'down').length;
    const degradedServices = Object.values(services).filter(status => status === 'degraded').length;
    
    let overall: 'healthy' | 'degraded' | 'critical';
    if (downServices === 0 && degradedServices === 0) {
      overall = 'healthy';
    } else if (downServices <= 1) {
      overall = 'degraded';
    } else {
      overall = 'critical';
    }
    
    return {
      overall,
      services,
      details: {
        rl_health: rlHealth.status === 'fulfilled' ? rlHealth.value : null,
        ai_health: aiHealth.status === 'fulfilled' ? aiHealth.value : null
      }
    };
    
  } catch (error) {
    return {
      overall: 'critical',
      services: {},
      details: { error: error instanceof Error ? error.message : String(error) }
    };
  }
}

/**
 * 工具函數：格式化測試結果為表格
 */
export function formatTestResultsAsTable(summary: APITestSummary): string {
  let table = '\n📊 API 端點測試結果:\n';
  table += '┌─────────────────────────────────────┬──────────┬─────────────┐\n';
  table += '│ Endpoint                            │ Status   │ Time (ms)   │\n';
  table += '├─────────────────────────────────────┼──────────┼─────────────┤\n';
  
  summary.results.forEach(result => {
    const endpoint = result.endpoint.padEnd(35);
    const status = (result.status === 'success' ? '✅ OK' : '❌ ERROR').padEnd(8);
    const time = result.responseTime.toFixed(2).padStart(11);
    table += `│ ${endpoint} │ ${status} │ ${time} │\n`;
  });
  
  table += '└─────────────────────────────────────┴──────────┴─────────────┘\n';
  table += `\n📈 總結: ${summary.successCount}/${summary.totalEndpoints} 成功 (${summary.successRate.toFixed(1)}%)\n`;
  table += `⏱️ 平均響應時間: ${summary.avgResponseTime.toFixed(2)}ms\n`;
  
  return table;
}

/**
 * 導出便捷測試函數
 */
export const apiTester = {
  testAll: testAllAPIEndpoints,
  testPhase3: testPhase3APIs,
  healthCheck: healthCheckAllServices,
  formatResults: formatTestResultsAsTable
};