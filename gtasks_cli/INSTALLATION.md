# Installation Guide for Google Tasks CLI

This guide provides detailed instructions for installing and setting up the Google Tasks CLI application.

## Prerequisites

Before installing Google Tasks CLI, ensure you have:

- Python 3.7 or higher
- pip package manager
- A Google account with Google Tasks enabled

## Installation Methods

### Method 1: PyPI Installation (Recommended)

The easiest way to install Google Tasks CLI is from PyPI:

```bash
pip install gtasks-cli
```

After installation, verify that the command is available:

```bash
gtasks --help
```

### Method 2: Development Installation

If you want to contribute or modify the code:

1. Clone the repository:
   ```bash
   git clone https://github.com/sirusdas/gtasks-terminal.git
   cd gtasks-terminal/gtasks_cli
   ```

2. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install in development mode:
   ```bash
   pip install -e .
   ```

## Post-Installation Setup

After installing the package, run the setup assistant to configure your environment:

```bash
python -m gtasks_cli.setup_assistant
```

The setup assistant will:
- Verify that gtasks-cli is properly installed
- Create the configuration directory (`~/.gtasks`)
- Set up default configuration values
- Guide you through Google authentication setup
- Test basic functionality

## Google Authentication Setup

To use Google Tasks CLI with your Google account, you need to set up authentication:

### 1. Create a Google Cloud Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Tasks API for your project

### 2. Create OAuth 2.0 Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth 2.0 Client IDs"
3. Select "Desktop application" as the application type
4. Download the credentials JSON file
5. Save it as `~/.gtasks/credentials.json`

### 3. Authenticate

Run the authentication command:

```bash
gtasks auth
```

This will open a browser window where you can sign in to your Google account and grant the necessary permissions.

## Configuration

The application stores configuration in `~/.gtasks/config.yaml`. The default configuration includes:

```yaml
default_tasklist: 'My Tasks'
date_format: '%Y-%m-%d'
time_format: '%H:%M'
sync_on_action: true
offline_mode: false
display:
  colors: true
  table_style: 'simple'
  max_width: 100
sync:
  pull_range_days: 10
  auto_save: true
accounts: {}
aliases:
  ls: 'list'
  rm: 'delete'
  complete: 'done'
```

## First Steps

Once installed and configured, try these commands:

```bash
# List your tasks
gtasks list

# Add a new task
gtasks add "Buy groceries" --due "tomorrow"

# Enter interactive mode
gtasks interactive

# Get help
gtasks --help
```

## Troubleshooting

### Command Not Found

If you get a "command not found" error:

1. Verify that your Python scripts directory is in your PATH
2. Try reinstalling with: `pip install --user gtasks-cli`
3. On some systems, you might need to restart your terminal after installation

### Authentication Issues

If authentication fails:

1. Verify your credentials file is in the correct location: `~/.gtasks/credentials.json`
2. Check that the Google Tasks API is enabled in your Google Cloud Console
3. Ensure your OAuth 2.0 credentials are for a "Desktop application"

### Virtual Environment

If using a virtual environment, make sure it's activated before running commands:

```bash
source venv/bin/activate  # On Windows: venv\Scripts\activate
gtasks --help
```

## Uninstalling

To uninstall Google Tasks CLI:

```bash
pip uninstall gtasks-cli
```

Note that this will not remove your configuration files, which are stored in `~/.gtasks/`.