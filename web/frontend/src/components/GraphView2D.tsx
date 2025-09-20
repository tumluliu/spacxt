import React, { useEffect, useRef, useState, useMemo, useCallback } from 'react';
import Graph from 'graphology';
import Sigma from 'sigma';
import forceAtlas2 from 'graphology-layout-forceatlas2';
import { Typography, Chip, IconButton, Tooltip } from '@mui/material';
import {
  AccountTree as GraphIcon,
  ZoomIn,
  ZoomOut,
  CenterFocusStrong,
  Refresh
} from '@mui/icons-material';
import { SpatialObject, SpatialRelationship } from '../types/spatial';

interface GraphView2DProps {
  objects?: SpatialObject[];
  relationships?: SpatialRelationship[];
  selectedObject?: string;
  onObjectClick?: (objectId: string) => void;
}

// Enhanced color palette with better contrast and visual hierarchy
const RELATION_COLORS: Record<string, string> = {
  on_top_of: '#DC2626', // Red-600
  supports: '#059669', // Emerald-600
  near: '#2563EB', // Blue-600
  beside: '#D97706', // Amber-600
  above: '#7C3AED', // Violet-600
  below: '#0891B2', // Cyan-600
  far: '#6B7280', // Gray-500
  default: '#4B5563' // Gray-600
};

const OBJECT_COLORS: Record<string, string> = {
  table: '#92400E', // Amber-800
  cup: '#B91C1C', // Red-700
  book: '#1D4ED8', // Blue-700
  chair: '#047857', // Emerald-700
  stove: '#374151', // Gray-700
  coffee_cup: '#B91C1C', // Red-700
  default: '#6B7280' // Gray-500
};

// Node size mapping for better visual hierarchy
const getNodeSize = (type: string, bbox?: number[]): number => {
  const baseSize = 12;
  const typeMultipliers: Record<string, number> = {
    table: 1.5,
    chair: 1.2,
    stove: 1.4,
    book: 0.8,
    cup: 0.7,
    coffee_cup: 0.7,
    default: 1.0
  };

  const multiplier = typeMultipliers[type] || typeMultipliers.default;
  const bboxSize = Array.isArray(bbox) ? Math.sqrt(bbox[0] * bbox[1]) : 1;

  return Math.max(8, Math.min(20, baseSize * multiplier * Math.log(bboxSize + 1)));
};

export default function GraphView2D({
  objects = [],
  relationships = [],
  selectedObject,
  onObjectClick
}: GraphView2DProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const sigmaRef = useRef<Sigma | null>(null);
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });

  // Process data for Sigma.js with enhanced styling
  const graphData = useMemo(() => {
    console.log('GraphView2D: Processing data - objects:', objects, 'relationships:', relationships);

    // Ensure objects is an array
    if (!Array.isArray(objects)) {
      console.warn('GraphView2D: objects prop is not an array:', objects);
      return { nodes: [], links: [] };
    }

    const nodes = objects.map(obj => {
      const cleanName = obj.id.replace(/_\d+$/, '');
      return {
        id: obj.id,
        name: cleanName,
        type: obj.type,
        color: OBJECT_COLORS[obj.type] || OBJECT_COLORS.default,
        size: getNodeSize(obj.type, Array.isArray(obj.bbox) ? obj.bbox : undefined),
        // Add visual properties for better rendering
        borderColor: '#FFFFFF',
        borderSize: 2,
        highlighted: obj.id === selectedObject
      };
    });

    // Ensure relationships is an array
    if (!Array.isArray(relationships)) {
      console.warn('GraphView2D: relationships prop is not an array:', relationships);
      return { nodes, links: [] };
    }

    // Create a set of valid node IDs for filtering
    const nodeIds = new Set(nodes.map(node => node.id));

    // Filter relationships to only include those with valid nodes
    const validRelationships = relationships.filter(rel => {
      const hasValidSource = nodeIds.has(rel.from);
      const hasValidTarget = nodeIds.has(rel.to);

      if (!hasValidSource || !hasValidTarget) {
        // Silently filter out relationships with invalid nodes (like "kitchen")
        return false;
      }
      return true;
    });

    const links = validRelationships.map(rel => {
      const baseWidth = 2;
      const confidenceMultiplier = Math.max(0.5, rel.confidence || 0.8);

      return {
        source: rel.from,
        target: rel.to,
        type: rel.type,
        confidence: rel.confidence,
        color: RELATION_COLORS[rel.type] || RELATION_COLORS.default,
        width: baseWidth * confidenceMultiplier,
        // Add visual enhancements for display purposes
        displayAlpha: Math.max(0.6, confidenceMultiplier),
        displayCurvature: 0.1, // Slight curve for better visibility
        displayLabel: rel.type.replace(/_/g, ' ')
      };
    });

    console.log('GraphView2D: Processed data:', {
      nodeCount: nodes.length,
      linkCount: links.length,
      nodes: nodes.map(n => ({ id: n.id, type: n.type, size: n.size })),
      links: links.map(l => ({ from: l.source, to: l.target, type: l.type }))
    });

    return { nodes, links };
  }, [objects, relationships, selectedObject]);

  // Simplified and more reliable container sizing
  useEffect(() => {
    const updateDimensions = () => {
      const container = containerRef.current;
      if (!container) return;

      // Get the actual available space from the container's parent
      const parent = container.parentElement;
      if (!parent) return;

      // Use computed styles to get the exact available space
      const parentStyles = window.getComputedStyle(parent);
      const parentRect = parent.getBoundingClientRect();

      // Calculate available space accounting for padding
      const paddingX = parseFloat(parentStyles.paddingLeft) + parseFloat(parentStyles.paddingRight);
      const paddingY = parseFloat(parentStyles.paddingTop) + parseFloat(parentStyles.paddingBottom);

      const newDimensions = {
        width: Math.floor(parentRect.width - paddingX),
        height: Math.floor(parentRect.height - paddingY)
      };

      // Ensure minimum dimensions for usability
      if (newDimensions.width < 200 || newDimensions.height < 200) {
        console.log('GraphView2D: Dimensions too small, using fallback');
        setDimensions({ width: 600, height: 400 });
        return;
      }

      console.log('GraphView2D: Updated dimensions:', newDimensions);
      setDimensions(newDimensions);
    };

    // Initial dimension calculation with a small delay for DOM settling
    const initialTimeout = setTimeout(updateDimensions, 100);

    // Set up resize observer for responsive behavior
    const container = containerRef.current;
    let resizeObserver: ResizeObserver | null = null;

    if (container?.parentElement) {
      resizeObserver = new ResizeObserver(() => {
        requestAnimationFrame(updateDimensions);
      });
      resizeObserver.observe(container.parentElement);
    }

    return () => {
      clearTimeout(initialTimeout);
      if (resizeObserver) {
        resizeObserver.disconnect();
      }
    };
  }, []);

  // Enhanced Sigma.js initialization with better layout and styling
  useEffect(() => {
    console.log('GraphView2D: Initializing Sigma with:', {
      containerRef: !!containerRef.current,
      dimensions,
      nodeCount: graphData.nodes.length,
      linkCount: graphData.links.length
    });

    if (!containerRef.current || !dimensions.width || !dimensions.height) {
      console.log('GraphView2D: Skipping Sigma creation - invalid state');
      return;
    }

    const container = containerRef.current;

    // Set container styles for proper rendering
    container.style.width = `${dimensions.width}px`;
    container.style.height = `${dimensions.height}px`;
    container.style.position = 'relative';
    container.style.overflow = 'hidden';

    // Clean up previous instance
    if (sigmaRef.current) {
      sigmaRef.current.kill();
      sigmaRef.current = null;
    }

    // Create graph with enhanced configuration
    const graph = new Graph({ type: 'directed' });

    // Determine if we have real data or should show test data
    const hasRealData = graphData.nodes.length > 0;
    const nodesToAdd = hasRealData ? graphData.nodes : [
      { id: 'demo1', name: 'Demo Object 1', color: '#3B82F6', size: 12, type: 'demo' },
      { id: 'demo2', name: 'Demo Object 2', color: '#EF4444', size: 12, type: 'demo' },
      { id: 'demo3', name: 'Demo Object 3', color: '#10B981', size: 12, type: 'demo' }
    ];

    const linksToAdd = hasRealData ? graphData.links : [
      { source: 'demo1', target: 'demo2', type: 'near', color: '#6B7280', width: 2 },
      { source: 'demo2', target: 'demo3', type: 'supports', color: '#6B7280', width: 2 }
    ];

    // Add nodes with enhanced styling
    nodesToAdd.forEach(node => {
      const isSelected = node.id === selectedObject;
      graph.addNode(node.id, {
        label: node.name || node.id,
        size: node.size || 12,
        color: isSelected ? '#F59E0B' : node.color, // Highlight selected
        borderColor: isSelected ? '#D97706' : '#FFFFFF',
        borderSize: isSelected ? 3 : 1,
        x: Math.random() * 200 - 100,
        y: Math.random() * 200 - 100,
        type: 'circle'
      });
    });

    // Add edges with enhanced styling
    linksToAdd.forEach((link, index) => {
      try {
        const edgeId = `edge-${index}`;
        graph.addEdge(link.source, link.target, {
          id: edgeId,
          label: (link as any).displayLabel || link.type,
          color: link.color,
          size: link.width || 2,
          type: 'arrow'
        });
      } catch (error) {
        console.warn(`Failed to add edge ${link.source} -> ${link.target}:`, error);
      }
    });

    // Apply improved layout algorithm
    if (graph.order > 0) {
      try {
        const layoutSettings = {
          iterations: hasRealData ? 100 : 50,
          settings: {
            gravity: 0.5,
            scalingRatio: hasRealData ? 20 : 15,
            strongGravityMode: false,
            barnesHutOptimize: true,
            slowDown: 1,
            startingIterations: 10,
            iterationsPerRender: 1
          }
        };

        forceAtlas2.assign(graph, layoutSettings);
        console.log('Enhanced ForceAtlas2 layout applied');
      } catch (error) {
        console.warn('Layout failed, using circular positioning:', error);
        // Fallback to circular layout
        const angleStep = (2 * Math.PI) / graph.order;
        let angle = 0;
        graph.forEachNode((node, attributes) => {
          const radius = 80;
          graph.setNodeAttribute(node, 'x', Math.cos(angle) * radius);
          graph.setNodeAttribute(node, 'y', Math.sin(angle) * radius);
          angle += angleStep;
        });
      }
    }

    // Create Sigma instance with optimized settings
    let sigma: Sigma;
    try {
      sigma = new Sigma(graph, container, {
        // Rendering settings
        renderLabels: true,
        renderEdgeLabels: true,
        allowInvalidContainer: false,

        // Visual settings
        defaultNodeColor: '#6B7280',
        defaultEdgeColor: '#9CA3AF',
        labelColor: { color: '#374151' },
        labelSize: 14,
        labelWeight: '500',

        // Performance settings
        hideEdgesOnMove: false,
        hideLabelsOnMove: false,

        // Camera settings
        minCameraRatio: 0.05,
        maxCameraRatio: 5,

        // Node settings
        nodeProgramClasses: {},

        // Edge settings
        edgeProgramClasses: {},

        // Interaction settings
        enableEdgeEvents: true
      });

      console.log('Enhanced Sigma instance created');
    } catch (error) {
      console.error('Failed to create Sigma instance:', error);
      return;
    }

    // Enhanced event listeners
    sigma.on('clickNode', (event) => {
      console.log('Node clicked:', event.node);
      if (onObjectClick) {
        onObjectClick(event.node);
      }
    });

    sigma.on('enterNode', (event) => {
      // Highlight node on hover
      sigma.getGraph().setNodeAttribute(event.node, 'highlighted', true);
      sigma.refresh();
    });

    sigma.on('leaveNode', (event) => {
      // Remove highlight on leave
      sigma.getGraph().setNodeAttribute(event.node, 'highlighted', false);
      sigma.refresh();
    });

    // Store reference
    sigmaRef.current = sigma;

    // Initial camera positioning
    setTimeout(() => {
      if (sigma && graph.order > 0) {
        sigma.getCamera().animatedReset({ duration: 300 });
        sigma.refresh();
        console.log('Sigma positioned and refreshed');
      }
    }, 100);

    // Cleanup function
    return () => {
      if (sigmaRef.current) {
        sigmaRef.current.kill();
        sigmaRef.current = null;
      }
    };
  }, [graphData, dimensions, selectedObject, onObjectClick]);

  // Control handlers
  const handleZoomIn = useCallback(() => {
    if (sigmaRef.current) {
      const camera = sigmaRef.current.getCamera();
      camera.animatedZoom({ duration: 200 });
    }
  }, []);

  const handleZoomOut = useCallback(() => {
    if (sigmaRef.current) {
      const camera = sigmaRef.current.getCamera();
      camera.animatedUnzoom({ duration: 200 });
    }
  }, []);

  const handleResetView = useCallback(() => {
    if (sigmaRef.current) {
      const camera = sigmaRef.current.getCamera();
      camera.animatedReset({ duration: 200 });
    }
  }, []);

  const handleRestartSimulation = useCallback(() => {
    if (sigmaRef.current) {
      sigmaRef.current.refresh();
    }
  }, []);

  return (
    <div
      style={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        backgroundColor: '#ffffff',
        borderRadius: '12px',
        overflow: 'hidden',
        boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
        border: '1px solid rgba(226, 232, 240, 0.5)',
      }}
    >
      {/* Enhanced Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '20px 24px',
          background: 'linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%)',
          borderBottom: '1px solid rgba(226, 232, 240, 0.6)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div
            style={{
              padding: '8px',
              backgroundColor: '#3B82F6',
              borderRadius: '8px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            <GraphIcon sx={{ color: 'white', fontSize: '20px' }} />
          </div>
          <div>
            <Typography variant="h6" sx={{ fontWeight: 600, color: '#1e293b', fontSize: '18px' }}>
              Spatial Relationship Graph
            </Typography>
            <Typography variant="body2" sx={{ color: '#64748b', fontSize: '13px' }}>
              {objects.length} objects • {relationships.length} relationships
            </Typography>
          </div>
        </div>

        {/* Enhanced Controls */}
        <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
          <Tooltip title="Zoom In">
            <IconButton
              onClick={handleZoomIn}
              size="small"
              sx={{
                backgroundColor: '#f1f5f9',
                color: '#475569',
                border: '1px solid #e2e8f0',
                '&:hover': {
                  backgroundColor: '#e2e8f0',
                  color: '#334155'
                },
                width: 36,
                height: 36
              }}
            >
              <ZoomIn fontSize="small" />
            </IconButton>
          </Tooltip>

          <Tooltip title="Zoom Out">
            <IconButton
              onClick={handleZoomOut}
              size="small"
              sx={{
                backgroundColor: '#f1f5f9',
                color: '#475569',
                border: '1px solid #e2e8f0',
                '&:hover': {
                  backgroundColor: '#e2e8f0',
                  color: '#334155'
                },
                width: 36,
                height: 36
              }}
            >
              <ZoomOut fontSize="small" />
            </IconButton>
          </Tooltip>

          <Tooltip title="Reset View">
            <IconButton
              onClick={handleResetView}
              size="small"
              sx={{
                backgroundColor: '#f1f5f9',
                color: '#475569',
                border: '1px solid #e2e8f0',
                '&:hover': {
                  backgroundColor: '#e2e8f0',
                  color: '#334155'
                },
                width: 36,
                height: 36
              }}
            >
              <CenterFocusStrong fontSize="small" />
            </IconButton>
          </Tooltip>

          <Tooltip title="Refresh Layout">
            <IconButton
              onClick={handleRestartSimulation}
              size="small"
              sx={{
                backgroundColor: '#3B82F6',
                color: 'white',
                border: '1px solid #2563EB',
                '&:hover': {
                  backgroundColor: '#2563EB',
                },
                width: 36,
                height: 36,
                marginLeft: '6px'
              }}
            >
              <Refresh fontSize="small" />
            </IconButton>
          </Tooltip>
        </div>
      </div>

      {/* Enhanced Sigma Container */}
      <div
        ref={containerRef}
        style={{
          flex: 1,
          position: 'relative',
          background: 'radial-gradient(circle at 30% 30%, rgba(59, 130, 246, 0.02) 0%, transparent 50%), linear-gradient(135deg, #fefefe 0%, #f8fafc 100%)',
          minHeight: 0 // Ensure flex child can shrink
        }}
      />

      {/* Enhanced Empty State */}
      {graphData.nodes.length === 0 && (
        <div
          style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            textAlign: 'center',
            color: '#64748b',
            padding: '40px'
          }}
        >
          <div
            style={{
              padding: '20px',
              backgroundColor: 'rgba(59, 130, 246, 0.1)',
              borderRadius: '20px',
              display: 'inline-block',
              marginBottom: '16px'
            }}
          >
            <GraphIcon sx={{ fontSize: 48, color: '#3B82F6', opacity: 0.7 }} />
          </div>
          <Typography variant="h6" sx={{ fontWeight: 600, color: '#374151', mb: 1 }}>
            No spatial relationships to display
          </Typography>
          <Typography variant="body2" sx={{ color: '#6b7280' }}>
            Add objects and their spatial relationships to see the interactive graph
          </Typography>
        </div>
      )}

      {/* Relationship Legend */}
      {relationships.length > 0 && (
        <div
          style={{
            position: 'absolute',
            top: '80px',
            left: '24px',
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            backdropFilter: 'blur(8px)',
            borderRadius: '8px',
            padding: '12px 16px',
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
            border: '1px solid rgba(226, 232, 240, 0.6)',
            maxWidth: '200px'
          }}
        >
          <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#374151', mb: 1, fontSize: '12px' }}>
            RELATIONSHIP TYPES
          </Typography>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            {Array.from(new Set(relationships.map(r => r.type))).slice(0, 5).map(type => (
              <div key={type} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <div
                  style={{
                    width: '12px',
                    height: '2px',
                    backgroundColor: RELATION_COLORS[type] || RELATION_COLORS.default,
                    borderRadius: '1px'
                  }}
                />
                <Typography variant="caption" sx={{ color: '#6b7280', fontSize: '11px' }}>
                  {type.replace(/_/g, ' ')}
                </Typography>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}