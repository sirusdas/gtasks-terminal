/**
 * Hierarchy Filters Module
 * Handles filtering hierarchy data by tags, status, and date range
 */

// Filter state
export const hierarchyFilters = {
    tagSearch: '',
    status: '',
    dateStart: '',
    dateEnd: ''
};

/**
 * Initialize hierarchy filter event listeners
 */
export function initHierarchyFilters() {
    const tagSearchInput = document.getElementById('hierarchy-tag-search');
    const statusFilter = document.getElementById('hierarchy-status-filter');
    const dateStartInput = document.getElementById('hierarchy-date-start');
    const dateEndInput = document.getElementById('hierarchy-date-end');
    
    if (!tagSearchInput) return;
    
    tagSearchInput.addEventListener('input', function() {
        hierarchyFilters.tagSearch = (this.value || '').trim();
    });
    
    if (statusFilter) {
        statusFilter.addEventListener('change', function() {
            hierarchyFilters.status = this.value || '';
        });
    }
    
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
    
    // Store globally for other modules
    window.hierarchyFilters = hierarchyFilters;
}

/**
 * Parse DD/MM/YYYY date string to YYYY-MM-DD format for API
 */
function parseDMYToYMD(dateString) {
    if (!dateString) return null;
    
    // Handle DD/MM/YYYY format
    if (dateString.includes('/')) {
        const parts = dateString.split('/');
        if (parts.length === 3) {
            const day = parseInt(parts[0], 10);
            const month = parseInt(parts[1], 10);
            const year = parseInt(parts[2], 10);
            
            // Validate ranges
            if (day < 1 || day > 31 || month < 1 || month > 12 || year < 2000 || year > 2100) {
                return null;
            }
            
            // Pad with zeros
            const paddedMonth = month.toString().padStart(2, '0');
            const paddedDay = day.toString().padStart(2, '0');
            
            return `${year}-${paddedMonth}-${paddedDay}`;
        }
    }
    
    // Already in YYYY-MM-DD format
    if (dateString.includes('-') && dateString.length === 10) {
        return dateString;
    }
    
    return null;
}

/**
 * Refresh hierarchy visualization with filters
 */
export async function refreshHierarchyVisualization() {
    console.log('[HierarchyFilters] refreshHierarchyVisualization called');
    console.log('[HierarchyFilters] Current filters:', hierarchyFilters);
    
    const params = new URLSearchParams();
    
    if (hierarchyFilters.tagSearch && hierarchyFilters.tagSearch.length >= 3) {
        params.append('tag_search', hierarchyFilters.tagSearch);
        console.log('[HierarchyFilters] Tag filter added:', hierarchyFilters.tagSearch);
    }
    
    if (hierarchyFilters.status) {
        params.append('status', hierarchyFilters.status);
        console.log('[HierarchyFilters] Status filter added:', hierarchyFilters.status);
    }
    
    if (hierarchyFilters.dateStart) {
        const apiDateStart = parseDMYToYMD(hierarchyFilters.dateStart);
        console.log('[HierarchyFilters] Date start input:', hierarchyFilters.dateStart, '-> API format:', apiDateStart);
        if (apiDateStart) {
            params.append('date_start', apiDateStart);
        }
    }
    
    if (hierarchyFilters.dateEnd) {
        const apiDateEnd = parseDMYToYMD(hierarchyFilters.dateEnd);
        console.log('[HierarchyFilters] Date end input:', hierarchyFilters.dateEnd, '-> API format:', apiDateEnd);
        if (apiDateEnd) {
            params.append('date_end', apiDateEnd);
        }
    }
    
    const apiUrl = `/api/hierarchy/filtered?${params.toString()}`;
    console.log('[HierarchyFilters] Calling API:', apiUrl);
    
    try {
        const response = await fetch(apiUrl);
        console.log('[HierarchyFilters] API response status:', response.status);
        const hierarchyData = await response.json();
        console.log('[HierarchyFilters] API response data:', hierarchyData);
        console.log('[HierarchyFilters] Nodes:', hierarchyData.nodes?.length, 'Links:', hierarchyData.links?.length);
        
        // Update window.hierarchyData before updating visualization
        window.hierarchyData = hierarchyData;
        console.log('[HierarchyFilters] window.hierarchyData updated');
        
        if (window.updateHierarchyVisualization) {
            console.log('[HierarchyFilters] Calling window.updateHierarchyVisualization');
            window.updateHierarchyVisualization(hierarchyData);
        } else {
            console.error('[HierarchyFilters] window.updateHierarchyVisualization is NOT defined!');
        }
    } catch (error) {
        console.error('[HierarchyFilters] Error refreshing hierarchy:', error);
    }
}

/**
 * Clear all hierarchy filters
 */
export function clearHierarchyFilters() {
    hierarchyFilters.tagSearch = '';
    hierarchyFilters.status = '';
    hierarchyFilters.dateStart = '';
    hierarchyFilters.dateEnd = '';
    
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
 * Filter hierarchy data by tags
 */
export function filterHierarchyByTags(data, tagSearch) {
    if (!tagSearch || tagSearch.length < 3) {
        return data;
    }
    
    const searchTerms = tagSearch.split(',')
        .map(term => term.trim().toLowerCase())
        .filter(term => term.length >= 3);
    
    if (searchTerms.length === 0) {
        return data;
    }
    
    const tasks = window.dashboardData?.tasks || [];
    
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
    
    const matchingTagIds = new Set();
    matchingTasks.forEach(task => {
        if (task.hybrid_tags) {
            const allTags = [
                ...task.hybrid_tags.bracket || [],
                ...task.hybrid_tags.hash || [],
                ...task.hybrid_tags.user || []
            ];
            allTags.forEach(tag => {
                const tagId = `tag_${tag}`;
                matchingTagIds.add(tagId);
            });
        }
    });
    
    const filteredNodes = data.nodes.filter(node => {
        if (node.level <= 2) return true;
        if (node.type === 'tag' && matchingTagIds.has(node.id)) return true;
        return false;
    });
    
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
 */
export function filterHierarchyByDate(data, dateField, dateStart, dateEnd) {
    if (!dateStart && !dateEnd) {
        return data;
    }
    
    const tasks = window.dashboardData?.tasks || [];
    
    // Convert DD/MM/YYYY to YYYY-MM-DD for JavaScript Date parsing
    let startDate = dateStart ? parseDMYToYMD(dateStart) : null;
    let endDate = dateEnd ? parseDMYToYMD(dateEnd) : null;
    
    // If parsing failed, try using the raw date
    if (!startDate && dateStart) startDate = new Date(dateStart);
    if (!endDate && dateEnd) endDate = new Date(dateEnd);
    
    if (startDate && !(startDate instanceof Date)) startDate = new Date(startDate);
    if (endDate && !(endDate instanceof Date)) endDate = new Date(endDate);
    
    if (endDate) {
        endDate.setHours(23, 59, 59, 999);
    }
    
    const matchingTasks = tasks.filter(task => {
        const taskDate = task[dateField] || task.due;
        if (!taskDate) return false;
        
        const taskDateObj = new Date(taskDate);
        
        if (startDate && taskDateObj < startDate) return false;
        if (endDate && taskDateObj > endDate) return false;
        
        return true;
    });
    
    const matchingTaskIds = new Set(matchingTasks.map(t => t.id));
    
    const matchingTagIds = new Set();
    matchingTasks.forEach(task => {
        if (task.hybrid_tags) {
            const allTags = [
                ...task.hybrid_tags.bracket || [],
                ...task.hybrid_tags.hash || [],
                ...task.hybrid_tags.user || []
            ];
            allTags.forEach(tag => {
                const tagId = `tag_${tag}`;
                matchingTagIds.add(tagId);
            });
        }
    });
    
    const priorityCounts = { critical: 0, high: 0, medium: 0, low: 0 };
    const categoryCounts = {};
    
    matchingTasks.forEach(task => {
        const priority = task.calculated_priority || 'medium';
        if (priorityCounts.hasOwnProperty(priority)) {
            priorityCounts[priority]++;
        }
        
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
    
    const filteredNodes = data.nodes.filter(node => {
        if (node.level === 0) return true;
        
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
 * Filter hierarchy data by status
 */
export function filterHierarchyByStatus(data, status) {
    if (!status) {
        return data;
    }
    
    const tasks = window.dashboardData?.tasks || [];
    
    const matchingTasks = tasks.filter(task => task.status === status);
    
    const priorityCounts = { critical: 0, high: 0, medium: 0, low: 0 };
    const categoryCounts = {};
    
    matchingTasks.forEach(task => {
        const priority = task.calculated_priority || 'medium';
        if (priorityCounts.hasOwnProperty(priority)) {
            priorityCounts[priority]++;
        }
        
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
    
    const filteredNodes = data.nodes.filter(node => {
        if (node.level === 0) return true;
        
        if (node.type === 'priority') {
            const priority = node.priority || node.name.toLowerCase().split(' ')[0];
            return priorityCounts[priority] > 0;
        }
        
        if (node.type === 'category') {
            const category = node.id.replace('category_', '');
            return (categoryCounts[category] || 0) > 0;
        }
        
        if (node.type === 'tag') {
            const tag = node.id.replace('tag_', '');
            return matchingTasks.some(task => {
                if (!task.hybrid_tags) return false;
                const allTags = [
                    ...task.hybrid_tags.bracket || [],
                    ...task.hybrid_tags.hash || [],
                    ...task.hybrid_tags.user || []
                ];
                return allTags.some(t => t.toLowerCase().includes(tag.toLowerCase()));
            });
        }
        
        return true;
    });
    
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
 */
export function applyHierarchyFilters(hierarchyData) {
    let filteredData = hierarchyData;
    
    if (hierarchyFilters.tagSearch && hierarchyFilters.tagSearch.length >= 3) {
        filteredData = filterHierarchyByTags(filteredData, hierarchyFilters.tagSearch);
    }
    
    if (hierarchyFilters.status) {
        filteredData = filterHierarchyByStatus(filteredData, hierarchyFilters.status);
    }
    
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

// Expose globally for backward compatibility
window.initHierarchyFilters = initHierarchyFilters;
window.clearHierarchyFilters = clearHierarchyFilters;
window.refreshHierarchyVisualization = refreshHierarchyVisualization;
window.applyChartFilters = refreshHierarchyVisualization;  // Alias for Apply button
window.hierarchyFilters = hierarchyFilters;
