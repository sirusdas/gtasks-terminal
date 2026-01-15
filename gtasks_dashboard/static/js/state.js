/**
 * State Management
 * Centralized state management for the dashboard
 */

import { storage, storageKeys, defaultConfig } from './constants.js';

// Global state object
const state = {
    // Data state
    dashboardData: {},
    hierarchyData: {},
    
    // UI state
    selectedAccount: null,
    isFullscreen: false,
    currentSection: 'dashboard',
    selectedNode: null,
    
    // Settings state
    settings: {
        autoRefreshEnabled: defaultConfig.autoRefreshEnabled,
        refreshInterval: defaultConfig.refreshInterval,
        defaultView: defaultConfig.defaultView,
        hideDeletedEnabled: defaultConfig.hideDeletedEnabled,
        darkModeEnabled: defaultConfig.darkModeEnabled
    },
    
    // Hierarchy filter state
    hierarchyFilters: {
        tagSearch: '',
        status: '',
        dateStart: '',
        dateEnd: ''
    },
    
    // Auto-refresh interval ID
    autoRefreshInterval: null,
    
    // D3 simulation reference
    simulation: null,
    
    // D3 zoom reference
    zoom: null,
    
    // SVG references
    svg: null,
    g: null
};

// State management functions
export const stateManager = {
    /**
     * Get the current state
     * @returns {Object} - The current state
     */
    getState() {
        return state;
    },
    
    /**
     * Get a specific state value
     * @param {string} key - The state key
     * @returns {*} - The state value
     */
    get(key) {
        return state[key];
    },
    
    /**
     * Set a state value
     * @param {string} key - The state key
     * @param {*} value - The value to set
     */
    set(key, value) {
        state[key] = value;
    },
    
    /**
     * Update multiple state values
     * @param {Object} updates - Object with key-value pairs to update
     */
    update(updates) {
        Object.assign(state, updates);
    },
    
    /**
     * Initialize state from localStorage
     */
    initFromStorage() {
        // Load settings from localStorage
        state.settings.autoRefreshEnabled = storage.get(storageKeys.autoRefresh, defaultConfig.autoRefreshEnabled);
        state.settings.refreshInterval = storage.get(storageKeys.refreshInterval, defaultConfig.refreshInterval);
        state.settings.defaultView = storage.get(storageKeys.defaultView, defaultConfig.defaultView);
        state.settings.hideDeletedEnabled = storage.get(storageKeys.hideDeleted, defaultConfig.hideDeletedEnabled);
        state.settings.darkModeEnabled = storage.get(storageKeys.darkMode, defaultConfig.darkModeEnabled) === 'enabled';
        
        // Apply dark mode if enabled
        if (state.settings.darkModeEnabled) {
            document.body.classList.add('dark-mode');
        }
    },
    
    /**
     * Save settings to localStorage
     */
    saveSettings() {
        storage.set(storageKeys.autoRefresh, state.settings.autoRefreshEnabled);
        storage.set(storageKeys.refreshInterval, state.settings.refreshInterval);
        storage.set(storageKeys.defaultView, state.settings.defaultView);
        storage.set(storageKeys.hideDeleted, state.settings.hideDeletedEnabled);
    },
    
    /**
     * Update a setting
     * @param {string} key - The setting key
     * @param {*} value - The setting value
     */
    updateSetting(key, value) {
        if (state.settings.hasOwnProperty(key)) {
            state.settings[key] = value;
            this.saveSettings();
        }
    },
    
    /**
     * Toggle dark mode
     */
    toggleDarkMode() {
        state.settings.darkModeEnabled = !state.settings.darkModeEnabled;
        document.body.classList.toggle('dark-mode', state.settings.darkModeEnabled);
        storage.set(storageKeys.darkMode, state.settings.darkModeEnabled ? 'enabled' : 'disabled');
    },
    
    /**
     * Initialize dark mode from storage
     */
    initDarkMode() {
        const savedDarkMode = storage.get(storageKeys.darkMode);
        if (savedDarkMode === 'enabled') {
            state.settings.darkModeEnabled = true;
            document.body.classList.add('dark-mode');
        }
    },
    
    /**
     * Start auto-refresh
     * @param {number} interval - The refresh interval in milliseconds
     */
    startAutoRefresh(interval) {
        this.stopAutoRefresh();
        
        state.autoRefreshInterval = setInterval(async () => {
            console.log('Auto-refreshing data...');
            const { loadDashboard } = await import('./dashboard.js');
            await loadDashboard();
        }, interval);
        
        console.log(`Auto-refresh started with interval: ${interval}ms`);
    },
    
    /**
     * Stop auto-refresh
     */
    stopAutoRefresh() {
        if (state.autoRefreshInterval) {
            clearInterval(state.autoRefreshInterval);
            state.autoRefreshInterval = null;
            console.log('Auto-refresh stopped');
        }
    },
    
    /**
     * Reset hierarchy filters
     */
    resetHierarchyFilters() {
        state.hierarchyFilters = {
            tagSearch: '',
            status: '',
            dateStart: '',
            dateEnd: ''
        };
    },
    
    /**
     * Update hierarchy filter
     * @param {string} key - The filter key
     * @param {*} value - The filter value
     */
    updateHierarchyFilter(key, value) {
        if (state.hierarchyFilters.hasOwnProperty(key)) {
            state.hierarchyFilters[key] = value;
        }
    },
    
    /**
     * Set selected node
     * @param {Object} node - The selected node
     */
    setSelectedNode(node) {
        state.selectedNode = node;
    },
    
    /**
     * Clear selected node
     */
    clearSelectedNode() {
        state.selectedNode = null;
    },
    
    /**
     * Toggle fullscreen mode
     */
    toggleFullscreen() {
        state.isFullscreen = !state.isFullscreen;
        const vizContainer = document.getElementById('viz-container');
        const exitButton = document.getElementById('fullscreen-exit');
        
        if (vizContainer && exitButton) {
            if (state.isFullscreen) {
                vizContainer.classList.add('fullscreen-mode');
                exitButton.style.display = 'block';
            } else {
                vizContainer.classList.remove('fullscreen-mode');
                exitButton.style.display = 'none';
            }
        }
        
        return state.isFullscreen;
    },
    
    /**
     * Set current section
     * @param {string} section - The section name
     */
    setCurrentSection(section) {
        state.currentSection = section;
    },
    
    /**
     * Set dashboard data
     * @param {Object} data - The dashboard data
     */
    setDashboardData(data) {
        state.dashboardData = data;
        state.selectedAccount = data.current_account || null;
    },
    
    /**
     * Set hierarchy data
     * @param {Object} data - The hierarchy data
     */
    setHierarchyData(data) {
        state.hierarchyData = data;
    },
    
    /**
     * Get hierarchy filter state
     * @returns {Object} - The hierarchy filter state
     */
    getHierarchyFilters() {
        return { ...state.hierarchyFilters };
    },
    
    /**
     * Get settings
     * @returns {Object} - The settings
     */
    getSettings() {
        return { ...state.settings };
    },
    
    /**
     * Store D3 simulation reference
     * @param {Object} simulation - The D3 simulation
     */
    storeSimulation(simulation) {
        state.simulation = simulation;
    },
    
    /**
     * Store D3 zoom reference
     * @param {Object} zoom - The D3 zoom
     */
    storeZoom(zoom) {
        state.zoom = zoom;
    },
    
    /**
     * Store SVG references
     * @param {Object} svg - The D3 SVG selection
     * @param {Object} g - The D3 g selection
     */
    storeSvgReferences(svg, g) {
        state.svg = svg;
        state.g = g;
    },
    
    /**
     * Get SVG references
     * @returns {Object} - The SVG references
     */
    getSvgReferences() {
        return { svg: state.svg, g: state.g };
    }
};

// Export state for backward compatibility
export const appState = state;
