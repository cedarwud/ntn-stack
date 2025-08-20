/**
 * 統一衛星軌道計算工具類
 * 消除重複的計算邏輯，統一處理所有軌道相關計算
 */

export interface TimeseriesPoint {
    time: string
    time_offset_seconds: number
    elevation_deg: number
    azimuth_deg: number
    range_km: number
    is_visible: boolean
}

export interface SphericalCoordinates {
    elevation_deg: number
    azimuth_deg: number
    range_km: number
}

export interface CartesianCoordinates {
    x: number
    y: number
    z: number
}

export interface OrbitCalculationResult {
    position: [number, number, number]
    isVisible: boolean
    progress: number
    currentPoint: TimeseriesPoint | null
}

/**
 * 統一衛星軌道計算器
 */
export class SatelliteOrbitCalculator {
    
    /**
     * 基於position_timeseries數據計算當前軌道位置
     * 這是核心方法，統一處理所有軌道計算
     * 修復：實現真正的升降軌跡，避免循環轉圈
     */
    static calculateOrbitPosition(
        timeseries: TimeseriesPoint[],
        currentTime: number,
        speedMultiplier: number = 1
    ): OrbitCalculationResult {
        if (!timeseries || timeseries.length === 0) {
            return {
                position: [0, -500, 0],
                isVisible: false,
                progress: 0,
                currentPoint: null
            };
        }

        // 🎯 修復時間進度計算：識別連續數據段並循環播放
        const maxTimeOffset = timeseries[timeseries.length - 1]?.time_offset_seconds || 0;
        
        // 🔍 識別連續的數據段（避免間隙問題）
        const continuousSegments: TimeseriesPoint[][] = [];
        let currentSegment: TimeseriesPoint[] = [timeseries[0]];
        
        for (let i = 1; i < timeseries.length; i++) {
            const timeDiff = timeseries[i].time_offset_seconds - timeseries[i-1].time_offset_seconds;
            
            if (timeDiff <= 60) { // 連續數據（≤60秒間隔）
                currentSegment.push(timeseries[i]);
            } else { // 發現間隙，開始新段
                if (currentSegment.length > 1) {
                    continuousSegments.push(currentSegment);
                }
                currentSegment = [timeseries[i]];
            }
        }
        
        if (currentSegment.length > 1) {
            continuousSegments.push(currentSegment);
        }
        
        // 選擇最長的連續段作為主要軌道
        const mainSegment = continuousSegments.reduce((longest, current) => 
            current.length > longest.length ? current : longest, continuousSegments[0] || []);
        
        if (!mainSegment || mainSegment.length < 2) {
            return {
                position: [0, -500, 0],
                isVisible: false,
                progress: 0,
                currentPoint: null
            };
        }
        
        // 在主要段內循環播放
        const segmentDuration = mainSegment[mainSegment.length - 1].time_offset_seconds - mainSegment[0].time_offset_seconds;
        const timeProgress = (currentTime * speedMultiplier) % segmentDuration;
        
        // 🔍 在主要段內尋找當前位置
        let currentIndex = 0;
        let nextIndex = 1;
        
        const adjustedTimeProgress = timeProgress + mainSegment[0].time_offset_seconds;
        
        for (let i = 0; i < mainSegment.length - 1; i++) {
            const currentTime_offset = mainSegment[i].time_offset_seconds;
            const nextTime_offset = mainSegment[i + 1].time_offset_seconds;
            
            if (adjustedTimeProgress >= currentTime_offset && adjustedTimeProgress <= nextTime_offset) {
                currentIndex = i;
                nextIndex = i + 1;
                break;
            }
        }
        
        const currentPoint = mainSegment[currentIndex];
        const nextPoint = mainSegment[nextIndex];
        
        // 計算在當前段內的比例
        const pointDuration = nextPoint.time_offset_seconds - currentPoint.time_offset_seconds;
        const pointProgress = adjustedTimeProgress - currentPoint.time_offset_seconds;
        const timeRatio = Math.max(0, Math.min(1, pointProgress / pointDuration));
        
        // 🔄 線性插值：在真實數據點之間平滑過渡
        const interpolated = this.interpolateTimeseriesPoint(currentPoint, nextPoint, timeRatio);
        
        // 🌍 轉換為3D座標（修復後的轉換）
        const position = this.sphericalToCartesian(interpolated);
        
        // ✅ 修復可見性判斷：基於真實仰角和API數據
        const isVisible = currentPoint.is_visible && interpolated.elevation_deg > 5; // 5度以上才可見
        
        return {
            position,
            isVisible,
            progress: timeProgress / segmentDuration,
            currentPoint: currentPoint
        };
    }
    
    /**
     * 時間序列點插值
     */
    private static interpolateTimeseriesPoint(
        current: TimeseriesPoint,
        next: TimeseriesPoint,
        ratio: number
    ): SphericalCoordinates {
        return {
            elevation_deg: current.elevation_deg + (next.elevation_deg - current.elevation_deg) * ratio,
            azimuth_deg: current.azimuth_deg + (next.azimuth_deg - current.azimuth_deg) * ratio,
            range_km: current.range_km + (next.range_km - current.range_km) * ratio
        };
    }
    
    /**
     * 球面座標轉3D直角座標
     * 修復：實現真正的升降軌跡，允許負Y值
     */
    static sphericalToCartesian(
        spherical: SphericalCoordinates,
        scaleRange: number = 3.0,
        maxRange: number = 300,
        heightScale: number = 1.0
    ): [number, number, number] {
        const { elevation_deg, azimuth_deg, range_km } = spherical;
        
        // 角度轉弧度
        const elevationRad = (elevation_deg * Math.PI) / 180;
        const azimuthRad = (azimuth_deg * Math.PI) / 180;
        
        // 距離縮放（調整為更合理的範圍）
        const scaledRange = Math.min(range_km / scaleRange, maxRange);
        
        // 🌍 修復3D座標轉換：允許衛星自然升降
        const x = scaledRange * Math.cos(elevationRad) * Math.sin(azimuthRad);
        const z = scaledRange * Math.cos(elevationRad) * Math.cos(azimuthRad);
        
        // ⭐ 關鍵修復：Y座標直接反映仰角，允許負值（地平線以下）
        const baseHeight = 100; // 地面基準高度
        const y = baseHeight + (scaledRange * Math.sin(elevationRad) * heightScale);
        
        
        return [x, y, z];
    }
    
    /**
     * 批量計算多顆衛星位置
     */
    static calculateMultipleSatellitePositions(
        satellitesTimeseries: Map<string, TimeseriesPoint[]>,
        currentTime: number,
        speedMultiplier: number = 1
    ): Map<string, OrbitCalculationResult> {
        const results = new Map<string, OrbitCalculationResult>();
        
        satellitesTimeseries.forEach((timeseries, satelliteId) => {
            const result = this.calculateOrbitPosition(timeseries, currentTime, speedMultiplier);
            results.set(satelliteId, result);
        });
        
        return results;
    }
    
    /**
     * 生成軌道預測路徑
     * 用於預測路徑組件
     */
    static generatePredictionPath(
        timeseries: TimeseriesPoint[],
        startTime: number,
        predictionDuration: number,
        steps: number = 60
    ): CartesianCoordinates[] {
        const path: CartesianCoordinates[] = [];
        const timeStep = predictionDuration / steps;
        
        for (let i = 0; i < steps; i++) {
            const time = startTime + i * timeStep;
            const result = this.calculateOrbitPosition(timeseries, time, 1);
            path.push({
                x: result.position[0],
                y: result.position[1],
                z: result.position[2]
            });
        }
        
        return path;
    }
    
    /**
     * 計算衛星可見性窗口
     */
    static calculateVisibilityWindow(timeseries: TimeseriesPoint[]): {
        start: number;
        end: number;
        duration: number;
        maxElevation: number;
    } {
        let start = -1;
        let end = -1;
        let maxElevation = -90;
        
        for (let i = 0; i < timeseries.length; i++) {
            const point = timeseries[i];
            
            if (point.is_visible && point.elevation_deg > 0) {
                if (start === -1) start = i;
                end = i;
                maxElevation = Math.max(maxElevation, point.elevation_deg);
            }
        }
        
        return {
            start: start * 30, // 轉換為秒
            end: end * 30,
            duration: (end - start) * 30,
            maxElevation
        };
    }
    
    /**
     * 驗證時間序列數據完整性
     */
    static validateTimeseries(timeseries: TimeseriesPoint[]): {
        isValid: boolean;
        errors: string[];
        warnings: string[];
    } {
        const errors: string[] = [];
        const warnings: string[] = [];
        
        if (!timeseries || timeseries.length === 0) {
            errors.push('時間序列數據為空');
            return { isValid: false, errors, warnings };
        }
        
        // 檢查數據點數量
        if (timeseries.length < 10) {
            warnings.push(`時間序列數據點過少: ${timeseries.length}`);
        }
        
        // 檢查時間連續性
        for (let i = 1; i < timeseries.length; i++) {
            const timeDiff = timeseries[i].time_offset_seconds - timeseries[i-1].time_offset_seconds;
            if (Math.abs(timeDiff - 30) > 1) { // 允許1秒誤差
                warnings.push(`時間間隔不一致: ${timeDiff}秒 at index ${i}`);
            }
        }
        
        return {
            isValid: errors.length === 0,
            errors,
            warnings
        };
    }
}

export default SatelliteOrbitCalculator;