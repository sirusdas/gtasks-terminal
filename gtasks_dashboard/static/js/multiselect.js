/**
 * Multiselect Component
 * Reusable multiselect with search and suggest functionality
 */

// Create multiselect element
export function createMultiselect(config) {
    const {
        id,
        placeholder = 'Select options...',
        options = [],
        initialValues = [],
        onChange = () => {},
        searchMinChars = 0
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

    // Update display
    function updateDisplay() {
        selectionArea.innerHTML = '';
        hiddenInput.value = JSON.stringify(selectedValues);

        selectedValues.forEach(value => {
            const tag = document.createElement('span');
            tag.className = 'multiselect-tag';
            tag.innerHTML = `
                ${value}
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
        selectedValues = selectedValues.filter(v => v !== value);
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

        const filtered = currentOptions.filter(opt => 
            opt.toLowerCase().includes(term) && !selectedValues.includes(opt)
        );

        if (filtered.length === 0) {
            dropdown.innerHTML = '<div class="multiselect-empty">No results found</div>';
        } else {
            dropdown.innerHTML = filtered.map(opt => 
                `<div class="multiselect-option" data-value="${opt}">${opt}</div>`
            ).join('');
            
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

// Get all unique tags from tasks
export function getUniqueTags(tasks) {
    if (!tasks || !Array.isArray(tasks)) return [];
    
    const tags = new Set();
    tasks.forEach(task => {
        // Collect all tags from hybrid_tags
        if (task.hybrid_tags) {
            task.hybrid_tags.bracket?.forEach(t => tags.add(t));
            task.hybrid_tags.hash?.forEach(t => tags.add(t));
            task.hybrid_tags.user?.forEach(t => tags.add(t));
        }
        // Also check regular tags
        task.tags?.forEach(t => tags.add(t));
    });
    
    return Array.from(tags).sort();
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        createMultiselect,
        initMultiselectFilter,
        getUniqueLists,
        getUniqueTags
    };
}
