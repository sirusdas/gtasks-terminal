"""
Display utilities for the Google Tasks CLI application.
"""

from typing import List, Dict
from collections import defaultdict
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.text import Text
from gtasks_cli.models.task import Task

console = Console()


def display_tasks_grouped_by_list(tasks: List[Task]) -> None:
    """
    Display tasks grouped by list names with color coding.
    
    Args:
        tasks: List of Task objects to display
    """
    if not tasks:
        console.print("No tasks found.")
        return
    
    # Group tasks by list title
    tasks_by_list = defaultdict(list)
    for task in tasks:
        list_title = getattr(task, 'list_title', 'Tasks')
        tasks_by_list[list_title].append(task)
    
    # Display tasks for each list
    task_count = 1
    for list_title, list_tasks in tasks_by_list.items():
        # Create table for this list
        table = Table(title=f"[bold blue]{list_title}[/bold blue]", show_header=True, header_style="bold magenta")
        table.add_column("No.", style="dim", width=4)
        table.add_column("Task", min_width=20)
        table.add_column("Due Date", min_width=12)
        table.add_column("Priority", min_width=8)
        table.add_column("Status", min_width=12)
        
        # Add tasks to table
        for task in list_tasks:
            # Format task number
            task_number = str(task_count)
            task_count += 1
            
            # Format task title with notes indicator
            task_title = task.title
            if task.notes:
                task_title = f"{task_title} [italic](+)[/italic]"
            
            # Format due date with color coding
            due_date_str = ""
            if task.due:
                due_date = task.due.date() if isinstance(task.due, datetime) else task.due
                today = datetime.now().date()
                diff = (due_date - today).days
                
                if diff < 0:
                    due_date_str = f"[red]{due_date}[/red]"  # Overdue
                elif diff == 0:
                    due_date_str = f"[yellow]{due_date}[/yellow]"  # Today
                elif diff <= 3:
                    due_date_str = f"[orange1]{due_date}[/orange1]"  # Due soon
                elif diff <= 7:
                    due_date_str = f"[yellow]{due_date}[/yellow]"  # This week
                else:
                    due_date_str = f"[green]{due_date}[/green]"  # Future
            
            # Format priority with color coding
            # Handle both string and enum priorities
            priority_value = task.priority
            if hasattr(task.priority, 'value'):
                priority_value = task.priority.value
            
            priority_colors = {
                'critical': 'red',
                'high': 'orange1',
                'medium': 'yellow',
                'low': 'green'
            }
            priority_str = f"[{priority_colors.get(priority_value, 'white')}]{priority_value.title()}[/{priority_colors.get(priority_value, 'white')}]"
            
            # Format status with color coding
            # Handle both string and enum statuses
            status_value = task.status
            if hasattr(task.status, 'value'):
                status_value = task.status.value
                
            status_colors = {
                'pending': 'yellow',
                'in_progress': 'blue',
                'completed': 'green',
                'waiting': 'magenta',
                'deleted': 'red'
            }
            status_str = f"[{status_colors.get(status_value, 'white')}]{status_value.replace('_', ' ').title()}[/{status_colors.get(status_value, 'white')}]"
            
            table.add_row(
                task_number,
                task_title,
                due_date_str,
                priority_str,
                status_str
            )
        
        console.print(table)
        console.print()  # Add spacing between lists