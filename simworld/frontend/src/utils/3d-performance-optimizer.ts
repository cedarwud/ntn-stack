/**
 * Three.js 3D 渲染性能優化工具
 * 為 LEO 衛星換手研究項目提供專用的 3D 性能優化
 */

import * as THREE from 'three'

export class ThreeJSPerformanceOptimizer {
  private static instance: ThreeJSPerformanceOptimizer
  private rendererCache = new WeakMap<THREE.Renderer, boolean>()
  private materialCache = new Map<string, THREE.Material>()
  private geometryCache = new Map<string, THREE.Geometry | THREE.BufferGeometry>()
  
  private constructor() {}
  
  static getInstance(): ThreeJSPerformanceOptimizer {
    if (!ThreeJSPerformanceOptimizer.instance) {
      ThreeJSPerformanceOptimizer.instance = new ThreeJSPerformanceOptimizer()
    }
    return ThreeJSPerformanceOptimizer.instance
  }

  /**
   * 優化 WebGL 渲染器設置 - 專為衛星可視化調優
   */
  optimizeRenderer(renderer: THREE.WebGLRenderer): void {
    if (this.rendererCache.has(renderer)) return
    
    // 基礎性能優化
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2)) // 限制像素比率
    renderer.setClearColor(0x000011, 1) // 太空背景色
    
    // 衛星場景專用優化
    renderer.sortObjects = false // 關閉自動排序（手動控制渲染順序）
    renderer.shadowMap.enabled = false // 衛星場景不需要陰影
    
    // 抗鋸齒優化（針對線條和軌道）
    renderer.antialias = true
    
    // WebGL 優化
    const gl = renderer.getContext()
    if (gl) {
      gl.disable(gl.DITHER) // 關閉抖動
      gl.disable(gl.CULL_FACE) // 衛星模型可能需要雙面渲染
    }
    
    this.rendererCache.set(renderer, true)
  }

  /**
   * 創建優化的衛星材質
   */
  createOptimizedSatelliteMaterial(
    type: 'active' | 'inactive' | 'predicted' | 'orbit',
    customColor?: number
  ): THREE.Material {
    const cacheKey = `satellite-${type}-${customColor || 'default'}`
    
    if (this.materialCache.has(cacheKey)) {
      return this.materialCache.get(cacheKey)!.clone()
    }
    
    let material: THREE.Material
    
    switch (type) {
      case 'active':
        // 當前連接的衛星 - 高亮顯示
        material = new THREE.MeshBasicMaterial({
          color: customColor || 0x00ff00,
          transparent: true,
          opacity: 0.9,
          side: THREE.DoubleSide
        })
        break
        
      case 'predicted':
        // 預測的目標衛星 - 警告色
        material = new THREE.MeshBasicMaterial({
          color: customColor || 0xffaa00,
          transparent: true,
          opacity: 0.8,
          side: THREE.DoubleSide
        })
        break
        
      case 'orbit':
        // 軌道線材質
        material = new THREE.LineBasicMaterial({
          color: customColor || 0x4444ff,
          transparent: true,
          opacity: 0.3,
          linewidth: 1
        })
        break
        
      default:
        // 普通衛星
        material = new THREE.MeshBasicMaterial({
          color: customColor || 0x666666,
          transparent: true,
          opacity: 0.6,
          side: THREE.DoubleSide
        })
    }
    
    // 性能優化設置
    material.needsUpdate = false
    
    this.materialCache.set(cacheKey, material)
    return material.clone()
  }

  /**
   * 創建優化的衛星幾何體
   */
  createOptimizedSatelliteGeometry(type: 'cube' | 'sphere' | 'detailed'): THREE.BufferGeometry {
    const cacheKey = `geometry-${type}`
    
    if (this.geometryCache.has(cacheKey)) {
      return this.geometryCache.get(cacheKey)! as THREE.BufferGeometry
    }
    
    let geometry: THREE.BufferGeometry
    
    switch (type) {
      case 'sphere':
        // 低多邊形球體 - 遠距離衛星
        geometry = new THREE.SphereGeometry(0.5, 8, 6)
        break
        
      case 'detailed':
        // 詳細模型 - 近距離或重要衛星
        geometry = new THREE.BoxGeometry(0.8, 0.3, 1.2)
        break
        
      default:
        // 預設立方體 - 平衡性能和視覺效果
        geometry = new THREE.BoxGeometry(0.6, 0.6, 0.6)
    }
    
    // 性能優化
    geometry.computeBoundingSphere()
    
    this.geometryCache.set(cacheKey, geometry)
    return geometry
  }

  /**
   * LOD (Level of Detail) 系統
   * 根據距離動態調整衛星模型複雜度
   */
  createSatelliteLOD(position: [number, number, number], cameraDistance: number): {
    geometry: THREE.BufferGeometry
    material: THREE.Material
    shouldRender: boolean
  } {
    const distance = cameraDistance
    
    // 距離閾值
    const NEAR_DISTANCE = 20
    const FAR_DISTANCE = 100
    const CULL_DISTANCE = 200
    
    if (distance > CULL_DISTANCE) {
      return { 
        geometry: this.createOptimizedSatelliteGeometry('cube'), 
        material: this.createOptimizedSatelliteMaterial('inactive'),
        shouldRender: false 
      }
    }
    
    if (distance < NEAR_DISTANCE) {
      // 近距離 - 詳細模型
      return {
        geometry: this.createOptimizedSatelliteGeometry('detailed'),
        material: this.createOptimizedSatelliteMaterial('active'),
        shouldRender: true
      }
    } else if (distance < FAR_DISTANCE) {
      // 中距離 - 標準模型
      return {
        geometry: this.createOptimizedSatelliteGeometry('cube'),
        material: this.createOptimizedSatelliteMaterial('inactive'),
        shouldRender: true
      }
    } else {
      // 遠距離 - 簡化模型
      return {
        geometry: this.createOptimizedSatelliteGeometry('sphere'),
        material: this.createOptimizedSatelliteMaterial('inactive'),
        shouldRender: true
      }
    }
  }

  /**
   * 批量更新衛星位置 - 減少渲染調用
   */
  updateSatellitePositions(
    satellites: Array<{
      mesh: THREE.Mesh
      targetPosition: [number, number, number]
      currentPosition: [number, number, number]
    }>,
    deltaTime: number,
    speedMultiplier: number = 1
  ): void {
    const lerpFactor = Math.min(deltaTime * speedMultiplier * 2, 1)
    
    satellites.forEach(({ mesh, targetPosition, currentPosition }) => {
      // 使用線性插值平滑移動
      currentPosition[0] = THREE.MathUtils.lerp(currentPosition[0], targetPosition[0], lerpFactor)
      currentPosition[1] = THREE.MathUtils.lerp(currentPosition[1], targetPosition[1], lerpFactor)
      currentPosition[2] = THREE.MathUtils.lerp(currentPosition[2], targetPosition[2], lerpFactor)
      
      mesh.position.set(...currentPosition)
    })
  }

  /**
   * 清理緩存 - 防止內存洩漏
   */
  clearCache(): void {
    // 清理材質緩存
    this.materialCache.forEach(material => material.dispose())
    this.materialCache.clear()
    
    // 清理幾何體緩存
    this.geometryCache.forEach(geometry => geometry.dispose())
    this.geometryCache.clear()
    
    // 清理渲染器緩存
    this.rendererCache = new WeakMap()
  }

  /**
   * 性能監控 - 獲取渲染統計
   */
  getPerformanceStats(renderer: THREE.WebGLRenderer): {
    drawCalls: number
    triangles: number
    points: number
    lines: number
    memory: {
      geometries: number
      textures: number
    }
  } {
    const info = renderer.info
    
    return {
      drawCalls: info.render.calls,
      triangles: info.render.triangles,
      points: info.render.points,
      lines: info.render.lines,
      memory: {
        geometries: info.memory.geometries,
        textures: info.memory.textures
      }
    }
  }
}

// 全局實例
export const threePerformanceOptimizer = ThreeJSPerformanceOptimizer.getInstance()