# Multi-Account Support

The Google Tasks CLI now supports multiple Google accounts, allowing you to manage tasks from different accounts simultaneously. Each account uses its own:

1. Credentials file (`credentials.json`)
2. Authentication token (`token.pickle`)
3. Database file (`tasks.db`)

## Setting Up Multiple Accounts

### 1. Create Account-Specific Directories

Each account's data is stored in a separate directory under `~/.gtasks/ACCOUNT_NAME/`. For example:
- `~/.gtasks/personal/` for your personal account
- `~/.gtasks/work/` for your work account

### 2. Authenticate with Different Accounts

To authenticate with a specific account:

```bash
# Authenticate with your personal account
gtasks --account personal auth

# Authenticate with your work account
gtasks --account work auth
```

You can also specify a custom credentials file:

```bash
gtasks --account personal auth --credentials /path/to/personal/credentials.json
gtasks --account work auth --credentials /path/to/work/credentials.json
```

### 3. Using Commands with Specific Accounts

Once authenticated, you can use any command with a specific account:

```bash
# List tasks from your personal account
gtasks --account personal list

# List tasks from your work account
gtasks --account work list

# Add a task to your personal account
gtasks --account personal add "Personal task"

# Add a task to your work account
gtasks --account work add "Work task"

# Sync your personal account with Google Tasks
gtasks --account personal sync

# Sync your work account with Google Tasks
gtasks --account work sync
```

### 4. Using Interactive Mode

You can also use interactive mode with a specific account:

```bash
# Start interactive mode for your personal account
gtasks --account personal interactive

# Start interactive mode for your work account
gtasks --account work interactive
```

## Setting Default Accounts

To avoid having to specify the account for every command, you can set default accounts at different levels:

### Session-Level Default Account

Set a default account for the current terminal session:

```bash
# Set personal account as default for current session
export GTASKS_DEFAULT_ACCOUNT=personal
gtasks list  # Will use personal account
gtasks add "Task for personal account"
```

In interactive mode, you can also switch accounts dynamically:

```bash
# Start interactive mode (with any account or default)
gtasks interactive

# Inside interactive mode, switch accounts
account work  # Switch to work account
list          # Will show work account tasks
account personal  # Switch back to personal account
```

### Global Default Account

Set a global default account that persists across sessions:

```bash
# Set work account as global default
gtasks account use work

# Set personal account as global default
gtasks account use personal --global
```

Check which accounts are configured:

```bash
# List all configured accounts
gtasks account list

# Show current account
gtasks account current
```

## Environment Variable Alternative

You can also use the `GTASKS_CONFIG_DIR` environment variable to specify a custom configuration directory:

```bash
# Set environment variable for personal account
export GTASKS_CONFIG_DIR=~/.gtasks/personal
gtasks auth
gtasks list

# Set environment variable for work account
export GTASKS_CONFIG_DIR=~/.gtasks/work
gtasks auth
gtasks list
```

## Benefits of Multi-Account Support

1. **Complete Data Isolation**: Each account has its own credentials, tokens, and database
2. **Easy Switching**: Switch between accounts with a simple `--account` flag
3. **Simultaneous Usage**: Run commands for different accounts in different terminal sessions
4. **No Data Mixing**: Tasks from different accounts are never mixed together
5. **Flexible Configuration**: Each account can have its own settings and preferences
6. **Session Management**: Set default accounts for terminal sessions or globally

## Example Workflow

Here's a typical workflow for setting up and using multiple accounts:

1. **Set up personal account**:
   ```bash
   gtasks --account personal auth --credentials /path/to/personal/credentials.json
   gtasks --account personal sync
   gtasks --account personal list
   ```

2. **Set up work account**:
   ```bash
   gtasks --account work auth --credentials /path/to/work/credentials.json
   gtasks --account work sync
   gtasks --account work list
   ```

3. **Daily usage with session defaults**:
   ```bash
   # Set personal account as default for current session
   export GTASKS_DEFAULT_ACCOUNT=personal
   
   # Check personal tasks
   gtasks list --filter today
   
   # Add a personal task
   gtasks add "Call family"
   
   # Switch to work account for the session
   export GTASKS_DEFAULT_ACCOUNT=work
   
   # Add a work task
   gtasks add "Prepare meeting notes"
   
   # Mark a work task as done
   gtasks done TASK_ID
   ```

4. **Interactive mode usage**:
   ```bash
   # Start interactive mode
   gtasks interactive
   
   # Inside interactive mode
   list --filter today
   add "New task"
   
   # Switch to different account
   account personal
   list
   add "Personal task"
   
   # Switch back to work account
   account work
   ```

This multi-account system ensures complete separation of your task data while providing a simple and consistent interface for managing multiple Google accounts.