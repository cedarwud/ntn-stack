import { useState, ReactNode, useEffect } from 'react'
import '../../styles/Layout.scss'

interface LayoutProps {
    children?: ReactNode
    sidebar: ReactNode
    content?: ReactNode
    activeComponent: string
}

const Layout: React.FC<LayoutProps> = ({
    children,
    sidebar,
    content,
    activeComponent,
}) => {
    // Initial state: collapsed is true UNLESS activeComponent is '3DRT'
    const [collapsed, setCollapsed] = useState<boolean>(
        activeComponent !== '3DRT'
    )

    useEffect(() => {
        // When activeComponent changes, ensure sidebar is open for 3DRT
        if (activeComponent === '3DRT') {
            setCollapsed(false)
        } else {
            // Optional: collapse for other components if needed, or maintain current state
            // For now, let's explicitly collapse if not 3DRT (matches previous implicit behavior for non-2DRT)
            setCollapsed(true)
        }
    }, [activeComponent])

    const toggleSidebar = () => {
        setCollapsed(!collapsed)
    }

    return (
        <div
            className={`layout ${
                collapsed ? 'sidebar-collapsed' : 'sidebar-expanded'
            }`}
        >
            <div className="sidebar-toggle" onClick={toggleSidebar}>
                ☰
            </div>
            <div className={`sidebar ${collapsed ? 'collapsed' : ''}`}>
                <div className="sidebar-content">{sidebar}</div>
            </div>
            <main className="main-content">{content || children}</main>
        </div>
    )
}

export default Layout
