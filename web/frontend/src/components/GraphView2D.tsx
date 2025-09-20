import React, { useEffect, useRef, useState, useMemo, useCallback } from 'react';
import * as d3 from 'd3';
import { Box, Typography, Button, ButtonGroup, Chip } from '@mui/material';
import { AccountTree as GraphIcon } from '@mui/icons-material';
import { SpatialObject, SpatialRelationship } from '../types/spatial';

interface GraphView2DProps {
  objects?: SpatialObject[];
  relationships?: SpatialRelationship[];
  selectedObject?: string;
  onObjectClick?: (objectId: string) => void;
}

const RELATION_COLORS: Record<string, string> = {
  on_top_of: '#ef4444',
  supports: '#22c55e',
  near: '#3b82f6',
  beside: '#f59e0b',
  above: '#8b5cf6',
  below: '#06b6d4',
  far: '#64748b',
  default: '#6b7280'
};

const OBJECT_COLORS: Record<string, string> = {
  table: '#8b4513',
  cup: '#dc2626',
  book: '#1d4ed8',
  chair: '#059669',
  stove: '#374151',
  default: '#6b7280'
};

export default function GraphView2D({
  objects = [],
  relationships = [],
  selectedObject,
  onObjectClick
}: GraphView2DProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });

  // Process data for D3
  const graphData = useMemo(() => {
    // Ensure objects is an array
    if (!Array.isArray(objects)) {
      console.warn('GraphView2D: objects prop is not an array:', objects);
      return { nodes: [], links: [] };
    }

    const nodes = objects.map(obj => ({
      id: obj.id,
      name: obj.id.replace(/_\d+$/, ''),
      type: obj.type,
      color: OBJECT_COLORS[obj.type] || OBJECT_COLORS.default,
      size: Math.max(15, Math.min(30, (Array.isArray(obj.bbox) ? obj.bbox[0] : 1) * 10))
    }));

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
        console.warn(`GraphView2D: Filtering out relationship with invalid nodes: ${rel.from} -> ${rel.to}`);
        return false;
      }
      return true;
    });

    const links = validRelationships.map(rel => ({
      source: rel.from,
      target: rel.to,
      type: rel.type,
      confidence: rel.confidence,
      color: RELATION_COLORS[rel.type] || RELATION_COLORS.default,
      width: Math.max(2, rel.confidence * 3)
    }));

    console.log('GraphView2D: Processed data:', {
      nodeCount: nodes.length,
      linkCount: links.length,
      nodeIds: nodes.map(n => n.id),
      linkSources: links.map(l => l.source),
      linkTargets: links.map(l => l.target)
    });

    return { nodes, links };
  }, [objects, relationships]);

  // Handle container resize
  useEffect(() => {
    const container = svgRef.current?.parentElement;
    if (!container) return;

    const resizeObserver = new ResizeObserver(entries => {
      const { width, height } = entries[0].contentRect;
      setDimensions({
        width: width - 40,
        height: height - 120
      });
    });

    resizeObserver.observe(container);
    return () => resizeObserver.disconnect();
  }, []);

  // Main D3 visualization
  useEffect(() => {
    if (!svgRef.current || !dimensions.width || !dimensions.height || graphData.nodes.length === 0) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const { width, height } = dimensions;

    // Create main container
    const container = svg.append('g');

    // Set up zoom and pan
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 4])
      .on('zoom', (event) => {
        container.attr('transform', event.transform);
      });

    svg.call(zoom);

    // Create arrow markers
    const defs = svg.append('defs');
    Object.entries(RELATION_COLORS).forEach(([type, color]) => {
      defs.append('marker')
        .attr('id', `arrow-${type}`)
        .attr('viewBox', '0 -5 10 10')
        .attr('refX', 15)
        .attr('refY', 0)
        .attr('markerWidth', 6)
        .attr('markerHeight', 6)
        .attr('orient', 'auto')
        .append('path')
        .attr('d', 'M0,-5L10,0L0,5')
        .attr('fill', color);
    });

    // Create force simulation
    const simulation = d3.forceSimulation(graphData.nodes as any)
      .force('link', d3.forceLink(graphData.links)
        .id((d: any) => d.id)
        .distance(120)
        .strength(0.6)
      )
      .force('charge', d3.forceManyBody().strength(-400))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius((d: any) => d.size + 10));

    // Create links
    const link = container.append('g')
      .attr('stroke-opacity', 0.8)
      .selectAll('path')
      .data(graphData.links)
      .join('path')
      .attr('fill', 'none')
      .attr('stroke', (d: any) => d.color)
      .attr('stroke-width', (d: any) => d.width)
      .attr('marker-end', (d: any) => `url(#arrow-${d.type})`);

    // Create nodes
    const node = container.append('g')
      .selectAll('circle')
      .data(graphData.nodes)
      .join('circle')
      .attr('r', (d: any) => d.size)
      .attr('fill', (d: any) => d.color)
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)
      .style('cursor', 'pointer')
      .on('click', (event: any, d: any) => {
        onObjectClick?.(d.id);
      })
      .on('mouseover', function(event: any, d: any) {
        d3.select(this).attr('stroke-width', 4);
      })
      .on('mouseout', function(event: any, d: any) {
        d3.select(this).attr('stroke-width', 2);
      })
      .call(d3.drag<any, any>()
        .on('start', (event: any, d: any) => {
          if (!event.active) simulation.alphaTarget(0.3).restart();
          d.fx = d.x;
          d.fy = d.y;
        })
        .on('drag', (event: any, d: any) => {
          d.fx = event.x;
          d.fy = event.y;
        })
        .on('end', (event: any, d: any) => {
          if (!event.active) simulation.alphaTarget(0);
          d.fx = null;
          d.fy = null;
        })
      );

    // Create node labels
    const label = container.append('g')
      .selectAll('text')
      .data(graphData.nodes)
      .join('text')
      .attr('text-anchor', 'middle')
      .attr('dy', '0.35em')
      .attr('font-size', '12px')
      .attr('font-weight', '600')
      .attr('fill', '#1f2937')
      .text((d: any) => d.name)
      .style('pointer-events', 'none');

    // Update positions on simulation tick
    simulation.on('tick', () => {
      // Update links with smart curves for bidirectional relationships
      link.attr('d', (d: any) => {
        const dx = d.target.x - d.source.x;
        const dy = d.target.y - d.source.y;
        const dr = Math.sqrt(dx * dx + dy * dy);

        // Check for reverse relationship
        const reverse = graphData.links.find((l: any) =>
          l.source.id === d.target.id && l.target.id === d.source.id
        );

        if (reverse && dr > 0) {
          // Create curved path for bidirectional relationships
          const sweep = d.type === 'supports' ? 1 : 0;
          const arc = dr * 0.3;
          return `M${d.source.x},${d.source.y}A${arc},${arc} 0 0,${sweep} ${d.target.x},${d.target.y}`;
        } else {
          // Straight line for single relationships
          return `M${d.source.x},${d.source.y}L${d.target.x},${d.target.y}`;
        }
      });

      // Update node positions
      node
        .attr('cx', (d: any) => d.x)
        .attr('cy', (d: any) => d.y);

      // Update label positions
      label
        .attr('x', (d: any) => d.x)
        .attr('y', (d: any) => d.y);
    });

    // Control functions
    const zoomIn = () => {
      svg.transition().call(zoom.scaleBy, 1.5);
    };

    const zoomOut = () => {
      svg.transition().call(zoom.scaleBy, 1 / 1.5);
    };

    const resetView = () => {
      svg.transition().call(zoom.transform, d3.zoomIdentity);
    };

    const restartSimulation = () => {
      simulation.alpha(1).restart();
    };

    // Store control functions for external access
    if (svgRef.current) {
      (svgRef.current as any).controls = {
        zoomIn,
        zoomOut,
        resetView,
        restartSimulation
      };
    }

    // Cleanup
    return () => {
      simulation.stop();
    };
  }, [graphData, dimensions, onObjectClick]);

  // Control handlers
  const handleZoomIn = useCallback(() => {
    (svgRef.current as any)?.controls?.zoomIn();
  }, []);

  const handleZoomOut = useCallback(() => {
    (svgRef.current as any)?.controls?.zoomOut();
  }, []);

  const handleResetView = useCallback(() => {
    (svgRef.current as any)?.controls?.resetView();
  }, []);

  const handleRestartSimulation = useCallback(() => {
    (svgRef.current as any)?.controls?.restartSimulation();
  }, []);

  const containerStyle = {
    height: '100%',
    display: 'flex',
    flexDirection: 'column' as const,
    backgroundColor: '#f8fafc',
    borderRadius: '8px',
    overflow: 'hidden' as const,
    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
    border: '1px solid rgba(148, 163, 184, 0.2)',
  };

  return (
    <div style={containerStyle}>
      {/* Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '16px',
          borderBottom: '1px solid #e2e8f0',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <GraphIcon sx={{ color: '#3b82f6' }} />
          <Typography variant="h6" sx={{ fontWeight: 600, color: '#1e293b' }}>
            Spatial Relationship Graph
          </Typography>
          <Chip
            label={`${relationships.length} relations`}
            size="small"
            sx={{
              backgroundColor: '#dbeafe',
              color: '#1e40af',
              fontWeight: 600
            }}
          />
        </div>

        {/* Controls */}
        <ButtonGroup size="small" variant="contained">
          <Button
            onClick={handleZoomIn}
            sx={{
              backgroundColor: '#374151',
              color: 'white',
              '&:hover': { backgroundColor: '#1f2937' }
            }}
          >
            Zoom In
          </Button>
          <Button
            onClick={handleZoomOut}
            sx={{
              backgroundColor: '#374151',
              color: 'white',
              '&:hover': { backgroundColor: '#1f2937' }
            }}
          >
            Zoom Out
          </Button>
          <Button
            onClick={handleResetView}
            sx={{
              backgroundColor: '#374151',
              color: 'white',
              '&:hover': { backgroundColor: '#1f2937' }
            }}
          >
            Reset
          </Button>
          <Button
            onClick={handleRestartSimulation}
            sx={{
              backgroundColor: '#374151',
              color: 'white',
              '&:hover': { backgroundColor: '#1f2937' }
            }}
          >
            Restart
          </Button>
        </ButtonGroup>
      </div>

      {/* SVG Container */}
      <div style={{ flex: 1, position: 'relative' }}>
        <svg
          ref={svgRef}
          width="100%"
          height="100%"
          style={{
            display: 'block',
            background: 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)'
          }}
        />

        {graphData.nodes.length === 0 && (
          <div
            style={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              textAlign: 'center',
              color: '#64748b'
            }}
          >
            <GraphIcon sx={{ fontSize: 48, mb: 2, opacity: 0.5 }} />
            <Typography variant="body1">No spatial relationships to display</Typography>
            <Typography variant="body2">Add objects to see their connections</Typography>
          </div>
        )}
      </div>
    </div>
  );
}