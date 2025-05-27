import api from './api';
import ApiRoutes from '../config/apiRoutes';

// 衛星相關類型定義
interface Satellite {
  id: string;
  name: string;
  norad_id: number;
  description?: string;
  created_at: string;
  updated_at?: string;
}

interface TLEData {
  satellite_id: string;
  line1: string;
  line2: string;
  epoch: string;
  created_at: string;
}

interface SatellitePass {
  satellite_id: string;
  start_time: string;
  end_time: string;
  max_elevation: number;
  duration_seconds: number;
}

interface OrbitPoint {
  satellite_id: string;
  timestamp: string;
  latitude: number;
  longitude: number;
  altitude: number;
}

// 獲取所有衛星
export const getSatellites = async (): Promise<Satellite[]> => {
  try {
    const response = await api.get<Satellite[]>(ApiRoutes.satellites.getAll);
    return response.data;
  } catch (error) {
    console.error('獲取衛星列表失敗:', error);
    throw error;
  }
};

// 根據ID獲取衛星
export const getSatelliteById = async (id: string): Promise<Satellite> => {
  try {
    const response = await api.get<Satellite>(ApiRoutes.satellites.getById(id));
    return response.data;
  } catch (error) {
    console.error(`獲取衛星 ${id} 失敗:`, error);
    throw error;
  }
};

// 獲取衛星的TLE數據
export const getSatelliteTLE = async (id: string): Promise<TLEData> => {
  try {
    const response = await api.get<TLEData>(ApiRoutes.satellites.getTLE(id));
    return response.data;
  } catch (error) {
    console.error(`獲取衛星 ${id} TLE數據失敗:`, error);
    throw error;
  }
};

// 獲取衛星過境數據
export const getSatellitePasses = async (
  id: string,
  startTime?: string,
  endTime?: string,
  minElevation?: number
): Promise<SatellitePass[]> => {
  let url = ApiRoutes.satellites.getPasses(id);
  const params: Record<string, string> = {};
  
  if (startTime) params.start_time = startTime;
  if (endTime) params.end_time = endTime;
  if (minElevation !== undefined) params.min_elevation = minElevation.toString();
  
  try {
    const response = await api.get<SatellitePass[]>(url, { params });
    return response.data;
  } catch (error) {
    console.error(`獲取衛星 ${id} 過境數據失敗:`, error);
    throw error;
  }
};

// 獲取衛星軌道
export const getSatelliteOrbit = async (
  id: string,
  startTime?: string,
  endTime?: string,
  pointCount?: number
): Promise<OrbitPoint[]> => {
  let url = ApiRoutes.satellites.getOrbit(id);
  const params: Record<string, string> = {};
  
  if (startTime) params.start_time = startTime;
  if (endTime) params.end_time = endTime;
  if (pointCount !== undefined) params.point_count = pointCount.toString();
  
  try {
    const response = await api.get<OrbitPoint[]>(url, { params });
    return response.data;
  } catch (error) {
    console.error(`獲取衛星 ${id} 軌道數據失敗:`, error);
    throw error;
  }
};

export default {
  getSatellites,
  getSatelliteById,
  getSatelliteTLE,
  getSatellitePasses,
  getSatelliteOrbit
}; 