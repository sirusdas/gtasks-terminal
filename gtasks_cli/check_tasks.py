#!/usr/bin/env python3

import json
from pathlib import Path
from datetime import datetime

# Load tasks from storage
storage_path = Path.home() / '.gtasks' / 'tasks.json'
with open(storage_path, 'r') as f:
    tasks = json.load(f)

print(f"Total tasks in storage: {len(tasks)}")

# Print all task titles and statuses
for task in tasks:
    print(f"  {task['title']} (ID: {task['id'][:8]}...) - Status: {task['status']} - Recurring: {task.get('is_recurring', False)}")