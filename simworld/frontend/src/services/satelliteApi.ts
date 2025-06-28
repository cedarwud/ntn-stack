import api from './api';
import ApiRoutes from '../config/apiRoutes';

// 統一的API響應格式
export interface ApiResponse<T> {
  status: 'success' | 'error' | 'warning';
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
    timestamp: string;
  };
  meta?: Record<string, unknown>;
  timestamp: string;
}

// 統一的衛星位置格式
export interface SatellitePosition {
  latitude: number;
  longitude: number;
  altitude: number;
  timestamp: string;
  ecef_x_km?: number;
  ecef_y_km?: number;
  ecef_z_km?: number;
  elevation_deg?: number;
  azimuth_deg?: number;
  distance_km?: number;
}

// 衛星速度信息
export interface SatelliteVelocity {
  speed_km_s: number;
  velocity_x: number;
  velocity_y: number;
  velocity_z: number;
}

// 軌道參數
export interface SatelliteOrbitalParameters {
  period_minutes: number;
  inclination_deg: number;
  apogee_km: number;
  perigee_km: number;
  eccentricity: number;
}

// TLE數據
export interface TLEData {
  line1: string;
  line2: string;
  epoch: string;
  source: string;
  last_updated: string;
}

// 標準化的衛星信息
export interface StandardSatelliteInfo {
  id: number;
  name: string;
  norad_id: number;
  position: SatellitePosition;
  velocity?: SatelliteVelocity;
  orbital_parameters: SatelliteOrbitalParameters;
  tle_data?: TLEData;
  constellation?: string;
  operational_status?: string;
  launch_date?: string;
}

// 傳統格式保持向後兼容
interface Satellite {
  id: string;
  name: string;
  norad_id: number;
  description?: string;
  created_at: string;
  updated_at?: string;
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

// 統一的錯誤代碼
export enum ErrorCode {
  TLE_FETCH_FAILED = 'TLE_FETCH_FAILED',
  TLE_INVALID_FORMAT = 'TLE_INVALID_FORMAT',
  ORBIT_CALCULATION_FAILED = 'ORBIT_CALCULATION_FAILED',
  SATELLITE_NOT_FOUND = 'SATELLITE_NOT_FOUND',
  INVALID_COORDINATES = 'INVALID_COORDINATES',
  NETWORK_ERROR = 'NETWORK_ERROR',
  INTERNAL_SERVER_ERROR = 'INTERNAL_SERVER_ERROR'
}

// 統一的錯誤處理類
export class SatelliteApiError extends Error {
  constructor(
    public code: ErrorCode,
    message: string,
    public details?: Record<string, unknown>
  ) {
    super(message);
    this.name = 'SatelliteApiError';
  }
}

// API響應驗證工具
export class ApiResponseValidator {
  static validateSatelliteInfo(data: unknown): data is StandardSatelliteInfo {
    return (
      typeof data.id === 'number' &&
      typeof data.name === 'string' &&
      typeof data.norad_id === 'number' &&
      data.position &&
      typeof data.position.latitude === 'number' &&
      typeof data.position.longitude === 'number' &&
      typeof data.position.altitude === 'number' &&
      data.orbital_parameters &&
      typeof data.orbital_parameters.period_minutes === 'number'
    );
  }

  static validateApiResponse<T>(response: unknown): response is ApiResponse<T> {
    return (
      response &&
      typeof response === 'object' &&
      'status' in response &&
      typeof (response as { status: unknown }).status === 'string' &&
      ['success', 'error', 'warning'].includes((response as { status: string }).status) &&
      'timestamp' in response &&
      typeof (response as { timestamp: unknown }).timestamp === 'string'
    );
  }

  static validateCoordinates(lat: number, lon: number, alt: number): boolean {
    return (
      lat >= -90 && lat <= 90 &&
      lon >= -180 && lon <= 180 &&
      alt >= -500 // 允許海平面以下500m
    );
  }
}

// 統一的API請求處理器
// This function is currently unused but kept for future API standardization
/* async function handleApiRequest<T>(
  request: () => Promise<unknown>,
  validator?: (data: unknown) => data is T
): Promise<T> {
  try {
    const response = await request();
    
    // 檢查是否是新的統一API響應格式
    if (ApiResponseValidator.validateApiResponse(response.data)) {
      const apiResponse = response.data as ApiResponse<T>;
      
      if (apiResponse.status === 'error') {
        throw new SatelliteApiError(
          (apiResponse.error?.code as ErrorCode) || ErrorCode.INTERNAL_SERVER_ERROR,
          apiResponse.error?.message || '未知錯誤',
          apiResponse.error?.details
        );
      }
      
      if (apiResponse.data && validator && !validator(apiResponse.data)) {
        throw new SatelliteApiError(
          ErrorCode.INTERNAL_SERVER_ERROR,
          '響應數據格式驗證失敗'
        );
      }
      
      return apiResponse.data as T;
    }
    
    // 向後兼容：處理舊格式響應
    if (validator && !validator(response.data)) {
      throw new SatelliteApiError(
        ErrorCode.INTERNAL_SERVER_ERROR,
        '響應數據格式驗證失敗'
      );
    }
    
    return response.data;
    
  } catch (error) {
    if (error instanceof SatelliteApiError) {
      throw error;
    }
    
    // 處理網絡錯誤和其他錯誤
    const axiosError = error as { response?: { status: number; data?: { message?: string } }; message?: string };
    if (axiosError.response) {
      const status = axiosError.response.status;
      const message = axiosError.response.data?.message || axiosError.message;
      
      if (status === 404) {
        throw new SatelliteApiError(ErrorCode.SATELLITE_NOT_FOUND, message);
      } else if (status >= 500) {
        throw new SatelliteApiError(ErrorCode.INTERNAL_SERVER_ERROR, message);
      } else {
        throw new SatelliteApiError(ErrorCode.NETWORK_ERROR, message);
      }
    }
    
    throw new SatelliteApiError(
      ErrorCode.NETWORK_ERROR,
      axiosError.message || '網絡請求失敗'
    );
  }
} */

// API服務函數

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
  const url = ApiRoutes.satellites.getPasses(id);
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
  const url = ApiRoutes.satellites.getOrbit(id);
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