import os
import json
import litellm
from typing import Optional, Dict, Any
from gtasks_cli.core.task_manager import TaskManager
from gtasks_cli.ai.tools import GTasksTools, TOOL_DEFINITIONS
from gtasks_cli.storage.config_manager import ConfigManager
from gtasks_cli.utils.logger import setup_logger

logger = setup_logger(__name__)

class AIClient:
    def __init__(self, task_manager: TaskManager, account_name: Optional[str] = None):
        self.task_manager = task_manager
        self.tools = GTasksTools(task_manager, account_name=account_name)
        self.config_manager = ConfigManager(account_name=account_name)
        
        # Load AI config
        self.ai_config = self.config_manager.get('ai', {})
        self.model = self.ai_config.get('model', 'gpt-4o')
        self.provider = self.ai_config.get('provider', 'openai')
        
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
        
        # If not in config, check env vars directly (litellm does this, but good to verify)
        # We don't error here, we let litellm error if key is missing.

    def ask(self, query: str) -> str:
        """
        Process a natural language query and execute actions.
        """
        messages = [{"role": "user", "content": query}]
        
        try:
            response = litellm.completion(
                model=self.model,
                messages=messages,
                tools=TOOL_DEFINITIONS,
                tool_choice="auto"
            )
            
            message = response.choices[0].message
            
            if message.tool_calls:
                results = []
                for tool_call in message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    if hasattr(self.tools, function_name):
                        func = getattr(self.tools, function_name)
                        result = func(**function_args)
                        results.append(result)
                    else:
                        results.append(f"Error: Tool {function_name} not found.")
                
                return "\n".join(results)
            else:
                return message.content
                
        except Exception as e:
            logger.error(f"AI Error: {e}")
            return f"Error processing request: {str(e)}"

    def set_config(self, key: str, value: str):
        """Update AI configuration."""
        self.config_manager.set(f'ai.{key}', value)
