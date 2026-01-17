"""
Remote database management commands for gtasks CLI.
Provides commands for adding, listing, removing, and syncing with remote databases.
"""
import click
from typing import Optional
from pathlib import Path
import sys

# Add gtasks_cli to path
gtasks_cli_path = Path(__file__).parent.parent.parent.parent
if str(gtasks_cli_path) not in sys.path:
    sys.path.insert(0, str(gtasks_cli_path))

from gtasks_cli.sync.remote_sync_manager import RemoteSyncManager, SyncResult
from gtasks_cli.utils.logger import setup_logger

logger = setup_logger(__name__)


@click.group(name='remote')
def remote_commands():
    """Manage remote database connections for synchronization."""
    pass


@remote_commands.command(name='add')
@click.argument('url', type=str, metavar='URL')
@click.argument('token', type=str, required=False, metavar='TOKEN')
@click.option('--name', '-n', type=str, default=None,
              help='Friendly name for the remote database')
@click.option('--account', '-a', type=str, default=None,
              help='Account name for multi-account support')
@click.option('--auto-sync', is_flag=True, default=False,
              help='Enable automatic periodic sync')
@click.option('--frequency', '-f', type=int, default=5,
              help='Sync frequency in minutes (default: 5)')
def add_remote(url: str, token: Optional[str], name: Optional[str], 
               account: Optional[str], auto_sync: bool, frequency: int):
    """Add a new remote Turso database for synchronization."""
    
    if not token:
        token = click.prompt('Enter authentication token', type=str, hide_input=True)
    
    try:
        manager = RemoteSyncManager(account_name=account)
        result = manager.add_remote_db(
            url=url,
            name=name,
            token=token,
            auto_sync=auto_sync,
            sync_frequency=frequency
        )
        
        if result.success:
            click.echo(click.style("✓ ", fg='green') + result.message)
            
            if result.details.get('task_count') is not None:
                click.echo(f"  Database contains {result.details['task_count']} tasks")
            
            if auto_sync:
                click.echo(f"  Auto-sync enabled (every {frequency} minutes)")
        else:
            click.echo(click.style("✗ ", fg='red') + result.message)
            
    except Exception as e:
        logger.error(f"Failed to add remote database: {e}")
        click.echo(click.style(f"✗ Error: {str(e)}", fg='red'), err=True)


@remote_commands.command(name='list')
@click.option('--account', '-a', type=str, default=None,
              help='Account name for multi-account support')
@click.option('--verbose', '-v', is_flag=True, default=False,
              help='Show detailed information including task counts')
def list_remotes(account: Optional[str], verbose: bool):
    """List all configured remote databases."""
    try:
        manager = RemoteSyncManager(account_name=account)
        remote_dbs = manager.list_remote_dbs()
        
        if not remote_dbs:
            click.echo("No remote databases configured.")
            click.echo("\nAdd one with: gtasks remote add <url> [token]")
            return
        
        click.echo(f"Configured remote databases ({len(remote_dbs)}):\n")
        
        for i, db in enumerate(remote_dbs, 1):
            status_emoji = "✓" if db.is_active else "○"
            status_text = "Active" if db.is_active else "Inactive"
            
            click.echo(f"{i}. {status_emoji} {db.name}")
            click.echo(f"   URL: {db.url}")
            click.echo(f"   Status: {status_text}")
            click.echo(f"   Created: {db.created_at}")
            
            if db.last_synced_at:
                click.echo(f"   Last synced: {db.last_synced_at}")
            else:
                click.echo("   Last synced: Never")
            
            if db.auto_sync:
                click.echo(f"   Auto-sync: Every {db.sync_frequency} minutes")
            
            if verbose:
                # Try to get task count
                try:
                    from gtasks_cli.storage.libsql_storage import LibSQLStorage
                    storage = LibSQLStorage(url=db.url)
                    count = storage.get_task_count()
                    storage.close()
                    click.echo(f"   Tasks: {count}")
                except Exception:
                    click.echo("   Tasks: Unable to connect")
            
            click.echo()
            
    except Exception as e:
        logger.error(f"Failed to list remote databases: {e}")
        click.echo(click.style(f"✗ Error: {str(e)}", fg='red'), err=True)


@remote_commands.command(name='status')
@click.option('--account', '-a', type=str, default=None,
              help='Account name for multi-account support')
def remote_status(account: Optional[str]):
    """Show current sync status and statistics."""
    try:
        manager = RemoteSyncManager(account_name=account)
        status = manager.get_status()
        
        click.echo("=== Sync Status ===\n")
        
        click.echo(f"Local database: {status['local_tasks']} tasks")
        click.echo(f"Remote databases: {status['active_remote_dbs']}/{status['total_remote_dbs']} active\n")
        
        for db in status['remote_databases']:
            emoji = "✓" if db['status'] == 'connected' else ("○" if db['status'] == 'inactive' else "✗")
            color = 'green' if db['status'] == 'connected' else ('yellow' if db['status'] == 'inactive' else 'red')
            
            click.secho(f"{emoji} {db['name']}", fg=color)
            click.echo(f"   Tasks: {db.get('task_count', 'N/A')}")
            
            if db.get('last_synced'):
                click.echo(f"   Last sync: {db['last_synced']}")
            else:
                click.echo("   Last sync: Never")
            
            if db.get('auto_sync'):
                click.echo("   Auto-sync: Enabled")
            
            if db.get('error'):
                click.secho(f"   Error: {db['error']}", fg='red')
            
            click.echo()
        
        click.echo(f"Conflict resolution: {status['conflict_strategy']}")
        
    except Exception as e:
        logger.error(f"Failed to get status: {e}")
        click.echo(click.style(f"✗ Error: {str(e)}", fg='red'), err=True)


@remote_commands.command(name='remove')
@click.argument('url', type=str, metavar='URL')
@click.option('--account', '-a', type=str, default=None,
              help='Account name for multi-account support')
@click.confirmation_option(
    prompt='Are you sure you want to remove this remote database?'
)
def remove_remote(url: str, account: Optional[str]):
    """Remove a remote database configuration."""
    try:
        manager = RemoteSyncManager(account_name=account)
        result = manager.remove_remote_db(url)
        
        if result.success:
            click.echo(click.style("✓ ", fg='green') + result.message)
        else:
            click.echo(click.style("✗ ", fg='red') + result.message)
            
    except Exception as e:
        logger.error(f"Failed to remove remote database: {e}")
        click.echo(click.style(f"✗ Error: {str(e)}", fg='red'), err=True)


@remote_commands.command(name='deactivate')
@click.argument('url', type=str, metavar='URL')
@click.option('--account', '-a', type=str, default=None,
              help='Account name for multi-account support')
def deactivate_remote(url: str, account: Optional[str]):
    """Deactivate a remote database (disable sync without removing)."""
    try:
        manager = RemoteSyncManager(account_name=account)
        result = manager.deactivate_remote_db(url)
        
        if result.success:
            click.echo(click.style("✓ ", fg='green') + result.message)
        else:
            click.echo(click.style("✗ ", fg='red') + result.message)
            
    except Exception as e:
        logger.error(f"Failed to deactivate remote database: {e}")
        click.echo(click.style(f"✗ Error: {str(e)}", fg='red'), err=True)


@remote_commands.command(name='activate')
@click.argument('url', type=str, metavar='URL')
@click.option('--account', '-a', type=str, default=None,
              help='Account name for multi-account support')
def activate_remote(url: str, account: Optional[str]):
    """Activate a previously deactivated remote database."""
    try:
        manager = RemoteSyncManager(account_name=account)
        result = manager.activate_remote_db(url)
        
        if result.success:
            click.echo(click.style("✓ ", fg='green') + result.message)
        else:
            click.echo(click.style("✗ ", fg='red') + result.message)
            
    except Exception as e:
        logger.error(f"Failed to activate remote database: {e}")
        click.echo(click.style(f"✗ Error: {str(e)}", fg='red'), err=True)


@remote_commands.command(name='sync')
@click.option('--account', '-a', type=str, default=None,
              help='Account name for multi-account support')
@click.option('--url', type=str, default=None,
              help='Specific remote DB URL to sync with (syncs all if not specified)')
@click.option('--push-only', is_flag=True, default=False,
              help='Only push local changes to remote (no pull)')
@click.option('--pull-only', is_flag=True, default=False,
              help='Only pull remote changes to local (no push)')
@click.option('--no-google', is_flag=True, default=False,
              help='Do not sync with Google Tasks')
@click.option('--force', '-f', is_flag=True, default=False,
              help='Force full sync (push all tasks, not just changes)')
@click.option('--preview', is_flag=True, default=False,
              help='Preview what would be synced without making changes')
@click.option('--verbose', '-v', is_flag=True, default=False,
              help='Show detailed sync progress')
@click.pass_context
def sync_remote(ctx, account: Optional[str], url: Optional[str], 
                push_only: bool, pull_only: bool, no_google: bool,
                force: bool, preview: bool, verbose: bool):
    """Sync with all configured remote databases and optionally Google Tasks."""
    try:
        # Use account from CLI context if not explicitly specified
        if not account:
            account = ctx.obj.get('account_name')
        
        # Respect google setting from CLI context, but allow --no-google override
        use_google = ctx.obj.get('use_google_tasks', True)
        if no_google:
            use_google = False
        
        manager = RemoteSyncManager(account_name=account)
        
        if preview:
            # Show preview
            preview_info = manager.preview_sync()
            
            click.echo("=== Sync Preview ===\n")
            click.echo(f"Local tasks: {preview_info['local_tasks']}")
            click.echo(f"Remote tasks: {preview_info['remote_tasks']}")
            click.echo(f"Unique tasks after merge: {preview_info['unique_tasks']}")
            click.echo(f"Potential conflicts: {preview_info['conflicts']}")
            click.echo(f"Duplicates detected: {preview_info['duplicates']}")
            click.echo()
            click.echo("Changes if synced:")
            click.echo(f"  - New tasks from remote: {preview_info['changes_if_synced']['new_local_tasks']}")
            click.echo(f"  - Tasks to push to remote: {preview_info['changes_if_synced']['new_remote_tasks']}")
            click.echo(f"  - Tasks to update: {preview_info['changes_if_synced']['updated_tasks']}")
            
            if not click.confirm('\nProceed with sync?'):
                click.echo("Sync cancelled.")
                return
        
        # Perform sync
        if url:
            # Sync with specific remote DB
            if push_only:
                result = manager.push_to_remote(url)
            elif pull_only:
                result = manager.pull_from_remote(url)
            else:
                result = manager.sync_with_remote(url, bidirectional=True)
        else:
            # Sync with all
            result = manager.sync_all(
                push_to_remote=not pull_only,
                sync_with_google=use_google,
                force_full=force
            )
        
        if result.success:
            click.echo(click.style("✓ ", fg='green') + result.message)
            
            if verbose and result.details:
                if result.details.get('local_tasks'):
                    click.echo(f"  Local tasks processed: {result.details['local_tasks']}")
                if result.details.get('merged_tasks'):
                    click.echo(f"  Tasks after merge: {result.details['merged_tasks']}")
                if result.details.get('push_results'):
                    pushes = result.details['push_results']
                    successful = sum(1 for r in pushes.values() if r.get('success'))
                    click.echo(f"  Remote updates: {successful}/{len(pushes)} successful")
        else:
            click.echo(click.style("✗ ", fg='red') + result.message)
            
    except Exception as e:
        logger.error(f"Sync failed: {e}")
        click.echo(click.style(f"✗ Error: {str(e)}", fg='red'), err=True)


@remote_commands.command(name='push')
@click.argument('url', type=str, required=False, metavar='URL')
@click.option('--account', '-a', type=str, default=None,
              help='Account name for multi-account support')
def push_to_remote(url: Optional[str], account: Optional[str]):
    """Push local changes to remote database(s)."""
    try:
        manager = RemoteSyncManager(account_name=account)
        result = manager.push_to_remote(url)
        
        if result.success:
            click.echo(click.style("✓ ", fg='green') + result.message)
        else:
            click.echo(click.style("✗ ", fg='red') + result.message)
            
    except Exception as e:
        logger.error(f"Push failed: {e}")
        click.echo(click.style(f"✗ Error: {str(e)}", fg='red'), err=True)


@remote_commands.command(name='pull')
@click.argument('url', type=str, required=False, metavar='URL')
@click.option('--account', '-a', type=str, default=None,
              help='Account name for multi-account support')
def pull_from_remote(url: Optional[str], account: Optional[str]):
    """Pull changes from remote database(s) to local."""
    try:
        manager = RemoteSyncManager(account_name=account)
        result = manager.pull_from_remote(url)
        
        if result.success:
            click.echo(click.style("✓ ", fg='green') + result.message)
        else:
            click.echo(click.style("✗ ", fg='red') + result.message)
            
    except Exception as e:
        logger.error(f"Pull failed: {e}")
        click.echo(click.style(f"✗ Error: {str(e)}", fg='red'), err=True)
