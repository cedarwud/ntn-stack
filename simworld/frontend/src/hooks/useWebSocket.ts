/**
 * WebSocket Hook
 * 負責管理 WebSocket 連接，提供實時數據更新功能
 */
import { useState, useEffect, useCallback, useRef } from 'react';
import { WebSocketEvent } from '../types/charts';

interface UseWebSocketOptions {
  url?: string;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  enableReconnect?: boolean;
  onMessage?: (event: WebSocketEvent) => void;
  onError?: (error: Event) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
}

interface UseWebSocketReturn {
  isConnected: boolean;
  reconnectCount: number;
  connectionStatus: 'connecting' | 'connected' | 'disconnected' | 'failed';
  sendMessage: (data: any) => void;
  disconnect: () => void;
  connect: () => void;
  resetReconnection: () => void;
}

export const useWebSocket = (options: UseWebSocketOptions = {}): UseWebSocketReturn => {
  const {
    url = '/api/ws',
    reconnectInterval = 5000,
    maxReconnectAttempts = 3,
    enableReconnect = true,
    onMessage,
    onError,
    onConnect,
    onDisconnect
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [reconnectCount, setReconnectCount] = useState(0);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected' | 'failed'>('disconnected');
  
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);
  const shouldReconnect = useRef(true);
  const isManualDisconnect = useRef(false);

  const clearReconnectTimeout = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      window.clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
  }, []);

  const resetReconnection = useCallback(() => {
    setReconnectCount(0);
    shouldReconnect.current = true;
    clearReconnectTimeout();
    if (connectionStatus === 'failed') {
      setConnectionStatus('disconnected');
    }
  }, [connectionStatus, clearReconnectTimeout]);

  const connect = useCallback(() => {
    // 如果已經連接或正在連接，不重複連接
    if (wsRef.current?.readyState === WebSocket.CONNECTING || 
        wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    // 如果超過最大重試次數，標記為失敗
    if (reconnectCount >= maxReconnectAttempts) {
      console.warn(`WebSocket 已達到最大重試次數 (${maxReconnectAttempts})，停止重連`);
      setConnectionStatus('failed');
      shouldReconnect.current = false;
      return;
    }

    try {
      setConnectionStatus('connecting');
      
      // 構建 WebSocket URL - 使用模擬 URL，因為實際沒有 WebSocket 服務
      // 在生產環境中，這裡應該是真實的 WebSocket 服務 URL
      const wsUrl = `ws://localhost:8080/ws`; // 假設 NetStack 提供 WebSocket
      
      console.log(`正在連接 WebSocket (嘗試 ${reconnectCount + 1}/${maxReconnectAttempts}):`, wsUrl);
      
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        console.log('WebSocket 連接已建立');
        setIsConnected(true);
        setConnectionStatus('connected');
        setReconnectCount(0);
        isManualDisconnect.current = false;
        onConnect?.();
      };

      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('收到 WebSocket 消息:', data);
          
          // 轉換為標準格式
          const wsEvent: WebSocketEvent = {
            type: data.type || 'unknown',
            data: data.data || data,
            timestamp: data.timestamp || new Date().toISOString()
          };
          
          onMessage?.(wsEvent);
        } catch (error) {
          console.error('解析 WebSocket 消息失敗:', error);
        }
      };

      wsRef.current.onclose = (event) => {
        console.log('WebSocket 連接已關閉:', event.code, event.reason);
        setIsConnected(false);
        
        if (!isManualDisconnect.current) {
          setConnectionStatus('disconnected');
          onDisconnect?.();

          // 如果需要重連且未超過最大重連次數且啟用重連
          if (shouldReconnect.current && 
              enableReconnect && 
              reconnectCount < maxReconnectAttempts) {
            
            console.log(`將在 ${reconnectInterval}ms 後嘗試重連...`);
            reconnectTimeoutRef.current = window.setTimeout(() => {
              setReconnectCount(prev => prev + 1);
              connect();
            }, reconnectInterval);
          } else if (reconnectCount >= maxReconnectAttempts) {
            setConnectionStatus('failed');
            shouldReconnect.current = false;
          }
        }
      };

      wsRef.current.onerror = (error) => {
        console.error('WebSocket 錯誤:', error);
        setConnectionStatus('disconnected');
        onError?.(error);
      };

    } catch (error) {
      console.error('創建 WebSocket 連接失敗:', error);
      setConnectionStatus('failed');
      onError?.(error as Event);
    }
  }, [reconnectInterval, maxReconnectAttempts, reconnectCount, onMessage, onError, onConnect, onDisconnect, enableReconnect]);

  const disconnect = useCallback(() => {
    console.log('手動斷開 WebSocket 連接');
    isManualDisconnect.current = true;
    shouldReconnect.current = false;
    
    clearReconnectTimeout();

    if (wsRef.current) {
      wsRef.current.close(1000, 'Manual disconnect');
      wsRef.current = null;
    }
    
    setIsConnected(false);
    setConnectionStatus('disconnected');
    setReconnectCount(0);
  }, [clearReconnectTimeout]);

  const sendMessage = useCallback((data: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      try {
        const message = JSON.stringify(data);
        wsRef.current.send(message);
        console.log('發送 WebSocket 消息:', message);
      } catch (error) {
        console.error('發送 WebSocket 消息失敗:', error);
      }
    } else {
      console.warn('WebSocket 未連接，無法發送消息');
    }
  }, []);

  // 組件掛載時嘗試連接（僅在 enableReconnect 為 true 時）
  useEffect(() => {
    if (enableReconnect) {
      // 延遲連接，避免立即失敗
      const connectTimeout = setTimeout(() => {
        connect();
      }, 1000);

      return () => {
        clearTimeout(connectTimeout);
        disconnect();
      };
    }
    
    return () => {
      disconnect();
    };
  }, [enableReconnect]); // 移除 connect 和 disconnect 依賴，避免無限循環

  // 瀏覽器可見性變化時的處理
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible' && 
          !isConnected && 
          enableReconnect && 
          connectionStatus !== 'failed') {
        console.log('頁面變為可見，嘗試重連 WebSocket');
        resetReconnection();
        connect();
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [isConnected, enableReconnect, connectionStatus, resetReconnection, connect]);

  return {
    isConnected,
    reconnectCount,
    connectionStatus,
    sendMessage,
    disconnect,
    connect,
    resetReconnection
  };
};

export default useWebSocket; 