import React from 'react'
import Dashboard from '../components/dashboard/Dashboard'

interface DashboardPageProps {
    currentScene?: string
}

const DashboardPage: React.FC<DashboardPageProps> = ({
    currentScene = 'default-scene',
}) => {
    return (
        <div className="dashboard-page">
            <Dashboard currentScene={currentScene} />
        </div>
    )
}

export default DashboardPage
