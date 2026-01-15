/**
 * Hierarchy Visualization with D3.js
 * Handles node click, dependent tasks display, and advanced filtering
 */

// hierarchyData is used globally - declared here
let hierarchyData = {};
let selectedNode = null;
let simulation = null;

// Hierarchy filter state
let hierarchyFilters = {
    tagSearch: '',
    status: '',
    dateStart: '',
    dateEnd: ''
};

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

// Initialize when DOM is ready - wait for loadDashboard to set dashboardData
// The actual initialization happens via loadDashboard() -> loadHierarchy() -> renderHierarchy()

// Render hierarchy visualization
function renderHierarchy(data) {
    hierarchyData = data;
    initHierarchy();
}

function initHierarchy() {
    const svg = d3.select('#hierarchy-viz');
    if (svg.empty()) return;

    // Clear existing SVG content properly (SVG elements need different handling than HTML)
    while (svg.node().firstChild) {
        svg.node().removeChild(svg.node().firstChild);
    }

    if (!hierarchyData.nodes || hierarchyData.nodes.length === 0) {
        svg.append('text')
            .attr('x', '50%')
            .attr('y', '50%')
            .attr('text-anchor', 'middle')
            .attr('fill', '#6b7280')
            .text('No hierarchy data available. Load tasks first.');
        return;
    }

    const width = svg.node().clientWidth || 800;
    const height = svg.node().clientHeight || 500;

    // Use the existing SVG - no need to append a new one
    const g = svg.append('g');

    const zoom = d3.zoom()
        .scaleExtent([0.1, 10])  // Wider zoom range: 0.1x to 10x
        .on('zoom', (event) => {
            console.log('D3 Zoom event:', event.transform.k);
            g.attr('transform', event.transform);
        });

    // Store zoom reference globally for external access
    window.hierarchyZoom = zoom;

    // Call zoom on the SVG - this attaches all event handlers
    svg.call(zoom);

    // Store references for external use
    window.hierarchySvg = svg;
    window.hierarchyG = g;
    window.hierarchyZoomRef = zoom;

    // Create links
    const link = g.append('g')
        .attr('class', 'links')
        .selectAll('line')
        .data(hierarchyData.links || [])
        .enter()
        .append('line')
        .attr('stroke', '#d1d5db')
        .attr('stroke-opacity', 0.7)
        .attr('stroke-width', d => Math.max(1, Math.sqrt(d.value || 1)));

    // Create nodes
    const node = g.append('g')
        .attr('class', 'nodes')
        .selectAll('circle')
        .data(hierarchyData.nodes || [])
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

            // Show tooltip
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

    // Initialize force simulation
    simulation = d3.forceSimulation(hierarchyData.nodes)
        .force('link', d3.forceLink(hierarchyData.links)
            .id(d => d.id)
            .distance(d => {
                const sourceLevel = hierarchyData.nodes.find(n => n.id === d.source)?.level || 0;
                const targetLevel = hierarchyData.nodes.find(n => n.id === d.target)?.level || 0;
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

    // NOTE: No automatic centering - D3 zoom works natively
    // Users can zoom/pan freely from the start using mouse wheel and drag

    // Manual wheel listener removed to allow native D3 zoom to handle smoothness and pointer-centering correctly.
    // D3's default zoom behavior matches standard interaction patterns better.


    // Store references for external use
    window.hierarchySvg = svg;
    window.hierarchyG = g;
    window.hierarchyZoomRef = zoom;
    window.hierarchyZoom = zoom;

    // Auto-center the visualization after initialization
    if (typeof window.centerVisualizationOnce === 'function') {
        window.centerVisualizationOnce();
    }
}

function getNodeColor(node) {
    if (node.type === 'priority' && node.priority) {
        return colorScale.priority[node.priority] || colorScale.priority.medium;
    }
    return colorScale[node.type] || '#6b7280';
}

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

// Tooltip functions
function showNodeTooltip(event, d) {
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

function hideNodeTooltip() {
    const tooltip = document.getElementById('node-tooltip');
    if (tooltip) {
        tooltip.style.display = 'none';
    }
}

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

// Node click handler
function handleNodeClick(node) {
    console.log('Node clicked:', node);
    selectedNode = node;

    // Show task panel
    showTaskPanel(node);

    // Highlight selected node
    highlightSelectedNode(node);

    // Load related tasks
    loadNodeTasks(node);
}

function highlightSelectedNode(node) {
    d3.selectAll('#hierarchy-viz circle').classed('selected', false);

    d3.selectAll('#hierarchy-viz circle')
        .filter(d => d.id === node.id)
        .classed('selected', true)
        .style('stroke', '#3b82f6')
        .style('stroke-width', 4)
        .style('filter', 'drop-shadow(0 0 8px rgba(59, 130, 246, 0.6))');
}

function showTaskPanel(node) {
    const panel = document.getElementById('task-panel');
    const title = document.getElementById('selected-node-title');

    title.textContent = `Tasks for: ${node.name || node.id}`;
    panel.style.display = 'block';
    
    // Remove any previous animation styles
    panel.style.maxHeight = '';
    panel.style.transition = '';
    
    // Make the panel very tall so users can scroll through all tasks and bring any part to the top
    panel.style.minHeight = '300vh'; // Much taller than viewport for full scrolling
    
    // Scroll the task panel into view
    setTimeout(() => {
        panel.scrollIntoView({ 
            behavior: 'smooth', 
            block: 'start' 
        });
    }, 50);
}

function closeTaskPanel() {
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

    // Clear selection
    selectedNode = null;
    d3.selectAll('#hierarchy-viz circle').classed('selected', false)
        .style('stroke', '#fff')
        .style('stroke-width', 2)
        .style('filter', 'drop-shadow(0 2px 4px rgba(0,0,0,0.1))');
}

function loadNodeTasks(node) {
    const relatedTasks = getRelatedTasks(node);
    displayNodeTasks(relatedTasks, node);
    setupTaskFilters(node);
}

function getRelatedTasks(node) {
    const allTasks = dashboardData.tasks || [];
    
    // Apply current hierarchy filters to get filtered tasks
    let filteredTasks = allTasks;
    
    // Filter out deleted tasks if setting is enabled
    if (window.shouldHideDeleted && window.shouldHideDeleted()) {
        filteredTasks = filteredTasks.filter(task => task.status !== 'deleted');
    }
    
    // Apply status filter
    if (hierarchyFilters.status) {
        filteredTasks = filteredTasks.filter(task => task.status === hierarchyFilters.status);
    }
    
    // Apply date filters
    if (hierarchyFilters.dateStart || hierarchyFilters.dateEnd) {
        filteredTasks = filteredTasks.filter(task => {
            const taskDate = task.due;
            if (!taskDate) return false;
            
            const taskDateObj = new Date(taskDate);
            
            if (hierarchyFilters.dateStart) {
                const startDate = new Date(hierarchyFilters.dateStart);
                startDate.setHours(0, 0, 0, 0);
                if (taskDateObj < startDate) return false;
            }
            
            if (hierarchyFilters.dateEnd) {
                const endDate = new Date(hierarchyFilters.dateEnd);
                endDate.setHours(23, 59, 59, 999);
                if (taskDateObj > endDate) return false;
            }
            
            return true;
        });
    }
    
    // Apply tag search filter
    if (hierarchyFilters.tagSearch && hierarchyFilters.tagSearch.length >= 3) {
        const searchTerms = hierarchyFilters.tagSearch.split(',')
            .map(term => term.trim().toLowerCase())
            .filter(term => term.length >= 3);
        
        if (searchTerms.length > 0) {
            filteredTasks = filteredTasks.filter(task => {
                if (!task.hybrid_tags) return false;
                
                const taskTags = [
                    ...task.hybrid_tags.bracket || [],
                    ...task.hybrid_tags.hash || [],
                    ...task.hybrid_tags.user || []
                ];
                
                return searchTerms.some(searchTerm =>
                    taskTags.some(taskTag => 
                        taskTag.toLowerCase().startsWith(searchTerm)
                    )
                );
            });
        }
    }
    
    let filteredTaskIds = new Set(filteredTasks.map(t => t.id));
    
    let relatedTasks;

    switch (node.type) {
        case 'priority':
            const priority = (node.priority || node.name.toLowerCase().split(' ')[0]);
            relatedTasks = filteredTasks.filter(task =>
                task.calculated_priority === priority ||
                task.priority === priority
            );
            break;

        case 'category':
            const category = node.id.replace('category_', '');
            const categoryKeywords = {
                'development': ['api', 'frontend', 'backend', 'code', 'implementation', 'feature'],
                'testing': ['test', 'bug', 'qa', 'validation', 'verification'],
                'infrastructure': ['deploy', 'setup', 'config', 'infrastructure', 'environment'],
                'documentation': ['doc', 'documentation', 'readme', 'guide'],
                'meeting': ['meeting', 'review', 'discussion', 'standup'],
                'research': ['research', 'investigate', 'explore', 'analysis']
            };
            const keywords = categoryKeywords[category] || [];
            relatedTasks = filteredTasks.filter(task => {
                const taskText = `${task.title} ${task.description}`.toLowerCase();
                return keywords.some(keyword => taskText.includes(keyword));
            });
            break;

        case 'tag':
            const tag = node.id.replace('tag_', '');
            relatedTasks = filteredTasks.filter(task => {
                if (!task.hybrid_tags) return false;
                const allTags = [
                    ...task.hybrid_tags.bracket || [],
                    ...task.hybrid_tags.hash || [],
                    ...task.hybrid_tags.user || []
                ];
                return allTags.some(t => t.toLowerCase().includes(tag.toLowerCase()));
            });
            break;

        case 'account':
            const account = node.id.replace('account_', '');
            relatedTasks = filteredTasks.filter(task => task.account === account);
            break;

        case 'meta':
            relatedTasks = filteredTasks.slice(0, 10);
            break;

        default:
            relatedTasks = filteredTasks;
    }

    // Get dependent tasks from filtered set
    const dependentTasks = getDependentTasks(relatedTasks, filteredTasks);

    // Combine related tasks with their dependents
    const allRelatedTasks = [...relatedTasks];
    dependentTasks.forEach(depTask => {
        if (!allRelatedTasks.find(t => t.id === depTask.id)) {
            allRelatedTasks.push(depTask);
        }
    });

    return allRelatedTasks;
}

function getDependentTasks(tasks, allTasks) {
    const dependentTasks = [];
    const taskIds = new Set(tasks.map(t => t.id));

    allTasks.forEach(task => {
        // Check if this task depends on any of the filtered tasks
        if (task.dependencies && task.dependencies.length > 0) {
            const hasDependency = task.dependencies.some(depId => taskIds.has(depId));
            if (hasDependency) {
                dependentTasks.push(task);
            }
        }

        // Check if any of the filtered tasks depend on this task
        if (taskIds.has(task.id)) {
            tasks.forEach(filteredTask => {
                if (filteredTask.dependencies && filteredTask.dependencies.includes(task.id)) {
                    if (!dependentTasks.find(t => t.id === task.id)) {
                        dependentTasks.push(task);
                    }
                }
            });
        }
    });

    return dependentTasks;
}

function displayNodeTasks(tasks, node) {
    const container = document.getElementById('node-tasks-grid');
    if (!container) return;

    container.innerHTML = '';

    if (tasks.length === 0) {
        container.innerHTML = '<p style="text-align: center; color: #6b7280; grid-column: 1/-1;">No tasks found for this node.</p>';
        return;
    }
    
    // Sort by due date descending (default)
    tasks.sort((a, b) => {
        const aDue = a.due ? new Date(a.due).getTime() : -Infinity;
        const bDue = b.due ? new Date(b.due).getTime() : -Infinity;
        return bDue - aDue; // Descending order
    });

    tasks.forEach(task => {
        const taskCard = createNodeTaskCard(task, node);
        container.appendChild(taskCard);
    });
}

function createNodeTaskCard(task, node) {
    const card = document.createElement('div');
    card.className = 'node-task-card';

    const priorityClass = `priority-${task.calculated_priority || 'medium'}`;
    const priorityIcon = {
        'critical': '<i class="fas fa-exclamation-circle"></i>',
        'high': '<i class="fas fa-arrow-up"></i>',
        'medium': '<i class="fas fa-minus"></i>',
        'low': '<i class="fas fa-arrow-down"></i>'
    }[task.calculated_priority || 'medium'] || '<i class="fas fa-minus"></i>';

    // Date status calculation
    const dateStatus = getDateStatus(task.due);
    const dateStatusBadge = getDateStatusBadge(dateStatus);
    
    // Compact date display
    const compactDates = getCompactDateDisplay(task);
    
    // Notes section (expandable)
    const notesSection = getNotesSection(task);
    
    // Tags display
    const tagsDisplay = getTagsDisplay(task);

    // Check if this task has dependencies
    const hasDeps = task.dependencies && task.dependencies.length > 0;
    const depsInfo = hasDeps ? `<small style="color: #f59e0b; font-size: 0.7rem; display: block; margin-top: 0.25rem;"><i class="fas fa-link"></i> ${task.dependencies.length} dependency(ies)</small>` : '';

    card.innerHTML = `
        <div class="node-task-header">
            <span class="priority-icon">🔸</span>
            <div class="node-task-title">${task.title}</div>
            ${dateStatusBadge}
        </div>
        <div class="node-task-dates">${compactDates}</div>
        ${task.description ? `<p style="color: #6b7280; font-size: 0.875rem; margin: 0.5rem 0;">${task.description}</p>` : ''}
        <div class="node-task-meta">
            <span class="node-task-priority ${priorityClass}">
                ${priorityIcon} ${task.calculated_priority || 'medium'}
            </span>
            <span class="node-task-status">${task.status || 'pending'}</span>
        </div>
        ${depsInfo}
        ${tagsDisplay}
        ${notesSection}
        ${task.account ? `<small style="color: #9ca3af; font-size: 0.75rem; margin-top: 0.5rem; display: block;">Account: ${task.account}</small>` : ''}
    `;

    // Add click handler for expanding notes
    const notesToggle = card.querySelector('.notes-toggle');
    if (notesToggle) {
        notesToggle.addEventListener('click', function() {
            const notesContent = this.nextElementSibling;
            const isExpanded = notesContent.style.maxHeight !== '0px' && notesContent.style.maxHeight !== '';
            
            if (isExpanded) {
                notesContent.style.maxHeight = '0px';
                this.textContent = 'Show more 📓';
            } else {
                notesContent.style.maxHeight = notesContent.scrollHeight + 'px';
                this.textContent = 'Show less 📓';
            }
        });
    }

    return card;
}

// Helper function to calculate date status
function getDateStatus(dueDate) {
    if (!dueDate) return 'none';
    
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    const due = new Date(dueDate);
    due.setHours(0, 0, 0, 0);
    
    if (due < today) return 'overdue';
    if (due.getTime() === today.getTime()) return 'today';
    return 'future';
}

// Helper function to generate date status badge
function getDateStatusBadge(dateStatus) {
    const badges = {
        'overdue': '<span class="date-status-badge overdue">⏳ Overdue</span>',
        'today': '<span class="date-status-badge today">📅 Today</span>',
        'future': '<span class="date-status-badge future">📅 Future</span>',
        'none': ''
    };
    return badges[dateStatus] || badges['none'];
}

// Helper function to format date to YYYY-MM-DD
function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toISOString().split('T')[0];
}

// Helper function to generate compact date display
function getCompactDateDisplay(task) {
    const due = formatDate(task.due);
    const created = formatDate(task.created_at);
    const modified = formatDate(task.modified_at);
    
    return `<span class="compact-dates">
        <span class="date-label">D:${due}</span>
        <span class="date-label">C:${created}</span>
        <span class="date-label">M:${modified}</span>
    </span>`;
}

// Helper function to generate notes section
function getNotesSection(task) {
    const notes = task.notes || task.description || '';
    if (!notes) return '';
    
    const truncated = notes.length > 100;
    const displayText = truncated ? notes.substring(0, 100) + '...' : notes;
    const fullContent = notes.split('\n').map(line => line.trim()).filter(line => line).join('<br>');
    
    return `
        <div class="notes-section">
            <button class="notes-toggle">${truncated ? 'Show more 📓' : 'Show less 📓'}</button>
            <div class="notes-content" style="${truncated ? 'max-height: 0px; overflow: hidden;' : 'max-height: none;'}">
                <div class="notes-text">📓 ${fullContent}</div>
            </div>
        </div>
    `;
}

// Helper function to generate tags display
function getTagsDisplay(task) {
    const tags = [];
    
    // Add bracket tags
    if (task.hybrid_tags && task.hybrid_tags.bracket) {
        tags.push(...task.hybrid_tags.bracket);
    }
    
    // Add hash tags
    if (task.hybrid_tags && task.hybrid_tags.hash) {
        tags.push(...task.hybrid_tags.hash);
    }
    
    // Add user tags
    if (task.hybrid_tags && task.hybrid_tags.user) {
        tags.push(...task.hybrid_tags.user);
    }
    
    // Add regular tags
    if (task.tags) {
        tags.push(...task.tags);
    }
    
    if (tags.length === 0) return '';
    
    const tagsHtml = tags.map(tag => `<span class="task-tag">[${tag}]</span>`).join(' ');
    return `<div class="task-tags">${tagsHtml}</div>`;
}

function setupTaskFilters(node) {
    const statusFilter = document.getElementById('node-task-status-filter');
    const priorityFilter = document.getElementById('node-task-priority-filter');
    const searchFilter = document.getElementById('node-task-search-filter');
    const projectFilter = document.getElementById('node-task-project-filter');
    const tagsFilter = document.getElementById('node-task-tags-filter');
    const dateFieldFilter = document.getElementById('node-task-date-field');
    const dateStartFilter = document.getElementById('node-task-date-start');
    const dateEndFilter = document.getElementById('node-task-date-end');
    const sortFieldFilter = document.getElementById('node-task-sort-field');
    const sortOrderFilter = document.getElementById('node-task-sort-order');

    const applyFilters = () => {
        if (selectedNode) {
            filterNodeTasks(selectedNode);
        }
    };

    // Remove old event listeners by cloning and replacing elements
    const newStatusFilter = statusFilter.cloneNode(true);
    statusFilter.parentNode.replaceChild(newStatusFilter, statusFilter);

    const newPriorityFilter = priorityFilter.cloneNode(true);
    priorityFilter.parentNode.replaceChild(newPriorityFilter, priorityFilter);

    const newSearchFilter = searchFilter.cloneNode(true);
    searchFilter.parentNode.replaceChild(newSearchFilter, searchFilter);

    const newProjectFilter = projectFilter.cloneNode(true);
    projectFilter.parentNode.replaceChild(newProjectFilter, projectFilter);

    const newTagsFilter = tagsFilter.cloneNode(true);
    tagsFilter.parentNode.replaceChild(newTagsFilter, tagsFilter);

    const newDateFieldFilter = dateFieldFilter.cloneNode(true);
    dateFieldFilter.parentNode.replaceChild(newDateFieldFilter, dateFieldFilter);

    const newDateStartFilter = dateStartFilter.cloneNode(true);
    dateStartFilter.parentNode.replaceChild(newDateStartFilter, dateStartFilter);

    const newDateEndFilter = dateEndFilter.cloneNode(true);
    dateEndFilter.parentNode.replaceChild(newDateEndFilter, dateEndFilter);

    const newSortFieldFilter = sortFieldFilter.cloneNode(true);
    sortFieldFilter.parentNode.replaceChild(newSortFieldFilter, sortFieldFilter);

    const newSortOrderFilter = sortOrderFilter.cloneNode(true);
    sortOrderFilter.parentNode.replaceChild(newSortOrderFilter, sortOrderFilter);

    // Add new event listeners
    newStatusFilter.onchange = applyFilters;
    newPriorityFilter.onchange = applyFilters;
    newSearchFilter.oninput = debounce(applyFilters, 300);
    newProjectFilter.oninput = debounce(applyFilters, 300);
    newTagsFilter.oninput = debounce(applyFilters, 300);
    newDateFieldFilter.onchange = applyFilters;
    newDateStartFilter.onchange = applyFilters;
    newDateEndFilter.onchange = applyFilters;
    newSortFieldFilter.onchange = applyFilters;
    newSortOrderFilter.onchange = applyFilters;
}

function filterNodeTasks(node) {
    const relatedTasks = getRelatedTasks(node);

    const statusFilter = document.getElementById('node-task-status-filter')?.value || '';
    const priorityFilter = document.getElementById('node-task-priority-filter')?.value || '';
    const searchFilter = document.getElementById('node-task-search-filter')?.value.toLowerCase() || '';
    const projectFilter = document.getElementById('node-task-project-filter')?.value.toLowerCase() || '';
    const tagsFilter = document.getElementById('node-task-tags-filter')?.value.toLowerCase() || '';
    const dateField = document.getElementById('node-task-date-field')?.value || 'due';
    const dateStart = document.getElementById('node-task-date-start')?.value || '';
    const dateEnd = document.getElementById('node-task-date-end')?.value || '';
    const sortField = document.getElementById('node-task-sort-field')?.value || 'due';
    const sortOrder = document.getElementById('node-task-sort-order')?.value || 'asc';

    let filteredTasks = relatedTasks;

    if (statusFilter) {
        filteredTasks = filteredTasks.filter(task => task.status === statusFilter);
    }

    if (priorityFilter) {
        filteredTasks = filteredTasks.filter(task =>
            task.calculated_priority === priorityFilter || task.priority === priorityFilter
        );
    }

    if (searchFilter) {
        filteredTasks = filteredTasks.filter(task =>
            task.title.toLowerCase().includes(searchFilter) ||
            (task.description && task.description.toLowerCase().includes(searchFilter))
        );
    }

    if (projectFilter) {
        filteredTasks = filteredTasks.filter(task =>
            task.project && task.project.toLowerCase().includes(projectFilter)
        );
    }

    if (tagsFilter) {
        const tagsArray = tagsFilter.split(',').map(tag => tag.trim()).filter(tag => tag);
        if (tagsArray.length > 0) {
            filteredTasks = filteredTasks.filter(task => {
                const taskTags = [
                    ...task.hybrid_tags?.bracket || [],
                    ...task.hybrid_tags?.hash || [],
                    ...task.hybrid_tags?.user || [],
                    ...(task.tags || [])
                ];
                return tagsArray.some(filterTag =>
                    taskTags.some(taskTag => taskTag.toLowerCase().includes(filterTag))
                );
            });
        }
    }

    // Apply unified date filter based on selected date field
    if (dateField && (dateStart || dateEnd)) {
        filteredTasks = filteredTasks.filter(task => {
            let taskDate;
            
            // Get the date based on the selected field
            switch (dateField) {
                case 'due':
                    taskDate = task.due;
                    break;
                case 'created_at':
                    taskDate = task.created_at;
                    break;
                case 'modified_at':
                    taskDate = task.modified_at;
                    break;
                default:
                    taskDate = task.due;
            }
            
            if (!taskDate) return false;
            
            const taskDateObj = parseDateInput(taskDate);
            if (!taskDateObj) return false;
            
            if (dateStart) {
                const startDate = parseDateInput(dateStart);
                if (startDate && taskDateObj < startDate) return false;
            }
            
            if (dateEnd) {
                const endDate = parseDateInput(dateEnd);
                if (endDate) {
                    // Set end date to end of day
                    endDate.setHours(23, 59, 59, 999);
                    if (taskDateObj > endDate) return false;
                }
            }
            
            return true;
        });
    }

    // Apply sorting
    if (sortField) {
        filteredTasks = sortTasksByField(filteredTasks, sortField, sortOrder);
    }

    displayNodeTasks(filteredTasks, node);
}

// Sort tasks by field with direction
function sortTasksByField(tasks, sortField, sortOrder = 'asc') {
    const sortedTasks = [...tasks];
    
    sortedTasks.sort((a, b) => {
        let comparison = 0;
        
        switch (sortField) {
            case 'due': {
                const aDue = a.due ? new Date(a.due).getTime() : -Infinity;
                const bDue = b.due ? new Date(b.due).getTime() : -Infinity;
                comparison = aDue - bDue;
                break;
            }
                
            case 'created_at': {
                const aCreated = a.created_at ? new Date(a.created_at).getTime() : -Infinity;
                const bCreated = b.created_at ? new Date(b.created_at).getTime() : -Infinity;
                comparison = aCreated - bCreated;
                break;
            }
                
            case 'modified_at': {
                const aModified = a.modified_at ? new Date(a.modified_at).getTime() : -Infinity;
                const bModified = b.modified_at ? new Date(b.modified_at).getTime() : -Infinity;
                comparison = aModified - bModified;
                break;
            }
                
            case 'priority':
                const priorityOrder = { 'critical': 0, 'high': 1, 'medium': 2, 'low': 3 };
                const aPriority = priorityOrder[a.calculated_priority || a.priority || 'medium'] || 2;
                const bPriority = priorityOrder[b.calculated_priority || b.priority || 'medium'] || 2;
                comparison = aPriority - bPriority;
                break;
                
            case 'title':
                comparison = a.title.localeCompare(b.title);
                break;
                
            default:
                comparison = 0;
        }
        
        return sortOrder === 'desc' ? -comparison : comparison;
    });
    
    return sortedTasks;
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

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
                taskTag.toLowerCase().startsWith(searchTerm)
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

// Make functions available globally
window.renderHierarchy = renderHierarchy;
window.closeTaskPanelHierarchy = closeTaskPanel;
window.initHierarchyFilters = initHierarchyFilters;
window.clearHierarchyFilters = clearHierarchyFilters;
window.refreshHierarchyVisualization = refreshHierarchyVisualization;

/**
 * Initialize hierarchy filter event listeners
 * Note: Network calls only happen when Apply button is clicked
 */
function initHierarchyFilters() {
    const tagSearchInput = document.getElementById('hierarchy-tag-search');
    const statusFilter = document.getElementById('hierarchy-status-filter');
    const dateStartInput = document.getElementById('hierarchy-date-start');
    const dateEndInput = document.getElementById('hierarchy-date-end');
    
    if (!tagSearchInput) return;
    
    // Tag search - only update filter state (no network call)
    tagSearchInput.addEventListener('input', function() {
        hierarchyFilters.tagSearch = (this.value || '').trim();
    });
    
    // Status filter - only update filter state (no network call)
    if (statusFilter) {
        statusFilter.addEventListener('change', function() {
            hierarchyFilters.status = this.value || '';
        });
    }
    
    // Date filters - only update filter state (no network call)
    if (dateStartInput) {
        dateStartInput.addEventListener('change', function() {
            hierarchyFilters.dateStart = this.value || '';
        });
    }
    
    if (dateEndInput) {
        dateEndInput.addEventListener('change', function() {
            hierarchyFilters.dateEnd = this.value || '';
        });
    }
}

/**
 * Refresh hierarchy visualization with filters
 */
async function refreshHierarchyVisualization() {
    // Build query params from filters
    const params = new URLSearchParams();
    
    if (hierarchyFilters.tagSearch && hierarchyFilters.tagSearch.length >= 3) {
        params.append('tag_search', hierarchyFilters.tagSearch);
    }
    
    if (hierarchyFilters.status) {
        params.append('status', hierarchyFilters.status);
    }
    
    if (hierarchyFilters.dateStart) {
        params.append('date_start', hierarchyFilters.dateStart);
    }
    
    if (hierarchyFilters.dateEnd) {
        params.append('date_end', hierarchyFilters.dateEnd);
    }
    
    try {
        const response = await fetch(`/api/hierarchy/filtered?${params.toString()}`);
        hierarchyData = await response.json();
        updateHierarchyVisualization();
    } catch (error) {
        console.error('Error refreshing hierarchy:', error);
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

/**
 * Update existing hierarchy visualization with new data
 */
function updateHierarchyVisualization() {
    const svg = d3.select('#hierarchy-viz');
    if (svg.empty()) return;
    
    const g = svg.select('g');
    if (g.empty()) return;
    
    // Clear existing content
    g.selectAll('*').remove();
    
    if (!hierarchyData.nodes || hierarchyData.nodes.length === 0) {
        g.append('text')
            .attr('x', '50%')
            .attr('y', '50%')
            .attr('text-anchor', 'middle')
            .attr('fill', '#6b7280')
            .text('No matching hierarchy data. Try adjusting filters.');
        return;
    }
    
    // Recreate visualization
    const width = svg.node().clientWidth || 800;
    const height = svg.node().clientHeight || 500;
    
    // Create links
    const link = g.append('g')
        .attr('class', 'links')
        .selectAll('line')
        .data(hierarchyData.links || [])
        .enter()
        .append('line')
        .attr('stroke', '#d1d5db')
        .attr('stroke-opacity', 0.7)
        .attr('stroke-width', d => Math.max(1, Math.sqrt(d.value || 1)));
    
    // Create nodes
    const node = g.append('g')
        .attr('class', 'nodes')
        .selectAll('circle')
        .data(hierarchyData.nodes || [])
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
    
    // Add labels with truncation
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
            d3.select(this)
                .attr('data-full-name', d.name)
                .on('mouseover', function(event) {
                    showLabelTooltip(event, d.name);
                })
                .on('mouseout', hideLabelTooltip);
        });
    
    // Restart simulation
    simulation = d3.forceSimulation(hierarchyData.nodes)
        .force('link', d3.forceLink(hierarchyData.links)
            .id(d => d.id)
            .distance(d => {
                const sourceLevel = hierarchyData.nodes.find(n => n.id === d.source)?.level || 0;
                const targetLevel = hierarchyData.nodes.find(n => n.id === d.target)?.level || 0;
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
    
    // Add drag behavior
    node.call(d3.drag()
        .on('start', dragstarted)
        .on('drag', dragged)
        .on('end', dragended));
}

// Implement centerVisualizationOnce to fit graph to screen
window.centerVisualizationOnce = function () {
    const svg = d3.select('#hierarchy-viz');
    const g = svg.select('g');
    if (svg.empty() || g.empty()) return;

    // Wait slightly for simulation to spread nodes out, or check immediately if stable
    // Using a small timeout to allow initial ticks to position nodes better
    setTimeout(() => {
        try {
            const bounds = g.node().getBBox();
            if (bounds.width === 0 || bounds.height === 0) return;

            const fullWidth = svg.node().clientWidth || 800;
            const fullHeight = svg.node().clientHeight || 500;
            const padding = 40;

            const width = bounds.width;
            const height = bounds.height;

            // Calculate scale to fit
            const midX = bounds.x + width / 2;
            const midY = bounds.y + height / 2;

            if (width === 0 || height === 0) return;

            const scale = 0.85 / Math.max(width / fullWidth, height / fullHeight);
            const translate = [
                fullWidth / 2 - scale * midX,
                fullHeight / 2 - scale * midY
            ];

            // Apply transform smoothly
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

// Ensure it runs after render
if (typeof window.centerVisualizationOnce === 'function') {
    // It's defined above
}
