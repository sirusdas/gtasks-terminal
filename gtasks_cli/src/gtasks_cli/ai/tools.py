from typing import List, Optional
from gtasks_cli.core.task_manager import TaskManager
from gtasks_cli.models.task import Priority, TaskStatus
from gtasks_cli.storage.config_manager import ConfigManager
from gtasks_cli.integrations.advanced_sync_manager import AdvancedSyncManager

class GTasksTools:
    def __init__(self, task_manager: TaskManager, account_name: Optional[str] = None):
        self.task_manager = task_manager
        self.account_name = account_name
        self.config_manager = ConfigManager(account_name=account_name)

    def _auto_save(self, task, operation: str, old_task_id: str = None) -> str:
        """Handle auto-save to Google Tasks if enabled."""
        # Check config for auto-save
        auto_save = self.config_manager.get('sync.auto_save', False)
        
        if not self.task_manager.use_google_tasks and auto_save:
            try:
                sync_manager = AdvancedSyncManager(self.task_manager.storage, self.task_manager.google_client)
                if sync_manager.sync_single_task(task, operation, old_task_id=old_task_id):
                    return " (Auto-saved to Google Tasks)"
                else:
                    return " (Failed to auto-save to Google Tasks)"
            except Exception as e:
                return f" (Auto-save error: {str(e)})"
        return ""

    def add_task(self, title: str, description: Optional[str] = None, 
                 due: Optional[str] = None, priority: str = "medium", 
                 tags: Optional[List[str]] = None, list_name: Optional[str] = None,
                 project: Optional[str] = None, notes: Optional[str] = None,
                 recurrence: Optional[str] = None, estimated_duration: Optional[int] = None):
        """
        Add a new task to the list.
        """
        priority_enum = Priority[priority.upper()]
        
        task = self.task_manager.create_task(
            title=title,
            description=description,
            due=due,
            priority=priority_enum,
            tags=tags or [],
            tasklist_name=list_name,
            project=project,
            notes=notes,
            recurrence_rule=recurrence
            # estimated_duration is not supported in create_task yet? checking add.py... 
            # add.py doesn't pass estimated_duration to create_task, it seems ignored or I missed it.
            # checking TaskManager.create_task signature...
        )
        
        if task:
            msg = f"Task created successfully: {task.title} (ID: {task.id})"
            msg += self._auto_save(task, 'create', old_task_id=task.id)
            return msg
        else:
            return "Failed to create task."

    def update_task(self, task_id: str, title: Optional[str] = None, 
                    description: Optional[str] = None, due: Optional[str] = None, 
                    priority: Optional[str] = None, project: Optional[str] = None,
                    status: Optional[str] = None, tags: Optional[List[str]] = None,
                    notes: Optional[str] = None, recurrence: Optional[str] = None):
        """
        Update an existing task.
        """
        update_data = {}
        if title: update_data['title'] = title
        if description: update_data['description'] = description
        if due: update_data['due'] = due
        if priority: update_data['priority'] = Priority[priority.upper()]
        if project: update_data['project'] = project
        if status: update_data['status'] = TaskStatus(status)
        if tags: update_data['tags'] = tags
        if notes is not None: update_data['notes'] = notes
        if recurrence is not None: 
            update_data['recurrence_rule'] = recurrence
            update_data['is_recurring'] = bool(recurrence)

        updated_task = self.task_manager.update_task(task_id, **update_data)
        
        if updated_task:
            msg = f"Task updated successfully: {updated_task.title}"
            msg += self._auto_save(updated_task, 'update')
            return msg
        else:
            return f"Task with ID {task_id} not found."

    def delete_task(self, task_id: str):
        """
        Delete a task.
        """
        # We need the task object before deletion for auto-save (maybe?)
        # Actually sync_single_task for delete needs the task object or at least ID.
        # Let's check delete command implementation.
        # It calls task_manager.delete_task(task_id) which returns success bool.
        # But for sync, we need the task.
        
        # Get task first
        tasks = self.task_manager.list_tasks()
        task = next((t for t in tasks if t.id == task_id), None)
        
        if not task:
            return f"Task with ID {task_id} not found."
            
        if self.task_manager.delete_task(task_id):
            msg = f"Task deleted successfully: {task.title}"
            # For delete, we pass the task object but operation is 'delete'
            # The sync manager handles it.
            msg += self._auto_save(task, 'delete')
            return msg
        else:
            return "Failed to delete task."

    def complete_task(self, task_id: str):
        """
        Mark a task as completed.
        """
        return self.update_task(task_id, status='completed')

    def list_tasks(self, filter_query: Optional[str] = None, limit: int = 20,
                   status: Optional[str] = None, priority: Optional[str] = None,
                   project: Optional[str] = None, tags: Optional[List[str]] = None,
                   list_name: Optional[str] = None):
        """
        List tasks with various filters.
        """
        # Convert string filters to enums
        status_enum = TaskStatus(status) if status else None
        priority_enum = Priority[priority.upper()] if priority else None
        
        # Get tasks
        tasks = self.task_manager.list_tasks(
            status=status_enum,
            priority=priority_enum,
            project=project
        )
        
        # Apply other filters manually if not supported by list_tasks directly
        if list_name:
            tasks = [t for t in tasks if getattr(t, 'list_title', '').lower() == list_name.lower()]
            
        if tags:
            # Simple check if any of the requested tags are in the task tags
            tasks = [t for t in tasks if any(tag in t.tags for tag in tags)]
            
        if filter_query:
            # Simple text search
            q = filter_query.lower()
            tasks = [t for t in tasks if q in t.title.lower() or (t.description and q in t.description.lower())]

        # Format output
        output = []
        for t in tasks[:limit]:
            due_str = f" Due: {t.due}" if t.due else ""
            output.append(f"- [ID: {t.id}] [{t.status.value}] {t.title}{due_str}")
            
        if not output:
            return "No tasks found matching criteria."
            
        return "\n".join(output)

    def search_tasks(self, query: str):
        """
        Search tasks using advanced search syntax (e.g. "meeting|call").
        """
        from gtasks_cli.commands.interactive_utils.search import apply_search_filter
        
        tasks = self.task_manager.list_tasks()
        results = apply_search_filter(tasks, query)
        
        output = []
        for t in results[:20]:
            due_str = f" Due: {t.due}" if t.due else ""
            output.append(f"- [ID: {t.id}] [{t.status.value}] {t.title}{due_str}")
            
        if not output:
            return f"No tasks found for query: {query}"
            
        return "\n".join(output)

# Tool Definitions
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "add_task",
            "description": "Add a new task.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "due": {"type": "string"},
                    "priority": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
                    "tags": {"type": "array", "items": {"type": "string"}},
                    "list_name": {"type": "string"},
                    "project": {"type": "string"},
                    "notes": {"type": "string"},
                    "recurrence": {"type": "string"}
                },
                "required": ["title"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_task",
            "description": "Update an existing task.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "string"},
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "due": {"type": "string"},
                    "priority": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
                    "status": {"type": "string", "enum": ["pending", "in_progress", "completed", "waiting", "deleted"]},
                    "project": {"type": "string"},
                    "tags": {"type": "array", "items": {"type": "string"}},
                    "notes": {"type": "string"},
                    "recurrence": {"type": "string"}
                },
                "required": ["task_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_task",
            "description": "Delete a task.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "string"}
                },
                "required": ["task_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "complete_task",
            "description": "Mark a task as completed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "string"}
                },
                "required": ["task_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_tasks",
            "description": "List tasks with filters.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filter_query": {"type": "string"},
                    "limit": {"type": "integer"},
                    "status": {"type": "string", "enum": ["pending", "in_progress", "completed", "waiting", "deleted"]},
                    "priority": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
                    "project": {"type": "string"},
                    "tags": {"type": "array", "items": {"type": "string"}},
                    "list_name": {"type": "string"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_tasks",
            "description": "Search tasks using advanced syntax (e.g. 'foo|bar').",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                },
                "required": ["query"]
            }
        }
    }
]
