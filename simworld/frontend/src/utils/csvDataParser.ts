/**
 * CSV Data Parser for 3GPP Measurement Events
 * Parses Line-Plot.csv data for RSRP curve visualization
 */

export interface DataPoint {
  x: number; // Time
  y: number; // RSRP value in dBm
}

export interface ParsedCSVData {
  points: DataPoint[];
  timeRange: { min: number; max: number };
  rsrpRange: { min: number; max: number };
}

/**
 * Parse CSV content and convert to Chart.js compatible format
 * 對照 chart.html，進行數據抽樣以獲得更平滑的曲線
 */
export function parseCSVData(csvContent: string): ParsedCSVData {
  const lines = csvContent.trim().split('\n');
  const allPoints: DataPoint[] = [];
  
  let minTime = Infinity;
  let maxTime = -Infinity;
  let minRsrp = Infinity;
  let maxRsrp = -Infinity;

  // 先解析所有數據點
  for (const line of lines) {
    if (!line.trim()) continue;
    
    const [timeStr, rsrpStr] = line.split(',');
    const time = parseFloat(timeStr.trim());
    const rsrp = parseFloat(rsrpStr.trim());
    
    if (!isNaN(time) && !isNaN(rsrp)) {
      allPoints.push({ x: time, y: rsrp });
      
      // Update ranges
      minTime = Math.min(minTime, time);
      maxTime = Math.max(maxTime, time);
      minRsrp = Math.min(minRsrp, rsrp);
      maxRsrp = Math.max(maxRsrp, rsrp);
    }
  }

  // 對照 chart.html 的 64 個數據點，進行抽樣
  // 目標：從 376 個點抽樣到約 64 個點
  const targetPoints = 64;
  const samplingInterval = Math.max(1, Math.floor(allPoints.length / targetPoints));
  const points: DataPoint[] = [];
  
  for (let i = 0; i < allPoints.length; i += samplingInterval) {
    points.push(allPoints[i]);
  }
  
  // 確保包含最後一個點
  if (allPoints.length > 0 && points[points.length - 1] !== allPoints[allPoints.length - 1]) {
    points.push(allPoints[allPoints.length - 1]);
  }

  return {
    points,
    timeRange: { min: minTime, max: maxTime },
    rsrpRange: { min: minRsrp, max: maxRsrp }
  };
}

/**
 * Load CSV data from the Line-Plot.csv file
 */
export async function loadCSVData(): Promise<ParsedCSVData> {
  try {
    const response = await fetch('/Line-Plot.csv');
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const csvContent = await response.text();
    return parseCSVData(csvContent);
  } catch (error) {
    console.error('Error loading CSV data:', error);
    throw error;
  }
}

/**
 * Generate sample RSRP data for testing purposes
 */
export function generateSampleRSRPData(length: number = 100): ParsedCSVData {
  const points: DataPoint[] = [];
  
  for (let i = 0; i < length; i++) {
    const time = i * 0.5; // 0.5 second intervals
    // Generate a curve that resembles the shape in Event-A4.jpg
    const baseRsrp = -90;
    const amplitude = 30;
    const phase = (i / length) * Math.PI * 2;
    const rsrp = baseRsrp + amplitude * Math.sin(phase);
    
    points.push({ x: time, y: rsrp });
  }
  
  const timeRange = { min: 0, max: (length - 1) * 0.5 };
  const rsrpRange = { min: -120, max: -40 };
  
  return { points, timeRange, rsrpRange };
}

/**
 * Smooth the RSRP curve using simple moving average
 */
export function smoothData(points: DataPoint[], windowSize: number = 3): DataPoint[] {
  if (windowSize <= 1) return points;
  
  const smoothed: DataPoint[] = [];
  const halfWindow = Math.floor(windowSize / 2);
  
  for (let i = 0; i < points.length; i++) {
    const start = Math.max(0, i - halfWindow);
    const end = Math.min(points.length - 1, i + halfWindow);
    
    let sum = 0;
    let count = 0;
    
    for (let j = start; j <= end; j++) {
      sum += points[j].y;
      count++;
    }
    
    smoothed.push({
      x: points[i].x,
      y: sum / count
    });
  }
  
  return smoothed;
}

/**
 * Find the closest data point to a given time
 */
export function findClosestPoint(points: DataPoint[], targetTime: number): DataPoint | null {
  if (points.length === 0) return null;
  
  let closest = points[0];
  let minDistance = Math.abs(points[0].x - targetTime);
  
  for (const point of points) {
    const distance = Math.abs(point.x - targetTime);
    if (distance < minDistance) {
      minDistance = distance;
      closest = point;
    }
  }
  
  return closest;
}

/**
 * Interpolate RSRP value at a specific time
 */
export function interpolateRSRP(points: DataPoint[], targetTime: number): number {
  if (points.length === 0) return 0;
  if (points.length === 1) return points[0].y;
  
  // Find the two points to interpolate between
  let leftPoint = points[0];
  let rightPoint = points[points.length - 1];
  
  for (let i = 0; i < points.length - 1; i++) {
    if (points[i].x <= targetTime && points[i + 1].x >= targetTime) {
      leftPoint = points[i];
      rightPoint = points[i + 1];
      break;
    }
  }
  
  // Linear interpolation
  if (leftPoint.x === rightPoint.x) {
    return leftPoint.y;
  }
  
  const ratio = (targetTime - leftPoint.x) / (rightPoint.x - leftPoint.x);
  return leftPoint.y + ratio * (rightPoint.y - leftPoint.y);
}