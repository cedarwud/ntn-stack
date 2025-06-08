import React, { useMemo, useEffect, useState } from 'react'
import * as THREE from 'three'
import { useFrame } from '@react-three/fiber'

interface SINRHeatmapProps {
    devices: any[]
    enabled: boolean
}

const SINRHeatmap: React.FC<SINRHeatmapProps> = ({ devices, enabled }) => {
    const [heatmapData, setHeatmapData] = useState<number[][]>([])
    
    // 計算 SINR 熱力圖數據
    const { texture, geometry } = useMemo(() => {
        if (!enabled) return { texture: null, geometry: null }
        
        const width = 100
        const height = 100
        const data = new Uint8Array(width * height * 4)
        
        // 獲取發射器(Tx)和干擾源(Jammer)位置
        const transmitters = devices.filter(d => d.role === 'desired')
        const jammers = devices.filter(d => d.role === 'jammer')
        
        for (let i = 0; i < height; i++) {
            for (let j = 0; j < width; j++) {
                const x = (j / width) * 200 - 100 // -100 到 +100 的範圍
                const y = (i / height) * 200 - 100
                
                let signalStrength = 0
                let interferenceLevel = 0
                
                // 計算信號強度（來自 Tx 發射器）
                transmitters.forEach(tx => {
                    const distance = Math.sqrt(
                        Math.pow(x - (tx.position_x || 0), 2) + 
                        Math.pow(y - (tx.position_y || 0), 2)
                    )
                    // 簡化的路徑損耗模型 (Free Space Path Loss)
                    const pathLoss = 20 * Math.log10(Math.max(distance, 1)) + 32.45
                    signalStrength += Math.pow(10, (30 - pathLoss) / 10) // 轉換為線性功率
                })
                
                // 計算干擾強度（來自 Jammer 干擾源）
                jammers.forEach(jammer => {
                    const distance = Math.sqrt(
                        Math.pow(x - (jammer.position_x || 0), 2) + 
                        Math.pow(y - (jammer.position_y || 0), 2)
                    )
                    const pathLoss = 20 * Math.log10(Math.max(distance, 1)) + 32.45
                    interferenceLevel += Math.pow(10, (25 - pathLoss) / 10) // 干擾功率
                })
                
                // 計算 SINR (Signal to Interference + Noise Ratio)
                const noise = 1e-12 // 熱雜訊功率
                const sinr = signalStrength / (interferenceLevel + noise)
                const sinrDb = 10 * Math.log10(sinr)
                
                // 將 SINR 映射到顏色 (-20dB 到 +20dB)
                const normalizedSinr = Math.max(0, Math.min(1, (sinrDb + 20) / 40))
                
                const index = (i * width + j) * 4
                
                // 彩色映射：藍色(低) -> 綠色(中) -> 紅色(高)
                if (normalizedSinr < 0.5) {
                    // 藍色到綠色
                    const t = normalizedSinr * 2
                    data[index] = Math.floor(255 * (1 - t))     // R
                    data[index + 1] = Math.floor(255 * t)       // G
                    data[index + 2] = 255                       // B
                } else {
                    // 綠色到紅色
                    const t = (normalizedSinr - 0.5) * 2
                    data[index] = Math.floor(255 * t)           // R
                    data[index + 1] = Math.floor(255 * (1 - t)) // G
                    data[index + 2] = 0                         // B
                }
                data[index + 3] = 180 // Alpha (透明度)
            }
        }
        
        const texture = new THREE.DataTexture(data, width, height, THREE.RGBAFormat)
        texture.needsUpdate = true
        texture.minFilter = THREE.LinearFilter
        texture.magFilter = THREE.LinearFilter
        
        const geometry = new THREE.PlaneGeometry(200, 200)
        
        return { texture, geometry }
    }, [devices, enabled])
    
    if (!enabled || !texture || !geometry) return null
    
    return (
        <mesh position={[0, 0.5, 0]} rotation={[-Math.PI / 2, 0, 0]}>
            <primitive object={geometry} />
            <meshBasicMaterial
                map={texture}
                transparent
                opacity={0.6}
                side={THREE.DoubleSide}
            />
        </mesh>
    )
}

// SINR 圖例組件
export const SINRLegend: React.FC = () => {
    return (
        <div className="sinr-legend" style={{
            position: 'absolute',
            top: '20px',
            right: '20px',
            background: 'rgba(0, 0, 0, 0.8)',
            color: 'white',
            padding: '10px',
            borderRadius: '5px',
            fontSize: '12px',
            zIndex: 1000
        }}>
            <h4 style={{ margin: '0 0 8px 0' }}>SINR 熱力圖</h4>
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: '4px' }}>
                <div style={{ width: '20px', height: '10px', background: 'red', marginRight: '8px' }}></div>
                <span>高 SINR (&gt; 10dB)</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: '4px' }}>
                <div style={{ width: '20px', height: '10px', background: 'green', marginRight: '8px' }}></div>
                <span>中 SINR (0dB)</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center' }}>
                <div style={{ width: '20px', height: '10px', background: 'blue', marginRight: '8px' }}></div>
                <span>低 SINR (&lt; -10dB)</span>
            </div>
        </div>
    )
}

export default SINRHeatmap