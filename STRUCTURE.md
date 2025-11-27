# Project Structure

This document provides an overview of the Google Tasks CLI project structure.

## Overview

The Google Tasks CLI project is organized in a modular structure that separates concerns and makes the codebase maintainable and extensible.

## Installation Options

### From PyPI (Recommended)

The easiest way to use Google Tasks CLI is to install it from PyPI:

```
pip install gtasks-cli
```

This installs the latest stable version with all dependencies.

### From Source

For development, clone the repository and install in development mode:

```
git clone <repository-url>
cd gtasks_automation/gtasks_cli
pip install -e .
```

## Directory Structure

```
gtasks_automation/
├── gtasks_cli/                 # Main package directory
│   ├── src/                    # Source code
│   │   └── gtasks_cli/         # Main package
│   │       ├── __init__.py     # Package initialization
│   │       ├── main.py         # Main entry point
│   │       ├── cli/            # CLI components
│   │       ├── commands/       # Command implementations
│   │       ├── core/           # Core business logic
│   │       ├── integrations/   # Third-party integrations
│   │       ├── models/         # Data models
│   │       ├── reports/        # Reporting functionality
│   │       ├── storage/        # Data storage implementations
│   │       ├── ui/             # User interface components
│   │       └── utils/          # Utility functions
│   ├── requirements.txt        # Python dependencies
│   ├── setup.py                # Legacy setup script
│   ├── pyproject.toml          # Modern Python packaging configuration
│   └── README.md               # Development instructions
├── README.md                   # Main project documentation
├── INSTALLATION.md             # Detailed installation guide
├── PYPI_INSTALLATION.md        # PyPI-specific installation guide
└── ...                         # Other documentation files
```

## Package Components

### Commands (`commands/`)
Individual command implementations:
- `add.py` - Add new tasks
- `list.py` - List tasks with filtering
- `done.py` - Mark tasks as complete
- `delete.py` - Delete tasks
- `update.py` - Update task properties
- `sync.py` - Synchronize with Google Tasks
- `search.py` - Search tasks

### Core (`core/`)
Core business logic including the main `TaskManager` class.

### Integrations (`integrations/`)
Third-party service integrations:
- `google_tasks_client.py` - Google Tasks API client
- `google_auth.py` - Authentication handling
- `sync_manager.py` - Basic sync functionality

### Models (`models/`)
Data models representing tasks and task lists.

### Reports (`reports/`)
Reporting functionality with various report types.

### Storage (`storage/`)
Data storage implementations:
- `local_storage.py` - JSON-based local storage
- `sqlite_storage.py` - SQLite database storage
- `config_manager.py` - Configuration management

### Utils (`utils/`)
Utility functions used throughout the application.

## Entry Points

The main entry point is `gtasks_cli/main.py` which sets up the CLI application.

When installed from PyPI, the `gtasks` command is available system-wide.

