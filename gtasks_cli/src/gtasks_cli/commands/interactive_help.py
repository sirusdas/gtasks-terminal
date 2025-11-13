#!/usr/bin/env python3
"""
Help system for interactive mode commands
"""

import click
from rich.console import Console
from rich.panel import Panel

# Initialize Rich console for colored output
console = Console()


def show_general_help():
    """Display general help for interactive mode"""
    click.echo("""
Interactive Mode Commands:
  view <number>     - View task details
  done <number>     - Mark task as completed
  delete <number>   - Delete a task
  update <number>   - Update a task (not yet implemented)
  add               - Add a new task
  list              - List all tasks
  list [filters]    - List tasks with filters (same as gtasks list command)
  search <query>    - Search tasks
  help              - Show this help
  help <command>    - Show detailed help for a command (e.g., help view)
  quit/exit         - Exit interactive mode
  
List Filter Options (same as gtasks list):
  LIST_FILTER       - Filter task lists by name (e.g., "My")
  --status STATUS   - Filter by status (pending, completed, etc.)
  --priority LEVEL  - Filter by priority (low, medium, high, critical)
  --project NAME    - Filter by project
  --recurring       - Show only recurring tasks
  --filter PERIOD   - Filter by time (today, this_week, this_month, last_3m, etc.)
  --search QUERY    - Search in title, description, notes
    """)


def show_view_help():
    """Display detailed help for the view command"""
    console.print(Panel("[bold blue]View Command Help[/bold blue]", expand=False))
    
    console.print("[bold]Description:[/bold]")
    console.print("Display detailed information about a specific task including its title,")
    console.print("description, status, priority, due date, project, and any notes.\n")
    
    console.print("[bold]Usage:[/bold]")
    console.print("  view <task_number>\n")
    
    console.print("[bold]Arguments:[/bold]")
    console.print("  task_number    The number of the task to view (as shown in the list)\n")
    
    console.print("[bold]Example:[/bold]")
    console.print("  [green]# View details of task number 3[/green]")
    console.print("  view 3\n")
    
    console.print("[bold]Notes:[/bold]")
    console.print("  - The task number is based on the current displayed list")
    console.print("  - Use the [yellow]list[/yellow] command to see task numbers")
    console.print("  - Task details include all available information about the task")


def show_done_help():
    """Display detailed help for the done command"""
    console.print(Panel("[bold blue]Done Command Help[/bold blue]", expand=False))
    
    console.print("[bold]Description:[/bold]")
    console.print("Mark a task as completed. This changes the task status to 'completed'.\n")
    
    console.print("[bold]Usage:[/bold]")
    console.print("  done <task_number>\n")
    
    console.print("[bold]Arguments:[/bold]")
    console.print("  task_number    The number of the task to mark as completed\n")
    
    console.print("[bold]Example:[/bold]")
    console.print("  [green]# Mark task number 5 as completed[/green]")
    console.print("  done 5\n")
    
    console.print("[bold]Notes:[/bold]")
    console.print("  - The task will be removed from the default task list (which shows only pending tasks)")
    console.print("  - Use [yellow]list --status completed[/yellow] to see completed tasks")
    console.print("  - Completed tasks are displayed with a green [green]✅[/green] icon")


def show_delete_help():
    """Display detailed help for the delete command"""
    console.print(Panel("[bold blue]Delete Command Help[/bold blue]", expand=False))
    
    console.print("[bold]Description:[/bold]")
    console.print("Delete a task. This marks the task as deleted but does not permanently remove it.\n")
    
    console.print("[bold]Usage:[/bold]")
    console.print("  delete <task_number>\n")
    
    console.print("[bold]Arguments:[/bold]")
    console.print("  task_number    The number of the task to delete\n")
    
    console.print("[bold]Example:[/bold]")
    console.print("  [green]# Delete task number 2[/green]")
    console.print("  delete 2\n")
    
    console.print("[bold]Notes:[/bold]")
    console.print("  - Deleted tasks are displayed with a red [red]🗑️[/red] icon")
    console.print("  - Use [yellow]list --status deleted[/yellow] to see deleted tasks")
    console.print("  - Tasks are soft-deleted and can potentially be recovered")


def show_update_help():
    """Display detailed help for the update command"""
    console.print(Panel("[bold blue]Update Command Help[/bold blue]", expand=False))
    
    console.print("[bold]Description:[/bold]")
    console.print("Update the details of an existing task including title and description.\n")
    
    console.print("[bold]Usage:[/bold]")
    console.print("  update <task_number>\n")
    
    console.print("[bold]Arguments:[/bold]")
    console.print("  task_number    The number of the task to update\n")
    
    console.print("[bold]Example:[/bold]")
    console.print("  [green]# Update task number 4[/green]")
    console.print("  update 4\n")
    
    console.print("[bold]Process:[/bold]")
    console.print("  1. You will be prompted to enter a new title (current title shown as default)")
    console.print("  2. You will be prompted to enter a new description (current description shown as default)")
    console.print("  3. Press [yellow]Enter[/yellow] to keep the current value")
    console.print("  4. Enter an empty value to clear the description\n")
    
    console.print("[bold]Notes:[/bold]")
    console.print("  - Only title and description can be updated through this command")
    console.print("  - For other updates (status, priority, etc.), use the appropriate commands")


def show_add_help():
    """Display detailed help for the add command"""
    console.print(Panel("[bold blue]Add Command Help[/bold blue]", expand=False))
    
    console.print("[bold]Description:[/bold]")
    console.print("Add a new task to your task list.\n")
    
    console.print("[bold]Usage:[/bold]")
    console.print("  add\n")
    
    console.print("[bold]Process:[/bold]")
    console.print("  1. You will be prompted to enter a task title")
    console.print("  2. You will be prompted to enter a task description (optional)")
    console.print("  3. Press [yellow]Enter[/yellow] to skip the description\n")
    
    console.print("[bold]Example:[/bold]")
    console.print("  [green]# Add a new task[/green]")
    console.print("  add")
    console.print("  Task title: Buy groceries")
    console.print("  Task description: Milk, eggs, bread, fruits\n")
    
    console.print("[bold]Notes:[/bold]")
    console.print("  - The new task will be added with 'pending' status by default")
    console.print("  - The new task will be displayed in the updated task list")


def show_list_help():
    """Display detailed help for the list command"""
    console.print(Panel("[bold blue]List Command Help[/bold blue]", expand=False))
    
    console.print("[bold]Description:[/bold]")
    console.print("List all tasks, optionally filtered by various criteria.\n")
    
    console.print("[bold]Usage:[/bold]")
    console.print("  list [FILTERS]\n")
    
    console.print("[bold]Filters:[/bold]")
    console.print("  LIST_FILTER           Filter task lists by name (e.g., \"My\")")
    console.print("  --status STATUS       Filter by status (pending, in_progress, completed, waiting, deleted)")
    console.print("  --priority LEVEL      Filter by priority (low, medium, high, critical)")
    console.print("  --project NAME        Filter by project")
    console.print("  --recurring           Show only recurring tasks")
    console.print("  --filter PERIOD       Filter by time (today, this_week, this_month, last_3m, etc.)")
    console.print("  --search QUERY        Search in title, description, notes\n")
    
    console.print("[bold]Examples:[/bold]")
    console.print("  [green]# List all tasks[/green]")
    console.print("  list\n")
    
    console.print("  [green]# List only high priority tasks[/green]")
    console.print("  list --priority high\n")
    
    console.print("  [green]# List tasks in the 'Work' project[/green]")
    console.print("  list --project Work\n")
    
    console.print("  [green]# List tasks due this week[/green]")
    console.print("  list --filter this_week\n")
    
    console.print("  [green]# List completed tasks containing 'report'[/green]")
    console.print("  list --status completed --search report\n")
    
    console.print("[bold]Notes:[/bold]")
    console.print("  - Tasks are grouped by list name")
    console.print("  - By default, only pending, in_progress, and waiting tasks are shown")
    console.print("  - Combine multiple filters for more specific results")


def show_search_help():
    """Display detailed help for the search command"""
    console.print(Panel("[bold blue]Search Command Help[/bold blue]", expand=False))
    
    console.print("[bold]Description:[/bold]")
    console.print("Search for tasks by providing terms that will be matched against task titles,")
    console.print("descriptions, and notes. Use the pipe character (|) to search for multiple")
    console.print("terms with OR logic. You can also filter by date ranges and list names.\n")
    
    console.print("[bold]Usage:[/bold]")
    console.print("  search <query> [filters]\n")
    
    console.print("[bold]Date Filters:[/bold]")
    console.print("  [green]today[/green]                     Today's tasks")
    console.print("  [green]yesterday[/green]                 Yesterday's tasks")
    console.print("  [green]this_week[/green]                 This week's tasks")
    console.print("  [green]last_N_days[/green]               Last N days (e.g., last_3_days, last_5_days)")
    console.print("  [green]upcoming[/green]                  All upcoming tasks")
    console.print("  [green]upcoming_this_week[/green]        Upcoming tasks this week")
    console.print("  [green]upcoming_this_month[/green]       Upcoming tasks this month")
    console.print("  [green]upcoming_next_N_days[/green]      Upcoming tasks in next N days (e.g., upcoming_next_3_days)\n")
    
    console.print("[bold]Other Filters:[/bold]")
    console.print("  [green]--list LIST_NAME[/green]          Filter by list name\n")
    
    console.print("[bold]Examples:[/bold]")
    console.print("  [green]# Search for tasks containing \"meeting\"[/green]")
    console.print("  search meeting\n")
    
    console.print("  [green]# Search for tasks containing \"meeting\", \"project\", OR \"review\"[/green]")
    console.print("  search \"meeting|project|review\"\n")
    
    console.print("  [green]# Search for tasks due today[/green]")
    console.print("  search today\n")
    
    console.print("  [green]# Search for tasks due in the last 3 days[/green]")
    console.print("  search last_3_days\n")
    
    console.print("  [green]# Search for upcoming tasks in the next 5 days[/green]")
    console.print("  search upcoming_next_5_days\n")
    
    console.print("  [green]# Search for tasks in a specific list[/green]")
    console.print("  search --list \"My Tasks\"\n")
    
    console.print("  [green]# Combined search with text and date filter[/green]")
    console.print("  search report today\n")
    
    console.print("  [green]# Combined search with text and list filter[/green]")
    console.print("  search meeting --list \"Work Projects\"\n")


def show_quit_help():
    """Display detailed help for the quit/exit command"""
    console.print(Panel("[bold blue]Quit/Exit Command Help[/bold blue]", expand=False))
    
    console.print("[bold]Description:[/bold]")
    console.print("Exit the interactive mode and return to the command line.\n")
    
    console.print("[bold]Usage:[/bold]")
    console.print("  quit")
    console.print("  exit\n")
    
    console.print("[bold]Examples:[/bold]")
    console.print("  [green]# Exit interactive mode[/green]")
    console.print("  quit")
    console.print("  [green]# Exit interactive mode[/green]")
    console.print("  exit\n")
    
    console.print("[bold]Notes:[/bold]")
    console.print("  - Either [yellow]quit[/yellow] or [yellow]exit[/yellow] can be used")
    console.print("  - No confirmation is required")
    console.print("  - All changes are automatically saved")