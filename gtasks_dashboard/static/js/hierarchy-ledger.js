/**
 * Hierarchy Ledger Module
 * Handles tabular display of hierarchy nodes with click interactions
 * 
 * Features:
 * - Display hierarchy nodes in a tabular format
 * - Click to highlight corresponding graph node and show related tasks
 * - Sortable columns and search filtering
 * - Synchronized with D3 graph visualization
 */

// Console logging for debugging
console.log('[HierarchyLedger] 🔥 Module file is being executed!');

// State management
const ledgerState = {
    data: [],
    selectedNode: null,
    sortColumn: 'name',
    sortDirection: 'asc',
    searchQuery: '',
    currentView: 'graph' // 'graph', 'ledger', or 'both'
};

/**
 * Main render function - generates ledger table from hierarchy data
 * @param {Object} hierarchyData - Object containing nodes and links arrays
 */
export function renderLedger(hierarchyData) {
    console.log('[HierarchyLedger] renderLedger called with data:', hierarchyData);
    
    if (!hierarchyData || !hierarchyData.nodes) {
        console.warn('[HierarchyLedger] No nodes data provided');
        return;
    }
    
    ledgerState.data = hierarchyData.nodes;
    
    const container = document.getElementById('ledger-panel');
    if (!container) {
        console.error('[HierarchyLedger] Ledger panel container not found');
        return;
    }
    
    console.log('[HierarchyLedger] Rendering ledger with', ledgerState.data.length, 'nodes');
    
    // Apply filters and sorting
    let filteredData = filterLedgerData(ledgerState.data);
    filteredData = sortLedgerData(filteredData);
    
    // Generate table HTML
    container.innerHTML = generateLedgerTable(filteredData);
    
    // Setup event listeners
    setupLedgerEventListeners();
    
    console.log('[HierarchyLedger] Ledger rendering complete');
}

/**
 * Generate the complete ledger table HTML
 */
function generateLedgerTable(data) {
    // Always show the header with search bar
    const headerHtml = `
        <div class="ledger-header">
            <div class="ledger-title">Hierarchy Ledger</div>
            <div style="display: flex; gap: 12px; align-items: center; flex-wrap: wrap;">
                <input type="text" id="ledger-search" class="ledger-search" 
                       placeholder="Search nodes..." value="${escapeHtml(ledgerState.searchQuery)}">
                <div class="ledger-view-toggle">
                    <button class="ledger-view-btn ${ledgerState.currentView === 'graph' ? 'active' : ''}" 
                            data-view="graph" title="Graph View">📊</button>
                    <button class="ledger-view-btn ${ledgerState.currentView === 'both' ? 'active' : ''}" 
                            data-view="both" title="Both Views">🔀</button>
                    <button class="ledger-view-btn ${ledgerState.currentView === 'ledger' ? 'active' : ''}" 
                            data-view="ledger" title="Ledger View">📋</button>
                </div>
            </div>
        </div>
    `;
    
    if (!data || data.length === 0) {
        return headerHtml + `
            <div class="ledger-empty">
                <div class="ledger-empty-icon">📋</div>
                <p class="ledger-empty-text">
                    ${ledgerState.searchQuery ? 'No nodes match your search.' : 'No nodes to display. Load hierarchy data first.'}
                </p>
            </div>
        `;
    }
    
    const rows = data.map(node => generateLedgerRow(node)).join('');
    const sortIcon = ledgerState.sortDirection === 'asc' ? '▲' : '▼';
    
    return headerHtml + `
        <div class="ledger-scroll-container">
            <table class="ledger-table">
                <thead>
                    <tr>
                        <th class="ledger-th ${ledgerState.sortColumn === 'name' ? 'sorted ' + ledgerState.sortDirection : ''}" 
                            data-sort="name">Name<span class="sort-icon"></span></th>
                        <th class="ledger-th ${ledgerState.sortColumn === 'type' ? 'sorted ' + ledgerState.sortDirection : ''}" 
                            data-sort="type">Type<span class="sort-icon"></span></th>
                        <th class="ledger-th ${ledgerState.sortColumn === 'priority' ? 'sorted ' + ledgerState.sortDirection : ''}" 
                            data-sort="priority">Priority<span class="sort-icon"></span></th>
                        <th class="ledger-th ${ledgerState.sortColumn === 'count' ? 'sorted ' + ledgerState.sortDirection : ''}" 
                            data-sort="count">Tasks<span class="sort-icon"></span></th>
                        <th class="ledger-th ${ledgerState.sortColumn === 'status' ? 'sorted ' + ledgerState.sortDirection : ''}" 
                            data-sort="status">Status<span class="sort-icon"></span></th>
                    </tr>
                </thead>
                <tbody id="ledger-tbody">
                    ${rows}
                </tbody>
            </table>
        </div>
        <div class="ledger-footer">
            <div class="ledger-info">
                <span><strong>${data.length}</strong> nodes</span>
                <span>${ledgerState.searchQuery ? 'filtered' : 'showing all'}</span>
            </div>
            <div>
                Click row to view details
            </div>
        </div>
    `;
}

/**
 * Generate HTML for a single ledger row
 */
function generateLedgerRow(node) {
    // Type badge
    const typeClass = node.type || 'meta';
    const typeLabel = capitalizeFirst(node.type || 'meta');
    
    // Priority display
    const priorityCell = node.priority ? `
        <div class="priority-cell">
            <span class="priority-dot ${node.priority}"></span>
            ${capitalizeFirst(node.priority)}
        </div>
    ` : '<span style="color: #9ca3af;">—</span>';
    
    // Task count
    const taskCount = node.val || 0;
    
    // Status pills (placeholder - would need task data)
    const statusHtml = `
        <div class="status-cell">
            <span class="status-pill pending">${taskCount} pending</span>
        </div>
    `;
    
    // Check if this row is selected
    const isSelected = ledgerState.selectedNode && ledgerState.selectedNode.id === node.id;
    const selectedClass = isSelected ? 'selected' : '';
    
    // Node name with ID
    const nameHtml = `
        <div class="name-cell">
            ${escapeHtml(node.name || node.id)}
            <span class="node-id">${escapeHtml(node.id)}</span>
        </div>
    `;
    
    return `
        <tr class="ledger-row ${selectedClass}" data-node-id="${node.id}">
            <td class="ledger-td">${nameHtml}</td>
            <td class="ledger-td"><span class="type-badge ${typeClass}">${typeLabel}</span></td>
            <td class="ledger-td">${priorityCell}</td>
            <td class="ledger-td"><span class="task-count">${taskCount}</span></td>
            <td class="ledger-td">${statusHtml}</td>
        </tr>
    `;
}

/**
 * Setup all event listeners for the ledger
 */
function setupLedgerEventListeners() {
    // Search input
    const searchInput = document.getElementById('ledger-search');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(function() {
            // Save cursor position and value before re-render
            const selectionStart = this.selectionStart;
            const selectionEnd = this.selectionEnd;
            const currentValue = this.value;
            
            ledgerState.searchQuery = currentValue.trim();
            console.log('[HierarchyLedger] Search query:', ledgerState.searchQuery);
            renderLedger({ nodes: ledgerState.data });
            
            // Restore focus and cursor position after re-render
            setTimeout(() => {
                const newInput = document.getElementById('ledger-search');
                if (newInput) {
                    newInput.focus();
                    newInput.setSelectionRange(selectionStart, selectionEnd);
                }
            }, 0);
        }, 300));
    }
    
    // Column sorting
    document.querySelectorAll('.ledger-th').forEach(th => {
        th.addEventListener('click', function() {
            const column = this.dataset.sort;
            if (ledgerState.sortColumn === column) {
                ledgerState.sortDirection = ledgerState.sortDirection === 'asc' ? 'desc' : 'asc';
            } else {
                ledgerState.sortColumn = column;
                ledgerState.sortDirection = 'asc';
            }
            console.log('[HierarchyLedger] Sorting by', column, 'direction:', ledgerState.sortDirection);
            renderLedger({ nodes: ledgerState.data });
        });
    });
    
    // Row clicks
    document.querySelectorAll('.ledger-row').forEach(row => {
        row.addEventListener('click', function() {
            const nodeId = this.dataset.nodeId;
            const node = ledgerState.data.find(n => n.id === nodeId);
            if (node) {
                handleLedgerClick(node, this);
            }
        });
    });
    
    // View toggle buttons
    document.querySelectorAll('.ledger-view-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const view = this.dataset.view;
            if (view) {
                switchHierarchyView(view);
            }
        });
    });
    
    console.log('[HierarchyLedger] Event listeners setup complete');
}

/**
 * Handle ledger row click
 */
function handleLedgerClick(node, rowElement) {
    console.log('[HierarchyLedger] Row clicked:', node);
    ledgerState.selectedNode = node;
    
    // Update row selection
    document.querySelectorAll('.ledger-row').forEach(r => {
        r.classList.remove('selected');
    });
    if (rowElement) {
        rowElement.classList.add('selected');
        // Add flash animation
        rowElement.classList.add('flash');
        setTimeout(() => rowElement.classList.remove('flash'), 300);
    }
    
    // Highlight corresponding graph node
    if (typeof window.highlightSelectedNode === 'function') {
        console.log('[HierarchyLedger] Highlighting graph node:', node.id);
        window.highlightSelectedNode(node);
    }
    
    // Use the existing task panel (same as graph node click)
    if (typeof window.showTaskPanel === 'function') {
        window.showTaskPanel(node);
    }
    
    // Also load tasks using the existing function
    if (typeof window.loadNodeTasksHierarchy === 'function') {
        window.loadNodeTasksHierarchy(node);
    }
}

/**
 * Filter ledger data based on search query
 */
function filterLedgerData(data) {
    if (!ledgerState.searchQuery) return data;
    
    const query = ledgerState.searchQuery.toLowerCase();
    return data.filter(node => {
        const searchableText = [
            node.name || '',
            node.id || '',
            node.type || '',
            node.priority || ''
        ].join(' ').toLowerCase();
        
        return searchableText.includes(query);
    });
}

/**
 * Sort ledger data by current sort column and direction
 */
function sortLedgerData(data) {
    return [...data].sort((a, b) => {
        let aVal = a[ledgerState.sortColumn];
        let bVal = b[ledgerState.sortColumn];
        
        // Handle different column types
        if (ledgerState.sortColumn === 'name' || ledgerState.sortColumn === 'type') {
            aVal = (aVal || '').toString().toLowerCase();
            bVal = (bVal || '').toString().toLowerCase();
        } else if (ledgerState.sortColumn === 'count') {
            aVal = a.val || 0;
            bVal = b.val || 0;
        } else if (ledgerState.sortColumn === 'priority') {
            // Convert priority to numeric for sorting
            const priorityOrder = { 'critical': 0, 'high': 1, 'medium': 2, 'low': 3 };
            aVal = priorityOrder[a.priority] ?? 99;
            bVal = priorityOrder[b.priority] ?? 99;
        }
        
        // Compare values
        let comparison = 0;
        if (aVal < bVal) comparison = -1;
        if (aVal > bVal) comparison = 1;
        
        return ledgerState.sortDirection === 'asc' ? comparison : -comparison;
    });
}

/**
 * Update ledger when hierarchy filters change
 */
export function updateLedgerWithFilters(hierarchyData) {
    console.log('[HierarchyLedger] Updating with filtered data');
    if (hierarchyData && hierarchyData.nodes) {
        ledgerState.data = hierarchyData.nodes;
        renderLedger({ nodes: ledgerState.data });
    }
}

/**
 * Clear ledger selection and close tasks panel
 */
export function clearLedgerSelection() {
    if (typeof window.closeTaskPanelHierarchy === 'function') {
        window.closeTaskPanelHierarchy();
    }
}

/**
 * Switch between graph, ledger, or both views
 */
function switchHierarchyView(view) {
    console.log('[HierarchyLedger] Switching to view:', view);
    ledgerState.currentView = view;
    
    const ledgerPanel = document.getElementById('ledger-panel');
    const vizContainer = document.getElementById('hierarchy-viz-container');
    
    if (!ledgerPanel || !vizContainer) {
        console.warn('[HierarchyLedger] Required containers not found');
        return;
    }
    
    // Use global hierarchyData if available, otherwise use ledgerState.data
    let dataToRender = { nodes: ledgerState.data };
    if (window.hierarchyData && window.hierarchyData.nodes && window.hierarchyData.nodes.length > 0) {
        dataToRender = window.hierarchyData;
        ledgerState.data = window.hierarchyData.nodes;
    }
    
    // Update visibility based on view
    switch(view) {
        case 'graph':
            ledgerPanel.style.display = 'none';
            vizContainer.style.display = 'block';
            break;
        case 'ledger':
            ledgerPanel.style.display = 'block';
            vizContainer.style.display = 'none';
            // Re-render ledger with available data
            if (dataToRender.nodes && dataToRender.nodes.length > 0) {
                renderLedger(dataToRender);
            }
            break;
        case 'both':
            ledgerPanel.style.display = 'block';
            vizContainer.style.display = 'block';
            // Re-render ledger with available data
            if (dataToRender.nodes && dataToRender.nodes.length > 0) {
                renderLedger(dataToRender);
            }
            break;
    }
    
    // Update view toggle buttons in the header
    const headerViewBtns = document.querySelectorAll('#hierarchy-view-toggle .view-btn');
    headerViewBtns.forEach(btn => {
        btn.classList.remove('active');
        btn.style.background = 'transparent';
        btn.style.color = '#6b7280';
        if (btn.dataset.view === view) {
            btn.classList.add('active');
            btn.style.background = '#3b82f6';
            btn.style.color = 'white';
        }
    });
    
    // Update view toggle buttons in ledger header (if visible)
    const ledgerViewBtns = document.querySelectorAll('.ledger-view-btn');
    ledgerViewBtns.forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.view === view) {
            btn.classList.add('active');
        }
    });
    
    // Save preference to localStorage
    try {
        localStorage.setItem('hierarchyView', view);
    } catch (e) {
        console.warn('[HierarchyLedger] Could not save view preference:', e);
    }
}

/**
 * Initialize ledger with saved view preference
 */
export function initLedgerView() {
    console.log('[HierarchyLedger] initLedgerView called');
    
    // Wait for hierarchy data to be available
    const waitForData = () => {
        const savedView = localStorage.getItem('hierarchyView') || 'graph';
        
        // Check if data is available
        if (window.hierarchyData && window.hierarchyData.nodes && window.hierarchyData.nodes.length > 0) {
            console.log('[HierarchyLedger] Data available, switching to view:', savedView);
            ledgerState.data = window.hierarchyData.nodes;
            switchHierarchyView(savedView);
        } else if (ledgerState.data && ledgerState.data.length > 0) {
            console.log('[HierarchyLedger] Using ledgerState.data, switching to view:', savedView);
            switchHierarchyView(savedView);
        } else {
            // Data not yet available, wait a bit and try again
            console.log('[HierarchyLedger] Waiting for data...');
            setTimeout(waitForData, 100);
        }
    };
    
    // Start waiting for data
    setTimeout(waitForData, 50);
}

/**
 * Highlight ledger row for corresponding graph node
 */
export function highlightLedgerNode(nodeId) {
    const row = document.querySelector(`.ledger-row[data-node-id="${nodeId}"]`);
    if (row) {
        // Remove previous selection
        document.querySelectorAll('.ledger-row').forEach(r => {
            r.classList.remove('selected');
        });
        
        // Add selection to this row
        row.classList.add('selected');
        
        // Scroll row into view if in ledger view
        if (ledgerState.currentView !== 'graph') {
            row.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
        
        console.log('[HierarchyLedger] Highlighted row for node:', nodeId);
    }
}

/**
 * Utility: Debounce function for search input
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func.apply(this, args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Utility: Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Utility: Capitalize first letter
 */
function capitalizeFirst(str) {
    if (!str) return '';
    return str.charAt(0).toUpperCase() + str.slice(1);
}

// Export functions for global use (backward compatibility)
window.renderLedger = renderLedger;
window.updateLedgerWithFilters = updateLedgerWithFilters;
window.clearLedgerSelection = clearLedgerSelection;
window.initLedgerView = initLedgerView;
window.highlightLedgerNode = highlightLedgerNode;
window.switchHierarchyView = switchHierarchyView;
window.ledgerState = ledgerState;

console.log('[HierarchyLedger] ✅ Module initialization complete');
