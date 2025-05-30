import { useState, useEffect, useRef, useCallback } from 'react'

interface WebSocketHookReturn {
    data: any
    connected: boolean
    error: string | null
    connect: () => void
    disconnect: () => void
    send: (data: any) => void
}

export const useWebSocket = (url: string): WebSocketHookReturn => {
    const [data, setData] = useState<any>(null)
    const [connected, setConnected] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const ws = useRef<WebSocket | null>(null)
    const reconnectTimeout = useRef<number | null>(null)

    const connect = useCallback(() => {
        try {
            ws.current = new WebSocket(url)

            ws.current.onopen = () => {
                setConnected(true)
                setError(null)
                console.log('WebSocket connected to:', url)
            }

            ws.current.onmessage = (event) => {
                try {
                    const parsedData = JSON.parse(event.data)
                    setData(parsedData)
                } catch (e) {
                    setData(event.data)
                }
            }

            ws.current.onclose = () => {
                setConnected(false)
                console.log('WebSocket disconnected')
                
                // 自動重連 (5秒後)
                if (reconnectTimeout.current) {
                    clearTimeout(reconnectTimeout.current)
                }
                reconnectTimeout.current = window.setTimeout(() => {
                    connect()
                }, 5000)
            }

            ws.current.onerror = (error) => {
                setError('WebSocket connection error')
                console.error('WebSocket error:', error)
            }
        } catch (e) {
            setError('Failed to create WebSocket connection')
            console.error('WebSocket creation error:', e)
        }
    }, [url])

    const disconnect = useCallback(() => {
        if (reconnectTimeout.current) {
            clearTimeout(reconnectTimeout.current)
        }
        if (ws.current) {
            ws.current.close()
            ws.current = null
        }
        setConnected(false)
    }, [])

    const send = useCallback((data: any) => {
        if (ws.current && ws.current.readyState === WebSocket.OPEN) {
            ws.current.send(typeof data === 'string' ? data : JSON.stringify(data))
        }
    }, [])

    useEffect(() => {
        return () => {
            disconnect()
        }
    }, [disconnect])

    return {
        data,
        connected,
        error,
        connect,
        disconnect,
        send
    }
} 