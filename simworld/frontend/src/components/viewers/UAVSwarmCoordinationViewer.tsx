/**
 * UAV 群組協同視覺化組件
 * 實現多 UAV 群組的 3D 視覺化和軌跡協同顯示
 */

import React, { useEffect, useRef, useState, useCallback } from 'react';
import * as THREE from 'three';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { OrbitControls, Line, Text, Html } from '@react-three/drei';

interface UAVPosition {
  latitude: number;
  longitude: number;
  altitude: number;
}

interface UAVMember {
  uav_id: string;
  role: string;
  position: UAVPosition;
  target_position: UAVPosition;
  battery_level: number;
  is_active: boolean;
  formation_compliance: number;
}

interface SwarmGroup {
  group_id: string;
  name: string;
  leader_id: string;
  uavs: UAVMember[];
  formation_type: string;
  coordination_quality: number;
}

interface FormationData {
  formation_id: string;
  name: string;
  shape: string;
  state: string;
  quality_score: number;
  members: UAVMember[];
}

interface SwarmCoordinationData {
  swarm_groups: SwarmGroup[];
  formations: FormationData[];
  network_topology: {
    nodes: Array<{
      node_id: string;
      node_type: string;
      position: UAVPosition;
      connections: string[];
    }>;
    links: Array<{
      source: string;
      target: string;
      quality: number;
    }>;
  };
}

interface UAVSwarmCoordinationViewerProps {
  data?: SwarmCoordinationData;
  viewMode?: 'swarm' | 'formation' | 'network';
  showTrajectories?: boolean;
  showConnections?: boolean;
  onUAVSelect?: (uavId: string) => void;
  onGroupSelect?: (groupId: string) => void;
}

// UAV 3D 模型組件
const UAVModel: React.FC<{
  position: [number, number, number];
  role: string;
  batteryLevel: number;
  isActive: boolean;
  isSelected?: boolean;
  onClick?: () => void;
}> = ({ position, role, batteryLevel, isActive, isSelected, onClick }) => {
  const meshRef = useRef<THREE.Mesh>(null);
  
  // 根據角色確定顏色
  const getUAVColor = (role: string) => {
    switch (role) {
      case 'leader': return '#ff6b35';
      case 'wing_left': return '#4ecdc4';
      case 'wing_right': return '#45b7d1';
      case 'scout': return '#96ceb4';
      case 'relay': return '#feca57';
      default: return '#95a5a6';
    }
  };

  // 根據電池電量確定材質
  const getMaterial = () => {
    const color = getUAVColor(role);
    const opacity = isActive ? 1.0 : 0.5;
    const emissive = isSelected ? '#ffffff' : '#000000';
    
    return new THREE.MeshLambertMaterial({
      color: color,
      opacity: opacity,
      transparent: true,
      emissive: emissive,
      emissiveIntensity: isSelected ? 0.3 : 0
    });
  };

  useFrame((state) => {
    if (meshRef.current && isActive) {
      // 輕微的懸浮動畫
      meshRef.current.rotation.z = Math.sin(state.clock.elapsedTime * 2) * 0.1;
    }
  });

  return (
    <group position={position} onClick={onClick}>
      {/* UAV 主體 */}
      <mesh ref={meshRef} material={getMaterial()}>
        <boxGeometry args={[2, 0.5, 2]} />
      </mesh>
      
      {/* 螺旋槳 */}
      <mesh position={[0.8, 0.3, 0.8]}>
        <cylinderGeometry args={[0.4, 0.4, 0.1]} />
        <meshLambertMaterial color="#34495e" />
      </mesh>
      <mesh position={[-0.8, 0.3, 0.8]}>
        <cylinderGeometry args={[0.4, 0.4, 0.1]} />
        <meshLambertMaterial color="#34495e" />
      </mesh>
      <mesh position={[0.8, 0.3, -0.8]}>
        <cylinderGeometry args={[0.4, 0.4, 0.1]} />
        <meshLambertMaterial color="#34495e" />
      </mesh>
      <mesh position={[-0.8, 0.3, -0.8]}>
        <cylinderGeometry args={[0.4, 0.4, 0.1]} />
        <meshLambertMaterial color="#34495e" />
      </mesh>

      {/* 電池指示器 */}
      <mesh position={[0, 1, 0]}>
        <boxGeometry args={[1, 0.2, 0.2]} />
        <meshLambertMaterial color={batteryLevel > 30 ? '#2ecc71' : '#e74c3c'} />
      </mesh>
      
      {/* 角色標籤 */}
      <Html position={[0, 2, 0]}>
        <div style={{
          background: 'rgba(0,0,0,0.7)',
          color: 'white',
          padding: '2px 6px',
          borderRadius: '4px',
          fontSize: '10px',
          whiteSpace: 'nowrap'
        }}>
          {role} - {batteryLevel.toFixed(0)}%
        </div>
      </Html>
    </group>
  );
};

// 編隊連線組件
const FormationConnections: React.FC<{
  members: UAVMember[];
  leaderId: string;
}> = ({ members, leaderId }) => {
  const leader = members.find(m => m.uav_id === leaderId);
  if (!leader) return null;

  const leaderPos = [
    (leader.position.longitude - 121.0) * 100000,
    leader.position.altitude,
    (leader.position.latitude - 25.0) * 100000
  ] as [number, number, number];

  return (
    <>
      {members
        .filter(m => m.uav_id !== leaderId && m.is_active)
        .map(member => {
          const memberPos = [
            (member.position.longitude - 121.0) * 100000,
            member.position.altitude,
            (member.position.latitude - 25.0) * 100000
          ] as [number, number, number];

          const points = [
            new THREE.Vector3(...leaderPos),
            new THREE.Vector3(...memberPos)
          ];

          return (
            <Line
              key={`connection-${member.uav_id}`}
              points={points}
              color="#3498db"
              lineWidth={2}
              transparent
              opacity={0.6}
            />
          );
        })}
    </>
  );
};

// 網路拓撲連線組件
const NetworkTopology: React.FC<{
  nodes: Array<{
    node_id: string;
    node_type: string;
    position: UAVPosition;
    connections: string[];
  }>;
  links: Array<{
    source: string;
    target: string;
    quality: number;
  }>;
}> = ({ nodes, links }) => {
  const nodePositions = new Map();
  
  // 建立節點位置映射
  nodes.forEach(node => {
    nodePositions.set(node.node_id, [
      (node.position.longitude - 121.0) * 100000,
      node.position.altitude,
      (node.position.latitude - 25.0) * 100000
    ]);
  });

  return (
    <>
      {links.map((link, index) => {
        const sourcePos = nodePositions.get(link.source);
        const targetPos = nodePositions.get(link.target);
        
        if (!sourcePos || !targetPos) return null;

        const points = [
          new THREE.Vector3(...sourcePos),
          new THREE.Vector3(...targetPos)
        ];

        // 根據連線品質設定顏色
        const getConnectionColor = (quality: number) => {
          if (quality > 0.8) return '#2ecc71';  // 綠色 - 良好
          if (quality > 0.6) return '#f39c12';  // 橙色 - 中等
          return '#e74c3c';  // 紅色 - 差
        };

        return (
          <Line
            key={`link-${index}`}
            points={points}
            color={getConnectionColor(link.quality)}
            lineWidth={link.quality * 3 + 1}
            transparent
            opacity={0.7}
          />
        );
      })}
    </>
  );
};

// 軌跡線組件
const TrajectoryPath: React.FC<{
  currentPosition: UAVPosition;
  targetPosition: UAVPosition;
  uavId: string;
}> = ({ currentPosition, targetPosition, uavId }) => {
  const currentPos = [
    (currentPosition.longitude - 121.0) * 100000,
    currentPosition.altitude,
    (currentPosition.latitude - 25.0) * 100000
  ] as [number, number, number];

  const targetPos = [
    (targetPosition.longitude - 121.0) * 100000,
    targetPosition.altitude,
    (targetPosition.latitude - 25.0) * 100000
  ] as [number, number, number];

  const points = [
    new THREE.Vector3(...currentPos),
    new THREE.Vector3(...targetPos)
  ];

  return (
    <Line
      points={points}
      color="#9b59b6"
      lineWidth={2}
      transparent
      opacity={0.8}
      dashed
      dashScale={50}
      dashSize={10}
      gapSize={5}
    />
  );
};

// 編隊形狀指示器
const FormationShape: React.FC<{
  shape: string;
  centerPosition: UAVPosition;
  size: number;
}> = ({ shape, centerPosition, size }) => {
  const center = [
    (centerPosition.longitude - 121.0) * 100000,
    centerPosition.altitude - 10,
    (centerPosition.latitude - 25.0) * 100000
  ] as [number, number, number];

  const getShapeGeometry = () => {
    switch (shape) {
      case 'circle':
        return <ringGeometry args={[size * 0.8, size, 32]} />;
      case 'line':
        return <planeGeometry args={[size * 2, 2]} />;
      case 'diamond':
        return <octahedronGeometry args={[size * 0.7, 0]} />;
      case 'vee':
        return <coneGeometry args={[size * 0.8, 2, 8]} />;
      default:
        return <ringGeometry args={[size * 0.8, size, 6]} />;
    }
  };

  return (
    <mesh position={center} rotation={[-Math.PI / 2, 0, 0]}>
      {getShapeGeometry()}
      <meshLambertMaterial 
        color="#3498db" 
        transparent 
        opacity={0.3} 
        wireframe 
      />
    </mesh>
  );
};

// 主要場景組件
const SwarmScene: React.FC<{
  data: SwarmCoordinationData;
  viewMode: string;
  showTrajectories: boolean;
  showConnections: boolean;
  selectedUAV?: string;
  onUAVSelect?: (uavId: string) => void;
}> = ({ data, viewMode, showTrajectories, showConnections, selectedUAV, onUAVSelect }) => {

  // 渲染群組模式
  const renderSwarmMode = () => {
    return data.swarm_groups.map(group => (
      <group key={group.group_id}>
        {/* 渲染群組中的UAV */}
        {group.uavs.map(uav => {
          const position = [
            (uav.position.longitude - 121.0) * 100000,
            uav.position.altitude,
            (uav.position.latitude - 25.0) * 100000
          ] as [number, number, number];

          return (
            <UAVModel
              key={uav.uav_id}
              position={position}
              role={uav.role}
              batteryLevel={uav.battery_level}
              isActive={uav.is_active}
              isSelected={selectedUAV === uav.uav_id}
              onClick={() => onUAVSelect?.(uav.uav_id)}
            />
          );
        })}

        {/* 顯示群組連線 */}
        {showConnections && (
          <FormationConnections 
            members={group.uavs} 
            leaderId={group.leader_id} 
          />
        )}

        {/* 顯示軌跡 */}
        {showTrajectories && group.uavs.map(uav => (
          <TrajectoryPath
            key={`trajectory-${uav.uav_id}`}
            currentPosition={uav.position}
            targetPosition={uav.target_position}
            uavId={uav.uav_id}
          />
        ))}
      </group>
    ));
  };

  // 渲染編隊模式
  const renderFormationMode = () => {
    return data.formations.map(formation => {
      const centerPos = formation.members.length > 0 
        ? formation.members[0].position 
        : { latitude: 25.0, longitude: 121.0, altitude: 100 };

      return (
        <group key={formation.formation_id}>
          {/* 編隊形狀指示器 */}
          <FormationShape
            shape={formation.shape}
            centerPosition={centerPos}
            size={50}
          />

          {/* 渲染編隊成員 */}
          {formation.members.map(member => {
            const position = [
              (member.position.longitude - 121.0) * 100000,
              member.position.altitude,
              (member.position.latitude - 25.0) * 100000
            ] as [number, number, number];

            return (
              <UAVModel
                key={member.uav_id}
                position={position}
                role={member.role}
                batteryLevel={member.battery_level}
                isActive={member.is_active}
                isSelected={selectedUAV === member.uav_id}
                onClick={() => onUAVSelect?.(member.uav_id)}
              />
            );
          })}

          {/* 編隊品質指示器 */}
          <Html position={[0, 150, 0]}>
            <div style={{
              background: 'rgba(0,0,0,0.8)',
              color: 'white',
              padding: '8px 12px',
              borderRadius: '8px',
              fontSize: '12px'
            }}>
              <div>{formation.name}</div>
              <div>Quality: {(formation.quality_score * 100).toFixed(1)}%</div>
              <div>State: {formation.state}</div>
            </div>
          </Html>
        </group>
      );
    });
  };

  // 渲染網路模式
  const renderNetworkMode = () => {
    return (
      <group>
        {/* 網路拓撲連線 */}
        <NetworkTopology 
          nodes={data.network_topology.nodes}
          links={data.network_topology.links}
        />

        {/* 網路節點 */}
        {data.network_topology.nodes.map(node => {
          const position = [
            (node.position.longitude - 121.0) * 100000,
            node.position.altitude,
            (node.position.latitude - 25.0) * 100000
          ] as [number, number, number];

          return (
            <mesh key={node.node_id} position={position}>
              {node.node_type === 'uav' ? (
                <sphereGeometry args={[3]} />
              ) : (
                <boxGeometry args={[6, 6, 6]} />
              )}
              <meshLambertMaterial 
                color={node.node_type === 'uav' ? '#3498db' : '#e74c3c'} 
              />
            </mesh>
          );
        })}
      </group>
    );
  };

  return (
    <>
      {/* 環境光照 */}
      <ambientLight intensity={0.4} />
      <directionalLight position={[100, 100, 50]} intensity={0.8} />
      
      {/* 根據視圖模式渲染不同內容 */}
      {viewMode === 'swarm' && renderSwarmMode()}
      {viewMode === 'formation' && renderFormationMode()}
      {viewMode === 'network' && renderNetworkMode()}

      {/* 地面參考平面 */}
      <mesh position={[0, -10, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <planeGeometry args={[1000, 1000]} />
        <meshLambertMaterial color="#ecf0f1" transparent opacity={0.3} />
      </mesh>
    </>
  );
};

// 主組件
const UAVSwarmCoordinationViewer: React.FC<UAVSwarmCoordinationViewerProps> = ({
  data,
  viewMode = 'swarm',
  showTrajectories = true,
  showConnections = true,
  onUAVSelect,
  onGroupSelect
}) => {
  const [selectedUAV, setSelectedUAV] = useState<string>();
  const [currentViewMode, setCurrentViewMode] = useState(viewMode);

  const handleUAVSelect = useCallback((uavId: string) => {
    setSelectedUAV(uavId);
    onUAVSelect?.(uavId);
  }, [onUAVSelect]);

  const mockData: SwarmCoordinationData = {
    swarm_groups: [
      {
        group_id: 'group_001',
        name: 'Alpha Squadron',
        leader_id: 'uav_001',
        coordination_quality: 0.92,
        formation_type: 'vee',
        uavs: [
          {
            uav_id: 'uav_001',
            role: 'leader',
            position: { latitude: 25.0, longitude: 121.0, altitude: 100 },
            target_position: { latitude: 25.001, longitude: 121.001, altitude: 100 },
            battery_level: 85,
            is_active: true,
            formation_compliance: 0.95
          },
          {
            uav_id: 'uav_002',
            role: 'wing_left',
            position: { latitude: 25.0, longitude: 120.999, altitude: 95 },
            target_position: { latitude: 25.001, longitude: 121.0, altitude: 95 },
            battery_level: 78,
            is_active: true,
            formation_compliance: 0.88
          },
          {
            uav_id: 'uav_003',
            role: 'wing_right',
            position: { latitude: 25.0, longitude: 121.001, altitude: 95 },
            target_position: { latitude: 25.001, longitude: 121.002, altitude: 95 },
            battery_level: 92,
            is_active: true,
            formation_compliance: 0.91
          }
        ]
      }
    ],
    formations: [
      {
        formation_id: 'formation_001',
        name: 'Search Pattern Alpha',
        shape: 'line',
        state: 'formed',
        quality_score: 0.89,
        members: [
          {
            uav_id: 'uav_004',
            role: 'scout',
            position: { latitude: 25.005, longitude: 121.005, altitude: 80 },
            target_position: { latitude: 25.006, longitude: 121.006, altitude: 80 },
            battery_level: 67,
            is_active: true,
            formation_compliance: 0.85
          }
        ]
      }
    ],
    network_topology: {
      nodes: [
        {
          node_id: 'uav_001',
          node_type: 'uav',
          position: { latitude: 25.0, longitude: 121.0, altitude: 100 },
          connections: ['uav_002', 'uav_003']
        },
        {
          node_id: 'uav_002',
          node_type: 'uav', 
          position: { latitude: 25.0, longitude: 120.999, altitude: 95 },
          connections: ['uav_001']
        }
      ],
      links: [
        { source: 'uav_001', target: 'uav_002', quality: 0.85 },
        { source: 'uav_001', target: 'uav_003', quality: 0.92 }
      ]
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
            <option value="swarm">Swarm Groups</option>
            <option value="formation">Formations</option>
            <option value="network">Network Topology</option>
          </select>
        </div>
        
        <div>
          Active UAVs: {displayData.swarm_groups.reduce((total, group) => 
            total + group.uavs.filter(uav => uav.is_active).length, 0)}
        </div>
        <div>
          Groups: {displayData.swarm_groups.length}
        </div>
        <div>
          Formations: {displayData.formations.length}
        </div>
      </div>

      {/* 3D 場景 */}
      <Canvas camera={{ position: [200, 200, 200], fov: 60 }}>
        <OrbitControls enablePan enableZoom enableRotate />
        <SwarmScene
          data={displayData}
          viewMode={currentViewMode}
          showTrajectories={showTrajectories}
          showConnections={showConnections}
          selectedUAV={selectedUAV}
          onUAVSelect={handleUAVSelect}
        />
      </Canvas>
    </div>
  );
};

export default UAVSwarmCoordinationViewer;