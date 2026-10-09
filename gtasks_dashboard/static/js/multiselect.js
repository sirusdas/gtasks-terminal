/**
 * Multiselect Component
 * Reusable multiselect with search and suggest functionality
 */

import { parseDateInput, getTaskDate } from './utils.js';

// Helper to escape HTML strings safely
function escapeHtml(str) {
    if (str === null || str === undefined) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

// Create multiselect element with maximum-view full-screen modal overlay
export function createMultiselect(config) {
    const {
        id,
        placeholder = 'Select options...',
        options = [],
        initialValues = [],
        onChange = () => {},
        searchMinChars = 0,
        showCounts = false,
        title = ''
    } = config;

    // Filter metadata mapping for rich headers, icons, and subtitles
    const filterMeta = {
        'task-status-filter': {
            title: 'Filter by Status',
            subtitle: 'Select statuses to include in tasks view',
            icon: 'fas fa-info-circle',
            type: 'status'
        },
        'task-list-filter': {
            title: 'Filter by List',
            subtitle: 'Select one or more lists to view tasks from',
            icon: 'fas fa-folder',
            type: 'list'
        },
        'task-hide-lists-filter': {
            title: 'Hide Lists',
            subtitle: 'Select lists to exclude from tasks view',
            icon: 'fas fa-eye-slash',
            type: 'list'
        },
        'task-hide-recurring-filter': {
            title: 'Hide Recurring Tasks',
            subtitle: 'Select recurring patterns to exclude from tasks view',
            icon: 'fas fa-redo-alt',
            type: 'recurring'
        },
        'task-tags-filter': {
            title: 'Filter by Tags',
            subtitle: 'Select tags to include in tasks view',
            icon: 'fas fa-tags',
            type: 'tag'
        }
    };

    const meta = filterMeta[id] || {
        title: title || placeholder.replace('Filter by ', 'Select ').replace('...', ''),
        subtitle: 'Select options to filter tasks',
        icon: 'fas fa-filter',
        type: 'general'
    };

    // Container in the filter form/drawer
    const container = document.createElement('div');
    container.className = 'multiselect-container';
    container.id = `${id}-container`;

    // Hidden input to store selected values
    const hiddenInput = document.createElement('input');
    hiddenInput.type = 'hidden';
    hiddenInput.id = id;
    hiddenInput.name = id;
    container.appendChild(hiddenInput);

    // Selection display area (selected tag chips)
    const selectionArea = document.createElement('div');
    selectionArea.className = 'multiselect-selection';
    selectionArea.title = 'Click a tag × to remove, or click below to browse in full screen';
    container.appendChild(selectionArea);

    // Input wrapper (trigger for full screen modal)
    const inputWrapper = document.createElement('div');
    inputWrapper.className = 'multiselect-input-wrapper';
    inputWrapper.title = 'Click to open maximum view filter';

    // Trigger input (acts as clickable browse field)
    const triggerInput = document.createElement('input');
    triggerInput.type = 'text';
    triggerInput.className = 'multiselect-search';
    triggerInput.placeholder = placeholder;
    triggerInput.id = `${id}-search`;
    triggerInput.readOnly = true;
    inputWrapper.appendChild(triggerInput);

    // Toggle button icon
    const toggleBtn = document.createElement('button');
    toggleBtn.type = 'button';
    toggleBtn.className = 'multiselect-toggle';
    toggleBtn.setAttribute('aria-label', `Browse ${meta.title}`);
    toggleBtn.innerHTML = '<i class="fas fa-th-large"></i>';
    inputWrapper.appendChild(toggleBtn);

    container.appendChild(inputWrapper);

    // State
    let isOpen = false;
    let currentOptions = [...options];
    let selectedValues = [...initialValues];
    let pendingSelections = new Set(selectedValues.map(String));

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

    // Update display in the form/drawer
    function updateDisplay() {
        selectionArea.innerHTML = '';
        hiddenInput.value = JSON.stringify(selectedValues);

        if (selectedValues.length === 0) {
            selectionArea.style.display = 'none';
            triggerInput.placeholder = placeholder;
        } else {
            selectionArea.style.display = 'flex';
            triggerInput.placeholder = `${selectedValues.length} selected — click to edit`;

            selectedValues.forEach(value => {
                const tag = document.createElement('span');
                tag.className = 'multiselect-tag';
                const displayLabel = getOptionLabel(value);
                const prefix = meta.type === 'tag' ? '#' : '';
                tag.innerHTML = `
                    <span class="multiselect-tag-label">${prefix}${escapeHtml(displayLabel)}</span>
                    <button type="button" class="multiselect-remove" data-value="${escapeHtml(String(value))}" title="Remove">&times;</button>
                `;
                selectionArea.appendChild(tag);
            });
        }
    }

    // Event delegation for tag remove buttons in the chips area
    selectionArea.addEventListener('click', (e) => {
        const removeBtn = e.target.closest('.multiselect-remove');
        if (removeBtn) {
            e.stopPropagation();
            const value = removeBtn.dataset.value;
            removeValue(value);
        } else {
            // Clicking empty area of selectionArea opens the modal
            openModal();
        }
    });

    // Remove value helper
    function removeValue(value) {
        selectedValues = selectedValues.filter(v => String(v) !== String(value));
        pendingSelections = new Set(selectedValues.map(String));
        updateDisplay();
        onChange(selectedValues);
    }

    // ==========================================
    // Full-Screen Maximum View Modal Overlay
    // ==========================================
    const oldOverlay = document.getElementById(`${id}-modal-overlay`);
    if (oldOverlay) {
        oldOverlay.remove();
    }

    const overlay = document.createElement('div');
    overlay.className = 'multiselect-fullscreen-overlay';
    overlay.id = `${id}-modal-overlay`;

    overlay.innerHTML = `
        <div class="multiselect-modal-backdrop"></div>
        <div class="multiselect-modal-card" role="dialog" aria-modal="true" aria-labelledby="${id}-modal-title">
            <div class="multiselect-modal-header">
                <div class="multiselect-modal-title-group">
                    <h3 class="multiselect-modal-title" id="${id}-modal-title">
                        <i class="${meta.icon}"></i>
                        <span>${escapeHtml(meta.title)}</span>
                    </h3>
                    <div class="multiselect-modal-subtitle">${escapeHtml(meta.subtitle)}</div>
                </div>
                <div class="multiselect-modal-header-actions">
                    <button type="button" class="multiselect-modal-btn-action multiselect-btn-select-all" title="Select all visible items">
                        <i class="fas fa-check-double"></i> Select All
                    </button>
                    <button type="button" class="multiselect-modal-btn-action multiselect-btn-clear-all" title="Clear all selections">
                        <i class="fas fa-undo"></i> Clear All
                    </button>
                    <button type="button" class="multiselect-modal-close-icon" aria-label="Close modal">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </div>

            <div class="multiselect-modal-search-wrapper">
                <div class="multiselect-modal-search-inner">
                    <i class="fas fa-search multiselect-modal-search-ico"></i>
                    <input type="text" class="multiselect-modal-search-field" placeholder="Search ${escapeHtml(meta.title.toLowerCase())}...">
                    <button type="button" class="multiselect-modal-search-clear" style="display: none;" title="Clear search">
                        <i class="fas fa-times-circle"></i>
                    </button>
                </div>
                <div class="multiselect-modal-counts">
                    <span class="multiselect-modal-count-pill" id="${id}-modal-selected-pill">0 selected</span>
                    <span class="multiselect-modal-total-pill" id="${id}-modal-total-pill">0 options</span>
                </div>
            </div>

            <div class="multiselect-modal-body">
                <div class="multiselect-modal-grid" id="${id}-modal-grid"></div>
                <div class="multiselect-modal-empty" id="${id}-modal-empty" style="display: none;">
                    <i class="fas fa-search-minus"></i>
                    <p>No matching options found</p>
                </div>
            </div>

            <div class="multiselect-modal-footer">
                <div class="multiselect-modal-footer-left">
                    <span class="multiselect-selection-summary" id="${id}-modal-summary">No options selected</span>
                </div>
                <div class="multiselect-modal-footer-right">
                    <button type="button" class="multiselect-modal-btn-cancel">Cancel</button>
                    <button type="button" class="multiselect-modal-btn-apply">
                        <i class="fas fa-check"></i> Done
                    </button>
                </div>
            </div>
        </div>
    `;

    document.body.appendChild(overlay);

    const modalBackdrop = overlay.querySelector('.multiselect-modal-backdrop');
    const modalCloseIcon = overlay.querySelector('.multiselect-modal-close-icon');
    const modalSearchInput = overlay.querySelector('.multiselect-modal-search-field');
    const modalSearchClear = overlay.querySelector('.multiselect-modal-search-clear');
    const modalGrid = overlay.querySelector('.multiselect-modal-grid');
    const modalEmpty = overlay.querySelector('.multiselect-modal-empty');
    const modalSelectedPill = overlay.querySelector(`#${id}-modal-selected-pill`);
    const modalTotalPill = overlay.querySelector(`#${id}-modal-total-pill`);
    const modalSummary = overlay.querySelector(`#${id}-modal-summary`);
    const btnSelectAll = overlay.querySelector('.multiselect-btn-select-all');
    const btnClearAll = overlay.querySelector('.multiselect-btn-clear-all');
    const btnCancel = overlay.querySelector('.multiselect-modal-btn-cancel');
    const btnApply = overlay.querySelector('.multiselect-modal-btn-apply');

    // Update counts & summary indicators in modal
    function updateModalStats(visibleCount, totalCount) {
        const selCount = pendingSelections.size;
        modalSelectedPill.textContent = `${selCount} selected`;
        modalTotalPill.textContent = `${visibleCount} of ${totalCount} options`;

        if (selCount === 0) {
            modalSummary.textContent = 'Showing all (none filtered)';
        } else {
            modalSummary.textContent = `${selCount} option${selCount > 1 ? 's' : ''} selected`;
        }
    }

    // Render option cards in multi-column grid
    function renderCards(searchTerm = '') {
        const term = searchTerm.toLowerCase().trim();
        modalGrid.innerHTML = '';

        const filtered = currentOptions.filter(opt => {
            const optLabel = typeof opt === 'object' ? opt.label : String(opt);
            return !term || optLabel.toLowerCase().includes(term);
        });

        updateModalStats(filtered.length, currentOptions.length);

        if (filtered.length === 0) {
            modalGrid.style.display = 'none';
            modalEmpty.style.display = 'block';
            return;
        }

        modalGrid.style.display = 'grid';
        modalEmpty.style.display = 'none';

        filtered.forEach(opt => {
            const label = typeof opt === 'object' ? opt.label : String(opt);
            const val = typeof opt === 'object' && opt.value !== undefined ? opt.value : label;
            const strVal = String(val);
            const isSelected = pendingSelections.has(strVal);
            const count = typeof opt === 'object' && showCounts && opt.count !== undefined ? opt.count : null;

            // Prefix icon / symbol
            let prefixHtml = '';
            if (meta.type === 'tag') {
                prefixHtml = '<span class="multiselect-card-prefix hash-prefix">#</span>';
            } else if (meta.type === 'list') {
                prefixHtml = '<i class="fas fa-folder multiselect-card-prefix list-ico"></i>';
            } else if (meta.type === 'recurring') {
                prefixHtml = '<i class="fas fa-redo-alt multiselect-card-prefix recurring-ico"></i>';
            } else if (meta.type === 'status') {
                prefixHtml = `<span class="multiselect-card-prefix status-dot status-${escapeHtml(strVal.toLowerCase())}"></span>`;
            }

            const countHtml = (showCounts && count !== null) 
                ? `<span class="multiselect-card-count">${count}</span>` 
                : '';

            const card = document.createElement('div');
            card.className = `multiselect-grid-card ${isSelected ? 'selected' : ''}`;
            card.dataset.value = strVal;
            card.innerHTML = `
                <div class="multiselect-card-checkbox">
                    <i class="fas fa-check"></i>
                </div>
                <div class="multiselect-card-label-wrap">
                    ${prefixHtml}
                    <span class="multiselect-card-label" title="${escapeHtml(label)}">${escapeHtml(label)}</span>
                </div>
                ${countHtml}
            `;

            card.addEventListener('click', () => {
                if (pendingSelections.has(strVal)) {
                    pendingSelections.delete(strVal);
                    card.classList.remove('selected');
                } else {
                    pendingSelections.add(strVal);
                    card.classList.add('selected');
                }
                updateModalStats(filtered.length, currentOptions.length);
            });

            modalGrid.appendChild(card);
        });
    }

    // Open Modal
    function openModal() {
        isOpen = true;
        pendingSelections = new Set(selectedValues.map(String));
        modalSearchInput.value = '';
        modalSearchClear.style.display = 'none';

        overlay.style.display = 'flex';
        // Trigger smooth CSS transition
        requestAnimationFrame(() => {
            overlay.classList.add('active');
        });
        document.body.classList.add('multiselect-modal-open');

        renderCards('');

        setTimeout(() => {
            modalSearchInput.focus();
        }, 60);
    }

    // Close Modal without applying changes
    function closeModal() {
        isOpen = false;
        overlay.classList.remove('active');
        document.body.classList.remove('multiselect-modal-open');
        setTimeout(() => {
            if (!isOpen) {
                overlay.style.display = 'none';
            }
        }, 220);
    }

    // Apply selections and close
    function applyAndClose() {
        selectedValues = Array.from(pendingSelections);
        updateDisplay();
        onChange(selectedValues);
        closeModal();
    }

    // Modal Event Listeners
    modalSearchInput.addEventListener('input', (e) => {
        const val = e.target.value;
        modalSearchClear.style.display = val ? 'inline-block' : 'none';
        renderCards(val);
    });

    modalSearchClear.addEventListener('click', () => {
        modalSearchInput.value = '';
        modalSearchClear.style.display = 'none';
        renderCards('');
        modalSearchInput.focus();
    });

    btnSelectAll.addEventListener('click', () => {
        const term = modalSearchInput.value.toLowerCase().trim();
        const visibleOptions = currentOptions.filter(opt => {
            const optLabel = typeof opt === 'object' ? opt.label : String(opt);
            return !term || optLabel.toLowerCase().includes(term);
        });
        visibleOptions.forEach(opt => {
            const val = typeof opt === 'object' && opt.value !== undefined ? opt.value : (opt.label || opt);
            pendingSelections.add(String(val));
        });
        renderCards(modalSearchInput.value);
    });

    btnClearAll.addEventListener('click', () => {
        pendingSelections.clear();
        renderCards(modalSearchInput.value);
    });

    btnApply.addEventListener('click', () => {
        applyAndClose();
    });

    btnCancel.addEventListener('click', () => {
        closeModal();
    });

    modalCloseIcon.addEventListener('click', () => {
        applyAndClose();
    });

    modalBackdrop.addEventListener('click', () => {
        applyAndClose();
    });

    // Keyboard support
    overlay.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            applyAndClose();
        } else if (e.key === 'Enter' && e.target === modalSearchInput) {
            e.preventDefault();
            applyAndClose();
        }
    });

    // Form/drawer trigger clicks
    inputWrapper.addEventListener('click', (e) => {
        e.stopPropagation();
        openModal();
    });

    // Initialize display
    updateDisplay();

    // Container API methods
    container.setOptions = (newOptions) => {
        currentOptions = [...newOptions];
        if (isOpen) {
            renderCards(modalSearchInput.value);
        }
    };

    container.getSelectedValues = () => [...selectedValues];

    container.setSelectedValues = (values) => {
        selectedValues = [...values];
        pendingSelections = new Set(selectedValues.map(String));
        updateDisplay();
    };

    container.deselect = (value) => removeValue(value);
    container.removeValue = (value) => removeValue(value);

    container.clear = () => {
        selectedValues = [];
        pendingSelections.clear();
        updateDisplay();
        onChange(selectedValues);
    };

    container.open = () => {
        if (!isOpen) openModal();
    };

    container.close = () => {
        if (isOpen) closeModal();
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
