/**
 * Sync Status Component
 * Manages remote sync status and operations in the dashboard header.
 */

const SyncStatus = {
    state: {
        connectedDBs: [],
        lastSync: null,
        syncInProgress: false,
        currentSyncId: null,
        localAvailable: true,
        error: null
    },

    /**
     * Initialize sync status component
     */
    init() {
        this.loadStatus();
        this.render();
        
        // Periodic status refresh
        setInterval(() => {
            if (!this.state.syncInProgress) {
                this.loadStatus();
            }
        }, 30000); // Every 30 seconds
    },

    /**
     * Load sync status from server
     */
    async loadStatus() {
        try {
            const response = await fetch('/api/remote/status');
            const data = await response.json();
            
            this.state.connectedDBs = data.connected_dbs || [];
            this.state.lastSync = data.last_sync;
            this.state.localAvailable = data.local_available;
            this.state.error = data.error;
            
            this.render();
        } catch (error) {
            console.error('Failed to load sync status:', error);
            this.state.error = 'Failed to load status';
            this.render();
        }
    },

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Sync button click
        const syncBtn = document.getElementById('sync-btn');
        if (syncBtn) {
            syncBtn.addEventListener('click', () => this.startSync());
        }
        
        // Add remote button
        const addBtn = document.getElementById('add-remote-btn');
        if (addBtn) {
            addBtn.addEventListener('click', () => this.showAddRemoteModal());
        }
    },

    /**
     * Start a sync operation
     */
    async startSync() {
        if (this.state.syncInProgress) return;
        
        try {
            this.state.syncInProgress = true;
            this.render();
            
            const response = await fetch('/api/remote/sync', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({})
            });
            
            const data = await response.json();
            this.state.currentSyncId = data.sync_id;
            
            // Poll for progress
            this.pollSyncProgress();
            
        } catch (error) {
            console.error('Failed to start sync:', error);
            this.state.syncInProgress = false;
            this.showNotification('Failed to start sync', 'error');
            this.render();
        }
    },

    /**
     * Poll sync progress
     */
    async pollSyncProgress() {
        if (!this.state.currentSyncId) return;
        
        try {
            const response = await fetch(`/api/remote/sync/progress/${this.state.currentSyncId}`);
            const progress = await response.json();
            
            this.renderProgress(progress);
            
            if (progress.status === 'completed' || progress.status === 'error') {
                this.state.syncInProgress = false;
                this.state.currentSyncId = null;
                
                if (progress.status === 'completed') {
                    this.showNotification('Sync completed successfully!', 'success');
                } else {
                    this.showNotification(`Sync failed: ${progress.message}`, 'error');
                }
                
                this.loadStatus(); // Reload status
            } else if (progress.status === 'running') {
                setTimeout(() => this.pollSyncProgress(), 1000);
            }
            
        } catch (error) {
            console.error('Failed to poll sync progress:', error);
            this.state.syncInProgress = false;
            this.render();
        }
    },

    /**
     * Show add remote database modal
     */
    showAddRemoteModal() {
        const modal = document.getElementById('add-remote-modal');
        if (modal) {
            modal.style.display = 'flex';
        }
    },

    /**
     * Add a new remote database
     */
    async addRemote(url, name) {
        try {
            const response = await fetch('/api/remote/add', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ url, name })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showNotification('Remote database added successfully!', 'success');
                this.loadStatus();
            } else {
                this.showNotification(`Failed to add database: ${data.error}`, 'error');
            }
        } catch (error) {
            console.error('Failed to add remote database:', error);
            this.showNotification('Failed to add remote database', 'error');
        }
    },

    /**
     * Remove a remote database
     */
    async removeRemote(url) {
        if (!confirm(`Are you sure you want to remove this remote database?`)) {
            return;
        }
        
        try {
            const response = await fetch('/api/remote/remove', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ url })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showNotification('Remote database removed', 'success');
                this.loadStatus();
            } else {
                this.showNotification(`Failed to remove: ${data.error}`, 'error');
            }
        } catch (error) {
            console.error('Failed to remove remote database:', error);
            this.showNotification('Failed to remove remote database', 'error');
        }
    },

    /**
     * Render sync status UI
     */
    render() {
        const container = document.getElementById('sync-status');
        if (!container) return;

        const { connectedDBs, lastSync, syncInProgress, localAvailable, error } = this.state;
        const isConnected = connectedDBs.some(db => db.status === 'connected');
        
        let statusHTML = `
            <div class="sync-status-container">
                <div class="sync-indicator ${isConnected ? 'connected' : (localAvailable ? 'local-only' : 'offline')}" 
                     title="${isConnected ? 'Connected to remote database' : (localAvailable ? 'Using local database only' : 'No database available')}">
                    <span class="status-dot"></span>
                    <span class="status-text">
                        ${isConnected ? 'Connected' : (localAvailable ? 'Local' : 'Offline')}
                    </span>
                </div>
                
                ${connectedDBs.length > 0 ? `
                    <div class="db-count" title="${connectedDBs.length} remote database(s) configured">
                        ${connectedDBs.filter(db => db.status === 'connected').length} active
                    </div>
                ` : `
                    <div class="db-count no-db">No remote DB</div>
                `}
                
                ${lastSync ? `
                    <div class="last-sync" title="Last sync: ${lastSync}">
                        ${this.formatTimeAgo(lastSync)}
                    </div>
                ` : ''}
                
                <button id="sync-btn" class="sync-button ${syncInProgress ? 'syncing' : ''}" 
                        ${syncInProgress ? 'disabled' : ''}>
                    ${syncInProgress ? '⏳ Syncing...' : '🔄 Sync'}
                </button>
                
                <button id="add-remote-btn" class="add-remote-button" title="Add remote database">
                    ➕
                </button>
            </div>
            
            ${!localAvailable ? `
                <div class="sync-warning">
                    ⚠️ Using remote database (no local data)
                </div>
            ` : ''}
            
            ${error ? `
                <div class="sync-error">
                    ⚠️ ${error}
                </div>
            ` : ''}
        `;
        
        container.innerHTML = statusHTML;
        
        // Re-attach event listeners
        this.setupEventListeners();
        
        // Setup add remote modal handlers
        this.setupAddRemoteModal();
    },

    /**
     * Setup add remote modal event handlers
     */
    setupAddRemoteModal() {
        const modal = document.getElementById('add-remote-modal');
        const closeBtn = modal?.querySelector('.modal-close');
        const cancelBtn = modal?.querySelector('.modal-cancel');
        const saveBtn = modal?.querySelector('.modal-save');
        const form = modal?.querySelector('form');
        
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                modal.style.display = 'none';
            });
        }
        
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => {
                modal.style.display = 'none';
            });
        }
        
        if (saveBtn && form) {
            saveBtn.addEventListener('click', () => {
                const url = form.querySelector('input[name="url"]').value;
                const name = form.querySelector('input[name="name"]').value;
                
                if (url) {
                    this.addRemote(url, name);
                    modal.style.display = 'none';
                    form.reset();
                }
            });
        }
        
        // Close on outside click
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    modal.style.display = 'none';
                }
            });
        }
    },

    /**
     * Render sync progress overlay
     */
    renderProgress(progress) {
        let overlay = document.getElementById('sync-progress-overlay');
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.id = 'sync-progress-overlay';
            overlay.className = 'sync-progress-overlay';
            document.body.appendChild(overlay);
        }
        
        overlay.innerHTML = `
            <div class="sync-progress-content">
                <h3>${progress.message}</h3>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${progress.percentage}%"></div>
                </div>
                <p>${progress.percentage}% complete</p>
            </div>
        `;
        
        overlay.style.display = 'flex';
    },

    /**
     * Format time ago from timestamp
     */
    formatTimeAgo(timestamp) {
        const now = new Date();
        const time = new Date(timestamp);
        const diff = Math.floor((now - time) / 1000);
        
        if (diff < 60) return 'Just now';
        if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
        if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
        return `${Math.floor(diff / 86400)}d ago`;
    },

    /**
     * Show notification
     */
    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <span>${message}</span>
            <button class="notification-close">×</button>
        `;
        
        // Add to page
        let container = document.getElementById('notification-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'notification-container';
            document.body.appendChild(container);
        }
        
        container.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            notification.style.opacity = '0';
            setTimeout(() => notification.remove(), 300);
        }, 5000);
        
        // Close button
        notification.querySelector('.notification-close').addEventListener('click', () => {
            notification.remove();
        });
    }
};

// Export for use
window.SyncStatus = SyncStatus;
