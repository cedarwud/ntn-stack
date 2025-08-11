import api from './api';
import ApiRoutes from '../config/apiRoutes';

// 模擬相關類型定義
interface SimulationParameters {
  carrier_frequency: number;
  bandwidth: number;
  num_satellite_beams: number;
  num_ue_per_beam: number;
  num_jammers?: number;
  terrain_type?: string;
  seed?: number;
}

interface SimulationResult {
  id: string;
  parameters: SimulationParameters;
  created_at: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  cfr_map_url?: string;
  sinr_map_url?: string;
  doppler_map_url?: string;
}

// 創建新模擬
export const createSimulation = async (parameters: SimulationParameters): Promise<SimulationResult> => {
  try {
    const response = await api.post<SimulationResult>(ApiRoutes.simulations.createSimulation, parameters);
    return response.data;
  } catch (error) {
    console.error('創建模擬失敗:', error);
    throw error;
  }
};

// 獲取CFR地圖
export const getCFRMap = async (simulationId: string): Promise<Blob> => {
  try {
    const response = await api.get(`${ApiRoutes.simulations.getCFRMap}?simulation_id=${simulationId}`, {
      responseType: 'blob'
    });
    return response.data;
  } catch (error) {
    console.error(`獲取CFR地圖失敗: ${simulationId}`, error);
    throw error;
  }
};

// 獲取SINR地圖
export const getSINRMap = async (simulationId: string): Promise<Blob> => {
  try {
    const response = await api.get(`${ApiRoutes.simulations.getSINRMap}?simulation_id=${simulationId}`, {
      responseType: 'blob'
    });
    return response.data;
  } catch (error) {
    console.error(`獲取SINR地圖失敗: ${simulationId}`, error);
    throw error;
  }
};

// 獲取多普勒地圖
export const getDopplerMap = async (simulationId: string): Promise<Blob> => {
  try {
    const response = await api.get(`${ApiRoutes.simulations.getDopplerMap}?simulation_id=${simulationId}`, {
      responseType: 'blob'
    });
    return response.data;
  } catch (error) {
    console.error(`獲取多普勒地圖失敗: ${simulationId}`, error);
    throw error;
  }
};

// 獲取模擬結果
export const getSimulationResults = async (simulationId: string): Promise<SimulationResult> => {
  try {
    const response = await api.get<SimulationResult>(ApiRoutes.simulations.getResults(simulationId));
    return response.data;
  } catch (error) {
    console.error(`獲取模擬結果失敗: ${simulationId}`, error);
    throw error;
  }
};

export default {
  createSimulation,
  getCFRMap,
  getSINRMap,
  getDopplerMap,
  getSimulationResults
}; 