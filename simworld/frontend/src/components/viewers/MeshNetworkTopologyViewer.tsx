/**
 * Mesh 網路拓撲視覺化組件
 * 實現動態網路拓撲可視化和性能監控
 */

import React, { useEffect, useRef, useState, useCallback } from 'react';
import * as THREE from 'three';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Line, Text, Html } from '@react-three/drei';

interface NetworkNode {
  node_id: string;
  node_type: string;
  position: { x: number; y: number; z: number };
  capacity: number;
  current_load: number;
  energy_level: number;
  reliability: number;
  is_active: boolean;
  connections: string[];
}

interface NetworkLink {
  link_id: string;
  source_node: string;
  target_node: string;
  capacity: number;
  current_utilization: number;
  latency: number;
  reliability: number;
  is_active: boolean;
}

interface TopologyMetrics {
  connectivity_index: number;
  clustering_coefficient: number;
  average_path_length: number;
  network_diameter: number;
  fault_tolerance: number;
  energy_efficiency: number;
  load_distribution_variance: number;
}

interface RoutingPath {
  path_id: string;
  source_node: string;
  destination_node: string;
  hops: string[];
  total_latency: number;
  algorithm_used: string;
}

interface MeshNetworkData {
  topology_id: string;
  nodes: NetworkNode[];
  links: NetworkLink[];
  metrics: TopologyMetrics;
  routing_paths: RoutingPath[];
  optimization_status: {
    last_optimization: string;
    optimization_enabled: boolean;
    improvement_score: number;
  };
}

interface MeshNetworkTopologyViewerProps {
  data?: MeshNetworkData;
  viewMode?: 'topology' | 'performance' | 'routing';
  showMetrics?: boolean;
  showPaths?: boolean;
  autoLayout?: boolean;
  onNodeSelect?: (nodeId: string) => void;
  onLinkSelect?: (linkId: string) => void;
}

// 網路節點3D組件
const NetworkNodeModel: React.FC<{
  node: NetworkNode;
  position: [number, number, number];
  isSelected?: boolean;
  onClick?: () => void;
}> = ({ node, position, isSelected, onClick }) => {
  const meshRef = useRef<THREE.Mesh>(null);
  
  // 根據節點類型確定形狀和顏色
  const getNodeAppearance = () => {
    switch (node.node_type) {
      case 'uav':
        return {
          geometry: <octahedronGeometry args={[3]} />,
          color: '#3498db',
          scale: 1.0
        };
      case 'satellite':
        return {
          geometry: <icosahedronGeometry args={[4]} />,
          color: '#e74c3c',
          scale: 1.2
        };
      case 'ground_station':
        return {
          geometry: <boxGeometry args={[4, 4, 4]} />,
          color: '#2ecc71',
          scale: 1.0
        };
      case 'mesh_relay':
        return {
          geometry: <coneGeometry args={[2, 4]} />,
          color: '#9b59b6',
          scale: 0.8
        };
      default:
        return {
          geometry: <sphereGeometry args={[2]} />,
          color: '#95a5a6',
          scale: 1.0
        };
    }
  };

  const appearance = getNodeAppearance();
  
  // 根據負載調整顏色強度
  const getLoadColor = () => {
    const loadRatio = node.current_load / node.capacity;
    if (loadRatio > 0.8) return '#e74c3c';  // 紅色 - 高負載
    if (loadRatio > 0.6) return '#f39c12';  // 橙色 - 中負載
    return appearance.color;  // 正常顏色
  };

  // 根據能量水平調整透明度
  const getOpacity = () => {
    if (!node.is_active) return 0.3;
    return Math.max(0.5, node.energy_level / 100);
  };

  useFrame((state) => {
    if (meshRef.current && node.is_active) {
      // 根據負載添加脈衝效果
      const loadRatio = node.current_load / node.capacity;
      if (loadRatio > 0.7) {
        const pulse = Math.sin(state.clock.elapsedTime * 3) * 0.1 + 1;
        meshRef.current.scale.setScalar(appearance.scale * pulse);
      }
    }
  });

  return (
    <group position={position} onClick={onClick}>
      {/* 主節點 */}
      <mesh ref={meshRef}>
        {appearance.geometry}
        <meshLambertMaterial 
          color={getLoadColor()}
          transparent
          opacity={getOpacity()}
          emissive={isSelected ? '#ffffff' : '#000000'}
          emissiveIntensity={isSelected ? 0.3 : 0}
        />
      </mesh>

      {/* 能量指示器 */}
      <mesh position={[0, 6, 0]}>
        <boxGeometry args={[1, node.energy_level / 50, 0.2]} />
        <meshLambertMaterial 
          color={node.energy_level > 30 ? '#2ecc71' : '#e74c3c'} 
        />
      </mesh>

      {/* 負載指示器 */}
      <mesh position={[2, 0, 0]}>
        <cylinderGeometry args={[0.5, 0.5, node.current_load / node.capacity * 8]} />
        <meshLambertMaterial color="#f39c12" />
      </mesh>

      {/* 節點標籤 */}
      <Html position={[0, 8, 0]}>
        <div style={{
          background: 'rgba(0,0,0,0.8)',
          color: 'white',
          padding: '4px 8px',
          borderRadius: '4px',
          fontSize: '10px',
          textAlign: 'center',
          whiteSpace: 'nowrap'
        }}>
          <div>{node.node_id}</div>
          <div>{node.node_type}</div>
          <div>Load: {((node.current_load / node.capacity) * 100).toFixed(0)}%</div>
          <div>Energy: {node.energy_level.toFixed(0)}%</div>
        </div>
      </Html>

      {/* 可靠性環 */}
      <mesh rotation={[Math.PI / 2, 0, 0]}>
        <ringGeometry args={[5, 6, 32]} />
        <meshLambertMaterial 
          color="#3498db" 
          transparent 
          opacity={node.reliability * 0.8} 
        />
      </mesh>
    </group>
  );
};

// 網路連結組件
const NetworkLinkModel: React.FC<{
  link: NetworkLink;
  sourcePos: [number, number, number];
  targetPos: [number, number, number];
  isSelected?: boolean;
  onClick?: () => void;
}> = ({ link, sourcePos, targetPos, isSelected, onClick }) => {
  
  // 根據利用率確定連結顏色
  const getLinkColor = () => {
    const utilization = link.current_utilization;
    if (utilization > 0.8) return '#e74c3c';  // 紅色 - 高利用率
    if (utilization > 0.6) return '#f39c12';  // 橙色 - 中利用率
    if (utilization > 0.3) return '#f1c40f';  // 黃色 - 低利用率
    return '#2ecc71';  // 綠色 - 空閒
  };

  // 根據可靠性確定線寬
  const getLineWidth = () => {
    return Math.max(1, link.reliability * 4);
  };

  // 根據延遲確定透明度
  const getOpacity = () => {
    if (!link.is_active) return 0.2;
    return Math.max(0.4, 1 - (link.latency / 200)); // 假設最大延遲200ms
  };

  const points = [
    new THREE.Vector3(...sourcePos),
    new THREE.Vector3(...targetPos)
  ];

  // 如果連結有高利用率，添加動畫效果
  const isHighUtilization = link.current_utilization > 0.7;

  return (
    <group onClick={onClick}>
      <Line
        points={points}
        color={getLinkColor()}
        lineWidth={getLineWidth()}
        transparent
        opacity={getOpacity()}
        dashed={isHighUtilization}
        dashScale={isHighUtilization ? 20 : 1}
        dashSize={isHighUtilization ? 2 : 1}
        gapSize={isHighUtilization ? 1 : 0}
      />
      
      {/* 選中時的高亮 */}
      {isSelected && (
        <Line
          points={points}
          color="#ffffff"
          lineWidth={getLineWidth() + 2}
          transparent
          opacity={0.6}
        />
      )}

      {/* 數據流指示器 */}
      {link.current_utilization > 0.1 && (
        <group>
          <mesh position={[
            (sourcePos[0] + targetPos[0]) / 2,
            (sourcePos[1] + targetPos[1]) / 2 + 2,
            (sourcePos[2] + targetPos[2]) / 2
          ]}>
            <sphereGeometry args={[0.5]} />
            <meshLambertMaterial color="#f39c12" />
          </mesh>
        </group>
      )}
    </group>
  );
};

// 路由路徑視覺化
const RoutingPathViewer: React.FC<{
  path: RoutingPath;
  nodePositions: Map<string, [number, number, number]>;
  isSelected?: boolean;
}> = ({ path, nodePositions, isSelected }) => {
  const pathPoints: THREE.Vector3[] = [];
  
  path.hops.forEach(nodeId => {
    const pos = nodePositions.get(nodeId);
    if (pos) {
      pathPoints.push(new THREE.Vector3(pos[0], pos[1] + 1, pos[2]));
    }
  });

  if (pathPoints.length < 2) return null;

  return (
    <group>
      <Line
        points={pathPoints}
        color={isSelected ? "#e74c3c" : "#9b59b6"}
        lineWidth={isSelected ? 4 : 2}
        transparent
        opacity={0.8}
      />
      
      {/* 路徑標籤 */}
      {isSelected && (
        <Html position={[pathPoints[0].x, pathPoints[0].y + 5, pathPoints[0].z]}>
          <div style={{
            background: 'rgba(0,0,0,0.9)',
            color: 'white',
            padding: '6px 10px',
            borderRadius: '6px',
            fontSize: '11px'
          }}>
            <div>Path: {path.source_node} → {path.destination_node}</div>
            <div>Hops: {path.hops.length}</div>
            <div>Latency: {path.total_latency.toFixed(1)}ms</div>
            <div>Algorithm: {path.algorithm_used}</div>
          </div>
        </Html>
      )}
    </group>
  );
};

// 網路指標儀表板
const NetworkMetricsDashboard: React.FC<{
  metrics: TopologyMetrics;
  optimizationStatus: any;
}> = ({ metrics, optimizationStatus }) => {
  
  const getMetricColor = (value: number, isInverse = false) => {
    const threshold = isInverse ? 0.3 : 0.7;
    if (isInverse) {
      return value < threshold ? '#2ecc71' : value < 0.6 ? '#f39c12' : '#e74c3c';
    } else {
      return value > threshold ? '#2ecc71' : value > 0.4 ? '#f39c12' : '#e74c3c';
    }
  };

  return (
    <div style={{
      position: 'absolute',
      top: '10px',
      right: '10px',
      background: 'rgba(0,0,0,0.85)',
      color: 'white',
      padding: '15px',
      borderRadius: '10px',
      fontSize: '12px',
      minWidth: '250px',
      zIndex: 1000
    }}>
      <h3 style={{ margin: '0 0 10px 0', fontSize: '14px' }}>Network Metrics</h3>
      
      <div style={{ display: 'grid', gap: '8px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span>Connectivity:</span>
          <span style={{ color: getMetricColor(metrics.connectivity_index) }}>
            {(metrics.connectivity_index * 100).toFixed(1)}%
          </span>
        </div>
        
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span>Clustering:</span>
          <span style={{ color: getMetricColor(metrics.clustering_coefficient) }}>
            {metrics.clustering_coefficient.toFixed(3)}
          </span>
        </div>
        
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span>Avg Path Length:</span>
          <span style={{ color: getMetricColor(metrics.average_path_length, true) }}>
            {metrics.average_path_length.toFixed(2)}
          </span>
        </div>
        
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span>Fault Tolerance:</span>
          <span style={{ color: getMetricColor(metrics.fault_tolerance) }}>
            {(metrics.fault_tolerance * 100).toFixed(1)}%
          </span>
        </div>
        
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span>Energy Efficiency:</span>
          <span style={{ color: getMetricColor(metrics.energy_efficiency) }}>
            {(metrics.energy_efficiency * 100).toFixed(1)}%
          </span>
        </div>
        
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span>Load Variance:</span>
          <span style={{ color: getMetricColor(metrics.load_distribution_variance, true) }}>
            {metrics.load_distribution_variance.toFixed(3)}
          </span>
        </div>
      </div>

      <hr style={{ margin: '10px 0', border: '1px solid rgba(255,255,255,0.3)' }} />
      
      <div>
        <h4 style={{ margin: '0 0 5px 0', fontSize: '12px' }}>Optimization</h4>
        <div style={{ fontSize: '11px' }}>
          <div>Status: {optimizationStatus.optimization_enabled ? '🟢 Active' : '🔴 Disabled'}</div>
          <div>Last: {new Date(optimizationStatus.last_optimization).toLocaleTimeString()}</div>
          <div>Score: {optimizationStatus.improvement_score.toFixed(3)}</div>
        </div>
      </div>
    </div>
  );
};

// 主場景組件
const MeshNetworkScene: React.FC<{
  data: MeshNetworkData;
  viewMode: string;
  showPaths: boolean;
  selectedNode?: string;
  selectedLink?: string;
  selectedPath?: string;
  onNodeSelect?: (nodeId: string) => void;
  onLinkSelect?: (linkId: string) => void;
}> = ({ 
  data, 
  viewMode, 
  showPaths, 
  selectedNode, 
  selectedLink, 
  selectedPath, 
  onNodeSelect, 
  onLinkSelect 
}) => {

  // 建立節點位置映射
  const nodePositions = new Map<string, [number, number, number]>();
  data.nodes.forEach(node => {
    nodePositions.set(node.node_id, [
      node.position.x,
      node.position.y,
      node.position.z
    ]);
  });

  return (
    <>
      {/* 環境光照 */}
      <ambientLight intensity={0.4} />
      <directionalLight position={[50, 50, 25]} intensity={0.8} />

      {/* 渲染網路節點 */}
      {data.nodes.map(node => {
        const position = nodePositions.get(node.node_id);
        if (!position) return null;

        return (
          <NetworkNodeModel
            key={node.node_id}
            node={node}
            position={position}
            isSelected={selectedNode === node.node_id}
            onClick={() => onNodeSelect?.(node.node_id)}
          />
        );
      })}

      {/* 渲染網路連結 */}
      {data.links.map(link => {
        const sourcePos = nodePositions.get(link.source_node);
        const targetPos = nodePositions.get(link.target_node);
        
        if (!sourcePos || !targetPos) return null;

        return (
          <NetworkLinkModel
            key={link.link_id}
            link={link}
            sourcePos={sourcePos}
            targetPos={targetPos}
            isSelected={selectedLink === link.link_id}
            onClick={() => onLinkSelect?.(link.link_id)}
          />
        );
      })}

      {/* 渲染路由路徑 */}
      {showPaths && data.routing_paths.map(path => (
        <RoutingPathViewer
          key={path.path_id}
          path={path}
          nodePositions={nodePositions}
          isSelected={selectedPath === path.path_id}
        />
      ))}

      {/* 地面參考平面 */}
      <mesh position={[0, -20, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <planeGeometry args={[200, 200]} />
        <meshLambertMaterial color="#ecf0f1" transparent opacity={0.1} />
      </mesh>
    </>
  );
};

// 主組件
const MeshNetworkTopologyViewer: React.FC<MeshNetworkTopologyViewerProps> = ({
  data,
  viewMode = 'topology',
  showMetrics = true,
  showPaths = false,
  autoLayout = true,
  onNodeSelect,
  onLinkSelect
}) => {
  const [selectedNode, setSelectedNode] = useState<string>();
  const [selectedLink, setSelectedLink] = useState<string>();
  const [selectedPath, setSelectedPath] = useState<string>();
  const [currentViewMode, setCurrentViewMode] = useState(viewMode);

  const handleNodeSelect = useCallback((nodeId: string) => {
    setSelectedNode(nodeId);
    onNodeSelect?.(nodeId);
  }, [onNodeSelect]);

  const handleLinkSelect = useCallback((linkId: string) => {
    setSelectedLink(linkId);
    onLinkSelect?.(linkId);
  }, [onLinkSelect]);

  // 模擬數據
  const mockData: MeshNetworkData = {
    topology_id: 'topology_001',
    nodes: [
      {
        node_id: 'uav_001',
        node_type: 'uav',
        position: { x: 0, y: 10, z: 0 },
        capacity: 100,
        current_load: 45,
        energy_level: 85,
        reliability: 0.95,
        is_active: true,
        connections: ['uav_002', 'satellite_001']
      },
      {
        node_id: 'uav_002',
        node_type: 'uav',
        position: { x: 30, y: 15, z: 20 },
        capacity: 100,
        current_load: 65,
        energy_level: 72,
        reliability: 0.88,
        is_active: true,
        connections: ['uav_001', 'uav_003']
      },
      {
        node_id: 'uav_003',
        node_type: 'uav',
        position: { x: -20, y: 12, z: 30 },
        capacity: 100,
        current_load: 30,
        energy_level: 90,
        reliability: 0.92,
        is_active: true,
        connections: ['uav_002', 'ground_001']
      },
      {
        node_id: 'satellite_001',
        node_type: 'satellite',
        position: { x: 0, y: 80, z: 0 },
        capacity: 500,
        current_load: 120,
        energy_level: 100,
        reliability: 0.98,
        is_active: true,
        connections: ['uav_001', 'ground_001']
      },
      {
        node_id: 'ground_001',
        node_type: 'ground_station',
        position: { x: -40, y: 0, z: -10 },
        capacity: 1000,
        current_load: 200,
        energy_level: 100,
        reliability: 0.99,
        is_active: true,
        connections: ['satellite_001', 'uav_003']
      }
    ],
    links: [
      {
        link_id: 'link_001',
        source_node: 'uav_001',
        target_node: 'uav_002',
        capacity: 100,
        current_utilization: 0.45,
        latency: 25,
        reliability: 0.92,
        is_active: true
      },
      {
        link_id: 'link_002',
        source_node: 'uav_001',
        target_node: 'satellite_001',
        capacity: 200,
        current_utilization: 0.6,
        latency: 180,
        reliability: 0.85,
        is_active: true
      },
      {
        link_id: 'link_003',
        source_node: 'uav_002',
        target_node: 'uav_003',
        capacity: 100,
        current_utilization: 0.8,
        latency: 30,
        reliability: 0.89,
        is_active: true
      }
    ],
    metrics: {
      connectivity_index: 0.78,
      clustering_coefficient: 0.65,
      average_path_length: 2.1,
      network_diameter: 3,
      fault_tolerance: 0.82,
      energy_efficiency: 0.86,
      load_distribution_variance: 0.15
    },
    routing_paths: [
      {
        path_id: 'path_001',
        source_node: 'ground_001',
        destination_node: 'uav_002',
        hops: ['ground_001', 'uav_003', 'uav_002'],
        total_latency: 55,
        algorithm_used: 'shortest_path'
      }
    ],
    optimization_status: {
      last_optimization: new Date().toISOString(),
      optimization_enabled: true,
      improvement_score: 0.15
    }
  };

  const displayData = data || mockData;

  return (
    <div style={{ width: '100%', height: '600px', position: 'relative' }}>
      {/* 控制面板 */}
      <div style={{
        position: 'absolute',
        top: '10px',
        left: '10px',
        zIndex: 1000,
        background: 'rgba(0,0,0,0.8)',
        color: 'white',
        padding: '10px',
        borderRadius: '8px'
      }}>
        <div style={{ marginBottom: '10px' }}>
          <label>View Mode: </label>
          <select 
            value={currentViewMode} 
            onChange={(e) => setCurrentViewMode(e.target.value)}
            style={{ marginLeft: '5px' }}
          >
            <option value="topology">Network Topology</option>
            <option value="performance">Performance View</option>
            <option value="routing">Routing Paths</option>
          </select>
        </div>
        
        <div style={{ fontSize: '11px' }}>
          <div>Nodes: {displayData.nodes.length}</div>
          <div>Links: {displayData.links.length}</div>
          <div>Active: {displayData.nodes.filter(n => n.is_active).length}</div>
          <div>Paths: {displayData.routing_paths.length}</div>
        </div>
      </div>

      {/* 網路指標儀表板 */}
      {showMetrics && (
        <NetworkMetricsDashboard 
          metrics={displayData.metrics}
          optimizationStatus={displayData.optimization_status}
        />
      )}

      {/* 3D 場景 */}
      <Canvas camera={{ position: [100, 60, 100], fov: 60 }}>
        <OrbitControls enablePan enableZoom enableRotate />
        <MeshNetworkScene
          data={displayData}
          viewMode={currentViewMode}
          showPaths={showPaths || currentViewMode === 'routing'}
          selectedNode={selectedNode}
          selectedLink={selectedLink}
          selectedPath={selectedPath}
          onNodeSelect={handleNodeSelect}
          onLinkSelect={handleLinkSelect}
        />
      </Canvas>
    </div>
  );
};

export default MeshNetworkTopologyViewer;