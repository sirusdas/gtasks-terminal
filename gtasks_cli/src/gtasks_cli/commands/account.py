#!/usr/bin/env python3
"""
Account management commands for Google Tasks CLI
"""

import click
import os
from pathlib import Path
from gtasks_cli.utils.logger import setup_logger

logger = setup_logger(__name__)


@click.group()
def account():
    """Manage Google Tasks accounts"""
    pass


@account.command()
@click.argument('account_name')
@click.option('--global', 'global_setting', is_flag=True, 
              help='Set as global default account (stored in config)')
def use(account_name, global_setting):
    """Set the default account for the current session or globally"""
    if global_setting:
        # Store in config for global default
        from gtasks_cli.storage.config_manager import ConfigManager
        config = ConfigManager.get_global_config()
        config.set('default_account', account_name)
        click.echo(f"✅ Global default account set to '{account_name}'")
    else:
        # Set for current session only using environment variable
        os.environ['GTASKS_DEFAULT_ACCOUNT'] = account_name
        click.echo(f"✅ Default account for current session set to '{account_name}'")


@account.command()
def list():
    """List all configured accounts"""
    from gtasks_cli.storage.config_manager import ConfigManager
    
    # Get accounts from configuration
    config = ConfigManager()
    configured_accounts = config.get('accounts', {})
    
    # Get accounts from directory structure
    gtasks_dir = Path.home() / '.gtasks'
    if gtasks_dir.exists():
        account_dirs = [d.name for d in gtasks_dir.iterdir() if d.is_dir() and d.name != 'default']
        if account_dirs:
            click.echo("Available accounts:")
            # Use global config to get default account
            global_config = ConfigManager.get_global_config()
            default_account = global_config.get('default_account')
            for account in account_dirs:
                if account == default_account:
                    click.echo(f"  * {account} (global default)")
                else:
                    click.echo(f"  * {account}")
            return
    
    if configured_accounts:
        click.echo("Configured accounts:")
        # Use global config to get default account
        global_config = ConfigManager.get_global_config()
        default_account = global_config.get('default_account')
        for account in configured_accounts:
            if account == default_account:
                click.echo(f"  * {account} (global default)")
            else:
                click.echo(f"  * {account}")
    else:
        click.echo("No accounts configured yet.")


@account.command()
def current():
    """Show the currently active account"""
    # Check session default first
    session_default = os.environ.get('GTASKS_DEFAULT_ACCOUNT')
    if session_default:
        click.echo(f"Current session account: {session_default}")
        return
    
    # Check global default
    from gtasks_cli.storage.config_manager import ConfigManager
    config = ConfigManager.get_global_config()
    global_default = config.get('default_account')
    if global_default:
        click.echo(f"Global default account: {global_default}")
        return
    
    click.echo("No default account set")