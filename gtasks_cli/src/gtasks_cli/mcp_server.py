import asyncio
import sys
from typing import List, Optional
from mcp.server.fastmcp import FastMCP
from gtasks_cli.core.task_manager import TaskManager
from gtasks_cli.ai.tools import GTasksTools

# Initialize FastMCP server
mcp = FastMCP("gtasks")

def get_tools():
    # Initialize with defaults (local storage, default account)
    # We use sqlite backend by default for MCP
    tm = TaskManager(storage_backend='sqlite')
    return GTasksTools(tm)

@mcp.tool()
def add_task(title: str, description: str = None, due: str = None, 
             priority: str = "medium", tags: List[str] = None, 
             list_name: str = None, project: str = None, 
             notes: str = None, recurrence: str = None) -> str:
    """Add a new task."""
    return get_tools().add_task(
        title=title, description=description, due=due, priority=priority,
        tags=tags, list_name=list_name, project=project, notes=notes,
        recurrence=recurrence
    )

@mcp.tool()
def update_task(task_id: str, title: str = None, description: str = None, 
                due: str = None, priority: str = None, status: str = None,
                project: str = None, tags: List[str] = None, 
                notes: str = None, recurrence: str = None) -> str:
    """Update an existing task."""
    return get_tools().update_task(
        task_id=task_id, title=title, description=description, due=due,
        priority=priority, status=status, project=project, tags=tags,
        notes=notes, recurrence=recurrence
    )

@mcp.tool()
def delete_task(task_id: str) -> str:
    """Delete a task."""
    return get_tools().delete_task(task_id)

@mcp.tool()
def complete_task(task_id: str) -> str:
    """Mark a task as completed."""
    return get_tools().complete_task(task_id)

@mcp.tool()
def list_tasks(filter_query: str = None, limit: int = 20, 
               status: str = None, priority: str = None, 
               project: str = None, tags: List[str] = None, 
               list_name: str = None) -> str:
    """List tasks with filters."""
    return get_tools().list_tasks(
        filter_query=filter_query, limit=limit, status=status,
        priority=priority, project=project, tags=tags, list_name=list_name
    )

@mcp.tool()
def search_tasks(query: str) -> str:
    """Search tasks using advanced syntax (e.g. 'foo|bar')."""
    return get_tools().search_tasks(query)

def run_mcp_server():
    """Run the MCP server."""
    mcp.run()

if __name__ == "__main__":
    run_mcp_server()
