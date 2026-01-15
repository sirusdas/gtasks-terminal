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
    
    if (options.isNodeTask) {
        // Node task card HTML
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
    } else {
        // Main task card HTML
        card.innerHTML = `
            ${completeBtnHtml}
            <div class="task-card-header">
                <span class="task-priority-badge ${priorityClass}">${priorityIcon} ${task.calculated_priority || task.priority}</span>
                <span class="task-status-badge ${statusClass}">${task.status}</span>
                ${dateStatusBadge}
            </div>
            <h4 class="task-card-title">${task.title}</h4>
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
            const isExpanded = notesContent.style.maxHeight !== '0px' && notesContent.style.maxHeight !== '';
            
            if (isExpanded) {
                notesContent.style.maxHeight = '0px';
                this.textContent = 'Show more 📓';
            } else {
                notesContent.style.maxHeight = notesContent.scrollHeight + 'px';
                this.textContent = 'Show less 📓';
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
