# Google Tasks CLI Development

This directory contains the source code for the Google Tasks CLI application. 

For general usage, we recommend installing the package from PyPI:
```bash
pip install gtasks-cli
```

See the main project [README.md](../README.md) for more information on installation and usage.

## Features

- Full Google Tasks API integration with OAuth2 authentication
- Advanced filtering and search capabilities
- Context management for different task views
- Reporting and analytics
- Time tracking and Pomodoro technique integration
- Recurring tasks and dependencies
- Offline mode with synchronization
- Import/export functionality
- [Optimized Advanced Sync](https://github.com/sirusdas/gtasks-terminal/blob/main/ADVANCED_SYNC_OPTIMIZATION.md) for improved performance
- Multi-account support
- Interactive mode with keyboard navigation
- Task deduplication
- Rich terminal UI with color coding

## Installation for Development

To set up the development environment:

```bash
# Clone the repository
git clone <repository-url>
cd gtasks_automation/gtasks_cli

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

## Post-Installation Setup

After installing the package, we strongly recommend running the setup assistant to configure your environment:

```bash
python -m gtasks_cli.setup_assistant
```

The setup assistant will:
- Verify that gtasks-cli is properly installed
- Create the configuration directory (`~/.gtasks`)
- Set up default configuration values
- Guide you through Google authentication setup
- Test basic functionality

For more information, see [SETUP_ASSISTANT.md](SETUP_ASSISTANT.md).

## Running Tests

Various test scripts are available in the root directory:

```bash
# Run a simple sync test
python simple_sync_test.py

# Run comprehensive duplication tests
python comprehensive_dup_test.py
```

## Usage During Development

During development, you can run the CLI directly:

```bash
python -m gtasks_cli.main --help
```

Common development commands:

```bash
# Enter interactive mode for a rich, keyboard-driven interface
python -m gtasks_cli.main interactive

# List tasks
python -m gtasks_cli.main list

# Add a new task
python -m gtasks_cli.main add "Buy groceries" --due "tomorrow"

# Mark task as done
python -m gtasks_cli.main done <task-id>

# Sync with Google Tasks
python -m gtasks_cli.main sync
```

## Production Installation

For production use, install the package from PyPI:

```bash
pip install gtasks-cli
```

Then use the `gtasks` command directly:

```bash
gtasks --help
```

## TODO
- [ ] auto-sync on update/add/delete

## Development

This project follows a modular architecture with clear separation of concerns:
- **CLI Layer**: Command-line interface using Click framework
- **Core Layer**: Business logic for task and tasklist management
- **Integration Layer**: Google Tasks API integration and authentication
- **Storage Layer**: Local caching and configuration management
- **Reporting Layer**: Analytics and reporting functionality

## License

MIT