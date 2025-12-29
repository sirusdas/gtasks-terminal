# Google Tasks CLI

A powerful command-line interface for managing Google Tasks with enhanced features and functionality which is secure and easy to use with advanced features.

[![GitHub](https://img.shields.io/github/license/sirusdas/gtasks-terminal)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.7%2B-blue)](https://www.python.org/)
[![GitHub last commit](https://img.shields.io/github/last-commit/sirusdas/gtasks-terminal)](https://github.com/sirusdas/gtasks-terminal/commits)
[![PyPI](https://img.shields.io/pypi/v/gtasks-cli)](https://pypi.org/project/gtasks-cli/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/gtasks-cli)](https://pypi.org/project/gtasks-cli/)

## 🌟 Features

Google Tasks CLI provides a comprehensive set of features for power users who prefer working in the terminal:

1. **Basic Task Management**: Add, list, update, and delete tasks
2. **Advanced Filtering**: Filter tasks by status, priority, tags, and date ranges
3. **Multi-Account Support**: Manage tasks across multiple Google accounts
4. **Task Deduplication**: Automatically identify and remove duplicate tasks
5. **Enhanced Tagging**: Extract and manage tags from task titles and descriptions
6. **Interactive Mode**: Navigate tasks interactively with keyboard shortcuts
7. **Reports Generation**: Generate comprehensive analytical reports on task activities
8. **Advanced Sync**: Enhanced synchronization with tag processing and conflict resolution
9. **Task Recovery**: Backup and restore functionality for deleted tasks
10. **External Editor Integration**: Edit tasks using your preferred text editor

## 📦 Installation

### Prerequisites
- Python 3.7 or higher
- A Google account with Google Tasks enabled

### Quick Installation (Recommended)

Install directly from PyPI:

```bash
pip install gtasks-cli
```

This is the easiest and recommended way to install Google Tasks CLI. The latest version is 0.1.2.

After installation, you can optionally run the setup assistant to configure your environment:

```bash
python -m gtasks_cli.setup_assistant
```

For more information about the setup assistant, see [SETUP_ASSISTANT.md](gtasks_cli/SETUP_ASSISTANT.md).

### Manual Setup (Development)

1. Clone the repository:
```bash
git clone https://github.com/sirusdas/gtasks-terminal.git
cd gtasks-terminal
```

2. Set up virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
cd gtasks_cli
pip install -r requirements.txt
```

4. Install the package in development mode:
```bash
pip install -e .
```

## 🔐 Authentication

1. Create a Google Cloud Project and enable the Tasks API
2. Create OAuth 2.0 credentials for a Desktop application
3. Download the credentials JSON file and rename it to `client_secret.json`
4. Place the file in the project root directory

For detailed instructions, see [INSTALLATION.md](INSTALLATION.md).

## 🚀 Quick Start

After installation and authentication, you can start using the CLI:

```bash
# Enter interactive mode for a rich, keyboard-driven interface
gtasks interactive

# Sync with Google Tasks using advanced synchronization
gtasks advanced-sync

# Generate a report on completed tasks over the last 30 days
gtasks generate-report rp1 --days 30
```

### Command Features

Each command in Google Tasks CLI provides powerful functionality:

- **`list`**: Display tasks with extensive filtering options including status, priority, tags, and date ranges
- **`add`**: Create new tasks with rich metadata like due dates, priorities, and tags
- **`interactive`**: Enter a full-screen terminal interface for advanced task management
- **`advanced-sync`**: Synchronize tasks with sophisticated conflict resolution and tag processing
- **`generate-report`**: Create detailed analytical reports on your task activities

## 👥 Multi-Account Management

Google Tasks CLI supports managing tasks across multiple Google accounts seamlessly. This is especially useful for users who need to separate personal and work tasks, or manage tasks for different projects or clients.

### Connecting Multiple Accounts

To connect additional accounts:

```bash
# Add a new account (will prompt for authentication)
gtasks account add --name work

# List all configured accounts
gtasks account list

# Switch to a specific account
gtasks account use work

# Remove an account
gtasks account remove work
```

### Switching Between Accounts

Switching between accounts is effortless:

1. **Via Command Line**: Use `gtasks account use <account_name>` to switch
2. **In Interactive Mode**: Use the `switch-account` command
3. **Per-Command Basis**: Use the `--account` option with any command:
   ```bash
   gtasks list --account work --status pending
   ```

### Account Benefits

- **Complete Isolation**: Tasks from different accounts are kept completely separate
- **Easy Switching**: Toggle between accounts with a single command
- **Per-Command Selection**: Run individual commands against specific accounts
- **Secure Storage**: Each account's credentials are securely stored separately

Detailed instructions for multi-account management are available in [MULTI_ACCOUNT.md](gtasks_cli/MULTI_ACCOUNT.md).

## ▶️ Usage

After installation, you can use the `gtasks` command:

```bash
gtasks --help
```

For first-time setup, you'll need to authenticate with your Google account:

```bash
gtasks auth
```

### Advanced Features
- [ADVANCED_FILTERING.md](ADVANCED_FILTERING.md) - Advanced task filtering capabilities
- [ADVANCED_SYNC.md](ADVANCED_SYNC.md) - Advanced synchronization implementation
- [ADVANCED_SYNC_OPTIMIZATION.md](ADVANCED_SYNC_OPTIMIZATION.md) - Sync performance optimizations
- [EDITOR_FEATURE.md](EDITOR_FEATURE.md) - External editor integration
- [ORDER_BY_FEATURE.md](ORDER_BY_FEATURE.md) - Task sorting functionality
- [REPORTS_FEATURE