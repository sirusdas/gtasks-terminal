# Google Tasks CLI

A command-line interface for managing Google Tasks with enhanced features and functionality.

## Features

1. **Basic Task Management**: Add, list, update, and delete tasks
2. **Advanced Filtering**: Filter tasks by status, priority, tags, and date ranges
3. **Multi-Account Support**: Manage tasks across multiple Google accounts
4. **Task Deduplication**: Automatically identify and remove duplicate tasks
5. **Enhanced Tagging**: Extract and manage tags from task titles and descriptions
6. **Interactive Mode**: Navigate tasks interactively with keyboard shortcuts
7. **Reports Generation**: Generate comprehensive analytical reports on task activities
8. **Advanced Sync**: Enhanced synchronization with tag processing and conflict resolution

## Installation

1. Clone the repository
2. Install the required dependencies: `pip install -r requirements.txt`
3. Run the CLI: `python -m gtasks_cli.main --help`

## Usage

### Basic Commands

- `gtasks list`: List tasks with optional filtering
- `gtasks add`: Add a new task
- `gtasks update`: Update an existing task
- `gtasks delete`: Delete a task
- `gtasks sync`: Synchronize tasks with Google Tasks
- `gtasks advanced-sync`: Advanced synchronization with enhanced features
- `gtasks interactive`: Enter interactive mode
- `gtasks generate-report`: Generate analytical reports

### Filtering Options

Tasks can be filtered using various criteria:

- `--status`: Filter by task status (pending, in_progress, completed, etc.)
- `--priority`: Filter by task priority (low, medium, high, critical)
- `--project`: Filter by project
- `--filter`: Filter by time period (today, this_week, this_month, etc.)
- `--search`: Search tasks by title, description, or notes
- `--tags`: Filter by tags (comma-separated)
- `--with-all-tags`: Require all specified tags to be present (used with --tags)

### Tag Management

Tags can be added to tasks in two ways:
1. Using the `--tags` option when adding or updating tasks
2. Including tags directly in task titles or descriptions using square brackets, e.g., `[work]`, `[urgent]`

The system automatically extracts tags from square brackets in task titles and descriptions during synchronization.

### Reports

Generate comprehensive analytical reports on task activities:
- Task completion trends
- Pending and overdue tasks analysis
- Task distribution by status, priority, and tags
- Future timeline planning
- And more...

Use `gtasks generate-report --list` to see all available reports.

Reports can be filtered by tags using `--tags` and `--with-all-tags` options.

### Multi-Account Support

Manage tasks across multiple Google accounts:
- `gtasks account add`: Add a new account
- `gtasks account list`: List all configured accounts
- `gtasks account use`: Switch to a specific account
- Use `--account` option with any command to specify the account

## Examples

List all pending tasks:
```bash
gtasks list --status pending
```

Add a new urgent task with tags:
```bash
gtasks add "Finish project [work] [urgent]" --priority high --due 2023-12-31
```

Search for tasks related to "meeting":
```bash
gtasks list --search "meeting"
```

Generate a report on completed tasks:
```bash
gtasks generate-report rp1 --days 30
```

Generate a report filtered by tags:
```bash
gtasks generate-report rp1 --tags "work,urgent" --with-all-tags
```

Enter interactive mode:
```bash
gtasks interactive
```

## Advanced Features

### Advanced Sync

The `gtasks advanced-sync` command provides enhanced synchronization capabilities:
- Bidirectional sync with conflict resolution
- Tag processing from task content
- Duplicate detection and handling
- Incremental sync for better performance

### Interactive Mode

Interactive mode (`gtasks interactive`) provides a user-friendly interface for task management:
- Navigate tasks with keyboard shortcuts
- Perform batch operations
- Apply filters dynamically
- Edit tasks in external editors

## Configuration

The CLI stores configuration and data in the `~/.gtasks` directory:
- `credentials.json`: Google API credentials
- `token.pickle`: Authentication tokens
- `tasks.json`: Local task storage (when not using SQLite)
- `accounts.json`: Multi-account configuration

## Contributing

Contributions are welcome! Please submit issues and pull requests on GitHub.

## License

This project is licensed under the MIT License.

## Future Developments
- [ ] Develop VS Code extension
- [ ] Develop Browser extension
- [ ] Integrate AI
- [ ] Mobile App
- [ ] Browser App
