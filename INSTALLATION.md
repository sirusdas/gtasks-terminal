# Installation Guide

This guide will walk you through setting up the Google Tasks CLI application, authenticating with Google Tasks, and performing your first sync. Instructions are provided for Windows, macOS, and Linux systems.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation Options](#installation-options)
  - [Install from PyPI (Recommended)](#install-from-pypi-recommended)
  - [Install from Source](#install-from-source)
    - [Clone the Repository](#clone-the-repository)
    - [Set up Virtual Environment](#set-up-virtual-environment)
    - [Install Dependencies](#install-dependencies)
    - [Install the Package](#install-the-package)
- [Authentication](#authentication)
  - [Create Google Cloud Project](#create-google-cloud-project)
  - [Enable Google Tasks API](#enable-google-tasks-api)
  - [Create OAuth Credentials](#create-oauth-credentials)
  - [Configure Application](#configure-application)
- [First Sync](#first-sync)
- [Platform-Specific Instructions](#platform-specific-instructions)
  - [Windows](#windows)
  - [macOS](#macos)
  - [Linux](#linux)
- [Documentation Files Overview](#documentation-files-overview)

## Prerequisites

- Python 3.7 or higher installed on your system
- A Google account with Google Tasks enabled

## Installation Options

### Install from PyPI (Recommended)

The easiest way to install Google Tasks CLI is from PyPI:

```bash
pip install gtasks-cli
```

This will install the latest stable version and make the `gtasks` command available in your terminal.

After installation, proceed to the [Authentication](#authentication) section.

For detailed instructions on PyPI installation, see [PYPI_INSTALLATION.md](PYPI_INSTALLATION.md).

### Install from Source

If you prefer to install from source or want to contribute to the development of the tool, follow these steps:

#### Clone the Repository

```bash
git clone <repository-url>
cd gtasks_automation
```

#### Set up Virtual Environment

It's recommended to use a virtual environment to avoid conflicts with other Python projects:

**Windows (Command Prompt):**
```cmd
python -m venv venv
venv\Scripts\activate
```

**Windows (PowerShell):**
```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

#### Install Dependencies

Install the required Python packages:

```bash
pip install -r gtasks_cli/requirements.txt
```

#### Install the Package

For easier usage, install the package in development mode:

```bash
cd gtasks_cli
pip install -e .
```

This will make the `gtasks` command available in your terminal.

## Authentication

### Create Google Cloud Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Note down the Project ID for later use

### Enable Google Tasks API

1. In the Google Cloud Console, navigate to "APIs & Services" > "Library"
2. Search for "Tasks API"
3. Click on "Tasks API" and then click "Enable"

### Create OAuth Credentials

1. Navigate to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. If prompted, configure the OAuth consent screen:
   - Choose "External" user type (or "Internal" if you're using G Suite)
   - Fill in the required application information
   - Add your email to test users
4. For Application type, select "Desktop application"
5. Give it a name (e.g., "Google Tasks CLI")
6. Click "Create"
7. Download the JSON file and rename it to `client_secret.json`
8. Place the `client_secret.json` file in the project root directory

### Configure Application

The application stores configuration and authentication data in the `~/.gtasks` directory. On first run, it will create this directory and prompt you to authenticate.

On Windows, this directory is typically located at `C:\Users\{Username}\.gtasks`.

## First Sync

After completing the setup and authentication, you can perform your first sync:

If you installed from PyPI:
```bash
gtasks sync
```

If you installed from source:
**Windows:**
```cmd
cd gtasks_cli
python -m gtasks_cli.main sync
```

**macOS/Linux:**
```bash
cd gtasks_cli
python -m gtasks_cli.main sync
```

On first run, this will:
1. Open a browser window prompting you to authenticate with your Google account
2. Request permissions to access your Google Tasks data
3. Save the authentication token for future use
4. Sync your tasks between Google Tasks and the local storage

After successful authentication, subsequent runs won't require browser authentication unless the token expires.

## Platform-Specific Instructions

### Windows

On Windows systems, you have several options for running commands:

1. **Command Prompt (cmd)** - Use standard Windows command syntax
2. **PowerShell** - More powerful scripting environment
3. **Windows Subsystem for Linux (WSL)** - Run Linux commands on Windows

**Virtual Environment Activation:**
- Command Prompt: `venv\Scripts\activate.bat`
- PowerShell: `venv\Scripts\Activate.ps1`

**Important Notes:**
- If you encounter execution policy issues in PowerShell, run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` to allow script execution
- Path separators in Windows use backslashes (`\`) instead of forward slashes (`/`)
- The configuration directory is located at `%USERPROFILE%\.gtasks`

### macOS

macOS users can use the Terminal application or alternatives like iTerm2.

**Virtual Environment Activation:**
```bash
source venv/bin/activate
```

**Important Notes:**
- macOS comes with Python 2.7 by default, so make sure to install Python 3.x
- You can use Homebrew to install Python: `brew install python`
- The configuration directory is located at `~/.gtasks`

### Linux

Most Linux distributions come with Python pre-installed, but you may need to install Python 3.x if it's not already available.

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3 python3-pip git
```

**Fedora:**
```bash
sudo dnf install python3 python3-pip git
```

**Virtual Environment Activation:**
```bash
source venv/bin/activate
```

**Important Notes:**
- The configuration directory is located at `~/.gtasks`
- Make sure you have the necessary permissions to create directories and files

## Documentation Files Overview

This project includes several documentation files that provide detailed information about various features:

- [README.md](README.md) - Main project overview with basic usage instructions
- [PYPI_INSTALLATION.md](PYPI_INSTALLATION.md) - Detailed instructions for installing from PyPI
- [ADVANCED_FILTERING.md](ADVANCED_FILTERING.md) - Details on advanced task filtering capabilities including time-based filtering with specific date fields
- [ADVANCED_SYNC.md](ADVANCED_SYNC.md) - Information about the advanced sync feature implementation with its 4-step simplified approach
- [ADVANCED_SYNC_OPTIMIZATION.md](ADVANCED_SYNC_OPTIMIZATION.md) - Explanation of sync performance optimizations
- [EDITOR_FEATURE.md](EDITOR_FEATURE.md) - Guide to using external editors for task updates in interactive mode
- [ENVIRONMENT.md](ENVIRONMENT.md) - Environment setup instructions
- [ORDER_BY_FEATURE.md](ORDER_BY_FEATURE.md) - Documentation for task sorting functionality
- [ORGANIZED_TASKS_REPORT.md](ORGANIZED_TASKS_REPORT.md) - Details about the organized tasks report (rp9) with tag removal for clean email delivery
- [REPORTS_FEATURE.md](REPORTS_FEATURE.md) - Comprehensive guide to all reporting features
- [TASK_RECOVERY_GUIDE.md](TASK_RECOVERY_GUIDE.md) - Instructions for recovering deleted tasks with backup and restore procedures

Additional technical documents:
- [development_roadmap.md](development_roadmap.md) - Future development plans and roadmap
- [implementation_plan.md](implementation_plan.md) - Implementation details and phases
- [project_structure.md](project_structure.md) - Overview of project directory structure and architecture
- [status_report.md](status_report.md) - Current project status and completed milestones
- [technical_breakdown.md](technical_breakdown.md) - Technical architecture details

These documentation files provide comprehensive information about the features, usage, and implementation details of the Google Tasks CLI application.