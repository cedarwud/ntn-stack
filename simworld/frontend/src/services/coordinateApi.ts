import api from './api';
import ApiRoutes from '../config/apiRoutes';

// 座標相關類型定義
interface Coordinate {
  latitude: number;
  longitude: number;
  altitude?: number;
}

interface CoordinateConversionRequest {
  source_format: 'decimal' | 'dms' | 'utm';
  target_format: 'decimal' | 'dms' | 'utm';
  coordinates: Coordinate | string;
}

interface CoordinateConversionResponse {
  source: Coordinate | string;
  target: Coordinate | string;
  source_format: string;
  target_format: string;
}

interface CoordinateValidationResponse {
  is_valid: boolean;
  error_message?: string;
  normalized_coordinate?: Coordinate;
}

// 轉換座標
export const convertCoordinate = async (request: CoordinateConversionRequest): Promise<CoordinateConversionResponse> => {
  try {
    const response = await api.post<CoordinateConversionResponse>(
      ApiRoutes.coordinates.convert,
      request
    );
    return response.data;
  } catch (error) {
    console.error('座標轉換失敗:', error);
    throw error;
  }
};

// 驗證座標
export const validateCoordinate = async (coordinate: Coordinate | string, format: 'decimal' | 'dms' | 'utm' = 'decimal'): Promise<CoordinateValidationResponse> => {
  try {
    const response = await api.post<CoordinateValidationResponse>(
      ApiRoutes.coordinates.validate,
      {
        coordinate,
        format
      }
    );
    return response.data;
  } catch (error) {
    console.error('座標驗證失敗:', error);
    throw error;
  }
};

export default {
  convertCoordinate,
  validateCoordinate
}; 