"""
AI Assistant Service for GTasks Dashboard
Handles LLM communications (Gemini, OpenAI, Claude, Local/Ollama),
Function Calling / Tool Execution, Persistent Chat Sessions, and 1-Command Workflows.
"""

import json
import sqlite3
import urllib.request
import urllib.error
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Any, Optional, Generator, Tuple

from gtasks_cli.core.task_manager import TaskManager
from gtasks_cli.ai.tools import GTasksTools, TOOL_DEFINITIONS


class AiService:
    CONFIG_PATH = Path.home() / ".gtasks" / "ai_config.json"
    DB_PATH = Path.home() / ".gtasks" / "ai_chat.db"

    def __init__(self, account_name: Optional[str] = "Work"):
        self.account_name = account_name
        self._init_db()

    # -------------------------------------------------------------------------
    # Database & Session Persistence
    # -------------------------------------------------------------------------
    def _init_db(self):
        """Initialize SQLite database for chat sessions and history."""
        self.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.DB_PATH) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    tool_calls TEXT,
                    tool_results TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_msg_session ON messages(session_id, created_at)")
            conn.commit()

    def get_sessions(self) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sessions ORDER BY updated_at DESC")
            return [dict(row) for row in cursor.fetchall()]

    def get_messages(self, session_id: str) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM messages WHERE session_id = ? ORDER BY id ASC",
                (session_id,)
            )
            rows = cursor.fetchall()
            messages = []
            for r in rows:
                m = dict(r)
                if m.get('tool_calls'):
                    try: m['tool_calls'] = json.loads(m['tool_calls'])
                    except Exception: pass
                if m.get('tool_results'):
                    try: m['tool_results'] = json.loads(m['tool_results'])
                    except Exception: pass
                messages.append(m)
            return messages

    def save_message(self, session_id: str, role: str, content: str, tool_calls: Any = None, tool_results: Any = None) -> int:
        now = datetime.now().isoformat()
        with sqlite3.connect(self.DB_PATH) as conn:
            # Check or create session
            cur = conn.cursor()
            cur.execute("SELECT id FROM sessions WHERE id = ?", (session_id,))
            if not cur.fetchone():
                title = content[:35] + ("..." if len(content) > 35 else "") if content else "New Chat"
                cfg = self.get_config()
                conn.execute(
                    "INSERT INTO sessions (id, title, provider, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                    (session_id, title, cfg.get("provider", "gemini"), now, now)
                )
            else:
                conn.execute("UPDATE sessions SET updated_at = ? WHERE id = ?", (now, session_id))

            tc_json = json.dumps(tool_calls) if tool_calls else None
            tr_json = json.dumps(tool_results) if tool_results else None

            cur.execute(
                "INSERT INTO messages (session_id, role, content, tool_calls, tool_results, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (session_id, role, content, tc_json, tr_json, now)
            )
            conn.commit()
            return cur.lastrowid

    def delete_session(self, session_id: str):
        with sqlite3.connect(self.DB_PATH) as conn:
            conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
            conn.commit()

    # -------------------------------------------------------------------------
    # Configuration Management
    # -------------------------------------------------------------------------
    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        default_config = {
            "provider": "gemini",
            "api_key": "",
            "model": "gemini-1.5-flash",
            "local_endpoint": "http://localhost:11434/v1"
        }
        if cls.CONFIG_PATH.exists():
            try:
                with open(cls.CONFIG_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    default_config.update(data)
            except Exception:
                pass
        return default_config

    @classmethod
    def save_config(cls, config: Dict[str, Any]) -> Dict[str, Any]:
        cls.CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        current = cls.get_config()
        current.update(config)
        with open(cls.CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(current, f, indent=2)
        return current

    # -------------------------------------------------------------------------
    # Tools & Execution Engine
    # -------------------------------------------------------------------------
    def _get_tools(self, account_name: Optional[str] = None) -> GTasksTools:
        acc = account_name or self.account_name or "Work"
        tm = TaskManager(storage_backend="sqlite", account_name=acc, use_google_tasks=True)
        return GTasksTools(tm, account_name=acc)

    def execute_tool(self, name: str, args: Dict[str, Any], account_name: Optional[str] = None) -> str:
        tools = self._get_tools(account_name)
        if hasattr(tools, name):
            try:
                method = getattr(tools, name)
                result = method(**args)
                return str(result)
            except Exception as e:
                return f"Error executing tool '{name}': {str(e)}"
        return f"Unknown tool: '{name}'"

    # -------------------------------------------------------------------------
    # Chat Dispatcher & Gemini Integration
    # -------------------------------------------------------------------------
    def chat(self, user_message: str, session_id: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a user message, run function calling loop if needed, and return response.
        """
        cfg = self.get_config()
        api_key = cfg.get("api_key", "").strip()
        provider = cfg.get("provider", "gemini").lower()
        model = cfg.get("model", "gemini-1.5-flash")

        # Save user message to history
        self.save_message(session_id, "user", user_message)

        # Check for 1-command workflow triggers directly
        trimmed = user_message.strip()
        if trimmed.startswith("/"):
            parts = trimmed[1:].split(maxsplit=1)
            wf_name = parts[0]
            goal_arg = parts[1] if len(parts) > 1 else ""
            tools = self._get_tools(context.get("active_account") if context else None)
            wf_res = tools.execute_workflow(wf_name, {"goal": goal_arg})
            self.save_message(session_id, "assistant", wf_res)
            return {
                "reply": wf_res,
                "session_id": session_id,
                "workflow_executed": wf_name,
            }

        if not api_key and provider != "local":
            help_msg = (
                "⚠️ **No API Key configured.**\n\n"
                "To enable the AI Assistant:\n"
                "1. Click the **AI Settings (⚙️)** icon in the chat header.\n"
                "2. Click **'Get Free Gemini API Key'** (opens Google AI Studio in 1 tap).\n"
                "3. Paste your key and click Save."
            )
            self.save_message(session_id, "assistant", help_msg)
            return {"reply": help_msg, "session_id": session_id}

        # Dispatch based on provider
        if provider == "gemini":
            return self._chat_gemini(user_message, session_id, api_key, model, context)
        else:
            return self._chat_openai_compatible(user_message, session_id, api_key, model, cfg.get("local_endpoint"), context)

    def _build_system_prompt(self, context: Optional[Dict[str, Any]] = None) -> str:
        ctx = context or {}
        today = date.today().isoformat()
        active_acc = ctx.get("active_account", "All")
        active_spa = ctx.get("active_space", "All")

        return (
            f"You are GTasks AI Assistant, an ultra-fast, intelligent productivity coordinator. "
            f"Today's date is {today}. "
            f"The user is currently viewing account: '{active_acc}' and space: '{active_spa}'.\n"
            f"Guidelines:\n"
            f"1. You have direct tools to query, create, update, reschedule, and complete tasks.\n"
            f"2. GTasks uses Spaces and Sub-spaces for hierarchical categorization (e.g. work › dev, personal › health).\n"
            f"3. Always use `query_tasks` to inspect tasks instead of guessing or hallucinating.\n"
            f"4. Keep your conversational answers clear, formatted with markdown, and concise.\n"
            f"5. Suggest 1-tap workflows (/morning, /evening, /breakdown, /triage) when relevant."
        )

    def _chat_gemini(
        self,
        user_message: str,
        session_id: str,
        api_key: str,
        model: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Executes Gemini 1.5 API call with function calling loop via REST.
        """
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

        # Fetch recent chat history
        history = self.get_messages(session_id)
        # Keep last 12 messages
        recent = history[-12:] if len(history) > 12 else history

        # Format Gemini contents
        contents = []
        for m in recent:
            role = "user" if m["role"] == "user" else "model"
            contents.append({
                "role": role,
                "parts": [{"text": m["content"]}]
            })

        # Format Gemini Tool Declarations from TOOL_DEFINITIONS
        gemini_tools = []
        for td in TOOL_DEFINITIONS:
            fn = td["function"]
            gemini_tools.append({
                "name": fn["name"],
                "description": fn["description"],
                "parameters": fn["parameters"],
            })

        payload = {
            "system_instruction": {
                "parts": [{"text": self._build_system_prompt(context)}]
            },
            "contents": contents,
            "tools": [{"function_declarations": gemini_tools}]
        }

        # Multi-turn tool calling loop (max 3 turns)
        executed_tool_calls = []
        executed_tool_results = []

        for _ in range(3):
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )

            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    resp_data = json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                err_body = e.read().decode("utf-8")
                err_msg = f"Gemini API Error ({e.code}): {err_body}"
                self.save_message(session_id, "assistant", err_msg)
                return {"reply": err_msg, "session_id": session_id}
            except Exception as e:
                err_msg = f"Connection Error: {str(e)}"
                self.save_message(session_id, "assistant", err_msg)
                return {"reply": err_msg, "session_id": session_id}

            candidates = resp_data.get("candidates", [])
            if not candidates:
                msg = "No response generated by model."
                self.save_message(session_id, "assistant", msg)
                return {"reply": msg, "session_id": session_id}

            content = candidates[0].get("content", {})
            parts = content.get("parts", [])

            # Check for functionCall
            fn_calls = [p["functionCall"] for p in parts if "functionCall" in p]
            if not fn_calls:
                # Text answer
                text_parts = [p["text"] for p in parts if "text" in p]
                reply_text = "\n".join(text_parts).strip()
                self.save_message(session_id, "assistant", reply_text, executed_tool_calls, executed_tool_results)
                return {
                    "reply": reply_text,
                    "session_id": session_id,
                    "tool_calls": executed_tool_calls,
                    "tool_results": executed_tool_results,
                }

            # Execute function call
            fn_call = fn_calls[0]
            name = fn_call["name"]
            args = fn_call.get("args", {})
            target_account = args.get("account_name") or (context.get("active_account") if context else None)

            result_str = self.execute_tool(name, args, account_name=target_account)
            executed_tool_calls.append({"name": name, "args": args})
            executed_tool_results.append({"name": name, "result": result_str})

            # Append model functionCall part and functionResponse part
            contents.append({
                "role": "model",
                "parts": [{"functionCall": fn_call}]
            })
            contents.append({
                "role": "function",
                "parts": [{
                    "functionResponse": {
                        "name": name,
                        "response": {"output": result_str}
                    }
                }]
            })
            payload["contents"] = contents

        return {
            "reply": "Operation completed.",
            "session_id": session_id,
            "tool_calls": executed_tool_calls,
            "tool_results": executed_tool_results,
        }

    def _chat_openai_compatible(
        self,
        user_message: str,
        session_id: str,
        api_key: str,
        model: str,
        endpoint: Optional[str],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Supports OpenAI, Claude, and Local Ollama via OpenAI standard chat API."""
        base_url = endpoint or "https://api.openai.com/v1"
        url = f"{base_url.rstrip('/')}/chat/completions"

        history = self.get_messages(session_id)
        messages = [{"role": "system", "content": self._build_system_prompt(context)}]
        for m in history[-10:]:
            messages.append({"role": m["role"], "content": m["content"]})

        payload = {
            "model": model,
            "messages": messages,
            "tools": TOOL_DEFINITIONS,
            "tool_choice": "auto"
        }

        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            err = f"AI Provider Error: {str(e)}"
            self.save_message(session_id, "assistant", err)
            return {"reply": err, "session_id": session_id}

        choice = data.get("choices", [{}])[0].get("message", {})
        if choice.get("tool_calls"):
            # Handle first tool call
            tc = choice["tool_calls"][0]
            fn = tc.get("function", {})
            name = fn.get("name", "")
            try: args = json.loads(fn.get("arguments", "{}"))
            except Exception: args = {}

            res_str = self.execute_tool(name, args, context.get("active_account") if context else None)
            reply = f"🛠️ Executed `{name}`:\n\n{res_str}"
            self.save_message(session_id, "assistant", reply, [fn], [{"name": name, "result": res_str}])
            return {"reply": reply, "session_id": session_id}

        reply = choice.get("content", "").strip()
        self.save_message(session_id, "assistant", reply)
        return {"reply": reply, "session_id": session_id}
