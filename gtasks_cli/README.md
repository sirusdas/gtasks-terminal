# Google Tasks CLI

A powerful, feature-rich CLI application for Google Tasks management in Python.

## Features

- Full Google Tasks API integration with OAuth2 authentication
- Advanced filtering and search capabilities
- Context management for different task views
- Reporting and analytics
- Time tracking and Pomodoro technique integration
- Recurring tasks and dependencies
- Offline mode with synchronization
- Import/export functionality

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python -m gtasks_cli.main --help
```

Or after installation:

```bash
gtasks --help
```

## Development

This project follows a modular architecture with clear separation of concerns:
- **CLI Layer**: Command-line interface using Click framework
- **Core Layer**: Business logic for task and tasklist management
- **Integration Layer**: Google Tasks API integration and authentication
- **Storage Layer**: Local caching and configuration management
- **Reporting Layer**: Analytics and reporting functionality

## License

MIT