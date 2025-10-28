# Google Tasks CLI Application - Comprehensive Development Prompt

## Project Overview

Build a powerful, feature-rich CLI application for Google Tasks management in Python, combining the simplicity of task management with advanced productivity features. This application should be well-architected, maintainable, and follow Python best practices.

---

## Architecture & Design Patterns

### 1. **Project Structure**
```
gtasks-cli/
├── src/
│   ├── __init__.py
│   ├── main.py                 # Entry point
│   ├── cli/
│   │   ├── __init__.py
│   │   ├── commands.py         # CLI command definitions
│   │   ├── decorators.py       # Command decorators
│   │   └── validators.py       # Input validation
│   ├── core/
│   │   ├── __init__.py
│   │   ├── task_manager.py     # Task operations
│   │   ├── tasklist_manager.py # Tasklist operations
│   │   ├── context_manager.py  # Context switching
│   │   └── filter_engine.py    # Advanced filtering
│   ├── integrations/
│   │   ├── __init__.py
│   │   ├── google_auth.py      # OAuth2 authentication
│   │   ├── google_tasks_api.py # API wrapper
│   │   └── sync_manager.py     # Synchronization logic
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── local_storage.py    # Local caching/storage
│   │   └── config_manager.py   # Configuration management
│   ├── reports/
│   │   ├── __init__.py
│   │   ├── report_engine.py    # Report generation
│   │   └── exporters.py        # Export to various formats
│   ├── analytics/
│   │   ├── __init__.py
│   │   ├── statistics.py       # Task statistics
│   │   └── burndown.py         # Burndown charts
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── formatters.py       # Output formatting
│   │   ├── tables.py           # Table rendering
│   │   └── prompts.py          # Interactive prompts
│   └── utils/
│       ├── __init__.py
│       ├── logger.py           # Logging configuration
│       ├── exceptions.py       # Custom exceptions
│       └── helpers.py          # Utility functions
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── config/
│   └── default_config.yaml
├── requirements.txt
├── setup.py
├── README.md
└── .env.example
```

### 2. **Design Patterns to Implement**

#### **Command Pattern**
- Each CLI command is a separate class implementing a common interface
- Allows for easy addition of new commands
- Supports undo/redo functionality

```python
from abc import ABC, abstractmethod

class Command(ABC):
    @abstractmethod
    def execute(self):
        pass
    
    @abstractmethod
    def undo(self):
        pass
```

#### **Repository Pattern**
- Abstract data access layer for Google Tasks API
- Easy to mock for testing
- Supports caching and offline mode

```python
class TaskRepository:
    def __init__(self, api_client, cache):
        self.api = api_client
        self.cache = cache
    
    def get_task(self, task_id):
        # Check cache first, then API
        pass
```

#### **Factory Pattern**
- Create different types of reports, exporters, and filters
- Extensible for new formats

```python
class ReportFactory:
    @staticmethod
    def create_report(report_type):
        if report_type == 'list':
            return ListReport()
        elif report_type == 'burndown':
            return BurndownReport()
```

#### **Strategy Pattern**
- Different sorting strategies (by due date, priority, title)
- Different filtering strategies
- Different export formats

#### **Singleton Pattern**
- Configuration manager
- Logger instance
- Authentication manager

---

## Core Features & Implementation Details

### 1. **Authentication & Authorization**

#### OAuth2 Implementation
```python
# Key requirements:
- Use google-auth-oauthlib for OAuth2 flow
- Support multiple authentication methods:
  - Desktop application flow (default)
  - Service account (for automation)
  - Refresh token management
- Store credentials securely in ~/.gtasks/credentials.json
- Auto-refresh expired tokens
- Support multiple Google accounts (profile switching)
```

**Implementation Details:**
- Implement `GoogleAuthManager` class
- Support scopes: `https://www.googleapis.com/auth/tasks`
- Handle authorization errors gracefully
- Provide clear OAuth2 setup instructions
- Support proxy authentication via environment variables

### 2. **Task Management Features**

#### A. Basic Task Operations

**Add Tasks**
```python
# Features:
- Simple add: gtasks add "Task title"
- Add with description: gtasks add "Title" -d "Description"
- Add with due date: gtasks add "Title" --due "2024-12-31"
- Add with notes: gtasks add "Title" --notes "Additional info"
- Quick add with natural language parsing: gtasks add "Buy milk tomorrow at 5pm"
- Add to specific tasklist: gtasks add "Title" -l "Work"
- Add with priority levels
- Add recurring tasks with patterns
```

**View/List Tasks**
```python
# Features:
- List all pending tasks: gtasks list
- Include completed: gtasks list --completed
- Filter by tasklist: gtasks list -l "Work"
- Filter by date range: gtasks list --from "2024-01-01" --to "2024-12-31"
- Filter by status: gtasks list --status completed|pending|deleted
- Sort options: --sort due|priority|title|position|created|modified
- Limit results: gtasks list --limit 10
- Show detailed view: gtasks list --detailed
- Tree view for subtasks
```

**Modify Tasks**
```python
# Features:
- Modify title: gtasks modify <id> --title "New title"
- Modify description: gtasks modify <id> --desc "New description"
- Change due date: gtasks modify <id> --due "2024-12-31"
- Move to different tasklist: gtasks modify <id> --move-to "Work"
- Change position: gtasks modify <id> --position 3
- Bulk modify: gtasks modify <filter> --set priority:high
- Append to description: gtasks append <id> "Additional text"
- Prepend to description: gtasks prepend <id> "Start text"
```

**Complete Tasks**
```python
# Features:
- Mark as done: gtasks done <id>
- Mark multiple: gtasks done <id1> <id2> <id3>
- Mark by filter: gtasks done project:urgent
- Completion timestamp recording
- Support for recurring task generation upon completion
```

**Delete Tasks**
```python
# Features:
- Soft delete (mark as deleted): gtasks delete <id>
- Hard delete (purge): gtasks purge <id>
- Delete all completed: gtasks delete --completed
- Bulk delete by filter: gtasks delete project:archive
```

#### B. Advanced Task Features

**Task Dependencies**
```python
# Implement blocking/blocked relationships
- Block a task: gtasks <id> depends <id2>
- Show blocked tasks: gtasks list --blocked
- Show blocking tasks: gtasks list --blocking
- Auto-update status when dependencies complete
```

**Annotations**
```python
# Add time-stamped notes to tasks
- Add annotation: gtasks annotate <id> "Progress update"
- List annotations: gtasks <id> info --annotations
- Delete annotation: gtasks denotate <id> <annotation-id>
```

**Subtasks**
```python
# Hierarchical task management
- Add subtask: gtasks add "Subtask" --parent <parent-id>
- List with subtasks: gtasks list --show-subtasks
- Indent/dedent: gtasks <id> indent|dedent
- Auto-complete parent when all subtasks done
```

**Task Attributes**
```python
# Support rich task metadata:
- Priority: low, medium, high, critical
- Projects: Grouping mechanism
- Tags: Multiple tags per task
- Due date with time
- Reminder times
- Estimated duration
- Actual time spent
- Status: pending, in-progress, completed, waiting, deleted
- Created/modified timestamps
- Notes (multi-line)
```

### 3. **Tasklist Management**

```python
# Features:
- Create tasklist: gtasks tasklist add "Work"
- List all tasklists: gtasks tasklist list
- Delete tasklist: gtasks tasklist delete "Work"
- Rename tasklist: gtasks tasklist rename "Work" "Professional"
- Set default tasklist: gtasks tasklist default "Work"
- Archive tasklist: gtasks tasklist archive "Old Project"
- Share tasklist (if API supports)
```

### 4. **Filtering & Searching**

Implement a powerful filter engine similar to TaskWarrior:

```python
# Filter syntax:
gtasks list project:work status:pending priority:high
gtasks list due.before:today
gtasks list '(priority:high or priority:critical) and status:pending'
gtasks list description.contains:urgent

# Operators:
- Equality: project:work
- Comparison: due.before:, due.after:, priority.above:
- Logical: and, or, not, ()
- Pattern matching: description.contains:, title.matches:
- Date math: due:today, due:tomorrow, due:eow, due:eom
```

**Implementation:**
- Create a `FilterEngine` class
- Support complex boolean expressions
- Parse date expressions (today, tomorrow, +3d, eow, eom)
- Support regex patterns
- Virtual tags (OVERDUE, COMPLETED, PENDING, etc.)

### 5. **Context Management**

```python
# Save and switch between filter contexts
- Define context: gtasks context define work project:work status:pending
- List contexts: gtasks context list
- Set active context: gtasks context use work
- Clear context: gtasks context none
- Show current: gtasks context show

# When context is active, all commands use that filter
```

### 6. **Reports & Visualization**

#### Built-in Reports

**List Reports**
```python
- pending: All pending tasks
- active: Currently active/in-progress tasks
- completed: Recently completed tasks
- overdue: Tasks past due date
- today: Due today
- week: Due this week
- next: Most urgent tasks (by priority and due date)
- blocked: Tasks waiting on dependencies
- blocking: Tasks blocking others
- waiting: Tasks with waiting status
- recurring: All recurring tasks
- minimal: Compact view
- long: Detailed view
```

**Analytics Reports**
```python
- summary: Overview of tasks by project, status, priority
- statistics: Completion rates, average time, etc.
- burndown: Burndown chart (daily, weekly, monthly)
- history: Task creation/completion trends
- calendar: Calendar view with tasks
- timesheet: Time tracking report
```

**Custom Reports**
- Allow users to define custom reports with specific:
  - Columns to display
  - Default filter
  - Sort order
  - Output format

#### Visualization

```python
# ASCII charts and graphs
- Burndown charts using matplotlib or ASCII art
- Calendar views
- Priority distribution
- Project completion percentages
- Activity heatmaps
```

### 7. **Time Tracking**

```python
# Start/stop timer on tasks
- Start: gtasks start <id>
- Stop: gtasks stop <id>
- Toggle: gtasks toggle <id>
- Track multiple active tasks
- Generate timesheet reports
- Calculate actual vs estimated time
```

### 8. **Recurring Tasks**

```python
# Support various recurrence patterns
- Daily: gtasks add "Stand-up" --recur daily
- Weekly: gtasks add "Report" --recur weekly --on monday
- Monthly: gtasks add "Review" --recur monthly --on 1st
- Yearly: gtasks add "Birthday" --recur yearly
- Custom: gtasks add "Task" --recur "every 3 days"
- Until date: --until "2024-12-31"
- After N occurrences: --count 10

# Auto-generate next occurrence when completed
```

### 9. **Import/Export**

```python
# Support multiple formats
- JSON: gtasks export --format json > tasks.json
- CSV: gtasks export --format csv > tasks.csv
- Markdown: gtasks export --format markdown > tasks.md
- iCalendar: gtasks export --format ical > tasks.ics
- Import: gtasks import --format json tasks.json

# Batch operations via import
# Backup entire task database
```

### 10. **Sync & Offline Mode**

```python
# Features:
- Local caching for offline work
- Sync command: gtasks sync
- Auto-sync on actions (configurable)
- Conflict resolution strategies
- Manual sync control
- Sync status display
```

### 11. **Undo/Redo Functionality**

```python
# Command history tracking
- Undo last command: gtasks undo
- Show undo history: gtasks history
- Undo specific action: gtasks undo <id>
- Redo: gtasks redo

# Store command log with ability to reverse
```

### 12. **Productivity Features**

#### Pomodoro Timer
```python
# Integrated pomodoro technique
- Start pomodoro: gtasks pomodoro start <task-id>
- Break: gtasks pomodoro break
- Status: gtasks pomodoro status
- Statistics: gtasks pomodoro stats
- Configurable durations (25min work, 5min break)
```

#### Habit Tracking
```python
# Track habits linked to recurring tasks
- Create habit: gtasks habit add "Exercise" --daily
- Log completion: gtasks habit done "Exercise"
- Streak tracking
- Habit statistics and charts
```

#### Journal Integration
```python
# Daily journal entries
- Add journal entry: gtasks journal "Today's reflection"
- List entries: gtasks journal list
- Export journal: gtasks journal export
```

### 13. **Configuration Management**

```python
# Config file: ~/.gtasks/config.yaml
settings:
  default_tasklist: "My Tasks"
  date_format: "%Y-%m-%d"
  time_format: "%H:%M"
  sync_on_action: true
  offline_mode: false
  
display:
  colors: true
  table_style: "simple"
  max_width: 100
  
aliases:
  - ls: list
  - rm: delete
  
custom_reports:
  urgent:
    filter: "priority:high status:pending"
    sort: "due"
    columns: ["id", "title", "due", "project"]

# Commands:
gtasks config set display.colors false
gtasks config get date_format
gtasks config list
```

### 14. **Interactive TUI Dashboard** (Optional Advanced Feature)

```python
# Rich terminal UI using libraries like:
# - textual
# - rich
# - urwid

# Features:
- Dashboard view of all tasklists
- Quick task entry
- Drag-and-drop reordering
- Real-time sync indication
- Keyboard shortcuts
- Mouse support
- Split panes (tasks, calendar, statistics)
```

---

## Technical Implementation Guide

### 1. **Dependencies & Libraries**

```python
# requirements.txt
click>=8.1.0                  # CLI framework
google-auth-oauthlib>=1.0.0   # Google OAuth2
google-api-python-client>=2.0 # Google Tasks API
pydantic>=2.0.0               # Data validation
sqlalchemy>=2.0.0             # Local storage
rich>=13.0.0                  # Terminal formatting
tabulate>=0.9.0               # Table rendering
python-dateutil>=2.8.0        # Date parsing
pytz>=2023.3                  # Timezone support
pyyaml>=6.0                   # Config files
appdirs>=1.4.4                # Cross-platform paths
cryptography>=41.0.0          # Secure storage
requests>=2.31.0              # HTTP requests
matplotlib>=3.7.0             # Charts (optional)
prompt-toolkit>=3.0.0         # Advanced prompts
colorama>=0.4.6               # Cross-platform colors
```

### 2. **Logging Strategy**

```python
# utils/logger.py
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path

def setup_logger(name='gtasks'):
    """
    Configure application logging with:
    - Console output (INFO level)
    - File output with rotation (DEBUG level)
    - Structured log format
    """
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Log directory
    log_dir = Path.home() / '.gtasks' / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    
    # Console handler (INFO)
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(formatter)
    
    # File handler with rotation (DEBUG)
    file_handler = RotatingFileHandler(
        log_dir / 'gtasks.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    logger.addHandler(console)
    logger.addHandler(file_handler)
    
    return logger

# Usage in modules:
from utils.logger import setup_logger
logger = setup_logger(__name__)
logger.info("Starting task operation")
logger.debug(f"Task data: {task_dict}")
logger.error("API request failed", exc_info=True)
```

### 3. **Error Handling Strategy**

```python
# utils/exceptions.py

class GTa sksError(Exception):
    """Base exception for all gtasks errors"""
    pass

class AuthenticationError(GTasksError):
    """OAuth or authentication failures"""
    pass

class APIError(GTasksError):
    """Google API errors"""
    def __init__(self, message, status_code=None, response=None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response

class TaskNotFoundError(GTasksError):
    """Task doesn't exist"""
    pass

class ValidationError(GTasksError):
    """Invalid input data"""
    pass

class SyncError(GTasksError):
    """Synchronization failures"""
    pass

class ConfigError(GTasksError):
    """Configuration issues"""
    pass

# Error handling decorator
def handle_errors(func):
    """Decorator for consistent error handling"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except AuthenticationError as e:
            logger.error(f"Authentication failed: {e}")
            click.echo(f"❌ Authentication error: {e}", err=True)
            click.echo("Run 'gtasks login' to authenticate", err=True)
            sys.exit(1)
        except APIError as e:
            logger.error(f"API error: {e}", exc_info=True)
            click.echo(f"❌ API error: {e}", err=True)
            sys.exit(1)
        except ValidationError as e:
            logger.warning(f"Validation error: {e}")
            click.echo(f"❌ Invalid input: {e}", err=True)
            sys.exit(1)
        except Exception as e:
            logger.critical(f"Unexpected error: {e}", exc_info=True)
            click.echo(f"❌ Unexpected error: {e}", err=True)
            click.echo("Please check logs for details", err=True)
            sys.exit(1)
    return wrapper
```

### 4. **Data Models Using Pydantic**

```python
# models/task.py
from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, List
from enum import Enum

class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    WAITING = "waiting"
    DELETED = "deleted"

class Task(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    due: Optional[datetime] = None
    priority: Priority = Priority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    project: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    parent_id: Optional[str] = None
    tasklist_id: str
    position: int = 0
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    modified_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    estimated_duration: Optional[int] = None  # minutes
    actual_duration: Optional[int] = None
    recurrence_rule: Optional[str] = None
    
    @validator('tags')
    def validate_tags(cls, v):
        return [tag.lower().strip() for tag in v]
    
    class Config:
        use_enum_values = True
```

### 5. **CLI Framework with Click**

```python
# cli/commands.py
import click
from cli.decorators import handle_errors, require_auth

@click.group()
@click.version_option(version='1.0.0')
@click.option('--config', type=click.Path(), help='Config file path')
@click.option('--verbose', '-v', count=True, help='Verbose output')
@click.pass_context
def cli(ctx, config, verbose):
    """Google Tasks CLI with superpowers ⚡"""
    ctx.ensure_object(dict)
    ctx.obj['CONFIG'] = config
    ctx.obj['VERBOSE'] = verbose
    
    # Setup logging level based on verbosity
    if verbose >= 2:
        logger.setLevel(logging.DEBUG)
    elif verbose == 1:
        logger.setLevel(logging.INFO)

@cli.command()
@click.argument('title')
@click.option('--desc', '-d', help='Task description')
@click.option('--due', type=click.DateTime(), help='Due date')
@click.option('--priority', type=click.Choice(['low', 'medium', 'high', 'critical']))
@click.option('--project', '-p', help='Project name')
@click.option('--tags', '-t', multiple=True, help='Tags')
@click.option('--tasklist', '-l', help='Tasklist name')
@handle_errors
@require_auth
def add(title, desc, due, priority, project, tags, tasklist):
    """Add a new task"""
    task_manager = TaskManager()
    task = task_manager.create_task(
        title=title,
        description=desc,
        due=due,
        priority=priority,
        project=project,
        tags=list(tags),
        tasklist=tasklist
    )
    click.echo(f"✅ Task created: {task.id} - {task.title}")

# More commands...
```

### 6. **API Client Implementation**

```python
# integrations/google_tasks_api.py
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

class GoogleTasksClient:
    def __init__(self, credentials: Credentials):
        self.service = build('tasks', 'v1', credentials=credentials)
        self.logger = setup_logger(__name__)
    
    def list_tasklists(self):
        """Get all tasklists"""
        try:
            results = self.service.tasklists().list().execute()
            return results.get('items', [])
        except Exception as e:
            self.logger.error(f"Failed to list tasklists: {e}")
            raise APIError("Failed to fetch tasklists") from e
    
    def list_tasks(self, tasklist_id, show_completed=False, 
                    show_deleted=False, show_hidden=False):
        """Get tasks from a tasklist"""
        try:
            results = self.service.tasks().list(
                tasklist=tasklist_id,
                showCompleted=show_completed,
                showDeleted=show_deleted,
                showHidden=show_hidden
            ).execute()
            return results.get('items', [])
        except Exception as e:
            self.logger.error(f"Failed to list tasks: {e}")
            raise APIError("Failed to fetch tasks") from e
    
    def create_task(self, tasklist_id, task_data):
        """Create a new task"""
        try:
            result = self.service.tasks().insert(
                tasklist=tasklist_id,
                body=task_data
            ).execute()
            self.logger.info(f"Created task: {result['id']}")
            return result
        except Exception as e:
            self.logger.error(f"Failed to create task: {e}")
            raise APIError("Failed to create task") from e
    
    # More API methods...
```

### 7. **Local Storage & Caching**

```python
# storage/local_storage.py
from sqlalchemy import create_engine, Column, String, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pathlib import Path

Base = declarative_base()

class TaskCache(Base):
    __tablename__ = 'tasks'
    
    id = Column(String, primary_key=True)
    tasklist_id = Column(String, index=True)
    title = Column(String)
    data = Column(String)  # JSON serialized task data
    updated_at = Column(DateTime)
    sync_status = Column(String)  # synced, modified, new, deleted

class LocalStorage:
    def __init__(self, db_path=None):
        if db_path is None:
            db_dir = Path.home() / '.gtasks'
            db_dir.mkdir(parents=True, exist_ok=True)
            db_path = db_dir / 'cache.db'
        
        self.engine = create_engine(f'sqlite:///{db_path}')
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
    
    def cache_task(self, task):
        """Cache task locally"""
        session = self.Session()
        try:
            cached = session.query(TaskCache).filter_by(id=task.id).first()
            if cached:
                cached.data = task.json()
                cached.updated_at = datetime.utcnow()
            else:
                cached = TaskCache(
                    id=task.id,
                    tasklist_id=task.tasklist_id,
                    title=task.title,
                    data=task.json(),
                    updated_at=datetime.utcnow(),
                    sync_status='synced'
                )
                session.add(cached)
            session.commit()
        finally:
            session.close()
    
    def get_cached_tasks(self, tasklist_id=None):
        """Retrieve cached tasks"""
        session = self.Session()
        try:
            query = session.query(TaskCache)
            if tasklist_id:
                query = query.filter_by(tasklist_id=tasklist_id)
            return query.all()
        finally:
            session.close()
```

### 8. **Filter Engine Implementation**

```python
# core/filter_engine.py
import re
from typing import List, Callable
from datetime import datetime, timedelta
import operator

class FilterEngine:
    """Parse and apply complex filters to tasks"""
    
    OPERATORS = {
        ':': operator.eq,
        '.contains:': lambda a, b: b in a,
        '.matches:': lambda a, b: re.search(b, a) is not None,
        '.before:': operator.lt,
        '.after:': operator.gt,
        '.above:': operator.gt,
        '.below:': operator.lt,
    }
    
    def __init__(self):
        self.logger = setup_logger(__name__)
    
    def parse_filter(self, filter_string: str) -> Callable:
        """Parse filter string into callable predicate"""
        # Handle logical operators
        if ' and ' in filter_string:
            parts = filter_string.split(' and ')
            predicates = [self.parse_filter(p.strip()) for p in parts]
            return lambda task: all(pred(task) for pred in predicates)
        
        if ' or ' in filter_string:
            parts = filter_string.split(' or ')
            predicates = [self.parse_filter(p.strip()) for p in parts]
            return lambda task: any(pred(task) for pred in predicates)
        
        # Parse single condition
        for op_str, op_func in self.OPERATORS.items():
            if op_str in filter_string:
                field, value = filter_string.split(op_str, 1)
                field = field.strip()
                value = value.strip()
                
                # Handle date values
                if field in ['due', 'created_at', 'modified_at']:
                    value = self.parse_date(value)
                
                return lambda task: op_func(
                    getattr(task, field, None), 
                    value
                )
        
        raise ValidationError(f"Invalid filter: {filter_string}")
    
    def parse_date(self, date_string: str) -> datetime:
        """Parse relative date strings"""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        if date_string == 'today':
            return today
        elif date_string == 'tomorrow':
            return today + timedelta(days=1)
        elif date_string == 'yesterday':
            return today - timedelta(days=1)
        elif date_string == 'eow':  # End of week
            days_ahead = 6 - today.weekday()
            return today + timedelta(days=days_ahead)
        elif date_string == 'eom':  # End of month
            next_month = today.replace(day=28) + timedelta(days=4)
            return next_month - timedelta(days=next_month.day)
        elif date_string.startswith('+'):
            # Relative date: +3d, +2w, +1m
            match = re.match(r'\+(\d+)([dwmy])', date_string)
            if match:
                amount, unit = match.groups()
                amount = int(amount)
                if unit == 'd':
                    return today + timedelta(days=amount)
                elif unit == 'w':
                    return today + timedelta(weeks=amount)
                elif unit == 'm':
                    return today + timedelta(days=amount*30)
                elif unit == 'y':
                    return today + timedelta(days=amount*365)
        
        # Try parsing as ISO date
        try:
            return datetime.fromisoformat(date_string)
        except ValueError:
            raise ValidationError(f"Invalid date format: {date_string}")
    
    def apply_filter(self, tasks: List, filter_string: str) -> List:
        """Filter tasks based on filter string"""
        if not filter_string:
            return tasks
        
        predicate = self.parse_filter(filter_string)
        return [task for task in tasks if predicate(task)]
```

---

## Testing Strategy

### Unit Tests
```python
# tests/unit/test_task_manager.py
import pytest
from core.task_manager import TaskManager
from models.task import Task

def test_create_task():
    manager = TaskManager()
    task = manager.create_task(title="Test Task")
    assert task.title == "Test Task"
    assert task.status == "pending"

def test_filter_by_priority():
    # Test filtering logic
    pass

# More unit tests...
```

### Integration Tests
```python
# tests/integration/test_google_api.py
def test_create_and_fetch_task():
    # Test actual API integration
    pass
```

### Test Coverage
- Aim for >80% code coverage
- Use pytest with pytest-cov
- Mock external API calls
- Test error scenarios

---

## Documentation Requirements

1. **README.md**: Installation, quick start, features overview
2. **CONTRIBUTING.md**: How to contribute
3. **API.md**: Internal API documentation
4. **CLI.md**: Complete CLI command reference
5. **CONFIGURATION.md**: Configuration options
6. **Docstrings**: Every function/class documented
7. **Examples**: Common use cases and workflows

---

## Performance Considerations

1. **Caching**: Aggressive local caching with smart invalidation
2. **Batch Operations**: Batch API requests when possible
3. **Lazy Loading**: Load data only when needed
4. **Pagination**: Handle large task lists efficiently
5. **Async Operations**: Use async for API calls (asyncio)
6. **Database Indexing**: Proper indexes on cache tables

---

## Security Best Practices

1. **Credential Storage**: Use secure keyring libraries
2. **Token Encryption**: Encrypt stored tokens
3. **Input Validation**: Validate all user inputs
4. **API Key Protection**: Never log or expose API keys
5. **HTTPS Only**: Enforce secure connections
6. **Dependency Auditing**: Regular security audits

---

## Deployment & Distribution

1. **PyPI Package**: Publish to PyPI for pip installation
2. **Binary Distribution**: Use PyInstaller for standalone binaries
3. **Docker Image**: Provide Docker container
4. **CI/CD**: GitHub Actions for automated testing and releases
5. **Versioning**: Semantic versioning (MAJOR.MINOR.PATCH)

---

## Future Enhancements

1. **Web Interface**: Optional web dashboard
2. **Mobile App**: Companion mobile application
3. **Team Features**: Task sharing and collaboration
4. **AI Integration**: Smart task suggestions, auto-categorization
5. **Voice Commands**: Voice-to-task creation
6. **Email Integration**: Create tasks from emails
7. **Notification System**: Desktop/mobile notifications
8. **Plugin System**: Extensible plugin architecture
9. **Calendar Sync**: Bi-directional calendar integration
10. **Analytics Dashboard**: Advanced productivity analytics

---

## Example Usage Scenarios

```bash
# Daily workflow
gtasks context use work
gtasks list due.before:+2d --sort due
gtasks add "Review PR #123" --priority high --project dev --due tomorrow
gtasks start 42
gtasks pomodoro start 42
gtasks done 42

# Weekly review
gtasks list status:completed --from -7d
gtasks report burndown --weekly
gtasks report summary --by-project

# Bulk operations
gtasks list project:migration status:pending --export tasks.json
gtasks import --format json tasks.json --move-to "Archive"

# Advanced filtering
gtasks list '(priority:high or priority:critical) and due.before:eow'
gtasks modify 'project:oldname' --set project:newname

# Synchronization
gtasks sync --force
gtasks list --offline
```

---

## Implementation Checklist

### Phase 1: Core Foundation
- [ ] Project setup and structure
- [ ] OAuth2 authentication
- [ ] Google Tasks API integration
- [ ] Basic task operations (CRUD)
- [ ] Basic tasklist operations
- [ ] Configuration management
- [ ] Logging system
- [ ] Error handling
- [ ] Local storage/caching

### Phase 2: Advanced Features
- [ ] Filter engine
- [ ] Context management
- [ ] Task dependencies
- [ ] Recurring tasks
- [ ] Time tracking
- [ ] Annotations and notes
- [ ] Import/Export functionality
- [ ] Undo/Redo system

### Phase 3: Reports & Analytics
- [ ] Report engine
- [ ] Built-in reports
- [ ] Custom reports
- [ ] Statistics
- [ ] Burndown charts
- [ ] Calendar views

### Phase 4: Productivity Tools
- [ ] Pomodoro timer
- [ ] Habit tracking
- [ ] Journal integration
- [ ] TUI dashboard (optional)

### Phase 5: Polish & Release
- [ ] Comprehensive testing
- [ ] Documentation
- [ ] Performance optimization
- [ ] Packaging and distribution
- [ ] CI/CD setup

---

## Key Principles

1. **User-Centric Design**: Make common operations simple and fast
2. **Offline-First**: Work seamlessly without internet connection
3. **Performance**: Minimize API calls, maximize responsiveness
4. **Extensibility**: Easy to add new features and integrations
5. **Reliability**: Robust error handling and data integrity
6. **Discoverability**: Intuitive commands with helpful messages
7. **Power User Friendly**: Advanced features for power users
8. **Cross-Platform**: Works on Windows, macOS, and Linux

Build this application incrementally, testing thoroughly at each stage. Focus on core functionality first, then layer on advanced features. Prioritize code quality, maintainability, and user experience.