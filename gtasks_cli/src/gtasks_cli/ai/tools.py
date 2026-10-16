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
                if not self.task_manager.google_client.connect(interactive=False):
                    return ""
                sync_manager = AdvancedSyncManager(self.task_manager.storage, self.task_manager.google_client)
                if sync_manager.sync_single_task(task, operation, old_task_id=old_task_id):
                    return " (Auto-saved to Google Tasks)"
                else:
                    return " (Failed to auto-save to Google Tasks)"
            except Exception as e:
                return f" (Auto-save error: {str(e)})"
        return ""

    def _resolve_task(self, identifier: str):
        """Resolve a task by exact ID, 1-based display number, or title matching."""
        tasks = self.task_manager.list_tasks()
        if not tasks or not identifier:
            return None
            
        ident = str(identifier).strip()
        
        # 1. Exact ID match
        for t in tasks:
            if t.id == ident:
                return t
                
        # 2. Number match (1-based index)
        if ident.isdigit():
            idx = int(ident) - 1
            if 0 <= idx < len(tasks):
                return tasks[idx]
                
        # 3. Exact title match (case-insensitive)
        for t in tasks:
            if t.title.lower() == ident.lower():
                return t
                
        # 4. Substring title match
        for t in tasks:
            if ident.lower() in t.title.lower():
                return t
                
        return None

    def add_task(self, title: str, description: Optional[str] = None, 
                 due: Optional[str] = None, priority: str = "medium", 
                 tags: Optional[List[str]] = None, list_name: Optional[str] = None,
                 project: Optional[str] = None, notes: Optional[str] = None,
                 spaces: Optional[str] = None, recurrence: Optional[str] = None,
                 estimated_duration: Optional[int] = None):
        """
        Add a new task to the list with optional spaces and metadata.
        """
        priority_enum = Priority[priority.upper()] if hasattr(Priority, priority.upper()) else Priority.MEDIUM
        
        content = notes or description or ""
        from gtasks_cli.utils.space_extractor import parse_spaces_input, combine_notes_and_metadata
        parsed_spaces = parse_spaces_input(spaces) if spaces else None
        if parsed_spaces or tags:
            content = combine_notes_and_metadata(content, tags=tags, spaces=parsed_spaces)
            description = content
            notes = content

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
        )
        
        if task:
            msg = f"Task '{task.title}' created successfully."
            msg += self._auto_save(task, 'create', old_task_id=task.id)
            return msg
        else:
            return "Failed to create task."

    def update_task(self, task_id: str, title: Optional[str] = None, 
                    description: Optional[str] = None, due: Optional[str] = None, 
                    priority: Optional[str] = None, project: Optional[str] = None,
                    status: Optional[str] = None, tags: Optional[List[str]] = None,
                    notes: Optional[str] = None, spaces: Optional[str] = None,
                    recurrence: Optional[str] = None):
        """
        Update an existing task.
        """
        task = self._resolve_task(task_id)
        if not task:
            return f"Task '{task_id}' not found."

        update_data = {}
        if title: update_data['title'] = title
        if due: update_data['due'] = due
        if priority and hasattr(Priority, priority.upper()): 
            update_data['priority'] = Priority[priority.upper()]
        if project: update_data['project'] = project
        if status: update_data['status'] = TaskStatus(status)
        if tags: update_data['tags'] = tags
        if recurrence is not None: 
            update_data['recurrence_rule'] = recurrence
            update_data['is_recurring'] = bool(recurrence)

        if spaces or notes is not None or description is not None:
            from gtasks_cli.utils.space_extractor import parse_spaces_input, combine_notes_and_metadata
            parsed_spaces = parse_spaces_input(spaces) if spaces else getattr(task, 'spaces', None)
            base_content = notes if notes is not None else (description if description is not None else (task.notes or task.description or ""))
            combined = combine_notes_and_metadata(base_content, tags=tags or task.tags, spaces=parsed_spaces)
            update_data['notes'] = combined
            update_data['description'] = combined
            if parsed_spaces:
                update_data['spaces'] = parsed_spaces

        updated_task = self.task_manager.update_task(task.id, **update_data)
        
        if updated_task:
            msg = f"Task '{task.title}' updated successfully."
            msg += self._auto_save(task, 'update')
            return msg
        else:
            return f"Failed to update task '{task.title}'."

    def delete_task(self, task_id: str):
        """
        Delete a task.
        """
        task = self._resolve_task(task_id)
        if not task:
            return f"Task '{task_id}' not found."
            
        if self.task_manager.delete_task(task.id):
            msg = f"Task '{task.title}' deleted successfully."
            msg += self._auto_save(task, 'delete')
            return msg
        else:
            return f"Failed to delete task '{task.title}'."

    def complete_task(self, task_id: str):
        """
        Mark a task as completed.
        """
        task = self._resolve_task(task_id)
        if not task:
            return f"Task '{task_id}' not found."
        return self.update_task(task.id, status='completed')

    def get_summary(self) -> str:
        """
        Get summary of task counts by status, priority, and overdue status.
        """
        tasks = self.task_manager.list_tasks()
        total = len(tasks)
        pending = sum(1 for t in tasks if str(getattr(t, 'status', '')).lower() in ['pending', 'in_progress'])
        completed = sum(1 for t in tasks if str(getattr(t, 'status', '')).lower() == 'completed')
        
        from datetime import datetime
        now = datetime.now()
        overdue = 0
        for t in tasks:
            if getattr(t, 'due', None) and str(getattr(t, 'status', '')).lower() in ['pending', 'in_progress']:
                try:
                    d = t.due if isinstance(t.due, datetime) else datetime.fromisoformat(str(t.due))
                    if d.date() < now.date():
                        overdue += 1
                except Exception:
                    pass
                    
        return f"📊 Tasks Summary:\n- Total: {total}\n- Pending/In Progress: {pending}\n- Completed: {completed}\n- Overdue: {overdue}"

    def get_task_details(self, task_id: str) -> str:
        """
        Get full details of a specific task.
        """
        task = self._resolve_task(task_id)
        if not task:
            return f"Task '{task_id}' not found."
            
        due_str = f"Due: {task.due}" if task.due else "No due date"
        prio_str = task.priority if isinstance(task.priority, str) else task.priority.value
        status_str = task.status if isinstance(task.status, str) else task.status.value
        lines = [
            f"Title: {task.title}",
            f"Status: {status_str.upper()}",
            f"Priority: {prio_str.upper()}",
            f"Due Date: {due_str}",
        ]
        if task.tags:
            lines.append(f"Tags: {', '.join(task.tags)}")
        from gtasks_cli.utils.space_extractor import extract_spaces_from_text, split_notes_and_metadata
        spaces = getattr(task, 'spaces', None) or extract_spaces_from_text(task.notes or task.description or "")
        if spaces:
            sp_strs = [f"{s} › {', '.join(subs)}" if subs else s for s, subs in spaces.items()]
            lines.append(f"Spaces: {' | '.join(sp_strs)}")
        raw = task.notes or task.description or ""
        clean_notes, _, _ = split_notes_and_metadata(raw)
        if clean_notes:
            lines.append(f"Notes:\n  {clean_notes.strip()}")
        return "\n".join(lines)

    def list_tasks(self, filter_query: Optional[str] = None, limit: int = 20,
                   status: Optional[str] = None, priority: Optional[str] = None,
                   project: Optional[str] = None, tags: Optional[List[str]] = None,
                   space: Optional[str] = None, list_name: Optional[str] = None):
        """
        List tasks with various filters.
        """
        status_enum = TaskStatus(status) if status else None
        priority_enum = Priority[priority.upper()] if priority and hasattr(Priority, priority.upper()) else None
        
        tasks = self.task_manager.list_tasks(
            status=status_enum,
            priority=priority_enum,
            project=project
        )
        
        if list_name:
            tasks = [t for t in tasks if getattr(t, 'list_title', '').lower() == list_name.lower()]
            
        if tags:
            tasks = [t for t in tasks if any(tag in t.tags for tag in tags)]

        if space:
            from gtasks_cli.commands.interactive_utils.search import apply_space_filter
            tasks = apply_space_filter(tasks, space)
            
        if filter_query:
            q = filter_query.lower()
            tasks = [t for t in tasks if q in t.title.lower() or (t.description and q in t.description.lower())]

        output = []
        for i, t in enumerate(tasks[:limit], 1):
            due_str = f" | 📅 {t.due.strftime('%Y-%m-%d') if hasattr(t.due, 'strftime') else str(t.due)[:10]}" if t.due else ""
            status_str = t.status.value if hasattr(t.status, 'value') else str(t.status)
            prio_str = t.priority.value if hasattr(t.priority, 'value') else str(t.priority)
            output.append(f"{i}. [{status_str.upper()}] [{prio_str.upper()}] {t.title}{due_str}")
            
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
        for i, t in enumerate(results[:20], 1):
            due_str = f" | 📅 {t.due.strftime('%Y-%m-%d') if hasattr(t.due, 'strftime') else str(t.due)[:10]}" if t.due else ""
            status_str = t.status.value if hasattr(t.status, 'value') else str(t.status)
            output.append(f"{i}. [{status_str.upper()}] {t.title}{due_str}")
            
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
                    "title": {"type": "string", "description": "Title of the task"},
                    "description": {"type": "string", "description": "Optional description or notes"},
                    "due": {"type": "string", "description": "Due date (YYYY-MM-DD or natural language like 'tomorrow')"},
                    "priority": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
                    "tags": {"type": "array", "items": {"type": "string"}, "description": "Tags list"},
                    "spaces": {"type": "string", "description": "Spaces and subspaces, e.g. 'work:frontend, personal'"},
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
            "description": "Update an existing task by ID, number, or title.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "Task ID, display number (e.g. '1'), or title"},
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "due": {"type": "string"},
                    "priority": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
                    "status": {"type": "string", "enum": ["pending", "in_progress", "completed", "waiting", "deleted"]},
                    "spaces": {"type": "string", "description": "Spaces and subspaces, e.g. 'work:frontend'"},
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
            "description": "Delete a task by ID, number, or title.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "Task ID, display number, or title"}
                },
                "required": ["task_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "complete_task",
            "description": "Mark a task as completed by ID, number, or title.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "Task ID, display number, or title"}
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
                    "space": {"type": "string", "description": "Filter by space or subspace"},
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
    },
    {
        "type": "function",
        "function": {
            "name": "get_summary",
            "description": "Get summary metrics of tasks: total, pending, completed, overdue counts.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_task_details",
            "description": "Get detailed information for a task by ID, number, or title.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "Task ID, display number, or title"}
                },
                "required": ["task_id"]
            }
        }
    }
]
