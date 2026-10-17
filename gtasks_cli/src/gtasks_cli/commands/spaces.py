#!/usr/bin/env python3
"""
Spaces and sub-spaces management commands for Google Tasks CLI.
"""

import click
from typing import Dict, List, Optional
from collections import defaultdict
from gtasks_cli.utils.logger import setup_logger
from gtasks_cli.core.task_manager import TaskManager
from gtasks_cli.utils.space_extractor import (
    extract_spaces_from_text,
    split_notes_and_metadata,
    combine_notes_and_metadata,
)

logger = setup_logger(__name__)


@click.group()
def spaces():
    """Manage spaces and sub-spaces."""
    pass


@spaces.command(name='list')
@click.option('--account', '-a', help='Account name for multi-account support')
@click.pass_context
def list_spaces(ctx, account):
    """List all spaces and sub-spaces with task counts."""
    use_google_tasks = ctx.obj.get('use_google_tasks', False)
    storage_backend = ctx.obj.get('storage_backend', 'sqlite')
    account_name = account or ctx.obj.get('account_name')

    task_manager = TaskManager(
        use_google_tasks=use_google_tasks,
        storage_backend=storage_backend,
        account_name=account_name,
    )

    tasks = task_manager.list_tasks()
    if not tasks:
        click.echo("No tasks found.")
        return

    space_counts = defaultdict(int)
    subspace_counts = defaultdict(lambda: defaultdict(int))

    for task in tasks:
        raw_notes = getattr(task, 'notes', None) or getattr(task, 'description', None) or ''
        sp = getattr(task, 'spaces', None) or extract_spaces_from_text(raw_notes)
        for s_name, s_subs in sp.items():
            s_clean = s_name.strip()
            if not s_clean:
                continue
            space_counts[s_clean] += 1
            for sub in s_subs:
                sub_clean = str(sub).strip().replace('sub::', '')
                if sub_clean:
                    subspace_counts[s_clean][sub_clean] += 1

    if not space_counts:
        click.echo("🌌 No spaces found in any tasks.")
        return

    click.echo(f"\n🌌 Spaces ({len(space_counts)}):")
    click.echo("=" * 60)
    for idx, s_name in enumerate(sorted(space_counts.keys()), 1):
        count = space_counts[s_name]
        subs = subspace_counts[s_name]
        click.echo(f"  {idx:2d}. {s_name} ({count} task{'s' if count != 1 else ''})")
        if subs:
            for sub_name, sub_count in sorted(subs.items()):
                click.echo(f"      └─ {sub_name} ({sub_count} task{'s' if sub_count != 1 else ''})")
    click.echo("=" * 60)


@spaces.command(name='remove')
@click.argument('space_name')
@click.option('--subspace', '-s', help='Specific sub-space to remove (leaves parent space intact)')
@click.option('--account', '-a', help='Account name for multi-account support')
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation prompt')
@click.pass_context
def remove_space(ctx, space_name, subspace, account, yes):
    """Remove a space or sub-space across all tasks."""
    use_google_tasks = ctx.obj.get('use_google_tasks', False)
    storage_backend = ctx.obj.get('storage_backend', 'sqlite')
    account_name = account or ctx.obj.get('account_name')

    target_space = space_name.strip()
    target_subspace = subspace.strip() if subspace else None

    task_manager = TaskManager(
        use_google_tasks=use_google_tasks,
        storage_backend=storage_backend,
        account_name=account_name,
    )

    tasks = task_manager.list_tasks()
    matching_tasks = []

    for task in tasks:
        raw_notes = getattr(task, 'notes', None) or getattr(task, 'description', None) or ''
        clean_notes, tags, sp = split_notes_and_metadata(raw_notes)

        matched_key = None
        for k in sp.keys():
            if k.lower() == target_space.lower():
                matched_key = k
                break

        if matched_key:
            if target_subspace:
                subs = [str(s).lower().replace('sub::', '') for s in sp.get(matched_key, [])]
                if target_subspace.lower() in subs:
                    matching_tasks.append((task, clean_notes, tags, sp, matched_key))
            else:
                matching_tasks.append((task, clean_notes, tags, sp, matched_key))

    target_desc = f"sub-space '{target_space} › {target_subspace}'" if target_subspace else f"space '{target_space}'"

    if not matching_tasks:
        click.echo(f"No tasks found containing {target_desc}.")
        return

    click.echo(f"Found {len(matching_tasks)} task(s) containing {target_desc}:")
    for t, _, _, _, _ in matching_tasks[:10]:
        click.echo(f"  • {t.title}")
    if len(matching_tasks) > 10:
        click.echo(f"  ... and {len(matching_tasks) - 10} more.")

    if not yes:
        confirmed = click.confirm(f"\nAre you sure you want to remove {target_desc} from these {len(matching_tasks)} task(s)?")
        if not confirmed:
            click.echo("Operation cancelled.")
            return

    updated_count = 0
    for task, clean_notes, tags, sp, matched_key in matching_tasks:
        new_spaces = {k: list(v) for k, v in sp.items()}
        if target_subspace:
            filtered_subs = [s for s in new_spaces.get(matched_key, []) if str(s).lower().replace('sub::', '') != target_subspace.lower()]
            new_spaces[matched_key] = filtered_subs
        else:
            if matched_key in new_spaces:
                del new_spaces[matched_key]

        new_notes = combine_notes_and_metadata(clean_notes, tags, new_spaces)
        try:
            task_manager.update_task(task.id, notes=new_notes, description=new_notes)
            updated_count += 1
        except Exception as e:
            logger.error(f"Error updating task {task.id}: {e}")
            click.echo(f"❌ Failed to update task '{task.title}': {e}")

    click.echo(f"✅ Successfully removed {target_desc} from {updated_count} task(s).")
