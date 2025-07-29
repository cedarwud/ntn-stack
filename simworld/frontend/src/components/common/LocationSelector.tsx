/**
 * Phase 2: 觀測點選擇組件
 * 
 * 支援切換不同觀測座標的軌道視圖
 * 整合 NetStack API 預計算數據
 */

import React, { useState, useCallback } from 'react'
import { MapPin, Globe, Satellite } from 'lucide-react'
import { Button } from '../ui/button'
import { Card } from '../ui/card'

export interface ObserverLocation {
  id: string
  name: string
  lat: number
  lon: number
  alt: number
  description?: string
  timezone?: string
  environment: 'open_area' | 'urban' | 'mountainous'
}

export interface LocationSelectorProps {
  currentLocation: string
  onLocationChange: (locationId: string) => void
  availableLocations?: ObserverLocation[]
  className?: string
  showDetails?: boolean
}

// 支援的觀測點配置
const DEFAULT_LOCATIONS: ObserverLocation[] = [
  {
    id: 'ntpu',
    name: 'NTPU 國立臺北大學',
    lat: 24.94417,
    lon: 121.37139,
    alt: 50,
    description: '三峽校區，開闊地形，適合衛星觀測',
    timezone: 'Asia/Taipei',
    environment: 'open_area'
  },
  // 未來可擴展的觀測點
  {
    id: 'nctu',
    name: 'NYCU 國立陽明交通大學',
    lat: 24.7881,
    lon: 120.9971,
    alt: 30,
    description: '新竹校區，都市環境',
    timezone: 'Asia/Taipei',
    environment: 'urban'
  },
  {
    id: 'ntu',
    name: 'NTU 國立臺灣大學',
    lat: 25.0173,
    lon: 121.5397,
    alt: 10,
    description: '台北校區，都市環境',
    timezone: 'Asia/Taipei',
    environment: 'urban'
  }
]

export const LocationSelector: React.FC<LocationSelectorProps> = ({
  currentLocation,
  onLocationChange,
  availableLocations = DEFAULT_LOCATIONS,
  className = '',
  showDetails = true
}) => {
  const [isExpanded, setIsExpanded] = useState(false)

  const currentLocationData = availableLocations.find(loc => loc.id === currentLocation)

  const handleLocationSelect = useCallback((locationId: string) => {
    if (locationId !== currentLocation) {
      console.log(`🌍 切換觀測點: ${currentLocation} -> ${locationId}`)
      onLocationChange(locationId)
    }
    setIsExpanded(false)
  }, [currentLocation, onLocationChange])

  const formatCoordinate = useCallback((value: number, type: 'lat' | 'lon'): string => {
    const abs = Math.abs(value)
    const direction = type === 'lat' 
      ? (value >= 0 ? 'N' : 'S')
      : (value >= 0 ? 'E' : 'W')
    return `${abs.toFixed(5)}°${direction}`
  }, [])

  const getEnvironmentIcon = useCallback((environment: string) => {
    switch (environment) {
      case 'open_area':
        return '🌾'
      case 'urban':
        return '🏙️'
      case 'mountainous':
        return '⛰️'
      default:
        return '📍'
    }
  }, [])

  const getEnvironmentLabel = useCallback((environment: string) => {
    switch (environment) {
      case 'open_area':
        return '開闊地區'
      case 'urban':
        return '都市環境'
      case 'mountainous':
        return '山區環境'
      default:
        return '未知環境'
    }
  }, [])

  return (
    <Card className={`bg-gray-900/90 backdrop-blur-sm border-gray-700 ${className}`}>
      <div className="p-4">
        {/* 當前觀測點顯示 */}
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-2">
            <MapPin className="w-5 h-5 text-blue-400" />
            <span className="text-sm font-medium text-gray-200">觀測點</span>
          </div>
          
          <Button
            variant="outline"
            size="sm"
            onClick={() => setIsExpanded(!isExpanded)}
            className="bg-gray-800 border-gray-600 hover:bg-gray-700 text-xs"
          >
            {isExpanded ? '收起' : '切換'}
          </Button>
        </div>

        {/* 當前位置信息 */}
        {currentLocationData && (
          <div className="space-y-2">
            <div className="flex items-center space-x-2">
              <span className="text-lg">{getEnvironmentIcon(currentLocationData.environment)}</span>
              <span className="text-white font-medium">{currentLocationData.name}</span>
            </div>
            
            {showDetails && (
              <div className="text-xs text-gray-400 space-y-1">
                <div className="flex items-center space-x-4">
                  <span>📍 {formatCoordinate(currentLocationData.lat, 'lat')}, {formatCoordinate(currentLocationData.lon, 'lon')}</span>
                  <span>⬆️ {currentLocationData.alt}m</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span>{getEnvironmentLabel(currentLocationData.environment)}</span>
                </div>
                {currentLocationData.description && (
                  <div className="text-gray-500 text-xs">
                    {currentLocationData.description}
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* 觀測點選擇列表 */}
        {isExpanded && (
          <div className="mt-4 space-y-2 border-t border-gray-700 pt-3">
            <div className="text-xs text-gray-400 mb-2">選擇觀測點:</div>
            
            {availableLocations.map((location) => (
              <Button
                key={location.id}
                variant={location.id === currentLocation ? "default" : "outline"}
                size="sm"
                onClick={() => handleLocationSelect(location.id)}
                className={`w-full justify-start text-left p-3 h-auto ${
                  location.id === currentLocation
                    ? 'bg-blue-600 border-blue-500 text-white'
                    : 'bg-gray-800 border-gray-600 hover:bg-gray-700 text-gray-300'
                }`}
              >
                <div className="flex items-start space-x-3 w-full">
                  <span className="text-lg mt-0.5">
                    {getEnvironmentIcon(location.environment)}
                  </span>
                  
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-sm">{location.name}</div>
                    <div className="text-xs opacity-75 mt-1">
                      {formatCoordinate(location.lat, 'lat')}, {formatCoordinate(location.lon, 'lon')}
                    </div>
                    {location.description && (
                      <div className="text-xs opacity-60 mt-1">
                        {location.description}
                      </div>
                    )}
                  </div>
                  
                  {location.id === currentLocation && (
                    <Satellite className="w-4 h-4 text-blue-300 mt-1" />
                  )}
                </div>
              </Button>
            ))}
          </div>
        )}

        {/* 狀態指示器 */}
        <div className="mt-3 pt-3 border-t border-gray-700">
          <div className="flex items-center justify-between text-xs text-gray-500">
            <div className="flex items-center space-x-2">
              <Globe className="w-3 h-3" />
              <span>預計算數據已載入</span>
            </div>
            <div className="flex items-center space-x-1">
              <div className="w-2 h-2 bg-green-500 rounded-full" />
              <span>就緒</span>
            </div>
          </div>
        </div>
      </div>
    </Card>
  )
}

export default LocationSelector
