/**
 * Toast 工具函數和管理器
 * 分離出來以避免 Fast Refresh 警告
 */
import { useState, useEffect, useCallback } from 'react'

export interface ToastMessage {
  id: string
  message: string
  type: 'success' | 'error' | 'warning' | 'info'
  duration?: number
  timestamp: number
}

class ToastManager {
  private toasts: ToastMessage[] = []
  private listeners: Set<(toasts: ToastMessage[]) => void> = new Set()

  subscribe(listener: (toasts: ToastMessage[]) => void) {
    this.listeners.add(listener)
    listener(this.toasts)
    
    return () => {
      this.listeners.delete(listener)
    }
  }

  private notify() {
    this.listeners.forEach(listener => listener([...this.toasts]))
  }

  addToast(message: string, type: ToastMessage['type'] = 'info', duration = 5000) {
    const id = Math.random().toString(36).substr(2, 9)
    const toast: ToastMessage = {
      id,
      message,
      type,
      duration,
      timestamp: Date.now()
    }

    this.toasts.push(toast)
    this.notify()

    if (duration > 0) {
      setTimeout(() => {
        this.removeToast(id)
      }, duration)
    }

    return id
  }

  removeToast(id: string) {
    this.toasts = this.toasts.filter(toast => toast.id !== id)
    this.notify()
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

  const hideToast = useCallback((id: string) => {
    toastManager.removeToast(id)
  }, [])

  const clearToasts = useCallback(() => {
    toastManager.clear()
  }, [])

  return {
    toasts,
    showToast,
    hideToast,
    clearToasts
  }
}
