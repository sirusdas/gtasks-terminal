"""
Module for displaying tasks in interactive mode
"""

from collections import defaultdict
from gtasks_cli.models.task import TaskStatus
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from datetime import datetime

# Initialize Rich console for colored output
console = Console()


def display_tasks_grouped_by_list(tasks, start_number=1):
    """Display tasks grouped by their list names"""
    # Debug: Show total tasks received
    console.print(f"[dim]DEBUG: Received {len(tasks)} total tasks to display[/dim]")
    
    # Group tasks by list title
    tasks_by_list = defaultdict(list)
    for task in tasks:
        list_title = getattr(task, 'list_title', 'Unknown List')
        tasks_by_list[list_title].append(task)
    
    # Debug: Show how many lists we're displaying
    console.print(f"[dim]DEBUG: Found {len(tasks_by_list)} lists to display tasks for[/dim]")
    
    # Display tasks grouped by list
    task_index = start_number
    all_tasks = []
    
    for list_title, list_tasks in tasks_by_list.items():
        # Debug: Show number of tasks in this list
        console.print(f"[dim]DEBUG: Processing list '{list_title}' with {len(list_tasks)} tasks[/dim]")
        
        # Display list name with color in a panel
        console.print(Panel(f"[bold blue]List Name: \"{list_title}\"[/bold blue]", expand=False))
        
        for i, task in enumerate(list_tasks, task_index):
            # Debug: Show raw task data
            console.print(f"[dim]DEBUG: Displaying task {i}: {task.id} - {task.title}[/dim]")
            
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

            # Format spaces if present
            spaces_info = ""
            from gtasks_cli.utils.space_extractor import extract_spaces_from_text, split_notes_and_metadata
            spaces = task.spaces or extract_spaces_from_text(task.notes or task.description or "")
            if spaces:
                sp_strs = []
                for s_name, s_subs in spaces.items():
                    if s_subs:
                        sp_strs.append(f"{s_name} › {', '.join(s_subs)}")
                    else:
                        sp_strs.append(s_name)
                spaces_info = f" [magenta]🌌 [{ ' | '.join(sp_strs) }][/magenta]"

            # Format recurring info
            recurring_info = ""
            if task.is_recurring:
                recurring_info = " [green]🔁[/green]"

            # Format created, modified, and due dates
            dates_info = ""
            if task.due:
                due_str = task.due.strftime('%Y-%m-%d') if hasattr(task.due, 'strftime') else str(task.due)[:10]
                dates_info += f" [dim]D:{due_str}[/dim]"

            if task.created_at:
                created_str = task.created_at.strftime('%Y-%m-%d')
                dates_info += f" [dim]C:{created_str}[/dim]"

            if task.modified_at:
                modified_str = task.modified_at.strftime('%Y-%m-%d')
                dates_info += f" [dim]M:{modified_str}[/dim]"

            # Format description/notes with limit (at least 3 lines)
            description_info = ""
            content = task.description or task.notes
            if content:
                # Strip metadata dividers so clean notes are displayed
                clean_content, _, _ = split_notes_and_metadata(content)
                desc = clean_content.strip()
                if desc:
                    desc_lines = desc.split('\n')
                    formatted_lines = []
                    for line in desc_lines[:3]:
                        if line.strip():
                            line_text = Text(f"      {line}", style="italic white")
                            formatted_lines.append(line_text)
                    if formatted_lines:
                        description_info = formatted_lines

            # Display task with number
            task_line = f"  {i:2d}. [bright_black]{task.id[:8]}[/bright_black]: [{status_color}]{status_icon}[/{status_color}] [{priority_color}]{priority_icon}[/{priority_color}] {task.title}{due_info}{project_info}{tags_info}{spaces_info}{recurring_info}{dates_info}"
            console.print(task_line)
            
            # Display description/notes separately to avoid markup interpretation issues
            if description_info:
                for line_text in description_info:
                    console.print(line_text)
            
            # Add list name for the task
            list_title = getattr(task, 'list_title', 'Unknown List')
            console.print(f"     [dim]📓 List: {list_title}[/dim]")
                
            all_tasks.append(task)
        task_index += len(list_tasks)
        console.print()  # Add spacing between lists
    
    return all_tasks

def _format_date_display(date_obj) -> str:
    """Format date for display"""
    if not date_obj:
        return ""
    return date_obj.strftime('%Y-%m-%d')