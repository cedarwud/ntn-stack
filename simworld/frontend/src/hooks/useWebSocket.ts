import { useState, useEffect, useCallback, useRef } from 'react'

interface UseWebSocketReturn {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  data: any
  isConnected: boolean
  error: Error | null
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  send: (data: any) => void
  close: () => void
}

export const useWebSocket = (url: string): UseWebSocketReturn => {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [data, setData] = useState<any>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState<Error | null>(null)
  const websocketRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)

  const connect = useCallback(() => {
    try {
      // 構建完整的 WebSocket URL
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const host = window.location.host
      const wsUrl = `${protocol}//${host}${url}`
      
      const ws = new WebSocket(wsUrl)
      websocketRef.current = ws

      ws.onopen = () => {
        setIsConnected(true)
        setError(null)
        console.log('✅ WebSocket 連接已建立:', wsUrl)
      }

      ws.onmessage = (event) => {
        try {
          const parsedData = JSON.parse(event.data)
          setData(parsedData)
        } catch (_e) {
          // 如果不是 JSON，直接使用原始數據
          setData(event.data)
        }
      }

      ws.onclose = (event) => {
        setIsConnected(false)
        console.log('⚠️ WebSocket 連接已關閉:', event.code, event.reason)
        
        // 自動重連（除非是正常關閉）
        if (event.code !== 1000) {
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log('🔄 正在重新連接 WebSocket...')
            connect()
          }, 3000)
        }
      }

      ws.onerror = (event) => {
        const errorMsg = `WebSocket 連接錯誤: ${url}`
        setError(new Error(errorMsg))
        console.error('❌ WebSocket 錯誤:', event)
      }

    } catch (err) {
      setError(err as Error)
      console.error('❌ 建立 WebSocket 連接時發生錯誤:', err)
    }
  }, [url])

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const send = useCallback((data: any) => {
    if (websocketRef.current && websocketRef.current.readyState === WebSocket.OPEN) {
      const message = typeof data === 'string' ? data : JSON.stringify(data)
      websocketRef.current.send(message)
    } else {
      console.warn('⚠️ WebSocket 未連接，無法發送數據')
    }
  }, [])

  const close = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
    }
    if (websocketRef.current) {
      websocketRef.current.close(1000, 'User closed connection')
    }
  }, [])

  useEffect(() => {
    connect()

    return () => {
      close()
    }
  }, [connect, close])

  return {
    data,
    isConnected,
    error,
    send,
    close
  }
}

export default useWebSocket