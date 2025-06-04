import { Component, ErrorInfo, ReactNode } from 'react'

interface Props {
    children: ReactNode
    fallback?: ReactNode
}

interface State {
    hasError: boolean
    error?: Error
    errorInfo?: ErrorInfo
}

class ErrorBoundary extends Component<Props, State> {
    constructor(props: Props) {
        super(props)
        this.state = { hasError: false }
    }

    static getDerivedStateFromError(error: Error): State {
        return { hasError: true, error }
    }

    componentDidCatch(error: Error, errorInfo: ErrorInfo) {
        console.error('ErrorBoundary 捕獲到錯誤:', error, errorInfo)
        this.setState({ errorInfo })
    }

    render() {
        if (this.state.hasError) {
            return (
                this.props.fallback || (
                    <div className="error-boundary">
                        <h2>出現了一些問題</h2>
                        <p>抱歉，頁面遇到了錯誤。請刷新頁面重試。</p>
                        <button
                            onClick={() => window.location.reload()}
                            className="error-boundary-button"
                        >
                            刷新頁面
                        </button>
                        {import.meta.env.DEV && (
                            <details className="error-details">
                                <summary>錯誤詳情</summary>
                                <pre>{this.state.error?.toString()}</pre>
                                <pre>
                                    {this.state.errorInfo?.componentStack}
                                </pre>
                            </details>
                        )}
                    </div>
                )
            )
        }

        return this.props.children
    }
}

export default ErrorBoundary

// 添加樣式
const styleSheet = document.createElement('style')
styleSheet.type = 'text/css'
styleSheet.innerHTML = `
.error-boundary {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 300px;
    padding: 20px;
    background-color: #f8f9fa;
    border: 1px solid #dee2e6;
    border-radius: 8px;
    margin: 20px;
    text-align: center;
}

.error-boundary h2 {
    color: #dc3545;
    margin-bottom: 16px;
}

.error-boundary p {
    color: #6c757d;
    margin-bottom: 20px;
}

.error-boundary-button {
    background-color: #007bff;
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 16px;
}

.error-boundary-button:hover {
    background-color: #0056b3;
}

.error-details {
    margin-top: 20px;
    text-align: left;
    width: 100%;
    max-width: 600px;
}

.error-details summary {
    cursor: pointer;
    margin-bottom: 10px;
    font-weight: bold;
}

.error-details pre {
    background-color: #f1f3f4;
    padding: 10px;
    border-radius: 4px;
    overflow-x: auto;
    font-size: 12px;
    white-space: pre-wrap;
}
`
document.head.appendChild(styleSheet)
