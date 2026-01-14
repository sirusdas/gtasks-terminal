/**
 * Advanced Filter Functions
 * Reusable filtering logic for task management
 */

// Filter task list with multiple criteria
function filterTasksList(tasks, filters) {
    if (!tasks || !Array.isArray(tasks)) return [];
    
    return tasks.filter(task => {
        // Status filter
        if (filters.status && filters.status.length > 0) {
            if (!filters.status.includes(task.status)) return false;
        }
        
        // Priority filter
        if (filters.priority && filters.priority.length > 0) {
            const taskPriority = task.calculated_priority || task.priority;
            if (!filters.priority.includes(taskPriority)) return false;
        }
        
        // Project filter
        if (filters.project && filters.project.length > 0) {
            if (!filters.project.includes(task.project || 'unassigned')) return false;
        }
        
        // Tags filter
        if (filters.tags && filters.tags.length > 0) {
            const taskTags = [
                ...task.hybrid_tags?.bracket || [],
                ...task.hybrid_tags?.hash || [],
                ...task.hybrid_tags?.user || [],
                ...(task.tags || [])
            ];
            const hasMatchingTag = filters.tags.some(filterTag => 
                taskTags.some(taskTag => taskTag.toLowerCase().includes(filterTag.toLowerCase()))
            );
            if (!hasMatchingTag) return false;
        }
        
        // Search filter
        if (filters.search) {
            const searchLower = filters.search.toLowerCase();
            const matchesTitle = task.title.toLowerCase().includes(searchLower);
            const matchesDescription = task.description?.toLowerCase().includes(searchLower);
            const matchesNotes = task.notes?.toLowerCase().includes(searchLower);
            const matchesTags = task.tags?.some(tag => tag.toLowerCase().includes(searchLower));
            
            if (!matchesTitle && !matchesDescription && !matchesNotes && !matchesTags) {
                return false;
            }
        }
        
        // Date range filter - due date
        if (filters.due_date_range) {
            if (!isDateInRange(task.due, filters.due_date_range)) return false;
        }
        
        // Date range filter - created date
        if (filters.created_date_range) {
            if (!isDateInRange(task.created_at, filters.created_date_range)) return false;
        }
        
        // Account filter
        if (filters.account && filters.account !== task.account) {
            return false;
        }
        
        return true;
    });
}

// Check if date falls within range
function isDateInRange(dateStr, range) {
    if (!dateStr || !range) return true;
    
    const taskDate = new Date(dateStr);
    const start = range.start ? new Date(range.start) : null;
    const end = range.end ? new Date(range.end) : null;
    
    if (start && taskDate < start) return false;
    if (end && taskDate > end) return false;
    
    return true;
}

// Sort tasks
function sortTasks(tasks, sortBy = 'due', sortOrder = 'asc') {
    if (!tasks) return [];
    
    return [...tasks].sort((a, b) => {
        let comparison = 0;
        
        switch (sortBy) {
            case 'due':
                if (!a.due && !b.due) comparison = 0;
                else if (!a.due) comparison = 1;
                else if (!b.due) comparison = -1;
                else comparison = new Date(a.due).getTime() - new Date(b.due).getTime();
                break;
                
            case 'priority':
                const priorityOrder = { 'critical': 4, 'high': 3, 'medium': 2, 'low': 1 };
                comparison = (priorityOrder[b.calculated_priority || b.priority] || 0) - 
                            (priorityOrder[a.calculated_priority || a.priority] || 0);
                break;
                
            case 'created':
                comparison = new Date(a.created_at || 0).getTime() - new Date(b.created_at || 0).getTime();
                break;
                
            case 'title':
                comparison = a.title.localeCompare(b.title);
                break;
                
            case 'status':
                const statusOrder = { 'completed': 0, 'in_progress': 1, 'pending': 2 };
                comparison = (statusOrder[a.status] || 3) - (statusOrder[b.status] || 3);
                break;
                
            default:
                comparison = 0;
        }
        
        return sortOrder === 'desc' ? -comparison : comparison;
    });
}

// Get unique values for a field
function getUniqueValues(tasks, field) {
    if (!tasks) return [];
    
    const values = new Set();
    tasks.forEach(task => {
        if (field === 'tags') {
            // Collect all tags
            if (task.hybrid_tags) {
                task.hybrid_tags.bracket.forEach(t => values.add(t));
                task.hybrid_tags.hash.forEach(t => values.add(t));
                task.hybrid_tags.user.forEach(t => values.add(t));
            }
            task.tags?.forEach(t => values.add(t));
        } else if (field === 'project') {
            values.add(task.project || 'unassigned');
        } else {
            values.add(task[field]);
        }
    });
    
    return Array.from(values).sort();
}

// Get value counts for a field
function getValueCounts(tasks, field) {
    if (!tasks) return {};
    
    const counts = {};
    tasks.forEach(task => {
        let value;
        if (field === 'tags') {
            const tags = task.hybrid_tags ? 
                [...task.hybrid_tags.bracket, ...task.hybrid_tags.hash, ...task.hybrid_tags.user] : 
                task.tags || [];
            tags.forEach(tag => {
                counts[tag] = (counts[tag] || 0) + 1;
            });
        } else if (field === 'priority') {
            value = task.calculated_priority || task.priority;
            counts[value] = (counts[value] || 0) + 1;
        } else if (field === 'status') {
            value = task.status;
            counts[value] = (counts[value] || 0) + 1;
        } else {
            value = task[field] || 'unknown';
            counts[value] = (counts[value] || 0) + 1;
        }
    });
    
    return counts;
}

// Debounce utility
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

// Throttle utility
function throttle(func, limit) {
    let inThrottle;
    return function executedFunction(...args) {
        if (!inThrottle) {
            func(...args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Export functions for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        filterTasksList,
        sortTasks,
        getUniqueValues,
        getValueCounts,
        isDateInRange,
        debounce,
        throttle
    };
}
