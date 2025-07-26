import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../../ui/card';
import { Badge } from '../../ui/badge';
import { Alert } from '../../ui/alert';
import { netstackFetch } from '../../../config/api-config';

interface ConstellationInfo {
  name: string;
  displayName: string;
  color: string;
  icon: string;
  satelliteCount: number;
  coverage: string;
  orbitAltitude: string;
  latency: string;
  dataAvailability: {
    start: string;
    end: string;
    totalDays: number;
  };
}

const CONSTELLATION_CONFIGS: Record<string, ConstellationInfo> = {
  starlink: {
    name: 'starlink',
    displayName: 'Starlink',
    color: '#1890ff',
    icon: '🛰️',
    satelliteCount: 0,
    coverage: '全球覆蓋 (±70°)',
    orbitAltitude: '550km',
    latency: '20-40ms',
    dataAvailability: { start: '', end: '', totalDays: 0 }
  },
  oneweb: {
    name: 'oneweb',
    displayName: 'OneWeb', 
    color: '#52c41a',
    icon: '🌍',
    satelliteCount: 0,
    coverage: '極地覆蓋 (±88°)',
    orbitAltitude: '1200km',
    latency: '32-50ms',
    dataAvailability: { start: '', end: '', totalDays: 0 }
  }
};

interface Props {
  value: string;
  onChange: (constellation: string) => void;
  disabled?: boolean;
  showComparison?: boolean;
}

export const ConstellationSelector: React.FC<Props> = ({ 
  value, 
  onChange, 
  disabled = false,
  showComparison = true
}) => {
  const [constellations, setConstellations] = useState(CONSTELLATION_CONFIGS);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchConstellationData = async () => {
      setLoading(true);
      try {
        const response = await netstackFetch('/api/v1/satellites/constellations/info');
        const data = await response.json();
        
        if (data.success && data.constellations) {
          const updated = { ...constellations };
          data.constellations.forEach((item: any) => {
            if (updated[item.constellation]) {
              updated[item.constellation].satelliteCount = item.satellite_count || 0;
              updated[item.constellation].dataAvailability = {
                start: item.data_start || '',
                end: item.data_end || '',
                totalDays: item.total_days || 0
              };
            }
          });
          setConstellations(updated);
        }
      } catch (error) {
        console.error('Failed to fetch constellation data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchConstellationData();
  }, []);

  const handleChange = (newValue: string) => {
    if (!disabled) {
      onChange(newValue);
    }
  };

  const selectedConstellation = constellations[value];

  return (
    <div className="constellation-selector">
      <div className="mb-3">
        <h3 className="text-base font-semibold text-gray-800 mb-2">
          🛰️ LEO 衛星星座系統
        </h3>
        {loading && <span className="text-sm text-blue-500">載入中...</span>}
      </div>
      
      <div className="space-y-2 mb-4">
        {Object.entries(constellations).map(([key, info]) => (
          <button
            key={key}
            onClick={() => handleChange(key)}
            disabled={disabled || loading}
            className={`w-full p-3 border rounded-lg text-left transition-all ${
              value === key 
                ? 'border-blue-500 bg-blue-50 shadow-sm' 
                : 'border-gray-200 bg-white hover:border-gray-300 hover:shadow-sm'
            } ${disabled || loading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
          >
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center">
                <span className="text-lg mr-2">{info.icon}</span>
                <span className="font-semibold text-gray-800">
                  {info.displayName}
                </span>
              </div>
              {info.satelliteCount > 0 && (
                <Badge variant="default" className="bg-blue-100 text-blue-800">
                  {info.satelliteCount}
                </Badge>
              )}
            </div>
            
            <div className="text-sm text-gray-600 space-y-1">
              <div>📍 覆蓋: {info.coverage}</div>
              <div>🚀 高度: {info.orbitAltitude}</div>
              <div>⚡ 延遲: {info.latency}</div>
              {info.dataAvailability.totalDays > 0 && (
                <div>📊 數據: {info.dataAvailability.totalDays} 天</div>
              )}
            </div>
          </button>
        ))}
      </div>
      
      {selectedConstellation && (
        <Card className="shadow-sm">
          <CardHeader className="pb-4">
            <CardTitle className="flex items-center">
              <span className="text-lg mr-2">{selectedConstellation.icon}</span>
              <span>{selectedConstellation.displayName}</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-gray-500">覆蓋範圍:</span>
                  <span className="font-medium">{selectedConstellation.coverage}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">軌道高度:</span>
                  <span className="font-medium">{selectedConstellation.orbitAltitude}</span>
                </div>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-gray-500">預期延遲:</span>
                  <span className="font-medium">{selectedConstellation.latency}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">數據覆蓋:</span>
                  <span className="font-medium">
                    {selectedConstellation.dataAvailability.totalDays} 天
                  </span>
                </div>
              </div>
            </div>
            
            <div className="text-center p-4 bg-gray-50 rounded-lg mb-4">
              <div className="text-2xl font-bold text-blue-600">
                {selectedConstellation.satelliteCount}
              </div>
              <div className="text-sm text-gray-500">可見衛星數量</div>
            </div>
            
            {selectedConstellation.dataAvailability.start && (
              <div className="mb-4 p-3 bg-blue-50 rounded text-xs text-gray-600">
                💡 數據期間: {selectedConstellation.dataAvailability.start} ~ {selectedConstellation.dataAvailability.end}
                <br />
                🎯 適用於論文級 LEO 衛星 Handover 研究和 RL 訓練
              </div>
            )}
            
            <Alert>
              <div className="text-sm">
                <strong>星座隔離原則:</strong> 不同衛星星座間無法進行 Handover，請分別進行分析。
                每個星座的軌道參數、覆蓋模式和服務特性均不相同。
              </div>
            </Alert>
          </CardContent>
        </Card>
      )}
    </div>
  );
};