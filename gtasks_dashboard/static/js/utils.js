/**
 * Utility Functions
 * Reusable utility functions for the dashboard
 */

/**
 * Debounce function to limit how often a function can be called
 * @param {Function} func - The function to debounce
 * @param {number} wait - The number of milliseconds to wait
 * @returns {Function} - The debounced function
 */
export function debounce(func, wait) {
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
 * Parse date string in DD/MM/YYYY or YYYY-MM-DD format
 * @param {string} dateString - The date string to parse
 * @returns {Date|null} - The parsed date or null if invalid
 */
export function parseDateInput(dateString) {
    if (!dateString) return null;
    
    // Try to parse DD/MM/YYYY format (common in India)
    if (dateString.includes('/')) {
        const parts = dateString.split('/');
        if (parts.length === 3) {
            const day = parseInt(parts[0], 10);
            const month = parseInt(parts[1], 10) - 1; // Month is 0-indexed
            const year = parseInt(parts[2], 10);
            return new Date(year, month, day, 0, 0, 0, 0);
        }
    }
    
    // Try to parse YYYY-MM-DD format (ISO format from date input)
    if (dateString.includes('-')) {
        const parts = dateString.split('-');
        if (parts.length === 3) {
            const year = parseInt(parts[0], 10);
            const month = parseInt(parts[1], 10) - 1;
            const day = parseInt(parts[2], 10);
            return new Date(year, month, day, 0, 0, 0, 0);
        }
    }
    
    // Fallback to standard Date parsing
    const date = new Date(dateString);
    return isNaN(date.getTime()) ? null : date;
}

/**
 * Format date to YYYY-MM-DD
 * @param {string} dateString - The date string to format
 * @returns {string} - The formatted date string
 */
export function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toISOString().split('T')[0];
}

/**
 * Calculate date status (overdue, today, future, none)
 * @param {string} dueDate - The due date string
 * @returns {string} - The date status
 */
export function getDateStatus(dueDate) {
    if (!dueDate) return 'none';
    
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    const due = new Date(dueDate);
    due.setHours(0, 0, 0, 0);
    
    if (due < today) return 'overdue';
    if (due.getTime() === today.getTime()) return 'today';
    return 'future';
}

/**
 * Generate date status badge HTML
 * @param {string} dateStatus - The date status
 * @returns {string} - The badge HTML
 */
export function getDateStatusBadge(dateStatus) {
    const badges = {
        'overdue': '<span class="date-status-badge overdue">⏳ Overdue</span>',
        'today': '<span class="date-status-badge today">📅 Today</span>',
        'future': '<span class="date-status-badge future">📅 Future</span>',
        'none': ''
    };
    return badges[dateStatus] || badges['none'];
}

/**
 * Generate compact date display for a task
 * @param {Object} task - The task object
 * @returns {string} - The HTML for date display
 */
export function getCompactDateDisplay(task) {
    const due = formatDate(task.due);
    const created = formatDate(task.created_at);
    const modified = formatDate(task.modified_at);
    
    return `<span class="compact-dates">
        <span class="date-label">D:${due}</span>
        <span class="date-label">C:${created}</span>
        <span class="date-label">M:${modified}</span>
    </span>`;
}

/**
 * Generate notes section HTML for a task
 * @param {Object} task - The task object
 * @returns {string} - The notes section HTML
 */
export function getNotesSection(task) {
    const notes = task.notes || task.description || '';
    if (!notes) return '';
    
    const truncated = notes.length > 100;
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

/**
 * Generate tags display HTML for a task
 * @param {Object} task - The task object
 * @returns {string} - The tags HTML
 */
export function getTagsDisplay(task) {
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

/**
 * Get all tags from a task as a flat array
 * @param {Object} task - The task object
 * @returns {Array} - Array of all tags
 */
export function getAllTags(task) {
    const tags = [];
    
    if (task.hybrid_tags) {
        if (task.hybrid_tags.bracket) tags.push(...task.hybrid_tags.bracket);
        if (task.hybrid_tags.hash) tags.push(...task.hybrid_tags.hash);
        if (task.hybrid_tags.user) tags.push(...task.hybrid_tags.user);
    }
    
    if (task.tags) {
        tags.push(...task.tags);
    }
    
    return tags;
}

/**
 * Sort tasks by field with direction
 * @param {Array} tasks - Array of tasks to sort
 * @param {string} sortField - Field to sort by
 * @param {string} sortOrder - 'asc' or 'desc'
 * @returns {Array} - Sorted tasks
 */
export function sortTasksByField(tasks, sortField, sortOrder = 'asc') {
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

/**
 * Filter tasks by multiple criteria
 * @param {Array} tasks - Array of tasks to filter
 * @param {Object} filters - Filter criteria
 * @returns {Array} - Filtered tasks
 */
export function filterTasksByCriteria(tasks, filters) {
    let filteredTasks = [...tasks];
    
    // Apply status filter
    if (filters.status) {
        filteredTasks = filteredTasks.filter(task => task.status === filters.status);
    }
    
    // Apply priority filter
    if (filters.priority) {
        filteredTasks = filteredTasks.filter(task =>
            task.calculated_priority === filters.priority || task.priority === filters.priority
        );
    }
    
    // Apply search filter
    if (filters.search) {
        const searchLower = filters.search.toLowerCase();
        filteredTasks = filteredTasks.filter(task =>
            task.title.toLowerCase().includes(searchLower) ||
            (task.description && task.description.toLowerCase().includes(searchLower))
        );
    }
    
    // Apply project filter
    if (filters.project) {
        filteredTasks = filteredTasks.filter(task =>
            task.project && task.project.toLowerCase().includes(filters.project)
        );
    }
    
    // Apply tags filter
    if (filters.tags) {
        const tagsArray = filters.tags.split(',').map(tag => tag.trim()).filter(tag => tag);
        if (tagsArray.length > 0) {
            filteredTasks = filteredTasks.filter(task => {
                const taskTags = getAllTags(task);
                return tagsArray.some(filterTag =>
                    taskTags.some(taskTag => taskTag.toLowerCase().includes(filterTag))
                );
            });
        }
    }
    
    // Apply date filter
    if (filters.dateField && (filters.dateStart || filters.dateEnd)) {
        filteredTasks = filteredTasks.filter(task => {
            let taskDate;
            
            switch (filters.dateField) {
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
            
            if (filters.dateStart) {
                const startDate = parseDateInput(filters.dateStart);
                if (startDate && taskDateObj < startDate) return false;
            }
            
            if (filters.dateEnd) {
                const endDate = parseDateInput(filters.dateEnd);
                if (endDate) {
                    endDate.setHours(23, 59, 59, 999);
                    if (taskDateObj > endDate) return false;
                }
            }
            
            return true;
        });
    }
    
    // Apply sorting
    if (filters.sortField) {
        filteredTasks = sortTasksByField(filteredTasks, filters.sortField, filters.sortOrder);
    }
    
    return filteredTasks;
}

/**
 * Check if deleted tasks should be hidden
 * @returns {boolean} - True if deleted tasks should be hidden
 */
export function shouldHideDeleted() {
    return localStorage.getItem('hideDeleted') === 'enabled';
}

/**
 * Filter out deleted tasks if setting is enabled
 * @param {Array} tasks - Array of tasks
 * @returns {Array} - Filtered tasks
 */
export function filterOutDeletedTasks(tasks) {
    if (!shouldHideDeleted()) {
        return tasks;
    }
    return tasks.filter(task => task.status !== 'deleted');
}

/**
 * Get priority class name
 * @param {string} priority - The priority value
 * @returns {string} - The priority class name
 */
export function getPriorityClass(priority) {
    return `priority-${priority || 'medium'}`;
}

/**
 * Get priority icon HTML
 * @param {string} priority - The priority value
 * @returns {string} - The priority icon HTML
 */
export function getPriorityIcon(priority) {
    const icons = {
        'critical': '<i class="fas fa-exclamation-circle"></i>',
        'high': '<i class="fas fa-arrow-up"></i>',
        'medium': '<i class="fas fa-minus"></i>',
        'low': '<i class="fas fa-arrow-down"></i>'
    };
    return icons[priority || 'medium'] || '<i class="fas fa-minus"></i>';
}

/**
 * Get status class name
 * @param {string} status - The status value
 * @returns {string} - The status class name
 */
export function getStatusClass(status) {
    const classes = {
        'completed': 'status-completed',
        'in_progress': 'status-in-progress',
        'pending': 'status-pending'
    };
    return classes[status] || 'status-pending';
}
