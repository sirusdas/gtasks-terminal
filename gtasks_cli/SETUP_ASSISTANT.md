# Google Tasks CLI Setup Assistant

This document explains how to use the post-installation setup assistant for Google Tasks CLI.

## Installation

First, install the Google Tasks CLI package:

```bash
pip install gtasks-cli
```

After installation, the `gtasks` command will be available in your terminal.

## Running the Setup Assistant

To run the setup assistant, execute the following command after installing the package:

```bash
python -m gtasks_cli.setup_assistant
```

Alternatively, if you downloaded the setup assistant separately, you can run:

```bash
python setup_assistant.py
```

## What the Setup Assistant Does

The setup assistant will:

1. Verify that gtasks-cli is properly installed
2. Create the configuration directory (`~/.gtasks`)
3. Set up default configuration values
4. Guide you through Google authentication setup
5. Test basic functionality

## Manual Setup

If you prefer to set up manually, you can:

1. Create a configuration directory:
   ```bash
   mkdir -p ~/.gtasks
   ```

2. Create a default configuration file at `~/.gtasks/config.yaml` with your preferred settings

3. Set up Google authentication by following the instructions in the main README

## Google Authentication

To use the Google Tasks API, you'll need to set up authentication:

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Tasks API
4. Create credentials for an OAuth 2.0 client ID (desktop application)
5. Download the credentials JSON file
6. Save it as `~/.gtasks/credentials.json`
7. Run `gtasks auth` to complete the authentication process

## Getting Started

Once setup is complete, you can start using gtasks:

```bash
gtasks --help                    # Show all available commands
gtasks list                      # List your tasks
gtasks add "My new task"         # Add a new task
gtasks interactive               # Enter interactive mode
gtasks auth                      # Authenticate with Google
```

## Cross-Platform Availability

After installing with pip, the `gtasks` command should be available in any terminal on your system as long as your Python scripts directory is in your PATH. This is handled automatically by pip during installation.