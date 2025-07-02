/**
 * Measurement Events Modal
 * 直接顯示測量事件圖表，內建事件類型選擇器
 */

import React, { useState, useCallback, useMemo } from 'react'
import ViewerModal from '../shared/ui/layout/ViewerModal'
import EventA4Viewer from '../domains/measurement/charts/EventA4Viewer'
import { ViewerProps } from '../../types/viewer'
import './MeasurementEventsModal.scss'

interface MeasurementEventsModalProps {
  isOpen: boolean
  onClose: () => void
}

type EventType = 'A4' | 'D1' | 'D2' | 'T1'

interface EventConfig {
  id: EventType
  name: string
  description: string
  status: 'available' | 'coming-soon'
  ViewerComponent?: React.FC<ViewerProps>
}

const eventConfigs: EventConfig[] = [
  {
    id: 'A4',
    name: 'Event A4',
    description: 'Neighbour becomes better than threshold',
    status: 'available',
    ViewerComponent: EventA4Viewer,
  },
  {
    id: 'D1',
    name: 'Event D1',
    description: 'Distance between UE and reference locations',
    status: 'coming-soon',
  },
  {
    id: 'D2',
    name: 'Event D2', 
    description: 'Distance between UE and moving reference locations',
    status: 'coming-soon',
  },
  {
    id: 'T1',
    name: 'CondEvent T1',
    description: 'Time measured at UE within duration from threshold',
    status: 'coming-soon',
  },
]

// 創建一個包含事件選擇器的 Viewer 組件
const MeasurementEventsViewer: React.FC<ViewerProps> = React.memo((viewerProps) => {
  console.log('📊 MeasurementEventsViewer render')
  const [selectedEvent, setSelectedEvent] = useState<EventType>('A4')

  const handleEventChange = useCallback((eventType: EventType) => {
    console.log('🔄 Event changed to:', eventType)
    const eventConfig = eventConfigs.find(config => config.id === eventType)
    if (eventConfig?.status === 'available') {
      setSelectedEvent(eventType)
    }
  }, [])

  const selectedEventConfig = useMemo(() => 
    eventConfigs.find(config => config.id === selectedEvent), 
    [selectedEvent]
  )

  // 穩定的 ViewerComponent 渲染，避免重新創建
  const CurrentViewer = useMemo(() => {
    return selectedEventConfig?.ViewerComponent || null
  }, [selectedEventConfig?.ViewerComponent])

  return (
    <div className="measurement-events-viewer">
      {/* 圖表顯示區域 */}
      <div className="event-chart-container">
        {CurrentViewer ? (
          <CurrentViewer 
            {...viewerProps} 
            selectedEvent={selectedEvent}
            onEventChange={handleEventChange}
          />
        ) : (
          <div className="coming-soon-placeholder">
            <h3>{selectedEventConfig?.name}</h3>
            <p>此事件類型即將推出</p>
            <div className="formula-preview">
              {selectedEvent === 'D1' && (
                <p><strong>距離條件:</strong> Ml1 &gt; Thresh1 AND Ml2 &lt; Thresh2</p>
              )}
              {selectedEvent === 'D2' && (
                <p><strong>移動參考:</strong> 基於衛星星曆的動態位置</p>
              )}
              {selectedEvent === 'T1' && (
                <p><strong>時間條件:</strong> Mt &gt; Thresh1 (持續時間)</p>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
})

const MeasurementEventsModal: React.FC<MeasurementEventsModalProps> = ({
  isOpen,
  onClose,
}) => {
  const modalTitleConfig = useMemo(() => ({
    base: '3GPP TS 38.331 測量事件',
    loading: '正在載入測量事件數據...',
    hoverRefresh: '重新載入測量事件',
  }), [])

  // 穩定的 viewerProps，避免每次渲染都創建新對象
  const stableViewerProps = useMemo(() => ({
    onReportLastUpdateToNavbar: () => {},
    reportRefreshHandlerToNavbar: () => {},
    reportIsLoadingToNavbar: () => {},
  }), [])

  const viewerComponent = useMemo(() => (
    <MeasurementEventsViewer {...stableViewerProps} />
  ), [stableViewerProps])

  return (
    <ViewerModal
      isOpen={isOpen}
      onClose={onClose}
      modalTitleConfig={modalTitleConfig}
      lastUpdateTimestamp=""
      isLoading={false}
      viewerComponent={viewerComponent}
    />
  )
}

export default MeasurementEventsModal