import React, { useState, useEffect, useCallback } from 'react';
import { Button } from '../../ui/button';
import { Card, CardHeader, CardTitle, CardContent } from '../../ui/card';
import { Progress } from '../../ui/progress';
import { format } from 'date-fns';
import { netstackFetch } from '../../../config/api-config';

interface TimelineData {
  start: string;
  end: string;
  totalDurationHours: number;
  dataPoints: number;
  resolution: string;
}

interface Props {
  constellation: string;
  onTimeChange: (timestamp: number) => void;
  onPlaybackSpeedChange?: (speed: number) => void;
  disabled?: boolean;
  showStatistics?: boolean;
}

export const TimelineControl: React.FC<Props> = ({ 
  constellation,
  onTimeChange,
  onPlaybackSpeedChange,
  disabled = false,
  showStatistics = true
}) => {
  const [timelineData, setTimelineData] = useState<TimelineData | null>(null);
  const [currentTime, setCurrentTime] = useState(Date.now());
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const [realTimeMode, setRealTimeMode] = useState(false);
  const [loading, setLoading] = useState(false);
  
  useEffect(() => {
    const fetchTimelineData = async () => {
      if (!constellation) return;
      
      setLoading(true);
      try {
        const response = await netstackFetch(`/api/v1/satellites/timeline/${constellation}`);
        const data = await response.json();
        
        if (data.success) {
          setTimelineData({
            start: data.start_time,
            end: data.end_time,
            totalDurationHours: data.duration_hours,
            dataPoints: data.total_points,
            resolution: data.resolution
          });
          
          const startTime = new Date(data.start_time).getTime();
          setCurrentTime(startTime);
          onTimeChange(startTime);
        }
        
      } catch (error) {
        console.error('Failed to fetch timeline data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchTimelineData();
    setIsPlaying(false);
  }, [constellation, onTimeChange]);

  useEffect(() => {
    if (!isPlaying || !timelineData) return;
    
    const interval = setInterval(() => {
      setCurrentTime(prevTime => {
        const timeStep = realTimeMode ? 1000 : (60 * 1000 * playbackSpeed);
        const nextTime = prevTime + timeStep;
        const endTime = new Date(timelineData.end).getTime();
        
        if (nextTime > endTime) {
          setIsPlaying(false);
          return endTime;
        }
        
        onTimeChange(nextTime);
        return nextTime;
      });
    }, realTimeMode ? 1000 : 500);

    return () => clearInterval(interval);
  }, [isPlaying, playbackSpeed, realTimeMode, timelineData, onTimeChange]);

  useEffect(() => {
    if (onPlaybackSpeedChange) {
      onPlaybackSpeedChange(playbackSpeed);
    }
  }, [playbackSpeed, onPlaybackSpeedChange]);

  const handleSliderChange = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    if (!timelineData) return;
    
    const value = parseInt(event.target.value);
    const startTime = new Date(timelineData.start).getTime();
    const endTime = new Date(timelineData.end).getTime();
    const targetTime = startTime + (endTime - startTime) * (value / 100);
    
    setCurrentTime(targetTime);
    onTimeChange(targetTime);
  }, [timelineData, onTimeChange]);

  const togglePlayback = () => setIsPlaying(!isPlaying);

  const cycleSpeed = () => {
    const speeds = [0.5, 1, 2, 5, 10];
    const currentIndex = speeds.indexOf(playbackSpeed);
    const nextIndex = (currentIndex + 1) % speeds.length;
    setPlaybackSpeed(speeds[nextIndex]);
  };

  const stepForward = () => {
    if (!timelineData) return;
    const timeStep = 30 * 1000; // 30 seconds
    const nextTime = Math.min(
      currentTime + timeStep, 
      new Date(timelineData.end).getTime()
    );
    setCurrentTime(nextTime);
    onTimeChange(nextTime);
  };

  const stepBackward = () => {
    if (!timelineData) return;
    const timeStep = 30 * 1000; // 30 seconds
    const prevTime = Math.max(
      currentTime - timeStep, 
      new Date(timelineData.start).getTime()
    );
    setCurrentTime(prevTime);
    onTimeChange(prevTime);
  };

  const resetToStart = () => {
    if (!timelineData) return;
    const startTime = new Date(timelineData.start).getTime();
    setCurrentTime(startTime);
    onTimeChange(startTime);
    setIsPlaying(false);
  };

  if (loading || !timelineData) {
    return (
      <Card className="timeline-control">
        <CardContent className="text-center py-8 text-gray-500">
          載入 {constellation} 星座時間軸數據...
        </CardContent>
      </Card>
    );
  }

  const progress = ((currentTime - new Date(timelineData.start).getTime()) / 
                   (new Date(timelineData.end).getTime() - new Date(timelineData.start).getTime())) * 100;

  return (
    <Card className="timeline-control">
      <CardHeader>
        <CardTitle>⏰ 歷史數據時間軸控制</CardTitle>
      </CardHeader>
      <CardContent>
        {showStatistics && (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">
                {timelineData.totalDurationHours.toFixed(1)}
              </div>
              <div className="text-sm text-gray-500">數據覆蓋 (小時)</div>
            </div>
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <div className="text-2xl font-bold text-green-600">
                {(timelineData.dataPoints / 1000).toFixed(1)}K
              </div>
              <div className="text-sm text-gray-500">數據點數</div>
            </div>
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <div className="text-lg font-bold text-purple-600">
                {timelineData.resolution}
              </div>
              <div className="text-sm text-gray-500">解析度</div>
            </div>
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <div className="text-2xl font-bold text-orange-600">
                {progress.toFixed(1)}%
              </div>
              <div className="text-sm text-gray-500">進度</div>
            </div>
          </div>
        )}

        <div className="mb-6">
          <Progress value={progress} className="mb-2" />
          
          <input
            type="range"
            min={0}
            max={100}
            value={progress}
            onChange={handleSliderChange}
            disabled={disabled || isPlaying}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
            style={{
              background: `linear-gradient(to right, #3b82f6 0%, #3b82f6 ${progress}%, #e5e7eb ${progress}%, #e5e7eb 100%)`
            }}
          />
          
          <div className="flex justify-between text-xs text-gray-500 mt-2">
            <span>{format(new Date(timelineData.start), 'MM/dd HH:mm')}</span>
            <span className="font-semibold text-blue-600">
              {format(new Date(currentTime), 'MM-dd HH:mm:ss')}
            </span>
            <span>{format(new Date(timelineData.end), 'MM/dd HH:mm')}</span>
          </div>
        </div>

        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={stepBackward}
              disabled={disabled || currentTime <= new Date(timelineData.start).getTime()}
              title="後退30秒"
            >
              ⏮️
            </Button>
            
            <Button
              variant="default"
              onClick={togglePlayback}
              disabled={disabled || currentTime >= new Date(timelineData.end).getTime()}
            >
              {isPlaying ? '⏸️ 暫停' : '▶️ 播放'}
            </Button>
            
            <Button
              variant="outline"
              size="sm"
              onClick={stepForward}
              disabled={disabled || currentTime >= new Date(timelineData.end).getTime()}
              title="前進30秒"
            >
              ⏭️
            </Button>
            
            {!realTimeMode && (
              <Button
                variant="outline"
                size="sm"
                onClick={cycleSpeed}
                disabled={disabled}
              >
                🚀 {playbackSpeed}x
              </Button>
            )}
            
            <Button
              variant="outline"
              size="sm"
              onClick={resetToStart}
              disabled={disabled}
              title="重置到開始"
            >
              🔄
            </Button>
          </div>

          <div className="flex items-center space-x-4">
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={realTimeMode}
                onChange={(e) => setRealTimeMode(e.target.checked)}
                disabled={disabled}
                className="rounded"
              />
              <span className="text-sm text-gray-600">實時模式</span>
            </label>
            
            <div className="text-xs border border-gray-300 rounded px-3 py-2 bg-white">
              <span className="text-gray-600">
                {format(new Date(currentTime), 'MM/dd HH:mm')}
              </span>
            </div>
          </div>
        </div>
        
        <div className="mt-4 text-xs text-gray-500 bg-gray-50 p-3 rounded">
          💡 提示: 滑桿快速跳轉，播放控制動畫，實時模式按真實時間播放，加速模式可調整倍速
        </div>
      </CardContent>
    </Card>
  );
};