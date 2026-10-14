#!/usr/bin/env python3
"""
Space and sub-space selection commands for interactive mode
"""

import click
import os
import re
from typing import List, Dict, Set
from collections import defaultdict

from gtasks_cli.utils.logger import setup_logger
from gtasks_cli.models.task import Task
from gtasks_cli.utils.space_extractor import extract_spaces_from_text
from gtasks_cli.commands.interactive_utils.display import display_tasks_grouped_by_list
from gtasks_cli.commands.interactive_utils.task_details import view_task_details

# Try to import prompt_toolkit for enhanced command line experience
try:
    from prompt_toolkit import prompt
    from prompt_toolkit.history import FileHistory, InMemoryHistory
    from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
    HAS_PROMPT_TOOLKIT = True
except ImportError:
    HAS_PROMPT_TOOLKIT = False

logger = setup_logger(__name__)


def collect_spaces_and_subspaces_from_tasks(tasks: List[Task]):
    """Collect spaces and sub-spaces mapping to tasks."""
    space_to_tasks = defaultdict(list)
    subspace_to_tasks = defaultdict(lambda: defaultdict(list))
    all_spaces = set()

    for task in tasks:
        spaces = getattr(task, 'spaces', None) or extract_spaces_from_text(task.notes or task.description or "")
        for space_name, subspaces in spaces.items():
            all_spaces.add(space_name)
            space_to_tasks[space_name].append(task)
            for sub in subspaces:
                subspace_to_tasks[space_name][sub].append(task)

    return space_to_tasks, subspace_to_tasks, all_spaces


def handle_spaces_command(task_manager, use_google_tasks: bool = False) -> List[Task]:
    """Handle the spaces command in interactive mode - display spaces tree and allow selection."""
    try:
        tasks = task_manager.list_tasks()
        logger.info(f"Loaded {len(tasks)} tasks for spaces listing")

        if not tasks:
            click.echo("No tasks found.")
            return []

        space_to_tasks, subspace_to_tasks, all_spaces = collect_spaces_and_subspaces_from_tasks(tasks)

        if not all_spaces:
            click.echo("No spaces found in any tasks.")
            return []

        sorted_spaces = sorted(list(all_spaces))

        # Display spaces hierarchical tree
        click.echo("\nAvailable Spaces & Sub-spaces:")
        click.echo("=" * 50)

        # Index mapping for numeric / alphanumeric selection
        selection_map = {}  # "1" -> (space, None), "1a" -> (space, sub)

        for i, space in enumerate(sorted_spaces, 1):
            space_task_count = len(space_to_tasks[space])
            click.echo(f"  {i:2d}. 🌌 [bold]{space}[/bold] ({space_task_count} task{'s' if space_task_count != 1 else ''})")
            selection_map[str(i)] = (space, None)

            subs = sorted(list(subspace_to_tasks[space].keys()))
            for j, sub in enumerate(subs):
                letter = chr(ord('a') + j)
                sub_count = len(subspace_to_tasks[space][sub])
                code = f"{i}{letter}"
                selection_map[code] = (space, sub)
                click.echo(f"      {letter}. › {sub} ({sub_count} task{'s' if sub_count != 1 else ''}) [code: {code}]")

        click.echo(f"\nTotal: {len(sorted_spaces)} space(s)")
        click.echo("\nEnter space number (e.g. 1), sub-space code (e.g. 1a), name (e.g. work or work:frontend), or 'all'.")
        click.echo("Press Enter to cancel.")

        user_input = click.prompt("Select space", type=str, default="", show_default=False).strip()
        if not user_input:
            click.echo("Space selection cancelled.")
            return []

        selected_tasks = []
        target_label = ""

        input_lower = user_input.lower()

        if input_lower == 'all':
            seen_ids = set()
            for sp in sorted_spaces:
                for t in space_to_tasks[sp]:
                    if t.id not in seen_ids:
                        seen_ids.add(t.id)
                        selected_tasks.append(t)
            target_label = "all spaces"

        elif input_lower in selection_map:
            sp, sub = selection_map[input_lower]
            if sub:
                selected_tasks = subspace_to_tasks[sp][sub]
                target_label = f"{sp} › {sub}"
            else:
                selected_tasks = space_to_tasks[sp]
                target_label = sp

        elif ':' in user_input:
            # Format: space:subspace
            parts = user_input.split(':', 1)
            sp_query = parts[0].strip().lower()
            sub_query = parts[1].strip().lower()

            matched_sp = next((s for s in sorted_spaces if s.lower() == sp_query), None)
            if matched_sp and sub_query in [s.lower() for s in subspace_to_tasks[matched_sp]]:
                real_sub = next(s for s in subspace_to_tasks[matched_sp] if s.lower() == sub_query)
                selected_tasks = subspace_to_tasks[matched_sp][real_sub]
                target_label = f"{matched_sp} › {real_sub}"
            else:
                click.echo(f"No sub-space found matching: {user_input}")
                return []

        else:
            # Check by space name directly
            matched_sp = next((s for s in sorted_spaces if s.lower() == input_lower or input_lower in s.lower()), None)
            if matched_sp:
                selected_tasks = space_to_tasks[matched_sp]
                target_label = matched_sp
            else:
                # Check if it matches a subspace name anywhere
                sub_matches = []
                for sp, subs in subspace_to_tasks.items():
                    for sub in subs:
                        if sub.lower() == input_lower or input_lower in sub.lower():
                            sub_matches.append((sp, sub))

                if len(sub_matches) == 1:
                    sp, sub = sub_matches[0]
                    selected_tasks = subspace_to_tasks[sp][sub]
                    target_label = f"{sp} › {sub}"
                elif len(sub_matches) > 1:
                    click.echo("Multiple sub-spaces match. Please use space:subspace syntax:")
                    for sp, sub in sub_matches:
                        click.echo(f"  {sp}:{sub}")
                    return []
                else:
                    click.echo(f"No space or sub-space found matching: {user_input}")
                    return []

        if not selected_tasks:
            click.echo(f"No tasks found in {target_label}.")
            return []

        click.echo(f"\nFound {len(selected_tasks)} task(s) in {target_label}:")
        displayed_tasks = display_tasks_grouped_by_list(selected_tasks)
        return displayed_tasks

    except Exception as e:
        logger.error(f"Error in handle_spaces_command: {e}")
        click.echo(f"An error occurred while processing spaces: {e}")
        return []


def handle_space_filtering_interactive_mode(task_manager, use_google_tasks: bool = False):
    """Enter interactive mode for space-filtered tasks."""
    try:
        tasks = handle_spaces_command(task_manager, use_google_tasks)
        if not tasks:
            return

        _enter_space_filtered_interactive_mode(tasks, task_manager, use_google_tasks)

    except Exception as e:
        logger.error(f"Error in handle_space_filtering_interactive_mode: {e}")
        click.echo(f"An error occurred: {e}")


def _enter_space_filtered_interactive_mode(tasks: List[Task], task_manager, use_google_tasks: bool):
    """Interactive loop for space-filtered tasks."""
    try:
        from gtasks_cli.commands.interactive_utils.done_commands import handle_done_command
        from gtasks_cli.commands.interactive_utils.delete_commands import handle_delete_command
        from gtasks_cli.commands.interactive_utils.update_commands import handle_update_command
        from gtasks_cli.commands.interactive_utils.add_commands import handle_add_command
        from gtasks_cli.commands.interactive_utils.bulk_update_commands import handle_bulk_update_command

        class FilteredTaskState:
            def __init__(self, task_list):
                self.tasks = task_list
                self.task_number_to_id = {i: t.id for i, t in enumerate(task_list, 1)}
                self.task_id_to_number = {t.id: i for i, t in enumerate(task_list, 1)}

            def get_task_by_number(self, number: int):
                if 1 <= number <= len(self.tasks):
                    return self.tasks[number - 1]
                return None

        state = FilteredTaskState(tasks)

        history = None
        if HAS_PROMPT_TOOLKIT:
            history_file = os.path.expanduser("~/.gtasks_history")
            try:
                history = FileHistory(history_file)
            except Exception:
                history = InMemoryHistory()

        while True:
            click.echo("\nEnter command (view <num>, done <num>, delete <num>, update <num>, add, update-status <spec>, search <query>, back, quit):")

            if HAS_PROMPT_TOOLKIT:
                user_input = prompt(
                    "Command: ",
                    history=history,
                    auto_suggest=AutoSuggestFromHistory() if HAS_PROMPT_TOOLKIT else None
                ).strip()
            else:
                user_input = click.prompt("Command", type=str, default="", show_default=False).strip()

            if not user_input:
                continue

            parts = user_input.split()
            cmd = parts[0].lower()

            if cmd in ['quit', 'exit']:
                click.echo("Exiting space-filtered interactive mode.")
                break
            elif cmd == 'back':
                click.echo("Returning to space selection.")
                new_tasks = handle_spaces_command(task_manager, use_google_tasks)
                if not new_tasks:
                    break
                state = FilteredTaskState(new_tasks)
                continue
            elif cmd == 'view':
                if len(parts) < 2:
                    click.echo("Usage: view <number>")
                    continue
                try:
                    num = int(parts[1])
                    task = state.get_task_by_number(num)
                    if task:
                        view_task_details(task)
                    else:
                        click.echo(f"Invalid task number: {num}")
                except ValueError:
                    click.echo("Please enter a valid task number.")
            elif cmd == 'done':
                handle_done_command(state, task_manager, parts, use_google_tasks)
            elif cmd == 'delete':
                handle_delete_command(state, task_manager, parts, use_google_tasks)
            elif cmd == 'update':
                handle_update_command(state, task_manager, parts, use_google_tasks)
            elif cmd == 'add':
                handle_add_command(state, task_manager, parts, use_google_tasks)
            elif cmd == 'update-status':
                handle_bulk_update_command(state, task_manager, parts, use_google_tasks)
            elif cmd == 'search':
                if len(parts) < 2:
                    click.echo("Usage: search <query>")
                    continue
                from gtasks_cli.commands.interactive_utils.search import apply_search_filter
                query = " ".join(parts[1:])
                results = apply_search_filter(state.tasks, query)
                if results:
                    click.echo(f"\nSearch results for '{query}':")
                    display_tasks_grouped_by_list(results)
                    state = FilteredTaskState(results)
                else:
                    click.echo(f"No tasks found matching '{query}'.")
            else:
                click.echo(f"Unknown command '{cmd}'. Available: view, done, delete, update, add, update-status, search, back, quit")

    except Exception as e:
        logger.error(f"Error in _enter_space_filtered_interactive_mode: {e}")
        click.echo(f"An error occurred: {e}")
