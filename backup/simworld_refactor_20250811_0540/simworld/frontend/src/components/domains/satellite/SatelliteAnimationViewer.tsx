import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../../ui/card';
import { Badge } from '../../ui/badge';
import { netstackFetch } from '../../../config/api-config';

interface SatellitePosition {
  satellite_id: string;
  constellation: string;
  position: {
    latitude: number;
    longitude: number;
    altitude: number;
  };
  observation: {
    elevation_angle: number;
    azimuth_angle: number;
    range_km: number;
  };
  signal_quality: {
    signal_strength: number;
    path_loss_db: number;
  };
}

interface HandoverEvent {
  satellite_id: string;
  event_type: 'serving' | 'handover_candidate' | 'monitoring' | 'approaching';
  trigger_condition: string;
  event_priority: 'high' | 'medium' | 'low' | 'info';
  action: string;
}

interface Props {
  currentTime: Date;
  constellation: string;
  playbackSpeed: number;
}

export const SatelliteAnimationViewer: React.FC<Props> = ({
  currentTime,
  constellation,
  playbackSpeed
}) => {
  const [satellites, setSatellites] = useState<SatellitePosition[]>([]);
  const [handoverEvents, setHandoverEvents] = useState<HandoverEvent[]>([]);
  const [loading, setLoading] = useState(false);
  
  // 獲取當前時間點的衛星位置
  useEffect(() => {
    const fetchSatellitesAtTime = async () => {
      if (!currentTime || !constellation) return;
      
      setLoading(true);
      try {
        const timestamp = currentTime.toISOString();
        const response = await netstackFetch(
          `/api/v1/satellites/history/at_time?target_time=${timestamp}&constellation=${constellation}&count=20`
        );
        const data = await response.json();
        
        if (data.success && data.satellites) {
          setSatellites(data.satellites);
        } else {
          console.warn('No satellites data received:', data);
          setSatellites([]);
        }
      } catch (error) {
        console.error('Failed to fetch satellites:', error);
        setSatellites([]);
      } finally {
        setLoading(false);
      }
    };
    
    fetchSatellitesAtTime();
  }, [currentTime, constellation]);
  
  // 計算並顯示 handover 事件
  useEffect(() => {
    const fetchHandoverEvents = async () => {
      if (!currentTime || !constellation || satellites.length === 0) return;
      
      try {
        const timestamp = currentTime.toISOString();
        const response = await netstackFetch(
          `/api/v1/satellites/d2/events?timestamp=${timestamp}&constellation=${constellation}`
        );
        const data = await response.json();
        
        if (data.success && data.handover_events) {
          setHandoverEvents(data.handover_events);
        } else {
          setHandoverEvents([]);
        }
      } catch (error) {
        console.error('Failed to fetch handover events:', error);
        setHandoverEvents([]);
      }
    };
    
    fetchHandoverEvents();
  }, [satellites, currentTime, constellation]);

  const getEventTypeColor = (eventType: string) => {
    switch (eventType) {
      case 'serving': return 'bg-green-100 text-green-800';
      case 'handover_candidate': return 'bg-blue-100 text-blue-800';
      case 'monitoring': return 'bg-orange-100 text-orange-800';
      case 'approaching': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-600';
    }
  };

  const getEventTypeText = (eventType: string) => {
    switch (eventType) {
      case 'serving': return '服務中';
      case 'handover_candidate': return 'Handover候選';
      case 'monitoring': return '監測中';
      case 'approaching': return '即將可見';
      default: return eventType;
    }
  };

  const getSignalStrengthColor = (strength: number) => {
    if (strength > -80) return 'text-green-600'; // 強信號
    if (strength > -100) return 'text-yellow-600'; // 中等信號
    return 'text-red-600'; // 弱信號
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'bg-red-100 text-red-800';
      case 'medium': return 'bg-orange-100 text-orange-800';
      case 'low': return 'bg-blue-100 text-blue-800';
      default: return 'bg-gray-100 text-gray-600';
    }
  };

  return (
    <div className="satellite-animation-viewer">
      {/* 統計概覽 */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4 mb-6">
        <div className="text-center p-4 bg-green-50 rounded-lg border">
          <div className="text-2xl font-bold text-green-600">{satellites.length}</div>
          <div className="text-sm text-gray-500">可見衛星 (顆)</div>
        </div>
        <div className="text-center p-4 bg-red-50 rounded-lg border">
          <div className="text-2xl font-bold text-red-600">{handoverEvents.length}</div>
          <div className="text-sm text-gray-500">Handover事件 (個)</div>
        </div>
        <div className="text-center p-4 bg-blue-50 rounded-lg border">
          <div className="text-2xl font-bold text-blue-600">{playbackSpeed}x</div>
          <div className="text-sm text-gray-500">播放速度</div>
        </div>
        <div className="text-center p-4 bg-purple-50 rounded-lg border">
          <div className="text-lg font-bold text-purple-600">
            {currentTime.toLocaleTimeString('zh-TW', { hour12: false })}
          </div>
          <div className="text-sm text-gray-500">更新時間</div>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* 衛星位置表 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              🛰️ 當前可見衛星
              {loading && <span className="ml-2 text-sm text-blue-500">載入中...</span>}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-gray-50">
                    <th className="text-left p-2 font-medium">衛星ID</th>
                    <th className="text-left p-2 font-medium">仰角</th>
                    <th className="text-left p-2 font-medium">方位角</th>
                    <th className="text-left p-2 font-medium">距離</th>
                    <th className="text-left p-2 font-medium">信號強度</th>
                    <th className="text-left p-2 font-medium">狀態</th>
                  </tr>
                </thead>
                <tbody>
                  {satellites.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="text-center p-4 text-gray-500">
                        {loading ? '載入中...' : '無可見衛星'}
                      </td>
                    </tr>
                  ) : (
                    satellites
                      .sort((a, b) => b.observation.elevation_angle - a.observation.elevation_angle)
                      .map((satellite) => {
                        const event = handoverEvents.find(e => e.satellite_id === satellite.satellite_id);
                        return (
                          <tr key={satellite.satellite_id} className="border-b hover:bg-gray-50">
                            <td className="p-2 font-mono text-blue-600">{satellite.satellite_id}</td>
                            <td className="p-2">{satellite.observation.elevation_angle.toFixed(1)}°</td>
                            <td className="p-2">{satellite.observation.azimuth_angle.toFixed(1)}°</td>
                            <td className="p-2">{satellite.observation.range_km.toFixed(0)}km</td>
                            <td className={`p-2 font-bold ${getSignalStrengthColor(satellite.signal_quality.signal_strength)}`}>
                              {satellite.signal_quality.signal_strength.toFixed(1)}dBm
                            </td>
                            <td className="p-2">
                              {event ? (
                                <Badge className={getEventTypeColor(event.event_type)}>
                                  {getEventTypeText(event.event_type)}
                                </Badge>
                              ) : (
                                <Badge className="bg-gray-100 text-gray-600">未分類</Badge>
                              )}
                            </td>
                          </tr>
                        );
                      })
                  )}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>

        {/* Handover 事件表 */}
        <Card>
          <CardHeader>
            <CardTitle>📡 Handover 事件</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-gray-50">
                    <th className="text-left p-2 font-medium">衛星ID</th>
                    <th className="text-left p-2 font-medium">事件類型</th>
                    <th className="text-left p-2 font-medium">觸發條件</th>
                    <th className="text-left p-2 font-medium">優先級</th>
                    <th className="text-left p-2 font-medium">動作</th>
                  </tr>
                </thead>
                <tbody>
                  {handoverEvents.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="text-center p-4 text-gray-500">
                        無 Handover 事件
                      </td>
                    </tr>
                  ) : (
                    handoverEvents.map((event, index) => (
                      <tr key={`${event.satellite_id}-${event.event_type}-${index}`} className="border-b hover:bg-gray-50">
                        <td className="p-2 font-mono text-blue-600">{event.satellite_id}</td>
                        <td className="p-2">
                          <Badge className={getEventTypeColor(event.event_type)}>
                            {getEventTypeText(event.event_type)}
                          </Badge>
                        </td>
                        <td className="p-2 text-gray-600 max-w-32 truncate" title={event.trigger_condition}>
                          {event.trigger_condition}
                        </td>
                        <td className="p-2">
                          <Badge className={getPriorityColor(event.event_priority)}>
                            {event.event_priority}
                          </Badge>
                        </td>
                        <td className="p-2 text-gray-700 max-w-32 truncate" title={event.action}>
                          {event.action}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 3GPP NTN 符合性指標 */}
      <Card className="mt-6">
        <CardHeader>
          <CardTitle>📋 3GPP NTN 符合性檢查</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">
                {handoverEvents.filter(e => e.event_type === 'handover_candidate').length}
              </div>
              <div className="text-sm text-gray-500">Handover 候選</div>
              <div className="text-xs text-gray-400">標準: ≤ 5 顆</div>
            </div>
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <div className="text-2xl font-bold text-green-600">
                {handoverEvents.filter(e => e.event_type === 'monitoring').length}
              </div>
              <div className="text-sm text-gray-500">監測衛星</div>
              <div className="text-xs text-gray-400">標準: ≤ 8 顆</div>
            </div>
            <div className="text-center p-4 bg-purple-50 rounded-lg">
              <div className="text-2xl font-bold text-purple-600">
                {satellites.filter(s => s.observation.elevation_angle >= 10).length}
              </div>
              <div className="text-sm text-gray-500">可測量</div>
              <div className="text-xs text-gray-400">仰角 ≥ 10°</div>
            </div>
            <div className="text-center p-4 bg-orange-50 rounded-lg">
              <div className="text-2xl font-bold text-orange-600">
                {handoverEvents.filter(e => e.event_type === 'serving').length}
              </div>
              <div className="text-sm text-gray-500">服務中</div>
              <div className="text-xs text-gray-400">主要連接</div>
            </div>
          </div>
          
          <div className="text-xs text-gray-500 bg-blue-50 p-3 rounded">
            💡 符合性說明: 根據 3GPP TS 38.331 標準，LEO 衛星系統應維持合理數量的候選和監測衛星，
            確保 Handover 決策的準確性和網路服務的連續性。
          </div>
        </CardContent>
      </Card>
    </div>
  );
};