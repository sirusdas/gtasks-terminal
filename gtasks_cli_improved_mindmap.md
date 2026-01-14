# GTasks-CLI System Architecture Mindmap

## 📋 Table of Contents
1. [System Overview](#system-overview)
2. [Core Architecture Layers](#core-architecture-layers)
3. [Data Flow Architecture](#data-flow-architecture)
4. [Key Features Architecture](#key-features-architecture)
5. [File Structure Overview](#file-structure-overview)
6. [Usage Patterns](#usage-patterns)
7. [Technology Stack](#technology-stack)
8. [Design Patterns](#design-patterns)
9. [System Workflows](#system-workflows)
10. [Performance Considerations](#performance-considerations)

---

## System Overview
GTasks-CLI is a sophisticated command-line task management system that bridges local task management with Google Tasks API, providing both offline and online functionality with advanced features like deduplication, reporting, and interactive mode.

---

## Core Architecture Layers

### 1. CLI Entry Point
```
gtasks_cli/
└── src/gtasks_cli/main.py
    ├── Click Framework
    ├── Global Options (--google, --storage, --account, --auto-save)
    ├── Multi-Account Support
    └── Command Registration
```

### 2. Command Layer
```
gtasks_cli/src/gtasks_cli/commands/
├── Core Commands
│   ├── add.py              → Create new tasks
│   ├── list.py             → Display tasks with filtering/sorting
│   ├── search.py           → Multi-term search functionality
│   ├── view.py             → Task detail viewing
│   ├── done.py             → Mark tasks complete
│   ├── delete.py           → Soft delete tasks
│   ├── update.py           → Modify existing tasks
│   └── config.py           → Configuration management
│
├── Advanced Commands
│   ├── interactive.py      → Rich interactive mode
│   ├── advanced_sync.py    → Optimized synchronization
│   ├── deduplicate.py      → Task deduplication
│   ├── generate_report.py  → Analytics/reporting
│   ├── summary.py          → Task summaries
│   ├── tasklist.py         → Task list management
│   ├── account.py          → Multi-account handling
│   ├── auth.py             → Google authentication
│   ├── ai.py               → AI-powered features
│   └── mcp.py              → MCP server integration
│
└── Interactive Utils
    ├── common.py           → Shared utilities
    ├── display.py          → Rich console display
    ├── done_commands.py    → Task completion handlers
    ├── initial_commands.py → Command initialization
    ├── piped_commands.py   → Command piping
    └── tag_commands.py     → Tag management
```

### 3. Core Business Logic
```
gtasks_cli/src/gtasks_cli/core/
└── task_manager.py
    ├── TaskManager Class
    ├── CRUD Operations
    │   ├── create_task()      → Create new tasks
    │   ├── list_tasks()       → Retrieve and filter tasks
    │   ├── get_task()         → Get specific task by ID
    │   ├── update_task()      → Modify task attributes
    │   ├── complete_task()    → Mark tasks as completed
    │   └── delete_task()      → Soft delete tasks
    │
    ├── Dual Mode Support
    │   ├── Local Mode         → Offline-first operations
    │   └── Google Tasks Mode  → API-first operations
    │
    └── Storage Abstraction
        ├── SQLiteStorage Integration
        ├── LocalStorage Integration
        └── Auto-save Functionality
```

### 4. Storage Layer
```
gtasks_cli/src/gtasks_cli/storage/
├── config_manager.py
│   ├── YAML Configuration Management
│   ├── Multi-Account Configuration
│   ├── Default Settings
│   └── Environment Variable Integration
│
├── sqlite_storage.py
│   ├── SQLite Database Engine
│   ├── Task Schema Definition
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

### 5. Integration Layer
```
gtasks_cli/src/gtasks_cli/integrations/
├── google_tasks_client.py
│   ├── OAuth2 Authentication
│   ├── Google Tasks API Integration
│   ├── Task CRUD Operations
│   ├── List Management
│   ├── Duplicate Prevention
│   └── Error Handling
│
├── google_auth.py
│   ├── Credential Management
│   ├── Token Refresh
│   └── Multi-Account Authentication
│
├── sync_manager.py
│   ├── Bi-directional Synchronization
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

### 6. Data Models
```
gtasks_cli/src/gtasks_cli/models/
├── task.py
│   ├── Task Model (Pydantic)
│   ├── Priority Levels (low, medium, high, critical)
│   ├── Status Management (pending, completed, deleted, etc.)
│   ├── Date Handling (due, created, modified, completed)
│   ├── Recurring Tasks Support
│   ├── Dependencies
│   └── Metadata Support
│
└── task_list.py
    └── TaskList Model
```

### 7. Reports & Analytics
```
gtasks_cli/src/gtasks_cli/reports/
├── base_report.py                  → Report foundation
├── task_completion_report.py       → Completion statistics
├── task_creation_report.py         → Creation patterns
├── task_distribution_report.py     → Distribution analysis
├── timeline_report.py              → Timeline views
├── overdue_tasks_report.py         → Overdue task tracking
├── pending_tasks_report.py         → Pending task analysis
├── future_timeline_report.py      → Future planning
├── organized_tasks_report.py       → Organized views
├── custom_filtered_report.py       → Custom filtering
└── task_completion_rate_report.py  → Rate analytics
```

### 8. Utilities
```
gtasks_cli/src/gtasks_cli/utils/
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

## Data Flow Architecture

### Task Creation Flow
```
┌─────────────┐    ┌──────────────┐    ┌──────────────┐    ┌─────────────────┐
│ User Input  │───▶│ CLI Command  │───▶│ TaskManager  │───▶│ Storage Layer   │
└─────────────┘    └──────────────┘    └──────────────┘    └─────────────────┘
                                                              │
                                                              ▼
                                                       ┌─────────────────┐
                                                       │ Local/Google    │
                                                       │ Tasks API       │
                                                       └─────────────────┘
```

### Task Listing Flow
```
┌─────────────┐    ┌──────────────┐    ┌──────────────┐    ┌─────────────────┐
│ CLI Command │───▶│ TaskManager  │───▶│ Storage      │───▶│ Filtering &     │
└─────────────┘    └──────────────┘    └──────────────┘    │ Sorting        │
                                                              │
                                                              ▼
                                                       ┌─────────────────┐
                                                       │ Display         │
                                                       │ Formatting      │
                                                       └─────────────────┘
                                                              │
                                                              ▼
                                                       ┌─────────────────┐
                                                       │ Rich Console    │
                                                       │ Output          │
                                                       └─────────────────┘
```

### Sync Flow
```
┌─────────────┐    ┌──────────────┐    ┌──────────────┐
│ Manual/Auto │───▶│ SyncManager  │───▶│ Bi-directional│
│ Sync        │    └──────────────┘    │ Sync         │
└─────────────┘                         └──────────────┘
                                            │
                    ┌───────────────────────┼───────────────────────┐
                    ▼                       ▼                       ▼
            ┌──────────────┐    ┌──────────────────┐    ┌─────────────────┐
            │ Local        │    │ Conflict         │    │ Google Tasks    │
            │ Storage      │    │ Resolution       │    │ API             │
            └──────────────┘    └──────────────────┘    └─────────────────┘
```

---

## Key Features Architecture

### 1. Multi-Account Support
```
┌─────────────────────────────────┐
│ GTASKS_CONFIG_DIR Environment   │
│ Variable                       │
└─────────────┬───────────────────┘
              │
              ▼
┌─────────────────────────────────┐
│ Account-Specific Directories     │
│ ├── ~/.gtasks/work/            │
│ ├── ~/.gtasks/personal/        │
│ └── ~/.gtasks/default/          │
└─────────────┬───────────────────┘
              │
              ▼
┌─────────────────────────────────┐
│ Separate Storage & Auth Tokens  │
│ per Account                     │
└─────────────────────────────────┘
```

### 2. Interactive Mode
```
┌─────────────────────────────────┐
│ Rich Terminal UI (Rich Library) │
└─────────────┬───────────────────┘
              │
              ▼
┌─────────────────────────────────┐
│ Keyboard Navigation & Commands   │
└─────────────┬───────────────────┘
              │
              ▼
┌─────────────────────────────────┐
│ Piped Command Support           │
└─────────────┬───────────────────┘
              │
              ▼
┌─────────────────────────────────┐
│ State Management                │
│ (back/default)                 │
└─────────────┬───────────────────┘
              │
              ▼
┌─────────────────────────────────┐
│ Bulk Operations Support        │
└─────────────────────────────────┘
```

### 3. Advanced Filtering
```
Multiple Filter Types:
├── Status Filter      → pending/completed/deleted
├── Priority Filter   → low/medium/high/critical
├── Time Period       → today/week/month/custom
├── Project & Tags    → [tag] syntax support
├── Search Terms     → multi-term with | logic
└── Recurring Tasks  → template-based
```

### 4. Deduplication System
```
┌─────────────────────────────────┐
│ Task Signature Generation       │
└─────────────┬───────────────────┘
              │
              ▼
┌─────────────────────────────────┐
│ Hash-based Comparison          │
└─────────────┬───────────────────┘
              │
              ▼
┌─────────────────────────────────┐
│ Duplicate Detection            │
└─────────────┬───────────────────┘
              │
              ▼
┌─────────────────────────────────┐
│ Cleanup Operations             │
└─────────────────────────────────┘
```

### 5. Offline-First Design
```
┌─────────────────────────────────┐
│ Local Storage Primary          │
└─────────────┬───────────────────┘
              │
              ▼
┌─────────────────────────────────┐
│ Google Tasks Secondary         │
└─────────────┬───────────────────┘
              │
              ▼
┌─────────────────────────────────┐
│ Auto-sync on Change            │
└─────────────┬───────────────────┘
              │
              ▼
┌─────────────────────────────────┐
│ Conflict Resolution            │
└─────────────────────────────────┘
```

---

## File Structure Overview
```
gtasks_cli/
├── src/gtasks_cli/
│   ├── __init__.py
│   ├── main.py                 # CLI Entry Point
│   ├── commands/               # Command Implementations
│   │   ├── core_commands/     # Basic CRUD operations
│   │   ├── advanced_commands/ # Enhanced features
│   │   └── interactive_utils/ # Interactive mode support
│   ├── core/                  # Business Logic
│   │   └── task_manager.py    # Central task management
│   ├── integrations/          # External APIs
│   │   ├── google_tasks_client.py
│   │   ├── google_auth.py
│   │   ├── sync_manager.py
│   │   └── advanced_sync_manager.py
│   ├── models/                # Data Models
│   │   ├── task.py           # Task data structure
│   │   └── task_list.py      # TaskList data structure
│   ├── reports/               # Analytics & Reporting
│   │   ├── base_report.py    # Report foundation
│   │   ├── *_report.py       # Specific report types
│   ├── storage/               # Persistence Layer
│   │   ├── config_manager.py # Configuration management
│   │   ├── sqlite_storage.py # SQLite implementation
│   │   └── local_storage.py  # JSON implementation
│   ├── ui/                   # User Interface
│   └── utils/                # Helper Functions
│       ├── datetime_utils.py  # Date/time handling
│       ├── display.py         # Rich console output
│       ├── task_deduplication.py
│       ├── tag_extractor.py   # Tag processing
│       ├── email_sender.py    # Email functionality
│       ├── logger.py          # Logging system
│       └── exceptions.py      # Custom exceptions
├── config/
│   └── default_config.yaml   # Default Configuration
├── requirements.txt           # Dependencies
├── setup.py                  # Package Setup
├── pyproject.toml           # Modern Python packaging
└── README.md                # Documentation
```

---

## Usage Patterns

### Basic Usage
```bash
# Create and manage tasks
gtasks add "Task title" --due tomorrow --priority high
gtasks list --status pending --filter this_week
gtasks done 1
gtasks interactive

# Configuration
gtasks config set display.colors true
```

### Advanced Usage
```bash
# Multi-account operations
gtasks --google --storage sqlite --account work list

# Advanced synchronization
gtasks sync --advanced
gtasks deduplicate --cleanup

# Comprehensive reporting
gtasks generate_report --type completion_rate --email user@example.com
gtasks generate_report --tags "urgent|work" --filter this_month
```

### Interactive Mode
```bash
# Rich interactive experience
gtasks interactive
> list --status pending --filter today
> tags urgent
> update-tags ADD[1,2|work],DEL[3|old]
> search "meeting|review"
> quit
```

---

## Technology Stack

### Core Technologies
- **Python 3.8+**           → Primary Language
- **Click**                 → CLI Framework
- **Pydantic**              → Data Validation & Models
- **Rich**                  → Terminal UI Enhancement
- **SQLite**                → Local Database
- **Google APIs Client**    → Google Tasks Integration

### Key Libraries
- **google-auth-oauthlib**  → OAuth2 Authentication
- **google-auth-httplib2** → HTTP Transport
- **PyYAML**               → Configuration Management
- **sqlite3**              → Database Operations
- **prompt_toolkit**       → Interactive CLI Enhancement
- **re**                  → Regular Expressions

### Development Tools
- **pytest**               → Testing Framework
- **black**                → Code Formatting
- **mypy**                → Type Checking
- **flake8**              → Linting

---

## Design Patterns

### 1. Strategy Pattern
```python
# Different storage strategies
class TaskManager:
    def __init__(self, storage_backend='sqlite'):
        if storage_backend == 'sqlite':
            self.storage = SQLiteStorage()
        elif storage_backend == 'json':
            self.storage = LocalStorage()
```

### 2. Factory Pattern
```python
# TaskManager creation based on configuration
def create_task_manager(config):
    return TaskManager(
        storage_backend=config.get('storage', 'sqlite'),
        use_google_tasks=config.get('use_google', False)
    )
```

### 3. Observer Pattern
```python
# Auto-save notifications
class TaskManager:
    def __init__(self):
        self.observers = []
    
    def notify_observers(self, event):
        for observer in self.observers:
            observer.update(event)
```

### 4. Command Pattern
```python
# CLI commands as encapsulated operations
class Command:
    def execute(self):
        pass
    
    def undo(self):
        pass
```

### 5. Repository Pattern
```python
# Abstract storage layer
class TaskRepository:
    def save(self, task):
        pass
    
    def find_by_id(self, task_id):
        pass
    
    def find_all(self):
        pass
```

---

## System Workflows

### 1. Initial Setup
```
┌─────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│ Package         │───▶│ Setup Assistant  │───▶│ Configuration    │
│ Installation    │    │ Execution        │    │ Creation         │
└─────────────────┘    └──────────────────┘    └──────────────────┘
                                                        │
                                                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│ Google OAuth    │───▶│ First Sync       │───▶│ Ready for Use    │
│ Setup           │    │ Operation        │    │                  │
└─────────────────┘    └──────────────────┘    └──────────────────┘
```

### 2. Daily Usage
```
┌─────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│ Task Creation   │───▶│ Local Storage    │───▶│ Auto-sync        │
└─────────────────┘    └──────────────────┘    │ (if enabled)     │
                                                 └──────────────────┘
                                                                │
                                                                ▼
┌─────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│ Google Tasks    │◀───│ Cross-device     │◀───│ Task Available   │
│ API             │    │ Sync             │    │ Everywhere       │
└─────────────────┘    └──────────────────┘    └──────────────────┘
```

### 3. Interactive Session
```
┌─────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│ Interactive     │───▶│ Task List        │───▶│ Command          │
│ Mode Entry      │    │ Display          │    │ Processing       │
└─────────────────┘    └──────────────────┘    └──────────────────┘
                                                        │
                                                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│ State           │───▶│ Operation         │───▶│ Result Display   │
│ Management       │    │ Execution         │    │ & Update         │
└─────────────────┘    └──────────────────┘    └──────────────────┘
```

---

## Performance Considerations

### Optimization Strategies
```
┌─────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│ SQLite          │    │ Batch            │    │ Lazy             │
│ Indexing        │───▶│ Operations       │───▶│ Loading          │
└─────────────────┘    └──────────────────┘    └──────────────────┘
        │                       │                       │
        │                       │                       │
        ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│ Fast queries    │    │ Reduced API      │    │ Data loaded      │
│ on common       │    │ calls           │    │ only when needed │
│ fields          │    │                 │    │                 │
└─────────────────┘    └──────────────────┘    └──────────────────┘
```

### Scalability Features
- **Pagination**         → Large task list handling
- **Background Sync**    → Non-blocking operations
- **Memory Management**   → Efficient data structures
- **Connection Pooling** → API request optimization
- **Caching Strategy**   → Local task caching
- **Incremental Sync**   → Only changed data

---

## Full-Screen Viewing

This mindmap is designed for full-screen viewing. To view optimally:

### Recommended Settings
- **Terminal Size**: Minimum 120x40 characters
- **Font**: Monospace (Courier New, Monaco, or Consolas)
- **Zoom**: 100-150% for comfortable reading

### Navigation
- Use **Page Up/Down** for section navigation
- Use **Ctrl+F** to search within the document
- Use **Ctrl+Home** to return to top
- Use **Ctrl+End** to jump to end

### Presentation Mode
For presentation or demonstrations:
1. Open in full-screen terminal or browser
2. Use larger font size (150-200%)
3. Navigate section by section using scroll
4. Use line numbers for quick reference

---

*This mindmap provides a comprehensive overview of the GTasks-CLI system architecture, showing how all components work together to provide a powerful, flexible, and user-friendly task management solution.*