# Environment Setup for gtasks_automation

## Prerequisites
- Python 3.x installed

## Initial Setup
The virtual environment has already been created and packages installed. The environment is located in the `venv/` directory.

## Using the Environment

### Option 1: Using the setup script (recommended for macOS/Linux)

```bash
source setup_env.sh
```

This will activate the virtual environment and set the PYTHONPATH correctly.

### Option 2: Manual activation

**Windows (Command Prompt):**
```cmd
venv\Scripts\activate
set PYTHONPATH=%cd%\gtasks_cli\src
```

**Windows (PowerShell):**
```powershell
venv\Scripts\Activate.ps1
$env:PYTHONPATH = "$pwd\gtasks_cli\src"
```

**macOS/Linux:**
```bash
source venv/bin/activate
export PYTHONPATH=/Users/int/Documents/workspace/projects/gtasks_automation/gtasks_cli/src
```

Note: On macOS/Linux, you may need to update the path in the command above to match your actual project location.

## Running Scripts

After activating the environment, you can run scripts directly:

**Windows:**
```cmd
python gtasks_cli/list_task_lists.py
python gtasks_cli/list_tasks_direct.py
```

**macOS/Linux:**
```bash
python gtasks_cli/list_task_lists.py
python gtasks_cli/list_tasks_direct.py
```

## Adding New Dependencies

If you need to install new packages, make sure you're in the virtual environment and then:

```bash
pip install package_name
```

To update the requirements.txt file:

```bash
pip freeze > requirements.txt
```

## Exiting the Environment

To deactivate the virtual environment:

**Windows/macOS/Linux:**
```bash
deactivate
```