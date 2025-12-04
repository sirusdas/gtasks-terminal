import click
from gtasks_cli.storage.config_manager import ConfigManager
from gtasks_cli.utils.logger import setup_logger

logger = setup_logger(__name__)

@click.group()
def config():
    """Manage configuration settings."""
    pass

@config.command(name='set')
@click.argument('key')
@click.argument('value')
@click.option('--account', '-a', help='Account name for multi-account support')
@click.pass_context
def set_config(ctx, key, value, account):
    """Set a configuration value."""
    # Determine the account to use
    if account:
        account_name = account
    else:
        account_name = ctx.obj.get('account_name')
        
    config_manager = ConfigManager(account_name=account_name)
    
    # Handle boolean values
    if str(value).lower() == 'true':
        value = True
    elif str(value).lower() == 'false':
        value = False
    elif str(value).isdigit():
        value = int(value)
        
    config_manager.set(key, value)
    click.echo(f"Set '{key}' to '{value}'")

@config.command(name='get')
@click.argument('key')
@click.option('--account', '-a', help='Account name for multi-account support')
@click.pass_context
def get_config(ctx, key, account):
    """Get a configuration value."""
    # Determine the account to use
    if account:
        account_name = account
    else:
        account_name = ctx.obj.get('account_name')
        
    config_manager = ConfigManager(account_name=account_name)
    value = config_manager.get(key)
    click.echo(f"{key}: {value}")
