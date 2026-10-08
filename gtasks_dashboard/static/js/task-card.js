/**
 * Task Card Component
 * Creates and renders task cards for both main tasks grid and node tasks
 */

import { 
    getDateStatus, 
    getDateStatusBadge, 
    getCompactDateDisplay, 
    getNotesSection, 
    getTagsDisplay,
    getPriorityClass,
    getPriorityIcon,
    getStatusClass
} from './utils.js';

/**
 * Create a task card element
 * @param {Object} task - The task object
 * @param {Object} options - Rendering options
 * @returns {HTMLElement} - The task card element
 */
export function createTaskCard(task, options = {}) {
    const card = document.createElement('div');
    card.className = options.isNodeTask ? 'node-task-card' : 'task-card';
    card.setAttribute('data-task-id', task.id);
    
    const priorityClass = getPriorityClass(task.calculated_priority);
    const priorityIcon = getPriorityIcon(task.calculated_priority);
    const statusClass = getStatusClass(task.status);
    
    // Date status calculation
    const dateStatus = getDateStatus(task.due);
    const dateStatusBadge = getDateStatusBadge(dateStatus);
    
    // Compact date display
    const compactDates = getCompactDateDisplay(task);
    
    // Notes section (expandable)
    const notesSection = getNotesSection(task);
    
    // Tags display
    const tagsDisplay = getTagsDisplay(task);
    
    // Check if this task has dependencies (for node task cards)
    const hasDeps = task.dependencies && task.dependencies.length > 0;
    const depsInfo = hasDeps ? 
        `<small style="color: #f59e0b; font-size: 0.7rem; display: block; margin-top: 0.25rem;">
            <i class="fas fa-link"></i> ${task.dependencies.length} dependency(ies)
        </small>` : '';
    
    // Complete button - show checkmark for incomplete, completed for complete
    const isCompleted = task.status === 'completed';
    const completeBtnHtml = `
        <div class="task-complete-btn ${isCompleted ? 'completed' : ''}"
             onclick="${isCompleted ? '' : `completeTask('${task.id}')`}"
             title="${isCompleted ? 'Completed' : 'Mark as complete'}">
            ${isCompleted ? '✅' : '⭕'}
        </div>
    `;

    // Quick View button
    const quickViewBtnHtml = `
        <div class="task-quick-view-btn" onclick="openQuickView('${task.id}')" title="Quick view task details">
            <i class="fas fa-eye"></i>
        </div>
    `;

    const compactQuickViewBtnHtml = `
        <button class="compact-action-btn quick-view-btn" onclick="openQuickView('${task.id}'); event.stopPropagation();" title="Quick view task details">
            <i class="fas fa-eye"></i>
        </button>
    `;

    // Edit button
    const editBtnHtml = `
        <div class="task-edit-btn" onclick="openEditModal('${task.id}')" title="Edit task">
            <i class="fas fa-edit"></i>
        </div>
    `;

    // Recurrence badges
    const recurringBadge = task.is_recurring ? `
        <span class="task-badge badge-recurring badge-recurring-${task.recurrence_type || 'other'}" title="Recurring: ${task.recurrence_type || 'Repeating'}">
            <i class="fas fa-redo-alt"></i> ${(task.recurrence_type || 'recurring').toUpperCase()}
        </span>
    ` : '';

    const compactRecurringBadge = task.is_recurring ? `
        <span class="compact-recurring" title="Recurring: ${task.recurrence_type || 'Repeating'}">
            <i class="fas fa-redo-alt"></i> ${task.recurrence_type || 'recurring'}
        </span>
    ` : '';
    
    if (options.isNodeTask) {
        // Node task card HTML
        card.innerHTML = `
            <div class="node-task-header">
                ${completeBtnHtml}
                <span class="priority-icon">🔸</span>
                <div class="node-task-title" onclick="openQuickView('${task.id}')" style="cursor: pointer;" title="Quick view">${task.title}</div>
                ${recurringBadge}
                ${quickViewBtnHtml}
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
    } else if (options.isCompact) {
        // High-density compact view for mobile and compact mode
        card.className = `task-card-compact ${isCompleted ? 'completed' : ''}`;
        card.innerHTML = `
            <div class="compact-left">
                ${completeBtnHtml}
            </div>
            <div class="compact-body" onclick="window.toggleCompactDetails('${task.id}')">
                <div class="compact-title-row">
                    <span class="compact-title ${isCompleted ? 'line-through' : ''}" onclick="openQuickView('${task.id}'); event.stopPropagation();" style="cursor: pointer;" title="Quick view details">${task.title}</span>
                    <span class="compact-priority-indicator ${priorityClass}" title="Priority: ${task.calculated_priority || task.priority}">${priorityIcon}</span>
                </div>
                <div class="compact-meta-row">
                    ${compactRecurringBadge}
                    ${task.due ? `<span class="compact-due ${dateStatus}"><i class="fas fa-calendar-alt"></i> ${task.due}</span>` : ''}
                    ${task.list_title ? `<span class="compact-list"><i class="fas fa-list"></i> ${task.list_title}</span>` : ''}
                    <span class="compact-status-badge ${statusClass}">${task.status}</span>
                    ${task.notes || task.description ? `<span class="compact-has-notes" title="Has notes/description"><i class="fas fa-sticky-note"></i></span>` : ''}
                    ${task.tags && task.tags.length ? `<span class="compact-tag-count"><i class="fas fa-tag"></i> ${task.tags.length}</span>` : ''}
                </div>
                <div class="compact-details" id="compact-details-${task.id}" style="display: none;">
                    ${task.description ? `<p class="compact-desc">${task.description}</p>` : ''}
                    ${tagsDisplay}
                    ${notesSection}
                    <div class="compact-expanded-footer">
                        ${task.created_at ? `<span><i class="fas fa-clock"></i> Created: ${String(task.created_at).slice(0, 10)}</span>` : ''}
                        ${task.account ? `<span><i class="fas fa-user"></i> ${task.account}</span>` : ''}
                    </div>
                </div>
            </div>
            <div class="compact-actions">
                ${compactQuickViewBtnHtml}
                ${editBtnHtml}
                <button class="compact-expand-btn" onclick="window.toggleCompactDetails('${task.id}'); event.stopPropagation();" title="Toggle details">
                    <i class="fas fa-chevron-down" id="compact-chevron-${task.id}"></i>
                </button>
            </div>
        `;
    } else {
        // Main task card HTML (Comfortable Card View)
        card.innerHTML = `
            <div class="task-card-actions">
                ${completeBtnHtml}
                ${quickViewBtnHtml}
                ${editBtnHtml}
            </div>
            <div class="task-card-header">
                <span class="task-priority-badge ${priorityClass}">${priorityIcon} ${task.calculated_priority || task.priority}</span>
                <span class="task-status-badge ${statusClass}">${task.status}</span>
                ${recurringBadge}
                ${dateStatusBadge}
            </div>
            <h4 class="task-card-title" onclick="openQuickView('${task.id}')" style="cursor: pointer;" title="Quick view details">${task.title}</h4>
            <div class="task-card-dates">${compactDates}</div>
            ${task.description ? `<p class="task-card-description">${task.description}</p>` : ''}
            ${tagsDisplay}
            ${notesSection}
            <div class="task-card-footer">
                ${task.due ? `<span class="task-due"><i class="fas fa-calendar"></i> ${task.due}</span>` : ''}
                ${task.list_title ? `<span class="task-list"><i class="fas fa-list" style="color: #8b5cf6;"></i> ${task.list_title}</span>` : ''}
                ${task.account ? `<span class="task-account"><i class="fas fa-user"></i> ${task.account}</span>` : ''}
            </div>
        `;
    }
    
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
 * Render tasks to a container
 * @param {Array} tasks - Array of tasks to render
 * @param {HTMLElement} container - The container element
 * @param {Object} options - Rendering options
 */
export function renderTasks(tasks, container, options = {}) {
    if (!container) return;
    
    container.innerHTML = '';
    
    if (!tasks || tasks.length === 0) {
        container.innerHTML = '<p style="text-align: center; color: #6b7280;">No tasks found.</p>';
        return;
    }
    
    tasks.forEach(task => {
        const card = createTaskCard(task, options);
        container.appendChild(card);
    });
}

/**
 * Create and render tasks grid
 * @param {Array} tasks - Array of tasks
 * @param {string} containerId - The container element ID
 * @param {Object} options - Rendering options
 */
export function renderTasksGrid(tasks, containerId, options = {}) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    renderTasks(tasks, container, options);
}

// Global helper for toggling compact task details
window.toggleCompactDetails = function(taskId) {
    const details = document.getElementById(`compact-details-${taskId}`);
    const chevron = document.getElementById(`compact-chevron-${taskId}`);
    if (!details) return;
    
    const isHidden = details.style.display === 'none';
    if (isHidden) {
        details.style.display = 'block';
        if (chevron) chevron.className = 'fas fa-chevron-up';
    } else {
        details.style.display = 'none';
        if (chevron) chevron.className = 'fas fa-chevron-down';
    }
};

