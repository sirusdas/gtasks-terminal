/**
 * Hierarchy Visualization with D3.js
 * Handles node click, dependent tasks display, and advanced filtering
 */

// hierarchyData is used globally - declared here
let hierarchyData = {};
let selectedNode = null;
let simulation = null;

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

    // Smooth slide down animation
    panel.style.maxHeight = '0';
    panel.style.overflow = 'hidden';
    setTimeout(() => {
        panel.style.transition = 'max-height 0.3s ease';
        panel.style.maxHeight = '40vh';
        panel.style.overflow = 'auto';
    }, 10);
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

    let filteredTasks = [];

    switch (node.type) {
        case 'priority':
            const priority = (node.priority || node.name.toLowerCase().split(' ')[0]);
            filteredTasks = allTasks.filter(task =>
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
            filteredTasks = allTasks.filter(task => {
                const taskText = `${task.title} ${task.description}`.toLowerCase();
                return keywords.some(keyword => taskText.includes(keyword));
            });
            break;

        case 'tag':
            const tag = node.id.replace('tag_', '');
            filteredTasks = allTasks.filter(task => {
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
            filteredTasks = allTasks.filter(task => task.account === account);
            break;

        case 'meta':
            filteredTasks = allTasks.slice(0, 10);
            break;

        default:
            filteredTasks = allTasks;
    }

    // Get dependent tasks
    const dependentTasks = getDependentTasks(filteredTasks, allTasks);

    // Combine filtered tasks with their dependents
    const allRelatedTasks = [...filteredTasks];
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

    // Check if this task has dependencies
    const hasDeps = task.dependencies && task.dependencies.length > 0;
    const depsInfo = hasDeps ? `<small style="color: #f59e0b; font-size: 0.7rem; display: block; margin-top: 0.25rem;"><i class="fas fa-link"></i> ${task.dependencies.length} dependency(ies)</small>` : '';

    card.innerHTML = `
        <div class="node-task-title">${task.title}</div>
        ${task.description ? `<p style="color: #6b7280; font-size: 0.875rem; margin: 0.5rem 0;">${task.description}</p>` : ''}
        <div class="node-task-meta">
            <span class="node-task-priority ${priorityClass}">
                ${priorityIcon} ${task.calculated_priority || 'medium'}
            </span>
            <span class="node-task-status">${task.status || 'pending'}</span>
        </div>
        ${depsInfo}
        ${task.account ? `<small style="color: #9ca3af; font-size: 0.75rem; margin-top: 0.5rem; display: block;">Account: ${task.account}</small>` : ''}
    `;

    return card;
}

function setupTaskFilters(node) {
    const statusFilter = document.getElementById('node-task-status-filter');
    const priorityFilter = document.getElementById('node-task-priority-filter');
    const searchFilter = document.getElementById('node-task-search-filter');
    const projectFilter = document.getElementById('node-task-project-filter');
    const tagsFilter = document.getElementById('node-task-tags-filter');
    const dueDateStart = document.getElementById('node-task-due-date-start');
    const dueDateEnd = document.getElementById('node-task-due-date-end');
    const createdDateStart = document.getElementById('node-task-created-date-start');
    const createdDateEnd = document.getElementById('node-task-created-date-end');

    const applyFilters = () => {
        if (selectedNode) {
            filterNodeTasks(selectedNode);
        }
    };

    // Remove old event listeners
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

    const newDueDateStart = dueDateStart.cloneNode(true);
    dueDateStart.parentNode.replaceChild(newDueDateStart, dueDateStart);

    const newDueDateEnd = dueDateEnd.cloneNode(true);
    dueDateEnd.parentNode.replaceChild(newDueDateEnd, dueDateEnd);

    const newCreatedDateStart = createdDateStart.cloneNode(true);
    createdDateStart.parentNode.replaceChild(newCreatedDateStart, createdDateStart);

    const newCreatedDateEnd = createdDateEnd.cloneNode(true);
    createdDateEnd.parentNode.replaceChild(newCreatedDateEnd, createdDateEnd);

    // Add new event listeners
    newStatusFilter.onchange = applyFilters;
    newPriorityFilter.onchange = applyFilters;
    newSearchFilter.oninput = debounce(applyFilters, 300);
    newProjectFilter.oninput = debounce(applyFilters, 300);
    newTagsFilter.oninput = debounce(applyFilters, 300);
    newDueDateStart.onchange = applyFilters;
    newDueDateEnd.onchange = applyFilters;
    newCreatedDateStart.onchange = applyFilters;
    newCreatedDateEnd.onchange = applyFilters;
}

function filterNodeTasks(node) {
    const relatedTasks = getRelatedTasks(node);

    const statusFilter = document.getElementById('node-task-status-filter')?.value || '';
    const priorityFilter = document.getElementById('node-task-priority-filter')?.value || '';
    const searchFilter = document.getElementById('node-task-search-filter')?.value.toLowerCase() || '';
    const projectFilter = document.getElementById('node-task-project-filter')?.value.toLowerCase() || '';
    const tagsFilter = document.getElementById('node-task-tags-filter')?.value.toLowerCase() || '';
    const dueDateStart = document.getElementById('node-task-due-date-start')?.value || '';
    const dueDateEnd = document.getElementById('node-task-due-date-end')?.value || '';
    const createdDateStart = document.getElementById('node-task-created-date-start')?.value || '';
    const createdDateEnd = document.getElementById('node-task-created-date-end')?.value || '';

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

    if (dueDateStart) {
        filteredTasks = filteredTasks.filter(task => {
            if (!task.due) return false;
            return new Date(task.due) >= new Date(dueDateStart);
        });
    }

    if (dueDateEnd) {
        filteredTasks = filteredTasks.filter(task => {
            if (!task.due) return false;
            return new Date(task.due) <= new Date(dueDateEnd);
        });
    }

    if (createdDateStart) {
        filteredTasks = filteredTasks.filter(task => {
            if (!task.created_at) return false;
            return new Date(task.created_at) >= new Date(createdDateStart);
        });
    }

    if (createdDateEnd) {
        filteredTasks = filteredTasks.filter(task => {
            if (!task.created_at) return false;
            return new Date(task.created_at) <= new Date(createdDateEnd);
        });
    }

    displayNodeTasks(filteredTasks, node);
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

// Make functions available globally
window.renderHierarchy = renderHierarchy;
window.closeTaskPanelHierarchy = closeTaskPanel;

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
