import React from 'react'
import { ViewerProps } from '../../types/viewer'

const TestViewer: React.FC<ViewerProps> = ({
  currentScene,
  onReportLastUpdateToNavbar,
  reportRefreshHandlerToNavbar,
  reportIsLoadingToNavbar
}) => {
  // 立即報告載入完成
  React.useEffect(() => {
    reportIsLoadingToNavbar(false)
    if (onReportLastUpdateToNavbar) {
      onReportLastUpdateToNavbar(new Date().toISOString())
    }
    reportRefreshHandlerToNavbar(() => {
      console.log('Test refresh triggered')
    })
  }, [])

  return (
    <div style={{ 
      width: '100%', 
      height: '400px', 
      background: '#1a1a1a', 
      color: 'white',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      flexDirection: 'column'
    }}>
      <h2>測試組件</h2>
      <p>場景: {currentScene}</p>
      <p>時間: {new Date().toLocaleString()}</p>
    </div>
  )
}

export default TestViewer