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
| **Entry Point** | `gtasks_dashboard/main_dashboard.py` | Flask app initialization, blueprint registration |
| **Routes/API** | `gtasks_dashboard/routes/` | API and dashboard route handlers |
| **Routes** | `gtasks_dashboard/routes/api.py`, `dashboard.py` | REST API endpoints and page routes |
| **Models** | `gtasks_dashboard/models/` | Data models (Task, Account, DashboardStats, HybridTags) |
| **Services** | `gtasks_dashboard/services/` | Business logic (data_manager) |
| **Modules** | `gtasks_dashboard/modules/` | Feature modules (priority_system, tag_manager, account_manager, settings_manager) |
| **UI Components** | `gtasks_dashboard/ui_components.py` | Reusable UI components |
| **Config** | `gtasks_dashboard/config.py` | Dashboard configuration |

**Frontend**: HTML + JavaScript with D3.js for hierarchical visualization

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
