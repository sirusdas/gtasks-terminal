#!/usr/bin/env python3
"""
Help system for interactive mode commands
"""

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def show_general_help():
    """Show general help for interactive mode"""
    console.print(Panel("[bold blue]Interactive Mode Help[/bold blue]", expand=False))
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Command", style="cyan", width=15)
    table.add_column("Description", style="white")
    
    table.add_row("view <number>", "View detailed information about a task")
    table.add_row("done <number>", "Mark a task as completed")
    table.add_row("delete <number>", "Delete a task")
    table.add_row("update <number>", "Update a task (title, description)")
    table.add_row("update-status", "Bulk update task status and due dates")
    table.add_row("update-tags", "Bulk update task tags")
    table.add_row("add", "Add a new task")
    table.add_row("list", "List all tasks with optional filters")
    table.add_row("search <query>", "Search for tasks")
    table.add_row("back", "Go back to previous command results")
    table.add_row("default", "Go back to default task listing")
    table.add_row("help", "Show this help message")
    table.add_row("tags", "Filter tasks by tags")
    table.add_row("quit/exit", "Exit interactive mode")
    
    console.print(table)
    
    console.print("\n[bold]Examples:[/bold]")
    console.print("  [green]# View task details[/green]")
    console.print("  view 1")
    console.print("  [green]# Mark task as completed[/green]")
    console.print("  done 1")
    console.print("  [green]# Update task with editor[/green]")
    console.print("  update 1 --editor")
    console.print("  [green]# Bulk update task status[/green]")
    console.print("  update-status C[1,2], DT[3], DEL[4], P[5], DUE[6|21-09|10:10 PM]")
    console.print("  [green]# Bulk update task tags[/green]")
    console.print("  update-tags ADD[1,2|work], DEL[3|personal]")
    console.print("  update-tags ALL[ADD:urgent]")
    console.print("  [green]# List tasks with filters[/green]")
    console.print("  list --status pending --priority high")
    console.print("  [green]# Search for tasks[/green]")
    console.print("  search meeting")
    console.print("  [green]# List tasks by tag[/green]")
    console.print("  tags work")
    console.print("  tags personal --status pending")


def show_update_help():
    """Show help for the update command"""
    console.print(Panel("[bold blue]Update Command Help[/bold blue]", expand=False))
    
    console.print("[bold]Description:[/bold]")
    console.print("Update task details such as title and description.")
    console.print("You can use an external editor or interactive prompts.\n")
    
    console.print("[bold]Usage:[/bold]")
    console.print("  update <task_number> [--editor|-e]\n")
    
    console.print("[bold]Options:[/bold]")
    console.print("  [yellow]--editor, -e[/yellow]  Use external editor for editing task\n")
    
    console.print("[bold]Examples:[/bold]")
    console.print("  [green]# Update task with interactive prompts[/green]")
    console.print("  update 1")
    console.print("  [green]# Update task with external editor[/green]")
    console.print("  update 1 --editor")
    console.print("  update 1 -e")


def show_bulk_update_help():
    """Show help for the bulk update status command"""
    console.print(Panel("[bold blue]Bulk Update Status Command Help[/bold blue]", expand=False))
    
    console.print("[bold]Description:[/bold]")
    console.print("Bulk update multiple tasks' status and due dates in a single command.\n")
    
    console.print("[bold]Usage:[/bold]")
    console.print("  update-status C[1,2,3], DT[1,2,3], DEL[4], P[5,6], DUE[7,8,9|21-09|10:10 PM]")
    console.print("  update-status ALL[C], ALL[DT], ALL[DUE:TODAY], ALL[DUE:26-11]\n")
    
    console.print("[bold]Operations:[/bold]")
    console.print("  [yellow]C[task_numbers][/yellow]          Mark tasks as COMPLETED")
    console.print("  [yellow]DT[task_numbers][/yellow]         Set tasks due TODAY (end of day)")
    console.print("  [yellow]DT[task_numbers|time][/yellow]   Set tasks due TODAY at specific time")
    console.print("  [yellow]DEL[task_numbers][/yellow]        Mark tasks as DELETED")
    console.print("  [yellow]P[task_numbers][/yellow]          Mark tasks as PENDING")
    console.print("  [yellow]DUE[task_ids|date|time][/yellow] Set tasks due on specific date and time")
    console.print("  [yellow]ALL[operation][/yellow]           Apply operation to ALL currently displayed tasks\n")
    
    console.print("[bold]Format Details:[/bold]")
    console.print("  [yellow]task_numbers[/yellow]   Comma-separated list of task numbers (e.g., 1,2,3)")
    console.print("  [yellow]time[/yellow]          Time in 12-hour format with AM/PM (e.g., 09:00 PM)")
    console.print("  [yellow]date[/yellow]          Date in DD-MM format (e.g., 21-09)")
    console.print("  [yellow]ALL[][/yellow]         Apply to all displayed tasks (e.g., ALL[C], ALL[DUE:TODAY])\n")
    
    console.print("[bold]Examples:[/bold]")
    console.print("  [green]# Mark tasks 1,2,3 as completed[/green]")
    console.print("  update-status C[1,2,3]")
    console.print("  [green]# Mark tasks 1,2 as completed and 3 as deleted[/green]")
    console.print("  update-status C[1,2], DEL[3]")
    console.print("  [green]# Set task 1 due today at 3:30 PM[/green]")
    console.print("  update-status DT[1|3:30 PM]")
    console.print("  [green]# Mark ALL displayed tasks as completed[/green]")
    console.print("  update-status ALL[C]")
    console.print("  [green]# Set ALL displayed tasks due today[/green]")
    console.print("  update-status ALL[DUE:TODAY]")
    console.print("  [green]# Set ALL displayed tasks due on Nov 26[/green]")
    console.print("  update-status ALL[DUE:26-11]")
    console.print("  [green]# Set tasks 1,2 as completed, task 3 due today, task 4 deleted, task 5 pending, task 6 due Sept 21 at 10:10 PM[/green]")
    console.print("  update-status C[1,2], DT[3], DEL[4], P[5], DUE[6|21-09|10:10 PM]")


def show_view_help():
    """Show help for the view command"""
    console.print(Panel("[bold blue]View Command Help[/bold blue]", expand=False))
    
    console.print("[bold]Description:[/bold]")
    console.print("View detailed information about a specific task.\n")
    
    console.print("[bold]Usage:[/bold]")
    console.print("  view <task_number>\n")
    
    console.print("[bold]Examples:[/bold]")
    console.print("  [green]# View details of task number 1[/green]")
    console.print("  view 1")


def show_done_help():
    """Show help for the done command"""
    console.print(Panel("[bold blue]Done Command Help[/bold blue]", expand=False))
    
    console.print("[bold]Description:[/bold]")
    console.print("Mark a task as completed.\n")
    
    console.print("[bold]Usage:[/bold]")
    console.print("  done <task_number>\n")
    
    console.print("[bold]Examples:[/bold]")
    console.print("  [green]# Mark task number 1 as completed[/green]")
    console.print("  done 1")


def show_delete_help():
    """Show help for the delete command"""
    console.print(Panel("[bold blue]Delete Command Help[/bold blue]", expand=False))
    
    console.print("[bold]Description:[/bold]")
    console.print("Mark a task as deleted.\n")
    
    console.print("[bold]Usage:[/bold]")
    console.print("  delete <task_number>\n")
    
    console.print("[bold]Examples:[/bold]")
    console.print("  [green]# Mark task number 1 as deleted[/green]")
    console.print("  delete 1")


def show_add_help():
    """Show help for the add command"""
    console.print(Panel("[bold blue]Add Command Help[/bold blue]", expand=False))
    
    console.print("[bold]Description:[/bold]")
    console.print("Add a new task.\n")
    
    console.print("[bold]Usage:[/bold]")
    console.print("  add\n")
    
    console.print("[bold]Examples:[/bold]")
    console.print("  [green]# Add a new task[/green]")
    console.print("  add")


def show_list_help():
    """Show help for the list command"""
    console.print(Panel("[bold blue]List Command Help[/bold blue]", expand=False))
    
    console.print("[bold]Description:[/bold]")
    console.print("List tasks with optional filtering and sorting options.\n")
    
    console.print("[bold]Usage:[/bold]")
    console.print("  list [filter]")
    console.print("  list [--status <status>] [--priority <priority>] [--project <project>]")
    console.print("  list [--recurring] [--filter <time_filter>] [--search <query>]")
    console.print("  list [--order-by <field>]\n")
    
    console.print("[bold]Examples:[/bold]")
    console.print("  list")
    console.print("  list work")
    console.print("  list --status pending")
    console.print("  list --priority high")
    console.print("  list --filter this_week")
    console.print("  list --search \"meeting\"")
    console.print("  list --order-by due\n")
                        
    console.print("[bold]Time Filtering:[/bold]")
    console.print("You can filter tasks by time periods using the --filter option:")
    console.print("  [yellow]today[/yellow]          - Tasks for today")
    console.print("  [yellow]this_week[/yellow]      - Tasks for this week")
    console.print("  [yellow]this_month[/yellow]     - Tasks for this month")
    console.print("  [yellow]last_month[/yellow]     - Tasks from last month")
    console.print("  [yellow]last_3m[/yellow]        - Tasks from the last 3 months")
    console.print("  [yellow]last_6m[/yellow]        - Tasks from the last 6 months")
    console.print("  [yellow]last_year[/yellow]      - Tasks from the last year")
    console.print("  [yellow]DDMMYYYY[/yellow]       - Tasks for a specific date (e.g., 25122023)")
    console.print("  [yellow]DDMMYYYY-DDMMYYYY[/yellow] - Tasks within a date range (e.g., 01122023-31122023)\n")
                        
    console.print("You can also specify which date field to filter on by appending ':<field>' to the filter:")
    console.print("  [yellow]this_week:due_date[/yellow]     - Tasks due this week")
    console.print("  [yellow]this_month:created_at[/yellow]  - Tasks created this month")
    console.print("  [yellow]25122023:modified_at[/yellow]   - Tasks modified on Dec 25, 2023")
    console.print("Available date fields: [yellow]due_date[/yellow], [yellow]created_at[/yellow], [yellow]modified_at[/yellow]\n")

    console.print("[bold]Filter Options:[/bold]")
    console.print("  [yellow]--status[/yellow]     Filter by status (pending, in_progress, completed, waiting, deleted)")
    console.print("  [yellow]--priority[/yellow]   Filter by priority (low, medium, high, critical)")
    console.print("  [yellow]--project[/yellow]    Filter by project")
    console.print("  [yellow]--recurring[/yellow]  Show only recurring tasks")
    console.print("  [yellow]--filter[/yellow]     Filter by time period (today, this_week, this_month, etc.)")
    console.print("  [yellow]--search[/yellow]     Search by title, description or notes")
    console.print("  [yellow]--order-by[/yellow]   Sort by field (due, created, modified, title)")
    
    console.print("\n[bold]Time Filters:[/bold]")
    console.print("  today, this_week, this_month, last_month, last_3m, last_6m, last_year")


def show_tags_help():
    """Show help for the tags command"""
    console.print(Panel("[bold blue]Tags Command Help[/bold blue]", expand=False))
    
    console.print("[bold]Description:[/bold]")
    console.print("Filter tasks by tags. Tags are case-insensitive and can be combined with other filters.\n")
    
    console.print("[bold]Usage:[/bold]")
    console.print("  tags <tag> [filters]\n")
    
    console.print("[bold]Examples:[/bold]")
    console.print("  [green]# List tasks with 'work' tag[/green]")
    console.print("  tags work")
    console.print("  [green]# List tasks with 'personal' tag and pending status[/green]")
    console.print("  tags personal --status pending")
    console.print("  [green]# List tasks with multiple tags[/green]")
    console.print("  tags work family")
    console.print("  [green]# List tasks with 'work' tag due this week[/green]")
    console.print("  tags work --filter this_week")
    
    console.print("\n[bold]Note:[/bold]")
    console.print("The tags command supports all the filters available in the list command.")
    console.print("If multiple tags are provided, tasks must match all tags.")


def show_search_help():
    """Show help for the search command"""
    console.print(Panel("[bold blue]Search Command Help[/bold blue]", expand=False))
    
    console.print("[bold]Description:[/bold]")
    console.print("Search for tasks by title, description, or notes.\n")
    
    console.print("[bold]Usage:[/bold]")
    console.print("  search <query>\n")
    
    console.print("[bold]Examples:[/bold]")
    console.print("  [green]# Search for tasks containing 'meeting'[/green]")
    console.print("  search meeting")
    console.print("  [green]# Search for tasks containing 'report' or 'presentation'[/green]")
    console.print("  search report|presentation")
    console.print("  [green]# Search in combination with other commands[/green]")
    console.print("  list --search \"meeting\" --status pending")
    console.print("  list --search \"report|presentation\" --priority high\n")
                        
    console.print("[bold]Advanced Search Features:[/bold]")
    console.print("1. [yellow]Exclusion Search[/yellow]: Prefix your search term with '-' to exclude tasks containing that term")
    console.print("   Example: search \"-meeting\" - finds tasks that do NOT contain 'meeting'")
    console.print("2. [yellow]Exact Search[/yellow]: Wrap your search term in double quotes for exact matching")
    console.print("   Example: search \"\"important task\"\" - finds tasks with the exact title/description 'important task'")
    console.print("3. [yellow]Special Term Syntax[/yellow]: Use prefixes within search terms for advanced matching")
    console.print("   [yellow]--em:<term>[/yellow] - Exact match for the specified term")
    console.print("   Example: search \"--em:apple\" - finds tasks with exact match for 'apple'")
    console.print("   [yellow]--ex:<term>[/yellow] - Exclude tasks containing the specified term")
    console.print("   Example: search \"--ex:banana\" - excludes tasks containing 'banana'")
    console.print("   Combine with OR logic: search \"--em:apple|--em:mango|--ex:rotten\"")
    console.print("4. [yellow]Combined Search[/yellow]: Use pipe (|) for OR logic with multiple terms")
    console.print("   Example: search \"work|-personal\" - finds tasks with 'work' but not 'personal'\n")
