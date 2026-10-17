#!/usr/bin/env python3
"""
Tags management commands for Google Tasks CLI.
"""

import click
from typing import Dict, List, Optional
from collections import defaultdict
from gtasks_cli.utils.logger import setup_logger
from gtasks_cli.core.task_manager import TaskManager
from gtasks_cli.utils.tag_extractor import extract_tags_from_text, extract_tags_from_task
from gtasks_cli.utils.space_extractor import (
    split_notes_and_metadata,
    combine_notes_and_metadata,
)

logger = setup_logger(__name__)


@click.group()
def tags():
    """Manage task tags."""
    pass


@tags.command(name='list')
@click.option('--account', '-a', help='Account name for multi-account support')
@click.pass_context
def list_tags(ctx, account):
    """List all tags with task counts."""
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

    tag_counts = defaultdict(int)

    for task in tasks:
        t_tags = extract_tags_from_task(task)
        for tag in t_tags:
            t_clean = str(tag).strip().lower().lstrip('#[')
            if t_clean:
                tag_counts[t_clean] += 1

    if not tag_counts:
        click.echo("🏷️  No tags found in any tasks.")
        return

    click.echo(f"\n🏷️  Tags ({len(tag_counts)}):")
    click.echo("=" * 60)
    for idx, t_name in enumerate(sorted(tag_counts.keys()), 1):
        count = tag_counts[t_name]
        click.echo(f"  {idx:2d}. #{t_name:<25} ({count} task{'s' if count != 1 else ''})")
    click.echo("=" * 60)


@tags.command(name='remove')
@click.argument('tag_name')
@click.option('--account', '-a', help='Account name for multi-account support')
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation prompt')
@click.pass_context
def remove_tag(ctx, tag_name, account, yes):
    """Remove a tag across all tasks."""
    use_google_tasks = ctx.obj.get('use_google_tasks', False)
    storage_backend = ctx.obj.get('storage_backend', 'sqlite')
    account_name = account or ctx.obj.get('account_name')

    target_tag = tag_name.strip().lower().lstrip('#[')

    task_manager = TaskManager(
        use_google_tasks=use_google_tasks,
        storage_backend=storage_backend,
        account_name=account_name,
    )

    tasks = task_manager.list_tasks()
    matching_tasks = []

    for task in tasks:
        raw_notes = getattr(task, 'notes', None) or getattr(task, 'description', None) or ''
        clean_notes, task_tags, sp = split_notes_and_metadata(raw_notes)
        all_task_tags = extract_tags_from_task(task)

        # Check matching tag
        if any(t.lower() == target_tag for t in task_tags) or any(t.lower() == target_tag for t in all_task_tags):
            matching_tasks.append((task, clean_notes, task_tags, sp))

    if not matching_tasks:
        click.echo(f"No tasks found containing tag '#{target_tag}'.")
        return

    click.echo(f"Found {len(matching_tasks)} task(s) containing tag '#{target_tag}':")
    for t, _, _, _ in matching_tasks[:10]:
        click.echo(f"  • {t.title}")
    if len(matching_tasks) > 10:
        click.echo(f"  ... and {len(matching_tasks) - 10} more.")

    if not yes:
        confirmed = click.confirm(f"\nAre you sure you want to remove tag '#{target_tag}' from these {len(matching_tasks)} task(s)?")
        if not confirmed:
            click.echo("Operation cancelled.")
            return

    updated_count = 0
    for task, clean_notes, task_tags, sp in matching_tasks:
        new_tags = [t for t in task_tags if t.lower() != target_tag]
        new_notes = combine_notes_and_metadata(clean_notes, new_tags, sp)
        try:
            task_manager.update_task(task.id, notes=new_notes, description=new_notes)
            updated_count += 1
        except Exception as e:
            logger.error(f"Error updating task {task.id}: {e}")
            click.echo(f"❌ Failed to update task '{task.title}': {e}")

    click.echo(f"✅ Successfully removed tag '#{target_tag}' from {updated_count} task(s).")
