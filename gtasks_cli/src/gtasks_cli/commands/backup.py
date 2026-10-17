#!/usr/bin/env python3
"""
Backup and restore command group for GTasks CLI.
"""

import click
import shutil
import sqlite3
import json
import time
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.table import Table
from gtasks_cli.utils.logger import setup_logger

logger = setup_logger(__name__)
console = Console()


def get_gtasks_dir(account: str = None) -> Path:
    base = Path.home() / '.gtasks'
    if account and account.lower() not in ('default', 'personal'):
        return base / account
    return base


def get_backups_dir() -> Path:
    bdir = Path.home() / '.gtasks' / 'backups'
    bdir.mkdir(parents=True, exist_ok=True)
    return bdir


@click.group(name='backup')
def backup_group():
    """Backup and recovery management for GTasks database and tasks."""
    pass


@backup_group.command(name='create')
@click.option('--note', '-n', default='Manual Snapshot', help='Optional label/note for this backup')
@click.option('--account', '-a', help='Account name (default: current account)')
def create_backup(note, account):
    """Create a new timestamped backup of tasks database and JSON snapshot."""
    gtasks_dir = get_gtasks_dir(account)
    db_path = gtasks_dir / 'tasks.db'

    if not db_path.exists():
        console.print(f"[red]❌ Database not found at: {db_path}[/red]")
        return

    backups_dir = get_backups_dir()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    db_backup_path = backups_dir / f"tasks_backup_{timestamp}.db"
    json_backup_path = backups_dir / f"tasks_backup_{timestamp}.json"

    # Copy SQLite Database
    shutil.copy2(db_path, db_backup_path)

    # Export JSON snapshot for portable recovery
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    tasks_data = []
    try:
        cursor.execute("SELECT * FROM tasks")
        for row in cursor.fetchall():
            tasks_data.append(dict(row))
    except Exception as e:
        logger.warning(f"Failed to export tasks to JSON: {e}")

    lists_data = []
    try:
        cursor.execute("SELECT * FROM task_lists")
        for row in cursor.fetchall():
            lists_data.append(dict(row))
    except Exception:
        pass
    conn.close()

    meta = {
        "version": 1,
        "created_at": datetime.now().isoformat(),
        "note": note,
        "account": account or "default",
        "task_count": len(tasks_data),
        "list_count": len(lists_data),
        "lists": lists_data,
        "tasks": tasks_data,
    }

    with open(json_backup_path, 'w', encoding='utf-8') as f:
        json.dump(meta, f, indent=2, default=str)

    size_kb = db_backup_path.stat().st_size / 1024

    table = Table(title="✨ Backup Created Successfully", style="green")
    table.add_column("Property", style="bold cyan")
    table.add_column("Value", style="white")

    table.add_row("Database Backup", db_backup_path.name)
    table.add_row("JSON Export", json_backup_path.name)
    table.add_row("Directory", str(backups_dir))
    table.add_row("Tasks Saved", str(len(tasks_data)))
    table.add_row("Task Lists Saved", str(len(lists_data)))
    table.add_row("Database Size", f"{size_kb:.1f} KB")
    table.add_row("Note", note)

    console.print(table)


@backup_group.command(name='list')
def list_backups():
    """List all available backup snapshots."""
    backups_dir = get_backups_dir()
    db_files = sorted(backups_dir.glob("tasks_backup_*.db"), key=lambda p: p.stat().st_mtime, reverse=True)

    if not db_files:
        console.print("[yellow]No backups found in ~/.gtasks/backups[/yellow]")
        return

    table = Table(title="📁 Available GTasks Backups", style="blue")
    table.add_column("Backup Name", style="bold cyan")
    table.add_column("Created", style="white")
    table.add_column("Size", style="green")
    table.add_column("Tasks", style="magenta")

    for f in db_files:
        created = datetime.fromtimestamp(f.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        size_kb = f.stat().st_size / 1024

        # Count tasks inside sqlite file
        task_count = "?"
        try:
            conn = sqlite3.connect(str(f))
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM tasks")
            task_count = str(c.fetchone()[0])
            conn.close()
        except Exception:
            pass

        table.add_row(f.name, created, f"{size_kb:.1f} KB", task_count)

    console.print(table)


@backup_group.command(name='restore')
@click.argument('backup_target')
@click.option('--yes', '-y', is_flag=True, help='Confirm restore without interactive prompt')
@click.option('--account', '-a', help='Account name (default: current account)')
def restore_backup(backup_target, yes, account):
    """Restore tasks database from a backup file or backup filename."""
    backups_dir = get_backups_dir()
    target_path = Path(backup_target)

    if not target_path.exists():
        # Check if user passed just the filename in ~/.gtasks/backups/
        candidate = backups_dir / backup_target
        if candidate.exists():
            target_path = candidate
        else:
            console.print(f"[red]❌ Backup file not found: {backup_target}[/red]")
            return

    gtasks_dir = get_gtasks_dir(account)
    db_path = gtasks_dir / 'tasks.db'

    if not yes:
        if not click.confirm(f"⚠️  Are you sure you want to restore from '{target_path.name}'?\n"
                             f"A safety snapshot of your current database will be saved first."):
            console.print("[yellow]Restore cancelled.[/yellow]")
            return

    # Safety snapshot
    if db_path.exists():
        safety_path = backups_dir / f"tasks_backup_pre_restore_{int(time.time())}.db"
        shutil.copy2(db_path, safety_path)
        console.print(f"[dim]Saved safety snapshot to: {safety_path.name}[/dim]")

    if target_path.suffix == '.db':
        shutil.copy2(target_path, db_path)
        # Verify integrity
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()
        c.execute("PRAGMA integrity_check")
        status = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM tasks")
        count = c.fetchone()[0]
        conn.close()

        if status == 'ok':
            console.print(f"[bold green]✅ Database successfully restored from {target_path.name} ({count} tasks)![/bold green]")
        else:
            console.print(f"[bold red]❌ Integrity check failed: {status}[/bold red]")
    elif target_path.suffix == '.json':
        with open(target_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        tasks = data.get('tasks', [])
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()
        c.execute("DELETE FROM tasks")
        for t in tasks:
            cols = list(t.keys())
            placeholders = ','.join(['?'] * len(cols))
            c.execute(f"INSERT OR REPLACE INTO tasks ({','.join(cols)}) VALUES ({placeholders})", list(t.values()))
        conn.commit()
        conn.close()
        console.print(f"[bold green]✅ Successfully imported {len(tasks)} tasks from {target_path.name}![/bold green]")
