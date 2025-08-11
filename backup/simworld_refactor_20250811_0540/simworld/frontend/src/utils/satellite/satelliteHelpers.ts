import * as THREE from 'three'
import { MIN_SAT_HEIGHT, MAX_SAT_HEIGHT } from './satelliteConstants'

/**
 * 根據仰角生成衛星顏色
 * @param elevationDeg 衛星仰角(度)
 * @returns THREE.Color 對應的顏色
 */
export const getColorFromElevation = (elevationDeg: number): THREE.Color => {
    // 仰角範圍從 0 到 90 度
    // 將仰角映射到 0-1 之間的數值
    const normalizedElevation = Math.min(Math.max(elevationDeg, 0), 90) / 90

    // 使用藍色到紅色的漸變
    // 低仰角 (接近地平線) = 藍色 (0x0088ff)
    // 高仰角 (接近頭頂) = 紅色 (0xff3300)
    const startColor = new THREE.Color(0x0088ff)
    const endColor = new THREE.Color(0xff3300)

    // 創建顏色漸變
    const color = new THREE.Color()
    color.r = startColor.r + (endColor.r - startColor.r) * normalizedElevation
    color.g = startColor.g + (endColor.g - startColor.g) * normalizedElevation
    color.b = startColor.b + (endColor.b - startColor.b) * normalizedElevation

    return color
}

/**
 * 基於衛星距離計算速度因子
 * @param height 衛星高度
 * @param distance 衛星距離
 * @returns 速度因子
 */
export const calculateSpeedFactor = (height: number, distance: number) => {
    // 模擬低軌衛星視角移動速度 - 近處快，遠處慢
    const normalizedDistance = Math.max(distance, 100) / 2000 // 正規化距離
    const normalizedHeight = Math.max(height, MIN_SAT_HEIGHT) / MAX_SAT_HEIGHT // 正規化高度

    // 指數關係: 距離越近，速度越快
    return Math.pow(normalizedDistance, -0.7) * (0.5 + 0.5 * normalizedHeight)
} 