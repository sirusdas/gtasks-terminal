#!/bin/bash
# Setup script for gtasks_automation environment

echo "Activating virtual environment..."
source venv/bin/activate

echo "Setting PYTHONPATH..."
export PYTHONPATH=/Users/int/Documents/workspace/projects/gtasks_automation/gtasks_cli/src

echo "Environment is ready!"
echo "To run the application, use commands like:"
echo "  python gtasks_cli/list_task_lists.py"
echo "  python gtasks_cli/list_tasks_direct.py"