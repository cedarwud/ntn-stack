import React, { useState, useEffect } from 'react'
import { Html } from '@react-three/drei'

interface Device {
    id: string | number;
    role?: string;
    position_x?: number;
    position_y?: number;
    position_z?: number;
    [key: string]: unknown;
}

interface UAVSwarmCoordinationProps {
    devices: Device[]
    enabled: boolean
}

interface BasicUEInfo {
    id: string | number
    position: [number, number, number]
    isActive: boolean
}

const UAVSwarmCoordination: React.FC<UAVSwarmCoordinationProps> = ({ devices, enabled }) => {
    const [ueList, setUeList] = useState<BasicUEInfo[]>([])
    const [basicMetrics, setBasicMetrics] = useState({
        totalUEs: 0,
        activeUEs: 0
    })

    // 簡化的多UE管理 - 僅追踪基本信息
    useEffect(() => {
        if (!enabled) {
            setUeList([])
            setBasicMetrics({ totalUEs: 0, activeUEs: 0 })
            return
        }

        const updateUEList = () => {
            const receivers = devices.filter(d => d.role === 'receiver')
            
            const ueInfoList: BasicUEInfo[] = receivers.map(device => ({
                id: device.id,
                position: [
                    device.position_x ?? 0,
                    device.position_y ?? 0,
                    device.position_z ?? 0
                ],
                isActive: true
            }))

            setUeList(ueInfoList)
            setBasicMetrics({
                totalUEs: receivers.length,
                activeUEs: receivers.length
            })
        }

        updateUEList()
        const interval = setInterval(updateUEList, 2000) // 每2秒更新基本信息

        return () => clearInterval(interval)
    }, [devices, enabled])

    if (!enabled) return null

    return (
        <>
            {/* 簡化的UE狀態顯示 */}
            <Html position={[0, 5, 0]} center>
                <div className="ue-coordination-panel" style={{
                    background: 'rgba(0, 0, 0, 0.8)',
                    color: 'white',
                    padding: '10px',
                    borderRadius: '5px',
                    fontSize: '12px',
                    minWidth: '200px'
                }}>
                    <h4 style={{ margin: '0 0 8px 0', color: '#4CAF50' }}>
                        多UE管理 (簡化版)
                    </h4>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                        <div>總UE數: {basicMetrics.totalUEs}</div>
                        <div>活躍UE數: {basicMetrics.activeUEs}</div>
                        <div style={{ marginTop: '8px', fontSize: '10px', color: '#999' }}>
                            註: 編隊協調功能已移除，專注於基本UE管理
                        </div>
                    </div>
                </div>
            </Html>

            {/* UE位置標記 */}
            {ueList.map((ue) => (
                <Html key={ue.id} position={ue.position} center>
                    <div style={{
                        width: '8px',
                        height: '8px',
                        backgroundColor: '#4CAF50',
                        borderRadius: '50%',
                        border: '1px solid white',
                        boxShadow: '0 0 4px rgba(76, 175, 80, 0.6)'
                    }} />
                </Html>
            ))}
        </>
    )
}

export default UAVSwarmCoordination