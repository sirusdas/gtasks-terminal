/**
 * Constants and Configuration
 * Global constants and configuration for the dashboard
 */

// Color scale for hierarchy visualization
export const colorScale = {
    'meta': '#8b5cf6',
    'priority': {
        'critical': '#ef4444',
        'high': '#f97316',
        'medium': '#eab308',
        'low': '#6b7280'
    },
    'category': '#3b82f6',
    'tag': '#10b981',
    'account': '#8b5cf6'
};

// Priority order for sorting
export const priorityOrder = {
    'critical': 0,
    'high': 1,
    'medium': 2,
    'low': 3
};

// Default configuration
export const defaultConfig = {
    refreshInterval: 60000, // 1 minute
    defaultView: 'dashboard',
    autoRefreshEnabled: false,
    hideDeletedEnabled: false,
    darkModeEnabled: false
};

// Refresh interval options
export const refreshIntervalOptions = [
    { value: '30', label: '30 seconds' },
    { value: '60', label: '1 minute' },
    { value: '300', label: '5 minutes' },
    { value: '600', label: '10 minutes' }
];

// Category keywords for task categorization
export const categoryKeywords = {
    'development': ['api', 'frontend', 'backend', 'code', 'implementation', 'feature', 'bug'],
    'testing': ['test', 'qa', 'validation', 'verification'],
    'infrastructure': ['deploy', 'setup', 'config', 'infrastructure', 'environment', 'devops'],
    'documentation': ['doc', 'documentation', 'readme', 'guide'],
    'meeting': ['meeting', 'review', 'discussion', 'standup'],
    'research': ['research', 'investigate', 'explore', 'analysis']
};

// Storage keys
export const storageKeys = {
    darkMode: 'darkMode',
    autoRefresh: 'autoRefresh',
    refreshInterval: 'refreshInterval',
    defaultView: 'defaultView',
    hideDeleted: 'hideDeleted'
};

// Local storage helpers
export const storage = {
    get(key, defaultValue = null) {
        try {
            const value = localStorage.getItem(key);
            if (value === null) return defaultValue;
            // Try to parse as JSON, if it fails, return the string value
            try {
                return JSON.parse(value);
            } catch {
                // Value is a plain string, return it as-is
                return value;
            }
        } catch (e) {
            console.warn(`Error reading from localStorage: ${key}`, e);
            return defaultValue;
        }
    },
    
    set(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
        } catch (e) {
            console.warn(`Error writing to localStorage: ${key}`, e);
        }
    },
    
    remove(key) {
        try {
            localStorage.removeItem(key);
        } catch (e) {
            console.warn(`Error removing from localStorage: ${key}`, e);
        }
    }
};

// API endpoints
export const apiEndpoints = {
    data: '/api/data',
    hierarchy: '/api/hierarchy',
    hierarchyFiltered: '/api/hierarchy/filtered',
    accountsSwitch: (accountId) => `/api/accounts/${accountId}/switch`
};

// Event names for custom events
export const events = {
    DATA_LOADED: 'dashboard:dataLoaded',
    HIERARCHY_LOADED: 'dashboard:hierarchyLoaded',
    ACCOUNT_SWITCHED: 'dashboard:accountSwitched',
    DARK_MODE_TOGGLED: 'dashboard:darkModeToggled',
    TASKS_FILTERED: 'dashboard:tasksFiltered',
    NODE_SELECTED: 'dashboard:nodeSelected'
};

// Keyboard shortcuts
export const keyboardShortcuts = {
    toggleSidebar: { key: 'b', ctrlKey: true },
    toggleFullscreen: { key: 'f', ctrlKey: true },
    escape: { key: 'Escape' }
};

// UI defaults
export const uiDefaults = {
    nodeLabelMaxLength: 5,
    minNodeSize: 8,
    maxNodeSize: 25,
    zoomMin: 0.1,
    zoomMax: 10,
    simulationAlphaTarget: 0.3,
    transitionDuration: 750
};

// Animation keyframes
export const animations = {
    fadeIn: 'fadeIn 0.3s ease',
    slideIn: 'slideIn 0.3s ease'
};
