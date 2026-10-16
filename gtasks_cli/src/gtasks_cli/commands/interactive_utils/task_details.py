"""
Module for viewing task details in interactive mode
"""

from gtasks_cli.models.task import TaskStatus
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
    panel_content.append(f"[bold cyan]{escape(task.title)}[/bold cyan]")
    
    from gtasks_cli.utils.space_extractor import split_notes_and_metadata, extract_spaces_from_text

    raw_content = task.notes or task.description or ""
    clean_notes = ""
    spaces = getattr(task, 'spaces', None) or extract_spaces_from_text(raw_content)
    if raw_content:
        clean_notes, _, _ = split_notes_and_metadata(raw_content)

    # Add description / notes
    if clean_notes:
        max_chars = 600
        desc = clean_notes.strip()
        if len(desc) > max_chars:
            desc = desc[:max_chars].rsplit(' ', 1)[0] + "..."
        
        # Split description into lines for proper alignment
        desc_lines = desc.split('\n')
        formatted_desc = "\n".join([f"  [italic]{escape(line)}[/italic]" for line in desc_lines])
        panel_content.append(f"\n{formatted_desc}\n")
    
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
    
    status_priority_line = f"[{status_color}]{status_icon} {status_value.upper()}[/{status_color}]  |  [{priority_color}]{priority_icon} {priority_value.upper()}[/{priority_color}]"
    panel_content.append(status_priority_line)

    # Add due date
    if task.due:
        from datetime import datetime
        if isinstance(task.due, datetime):
            due_str = task.due.strftime('%Y-%m-%d %H:%M') if (task.due.hour or task.due.minute) else task.due.strftime('%Y-%m-%d')
        else:
            due_str = str(task.due)[:16]
        panel_content.append(f"[blue]📅 Due: {due_str}[/blue]")
    
    # Add project and tags
    project_tags_line = []
    if task.project:
        project_tags_line.append(f"📁 {task.project}")
    if task.tags:
        project_tags_line.append(f"🏷️  {', '.join(task.tags)}")
    if project_tags_line:
        panel_content.append("  ".join(project_tags_line))
    
    if spaces:
        space_strs = []
        for s_name, s_subs in spaces.items():
            if s_subs:
                space_strs.append(f"{escape(s_name)} › {escape(', '.join(s_subs))}")
            else:
                space_strs.append(escape(s_name))
        panel_content.append(f"[magenta]🌌 Spaces: {' | '.join(space_strs)}[/magenta]")
    
    # Add list name
    list_title = getattr(task, 'list_title', None)
    if list_title:
        panel_content.append(f"[dim]📓 List: {list_title}[/dim]")
    
    # Add recurrence info
    if task.is_recurring:
        panel_content.append("[green]🔁 Recurring Task[/green]")
    
    # Add dependencies
    if task.dependencies:
        deps_formatted = ", ".join(task.dependencies)
        panel_content.append(f"🔗 Dependencies: {deps_formatted}")
    
    # Add timestamps (clean format, no microseconds)
    timestamp_parts = []
    if task.created_at:
        c_str = task.created_at.strftime('%Y-%m-%d %H:%M') if hasattr(task.created_at, 'strftime') else str(task.created_at)[:16]
        timestamp_parts.append(f"⏱️ Created: {c_str}")
    if task.modified_at:
        m_str = task.modified_at.strftime('%Y-%m-%d %H:%M') if hasattr(task.modified_at, 'strftime') else str(task.modified_at)[:16]
        timestamp_parts.append(f"🔄 Modified: {m_str}")
    if hasattr(task, 'completed_at') and task.completed_at:
        done_str = task.completed_at.strftime('%Y-%m-%d %H:%M') if hasattr(task.completed_at, 'strftime') else str(task.completed_at)[:16]
        timestamp_parts.append(f"✅ Completed: {done_str}")
    
    if timestamp_parts:
        panel_content.append(f"[dim]{'  |  '.join(timestamp_parts)}[/dim]")
    
    # Create and print the panel
    panel = Panel("\n".join(panel_content), title="[bold]Task Details[/bold]", expand=False, border_style="cyan")
    console.print(panel)