/**
 * Dashboard Module
 * Main dashboard functionality and initialization
 */

import { stateManager } from './state.js';
import { apiEndpoints, refreshIntervalOptions, storageKeys } from './constants.js';
import { 
    filterOutDeletedTasks, 
    sortTasksByField, 
    filterTasksByCriteria,
    debounce 
} from './utils.js';
import { createTaskCard, renderTasksGrid } from './task-card.js';
import { createMultiselect, getUniqueLists, getUniqueTags, getListsWithCounts, getTagsWithCounts, getFilteredTagsByLists, getFilteredListsByTags, getFilteredTasksBySearchAndDate, getFilteredListsByTagsAndCriteria, getFilteredTagsByListsAndCriteria } from './multiselect.js';
import { 
    renderHierarchy,
    initHierarchy,
    updateHierarchyVisualization as updateHierarchyViz,
    initHierarchyFilters,
    refreshHierarchyVisualization
} from './hierarchy.js';

// Force load hierarchy-renderer.js module directly
import * as HierarchyRenderer from './hierarchy-renderer.js';

console.log('[Dashboard] HierarchyRenderer module loaded:', Object.keys(HierarchyRenderer));
console.log('[Dashboard] renderHierarchy function:', typeof HierarchyRenderer.renderHierarchy);
console.log('[Dashboard] updateHierarchyVisualization function:', typeof HierarchyRenderer.updateHierarchyVisualization);
console.log('[Dashboard] initHierarchy function:', typeof HierarchyRenderer.initHierarchy);

// Global references for backward compatibility
let dashboardData = {};
let selectedAccount = null;
let isFullscreen = false;
let hierarchyData = {};
let selectedNode = null;
let autoRefreshInterval = null;

// Sync state variables
let isSyncing = false;
let syncProgress = { percentage: 0, message: '', status: 'idle' };
let syncPollInterval = null;

// Export for backward compatibility
export function getDashboardData() {
    return dashboardData;
}

export function setDashboardData(data) {
    dashboardData = data;
    window.dashboardData = data;  // Also set on window for other modules to access
    stateManager.setDashboardData(data);
}

export function getHierarchyData() {
    return hierarchyData;
}

export function setHierarchyData(data) {
    hierarchyData = data;
    stateManager.setHierarchyData(data);
}

export function getSelectedNode() {
    return selectedNode;
}

export function setSelectedNode(node) {
    selectedNode = node;
    stateManager.setSelectedNode(node);
}

// ========== UI Functions ==========

/**
 * Show/hide loading overlay
 */
export function showLoading(show) {
    document.getElementById('loading-overlay').style.display = show ? 'flex' : 'none';
}

/**
 * Get current section from URL path
 * @returns {string} - The section name ('dashboard', 'hierarchy', 'tasks')
 */
export function getCurrentSectionFromPath() {
    const path = window.location.pathname;
    if (path === '/hierarchy' || path.startsWith('/hierarchy')) {
        return 'hierarchy';
    } else if (path === '/tasks' || path.startsWith('/tasks')) {
        return 'tasks';
    } else if (path === '/dashboard' || path === '/') {
        return 'dashboard';
    }
    return 'dashboard'; // Default to dashboard
}

/**
 * Update navigation active state based on current section
 * @param {string} section - The current section name
 */
export function updateNavActiveState(section) {
    // Remove active class from all nav items
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    
    // Add active class to current section's nav item
    const navItem = document.getElementById(`nav-${section}`);
    if (navItem) {
        navItem.classList.add('active');
    }
}

/**
 * Show section
 * @param {string} section - The section name to show
 * @param {boolean} updateUrl - Whether to update the URL (default: true)
 */
export function showSection(section, updateUrl = true) {
    document.querySelectorAll('.section').forEach(s => s.style.display = 'none');
    
    const sectionEl = document.getElementById(`${section}-section`);
    if (sectionEl) {
        sectionEl.style.display = 'block';
    }
    
    // Update navigation active state
    updateNavActiveState(section);
    
    // Update URL without full page reload (only if updateUrl is true)
    if (updateUrl) {
        const newUrl = `/${section === 'dashboard' ? '' : section}`;
        window.history.replaceState({}, '', newUrl);
    }
    
    stateManager.setCurrentSection(section);
    
    if (section === 'hierarchy') {
        // Add a small delay to allow the browser to calculate layout dimensions
        setTimeout(() => {
            loadHierarchy();
        }, 50);
    }
}

/**
 * Toggle sidebar
 */
export function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.getElementById('main-content');
    sidebar.classList.toggle('collapsed');
    mainContent.classList.toggle('expanded');
}

/**
 * Toggle fullscreen
 */
export function toggleFullscreen() {
    isFullscreen = stateManager.toggleFullscreen();
    
    setTimeout(() => {
        if (typeof updateHierarchyViz === 'function') {
            updateHierarchyViz(hierarchyData);
        }
    }, 300);
}

// ========== Data Loading ==========

/**
 * Load dashboard data
 */
export async function loadDashboard() {
    showLoading(true);
    try {
        const response = await fetch(apiEndpoints.data);
        const data = await response.json();
        setDashboardData(data);

        updateStats();
        updateAccountSelectors();
        loadTasks();

        // Load hierarchy data
        await loadHierarchy();

        console.log('Dashboard loaded successfully');
    } catch (error) {
        console.error('Error loading dashboard:', error);
    } finally {
        showLoading(false);
    }
}

// ========== Advanced Sync ==========

/**
 * Start an advanced sync operation
 */
export async function startAdvancedSync() {
    // Prevent multiple simultaneous sync operations
    if (isSyncing) {
        console.log('[Sync] Sync already in progress, ignoring duplicate request');
        showNotification('Sync already in progress...', 'warning');
        return;
    }

    isSyncing = true;
    syncProgress = { percentage: 0, message: 'Starting sync...', status: 'running' };

    // Disable refresh button
    const refreshBtn = document.querySelector('.header-refresh-btn');
    if (refreshBtn) {
        refreshBtn.disabled = true;
        refreshBtn.classList.add('disabled');
    }

    // Show progress UI
    updateSyncProgressUI();

    try {
        console.log('[Sync] Starting advanced sync...');

        // Start the advanced sync
        const startResponse = await fetch(apiEndpoints.sync.advanced, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ sync_type: 'both' })
        });

        if (!startResponse.ok) {
            throw new Error(`Failed to start sync: ${startResponse.status}`);
        }

        const startData = await startResponse.json();
        console.log('[Sync] Advanced sync started:', startData);

        const syncId = startData.sync_id;

        // Start polling for progress
        syncPollInterval = setInterval(async () => {
            await pollSyncProgress(syncId);
        }, 500);

    } catch (error) {
        console.error('[Sync] Error starting advanced sync:', error);
        syncProgress = { percentage: 0, message: error.message, status: 'error' };
        updateSyncProgressUI();

        // Re-enable refresh button after a delay
        setTimeout(() => {
            stopSyncProgressUI();
        }, 3000);
    }
}

/**
 * Poll sync progress
 * @param {string} syncId - The sync operation ID
 */
async function pollSyncProgress(syncId) {
    try {
        const response = await fetch(`${apiEndpoints.sync.progress}?sync_id=${syncId}`);
        if (!response.ok) {
            throw new Error(`Failed to get sync progress: ${response.status}`);
        }

        const progressData = await response.json();
        console.log('[Sync] Progress update:', progressData);

        // Extract progress from data object (API returns data nested in 'data' property)
        const progress = progressData.data || progressData;

        // Update progress state
        syncProgress = {
            percentage: progress.percentage || 0,
            message: progress.message || 'Processing...',
            status: progress.status || 'running'
        };

        // Update UI
        updateSyncProgressUI();

        // Check if sync is complete or error
        if (progress.status === 'completed') {
            clearInterval(syncPollInterval);
            syncPollInterval = null;

            // Show completion message
            syncProgress.message = 'Sync completed successfully!';
            syncProgress.status = 'completed';
            updateSyncProgressUI();

            console.log('[Sync] Sync completed successfully');

            // Wait a moment then refresh cache and dashboard
            setTimeout(async () => {
                // First refresh the cache on the server
                try {
                    await fetch(apiEndpoints.refresh, { method: 'POST' });
                } catch (e) {
                    console.warn('[Sync] Cache refresh failed, continuing with loadDashboard:', e);
                }
                
                // Then reload the dashboard data
                await loadDashboard();
                stopSyncProgressUI();
                showNotification('Data refreshed successfully! ✅', 'success');
            }, 1000);
        } else if (progressData.status === 'error') {
            clearInterval(syncPollInterval);
            syncPollInterval = null;

            syncProgress.message = progressData.message || 'Sync failed';
            syncProgress.status = 'error';
            updateSyncProgressUI();

            console.error('[Sync] Sync error:', progressData.message);

            // Re-enable refresh button after showing error
            setTimeout(() => {
                stopSyncProgressUI();
                showNotification(`Sync failed: ${progressData.message}`, 'error');
            }, 3000);
        }
    } catch (error) {
        console.error('[Sync] Error polling sync progress:', error);
        syncProgress.message = error.message;
        syncProgress.status = 'error';
        updateSyncProgressUI();
    }
}

/**
 * Update the sync progress UI
 */
export function updateSyncProgressUI() {
    let overlay = document.getElementById('sync-progress-overlay');

    // Create overlay if it doesn't exist
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'sync-progress-overlay';
        overlay.className = 'sync-progress-overlay';
        document.body.appendChild(overlay);

        overlay.innerHTML = `
            <div class="sync-progress-modal">
                <div class="sync-progress-header">
                    <i class="fas fa-sync-alt fa-spin"></i>
                    <span>Syncing Data</span>
                </div>
                <div class="sync-progress-content">
                    <div class="sync-progress-bar-container">
                        <div class="sync-progress-bar" id="sync-progress-bar" style="width: 0%"></div>
                    </div>
                    <div class="sync-progress-info">
                        <span id="sync-progress-percentage">0%</span>
                        <span id="sync-progress-message">Starting sync...</span>
                    </div>
                    <div class="sync-progress-status" id="sync-progress-status">Running</div>
                </div>
            </div>
        `;
    }

    // Update progress bar
    const progressBar = document.getElementById('sync-progress-bar');
    const percentageText = document.getElementById('sync-progress-percentage');
    const messageText = document.getElementById('sync-progress-message');
    const statusText = document.getElementById('sync-progress-status');
    const headerIcon = overlay.querySelector('.sync-progress-header i');

    if (progressBar) {
        progressBar.style.width = `${syncProgress.percentage}%`;
    }

    if (percentageText) {
        percentageText.textContent = `${syncProgress.percentage}%`;
    }

    if (messageText) {
        messageText.textContent = syncProgress.message;
    }

    if (statusText) {
        statusText.textContent = syncProgress.status.charAt(0).toUpperCase() + syncProgress.status.slice(1);
        statusText.className = `sync-progress-status status-${syncProgress.status}`;
    }

    // Update header icon based on status
    if (headerIcon) {
        if (syncProgress.status === 'completed') {
            headerIcon.className = 'fas fa-check-circle';
            headerIcon.style.color = 'var(--success-color)';
        } else if (syncProgress.status === 'error') {
            headerIcon.className = 'fas fa-exclamation-circle';
            headerIcon.style.color = 'var(--danger-color)';
        } else {
            headerIcon.className = 'fas fa-sync-alt fa-spin';
            headerIcon.style.color = 'var(--primary-color)';
        }
    }

    // Show overlay
    overlay.classList.add('active');
}

/**
 * Stop sync progress UI and reset state
 */
export function stopSyncProgressUI() {
    // Clear poll interval
    if (syncPollInterval) {
        clearInterval(syncPollInterval);
        syncPollInterval = null;
    }

    // Reset sync state
    isSyncing = false;
    syncProgress = { percentage: 0, message: '', status: 'idle' };

    // Hide overlay
    const overlay = document.getElementById('sync-progress-overlay');
    if (overlay) {
        overlay.classList.remove('active');
    }

    // Re-enable refresh button
    const refreshBtn = document.querySelector('.header-refresh-btn');
    if (refreshBtn) {
        refreshBtn.disabled = false;
        refreshBtn.classList.remove('disabled');
    }
}

/**
 * Refresh data using advanced sync
 * This is the new function that replaces direct loadDashboard() call
 */
export async function refreshWithAdvancedSync() {
    await startAdvancedSync();
}

/**
 * Simple cache refresh - reloads data from database without full sync
 * This is called when the refresh button is clicked
 */
export async function simpleCacheRefresh() {
    console.log('[Dashboard] Simple cache refresh...');
    try {
        const response = await fetch(apiEndpoints.refresh, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const data = await response.json();

        if (data.success) {
            console.log('[Dashboard] Cache refreshed successfully:', data);
            // Reload dashboard data to reflect changes
            await loadDashboard();
            showNotification('Dashboard refreshed! ✅', 'success');
        } else {
            console.error('[Dashboard] Cache refresh failed:', data.message);
            showNotification(data.message || 'Refresh failed', 'error');
        }
    } catch (error) {
        console.error('[Dashboard] Error during cache refresh:', error);
        showNotification('Error refreshing dashboard', 'error');
    }
}

// ========== Refresh Dropdown Functions ==========

/**
 * Toggle the refresh dropdown menu
 */
export function toggleRefreshDropdown() {
    const dropdown = document.getElementById('refresh-dropdown-menu');
    if (dropdown) {
        dropdown.classList.toggle('active');
    }
}

/**
 * Sync data and refresh cache
 * This is called when "Sync Data" option is selected
 */
export async function syncAndRefresh() {
    console.log('[Dashboard] Sync and refresh...');
    // Start advanced sync - this will automatically refresh cache when complete
    await startAdvancedSync();
}

/**
 * Close refresh dropdown when clicking outside
 */
export function setupRefreshDropdown() {
    document.addEventListener('click', (e) => {
        const dropdown = document.getElementById('refresh-dropdown-menu');
        const toggle = document.querySelector('.refresh-dropdown-toggle');
        if (dropdown && toggle && !dropdown.contains(e.target) && !toggle.contains(e.target)) {
            dropdown.classList.remove('active');
        }
    });
}

/**
 * Update statistics
 */
export function updateStats() {
    const stats = dashboardData.stats || {};
    document.getElementById('total-tasks').textContent = stats.total || 0;
    document.getElementById('completed-tasks').textContent = stats.completed || 0;
    document.getElementById('pending-tasks').textContent = stats.pending || 0;
    document.getElementById('critical-tasks').textContent = stats.critical || 0;
    document.getElementById('high-tasks').textContent = stats.high || 0;
    document.getElementById('overdue-tasks').textContent = stats.overdue || 0;
    
    // Update progress ring
    const completionRate = stats.completion_rate || 0;
    document.getElementById('completion-rate').textContent = Math.round(completionRate) + '%';
    const circle = document.getElementById('completion-ring');
    if (circle) {
        const circumference = 2 * Math.PI * 52;
        const offset = circumference - (completionRate / 100) * circumference;
        circle.style.strokeDasharray = circumference;
        circle.style.strokeDashoffset = offset;
    }
}

/**
 * Update account selectors
 */
export function updateAccountSelectors() {
    const accounts = dashboardData.accounts || [];
    const currentAccount = dashboardData.current_account;
    
    const selectors = [
        document.getElementById('account-selector'),
        document.getElementById('hierarchy-account-selector'),
        document.getElementById('tasks-account-selector')
    ];
    
    selectors.forEach(selector => {
        if (selector) {
            selector.innerHTML = accounts.map(acc => 
                `<option value="${acc.id}" ${acc.id === currentAccount ? 'selected' : ''}>${acc.name}</option>`
            ).join('');
        }
    });
}

/**
 * Switch account
 */
export async function switchAccount(accountId) {
    if (!accountId) return;
    
    showLoading(true);
    try {
        const response = await fetch(apiEndpoints.accountsSwitch(accountId), { method: 'POST' });
        const result = await response.json();
        
        if (result.success) {
            await loadDashboard();
        }
    } catch (error) {
        console.error('Error switching account:', error);
    } finally {
        showLoading(false);
    }
}

export function switchAccountForHierarchy(accountId) {
    switchAccount(accountId);
}

export function switchAccountForTasks(accountId) {
    switchAccount(accountId);
}

// ========== Tasks ==========

/**
 * Load tasks
 */
export function loadTasks() {
    const tasks = dashboardData.tasks || [];
    const filteredTasks = filterOutDeletedTasks(tasks);
    const container = document.getElementById('tasks-grid');
    if (!container) return;
    
    container.innerHTML = '';
    
    // Initialize task count display
    updateTasksCountDisplay(filteredTasks.length, tasks.length);
    
    if (filteredTasks.length === 0) {
        container.innerHTML = '<p style="text-align: center; color: #6b7280;">No tasks found for this account.</p>';
        return;
    }
    
    // Initialize multiselect filters with available options
    initMultiselectFilters(tasks);
    
    // Sort by due date descending by default
    const sortedTasks = sortTasksByField(filteredTasks, 'due', 'desc');
    
    sortedTasks.forEach(task => {
        const card = createTaskCard(task);
        container.appendChild(card);
    });
}

/**
 * Initialize multiselect filters
 */
let listMultiselect = null;
let tagsMultiselect = null;
let allTasks = []; // Store all tasks for filtering

export function initMultiselectFilters(tasks) {
    // Store all tasks for filtering
    allTasks = tasks;
    
    // Get unique lists and tags with pending task counts (sorted by count descending)
    const listsWithCounts = getListsWithCounts(tasks);
    const tagsWithCounts = getTagsWithCounts(tasks);
    
    // Also get plain lists for backward compatibility
    const lists = getUniqueLists(tasks);
    const tags = getUniqueTags(tasks);
    
    console.log('[Dashboard] initMultiselectFilters - Tasks count:', tasks.length);
    console.log('[Dashboard] Lists with counts:', listsWithCounts);
    console.log('[Dashboard] Tags with counts:', tagsWithCounts);
    
    // Initialize List filter (was "Filter by Project")
    const listContainer = document.getElementById('task-list-filter-container');
    if (listContainer) {
        // Clear existing content
        listContainer.innerHTML = '';
        
        listMultiselect = createMultiselect({
            id: 'task-list-filter',
            placeholder: 'Filter by List...',
            options: listsWithCounts,
            initialValues: [],
            onChange: (values) => {
                console.log('[Dashboard] List filter changed:', values);
                updateFilteredMultiselect();
                filterTasks();
            },
            searchMinChars: 0,
            showCounts: true
        });
        listContainer.appendChild(listMultiselect);
    }
    
    // Initialize Tags filter
    const tagsContainer = document.getElementById('task-tags-filter-container');
    if (tagsContainer) {
        // Clear existing content
        tagsContainer.innerHTML = '';
        
        tagsMultiselect = createMultiselect({
            id: 'task-tags-filter',
            placeholder: 'Filter by Tags...',
            options: tagsWithCounts,
            initialValues: [],
            onChange: (values) => {
                console.log('[Dashboard] Tags filter changed:', values);
                updateFilteredMultiselect();
                filterTasks();
            },
            searchMinChars: 0,
            showCounts: true
        });
        tagsContainer.appendChild(tagsMultiselect);
    }
    
    // Add event listeners for search and date filters to update multiselect options
    setupFilterEventListeners();
}

/**
 * Setup event listeners for search and date filters
 * These listeners trigger updateFilteredMultiselect() to provide bidirectional filtering
 */
function setupFilterEventListeners() {
    // Search filter input listener
    const searchFilter = document.getElementById('task-search-filter');
    if (searchFilter) {
        searchFilter.addEventListener('input', debounce((e) => {
            console.log('[Dashboard] Search filter changed:', e.target.value);
            updateFilteredMultiselect(
                e.target.value,
                document.getElementById('task-date-start')?.value || '',
                document.getElementById('task-date-end')?.value || '',
                document.getElementById('task-date-field')?.value || 'due'
            );
            filterTasks();
        }, 300)); // Debounce to avoid too frequent updates
    }
    
    // Date field listener
    const dateFieldFilter = document.getElementById('task-date-field');
    if (dateFieldFilter) {
        dateFieldFilter.addEventListener('change', (e) => {
            console.log('[Dashboard] Date field filter changed:', e.target.value);
            updateFilteredMultiselect(
                document.getElementById('task-search-filter')?.value || '',
                document.getElementById('task-date-start')?.value || '',
                document.getElementById('task-date-end')?.value || '',
                e.target.value
            );
            filterTasks();
        });
    }
    
    // Date start listener
    const dateStartFilter = document.getElementById('task-date-start');
    if (dateStartFilter) {
        dateStartFilter.addEventListener('change', (e) => {
            console.log('[Dashboard] Date start filter changed:', e.target.value);
            updateFilteredMultiselect(
                document.getElementById('task-search-filter')?.value || '',
                e.target.value,
                document.getElementById('task-date-end')?.value || '',
                document.getElementById('task-date-field')?.value || 'due'
            );
            filterTasks();
        });
    }
    
    // Date end listener
    const dateEndFilter = document.getElementById('task-date-end');
    if (dateEndFilter) {
        dateEndFilter.addEventListener('change', (e) => {
            console.log('[Dashboard] Date end filter changed:', e.target.value);
            updateFilteredMultiselect(
                document.getElementById('task-search-filter')?.value || '',
                document.getElementById('task-date-start')?.value || '',
                e.target.value,
                document.getElementById('task-date-field')?.value || 'due'
            );
            filterTasks();
        });
    }
}

/**
 * Update filtered multiselect options based on current selections
 * Implements bidirectional filtering between List and Tags filters
 * Also considers search text and date range filters
 * @param {string} searchText - Search text from task-search-filter
 * @param {string} dateStart - Start date from task-date-start
 * @param {string} dateEnd - End date from task-date-end
 * @param {string} dateField - Date field from task-date-field
 */
export function updateFilteredMultiselect(searchText = '', dateStart = '', dateEnd = '', dateField = 'due') {
    // Get current selections from both multiselects
    const selectedLists = listMultiselect ? listMultiselect.getSelectedValues() : [];
    const selectedTags = tagsMultiselect ? tagsMultiselect.getSelectedValues() : [];
    
    console.log('[Dashboard] updateFilteredMultiselect - Selected lists:', selectedLists);
    console.log('[Dashboard] updateFilteredMultiselect - Selected tags:', selectedTags);
    console.log('[Dashboard] updateFilteredMultiselect - Search text:', searchText);
    console.log('[Dashboard] updateFilteredMultiselect - Date range:', dateStart, 'to', dateEnd);
    console.log('[Dashboard] updateFilteredMultiselect - Date field:', dateField);
    
    // Get filtered options based on selections and search/date criteria
    const filteredTags = getFilteredTagsByListsAndCriteria(allTasks, selectedLists, searchText, dateField, dateStart, dateEnd);
    const filteredLists = getFilteredListsByTagsAndCriteria(allTasks, selectedTags, searchText, dateField, dateStart, dateEnd);
    
    console.log('[Dashboard] updateFilteredMultiselect - Filtered tags:', filteredTags);
    console.log('[Dashboard] updateFilteredMultiselect - Filtered lists:', filteredLists);
    
    // Update multiselect options
    if (tagsMultiselect) {
        tagsMultiselect.setOptions(filteredTags);
        console.log('[Dashboard] Updated tags multiselect with', filteredTags.length, 'options');
    }
    
    if (listMultiselect) {
        listMultiselect.setOptions(filteredLists);
        console.log('[Dashboard] Updated list multiselect with', filteredLists.length, 'options');
    }
}

/**
 * Update task count display
 * @param {number} filteredCount - Number of filtered tasks
 * @param {number} totalCount - Total number of tasks
 */
export function updateTasksCountDisplay(filteredCount, totalCount) {
    const countDisplay = document.getElementById('tasks-count-display');
    const countText = document.getElementById('tasks-count-text');
    
    if (countText) {
        if (filteredCount === totalCount) {
            countText.textContent = `Showing all ${totalCount} tasks`;
        } else {
            countText.textContent = `Showing ${filteredCount} of ${totalCount} tasks`;
        }
    }
    
    if (countDisplay) {
        countDisplay.style.display = 'block';
    }
}

/**
 * Filter tasks with advanced filters
 */
export function filterTasks() {
    // Get values from multiselect filters
    const listFilterEl = document.getElementById('task-list-filter');
    const tagsFilterEl = document.getElementById('task-tags-filter');
    
    let listValues = [];
    let tagValues = [];
    
    if (listFilterEl) {
        console.log('[Dashboard] List filter element value:', listFilterEl.value);
        try {
            listValues = listFilterEl.value ? JSON.parse(listFilterEl.value) : [];
            console.log('[Dashboard] Parsed list values:', listValues);
        } catch (e) {
            console.error('[Dashboard] Error parsing list filter:', e);
            listValues = [];
        }
    }
    
    if (tagsFilterEl) {
        console.log('[Dashboard] Tags filter element value:', tagsFilterEl.value);
        try {
            tagValues = tagsFilterEl.value ? JSON.parse(tagsFilterEl.value) : [];
            console.log('[Dashboard] Parsed tag values:', tagValues);
        } catch (e) {
            console.error('[Dashboard] Error parsing tags filter:', e);
            tagValues = [];
        }
    }
    
    const filters = {
        search: document.getElementById('task-search-filter')?.value.toLowerCase() || '',
        status: document.getElementById('task-status-filter')?.value || '',
        priority: document.getElementById('task-priority-filter')?.value || '',
        list: listValues,
        tags: tagValues,
        dateField: document.getElementById('task-date-field')?.value || 'due',
        dateStart: document.getElementById('task-date-start')?.value || '',
        dateEnd: document.getElementById('task-date-end')?.value || '',
        sortField: document.getElementById('task-sort-field')?.value || 'due',
        sortOrder: document.getElementById('task-sort-order')?.value || 'asc'
    };
    
    console.log('[Dashboard] Applying filters:', filters);
    
    let filteredTasks = dashboardData.tasks || [];
    const totalTasks = filteredTasks.length;
    const container = document.getElementById('tasks-grid');
    if (!container) return;
    
    container.innerHTML = '';
    
    // Filter out deleted tasks if setting is enabled
    filteredTasks = filterOutDeletedTasks(filteredTasks);
    
    // Apply filters
    filteredTasks = filterTasksByCriteria(filteredTasks, filters);
    
    console.log('[Dashboard] Filtered tasks count:', filteredTasks.length);
    
    // Update task count display
    updateTasksCountDisplay(filteredTasks.length, totalTasks);
    
    if (filteredTasks.length === 0) {
        container.innerHTML = '<p style="text-align: center; color: #6b7280;">No tasks match your filters.</p>';
        return;
    }
    
    filteredTasks.forEach(task => {
        const card = createTaskCard(task);
        container.appendChild(card);
    });
}

/**
 * Clear all task filters
 */
export function clearTasksFilters() {
    // Reset search filter
    const searchFilter = document.getElementById('task-search-filter');
    if (searchFilter) searchFilter.value = '';
    
    // Reset status filter
    const statusFilter = document.getElementById('task-status-filter');
    if (statusFilter) statusFilter.value = '';
    
    // Reset priority filter
    const priorityFilter = document.getElementById('task-priority-filter');
    if (priorityFilter) priorityFilter.value = '';
    
    // Reset list filter (was project filter)
    if (listMultiselect) {
        listMultiselect.clear();
    }
    
    // Reset tags filter
    if (tagsMultiselect) {
        tagsMultiselect.clear();
    }
    
    // Reset date field filter
    const dateFieldFilter = document.getElementById('task-date-field');
    if (dateFieldFilter) dateFieldFilter.value = 'due';
    
    // Reset date range filters
    const dateStartFilter = document.getElementById('task-date-start');
    if (dateStartFilter) dateStartFilter.value = '';
    
    const dateEndFilter = document.getElementById('task-date-end');
    if (dateEndFilter) dateEndFilter.value = '';
    
    // Reset sort field
    const sortFieldFilter = document.getElementById('task-sort-field');
    if (sortFieldFilter) sortFieldFilter.value = 'due';
    
    // Reset sort order
    const sortOrderFilter = document.getElementById('task-sort-order');
    if (sortOrderFilter) sortOrderFilter.value = 'desc';
    
    // Restore all options to multiselects and re-apply filters
    const allLists = getListsWithCounts(allTasks);
    const allTags = getTagsWithCounts(allTasks);
    
    if (listMultiselect) {
        listMultiselect.setOptions(allLists);
    }
    
    if (tagsMultiselect) {
        tagsMultiselect.setOptions(allTags);
    }
    
    // Update filtered multiselects with no search/date criteria to restore bidirectional filtering
    updateFilteredMultiselect('', '', '', 'due');
    
    // Re-apply filters
    filterTasks();
}

// ========== Hierarchy ==========

/**
 * Load hierarchy data
 */
export async function loadHierarchy() {
    console.log('[Dashboard] loadHierarchy called');
    try {
        console.log('[Dashboard] Fetching hierarchy data from:', apiEndpoints.hierarchy);
        const response = await fetch(apiEndpoints.hierarchy);
        console.log('[Dashboard] Hierarchy response status:', response.status);
        const data = await response.json();
        console.log('[Dashboard] Hierarchy data received:', data);
        setHierarchyData(data);
        
        // Update visualization
        console.log('[Dashboard] Calling updateHierarchyViz...');
        
        // Make sure hierarchyData is set in the renderer module
        console.log('[Dashboard] window.setHierarchyData exists:', typeof window.setHierarchyData);
        if (typeof window.setHierarchyData === 'function') {
            console.log('[Dashboard] Calling window.setHierarchyData...');
            window.setHierarchyData(data);
            console.log('[Dashboard] window.setHierarchyData called successfully');
        } else {
            console.error('[Dashboard] window.setHierarchyData is not a function!');
        }
        
        if (typeof updateHierarchyViz === 'function') {
            updateHierarchyViz(data);
        } else {
            console.error('[Dashboard] updateHierarchyViz is not a function:', typeof updateHierarchyViz);
        }
        
        // Initialize filter event listeners
        console.log('[Dashboard] Calling initHierarchyFilters...');
        if (typeof initHierarchyFilters === 'function') {
            window.initHierarchyFilters();
        } else {
            console.error('[Dashboard] initHierarchyFilters is not a function:', typeof initHierarchyFilters);
        }
    } catch (error) {
        console.error('[Dashboard] Error loading hierarchy:', error);
    }
}

/**
 * Refresh hierarchy
 */
export async function refreshHierarchy() {
    await loadHierarchy();
}

// ========== Settings ==========

/**
 * Initialize settings
 */
export function initSettings() {
    const settings = stateManager.getSettings();
    
    // Update UI
    const toggleElement = document.getElementById('auto-refresh-toggle');
    const intervalSelect = document.getElementById('refresh-interval');
    const viewSelect = document.getElementById('default-view');
    const hideDeletedToggle = document.getElementById('hide-deleted-toggle');
    
    if (settings.autoRefreshEnabled && toggleElement) {
        toggleElement.classList.add('active');
    }
    
    if (intervalSelect) {
        intervalSelect.value = settings.refreshInterval / 1000;
    }
    
    if (viewSelect) {
        viewSelect.value = settings.defaultView;
    }
    
    if (hideDeletedToggle && settings.hideDeletedEnabled) {
        hideDeletedToggle.classList.add('active');
    }
    
    // Apply auto-refresh if enabled
    if (settings.autoRefreshEnabled) {
        stateManager.startAutoRefresh(settings.refreshInterval);
    }
    
    // Apply default view only when accessing root URL (not /dashboard)
    // URL path takes precedence over saved default view setting
    const path = window.location.pathname;
    
    // Only apply default view on root URL, not on /dashboard
    if (settings.defaultView && settings.defaultView !== 'dashboard' && path === '/') {
        showSection(settings.defaultView, false);
    }
}

export function openSettings() {
    document.getElementById('settings-modal').classList.add('active');
}

export function closeSettings() {
    document.getElementById('settings-modal').classList.remove('active');
}

export function toggleAutoRefresh() {
    const toggleElement = document.getElementById('auto-refresh-toggle');
    const isEnabled = toggleElement.classList.toggle('active');
    
    stateManager.updateSetting('autoRefreshEnabled', isEnabled);
    
    const interval = stateManager.getSettings().refreshInterval;
    
    if (isEnabled) {
        stateManager.startAutoRefresh(interval);
    } else {
        stateManager.stopAutoRefresh();
    }
}

export function updateRefreshInterval() {
    const intervalSelect = document.getElementById('refresh-interval');
    const interval = intervalSelect ? parseInt(intervalSelect.value) * 1000 : 60000;
    
    stateManager.updateSetting('refreshInterval', interval);
    
    // Restart auto-refresh with new interval if enabled
    if (stateManager.getSettings().autoRefreshEnabled) {
        stateManager.stopAutoRefresh();
        stateManager.startAutoRefresh(interval);
    }
}

export function updateDefaultView() {
    const viewSelect = document.getElementById('default-view');
    stateManager.updateSetting('defaultView', viewSelect ? viewSelect.value : 'dashboard');
}

export function toggleHideDeleted() {
    const toggleElement = document.getElementById('hide-deleted-toggle');
    const isEnabled = toggleElement.classList.toggle('active');
    
    stateManager.updateSetting('hideDeletedEnabled', isEnabled);
    
    // Refresh tasks and hierarchy to apply the filter
    loadTasks();
    
    // Re-filter hierarchy visualization
    if (typeof refreshHierarchyVisualization === 'function') {
        refreshHierarchyVisualization();
    }
    
    console.log(`Hide deleted tasks: ${isEnabled ? 'enabled' : 'disabled'}`);
}

// ========== Keyboard Shortcuts ==========

/**
 * Setup keyboard shortcuts
 */
export function setupKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        if (e.ctrlKey && e.key === 'b') {
            e.preventDefault();
            toggleSidebar();
        }
        if (e.ctrlKey && e.key === 'f') {
            e.preventDefault();
            toggleFullscreen();
            // Show filter panel in fullscreen mode
            if (isFullscreen) {
                document.getElementById('hierarchy-filter-panel').style.display = 'flex';
            }
        }
        if (e.key === 'Escape' && isFullscreen) {
            toggleFullscreen();
        }
    });
}

// ========== Initialize ==========

/**
 * Parse URL query parameters
 * @returns {Object} - Key-value pairs of query parameters
 */
export function parseUrlParams() {
    const params = new URLSearchParams(window.location.search);
    const result = {};
    for (const [key, value] of params) {
        result[key] = value;
    }
    return result;
}

/**
 * Apply URL query parameters to dashboard
 */
export function applyUrlParams() {
    const params = parseUrlParams();
    
    // Handle account parameter
    if (params.account) {
        console.log('[Dashboard] Applying account from URL:', params.account);
        const accountSelector = document.getElementById('account-selector');
        if (accountSelector) {
            // Check if the account exists in the selector
            const options = accountSelector.options;
            let found = false;
            for (let i = 0; i < options.length; i++) {
                if (options[i].value === params.account || options[i].text === params.account) {
                    accountSelector.selectedIndex = i;
                    found = true;
                    break;
                }
            }
            
            // If not found, still try to switch
            if (!found) {
                console.log('[Dashboard] Account not found in selector, attempting to switch:', params.account);
                switchAccount(params.account);
            } else {
                switchAccount(params.account);
            }
        }
    }
    
    // Handle default view parameter
    if (params.view) {
        console.log('[Dashboard] Applying view from URL:', params.view);
        if (['dashboard', 'hierarchy', 'tasks'].includes(params.view)) {
            showSection(params.view);
        }
    }
}

/**
 * Initialize the dashboard
 */
export async function initDashboard() {
    console.log('[Dashboard] initDashboard called');

    // Initialize state from storage
    stateManager.initFromStorage();
    stateManager.initDarkMode();

    // Load settings
    initSettings();

    // Setup refresh dropdown click-outside listener
    setupRefreshDropdown();

    // Apply URL query parameters before loading dashboard data
    applyUrlParams();

    // Detect section from URL path (takes precedence over URL params)
    const pathSection = getCurrentSectionFromPath();
    console.log('[Dashboard] Detected section from path:', pathSection);

    // Show the appropriate section based on URL path
    if (pathSection) {
        showSection(pathSection);
    }

    // Load dashboard data
    await loadDashboard();

    // Setup keyboard shortcuts
    setupKeyboardShortcuts();

    console.log('Dashboard initialized');
}

// ========== Chart Filters ==========

/**
 * Toggle chart filter panel visibility
 */
export function toggleChartFilters() {
    const filterPanel = document.getElementById('hierarchy-filter-panel');
    const toggleBtn = document.querySelector('.filter-toggle-btn');
    
    if (filterPanel.style.display === 'none') {
        filterPanel.style.display = 'flex';
        toggleBtn.classList.add('active');
    } else {
        filterPanel.style.display = 'none';
        toggleBtn.classList.remove('active');
    }
}

/**
 * Apply chart filters - triggers hierarchy refresh
 */
export function applyChartFilters() {
    console.log('[Dashboard] applyChartFilters called');
    console.log('[Dashboard] typeof refreshHierarchyVisualization:', typeof refreshHierarchyVisualization);
    if (typeof refreshHierarchyVisualization === 'function') {
        console.log('[Dashboard] Calling refreshHierarchyVisualization...');
        refreshHierarchyVisualization();
    } else {
        console.error('[Dashboard] refreshHierarchyVisualization is not a function!');
        // Try calling window.refreshHierarchyVisualization as fallback
        if (typeof window.refreshHierarchyVisualization === 'function') {
            console.log('[Dashboard] Calling window.refreshHierarchyVisualization...');
            window.refreshHierarchyVisualization();
        }
    }
}

/**
 * Clear chart filters
 */
export function clearChartFilters() {
    // Reset hierarchy filter inputs
    const tagSearchInput = document.getElementById('hierarchy-tag-search');
    const statusFilter = document.getElementById('hierarchy-status-filter');
    const dateStartInput = document.getElementById('hierarchy-date-start');
    const dateEndInput = document.getElementById('hierarchy-date-end');
    
    if (tagSearchInput) tagSearchInput.value = '';
    if (statusFilter) statusFilter.value = '';
    if (dateStartInput) dateStartInput.value = '';
    if (dateEndInput) dateEndInput.value = '';
    
    // Refresh visualization
    if (typeof refreshHierarchyVisualization === 'function') {
        refreshHierarchyVisualization();
    }
}

/**
 * Clear all node filters
 */
export function clearNodeFilters() {
    // Reset status filter
    const statusFilter = document.getElementById('node-task-status-filter');
    if (statusFilter) statusFilter.value = '';
    
    // Reset priority filter
    const priorityFilter = document.getElementById('node-task-priority-filter');
    if (priorityFilter) priorityFilter.value = '';
    
    // Reset search filter
    const searchFilter = document.getElementById('node-task-search-filter');
    if (searchFilter) searchFilter.value = '';
    
    // Reset project filter
    const projectFilter = document.getElementById('node-task-project-filter');
    if (projectFilter) projectFilter.value = '';
    
    // Reset tags filter
    const tagsFilter = document.getElementById('node-task-tags-filter');
    if (tagsFilter) tagsFilter.value = '';
    
    // Reset date field filter
    const dateFieldFilter = document.getElementById('node-task-date-field');
    if (dateFieldFilter) dateFieldFilter.value = 'due';
    
    // Reset date range filters
    const dateStartFilter = document.getElementById('node-task-date-start');
    if (dateStartFilter) dateStartFilter.value = '';
    
    const dateEndFilter = document.getElementById('node-task-date-end');
    if (dateEndFilter) dateEndFilter.value = '';
    
    // Reset sort field
    const sortFieldFilter = document.getElementById('node-task-sort-field');
    if (sortFieldFilter) sortFieldFilter.value = 'due';
    
    // Reset sort order
    const sortOrderFilter = document.getElementById('node-task-sort-order');
    if (sortOrderFilter) sortOrderFilter.value = 'desc';
    
    // Re-apply filters if a node is selected
    const node = getSelectedNode();
    if (node) {
        if (typeof window.filterNodeTasksHierarchy === 'function') {
            window.filterNodeTasksHierarchy(node);
        }
    }
}

// ========== Complete Task ==========

/**
 * Mark a task as complete
 * @param {string} taskId - The task ID to complete
 */
export async function completeTask(taskId) {
    console.log('[Dashboard] Completing task:', taskId);
    
    try {
        const response = await fetch(`/api/tasks/${taskId}/complete`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({})
        });
        
        const data = await response.json();
        
        if (data.success) {
            console.log('Task completed:', taskId);
            
            // Update UI - change task appearance to completed (no full reload)
            updateTaskCompletedState(taskId);
            
            // Show success feedback
            showNotification('Task completed ✅', 'success');
            
            // Update stats in place without full dashboard reload
            updateStatsInPlace(taskId);
        } else {
            showNotification(data.message || 'Failed to complete task', 'error');
        }
    } catch (error) {
        console.error('Error completing task:', error);
        showNotification('Error completing task', 'error');
    }
}

/**
 * Update stats in place after task completion (no full reload)
 * @param {string} taskId - The completed task ID
 */
function updateStatsInPlace(taskId) {
    const stats = dashboardData.stats || {};
    
    // Update counters
    const completedEl = document.getElementById('completed-tasks');
    const pendingEl = document.getElementById('pending-tasks');
    
    if (completedEl) {
        const currentCompleted = parseInt(completedEl.textContent) || 0;
        completedEl.textContent = currentCompleted + 1;
    }
    
    if (pendingEl) {
        const currentPending = parseInt(pendingEl.textContent) || 0;
        pendingEl.textContent = Math.max(0, currentPending - 1);
    }
    
    // Update completion rate
    const completionRateEl = document.getElementById('completion-rate');
    const totalEl = document.getElementById('total-tasks');
    
    if (completionRateEl && totalEl) {
        const total = parseInt(totalEl.textContent) || 1;
        const completed = parseInt(completedEl?.textContent) || 0;
        const rate = (completed / total) * 100;
        completionRateEl.textContent = Math.round(rate) + '%';
        
        // Update progress ring
        const circle = document.getElementById('completion-ring');
        if (circle) {
            const circumference = 2 * Math.PI * 52;
            const offset = circumference - (rate / 100) * circumference;
            circle.style.strokeDasharray = circumference;
            circle.style.strokeDashoffset = offset;
        }
    }
}

/**
 * Update task UI to show completed state
 * @param {string} taskId - The task ID that was completed
 */
export function updateTaskCompletedState(taskId) {
    // Update in tasks grid
    const taskElement = document.querySelector(`.task-card[data-task-id="${taskId}"]`);
    if (taskElement) {
        taskElement.classList.add('completed');
        const completeBtn = taskElement.querySelector('.task-complete-btn');
        if (completeBtn) {
            completeBtn.innerHTML = '✅';
            completeBtn.title = 'Completed';
            completeBtn.onclick = null;
            completeBtn.style.cursor = 'default';
        }
    }
    
    // Update in hierarchy task panel (node-task-card)
    const nodeTaskElement = document.querySelector(`.node-task-card[data-task-id="${taskId}"]`);
    if (nodeTaskElement) {
        nodeTaskElement.classList.add('completed');
        const completeBtn = nodeTaskElement.querySelector('.task-complete-btn');
        if (completeBtn) {
            completeBtn.innerHTML = '✅';
            completeBtn.title = 'Completed';
            completeBtn.onclick = null;
            completeBtn.style.cursor = 'default';
        }
        // Update status badge
        const statusElement = nodeTaskElement.querySelector('.node-task-status');
        if (statusElement) {
            statusElement.textContent = 'completed';
            statusElement.classList.add('status-completed');
        }
    }
}

/**
 * Show notification
 * @param {string} message - The message to show
 * @param {string} type - The notification type ('success' or 'error')
 */
function showNotification(message, type = 'success') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 14px 28px;
        border-radius: 10px;
        color: white;
        font-weight: 600;
        font-size: 15px;
        z-index: 100000;
        animation: slideIn 0.3s ease;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        ${type === 'success' ? 'background: linear-gradient(135deg, #10b981, #059669);' : 'background: linear-gradient(135deg, #ef4444, #dc2626);'}
    `;
    notification.innerHTML = `
        <span style="margin-right: 10px;">${type === 'success' ? '✅' : '❌'}</span>
        ${message}
    `;
    
    document.body.appendChild(notification);
    
    // Remove after 3 seconds
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transform = 'translateX(100%)';
        notification.style.transition = 'all 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Make functions globally available for backward compatibility
window.showLoading = showLoading;
window.showSection = showSection;
window.toggleSidebar = toggleSidebar;
window.toggleFullscreen = toggleFullscreen;
window.loadDashboard = loadDashboard;
window.updateStats = updateStats;
window.updateAccountSelectors = updateAccountSelectors;
window.switchAccount = switchAccount;
window.switchAccountForHierarchy = switchAccountForHierarchy;
window.switchAccountForTasks = switchAccountForTasks;
window.loadTasks = loadTasks;
window.filterTasks = filterTasks;
window.clearTasksFilters = clearTasksFilters;
window.refreshData = simpleCacheRefresh;  // Use simple cache refresh instead of full sync
window.refreshHierarchy = refreshHierarchy;
window.loadHierarchy = loadHierarchy;
window.initSettings = initSettings;
window.openSettings = openSettings;
window.closeSettings = closeSettings;
window.toggleAutoRefresh = toggleAutoRefresh;
window.updateRefreshInterval = updateRefreshInterval;
window.updateDefaultView = updateDefaultView;
window.toggleHideDeleted = toggleHideDeleted;
window.setupKeyboardShortcuts = setupKeyboardShortcuts;
window.toggleChartFilters = toggleChartFilters;
window.applyChartFilters = applyChartFilters;
window.clearChartFilters = clearChartFilters;
window.clearNodeFilters = clearNodeFilters;
window.completeTask = completeTask;
window.updateTaskCompletedState = updateTaskCompletedState;
window.toggleDarkMode = stateManager.toggleDarkMode;
window.showNotification = showNotification;
window.parseUrlParams = parseUrlParams;
window.applyUrlParams = applyUrlParams;
window.updateTasksCountDisplay = updateTasksCountDisplay;
window.getCurrentSectionFromPath = getCurrentSectionFromPath;
window.updateNavActiveState = updateNavActiveState;
window.startAdvancedSync = startAdvancedSync;
window.updateSyncProgressUI = updateSyncProgressUI;
window.stopSyncProgressUI = stopSyncProgressUI;
window.refreshWithAdvancedSync = refreshWithAdvancedSync;
window.simpleCacheRefresh = simpleCacheRefresh;
window.toggleRefreshDropdown = toggleRefreshDropdown;
window.syncAndRefresh = syncAndRefresh;
window.setupRefreshDropdown = setupRefreshDropdown;
window.getListsWithCounts = getListsWithCounts;
window.getTagsWithCounts = getTagsWithCounts;
window.updateFilteredMultiselect = updateFilteredMultiselect;

// Export for use in other modules
export default {
    initDashboard,
    loadDashboard,
    updateStats,
    showSection,
    toggleSidebar,
    toggleFullscreen,
    switchAccount,
    loadTasks,
    filterTasks,
    loadHierarchy,
    simpleCacheRefresh
};

// Initialize the dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    initDashboard();
});
