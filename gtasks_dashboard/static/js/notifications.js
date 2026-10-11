/**
 * GTasks Dashboard - Notifications Controller
 */

let notificationsList = [];
let unreadCount = 0;
let pollTimer = null;

export async function initNotifications() {
    console.log('[Notifications] Initializing Notification System...');

    // Close notifications when clicking outside
    document.addEventListener('click', (e) => {
        const desktopDropdown = document.getElementById('notif-dropdown-desktop');
        const mobileDropdown = document.getElementById('notif-dropdown-mobile');
        const desktopContainer = document.getElementById('notif-bell-container-desktop');
        const mobileContainer = document.getElementById('notif-bell-container-mobile');

        if (desktopDropdown && desktopContainer && !desktopContainer.contains(e.target)) {
            desktopDropdown.classList.remove('show');
        }
        if (mobileDropdown && mobileContainer && !mobileContainer.contains(e.target)) {
            mobileDropdown.classList.remove('show');
        }
    });

    // Initial load & check
    await checkTaskAlerts();
    await fetchNotifications();

    // Setup periodic polling every 60 seconds
    if (pollTimer) clearInterval(pollTimer);
    pollTimer = setInterval(fetchNotifications, 60000);
}

export async function toggleNotifications(type = 'desktop') {
    const dropdown = document.getElementById(`notif-dropdown-${type}`);
    if (!dropdown) return;

    const isVisible = dropdown.classList.contains('show');
    if (isVisible) {
        dropdown.classList.remove('show');
    } else {
        dropdown.classList.add('show');
        await fetchNotifications();
    }
}

export async function fetchNotifications() {
    try {
        const basePath = window.GTASKS_BASE_PATH || '';
        const res = await fetch(`${basePath}/api/notifications`);
        const json = await res.json();

        if (json.success && json.data) {
            notificationsList = json.data.notifications || [];
            unreadCount = json.data.unread_count || 0;
            renderNotificationBadges();
            renderNotificationItems('desktop');
            renderNotificationItems('mobile');
        }
    } catch (e) {
        console.warn('[Notifications] Failed to fetch notifications:', e);
    }
}

export async function checkTaskAlerts() {
    try {
        const basePath = window.GTASKS_BASE_PATH || '';
        const res = await fetch(`${basePath}/api/notifications/check`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        const json = await res.json();
        if (json.success && json.data) {
            unreadCount = json.data.unread_count || 0;
            renderNotificationBadges();
        }
    } catch (e) {
        console.warn('[Notifications] Alert scan error:', e);
    }
}

export async function markNotificationAsRead(notifId = null) {
    try {
        const basePath = window.GTASKS_BASE_PATH || '';
        const res = await fetch(`${basePath}/api/notifications/read`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id: notifId })
        });
        const json = await res.json();
        if (json.success) {
            unreadCount = json.unread_count || 0;
            if (notifId) {
                const item = notificationsList.find(n => n.id === notifId);
                if (item) item.read = 1;
            } else {
                notificationsList.forEach(n => n.read = 1);
            }
            renderNotificationBadges();
            renderNotificationItems('desktop');
            renderNotificationItems('mobile');
        }
    } catch (e) {
        console.error('[Notifications] Failed to mark as read:', e);
    }
}

export async function clearNotifications(notifId = null) {
    try {
        const basePath = window.GTASKS_BASE_PATH || '';
        const res = await fetch(`${basePath}/api/notifications/clear`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id: notifId })
        });
        const json = await res.json();
        if (json.success) {
            unreadCount = json.unread_count || 0;
            if (notifId) {
                notificationsList = notificationsList.filter(n => n.id !== notifId);
            } else {
                notificationsList = [];
            }
            renderNotificationBadges();
            renderNotificationItems('desktop');
            renderNotificationItems('mobile');
        }
    } catch (e) {
        console.error('[Notifications] Failed to clear notifications:', e);
    }
}

function renderNotificationBadges() {
    const badges = document.querySelectorAll('.notif-badge');
    badges.forEach(b => {
        if (unreadCount > 0) {
            b.textContent = unreadCount > 99 ? '99+' : unreadCount;
            b.style.display = 'inline-block';
        } else {
            b.style.display = 'none';
        }
    });
}

function renderNotificationItems(type = 'desktop') {
    const listEl = document.getElementById(`notif-list-${type}`);
    if (!listEl) return;

    if (!notificationsList || notificationsList.length === 0) {
        listEl.innerHTML = `
            <div class="notif-empty">
                <i class="fas fa-bell-slash" style="font-size: 2rem; opacity: 0.3; margin-bottom: 0.5rem;"></i>
                <p>No notifications yet</p>
                <span style="font-size: 0.75rem; opacity: 0.7;">Overdue tasks & alerts will appear here</span>
            </div>
        `;
        return;
    }

    let html = '';
    notificationsList.forEach(n => {
        const unreadClass = !n.read ? 'unread' : '';
        const sevClass = n.severity || 'info';
        const icon = n.type === 'overdue' ? 'fa-exclamation-circle' :
                     n.type === 'due_today' ? 'fa-clock' : 'fa-info-circle';

        const timeStr = n.created_at ? new Date(n.created_at).toLocaleString([], {
            month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
        }) : '';

        html += `
            <div class="notif-item ${unreadClass}" onclick="window.onNotificationClicked('${n.id}', '${n.task_id || ''}')">
                <div class="notif-icon ${sevClass}">
                    <i class="fas ${icon}"></i>
                </div>
                <div class="notif-content">
                    <div class="notif-title">${escapeHtml(n.title)}</div>
                    <div class="notif-message">${escapeHtml(n.message)}</div>
                    <div class="notif-time">${timeStr}</div>
                </div>
            </div>
        `;
    });

    listEl.innerHTML = html;
}

function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

window.onNotificationClicked = function(notifId, taskId) {
    markNotificationAsRead(notifId);
    if (taskId && typeof window.openTaskDetails === 'function') {
        window.openTaskDetails(taskId);
    }
};

// Global exports
window.initNotifications = initNotifications;
window.toggleNotifications = toggleNotifications;
window.markNotificationAsRead = markNotificationAsRead;
window.clearNotifications = clearNotifications;
window.checkTaskAlerts = checkTaskAlerts;
