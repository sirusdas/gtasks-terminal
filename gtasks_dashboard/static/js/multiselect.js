/**
 * Multiselect Component
 * Reusable multiselect with search and suggest functionality
 */

import { parseDateInput, getTaskDate } from './utils.js';

// Create multiselect element
export function createMultiselect(config) {
    const {
        id,
        placeholder = 'Select options...',
        options = [],
        initialValues = [],
        onChange = () => {},
        searchMinChars = 0,
        showCounts = false
    } = config;

    // Container
    const container = document.createElement('div');
    container.className = 'multiselect-container';
    container.id = `${id}-container`;

    // Hidden input to store selected values
    const hiddenInput = document.createElement('input');
    hiddenInput.type = 'hidden';
    hiddenInput.id = id;
    hiddenInput.name = id;
    container.appendChild(hiddenInput);

    // Selection display area (selected tags)
    const selectionArea = document.createElement('div');
    selectionArea.className = 'multiselect-selection';
    container.appendChild(selectionArea);

    // Input wrapper
    const inputWrapper = document.createElement('div');
    inputWrapper.className = 'multiselect-input-wrapper';

    // Search input
    const searchInput = document.createElement('input');
    searchInput.type = 'text';
    searchInput.className = 'multiselect-search';
    searchInput.placeholder = placeholder;
    searchInput.id = `${id}-search`;
    inputWrapper.appendChild(searchInput);

    // Dropdown toggle button
    const toggleBtn = document.createElement('button');
    toggleBtn.type = 'button';
    toggleBtn.className = 'multiselect-toggle';
    toggleBtn.innerHTML = '<i class="fas fa-chevron-down"></i>';
    inputWrapper.appendChild(toggleBtn);

    container.appendChild(inputWrapper);

    // Suggestions dropdown
    const dropdown = document.createElement('div');
    dropdown.className = 'multiselect-dropdown';
    dropdown.id = `${id}-dropdown`;
    dropdown.style.display = 'none';
    container.appendChild(dropdown);

    // State
    let isOpen = false;
    let currentOptions = [...options];
    let selectedValues = [...initialValues];

    // Helper: get display label for a selected value
    function getOptionLabel(val) {
        const found = currentOptions.find(opt => {
            if (typeof opt === 'object') {
                const optVal = opt.value !== undefined ? opt.value : opt.label;
                return String(optVal) === String(val) || String(opt.label) === String(val);
            }
            return String(opt) === String(val);
        });
        if (found && typeof found === 'object') {
            return found.label;
        }
        return val;
    }

    // Update display
    function updateDisplay() {
        selectionArea.innerHTML = '';
        hiddenInput.value = JSON.stringify(selectedValues);

        selectedValues.forEach(value => {
            const tag = document.createElement('span');
            tag.className = 'multiselect-tag';
            const displayLabel = getOptionLabel(value);
            tag.innerHTML = `
                ${displayLabel}
                <button type="button" class="multiselect-remove" data-value="${value}">&times;</button>
            `;
            selectionArea.appendChild(tag);
        });
    }

    // Event delegation for remove buttons (fixed to work dynamically)
    selectionArea.addEventListener('click', (e) => {
        if (e.target.classList.contains('multiselect-remove')) {
            e.stopPropagation();
            const value = e.target.dataset.value;
            console.log('[Multiselect] Removing tag:', value);
            removeValue(value);
        }
    });

    // Add value
    function addValue(value) {
        if (!selectedValues.includes(value)) {
            selectedValues.push(value);
            updateDisplay();
            onChange(selectedValues);
        }
        searchInput.value = '';
        filterOptions('');
    }

    // Remove value
    function removeValue(value) {
        selectedValues = selectedValues.filter(v => String(v) !== String(value));
        updateDisplay();
        onChange(selectedValues);
    }

    // Filter options based on search
    function filterOptions(searchTerm) {
        const term = searchTerm.toLowerCase().trim();
        
        if (term.length < searchMinChars) {
            dropdown.innerHTML = '<div class="multiselect-empty">Type to search...</div>';
            return;
        }

        const filtered = currentOptions.filter(opt => {
            const optLabel = typeof opt === 'object' ? opt.label : opt;
            const optVal = typeof opt === 'object' && opt.value !== undefined ? opt.value : optLabel;
            return optLabel.toLowerCase().includes(term) && !selectedValues.includes(optVal);
        });

        if (filtered.length === 0) {
            dropdown.innerHTML = '<div class="multiselect-empty">No results found</div>';
        } else {
            dropdown.innerHTML = filtered.map(opt => {
                const label = typeof opt === 'object' ? opt.label : opt;
                const val = typeof opt === 'object' && opt.value !== undefined ? opt.value : label;
                const count = typeof opt === 'object' && showCounts && opt.count !== undefined ? opt.count : null;
                const countHtml = showCounts && count !== null ? `<span class="multiselect-count">${count}</span>` : '';
                return `<div class="multiselect-option" data-value="${val}">${label}${countHtml}</div>`;
            }).join('');
            
            // Add click listeners to options
            dropdown.querySelectorAll('.multiselect-option').forEach(opt => {
                opt.addEventListener('click', () => {
                    addValue(opt.dataset.value);
                });
            });
        }
    }

    // Toggle dropdown
    function toggleDropdown() {
        isOpen = !isOpen;
        dropdown.style.display = isOpen ? 'block' : 'none';
        toggleBtn.innerHTML = isOpen 
            ? '<i class="fas fa-chevron-up"></i>' 
            : '<i class="fas fa-chevron-down"></i>';
        
        if (isOpen && searchInput.value.length >= searchMinChars) {
            filterOptions(searchInput.value);
            searchInput.focus();
        }
    }

    // Close dropdown
    function closeDropdown() {
        isOpen = false;
        dropdown.style.display = 'none';
        toggleBtn.innerHTML = '<i class="fas fa-chevron-down"></i>';
    }

    // Event listeners
    toggleBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        toggleDropdown();
    });

    searchInput.addEventListener('input', (e) => {
        filterOptions(e.target.value);
        if (!isOpen && e.target.value.length >= searchMinChars) {
            toggleDropdown();
        }
    });

    searchInput.addEventListener('focus', () => {
        if (searchInput.value.length >= searchMinChars && !isOpen) {
            toggleDropdown();
        }
    });

    searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            const term = searchInput.value.trim();
            if (term && !selectedValues.includes(term)) {
                // Allow adding custom values
                addValue(term);
            }
        } else if (e.key === 'Escape') {
            closeDropdown();
            searchInput.blur();
        } else if (e.key === 'Backspace' && searchInput.value === '' && selectedValues.length > 0) {
            removeValue(selectedValues[selectedValues.length - 1]);
        }
    });

    // Close on outside click
    document.addEventListener('click', (e) => {
        if (!container.contains(e.target)) {
            closeDropdown();
        }
    });

    // Initialize
    updateDisplay();

    // Expose methods
    container.setOptions = (newOptions) => {
        currentOptions = [...newOptions];
    };

    container.getSelectedValues = () => [...selectedValues];

    container.setSelectedValues = (values) => {
        selectedValues = [...values];
        updateDisplay();
    };

    container.deselect = (value) => removeValue(value);
    container.removeValue = (value) => removeValue(value);

    container.clear = () => {
        selectedValues = [];
        updateDisplay();
        onChange(selectedValues);
    };

    container.open = () => {
        if (!isOpen) toggleDropdown();
    };

    container.close = () => {
        if (isOpen) closeDropdown();
    };

    return container;
}

// Initialize multiselect for a filter
export function initMultiselectFilter(config) {
    const container = document.getElementById(`${config.id}-container`);
    if (!container) {
        console.error(`Multiselect container not found: ${config.id}-container`);
        return null;
    }

    const multiselect = createMultiselect(config);
    container.appendChild(multiselect);

    return multiselect;
}

// Get all unique lists from tasks
// FIX: Use correct property name 'list_title' as defined in data_manager.py
export function getUniqueLists(tasks) {
    if (!tasks || !Array.isArray(tasks)) return [];
    
    const lists = new Set();
    tasks.forEach(task => {
        // The correct property is 'list_title' as defined in data_manager.py
        const listName = task.list_title || '';
        if (listName) {
            lists.add(listName);
        }
    });
    
    return Array.from(lists).sort();
}

// Get all unique lists with pending task counts, sorted by count descending
export function getListsWithCounts(tasks) {
    if (!tasks || !Array.isArray(tasks)) return [];
    
    const listCounts = {};
    
    tasks.forEach(task => {
        // Only count pending tasks (status === 'pending')
        if (task.status === 'pending') {
            const listName = task.list_title || '';
            if (listName) {
                listCounts[listName] = (listCounts[listName] || 0) + 1;
            }
        }
    });
    
    // Convert to array and sort by count descending
    return Object.entries(listCounts)
        .map(([label, count]) => ({ label, count }))
        .sort((a, b) => b.count - a.count);
}

// Validate if a tag string is clean (not a JSON blob, newline, quote, or overly long text)
export function isValidTag(tag) {
    if (!tag || typeof tag !== 'string') return false;
    const t = tag.trim();
    if (t.length === 0 || t.length > 40) return false;
    if (/[\{\}\"':,\r\n\t]/.test(t)) return false;
    return true;
}

// Get all unique tags from tasks
export function getUniqueTags(tasks) {
    if (!tasks || !Array.isArray(tasks)) return [];
    
    const tags = new Set();
    const addCleanTag = (t) => {
        if (isValidTag(t)) tags.add(t.trim().toLowerCase());
    };
    tasks.forEach(task => {
        // Collect all tags from hybrid_tags
        if (task.hybrid_tags) {
            task.hybrid_tags.bracket?.forEach(addCleanTag);
            task.hybrid_tags.hash?.forEach(addCleanTag);
            task.hybrid_tags.user?.forEach(addCleanTag);
        }
        // Also check regular tags
        task.tags?.forEach(addCleanTag);
    });
    
    return Array.from(tags).sort();
}

// Get all unique tags with pending task counts, sorted by count descending
export function getTagsWithCounts(tasks) {
    if (!tasks || !Array.isArray(tasks)) return [];
    
    const tagCounts = {};
    const countTag = (t) => {
        if (isValidTag(t)) {
            const clean = t.trim().toLowerCase();
            tagCounts[clean] = (tagCounts[clean] || 0) + 1;
        }
    };
    
    tasks.forEach(task => {
        // Only count pending tasks (status === 'pending')
        if (task.status === 'pending') {
            // Collect all tags from hybrid_tags
            if (task.hybrid_tags) {
                task.hybrid_tags.bracket?.forEach(countTag);
                task.hybrid_tags.hash?.forEach(countTag);
                task.hybrid_tags.user?.forEach(countTag);
            }
            // Also check regular tags
            task.tags?.forEach(countTag);
        }
    });
    
    // Convert to array and sort by count descending
    return Object.entries(tagCounts)
        .map(([label, count]) => ({ label, count }))
        .sort((a, b) => b.count - a.count);
}

/**
 * Get filtered tags based on selected lists
 * Returns tags that exist in tasks belonging to the selected lists, with pending task counts
 * @param {Array} tasks - Array of task objects
 * @param {Array} selectedLists - Array of selected list names
 * @returns {Array} - Array of tag objects with label and count, sorted by count descending
 */
export function getFilteredTagsByLists(tasks, selectedLists) {
    if (!tasks || !Array.isArray(tasks)) return [];
    
    // If no lists selected, return all tags with counts
    if (!selectedLists || selectedLists.length === 0) {
        return getTagsWithCounts(tasks);
    }
    
    // Filter tasks to only those in selected lists
    const filteredTasks = tasks.filter(task => {
        const listName = task.list_title || '';
        return selectedLists.includes(listName);
    });
    
    // Get tags with counts from filtered tasks
    return getTagsWithCounts(filteredTasks);
}

/**
 * Get filtered lists based on selected tags
 * Returns lists that have tasks with the selected tags, with pending task counts
 * @param {Array} tasks - Array of task objects
 * @param {Array} selectedTags - Array of selected tag names
 * @returns {Array} - Array of list objects with label and count, sorted by count descending
 */
export function getFilteredListsByTags(tasks, selectedTags) {
    if (!tasks || !Array.isArray(tasks)) return [];
    
    // If no tags selected, return all lists with counts
    if (!selectedTags || selectedTags.length === 0) {
        return getListsWithCounts(tasks);
    }
    
    // Filter tasks to only those with selected tags
    const filteredTasks = tasks.filter(task => {
        // Collect all valid tags from task
        const taskTags = new Set();
        const addCleanTag = (t) => {
            if (isValidTag(t)) taskTags.add(t.trim().toLowerCase());
        };
        if (task.hybrid_tags) {
            task.hybrid_tags.bracket?.forEach(addCleanTag);
            task.hybrid_tags.hash?.forEach(addCleanTag);
            task.hybrid_tags.user?.forEach(addCleanTag);
        }
        task.tags?.forEach(addCleanTag);
        
        // Check if task has any of the selected tags
        return [...taskTags].some(tag => selectedTags.map(s => s.toLowerCase()).includes(tag));
    });
    
    // Get lists with counts from filtered tasks
    return getListsWithCounts(filteredTasks);
}

/**
 * Get filtered tasks based on search text and date range
 * @param {Array} tasks - All tasks
 * @param {string} searchText - Search text to filter by (title/description)
 * @param {string} dateField - Field to filter by ('due', 'created', 'completed')
 * @param {string} dateStart - Start date (ISO format)
 * @param {string} dateEnd - End date (ISO format)
 * @returns {Array} - Filtered tasks
 */
export function getFilteredTasksBySearchAndDate(tasks, searchText, dateField, dateStart, dateEnd) {
    if (!tasks || !Array.isArray(tasks)) return [];
    
    let filteredTasks = tasks;
    
    // Filter by search text (case-insensitive, match title/description)
    if (searchText && searchText.trim()) {
        const searchLower = searchText.toLowerCase().trim();
        filteredTasks = filteredTasks.filter(task => {
            const titleMatch = task.title && task.title.toLowerCase().includes(searchLower);
            const descriptionMatch = task.description && task.description.toLowerCase().includes(searchLower);
            return titleMatch || descriptionMatch;
        });
    }
    
    // Filter by date range (Modified date first if not found then created date)
    if (dateStart || dateEnd) {
        const field = dateField || 'modified_at';
        filteredTasks = filteredTasks.filter(task => {
            const dateValue = getTaskDate(task, field);
            if (!dateValue) return false;
            
            const taskDate = parseDateInput(dateValue);
            if (!taskDate) return false;
            
            // Check start date
            if (dateStart) {
                const startDate = parseDateInput(dateStart);
                if (startDate && taskDate < startDate) return false;
            }
            
            // Check end date
            if (dateEnd) {
                const endDate = parseDateInput(dateEnd);
                if (endDate) {
                    endDate.setHours(23, 59, 59, 999);
                    if (taskDate > endDate) return false;
                }
            }
            
            return true;
        });
    }
    
    return filteredTasks;
}

/**
 * Get all unique statuses with counts from tasks
 * @param {Array} tasks - Array of task objects
 * @returns {Array} - Array of status objects with label, value, and count
 */
export function getStatusWithCounts(tasks) {
    if (!tasks || !Array.isArray(tasks)) return [];
    
    let pending = 0;
    let inProgress = 0;
    let completed = 0;
    
    tasks.forEach(task => {
        const s = String(task.status || '').toLowerCase().replace(/[\s\-_]/g, '');
        if (s === 'completed') {
            completed++;
        } else if (s === 'inprogress') {
            inProgress++;
        } else {
            pending++;
        }
    });
    
    return [
        { label: 'Pending', value: 'pending', count: pending },
        { label: 'In Progress', value: 'in_progress', count: inProgress },
        { label: 'Completed', value: 'completed', count: completed }
    ];
}

/**
 * Get filtered lists based on selected tags and search/date criteria
 * Returns lists that have tasks matching all criteria, with pending task counts
 * @param {Array} tasks - Array of task objects
 * @param {Array} selectedTags - Array of selected tag names
 * @param {string} searchText - Search text to filter by
 * @param {string} dateField - Field to filter by ('due', 'created', 'completed')
 * @param {string} dateStart - Start date (ISO format)
 * @param {string} dateEnd - End date (ISO format)
 * @returns {Array} - Array of list objects with label and count, sorted by count descending
 */
export function getFilteredListsByTagsAndCriteria(tasks, selectedTags, searchText, dateField, dateStart, dateEnd) {
    if (!tasks || !Array.isArray(tasks)) return [];
    
    // First filter by search and date criteria
    let filteredTasks = getFilteredTasksBySearchAndDate(tasks, searchText, dateField, dateStart, dateEnd);
    
    // If no tags selected, return all lists with counts from filtered tasks
    if (!selectedTags || selectedTags.length === 0) {
        return getListsWithCounts(filteredTasks);
    }
    
    // Further filter tasks to only those with selected tags
    filteredTasks = filteredTasks.filter(task => {
        // Collect all valid tags from task
        const taskTags = new Set();
        const addCleanTag = (t) => {
            if (isValidTag(t)) taskTags.add(t.trim().toLowerCase());
        };
        if (task.hybrid_tags) {
            task.hybrid_tags.bracket?.forEach(addCleanTag);
            task.hybrid_tags.hash?.forEach(addCleanTag);
            task.hybrid_tags.user?.forEach(addCleanTag);
        }
        task.tags?.forEach(addCleanTag);
        
        // Check if task has any of the selected tags
        return [...taskTags].some(tag => selectedTags.map(s => s.toLowerCase()).includes(tag));
    });
    
    // Get lists with counts from filtered tasks
    return getListsWithCounts(filteredTasks);
}

/**
 * Get filtered tags based on selected lists and search/date criteria
 * Returns tags that exist in tasks matching all criteria, with pending task counts
 * @param {Array} tasks - Array of task objects
 * @param {Array} selectedLists - Array of selected list names
 * @param {string} searchText - Search text to filter by
 * @param {string} dateField - Field to filter by ('due', 'created', 'completed')
 * @param {string} dateStart - Start date (ISO format)
 * @param {string} dateEnd - End date (ISO format)
 * @returns {Array} - Array of tag objects with label and count, sorted by count descending
 */
export function getFilteredTagsByListsAndCriteria(tasks, selectedLists, searchText, dateField, dateStart, dateEnd) {
    if (!tasks || !Array.isArray(tasks)) return [];
    
    // First filter by search and date criteria
    let filteredTasks = getFilteredTasksBySearchAndDate(tasks, searchText, dateField, dateStart, dateEnd);
    
    // If no lists selected, return all tags with counts from filtered tasks
    if (!selectedLists || selectedLists.length === 0) {
        return getTagsWithCounts(filteredTasks);
    }
    
    // Further filter tasks to only those in selected lists
    filteredTasks = filteredTasks.filter(task => {
        const listName = task.list_title || '';
        return selectedLists.includes(listName);
    });
    
    // Get tags with counts from filtered tasks
    return getTagsWithCounts(filteredTasks);
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        createMultiselect,
        initMultiselectFilter,
        getUniqueLists,
        getUniqueTags,
        getListsWithCounts,
        getTagsWithCounts,
        getStatusWithCounts,
        getFilteredTagsByLists,
        getFilteredListsByTags,
        getFilteredTasksBySearchAndDate,
        getFilteredListsByTagsAndCriteria,
        getFilteredTagsByListsAndCriteria
    };
}
