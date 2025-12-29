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

This is the easiest and recommended way to install Google Tasks CLI. The latest version is 0.1.3.

After installation, we recommend running the setup assistant to configure your environment:

```bash
python -m gtasks_cli.setup_assistant
```

The setup assistant will:
- Verify that gtasks-cli is properly installed
- Create the configuration directory (`~/.gtasks`)
- Set up default configuration values
- Guide you through Google authentication setup
- Test basic functionality

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
- [REPORTS_FEATURE.md](REPORTS_FEATURE.md) - Comprehensive reporting system

### Specialized Reports
- [ORGANIZED_TASKS_REPORT.md](ORGANIZED_TASKS_REPORT.md) - Organized tasks report (rp9)
- [REPORTS_FEATURE.md](REPORTS_FEATURE.md) - All reporting features

### Task Management
- [TASK_RECOVERY_GUIDE.md](TASK_RECOVERY_GUIDE.md) - Task recovery procedures
- [deduplication_summary.md](gtasks_cli/deduplication_summary.md) - Task deduplication overview

### Developer Documentation
- [development_roadmap.md](development_roadmap.md) - Project roadmap and future plans
- [implementation_plan.md](implementation_plan.md) - Implementation details
- [project_structure.md](project_structure.md) - Project architecture and organization explanation
- [status_report.md](status_report.md) - Current project status
- [technical_breakdown.md](technical_breakdown.md) - Technical architecture details

### Configuration
- [ENVIRONMENT.md](ENVIRONMENT.md) - Environment setup instructions
- [config/default_config.yaml](gtasks_cli/config/default_config.yaml) - Default configuration

## 📚 Documentation

- [Installation Guide](INSTALLATION.md)
- [Environment Setup](ENVIRONMENT.md)
- [Reports Feature](REPORTS_FEATURE.md)
- [Advanced Sync](ADVANCED_SYNC.md)
- [Organized Tasks Report](ORGANIZED_TASKS_REPORT.md)
- [Task Recovery Guide](TASK_RECOVERY_GUIDE.md)
- [Editor Feature](EDITOR_FEATURE.md)
- [Advanced Filtering](ADVANCED_FILTERING.md)
- [Order By Feature](ORDER_BY_FEATURE.md)
- [STRUCTURE.md](STRUCTURE.md) - Project structure and organization explanation
- [MULTI_ACCOUNT.md](gtasks_cli/MULTI_ACCOUNT.md) - Multi-account management guide
```bash
# Filter tasks due this week
gtasks interactive -- list "My Tasks" --filter this_week:created_at --search "apple|Tuku" --order-by title

# Filter tasks created this month
gtasks interactive -- list "My Tasks" --filter this_month:created_at
```
See [ADVANCED_FILTERING.md](ADVANCED_FILTERING.md) for more details.

### Tag Management
Tags can be added to tasks in two ways:
1. Using the `--tags` option when adding or updating tasks
2. Including tags directly in task titles or descriptions using square brackets, e.g., `[work]`, `[urgent]`

The system automatically extracts tags from square brackets in task titles and descriptions during synchronization.

### Reports Generation
Generate comprehensive analytical reports on task activities:
- Task completion trends
- Pending and overdue tasks analysis
- Task distribution by status, priority, and tags
- Future timeline planning

Use `gtasks generate-report --list` to see all available reports.

### Multi-Account Support
Manage tasks across multiple Google accounts:
```bash
gtasks account add --name work
gtasks account list
gtasks account use work
```

### Interactive Mode
Interactive mode (`gtasks interactive`) provides a user-friendly interface for task management:
- Navigate tasks with keyboard shortcuts
- Perform batch operations
- Apply filters dynamically
- Edit tasks in external editors

### Advanced Sync
The `gtasks advanced-sync` command provides enhanced synchronization capabilities:
- Bidirectional sync with conflict resolution
- Tag processing from task content
- Duplicate detection and handling
- Incremental sync for better performance

## 🤖 AI & MCP Integration

### AI Assistant
Enable AI capabilities to manage your tasks with natural language:

```bash
# Configure your AI provider (OpenAI, Anthropic, Gemini)
gtasks ai config --key provider --value openai
gtasks ai config --key api_key --value sk-...
gtasks ai config --key model --value gpt-4o

# Ask the AI to perform actions
gtasks ai ask "Add a task to buy milk tomorrow at 5pm with high priority"
gtasks ai ask "List my high priority tasks due this week"
```

### MCP Server
Expose `gtasks` as a tool for external AI agents (like Claude Desktop):

```bash
# Start the MCP server
gtasks mcp
```

This allows you to connect `gtasks` to any MCP-compliant client.

## 🛠️ Configuration

The CLI stores configuration and data in the `~/.gtasks` directory:
- `credentials.json`: Google API credentials
- `token.pickle`: Authentication tokens
- `tasks.json`: Local task storage (when not using SQLite)
- `accounts.json`: Multi-account configuration

## 🚀 Advanced Features

### Interactive Mode
Navigate tasks interactively with keyboard shortcuts:
```bash
gtasks interactive
```

### Reports Generation
Generate comprehensive analytical reports:
```bash
gtasks generate-report
```

### Task Deduplication
Automatically identify and remove duplicate tasks:
```bash
gtasks deduplicate
```

### Multi-Account Support
Manage tasks across multiple Google accounts:
```bash
gtasks account --help
```


## 🤝 Contributing

Contributions are welcome! This project thrives on community involvement and we appreciate any help you can provide.

### Why Contribute?

- **Improve Your Skills**: Work with a real-world Python CLI application using modern tools and frameworks
- **Solve Real Problems**: Help improve task management for users worldwide
- **Join a Growing Community**: Become part of an active open-source community
- **Build Your Portfolio**: Contributions are visible on GitHub and demonstrate your abilities
- **Learn Best Practices**: Work with well-structured, documented code following industry standards
- **Make a Difference**: Your contributions directly impact users' productivity

### How to Contribute

1. Fork the repository:
   ```bash
   git clone https://github.com/sirusdas/gtasks-terminal.git
   cd gtasks-terminal
   ```

2. Create a new branch for your feature or bugfix:
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. Make your changes and commit them:
   ```bash
   git commit -am "Add some feature"
   ```

4. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

5. Create a new Pull Request with a detailed description

### Ways to Contribute

- **Code**: Help implement new features or fix bugs
- **Documentation**: Improve existing docs or create new guides
- **Testing**: Write tests or help identify issues
- **Feedback**: Share your experience and suggestions
- **Design**: Improve the user interface or user experience
- **Translation**: Help translate the app to other languages

Please ensure your code follows the existing style and includes appropriate tests.

## 🔒 Security & Privacy

Your privacy and security are paramount. Here's how Google Tasks CLI protects your data:

### Zero Data Transmission Policy
- **No Data Collection**: We DO NOT collect any personal data or usage statistics
- **No Telemetry**: The application does not send any information to external servers
- **No Tracking**: There are no tracking mechanisms or analytics in the code

### Local Data Processing
- **Everything Stays Local**: All data processing happens on your machine
- **Direct API Communication**: The application communicates directly with Google's APIs, just like the official Google Tasks app
- **Token Security**: Authentication tokens are stored locally in your home directory (`~/.gtasks`) and never transmitted to any third-party servers

### Secure Authentication
- **OAuth 2.0 Standard**: Uses industry-standard OAuth 2.0 for authentication
- **Local Token Storage**: Tokens are securely stored on your device
- **Encrypted Communication**: All communication with Google's servers uses HTTPS encryption

### Open Source Transparency
- **Auditable Code**: As open source, anyone can review the code to verify security practices
- **Community Oversight**: The community helps identify and address potential security issues
- **Regular Updates**: Security patches are promptly released when needed

You retain complete control over your data at all times.


## 🛠️ Development

### Building and Publishing
For information on building and publishing the package to PyPI, see [PYPI_UPLOAD.md](gtasks_cli/PYPI_UPLOAD.md).

### Project Structure
See [STRUCTURE.md](STRUCTURE.md) for details about the project architecture.

### Contributing
Contributions are welcome! Please read our contributing guidelines before submitting pull requests.

See [development_roadmap.md](development_roadmap.md) for a complete roadmap.