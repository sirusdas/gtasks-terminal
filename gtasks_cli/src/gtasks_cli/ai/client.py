import os
import re
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

from gtasks_cli.core.task_manager import TaskManager
from gtasks_cli.ai.tools import GTasksTools, TOOL_DEFINITIONS
from gtasks_cli.storage.config_manager import ConfigManager
from gtasks_cli.utils.logger import setup_logger

logger = setup_logger(__name__)

try:
    import litellm
    HAS_LITELLM = True
except ImportError:
    litellm = None
    HAS_LITELLM = False


class AIClient:
    def __init__(self, task_manager: TaskManager, account_name: Optional[str] = None):
        self.task_manager = task_manager
        self.tools = GTasksTools(task_manager, account_name=account_name)
        self.config_manager = ConfigManager(account_name=account_name)
        
        # Load AI config
        self.ai_config = self.config_manager.get('ai', {})
        self.model = self.ai_config.get('model', 'gpt-4o')
        self.provider = self.ai_config.get('provider', 'openai')
        self.conversation_history: List[Dict[str, Any]] = []
        
        # Ensure API key is set
        self._setup_api_key()

    def _setup_api_key(self):
        """Ensure the appropriate API key is set in environment."""
        api_key = self.ai_config.get('api_key')
        if api_key:
            if self.provider == 'openai':
                os.environ['OPENAI_API_KEY'] = api_key
            elif self.provider == 'anthropic':
                os.environ['ANTHROPIC_API_KEY'] = api_key
            elif self.provider == 'gemini':
                os.environ['GEMINI_API_KEY'] = api_key

    def has_llm_configured(self) -> bool:
        """Check if litellm is installed and an API key is present."""
        if not HAS_LITELLM:
            return False
        if self.ai_config.get('api_key'):
            return True
        for env_var in ['OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'GEMINI_API_KEY', 'GROQ_API_KEY', 'MISTRAL_API_KEY']:
            if os.environ.get(env_var):
                return True
        return False

    def ask(self, query: str) -> str:
        """Process a one-off natural language query."""
        if self.has_llm_configured():
            return self._ask_llm(query)
        return self._ask_local(query)

    def _get_system_prompt(self) -> str:
        today_str = datetime.now().strftime('%Y-%m-%d (%A)')
        return f"""You are the GTasks AI Assistant, an intelligent task management companion.
Today's date is {today_str}.
You help the user manage their tasks, deadlines, priorities, spaces, and tags.
When the user asks you to perform an action, use the available tools (add_task, update_task, complete_task, delete_task, list_tasks, search_tasks, get_summary, get_task_details).
Always provide clear, friendly, and structured responses in clean Markdown.
Do not expose internal UUIDs to the user."""

    def _ask_llm(self, query: str, history: Optional[List[Dict[str, Any]]] = None) -> str:
        """Execute query using litellm with function calling."""
        messages = [{"role": "system", "content": self._get_system_prompt()}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": query})

        try:
            response = litellm.completion(
                model=self.model,
                messages=messages,
                tools=TOOL_DEFINITIONS,
                tool_choice="auto"
            )
            
            message = response.choices[0].message
            
            if hasattr(message, 'tool_calls') and message.tool_calls:
                messages.append(message)
                for tool_call in message.tool_calls:
                    function_name = tool_call.function.name
                    try:
                        function_args = json.loads(tool_call.function.arguments)
                    except Exception:
                        function_args = {}
                    
                    if hasattr(self.tools, function_name):
                        func = getattr(self.tools, function_name)
                        result = func(**function_args)
                    else:
                        result = f"Error: Tool {function_name} not found."
                        
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": function_name,
                        "content": str(result)
                    })
                
                # Second pass to get conversational response with tool results
                second_response = litellm.completion(
                    model=self.model,
                    messages=messages
                )
                return second_response.choices[0].message.content
            else:
                return message.content or ""
                
        except Exception as e:
            logger.error(f"LLM AI Error: {e}")
            # Fall back to local assistant
            local_res = self._ask_local(query)
            return f"{local_res}\n\n[dim](Note: LLM request encountered: {e})[/dim]"

    def _ask_local(self, query: str) -> str:
        """Local conversational assistant parsing common natural language commands."""
        q = query.strip()
        q_lower = q.lower()

        # 1. Summary
        if any(term in q_lower for term in ['summary', 'stats', 'how many task', 'overview']):
            return self.tools.get_summary()

        # 2. Complete / Done
        complete_match = re.search(r'^(?:complete|done|finish|mark done|mark complete)\s+(.+)$', q, re.IGNORECASE)
        if complete_match:
            target = complete_match.group(1).strip()
            return self.tools.complete_task(target)

        # 3. Delete / Remove
        delete_match = re.search(r'^(?:delete|remove|cancel task)\s+(.+)$', q, re.IGNORECASE)
        if delete_match:
            target = delete_match.group(1).strip()
            return self.tools.delete_task(target)

        # 4. Search
        search_match = re.search(r'^(?:search|find)\s+(.+)$', q, re.IGNORECASE)
        if search_match:
            term = search_match.group(1).strip()
            return self.tools.search_tasks(term)

        # 5. List / Show tasks
        if (any(term in q_lower for term in ['list', 'tasks', 'todo', 'to do']) or ('show' in q_lower and 'task' in q_lower)) and not any(q_lower.startswith(w) for w in ['add', 'create', 'new', 'complete', 'done', 'delete', 'remove', 'search', 'find']):
            status = 'pending' if 'pending' in q_lower else ('completed' if 'completed' in q_lower else None)
            priority = 'high' if 'high' in q_lower else ('low' if 'low' in q_lower else ('critical' in q_lower and 'critical' or None))
            return self.tools.list_tasks(status=status, priority=priority)

        # 6. Add / Create task
        add_match = re.search(r'^(?:add|create|new task)\s+(.+)$', q, re.IGNORECASE)
        if add_match:
            raw_text = add_match.group(1).strip()
            title = raw_text
            due = None
            priority = "medium"
            spaces = None
            tags = []

            # Extract priority if mentioned
            if "priority:high" in raw_text.lower() or "with high priority" in raw_text.lower():
                priority = "high"
                raw_text = re.sub(r'(?:with\s+)?priority:high|with\s+high\s+priority', '', raw_text, flags=re.I).strip()
            elif "priority:low" in raw_text.lower() or "with low priority" in raw_text.lower():
                priority = "low"
                raw_text = re.sub(r'(?:with\s+)?priority:low|with\s+low\s+priority', '', raw_text, flags=re.I).strip()
            elif "priority:critical" in raw_text.lower() or "with critical priority" in raw_text.lower():
                priority = "critical"
                raw_text = re.sub(r'(?:with\s+)?priority:critical|with\s+critical\s+priority', '', raw_text, flags=re.I).strip()

            # Extract due date if mentioned
            if "due tomorrow" in raw_text.lower() or "tomorrow" in raw_text.lower():
                due = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
                raw_text = re.sub(r'\bdue\s+tomorrow\b|\btomorrow\b', '', raw_text, flags=re.I).strip()
            elif "due today" in raw_text.lower() or "today" in raw_text.lower():
                due = datetime.now().strftime('%Y-%m-%d')
                raw_text = re.sub(r'\bdue\s+today\b|\btoday\b', '', raw_text, flags=re.I).strip()

            # Extract spaces
            space_match = re.search(r'space:([a-zA-Z0-9_:\-,]+)', raw_text, re.I)
            if space_match:
                spaces = space_match.group(1)
                raw_text = raw_text.replace(space_match.group(0), '').strip()

            # Extract tags
            tag_matches = re.findall(r'#([a-zA-Z0-9_\-]+)', raw_text)
            if tag_matches:
                tags = tag_matches
                raw_text = re.sub(r'#[a-zA-Z0-9_\-]+', '', raw_text).strip()

            title = raw_text.strip() or "Untitled Task"
            return self.tools.add_task(title=title, due=due, priority=priority, spaces=spaces, tags=tags)

        # 7. Help / Info
        if q_lower in ['help', 'what can you do', 'info', '?']:
            return """🤖 **I can help you manage your tasks conversationally:**
- **Create task:** "Add prepare slides tomorrow with high priority"
- **List tasks:** "Show my pending tasks" or "List tasks"
- **Complete task:** "Complete 1" or "Done buy groceries"
- **Delete task:** "Delete 3"
- **Search tasks:** "Search project"
- **Summary:** "Show task summary"
*(Tip: Configure external LLMs with `gtasks ai config --key api_key --value YOUR_KEY`)*"""

        # Default fallback
        return f"I understood: '{q}'.\nTry: 'add <task>', 'list', 'complete <number>', 'search <word>', or 'summary'."

    def chat_turn(self, user_input: str) -> str:
        """Process one turn in an ongoing chat conversation."""
        if self.has_llm_configured():
            response = self._ask_llm(user_input, history=self.conversation_history)
            self.conversation_history.append({"role": "user", "content": user_input})
            self.conversation_history.append({"role": "assistant", "content": response})
            # Keep history manageable
            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-20:]
            return response
        else:
            return self._ask_local(user_input)

    def chat_loop(self):
        """Run an interactive conversation loop in the terminal."""
        from rich.console import Console
        from rich.panel import Panel
        from rich.markdown import Markdown

        console = Console()
        has_llm = self.has_llm_configured()
        mode_desc = f"[green]Active LLM: {self.model}[/green]" if has_llm else "[yellow]Mode: Built-in Conversational Assistant (offline/local)[/yellow]"
        
        banner = [
            "[bold cyan]🤖 GTasks AI Chat Bot[/bold cyan]",
            mode_desc,
            "",
            "[dim]Talk naturally with your tasks! Examples:[/dim]",
            "  • [italic]'Add review quarterly budget tomorrow with high priority'[/italic]",
            "  • [italic]'Show my pending tasks'[/italic]",
            "  • [italic]'Complete task 1'[/italic]",
            "  • [italic]'Give me a summary of my tasks'[/italic]",
            "",
            "[dim]Type 'exit', 'quit', or 'back' to leave chat mode.[/dim]"
        ]
        console.print(Panel("\n".join(banner), title="[bold]Chat Assistant[/bold]", border_style="cyan"))

        while True:
            try:
                user_msg = console.input("\n[bold cyan]You > [/bold cyan]").strip()
                if not user_msg:
                    continue
                if user_msg.lower() in ['exit', 'quit', 'back', ':q']:
                    console.print("[dim]Exiting AI Chat. Goodbye![/dim]")
                    break
                
                with console.status("[bold green]Thinking...[/bold green]", spinner="dots"):
                    reply = self.chat_turn(user_msg)
                
                console.print(f"\n[bold magenta]🤖 Assistant:[/bold magenta]")
                console.print(Markdown(reply))

            except (KeyboardInterrupt, EOFError):
                console.print("\n[dim]Chat cancelled.[/dim]")
                break
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")

    def set_config(self, key: str, value: str):
        """Update AI configuration."""
        self.config_manager.set(f'ai.{key}', value)
