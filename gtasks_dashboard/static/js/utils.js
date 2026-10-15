/**
 * Utility Functions
 * Reusable utility functions for the dashboard
 */

/**
 * Escape HTML special characters for safe rendering in DOM
 * @param {string} text - String to escape
 * @returns {string} - Escaped string
 */
export function escapeHtml(text) {
    if (!text) return '';
    return String(text)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

/**
 * Escape string for safe insertion into inline JS function calls
 * @param {string} str - String to escape
 * @returns {string} - Escaped string
 */
export function escapeJsString(str) {
    if (!str) return '';
    return String(str)
        .replace(/\\/g, '\\\\')
        .replace(/'/g, "\\'")
        .replace(/"/g, '\\"');
}

if (typeof window !== 'undefined') {
    window.escapeHtml = escapeHtml;
    window.escapeJsString = escapeJsString;
}

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
    if (dateString instanceof Date) return isNaN(dateString.getTime()) ? null : dateString;
    
    const str = String(dateString).trim();
    // Try to parse DD/MM/YYYY format
    if (str.includes('/') && !str.includes('T')) {
        const parts = str.split('/');
        if (parts.length === 3) {
            const day = parseInt(parts[0], 10);
            const month = parseInt(parts[1], 10) - 1; // Month is 0-indexed
            const year = parseInt(parts[2], 10);
            return new Date(year, month, day, 0, 0, 0, 0);
        }
    }
    
    // Exact YYYY-MM-DD format (from input type="date")
    if (/^\d{4}-\d{2}-\d{2}$/.test(str)) {
        const parts = str.split('-');
        const year = parseInt(parts[0], 10);
        const month = parseInt(parts[1], 10) - 1;
        const day = parseInt(parts[2], 10);
        return new Date(year, month, day, 0, 0, 0, 0);
    }
    
    // Fallback to standard Date parsing (handles ISO-8601 timestamps)
    const date = new Date(str);
    if (!isNaN(date.getTime())) return date;
    
    const dateIso = new Date(str.replace(' ', 'T'));
    return isNaN(dateIso.getTime()) ? null : dateIso;
}

/**
 * Get date value for a task based on selected dateField.
 * Default behavior: Modified date first, if not found then created date.
 * @param {Object} task - Task object
 * @param {string} dateField - Date field ('modified_at', 'created_at', 'due')
 * @returns {string|null} - Date string
 */
export function getTaskDate(task, dateField = 'modified_at') {
    if (!task) return null;
    if (dateField === 'due') {
        return task.due || null;
    }
    if (dateField === 'created_at') {
        return task.created_at || task.created || task.modified_at || task.updated_at || null;
    }
    // 'modified_at' or default: modified date first, if not found then created date
    return task.modified_at || task.updated_at || task.updated || task.created_at || task.created || null;
}

/**
 * Get default date range formatted as YYYY-MM-DD for the past N days up to today.
 * @param {number} days - Number of days in the past (default: 31)
 * @returns {{start: string, end: string}} - Start and end dates
 */
export function getDefaultDateRange(days = 31) {
    const end = new Date();
    const start = new Date();
    start.setDate(start.getDate() - days);
    
    const pad = (n) => String(n).padStart(2, '0');
    const formatDateStr = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
    
    return {
        start: formatDateStr(start),
        end: formatDateStr(end)
    };
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
 * Splits raw task notes/description into clean human notes and tags array.
 * Looks for the divider:
/**
 * Extract spaces and sub-spaces mapping from raw text.
 * @param {string} text
 * @returns {Record<string, string[]>}
 */
export function extractSpacesFromText(text) {
    if (!text) return {};
    const str = String(text);
    const spacesDividerRegex = /(?:^|\r?\n)[ \t]*---[ \t]*\{spaces\}[ \t]*(?:\r?\n)([\s\S]*?)(?=(?:\r?\n[ \t]*---[ \t]*[^\r\n]*)|$)/i;
    const dividerMatch = str.match(spacesDividerRegex);
    const searchChunk = dividerMatch ? dividerMatch[1] : str;

    const spaceItemRegex = /\{spa::([a-zA-Z0-9_\-\s]+?)(?::\(([^)]*)\))?\}/gi;
    const spaces = {};
    let m;
    while ((m = spaceItemRegex.exec(searchChunk)) !== null) {
        const spaceName = m[1].trim();
        if (!spaceName || !isValidTag(spaceName)) continue;

        const rawSubspaces = m[2] || '';
        const subspaces = [];
        if (rawSubspaces.trim()) {
            const parts = rawSubspaces.split(',');
            for (let part of parts) {
                let s = part.trim();
                if (s.toLowerCase().startsWith('sub::')) {
                    s = s.substring(5).trim();
                }
                if (s && isValidTag(s) && !subspaces.includes(s)) {
                    subspaces.push(s);
                }
            }
        }

        if (spaces[spaceName]) {
            for (const s of subspaces) {
                if (!spaces[spaceName].includes(s)) spaces[spaceName].push(s);
            }
        } else {
            spaces[spaceName] = subspaces;
        }
    }
    return spaces;
}

/**
 * Splits raw task notes into user-readable clean notes, extracted tags, and spaces map,
 * stripping dividers (--- and ---{spaces}) and bracket tags at the bottom.
 * @param {string} rawText
 * @returns {{ cleanNotes: string, tags: string[], spaces: Record<string, string[]> }}
 */
export function splitNotesAndTags(rawText) {
    if (!rawText) return { cleanNotes: '', tags: [], spaces: {} };
    let str = String(rawText);
    const spaces = extractSpacesFromText(str);

    // Strip the ---{spaces} section first
    const spacesDividerRegex = /(?:^|\r?\n)[ \t]*---[ \t]*\{spaces\}[ \t]*(?:\r?\n)([\s\S]*?)(?=(?:\r?\n[ \t]*---[ \t]*[^\r\n]*)|$)/gi;
    str = str.replace(spacesDividerRegex, '').trimEnd();
    
    // Helper to extract clean unique valid bracket tags from a text chunk
    const extractTags = (chunk) => {
        const bracketRegex = /\[([^\]\r\n]+)\]/g;
        const result = [];
        let m;
        while ((m = bracketRegex.exec(chunk)) !== null) {
            const tag = m[1].trim();
            if (tag && !result.includes(tag) && isValidTag(tag)) {
                result.push(tag);
            }
        }
        return result;
    };

    // Case 1: Divider format (--- followed strictly by bracket tags at the end)
    const dividerRegex = /(?:^|\r?\n)[ \t]*---[ \t]*(?:\r?\n)((?:[ \t]*(?:\[[^\]\r\n]+\])[\s]*)+)$/;
    const dividerMatch = str.match(dividerRegex);
    if (dividerMatch) {
        const extractedTags = extractTags(dividerMatch[1]);
        if (extractedTags.length > 0) {
            const clean = str.substring(0, dividerMatch.index).replace(/[\r\n]+$/, '');
            return {
                cleanNotes: clean,
                tags: extractedTags,
                spaces: spaces
            };
        }
    }

    // Case 2: Legacy record where the entire notes text is solely bracket tags (e.g. "[my][p1]")
    const pureTagsRegex = /^(?:[ \t]*(?:\[[^\]\r\n]+\])[ \t]*)+$/;
    if (pureTagsRegex.test(str.trim())) {
        const extractedTags = extractTags(str);
        if (extractedTags.length > 0) {
            return {
                cleanNotes: '',
                tags: extractedTags,
                spaces: spaces
            };
        }
    }

    // Case 3: Legacy record where notes end with a trailing block of bracket tags preceded by newline(s)
    const trailingTagsRegex = /(?:\r?\n)+((?:[ \t]*(?:\[[^\]\r\n]+\])[ \t]*)+)$/;
    const trailingMatch = str.match(trailingTagsRegex);
    if (trailingMatch) {
        const extractedTags = extractTags(trailingMatch[1]);
        if (extractedTags.length > 0) {
            const clean = str.substring(0, trailingMatch.index).replace(/[\r\n]+$/, '');
            return {
                cleanNotes: clean,
                tags: extractedTags,
                spaces: spaces
            };
        }
    }
    
    return {
        cleanNotes: str,
        tags: [],
        spaces: spaces
    };
}

/**
 * Combines clean notes, tags, and spaces with standard dividers.
 * Format:
 * <cleanNotes>
 *
 * ---
 * [tag1][tag2]
 *
 * ---{spaces}
 * {spa::space:(sub::sub1,sub::sub2)}
 *
 * @param {string} cleanNotes
 * @param {string[]} tags
 * @param {Record<string, string[]>} spaces
 * @returns {string}
 */
export function combineNotesAndMetadata(cleanNotes, tags = [], spaces = {}) {
    const clean = (cleanNotes || '').trim();
    const sections = [];
    if (clean) sections.push(clean);

    const cleanTags = (tags || [])
        .map(t => String(t).trim().replace(/^\[|\]$/g, '').replace(/^#/, ''))
        .filter(t => t.length > 0 && isValidTag(t));
    const uniqueTags = Array.from(new Set(cleanTags));
    if (uniqueTags.length > 0) {
        const tagsLine = uniqueTags.map(t => `[${t}]`).join('');
        sections.push(`---\n${tagsLine}`);
    }

    if (spaces && Object.keys(spaces).length > 0) {
        const spaceLines = [];
        for (const [spaceName, subspaces] of Object.entries(spaces)) {
            const spa = String(spaceName).trim();
            if (!spa || !isValidTag(spa)) continue;
            const validSubs = (subspaces || [])
                .map(s => String(s).trim().replace(/^sub::/i, ''))
                .filter(s => s.length > 0 && isValidTag(s));
            const uniqueSubs = Array.from(new Set(validSubs));
            if (uniqueSubs.length > 0) {
                spaceLines.push(`{spa::${spa}:(${uniqueSubs.map(s => 'sub::' + s).join(',')})}`);
            } else {
                spaceLines.push(`{spa::${spa}}`);
            }
        }
        if (spaceLines.length > 0) {
            sections.push(`---{spaces}\n${spaceLines.join('\n')}`);
        }
    }

    return sections.join('\n\n').trim();
}

export function combineNotesAndTags(cleanNotes, tags = [], spaces = {}) {
    return combineNotesAndMetadata(cleanNotes, tags, spaces);
}

/**
 * Generate notes section HTML for a task
 * @param {Object} task - The task object
 * @returns {string} - The notes section HTML
 */
export function getNotesSection(task) {
    const rawNotes = task.notes || task.description || '';
    if (!rawNotes) return '';
    
    const { cleanNotes } = splitNotesAndTags(rawNotes);
    if (!cleanNotes || !cleanNotes.trim()) return '';
    
    const truncated = cleanNotes.length > 100;
    const fullContent = cleanNotes.split('\n').map(line => line.trim()).filter(line => line).join('<br>');
    
    // Only show toggle button when notes are truncated
    if (!truncated) {
        return `
            <div class="notes-section">
                <div class="notes-content">
                    <div class="notes-text">📓 ${fullContent}</div>
                </div>
            </div>
        `;
    }
    
    return `
        <div class="notes-section">
            <button class="notes-toggle">Show more 📓</button>
            <div class="notes-content" style="max-height: 0px; overflow: hidden;">
                <div class="notes-text">📓 ${fullContent}</div>
            </div>
        </div>
    `;
}

/**
 * Validate if a tag string is clean (not a JSON blob, newline, quote, or overly long text)
 * @param {string} tag
 * @returns {boolean}
 */
export function isValidTag(tag) {
    if (!tag || typeof tag !== 'string') return false;
    const t = tag.trim();
    if (t.length === 0 || t.length > 40) return false;
    if (/[\{\}\"':,\r\n\t]/.test(t)) return false;
    return true;
}

/**
 * Generate tags display HTML for a task
 * @param {Object} task - The task object
 * @returns {string} - The tags HTML
 */
export function getTagsDisplay(task) {
    const rawTags = [];
    
    // Add bracket tags from hybrid_tags
    if (task.hybrid_tags && task.hybrid_tags.bracket) {
        rawTags.push(...task.hybrid_tags.bracket);
    }
    
    // Add hash tags
    if (task.hybrid_tags && task.hybrid_tags.hash) {
        rawTags.push(...task.hybrid_tags.hash);
    }
    
    // Add user tags
    if (task.hybrid_tags && task.hybrid_tags.user) {
        rawTags.push(...task.hybrid_tags.user);
    }
    
    // Add regular tags
    if (task.tags) {
        rawTags.push(...task.tags);
    }

    // Extract any footer tags from notes
    const rawNotes = task.notes || task.description || '';
    if (rawNotes) {
        const { tags: footerTags } = splitNotesAndTags(rawNotes);
        rawTags.push(...footerTags);
    }
    
    // Deduplicate and filter
    const uniqueTags = Array.from(new Set(rawTags.filter(isValidTag)));
    if (uniqueTags.length === 0) return '';
    
    const tagsHtml = uniqueTags.map(tag => `<span class="task-tag">[${tag}]</span>`).join(' ');
    return `<div class="task-tags">${tagsHtml}</div>`;
}

/**
 * Generate spaces and sub-spaces display HTML for a task
 * @param {Object} task - The task object
 * @returns {string} - The spaces HTML
 */
export function getSpacesDisplay(task) {
    const rawNotes = task.notes || task.description || '';
    const spaces = (task.spaces && Object.keys(task.spaces).length > 0) ? task.spaces : extractSpacesFromText(rawNotes);
    if (!spaces || Object.keys(spaces).length === 0) return '';

    const chips = [];
    Object.entries(spaces).forEach(([spaceName, subspaces]) => {
        const spa = escapeHtml(spaceName);
        if (subspaces && subspaces.length > 0) {
            subspaces.forEach(sub => {
                const subEsc = escapeHtml(sub);
                chips.push(`
                    <span class="task-space-chip" onclick="selectSidebarFilter('subspace', '${escapeJsString(sub)}', '${escapeJsString(spaceName)}'); event.stopPropagation();" title="Space: ${spa} › Sub-space: ${subEsc}">
                        <i class="fas fa-layer-group"></i> ${spa} <span class="chip-sep">›</span> ${subEsc}
                    </span>
                `);
            });
        } else {
            chips.push(`
                <span class="task-space-chip" onclick="selectSidebarFilter('space', '${escapeJsString(spaceName)}'); event.stopPropagation();" title="Space: ${spa}">
                    <i class="fas fa-layer-group"></i> ${spa}
                </span>
            `);
        }
    });

    return `<div class="task-spaces-container">${chips.join('')}</div>`;
}

/**
 * Get all tags from a task as a flat array
 * @param {Object} task - The task object
 * @returns {Array} - Array of all tags
 */
export function getAllTags(task) {
    const rawTags = [];
    
    if (task.hybrid_tags) {
        if (task.hybrid_tags.bracket) rawTags.push(...task.hybrid_tags.bracket);
        if (task.hybrid_tags.hash) rawTags.push(...task.hybrid_tags.hash);
        if (task.hybrid_tags.user) rawTags.push(...task.hybrid_tags.user);
    }
    
    if (task.tags) {
        rawTags.push(...task.tags);
    }

    const rawNotes = task.notes || task.description || '';
    if (rawNotes) {
        const { tags: footerTags } = splitNotesAndTags(rawNotes);
        rawTags.push(...footerTags);
    }
    
    return Array.from(new Set(rawTags.filter(isValidTag)));
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
                const aVal = getTaskDate(a, 'modified_at');
                const bVal = getTaskDate(b, 'modified_at');
                const aTime = aVal ? (parseDateInput(aVal)?.getTime() || -Infinity) : -Infinity;
                const bTime = bVal ? (parseDateInput(bVal)?.getTime() || -Infinity) : -Infinity;
                comparison = aTime - bTime;
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
    
    // Apply status filter (supports single string or array of statuses, case-insensitive, normalized)
    if (filters.status) {
        let statuses = [];
        if (Array.isArray(filters.status)) {
            statuses = filters.status;
        } else if (typeof filters.status === 'string') {
            try {
                const parsed = JSON.parse(filters.status);
                if (Array.isArray(parsed)) statuses = parsed;
                else if (parsed) statuses = [String(parsed)];
            } catch (e) {
                if (filters.status.trim()) statuses = [filters.status.trim()];
            }
        }
        
        if (statuses.length > 0) {
            const normalizedStatuses = statuses.map(s => String(s).toLowerCase().replace(/[\s\-_]/g, ''));
            filteredTasks = filteredTasks.filter(task => {
                if (!task.status) return false;
                const taskStatusNorm = String(task.status).toLowerCase().replace(/[\s\-_]/g, '');
                return normalizedStatuses.includes(taskStatusNorm);
            });
        }
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
    
    // Apply list filter (was "Filter by Project" -> "Filter by List")
    // FIX: Use correct property name 'list_title' as defined in data_manager.py
    if (filters.list && filters.list.length > 0) {
        console.log('[Utils] Applying list filter:', filters.list);
        filteredTasks = filteredTasks.filter(task => {
            // The correct property is 'list_title' as defined in data_manager.py
            const taskList = task.list_title || '';
            console.log('[Utils] Task:', task.title, '| List:', taskList);
            const matches = filters.list.some(filterList => 
                taskList.toLowerCase().includes(filterList.toLowerCase())
            );
            console.log('[Utils] Task matches list filter:', matches);
            return matches;
        });
        console.log('[Utils] Tasks after list filter:', filteredTasks.length);
    }

    // Apply hide lists filter (exclude tasks from selected lists)
    if (filters.hideLists && filters.hideLists.length > 0) {
        console.log('[Utils] Applying hide lists filter:', filters.hideLists);
        filteredTasks = filteredTasks.filter(task => {
            const taskList = (task.list_title || '').toLowerCase();
            const shouldHide = filters.hideLists.some(hideList =>
                taskList === hideList.toLowerCase() || taskList.includes(hideList.toLowerCase())
            );
            return !shouldHide;
        });
        console.log('[Utils] Tasks after hide lists filter:', filteredTasks.length);
    }

    // Apply hide recurring filter (exclude recurring tasks or specific recurrence types)
    if (filters.hideRecurring && filters.hideRecurring.length > 0) {
        console.log('[Utils] Applying hide recurring filter:', filters.hideRecurring);
        const hideAll = filters.hideRecurring.some(r => String(r).toLowerCase() === 'all');
        const hideTypes = new Set(filters.hideRecurring.map(r => String(r).toLowerCase()));
        
        filteredTasks = filteredTasks.filter(task => {
            if (!task.is_recurring) return true;
            if (hideAll) return false;
            const taskType = (task.recurrence_type || 'other').toLowerCase();
            return !hideTypes.has(taskType);
        });
        console.log('[Utils] Tasks after hide recurring filter:', filteredTasks.length);
    }
    
    // Apply tags filter (now array-based from multiselect)
    // FIX: Changed to exact match instead of partial match
    if (filters.tags && filters.tags.length > 0) {
        console.log('[Utils] Applying tags filter (exact match):', filters.tags);
        filteredTasks = filteredTasks.filter(task => {
            const taskTags = getAllTags(task);
            console.log('[Utils] Task:', task.title, '| Tags:', taskTags);
            // Exact match: filterTag must exactly equal taskTag (case-insensitive)
            const matches = filters.tags.every(filterTag =>
                taskTags.some(taskTag => taskTag.toLowerCase() === filterTag.toLowerCase())
            );
            console.log('[Utils] Task matches filter:', matches);
            return matches;
        });
        console.log('[Utils] Tasks after tags filter:', filteredTasks.length);
    }
    
    // Apply space filter
    if (filters.space) {
        const filterSpace = String(filters.space).toLowerCase().trim();
        filteredTasks = filteredTasks.filter(task => {
            const spaces = (task.spaces && Object.keys(task.spaces).length > 0)
                ? task.spaces
                : extractSpacesFromText(task.notes || task.description || '');
            if (!spaces) return false;
            return Object.keys(spaces).some(s => s.toLowerCase() === filterSpace);
        });
    }

    // Apply subspace filter
    if (filters.subspace) {
        const filterSubspace = String(filters.subspace).toLowerCase().trim();
        const parentSpace = filters.space ? String(filters.space).toLowerCase().trim() : null;
        filteredTasks = filteredTasks.filter(task => {
            const spaces = (task.spaces && Object.keys(task.spaces).length > 0)
                ? task.spaces
                : extractSpacesFromText(task.notes || task.description || '');
            if (!spaces) return false;
            return Object.entries(spaces).some(([sp, subs]) => {
                if (parentSpace && sp.toLowerCase() !== parentSpace) return false;
                return (subs || []).some(sub => sub.toLowerCase() === filterSubspace);
            });
        });
    }

    // Apply date filter (Modified date first if not found then created date)
    if (filters.dateStart || filters.dateEnd) {
        const dateField = filters.dateField || 'modified_at';
        filteredTasks = filteredTasks.filter(task => {
            const taskDate = getTaskDate(task, dateField);
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
