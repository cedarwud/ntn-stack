import React, { useEffect, useRef, useState, useCallback, useMemo } from 'react'
import * as THREE from 'three'
import { useWebSocket } from '../../hooks/useWebSocket'
import { WebSocketEvent } from '../../types/charts'

interface InterferenceSource {
  id: string
  name: string
  position: { x: number; y: number; z: number }
  frequency_mhz: number
  power_dbm: number
  bandwidth_mhz: number
  interference_type: 'jammer' | 'unintentional' | 'adjacent_channel' | 'spurious'
  coverage_radius_m: number
  azimuth_deg?: number
  elevation_deg?: number
  beam_width_deg?: number
  active: boolean
  severity: 'low' | 'medium' | 'high' | 'critical'
  detection_time: string
}

interface VictimDevice {
  id: string
  name: string
  position: { x: number; y: number; z: number }
  frequency_mhz: number
  sinr_db: number
  affected_by: string[]
  protection_level: 'normal' | 'enhanced' | 'critical'
}

interface InterferenceVisualizationProps {
  currentScene?: string
  autoRotate?: boolean
  showGrid?: boolean
  showLabels?: boolean
  onInterferenceSourceClick?: (source: InterferenceSource) => void
  onVictimDeviceClick?: (device: VictimDevice) => void
}

const InterferenceVisualization: React.FC<InterferenceVisualizationProps> = ({
  currentScene = 'NYCU',
  autoRotate = true,
  showGrid = true,
  showLabels = true,
  onInterferenceSourceClick,
  onVictimDeviceClick
}) => {
  const containerRef = useRef<HTMLDivElement>(null)
  const sceneRef = useRef<THREE.Scene | null>(null)
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null)
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null)
  const controlsRef = useRef<any>(null)
  const animationFrameRef = useRef<number | null>(null)
  
  // 物件引用用於更新和交互
  const interferenceObjectsRef = useRef<Map<string, THREE.Group>>(new Map())
  const victimObjectsRef = useRef<Map<string, THREE.Group>>(new Map())
  const impactRangesRef = useRef<Map<string, THREE.Mesh>>(new Map())
  const raycasterRef = useRef<THREE.Raycaster>(new THREE.Raycaster())
  const mouseRef = useRef<THREE.Vector2>(new THREE.Vector2())
  
  // 狀態管理
  const [isInitialized, setIsInitialized] = useState(false)
  const [interferenceData, setInterferenceData] = useState<InterferenceSource[]>([])
  const [victimDevices, setVictimDevices] = useState<VictimDevice[]>([])
  const [hoveredObject, setHoveredObject] = useState<string | null>(null)
  const [selectedObject, setSelectedObject] = useState<string | null>(null)
  const [visualizationMode, setVisualizationMode] = useState<'impact' | 'frequency' | 'power'>('impact')
  const [realTimeEnabled, setRealTimeEnabled] = useState(true)
  const [lastUpdate, setLastUpdate] = useState<string | null>(null)
  
  // 配置選項
  const [showInterferenceRanges, setShowInterferenceRanges] = useState(true)
  const [showFrequencyBands, setShowFrequencyBands] = useState(false)
  const [animateEffects, setAnimateEffects] = useState(true)
  const [opacity, setOpacity] = useState(0.6)

  // WebSocket 連接處理干擾數據
  const { isConnected, sendMessage } = useWebSocket({
    url: 'ws://localhost:8080/ws/interference-visualization',
    enableReconnect: realTimeEnabled,
    onMessage: handleWebSocketMessage,
    onConnect: () => {
      console.log('Interference Visualization WebSocket 已連接')
      if (realTimeEnabled) {
        sendMessage({
          type: 'subscribe',
          topics: ['interference_detection', 'victim_updates', 'mitigation_effects']
        })
      }
    }
  })

  // 處理 WebSocket 消息
  function handleWebSocketMessage(event: WebSocketEvent) {
    try {
      switch (event.type) {
        case 'interference_updates':
          if (event.data.interference_sources) {
            setInterferenceData(event.data.interference_sources)
          }
          if (event.data.victim_devices) {
            setVictimDevices(event.data.victim_devices)
          }
          setLastUpdate(event.timestamp)
          break
          
        case 'ai_ran_decisions':
          // AI 決策後更新可視化效果
          if (event.data.mitigation_applied) {
            updateMitigationEffects(event.data)
          }
          break
      }
    } catch (error) {
      console.error('處理 WebSocket 消息失敗:', error)
    }
  }

  // 初始化 Three.js 場景
  const initializeThreeJS = useCallback(() => {
    if (!containerRef.current || isInitialized) return

    try {
      // 創建場景
      const scene = new THREE.Scene()
      scene.background = new THREE.Color(0x1a1a1a)
      scene.fog = new THREE.Fog(0x1a1a1a, 500, 2000)

      // 創建攝像機
      const camera = new THREE.PerspectiveCamera(
        75,
        containerRef.current.clientWidth / containerRef.current.clientHeight,
        0.1,
        2000
      )
      camera.position.set(100, 150, 200)

      // 創建渲染器
      const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
      renderer.setSize(containerRef.current.clientWidth, containerRef.current.clientHeight)
      renderer.setPixelRatio(window.devicePixelRatio)
      renderer.shadowMap.enabled = true
      renderer.shadowMap.type = THREE.PCFSoftShadowMap
      renderer.gammaOutput = true
      renderer.gammaFactor = 2.2
      containerRef.current.appendChild(renderer.domElement)

      // 添加光照
      setupLighting(scene)

      // 添加網格
      if (showGrid) {
        addGrid(scene)
      }

      // 初始化控制器（需要 OrbitControls）
      try {
        const { OrbitControls } = require('three/examples/jsm/controls/OrbitControls')
        const controls = new OrbitControls(camera, renderer.domElement)
        controls.enableDamping = true
        controls.dampingFactor = 0.05
        controls.enableZoom = true
        controls.autoRotate = autoRotate
        controls.autoRotateSpeed = 1.0
        controlsRef.current = controls
      } catch (error) {
        console.warn('OrbitControls 不可用:', error)
      }

      // 添加事件監聽器
      renderer.domElement.addEventListener('mousemove', onMouseMove)
      renderer.domElement.addEventListener('click', onMouseClick)
      window.addEventListener('resize', onWindowResize)

      sceneRef.current = scene
      rendererRef.current = renderer
      cameraRef.current = camera

      setIsInitialized(true)
      startRenderLoop()

    } catch (error) {
      console.error('初始化 Three.js 失敗:', error)
    }
  }, [isInitialized, showGrid, autoRotate])

  // 設置光照
  const setupLighting = (scene: THREE.Scene) => {
    // 環境光
    const ambientLight = new THREE.AmbientLight(0x404040, 0.3)
    scene.add(ambientLight)

    // 主方向光
    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.7)
    directionalLight.position.set(200, 200, 100)
    directionalLight.castShadow = true
    directionalLight.shadow.mapSize.width = 2048
    directionalLight.shadow.mapSize.height = 2048
    directionalLight.shadow.camera.near = 0.5
    directionalLight.shadow.camera.far = 1000
    scene.add(directionalLight)

    // 補充光源
    const fillLight = new THREE.DirectionalLight(0x9090ff, 0.2)
    fillLight.position.set(-100, 50, -100)
    scene.add(fillLight)
  }

  // 添加網格
  const addGrid = (scene: THREE.Scene) => {
    const gridHelper = new THREE.GridHelper(1000, 50, 0x444444, 0x222222)
    gridHelper.position.y = 0
    scene.add(gridHelper)

    // 坐標軸
    const axesHelper = new THREE.AxesHelper(100)
    scene.add(axesHelper)
  }

  // 創建干擾源可視化
  const createInterferenceSource = useCallback((source: InterferenceSource): THREE.Group => {
    const group = new THREE.Group()
    group.userData = { type: 'interference_source', id: source.id, data: source }

    // 根據干擾類型選擇顏色和形狀
    const colors = {
      jammer: 0xff0000,
      unintentional: 0xff8800,
      adjacent_channel: 0xffff00,
      spurious: 0xff4400
    }

    const severityScale = {
      low: 0.8,
      medium: 1.2,
      high: 1.6,
      critical: 2.0
    }

    const color = colors[source.interference_type] || 0xff0000
    const scale = severityScale[source.severity] || 1.0

    // 創建干擾源主體
    const geometry = new THREE.SphereGeometry(5 * scale, 16, 16)
    const material = new THREE.MeshPhongMaterial({
      color: color,
      emissive: new THREE.Color(color).multiplyScalar(0.2),
      transparent: true,
      opacity: source.active ? 0.9 : 0.5
    })
    const mesh = new THREE.Mesh(geometry, material)
    mesh.position.set(source.position.x, source.position.y, source.position.z)
    mesh.castShadow = true
    group.add(mesh)

    // 添加影響範圍可視化
    if (showInterferenceRanges) {
      const rangeGeometry = new THREE.SphereGeometry(source.coverage_radius_m, 32, 16)
      const rangeMaterial = new THREE.MeshBasicMaterial({
        color: color,
        transparent: true,
        opacity: opacity * 0.3,
        wireframe: false,
        side: THREE.DoubleSide
      })
      const rangeMesh = new THREE.Mesh(rangeGeometry, rangeMaterial)
      rangeMesh.position.copy(mesh.position)
      group.add(rangeMesh)
      impactRangesRef.current.set(source.id, rangeMesh)
    }

    // 添加定向天線可視化（如果有方向信息）
    if (source.azimuth_deg !== undefined && source.beam_width_deg) {
      const beamGroup = createDirectionalBeam(source)
      group.add(beamGroup)
    }

    // 添加標籤
    if (showLabels) {
      const label = createTextLabel(source.name, color)
      label.position.set(source.position.x, source.position.y + 15, source.position.z)
      group.add(label)
    }

    // 添加動畫效果
    if (animateEffects && source.active) {
      addPulseAnimation(mesh)
    }

    return group
  }, [showInterferenceRanges, showLabels, animateEffects, opacity])

  // 創建受害設備可視化
  const createVictimDevice = useCallback((device: VictimDevice): THREE.Group => {
    const group = new THREE.Group()
    group.userData = { type: 'victim_device', id: device.id, data: device }

    // 根據保護級別和 SINR 選擇顏色
    const getDeviceColor = (sinr: number, protection: string) => {
      if (protection === 'critical') return 0x9c27b0 // 紫色
      if (sinr < -10) return 0xf44336 // 紅色 - 嚴重干擾
      if (sinr < 0) return 0xff9800 // 橙色 - 中等干擾
      if (sinr < 10) return 0xffeb3b // 黃色 - 輕微干擾
      return 0x4caf50 // 綠色 - 正常
    }

    const color = getDeviceColor(device.sinr_db, device.protection_level)

    // 創建設備主體（立方體表示設備）
    const geometry = new THREE.BoxGeometry(8, 8, 8)
    const material = new THREE.MeshPhongMaterial({
      color: color,
      emissive: new THREE.Color(color).multiplyScalar(0.1)
    })
    const mesh = new THREE.Mesh(geometry, material)
    mesh.position.set(device.position.x, device.position.y, device.position.z)
    mesh.castShadow = true
    mesh.receiveShadow = true
    group.add(mesh)

    // 添加保護範圍指示器
    if (device.protection_level === 'critical' || device.protection_level === 'enhanced') {
      const protectionGeometry = new THREE.SphereGeometry(20, 16, 8)
      const protectionMaterial = new THREE.MeshBasicMaterial({
        color: 0x2196f3,
        transparent: true,
        opacity: 0.2,
        wireframe: true
      })
      const protectionMesh = new THREE.Mesh(protectionGeometry, protectionMaterial)
      protectionMesh.position.copy(mesh.position)
      group.add(protectionMesh)
    }

    // 添加 SINR 指示條
    const sinrBar = createSINRIndicator(device.sinr_db)
    sinrBar.position.set(device.position.x + 15, device.position.y, device.position.z)
    group.add(sinrBar)

    // 添加標籤
    if (showLabels) {
      const label = createTextLabel(`${device.name}\n${device.sinr_db.toFixed(1)} dB`, color)
      label.position.set(device.position.x, device.position.y + 20, device.position.z)
      group.add(label)
    }

    return group
  }, [showLabels])

  // 創建定向波束可視化
  const createDirectionalBeam = (source: InterferenceSource): THREE.Group => {
    const group = new THREE.Group()
    
    if (!source.azimuth_deg || !source.beam_width_deg) return group

    const beamLength = source.coverage_radius_m
    const beamWidth = (source.beam_width_deg * Math.PI) / 180

    // 創建圓錐形波束
    const geometry = new THREE.ConeGeometry(
      beamLength * Math.tan(beamWidth / 2),
      beamLength,
      8,
      1,
      true
    )
    const material = new THREE.MeshBasicMaterial({
      color: 0xff6600,
      transparent: true,
      opacity: 0.3,
      side: THREE.DoubleSide
    })
    const beam = new THREE.Mesh(geometry, material)
    
    // 設置波束方向
    beam.rotation.x = -Math.PI / 2
    beam.rotation.z = (source.azimuth_deg * Math.PI) / 180
    if (source.elevation_deg) {
      beam.rotation.y = (source.elevation_deg * Math.PI) / 180
    }
    
    beam.position.set(source.position.x, source.position.y, source.position.z)
    group.add(beam)

    return group
  }

  // 創建 SINR 指示條
  const createSINRIndicator = (sinr: number): THREE.Group => {
    const group = new THREE.Group()
    
    // 標準化 SINR 值到 0-1 範圍
    const normalizedSINR = Math.max(0, Math.min(1, (sinr + 20) / 40))
    
    // 創建背景條
    const bgGeometry = new THREE.BoxGeometry(2, 20, 2)
    const bgMaterial = new THREE.MeshBasicMaterial({ color: 0x333333 })
    const bgMesh = new THREE.Mesh(bgGeometry, bgMaterial)
    group.add(bgMesh)
    
    // 創建 SINR 條
    const sinrHeight = normalizedSINR * 20
    const sinrGeometry = new THREE.BoxGeometry(1.8, sinrHeight, 1.8)
    const sinrColor = normalizedSINR > 0.7 ? 0x4caf50 : 
                     normalizedSINR > 0.4 ? 0xffeb3b : 0xf44336
    const sinrMaterial = new THREE.MeshBasicMaterial({ color: sinrColor })
    const sinrMesh = new THREE.Mesh(sinrGeometry, sinrMaterial)
    sinrMesh.position.y = (sinrHeight - 20) / 2
    group.add(sinrMesh)
    
    return group
  }

  // 創建文字標籤
  const createTextLabel = (text: string, color: number): THREE.Sprite => {
    const canvas = document.createElement('canvas')
    const context = canvas.getContext('2d')
    if (!context) return new THREE.Sprite()

    canvas.width = 256
    canvas.height = 64
    context.fillStyle = '#000000'
    context.fillRect(0, 0, canvas.width, canvas.height)
    context.fillStyle = `#${color.toString(16).padStart(6, '0')}`
    context.font = '16px Arial'
    context.textAlign = 'center'
    context.fillText(text, canvas.width / 2, canvas.height / 2)

    const texture = new THREE.CanvasTexture(canvas)
    const material = new THREE.SpriteMaterial({ map: texture })
    const sprite = new THREE.Sprite(material)
    sprite.scale.set(30, 15, 1)

    return sprite
  }

  // 添加脈衝動畫
  const addPulseAnimation = (mesh: THREE.Mesh) => {
    const startScale = mesh.scale.clone()
    const animate = () => {
      const time = Date.now() * 0.005
      const scale = 1 + Math.sin(time) * 0.2
      mesh.scale.copy(startScale).multiplyScalar(scale)
    }
    mesh.userData.animate = animate
  }

  // 更新緩解效果
  const updateMitigationEffects = (mitigationData: any) => {
    if (mitigationData.affected_sources) {
      mitigationData.affected_sources.forEach((sourceId: string) => {
        const sourceObject = interferenceObjectsRef.current.get(sourceId)
        if (sourceObject) {
          // 添加緩解效果動畫
          const mesh = sourceObject.children.find(child => child instanceof THREE.Mesh) as THREE.Mesh
          if (mesh) {
            const originalColor = mesh.material as THREE.MeshPhongMaterial
            // 閃爍效果表示緩解措施已應用
            const flashAnimation = () => {
              originalColor.emissive.setHex(0x00ff00)
              setTimeout(() => {
                originalColor.emissive.setHex(0x000000)
              }, 200)
            }
            flashAnimation()
          }
        }
      })
    }
  }

  // 鼠標移動處理
  const onMouseMove = useCallback((event: MouseEvent) => {
    if (!containerRef.current || !cameraRef.current || !sceneRef.current) return

    const rect = containerRef.current.getBoundingClientRect()
    mouseRef.current.x = ((event.clientX - rect.left) / rect.width) * 2 - 1
    mouseRef.current.y = -((event.clientY - rect.top) / rect.height) * 2 + 1

    raycasterRef.current.setFromCamera(mouseRef.current, cameraRef.current)
    
    const allObjects: THREE.Object3D[] = []
    interferenceObjectsRef.current.forEach(obj => allObjects.push(...obj.children))
    victimObjectsRef.current.forEach(obj => allObjects.push(...obj.children))

    const intersects = raycasterRef.current.intersectObjects(allObjects, true)
    
    if (intersects.length > 0) {
      const intersectedObject = intersects[0].object
      let parent = intersectedObject.parent
      while (parent && !parent.userData.type) {
        parent = parent.parent
      }
      
      if (parent && parent.userData.id !== hoveredObject) {
        setHoveredObject(parent.userData.id)
        document.body.style.cursor = 'pointer'
      }
    } else {
      if (hoveredObject) {
        setHoveredObject(null)
        document.body.style.cursor = 'default'
      }
    }
  }, [hoveredObject])

  // 鼠標點擊處理
  const onMouseClick = useCallback((event: MouseEvent) => {
    if (!hoveredObject) return

    const interferenceObj = interferenceObjectsRef.current.get(hoveredObject)
    const victimObj = victimObjectsRef.current.get(hoveredObject)

    if (interferenceObj && onInterferenceSourceClick) {
      onInterferenceSourceClick(interferenceObj.userData.data)
      setSelectedObject(hoveredObject)
    } else if (victimObj && onVictimDeviceClick) {
      onVictimDeviceClick(victimObj.userData.data)
      setSelectedObject(hoveredObject)
    }
  }, [hoveredObject, onInterferenceSourceClick, onVictimDeviceClick])

  // 窗口大小調整處理
  const onWindowResize = useCallback(() => {
    if (!containerRef.current || !cameraRef.current || !rendererRef.current) return

    const width = containerRef.current.clientWidth
    const height = containerRef.current.clientHeight

    cameraRef.current.aspect = width / height
    cameraRef.current.updateProjectionMatrix()
    rendererRef.current.setSize(width, height)
  }, [])

  // 渲染循環
  const renderLoop = useCallback(() => {
    if (!rendererRef.current || !sceneRef.current || !cameraRef.current) return

    // 更新控制器
    if (controlsRef.current) {
      controlsRef.current.update()
    }

    // 更新動畫
    const updateAnimations = (object: THREE.Object3D) => {
      if (object.userData.animate) {
        object.userData.animate()
      }
      object.children.forEach(updateAnimations)
    }
    sceneRef.current.traverse(updateAnimations)

    rendererRef.current.render(sceneRef.current, cameraRef.current)
    animationFrameRef.current = requestAnimationFrame(renderLoop)
  }, [])

  const startRenderLoop = useCallback(() => {
    if (animationFrameRef.current) return
    animationFrameRef.current = requestAnimationFrame(renderLoop)
  }, [renderLoop])

  // 更新場景中的干擾源
  useEffect(() => {
    if (!sceneRef.current || !isInitialized) return

    // 清除現有的干擾源
    interferenceObjectsRef.current.forEach((obj, id) => {
      sceneRef.current!.remove(obj)
    })
    interferenceObjectsRef.current.clear()
    impactRangesRef.current.clear()

    // 添加新的干擾源
    interferenceData.forEach(source => {
      const sourceObj = createInterferenceSource(source)
      sceneRef.current!.add(sourceObj)
      interferenceObjectsRef.current.set(source.id, sourceObj)
    })
  }, [interferenceData, createInterferenceSource, isInitialized])

  // 更新場景中的受害設備
  useEffect(() => {
    if (!sceneRef.current || !isInitialized) return

    // 清除現有的受害設備
    victimObjectsRef.current.forEach((obj, id) => {
      sceneRef.current!.remove(obj)
    })
    victimObjectsRef.current.clear()

    // 添加新的受害設備
    victimDevices.forEach(device => {
      const deviceObj = createVictimDevice(device)
      sceneRef.current!.add(deviceObj)
      victimObjectsRef.current.set(device.id, deviceObj)
    })
  }, [victimDevices, createVictimDevice, isInitialized])

  // 初始化組件
  useEffect(() => {
    initializeThreeJS()

    return () => {
      // 清理資源
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current)
      }
      if (rendererRef.current && containerRef.current) {
        containerRef.current.removeChild(rendererRef.current.domElement)
        rendererRef.current.dispose()
      }
      window.removeEventListener('resize', onWindowResize)
    }
  }, [initializeThreeJS, onWindowResize])

  // 模擬數據（實際應用中從 API 獲取）
  useEffect(() => {
    if (!realTimeEnabled) {
      // 設置模擬數據
      const mockInterferenceSources: InterferenceSource[] = [
        {
          id: 'jammer_001',
          name: 'Jammer-1',
          position: { x: 50, y: 10, z: 30 },
          frequency_mhz: 2150,
          power_dbm: -60,
          bandwidth_mhz: 20,
          interference_type: 'jammer',
          coverage_radius_m: 100,
          azimuth_deg: 45,
          beam_width_deg: 60,
          active: true,
          severity: 'high',
          detection_time: new Date().toISOString()
        },
        {
          id: 'unint_002',
          name: 'Unintentional-2',
          position: { x: -80, y: 15, z: -50 },
          frequency_mhz: 2140,
          power_dbm: -70,
          bandwidth_mhz: 10,
          interference_type: 'unintentional',
          coverage_radius_m: 60,
          active: true,
          severity: 'medium',
          detection_time: new Date().toISOString()
        }
      ]

      const mockVictimDevices: VictimDevice[] = [
        {
          id: 'ue_001',
          name: 'UE-1',
          position: { x: 20, y: 5, z: 10 },
          frequency_mhz: 2150,
          sinr_db: -5,
          affected_by: ['jammer_001'],
          protection_level: 'normal'
        },
        {
          id: 'ue_002',
          name: 'UE-2',
          position: { x: -30, y: 8, z: -20 },
          frequency_mhz: 2140,
          sinr_db: 8,
          affected_by: ['unint_002'],
          protection_level: 'enhanced'
        }
      ]

      setInterferenceData(mockInterferenceSources)
      setVictimDevices(mockVictimDevices)
    }
  }, [realTimeEnabled])

  return (
    <div className="interference-visualization-container" style={{ width: '100%', height: '100%' }}>
      {/* 控制面板 */}
      <div className="visualization-controls" style={{
        position: 'absolute',
        top: '10px',
        left: '10px',
        background: 'rgba(0, 0, 0, 0.8)',
        color: 'white',
        padding: '10px',
        borderRadius: '4px',
        zIndex: 100,
        minWidth: '250px'
      }}>
        <h4 style={{ margin: '0 0 10px 0' }}>干擾可視化控制</h4>
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <input
              type="checkbox"
              checked={realTimeEnabled}
              onChange={(e) => setRealTimeEnabled(e.target.checked)}
            />
            實時模式 {isConnected ? '🟢' : '🔴'}
          </label>
          
          <label style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <input
              type="checkbox"
              checked={showInterferenceRanges}
              onChange={(e) => setShowInterferenceRanges(e.target.checked)}
            />
            顯示影響範圍
          </label>
          
          <label style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <input
              type="checkbox"
              checked={showLabels}
              onChange={(e) => setShowLabels(e.target.checked)}
            />
            顯示標籤
          </label>
          
          <label style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <input
              type="checkbox"
              checked={animateEffects}
              onChange={(e) => setAnimateEffects(e.target.checked)}
            />
            動畫效果
          </label>
          
          <label style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            透明度:
            <input
              type="range"
              min="0.1"
              max="1"
              step="0.1"
              value={opacity}
              onChange={(e) => setOpacity(Number(e.target.value))}
              style={{ width: '100px' }}
            />
            {opacity.toFixed(1)}
          </label>
          
          <div>
            可視化模式:
            <select
              value={visualizationMode}
              onChange={(e) => setVisualizationMode(e.target.value as any)}
              style={{ marginLeft: '5px', padding: '2px' }}
            >
              <option value="impact">影響分析</option>
              <option value="frequency">頻率分佈</option>
              <option value="power">功率強度</option>
            </select>
          </div>
        </div>
        
        {lastUpdate && (
          <div style={{ fontSize: '12px', marginTop: '10px', color: '#aaa' }}>
            最後更新: {new Date(lastUpdate).toLocaleTimeString()}
          </div>
        )}
      </div>
      
      {/* 圖例 */}
      <div className="visualization-legend" style={{
        position: 'absolute',
        top: '10px',
        right: '10px',
        background: 'rgba(0, 0, 0, 0.8)',
        color: 'white',
        padding: '10px',
        borderRadius: '4px',
        zIndex: 100,
        fontSize: '12px'
      }}>
        <h4 style={{ margin: '0 0 10px 0' }}>圖例</h4>
        <div>🔴 Jammer 干擾源</div>
        <div>🟠 意外干擾源</div>
        <div>🟡 鄰近通道干擾</div>
        <div>🟢 正常設備 (SINR > 10dB)</div>
        <div>🟡 輕微干擾 (0~10dB)</div>
        <div>🟠 中等干擾 (-10~0dB)</div>
        <div>🔴 嚴重干擾 (< -10dB)</div>
        <div>🟣 關鍵保護設備</div>
      </div>
      
      {/* 狀態信息 */}
      {(hoveredObject || selectedObject) && (
        <div className="object-info" style={{
          position: 'absolute',
          bottom: '10px',
          left: '10px',
          background: 'rgba(0, 0, 0, 0.9)',
          color: 'white',
          padding: '10px',
          borderRadius: '4px',
          zIndex: 100,
          maxWidth: '300px'
        }}>
          {selectedObject && (() => {
            const obj = interferenceObjectsRef.current.get(selectedObject) || 
                        victimObjectsRef.current.get(selectedObject)
            if (obj) {
              const data = obj.userData.data
              return (
                <div>
                  <h4>{data.name}</h4>
                  {data.frequency_mhz && <div>頻率: {data.frequency_mhz} MHz</div>}
                  {data.power_dbm && <div>功率: {data.power_dbm} dBm</div>}
                  {data.sinr_db !== undefined && <div>SINR: {data.sinr_db.toFixed(1)} dB</div>}
                  {data.interference_type && <div>類型: {data.interference_type}</div>}
                  {data.severity && <div>嚴重程度: {data.severity}</div>}
                </div>
              )
            }
          })()}
        </div>
      )}
      
      {/* Three.js 容器 */}
      <div
        ref={containerRef}
        style={{
          width: '100%',
          height: '100%',
          background: '#1a1a1a'
        }}
      />
    </div>
  )
}

export default InterferenceVisualization