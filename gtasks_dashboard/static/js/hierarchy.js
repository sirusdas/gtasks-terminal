/**
 * Hierarchy Visualization Module
 * Main entry point that coordinates all hierarchy sub-modules
 */

console.log('[Hierarchy] Module starting to load...');

// Import from sub-modules (ES6 modules)
import { renderHierarchy, initHierarchy, updateHierarchyVisualization } from './hierarchy-renderer.js';
import { 
    showNodeTooltip, hideNodeTooltip, 
    showLabelTooltip, hideLabelTooltip, 
    handleNodeClick, highlightSelectedNode,
    showTaskPanel, closeTaskPanel,
    getSelectedNode, setSelectedNode
} from './hierarchy-interactions.js';
import { 
    loadNodeTasks, displayNodeTasks, filterNodeTasks 
} from './hierarchy-task-panel.js';
import { 
    initHierarchyFilters, clearHierarchyFilters, 
    refreshHierarchyVisualization, hierarchyFilters,
    filterHierarchyByTags, filterHierarchyByDate, filterHierarchyByStatus
} from './hierarchy-filters.js';
import { 
    renderLedger, updateLedgerWithFilters,
    clearLedgerSelection, highlightLedgerNode, initLedgerView
} from './hierarchy-ledger.js';

console.log('[Hierarchy] All imports resolved successfully');

// Global state
let hierarchyData = {};

/**
 * Load hierarchy data from API
 */
async function loadHierarchy() {
    try {
        const response = await fetch('/api/hierarchy');
        hierarchyData = await response.json();
        renderHierarchy(hierarchyData);
        
        // Also render the ledger
        if (typeof renderLedger === 'function') {
            renderLedger(hierarchyData);
        }
        
        // Initialize ledger view based on saved preference
        if (typeof initLedgerView === 'function') {
            setTimeout(initLedgerView, 100);
        }
        
        // Initialize filter event listeners
        initHierarchyFilters();
        
        console.log('Hierarchy loaded successfully');
    } catch (error) {
        console.error('Error loading hierarchy:', error);
    }
}

/**
 * Set hierarchy data (for external use)
 */
function setHierarchyData(data) {
    hierarchyData = data;
    window.hierarchyData = data;  // Also set on window for renderer access
}

/**
 * Get hierarchy data
 */
function getHierarchyData() {
    return hierarchyData;
}

// Auto-center visualization
window.centerVisualizationOnce = function () {
    const svg = d3.select('#hierarchy-viz');
    const g = svg.select('g');
    if (svg.empty() || g.empty()) return;

    setTimeout(() => {
        try {
            const bounds = g.node().getBBox();
            if (bounds.width === 0 || bounds.height === 0) return;

            const fullWidth = svg.node().clientWidth || 800;
            const fullHeight = svg.node().clientHeight || 500;

            const width = bounds.width;
            const height = bounds.height;
            const midX = bounds.x + width / 2;
            const midY = bounds.y + height / 2;

            if (width === 0 || height === 0) return;

            const scale = 0.85 / Math.max(width / fullWidth, height / fullHeight);
            const translate = [
                fullWidth / 2 - scale * midX,
                fullHeight / 2 - scale * midY
            ];

            svg.transition()
                .duration(750)
                .call(window.hierarchyZoomRef.transform,
                    d3.zoomIdentity.translate(translate[0], translate[1]).scale(scale));

            console.log('Auto-centered visualization');
        } catch (e) {
            console.warn('Failed to center visualization:', e);
        }
    }, 500);
};

// Export functions globally for backward compatibility
window.renderHierarchy = renderHierarchy;
window.closeTaskPanelHierarchy = closeTaskPanel;
window.initHierarchyFilters = initHierarchyFilters;
window.clearHierarchyFilters = clearHierarchyFilters;
window.refreshHierarchyVisualization = refreshHierarchyVisualization;
window.applyChartFilters = refreshHierarchyVisualization;  // Alias for Apply button
window.updateHierarchyVisualization = updateHierarchyVisualization;  // Export for filters module
window.selectedNode = null;
window.loadNodeTasksHierarchy = loadNodeTasks;
window.filterNodeTasksHierarchy = filterNodeTasks;

// Wrap updateHierarchyVisualization to also update the ledger
const originalUpdateHierarchyVisualization = updateHierarchyVisualization;
window.updateHierarchyVisualization = function(hierarchyData) {
    console.log('[Hierarchy] Wrapped updateHierarchyVisualization called');
    
    // Update the graph
    if (typeof originalUpdateHierarchyVisualization === 'function') {
        originalUpdateHierarchyVisualization(hierarchyData);
    }
    
    // Also update the ledger with filtered data
    if (typeof window.updateLedgerWithFilters === 'function') {
        console.log('[Hierarchy] Updating ledger with filtered data');
        window.updateLedgerWithFilters(hierarchyData);
    }
};

// Re-export for ES6 module imports
export {
    renderHierarchy,
    initHierarchy,
    updateHierarchyVisualization,
    closeTaskPanel,
    initHierarchyFilters,
    clearHierarchyFilters,
    refreshHierarchyVisualization,
    loadNodeTasks,
    filterNodeTasks,
    loadHierarchy,
    setHierarchyData,
    getHierarchyData,
    getSelectedNode,
    setSelectedNode,
    // Ledger exports
    renderLedger,
    updateLedgerWithFilters,
    clearLedgerSelection,
    highlightLedgerNode,
    initLedgerView
};

// Make functions available for dashboard.js
window.loadHierarchy = loadHierarchy;
window.setHierarchyData = setHierarchyData;
window.getHierarchyData = getHierarchyData;
window.showNodeTooltip = showNodeTooltip;
window.hideNodeTooltip = hideNodeTooltip;
window.showLabelTooltip = showLabelTooltip;
window.hideLabelTooltip = hideLabelTooltip;
window.handleNodeClick = handleNodeClick;
window.highlightSelectedNode = highlightSelectedNode;
window.showTaskPanel = showTaskPanel;
window.closeTaskPanel = closeTaskPanel;
window.getSelectedNode = getSelectedNode;
window.setSelectedNode = setSelectedNode;

// Add graph-to-ledger synchronization: when a graph node is clicked, highlight the ledger row
const originalHighlightSelectedNode = highlightSelectedNode;
window.highlightSelectedNode = function(node) {
    // Call original function
    if (typeof originalHighlightSelectedNode === 'function') {
        originalHighlightSelectedNode(node);
    }
    
    // Also highlight the corresponding ledger row
    if (node && typeof highlightLedgerNode === 'function') {
        highlightLedgerNode(node.id);
    }
};

// Additional ledger function exports (for redundancy)
window.renderLedger = renderLedger;
window.updateLedgerWithFilters = updateLedgerWithFilters;
window.clearLedgerSelection = clearLedgerSelection;
window.highlightLedgerNode = highlightLedgerNode;
window.initLedgerView = initLedgerView;
