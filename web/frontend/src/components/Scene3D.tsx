// Professional 3D scene visualization using React Three Fiber

import React, { useRef, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import {
  OrbitControls,
  Grid,
  Text,
  Box,
  Sphere,
  Cylinder,
  Environment,
  PerspectiveCamera
} from '@react-three/drei';
import * as THREE from 'three';
import { SpatialObject, SpatialRelationship } from '../types/spatial';

interface Scene3DProps {
  objects: Record<string, SpatialObject>;
  relationships: SpatialRelationship[];
  selectedObject?: string;
  onObjectClick?: (objectId: string) => void;
  showRelationships?: boolean;
  showGrid?: boolean;
}

// Color mapping for different object types
const TYPE_COLORS: Record<string, string> = {
  furniture: '#8B4513',
  appliance: '#C0C0C0',
  container: '#228B22',
  book: '#4169E1',
  cup: '#FFFFFF',
  phone: '#000000',
  default: '#808080'
};

// Get color for object based on type or meta
const getObjectColor = (obj: SpatialObject): string => {
  if (obj.meta?.color) {
    return obj.meta.color;
  }
  return TYPE_COLORS[obj.type] || TYPE_COLORS.default;
};

// Individual 3D object component
const Object3D: React.FC<{
  object: SpatialObject;
  isSelected: boolean;
  onClick: () => void;
}> = ({ object, isSelected, onClick }) => {
  const meshRef = useRef<THREE.Mesh>(null);
  const color = getObjectColor(object);

  // Convert position and size
  const position: [number, number, number] = [
    object.position[0],
    object.position[2], // Y and Z swapped for Three.js coordinate system
    -object.position[1]
  ];

  const size: [number, number, number] = [
    object.bbox.xyz[0],
    object.bbox.xyz[2],
    object.bbox.xyz[1]
  ];

  // Animate selection
  useFrame((state) => {
    if (meshRef.current && isSelected) {
      meshRef.current.rotation.y = Math.sin(state.clock.elapsedTime * 2) * 0.1;
    }
  });

  // Choose geometry based on object type
  const renderGeometry = () => {
    switch (object.type) {
      case 'cup':
      case 'container':
        return (
          <Cylinder args={[size[0]/2, size[0]/2, size[1], 16]}>
            <meshStandardMaterial
              color={color}
              transparent
              opacity={object.type === 'cup' ? 0.8 : 1.0}
            />
          </Cylinder>
        );
      case 'phone':
      case 'book':
        return (
          <Box args={size}>
            <meshStandardMaterial color={color} />
          </Box>
        );
      default:
        return (
          <Box args={size}>
            <meshStandardMaterial
              color={color}
              wireframe={isSelected}
            />
          </Box>
        );
    }
  };

  return (
    <group position={position}>
      <mesh
        ref={meshRef}
        onClick={(e) => {
          e.stopPropagation();
          onClick();
        }}
        onPointerOver={(e) => {
          e.stopPropagation();
          document.body.style.cursor = 'pointer';
        }}
        onPointerOut={() => {
          document.body.style.cursor = 'default';
        }}
      >
        {renderGeometry()}
      </mesh>

      {/* Object label */}
      <Text
        position={[0, size[1]/2 + 0.3, 0]}
        fontSize={0.2}
        color={isSelected ? '#ff4444' : '#333333'}
        anchorX="center"
        anchorY="middle"
      >
        {object.id}
      </Text>

      {/* Selection highlight */}
      {isSelected && (
        <mesh position={[0, 0, 0]}>
          <boxGeometry args={[size[0] + 0.1, size[1] + 0.1, size[2] + 0.1]} />
          <meshBasicMaterial color="#ff4444" wireframe />
        </mesh>
      )}
    </group>
  );
};

// Relationship visualization component
const RelationshipLines: React.FC<{
  objects: Record<string, SpatialObject>;
  relationships: SpatialRelationship[];
}> = ({ objects, relationships }) => {
  const lines = useMemo(() => {
    return relationships
      .filter(rel => rel.type !== 'in') // Skip room containment
      .map(rel => {
        const fromObj = objects[rel.from];
        const toObj = objects[rel.to];

        if (!fromObj || !toObj) return null;

        const fromPos = new THREE.Vector3(
          fromObj.position[0],
          fromObj.position[2],
          -fromObj.position[1]
        );

        const toPos = new THREE.Vector3(
          toObj.position[0],
          toObj.position[2],
          -toObj.position[1]
        );

        // Color based on relationship type
        const color = rel.type === 'supports' || rel.type === 'on_top_of'
          ? '#00ff00'
          : rel.type === 'near'
          ? '#ffff00'
          : '#ff00ff';

        return {
          id: `${rel.from}-${rel.to}`,
          from: fromPos,
          to: toPos,
          color,
          type: rel.type
        };
      })
      .filter(Boolean);
  }, [objects, relationships]);

  return (
    <>
      {lines.map(line => line && (
        <group key={line.id}>
          <line>
            <bufferGeometry>
              <bufferAttribute
                attach="attributes-position"
                count={2}
                array={new Float32Array([
                  line.from.x, line.from.y, line.from.z,
                  line.to.x, line.to.y, line.to.z
                ])}
                itemSize={3}
              />
            </bufferGeometry>
            <lineBasicMaterial color={line.color} linewidth={2} />
          </line>

          {/* Relationship label */}
          <Text
            position={[
              (line.from.x + line.to.x) / 2,
              (line.from.y + line.to.y) / 2 + 0.2,
              (line.from.z + line.to.z) / 2
            ]}
            fontSize={0.15}
            color={line.color}
            anchorX="center"
            anchorY="middle"
          >
            {line.type}
          </Text>
        </group>
      ))}
    </>
  );
};

// Main Scene3D component
const Scene3D: React.FC<Scene3DProps> = ({
  objects,
  relationships,
  selectedObject,
  onObjectClick,
  showRelationships = true,
  showGrid = true
}) => {
  return (
    <div style={{ width: '100%', height: '100%', position: 'relative' }}>
      <Canvas
        shadows
        camera={{ position: [8, 8, 8], fov: 50 }}
        style={{ background: 'linear-gradient(to bottom, #87CEEB 0%, #98FB98 100%)' }}
      >
        {/* Lighting */}
        <ambientLight intensity={0.4} />
        <directionalLight
          position={[10, 10, 10]}
          intensity={1}
          castShadow
          shadow-mapSize-width={2048}
          shadow-mapSize-height={2048}
        />
        <pointLight position={[-10, -10, -10]} intensity={0.5} />

        {/* Environment */}
        <Environment preset="city" />

        {/* Ground grid */}
        {showGrid && (
          <Grid
            args={[20, 20]}
            position={[0, 0, 0]}
            cellSize={1}
            cellThickness={0.5}
            cellColor="#aaaaaa"
            sectionSize={5}
            sectionThickness={1}
            sectionColor="#666666"
          />
        )}

        {/* Ground plane */}
        <mesh position={[0, -0.01, 0]} rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
          <planeGeometry args={[50, 50]} />
          <meshStandardMaterial color="#f0f0f0" />
        </mesh>

        {/* 3D Objects */}
        {Object.entries(objects).map(([id, obj]) => (
          <Object3D
            key={id}
            object={obj}
            isSelected={selectedObject === id}
            onClick={() => onObjectClick?.(id)}
          />
        ))}

        {/* Relationship lines */}
        {showRelationships && (
          <RelationshipLines objects={objects} relationships={relationships} />
        )}

        {/* Camera controls */}
        <OrbitControls
          enablePan={true}
          enableZoom={true}
          enableRotate={true}
          minDistance={3}
          maxDistance={50}
          maxPolarAngle={Math.PI / 2}
        />
      </Canvas>

      {/* Scene info overlay */}
      <div style={{
        position: 'absolute',
        top: 10,
        left: 10,
        background: 'rgba(0, 0, 0, 0.7)',
        color: 'white',
        padding: '10px',
        borderRadius: '5px',
        fontSize: '14px'
      }}>
        <div>Objects: {Object.keys(objects).length}</div>
        <div>Relationships: {relationships.length}</div>
        {selectedObject && <div>Selected: {selectedObject}</div>}
      </div>
    </div>
  );
};

export default Scene3D;
