/**
 * Toast utility functions and types
 */

export interface ToastMessage {
    id: string
    message: string
    type: 'success' | 'error' | 'warning' | 'info'
    duration?: number
    timestamp: number
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
            timestamp: Date.now(),
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
        this.toasts = this.toasts.filter((toast) => toast.id !== id)
        this.notify()
    }

    subscribe(listener: (toasts: ToastMessage[]) => void) {
        this.listeners.add(listener)
        return () => this.listeners.delete(listener)
    }

    private notify() {
        this.listeners.forEach((listener) => listener([...this.toasts]))
    }

    clear() {
        this.toasts = []
        this.notify()
    }
}

export const toastManager = new ToastManager()
