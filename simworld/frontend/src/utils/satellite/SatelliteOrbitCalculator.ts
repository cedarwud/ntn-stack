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
     * 🚀 修復版本：只在可見窗口內循環，實現平滑升降軌跡
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

        // 🌟 關鍵修復：只識別可見窗口，避免長時間不可見期的跳躍
        const visibleWindows = this.extractVisibleWindows(timeseries);
        
        if (visibleWindows.length === 0) {
            return {
                position: [0, -500, 0],
                isVisible: false,
                progress: 0,
                currentPoint: null
            };
        }
        
        // 選擇最長的可見窗口作為主要軌道
        const mainWindow = visibleWindows.reduce((longest, current) => 
            current.duration > longest.duration ? current : longest);
        
        if (mainWindow.points.length < 2) {
            return {
                position: [0, -500, 0],
                isVisible: false,
                progress: 0,
                currentPoint: null
            };
        }
        
        // 🎯 只在可見窗口內循環，避免軌跡斷點
        const windowDuration = mainWindow.duration;
        const timeProgress = (currentTime * speedMultiplier) % windowDuration;
        
        // 🔍 在可見窗口內尋找當前位置
        let currentIndex = 0;
        let nextIndex = 1;
        
        const adjustedTimeProgress = timeProgress + mainWindow.startTime;
        
        for (let i = 0; i < mainWindow.points.length - 1; i++) {
            const currentTimeOffset = mainWindow.points[i].time_offset_seconds;
            const nextTimeOffset = mainWindow.points[i + 1].time_offset_seconds;
            
            if (adjustedTimeProgress >= currentTimeOffset && adjustedTimeProgress <= nextTimeOffset) {
                currentIndex = i;
                nextIndex = i + 1;
                break;
            }
        }
        
        const currentPoint = mainWindow.points[currentIndex];
        const nextPoint = mainWindow.points[nextIndex];
        
        // 計算在當前段內的比例
        const pointDuration = nextPoint.time_offset_seconds - currentPoint.time_offset_seconds;
        const pointProgress = adjustedTimeProgress - currentPoint.time_offset_seconds;
        const timeRatio = Math.max(0, Math.min(1, pointProgress / pointDuration));
        
        // 🔄 線性插值：在真實數據點之間平滑過渡
        const interpolated = this.interpolateTimeseriesPoint(currentPoint, nextPoint, timeRatio);
        
        // 🌍 轉換為3D座標（增強版升降軌跡）
        const position = this.sphericalToCartesian(interpolated);
        
        // ✅ 可見性判斷：只有可見窗口內的點才可見
        const isVisible = true; // 可見窗口內的所有點都應該可見
        
        return {
            position,
            isVisible,
            progress: timeProgress / windowDuration,
            currentPoint: currentPoint
        };
    }
    
    /**
     * 🌟 新增方法：提取可見窗口
     * 解決軌跡斷點問題的核心方法
     */
    private static extractVisibleWindows(timeseries: TimeseriesPoint[]): Array<{
        points: TimeseriesPoint[],
        startTime: number,
        endTime: number,
        duration: number
    }> {
        const windows = [];
        let currentWindow: TimeseriesPoint[] = [];
        
        for (const point of timeseries) {
            if (point.is_visible && point.elevation_deg >= 0) {
                currentWindow.push(point);
            } else {
                // 結束當前窗口
                if (currentWindow.length >= 2) {
                    const startTime = currentWindow[0].time_offset_seconds;
                    const endTime = currentWindow[currentWindow.length - 1].time_offset_seconds;
                    windows.push({
                        points: [...currentWindow],
                        startTime,
                        endTime,
                        duration: endTime - startTime
                    });
                }
                currentWindow = [];
            }
        }
        
        // 處理最後一個窗口
        if (currentWindow.length >= 2) {
            const startTime = currentWindow[0].time_offset_seconds;
            const endTime = currentWindow[currentWindow.length - 1].time_offset_seconds;
            windows.push({
                points: [...currentWindow],
                startTime,
                endTime,
                duration: endTime - startTime
            });
        }
        
        return windows;
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
     * 🚀 修復版：衛星應在天空中升降，而非地面附近
     */
    static sphericalToCartesian(
        spherical: SphericalCoordinates,
        scaleRange: number = 4.0,     // 增大縮放使衛星更遠離地面
        maxRange: number = 300,       // 適當減小最大範圍保持在場景內
        heightScale: number = 1.5     // 適中的高度縮放
    ): [number, number, number] {
        const { elevation_deg, azimuth_deg, range_km } = spherical;
        
        // 角度轉弧度
        const elevationRad = (elevation_deg * Math.PI) / 180;
        const azimuthRad = (azimuth_deg * Math.PI) / 180;
        
        // 🎯 改進的距離縮放：根據場景大小調整
        let scaledRange = Math.min(range_km / scaleRange, maxRange);
        
        // 🌍 3D座標計算：標準球面轉直角座標
        const x = scaledRange * Math.cos(elevationRad) * Math.sin(azimuthRad);
        const z = scaledRange * Math.cos(elevationRad) * Math.cos(azimuthRad);
        
        // ⭐ 關鍵修復：衛星應在天空中升降（地面設備在15-20高度，衛星應在150+）
        const skyBaseHeight = 200;  // 天空基準高度，遠高於地面設備
        const elevationHeight = scaledRange * Math.sin(elevationRad) * heightScale;
        const y = skyBaseHeight + elevationHeight;
        
        // 📊 調試信息
        // console.log(`衛星座標: 仰角${elevation_deg.toFixed(1)}° → Y=${y.toFixed(1)} (天空基準${skyBaseHeight} + 仰角高度${elevationHeight.toFixed(1)})`);
        
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