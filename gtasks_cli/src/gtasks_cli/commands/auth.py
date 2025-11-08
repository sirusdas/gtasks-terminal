#!/usr/bin/env python3
"""
Auth command for Google Tasks CLI
"""

import click
from gtasks_cli.utils.logger import setup_logger

# Set up logger
logger = setup_logger(__name__)


@click.command()
def auth():
    """Authenticate with Google Tasks API"""
    logger.info("Starting Google authentication flow")
    
    # Import here to avoid issues with module loading
    from gtasks_cli.integrations.google_auth import GoogleAuthManager
    
    # Create auth manager
    auth_manager = GoogleAuthManager()
    
    if auth_manager.authenticate():
        click.echo("✅ Successfully authenticated with Google Tasks API!")
    else:
        click.echo("❌ Failed to authenticate with Google Tasks API!")
        exit(1)