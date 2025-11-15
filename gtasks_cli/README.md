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
- Advanced sync operations (push/pull/bidirectional)

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

## Advanced Sync Functionality

The CLI includes advanced sync capabilities that allow for granular control over synchronization operations:

- **Push Operations**: Push only local changes to Google Tasks (`gtasks advanced-sync --push`)
- **Pull Operations**: Pull only changes from Google Tasks (`gtasks advanced-sync --pull`)
- **Bidirectional Sync**: Full synchronization in both directions (`gtasks advanced-sync`)

See [ADVANCED_SYNC.md](../ADVANCED_SYNC.md) for detailed documentation on the advanced sync functionality.

## Development

This project follows a modular architecture with clear separation of concerns:
- **CLI Layer**: Command-line interface using Click framework
- **Core Layer**: Business logic for task and tasklist management
- **Integration Layer**: Google Tasks API integration and authentication
- **Storage Layer**: Local caching and configuration management
- **Reporting Layer**: Analytics and reporting functionality

## License

MIT