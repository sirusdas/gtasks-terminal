/**
 * GTasks Dashboard - Debugger & Diagnostics Controller
 */

let debugPollingTimer = null;
let autoScrollLogs = true;
let currentLogLevel = 'DEBUG';

export async function initDebugger() {
    console.log('[Debugger] Initializing Real-time Debugger System...');
}

export async function openDebugger() {
    const modal = document.getElementById('debugger-modal');
    if (!modal) return;
    modal.classList.add('active');

    // Fetch initial diagnostics and logs
    await refreshDiagnostics();
    await fetchLogs();

    // Start auto polling logs every 3 seconds while modal is open
    if (debugPollingTimer) clearInterval(debugPollingTimer);
    debugPollingTimer = setInterval(fetchLogs, 3000);
}

export function closeDebugger() {
    const modal = document.getElementById('debugger-modal');
    if (modal) modal.classList.remove('active');
    if (debugPollingTimer) {
        clearInterval(debugPollingTimer);
        debugPollingTimer = null;
    }
}

export async function refreshDiagnostics() {
    try {
        const basePath = window.GTASKS_BASE_PATH || '';
        const res = await fetch(`${basePath}/api/debug/diagnostics`);
        const json = await res.json();

        if (json.success && json.data) {
            renderDiagnostics(json.data);
        }
    } catch (e) {
        console.error('[Debugger] Failed to load diagnostics:', e);
    }
}

function renderDiagnostics(data) {
    const db = data.database || {};
    const log = data.log_file || {};
    const state = data.dashboard_state || {};

    const dbStatusEl = document.getElementById('debug-diag-db-status');
    const dbSizeEl = document.getElementById('debug-diag-db-size');
    const tasksCountEl = document.getElementById('debug-diag-tasks-count');
    const logSizeEl = document.getElementById('debug-diag-log-size');

    if (dbStatusEl) {
        dbStatusEl.innerHTML = db.healthy 
            ? '<span class="debugger-badge healthy">HEALTHY (OK)</span>' 
            : '<span class="debugger-badge error">CHECK FAILED</span>';
    }

    if (dbSizeEl) {
        const kb = (db.size_bytes / 1024).toFixed(1);
        dbSizeEl.textContent = `${kb} KB`;
    }

    if (tasksCountEl) {
        const total = (db.tables && db.tables.tasks !== undefined) ? db.tables.tasks : state.cached_tasks_total;
        tasksCountEl.textContent = `${total} tasks`;
    }

    if (logSizeEl) {
        const kb = (log.size_bytes / 1024).toFixed(1);
        logSizeEl.textContent = `${kb} KB`;
    }
}

export async function fetchLogs() {
    try {
        const basePath = window.GTASKS_BASE_PATH || '';
        const levelSel = document.getElementById('debug-log-level-filter');
        const searchInput = document.getElementById('debug-log-search');

        const level = levelSel ? levelSel.value : '';
        const search = searchInput ? searchInput.value.trim() : '';

        let url = `${basePath}/api/debug/logs?limit=200`;
        if (level && level !== 'ALL') url += `&level=${encodeURIComponent(level)}`;
        if (search) url += `&search=${encodeURIComponent(search)}`;

        const res = await fetch(url);
        const json = await res.json();

        if (json.success && json.data) {
            renderLogs(json.data.logs || []);
        }
    } catch (e) {
        console.error('[Debugger] Failed to fetch logs:', e);
    }
}

function renderLogs(logs) {
    const terminal = document.getElementById('debugger-terminal-body');
    if (!terminal) return;

    if (!logs || logs.length === 0) {
        terminal.innerHTML = '<div style="color: #64748b; font-style: italic;">No logs recorded yet.</div>';
        return;
    }

    let html = '';
    logs.forEach(line => {
        let cls = 'INFO';
        if (line.includes(' - ERROR - ')) cls = 'ERROR';
        else if (line.includes(' - WARNING - ') || line.includes(' - WARN - ')) cls = 'WARNING';
        else if (line.includes(' - DEBUG - ')) cls = 'DEBUG';

        html += `<div class="log-line ${cls}">${escapeHtml(line)}</div>`;
    });

    terminal.innerHTML = html;

    if (autoScrollLogs) {
        terminal.scrollTop = terminal.scrollHeight;
    }
}

export async function toggleDebugLevel() {
    const nextLevel = currentLogLevel === 'DEBUG' ? 'INFO' : 'DEBUG';
    try {
        const basePath = window.GTASKS_BASE_PATH || '';
        const res = await fetch(`${basePath}/api/debug/toggle`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ level: nextLevel })
        });
        const json = await res.json();
        if (json.success) {
            currentLogLevel = json.active_level;
            updateDebugButtonUI();
            await fetchLogs();
        }
    } catch (e) {
        alert('Failed to switch log level: ' + e.message);
    }
}

function updateDebugButtonUI() {
    const btn = document.getElementById('debug-toggle-btn');
    if (btn) {
        btn.textContent = currentLogLevel === 'DEBUG' ? 'Debug Mode: ON' : 'Debug Mode: OFF';
        btn.style.color = currentLogLevel === 'DEBUG' ? '#ef4444' : '#64748b';
    }
}

export async function clearAllLogs() {
    if (!confirm('Are you sure you want to clear/truncate gtasks.log?')) return;
    try {
        const basePath = window.GTASKS_BASE_PATH || '';
        const res = await fetch(`${basePath}/api/debug/clear-logs`, { method: 'POST' });
        const json = await res.json();
        if (json.success) {
            await fetchLogs();
            await refreshDiagnostics();
        } else {
            alert(json.message);
        }
    } catch (e) {
        alert('Failed to clear logs: ' + e.message);
    }
}

export function toggleAutoScroll() {
    autoScrollLogs = !autoScrollLogs;
    const btn = document.getElementById('debug-autoscroll-toggle');
    if (btn) {
        btn.textContent = `Auto-Scroll: ${autoScrollLogs ? 'ON' : 'OFF'}`;
    }
}

function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

// Global window bindings
window.initDebugger = initDebugger;
window.openDebugger = openDebugger;
window.closeDebugger = closeDebugger;
window.refreshDiagnostics = refreshDiagnostics;
window.fetchLogs = fetchLogs;
window.toggleDebugLevel = toggleDebugLevel;
window.clearAllLogs = clearAllLogs;
window.toggleAutoScroll = toggleAutoScroll;
