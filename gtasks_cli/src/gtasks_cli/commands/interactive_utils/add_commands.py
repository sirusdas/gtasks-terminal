#!/usr/bin/env python3
"""
Add command functionality for interactive mode
"""

import click
from gtasks_cli.models.task import Task, TaskStatus, Priority


def handle_add_command(task_state, task_manager, command_parts, use_google_tasks=False):
    """Handle the add command in interactive mode with conversational wizard prompts"""
    import uuid
    from datetime import datetime, timedelta
    from rich.console import Console
    from rich.panel import Panel
    from gtasks_cli.utils.space_extractor import parse_spaces_input, combine_notes_and_metadata

    console = Console()
    console.print("\n[bold cyan]🤖 Guided Task Creation Assistant[/bold cyan]")
    console.print("[dim]Type your answers or press Enter for defaults. Type 'cancel' to exit.[/dim]\n")

    # Step 1: Title
    title = click.prompt("  📝 Task title", type=str).strip()
    if not title or title.lower() in ['cancel', 'exit', 'q']:
        console.print("[yellow]Task creation cancelled.[/yellow]")
        return

    # Step 2: Due Date with presets
    console.print("  📅 Due date: [1] Today  [2] Tomorrow  [3] In 3 days  [4] Next week  [Enter] None")
    due_choice = click.prompt("     Select (1-4) or type date (YYYY-MM-DD)", default="", show_default=False).strip()
    
    due_date = None
    if due_choice == "1":
        due_date = datetime.now()
    elif due_choice == "2":
        due_date = datetime.now() + timedelta(days=1)
    elif due_choice == "3":
        due_date = datetime.now() + timedelta(days=3)
    elif due_choice == "4":
        due_date = datetime.now() + timedelta(days=7)
    elif due_choice and due_choice.lower() not in ['none', 'skip', 'no']:
        try:
            from dateutil import parser as date_parser
            due_date = date_parser.parse(due_choice)
        except Exception:
            console.print(f"     [yellow]⚠️ Could not parse '{due_choice}', skipping due date.[/yellow]")

    # Step 3: Priority with presets
    console.print("  ⚡ Priority: [1] Low  [2] Medium (default)  [3] High  [4] Critical")
    prio_choice = click.prompt("     Select (1-4)", default="2", show_default=False).strip()
    prio_map = {
        "1": Priority.LOW,
        "2": Priority.MEDIUM,
        "3": Priority.HIGH,
        "4": Priority.CRITICAL,
        "low": Priority.LOW,
        "medium": Priority.MEDIUM,
        "high": Priority.HIGH,
        "critical": Priority.CRITICAL,
    }
    priority = prio_map.get(prio_choice.lower(), Priority.MEDIUM)

    # Step 4: Spaces & Subspaces
    spaces_input = click.prompt("  🌌 Space / Subspace (e.g. work:frontend, personal) [Enter to skip]", default="", show_default=False).strip()
    spaces = parse_spaces_input(spaces_input) if spaces_input else {}

    # Step 5: Tags
    tags_input = click.prompt("  🏷️  Tags (comma-separated, e.g. urgent, backend) [Enter to skip]", default="", show_default=False).strip()
    tags = [t.strip().lstrip('#') for t in tags_input.split(',') if t.strip()] if tags_input else []

    # Step 6: Description / Notes
    notes_input = click.prompt("  📝 Description / Notes [Enter to skip]", default="", show_default=False).strip()
    description = notes_input if notes_input else None

    # Merge metadata into description if spaces or tags present
    if spaces or tags:
        description = combine_notes_and_metadata(description or "", tags=tags or None, spaces=spaces or None)

    # Preview card
    preview = [
        f"[bold]Title:[/bold]    {title}",
        f"[bold]Priority:[/bold] {priority.value.upper()}",
    ]
    if due_date:
        preview.append(f"[bold]Due:[/bold]      {due_date.strftime('%Y-%m-%d')}")
    if spaces:
        sp_strs = [f"{s} › {', '.join(subs)}" if subs else s for s, subs in spaces.items()]
        preview.append(f"[bold]Spaces:[/bold]   {' | '.join(sp_strs)}")
    if tags:
        preview.append(f"[bold]Tags:[/bold]     {', '.join(tags)}")
    if notes_input:
        preview.append(f"[bold]Notes:[/bold]    {notes_input}")

    console.print(Panel("\n".join(preview), title="✨ Ready to Add Task", border_style="cyan", expand=False))
    confirm = click.confirm("  Create this task?", default=True)
    if not confirm:
        console.print("[yellow]Task creation cancelled.[/yellow]")
        return

    # Create the task
    task = Task(
        id=str(uuid.uuid4()),
        title=title,
        description=description,
        notes=description,
        spaces=spaces,
        tags=tags,
        due=due_date,
        status=TaskStatus.PENDING,
        priority=priority
    )
    
    # Add the task
    added_task = task_manager.add_task(task)
    if added_task:
        click.echo(f"Task '{added_task.title}' added successfully.")
        
        # Check for auto-save (CLI option overrides config)
        from gtasks_cli.storage.config_manager import ConfigManager
        config_manager = ConfigManager(account_name=task_manager.account_name)
        cli_auto_save = getattr(task_manager, 'cli_auto_save', None)
        
        # Use CLI option if provided, otherwise use config
        if cli_auto_save is not None:
            auto_save = cli_auto_save
        else:
            auto_save = config_manager.get('sync.auto_save', False)
        
        if not use_google_tasks and auto_save:
            from gtasks_cli.integrations.advanced_sync_manager import AdvancedSyncManager
            click.echo("Auto-saving to Google Tasks...")
            sync_manager = AdvancedSyncManager(task_manager.storage, task_manager.google_client)
            if sync_manager.sync_single_task(added_task, 'create', old_task_id=added_task.id):
                 click.echo("✅ Auto-saved to Google Tasks")
            else:
                 click.echo("⚠️ Failed to auto-save to Google Tasks")
        
        # Register undo operation
        from gtasks_cli.commands.interactive_utils.undo_manager import undo_manager
        
        def undo_add():
            try:
                task_manager.delete_task(added_task.id)
                return True
            except Exception as e:
                click.echo(f"Undo add failed: {e}")
                return False

        undo_manager.push_operation(
            description=f"Add task '{added_task.title}'",
            undo_func=undo_add
        )
        
        # Instead of refreshing the whole list, just add the new task to current view
        _add_task_to_state(task_state, added_task)
    else:
        click.echo("Failed to add task.")


def _add_task_to_state(task_state, new_task):
    """Add a new task to the task state instead of refreshing the entire list"""
    # Add the task to the list
    task_state.tasks.append(new_task)
    
    # Refresh the mappings
    task_state.task_number_to_id = {}
    task_state.task_id_to_number = {}
    for i, task in enumerate(task_state.tasks, 1):
        task_state.task_number_to_id[i] = task.id
        task_state.task_id_to_number[task.id] = i