#!/bin/bash
# Setup script for gtasks_automation environment

echo "Activating virtual environment..."
source venv/bin/activate

echo "Setting PYTHONPATH..."
# Use the current directory for PYTHONPATH to make it portable
export PYTHONPATH="$(pwd)/gtasks_cli/src"

echo "Environment is ready!"
echo "To run the application, use commands like:"
echo "  python gtasks_cli/list_task_lists.py"
echo "  python gtasks_cli/list_tasks_direct.py"
echo ""
echo "Note for Windows users:"
echo "----------------------"
echo "On Windows, use these commands instead:"
echo "  venv\Scripts\activate"
echo "  set PYTHONPATH=%cd%\gtasks_cli\src"
echo ""
echo "Or in PowerShell:"
echo "  venv\Scripts\Activate.ps1"
echo "  \$env:PYTHONPATH = \"\$pwd\gtasks_cli\src\""