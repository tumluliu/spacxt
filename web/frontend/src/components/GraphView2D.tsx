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

// Import curved edge support with arrows
import { EdgeCurvedArrowProgram } from '@sigma/edge-curve';

interface GraphView2DProps {
  objects?: SpatialObject[];
  relationships?: SpatialRelationship[];
  selectedObject?: string;
  onObjectClick?: (objectId: string) => void;
  isActive?: boolean;
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
  onObjectClick,
  isActive = true
}: GraphView2DProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const sigmaRef = useRef<Sigma | null>(null);
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });

  const updateDimensions = useCallback(() => {
    const container = containerRef.current;
    if (!container) return;

    const parent = container.parentElement;
    if (!parent) return;

    const parentStyles = window.getComputedStyle(parent);
    const parentRect = parent.getBoundingClientRect();

    const paddingX = parseFloat(parentStyles.paddingLeft) + parseFloat(parentStyles.paddingRight);
    const paddingY = parseFloat(parentStyles.paddingTop) + parseFloat(parentStyles.paddingBottom);

    const newDimensions = {
      width: Math.floor(parentRect.width - paddingX),
      height: Math.floor(parentRect.height - paddingY)
    };

    if (newDimensions.width < 200 || newDimensions.height < 200) {
      console.log('GraphView2D: Dimensions too small, using fallback');
      setDimensions({ width: 600, height: 400 });
      return;
    }

    console.log('GraphView2D: Updated dimensions:', newDimensions);
    setDimensions(newDimensions);
  }, []);

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
  }, [updateDimensions]);

  useEffect(() => {
    if (isActive) {
      const rafId = requestAnimationFrame(() => {
        updateDimensions();
      });
      return () => cancelAnimationFrame(rafId);
    }
    return undefined;
  }, [isActive, updateDimensions]);

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
      try {
        graph.addNode(node.id, {
          label: node.name || node.id,
          size: node.size || 12,
          color: isSelected ? '#F59E0B' : node.color, // Highlight selected
          borderColor: isSelected ? '#D97706' : '#FFFFFF',
          borderSize: isSelected ? 3 : 1,
          x: Math.random() * 200 - 100,
          y: Math.random() * 200 - 100,
          objectType: node.type || 'default' // Store as custom attribute, not 'type'
          // Explicitly do NOT set 'type' to avoid Sigma renderer conflicts
        });
      } catch (error) {
        console.warn(`Failed to add node ${node.id}:`, error);
      }
    });

    // Check for ANY edges between the same pair of nodes (regardless of relationship type)
    // to determine if we need curves to avoid visual overlap
    const nodeConnectionCounts = new Map();

    // Count connections between each pair of nodes
    linksToAdd.forEach(link => {
      const pairKey = [link.source, link.target].sort().join('<->');
      nodeConnectionCounts.set(pairKey, (nodeConnectionCounts.get(pairKey) || 0) + 1);
    });

    console.log('Node connection counts:', Array.from(nodeConnectionCounts.entries()));
    console.log('All links to add:', linksToAdd.map(l => `${l.source} -> ${l.target} (${l.type})`));

    // Add edges with curves for any multiple connections between same nodes
    linksToAdd.forEach((link, index) => {
      try {
        const edgeId = `edge-${index}`;
        const pairKey = [link.source, link.target].sort().join('<->');
        const hasMultipleConnections = (nodeConnectionCounts.get(pairKey) || 0) > 1;

        // Use curved arrows for any multiple connections to avoid overlap
        let edgeSize = link.width || 2;
        let edgeColor = link.color;
        let edgeType = 'arrow'; // Always use arrow type for direction indication
        let curvature = 0;

        if (hasMultipleConnections) {
          // Create deterministic curve direction based on relationship type and direction
          // This ensures consistent curves and separation
          const isForwardDirection = link.source.localeCompare(link.target) < 0;
          const relationshipHash = link.type.split('').reduce((hash, char) => {
            return hash + char.charCodeAt(0);
          }, 0);

          // Use relationship type and direction to determine curvature
          if (isForwardDirection) {
            curvature = (relationshipHash % 2 === 0) ? 0.4 : -0.4;
          } else {
            curvature = (relationshipHash % 2 === 0) ? -0.4 : 0.4;
          }

          edgeSize = Math.max(edgeSize, 3); // Thicker for visibility

          console.log(`Creating curved edge: ${link.source} -> ${link.target} (${link.type}), curvature: ${curvature}`);
        }

        const edgeAttributes: any = {
          id: edgeId,
          label: (link as any).displayLabel || link.type,
          color: edgeColor,
          size: edgeSize,
          type: edgeType
        };

        // Add curvature for multiple connections (curved arrows)
        if (hasMultipleConnections && curvature !== 0) {
          edgeAttributes.curvature = curvature;
        }

        graph.addEdge(link.source, link.target, edgeAttributes);
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
        allowInvalidContainer: true, // Allow invalid containers to prevent width errors

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

        // Edge settings - enable curved edges with arrows
        edgeProgramClasses: {
          arrow: EdgeCurvedArrowProgram, // Use EdgeCurvedArrowProgram for curved arrows with arrowheads
        },
        defaultEdgeType: 'arrow', // Use arrow type by default

        // Interaction settings
        enableEdgeEvents: true,

        // Disable all keyboard interactions completely
        stagePadding: 0
      });

      // Completely disable keyboard interactions by blocking at the document level for this container
      const sigmaContainer = sigma.getContainer();

      if (sigmaContainer) {
        // Remove any focus capability
        sigmaContainer.removeAttribute('tabindex');
        sigmaContainer.style.outline = 'none';

        // Create a comprehensive keyboard blocker
        const keyboardBlocker = (e: KeyboardEvent) => {
          // Check if the event target is within the Sigma container
          if (sigmaContainer.contains(e.target as Node) || e.target === sigmaContainer) {
            e.stopImmediatePropagation();
            e.preventDefault();
            return false;
          }
        };

        // Add listeners at the document level to catch all keyboard events
        document.addEventListener('keydown', keyboardBlocker, true);
        document.addEventListener('keyup', keyboardBlocker, true);
        document.addEventListener('keypress', keyboardBlocker, true);

        // Store the blocker function for cleanup
        (sigmaContainer as any)._keyboardBlocker = keyboardBlocker;
      }

      console.log('Enhanced Sigma instance created with keyboard disabled');
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

    // Additional container-level keyboard blocking
    container.setAttribute('tabindex', '-1');
    container.style.outline = 'none';

    // Store reference
    sigmaRef.current = sigma;

    // Initial camera positioning
    setTimeout(() => {
      if (sigma && graph.order > 0) {
        try {
          sigma.getCamera().animatedReset({ duration: 300 });
          sigma.refresh();
          console.log('Sigma positioned and refreshed');
        } catch (error) {
          console.error('Error during Sigma refresh:', error);
          // Try to identify problematic nodes
          graph.forEachNode((nodeId, attributes) => {
            if (attributes.type && attributes.type !== 'default') {
              console.warn(`Node ${nodeId} has problematic type:`, attributes.type);
              // Remove the problematic type attribute
              graph.removeNodeAttribute(nodeId, 'type');
            }
          });
          // Try refresh again
          try {
            sigma.refresh();
            console.log('Sigma refreshed after cleanup');
          } catch (secondError) {
            console.error('Still failing after cleanup:', secondError);
          }
        }
      }
    }, 100);

    // Cleanup function
    return () => {
      if (sigmaRef.current) {
        // Clean up document-level keyboard blockers
        const sigmaContainer = sigmaRef.current.getContainer();
        if (sigmaContainer && (sigmaContainer as any)._keyboardBlocker) {
          const blocker = (sigmaContainer as any)._keyboardBlocker;
          document.removeEventListener('keydown', blocker, true);
          document.removeEventListener('keyup', blocker, true);
          document.removeEventListener('keypress', blocker, true);
          delete (sigmaContainer as any)._keyboardBlocker;
        }

        sigmaRef.current.kill();
        sigmaRef.current = null;
      }
    };
  }, [graphData.nodes.length, graphData.links.length, dimensions.width, dimensions.height, updateDimensions]);

  // Handle selected object changes without recreating Sigma
  useEffect(() => {
    if (!sigmaRef.current) return;

    const graph = sigmaRef.current.getGraph();

    // Reset all nodes to unselected state
    graph.forEachNode((nodeId) => {
      const nodeType = graph.getNodeAttribute(nodeId, 'objectType') || 'default';
      graph.setNodeAttribute(nodeId, 'color', OBJECT_COLORS[nodeType] || OBJECT_COLORS.default);
      graph.setNodeAttribute(nodeId, 'borderColor', '#FFFFFF');
      graph.setNodeAttribute(nodeId, 'borderSize', 1);
    });

    // Highlight selected node
    if (selectedObject && graph.hasNode(selectedObject)) {
      graph.setNodeAttribute(selectedObject, 'color', '#F59E0B');
      graph.setNodeAttribute(selectedObject, 'borderColor', '#D97706');
      graph.setNodeAttribute(selectedObject, 'borderSize', 3);
    }

    sigmaRef.current.refresh();
  }, [selectedObject]);

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
