# GTasks Automation - Architecture Overview

## Project Purpose
Google Tasks automation tool with CLI and Web Dashboard interfaces for managing tasks, reports, and multi-account support.

---

## Core Components

### 1. gtasks_cli (Command Line Interface)
**Purpose**: Primary CLI application for managing Google Tasks

**Key Components**:

| Component | Location | Responsibility |
|-----------|----------|----------------|
| **Entry Point** | `gtasks_cli/src/gtasks_cli/main.py` | CLI group, command routing, global options |
| **Commands** | `gtasks_cli/src/gtasks_cli/commands/` | Individual command modules (add, list, search, view, done, delete, update, auth, summary, interactive, deduplicate, account, advanced_sync, generate_report, config, ai, mcp, tasklist) |
| **Models** | `gtasks_cli/src/gtasks_cli/models/` | Data structures (Task, TaskList, Account) |
| **Reports** | `gtasks_cli/src/gtasks_cli/reports/` | Report generators (base_report, task_completion_report, pending_tasks_report, organized_tasks_report, etc.) |
| **Utils** | `gtasks_cli/src/gtasks_cli/utils/` | Helper utilities (email_sender, exceptions, logger) |
| **Interactive Utils** | `gtasks_cli/src/gtasks_cli/commands/interactive_utils/` | Interactive mode helpers (add_commands, delete_commands, list_commands, update_commands, display, search, undo_manager, etc.) |

**Storage Options**: JSON or SQLite backends, sync with Google Tasks API

---

### 2. gtasks_dashboard (Web Dashboard)
**Purpose**: Visual web interface for task management using Flask + D3.js

**Key Components**:

| Component | Location | Responsibility |
|-----------|----------|----------------|
| **Entry Point** | `gtasks_dashboard/main_dashboard.py` | Flask app initialization, blueprint registration, feature flag management |
| **Routes** | `gtasks_dashboard/routes/api.py` | REST API endpoints for task operations |
| **Routes** | `gtasks_dashboard/routes/dashboard.py` | Page routes and view rendering |
| **Services** | `gtasks_dashboard/services/data_manager.py` | Business logic, data transformation, task operations |
| **Services** | `gtasks_dashboard/services/sync_service.py` | Thread-safe sync operations with progress tracking for advanced sync |
| **Services** | `gtasks_dashboard/services/dashboard_generator.py` | Static HTML dashboard generation (optional export) |
| **Models** | `gtasks_dashboard/models/` | Data models (Task, Account, DashboardStats, HybridTags) |
| **Modules** | `gtasks_dashboard/modules/priority_system.py` | Priority calculation and management |
| **Modules** | `gtasks_dashboard/modules/tag_manager.py` | Hybrid tag extraction (@user, #tag, [bracket]) |
| **Modules** | `gtasks_dashboard/modules/account_manager.py` | Multi-account support |
| **Modules** | `gtasks_dashboard/modules/settings_manager.py` | Dashboard configuration persistence |
| **Templates** | `gtasks_dashboard/templates/dashboard.html` | Main dashboard template |
| **Templates** | `gtasks_dashboard/templates/static_dashboard.html` | Standalone export template (optional) |
| **UI Components** | `gtasks_dashboard/ui_components.py` | Reusable UI components |
| **Config** | `gtasks_dashboard/config.py` | Dashboard configuration, feature flags |
| **Frontend Modules** | `gtasks_dashboard/static/js/` | Modular JavaScript for dashboard |

**Frontend JavaScript Modules**:

| Module | File | Responsibility |
|--------|------|---------------|
| **Constants** | `constants.js` | Configuration, color scales, API endpoints, storage keys |
| **Utils** | `utils.js` | Utility functions (date parsing, filtering, sorting) |
| **State** | `state.js` | Centralized state management |
| **Task Card** | `task-card.js` | Task card component rendering |
| **Dashboard** | `dashboard.js` | Main dashboard functionality and initialization |
| **Hierarchy** | `hierarchy.js` | D3.js hierarchy visualization |
| **Hierarchy Renderer** | `hierarchy-renderer.js` | D3.js graph rendering logic |
| **Hierarchy Interactions** | `hierarchy-interactions.js` | Node click, drag, and tooltip handling |
| **Hierarchy Filters** | `hierarchy-filters.js` | Filtering hierarchy data by tags, status, date |
| **Hierarchy Task Panel** | `hierarchy-task-panel.js` | Task display panel for selected nodes |
| **Hierarchy Ledger** | `hierarchy-ledger.js` | Tabular ledger view with click interactions |

**Frontend CSS Modules**:

| Module | File | Responsibility |
|--------|------|---------------|
| **Base Styles** | `dashboard.css` | Core layout, components, responsive design |
| **Dark Mode** | `dark-mode.css` | Dark mode specific styles |
| **Components** | `components.css` | Button, header, toggle styles |
| **Modal** | `modal.css` | Settings modal and overlay |
| **Hierarchy Filter** | `hierarchy-filter.css` | Hierarchy filter panel styles |
| **Hierarchy Ledger** | `hierarchy-ledger.css` | Ledger table and related tasks panel styles |

**Frontend**: HTML + JavaScript with Force-Graph/D3.js for hierarchical visualization + DataTables for task listing

**Architecture Principles**:
- **Single Source of Truth**: One dashboard implementation with feature flags
- **Modular Design**: Services handle business logic, routes handle HTTP, templates handle presentation
- **Configuration-Driven**: Features enabled/disabled via `config.py`, not duplicate files

---

### 3. Shared Concepts

| Concept | Description |
|---------|-------------|
| **Task Model** | Core entity representing a task with title, notes, due date, status, parent/child relationships, tags |
| **Multi-Account Support** | Ability to switch between multiple Google accounts |
| **Tag System** | Hybrid tagging with `@user`, `#tag`, `[priority]` formats |
| **Sync** | Two-way synchronization with Google Tasks API |
| **Reports** | Various task reports (completion, pending, timeline, distribution) |

---

## Data Flow

```
User Input (CLI or Web)
        ↓
Command/Route Handler
        ↓
Service Layer (data_manager, sync)
        ↓
Storage (SQLite/JSON) or Google Tasks API
        ↓
Response/View Rendering
```

---

## Entry Points

| Application | Command |
|-------------|---------|
| CLI | `python -m gtasks_cli` or `gtasks` (after installation) |
| Dashboard | `python gtasks_dashboard/main_dashboard.py` |
| Installation | `python install.py` |

---

## Dependencies

- **Python 3.x**
- **Google APIs**: google-auth, google-api-python-client
- **CLI**: click (command-line interface)
- **Dashboard**: flask, d3.js (frontend)
- **Database**: sqlite3 (built-in)
- **Reports**: Various visualization and reporting modules

---

## 🧠 AI Context Layer (Git-Native)
| Component | Implementation | Responsibility |
|-----------|----------------|----------------|
| **Memory Store** | `context-llemur` | Stores logic/rules in `context/` as plain text |
| **Tooling** | **MCP** | Exposes `ctx_read/write` to Kilo, Continue, and OpenCode |
| **Version Sync** | **Git** | Synchronizes AI "memory" across local and remote clones |

---

## 🌐 Browser Debugging Tools (MCP)
| Tool | Purpose | Key Functions |
|------|---------|---------------|
| **Playwright** | Interactive browser automation and testing | `browser_fill_form`, `browser_click`, `browser_take_screenshot`, `browser_snapshot`, `browser_console_messages`, `browser_network_requests` |

### Playwright Usage Guidelines
- **Navigation**: Use `browser_navigate` to navigate to URLs
- **DOM Inspection**: Use `browser_snapshot` to inspect DOM structure
- **Form Interactions**: Use `browser_fill_form`, `browser_click` for form filling and clicking
- **Screenshots**: Use `browser_take_screenshot` to capture page screenshots
- **Console Errors**: Use `browser_console_messages` to retrieve error logs
- **Network Monitoring**: Use `browser_network_requests` to monitor API calls

### Browser Debugging Workflow
1. **For UI Issues**: Use `browser_snapshot` to inspect DOM structure
2. **For Console Errors**: Use `browser_console_messages` to retrieve error logs
3. **For Network Issues**: Use `browser_network_requests` to monitor API calls
4. **For Automation**: Use `browser_fill_form`, `browser_click` for form interactions and user flows

---

## 🏗 Core Components

### 1. gtasks_cli (Command Line)
- **Location**: `gtasks_cli/src/gtasks_cli/`
- **Logic**: Uses `click` for command routing.
- **Key Modules**: 
    - `commands/`: Individual logic for `add`, `list`, `sync`, etc.
    - `models/`: Schema for `Task` and `Account`.
    - `reports/`: Logic for generating pending/completion summaries.

### 2. gtasks_dashboard (Web UI)
- **Location**: `gtasks_dashboard/`
- **Stack**: Flask (Backend) + D3.js (Frontend Visualization).
- **Logic**: Handles hierarchical task views and priority management.

---

## 🔄 Data & Sync Flow


1. **Input**: User triggers action via CLI Command or Flask Route.
2. **Context Check**: AI verifies rules in `context/rules.md`.
3. **Service**: `data_manager` or `sync_service` processes logic.
4. **Storage**: SQLite/JSON updated; Google Tasks API synced via OAuth2.
5. **Context Update**: AI updates `architecture.md` if structure changed.

---

## 🚀 Entry Points
- **CLI**: `python -m gtasks_cli`
- **Web**: `python gtasks_dashboard/main_dashboard.py`
- **AI Sync**: `ctx save` (Run this before `git push`)