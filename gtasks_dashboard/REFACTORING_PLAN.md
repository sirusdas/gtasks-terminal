# Dashboard Refactoring and Modularization Plan

## Executive Summary

The `dashboard.html` (2066 lines) and `hierarchy.js` (1564 lines) files have grown too large and are difficult to maintain. This plan outlines a systematic approach to modularize and refactor these files for better maintainability, testability, and code organization.

---

## Current State Analysis

### Issues Identified

| Issue | Location | Impact |
|-------|----------|--------|
| **Monolithic HTML file** | `dashboard.html` (2066 lines) | Difficult to navigate, edit, and debug |
| **Inline CSS (745 lines)** | `<style>` in `dashboard.html` | No caching, hard to maintain theme changes |
| **Inline JavaScript (900+ lines)** | `<script>` in `dashboard.html` | Mixing concerns, no module system |
| **Monolithic JS file** | `hierarchy.js` (1564 lines) | Multiple responsibilities in one file |
| **Code duplication** | Multiple files | Helper functions repeated across files |
| **No clear separation** | All files | Rendering, filtering, display logic mixed |

### Current File Sizes

```
dashboard.html:     2066 lines (745 CSS + 900+ JS inline)
hierarchy.js:       1564 lines (all JS)
filters.js:          218 lines (utilities - already extracted)
dashboard.css:       ~400 lines (external)
```

---

## Target Architecture

```
gtasks_dashboard/
├── templates/
│   └── dashboard.html          # Clean HTML structure only (~300 lines)
├── static/
│   ├── css/
│   │   ├── base.css            # Base styles (~100 lines)
│   │   ├── components.css      # Component styles (~150 lines)
│   │   ├── dark-mode.css       # Dark mode overrides (~150 lines)
│   │   ├── modal.css           # Settings modal styles (~80 lines)
│   │   └── dashboard.css       # Main dashboard styles (~200 lines)
│   └── js/
│       ├── vendor/
│       │   └── d3.v7.min.js    # D3.js library (external)
│       ├── core/
│       │   ├── constants.js    # Constants and config (~50 lines)
│       │   ├── state.js        # Global state management (~80 lines)
│       │   └── utils.js        # Shared utilities (~100 lines)
│       ├── modules/
│       │   ├── dark-mode.js    # Dark mode toggle (~80 lines)
│       │   ├── settings.js     # Settings modal (~100 lines)
│       │   └── keyboard.js     # Keyboard shortcuts (~50 lines)
│       ├── components/
│       │   ├── task-card.js    # Task card rendering (~120 lines)
│       │   ├── filters.js      # Advanced filtering (~150 lines)
│       │   └── stats.js        # Stats and metrics (~60 lines)
│       ├── hierarchy/
│       │   ├── config.js       # Hierarchy config (~40 lines)
│       │   ├── renderer.js     # D3 rendering logic (~200 lines)
│       │   ├── interactions.js # Node clicks, drag, zoom (~150 lines)
│       │   ├── filters.js      # Hierarchy-specific filters (~150 lines)
│       │   └── task-panel.js   # Task panel display (~150 lines)
│       ├── dashboard.js        # Main initialization (~100 lines)
│       └── main.js             # Entry point (~50 lines)
└── refactoring_plan.md         # This file
```

---

## Phase-by-Phase Implementation Plan

### Phase 1: Extract CSS to Separate Files

**Goal**: Remove all inline CSS from `dashboard.html` and create organized CSS modules.

**Steps**:
1. Create `css/base.css` - CSS variables, reset, typography
2. Create `css/components.css` - Cards, buttons, forms
3. Create `css/dark-mode.css` - Dark mode specific styles
4. Create `css/modal.css` - Modal and overlay styles
5. Update `dashboard.html` to link external CSS

**CSS Files Breakdown**:

#### `css/base.css` (~100 lines)
```css
:root {
    --bg-primary: #f3f4f6;
    --bg-secondary: #ffffff;
    --text-primary: #1f2937;
    --border-color: #e5e7eb;
    /* ... more variables */
}

* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: system-ui, sans-serif; }
```

#### `css/dark-mode.css` (~150 lines)
```css
.dark-mode {
    --bg-primary: #111827;
    --bg-secondary: #1f2937;
    /* ... all dark mode overrides */
}

.dark-mode .sidebar { background-color: var(--bg-secondary); }
/* ... more dark mode styles */
```

#### `css/modal.css` (~80 lines)
```css
.modal-overlay { /* styles */ }
.modal-content { /* styles */ }
.modal-header { /* styles */ }
/* ... modal specific styles */
```

---

### Phase 2: Extract Core JavaScript Utilities

**Goal**: Create shared utility modules used across the application.

**Files to Create**:

#### `js/core/constants.js` (~50 lines)
```javascript
export const PRIORITY_ORDER = {
    critical: 0,
    high: 1,
    medium: 2,
    low: 3
};

export const STATUS_ORDER = {
    completed: 0,
    in_progress: 1,
    pending: 2
};

export const COLOR_SCALE = {
    priority: {
        critical: '#ef4444',
        high: '#f97316',
        medium: '#eab308',
        low: '#6b7280'
    },
    type: {
        meta: '#8b5cf6',
        category: '#3b82f6',
        tag: '#10b981',
        account: '#8b5cf6'
    }
};
```

#### `js/core/state.js` (~80 lines)
```javascript
// Global state management
export const state = {
    dashboardData: {},
    hierarchyData: {},
    selectedNode: null,
    selectedAccount: null,
    isFullscreen: false,
    autoRefreshInterval: null
};

export function getState() { /* ... */ }
export function setState(updates) { /* ... */ }
```

#### `js/core/utils.js` (~100 lines)
```javascript
// Shared utilities extracted from both files
export function formatDate(dateString) {
    if (!dateString) return '-';
    return new Date(dateString).toISOString().split('T')[0];
}

export function getDateStatus(dueDate) {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const due = new Date(dueDate);
    due.setHours(0, 0, 0, 0);
    
    if (due < today) return 'overdue';
    if (due.getTime() === today.getTime()) return 'today';
    return 'future';
}

export function parseDateInput(dateString) { /* ... */ }
export function truncateText(text, maxLength) { /* ... */ }
export function debounce(func, wait) { /* ... */ }
export function sortTasksByField(tasks, sortField, sortOrder) { /* ... */ }
```

---

### Phase 3: Create Component Modules

**Goal**: Extract UI component logic into focused modules.

**Files to Create**:

#### `js/components/task-card.js` (~120 lines)
```javascript
import { getDateStatus, formatDate } from '../core/utils.js';

export function createTaskCard(task) {
    const card = document.createElement('div');
    card.className = 'task-card';
    // ... card creation logic
    return card;
}

export function createNodeTaskCard(task, node) {
    // ... node-specific card creation
}

export function getDateStatusBadge(dateStatus) {
    const badges = {
        overdue: '<span class="date-status-badge overdue">⏳ Overdue</span>',
        today: '<span class="date-status-badge today">📅 Today</span>',
        future: '<span class="date-status-badge future">📅 Future</span>',
        none: ''
    };
    return badges[dateStatus] || badges.none;
}

export function getCompactDateDisplay(task) { /* ... */ }
export function getNotesSection(task) { /* ... */ }
export function getTagsDisplay(task) { /* ... */ }
```

#### `js/components/filters.js` (~150 lines)
```javascript
import { filterTasksList, sortTasks } from './filters.js';

export function initTaskFilters() {
    // Setup filter event listeners
}

export function filterTasks() {
    // Main filter function using shared filter logic
}

export function clearTasksFilters() {
    // Reset all filter inputs
}

export function setupNodeTaskFilters(node) {
    // Node-specific filter setup
}

export function filterNodeTasks(node) {
    // Filter tasks for specific node
}
```

---

### Phase 4: Create Hierarchy-Specific Modules

**Goal**: Break down `hierarchy.js` into focused modules.

**Files to Create**:

#### `js/hierarchy/config.js` (~40 lines)
```javascript
export const HIERARCHY_CONFIG = {
    zoom: {
        scaleExtent: [0.1, 10]
    },
    force: {
        baseDistance: 100,
        levels: {
            0: { charge: -400, distance: 120 },
            1: { charge: -200, distance: 80 },
            2: { charge: -100, distance: 60 }
        }
    },
    node: {
        baseSize: { min: 8, max: 25 },
        levels: {
            0: { multiplier: 1.2 },
            1: { multiplier: 1.0 }
        }
    }
};
```

#### `js/hierarchy/renderer.js` (~200 lines)
```javascript
import * as d3 from 'd3';
import { HIERARCHY_CONFIG } from './config.js';
import { getNodeColor } from './utils.js';

export function renderHierarchy(data) {
    hierarchyData = data;
    initHierarchy();
}

function initHierarchy() {
    const svg = d3.select('#hierarchy-viz');
    // ... D3 rendering logic
}

function createNodes(g, data) { /* ... */ }
function createLinks(g, data) { /* ... */ }
function createLabels(g, data) { /* ... */ }
function initSimulation(width, height) { /* ... */ }
```

#### `js/hierarchy/interactions.js` (~150 lines)
```javascript
export function setupInteractions() {
    // Setup zoom, drag, click handlers
}

export function handleNodeClick(node) {
    selectedNode = node;
    showTaskPanel(node);
    highlightSelectedNode(node);
    loadNodeTasks(node);
}

export function setupZoom(svg) { /* ... */ }
export function setupDrag(nodes) { /* ... */ }

export function highlightSelectedNode(node) {
    d3.selectAll('#hierarchy-viz circle').classed('selected', false);
    d3.selectAll('#hierarchy-viz circle')
        .filter(d => d.id === node.id)
        .classed('selected', true)
        .style('stroke', '#3b82f6')
        .style('stroke-width', 4);
}

export function showLabelTooltip(event, fullText) { /* ... */ }
export function hideLabelTooltip() { /* ... */ }
```

#### `js/hierarchy/filters.js` (~150 lines)
```javascript
let hierarchyFilters = {
    tagSearch: '',
    status: '',
    dateStart: '',
    dateEnd: ''
};

export function initHierarchyFilters() {
    // Setup filter event listeners
}

export function applyChartFilters() {
    // Apply filters and refresh visualization
}

export function clearHierarchyFilters() {
    hierarchyFilters = { tagSearch: '', status: '', dateStart: '', dateEnd: '' };
    refreshHierarchyVisualization();
}

export function filterHierarchyByTags(data, tagSearch) { /* ... */ }
export function filterHierarchyByStatus(data, status) { /* ... */ }
export function filterHierarchyByDate(data, dateField, dateStart, dateEnd) { /* ... */ }
```

#### `js/hierarchy/task-panel.js` (~150 lines)
```javascript
export function showTaskPanel(node) {
    const panel = document.getElementById('task-panel');
    const title = document.getElementById('selected-node-title');
    
    title.textContent = `Tasks for: ${node.name || node.id}`;
    panel.style.display = 'block';
    panel.style.minHeight = '300vh';
}

export function closeTaskPanel() {
    const panel = document.getElementById('task-panel');
    panel.style.transition = 'max-height 0.3s ease';
    panel.style.maxHeight = '0';
    
    setTimeout(() => {
        panel.style.display = 'none';
        panel.style.maxHeight = '';
    }, 300);
    
    selectedNode = null;
    d3.selectAll('#hierarchy-viz circle').classed('selected', false);
}

export function loadNodeTasks(node) {
    const relatedTasks = getRelatedTasks(node);
    displayNodeTasks(relatedTasks, node);
    setupTaskFilters(node);
}

export function getRelatedTasks(node) { /* ... */ }
export function displayNodeTasks(tasks, node) { /* ... */ }
export function getDependentTasks(tasks, allTasks) { /* ... */ }
```

---

### Phase 5: Create Feature Modules

**Goal**: Extract feature-specific logic into modules.

**Files to Create**:

#### `js/modules/dark-mode.js` (~80 lines)
```javascript
export function initDarkMode() {
    const savedDarkMode = localStorage.getItem('darkMode');
    if (savedDarkMode === 'enabled') {
        document.body.classList.add('dark-mode');
    }
}

export function toggleDarkMode() {
    document.body.classList.toggle('dark-mode');
    const isDarkMode = document.body.classList.contains('dark-mode');
    localStorage.setItem('darkMode', isDarkMode ? 'enabled' : 'disabled');
}
```

#### `js/modules/settings.js` (~100 lines)
```javascript
let autoRefreshInterval = null;

export function initSettings() {
    // Load saved settings from localStorage
    const autoRefreshEnabled = localStorage.getItem('autoRefresh') === 'enabled';
    const refreshInterval = localStorage.getItem('refreshInterval') || '60';
    // ... more initialization
}

export function openSettings() {
    document.getElementById('settings-modal').classList.add('active');
}

export function closeSettings() {
    document.getElementById('settings-modal').classList.remove('active');
}

export function toggleAutoRefresh() { /* ... */ }
export function startAutoRefresh(interval) { /* ... */ }
export function stopAutoRefresh() { /* ... */ }
```

#### `js/modules/keyboard.js` (~50 lines)
```javascript
export function setupKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        if (e.ctrlKey && e.key === 'b') {
            e.preventDefault();
            toggleSidebar();
        }
        if (e.ctrlKey && e.key === 'f') {
            e.preventDefault();
            toggleFullscreen();
        }
        if (e.key === 'Escape' && isFullscreen) {
            toggleFullscreen();
        }
    });
}
```

---

### Phase 6: Create Main Entry Points

**Goal**: Create clean entry points for the application.

#### `js/dashboard.js` (~100 lines)
```javascript
import { initDarkMode } from './modules/dark-mode.js';
import { initSettings } from './modules/settings.js';
import { initKeyboard } from './modules/keyboard.js';
import { loadDashboard } from './services/api.js';
import { initHierarchy } from './hierarchy/renderer.js';

// Global state
export let dashboardData = {};
export let selectedAccount = null;
export let isFullscreen = false;

export async function initDashboard() {
    initDarkMode();
    initSettings();
    initKeyboard();
    await loadDashboard();
}

// API functions
export async function loadDashboard() {
    showLoading(true);
    try {
        const response = await fetch('/api/data');
        dashboardData = await response.json();
        updateStats();
        updateAccountSelectors();
        loadTasks();
        await loadHierarchy();
    } finally {
        showLoading(false);
    }
}

export function updateStats() { /* ... */ }
export function updateAccountSelectors() { /* ... */ }
export function loadTasks() { /* ... */ }
export async function loadHierarchy() { /* ... */ }
```

#### `js/main.js` (~50 lines)
```javascript
// Main entry point
import { initDashboard } from './dashboard.js';

document.addEventListener('DOMContentLoaded', async () => {
    await initDashboard();
});
```

---

## Updated Dashboard HTML Structure

After refactoring, `dashboard.html` will be reduced to approximately 300 lines:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GTasks Dashboard - Hierarchical Visualization</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <script src="https://d3js.org/d3.v7.min.js"></script>
    
    <!-- External CSS modules -->
    <link rel="stylesheet" href="/static/css/base.css">
    <link rel="stylesheet" href="/static/css/components.css">
    <link rel="stylesheet" href="/static/css/dark-mode.css">
    <link rel="stylesheet" href="/static/css/modal.css">
    <link rel="stylesheet" href="/static/css/dashboard.css">
</head>
<body>
    <div class="dashboard-container">
        <!-- Sidebar -->
        <aside class="sidebar" id="sidebar">
            <!-- ... sidebar content ... -->
        </aside>

        <!-- Main Content -->
        <main class="main-content" id="main-content">
            <!-- Dashboard Section -->
            <section id="dashboard-section" class="section">
                <!-- ... dashboard content ... -->
            </section>

            <!-- Hierarchy Section -->
            <section id="hierarchy-section" class="section" style="display: none;">
                <!-- ... hierarchy content ... -->
            </section>

            <!-- Tasks Section -->
            <section id="tasks-section" class="section" style="display: none;">
                <!-- ... tasks content ... -->
            </section>
        </main>
    </div>

    <!-- Settings Modal -->
    <div class="modal-overlay" id="settings-modal">
        <!-- ... modal content ... -->
    </div>

    <!-- Loading Overlay -->
    <div class="loading-overlay" id="loading-overlay" style="display: none;">
        <!-- ... loading content ... -->
    </div>

    <!-- Main JavaScript -->
    <script type="module" src="/static/js/main.js"></script>
</body>
</html>
```

---

## Benefits of This Refactoring

| Benefit | Description |
|---------|-------------|
| **Maintainability** | Each file has a single responsibility, making it easier to understand and modify |
| **Testability** | Modules can be unit tested in isolation |
| **Performance** | CSS can be cached by browsers; JS modules can be lazy-loaded |
| **Reusability** | Utility functions and components can be reused across the application |
| **Team Collaboration** | Multiple developers can work on different modules without conflicts |
| **Scalability** | New features can be added as new modules without bloating existing files |

---

## Migration Strategy

### Step 1: Create New Files
Create the new CSS and JS files with the extracted code.

### Step 2: Update HTML
Replace inline CSS with `<link>` tags and inline JS with `<script type="module">` tags.

### Step 3: Test Incrementally
Test each module independently before integrating.

### Step 4: Remove Old Code
Once all functionality is verified, remove the inline CSS and JS from `dashboard.html`.

### Step 5: Cleanup
Remove `hierarchy.js` once all its functionality has been migrated to the new modules.

---

## Estimated Line Count After Refactoring

| File | Original Lines | Refactored Lines |
|------|---------------|------------------|
| `dashboard.html` | 2066 | ~300 |
| `hierarchy.js` | 1564 | Removed (migrated) |
| `filters.js` | 218 | 218 |
| New CSS files | 0 | ~680 |
| New JS modules | 0 | ~1500 |
| **Total** | **3848** | **~2700** |

While the total line count is similar, the code is now:
- **Organized** by responsibility
- **Modular** with clear dependencies
- **Maintainable** with single-purpose files
- **Testable** with isolated components

---

## Implementation Order

1. **Week 1**: Extract CSS modules and update HTML
2. **Week 2**: Extract core utilities and state management
3. **Week 3**: Create component modules (task-card, filters)
4. **Week 4**: Break down hierarchy.js into focused modules
5. **Week 5**: Create feature modules (dark-mode, settings, keyboard)
6. **Week 6**: Create main entry points and final integration
7. **Week 7**: Testing and cleanup

---

## Success Criteria

- [ ] `dashboard.html` reduced to < 400 lines
- [ ] All inline CSS moved to external CSS files
- [ ] All inline JS moved to module files
- [ ] `hierarchy.js` functionality distributed to focused modules
- [ ] All existing functionality preserved
- [ ] All tests pass after refactoring
- [ ] No regression in performance

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| **Breaking changes** | Test incrementally after each phase |
| **Performance regression** | Use browser DevTools to profile |
| **Missing functionality** | Create a checklist of all features to verify |
| **Circular dependencies** | Use dependency analysis tools |
| **Module loading issues** | Test across browsers and ensure ES6 support |

---

## Conclusion

This refactoring plan transforms the monolithic `dashboard.html` and `hierarchy.js` files into a well-organized, modular architecture. While the total line count remains similar, the code becomes significantly more maintainable, testable, and scalable. The phased approach ensures minimal risk and allows for incremental verification at each step.
