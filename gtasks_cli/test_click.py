import click

@click.group()
@click.option('--verbose', '-v', count=True, help='Verbose output')
@click.pass_context
def cli(ctx, verbose):
    """Test CLI"""
    ctx.ensure_object(dict)
    ctx.obj['VERBOSE'] = verbose

@cli.command()
@click.option('--dry-run', '-d', is_flag=True, help='Dry run')
@click.pass_context
def deduplicate(ctx, dry_run):
    """Test deduplicate command"""
    print(f"Dry run: {dry_run}")
    print(f"Verbose: {ctx.obj.get('VERBOSE', 0)}")

if __name__ == '__main__':
    cli()