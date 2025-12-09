"""
Display utilities for the Google Tasks CLI application.
"""

from typing import List, Dict
from collections import defaultdict
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich.panel import Panel
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
        table.add_column("Created", style="dim", min_width=10)
        table.add_column("Modified", style="dim", min_width=10)
        
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
                status_str,
                task.created_at.strftime('%Y-%m-%d') if task.created_at else "",
                task.modified_at.strftime('%Y-%m-%d') if task.modified_at else ""
            )
        
        console.print(table)
        console.print()  # Add spacing between lists


def display_tasks_compact(tasks: List[Task]) -> None:
    """
    Display tasks in a compact format with essential details.
    
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
        console.print(f"\n[bold blue]{list_title}[/bold blue]")
        
        for task in list_tasks:
            # Format task number
            task_number = str(task_count)
            task_count += 1
            
            # Create content for the task
            task_content = []
            
            # Task title with notes indicator
            task_title = task.title
            if task.notes:
                task_title = f"{task_title} [italic](+)[/italic]"
            task_content.append(f"[bold]{task_title}[/bold]")
            
            # Add description/notes if available (max 3 lines)
            description_lines = []
            if task.description:
                # Limit to 3 lines
                desc_lines = task.description.strip().split('\n')[:3]
                for line in desc_lines:
                    if len(line) > 70:  # Limit line length
                        line = line[:67] + "..."
                    description_lines.append(f"  {line}")
            
            if task.notes:
                notes_lines = task.notes.strip().split('\n')[:3]
                for line in notes_lines:
                    if len(line) > 70:  # Limit line length
                        line = line[:67] + "..."
                    description_lines.append(f"  📌 {line}")
            
            # Add up to 3 lines of description/notes
            if description_lines:
                task_content.extend(description_lines[:3])
            
            # Add metadata line
            metadata_parts = []
            
            # Priority (moved up)
            priority_value = task.priority
            if hasattr(task.priority, 'value'):
                priority_value = task.priority.value
            
            priority_colors = {
                'critical': 'red',
                'high': 'orange1',
                'medium': 'yellow',
                'low': 'green'
            }
            metadata_parts.append(f"[{priority_colors.get(priority_value, 'white')}]{priority_value.title()}[/{priority_colors.get(priority_value, 'white')}]")
            

            
            # Status
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
            metadata_parts.append(f"[{status_colors.get(status_value, 'white')}]{status_value.replace('_', ' ').title()}[/{status_colors.get(status_value, 'white')}]")
            
            # Dates (Due, Created, Modified)
            if task.due:
                due_date = task.due.date() if isinstance(task.due, datetime) else task.due
                today = datetime.now().date()
                diff = (due_date - today).days
                
                due_str = f"D:{due_date}"
                if diff < 0:
                    metadata_parts.append(f"[red]{due_str}[/red]")
                elif diff == 0:
                    metadata_parts.append(f"[yellow]{due_str}[/yellow]")
                elif diff <= 3:
                    metadata_parts.append(f"[orange1]{due_str}[/orange1]")
                else:
                    metadata_parts.append(f"[green]{due_str}[/green]")

            if task.created_at:
                metadata_parts.append(f"[dim]C:{task.created_at.strftime('%Y-%m-%d')}[/dim]")
            if task.modified_at:
                metadata_parts.append(f"[dim]M:{task.modified_at.strftime('%Y-%m-%d')}[/dim]")
            
            # Combine metadata
            metadata_line = " | ".join(metadata_parts)
            task_content.append(metadata_line)
            
            # Print task content with minimal spacing
            console.print(f"[dim]{task_number}.[/dim] {' | '.join(task_content)}")
        
        console.print()  # Add spacing between lists


def display_tasks_with_details(tasks: List[Task]) -> None:
    """
    Display tasks with additional details in a formatted way.
    
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
        console.print(f"\n[bold blue]{list_title}[/bold blue]")
        console.print("=" * len(list_title))
        
        for task in list_tasks:
            # Format task number
            task_number = str(task_count)
            task_count += 1
            
            # Create panel content for the task
            panel_content = []
            
            # Task title with notes indicator
            task_title = task.title
            if task.notes:
                task_title = f"{task_title} [italic](+)[/italic]"
            panel_content.append(f"[bold]{task_title}[/bold]")
            
            # Add description/notes if available (max 3 lines)
            description_lines = []
            if task.description:
                # Limit to 3 lines
                desc_lines = task.description.strip().split('\n')[:3]
                for line in desc_lines:
                    if len(line) > 80:  # Limit line length
                        line = line[:77] + "..."
                    description_lines.append(f"  {line}")
            
            if task.notes:
                notes_lines = task.notes.strip().split('\n')[:3]
                for line in notes_lines:
                    if len(line) > 80:  # Limit line length
                        line = line[:77] + "..."
                    description_lines.append(f"  📌 {line}")
            
            # Add up to 3 lines of description/notes
            if description_lines:
                panel_content.extend(description_lines[:3])
            
            # Add metadata line
            metadata_parts = []
            
            # Priority (moved up)
            priority_value = task.priority
            if hasattr(task.priority, 'value'):
                priority_value = task.priority.value
            
            priority_colors = {
                'critical': 'red',
                'high': 'orange1',
                'medium': 'yellow',
                'low': 'green'
            }
            metadata_parts.append(f"[{priority_colors.get(priority_value, 'white')}]{priority_value.title()}[/{priority_colors.get(priority_value, 'white')}]")
            

            
            # Status
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
            metadata_parts.append(f"[{status_colors.get(status_value, 'white')}]{status_value.replace('_', ' ').title()}[/{status_colors.get(status_value, 'white')}]")
            
            # Dates (Due, Created, Modified)
            if task.due:
                due_date = task.due.date() if isinstance(task.due, datetime) else task.due
                today = datetime.now().date()
                diff = (due_date - today).days
                
                due_str = f"Due: {due_date}"
                if diff < 0:
                    metadata_parts.append(f"[red]{due_str} (Overdue)[/red]")
                elif diff == 0:
                    metadata_parts.append(f"[yellow]{due_str} (Today)[/yellow]")
                elif diff <= 3:
                    metadata_parts.append(f"[orange1]{due_str} ({diff} days)[/orange1]")
                else:
                    metadata_parts.append(f"[green]{due_str}[/green]")

            if task.created_at:
                metadata_parts.append(f"[dim]Created: {task.created_at.strftime('%Y-%m-%d')}[/dim]")
            if task.modified_at:
                metadata_parts.append(f"[dim]Modified: {task.modified_at.strftime('%Y-%m-%d')}[/dim]")
            
            # Combine metadata
            metadata_line = " | ".join(metadata_parts)
            panel_content.append(metadata_line)
            
            # Create and print panel for this task
            panel = Panel("\n".join(panel_content), title=f"[dim]#{task_number}[/dim]", 
                         border_style="bright_black", expand=False)
            console.print(panel)
        
        console.print()  # Add spacing between lists