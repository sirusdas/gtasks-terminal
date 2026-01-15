/**
 * Hierarchy Interactions Module
 * Handles node clicks, tooltips, drag, and user interactions
 */

// IMMEDIATE EXECUTION TEST
console.log('[HierarchyInteractions] 🔥 Module file is being executed!');
console.log('[HierarchyInteractions] Checking d3 availability:', typeof d3);

// Check if d3 is available
if (typeof d3 === 'undefined') {
    console.error('[HierarchyInteractions] ❌ D3 is not loaded! hierarchy-interactions.js cannot execute without D3.');
    throw new Error('D3.js is required but not loaded');
}

console.log('[HierarchyInteractions] D3 is available, proceeding with module execution...');

// State
let selectedNode = null;

/**
 * Show node tooltip
 */
export function showNodeTooltip(event, d) {
    let tooltip = document.getElementById('node-tooltip');
    if (!tooltip) {
        tooltip = document.createElement('div');
        tooltip.id = 'node-tooltip';
        tooltip.style.cssText = `
            position: fixed;
            background: rgba(0,0,0,0.8);
            color: white;
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 12px;
            pointer-events: none;
            z-index: 10000;
            max-width: 200px;
        `;
        document.body.appendChild(tooltip);
    }

    tooltip.innerHTML = `<strong>${d.name}</strong><br>Type: ${d.type}<br>Count: ${d.val}`;
    tooltip.style.left = (event.pageX + 10) + 'px';
    tooltip.style.top = (event.pageY + 10) + 'px';
    tooltip.style.display = 'block';
}

/**
 * Hide node tooltip
 */
export function hideNodeTooltip() {
    const tooltip = document.getElementById('node-tooltip');
    if (tooltip) {
        tooltip.style.display = 'none';
    }
}

/**
 * Show label tooltip for truncated text
 */
export function showLabelTooltip(event, fullText) {
    let tooltip = document.getElementById('label-tooltip');
    if (!tooltip) {
        tooltip = document.createElement('div');
        tooltip.id = 'label-tooltip';
        tooltip.style.cssText = `
            position: fixed;
            background: rgba(0,0,0,0.85);
            color: white;
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 12px;
            pointer-events: none;
            z-index: 10000;
            max-width: 200px;
            white-space: nowrap;
        `;
        document.body.appendChild(tooltip);
    }
    
    tooltip.textContent = fullText;
    tooltip.style.left = (event.pageX + 10) + 'px';
    tooltip.style.top = (event.pageY + 10) + 'px';
    tooltip.style.display = 'block';
}

/**
 * Hide label tooltip
 */
export function hideLabelTooltip() {
    const tooltip = document.getElementById('label-tooltip');
    if (tooltip) {
        tooltip.style.display = 'none';
    }
}

/**
 * Handle node click
 */
export function handleNodeClick(node) {
    console.log('Node clicked:', node);
    selectedNode = node;

    // Show task panel
    showTaskPanel(node);

    // Highlight selected node
    highlightSelectedNode(node);

    // Load related tasks
    if (typeof window.loadNodeTasksHierarchy === 'function') {
        window.loadNodeTasksHierarchy(node);
    }
}

/**
 * Highlight selected node
 */
export function highlightSelectedNode(node) {
    d3.selectAll('#hierarchy-viz circle').classed('selected', false);

    d3.selectAll('#hierarchy-viz circle')
        .filter(d => d.id === node.id)
        .classed('selected', true)
        .style('stroke', '#3b82f6')
        .style('stroke-width', 4)
        .style('filter', 'drop-shadow(0 0 8px rgba(59, 130, 246, 0.6))');
}

/**
 * Show task panel for node
 */
export function showTaskPanel(node) {
    const panel = document.getElementById('task-panel');
    const title = document.getElementById('selected-node-title');

    title.textContent = `Tasks for: ${node.name || node.id}`;
    panel.style.display = 'block';
    
    panel.style.maxHeight = '';
    panel.style.transition = '';
    panel.style.minHeight = '300vh';
    
    setTimeout(() => {
        panel.scrollIntoView({ 
            behavior: 'smooth', 
            block: 'start' 
        });
    }, 50);
}

/**
 * Close task panel
 */
export function closeTaskPanel() {
    const panel = document.getElementById('task-panel');
    panel.style.transition = 'max-height 0.3s ease';
    panel.style.maxHeight = '0';
    panel.style.overflow = 'hidden';

    setTimeout(() => {
        panel.style.display = 'none';
        panel.style.transition = '';
        panel.style.maxHeight = '';
        panel.style.overflow = '';
    }, 300);

    selectedNode = null;
    d3.selectAll('#hierarchy-viz circle').classed('selected', false)
        .style('stroke', '#fff')
        .style('stroke-width', 2)
        .style('filter', 'drop-shadow(0 2px 4px rgba(0,0,0,0.1))');
}

/**
 * Get selected node
 */
export function getSelectedNode() {
    return selectedNode;
}

/**
 * Set selected node (for external use)
 */
export function setSelectedNode(node) {
    selectedNode = node;
}
