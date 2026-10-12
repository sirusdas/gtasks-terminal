"""
CLI Debug Command - Real-time diagnostics, system health check, and log viewer.
"""
import click
import platform
import sys
import os
import sqlite3
from pathlib import Path
from gtasks_cli.utils.logger import (
    setup_logger,
    get_log_file_path,
    get_recent_logs,
    clear_logs,
    set_global_log_level
)
from gtasks_cli.storage.config_manager import ConfigManager

logger = setup_logger(__name__)


@click.group()
def debug():
    """Diagnostic, inspection, and log debugging tools."""
    pass


@click.command(name='doctor')
@click.option('--account', '-a', help='Account name to inspect')
@click.pass_context
def debug_doctor(ctx, account):
    """Run comprehensive system health check."""
    account_name = account or (ctx.obj.get('account_name') if ctx.obj else None)
    click.echo("\n🩺 Running GTasks System Doctor...")
    click.echo("=" * 60)

    # 1. Environment & System
    click.echo(f"• OS / Platform: {platform.system()} ({platform.platform()})")
    click.echo(f"• Python: {sys.version.split()[0]} ({sys.executable})")

    # 2. Config Check
    try:
        cm = ConfigManager(account_name=account_name)
        click.echo(click.style(f"✔ Configuration File: {cm.config_path} (Valid YAML)", fg='green'))
    except Exception as e:
        click.echo(click.style(f"✘ Configuration Error: {e}", fg='red'))

    # 3. Database Integrity Check
    db_path = Path.home() / '.gtasks' / (f"{account_name}/tasks.db" if account_name and account_name.lower() not in ('default', 'personal') else "tasks.db")
    if db_path.exists():
        size_kb = db_path.stat().st_size / 1024
        click.echo(click.style(f"✔ SQLite Database: {db_path} ({size_kb:.1f} KB)", fg='green'))
        try:
            conn = sqlite3.connect(str(db_path))
            cur = conn.cursor()
            cur.execute("PRAGMA quick_check;")
            res = cur.fetchone()
            if res and res[0] == 'ok':
                click.echo(click.style("  ✔ SQLite PRAGMA quick_check: PASSED", fg='green'))
            else:
                click.echo(click.style(f"  ✘ Integrity issue: {res}", fg='yellow'))

            cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [r[0] for r in cur.fetchall()]
            for tbl in tables:
                cur.execute(f"SELECT COUNT(*) FROM {tbl};")
                count = cur.fetchone()[0]
                click.echo(f"  - Table '{tbl}': {count} rows")
            conn.close()
        except Exception as e:
            click.echo(click.style(f"  ✘ DB Connection error: {e}", fg='red'))
    else:
        click.echo(click.style(f"✘ Database file not found at {db_path}", fg='yellow'))

    # 4. Log File Check
    log_file = get_log_file_path()
    if log_file.exists():
        size_kb = log_file.stat().st_size / 1024
        click.echo(click.style(f"✔ Log File: {log_file} ({size_kb:.1f} KB)", fg='green'))
    else:
        click.echo(click.style(f"• Log File: {log_file} (Not yet created)", fg='yellow'))

    click.echo("=" * 60)
    click.echo(click.style("Diagnostics completed.\n", fg='green', bold=True))


@click.command(name='logs')
@click.option('--lines', '-n', default=50, type=int, help='Number of log lines to show')
@click.option('--level', '-l', type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR'], case_sensitive=False), help='Filter by log level')
@click.option('--search', '-s', help='Search text in logs')
def debug_logs(lines, level, search):
    """View recent application logs."""
    log_lines = get_recent_logs(lines=lines, level=level, search=search)
    if not log_lines:
        click.echo("✨ No log entries found matching criteria.")
        return

    click.echo(f"\n📜 Recent Logs ({len(log_lines)} lines):")
    click.echo("=" * 70)
    for line in log_lines:
        if ' - ERROR - ' in line:
            click.echo(click.style(line, fg='red'))
        elif ' - WARNING - ' in line:
            click.echo(click.style(line, fg='yellow'))
        elif ' - DEBUG - ' in line:
            click.echo(click.style(line, fg='cyan'))
        else:
            click.echo(click.style(line, fg='white'))
    click.echo("=" * 70 + "\n")


@click.command(name='clear-logs')
@click.confirmation_option(prompt='Are you sure you want to clear all log files?')
def debug_clear_logs():
    """Clear and truncate application logs."""
    if clear_logs():
        click.echo(click.style("✔ Application logs cleared successfully.", fg='green'))
    else:
        click.echo(click.style("✘ Failed to clear logs.", fg='red'))


@click.command(name='set-level')
@click.argument('level', type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR'], case_sensitive=False))
def debug_set_level(level):
    """Set default logging level."""
    active = set_global_log_level(level)
    click.echo(click.style(f"✔ Global log level set to {active}", fg='green'))


# Register commands to debug group
debug.add_command(debug_doctor)
debug.add_command(debug_logs)
debug.add_command(debug_clear_logs)
debug.add_command(debug_set_level)
