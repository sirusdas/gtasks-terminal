# Hierarchical Task Visualization - Implementation Plan

## Overview

This document provides a detailed implementation plan for adding Hierarchical Task Visualization features to the GTasks Dashboard. The plan covers UI updates, JavaScript modifications, data flow changes, and testing approaches.

## Requirements Summary

| Feature | Description | Priority |
|---------|-------------|----------|
| Tag Search Filter | Search input with debounce and comma-separated terms | High |
| Date/Status Filters | Date range and status dropdown filters | High |
| Node Name Display Fix | Truncate to 5 chars with ellipsis, tooltip on hover | Medium |
| Fullscreen Filter Visibility | Floating panel, keyboard shortcut (Ctrl+F) | Medium |

---

## Phase 1: UI Structure Updates (`dashboard.html`)

### 1.1 Add Chart-Specific Filter Panel

**Location:** Lines 704-713 (after header, before viz-container)

**Current Code:**
```html
<!-- Visualization -->
<div class="viz-container" id="viz-container">
    <svg class="hierarchy-svg" id="hierarchy-viz"></svg>
    
    <!-- Fullscreen exit button -->
    <button class="fullscreen-exit" id="fullscreen-exit" onclick="toggleFullscreen()" style="display: none;">
        <i class="fas fa-times"></i>
    </button>
</div>
```

**New Code:**
```html
<!-- Chart Filter Panel -->
<div class="chart-filter-panel" id="chart-filter-panel">
    <div class="chart-filter-row">
        <!-- Tag Search Filter -->
        <div class="chart-filter-group">
            <label for="hierarchy-tag-search">
                <i class="fas fa-search"></i> Search Tags
            </label>
            <input type="text" id="hierarchy-tag-search" class="filter-input" 
                   placeholder="Search tags (3+ chars, comma separated)..." 
                   minlength="3">
        </div>
        
        <!-- Status Filter -->
        <div class="chart-filter-group">
            <label for="hierarchy-status-filter">
                <i class="fas fa-filter"></i> Status
            </label>
            <select id="hierarchy-status-filter" class="filter-select">
                <option value="">All Status</option>
                <option value="pending">Pending</option>
                <option value="in_progress">In Progress</option>
                <option value="completed">Completed</option>
            </select>
        </div>
        
        <!-- Date Filter -->
        <div class="chart-filter-group">
            <label for="hierarchy-date-start">
                <i class="fas fa-calendar"></i> From
            </label>
            <input type="date" id="hierarchy-date-start" class="filter-input">
        </div>
        <div class="chart-filter-group">
            <label for="hierarchy-date-end">
                <i class="fas fa-calendar"></i> To
            </label>
            <input type="date" id="hierarchy-date-end" class="filter-input">
        </div>
        
        <!-- Clear Filters Button -->
        <div class="chart-filter-group">
            <button id="hierarchy-clear-filters" class="btn btn-secondary" onclick="clearHierarchyFilters()">
                <i class="fas fa-times"></i> Clear
            </button>
        </div>
    </div>
</div>

<!-- Visualization -->
<div class="viz-container" id="viz-container">
    <svg class="hierarchy-svg" id="hierarchy-viz"></svg>
    
    <!-- Fullscreen exit button -->
    <button class="fullscreen-exit" id="fullscreen-exit" onclick="toggleFullscreen()" style="display: none;">
        <i class="fas fa-times"></i>
    </button>
    
    <!-- Floating Filter Toggle (visible in fullscreen) -->
    <button class="floating-filter-toggle" id="floating-filter-toggle" onclick="toggleHierarchyFilterPanel()" style="display: none;">
        <i class="fas fa-filter"></i>
    </button>
</div>
```

### 1.2 Update Fullscreen Button Group

**Location:** Lines 694-702

**Current Code:**
```html
<button class="btn btn-secondary" onclick="toggleFullscreen()">
    <i class="fas fa-expand"></i>
    Fullscreen
</button>
```

**New Code:**
```html
<button class="btn btn-secondary" onclick="toggleFullscreen()">
    <i class="fas fa-expand"></i>
    Fullscreen
</button>
<button class="btn btn-secondary" onclick="toggleHierarchyFilterPanel()" title="Toggle Filters (Ctrl+F)">
    <i class="fas fa-filter"></i>
    Filters
</button>
```

### 1.3 Add Fullscreen Filter Panel Styles

**Location:** Add to `<style>` section (after line 571)

```css
/* Chart Filter Panel */
.chart-filter-panel {
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 16px;
    box-shadow: 0 2px 4px var(--shadow-color);
}

.chart-filter-row {
    display: flex;
    flex-wrap: wrap;
    gap: 16px;
    align-items: flex-end;
}

.chart-filter-group {
    display: flex;
    flex-direction: column;
    gap: 4px;
    min-width: 150px;
}

.chart-filter-group label {
    font-size: 12px;
    color: var(--text-secondary);
    font-weight: 500;
    display: flex;
    align-items: center;
    gap: 4px;
}

.chart-filter-group .filter-input,
.chart-filter-group .filter-select {
    padding: 8px 12px;
    border-radius: 6px;
    border: 1px solid var(--border-color);
    background: var(--bg-tertiary);
    color: var(--text-primary);
    font-size: 14px;
}

.chart-filter-group .filter-input:focus,
.chart-filter-group .filter-select:focus {
    outline: none;
    border-color: #3b82f6;
    box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
}

/* Floating Filter Toggle */
.floating-filter-toggle {
    position: absolute;
    top: 16px;
    right: 16px;
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 2px 8px var(--shadow-color);
    z-index: 100;
}

.floating-filter-toggle:hover {
    background: var(--hover-bg);
}

/* Fullscreen Filter Panel */
.fullscreen-filter-panel {
    position: fixed;
    top: 16px;
    left: 16px;
    width: 300px;
    max-height: calc(100vh - 32px);
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    box-shadow: 0 4px 16px var(--shadow-color);
    z-index: 1000;
    overflow-y: auto;
    transition: transform 0.3s ease, opacity 0.3s ease;
}

.fullscreen-filter-panel.hidden {
    transform: translateX(-120%);
    opacity: 0;
    pointer-events: none;
}

.fullscreen-filter-panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    border-bottom: 1px solid var(--border-color);
    background: var(--bg-tertiary);
}

.fullscreen-filter-panel-header h4 {
    margin: 0;
    font-size: 14px;
    color: var(--text-primary);
}

.fullscreen-filter-panel-content {
    padding: 16px;
}

.fullscreen-filter-panel .chart-filter-group {
    width: 100%;
    min-width: auto;
}

.fullscreen-filter-panel .chart-filter-row {
    flex-direction: column;
    gap: 12px;
}
```

---

## Phase 2: Hierarchy.js Updates (`hierarchy.js`)

### 2.1 Add Global State for Hierarchy Filters

**Location:** After line 9 (after `simulation = null`)

```javascript
// Hierarchy filter state
let hierarchyFilters = {
    tagSearch: '',
    status: '',
    dateStart: '',
    dateEnd: ''
};
```

### 2.2 Add Tag Search Filter Functionality

**Location:** After line 841 (after `debounce` function)

```javascript
/**
 * Filter hierarchy data by tags
 * @param {Object} data - Original hierarchy data
 * @param {string} tagSearch - Comma-separated tag search terms
 * @returns {Object} - Filtered hierarchy data
 */
function filterHierarchyByTags(data, tagSearch) {
    if (!tagSearch || tagSearch.length < 3) {
        return data;
    }
    
    const searchTerms = tagSearch.split(',')
        .map(term => term.trim().toLowerCase())
        .filter(term => term.length >= 3);
    
    if (searchTerms.length === 0) {
        return data;
    }
    
    // Get tasks from dashboardData
    const tasks = window.dashboardData?.tasks || [];
    
    // Find matching tasks
    const matchingTasks = tasks.filter(task => {
        if (!task.hybrid_tags) return false;
        
        const taskTags = [
            ...task.hybrid_tags.bracket || [],
            ...task.hybrid_tags.hash || [],
            ...task.hybrid_tags.user || []
        ];
        
        return searchTerms.some(searchTerm =>
            taskTags.some(taskTag => 
                taskTag.toLowerCase().includes(searchTerm)
            )
        );
    });
    
    // Get tag IDs from matching tasks
    const matchingTagIds = new Set();
    matchingTasks.forEach(task => {
        if (task.hybrid_tags) {
            const allTags = task.hybrid_tags.to_list();
            allTags.forEach(tag => {
                const tagId = `tag_${tag}`;
                matchingTagIds.add(tagId);
            });
        }
    });
    
    // Filter nodes: keep meta, priority, category nodes and matching tag nodes
    const filteredNodes = data.nodes.filter(node => {
        if (node.level <= 2) return true; // Keep meta, priority, category nodes
        if (node.type === 'tag' && matchingTagIds.has(node.id)) return true;
        return false;
    });
    
    // Build link map for filtered nodes
    const nodeIds = new Set(filteredNodes.map(n => n.id));
    const filteredLinks = data.links.filter(link => {
        return nodeIds.has(link.source.id || link.source) && 
               nodeIds.has(link.target.id || link.target);
    });
    
    return {
        nodes: filteredNodes,
        links: filteredLinks
    };
}
```

### 2.3 Add Date Filter Functionality

**Location:** After `filterHierarchyByTags` function

```javascript
/**
 * Filter hierarchy data by date range
 * @param {Object} data - Original hierarchy data
 * @param {string} dateField - Field to filter by ('due', 'created_at', 'modified_at')
 * @param {string} dateStart - Start date (YYYY-MM-DD)
 * @param {string} dateEnd - End date (YYYY-MM-DD)
 * @returns {Object} - Filtered hierarchy data
 */
function filterHierarchyByDate(data, dateField, dateStart, dateEnd) {
    if (!dateStart && !dateEnd) {
        return data;
    }
    
    const tasks = window.dashboardData?.tasks || [];
    
    // Parse dates
    let startDate = dateStart ? new Date(dateStart) : null;
    let endDate = dateEnd ? new Date(dateEnd) : null;
    
    if (endDate) {
        endDate.setHours(23, 59, 59, 999);
    }
    
    // Find matching tasks
    const matchingTasks = tasks.filter(task => {
        const taskDate = task[dateField] || task.due;
        if (!taskDate) return false;
        
        const taskDateObj = new Date(taskDate);
        
        if (startDate && taskDateObj < startDate) return false;
        if (endDate && taskDateObj > endDate) return false;
        
        return true;
    });
    
    // Get matching task IDs
    const matchingTaskIds = new Set(matchingTasks.map(t => t.id));
    
    // Get tag IDs from matching tasks
    const matchingTagIds = new Set();
    matchingTasks.forEach(task => {
        if (task.hybrid_tags) {
            const allTags = task.hybrid_tags.to_list();
            allTags.forEach(tag => {
                const tagId = `tag_${tag}`;
                matchingTagIds.add(tagId);
            });
        }
    });
    
    // Count tasks per node type
    const priorityCounts = { critical: 0, high: 0, medium: 0, low: 0 };
    const categoryCounts = {};
    
    matchingTasks.forEach(task => {
        // Count by priority
        const priority = task.calculated_priority || 'medium';
        if (priorityCounts.hasOwnProperty(priority)) {
            priorityCounts[priority]++;
        }
        
        // Count by category
        const taskText = `${task.title} ${task.description}`.toLowerCase();
        const categoryKeywords = {
            'development': ['api', 'frontend', 'backend', 'code', 'implementation', 'feature', 'bug'],
            'testing': ['test', 'qa', 'validation', 'verification'],
            'infrastructure': ['deploy', 'setup', 'config', 'infrastructure', 'environment', 'devops'],
            'documentation': ['doc', 'documentation', 'readme', 'guide'],
            'meeting': ['meeting', 'review', 'discussion'],
            'research': ['research', 'investigate', 'explore', 'analysis']
        };
        
        for (const [category, keywords] of Object.entries(categoryKeywords)) {
            if (keywords.some(kw => taskText.includes(kw))) {
                categoryCounts[category] = (categoryCounts[category] || 0) + 1;
            }
        }
    });
    
    // Filter nodes based on counts
    const filteredNodes = data.nodes.filter(node => {
        if (node.level === 0) return true; // Keep meta node
        
        if (node.type === 'priority') {
            const priority = node.priority || node.name.toLowerCase().split(' ')[0];
            return priorityCounts[priority] > 0;
        }
        
        if (node.type === 'category') {
            const category = node.id.replace('category_', '');
            return (categoryCounts[category] || 0) > 0;
        }
        
        if (node.type === 'tag') {
            return matchingTagIds.has(node.id);
        }
        
        return true;
    });
    
    // Build link map for filtered nodes
    const nodeIds = new Set(filteredNodes.map(n => n.id));
    const filteredLinks = data.links.filter(link => {
        const sourceId = link.source.id || link.source;
        const targetId = link.target.id || link.target;
        return nodeIds.has(sourceId) && nodeIds.has(targetId);
    });
    
    return {
        nodes: filteredNodes,
        links: filteredLinks
    };
}
```

### 2.4 Add Status Filter Functionality

**Location:** After `filterHierarchyByDate` function

```javascript
/**
 * Filter hierarchy data by task status
 * @param {Object} data - Original hierarchy data
 * @param {string} status - Status to filter by
 * @returns {Object} - Filtered hierarchy data
 */
function filterHierarchyByStatus(data, status) {
    if (!status) {
        return data;
    }
    
    const tasks = window.dashboardData?.tasks || [];
    
    // Find matching tasks
    const matchingTasks = tasks.filter(task => task.status === status);
    
    // Count tasks per node type
    const priorityCounts = { critical: 0, high: 0, medium: 0, low: 0 };
    const categoryCounts = {};
    
    matchingTasks.forEach(task => {
        // Count by priority
        const priority = task.calculated_priority || 'medium';
        if (priorityCounts.hasOwnProperty(priority)) {
            priorityCounts[priority]++;
        }
        
        // Count by category
        const taskText = `${task.title} ${task.description}`.toLowerCase();
        const categoryKeywords = {
            'development': ['api', 'frontend', 'backend', 'code', 'implementation', 'feature', 'bug'],
            'testing': ['test', 'qa', 'validation', 'verification'],
            'infrastructure': ['deploy', 'setup', 'config', 'infrastructure', 'environment', 'devops'],
            'documentation': ['doc', 'documentation', 'readme', 'guide'],
            'meeting': ['meeting', 'review', 'discussion'],
            'research': ['research', 'investigate', 'explore', 'analysis']
        };
        
        for (const [category, keywords] of Object.entries(categoryKeywords)) {
            if (keywords.some(kw => taskText.includes(kw))) {
                categoryCounts[category] = (categoryCounts[category] || 0) + 1;
            }
        }
    });
    
    // Filter nodes based on counts
    const filteredNodes = data.nodes.filter(node => {
        if (node.level === 0) return true; // Keep meta node
        
        if (node.type === 'priority') {
            const priority = node.priority || node.name.toLowerCase().split(' ')[0];
            return priorityCounts[priority] > 0;
        }
        
        if (node.type === 'category') {
            const category = node.id.replace('category_', '');
            return (categoryCounts[category] || 0) > 0;
        }
        
        if (node.type === 'tag') {
            // Check if tag has any tasks with matching status
            const tag = node.id.replace('tag_', '');
            return matchingTasks.some(task => {
                if (!task.hybrid_tags) return false;
                const allTags = task.hybrid_tags.to_list();
                return allTags.some(t => t.toLowerCase().includes(tag.toLowerCase()));
            });
        }
        
        return true;
    });
    
    // Build link map for filtered nodes
    const nodeIds = new Set(filteredNodes.map(n => n.id));
    const filteredLinks = data.links.filter(link => {
        const sourceId = link.source.id || link.source;
        const targetId = link.target.id || link.target;
        return nodeIds.has(sourceId) && nodeIds.has(targetId);
    });
    
    return {
        nodes: filteredNodes,
        links: filteredLinks
    };
}
```

### 2.5 Add Combined Filter Function

**Location:** After `filterHierarchyByStatus` function

```javascript
/**
 * Apply all hierarchy filters
 * @returns {Object} - Filtered hierarchy data
 */
function applyHierarchyFilters() {
    let filteredData = hierarchyData;
    
    // Apply tag search filter
    if (hierarchyFilters.tagSearch && hierarchyFilters.tagSearch.length >= 3) {
        filteredData = filterHierarchyByTags(filteredData, hierarchyFilters.tagSearch);
    }
    
    // Apply status filter
    if (hierarchyFilters.status) {
        filteredData = filterHierarchyByStatus(filteredData, hierarchyFilters.status);
    }
    
    // Apply date filter
    if (hierarchyFilters.dateStart || hierarchyFilters.dateEnd) {
        filteredData = filterHierarchyByDate(
            filteredData, 
            'due',
            hierarchyFilters.dateStart, 
            hierarchyFilters.dateEnd
        );
    }
    
    return filteredData;
}
```

### 2.6 Update Node Label Display with Truncation

**Location:** Lines 128-140 (update label rendering)

**Current Code:**
```javascript
// Add labels for level 0 and 1 nodes
const labels = g.append('g')
    .attr('class', 'labels')
    .selectAll('text')
    .data(hierarchyData.nodes.filter(d => d.level <= 1) || [])
    .enter()
    .append('text')
    .attr('dy', d => (d.val || 10) + 15)
    .attr('text-anchor', 'middle')
    .attr('font-size', '11px')
    .attr('fill', '#374151')
    .attr('font-weight', '500')
    .text(d => d.name);
```

**New Code:**
```javascript
// Add labels for level 0 and 1 nodes with truncation
const labels = g.append('g')
    .attr('class', 'labels')
    .selectAll('text')
    .data(hierarchyData.nodes.filter(d => d.level <= 1) || [])
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
        // Store full name in data attribute for tooltip
        d3.select(this)
            .attr('data-full-name', d.name)
            .on('mouseover', function(event) {
                showLabelTooltip(event, d.name);
            })
            .on('mouseout', hideLabelTooltip);
    });

// Text truncation helper
function truncateText(text, maxLength) {
    if (!text) return '';
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

// Label tooltip for truncated text
function showLabelTooltip(event, fullText) {
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

function hideLabelTooltip() {
    const tooltip = document.getElementById('label-tooltip');
    if (tooltip) {
        tooltip.style.display = 'none';
    }
}
```

### 2.7 Add Filter Event Handlers

**Location:** Add after `initHierarchy` function (around line 197)

```javascript
/**
 * Initialize hierarchy filter event listeners
 */
function initHierarchyFilters() {
    const tagSearchInput = document.getElementById('hierarchy-tag-search');
    const statusFilter = document.getElementById('hierarchy-status-filter');
    const dateStartInput = document.getElementById('hierarchy-date-start');
    const dateEndInput = document.getElementById('hierarchy-date-end');
    
    if (!tagSearchInput) return;
    
    // Tag search with debounce (300ms, trigger after 3+ chars)
    tagSearchInput.addEventListener('input', debounce(function() {
        const value = this.value.trim();
        hierarchyFilters.tagSearch = value;
        
        // Only search if 3+ characters
        if (value.length >= 3 || value.length === 0) {
            refreshHierarchyVisualization();
        }
    }, 300));
    
    // Status filter
    if (statusFilter) {
        statusFilter.addEventListener('change', function() {
            hierarchyFilters.status = this.value;
            refreshHierarchyVisualization();
        });
    }
    
    // Date filters
    if (dateStartInput) {
        dateStartInput.addEventListener('change', function() {
            hierarchyFilters.dateStart = this.value;
            refreshHierarchyVisualization();
        });
    }
    
    if (dateEndInput) {
        dateEndInput.addEventListener('change', function() {
            hierarchyFilters.dateEnd = this.value;
            refreshHierarchyVisualization();
        });
    }
}

/**
 * Refresh hierarchy visualization with filters
 */
function refreshHierarchyVisualization() {
    const filteredData = applyHierarchyFilters();
    
    // Re-render with filtered data
    initHierarchy();
    
    // Apply filtered data
    renderFilteredHierarchy(filteredData);
}

/**
 * Render filtered hierarchy data
 */
function renderFilteredHierarchy(data) {
    // Clear existing
    const svg = d3.select('#hierarchy-viz');
    svg.selectAll('.links').remove();
    svg.selectAll('.nodes').remove();
    svg.selectAll('.labels').remove();
    
    const g = svg.select('g');
    
    // Create links
    const link = g.append('g')
        .attr('class', 'links')
        .selectAll('line')
        .data(data.links || [])
        .enter()
        .append('line')
        .attr('stroke', '#d1d5db')
        .attr('stroke-opacity', 0.7)
        .attr('stroke-width', d => Math.max(1, Math.sqrt(d.value || 1)));
    
    // Create nodes
    const node = g.append('g')
        .attr('class', 'nodes')
        .selectAll('circle')
        .data(data.nodes || [])
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
        .on('mouseover', function(event, d) {
            d3.select(this)
                .transition()
                .duration(150)
                .attr('r', (d.val || 10) * 1.2);
            showNodeTooltip(event, d);
        })
        .on('mouseout', function(event, d) {
            d3.select(this)
                .transition()
                .duration(150)
                .attr('r', d => {
                    const baseSize = Math.max(8, Math.min(25, d.val || 10));
                    return d.level === 0 ? baseSize * 1.2 : baseSize;
                });
            hideNodeTooltip();
        })
        .on('click', function(event, d) {
            event.stopPropagation();
            handleNodeClick(d);
        });
    
    // Add labels
    const labels = g.append('g')
        .attr('class', 'labels')
        .selectAll('text')
        .data(data.nodes.filter(d => d.level <= 1) || [])
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
    if (simulation) {
        simulation.nodes(data.nodes);
        simulation.force('link').links(data.links);
        simulation.alpha(0.3).restart();
    }
}

/**
 * Clear all hierarchy filters
 */
function clearHierarchyFilters() {
    hierarchyFilters = {
        tagSearch: '',
        status: '',
        dateStart: '',
        dateEnd: ''
    };
    
    // Reset UI
    const tagSearchInput = document.getElementById('hierarchy-tag-search');
    const statusFilter = document.getElementById('hierarchy-status-filter');
    const dateStartInput = document.getElementById('hierarchy-date-start');
    const dateEndInput = document.getElementById('hierarchy-date-end');
    
    if (tagSearchInput) tagSearchInput.value = '';
    if (statusFilter) statusFilter.value = '';
    if (dateStartInput) dateStartInput.value = '';
    if (dateEndInput) dateEndInput.value = '';
    
    // Refresh visualization
    refreshHierarchyVisualization();
}
```

### 2.8 Update Fullscreen Handling

**Location:** Update `toggleFullscreen` function (around line 1105 in dashboard.html)

```javascript
// Update the toggleFullscreen function to handle filter visibility
function toggleFullscreen() {
    const vizContainer = document.getElementById('viz-container');
    const exitButton = document.getElementById('fullscreen-exit');
    const filterToggle = document.getElementById('floating-filter-toggle');
    const filterPanel = document.getElementById('chart-filter-panel');
    
    isFullscreen = !isFullscreen;
    
    if (isFullscreen) {
        vizContainer.classList.add('fullscreen-mode');
        exitButton.style.display = 'block';
        
        // Show floating filter toggle
        if (filterToggle) filterToggle.style.display = 'flex';
        
        // Hide regular filter panel, show floating version
        if (filterPanel) filterPanel.style.display = 'none';
        
        // Create floating filter panel
        createFloatingFilterPanel();
    } else {
        vizContainer.classList.remove('fullscreen-mode');
        exitButton.style.display = 'none';
        
        // Hide floating filter toggle
        if (filterToggle) filterToggle.style.display = 'none';
        
        // Show regular filter panel
        if (filterPanel) filterPanel.style.display = 'block';
        
        // Remove floating filter panel
        removeFloatingFilterPanel();
    }
    
    setTimeout(updateHierarchyVisualization, 300);
}

/**
 * Create floating filter panel for fullscreen mode
 */
function createFloatingFilterPanel() {
    // Remove existing
    removeFloatingFilterPanel();
    
    const filterPanel = document.getElementById('chart-filter-panel');
    if (!filterPanel) return;
    
    // Clone the filter panel
    const floatingPanel = filterPanel.cloneNode(true);
    floatingPanel.id = 'floating-filter-panel';
    floatingPanel.className = 'fullscreen-filter-panel';
    
    // Add header
    const header = document.createElement('div');
    header.className = 'fullscreen-filter-panel-header';
    header.innerHTML = `
        <h4><i class="fas fa-filter"></i> Chart Filters</h4>
        <button onclick="toggleHierarchyFilterPanel()" style="background:none;border:none;cursor:pointer;">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    floatingPanel.insertBefore(header, floatingPanel.firstChild);
    
    document.body.appendChild(floatingPanel);
    
    // Make draggable
    makeDraggable(floatingPanel);
}

/**
 * Remove floating filter panel
 */
function removeFloatingFilterPanel() {
    const existing = document.getElementById('floating-filter-panel');
    if (existing) {
        existing.remove();
    }
}

/**
 * Toggle hierarchy filter panel visibility
 */
function toggleHierarchyFilterPanel() {
    const panel = document.getElementById('floating-filter-panel');
    if (panel) {
        panel.classList.toggle('hidden');
    }
}

/**
 * Make element draggable
 */
function makeDraggable(element) {
    let isDragging = false;
    let startX, startY, initialX, initialY;
    
    const header = element.querySelector('.fullscreen-filter-panel-header');
    if (!header) return;
    
    header.style.cursor = 'move';
    
    header.addEventListener('mousedown', function(e) {
        if (e.target.tagName === 'BUTTON') return;
        
        isDragging = true;
        startX = e.clientX;
        startY = e.clientY;
        initialX = element.offsetLeft;
        initialY = element.offsetTop;
        
        element.style.zIndex = '1001';
    });
    
    document.addEventListener('mousemove', function(e) {
        if (!isDragging) return;
        
        const dx = e.clientX - startX;
        const dy = e.clientY - startY;
        
        element.style.left = (initialX + dx) + 'px';
        element.style.top = (initialY + dy) + 'px';
    });
    
    document.addEventListener('mouseup', function() {
        isDragging = false;
        element.style.zIndex = '1000';
    });
}
```

### 2.9 Update Keyboard Shortcuts

**Location:** Update `setupKeyboardShortcuts` function (lines 1678-1689)

```javascript
function setupKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        if (e.ctrlKey && e.key === 'b') {
            e.preventDefault();
            toggleSidebar();
        }
        if (e.key === 'Escape' && isFullscreen) {
            toggleFullscreen();
        }
        // Toggle filter panel with Ctrl+F
        if (e.ctrlKey && e.key === 'f') {
            e.preventDefault();
            if (isFullscreen) {
                toggleHierarchyFilterPanel();
            }
        }
    });
}
```

### 2.10 Initialize Filters

**Location:** Add to end of `renderHierarchy` function (around line 31)

```javascript
function renderHierarchy(data) {
    hierarchyData = data;
    initHierarchy();
    initHierarchyFilters(); // Add this line
}
```

---

## Phase 3: Data Manager Updates (`data_manager.py`)

### 3.1 Add Filtered Hierarchy Data Method

**Location:** After line 395 (after `get_hierarchy_data` method)

```python
def get_filtered_hierarchy_data(
    self, 
    tasks: List[Task],
    tag_filters: Optional[List[str]] = None,
    status_filter: Optional[str] = None,
    date_field: str = 'due',
    date_start: Optional[str] = None,
    date_end: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate filtered hierarchy visualization data from tasks
    
    Args:
        tasks: List of Task objects
        tag_filters: List of tag search terms to filter by
        status_filter: Status to filter by (pending, in_progress, completed)
        date_field: Field to filter by ('due', 'created_at', 'modified_at')
        date_start: Start date (YYYY-MM-DD)
        date_end: End date (YYYY-MM-DD)
    
    Returns:
        Dictionary with 'nodes' and 'links' lists
    """
    # Apply filters to get filtered tasks
    filtered_tasks = tasks
    
    # Apply status filter
    if status_filter:
        filtered_tasks = [t for t in filtered_tasks if t.status == status_filter]
    
    # Apply date filters
    if date_start or date_end:
        filtered_tasks = self._filter_tasks_by_date_range(
            filtered_tasks, 
            date_field, 
            date_start, 
            date_end
        )
    
    # Apply tag filters
    if tag_filters:
        filtered_tasks = self._filter_tasks_by_tags(filtered_tasks, tag_filters)
    
    # Generate hierarchy from filtered tasks
    return self.get_hierarchy_data(filtered_tasks)

def _filter_tasks_by_date_range(
    self, 
    tasks: List[Task],
    date_field: str,
    date_start: Optional[str],
    date_end: Optional[str]
) -> List[Task]:
    """Filter tasks by date range"""
    filtered_tasks = []
    
    for task in tasks:
        task_date = getattr(task, date_field, None) or task.due
        if not task_date:
            continue
        
        task_date_obj = datetime.fromisoformat(task_date).date() if isinstance(task_date, str) else task_date
        
        if date_start:
            start_date = datetime.fromisoformat(date_start).date() if isinstance(date_start, str) else date_start
            if task_date_obj < start_date:
                continue
        
        if date_end:
            end_date = datetime.fromisoformat(date_end).date() if isinstance(date_end, str) else date_end
            if task_date_obj > end_date:
                continue
        
        filtered_tasks.append(task)
    
    return filtered_tasks

def _filter_tasks_by_tags(self, tasks: List[Task], tag_filters: List[str]) -> List[Task]:
    """Filter tasks by tag search terms"""
    if not tag_filters:
        return tasks
    
    filtered_tasks = []
    
    for task in tasks:
        if not task.hybrid_tags:
            continue
        
        task_tags = task.hybrid_tags.to_list()
        
        # Check if any tag matches any filter
        matches = any(
            any(tag_filter.lower() in tag.lower() for tag in task_tags)
            for tag_filter in tag_filters
        )
        
        if matches:
            filtered_tasks.append(task)
    
    return filtered_tasks
```

### 3.2 Update API Endpoint

**Location:** Update `api_handlers.py` (not shown in files, but typically in `gtasks_dashboard/api_handlers.py`)

```python
@route('/api/hierarchy')
async def get_hierarchy(request):
    """Get hierarchy visualization data with optional filters"""
    dm = request.app.get('data_manager')
    
    # Get current account
    current_account = dm.dashboard_state.get('current_account', 'default')
    tasks = dm.load_tasks_for_account(current_account)
    
    # Get filter parameters
    tag_search = request.query.get('tag_search', '')
    status = request.query.get('status', '')
    date_field = request.query.get('date_field', 'due')
    date_start = request.query.get('date_start', '')
    date_end = request.query.get('date_end', '')
    
    # Parse tag search (comma-separated)
    tag_filters = [t.strip() for t in tag_search.split(',')] if tag_search else []
    
    # Get hierarchy data
    if tag_filters or status or date_start or date_end:
        hierarchy_data = dm.get_filtered_hierarchy_data(
            tasks,
            tag_filters=tag_filters,
            status_filter=status or None,
            date_field=date_field,
            date_start=date_start or None,
            date_end=date_end or None
        )
    else:
        hierarchy_data = dm.get_hierarchy_data(tasks)
    
    return json_response(hierarchy_data)
```

---

## Phase 4: CSS/Styling Updates

### 4.1 Chart Filter Panel Styles (Already included in Phase 1.3)

### 4.2 Fullscreen Mode Styles

Add to `<style>` section:

```css
/* Fullscreen mode */
.viz-container.fullscreen-mode {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    z-index: 999;
    background: var(--bg-primary);
    padding: 16px;
}

.viz-container.fullscreen-mode .hierarchy-svg {
    width: 100%;
    height: 100%;
}

/* Dark mode adjustments for chart filters */
.dark-mode .chart-filter-panel {
    background: var(--bg-secondary);
    border-color: var(--border-color);
}

.dark-mode .chart-filter-group label {
    color: var(--text-primary);
}

.dark-mode .chart-filter-group .filter-input,
.dark-mode .chart-filter-group .filter-select {
    background: var(--bg-tertiary);
    color: var(--text-primary);
    border-color: var(--border-color);
}

.dark-mode .chart-filter-group .filter-input:focus,
.dark-mode .chart-filter-group .filter-select:focus {
    border-color: #60a5fa;
    box-shadow: 0 0 0 2px rgba(96, 165, 250, 0.2);
}

.dark-mode .fullscreen-filter-panel {
    background: var(--bg-secondary);
    border-color: var(--border-color);
}

.dark-mode .fullscreen-filter-panel-header {
    background: var(--bg-tertiary);
}

.dark-mode .fullscreen-filter-panel-header h4 {
    color: var(--text-primary);
}

.dark-mode .floating-filter-toggle {
    background: var(--bg-secondary);
    color: var(--text-primary);
}

.dark-mode .floating-filter-toggle:hover {
    background: var(--hover-bg);
}
```

---

## Phase 5: Testing Approach

### 5.1 Tag Search Filter Testing

| Test Case | Steps | Expected Result |
|-----------|-------|-----------------|
| Single tag search | Enter "api" in search field | Chart shows only nodes related to "api" tag |
| Comma-separated tags | Enter "api, bug" in search field | Chart shows nodes matching either tag |
| Empty search | Clear search field | Chart shows all nodes |
| Below threshold | Enter "a" (2 chars) | No filtering applied |
| At threshold | Enter "abc" (3 chars) | Filtering applied |
| Debounce | Type "api" quickly | Chart updates 300ms after typing stops |

### 5.2 Date/Status Filter Testing

| Test Case | Steps | Expected Result |
|-----------|-------|-----------------|
| Date range filter | Set start date to 7 days ago, end date to today | Chart shows tasks due in that range |
| Status filter | Select "completed" from dropdown | Chart shows only completed task nodes |
| Combined filters | Set date range + status filter | Chart shows tasks matching both criteria |
| Clear filters | Click "Clear" button | Chart resets to show all data |

### 5.3 Node Name Display Testing

| Test Case | Steps | Expected Result |
|-----------|-------|-----------------|
| Long name truncation | Hover over node with long name | Shows truncated text (5 chars + ...) |
| Tooltip display | Hover over truncated name | Tooltip shows full name |
| Short name | Hover over node with short name | Shows full name without truncation |
| All node types | Check all node types (priority, category, tag, account) | All display names correctly |

### 5.4 Fullscreen Filter Visibility Testing

| Test Case | Steps | Expected Result |
|-----------|-------|-----------------|
| Enter fullscreen | Click Fullscreen button | Chart enters fullscreen mode |
| Filter panel visibility | Enter fullscreen, click filter toggle | Filter panel appears/disappears |
| Keyboard shortcut | In fullscreen, press Ctrl+F | Filter panel toggles visibility |
| Draggable panel | Drag filter panel | Panel moves with mouse |
| Exit fullscreen | Press Escape or click exit button | Returns to normal view |

---

## File Modification Summary

| File | Changes | Lines |
|------|---------|-------|
| `dashboard.html` | Add filter panel HTML, styles, filter toggle button | 704-713, 694-702, 572-600+ |
| `hierarchy.js` | Add filter functions, truncation, fullscreen handling | 10+, 128-140, 841+ |
| `data_manager.py` | Add filtered hierarchy methods | 396-450+ |
| `api_handlers.py` | Update hierarchy endpoint with filters | (new/modified) |

---

## Data Flow Diagram

```
User Input
    │
    ├─ Tag Search (3+ chars, comma-separated)
    │  └─> debounce(300ms) -> filterHierarchyByTags()
    │       └─> Update hierarchy visualization
    │
    ├─ Status Filter
    │  └─> filterHierarchyByStatus()
    │       └─> Update hierarchy visualization
    │
    ├─ Date Range Filter
    │  └─> filterHierarchyByDate()
    │       └─> Update hierarchy visualization
    │
    └─ Fullscreen Toggle
        └─> Show/hide floating filter panel
             └─> Keyboard shortcut (Ctrl+F)
```

---

## Implementation Order

1. **Phase 1**: UI Structure Updates (dashboard.html)
2. **Phase 2**: Hierarchy.js Updates (hierarchy.js) - Core functionality
3. **Phase 3**: Data Manager Updates (data_manager.py) - Backend support
4. **Phase 4**: CSS/Styling Updates
5. **Phase 5**: Testing and refinement

---

## Notes

- All new functions should be exported to `window` object for global access
- Debounce function already exists in hierarchy.js (line 831)
- Dark mode styles already defined in dashboard.html
- Existing filter panel in task panel can be reused for reference
- Filter state should persist across account switches
