import click
from gtasks_cli.utils.logger import setup_logger
from gtasks_cli.core.task_manager import TaskManager
from gtasks_cli.ai.client import AIClient

logger = setup_logger(__name__)

@click.group()
def ai():
    """AI capabilities for Google Tasks."""
    pass

@ai.command()
@click.argument('query')
@click.pass_context
def ask(ctx, query):
    """Execute a natural language command."""
    # Get context values
    use_google_tasks = ctx.obj.get('use_google_tasks', False)
    storage_backend = ctx.obj.get('storage_backend', 'json')
    account_name = ctx.obj.get('account_name')
    
    # Initialize TaskManager
    task_manager = TaskManager(
        use_google_tasks=use_google_tasks,
        storage_backend=storage_backend,
        account_name=account_name
    )
    
    # Initialize AI Client
    client = AIClient(task_manager, account_name)
    
    click.echo("Thinking...")
    result = client.ask(query)
    click.echo(result)

@ai.command()
@click.option('--key', help='Config key (e.g., api_key, model, provider)')
@click.option('--value', help='Config value')
@click.pass_context
def config(ctx, key, value):
    """Configure AI settings."""
    account_name = ctx.obj.get('account_name')
    
    # We don't need a real TaskManager for config, but AIClient expects one.
    # We can pass a dummy or just use ConfigManager directly.
    # For simplicity, let's just use ConfigManager directly here.
    from gtasks_cli.storage.config_manager import ConfigManager
    cm = ConfigManager(account_name=account_name)
    
    if key and value:
        cm.set(f'ai.{key}', value)
        click.echo(f"Updated ai.{key} to {value}")
    else:
        # List current config
        ai_config = cm.get('ai', {})
        click.echo("Current AI Configuration:")
        for k, v in ai_config.items():
            # Mask API key
            if 'key' in k and v:
                v = '****' + v[-4:]
            click.echo(f"  {k}: {v}")
