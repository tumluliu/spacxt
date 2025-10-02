// 3D Force-Directed Graph View using react-force-graph-3d
// Shows spatial relationships as nodes and edges in a clean graph layout

import React, { useRef, useEffect, useState } from 'react';
import ForceGraph3D from 'react-force-graph-3d';
import { SpatialObject, SpatialRelationship } from '../types/spatial';

interface GraphView3DProps {
  objects: Record<string, SpatialObject>;
  relationships: SpatialRelationship[];
  selectedObject?: string;
  onObjectClick?: (objectId: string) => void;
  width?: number;
  height?: number;
}

interface GraphNode {
  id: string;
  name: string;
  type: string;
  position: [number, number, number];
  color: string;
  size: number;
}

interface GraphLink {
  source: string;
  target: string;
  type: string;
  confidence: number;
  color: string;
  width: number;
}

// Color mapping for different object types
const TYPE_COLORS: Record<string, string> = {
  furniture: '#8B4513',
  appliance: '#C0C0C0',
  coffee_cup: '#FFFFFF',
  cup: '#FFFFFF',
  book: '#4169E1',
  phone: '#000000',
  default: '#808080'
};

// Color mapping for different relationship types - more distinct colors
const RELATION_COLORS: Record<string, string> = {
  on_top_of: '#FF4757',    // Bright red
  supports: '#2ED573',     // Bright green
  near: '#3742FA',         // Bright blue
  beside: '#FF6348',       // Orange-red
  above: '#FFA502',        // Orange
  below: '#A55EEA',        // Purple
  in: '#26C6DA',          // Cyan
  default: '#95A5A6'
};

const GraphView3D: React.FC<GraphView3DProps> = ({
  objects,
  relationships,
  selectedObject,
  onObjectClick,
  width = 800,
  height = 600
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: width, height: height });

  // Update dimensions when container size changes
  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        const rect = containerRef.current.getBoundingClientRect();
        if (rect.width > 0 && rect.height > 0) {
          setDimensions({
            width: rect.width,
            height: rect.height
          });
          console.log('GraphView3D: Updated dimensions:', rect.width, 'x', rect.height);
        }
      }
    };

    // Small delay to ensure DOM is fully rendered
    const timer = setTimeout(updateDimensions, 100);
    window.addEventListener('resize', updateDimensions);

    return () => {
      clearTimeout(timer);
      window.removeEventListener('resize', updateDimensions);
    };
  }, []);

  // Also update when objects change (component might be re-rendered)
  useEffect(() => {
    const timer = setTimeout(() => {
      if (containerRef.current) {
        const rect = containerRef.current.getBoundingClientRect();
        if (rect.width > 0 && rect.height > 0) {
          setDimensions({
            width: rect.width,
            height: rect.height
          });
        }
      }
    }, 50);

    return () => clearTimeout(timer);
  }, [objects, relationships]);

  console.log('GraphView3D: Rendering with objects:', Object.keys(objects).length, 'relationships:', relationships.length);

  // Convert spatial objects to graph nodes
  const nodes: GraphNode[] = Object.values(objects).map(obj => ({
    id: obj.id,
    name: obj.name || obj.id.replace(/_\d+$/, '').replace(/_/g, ' '),
    type: obj.type,
    position: obj.position,
    color: obj.id === selectedObject ? '#FFD700' : (TYPE_COLORS[obj.type] || TYPE_COLORS.default),
    size: Math.max(8, Math.min(20, (obj.bbox?.xyz?.[0] || 0.5) * 30))
  }));

  // Convert spatial relationships to graph links
  const links: GraphLink[] = relationships
    .filter(rel => {
      // Only filter out room containment and ensure both objects exist
      const shouldSkip = rel.type === 'in' || !objects[rel.from] || !objects[rel.to];
      return !shouldSkip;
    })
    .map(rel => ({
      source: rel.from,
      target: rel.to,
      type: rel.type,
      confidence: rel.confidence,
      color: RELATION_COLORS[rel.type] || RELATION_COLORS.default,
      width: Math.max(1, rel.confidence * 4)
    }));

  const graphData = { nodes, links };
  console.log('GraphView3D: Graph data prepared:', graphData);

  return (
    <div
      ref={containerRef}
      style={{
        width: '100%',
        height: '100%',
        position: 'relative',
        background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)'
      }}
    >
      {/* Status indicator */}
      <div style={{
        position: 'absolute',
        top: 20,
        right: 20,
        background: 'rgba(15, 23, 42, 0.95)',
        backdropFilter: 'blur(20px)',
        color: 'white',
        padding: '12px 16px',
        borderRadius: '12px',
        fontSize: '13px',
        fontWeight: 600,
        pointerEvents: 'none',
        zIndex: 1000,
        border: '1px solid rgba(148, 163, 184, 0.1)',
        boxShadow: '0 4px 20px rgba(0, 0, 0, 0.15)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <span style={{ color: '#00e5ff' }}>Objects: {Object.keys(objects).length}</span>
          <span style={{ color: '#ff6b35' }}>Relations: {relationships.length}</span>
          <span style={{ color: '#10b981' }}>Visible: {links.length}</span>
        </div>
      </div>

      {Object.keys(objects).length > 0 ? (
        <ForceGraph3D
          width={dimensions.width}
          height={dimensions.height}
          graphData={graphData}
          backgroundColor="rgba(0,0,0,0.1)"
          showNavInfo={false}

          // Node appearance
          nodeLabel={(node: GraphNode) => `
            <div style="
              background: rgba(0,0,0,0.8);
              color: white;
              padding: 8px;
              border-radius: 4px;
              font-size: 12px;
              max-width: 200px;
            ">
              <strong>${node.name}</strong><br/>
              Type: ${node.type}<br/>
              Position: [${node.position.map(p => p.toFixed(1)).join(', ')}]
            </div>
          `}
          nodeColor={(node: GraphNode) => node.color}
          nodeVal={(node: GraphNode) => node.size}
          nodeOpacity={0.9}

          // Link appearance with curved edges for bidirectional relationships
          linkLabel={(link: GraphLink) => `
            <div style="
              background: rgba(0,0,0,0.8);
              color: white;
              padding: 6px;
              border-radius: 4px;
              font-size: 11px;
            ">
              <strong>${link.type.replace(/_/g, ' ')}</strong><br/>
              Confidence: ${(link.confidence * 100).toFixed(1)}%
            </div>
          `}
          linkColor={(link: GraphLink) => link.color}
          linkWidth={(link: GraphLink) => link.width}
          linkOpacity={0.9}
          linkCurvature={(link: GraphLink) => {
            // Add curvature to prevent overlapping of bidirectional relationships
            const reverseLink = links.find(l =>
              l.source === link.target && l.target === link.source
            );
            if (reverseLink) {
              // Different curvature based on relationship type for visual distinction
              if (link.type === 'on_top_of') return 0.4;
              if (link.type === 'supports') return -0.4;  // Curve in opposite direction
              if (link.type === 'near') return 0.2;
              return 0.3;
            }
            return 0;
          }}
          linkDirectionalArrowLength={8}
          linkDirectionalArrowRelPos={0.8}
          linkDirectionalArrowColor={(link: GraphLink) => link.color}

          // Interaction handlers
          onNodeClick={(node: GraphNode) => {
            console.log('Node clicked:', node.id);
            if (onObjectClick) {
              onObjectClick(node.id);
            }
          }}
          onNodeHover={(node: GraphNode | null) => {
            // Change cursor on hover
            const container = document.querySelector('canvas');
            if (container) {
              container.style.cursor = node ? 'pointer' : 'default';
            }
          }}

          // Physics settings for better layout
          d3Force="charge"
          d3ForceStrength={-300}
          d3LinkDistance={100}
          d3CenterStrength={0.1}
        />
      ) : (
        // Fallback content when no objects
        <div style={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          color: 'white',
          fontSize: '18px',
          textAlign: 'center',
          background: 'rgba(15, 23, 42, 0.8)',
          backdropFilter: 'blur(20px)',
          padding: '40px',
          borderRadius: '20px',
          border: '1px solid rgba(148, 163, 184, 0.1)',
        }}>
          <div style={{
            fontSize: '48px',
            marginBottom: '16px',
            background: 'linear-gradient(135deg, #00e5ff 0%, #ff6b35 100%)',
            backgroundClip: 'text',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
          }}>
            🔗
          </div>
          <div style={{
            fontWeight: 700,
            marginBottom: '8px',
            background: 'linear-gradient(135deg, #00e5ff 0%, #ffffff 100%)',
            backgroundClip: 'text',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
          }}>
            Spatial Relationship Graph
          </div>
          <div style={{
            fontSize: '14px',
            opacity: 0.7,
            color: '#cbd5e1',
            fontWeight: 500,
          }}>
            Add objects to visualize their spatial relationships
          </div>
        </div>
      )}
    </div>
  );
};

export default GraphView3D;