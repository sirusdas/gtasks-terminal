#!/usr/bin/env python3
"""
Auth command for Google Tasks CLI
"""

import click
import os
from gtasks_cli.utils.logger import setup_logger

# Set up logger
logger = setup_logger(__name__)


@click.command()
@click.option('--account', '-a', help='Account name for multi-account support')
@click.option('--credentials', '-c', help='Path to credentials file')
@click.pass_context
def auth(ctx, account, credentials):
    """Authenticate with Google Tasks API"""
    logger.info("Starting Google authentication flow")
    
    # Import here to avoid issues with module loading
    from gtasks_cli.integrations.google_auth import GoogleAuthManager
    from gtasks_cli.storage.config_manager import ConfigManager
    
    # Create auth manager with account-specific settings
    auth_manager = GoogleAuthManager(credentials_file=credentials, account_name=account)
    
    if auth_manager.authenticate():
        # Register the account in the configuration if it's a named account
        if account:
            config = ConfigManager()
            account_config = config.get_account_config(account)
            # Update the account configuration
            account_config['authenticated'] = True
            config.set_account_config(account, account_config)
            
            # If this is the first account, make it the default
            if not config.get('default_account'):
                config.set('default_account', account)
            
            click.echo(f"✅ Successfully authenticated with Google Tasks API for account '{account}'!")
        else:
            click.echo("✅ Successfully authenticated with Google Tasks API!")
    else:
        if account:
            click.echo(f"❌ Failed to authenticate with Google Tasks API for account '{account}'!")
        else:
            click.echo("❌ Failed to authenticate with Google Tasks API!")
        exit(1)