/**
 * Toast 通知組件
 * 用於顯示系統警告和狀態通知
 */

import React, { useState, useEffect, useCallback } from 'react'
import './ToastNotification.scss'

export interface ToastMessage {
  id: string
  message: string
  type: 'success' | 'error' | 'warning' | 'info'
  duration?: number
  timestamp: number
}

interface ToastNotificationProps {
  maxToasts?: number
}

// 全局 toast 管理器
class ToastManager {
  private listeners: Set<(toasts: ToastMessage[]) => void> = new Set()
  private toasts: ToastMessage[] = []
  private nextId = 1

  addToast(message: string, type: ToastMessage['type'], duration = 5000) {
    const toast: ToastMessage = {
      id: `toast-${this.nextId++}`,
      message,
      type,
      duration,
      timestamp: Date.now()
    }

    this.toasts = [toast, ...this.toasts].slice(0, 5) // 最多顯示5個
    this.notify()

    if (duration > 0) {
      setTimeout(() => {
        this.removeToast(toast.id)
      }, duration)
    }

    return toast.id
  }

  removeToast(id: string) {
    this.toasts = this.toasts.filter(toast => toast.id !== id)
    this.notify()
  }

  subscribe(listener: (toasts: ToastMessage[]) => void) {
    this.listeners.add(listener)
    return () => this.listeners.delete(listener)
  }

  private notify() {
    this.listeners.forEach(listener => listener([...this.toasts]))
  }

  clear() {
    this.toasts = []
    this.notify()
  }
}

export const toastManager = new ToastManager()

// React Hook
export const useToast = () => {
  const [toasts, setToasts] = useState<ToastMessage[]>([])

  useEffect(() => {
    return toastManager.subscribe(setToasts)
  }, [])

  const showToast = useCallback((message: string, type: ToastMessage['type'] = 'info', duration?: number) => {
    return toastManager.addToast(message, type, duration)
  }, [])

  const removeToast = useCallback((id: string) => {
    toastManager.removeToast(id)
  }, [])

  const clearToasts = useCallback(() => {
    toastManager.clear()
  }, [])

  return { toasts, showToast, removeToast, clearToasts }
}

// Toast 容器組件
const ToastNotification: React.FC<ToastNotificationProps> = ({ maxToasts = 5 }) => {
  const { toasts, removeToast } = useToast()

  const getToastIcon = (type: ToastMessage['type']) => {
    switch (type) {
      case 'success': return '✅'
      case 'error': return '❌'
      case 'warning': return '⚠️'
      case 'info': return 'ℹ️'
      default: return 'ℹ️'
    }
  }

  const getToastClass = (type: ToastMessage['type']) => {
    return `toast toast--${type}`
  }

  return (
    <div className="toast-container">
      {toasts.slice(0, maxToasts).map((toast) => (
        <div 
          key={toast.id} 
          className={getToastClass(toast.type)}
          onClick={() => removeToast(toast.id)}
        >
          <div className="toast__content">
            <span className="toast__icon">{getToastIcon(toast.type)}</span>
            <span className="toast__message">{toast.message}</span>
            <button 
              className="toast__close"
              onClick={(e) => {
                e.stopPropagation()
                removeToast(toast.id)
              }}
            >
              ×
            </button>
          </div>
        </div>
      ))}
    </div>
  )
}

export default ToastNotification