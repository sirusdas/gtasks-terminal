/**
 * GTasks Dashboard - Reports & Analytics Controller
 */

// Active state
let reportTypes = {};
let currentReportData = null;
let currentReportType = 'rp1';
let completionTrendChart = null;
let distributionDoughnutChart = null;

/**
 * Initialize reports view
 */
export async function initReportsView() {
    console.log('[Reports] Initializing Reports & Analytics view...');
    
    // Sync account selector in reports view with global account
    populateReportsAccountSelector();
    
    // Fetch available report types
    await loadReportTypes();
    
    // Set default dates if empty
    setupDefaultDates();
    
    // Populate list & tag filter options from current dashboardData
    populateFilterOptions();
    
    // Generate default preset (Weekly Pulse)
    applyPreset('weekly');
}

/**
 * Populate account selector in reports section
 */
function populateReportsAccountSelector() {
    const sel = document.getElementById('reports-account-selector');
    if (!sel) return;
    
    const globalSel = document.getElementById('account-selector');
    if (globalSel && globalSel.options.length > 0) {
        sel.innerHTML = '<option value="all">All Accounts</option>';
        for (let opt of globalSel.options) {
            if (opt.value) {
                const optEl = document.createElement('option');
                optEl.value = opt.value;
                optEl.textContent = opt.textContent;
                if (opt.value === globalSel.value) {
                    optEl.selected = true;
                }
                sel.appendChild(optEl);
            }
        }
    }
}

/**
 * Setup default date values (last 30 days)
 */
function setupDefaultDates() {
    const startInput = document.getElementById('report-start-date');
    const endInput = document.getElementById('report-end-date');
    
    const end = new Date();
    const start = new Date();
    start.setDate(end.getDate() - 30);
    
    if (startInput && !startInput.value) {
        startInput.value = start.toISOString().split('T')[0];
    }
    if (endInput && !endInput.value) {
        endInput.value = end.toISOString().split('T')[0];
    }
}

/**
 * Populate list and tag dropdowns from dashboard state
 */
function populateFilterOptions() {
    const listSel = document.getElementById('report-list-filter');
    if (listSel && window.dashboardData && window.dashboardData.lists) {
        listSel.innerHTML = '<option value="all">All Lists</option>';
        window.dashboardData.lists.forEach(l => {
            const opt = document.createElement('option');
            opt.value = l.id;
            opt.textContent = l.title || l.name;
            listSel.appendChild(opt);
        });
    }

    const tagSel = document.getElementById('report-tag-filter');
    if (tagSel && window.dashboardData && window.dashboardData.tags) {
        tagSel.innerHTML = '<option value="">All Tags</option>';
        window.dashboardData.tags.forEach(t => {
            const opt = document.createElement('option');
            opt.value = t.name;
            opt.textContent = `${t.name} (${t.count || 0})`;
            tagSel.appendChild(opt);
        });
    }
}

/**
 * Load report types from backend
 */
async function loadReportTypes() {
    try {
        const basePath = window.GTASKS_BASE_PATH || '';
        const res = await fetch(`${basePath}/api/reports/types`);
        const json = await res.json();
        
        if (json.success && json.data) {
            reportTypes = json.data;
            const sel = document.getElementById('report-type-selector');
            if (sel) {
                sel.innerHTML = '';
                // Only show main codes rp1..rp10
                const keys = ['rp1', 'rp2', 'rp3', 'rp4', 'rp5', 'rp6', 'rp7', 'rp8', 'rp9', 'rp10'];
                keys.forEach(k => {
                    const r = reportTypes[k];
                    if (r) {
                        const opt = document.createElement('option');
                        opt.value = k;
                        opt.textContent = `${k.toUpperCase()} - ${r.name}`;
                        sel.appendChild(opt);
                    }
                });
            }
        }
    } catch (err) {
        console.error('[Reports] Error loading report types:', err);
    }
}

/**
 * Apply preset configurations
 */
export function applyPreset(presetName) {
    document.querySelectorAll('.preset-chip').forEach(c => c.classList.remove('active'));
    const activeChip = document.getElementById(`preset-${presetName}`);
    if (activeChip) activeChip.classList.add('active');

    const typeSel = document.getElementById('report-type-selector');
    const startInput = document.getElementById('report-start-date');
    const endInput = document.getElementById('report-end-date');
    const end = new Date();

    if (presetName === 'weekly') {
        if (typeSel) typeSel.value = 'rp1';
        const start = new Date();
        start.setDate(end.getDate() - 7);
        if (startInput) startInput.value = start.toISOString().split('T')[0];
        if (endInput) endInput.value = end.toISOString().split('T')[0];
    } else if (presetName === 'monthly') {
        if (typeSel) typeSel.value = 'rp1';
        const start = new Date();
        start.setDate(end.getDate() - 30);
        if (startInput) startInput.value = start.toISOString().split('T')[0];
        if (endInput) endInput.value = end.toISOString().split('T')[0];
    } else if (presetName === 'overdue') {
        if (typeSel) typeSel.value = 'rp4';
    } else if (presetName === 'distribution') {
        if (typeSel) typeSel.value = 'rp5';
    } else if (presetName === 'organized') {
        if (typeSel) typeSel.value = 'rp9';
    }

    generateSelectedReport();
}

/**
 * Generate report with current form controls
 */
export async function generateSelectedReport() {
    const typeSel = document.getElementById('report-type-selector');
    const accSel = document.getElementById('reports-account-selector');
    const listSel = document.getElementById('report-list-filter');
    const tagSel = document.getElementById('report-tag-filter');
    const startInput = document.getElementById('report-start-date');
    const endInput = document.getElementById('report-end-date');

    const reportType = typeSel ? typeSel.value : 'rp1';
    currentReportType = reportType;
    const account = accSel ? accSel.value : 'all';
    const listId = listSel ? listSel.value : 'all';
    const tag = tagSel ? tagSel.value : '';

    let periodDays = 30;
    if (startInput && startInput.value && endInput && endInput.value) {
        const s = new Date(startInput.value);
        const e = new Date(endInput.value);
        const diffMs = e.getTime() - s.getTime();
        periodDays = Math.max(1, Math.round(diffMs / (1000 * 60 * 60 * 24)));
    }

    const filterStrInput = document.getElementById('report-custom-filter-str');
    const orderByInput = document.getElementById('report-custom-order-by');
    const outputTagsInput = document.getElementById('report-custom-output-tags');
    const outputListsInput = document.getElementById('report-custom-output-lists');

    const payload = {
        report_type: reportType,
        account: account,
        filters: {
            list_id: listId,
            tags: tag || undefined
        },
        parameters: {
            period_days: periodDays,
            start_date: startInput && startInput.value ? startInput.value : undefined,
            end_date: endInput && endInput.value ? endInput.value : undefined,
            filter_str: filterStrInput && filterStrInput.value ? filterStrInput.value : undefined,
            order_by: orderByInput && orderByInput.value ? orderByInput.value : undefined,
            output_tags: outputTagsInput && outputTagsInput.value ? outputTagsInput.value : undefined,
            output_lists: outputListsInput && outputListsInput.value ? outputListsInput.value : undefined
        }
    };

    // Show loading state
    const loadingEl = document.getElementById('reports-loading');
    if (loadingEl) loadingEl.style.display = 'block';

    try {
        const basePath = window.GTASKS_BASE_PATH || '';
        const res = await fetch(`${basePath}/api/reports/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const json = await res.json();
        if (json.success && json.data) {
            currentReportData = json.data;
            renderReportUI(json.data, reportType);
        } else {
            alert(json.message || 'Failed to generate report');
        }
    } catch (err) {
        console.error('[Reports] Error generating report:', err);
        alert('Error generating report: ' + err.message);
    } finally {
        if (loadingEl) loadingEl.style.display = 'none';
    }
}

/**
 * Render KPI Cards, Charts, and Data tables based on report response
 */
function renderReportUI(data, reportType) {
    // 1. Update Metrics Cards
    updateMetricCards(data, reportType);

    // 2. Render / Update Charts
    renderCharts(data, reportType);

    // 3. Render Output Table or Formatted Text
    renderOutputDetails(data, reportType);
}

/**
 * Update the 4 KPI metric cards
 */
function updateMetricCards(data, reportType) {
    const m1Val = document.getElementById('metric-1-val');
    const m1Lbl = document.getElementById('metric-1-lbl');
    const m2Val = document.getElementById('metric-2-val');
    const m2Lbl = document.getElementById('metric-2-lbl');
    const m3Val = document.getElementById('metric-3-val');
    const m3Lbl = document.getElementById('metric-3-lbl');
    const m4Val = document.getElementById('metric-4-val');
    const m4Lbl = document.getElementById('metric-4-lbl');

    if (reportType === 'rp1' || reportType === 'task_completion') {
        if (m1Val) m1Val.textContent = data.total_completed ?? 0;
        if (m1Lbl) m1Lbl.textContent = 'Completed Tasks';

        if (m2Val) m2Val.textContent = (data.completion_rate ? data.completion_rate.toFixed(1) : 0) + '%';
        if (m2Lbl) m2Lbl.textContent = 'Completion Rate';

        if (m3Val) m3Val.textContent = (data.average_per_day ? data.average_per_day.toFixed(1) : 0);
        if (m3Lbl) m3Lbl.textContent = 'Avg Completed / Day';

        if (m4Val) m4Val.textContent = data.period_days ?? 30;
        if (m4Lbl) m4Lbl.textContent = 'Analyzed Days';
    } else if (reportType === 'rp4' || reportType === 'overdue_tasks') {
        if (m1Val) m1Val.textContent = data.total_overdue ?? 0;
        if (m1Lbl) m1Lbl.textContent = 'Total Overdue';

        if (m2Val) m2Val.textContent = (data.very_overdue ? data.very_overdue.length : 0);
        if (m2Lbl) m2Lbl.textContent = 'Critical (> 7 Days)';

        if (m3Val) m3Val.textContent = (data.moderately_overdue ? data.moderately_overdue.length : 0);
        if (m3Lbl) m3Lbl.textContent = 'Moderate (3-7 Days)';

        if (m4Val) m4Val.textContent = (data.slightly_overdue ? data.slightly_overdue.length : 0);
        if (m4Lbl) m4Lbl.textContent = 'Recent (1-2 Days)';
    } else {
        if (m1Val) m1Val.textContent = data.total_tasks ?? data.total_pending ?? data.total_completed ?? '-';
        if (m1Lbl) m1Lbl.textContent = 'Total Tasks';

        if (m2Val) m2Val.textContent = data.status_distribution ? Object.keys(data.status_distribution).length : '-';
        if (m2Lbl) m2Lbl.textContent = 'Status Categories';

        if (m3Val) m3Val.textContent = data.priority_distribution ? Object.keys(data.priority_distribution).length : '-';
        if (m3Lbl) m3Lbl.textContent = 'Priorities';

        if (m4Val) m4Val.textContent = data.period_days ? `${data.period_days} Days` : 'All Time';
        if (m4Lbl) m4Lbl.textContent = 'Scope';
    }
}

/**
 * Render Chart.js charts
 */
function renderCharts(data, reportType) {
    if (typeof Chart === 'undefined') {
        console.warn('[Reports] Chart.js is not loaded yet');
        return;
    }

    const isDark = document.body.classList.contains('dark-mode');
    const textColor = isDark ? '#cbd5e1' : '#475569';
    const gridColor = isDark ? '#334155' : '#f1f5f9';

    // Chart 1: Trend / Volume
    const trendCanvas = document.getElementById('report-trend-chart');
    if (trendCanvas) {
        if (completionTrendChart) {
            completionTrendChart.destroy();
        }

        let labels = [];
        let values = [];

        if (data.daily_counts) {
            labels = Object.keys(data.daily_counts).sort();
            values = labels.map(k => data.daily_counts[k]);
        } else if (data.status_distribution) {
            labels = Object.keys(data.status_distribution);
            values = Object.values(data.status_distribution);
        } else {
            labels = ['Pending', 'Completed'];
            values = [data.total_pending || 0, data.total_completed || 0];
        }

        completionTrendChart = new Chart(trendCanvas, {
            type: data.daily_counts ? 'line' : 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: data.daily_counts ? 'Tasks' : 'Volume',
                    data: values,
                    borderColor: '#3b82f6',
                    backgroundColor: data.daily_counts ? 'rgba(59, 130, 246, 0.15)' : '#3b82f6',
                    fill: true,
                    tension: 0.3,
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: {
                        ticks: { color: textColor },
                        grid: { color: gridColor }
                    },
                    y: {
                        beginAtZero: true,
                        ticks: { color: textColor, precision: 0 },
                        grid: { color: gridColor }
                    }
                }
            }
        });
    }

    // Chart 2: Distribution Doughnut
    const distCanvas = document.getElementById('report-dist-chart');
    if (distCanvas) {
        if (distributionDoughnutChart) {
            distributionDoughnutChart.destroy();
        }

        let labels = [];
        let values = [];
        let colors = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6'];

        if (data.status_distribution) {
            labels = Object.keys(data.status_distribution);
            values = Object.values(data.status_distribution);
        } else if (data.priority_distribution) {
            labels = Object.keys(data.priority_distribution);
            values = Object.values(data.priority_distribution);
        } else if (reportType === 'rp4') {
            labels = ['Very Overdue', 'Moderately Overdue', 'Slightly Overdue'];
            values = [
                (data.very_overdue || []).length,
                (data.moderately_overdue || []).length,
                (data.slightly_overdue || []).length
            ];
            colors = ['#ef4444', '#f97316', '#f59e0b'];
        } else {
            labels = ['Completed', 'Pending'];
            values = [data.total_completed || 0, (data.total_tasks || 0) - (data.total_completed || 0)];
        }

        distributionDoughnutChart = new Chart(distCanvas, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    backgroundColor: colors,
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { color: textColor, boxWidth: 12 }
                    }
                }
            }
        });
    }
}

/**
 * Render Output details (table or clean text format)
 */
function renderOutputDetails(data, reportType) {
    const tableContainer = document.getElementById('reports-table-container');
    const titleEl = document.getElementById('reports-output-title');
    if (titleEl) {
        titleEl.textContent = data.report_name || `${reportType.toUpperCase()} Report`;
    }

    if (!tableContainer) return;

    // Check if report has list of tasks
    const taskList = data.tasks || data.completed_tasks || data.overdue_tasks || (data.categories ? Object.values(data.categories).flat() : null);

    if (taskList && Array.isArray(taskList) && taskList.length > 0) {
        const isCompletionReport = reportType === 'rp1' || reportType === 'task_completion';
        let html = `
            <div class="reports-table-wrapper">
                <table class="reports-table">
                    <thead>
                        <tr>
                            <th>Title</th>
                            <th>Status / Priority</th>
                            <th>${isCompletionReport ? 'Completed Date' : 'Due Date'}</th>
                            <th>Notes / Info</th>
                        </tr>
                    </thead>
                    <tbody>
        `;

        taskList.slice(0, 100).forEach(t => {
            const title = t.title || 'Untitled';
            const status = t.status || '-';
            let dateStr = '-';
            if (isCompletionReport && t.completed_at) {
                dateStr = new Date(t.completed_at).toLocaleDateString() + ' ' + new Date(t.completed_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
            } else if (t.due) {
                dateStr = new Date(t.due).toLocaleDateString();
            }
            const extra = t.days_overdue ? `<span style="color:#ef4444;font-weight:600;">${t.days_overdue}d overdue</span>` : (t.notes || '-');

            html += `
                <tr>
                    <td style="font-weight: 500;">${title}</td>
                    <td><span class="status-badge status-${status}">${status}</span></td>
                    <td>${dateStr}</td>
                    <td>${extra}</td>
                </tr>
            `;
        });

        html += `
                    </tbody>
                </table>
            </div>
        `;
        tableContainer.innerHTML = html;
    } else if (taskList && Array.isArray(taskList) && taskList.length === 0) {
        tableContainer.innerHTML = `
            <div style="padding: 2.5rem; text-align: center; color: var(--text-secondary, #64748b);">
                <i class="fas fa-inbox fa-3x" style="opacity: 0.4; margin-bottom: 0.75rem;"></i>
                <p style="font-weight: 500; font-size: 1rem;">No tasks found for the selected timeframe and filters.</p>
                <p style="font-size: 0.85rem; opacity: 0.75; margin-top: 0.25rem;">Try expanding the date range or selecting "All Lists".</p>
            </div>
        `;
    } else {
        // Fallback to formatted JSON preview
        tableContainer.innerHTML = `
            <div class="reports-raw-text">${JSON.stringify(data, null, 2)}</div>
        `;
    }
}

/**
 * Export current report
 */
export async function exportReport(format) {
    if (!currentReportData) {
        alert('Please generate a report first.');
        return;
    }

    try {
        const basePath = window.GTASKS_BASE_PATH || '';
        const res = await fetch(`${basePath}/api/reports/export`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                report_type: currentReportType,
                report_data: currentReportData,
                format: format
            })
        });

        if (format === 'json' || format === 'csv' || format === 'txt') {
            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${currentReportType}_report.${format}`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
        }
    } catch (err) {
        console.error('[Reports] Export error:', err);
        alert('Failed to export report: ' + err.message);
    }
}

/**
 * Copy formatted report to clipboard
 */
export function copyReportToClipboard() {
    if (!currentReportData) {
        alert('Please generate a report first.');
        return;
    }

    const text = JSON.stringify(currentReportData, null, 2);
    navigator.clipboard.writeText(text).then(() => {
        alert('Report data copied to clipboard!');
    }).catch(err => {
        console.error('Failed to copy: ', err);
    });
}

/**
 * Email Report Modal Controls
 */
export function openEmailModal() {
    if (!currentReportData) {
        alert('Please run/generate a report first before sending email.');
        return;
    }
    const modal = document.getElementById('report-email-modal');
    if (modal) {
        modal.style.display = 'flex';
        const subjInput = document.getElementById('report-email-subject');
        if (subjInput) {
            const reportName = currentReportData.report_name || currentReportData.title || `${currentReportType.toUpperCase()} Report`;
            subjInput.value = `GTasks Report: ${reportName} (${new Date().toLocaleDateString()})`;
        }
    }
}

export function closeEmailModal() {
    const modal = document.getElementById('report-email-modal');
    if (modal) modal.style.display = 'none';
}

export async function sendReportViaEmail() {
    const recInput = document.getElementById('report-email-recipients');
    const subjInput = document.getElementById('report-email-subject');
    const ccInput = document.getElementById('report-email-cc');
    const btn = document.getElementById('btn-confirm-send-email');

    if (!recInput || !recInput.value.trim()) {
        alert('Please enter at least one recipient email address.');
        return;
    }

    const recipients = recInput.value.split(',').map(e => e.trim()).filter(Boolean);
    const cc = ccInput && ccInput.value ? ccInput.value.split(',').map(e => e.trim()).filter(Boolean) : [];
    const subject = subjInput ? subjInput.value.trim() : undefined;

    const originalBtnHtml = btn ? btn.innerHTML : '';
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sending...';
    }

    try {
        const basePath = window.GTASKS_BASE_PATH || '';
        const res = await fetch(`${basePath}/api/reports/email`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                report_type: currentReportType,
                report_data: currentReportData,
                recipients: recipients,
                cc: cc,
                subject: subject
            })
        });

        const json = await res.json();
        if (json.success) {
            alert('✅ ' + json.message);
            closeEmailModal();
        } else {
            alert('❌ ' + (json.message || 'Failed to send report email.'));
        }
    } catch (err) {
        console.error('[Reports] Error sending email:', err);
        alert('Error sending email: ' + err.message);
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = originalBtnHtml;
        }
    }
}

/**
 * Toggle between Standard & Advanced Builder panels
 */
export function toggleReportBuilderMode(mode) {
    const stdCard = document.getElementById('reports-standard-builder');
    const advCard = document.getElementById('reports-custom-builder');
    const tabStd = document.getElementById('tab-builder-standard');
    const tabAdv = document.getElementById('tab-builder-custom');

    if (mode === 'custom') {
        if (stdCard) stdCard.style.display = 'none';
        if (advCard) advCard.style.display = 'block';
        if (tabStd) tabStd.classList.remove('active');
        if (tabAdv) tabAdv.classList.add('active');

        // Select rp10
        const sel = document.getElementById('report-type-selector');
        if (sel) sel.value = 'rp10';
    } else {
        if (stdCard) stdCard.style.display = 'block';
        if (advCard) advCard.style.display = 'none';
        if (tabStd) tabStd.classList.add('active');
        if (tabAdv) tabAdv.classList.remove('active');
    }
}

// Attach globals for HTML event attributes
window.initReportsView = initReportsView;
window.applyPreset = applyPreset;
window.generateSelectedReport = generateSelectedReport;
window.exportReport = exportReport;
window.copyReportToClipboard = copyReportToClipboard;
window.openEmailModal = openEmailModal;
window.closeEmailModal = closeEmailModal;
window.sendReportViaEmail = sendReportViaEmail;
window.toggleReportBuilderMode = toggleReportBuilderMode;

