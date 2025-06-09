// 換手相關類型定義

export interface HandoverState {
  currentSatellite: string;    // AT - 當前接入衛星
  predictedSatellite: string;  // AT+Δt - 預測下一時段接入衛星
  handoverTime: number;        // Tp - 預測換手觸發時間 (timestamp)
  status: 'idle' | 'predicting' | 'handover' | 'complete' | 'failed';
  confidence: number;          // 預測信心度 0-1
  deltaT: number;             // Δt 時間間隔 (秒)
}

export interface BinarySearchIteration {
  iteration: number;
  startTime: number;
  endTime: number;
  midTime: number;
  satellite: string;
  precision: number;
  completed: boolean;
}

export interface TimePredictionData {
  currentTime: number;        // T - 當前時間
  futureTime: number;         // T+Δt - 預測時間
  handoverTime?: number;      // Tp - 換手觸發時間
  iterations: BinarySearchIteration[];
  accuracy: number;           // 預測準確率
}

export interface SatelliteConnection {
  satelliteId: string;
  satelliteName: string;
  elevation: number;
  azimuth: number;
  distance: number;
  signalStrength: number;
  isConnected: boolean;
  isPredicted: boolean;
}

export interface HandoverEvent {
  id: string;
  timestamp: number;
  fromSatellite: string;
  toSatellite: string;
  duration: number;           // 換手持續時間 (ms)
  success: boolean;
  reason: 'automatic' | 'manual' | 'fallback';
}