"""
Module for displaying tasks in interactive mode
"""

from collections import defaultdict
from gtasks_cli.models.task import TaskStatus, Priority
from rich.console import Console
from rich.panel import Panel

# Initialize Rich console for colored output
console = Console()


def display_tasks_grouped_by_list(tasks, start_number=1):
    """Display tasks grouped by their list names"""
    # Group tasks by list title
    tasks_by_list = defaultdict(list)
    for task in tasks:
        list_title = getattr(task, 'list_title', 'Unknown List')
        tasks_by_list[list_title].append(task)
    
    # Display tasks grouped by list
    task_index = start_number
    all_tasks = []
    
    for list_title, list_tasks in tasks_by_list.items():
        # Display list name with color in a panel
        console.print(Panel(f"[bold blue]List Name: \"{list_title}\"[/bold blue]", expand=False))
        
        for i, task in enumerate(list_tasks, task_index):
            # For enum values, we need to check if they are already strings or enum instances
            status_value = task.status if isinstance(task.status, str) else task.status.value
            priority_value = task.priority if isinstance(task.priority, str) else task.priority.value
            
            # Color coding for status
            status_colors = {
                'pending': 'yellow',
                'in_progress': 'cyan',
                'completed': 'green',
                'waiting': 'magenta',
                'deleted': 'red'
            }
            status_icon = {
                'pending': '⏳',
                'in_progress': '🔄',
                'completed': '✅',
                'waiting': '⏸️',
                'deleted': '🗑️'
            }.get(status_value, '❓')
            status_color = status_colors.get(status_value, 'white')
            
            # Color coding for priority
            priority_colors = {
                'low': 'blue',
                'medium': 'yellow',
                'high': 'orange_red1',  # More vibrant orange
                'critical': 'red'
            }
            priority_icon = {
                'low': '🔽',
                'medium': '🔸',
                'high': '🔺',
                'critical': '💥'
            }.get(priority_value, '🔹')
            priority_color = priority_colors.get(priority_value, 'white')
            
            # Format due date if present
            due_info = ""
            if task.due:
                due_info = f" [blue]📅 {task.due.strftime('%Y-%m-%d')}[/blue]"
            
            # Format project if present
            project_info = ""
            if task.project:
                project_info = f" [purple]📁 {task.project}[/purple]"
            
            # Format tags if present
            tags_info = ""
            if task.tags:
                tags_info = f" [cyan]🏷️  {', '.join(task.tags)}[/cyan]"
            
            # Format recurring info
            recurring_info = ""
            if task.is_recurring:
                recurring_info = " [green]🔁[/green]"
            
            # Format description/notes with limit (max 3 lines)
            description_info = ""
            content = task.description or task.notes
            if content:
                # Limit content to 3 lines
                max_chars = 300
                desc = content.strip()
                if len(desc) > max_chars:
                    # Try to break at a word boundary
                    truncated = desc[:max_chars].rsplit(' ', 1)[0] + "..."
                    desc_lines = truncated.split('\n')
                else:
                    desc_lines = desc.split('\n')
                
                # Take only first 3 lines and format them
                formatted_lines = []
                for line in desc_lines[:3]:
                    if line.strip():  # Only add non-empty lines
                        formatted_lines.append(f"      [italic white]{line.strip()}[/italic white]")
                
                # Join the lines with newlines
                if formatted_lines:
                    description_info = "\n" + "\n".join(formatted_lines)
            
            # Display task with number
            task_line = f"  {i:2d}. [bright_black]{task.id[:8]}[/bright_black]: [{status_color}]{status_icon}[/{status_color}] [{priority_color}]{priority_icon}[/{priority_color}] {task.title}{due_info}{project_info}{tags_info}{recurring_info}{description_info}"
            console.print(task_line)
                
            all_tasks.append(task)
        task_index += len(list_tasks)
        console.print()  # Add spacing between lists
    
    return all_tasks