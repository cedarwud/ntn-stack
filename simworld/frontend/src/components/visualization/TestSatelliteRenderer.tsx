import React from 'react'
import StaticModel from '../scenes/StaticModel'
import { ApiRoutes } from '../../config/apiRoutes'

interface TestSatelliteRendererProps {
    enabled: boolean
}

const SATELLITE_MODEL_URL = ApiRoutes.simulations.getModel('sat')

const TestSatelliteRenderer: React.FC<TestSatelliteRendererProps> = ({ enabled }) => {
    if (!enabled) {
        return null
    }

    console.log('TestSatelliteRenderer: rendering single static satellite')
    
    return (
        <group>
            {/* 靜態衛星測試 - 完全參考 tower 和 jammer 的做法 */}
            <StaticModel
                url={SATELLITE_MODEL_URL}
                position={[0, 200, 0]}
                scale={[1, 1, 1]}
                pivotOffset={[0, 0, 0]}
            />
        </group>
    )
}

export default TestSatelliteRenderer