#!/usr/bin/env python3
"""
Help system for interactive mode commands
"""

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
    table.add_row("add", "Add a new task")
    table.add_row("list", "List all tasks with optional filters")
    table.add_row("search <query>", "Search for tasks")
    table.add_row("back", "Go back to previous command results")
    table.add_row("default", "Go back to default task listing")
    table.add_row("help", "Show this help message")
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
    console.print("  [green]# List tasks with filters[/green]")
    console.print("  list --status pending --priority high")
    console.print("  [green]# Search for tasks[/green]")
    console.print("  search meeting")


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
    console.print("  update-status C[1,2,3], DT[1,2,3], DEL[4], P[5,6], DUE[7,8,9|21-09|10:10 PM]\n")
    
    console.print("[bold]Operations:[/bold]")
    console.print("  [yellow]C[task_numbers][/yellow]          Mark tasks as COMPLETED")
    console.print("  [yellow]DT[task_numbers][/yellow]         Set tasks due TODAY (end of day)")
    console.print("  [yellow]DT[task_numbers|time][/yellow]   Set tasks due TODAY at specific time")
    console.print("  [yellow]DEL[task_numbers][/yellow]        Mark tasks as DELETED")
    console.print("  [yellow]P[task_numbers][/yellow]          Mark tasks as PENDING")
    console.print("  [yellow]DUE[task_ids|date|time][/yellow] Set tasks due on specific date and time\n")
    
    console.print("[bold]Format Details:[/bold]")
    console.print("  [yellow]task_numbers[/yellow]   Comma-separated list of task numbers (e.g., 1,2,3)")
    console.print("  [yellow]time[/yellow]          Time in 12-hour format with AM/PM (e.g., 09:00 PM)")
    console.print("  [yellow]date[/yellow]          Date in DD-MM format (e.g., 21-09)\n")
    
    console.print("[bold]Examples:[/bold]")
    console.print("  [green]# Mark tasks 1,2,3 as completed[/green]")
    console.print("  update-status C[1,2,3]")
    console.print("  [green]# Mark tasks 1,2 as completed and 3 as deleted[/green]")
    console.print("  update-status C[1,2], DEL[3]")
    console.print("  [green]# Set task 1 due today at 3:30 PM[/green]")
    console.print("  update-status DT[1|3:30 PM]")
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
    console.print("List tasks with optional filters and sorting.\n")
    
    console.print("[bold]Usage:[/bold]")
    console.print("  list [--status <status>] [--priority <priority>] [--project <project>] [--recurring]")
    console.print("       [--filter <time_filter>] [--order-by <field>] [--search <query>]\n")
    
    console.print("[bold]Options:[/bold]")
    console.print("  [yellow]--status[/yellow]      Filter by status (pending, in_progress, completed, waiting, deleted)")
    console.print("  [yellow]--priority[/yellow]    Filter by priority (low, medium, high, critical)")
    console.print("  [yellow]--project[/yellow]     Filter by project")
    console.print("  [yellow]--recurring, -r[/yellow]  Show only recurring tasks")
    console.print("  [yellow]--filter[/yellow]      Filter by time (today, this_week, this_month, etc.)")
    console.print("  [yellow]--order-by, -o[/yellow]  Sort tasks by field (title, due_date, created_at, modified_at)")
    console.print("  [yellow]--search[/yellow]      Search for tasks by query\n")
    
    console.print("[bold]Examples:[/bold]")
    console.print("  [green]# List all tasks[/green]")
    console.print("  list")
    console.print("  [green]# List pending high priority tasks[/green]")
    console.print("  list --status pending --priority high")
    console.print("  [green]# List tasks due this week, sorted by due date[/green]")
    console.print("  list --filter this_week --order-by due_date")


def show_quit_help():
    """Show help for the quit/exit command"""
    console.print(Panel("[bold blue]Quit/Exit Command Help[/bold blue]", expand=False))
    
    console.print("[bold]Description:[/bold]")
    console.print("Exit the interactive mode.\n")
    
    console.print("[bold]Usage:[/bold]")
    console.print("  quit")
    console.print("  exit\n")
    
    console.print("[bold]Examples:[/bold]")
    console.print("  [green]# Exit interactive mode[/green]")
    console.print("  quit")
    console.print("  exit")