"""
Module for viewing task details in interactive mode
"""

from gtasks_cli.models.task import TaskStatus, Priority
from rich.console import Console
from rich.panel import Panel
from rich.markup import escape

# Initialize Rich console for colored output
console = Console()


def view_task_details(task):
    """Display detailed information about a task with color formatting"""
    # Create a panel for the task details
    panel_content = []
    
    # Add basic task info
    panel_content.append(f"[bold]{escape(task.title)}[/bold]")
    panel_content.append(f"ID: {task.id}")
    
    # Add description
    if task.description:
        # Format description with proper alignment and limit
        max_chars = 500  # Increased limit for view details
        desc = task.description.strip()
        if len(desc) > max_chars:
            desc = desc[:max_chars].rsplit(' ', 1)[0] + "..."
        
        # Split description into lines for proper alignment
        desc_lines = desc.split('\n')
        formatted_desc = "\n".join([f"    {escape(line)}" for line in desc_lines])
        panel_content.append(f"[italic white]📝 {formatted_desc}[/italic white]")
    
    # Add notes
    if task.notes:
        panel_content.append(f"📌 Notes: {escape(task.notes)}")
    
    # Add due date
    if task.due:
        panel_content.append(f"[blue]📅 Due: {task.due.strftime('%Y-%m-%d')}[/blue]")
    
    # Add status and priority on the same line
    status_value = task.status if isinstance(task.status, str) else task.status.value
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
    
    priority_value = task.priority if isinstance(task.priority, str) else task.priority.value
    priority_colors = {
        'low': 'blue',
        'medium': 'yellow',
        'high': 'orange_red1',
        'critical': 'red'
    }
    priority_icon = {
        'low': '🔽',
        'medium': '🔸',
        'high': '🔺',
        'critical': '💥'
    }.get(priority_value, '🔹')
    priority_color = priority_colors.get(priority_value, 'white')
    
    status_priority_line = f"[{status_color}]{status_icon} {status_value.upper()}[/{status_color}] | [{priority_color}]{priority_icon} {priority_value.upper()}[/{priority_color}]"
    panel_content.append(status_priority_line)
    
    # Add project and tags
    project_tags_line = ""
    if task.project:
        project_tags_line += f"📁 {task.project}  "
    if task.tags:
        project_tags_line += f"🏷️  {', '.join(task.tags)}"
    
    if project_tags_line:
        panel_content.append(project_tags_line)
    
    # Add recurrence info
    if task.is_recurring:
        panel_content.append("🔁 Recurring Task")
    
    # Add dependencies
    if task.dependencies:
        deps_formatted = ", ".join(task.dependencies)
        panel_content.append(f"🔗 Dependencies: {deps_formatted}")
    
    # Add timestamps
    timestamp_lines = []
    timestamp_lines.append(f"⏱️ Created: {task.created_at}")
    if task.modified_at:
        timestamp_lines.append(f"🔄 Modified: {task.modified_at}")
    if hasattr(task, 'completed_at') and task.completed_at:
        timestamp_lines.append(f"✅ Completed: {task.completed_at}")
    
    if timestamp_lines:
        panel_content.extend(timestamp_lines)
    
    # Create and print the panel
    panel = Panel("\n".join(panel_content), title="Task Details", expand=False, border_style="bright_black")
    console.print(panel)