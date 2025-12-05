# AI Integration Plan for Google Tasks CLI

This document outlines the strategy for enabling AI capabilities within the `gtasks` CLI.

## 1. Objectives
- Enable natural language interaction with tasks (e.g., "Remind me to call John next Friday at 2pm").
- Provide intelligent task organization and prioritization.
- Allow switching between different AI models (OpenAI, Anthropic, Gemini, Local LLMs).
- Expose `gtasks` functionality to external AI agents via MCP (Model Context Protocol).

## 2. Architecture

We will implement a dual-faceted approach:
1.  **Internal AI Client**: Embed AI *into* the CLI to enhance user experience.
2.  **External MCP Server**: Expose the CLI *as* a tool for other AI agents.

### 2.1 Internal AI Client (`gtasks ai`)

A new command group `ai` will be added to the CLI.

**Commands:**
- `gtasks ai ask "<query>"`: Single-shot natural language command.
    - Example: `gtasks ai ask "Add a high priority task to review the quarterly report by next Tuesday"`
    - The AI interprets this and executes the corresponding `gtasks add` command.
- `gtasks ai chat`: Interactive chat session with your tasks.
    - Context: The AI will have access to your current task list (or a summary of it).
    - Capabilities: Querying, summarizing, planning.
- `gtasks ai config`: Manage AI settings.
    - Select Provider: OpenAI, Anthropic, Gemini, Ollama (local).
    - Set API Keys.
    - Select Model (e.g., gpt-4o, claude-3-5-sonnet).

**Implementation Details:**
- **Library**: Use `litellm` for a unified interface to multiple LLM providers.
- **Tool Use**: The AI will be given a set of "tools" corresponding to internal `gtasks` Python functions (add, list, update, etc.).

### 2.2 External MCP Server (`gtasks mcp`)

We will implement an MCP server that exposes `gtasks` capabilities.

**Why?**
- Allows you to use `gtasks` from within AI-powered IDEs (like Cursor, Windsurf) or desktop agents (like Claude Desktop).
- You can ask Claude Desktop: "Check my tasks and tell me what I need to do today."

**Implementation Details:**
- **Library**: `mcp` (Python SDK).
- **Transport**: Stdio (standard input/output) for easy integration with local agents.
- **Resources**: Expose tasks as resources (e.g., `gtasks://tasks`).
- **Tools**: Expose functions:
    - `add_task(title, notes, due_date, priority)`
    - `list_tasks(filter, limit)`
    - `update_task(task_id, ...)`
    - `complete_task(task_id)`

## 3. Implementation Steps

### Phase 1: Core AI Integration
1.  Add `litellm` to `requirements.txt`.
2.  Create `gtasks_cli/src/gtasks_cli/ai/` module.
3.  Implement `AIClient` class using `litellm`.
4.  Implement `gtasks ai ask` command.
    - Define tools schema for `add`, `list`, `update`.
    - Pass user query + tools to LLM.
    - Execute returned tool calls.

### Phase 2: Configuration & Multi-Model Support
1.  Implement `gtasks ai config` to save preferences to `~/.gtasks/ai_config.yaml`.
2.  Ensure seamless switching between providers.

### Phase 3: MCP Server
1.  Add `mcp` to `requirements.txt`.
2.  Create `gtasks_cli/src/gtasks_cli/mcp_server.py`.
3.  Implement the MCP server using `FastMCP` or low-level server.
4.  Add `gtasks mcp` command to start the server.

## 4. Dependencies
- `litellm`: For multi-provider LLM support.
- `mcp`: For Model Context Protocol server implementation.
