# PyPI Installation Guide

This guide explains how to install Google Tasks CLI from PyPI, the official Python package repository.

## What is PyPI?

PyPI (Python Package Index) is the official repository for Python packages. Installing from PyPI ensures you get a stable, tested version of the software that is easy to update and manage.

## Installation

### Prerequisites

- Python 3.7 or higher installed on your system

### Installing the Package

To install Google Tasks CLI from PyPI, simply run:

```bash
pip install gtasks-cli
```

This command will:
1. Download the latest version of the package from PyPI
2. Install all required dependencies
3. Make the `gtasks` command available in your terminal

### Verifying Installation

After installation, you can verify that the package was installed correctly:

```bash
gtasks --help
```

This should display the help information for the Google Tasks CLI.

## Usage

Once installed, you can use all the features of Google Tasks CLI:

```bash
# Enter interactive mode
gtasks interactive

# List tasks
gtasks list

# Add a new task
gtasks add "Buy groceries" --due tomorrow

# Sync with Google Tasks
gtasks sync

# Generate reports
gtasks generate-report rp1 --days 30
```

## Updating

To update to the latest version:

```bash
pip install --upgrade gtasks-cli
```

## Uninstalling

To uninstall the package:

```bash
pip uninstall gtasks-cli
```

## Authentication Setup

After installing from PyPI, you'll still need to set up authentication with Google:

1. Create a Google Cloud Project and enable the Tasks API
2. Create OAuth 2.0 credentials for a Desktop application
3. Download the credentials JSON file and rename it to `client_secret.json`
4. Place the file in your home directory or project root

The first time you run a command that requires authentication, your browser will open and prompt you to log in to your Google account.

## Benefits of PyPI Installation

Installing from PyPI offers several advantages:

1. **Easy Installation**: Single command installs everything you need
2. **Automatic Dependency Management**: All required packages are automatically installed
3. **Simple Updates**: Easy to keep the software up to date
4. **Stable Releases**: Get tested, stable versions of the software
5. **Cross-Platform**: Works on Windows, macOS, and Linux
6. **System Integration**: The `gtasks` command is available system-wide

## Troubleshooting

### Permission Issues

If you encounter permission errors during installation, you may need to use:

```bash
pip install --user gtasks-cli
```

This installs the package for your user account only.

### Virtual Environments

For better isolation, you can use a virtual environment:

```bash
# Create a virtual environment
python3 -m venv gtasks-env

# Activate it
source gtasks-env/bin/activate  # On Windows: gtasks-env\Scripts\activate

# Install the package
pip install gtasks-cli

# Use the tool
gtasks --help

# Deactivate when done
deactivate
```

## Getting Help

For more detailed usage instructions, visit:
- [Main README](README.md)
- [Full Installation Guide](INSTALLATION.md)
- [Advanced Features Documentation](ADVANCED_SYNC.md)