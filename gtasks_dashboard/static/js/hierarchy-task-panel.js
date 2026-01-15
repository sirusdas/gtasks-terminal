/**
 * Hierarchy Task Panel Module
 * Handles task display in the hierarchy panel
 */

import { getDateStatus, getDateStatusBadge, getCompactDateDisplay, getNotesSection, getTagsDisplay } from './utils.js';
import { getSelectedNode } from './hierarchy-interactions.js';

/**
 * Load node tasks and display them
 */
export function loadNodeTasks(node) {
    const relatedTasks = getRelatedTasks(node);
    displayNodeTasks(relatedTasks, node);
    setupTaskFilters(node);
}

/**
 * Get related tasks for a node
 */
function getRelatedTasks(node) {
    const allTasks = window.dashboardData?.tasks || [];
    
    let filteredTasks = allTasks;
    
    // Filter out deleted tasks
    if (window.shouldHideDeleted && window.shouldHideDeleted()) {
        filteredTasks = filteredTasks.filter(task => task.status !== 'deleted');
    }
    
    // Get hierarchy filters from global state
    const hierarchyFilters = window.hierarchyFilters || {};
    
    // Apply filters
    if (hierarchyFilters.status) {
        filteredTasks = filteredTasks.filter(task => task.status === hierarchyFilters.status);
    }
    
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

    // Get dependent tasks
    const dependentTasks = getDependentTasks(relatedTasks, filteredTasks);

    const allRelatedTasks = [...relatedTasks];
    dependentTasks.forEach(depTask => {
        if (!allRelatedTasks.find(t => t.id === depTask.id)) {
            allRelatedTasks.push(depTask);
        }
    });

    return allRelatedTasks;
}

/**
 * Get dependent tasks
 */
function getDependentTasks(tasks, allTasks) {
    const dependentTasks = [];
    const taskIds = new Set(tasks.map(t => t.id));

    allTasks.forEach(task => {
        if (task.dependencies && task.dependencies.length > 0) {
            const hasDependency = task.dependencies.some(depId => taskIds.has(depId));
            if (hasDependency) {
                dependentTasks.push(task);
            }
        }

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

/**
 * Display node tasks in the panel
 */
export function displayNodeTasks(tasks, node) {
    const container = document.getElementById('node-tasks-grid');
    if (!container) return;

    container.innerHTML = '';

    if (tasks.length === 0) {
        container.innerHTML = '<p style="text-align: center; color: #6b7280; grid-column: 1/-1;">No tasks found for this node.</p>';
        return;
    }
    
    // Sort by due date descending
    tasks.sort((a, b) => {
        const aDue = a.due ? new Date(a.due).getTime() : -Infinity;
        const bDue = b.due ? new Date(b.due).getTime() : -Infinity;
        return bDue - aDue;
    });

    tasks.forEach(task => {
        const taskCard = createNodeTaskCard(task, node);
        container.appendChild(taskCard);
    });
}

/**
 * Create a task card for the node panel
 */
function createNodeTaskCard(task, node) {
    const card = document.createElement('div');
    card.className = 'node-task-card';
    card.setAttribute('data-task-id', task.id);

    const priorityClass = `priority-${task.calculated_priority || 'medium'}`;
    const priorityIcon = {
        'critical': '<i class="fas fa-exclamation-circle"></i>',
        'high': '<i class="fas fa-arrow-up"></i>',
        'medium': '<i class="fas fa-minus"></i>',
        'low': '<i class="fas fa-arrow-down"></i>'
    }[task.calculated_priority || 'medium'] || '<i class="fas fa-minus"></i>';

    const dateStatus = getDateStatus(task.due);
    const dateStatusBadge = getDateStatusBadge(dateStatus);
    const compactDates = getCompactDateDisplay(task);
    const notesSection = getNotesSection(task);
    const tagsDisplay = getTagsDisplay(task);

    const hasDeps = task.dependencies && task.dependencies.length > 0;
    const depsInfo = hasDeps ? `<small style="color: #f59e0b; font-size: 0.7rem; display: block; margin-top: 0.25rem;"><i class="fas fa-link"></i> ${task.dependencies.length} dependency(ies)</small>` : '';

    // Complete button - show checkmark for incomplete, completed for complete
    const isCompleted = task.status === 'completed';
    const completeBtnHtml = `
        <div class="task-complete-btn ${isCompleted ? 'completed' : ''}" 
             onclick="${isCompleted ? '' : `completeTask('${task.id}')`}"
             title="${isCompleted ? 'Completed' : 'Mark as complete'}"
             style="cursor: ${isCompleted ? 'default' : 'pointer'}; font-size: 1.2rem;">
            ${isCompleted ? '✅' : '⭕'}
        </div>
    `;

    card.innerHTML = `
        <div class="node-task-header">
            ${completeBtnHtml}
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
        ${task.account ? `<small style="color: #9ca3af; font-size: 0.75rem; margin-top: 0.25rem; display: block;">Account: ${task.account}</small>` : ''}
        ${task.list_title ? `<small style="color: #8b5cf6; font-size: 0.75rem; margin-top: 0.5rem; display: block;"><i class="fas fa-list"></i> List: ${task.list_title}</small>` : ''}
    `;

    // Add click handler for expanding notes
    const notesToggle = card.querySelector('.notes-toggle');
    if (notesToggle) {
        notesToggle.addEventListener('click', function() {
            const notesContent = this.nextElementSibling;
            const isExpanded = this.getAttribute('data-expanded') === 'true';
            
            if (isExpanded) {
                // Collapse
                notesContent.style.maxHeight = '0px';
                this.textContent = 'Show more 📓';
                this.setAttribute('data-expanded', 'false');
            } else {
                // Expand
                notesContent.style.maxHeight = notesContent.scrollHeight + 'px';
                this.textContent = 'Show less 📓';
                this.setAttribute('data-expanded', 'true');
            }
        });
    }

    return card;
}

/**
 * Setup task filters for node panel
 */
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
        const currentNode = getSelectedNode();
        if (currentNode) {
            filterNodeTasks(currentNode);
        }
    };

    // Clone and replace to remove old event listeners
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

/**
 * Filter node tasks
 */
export function filterNodeTasks(node) {
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

    if (dateField && (dateStart || dateEnd)) {
        filteredTasks = filteredTasks.filter(task => {
            let taskDate;
            switch (dateField) {
                case 'due': taskDate = task.due; break;
                case 'created_at': taskDate = task.created_at; break;
                case 'modified_at': taskDate = task.modified_at; break;
                default: taskDate = task.due;
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

// Re-export for global use
window.loadNodeTasksHierarchy = loadNodeTasks;
window.filterNodeTasksHierarchy = filterNodeTasks;

/**
 * Debounce helper
 */
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
 * Sort tasks by field
 */
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
            case 'priority': {
                const priorityOrder = { 'critical': 0, 'high': 1, 'medium': 2, 'low': 3 };
                const aPriority = priorityOrder[a.calculated_priority || a.priority || 'medium'] || 2;
                const bPriority = priorityOrder[b.calculated_priority || b.priority || 'medium'] || 2;
                comparison = aPriority - bPriority;
                break;
            }
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

/**
 * Parse date input
 */
function parseDateInput(dateString) {
    if (!dateString) return null;
    
    if (dateString.includes('/')) {
        const parts = dateString.split('/');
        if (parts.length === 3) {
            const day = parseInt(parts[0], 10);
            const month = parseInt(parts[1], 10) - 1;
            const year = parseInt(parts[2], 10);
            return new Date(year, month, day, 0, 0, 0, 0);
        }
    }
    
    if (dateString.includes('-')) {
        const parts = dateString.split('-');
        if (parts.length === 3) {
            const year = parseInt(parts[0], 10);
            const month = parseInt(parts[1], 10) - 1;
            const day = parseInt(parts[2], 10);
            return new Date(year, month, day, 0, 0, 0, 0);
        }
    }
    
    const date = new Date(dateString);
    return isNaN(date.getTime()) ? null : date;
}
