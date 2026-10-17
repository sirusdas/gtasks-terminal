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
    debounce,
    getDateStatus,
    getDateStatusBadge,
    getPriorityClass,
    getPriorityIcon,
    getStatusClass,
    getAllTags,
    isValidTag,
    getTaskDate,
    getDefaultDateRange,
    splitNotesAndTags,
    combineNotesAndTags,
    extractSpacesFromText
} from './utils.js?v=45';
import { createTaskCard, renderTasksGrid } from './task-card.js?v=45';
import { createMultiselect, getUniqueLists, getUniqueTags, getListsWithCounts, getTagsWithCounts, getStatusWithCounts, getFilteredTagsByLists, getFilteredListsByTags, getFilteredTasksBySearchAndDate, getFilteredListsByTagsAndCriteria, getFilteredTagsByListsAndCriteria } from './multiselect.js';
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

// Sync state variables & concurrency mutex
let isSyncing = false;
let isCacheRefreshInProgress = false;
let isRemoteSyncInProgress = false;
let syncProgress = { percentage: 0, message: '', status: 'idle' };
let syncPollInterval = null;

// Browser Tabs state variables
let browserTabs = [];
let activeBrowserTabId = null;

// Space filter state variables
export let activeSpaceFilter = null;
export let activeSubspaceFilter = null;

// Export for backward compatibility
export function getDashboardData() {
    return dashboardData;
}

export function setDashboardData(data) {
    dashboardData = data;
    window.dashboardData = data;  // Also set on window for other modules to access
    window.allGoogleLists = data.all_google_lists || [];
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
    const basePath = window.GTASKS_BASE_PATH || '';
    const path = window.location.pathname;
    
    // Remove base path from path for comparison
    const relativePath = path.replace(basePath, '') || '/';
    
    if (relativePath === '/hierarchy' || relativePath.startsWith('/hierarchy')) {
        return 'hierarchy';
    } else if (relativePath === '/tasks' || relativePath.startsWith('/tasks')) {
        return 'tasks';
    } else if (relativePath === '/reports' || relativePath.startsWith('/reports')) {
        return 'reports';
    } else if (relativePath === '/dashboard' || relativePath === '/') {
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
        const basePath = window.GTASKS_BASE_PATH || '';
        const newUrl = `${basePath}/${section === 'dashboard' ? '' : section}`;
        window.history.replaceState({}, '', newUrl);
    }
    
    stateManager.setCurrentSection(section);
    
    if (section === 'hierarchy') {
        // Add a small delay to allow the browser to calculate layout dimensions
        setTimeout(() => {
            loadHierarchy();
        }, 50);
    } else if (section === 'tasks') {
        if (dashboardData && dashboardData.tasks) {
            filterTasks();
        }
    } else if (section === 'reports') {
        if (window.initReportsView) {
            window.initReportsView();
        }
    }
}

/**
 * Toggle sidebar
 */
export function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const backdrop = document.getElementById('sidebar-backdrop');
    const mainContent = document.getElementById('main-content');
    
    if (window.innerWidth <= 768) {
        if (!sidebar) return;
        const isOpen = sidebar.classList.contains('open');
        if (isOpen) {
            sidebar.classList.remove('open');
            if (backdrop) backdrop.classList.remove('active');
        } else {
            sidebar.classList.add('open');
            if (backdrop) backdrop.classList.add('active');
        }
    } else {
        if (sidebar) sidebar.classList.toggle('collapsed');
        if (mainContent) mainContent.classList.toggle('expanded');
    }
}

/**
 * Close sidebar (mobile)
 */
export function closeSidebar() {
    const sidebar = document.getElementById('sidebar');
    const backdrop = document.getElementById('sidebar-backdrop');
    if (sidebar) sidebar.classList.remove('open');
    if (backdrop) backdrop.classList.remove('active');
}

/**
 * Close sidebar on mobile when navigating
 */
export function closeSidebarOnMobile() {
    if (window.innerWidth <= 768) {
        closeSidebar();
    }
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
    if (isSyncing || isCacheRefreshInProgress || isRemoteSyncInProgress) {
        console.log('[Sync] Sync already in progress, ignoring duplicate request');
        showNotification('Sync or refresh is already in progress, please wait...', 'warning');
        return;
    }

    isSyncing = true;
    syncProgress = { percentage: 0, message: 'Starting sync...', status: 'running' };

    // Disable all refresh buttons and animate spinner icon
    document.querySelectorAll('.header-refresh-btn').forEach(refreshBtn => {
        refreshBtn.disabled = true;
        refreshBtn.classList.add('disabled');
        const icon = refreshBtn.querySelector('i');
        if (icon) icon.classList.add('fa-spin');
    });

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

    // Re-enable all refresh buttons and remove spinner animation
    document.querySelectorAll('.header-refresh-btn').forEach(refreshBtn => {
        refreshBtn.disabled = false;
        refreshBtn.classList.remove('disabled');
        const icon = refreshBtn.querySelector('i');
        if (icon) icon.classList.remove('fa-spin');
    });
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
    if (isCacheRefreshInProgress || isSyncing || isRemoteSyncInProgress) {
        console.log('[Dashboard] Refresh/sync already running, ignoring duplicate request');
        showNotification('Sync or refresh is already in progress, please wait...', 'warning');
        return;
    }

    isCacheRefreshInProgress = true;
    console.log('[Dashboard] Simple cache refresh...');
    const refreshBtns = document.querySelectorAll('.header-refresh-btn');
    refreshBtns.forEach(btn => {
        btn.disabled = true;
        btn.classList.add('disabled');
        const icon = btn.querySelector('i');
        if (icon) icon.classList.add('fa-spin');
    });

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
            const currentSec = (typeof stateManager.getCurrentSection === 'function' ? stateManager.getCurrentSection() : stateManager.get('currentSection')) || getCurrentSectionFromPath();
            if (currentSec === 'reports' && typeof window.generateSelectedReport === 'function') {
                window.generateSelectedReport();
            }
            showNotification('Dashboard refreshed! ✅', 'success');
        } else {
            console.error('[Dashboard] Cache refresh failed:', data.message);
            showNotification(data.message || 'Refresh failed', 'error');
        }
    } catch (error) {
        console.error('[Dashboard] Error during cache refresh:', error);
        showNotification('Error refreshing dashboard', 'error');
    } finally {
        isCacheRefreshInProgress = false;
        refreshBtns.forEach(btn => {
            btn.disabled = false;
            btn.classList.remove('disabled');
            const icon = btn.querySelector('i');
            if (icon) icon.classList.remove('fa-spin');
        });
    }
}

// ========== Refresh Dropdown Functions ==========

/**
 * Close all active refresh dropdown menus across the page
 */
export function closeAllRefreshDropdowns() {
    document.querySelectorAll('.refresh-dropdown-menu.active').forEach(menu => {
        menu.classList.remove('active');
    });
}

/**
 * Toggle the refresh dropdown menu for the clicked element or current visible view
 */
export function toggleRefreshDropdown(event) {
    if (event) {
        if (typeof event.stopPropagation === 'function') {
            event.stopPropagation();
        }
        const toggleBtn = event.currentTarget || (event.target ? event.target.closest('.refresh-dropdown-toggle') : null);
        const container = toggleBtn ? toggleBtn.closest('.refresh-dropdown') : null;
        if (container) {
            const menu = container.querySelector('.refresh-dropdown-menu');
            if (menu) {
                const isCurrentlyActive = menu.classList.contains('active');
                closeAllRefreshDropdowns();
                if (!isCurrentlyActive) {
                    menu.classList.add('active');
                }
                return;
            }
        }
    }
    // Fallback if called without event or button context
    const visibleSection = document.querySelector('.section:not([style*="display: none"])');
    const targetMenu = (visibleSection && visibleSection.querySelector('.refresh-dropdown-menu')) || document.querySelector('.refresh-dropdown-menu');
    if (targetMenu) {
        const isCurrentlyActive = targetMenu.classList.contains('active');
        closeAllRefreshDropdowns();
        if (!isCurrentlyActive) {
            targetMenu.classList.add('active');
        }
    }
}

/**
 * Sync data and refresh cache
 * This is called when "Sync Data" option is selected
 */
export async function syncAndRefresh() {
    if (isSyncing || isCacheRefreshInProgress || isRemoteSyncInProgress) {
        console.log('[Dashboard] Sync/refresh already running, ignoring duplicate request');
        showNotification('Sync or refresh is already in progress, please wait...', 'warning');
        return;
    }
    console.log('[Dashboard] Sync and refresh...');
    // Start advanced sync - this will automatically refresh cache when complete
    await startAdvancedSync();
}

/**
 * Run gtasks remote sync command in background thread
 * This is called when "Sync External DB" option is selected
 */
export async function syncRemoteDb() {
    if (isRemoteSyncInProgress || isSyncing || isCacheRefreshInProgress) {
        console.log('[Dashboard] Sync already in progress, ignoring duplicate request');
        showNotification('Sync is already in progress, please wait...', 'warning');
        return;
    }

    isRemoteSyncInProgress = true;
    console.log('[Dashboard] Sync External DB - starting background command...');
    const refreshBtns = document.querySelectorAll('.header-refresh-btn');
    refreshBtns.forEach(btn => {
        btn.disabled = true;
        btn.classList.add('disabled');
        const icon = btn.querySelector('i');
        if (icon) icon.classList.add('fa-spin');
    });

    try {
        const basePath = window.GTASKS_BASE_PATH || '';
        const response = await fetch(`${basePath}/api/remote/sync-command`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const data = await response.json();

        if (data.success) {
            console.log('[Dashboard] Remote sync command started:', data.message);
            showNotification(data.message || 'Remote sync started in background... ℹ️', 'info');
        } else {
            console.error('[Dashboard] Failed to start remote sync:', data.message);
            showNotification(data.message || 'Failed to start remote sync', 'error');
        }
    } catch (error) {
        console.error('[Dashboard] Error starting remote sync:', error);
        showNotification('Error starting remote sync', 'error');
    } finally {
        setTimeout(() => {
            isRemoteSyncInProgress = false;
            refreshBtns.forEach(btn => {
                btn.disabled = false;
                btn.classList.remove('disabled');
                const icon = btn.querySelector('i');
                if (icon) icon.classList.remove('fa-spin');
            });
        }, 1500);
    }
}

/**
 * Close refresh dropdown when clicking outside
 */
export function setupRefreshDropdown() {
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.refresh-dropdown')) {
            closeAllRefreshDropdowns();
        }
        if (!e.target.closest('.browser-tab-actions')) {
            closeNewTabMenu();
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
// ========== Browser-Style Live Multi-Tabs ==========

const BROWSER_TABS_STORAGE_KEY = 'gtasks_browser_tabs_v2';
const BROWSER_ACTIVE_TAB_KEY = 'gtasks_active_tab_id_v2';

export function getDefaultBrowserTabs() {
    const defaultDates = getDefaultDateRange(31);
    const todayStr = new Date().toISOString().slice(0, 10);
    return [
        {
            id: 'tab_all',
            title: 'All Tasks',
            icon: 'fas fa-inbox',
            filters: {
                search: '',
                status: ['pending', 'in_progress'],
                priority: '',
                list: [],
                hideLists: [],
                hideRecurring: [],
                spaces: [],
                tags: [],
                space: null,
                subspace: null,
                dateField: 'modified_at',
                dateStart: defaultDates.start,
                dateEnd: defaultDates.end,
                sortField: 'modified_at',
                sortOrder: 'desc'
            },
            viewMode: currentTaskViewMode || 'compact'
        },
        {
            id: 'tab_today',
            title: 'Due Today',
            icon: 'fas fa-calendar-day',
            filters: {
                search: '',
                status: ['pending', 'in_progress'],
                priority: '',
                list: [],
                hideLists: [],
                hideRecurring: [],
                spaces: [],
                tags: [],
                space: null,
                subspace: null,
                dateField: 'due',
                dateStart: todayStr,
                dateEnd: todayStr,
                sortField: 'due',
                sortOrder: 'asc'
            },
            viewMode: currentTaskViewMode || 'compact'
        },
        {
            id: 'tab_high_prio',
            title: 'High Priority',
            icon: 'fas fa-fire',
            filters: {
                search: '',
                status: ['pending', 'in_progress'],
                priority: 'high',
                list: [],
                hideLists: [],
                hideRecurring: [],
                spaces: [],
                tags: [],
                space: null,
                subspace: null,
                dateField: 'modified_at',
                dateStart: defaultDates.start,
                dateEnd: defaultDates.end,
                sortField: 'priority',
                sortOrder: 'desc'
            },
            viewMode: currentTaskViewMode || 'compact'
        },
        {
            id: 'tab_work',
            title: 'Work Space',
            icon: 'fas fa-briefcase',
            filters: {
                search: '',
                status: ['pending', 'in_progress'],
                priority: '',
                list: [],
                hideLists: [],
                hideRecurring: [],
                spaces: ['Work'],
                tags: [],
                space: 'Work',
                subspace: null,
                dateField: 'modified_at',
                dateStart: defaultDates.start,
                dateEnd: defaultDates.end,
                sortField: 'modified_at',
                sortOrder: 'desc'
            },
            viewMode: currentTaskViewMode || 'compact'
        }
    ];
}

export function getActiveBrowserTab() {
    if (!browserTabs || browserTabs.length === 0) return null;
    let tab = browserTabs.find(t => t.id === activeBrowserTabId);
    if (!tab) {
        tab = browserTabs[0];
        activeBrowserTabId = tab.id;
    }
    return tab;
}

export function saveBrowserTabs() {
    try {
        localStorage.setItem(BROWSER_TABS_STORAGE_KEY, JSON.stringify(browserTabs));
        if (activeBrowserTabId) {
            localStorage.setItem(BROWSER_ACTIVE_TAB_KEY, activeBrowserTabId);
        }
    } catch (e) {
        console.error('[BrowserTabs] Error saving tabs:', e);
    }
}

export function loadBrowserTabs() {
    try {
        const saved = localStorage.getItem(BROWSER_TABS_STORAGE_KEY);
        if (saved) {
            const parsed = JSON.parse(saved);
            if (Array.isArray(parsed) && parsed.length > 0) {
                browserTabs = parsed;
                const savedActiveId = localStorage.getItem(BROWSER_ACTIVE_TAB_KEY);
                if (savedActiveId && browserTabs.some(t => t.id === savedActiveId)) {
                    activeBrowserTabId = savedActiveId;
                } else {
                    activeBrowserTabId = browserTabs[0].id;
                }
                return;
            }
        }
    } catch (e) {
        console.error('[BrowserTabs] Error loading tabs from storage:', e);
    }

    // Default migration if prior filter state existed
    const defaultTabs = getDefaultBrowserTabs();
    try {
        const oldState = localStorage.getItem('gtasks_filter_state');
        if (oldState) {
            const parsedOld = JSON.parse(oldState);
            if (parsedOld && typeof parsedOld === 'object') {
                defaultTabs[0].filters = { ...defaultTabs[0].filters, ...parsedOld };
            }
        }
    } catch (e) {}

    browserTabs = defaultTabs;
    activeBrowserTabId = browserTabs[0].id;
    saveBrowserTabs();
}

export function initBrowserTabs() {
    loadBrowserTabs();
    renderBrowserTabs();
    updateBrowserTabBadges();
    initSidebarContextMenu();
}

export function renderBrowserTabs() {
    const track = document.getElementById('browser-tabs-track');
    if (!track) return;

    track.innerHTML = '';
    const canClose = browserTabs.length > 1;

    browserTabs.forEach(tab => {
        const isActive = tab.id === activeBrowserTabId;
        const chip = document.createElement('div');
        chip.className = `browser-tab-chip ${isActive ? 'active' : ''}`;
        chip.setAttribute('data-tab-id', tab.id);
        chip.title = `${tab.title} (Click to switch, double-click to rename)`;

        chip.onclick = (e) => {
            if (e.target.closest('.browser-tab-chip-actions') || e.target.closest('.browser-tab-rename-input')) return;
            switchBrowserTab(tab.id);
        };

        const iconSpan = document.createElement('span');
        iconSpan.className = 'browser-tab-icon';
        iconSpan.innerHTML = `<i class="${tab.icon || 'fas fa-tasks'}"></i>`;

        const titleSpan = document.createElement('span');
        titleSpan.className = 'browser-tab-title';
        titleSpan.textContent = tab.title;
        titleSpan.ondblclick = (e) => {
            e.stopPropagation();
            startTabRename(tab.id, e);
        };

        const badgeSpan = document.createElement('span');
        badgeSpan.className = 'browser-tab-badge';
        badgeSpan.id = `tab-badge-${tab.id}`;
        badgeSpan.textContent = '...';

        const actionsDiv = document.createElement('div');
        actionsDiv.className = 'browser-tab-chip-actions';
        actionsDiv.onclick = (e) => e.stopPropagation();

        actionsDiv.innerHTML = `
            <button type="button" class="browser-tab-action-btn edit" onclick="window.startTabRename('${tab.id}', event)" title="Rename tab">
                <i class="fas fa-pen"></i>
            </button>
            <button type="button" class="browser-tab-action-btn duplicate" onclick="window.duplicateBrowserTab('${tab.id}', event)" title="Duplicate tab">
                <i class="fas fa-copy"></i>
            </button>
            ${canClose ? `
            <button type="button" class="browser-tab-action-btn close" onclick="window.closeBrowserTab('${tab.id}', event)" title="Close tab">
                <i class="fas fa-times"></i>
            </button>` : ''}
        `;

        chip.appendChild(iconSpan);
        chip.appendChild(titleSpan);

        // Account badge if tab is scoped to a specific account
        if (tab.filters?.account && tab.filters.account !== 'all' && tab.filters.account !== '') {
            const accBadge = document.createElement('span');
            accBadge.className = 'browser-tab-account-badge';
            accBadge.textContent = tab.filters.account;
            accBadge.title = `Account: ${tab.filters.account}`;
            chip.appendChild(accBadge);
        }

        chip.appendChild(badgeSpan);
        chip.appendChild(actionsDiv);

        track.appendChild(chip);

        if (isActive) {
            setTimeout(() => {
                chip.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'nearest' });
            }, 30);
        }
    });

    checkTabTrackScroll();
}

export function updateBrowserTabBadges() {
    if (!browserTabs || browserTabs.length === 0) return;
    const tasks = filterOutDeletedTasks(dashboardData.tasks || []);
    browserTabs.forEach(tab => {
        const badgeEl = document.getElementById(`tab-badge-${tab.id}`);
        if (!badgeEl) return;
        const matchingTasks = filterTasksByCriteria(tasks, tab.filters || {});
        badgeEl.textContent = matchingTasks.length;
        if (tab.filters?.priority === 'high' && matchingTasks.length > 0) {
            badgeEl.classList.add('has-urgent');
        } else {
            badgeEl.classList.remove('has-urgent');
        }
    });
}

export function switchBrowserTab(tabId) {
    if (activeBrowserTabId === tabId) return;

    // Save current active tab filter values before switching
    saveFilterState();

    activeBrowserTabId = tabId;
    localStorage.setItem(BROWSER_ACTIVE_TAB_KEY, tabId);

    const newTab = getActiveBrowserTab();
    if (!newTab) return;

    const f = newTab.filters || {};

    // 1. Search filter input
    const searchEl = document.getElementById('task-search-filter');
    if (searchEl) searchEl.value = f.search || '';

    // 2. Priority filter select
    const prioEl = document.getElementById('task-priority-filter');
    if (prioEl) prioEl.value = f.priority || '';

    // 3. Date fields
    const dateFieldEl = document.getElementById('task-date-field');
    if (dateFieldEl) dateFieldEl.value = f.dateField || 'modified_at';
    const dateStartEl = document.getElementById('task-date-start');
    if (dateStartEl) dateStartEl.value = f.dateStart || '';
    const dateEndEl = document.getElementById('task-date-end');
    if (dateEndEl) dateEndEl.value = f.dateEnd || '';

    // 4. Sort fields
    const sortFieldEl = document.getElementById('task-sort-field');
    if (sortFieldEl) sortFieldEl.value = f.sortField || 'modified_at';
    const sortOrderEl = document.getElementById('task-sort-order');
    if (sortOrderEl) sortOrderEl.value = f.sortOrder || 'desc';

    // 5. Space and subspace filters
    activeSpaceFilter = f.space || null;
    activeSubspaceFilter = f.subspace || null;

    // 6. Multiselects
    if (statusMultiselect) statusMultiselect.setSelectedValues(f.status || ['pending', 'in_progress']);
    if (listMultiselect) listMultiselect.setSelectedValues(f.list || []);
    if (hideListsMultiselect) hideListsMultiselect.setSelectedValues(f.hideLists || []);
    if (hideRecurringMultiselect) hideRecurringMultiselect.setSelectedValues(f.hideRecurring || []);
    if (spacesMultiselect) spacesMultiselect.setSelectedValues(f.spaces || []);
    if (tagsMultiselect) tagsMultiselect.setSelectedValues(f.tags || []);

    // 7. View Mode
    if (newTab.viewMode && newTab.viewMode !== currentTaskViewMode) {
        currentTaskViewMode = newTab.viewMode;
        localStorage.setItem('gtasks_task_view_mode', newTab.viewMode);
        const compactBtn = document.getElementById('view-mode-compact');
        const cardBtn = document.getElementById('view-mode-card');
        if (compactBtn && cardBtn) {
            compactBtn.classList.toggle('active', newTab.viewMode === 'compact');
            cardBtn.classList.toggle('active', newTab.viewMode === 'card');
        }
        const container = document.getElementById('tasks-grid');
        if (container) {
            container.classList.toggle('compact', newTab.viewMode === 'compact');
        }
    }

    // 7b. Account sync for per-tab account isolation
    if (f.account && f.account !== 'all' && f.account !== '') {
        const accSelect = document.getElementById('tasks-account-selector');
        if (accSelect && accSelect.value !== f.account) {
            accSelect.value = f.account;
            if (dashboardData.current_account && dashboardData.current_account !== f.account) {
                switchAccountForTasks(f.account);
                return;
            }
        }
    }

    // 7c. Update sidebar and filter options for this tab's account smoothly & instantly
    updateSidebarAndFiltersForTab(newTab);

    // 8. Re-render tab bar active state
    renderBrowserTabs();

    // 9. Filter and render tasks for this tab
    filterTasks();
}

/**
 * Update sidebar lists, spaces, and tags according to tab's account
 */
export function updateSidebarAndFiltersForTab(tab) {
    if (!tab) return;
    const tabAccount = tab.filters?.account;
    const allTasks = filterOutDeletedTasks(dashboardData.tasks || []);
    let scopedTasks = allTasks;
    if (tabAccount && tabAccount !== 'all' && tabAccount !== '') {
        const accLower = String(tabAccount).toLowerCase();
        scopedTasks = allTasks.filter(t => t.account && String(t.account).toLowerCase() === accLower);
    }
    // Instantly update sidebar counts, lists, spaces, tags for this tab's account without network lag
    populateSidebarTasksSubmenu(scopedTasks);
}

/**
 * Open a sidebar item (space, subspace, list, tag, or all) directly in a new browser tab
 */
export function openSidebarItemInNewTab(type, value, space = null) {
    const id = 'tab_' + Date.now();
    const activeTab = getActiveBrowserTab();
    const currentAccount = activeTab?.filters?.account || '';

    let title = value || 'All Tasks';
    let icon = 'fas fa-tasks';
    const filters = getDefaultFilterState();
    filters.account = currentAccount;

    if (type === 'list') {
        title = value;
        icon = 'fas fa-list-ul';
        filters.list = [value];
    } else if (type === 'space') {
        title = value;
        icon = 'fas fa-layer-group';
        filters.spaces = [value];
        filters.space = value;
    } else if (type === 'subspace') {
        title = `${space} › ${value}`;
        icon = 'fas fa-angle-right';
        filters.spaces = [space];
        filters.space = space;
        filters.subspace = value;
    } else if (type === 'tag') {
        title = '#' + value;
        icon = 'fas fa-tag';
        filters.tags = [value];
    }

    const tabData = {
        id,
        title,
        icon,
        filters,
        viewMode: currentTaskViewMode || 'compact'
    };

    browserTabs.push(tabData);
    saveBrowserTabs();
    renderBrowserTabs();
    switchBrowserTab(id);
    showNotification(`Opened "${title}" in new tab`, 'success');
}

/**
 * Right-click context menu on sidebar items to open in new tab
 */
export function initSidebarContextMenu() {
    const sidebar = document.getElementById('sidebar');
    if (!sidebar) return;

    let menu = document.getElementById('sidebar-context-menu');
    if (!menu) {
        menu = document.createElement('div');
        menu.id = 'sidebar-context-menu';
        menu.className = 'sidebar-context-menu';
        document.body.appendChild(menu);
    }

    // Dismiss on click outside or escape
    document.addEventListener('click', (e) => {
        if (!menu.contains(e.target)) {
            menu.style.display = 'none';
        }
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') menu.style.display = 'none';
    });

    sidebar.addEventListener('contextmenu', (e) => {
        const item = e.target.closest('.sidebar-subitem, .sidebar-item');
        if (!item) return;

        const type = item.getAttribute('data-type');
        const value = item.getAttribute('data-value');
        const space = item.getAttribute('data-space');

        // Only handle items that can be opened as a tab view (lists, spaces, subspaces, tags, or all tasks)
        const isTasksItem = item.id === 'sidebar-all-tasks' || item.getAttribute('onclick')?.includes('tasks') || type;
        if (!isTasksItem && !type) return;

        e.preventDefault();
        const displayTitle = value || 'All Tasks';

        let deleteHtml = '';
        if (type === 'space') {
            deleteHtml = `
                <div class="sidebar-context-item text-danger" id="sidebar-ctx-delete" style="color: #ef4444; border-top: 1px solid var(--border-color, #e2e8f0); margin-top: 4px; padding-top: 6px;">
                    <i class="fas fa-trash-alt text-danger"></i>
                    <span>Delete Space "${escapeHtml(value)}"</span>
                </div>
            `;
        } else if (type === 'subspace') {
            deleteHtml = `
                <div class="sidebar-context-item text-danger" id="sidebar-ctx-delete" style="color: #ef4444; border-top: 1px solid var(--border-color, #e2e8f0); margin-top: 4px; padding-top: 6px;">
                    <i class="fas fa-trash-alt text-danger"></i>
                    <span>Delete Sub-space "${escapeHtml(value)}"</span>
                </div>
            `;
        } else if (type === 'tag') {
            deleteHtml = `
                <div class="sidebar-context-item text-danger" id="sidebar-ctx-delete" style="color: #ef4444; border-top: 1px solid var(--border-color, #e2e8f0); margin-top: 4px; padding-top: 6px;">
                    <i class="fas fa-trash-alt text-danger"></i>
                    <span>Delete Tag "#${escapeHtml(value)}"</span>
                </div>
            `;
        }

        menu.innerHTML = `
            <div class="sidebar-context-item" id="sidebar-ctx-open-new-tab">
                <i class="fas fa-folder-plus text-blue"></i>
                <span>Open "${escapeHtml(displayTitle)}" in New Tab</span>
            </div>
            <div class="sidebar-context-item" id="sidebar-ctx-filter-current">
                <i class="fas fa-filter text-purple"></i>
                <span>Filter in Current View</span>
            </div>
            ${deleteHtml}
        `;

        const x = Math.min(e.clientX, window.innerWidth - 220);
        const y = Math.min(e.clientY, window.innerHeight - 150);
        menu.style.left = `${x}px`;
        menu.style.top = `${y}px`;
        menu.style.display = 'block';

        const openBtn = document.getElementById('sidebar-ctx-open-new-tab');
        if (openBtn) {
            openBtn.onclick = () => {
                menu.style.display = 'none';
                openSidebarItemInNewTab(type, value, space);
            };
        }

        const filterBtn = document.getElementById('sidebar-ctx-filter-current');
        if (filterBtn) {
            filterBtn.onclick = () => {
                menu.style.display = 'none';
                if (type && value) {
                    selectSidebarFilter(type, value, space);
                } else if (item.id === 'sidebar-all-tasks') {
                    resetAllFilters();
                }
            };
        }

        const deleteBtn = document.getElementById('sidebar-ctx-delete');
        if (deleteBtn) {
            deleteBtn.onclick = () => {
                menu.style.display = 'none';
                if (type === 'space') {
                    deleteSpaceFromDashboard(value);
                } else if (type === 'subspace') {
                    deleteSpaceFromDashboard(space, value);
                } else if (type === 'tag') {
                    deleteTagFromDashboard(value);
                }
            };
        }
    });
}

export function createBrowserTabPreset(preset, accountId = null) {
    const id = 'tab_' + Date.now();
    let tabData = {
        id,
        title: 'New Tab',
        icon: 'fas fa-tasks',
        filters: getDefaultFilterState(),
        viewMode: currentTaskViewMode || 'compact'
    };

    let targetAccount = accountId;
    if (!targetAccount) {
        const activeTab = getActiveBrowserTab();
        if (activeTab?.filters?.accounts && Array.isArray(activeTab.filters.accounts) && activeTab.filters.accounts.length > 0) {
            targetAccount = activeTab.filters.accounts;
        } else if (activeTab?.filters?.account && activeTab.filters.account !== 'all') {
            targetAccount = activeTab.filters.account;
        }
    }

    let accLabel = '';
    if (Array.isArray(targetAccount) && targetAccount.length > 0) {
        tabData.filters.accounts = targetAccount;
        tabData.filters.account = targetAccount.length === 1 ? targetAccount[0] : '';
        accLabel = targetAccount.map(id => {
            const accObj = (dashboardData.accounts || []).find(a => a.id === id);
            return accObj ? accObj.name : id;
        }).join(', ');
    } else if (typeof targetAccount === 'string' && targetAccount && targetAccount !== 'all') {
        tabData.filters.account = targetAccount;
        tabData.filters.accounts = [targetAccount];
        const accObj = (dashboardData.accounts || []).find(a => a.id === targetAccount);
        accLabel = accObj ? accObj.name : targetAccount;
    }

    if (preset === 'account') {
        if (!accLabel) {
            tabData.title = 'All Accounts';
            tabData.icon = 'fas fa-users';
            tabData.filters.account = '';
            tabData.filters.accounts = [];
        } else {
            tabData.title = accLabel;
            tabData.icon = 'fas fa-user-circle';
        }
    } else if (preset === 'all') {
        tabData.title = accLabel ? `${accLabel} - All Tasks` : 'All Tasks';
        tabData.icon = 'fas fa-inbox';
        tabData.filters.status = ['pending', 'completed'];
    } else if (preset === 'today') {
        tabData.title = accLabel ? `${accLabel} - Due Today` : 'Due Today';
        tabData.icon = 'fas fa-calendar-day';
        const todayStr = new Date().toISOString().slice(0, 10);
        tabData.filters.dateField = 'due';
        tabData.filters.dateStart = todayStr;
        tabData.filters.dateEnd = todayStr;
        tabData.filters.sortField = 'due';
        tabData.filters.sortOrder = 'asc';
    } else if (preset === 'high_priority') {
        tabData.title = accLabel ? `${accLabel} - High Priority` : 'High Priority';
        tabData.icon = 'fas fa-fire';
        tabData.filters.priority = 'high';
        tabData.filters.sortField = 'priority';
        tabData.filters.sortOrder = 'desc';
    } else if (preset === 'work') {
        tabData.title = accLabel ? `${accLabel} - Work Space` : 'Work Space';
        tabData.icon = 'fas fa-briefcase';
        tabData.filters.spaces = ['Work'];
        tabData.filters.space = 'Work';
    } else if (preset === 'completed') {
        tabData.title = accLabel ? `${accLabel} - Completed` : 'Completed';
        tabData.icon = 'fas fa-check-circle';
        tabData.filters.status = ['completed'];
    }

    browserTabs.push(tabData);
    saveBrowserTabs();
    renderBrowserTabs();
    switchBrowserTab(id);
    showNotification(`Opened tab "${tabData.title}"`, 'success');
}

export function promptCreateCustomBrowserTab() {
    const name = prompt('Enter a name for the new tab:', 'My Custom View');
    if (!name || !name.trim()) return;

    const id = 'tab_' + Date.now();
    const tabData = {
        id,
        title: name.trim(),
        icon: 'fas fa-folder',
        filters: getDefaultFilterState(),
        viewMode: currentTaskViewMode || 'compact'
    };

    browserTabs.push(tabData);
    saveBrowserTabs();
    renderBrowserTabs();
    switchBrowserTab(id);
    showNotification(`Created tab "${tabData.title}"`, 'success');
}

export function closeBrowserTab(tabId, event) {
    if (event) event.stopPropagation();
    if (browserTabs.length <= 1) {
        showNotification('Cannot close the only tab', 'warning');
        return;
    }

    const tabIndex = browserTabs.findIndex(t => t.id === tabId);
    if (tabIndex === -1) return;

    const wasActive = activeBrowserTabId === tabId;
    browserTabs.splice(tabIndex, 1);

    if (wasActive) {
        const nextIndex = Math.min(tabIndex, browserTabs.length - 1);
        activeBrowserTabId = browserTabs[nextIndex].id;
        localStorage.setItem(BROWSER_ACTIVE_TAB_KEY, activeBrowserTabId);
    }

    saveBrowserTabs();
    renderBrowserTabs();
    if (wasActive) {
        const activeTab = getActiveBrowserTab();
        if (activeTab) {
            switchBrowserTab(activeTab.id);
        }
    }
}

export function startTabRename(tabId, event) {
    if (event) event.stopPropagation();
    const chip = document.querySelector(`.browser-tab-chip[data-tab-id="${tabId}"]`);
    if (!chip) return;
    const titleSpan = chip.querySelector('.browser-tab-title');
    if (!titleSpan) return;

    const currentTitle = titleSpan.textContent;
    const input = document.createElement('input');
    input.type = 'text';
    input.className = 'browser-tab-rename-input';
    input.value = currentTitle;

    let finished = false;
    const finish = () => {
        if (finished) return;
        finished = true;
        const newTitle = input.value.trim() || currentTitle;
        finishTabRename(tabId, newTitle);
    };

    input.onkeydown = (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            finish();
        } else if (e.key === 'Escape') {
            e.preventDefault();
            finished = true;
            renderBrowserTabs();
        }
    };

    input.onblur = finish;

    titleSpan.replaceWith(input);
    input.focus();
    input.select();
}

export function finishTabRename(tabId, newTitle) {
    const tab = browserTabs.find(t => t.id === tabId);
    if (tab && newTitle) {
        tab.title = newTitle;
        saveBrowserTabs();
    }
    renderBrowserTabs();
}

export function duplicateBrowserTab(tabId, event) {
    if (event) event.stopPropagation();
    const tabIndex = browserTabs.findIndex(t => t.id === tabId);
    if (tabIndex === -1) return;

    const sourceTab = browserTabs[tabIndex];
    const newId = 'tab_' + Date.now();
    const clonedTab = {
        id: newId,
        title: `${sourceTab.title} (Copy)`,
        icon: sourceTab.icon || 'fas fa-tasks',
        filters: JSON.parse(JSON.stringify(sourceTab.filters || {})),
        viewMode: sourceTab.viewMode || 'compact'
    };

    browserTabs.splice(tabIndex + 1, 0, clonedTab);
    saveBrowserTabs();
    renderBrowserTabs();
    switchBrowserTab(newId);
    showNotification(`Duplicated tab "${clonedTab.title}"`, 'info');
}

export function scrollBrowserTabs(offset) {
    const track = document.getElementById('browser-tabs-track');
    if (track) {
        track.scrollBy({ left: offset, behavior: 'smooth' });
        setTimeout(checkTabTrackScroll, 200);
    }
}

export function checkTabTrackScroll() {
    const track = document.getElementById('browser-tabs-track');
    const leftBtn = document.getElementById('browser-tabs-scroll-left');
    const rightBtn = document.getElementById('browser-tabs-scroll-right');
    if (!track || !leftBtn || !rightBtn) return;
    const hasOverflow = track.scrollWidth > track.clientWidth + 2;
    leftBtn.style.display = (hasOverflow && track.scrollLeft > 10) ? 'inline-flex' : 'none';
    rightBtn.style.display = (hasOverflow && track.scrollLeft < (track.scrollWidth - track.clientWidth - 10)) ? 'inline-flex' : 'none';
}

export function populateBrowserTabAccountsMenu() {
    const container = document.getElementById('browser-tab-accounts-section');
    if (!container) return;
    const accounts = dashboardData.accounts || [];
    if (accounts.length === 0) {
        container.innerHTML = '';
        return;
    }

    container.innerHTML = `
        <div class="browser-tab-menu-header">Accounts</div>
        <button type="button" class="browser-tab-menu-item" onclick="createBrowserTabPreset('account', 'all'); closeNewTabMenu();">
            <i class="fas fa-users text-blue"></i>
            <div>
                <div class="menu-item-title">All Accounts</div>
                <div class="menu-item-sub">View tasks across all accounts</div>
            </div>
        </button>
        ${accounts.map(acc => `
            <button type="button" class="browser-tab-menu-item" onclick="createBrowserTabPreset('account', '${acc.id}'); closeNewTabMenu();">
                <i class="fas fa-user-circle text-teal"></i>
                <div>
                    <div class="menu-item-title">${acc.name}</div>
                    <div class="menu-item-sub">Account: ${acc.id}</div>
                </div>
            </button>
        `).join('')}
    `;
}

export function toggleNewTabMenu(event) {
    if (event) event.stopPropagation();
    const menu = document.getElementById('browser-new-tab-dropdown');
    if (!menu) return;
    const isHidden = menu.style.display === 'none';
    if (isHidden) {
        populateBrowserTabAccountsMenu();
        menu.style.display = 'flex';
    } else {
        menu.style.display = 'none';
    }
}

export function closeNewTabMenu() {
    const menu = document.getElementById('browser-new-tab-dropdown');
    if (menu) menu.style.display = 'none';
}

/**
 * Get default filter configuration
 * Default: past 31 days (modified date first, then created date), status: pending & in_progress, sorted by modified date desc
 */
export function getDefaultFilterState() {
    const defaultDates = getDefaultDateRange(31);
    return {
        search: '',
        status: ['pending', 'in_progress'],
        priority: '',
        list: [],
        hideLists: [],
        hideRecurring: [],
        spaces: [],
        tags: [],
        account: '',
        space: null,
        subspace: null,
        dateField: 'modified_at',
        dateStart: defaultDates.start,
        dateEnd: defaultDates.end,
        sortField: 'modified_at',
        sortOrder: 'desc'
    };
}

export function saveFilterState() {
    try {
        const listValues = listMultiselect ? listMultiselect.getSelectedValues() : [];
        const hideListValues = hideListsMultiselect ? hideListsMultiselect.getSelectedValues() : [];
        const hideRecurringValues = hideRecurringMultiselect ? hideRecurringMultiselect.getSelectedValues() : [];
        const spacesValues = spacesMultiselect ? spacesMultiselect.getSelectedValues() : [];
        const tagValues = tagsMultiselect ? tagsMultiselect.getSelectedValues() : [];
        let statusValues = statusMultiselect ? statusMultiselect.getSelectedValues() : [];
        if (!statusMultiselect) {
            const el = document.getElementById('task-status-filter');
            if (el && el.value) {
                try {
                    const parsed = JSON.parse(el.value);
                    statusValues = Array.isArray(parsed) ? parsed : [el.value];
                } catch(e) {
                    statusValues = [el.value];
                }
            }
        }
        const activeTab = getActiveBrowserTab();
        const currentAccount = document.getElementById('tasks-account-selector')?.value || activeTab?.filters?.account || '';
        const state = {
            search: document.getElementById('task-search-filter')?.value || '',
            status: statusValues,
            priority: document.getElementById('task-priority-filter')?.value || '',
            list: listValues,
            hideLists: hideListValues,
            hideRecurring: hideRecurringValues,
            spaces: spacesValues,
            tags: tagValues,
            account: currentAccount,
            space: activeSpaceFilter,
            subspace: activeSubspaceFilter,
            dateField: document.getElementById('task-date-field')?.value || 'modified_at',
            dateStart: document.getElementById('task-date-start')?.value || '',
            dateEnd: document.getElementById('task-date-end')?.value || '',
            sortField: document.getElementById('task-sort-field')?.value || 'modified_at',
            sortOrder: document.getElementById('task-sort-order')?.value || 'desc'
        };

        // Sync with active browser tab
        if (activeTab) {
            activeTab.filters = { ...state };
            activeTab.viewMode = currentTaskViewMode;
            saveBrowserTabs();
        }

        localStorage.setItem('gtasks_filter_state', JSON.stringify(state));
        sessionStorage.setItem('gtasks_filter_state', JSON.stringify(state));
    } catch (e) {
        console.error('[Dashboard] Error saving filter state:', e);
    }
}

export function loadFilterState() {
    try {
        const activeTab = getActiveBrowserTab();
        if (activeTab && activeTab.filters) {
            return activeTab.filters;
        }
        const saved = localStorage.getItem('gtasks_filter_state') || sessionStorage.getItem('gtasks_filter_state');
        return saved ? JSON.parse(saved) : null;
    } catch (e) {
        console.error('[Dashboard] Error loading filter state:', e);
        return null;
    }
}

export function loadTasks() {
    const tasks = dashboardData.tasks || [];
    const filteredTasks = filterOutDeletedTasks(tasks);
    const container = document.getElementById('tasks-grid');
    if (!container) return;
    
    container.innerHTML = '';
    
    // Initialize task count display
    updateTasksCountDisplay(filteredTasks.length, tasks.length);

    // Initialize browser tabs
    initBrowserTabs();
    
    if (filteredTasks.length === 0) {
        container.innerHTML = '<p style="text-align: center; color: #6b7280;">No tasks found for this account.</p>';
        updateBrowserTabBadges();
        return;
    }
    
    // Initialize multiselect filters with available options (preserving current/saved selections)
    initMultiselectFilters(tasks);
    
    // Apply filters and render tasks according to preserved filter state
    filterTasks();
}

/**
 * Calculate recurring task counts per frequency type
 */
export function getRecurringWithCounts(tasks) {
    if (!tasks || !Array.isArray(tasks)) return [];
    const allRec = tasks.filter(t => t.is_recurring);
    const dailyCount = tasks.filter(t => t.is_recurring && (t.recurrence_type || '').toLowerCase() === 'daily').length;
    const weeklyCount = tasks.filter(t => t.is_recurring && (t.recurrence_type || '').toLowerCase() === 'weekly').length;
    const monthlyCount = tasks.filter(t => t.is_recurring && (t.recurrence_type || '').toLowerCase() === 'monthly').length;
    const yearlyCount = tasks.filter(t => t.is_recurring && (t.recurrence_type || '').toLowerCase() === 'yearly').length;
    const otherCount = tasks.filter(t => t.is_recurring && (t.recurrence_type || '').toLowerCase() === 'other').length;

    const options = [
        { value: 'all', label: 'All Recurring', count: allRec.length },
        { value: 'daily', label: 'Daily', count: dailyCount },
        { value: 'weekly', label: 'Weekly', count: weeklyCount },
        { value: 'monthly', label: 'Monthly', count: monthlyCount },
        { value: 'yearly', label: 'Yearly', count: yearlyCount },
        { value: 'other', label: 'Other Repeating', count: otherCount }
    ];
    return options.filter(opt => opt.count > 0 || opt.value === 'all');
}

/**
 * Initialize multiselect filters
 */
let listMultiselect = null;
let hideListsMultiselect = null;
let hideRecurringMultiselect = null;
let spacesMultiselect = null;
let tagsMultiselect = null;
let statusMultiselect = null;
let allTasks = []; // Store all tasks for filtering
let filterEventListenersAttached = false;

export function initMultiselectFilters(tasks) {
    allTasks = tasks;
    
    // Capture current selections if multiselects exist
    const currentListValues = listMultiselect ? listMultiselect.getSelectedValues() : null;
    const currentHideListValues = hideListsMultiselect ? hideListsMultiselect.getSelectedValues() : null;
    const currentHideRecurringValues = hideRecurringMultiselect ? hideRecurringMultiselect.getSelectedValues() : null;
    const currentSpaceValues = spacesMultiselect ? spacesMultiselect.getSelectedValues() : null;
    const currentTagValues = tagsMultiselect ? tagsMultiselect.getSelectedValues() : null;
    const currentStatusValues = statusMultiselect ? statusMultiselect.getSelectedValues() : null;
    
    // Load persisted state if available, or fall back to defaults
    const loadedState = loadFilterState();
    const defaults = getDefaultFilterState();
    const isFirstTime = (loadedState === null);
    const savedState = isFirstTime ? defaults : loadedState;

    const initialListValues = (currentListValues && currentListValues.length > 0) ? currentListValues : (savedState.list || []);
    const initialHideListValues = (currentHideListValues && currentHideListValues.length > 0) ? currentHideListValues : (savedState.hideLists || []);
    const initialHideRecurringValues = (currentHideRecurringValues && currentHideRecurringValues.length > 0) ? currentHideRecurringValues : (savedState.hideRecurring || []);
    const initialSpaceValues = (currentSpaceValues && currentSpaceValues.length > 0) ? currentSpaceValues : (savedState.spaces || []);
    const initialTagValues = (currentTagValues && currentTagValues.length > 0) ? currentTagValues : (savedState.tags || []);
    let initialStatusValues = (currentStatusValues && currentStatusValues.length > 0) ? currentStatusValues : (savedState.status !== undefined ? savedState.status : defaults.status);
    if (typeof initialStatusValues === 'string') {
        try { initialStatusValues = JSON.parse(initialStatusValues); } catch(e) { initialStatusValues = initialStatusValues ? [initialStatusValues] : defaults.status; }
    }
    if (!Array.isArray(initialStatusValues)) {
        initialStatusValues = defaults.status;
    }

    // Restore single filter controls from savedState if available
    if (savedState.search !== undefined) {
        const el = document.getElementById('task-search-filter');
        if (el) el.value = savedState.search;
    }
    if (savedState.priority !== undefined) {
        const el = document.getElementById('task-priority-filter');
        if (el) el.value = savedState.priority;
    }
    if (savedState.dateField !== undefined) {
        const el = document.getElementById('task-date-field');
        if (el) el.value = savedState.dateField;
    }
    if (savedState.dateStart !== undefined) {
        const el = document.getElementById('task-date-start');
        if (el) el.value = savedState.dateStart;
    }
    if (savedState.dateEnd !== undefined) {
        const el = document.getElementById('task-date-end');
        if (el) el.value = savedState.dateEnd;
    }
    const sortFieldEl = document.getElementById('task-sort-field');
    if (sortFieldEl) sortFieldEl.value = savedState.sortField || 'modified_at';

    const sortOrderEl = document.getElementById('task-sort-order');
    if (sortOrderEl) sortOrderEl.value = savedState.sortOrder || 'desc';

    const listsWithCounts = getListsWithCounts(tasks);
    const recurringWithCounts = getRecurringWithCounts(tasks);
    const spacesWithCounts = getSpacesWithCounts(tasks);
    const tagsWithCounts = getTagsWithCounts(tasks);
    const statusesWithCounts = getStatusWithCounts(tasks);

    // Initialize Status filter
    const statusContainer = document.getElementById('task-status-filter-container');
    if (statusContainer) {
        statusContainer.innerHTML = '';
        statusMultiselect = createMultiselect({
            id: 'task-status-filter',
            placeholder: 'Filter by Status...',
            options: statusesWithCounts,
            initialValues: initialStatusValues,
            onChange: (values) => {
                saveFilterState();
                updateFilteredMultiselect();
                filterTasks();
            },
            searchMinChars: 0,
            showCounts: true
        });
        statusContainer.appendChild(statusMultiselect);
    }
    
    // Initialize List filter
    const listContainer = document.getElementById('task-list-filter-container');
    if (listContainer) {
        listContainer.innerHTML = '';
        listMultiselect = createMultiselect({
            id: 'task-list-filter',
            placeholder: 'Filter by List...',
            options: listsWithCounts,
            initialValues: initialListValues,
            onChange: (values) => {
                saveFilterState();
                updateFilteredMultiselect();
                filterTasks();
            },
            searchMinChars: 0,
            showCounts: true
        });
        listContainer.appendChild(listMultiselect);
    }

    // Initialize Hide Lists filter
    const hideListContainer = document.getElementById('task-hide-lists-filter-container');
    if (hideListContainer) {
        hideListContainer.innerHTML = '';
        hideListsMultiselect = createMultiselect({
            id: 'task-hide-lists-filter',
            placeholder: 'Select lists to hide...',
            options: listsWithCounts,
            initialValues: initialHideListValues,
            onChange: (values) => {
                saveFilterState();
                updateFilteredMultiselect();
                filterTasks();
            },
            searchMinChars: 0,
            showCounts: true
        });
        hideListContainer.appendChild(hideListsMultiselect);
    }

    // Initialize Hide Recurring filter
    const hideRecurringContainer = document.getElementById('task-hide-recurring-filter-container');
    if (hideRecurringContainer) {
        hideRecurringContainer.innerHTML = '';
        hideRecurringMultiselect = createMultiselect({
            id: 'task-hide-recurring-filter',
            placeholder: 'Select recurring to hide...',
            options: recurringWithCounts,
            initialValues: initialHideRecurringValues,
            onChange: (values) => {
                saveFilterState();
                updateFilteredMultiselect();
                filterTasks();
            },
            searchMinChars: 0,
            showCounts: true
        });
        hideRecurringContainer.appendChild(hideRecurringMultiselect);
    }

    // Initialize Spaces & Sub-spaces hierarchical filter
    const spacesContainer = document.getElementById('task-spaces-filter-container');
    if (spacesContainer) {
        spacesContainer.innerHTML = '';
        spacesMultiselect = createMultiselect({
            id: 'task-spaces-filter',
            placeholder: 'Filter by Spaces & Sub-spaces...',
            options: spacesWithCounts,
            initialValues: initialSpaceValues,
            isSpaceHierarchy: true,
            allowAddNew: false,
            onChange: (values) => {
                saveFilterState();
                updateFilteredMultiselect();
                filterTasks();
            },
            searchMinChars: 0,
            showCounts: true
        });
        spacesContainer.appendChild(spacesMultiselect);
    }
    
    // Initialize Tags filter
    const tagsContainer = document.getElementById('task-tags-filter-container');
    if (tagsContainer) {
        tagsContainer.innerHTML = '';
        tagsMultiselect = createMultiselect({
            id: 'task-tags-filter',
            placeholder: 'Filter by Tags...',
            options: tagsWithCounts,
            initialValues: initialTagValues,
            onChange: (values) => {
                saveFilterState();
                updateFilteredMultiselect();
                filterTasks();
            },
            searchMinChars: 0,
            showCounts: true
        });
        tagsContainer.appendChild(tagsMultiselect);
    }

    // Save initial defaults if first time visit
    if (isFirstTime) {
        saveFilterState();
    }
    
    if (!filterEventListenersAttached) {
        setupFilterEventListeners();
        filterEventListenersAttached = true;
    }

    // Populate sidebar nested lists & tags
    populateSidebarTasksSubmenu(tasks);
}

/**
 * Setup event listeners for search, date, priority, and sort filters
 */
function setupFilterEventListeners() {
    const triggerFilterUpdate = () => {
        saveFilterState();
        updateFilteredMultiselect();
        filterTasks();
    };

    const searchFilter = document.getElementById('task-search-filter');
    if (searchFilter) {
        searchFilter.addEventListener('input', debounce(triggerFilterUpdate, 300));
    }
    
    ['task-date-field', 'task-date-start', 'task-date-end', 'task-priority-filter', 'task-sort-field', 'task-sort-order'].forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.addEventListener('change', triggerFilterUpdate);
        }
    });
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
export function updateFilteredMultiselect(searchText, dateStart, dateEnd, dateField) {
    const sText = searchText !== undefined ? searchText : (document.getElementById('task-search-filter')?.value || '');
    const dStart = dateStart !== undefined ? dateStart : (document.getElementById('task-date-start')?.value || '');
    const dEnd = dateEnd !== undefined ? dateEnd : (document.getElementById('task-date-end')?.value || '');
    const dField = dateField !== undefined ? dateField : (document.getElementById('task-date-field')?.value || 'modified_at');

    // Get current selections from both multiselects
    const selectedLists = listMultiselect ? listMultiselect.getSelectedValues() : [];
    const selectedTags = tagsMultiselect ? tagsMultiselect.getSelectedValues() : [];
    
    // Get filtered options based on selections and search/date criteria
    const filteredTags = getFilteredTagsByListsAndCriteria(allTasks, selectedLists, sText, dField, dStart, dEnd);
    const filteredLists = getFilteredListsByTagsAndCriteria(allTasks, selectedTags, sText, dField, dStart, dEnd);
    
    // Update multiselect options
    if (tagsMultiselect) {
        tagsMultiselect.setOptions(filteredTags);
    }
    
    if (listMultiselect) {
        listMultiselect.setOptions(filteredLists);
    }

    if (hideListsMultiselect) {
        hideListsMultiselect.setOptions(getListsWithCounts(allTasks));
    }

    if (hideRecurringMultiselect) {
        hideRecurringMultiselect.setOptions(getRecurringWithCounts(allTasks));
    }

    if (spacesMultiselect) {
        spacesMultiselect.setOptions(getSpacesWithCounts(allTasks));
    }
}

/* ========== Sidebar Tasks Navigation & Auto-Filtering ========== */

/**
 * Escape string for safe insertion into inline JS function calls
 * @param {string} str
 */
function escapeJsString(str) {
    if (!str) return '';
    return String(str)
        .replace(/\\/g, '\\\\')
        .replace(/'/g, "\\'")
        .replace(/"/g, '\\"');
}

/**
 * Get unique spaces and sub-spaces with counts from tasks
 * @param {Array} tasks
 * @returns {Array}
 */
export function getSpacesWithCounts(tasks) {
    const spacesMap = new Map();
    tasks.forEach(t => {
        if (t.is_deleted) return;
        const spaces = (t.spaces && Object.keys(t.spaces).length > 0)
            ? t.spaces
            : extractSpacesFromText(t.notes || t.description || '');
        if (!spaces || typeof spaces !== 'object') return;

        Object.entries(spaces).forEach(([spaceName, subs]) => {
            const spa = String(spaceName).trim();
            if (!spa) return;
            if (!spacesMap.has(spa)) {
                spacesMap.set(spa, { count: 0, subspaces: new Map() });
            }
            const spObj = spacesMap.get(spa);
            spObj.count++;

            (subs || []).forEach(sub => {
                const s = String(sub).trim();
                if (!s) return;
                spObj.subspaces.set(s, (spObj.subspaces.get(s) || 0) + 1);
            });
        });
    });

    return Array.from(spacesMap.entries())
        .map(([label, data]) => ({
            label,
            count: data.count,
            subspaces: Array.from(data.subspaces.entries())
                .map(([subLabel, subCount]) => ({ label: subLabel, count: subCount }))
                .sort((a, b) => a.label.localeCompare(b.label))
        }))
        .sort((a, b) => a.label.localeCompare(b.label));
}

/**
 * Convert spaces hierarchy to flat options array for multiselect
 * @param {Array} tasks
 * @returns {Array}
 */
export function getFlatSpacesAndSubspacesWithCounts(tasks) {
    const spacesHierarchy = getSpacesWithCounts(tasks);
    const options = [];
    spacesHierarchy.forEach(sp => {
        options.push({
            value: sp.label,
            label: sp.label,
            count: sp.count,
            type: 'space'
        });
        (sp.subspaces || []).forEach(sub => {
            options.push({
                value: `${sp.label}:${sub.label}`,
                label: `${sp.label} › ${sub.label}`,
                count: sub.count,
                type: 'subspace'
            });
        });
    });
    return options;
}

/**
 * Convert spaces hierarchy to unique space options for multiselect
 * @param {Array} tasks
 * @returns {Array}
 */
export function getUniqueSpacesWithCounts(tasks) {
    const spacesHierarchy = getSpacesWithCounts(tasks);
    return spacesHierarchy.map(sp => ({
        value: sp.label,
        label: sp.label,
        count: sp.count,
        type: 'space'
    }));
}

/**
 * Convert spaces hierarchy to unique sub-space options, optionally filtered by active parent spaces
 * @param {Array} tasks
 * @param {Array<string>|null} filterSpaces
 * @returns {Array}
 */
export function getUniqueSubspacesWithCounts(tasks, filterSpaces = null) {
    const spacesHierarchy = getSpacesWithCounts(tasks);
    const options = [];
    const filterSet = (filterSpaces && Array.isArray(filterSpaces) && filterSpaces.length > 0)
        ? new Set(filterSpaces.map(s => String(s).toLowerCase()))
        : null;

    spacesHierarchy.forEach(sp => {
        if (filterSet && !filterSet.has(sp.label.toLowerCase())) {
            return;
        }
        (sp.subspaces || []).forEach(sub => {
            options.push({
                value: `${sp.label}:${sub.label}`,
                label: `${sp.label} › ${sub.label}`,
                space: sp.label,
                sub: sub.label,
                count: sub.count,
                type: 'subspace'
            });
        });
    });
    return options;
}


/**
 * Convert spaces object to multiselect values array: ['spa:sub1', 'spa2']
 * @param {Object} spaces
 * @returns {Array<string>}
 */
export function spacesObjectToMultiselectValues(spaces) {
    if (!spaces || typeof spaces !== 'object') return [];
    const values = [];
    for (const [spaceName, subs] of Object.entries(spaces)) {
        const spa = String(spaceName).trim();
        if (!spa) continue;
        if (Array.isArray(subs) && subs.length > 0) {
            subs.forEach(sub => {
                const s = String(sub).trim();
                if (s) {
                    values.push(`${spa}:${s}`);
                }
            });
        } else {
            values.push(spa);
        }
    }
    return values;
}

/**
 * Convert multiselect values array ['spa:sub1', 'spa2'] to spaces object { spa: ['sub1'], spa2: [] }
 * @param {Array<string>} values
 * @returns {Object}
 */
export function multiselectValuesToSpacesObject(values) {
    if (!values || !Array.isArray(values)) return {};
    const spaces = {};
    for (const val of values) {
        if (!val || typeof val !== 'string') continue;
        const clean = val.replace(/[{}\(\)]/g, '').replace(/^spa::/i, '').trim();
        const colonIdx = clean.indexOf(':');
        if (colonIdx !== -1) {
            const spa = clean.substring(0, colonIdx).trim().replace(/^spa::/i, '');
            const sub = clean.substring(colonIdx + 1).trim().replace(/^sub::/i, '');
            if (spa && isValidTag(spa)) {
                if (!spaces[spa]) spaces[spa] = [];
                if (sub && isValidTag(sub) && !spaces[spa].includes(sub)) {
                    spaces[spa].push(sub);
                }
            }
        } else {
            const spa = clean.replace(/^spa::/i, '').trim();
            if (spa && isValidTag(spa)) {
                if (!spaces[spa]) spaces[spa] = [];
            }
        }
    }
    return spaces;
}


/**
 * Populate the sidebar nested lists, spaces, and tags under /tasks with counts
 * @param {Array} tasks - Array of task objects
 */
export function populateSidebarTasksSubmenu(tasks) {
    if (!tasks || !Array.isArray(tasks)) return;

    const listsContainer = document.getElementById('sidebar-lists-container');
    const spacesContainer = document.getElementById('sidebar-spaces-container');
    const tagsContainer = document.getElementById('sidebar-tags-container');
    const allCountBadge = document.getElementById('sidebar-all-tasks-count');

    // Total tasks count (pending or total)
    if (allCountBadge) {
        const pendingCount = tasks.filter(t => t.status === 'pending' && !t.is_deleted).length;
        allCountBadge.textContent = pendingCount || tasks.length;
    }

    // Get unique lists, spaces, and tags with counts
    const listsWithCounts = getListsWithCounts(tasks);
    const spacesWithCounts = getSpacesWithCounts(tasks);
    const tagsWithCounts = getTagsWithCounts(tasks);

    // Populate lists container
    if (listsContainer) {
        if (listsWithCounts.length === 0) {
            listsContainer.innerHTML = '<div class="sidebar-empty-hint">No lists</div>';
        } else {
            listsContainer.innerHTML = listsWithCounts.map(item => `
                <div class="sidebar-subitem" data-type="list" data-value="${escapeHtml(item.label)}" onclick="selectSidebarFilter('list', '${escapeJsString(item.label)}')">
                    <div class="sidebar-subitem-main">
                        <i class="fas fa-list-ul subitem-icon"></i>
                        <span class="subitem-title" title="${escapeHtml(item.label)}">${escapeHtml(item.label)}</span>
                    </div>
                    <span class="subitem-badge">${item.count}</span>
                </div>
            `).join('');
        }
    }

    // Populate spaces container
    if (spacesContainer) {
        if (spacesWithCounts.length === 0) {
            spacesContainer.innerHTML = '<div class="sidebar-empty-hint">No spaces</div>';
        } else {
            spacesContainer.innerHTML = spacesWithCounts.map(item => `
                <div class="sidebar-subitem" data-type="space" data-value="${escapeHtml(item.label)}" onclick="selectSidebarFilter('space', '${escapeJsString(item.label)}')">
                    <div class="sidebar-subitem-main">
                        <i class="fas fa-layer-group subitem-icon" style="color: #6366f1;"></i>
                        <span class="subitem-title" title="${escapeHtml(item.label)}">${escapeHtml(item.label)}</span>
                    </div>
                    <span class="subitem-badge">${item.count}</span>
                </div>
                ${item.subspaces.map(sub => `
                    <div class="sidebar-subitem sidebar-subspace-item" data-type="subspace" data-space="${escapeHtml(item.label)}" data-value="${escapeHtml(sub.label)}" onclick="selectSidebarFilter('subspace', '${escapeJsString(sub.label)}', '${escapeJsString(item.label)}')">
                        <div class="sidebar-subitem-main" style="padding-left: 1.5rem;">
                            <i class="fas fa-angle-right subitem-icon" style="color: #a5b4fc; font-size: 0.75rem; margin-right: 0.25rem;"></i>
                            <span class="subitem-title" title="${escapeHtml(sub.label)}">${escapeHtml(sub.label)}</span>
                        </div>
                        <span class="subitem-badge" style="opacity: 0.85;">${sub.count}</span>
                    </div>
                `).join('')}
            `).join('');
        }
    }

    // Populate tags container
    if (tagsContainer) {
        if (tagsWithCounts.length === 0) {
            tagsContainer.innerHTML = '<div class="sidebar-empty-hint">No tags</div>';
        } else {
            tagsContainer.innerHTML = tagsWithCounts.map(item => `
                <div class="sidebar-subitem" data-type="tag" data-value="${escapeHtml(item.label)}" onclick="selectSidebarFilter('tag', '${escapeJsString(item.label)}')">
                    <div class="sidebar-subitem-main">
                        <span class="subitem-tag-hash">#</span>
                        <span class="subitem-title" title="#${escapeHtml(item.label)}">${escapeHtml(item.label)}</span>
                    </div>
                    <span class="subitem-badge">${item.count}</span>
                </div>
            `).join('');
        }
    }

    // Reapply quick search filter if already typed
    const searchInput = document.getElementById('sidebar-quick-search');
    if (searchInput && searchInput.value) {
        filterSidebarListItems(searchInput.value);
    }
}

/**
 * Handle clicking a list, tag, space, subspace, or 'all' from the sidebar.
 * Automatically navigates to /tasks and applies the filter.
 * @param {string} type - 'all' | 'list' | 'tag' | 'space' | 'subspace'
 * @param {string|null} value
 * @param {string|null} parentSpace
 */
export function selectSidebarFilter(type, value = null, parentSpace = null) {
    // 1. Ensure we are in Tasks section
    showSection('tasks', true);

    // 2. Set filter selection
    if (type === 'all') {
        activeSpaceFilter = null;
        activeSubspaceFilter = null;
        if (listMultiselect) listMultiselect.clear();
        if (tagsMultiselect) tagsMultiselect.clear();
        if (spacesMultiselect) spacesMultiselect.clear();
    } else if (type === 'list') {
        activeSpaceFilter = null;
        activeSubspaceFilter = null;
        if (listMultiselect) listMultiselect.setSelectedValues([value]);
        if (tagsMultiselect) tagsMultiselect.clear();
        if (spacesMultiselect) spacesMultiselect.clear();
    } else if (type === 'tag') {
        activeSpaceFilter = null;
        activeSubspaceFilter = null;
        if (tagsMultiselect) tagsMultiselect.setSelectedValues([value]);
        if (listMultiselect) listMultiselect.clear();
        if (spacesMultiselect) spacesMultiselect.clear();
    } else if (type === 'space') {
        activeSpaceFilter = value;
        activeSubspaceFilter = null;
        if (listMultiselect) listMultiselect.clear();
        if (tagsMultiselect) tagsMultiselect.clear();
        if (spacesMultiselect) spacesMultiselect.setSelectedValues([value]);
    } else if (type === 'subspace') {
        activeSpaceFilter = parentSpace;
        activeSubspaceFilter = value;
        if (listMultiselect) listMultiselect.clear();
        if (tagsMultiselect) tagsMultiselect.clear();
        const subVal = parentSpace ? `${parentSpace}:${value}` : value;
        if (spacesMultiselect) spacesMultiselect.setSelectedValues([subVal]);
    }

    // 3. Save state & trigger filter update
    saveFilterState();
    filterTasks();

    // 4. Update sidebar active item highlighting
    updateSidebarActiveItem(type, value, parentSpace);

    // 5. On mobile, close sidebar drawer
    if (window.innerWidth <= 768) {
        closeSidebarOnMobile();
    }
}

/**
 * Update the visual active state of items in the sidebar
 * @param {string} type - 'all' | 'list' | 'tag' | 'space' | 'subspace'
 * @param {string|null} value
 * @param {string|null} parentSpace
 */
export function updateSidebarActiveItem(type, value = null, parentSpace = null) {
    document.querySelectorAll('#sidebar-tasks-submenu .sidebar-subitem').forEach(el => el.classList.remove('active'));

    if (type === 'all') {
        const allEl = document.getElementById('sidebar-item-all-tasks');
        if (allEl) allEl.classList.add('active');
    } else if (type === 'list' && value) {
        const escaped = value.replace(/["\\]/g, '\\$&');
        const el = document.querySelector(`#sidebar-tasks-submenu .sidebar-subitem[data-type="list"][data-value="${escaped}"]`);
        if (el) el.classList.add('active');
    } else if (type === 'tag' && value) {
        const escaped = value.replace(/["\\]/g, '\\$&');
        const el = document.querySelector(`#sidebar-tasks-submenu .sidebar-subitem[data-type="tag"][data-value="${escaped}"]`);
        if (el) el.classList.add('active');
    } else if (type === 'space' && value) {
        const escaped = value.replace(/["\\]/g, '\\$&');
        const el = document.querySelector(`#sidebar-tasks-submenu .sidebar-subitem[data-type="space"][data-value="${escaped}"]`);
        if (el) el.classList.add('active');
    } else if (type === 'subspace' && value) {
        const escapedVal = value.replace(/["\\]/g, '\\$&');
        const escapedSpa = (parentSpace || '').replace(/["\\]/g, '\\$&');
        const el = document.querySelector(`#sidebar-tasks-submenu .sidebar-subitem[data-type="subspace"][data-value="${escapedVal}"][data-space="${escapedSpa}"]`);
        if (el) el.classList.add('active');
    }
}

/**
 * Sync the sidebar active item highlight based on active filters
 * @param {Object} filters
 */
export function syncSidebarActiveFilter(filters) {
    if (!filters) return;
    const lists = filters.list || [];
    const tags = filters.tags || [];
    let space = filters.space || null;
    let subspace = filters.subspace || null;

    if (!space && !subspace && filters.spaces && filters.spaces.length === 1) {
        const val = filters.spaces[0];
        if (val.includes(':')) {
            const parts = val.split(':');
            space = parts[0];
            subspace = parts[1];
        } else {
            space = val;
        }
    }

    if (subspace && space) {
        updateSidebarActiveItem('subspace', subspace, space);
    } else if (space) {
        updateSidebarActiveItem('space', space);
    } else if (lists.length === 1 && tags.length === 0) {
        updateSidebarActiveItem('list', lists[0]);
    } else if (tags.length === 1 && lists.length === 0) {
        updateSidebarActiveItem('tag', tags[0]);
    } else if (lists.length === 0 && tags.length === 0 && !space && !subspace && (!filters.spaces || filters.spaces.length === 0)) {
        updateSidebarActiveItem('all');
    } else {
        document.querySelectorAll('#sidebar-tasks-submenu .sidebar-subitem').forEach(el => el.classList.remove('active'));
    }
}

/**
 * Filter sidebar lists and tags in real-time by search query
 * @param {string} query
 */
export function filterSidebarListItems(query) {
    const q = (query || '').trim().toLowerCase();
    const clearBtn = document.getElementById('sidebar-quick-search-clear');
    if (clearBtn) {
        clearBtn.style.display = q ? 'inline-flex' : 'none';
    }

    const subitems = document.querySelectorAll('#sidebar-tasks-submenu .sidebar-subitem[data-value]');
    let visibleLists = 0;
    let visibleTags = 0;
    let visibleSpaces = 0;

    subitems.forEach(item => {
        const val = (item.getAttribute('data-value') || '').toLowerCase();
        const spa = (item.getAttribute('data-space') || '').toLowerCase();
        const matches = !q || val.includes(q) || spa.includes(q);
        item.style.display = matches ? 'flex' : 'none';
        if (matches) {
            if (item.getAttribute('data-type') === 'list') visibleLists++;
            if (item.getAttribute('data-type') === 'tag') visibleTags++;
            if (item.getAttribute('data-type') === 'space' || item.getAttribute('data-type') === 'subspace') visibleSpaces++;
        }
    });

    const listsContainer = document.getElementById('sidebar-lists-container');
    const spacesContainer = document.getElementById('sidebar-spaces-container');
    const tagsContainer = document.getElementById('sidebar-tags-container');

    // Remove old no-match hints
    listsContainer?.querySelectorAll('.sidebar-no-match').forEach(e => e.remove());
    spacesContainer?.querySelectorAll('.sidebar-no-match').forEach(e => e.remove());
    tagsContainer?.querySelectorAll('.sidebar-no-match').forEach(e => e.remove());

    if (q && visibleSpaces === 0 && spacesContainer) {
        spacesContainer.insertAdjacentHTML('beforeend', '<div class="sidebar-empty-hint sidebar-no-match">No matching spaces</div>');
    }
    if (q && visibleLists === 0 && listsContainer) {
        listsContainer.insertAdjacentHTML('beforeend', '<div class="sidebar-empty-hint sidebar-no-match">No matching lists</div>');
    }
    if (q && visibleTags === 0 && tagsContainer) {
        tagsContainer.insertAdjacentHTML('beforeend', '<div class="sidebar-empty-hint sidebar-no-match">No matching tags</div>');
    }
}

/**
 * Clear the sidebar quick search input
 */
export function clearSidebarQuickSearch() {
    const input = document.getElementById('sidebar-quick-search');
    if (input) {
        input.value = '';
        filterSidebarListItems('');
        input.focus();
    }
}

/**
 * Toggle collapse/expand of a specific section (lists or tags) in the sidebar
 * When expanding, collapses the other section so the selected one has full vertical length,
 * and scrolls the sidebar so #sidebar-tasks-group sticks to the top.
 * @param {string} section - 'lists' | 'tags'
 */
export function toggleSidebarSection(section) {
    const container = document.getElementById(`sidebar-${section}-container`);
    const chevron = document.getElementById(`sidebar-${section}-chevron`);
    if (!container) return;

    const isCollapsed = container.classList.contains('collapsed');

    if (isCollapsed) {
        // Expand this section
        container.classList.remove('collapsed');
        if (chevron) {
            chevron.style.transform = 'rotate(0deg)';
        }

        // Accordion behavior: collapse other section so current section gets maximum vertical height
        const otherSection = section === 'lists' ? 'tags' : 'lists';
        const otherContainer = document.getElementById(`sidebar-${otherSection}-container`);
        const otherChevron = document.getElementById(`sidebar-${otherSection}-chevron`);
        if (otherContainer) {
            otherContainer.classList.add('collapsed');
        }
        if (otherChevron) {
            otherChevron.style.transform = 'rotate(-90deg)';
        }

        // Scroll sidebar so #sidebar-tasks-group sticks to top
        const sidebar = document.getElementById('sidebar');
        const tasksGroup = document.getElementById('sidebar-tasks-group');
        if (sidebar && tasksGroup) {
            sidebar.scrollTo({
                top: tasksGroup.offsetTop,
                behavior: 'smooth'
            });
        }
    } else {
        // Collapse this section
        container.classList.add('collapsed');
        if (chevron) {
            chevron.style.transform = 'rotate(-90deg)';
        }
    }
}

/**
 * Toggle collapse/expand of the entire tasks submenu in the sidebar
 * @param {Event} e
 */
export function toggleSidebarTasksGroup(e) {
    const sidebar = document.getElementById('sidebar');
    if (sidebar && sidebar.classList.contains('collapsed')) {
        toggleSidebar();
        return;
    }

    const isChevron = e && e.target && (e.target.id === 'tasks-group-chevron' || e.target.classList.contains('submenu-chevron'));
    if (isChevron) {
        if (e.stopPropagation) e.stopPropagation();
        if (e.preventDefault) e.preventDefault();
        const submenu = document.getElementById('sidebar-tasks-submenu');
        const chevron = document.getElementById('tasks-group-chevron');
        if (submenu) {
            const isCollapsed = submenu.classList.toggle('collapsed');
            if (chevron) {
                chevron.style.transform = isCollapsed ? 'rotate(-90deg)' : 'rotate(0deg)';
            }
        }
        return;
    }

    const submenu = document.getElementById('sidebar-tasks-submenu');
    const chevron = document.getElementById('tasks-group-chevron');
    if (submenu && submenu.classList.contains('collapsed')) {
        submenu.classList.remove('collapsed');
        if (chevron) {
            chevron.style.transform = 'rotate(0deg)';
        }
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
// Task View Mode state (compact vs card)
let currentTaskViewMode = localStorage.getItem('gtasks_task_view_mode') || (window.innerWidth <= 768 ? 'compact' : 'card');

export function setTaskViewMode(mode) {
    currentTaskViewMode = mode;
    localStorage.setItem('gtasks_task_view_mode', mode);

    const activeTab = getActiveBrowserTab();
    if (activeTab) {
        activeTab.viewMode = mode;
        saveBrowserTabs();
    }
    
    const compactBtn = document.getElementById('view-mode-compact');
    const cardBtn = document.getElementById('view-mode-card');
    if (compactBtn && cardBtn) {
        compactBtn.classList.toggle('active', mode === 'compact');
        cardBtn.classList.toggle('active', mode === 'card');
    }
    
    const container = document.getElementById('tasks-grid');
    if (container) {
        container.classList.toggle('compact', mode === 'compact');
    }
    
    filterTasks();
}

export function toggleFilterDrawer() {
    const drawer = document.getElementById('task-filters-drawer');
    const backdrop = document.getElementById('filter-drawer-backdrop');
    if (!drawer) return;
    
    if (window.innerWidth <= 768) {
        const isOpen = drawer.classList.contains('open');
        if (isOpen) {
            closeFilterDrawer();
        } else {
            openFilterDrawer();
        }
    } else {
        const isHidden = drawer.style.display === 'none';
        drawer.style.display = isHidden ? 'flex' : 'none';
        const toggleBtn = document.getElementById('filter-drawer-toggle-btn');
        if (toggleBtn) {
            toggleBtn.classList.toggle('active', isHidden);
        }
    }
}

export function openFilterDrawer() {
    const drawer = document.getElementById('task-filters-drawer');
    const backdrop = document.getElementById('filter-drawer-backdrop');
    if (!drawer) return;
    if (window.innerWidth <= 768) {
        drawer.classList.add('open');
        if (backdrop) backdrop.classList.add('active');
        document.body.classList.add('drawer-open');
    } else {
        drawer.style.display = 'flex';
    }
}

export function closeFilterDrawer() {
    const drawer = document.getElementById('task-filters-drawer');
    const backdrop = document.getElementById('filter-drawer-backdrop');
    if (!drawer) return;
    if (window.innerWidth <= 768) {
        drawer.classList.remove('open');
        if (backdrop) backdrop.classList.remove('active');
        document.body.classList.remove('drawer-open');
    } else {
        drawer.style.display = 'none';
    }
}

export function clearTaskSearch() {
    const searchFilter = document.getElementById('task-search-filter');
    if (searchFilter) {
        searchFilter.value = '';
        filterTasks();
    }
}

export function removeFilterChip(filterType, value = null) {
    if (filterType === 'search') {
        const el = document.getElementById('task-search-filter');
        if (el) el.value = '';
    } else if (filterType === 'status') {
        if (statusMultiselect) {
            if (value) statusMultiselect.deselect(value);
            else statusMultiselect.clear();
        } else {
            const el = document.getElementById('task-status-filter');
            if (el) el.value = '';
        }
    } else if (filterType === 'priority') {
        const el = document.getElementById('task-priority-filter');
        if (el) el.value = '';
    } else if (filterType === 'date') {
        const s = document.getElementById('task-date-start');
        const e = document.getElementById('task-date-end');
        if (s) s.value = '';
        if (e) e.value = '';
    } else if (filterType === 'list') {
        if (listMultiselect) {
            if (value) listMultiselect.deselect(value);
            else listMultiselect.clear();
        }
    } else if (filterType === 'hideList' || filterType === 'hideLists') {
        if (hideListsMultiselect) {
            if (value) hideListsMultiselect.deselect(value);
            else hideListsMultiselect.clear();
        }
    } else if (filterType === 'hideRecurring') {
        if (hideRecurringMultiselect) {
            if (value) hideRecurringMultiselect.deselect(value);
            else hideRecurringMultiselect.clear();
        }
    } else if (filterType === 'tags') {
        if (tagsMultiselect) {
            if (value) tagsMultiselect.deselect(value);
            else tagsMultiselect.clear();
        }
    } else if (filterType === 'spaces' || filterType === 'space') {
        if (spacesMultiselect) {
            if (value) spacesMultiselect.deselect(value);
            else spacesMultiselect.clear();
        }
        activeSpaceFilter = null;
        activeSubspaceFilter = null;
        if (typeof updateSidebarActiveItem === 'function') {
            updateSidebarActiveItem('all');
        }
    } else if (filterType === 'subspace') {
        if (spacesMultiselect && value) {
            spacesMultiselect.deselect(value);
        }
        activeSubspaceFilter = null;
        if (activeSpaceFilter && typeof updateSidebarActiveItem === 'function') {
            updateSidebarActiveItem('space', activeSpaceFilter);
        } else if (typeof updateSidebarActiveItem === 'function') {
            updateSidebarActiveItem('all');
        }
    }
    saveFilterState();
    updateFilteredMultiselect();
    filterTasks();
}

export function updateActiveFilterChips(filters) {
    const chipsContainer = document.getElementById('active-filter-chips');
    const badge = document.getElementById('filter-count-badge');
    const toggleBtn = document.getElementById('filter-drawer-toggle-btn');
    const clearSearchBtn = document.getElementById('clear-search-btn');
    
    if (clearSearchBtn) {
        clearSearchBtn.style.display = filters.search ? 'inline-flex' : 'none';
    }
    
    let activeCount = 0;
    const chips = [];
    
    if (filters.search) {
        activeCount++;
        chips.push({
            type: 'search',
            label: `Search: "${filters.search}"`,
            remove: "window.removeFilterChip('search')"
        });
    }
    if (Array.isArray(filters.status) && filters.status.length > 0) {
        activeCount += filters.status.length;
        const labelMap = { pending: 'Pending', in_progress: 'In Progress', inprogress: 'In Progress', completed: 'Completed' };
        filters.status.forEach(st => {
            const displayStatus = labelMap[String(st).toLowerCase()] || st;
            chips.push({
                type: 'status',
                label: `Status: ${displayStatus}`,
                remove: `window.removeFilterChip('status', '${st}')`
            });
        });
    } else if (typeof filters.status === 'string' && filters.status) {
        activeCount++;
        chips.push({
            type: 'status',
            label: `Status: ${filters.status}`,
            remove: "window.removeFilterChip('status')"
        });
    }
    if (filters.priority) {
        activeCount++;
        chips.push({
            type: 'priority',
            label: `Priority: ${filters.priority}`,
            remove: "window.removeFilterChip('priority')"
        });
    }
    if (filters.list && filters.list.length > 0) {
        activeCount += filters.list.length;
        filters.list.forEach(item => {
            chips.push({
                type: 'list',
                label: `List: ${item}`,
                remove: `window.removeFilterChip('list', '${item.replace(/'/g, "\\'")}')`
            });
        });
    }
    if (filters.hideLists && filters.hideLists.length > 0) {
        activeCount += filters.hideLists.length;
        filters.hideLists.forEach(item => {
            chips.push({
                type: 'hideList',
                label: `Hidden: ${item}`,
                remove: `window.removeFilterChip('hideList', '${item.replace(/'/g, "\\'")}')`
            });
        });
    }
    if (filters.hideRecurring && filters.hideRecurring.length > 0) {
        activeCount += filters.hideRecurring.length;
        const recLabelMap = {
            all: 'All Recurring',
            daily: 'Daily',
            weekly: 'Weekly',
            monthly: 'Monthly',
            yearly: 'Yearly',
            other: 'Other Repeating'
        };
        filters.hideRecurring.forEach(item => {
            const displayLabel = recLabelMap[String(item).toLowerCase()] || item;
            chips.push({
                type: 'hideRecurring',
                label: `Hide: ${displayLabel}`,
                remove: `window.removeFilterChip('hideRecurring', '${item.replace(/'/g, "\\'")}')`
            });
        });
    }
    if (filters.tags && filters.tags.length > 0) {
        activeCount += filters.tags.length;
        filters.tags.forEach(item => {
            chips.push({
                type: 'tags',
                label: `Tag: #${item}`,
                remove: `window.removeFilterChip('tags', '${item.replace(/'/g, "\\'")}')`
            });
        });
    }
    if (filters.spaces && filters.spaces.length > 0) {
        activeCount += filters.spaces.length;
        filters.spaces.forEach(item => {
            let label = `Space: ${item}`;
            if (item.includes(':')) {
                const [spa, sub] = item.split(':', 2);
                label = `Space: ${spa} › ${sub}`;
            }
            chips.push({
                type: 'spaces',
                label: label,
                remove: `window.removeFilterChip('spaces', '${item.replace(/'/g, "\\'")}')`
            });
        });
    } else {
        if (filters.space) {
            activeCount++;
            chips.push({
                type: 'space',
                label: `Space: ${filters.space}`,
                remove: "window.removeFilterChip('space')"
            });
        }
        if (filters.subspace) {
            activeCount++;
            chips.push({
                type: 'subspace',
                label: `Sub-space: ${filters.subspace}`,
                remove: "window.removeFilterChip('subspace')"
            });
        }
    }
    if (filters.dateStart || filters.dateEnd) {
        activeCount++;
        const rangeStr = `${filters.dateStart || 'any'} to ${filters.dateEnd || 'any'}`;
        chips.push({
            type: 'date',
            label: `Date: ${rangeStr}`,
            remove: "window.removeFilterChip('date')"
        });
    }
    
    const mobileBadge = document.getElementById('mobile-filter-badge');
    const mobileToggleBtn = document.getElementById('mobile-top-filter-btn');
    
    if (badge) {
        if (activeCount > 0) {
            badge.textContent = activeCount;
            badge.style.display = 'inline-flex';
            if (toggleBtn) toggleBtn.classList.add('has-filters');
        } else {
            badge.style.display = 'none';
            if (toggleBtn) toggleBtn.classList.remove('has-filters');
        }
    }
    
    if (mobileBadge) {
        if (activeCount > 0) {
            mobileBadge.textContent = activeCount;
            mobileBadge.style.display = 'inline-flex';
            if (mobileToggleBtn) mobileToggleBtn.classList.add('has-filters');
        } else {
            mobileBadge.style.display = 'none';
            if (mobileToggleBtn) mobileToggleBtn.classList.remove('has-filters');
        }
    }
    
    if (chipsContainer) {
        if (chips.length > 0) {
            chipsContainer.style.display = 'flex';
            let html = chips.map(c => `
                <span class="filter-chip">
                    <span class="chip-text">${c.label}</span>
                    <button type="button" class="chip-remove" onclick="${c.remove}" aria-label="Remove filter">&times;</button>
                </span>
            `).join('');
            html += `
                <button type="button" class="filter-clear-all-link" onclick="window.clearTasksFilters()">
                    Reset All
                </button>
            `;
            chipsContainer.innerHTML = html;
        } else {
            chipsContainer.style.display = 'none';
            chipsContainer.innerHTML = '';
        }
    }
}

export function filterTasks() {
    // Get values from multiselect filters
    let listValues = [];
    let spaceValues = [];
    let tagValues = [];
    let statusValues = [];
    
    if (listMultiselect) {
        listValues = listMultiselect.getSelectedValues();
    } else {
        const listFilterEl = document.getElementById('task-list-filter');
        if (listFilterEl && listFilterEl.value) {
            try { listValues = JSON.parse(listFilterEl.value); } catch (e) { listValues = []; }
        }
    }

    let hideListValues = [];
    if (hideListsMultiselect) {
        hideListValues = hideListsMultiselect.getSelectedValues();
    } else {
        const hideListFilterEl = document.getElementById('task-hide-lists-filter');
        if (hideListFilterEl && hideListFilterEl.value) {
            try { hideListValues = JSON.parse(hideListFilterEl.value); } catch (e) { hideListValues = []; }
        }
    }

    let hideRecurringValues = [];
    if (hideRecurringMultiselect) {
        hideRecurringValues = hideRecurringMultiselect.getSelectedValues();
    } else {
        const hideRecFilterEl = document.getElementById('task-hide-recurring-filter');
        if (hideRecFilterEl && hideRecFilterEl.value) {
            try { hideRecurringValues = JSON.parse(hideRecFilterEl.value); } catch (e) { hideRecurringValues = []; }
        }
    }

    if (spacesMultiselect) {
        spaceValues = spacesMultiselect.getSelectedValues();
    }
    
    if (tagsMultiselect) {
        tagValues = tagsMultiselect.getSelectedValues();
    } else {
        const tagsFilterEl = document.getElementById('task-tags-filter');
        if (tagsFilterEl && tagsFilterEl.value) {
            try { tagValues = JSON.parse(tagsFilterEl.value); } catch (e) { tagValues = []; }
        }
    }

    if (statusMultiselect) {
        statusValues = statusMultiselect.getSelectedValues();
    } else {
        const statusFilterEl = document.getElementById('task-status-filter');
        if (statusFilterEl && statusFilterEl.value) {
            try {
                const parsed = JSON.parse(statusFilterEl.value);
                statusValues = Array.isArray(parsed) ? parsed : [statusFilterEl.value];
            } catch (e) {
                statusValues = statusFilterEl.value ? [statusFilterEl.value] : [];
            }
        }
    }
    
    const filters = {
        search: document.getElementById('task-search-filter')?.value.toLowerCase() || '',
        status: statusValues,
        priority: document.getElementById('task-priority-filter')?.value || '',
        list: listValues,
        hideLists: hideListValues,
        hideRecurring: hideRecurringValues,
        spaces: spaceValues,
        tags: tagValues,
        space: activeSpaceFilter,
        subspace: activeSubspaceFilter,
        dateField: document.getElementById('task-date-field')?.value || 'modified_at',
        dateStart: document.getElementById('task-date-start')?.value || '',
        dateEnd: document.getElementById('task-date-end')?.value || '',
        sortField: document.getElementById('task-sort-field')?.value || 'modified_at',
        sortOrder: document.getElementById('task-sort-order')?.value || 'desc'
    };
    
    let filteredTasks = dashboardData.tasks || [];
    const totalTasks = filteredTasks.length;
    const container = document.getElementById('tasks-grid');
    if (!container) return;
    
    container.innerHTML = '';
    
    // Update container compact class
    container.classList.toggle('compact', currentTaskViewMode === 'compact');
    
    // Update active filter chips and badges
    updateActiveFilterChips(filters);
    
    // Synchronize sidebar active list/tag highlight
    syncSidebarActiveFilter(filters);
    
    // Filter out deleted tasks if setting is enabled
    filteredTasks = filterOutDeletedTasks(filteredTasks);
    
    // Apply filters
    filteredTasks = filterTasksByCriteria(filteredTasks, filters);
    
    // Expose active view state for AI Assistant & update context
    window.currentFilteredTasks = filteredTasks;
    window.currentActiveFilters = filters;
    if (window.AiChatController && typeof window.AiChatController.onViewContextUpdated === 'function') {
        window.AiChatController.onViewContextUpdated({
            tasks: filteredTasks,
            allTasks: dashboardData.tasks || [],
            filters: filters,
            totalCount: totalTasks,
            filteredCount: filteredTasks.length
        });
    }
    
    // Update task count display
    updateTasksCountDisplay(filteredTasks.length, totalTasks);

    // Sync active browser tab filters and update live tab badges
    const activeTab = getActiveBrowserTab();
    if (activeTab) {
        activeTab.filters = { ...filters };
        activeTab.viewMode = currentTaskViewMode;
        saveBrowserTabs();
    }
    updateBrowserTabBadges();
    
    if (filteredTasks.length === 0) {
        container.innerHTML = '<p style="text-align: center; color: #6b7280; padding: 2rem;">No tasks match your filters.</p>';
        return;
    }
    
    filteredTasks.forEach(task => {
        const card = createTaskCard(task, { isCompact: currentTaskViewMode === 'compact' });
        container.appendChild(card);
    });
}

/**
 * Clear all task filters and restore defaults
 */
export function clearTasksFilters() {
    activeSpaceFilter = null;
    activeSubspaceFilter = null;
    if (typeof updateSidebarActiveItem === 'function') {
        updateSidebarActiveItem('all');
    }
    const defaults = getDefaultFilterState();
    
    // Reset search filter
    const searchFilter = document.getElementById('task-search-filter');
    if (searchFilter) searchFilter.value = defaults.search;
    
    // Reset status multiselect
    if (statusMultiselect) {
        statusMultiselect.setSelectedValues(defaults.status);
    } else {
        const statusFilter = document.getElementById('task-status-filter');
        if (statusFilter) statusFilter.value = '';
    }
    
    // Reset priority filter
    const priorityFilter = document.getElementById('task-priority-filter');
    if (priorityFilter) priorityFilter.value = defaults.priority;
    
    // Reset list filter
    if (listMultiselect) {
        listMultiselect.clear();
    }

    // Reset hide lists filter
    if (hideListsMultiselect) {
        hideListsMultiselect.clear();
    }

    // Reset hide recurring filter
    if (hideRecurringMultiselect) {
        hideRecurringMultiselect.clear();
    }

    // Reset spaces filter
    if (spacesMultiselect) {
        spacesMultiselect.clear();
    }
    
    // Reset tags filter
    if (tagsMultiselect) {
        tagsMultiselect.clear();
    }
    
    // Reset date field filter
    const dateFieldFilter = document.getElementById('task-date-field');
    if (dateFieldFilter) dateFieldFilter.value = defaults.dateField;
    
    // Reset date range filters to default past 31 days
    const dateStartFilter = document.getElementById('task-date-start');
    if (dateStartFilter) dateStartFilter.value = defaults.dateStart;
    
    const dateEndFilter = document.getElementById('task-date-end');
    if (dateEndFilter) dateEndFilter.value = defaults.dateEnd;
    
    // Reset sort field
    const sortFieldFilter = document.getElementById('task-sort-field');
    if (sortFieldFilter) sortFieldFilter.value = defaults.sortField;
    
    // Reset sort order
    const sortOrderFilter = document.getElementById('task-sort-order');
    if (sortOrderFilter) sortOrderFilter.value = defaults.sortOrder;
    
    // Save to storage
    saveFilterState();
    
    // Restore all options to multiselects and re-apply filters
    const allLists = getListsWithCounts(allTasks);
    const allSpaces = getSpacesWithCounts(allTasks);
    const allTags = getTagsWithCounts(allTasks);
    const allStatuses = getStatusWithCounts(allTasks);
    
    if (listMultiselect) {
        listMultiselect.setOptions(allLists);
    }

    if (spacesMultiselect) {
        spacesMultiselect.setOptions(allSpaces);
    }
    
    if (tagsMultiselect) {
        tagsMultiselect.setOptions(allTags);
    }

    if (statusMultiselect) {
        statusMultiselect.setOptions(allStatuses);
    }
    
    // Update filtered multiselects
    updateFilteredMultiselect(
        defaults.search,
        defaults.dateStart,
        defaults.dateEnd,
        defaults.dateField
    );
    
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
export async function initSettings() {
    const settings = stateManager.getSettings();
    
    // Update local UI
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
    
    const path = window.location.pathname;
    if (settings.defaultView && settings.defaultView !== 'dashboard' && path === '/') {
        showSection(settings.defaultView, false);
    }
}

export async function openSettings() {
    const modal = document.getElementById('settings-modal');
    if (!modal) return;
    modal.classList.add('active');

    // Pre-render Tags and Spaces management view
    renderSettingsTagsAndSpaces();

    // Fetch live backend config
    try {
        const basePath = window.GTASKS_BASE_PATH || '';
        const res = await fetch(`${basePath}/api/settings`);
        const json = await res.json();
        if (json.success && json.data) {
            populateBackendSettingsForm(json.data.config || {}, json.data.feature_flags || {});
        }
    } catch (e) {
        console.warn('[Settings] Failed to fetch backend settings:', e);
    }
}

function populateBackendSettingsForm(cfg, flags) {
    const defaultList = document.getElementById('setting-default-list');
    const dateFormat = document.getElementById('setting-date-format');
    const timeFormat = document.getElementById('setting-time-format');
    const tableStyle = document.getElementById('setting-table-style');

    const autoSave = document.getElementById('setting-auto-save');
    const pullDays = document.getElementById('setting-pull-days');

    const emailUser = document.getElementById('setting-email-user');
    const emailPassword = document.getElementById('setting-email-password');

    const flagPriority = document.getElementById('setting-flag-priority');
    const flagReports = document.getElementById('setting-flag-reports');
    const flagAdvanced = document.getElementById('setting-flag-advanced');

    if (defaultList) defaultList.value = cfg.default_tasklist || 'My Tasks';
    if (dateFormat) dateFormat.value = cfg.date_format || '%Y-%m-%d';
    if (timeFormat) timeFormat.value = cfg.time_format || '%H:%M';
    if (tableStyle && cfg.display) tableStyle.value = cfg.display.table_style || 'simple';

    if (autoSave && cfg.sync) autoSave.checked = Boolean(cfg.sync.auto_save);
    if (pullDays && cfg.sync) pullDays.value = cfg.sync.pull_range_days || 10;

    if (emailUser && cfg.email) emailUser.value = cfg.email.user || '';
    if (emailPassword && cfg.email) emailPassword.value = cfg.email.password || '';

    if (flagPriority) flagPriority.checked = Boolean(flags.ENABLE_PRIORITY_SYSTEM);
    if (flagReports) flagReports.checked = Boolean(flags.ENABLE_REPORTS);
    if (flagAdvanced) flagAdvanced.checked = Boolean(flags.ENABLE_ADVANCED_FILTERS);
}

export function switchSettingsTab(tabName) {
    document.querySelectorAll('.settings-tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.settings-tab-pane').forEach(p => p.classList.remove('active'));

    const btn = document.getElementById(`tab-btn-${tabName}`);
    const pane = document.getElementById(`tab-pane-${tabName}`);

    if (btn) btn.classList.add('active');
    if (pane) pane.classList.add('active');

    if (tabName === 'tags-spaces') {
        renderSettingsTagsAndSpaces();
    }
}

export function renderSettingsTagsAndSpaces() {
    const spacesListEl = document.getElementById('settings-spaces-list');
    const tagsListEl = document.getElementById('settings-tags-list');
    const spacesSummaryEl = document.getElementById('settings-spaces-summary');
    const tagsSummaryEl = document.getElementById('settings-tags-summary');
    if (!spacesListEl || !tagsListEl) return;

    // Collect all tasks across accounts
    const allTasks = [];
    if (dashboardData && dashboardData.tasks) {
        if (Array.isArray(dashboardData.tasks)) {
            allTasks.push(...dashboardData.tasks);
        } else {
            Object.values(dashboardData.tasks).forEach(list => {
                if (Array.isArray(list)) allTasks.push(...list);
            });
        }
    }

    const spacesMap = {};
    const tagsMap = {};

    allTasks.forEach(task => {
        let spaces = task.spaces;
        if (!spaces && (task.notes || task.description)) {
            spaces = extractSpacesFromText(task.notes || task.description || '');
        }
        if (spaces && typeof spaces === 'object') {
            Object.entries(spaces).forEach(([sName, subs]) => {
                const sClean = sName.trim();
                if (!sClean) return;
                if (!spacesMap[sClean]) {
                    spacesMap[sClean] = { total: 0, subspaces: {} };
                }
                spacesMap[sClean].total++;
                if (Array.isArray(subs)) {
                    subs.forEach(sub => {
                        const subClean = sub.trim().replace(/^sub::/i, '');
                        if (subClean) {
                            spacesMap[sClean].subspaces[subClean] = (spacesMap[sClean].subspaces[subClean] || 0) + 1;
                        }
                    });
                }
            });
        }

        let tags = task.tags;
        if ((!tags || tags.length === 0) && (task.notes || task.description)) {
            const split = splitNotesAndTags(task.notes || task.description || '');
            tags = split.tags;
        }
        if (Array.isArray(tags)) {
            tags.forEach(t => {
                const tClean = String(t).trim().toLowerCase().replace(/^[\[#]+|[\]]+$/g, '');
                if (tClean && isValidTag(tClean)) {
                    tagsMap[tClean] = (tagsMap[tClean] || 0) + 1;
                }
            });
        }
    });

    const spaceKeys = Object.keys(spacesMap).sort();
    const tagKeys = Object.keys(tagsMap).sort();

    if (spacesSummaryEl) spacesSummaryEl.textContent = `${spaceKeys.length} space(s)`;
    if (tagsSummaryEl) tagsSummaryEl.textContent = `${tagKeys.length} tag(s)`;

    if (spaceKeys.length === 0) {
        spacesListEl.innerHTML = `<div style="font-size: 0.8rem; color: var(--text-muted); font-style: italic; padding: 0.5rem 0;">No spaces found in tasks.</div>`;
    } else {
        spacesListEl.innerHTML = spaceKeys.map(space => {
            const data = spacesMap[space];
            const subKeys = Object.keys(data.subspaces).sort();
            const subsHtml = subKeys.length > 0 ? `
                <div style="display: flex; flex-wrap: wrap; gap: 0.4rem; margin-top: 0.4rem; padding-left: 0.25rem;">
                    ${subKeys.map(sub => `
                        <span class="subspace-pill" style="display: inline-flex; align-items: center; gap: 0.35rem; background: var(--hover-bg, rgba(0,0,0,0.05)); border: 1px solid var(--border-color, #e2e8f0); border-radius: 12px; padding: 0.15rem 0.55rem; font-size: 0.75rem;">
                            <span>${escapeHtml(sub)}</span>
                            <span style="font-size: 0.65rem; color: var(--text-muted);">(${data.subspaces[sub]})</span>
                            <button type="button" onclick="deleteSpaceFromDashboard('${escapeJsString(space)}', '${escapeJsString(sub)}')" style="background: none; border: none; cursor: pointer; padding: 0; color: #ef4444; font-size: 0.75rem; display: flex; align-items: center;" title="Remove sub-space '${escapeHtml(sub)}'">
                                <i class="fas fa-times"></i>
                            </button>
                        </span>
                    `).join('')}
                </div>
            ` : '';

            return `
                <div style="background: var(--bg-secondary, rgba(0,0,0,0.02)); border: 1px solid var(--border-color, #e2e8f0); border-radius: 8px; padding: 0.6rem 0.75rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div style="display: flex; align-items: center; gap: 0.5rem;">
                            <i class="fas fa-rocket text-primary" style="font-size: 0.85rem;"></i>
                            <span style="font-weight: 600; font-size: 0.85rem;">${escapeHtml(space)}</span>
                            <span class="badge" style="background: rgba(99, 102, 241, 0.15); color: #6366f1; font-size: 0.7rem; font-weight: 600; padding: 0.15rem 0.45rem; border-radius: 10px;">${data.total} tasks</span>
                        </div>
                        <button type="button" class="btn btn-sm" onclick="deleteSpaceFromDashboard('${escapeJsString(space)}')" style="color: #ef4444; background: rgba(239, 68, 68, 0.08); border: 1px solid rgba(239, 68, 68, 0.25); border-radius: 6px; padding: 0.25rem 0.6rem; font-size: 0.75rem; cursor: pointer; display: flex; align-items: center; gap: 0.35rem;" title="Delete entire space '${escapeHtml(space)}'">
                            <i class="fas fa-trash-alt"></i>
                            <span>Delete Space</span>
                        </button>
                    </div>
                    ${subsHtml}
                </div>
            `;
        }).join('');
    }

    if (tagKeys.length === 0) {
        tagsListEl.innerHTML = `<div style="font-size: 0.8rem; color: var(--text-muted); font-style: italic; padding: 0.5rem 0;">No tags found in tasks.</div>`;
    } else {
        tagsListEl.innerHTML = tagKeys.map(tag => {
            const count = tagsMap[tag];
            return `
                <span style="display: inline-flex; align-items: center; gap: 0.4rem; background: rgba(13, 148, 136, 0.1); border: 1px solid rgba(13, 148, 136, 0.25); color: #0d9488; border-radius: 14px; padding: 0.25rem 0.6rem; font-size: 0.8rem; font-weight: 500;">
                    <span>#${escapeHtml(tag)}</span>
                    <span style="font-size: 0.7rem; opacity: 0.8;">(${count})</span>
                    <button type="button" onclick="deleteTagFromDashboard('${escapeJsString(tag)}')" style="background: none; border: none; cursor: pointer; padding: 0 0 0 2px; color: #ef4444; font-size: 0.8rem; display: flex; align-items: center;" title="Remove tag '#${escapeHtml(tag)}' from all tasks">
                        <i class="fas fa-times-circle"></i>
                    </button>
                </span>
            `;
        }).join('');
    }
}

export async function deleteTagFromDashboard(tagName) {
    if (!tagName) return;
    const confirmed = confirm(`Are you sure you want to remove tag '#${tagName}' from all tasks?`);
    if (!confirmed) return;

    try {
        const basePath = window.GTASKS_BASE_PATH || '';
        const res = await fetch(`${basePath}/api/tags/delete`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ tag: tagName })
        });
        const json = await res.json();
        if (json.success) {
            alert(`✅ ${json.message}`);
            await fetchDashboardData();
            renderSettingsTagsAndSpaces();
        } else {
            alert(`❌ Error: ${json.message || 'Failed to remove tag'}`);
        }
    } catch (e) {
        alert(`❌ Network error: ${e.message}`);
    }
}

export async function deleteSpaceFromDashboard(spaceName, subspaceName = null) {
    if (!spaceName) return;
    const label = subspaceName ? `sub-space '${spaceName} › ${subspaceName}'` : `space '${spaceName}' and all its sub-spaces`;
    const confirmed = confirm(`Are you sure you want to remove ${label} from all tasks?`);
    if (!confirmed) return;

    try {
        const basePath = window.GTASKS_BASE_PATH || '';
        const res = await fetch(`${basePath}/api/spaces/delete`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ space: spaceName, subspace: subspaceName || undefined })
        });
        const json = await res.json();
        if (json.success) {
            alert(`✅ ${json.message}`);
            await fetchDashboardData();
            renderSettingsTagsAndSpaces();
        } else {
            alert(`❌ Error: ${json.message || 'Failed to remove space'}`);
        }
    } catch (e) {
        alert(`❌ Network error: ${e.message}`);
    }
}

export async function saveAllSettings() {
    const btn = document.getElementById('btn-save-settings');
    const originalText = btn ? btn.innerHTML : '';
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';
    }

    try {
        const defaultList = document.getElementById('setting-default-list');
        const dateFormat = document.getElementById('setting-date-format');
        const timeFormat = document.getElementById('setting-time-format');
        const tableStyle = document.getElementById('setting-table-style');

        const autoSave = document.getElementById('setting-auto-save');
        const pullDays = document.getElementById('setting-pull-days');

        const emailUser = document.getElementById('setting-email-user');
        const emailPassword = document.getElementById('setting-email-password');

        const flagPriority = document.getElementById('setting-flag-priority');
        const flagReports = document.getElementById('setting-flag-reports');
        const flagAdvanced = document.getElementById('setting-flag-advanced');

        const settingsPayload = {
            'default_tasklist': defaultList ? defaultList.value : 'My Tasks',
            'date_format': dateFormat ? dateFormat.value : '%Y-%m-%d',
            'time_format': timeFormat ? timeFormat.value : '%H:%M',
            'display.table_style': tableStyle ? tableStyle.value : 'simple',
            'sync.auto_save': autoSave ? autoSave.checked : true,
            'sync.pull_range_days': pullDays ? parseInt(pullDays.value) : 10
        };

        if (emailUser && emailUser.value) {
            settingsPayload['email.user'] = emailUser.value.trim();
        }
        if (emailPassword && emailPassword.value && !emailPassword.value.startsWith('•••')) {
            settingsPayload['email.password'] = emailPassword.value.trim();
        }

        const featureFlagsPayload = {
            'ENABLE_PRIORITY_SYSTEM': flagPriority ? flagPriority.checked : true,
            'ENABLE_REPORTS': flagReports ? flagReports.checked : true,
            'ENABLE_ADVANCED_FILTERS': flagAdvanced ? flagAdvanced.checked : true
        };

        const basePath = window.GTASKS_BASE_PATH || '';
        const res = await fetch(`${basePath}/api/settings`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                settings: settingsPayload,
                feature_flags: featureFlagsPayload
            })
        });

        const json = await res.json();
        if (json.success) {
            alert('✅ Settings saved and synchronized successfully!');
            closeSettings();
        } else {
            alert('❌ Failed to save settings: ' + json.message);
        }
    } catch (e) {
        alert('Error saving settings: ' + e.message);
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = originalText;
        }
    }
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
    loadTasks();
    if (typeof refreshHierarchyVisualization === 'function') {
        refreshHierarchyVisualization();
    }
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
        if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 't') {
            const tasksSec = document.getElementById('tasks-section');
            if (tasksSec && tasksSec.style.display !== 'none') {
                e.preventDefault();
                toggleNewTabMenu();
            }
        }
        if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'w') {
            const tasksSec = document.getElementById('tasks-section');
            if (tasksSec && tasksSec.style.display !== 'none' && browserTabs && browserTabs.length > 1) {
                e.preventDefault();
                closeBrowserTab(activeBrowserTabId);
            }
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

    // Initialize task view mode buttons and grid class
    const compactBtn = document.getElementById('view-mode-compact');
    const cardBtn = document.getElementById('view-mode-card');
    if (compactBtn && cardBtn) {
        compactBtn.classList.toggle('active', currentTaskViewMode === 'compact');
        cardBtn.classList.toggle('active', currentTaskViewMode === 'card');
    }
    const tasksGrid = document.getElementById('tasks-grid');
    if (tasksGrid) {
        tasksGrid.classList.toggle('compact', currentTaskViewMode === 'compact');
    }

    // Initialize notifications system
    if (window.initNotifications) {
        window.initNotifications();
    }

    console.log('Dashboard initialized with task view mode:', currentTaskViewMode);
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
    if (sortFieldFilter) sortFieldFilter.value = 'modified_at';
    
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
        const basePath = window.GTASKS_BASE_PATH || '';
        const response = await fetch(`${basePath}/api/tasks/${taskId}/complete`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({})
        });
        
        const data = await response.json();
        
        if (data.success) {
            console.log('Task completed:', taskId);
            
            // 1. Update task in local dashboardData.tasks array
            if (dashboardData.tasks && Array.isArray(dashboardData.tasks)) {
                const localTask = dashboardData.tasks.find(t => t.id === taskId);
                if (localTask) {
                    localTask.status = 'completed';
                    localTask.completed_at = new Date().toISOString();
                }
            }
            
            // 2. Re-filter tasks so active filters (e.g. pending) immediately hide the task,
            // or re-render it with completed state if all/completed filter is active
            filterTasks();
            
            // 3. Update task in hierarchy node tasks or remaining DOM elements
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
window.switchSettingsTab = switchSettingsTab;
window.renderSettingsTagsAndSpaces = renderSettingsTagsAndSpaces;
window.deleteTagFromDashboard = deleteTagFromDashboard;
window.deleteSpaceFromDashboard = deleteSpaceFromDashboard;
window.saveAllSettings = saveAllSettings;
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
window.closeAllRefreshDropdowns = closeAllRefreshDropdowns;
window.syncAndRefresh = syncAndRefresh;
window.syncRemoteDb = syncRemoteDb;
window.setupRefreshDropdown = setupRefreshDropdown;
window.getListsWithCounts = getListsWithCounts;
window.getTagsWithCounts = getTagsWithCounts;
window.updateFilteredMultiselect = updateFilteredMultiselect;
window.populateSidebarTasksSubmenu = populateSidebarTasksSubmenu;
window.selectSidebarFilter = selectSidebarFilter;
window.updateSidebarActiveItem = updateSidebarActiveItem;
window.initBrowserTabs = initBrowserTabs;
window.renderBrowserTabs = renderBrowserTabs;
window.switchBrowserTab = switchBrowserTab;
window.createBrowserTabPreset = createBrowserTabPreset;
window.promptCreateCustomBrowserTab = promptCreateCustomBrowserTab;
window.closeBrowserTab = closeBrowserTab;
window.startTabRename = startTabRename;
window.finishTabRename = finishTabRename;
window.duplicateBrowserTab = duplicateBrowserTab;
window.scrollBrowserTabs = scrollBrowserTabs;
window.toggleNewTabMenu = toggleNewTabMenu;
window.closeNewTabMenu = closeNewTabMenu;
window.updateBrowserTabBadges = updateBrowserTabBadges;
window.syncSidebarActiveFilter = syncSidebarActiveFilter;
window.filterSidebarListItems = filterSidebarListItems;
window.clearSidebarQuickSearch = clearSidebarQuickSearch;
window.toggleSidebarSection = toggleSidebarSection;
window.toggleSidebarTasksGroup = toggleSidebarTasksGroup;

// Edit & Add Modal Functions
window.openEditModal = openEditModal;
window.closeEditModal = closeEditModal;
window.saveTaskEdit = saveTaskEdit;
window.switchNotesTab = switchNotesTab;
window.openAddModal = openAddModal;
window.closeAddModal = closeAddModal;
window.saveNewTask = saveNewTask;
window.onAddAccountChange = onAddAccountChange;
window.switchAddNotesTab = switchAddNotesTab;

// Tag and Space Multiselect instances for Add and Edit modals
let addTaskTagsMultiselect = null;
let editTaskTagsMultiselect = null;
let addTaskSpacesMultiselect = null;
let editTaskSpacesMultiselect = null;

export function initModalTagSelectors() {
    const tasks = (typeof dashboardData !== 'undefined' && dashboardData.tasks) ? dashboardData.tasks : [];
    const allTags = getTagsWithCounts(tasks);
    const allSpacesHierarchy = getSpacesWithCounts(tasks);

    // 1. Tags Selectors
    const addContainer = document.getElementById('add-task-tags-container');
    if (addContainer && !addTaskTagsMultiselect) {
        addContainer.innerHTML = '';
        addTaskTagsMultiselect = createMultiselect({
            id: 'add-task-tags',
            placeholder: 'Click to browse or add tags...',
            options: allTags,
            initialValues: [],
            allowAddNew: true,
            tagFormat: 'bracket',
            showCounts: true
        });
        addContainer.appendChild(addTaskTagsMultiselect);
    }

    const editContainer = document.getElementById('edit-task-tags-container');
    if (editContainer && !editTaskTagsMultiselect) {
        editContainer.innerHTML = '';
        editTaskTagsMultiselect = createMultiselect({
            id: 'edit-task-tags',
            placeholder: 'Click to browse or add tags...',
            options: allTags,
            initialValues: [],
            allowAddNew: true,
            tagFormat: 'bracket',
            showCounts: true
        });
        editContainer.appendChild(editTaskTagsMultiselect);
    }

    // 2. Spaces & Sub-spaces Hierarchical Selectors (Mobile-inspired UX)
    const addSpacesContainer = document.getElementById('add-task-spaces-container');
    if (addSpacesContainer && !addTaskSpacesMultiselect) {
        addSpacesContainer.innerHTML = '';
        addTaskSpacesMultiselect = createMultiselect({
            id: 'add-task-spaces',
            placeholder: 'Click to browse or add spaces & sub-spaces...',
            options: allSpacesHierarchy,
            initialValues: [],
            isSpaceHierarchy: true,
            allowAddNew: true,
            showCounts: true
        });
        addSpacesContainer.appendChild(addTaskSpacesMultiselect);
    }

    const editSpacesContainer = document.getElementById('edit-task-spaces-container');
    if (editSpacesContainer && !editTaskSpacesMultiselect) {
        editSpacesContainer.innerHTML = '';
        editTaskSpacesMultiselect = createMultiselect({
            id: 'edit-task-spaces',
            placeholder: 'Click to browse or add spaces & sub-spaces...',
            options: allSpacesHierarchy,
            initialValues: [],
            isSpaceHierarchy: true,
            allowAddNew: true,
            showCounts: true
        });
        editSpacesContainer.appendChild(editTaskSpacesMultiselect);
    }
}

function openAddModal() {
    // Reset form fields
    document.getElementById('add-task-title').value = '';
    document.getElementById('add-task-priority').value = 'medium';
    document.getElementById('add-task-status').value = 'pending';
    document.getElementById('add-task-due').value = '';
    document.getElementById('add-task-notes').value = '';

    // Initialize or refresh tags and spaces multiselect
    initModalTagSelectors();
    const tasks = (typeof dashboardData !== 'undefined' && dashboardData.tasks) ? dashboardData.tasks : [];
    if (addTaskTagsMultiselect) {
        addTaskTagsMultiselect.setOptions(getTagsWithCounts(tasks));
        addTaskTagsMultiselect.clear();
    }
    if (addTaskSpacesMultiselect) {
        addTaskSpacesMultiselect.setOptions(getSpacesWithCounts(tasks));
        addTaskSpacesMultiselect.clear();
    }

    // Populate Account select
    const accountSelect = document.getElementById('add-task-account');
    accountSelect.innerHTML = '';
    const accounts = (typeof dashboardData !== 'undefined' && dashboardData.accounts) ? dashboardData.accounts : [];
    accounts.forEach(acc => {
        const opt = document.createElement('option');
        opt.value = acc.id;
        opt.textContent = acc.name || acc.id;
        if (acc.id === window.currentAccountId) opt.selected = true;
        accountSelect.appendChild(opt);
    });

    onAddAccountChange(accountSelect.value || window.currentAccountId);
    switchAddNotesTab('edit');
    document.getElementById('add-task-modal').classList.add('active');
}

function closeAddModal() {
    const modal = document.getElementById('add-task-modal');
    if (modal) {
        modal.classList.remove('active');
        modal.classList.remove('is-fullscreen');
        const modalContent = modal.querySelector('.modal-content');
        if (modalContent) modalContent.classList.remove('is-fullscreen');
        if (typeof updateFullscreenIcons === 'function') updateFullscreenIcons(modal, false);
    }
    document.body.classList.remove('modal-fullscreen-active');
}

function onAddAccountChange(accountId) {
    const listSelect = document.getElementById('add-task-list');
    listSelect.innerHTML = '';

    const availableLists = new Set();
    if (typeof dashboardData !== 'undefined') {
        (dashboardData.lists || []).forEach(l => { if (l) availableLists.add(l); });
        (window.allGoogleLists || []).forEach(l => { if (l && l.title) availableLists.add(l.title); });
        (dashboardData.tasks || []).forEach(t => { if (t.list_title) availableLists.add(t.list_title); });
    }
    if (availableLists.size === 0) availableLists.add('My Tasks');

    Array.from(availableLists).sort().forEach(listTitle => {
        const opt = document.createElement('option');
        opt.value = listTitle;
        opt.textContent = listTitle;
        listSelect.appendChild(opt);
    });
}

function switchAddNotesTab(tab) {
    const editBtn = document.getElementById('add-notes-tab-edit');
    const prevBtn = document.getElementById('add-notes-tab-preview');
    if (editBtn && prevBtn) {
        editBtn.classList.toggle('active', tab === 'edit');
        prevBtn.classList.toggle('active', tab === 'preview');
    }

    const textarea = document.getElementById('add-task-notes');
    const preview = document.getElementById('add-notes-preview');

    if (tab === 'preview') {
        textarea.style.display = 'none';
        preview.style.display = 'block';
        if (typeof marked !== 'undefined') {
            preview.innerHTML = marked.parse(textarea.value || '');
        } else {
            preview.textContent = textarea.value;
        }
    } else {
        textarea.style.display = 'block';
        preview.style.display = 'none';
    }
}

function parseSpacesInput(inputStr) {
    if (!inputStr) return {};
    const spaces = {};
    const chunks = inputStr.split(/[|\n;]+/);
    for (const chunk of chunks) {
        const trimmed = chunk.trim();
        if (!trimmed) continue;
        const colonIdx = trimmed.indexOf(':');
        if (colonIdx !== -1) {
            const spa = trimmed.substring(0, colonIdx).trim().replace(/^spa::/i, '');
            const rawSubs = trimmed.substring(colonIdx + 1).trim().replace(/^\(|\)$/g, '');
            const subs = rawSubs.split(',')
                .map(s => s.trim().replace(/^sub::/i, ''))
                .filter(s => s.length > 0 && isValidTag(s));
            if (spa && isValidTag(spa)) {
                spaces[spa] = subs;
            }
        } else {
            const spa = trimmed.replace(/^spa::/i, '');
            if (spa && isValidTag(spa)) {
                spaces[spa] = [];
            }
        }
    }
    return spaces;
}

function formatSpacesForInput(spaces) {
    if (!spaces || typeof spaces !== 'object') return '';
    const parts = [];
    Object.entries(spaces).forEach(([spa, subs]) => {
        if (subs && subs.length > 0) {
            parts.push(`${spa}:${subs.join(',')}`);
        } else {
            parts.push(spa);
        }
    });
    return parts.join(' | ');
}

async function saveNewTask() {
    const title = document.getElementById('add-task-title').value.trim();
    if (!title) {
        showNotification('Task title is required!', 'error');
        return;
    }

    const saveBtn = document.getElementById('add-task-save-btn');
    const originalBtnHtml = saveBtn ? saveBtn.innerHTML : '<i class="fas fa-plus"></i> <span>Create Task</span>';

    if (saveBtn) {
        saveBtn.disabled = true;
        saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> <span>Creating...</span>';
    }

    const cleanNotesInput = document.getElementById('add-task-notes').value;
    const selectedTags = addTaskTagsMultiselect ? addTaskTagsMultiselect.getSelectedValues() : [];
    let parsedSpaces = {};
    if (addTaskSpacesMultiselect) {
        const selectedSpaces = addTaskSpacesMultiselect.getSelectedValues();
        parsedSpaces = multiselectValuesToSpacesObject(selectedSpaces);
    } else {
        const spacesInput = document.getElementById('add-task-spaces')?.value || '';
        parsedSpaces = parseSpacesInput(spacesInput);
    }
    const finalNotes = combineNotesAndTags(cleanNotesInput, selectedTags, parsedSpaces);

    const payload = {
        title: title,
        account_id: document.getElementById('add-task-account').value,
        list_title: document.getElementById('add-task-list').value,
        priority: document.getElementById('add-task-priority').value,
        status: document.getElementById('add-task-status').value,
        due: document.getElementById('add-task-due').value || null,
        notes: finalNotes
    };

    try {
        const basePath = window.GTASKS_BASE_PATH || '';
        let response = await fetch(`${basePath}/api/tasks`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (response.status === 405 || response.status === 404) {
            response = await fetch(`/api/tasks`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
        }

        const data = await response.json();
        if (data.success) {
            const msg = data.synced_to_google ? 'Task created & synced to Google Tasks ✅' : 'Task created locally ✅';
            showNotification(msg, 'success');
            closeAddModal();
            if (typeof window.loadDashboard === 'function') {
                window.loadDashboard();
            } else if (typeof window.loadTasks === 'function') {
                window.loadTasks(window.currentAccountId);
            }
        } else {
            showNotification(data.error || 'Failed to create task', 'error');
        }
    } catch (error) {
        console.error('Error creating task:', error);
        showNotification('Error creating task', 'error');
    } finally {
        if (saveBtn) {
            saveBtn.disabled = false;
            saveBtn.innerHTML = originalBtnHtml;
        }
    }
}

function openEditModal(taskId) {
    const tasks = (typeof dashboardData !== 'undefined' && dashboardData.tasks) ? dashboardData.tasks : [];
    let task = tasks.find(t => t.id === taskId);
    if (!task && window._allLoadedTasks) {
        task = window._allLoadedTasks.find(t => t.id === taskId);
    }
    if (!task) return;

    window.editingTaskId = taskId;

    // Parse raw notes to extract cleanNotes, tags, and spaces
    const rawNotes = task.notes || task.description || '';
    const { cleanNotes, tags: footerTags, spaces: extractedSpaces } = splitNotesAndTags(rawNotes);
    const taskSpaces = (task.spaces && Object.keys(task.spaces).length > 0) ? task.spaces : extractedSpaces;

    document.getElementById('edit-task-title').value = task.title || '';
    document.getElementById('edit-task-priority').value = task.calculated_priority || task.priority || 'medium';
    document.getElementById('edit-task-status').value = task.status || 'pending';
    document.getElementById('edit-task-notes').value = cleanNotes;
    const editSpacesEl = document.getElementById('edit-task-spaces');
    if (editSpacesEl) {
        editSpacesEl.value = formatSpacesForInput(taskSpaces);
    }

    // Initialize or refresh tags multiselect for Edit modal
    initModalTagSelectors();
    const activeTags = new Set(footerTags);
    if (task.tags && Array.isArray(task.tags)) {
        task.tags.forEach(t => { if (isValidTag(t)) activeTags.add(t); });
    }
    if (task.hybrid_tags) {
        (task.hybrid_tags.bracket || []).forEach(t => { if (isValidTag(t)) activeTags.add(t); });
        (task.hybrid_tags.hash || []).forEach(t => { if (isValidTag(t)) activeTags.add(t); });
        (task.hybrid_tags.user || []).forEach(t => { if (isValidTag(t)) activeTags.add(t); });
    }

    if (editTaskTagsMultiselect) {
        const allTags = getTagsWithCounts(tasks);
        editTaskTagsMultiselect.setOptions(allTags);
        editTaskTagsMultiselect.setSelectedValues(Array.from(activeTags));
    }

    if (editTaskSpacesMultiselect) {
        editTaskSpacesMultiselect.setOptions(getSpacesWithCounts(tasks));
        editTaskSpacesMultiselect.setSelectedValues(spacesObjectToMultiselectValues(taskSpaces));
    }

    // Populate list dropdown with all available lists
    const listSelect = document.getElementById('edit-task-list');
    listSelect.innerHTML = '';
    const availableLists = new Set();
    (window.allGoogleLists || []).forEach(l => { if (l && l.title) availableLists.add(l.title); });
    (typeof dashboardData !== 'undefined' && dashboardData.lists ? dashboardData.lists : []).forEach(l => { if (l) availableLists.add(l); });
    (typeof dashboardData !== 'undefined' && dashboardData.tasks ? dashboardData.tasks : []).forEach(t => { if (t.list_title) availableLists.add(t.list_title); });
    if (task.list_title) availableLists.add(task.list_title);
    if (availableLists.size === 0) availableLists.add('My Tasks');

    Array.from(availableLists).sort().forEach(listTitle => {
        const opt = document.createElement('option');
        opt.value = listTitle;
        opt.textContent = listTitle;
        if (listTitle === task.list_title) opt.selected = true;
        listSelect.appendChild(opt);
    });

    // Reset to edit tab
    switchNotesTab('edit');

    const modal = document.getElementById('edit-task-modal');
    if (modal) {
        modal.classList.add('active');
    }
}

function closeEditModal() {
    const modal = document.getElementById('edit-task-modal');
    if (modal) {
        modal.classList.remove('active');
        modal.classList.remove('is-fullscreen');
        const modalContent = modal.querySelector('.modal-content');
        if (modalContent) modalContent.classList.remove('is-fullscreen');
        if (typeof updateFullscreenIcons === 'function') updateFullscreenIcons(modal, false);
    }
    document.body.classList.remove('modal-fullscreen-active');
    window.editingTaskId = null;
}

async function saveTaskEdit() {
    const taskId = window.editingTaskId;
    if (!taskId) return;

    const saveBtn = document.getElementById('edit-task-save-btn');
    const originalBtnHtml = saveBtn ? saveBtn.innerHTML : '<i class="fas fa-save"></i> <span>Save Changes</span>';

    if (saveBtn) {
        saveBtn.disabled = true;
        saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> <span>Saving...</span>';
    }

    const cleanNotesInput = document.getElementById('edit-task-notes').value;
    const selectedTags = editTaskTagsMultiselect ? editTaskTagsMultiselect.getSelectedValues() : [];
    let parsedSpaces = {};
    if (editTaskSpacesMultiselect) {
        const selectedSpaces = editTaskSpacesMultiselect.getSelectedValues();
        parsedSpaces = multiselectValuesToSpacesObject(selectedSpaces);
    } else {
        const spacesInput = document.getElementById('edit-task-spaces')?.value || '';
        parsedSpaces = parseSpacesInput(spacesInput);
    }
    const finalNotes = combineNotesAndTags(cleanNotesInput, selectedTags, parsedSpaces);

    const payload = {
        title: document.getElementById('edit-task-title').value,
        priority: document.getElementById('edit-task-priority').value,
        status: document.getElementById('edit-task-status').value,
        notes: finalNotes,
        list_title: document.getElementById('edit-task-list').value
    };

    try {
        const basePath = window.GTASKS_BASE_PATH || '';
        const apiPath = `${basePath}/api/tasks/${taskId}`;
        let response = await fetch(apiPath, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (response.status === 405 || response.status === 404) {
            // BASE_PATH not recognized, try root-level API
            const fallbackPath = `/api/tasks/${taskId}`;
            response = await fetch(fallbackPath, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
        }

        const data = await response.json();
        if (data.success) {
            const msg = data.synced_to_google ? 'Task updated & moved/synced to Google Tasks ✅' : 'Task updated ✅';
            showNotification(msg, 'success');
            closeEditModal();
            if (typeof window.loadDashboard === 'function') {
                window.loadDashboard();
            } else if (typeof window.loadTasks === 'function') {
                window.loadTasks(window.currentAccountId);
            }
        } else {
            showNotification('Failed to update task', 'error');
        }
    } catch (error) {
        console.error('Error updating task:', error);
        showNotification('Error updating task', 'error');
    } finally {
        if (saveBtn) {
            saveBtn.disabled = false;
            saveBtn.innerHTML = originalBtnHtml;
        }
    }
}

function switchNotesTab(tab) {
    const tabs = document.querySelectorAll('#edit-task-modal .edit-notes-tab');
    tabs.forEach(t => t.classList.toggle('active', t.dataset.tab === tab));

    const textarea = document.getElementById('edit-task-notes');
    const preview = document.getElementById('edit-notes-preview');

    if (tab === 'preview') {
        textarea.style.display = 'none';
        preview.style.display = 'block';
        if (typeof marked !== 'undefined') {
            preview.innerHTML = marked.parse(textarea.value || '');
        } else {
            preview.textContent = textarea.value;
        }
    } else {
        textarea.style.display = 'block';
        preview.style.display = 'none';
    }
}

// Utility: escape HTML
function escapeHtml(text) {
    if (!text) return '';
    return String(text)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

// Utility: syntax highlight JSON string
function syntaxHighlightJson(jsonString) {
    if (!jsonString) return '';
    const escaped = jsonString
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
    return escaped.replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g, function (match) {
        let cls = 'json-number';
        if (/^"/.test(match)) {
            if (/:$/.test(match.trim())) {
                cls = 'json-key';
            } else {
                cls = 'json-string';
            }
        } else if (/true|false/.test(match)) {
            cls = 'json-boolean';
        } else if (/null/.test(match)) {
            cls = 'json-null';
        }
        return `<span class="${cls}">${match}</span>`;
    });
}

// Fullscreen helper to sync all expand/compress icons, labels, and aria attributes
export function updateFullscreenIcons(modal, isFullscreen) {
    if (!modal) return;
    const expandIcons = modal.querySelectorAll('.fa-expand, .fa-compress');
    expandIcons.forEach(icon => {
        if (isFullscreen) {
            icon.classList.remove('fa-expand');
            icon.classList.add('fa-compress');
        } else {
            icon.classList.remove('fa-compress');
            icon.classList.add('fa-expand');
        }
    });

    const expandTexts = modal.querySelectorAll('.fullscreen-btn-text');
    expandTexts.forEach(txt => {
        txt.textContent = isFullscreen ? 'Exit Full Screen' : 'Full Screen';
    });

    const expandBtns = modal.querySelectorAll('.btn-fullscreen-toggle, .modal-expand-btn');
    expandBtns.forEach(btn => {
        btn.setAttribute('title', isFullscreen ? 'Exit full screen' : 'Toggle full screen');
        btn.setAttribute('aria-label', isFullscreen ? 'Exit full screen' : 'Toggle full screen');
    });
}

// Universal modal fullscreen toggle (Quick View, Edit Task, Add Task)
export function toggleModalFullscreen(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) return false;
    const modalContent = modal.querySelector('.modal-content');
    if (!modalContent) return false;

    const isFullscreen = modalContent.classList.toggle('is-fullscreen');
    if (isFullscreen) {
        modal.classList.add('is-fullscreen');
        document.body.classList.add('modal-fullscreen-active');
    } else {
        modal.classList.remove('is-fullscreen');
        document.body.classList.remove('modal-fullscreen-active');
    }

    updateFullscreenIcons(modal, isFullscreen);
    return isFullscreen;
}

// Quick View Fullscreen
export function toggleQuickViewFullscreen() {
    return toggleModalFullscreen('quick-view-modal');
}

// Edit Modal Fullscreen
export function toggleEditModalFullscreen() {
    return toggleModalFullscreen('edit-task-modal');
}

// Add Modal Fullscreen
export function toggleAddModalFullscreen() {
    return toggleModalFullscreen('add-task-modal');
}

// Format JSON in notes textarea
export function formatJsonInTextarea(textareaId) {
    const textarea = document.getElementById(textareaId);
    if (!textarea) return;
    const rawVal = textarea.value.trim();
    if (!rawVal) {
        showNotification('No notes content to format', 'info');
        return;
    }

    try {
        const parsed = JSON.parse(rawVal);
        textarea.value = JSON.stringify(parsed, null, 2);
        showNotification('JSON formatted successfully! ✨', 'success');
        return;
    } catch (e) {
        const match = rawVal.match(/(\{[\s\S]*\}|\[[\s\S]*\])/);
        if (match) {
            try {
                const parsed = JSON.parse(match[0]);
                const formatted = JSON.stringify(parsed, null, 2);
                textarea.value = rawVal.replace(match[0], formatted);
                showNotification('Embedded JSON formatted! ✨', 'success');
                return;
            } catch (err) {
                // Not valid JSON
            }
        }
        showNotification('Notes content is not valid JSON', 'warning');
    }
}

export function formatEditTaskJson() {
    formatJsonInTextarea('edit-task-notes');
}

export function formatAddTaskJson() {
    formatJsonInTextarea('add-task-notes');
}

// Font size controls for Quick View notes
export function adjustQuickViewFontSize(delta) {
    const container = document.querySelector('.quick-view-notes-container');
    if (!container) return;
    const currentSize = parseFloat(window.getComputedStyle(container).fontSize) || 14;
    const newSize = Math.max(11, Math.min(24, currentSize + delta * 1.5));
    container.style.fontSize = `${newSize}px`;
    const pre = container.querySelector('pre');
    if (pre) pre.style.fontSize = `${Math.max(10, newSize * 0.9)}px`;
}

// Quick View Functions
export function openQuickView(taskId) {
    const tasks = (typeof dashboardData !== 'undefined' && dashboardData.tasks) ? dashboardData.tasks : [];
    let task = tasks.find(t => t.id === taskId);
    if (!task && window._allLoadedTasks) {
        task = window._allLoadedTasks.find(t => t.id === taskId);
    }
    if (!task) return;

    window.quickViewingTaskId = taskId;

    // Reset custom font size on open
    const notesContainer = document.querySelector('.quick-view-notes-container');
    if (notesContainer) {
        notesContainer.style.fontSize = '';
    }

    // Title
    const titleEl = document.getElementById('quick-view-title');
    if (titleEl) {
        titleEl.textContent = task.title || 'Untitled Task';
    }

    // Badges Row: Priority, Status, Date Status
    const badgesEl = document.getElementById('quick-view-badges');
    if (badgesEl) {
        const priorityClass = getPriorityClass(task.calculated_priority || task.priority);
        const priorityIcon = getPriorityIcon(task.calculated_priority || task.priority);
        const statusClass = getStatusClass(task.status);
        const dateStatus = getDateStatus(task.due);
        const dateBadge = getDateStatusBadge(dateStatus);
        const recurringBadgeHtml = task.is_recurring ? `
            <span class="task-badge badge-recurring badge-recurring-${task.recurrence_type || 'other'}" title="Recurring: ${task.recurrence_type || 'Repeating'}">
                <i class="fas fa-redo-alt"></i> ${(task.recurrence_type || 'recurring').toUpperCase()}
            </span>
        ` : '';

        badgesEl.innerHTML = `
            <span class="task-priority-badge ${priorityClass}">${priorityIcon} ${task.calculated_priority || task.priority || 'medium'}</span>
            <span class="task-status-badge ${statusClass}">${task.status || 'pending'}</span>
            ${recurringBadgeHtml}
            ${dateBadge}
        `;
    }

    // Meta Grid: List, Account, Due Date, Created Date
    const listEl = document.getElementById('quick-view-list');
    if (listEl) listEl.textContent = task.list_title || 'Tasks';

    const accountEl = document.getElementById('quick-view-account');
    if (accountEl) accountEl.textContent = task.account || window.currentAccountId || 'Default';

    const dueEl = document.getElementById('quick-view-due');
    if (dueEl) dueEl.textContent = task.due ? task.due : 'No due date';

    const createdEl = document.getElementById('quick-view-created');
    if (createdEl) {
        createdEl.textContent = task.created_at ? String(task.created_at).slice(0, 16).replace('T', ' ') : '-';
    }

    // Tags Section
    const tagsSection = document.getElementById('quick-view-tags-section');
    const tagsContainer = document.getElementById('quick-view-tags');
    if (tagsSection && tagsContainer) {
        const tags = getAllTags(task);
        if (tags && tags.length > 0) {
            tagsContainer.innerHTML = tags.map(tag => `<span class="quick-view-tag">[${escapeHtml(tag)}]</span>`).join(' ');
            tagsSection.style.display = 'block';
        } else {
            tagsContainer.innerHTML = '';
            tagsSection.style.display = 'none';
        }
    }

    // Notes / Details Section
    const rawNotes = task.notes || task.description || '';
    const { cleanNotes } = splitNotesAndTags(rawNotes);
    const notesContent = cleanNotes;
    const notesBody = document.getElementById('quick-view-notes-body');
    const formatBadge = document.getElementById('quick-view-format-badge');
    const copyBtn = document.getElementById('quick-view-copy-btn');

    window._currentQuickViewNotesText = notesContent;

    if (notesBody) {
        const trimmed = notesContent.trim();
        let isJson = false;

        if ((trimmed.startsWith('{') && trimmed.endsWith('}')) || (trimmed.startsWith('[') && trimmed.endsWith(']'))) {
            try {
                const parsed = JSON.parse(trimmed);
                const prettyJson = JSON.stringify(parsed, null, 2);
                window._currentQuickViewNotesText = prettyJson;
                isJson = true;
                const highlighted = syntaxHighlightJson(prettyJson);
                notesBody.innerHTML = `<pre class="json-code-block"><code>${highlighted}</code></pre>`;
                if (formatBadge) {
                    const lines = prettyJson.split('\n').length;
                    const sizeKb = (new Blob([prettyJson]).size / 1024).toFixed(1);
                    formatBadge.innerHTML = `<i class="fas fa-code"></i> JSON Payload (${lines} lines, ${sizeKb} KB)`;
                    formatBadge.style.display = 'inline-flex';
                }
            } catch (e) {
                isJson = false;
            }
        }

        if (!isJson) {
            if (!trimmed) {
                if (formatBadge) formatBadge.style.display = 'none';
                notesBody.innerHTML = '<div class="quick-view-empty-notes"><i class="fas fa-info-circle"></i> No notes or details provided for this task.</div>';
                if (copyBtn) copyBtn.style.display = 'none';
            } else {
                if (copyBtn) copyBtn.style.display = 'inline-flex';
                const lines = trimmed.split('\n').length;
                if (formatBadge) {
                    formatBadge.innerHTML = `<i class="fas fa-file-alt"></i> Notes (${lines} line${lines === 1 ? '' : 's'})`;
                    formatBadge.style.display = 'inline-flex';
                }
                if (typeof marked !== 'undefined') {
                    try {
                        notesBody.innerHTML = marked.parse(trimmed);
                        notesBody.querySelectorAll('a').forEach(a => {
                            a.setAttribute('target', '_blank');
                            a.setAttribute('rel', 'noopener noreferrer');
                        });
                    } catch (e) {
                        notesBody.innerHTML = `<p style="white-space: pre-wrap;">${escapeHtml(trimmed)}</p>`;
                    }
                } else {
                    notesBody.innerHTML = `<p style="white-space: pre-wrap;">${escapeHtml(trimmed)}</p>`;
                }
            }
        } else {
            if (copyBtn) copyBtn.style.display = 'inline-flex';
        }
    }

    // Dependencies Section
    const depsSection = document.getElementById('quick-view-deps-section');
    const depsList = document.getElementById('quick-view-deps-list');
    if (depsSection && depsList) {
        if (task.dependencies && task.dependencies.length > 0) {
            depsList.innerHTML = task.dependencies.map(dep => `
                <span class="dependency-badge" style="display: inline-flex; align-items: center; gap: 4px; padding: 2px 8px; border-radius: 6px; background: rgba(245, 158, 11, 0.1); color: #d97706; font-size: 0.8rem; margin-right: 6px;">
                    <i class="fas fa-link"></i> ${escapeHtml(dep)}
                </span>
            `).join('');
            depsSection.style.display = 'block';
        } else {
            depsList.innerHTML = '';
            depsSection.style.display = 'none';
        }
    }

    // Complete / Pending Button
    const completeBtn = document.getElementById('quick-view-complete-btn');
    if (completeBtn) {
        if (task.status === 'completed') {
            completeBtn.classList.add('completed');
            completeBtn.innerHTML = '<i class="fas fa-undo"></i> <span id="quick-view-complete-text">Mark Pending</span>';
        } else {
            completeBtn.classList.remove('completed');
            completeBtn.innerHTML = '<i class="fas fa-check"></i> <span id="quick-view-complete-text">Complete</span>';
        }
    }

    // Show modal
    const modal = document.getElementById('quick-view-modal');
    if (modal) {
        modal.classList.add('active');
    }
}

export function closeQuickView() {
    const modal = document.getElementById('quick-view-modal');
    if (modal) {
        modal.classList.remove('active');
        modal.classList.remove('is-fullscreen');
        const content = modal.querySelector('.modal-content');
        if (content) {
            content.classList.remove('is-fullscreen');
        }
        updateFullscreenIcons(modal, false);
    }
    document.body.classList.remove('modal-fullscreen-active');
    // Reset font size
    const notesContainer = document.querySelector('.quick-view-notes-container');
    if (notesContainer) {
        notesContainer.style.fontSize = '';
    }

    window.quickViewingTaskId = null;
}

export async function quickViewToggleComplete() {
    const taskId = window.quickViewingTaskId;
    if (!taskId) return;

    const tasks = (typeof dashboardData !== 'undefined' && dashboardData.tasks) ? dashboardData.tasks : [];
    const task = tasks.find(t => t.id === taskId);
    if (!task) return;

    if (task.status === 'completed') {
        try {
            const basePath = window.GTASKS_BASE_PATH || '';
            let response = await fetch(`${basePath}/api/tasks/${taskId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ status: 'pending' })
            });
            if (response.status === 405 || response.status === 404) {
                response = await fetch(`/api/tasks/${taskId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ status: 'pending' })
                });
            }
            const data = await response.json();
            if (data.success) {
                task.status = 'pending';
                showNotification('Task marked as pending ⭕', 'success');
                openQuickView(taskId);
                if (typeof window.filterTasks === 'function') {
                    window.filterTasks();
                }
            } else {
                showNotification(data.message || 'Failed to update task', 'error');
            }
        } catch (error) {
            console.error('Error reopening task:', error);
            showNotification('Error updating task', 'error');
        }
    } else {
        await completeTask(taskId);
        task.status = 'completed';
        openQuickView(taskId);
    }
}

export function quickViewEditTask() {
    const taskId = window.quickViewingTaskId;
    closeQuickView();
    if (taskId && typeof window.openEditModal === 'function') {
        window.openEditModal(taskId);
    }
}

export async function copyQuickViewNotes() {
    const text = window._currentQuickViewNotesText || '';
    if (!text) return;

    try {
        if (navigator.clipboard && navigator.clipboard.writeText) {
            await navigator.clipboard.writeText(text);
        } else {
            const textarea = document.createElement('textarea');
            textarea.value = text;
            document.body.appendChild(textarea);
            textarea.select();
            document.execCommand('copy');
            document.body.removeChild(textarea);
        }

        const copyBtn = document.getElementById('quick-view-copy-btn');
        if (copyBtn) {
            const origHtml = copyBtn.innerHTML;
            copyBtn.innerHTML = '<i class="fas fa-check"></i> Copied!';
            copyBtn.classList.add('copied');
            setTimeout(() => {
                copyBtn.innerHTML = origHtml;
                copyBtn.classList.remove('copied');
            }, 2000);
        }
    } catch (e) {
        console.error('Failed to copy to clipboard:', e);
    }
}

// Attach backdrop and escape key listeners for all modals
if (typeof document !== 'undefined') {
    document.addEventListener('click', (e) => {
        const qvModal = document.getElementById('quick-view-modal');
        if (qvModal && e.target === qvModal) {
            closeQuickView();
        }
        const editModal = document.getElementById('edit-task-modal');
        if (editModal && e.target === editModal && !editModal.classList.contains('is-fullscreen')) {
            closeEditModal();
        }
        const addModal = document.getElementById('add-task-modal');
        if (addModal && e.target === addModal && !addModal.classList.contains('is-fullscreen')) {
            closeAddModal();
        }
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            const qvModal = document.getElementById('quick-view-modal');
            if (qvModal && qvModal.classList.contains('active')) {
                if (qvModal.classList.contains('is-fullscreen') || (qvModal.querySelector('.modal-content') && qvModal.querySelector('.modal-content').classList.contains('is-fullscreen'))) {
                    toggleQuickViewFullscreen();
                } else {
                    closeQuickView();
                }
                return;
            }

            const editModal = document.getElementById('edit-task-modal');
            if (editModal && editModal.classList.contains('active')) {
                if (editModal.classList.contains('is-fullscreen') || (editModal.querySelector('.modal-content') && editModal.querySelector('.modal-content').classList.contains('is-fullscreen'))) {
                    toggleEditModalFullscreen();
                } else {
                    closeEditModal();
                }
                return;
            }

            const addModal = document.getElementById('add-task-modal');
            if (addModal && addModal.classList.contains('active')) {
                if (addModal.classList.contains('is-fullscreen') || (addModal.querySelector('.modal-content') && addModal.querySelector('.modal-content').classList.contains('is-fullscreen'))) {
                    toggleAddModalFullscreen();
                } else {
                    closeAddModal();
                }
                return;
            }
        }
    });
}

// Expose functions globally for inline HTML onclick handlers
window.toggleSidebar = toggleSidebar;
window.closeSidebar = closeSidebar;
window.closeSidebarOnMobile = closeSidebarOnMobile;
window.toggleFilterDrawer = toggleFilterDrawer;
window.openFilterDrawer = openFilterDrawer;
window.closeFilterDrawer = closeFilterDrawer;
window.setTaskViewMode = setTaskViewMode;
window.clearTaskSearch = clearTaskSearch;
window.removeFilterChip = removeFilterChip;
window.clearTasksFilters = clearTasksFilters;

// Modal & Fullscreen Exports
window.openQuickView = openQuickView;
window.closeQuickView = closeQuickView;
window.quickViewToggleComplete = quickViewToggleComplete;
window.quickViewEditTask = quickViewEditTask;
window.copyQuickViewNotes = copyQuickViewNotes;
window.toggleQuickViewFullscreen = toggleQuickViewFullscreen;
window.adjustQuickViewFontSize = adjustQuickViewFontSize;

window.openEditModal = openEditModal;
window.closeEditModal = closeEditModal;
window.saveTaskEdit = saveTaskEdit;
window.switchNotesTab = switchNotesTab;
window.toggleEditModalFullscreen = toggleEditModalFullscreen;
window.formatEditTaskJson = formatEditTaskJson;

window.openAddModal = openAddModal;
window.closeAddModal = closeAddModal;
window.saveNewTask = saveNewTask;
window.onAddAccountChange = onAddAccountChange;
window.switchAddNotesTab = switchAddNotesTab;
window.toggleAddModalFullscreen = toggleAddModalFullscreen;
window.formatAddTaskJson = formatAddTaskJson;

window.updateFullscreenIcons = updateFullscreenIcons;
window.toggleModalFullscreen = toggleModalFullscreen;
window.initModalTagSelectors = initModalTagSelectors;
window.getFlatSpacesAndSubspacesWithCounts = getFlatSpacesAndSubspacesWithCounts;
window.getUniqueSpacesWithCounts = getUniqueSpacesWithCounts;
window.getUniqueSubspacesWithCounts = getUniqueSubspacesWithCounts;
window.spacesObjectToMultiselectValues = spacesObjectToMultiselectValues;
window.multiselectValuesToSpacesObject = multiselectValuesToSpacesObject;

// Export for use in other modules
export default {
    initDashboard,
    loadDashboard,
    updateStats,
    showSection,
    toggleSidebar,
    closeSidebar,
    closeSidebarOnMobile,
    toggleFilterDrawer,
    openFilterDrawer,
    closeFilterDrawer,
    setTaskViewMode,
    clearTaskSearch,
    removeFilterChip,
    toggleFullscreen,
    switchAccount,
    loadTasks,
    filterTasks,
    loadHierarchy,
    simpleCacheRefresh,
    openQuickView,
    closeQuickView,
    quickViewToggleComplete,
    quickViewEditTask,
    copyQuickViewNotes,
    toggleQuickViewFullscreen,
    adjustQuickViewFontSize,
    openEditModal,
    closeEditModal,
    saveTaskEdit,
    toggleEditModalFullscreen,
    formatEditTaskJson,
    openAddModal,
    closeAddModal,
    saveNewTask,
    formatAddTaskJson,
    toggleModalFullscreen,
    initModalTagSelectors,
    getFlatSpacesAndSubspacesWithCounts,
    getUniqueSpacesWithCounts,
    getUniqueSubspacesWithCounts,
    spacesObjectToMultiselectValues,
    multiselectValuesToSpacesObject,
    populateSidebarTasksSubmenu,
    selectSidebarFilter,
    updateSidebarActiveItem,
    syncSidebarActiveFilter,
    filterSidebarListItems,
    clearSidebarQuickSearch,
    toggleSidebarSection,
    toggleSidebarTasksGroup,
    initBrowserTabs,
    renderBrowserTabs,
    switchBrowserTab,
    createBrowserTabPreset,
    promptCreateCustomBrowserTab,
    closeBrowserTab,
    startTabRename,
    finishTabRename,
    duplicateBrowserTab,
    scrollBrowserTabs,
    toggleNewTabMenu,
    closeNewTabMenu,
    updateBrowserTabBadges
};

// Initialize the dashboard when DOM is ready (or immediately if already parsed)
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        initDashboard();
    });
} else {
    initDashboard();
}
