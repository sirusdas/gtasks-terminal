import click
from gtasks_cli.utils.logger import setup_logger
from gtasks_cli.mcp_server import run_mcp_server

logger = setup_logger(__name__)

@click.command()
def mcp():
    """Start the MCP server (Model Context Protocol)."""
    click.echo("Starting MCP server on stdio...", err=True)
    run_mcp_server()
