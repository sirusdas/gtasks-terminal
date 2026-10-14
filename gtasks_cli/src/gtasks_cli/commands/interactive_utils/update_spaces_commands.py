#!/usr/bin/env python3
"""
Interactive command to bulk update task spaces and sub-spaces.
"""

import click
import re
from collections import defaultdict
from typing import List, Dict, Any, Tuple
from gtasks_cli.models.task import Task
from gtasks_cli.utils.logger import setup_logger
from gtasks_cli.utils.space_extractor import (
    extract_spaces_from_text,
    split_notes_and_metadata,
    combine_notes_and_metadata,
)

logger = setup_logger(__name__)


def _parse_space_spec(spec: str) -> Tuple[str, List[str]]:
    """
    Parse a space spec string into (space_name, [subspaces]).
    e.g. 'work:frontend,backend' -> ('work', ['frontend', 'backend'])
    or 'work' -> ('work', [])
    """
    spec = spec.strip()
    if ':' in spec:
        spa, raw_subs = spec.split(':', 1)
        spa = spa.strip()
        raw_subs = raw_subs.strip().strip('()')
        subs = [s.strip().replace('sub::', '') for s in raw_subs.split(',') if s.strip()]
        return (spa, subs)
    return (spec, [])


def handle_update_spaces_command(task_state, task_manager, command_parts, use_google_tasks=False):
    """
    Handle the update-spaces command in interactive mode.
    Syntax:
      update-spaces ADD[1,2|work:frontend,backend],DEL[3|personal]
      update-spaces ADD[1|work]
      update-spaces DEL[2|work:sub]  (removes sub-space 'sub' from 'work')
      update-spaces DEL[2|work]      (removes space 'work' entirely)
      update-spaces ALL[ADD:work]
      update-spaces ALL[DEL:personal]
    """
    if len(command_parts) < 2:
        click.echo("Usage: update-spaces ADD[ids|space:sub1,sub2],DEL[ids|space] or update-spaces ALL[ADD:space]")
        return

    full_args = " ".join(command_parts[1:])

    # Regex for ALL operations: ALL\[(ADD|DEL):(.*?)\]
    all_ops = re.findall(r'ALL\[(ADD|DEL):(.*?)\]', full_args, re.IGNORECASE)

    # Regex for regular operations: (ADD|DEL)\[(.*?)\]
    regular_ops = re.findall(r'(?<!ALL\[)(ADD|DEL)\[(.*?)\]', full_args, re.IGNORECASE)

    if not all_ops and not regular_ops:
        click.echo("Invalid format. Use ADD[ids|space:subs], DEL[ids|space], ALL[ADD:space], or ALL[DEL:space].")
        return

    tasks_to_update: Dict[str, Task] = {}
    updates = []  # List of (task_id, op_type, space_spec)

    # Process ALL operations
    for op_type, specs_part in all_ops:
        op_type = op_type.upper()
        specs = [s.strip() for s in specs_part.split(';') if s.strip()] or [specs_part.strip()]
        for task in task_state.tasks:
            tasks_to_update[task.id] = task
            for spec in specs:
                updates.append((task.id, op_type, spec))

    # Process regular operations
    for op_type, content in regular_ops:
        op_type = op_type.upper()
        content = content.strip()
        if '|' in content:
            ids_part, specs_part = content.split('|', 1)
            specs = [s.strip() for s in specs_part.split(';') if s.strip()] or [specs_part.strip()]
            num_strs = [n.strip() for n in ids_part.split(',') if n.strip()]

            for num_str in num_strs:
                try:
                    num = int(num_str)
                    task = task_state.get_task_by_number(num)
                    if task:
                        tasks_to_update[task.id] = task
                        for spec in specs:
                            updates.append((task.id, op_type, spec))
                    else:
                        click.echo(f"Warning: Task #{num} not found.")
                except ValueError:
                    click.echo(f"Warning: Invalid task number '{num_str}'.")
        else:
            click.echo(f"Invalid operation format '{content}'. Expected ids|space_spec")

    if not updates:
        click.echo("No valid operations to execute.")
        return

    # Group updates by task
    task_ops = defaultdict(list)
    for tid, op, spec in updates:
        task_ops[tid].append((op, spec))

    # Track undo data
    undo_data = {}  # task_id -> original notes
    updated_count = 0

    for tid, ops in task_ops.items():
        task = tasks_to_update[tid]
        current_raw = task.notes or task.description or ""
        clean_notes, tags, current_spaces = split_notes_and_metadata(current_raw)
        original_notes = current_raw
        undo_data[tid] = original_notes

        # Deep copy spaces map
        new_spaces = {k: list(v) for k, v in current_spaces.items()}

        changes = []
        for op, spec in ops:
            spa, subs = _parse_space_spec(spec)
            if not spa:
                continue

            if op == 'ADD':
                if spa not in new_spaces:
                    new_spaces[spa] = []
                for s in subs:
                    if s not in new_spaces[spa]:
                        new_spaces[spa].append(s)
                changes.append(f"Added space '{spa}'" + (f" › {', '.join(subs)}" if subs else ""))

            elif op == 'DEL':
                if spa in new_spaces:
                    if subs:
                        # Remove specific sub-spaces
                        for s in subs:
                            if s in new_spaces[spa]:
                                new_spaces[spa].remove(s)
                        changes.append(f"Removed sub-space(s) from '{spa}': {', '.join(subs)}")
                    else:
                        # Remove entire space
                        del new_spaces[spa]
                        changes.append(f"Removed space '{spa}'")

        # Recombine notes with metadata
        recombined = combine_notes_and_metadata(clean_notes, tags, new_spaces)
        try:
            task_manager.update_task(task.id, notes=recombined, description=recombined, spaces=new_spaces)
            task.notes = recombined
            task.description = recombined
            task.spaces = new_spaces
            updated_count += 1
            task_num = task_state.get_number_by_task_id(task.id) if hasattr(task_state, 'get_number_by_task_id') else task.id
            click.echo(f"  Task #{task_num} ({task.title[:30]}): {', '.join(changes)}")
        except Exception as e:
            logger.error(f"Failed to update spaces for task {task.id}: {e}")
            click.echo(f"  Error updating task {task.id}: {e}")

    # Register undo
    if undo_data:
        from gtasks_cli.commands.interactive_utils.undo_manager import undo_manager

        def undo_space_updates():
            undone = 0
            for t_id, orig_n in undo_data.items():
                try:
                    orig_spaces = extract_spaces_from_text(orig_n)
                    task_manager.update_task(t_id, notes=orig_n, description=orig_n, spaces=orig_spaces)
                    for t in task_state.tasks:
                        if t.id == t_id:
                            t.notes = orig_n
                            t.description = orig_n
                            t.spaces = orig_spaces
                            break
                    undone += 1
                except Exception as ex:
                    logger.error(f"Undo failed for {t_id}: {ex}")
            click.echo(f"Undid space updates for {undone} tasks.")
            return undone > 0

        undo_manager.push_operation(
            description=f"Update spaces for {len(undo_data)} task(s)",
            undo_func=undo_space_updates
        )

    click.echo(f"\nSuccessfully updated spaces for {updated_count} task(s).")
