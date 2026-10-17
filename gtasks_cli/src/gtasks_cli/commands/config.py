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


@config.command(name='remove-space')
@click.argument('space_name')
@click.option('--subspace', '-s', help='Specific sub-space to remove')
@click.option('--account', '-a', help='Account name for multi-account support')
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation prompt')
@click.pass_context
def remove_space_config(ctx, space_name, subspace, account, yes):
    """Remove a space or sub-space from tasks (setting/configuration)."""
    from gtasks_cli.commands.spaces import remove_space
    ctx.invoke(remove_space, space_name=space_name, subspace=subspace, account=account, yes=yes)


@config.command(name='remove-tag')
@click.argument('tag_name')
@click.option('--account', '-a', help='Account name for multi-account support')
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation prompt')
@click.pass_context
def remove_tag_config(ctx, tag_name, account, yes):
    """Remove a tag from tasks (setting/configuration)."""
    from gtasks_cli.commands.tags import remove_tag
    ctx.invoke(remove_tag, tag_name=tag_name, account=account, yes=yes)
