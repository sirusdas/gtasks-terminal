# GTasks-CLI System Architecture Mindmap

## Overview
GTasks-CLI is a sophisticated command-line task management system that bridges local task management with Google Tasks API, providing both offline and online functionality with advanced features like deduplication, reporting, and interactive mode.

---

## 🎯 Core Architecture Layers

### 1. **CLI Entry Point** (`src/gtasks_cli/main.py`)
```
├── Click Framework
├── Global Options (--google, --storage, --account, --auto-save)
├── Multi-Account Support
└── Command Registration
```

### 2. **Command Layer** (`src/gtasks_cli/commands/`)
```
├── Core Commands
│   ├── add.py           - Create new tasks
│   ├── list.py          - Display tasks with filtering/sorting
│   ├── search.py        - Multi-term search functionality
│   ├── view.py          - Task detail viewing
│   ├── done.py          - Mark tasks complete
│   ├── delete.py        - Soft delete tasks
│   ├── update.py        - Modify existing tasks
│   └── config.py        - Configuration management
│
├── Advanced Commands
│   ├── interactive.py   - Rich interactive mode
│   ├── advanced_sync.py - Optimized synchronization
│   ├── deduplicate.py   - Task deduplication
│   ├── generate_report.py - Analytics/reporting
│   ├── summary.py       - Task summaries
│   ├── tasklist.py      - Task list management
│   ├── account.py       - Multi-account handling
│   ├── auth.py          - Google authentication
│   ├── ai.py            - AI-powered features
│   └── mcp.py           - MCP server integration
│
└── Interactive Utils
    ├── common.py
    ├── display.py
    ├── done_commands.py
    ├── initial_commands.py
    ├── piped_commands.py
    └── tag_commands.py
```

### 3. **Core Business Logic** (`src/gtasks_cli/core/`)
```
└── task_manager.py
    ├── TaskManager Class
    ├── CRUD Operations
    │   ├── create_task()
    ├── list_tasks()
    ├── get_task()
    ├── update_task()
    ├── complete_task()
    └── delete_task()
    │
    ├── Dual Mode Support
    │   ├── Local Mode (Offline-first)
    │   └── Google Tasks Mode (API-first)
    │
    └── Storage Abstraction
        ├── SQLiteStorage Integration
        ├── LocalStorage Integration
        └── Auto-save Functionality
```

### 4. **Storage Layer** (`src/gtasks_cli/storage/`)
```
├── config_manager.py
│   ├── YAML Configuration
│   ├── Multi-Account Config
│   ├── Default Settings
│   └── Environment Integration
│
├── sqlite_storage.py
│   ├── SQLite Database
│   ├── Task Schema
│   ├── List Mappings
│   ├── Indexed Queries
│   └── Transaction Safety
│
└── local_storage.py
    ├── JSON File Storage
    ├── List Mappings
    ├── Offline Support
    └── Simple Persistence
```

### 5. **Integration Layer** (`src/gtasks_cli/integrations/`)
```
├── google_tasks_client.py
│   ├── OAuth2 Authentication
│   ├── Google Tasks API
│   ├── Task CRUD Operations
│   ├── List Management
│   ├── Duplicate Prevention
│   └── Error Handling
│
├── google_auth.py
│   ├── Credential Management
│   ├── Token Refresh
│   └── Multi-Account Auth
│
├── sync_manager.py
│   ├── Bi-directional Sync
│   ├── Conflict Resolution
│   ├── Deduplication
│   ├── Sync Metadata
│   └── Deletion Logging
│
└── advanced_sync_manager.py
    ├── Optimized Queries
    ├── Batch Operations
    ├── Performance Tuning
    └── Error Recovery
```

### 6. **Data Models** (`src/gtasks_cli/models/`)
```
├── task.py
│   ├── Task Model (Pydantic)
│   ├── Priority Levels
│   ├── Status Management
│   ├── Date Handling
│   ├── Recurring Tasks
│   ├── Dependencies
│   └── Metadata Support
│
└── task_list.py
    └── TaskList Model
```

### 7. **Reports & Analytics** (`src/gtasks_cli/reports/`)
```
├── base_report.py
├── task_completion_report.py
├── task_creation_report.py
├── task_distribution_report.py
├── timeline_report.py
├── overdue_tasks_report.py
├── pending_tasks_report.py
├── future_timeline_report.py
├── organized_tasks_report.py
├── custom_filtered_report.py
└── task_completion_rate_report.py
```

### 8. **Utilities** (`src/gtasks_cli/utils/`)
```
├── datetime_utils.py
│   ├── Timezone Handling
│   ├── Date Normalization
│   └── Format Conversion
│
├── display.py
│   ├── Rich Console Output
│   ├── Color Coding
│   └── Table Formatting
│
├── task_deduplication.py
│   ├── Signature Generation
│   ├── Duplicate Detection
│   └── Cleanup Operations
│
├── tag_extractor.py
│   ├── Tag Parsing ([tag] syntax)
│   ├── Tag Filtering
│   └── Tag Management
│
├── email_sender.py
│   ├── SMTP Integration
│   ├── Report Emailing
│   └── Template Support
│
├── logger.py
│   ├── Structured Logging
│   ├── Level Control
│   └── File/Rotation Support
│
└── exceptions.py
    └── Custom Exception Classes
```

---

## 🔄 Data Flow Architecture

### Task Creation Flow
```
User Input → CLI Command → TaskManager → Storage Layer
                                      ↓
                           Local/Google Tasks API
```

### Task Listing Flow
```
CLI Command → TaskManager → Storage Layer
                ↓
        Filtering & Sorting
                ↓
        Display Formatting
                ↓
        Rich Console Output
```

### Sync Flow
```
Manual/Auto Sync → SyncManager → Bi-directional Sync
                                    ↓
                    ┌──────────────┼──────────────┐
                    ↓              ↓              ↓
            Local Storage    Conflict Resolution   Google Tasks API
```

---

## 🔑 Key Features Architecture

### 1. **Multi-Account Support**
```
GTASKS_CONFIG_DIR Environment Variable
        ↓
Account-Specific Directories
        ↓
Separate Storage & Auth Tokens
```

### 2. **Interactive Mode**
```
Rich Terminal UI with Rich Library
        ↓
Keyboard Navigation & Commands
        ↓
Piped Command Support
        ↓
State Management (back/default)
        ↓
Bulk Operations Support
```

### 3. **Advanced Filtering**
```
Multiple Filter Types:
├── Status (pending/completed/deleted)
├── Priority (low/medium/high/critical)
├── Time Period (today/week/month/custom)
├── Project & Tags
├── Search Terms (multi-term with |)
└── Recurring Tasks
```

### 4. **Deduplication System**
```
Task Signature Generation
        ↓
Hash-based Comparison
        ↓
Duplicate Detection
        ↓
Cleanup Operations
```

### 5. **Offline-First Design**
```
Local Storage Primary
        ↓
Google Tasks Secondary
        ↓
Auto-sync on Change
        ↓
Conflict Resolution
```

---

## 📁 File Structure Overview

```
gtasks_cli/
├── src/gtasks_cli/
│   ├── __init__.py
│   ├── main.py                 # CLI Entry Point
│   ├── commands/               # Command Implementations
│   ├── core/                  # Business Logic
│   ├── integrations/          # External APIs
│   ├── models/                # Data Models
│   ├── reports/               # Analytics
│   ├── storage/               # Persistence Layer
│   ├── ui/                   # User Interface
│   └── utils/                # Helper Functions
├── config/
│   └── default_config.yaml   # Default Configuration
├── requirements.txt           # Dependencies
├── setup.py                  # Package Setup
└── README.md                 # Documentation
```

---

## 🚀 Usage Patterns

### Basic Usage
```bash
gtasks add "Task title" --due tomorrow --priority high
gtasks list --status pending --filter this_week
gtasks done 1
gtasks interactive
```

### Advanced Usage
```bash
gtasks --google --storage sqlite --account work list
gtasks sync --advanced
gtasks deduplicate --cleanup
gtasks generate_report --type completion_rate --email
```

### Configuration
```bash
gtasks config set display.colors true
gtasks config set sync.auto_save true
gtasks account add work --credentials path/to/creds.json
```

---

## 🔧 Technology Stack

### Core Technologies
- **Python 3.8+** - Primary Language
- **Click** - CLI Framework
- **Pydantic** - Data Validation & Models
- **Rich** - Terminal UI Enhancement
- **SQLite** - Local Database
- **Google APIs Client** - Google Tasks Integration

### Key Libraries
- **google-auth-oauthlib** - OAuth2 Authentication
- **google-auth-httplib2** - HTTP Transport
- **PyYAML** - Configuration Management
- **sqlite3** - Database Operations
- **prompt_toolkit** - Interactive CLI Enhancement

---

## 🎯 Design Patterns Used

### 1. **Strategy Pattern**
- Different storage backends (Local/SQLite)
- Different sync strategies (Basic/Advanced)

### 2. **Factory Pattern**
- TaskManager creation based on configuration
- Report generation based on type

### 3. **Observer Pattern**
- Auto-save notifications
- Sync state changes

### 4. **Command Pattern**
- CLI commands as encapsulated operations
- Interactive mode command processing

### 5. **Repository Pattern**
- Abstract storage layer
- Multiple persistence implementations

---

## 🔄 System Workflows

### 1. **Initial Setup**
```
Package Installation
        ↓
Setup Assistant Execution
        ↓
Configuration Creation
        ↓
Google OAuth Setup
        ↓
First Sync
```

### 2. **Daily Usage**
```
Task Creation
        ↓
Local Storage
        ↓
Auto-sync (if enabled)
        ↓
Google Tasks API
        ↓
Cross-device Sync
```

### 3. **Interactive Session**
```
Interactive Mode Entry
        ↓
Task List Display
        ↓
Command Processing
        ↓
State Management
        ↓
Operation Execution
```

---

## 📊 Performance Considerations

### Optimization Strategies
- **SQLite Indexing** - Fast queries on common fields
- **Batch Operations** - Reduce API calls
- **Lazy Loading** - Load data only when needed
- **Caching** - Local task caching
- **Incremental Sync** - Only changed data

### Scalability Features
- **Pagination** - Large task list handling
- **Background Sync** - Non-blocking operations
- **Memory Management** - Efficient data structures
- **Connection Pooling** - API request optimization

---

This mindmap provides a comprehensive overview of the GTasks-CLI system architecture, showing how all components work together to provide a powerful, flexible, and user-friendly task management solution.