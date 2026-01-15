/**
 * Hierarchy Renderer Module
 * Handles D3.js visualization rendering
 */

// IMMEDIATE EXECUTION TEST
console.log('[HierarchyRenderer] 🔥 Module file is being executed!');
console.log('[HierarchyRenderer] Checking d3 availability:', typeof d3);

// Check if d3 is available
if (typeof d3 === 'undefined') {
    console.error('[HierarchyRenderer] ❌ D3 is not loaded! hierarchy-renderer.js cannot execute without D3.');
    throw new Error('D3.js is required but not loaded');
}

console.log('[HierarchyRenderer] D3 is available, proceeding with module execution...');

// Import tooltip and interaction functions from interactions module
import { 
    showNodeTooltip, 
    hideNodeTooltip, 
    showLabelTooltip, 
    hideLabelTooltip, 
    handleNodeClick 
} from './hierarchy-interactions.js';

console.log('[HierarchyRenderer] ✅ Imports from hierarchy-interactions.js resolved successfully');

// State (imported from hierarchy module)
// Don't create local hierarchyData - use the one from hierarchy.js via window
let simulation = null;

/**
 * Render hierarchy visualization
 * @param {Object} data - Hierarchy data with nodes and links
 */
export function renderHierarchy(data) {
    console.log('[HierarchyRenderer] renderHierarchy called with data:', data);
    window.hierarchyData = data;
    initHierarchy();
}

export function initHierarchy() {
    console.log('[HierarchyRenderer] initHierarchy called');
    const svg = d3.select('#hierarchy-viz');
    console.log('[HierarchyRenderer] SVG element found:', !svg.empty());
    console.log('[HierarchyRenderer] SVG node:', svg.node());
    
    if (svg.empty()) {
        console.error('[HierarchyRenderer] SVG element not found!');
        return;
    }
    
    // Check SVG dimensions
    const svgNode = svg.node();
    console.log('[HierarchyRenderer] SVG clientWidth:', svgNode.clientWidth);
    console.log('[HierarchyRenderer] SVG clientHeight:', svgNode.clientHeight);
    console.log('[HierarchyRenderer] SVG offsetWidth:', svgNode.offsetWidth);
    console.log('[HierarchyRenderer] SVG offsetHeight:', svgNode.offsetHeight);
    console.log('[HierarchyRenderer] SVG getBoundingClientRect:', svgNode.getBoundingClientRect());

    // Clear existing SVG content properly
    while (svg.node().firstChild) {
        svg.node().removeChild(svg.node().firstChild);
    }

    // Safety check: if window.hierarchyData is undefined, wait for it
    if (!window.hierarchyData) {
        console.log('[HierarchyRenderer] window.hierarchyData is undefined, waiting...')
        svg.append('text')
            .attr('x', '50%')
            .attr('y', '50%')
            .attr('text-anchor', 'middle')
            .attr('fill', '#6b7280')
            .text('Loading hierarchy data...');
        
        // Wait up to 2 seconds for data
        let waitCount = 0;
        const waitInterval = setInterval(() => {
            waitCount++;
            if (window.hierarchyData) {
                clearInterval(waitInterval);
                initHierarchy();
            } else if (waitCount >= 20) {
                clearInterval(waitInterval);
                console.error('[HierarchyRenderer] window.hierarchyData never arrived after 2 seconds');
            }
        }, 100);
        return;
    }

    if (!window.hierarchyData.nodes || window.hierarchyData.nodes.length === 0) {
        console.log('[HierarchyRenderer] No nodes in data, showing empty message');
        svg.append('text')
            .attr('x', '50%')
            .attr('y', '50%')
            .attr('text-anchor', 'middle')
            .attr('fill', '#6b7280')
            .text('No hierarchy data available. Load tasks first.');
        return;
    }

    console.log('[HierarchyRenderer] Rendering', window.hierarchyData.nodes.length, 'nodes and', window.hierarchyData.links.length, 'links');
    
    const width = svg.node().clientWidth || 800;
    const height = svg.node().clientHeight || 500;
    console.log('[HierarchyRenderer] SVG dimensions:', width, 'x', height);

    const g = svg.append('g');

    const zoom = d3.zoom()
        .scaleExtent([0.1, 10])
        .on('zoom', (event) => {
            g.attr('transform', event.transform);
        });

    window.hierarchyZoom = zoom;
    svg.call(zoom);

    window.hierarchySvg = svg;
    window.hierarchyG = g;
    window.hierarchyZoomRef = zoom;

    // Create links
    const link = g.append('g')
        .attr('class', 'links')
        .selectAll('line')
        .data(window.hierarchyData.links || [])
        .enter()
        .append('line')
        .attr('stroke', '#d1d5db')
        .attr('stroke-opacity', 0.7)
        .attr('stroke-width', d => Math.max(1, Math.sqrt(d.value || 1)));

    // Create nodes
    const node = g.append('g')
        .attr('class', 'nodes')
        .selectAll('circle')
        .data(window.hierarchyData.nodes || [])
        .enter()
        .append('circle')
        .attr('r', d => {
            const baseSize = Math.max(8, Math.min(25, d.val || 10));
            return d.level === 0 ? baseSize * 1.2 : baseSize;
        })
        .attr('fill', d => getNodeColor(d))
        .attr('stroke', '#fff')
        .attr('stroke-width', 2)
        .style('cursor', 'pointer')
        .style('filter', 'drop-shadow(0 2px 4px rgba(0,0,0,0.1))')
        .on('mouseover', function (event, d) {
            d3.select(this)
                .transition()
                .duration(150)
                .attr('r', (d.val || 10) * 1.2);
            showNodeTooltip(event, d);
        })
        .on('mouseout', function (event, d) {
            d3.select(this)
                .transition()
                .duration(150)
                .attr('r', d => {
                    const baseSize = Math.max(8, Math.min(25, d.val || 10));
                    return d.level === 0 ? baseSize * 1.2 : baseSize;
                });
            hideNodeTooltip();
        })
        .on('click', function (event, d) {
            event.stopPropagation();
            handleNodeClick(d);
        });

    // Add labels for level 0 and 1 nodes
    const labels = g.append('g')
        .attr('class', 'labels')
        .selectAll('text')
        .data(window.hierarchyData.nodes.filter(d => d.level <= 1) || [])
        .enter()
        .append('text')
        .attr('dy', d => (d.val || 10) + 15)
        .attr('text-anchor', 'middle')
        .attr('font-size', '11px')
        .attr('fill', '#374151')
        .attr('font-weight', '500')
        .style('cursor', 'pointer')
        .text(d => truncateText(d.name, 5))
        .each(function(d) {
            d3.select(this)
                .attr('data-full-name', d.name)
                .on('mouseover', function(event) {
                    showLabelTooltip(event, d.name);
                })
                .on('mouseout', hideLabelTooltip);
        });

    // Initialize force simulation
    simulation = d3.forceSimulation(window.hierarchyData.nodes)
        .force('link', d3.forceLink(window.hierarchyData.links)
            .id(d => d.id)
            .distance(d => {
                const sourceLevel = window.hierarchyData.nodes.find(n => n.id === d.source)?.level || 0;
                const targetLevel = window.hierarchyData.nodes.find(n => n.id === d.target)?.level || 0;
                return Math.max(60, (sourceLevel + targetLevel) * 30);
            }))
        .force('charge', d3.forceManyBody().strength(d => {
            if (d.level === 0) return -400;
            if (d.level === 1) return -200;
            return -100;
        }))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide().radius(d => (d.val || 10) + 10))
        .on('tick', () => {
            link
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);
            node
                .attr('cx', d => d.x)
                .attr('cy', d => d.y);
            labels
                .attr('x', d => d.x)
                .attr('y', d => d.y);
        });

    // Drag behavior
    node.call(d3.drag()
        .on('start', dragstarted)
        .on('drag', dragged)
        .on('end', dragended));

    window.hierarchySvg = svg;
    window.hierarchyG = g;
    window.hierarchyZoomRef = zoom;
    window.hierarchyZoom = zoom;

    console.log('[HierarchyRenderer] Visualization created successfully');
    
    // Auto-center the visualization
    if (typeof window.centerVisualizationOnce === 'function') {
        window.centerVisualizationOnce();
    }
}

// Drag functions
function dragstarted(event, d) {
    if (!event.active) simulation.alphaTarget(0.3).restart();
    d.fx = d.x;
    d.fy = d.y;
}

function dragged(event, d) {
    d.fx = event.x;
    d.fy = event.y;
}

function dragended(event, d) {
    if (!event.active) simulation.alphaTarget(0);
    d.fx = null;
    d.fy = null;
}

// Color scale
const colorScale = {
    'meta': '#8b5cf6',
    'priority': {
        'critical': '#ef4444',
        'high': '#f97316',
        'medium': '#eab308',
        'low': '#6b7280'
    },
    'category': '#3b82f6',
    'tag': '#10b981',
    'account': '#8b5cf6'
};

function getNodeColor(node) {
    if (node.type === 'priority' && node.priority) {
        return colorScale.priority[node.priority] || colorScale.priority.medium;
    }
    return colorScale[node.type] || '#6b7280';
}

// Text truncation
function truncateText(text, maxLength) {
    if (!text) return '';
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

// Update visualization with new data
export function updateHierarchyVisualization() {
    console.log('[HierarchyRenderer] updateHierarchyVisualization called');
    const svg = d3.select('#hierarchy-viz');
    console.log('[HierarchyRenderer] updateHierarchyVisualization - SVG found:', !svg.empty());
    if (svg.empty()) {
        console.error('[HierarchyRenderer] SVG element not found in updateHierarchyVisualization!');
        return;
    }
    
    const g = svg.select('g');
    console.log('[HierarchyRenderer] updateHierarchyVisualization - G element found:', !g.empty());
    if (g.empty()) {
        console.log('[HierarchyRenderer] No G element found, calling initHierarchy instead');
        initHierarchy();
        return;
    }
    
    g.selectAll('*').remove();
    
    if (!window.hierarchyData.nodes || window.hierarchyData.nodes.length === 0) {
        g.append('text')
            .attr('x', '50%')
            .attr('y', '50%')
            .attr('text-anchor', 'middle')
            .attr('fill', '#6b7280')
            .text('No matching hierarchy data.');
        return;
    }
    
    const width = svg.node().clientWidth || 800;
    const height = svg.node().clientHeight || 500;
    
    // Create links
    const link = g.append('g')
        .attr('class', 'links')
        .selectAll('line')
        .data(window.hierarchyData.links || [])
        .enter()
        .append('line')
        .attr('stroke', '#d1d5db')
        .attr('stroke-opacity', 0.7)
        .attr('stroke-width', d => Math.max(1, Math.sqrt(d.value || 1)));
    
    // Create nodes
    const node = g.append('g')
        .attr('class', 'nodes')
        .selectAll('circle')
        .data(window.hierarchyData.nodes || [])
        .enter()
        .append('circle')
        .attr('r', d => {
            const baseSize = Math.max(8, Math.min(25, d.val || 10));
            return d.level === 0 ? baseSize * 1.2 : baseSize;
        })
        .attr('fill', d => getNodeColor(d))
        .attr('stroke', '#fff')
        .attr('stroke-width', 2)
        .style('cursor', 'pointer')
        .style('filter', 'drop-shadow(0 2px 4px rgba(0,0,0,0.1))')
        .on('mouseover', function (event, d) {
            d3.select(this)
                .transition()
                .duration(150)
                .attr('r', (d.val || 10) * 1.2);
            showNodeTooltip(event, d);
        })
        .on('mouseout', function (event, d) {
            d3.select(this)
                .transition()
                .duration(150)
                .attr('r', d => {
                    const baseSize = Math.max(8, Math.min(25, d.val || 10));
                    return d.level === 0 ? baseSize * 1.2 : baseSize;
                });
            hideNodeTooltip();
        })
        .on('click', function (event, d) {
            event.stopPropagation();
            handleNodeClick(d);
        });
    
    // Add labels
    const labels = g.append('g')
        .attr('class', 'labels')
        .selectAll('text')
        .data(window.hierarchyData.nodes.filter(d => d.level <= 1) || [])
        .enter()
        .append('text')
        .attr('dy', d => (d.val || 10) + 15)
        .attr('text-anchor', 'middle')
        .attr('font-size', '11px')
        .attr('fill', '#374151')
        .attr('font-weight', '500')
        .style('cursor', 'pointer')
        .text(d => truncateText(d.name, 5))
        .each(function(d) {
            d3.select(this)
                .attr('data-full-name', d.name)
                .on('mouseover', function(event) {
                    showLabelTooltip(event, d.name);
                })
                .on('mouseout', hideLabelTooltip);
        });
    
    // Restart simulation
    simulation = d3.forceSimulation(window.hierarchyData.nodes)
        .force('link', d3.forceLink(window.hierarchyData.links)
            .id(d => d.id)
            .distance(d => {
                const sourceLevel = window.hierarchyData.nodes.find(n => n.id === d.source)?.level || 0;
                const targetLevel = window.hierarchyData.nodes.find(n => n.id === d.target)?.level || 0;
                return Math.max(60, (sourceLevel + targetLevel) * 30);
            }))
        .force('charge', d3.forceManyBody().strength(d => {
            if (d.level === 0) return -400;
            if (d.level === 1) return -200;
            return -100;
        }))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide().radius(d => (d.val || 10) + 10))
        .on('tick', () => {
            link
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);
            node
                .attr('cx', d => d.x)
                .attr('cy', d => d.y);
            labels
                .attr('x', d => d.x)
                .attr('y', d => d.y);
        });
    
    node.call(d3.drag()
        .on('start', dragstarted)
        .on('drag', dragged)
        .on('end', dragended));
}

// Re-export for backward compatibility
// All functions are already exported above, no duplicate exports needed
