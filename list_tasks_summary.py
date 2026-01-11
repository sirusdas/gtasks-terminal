import json
import os

backup_file = '/Users/int/Documents/workspace/projects/gtasks_automation/google_tasks_backup_20251106_063835.json'

with open(backup_file, 'r') as f:
    data = json.load(f)

print(f"Backup Timestamp: {data.get('backup_timestamp')}")
print("-" * 50)

for tasklist in data.get('tasklists', []):
    print(f"\nTask List: {tasklist.get('title')}")
    tasks = tasklist.get('tasks', [])
    pending = [t for t in tasks if t.get('status') == 'pending']
    completed = [t for t in tasks if t.get('status') == 'completed']
    
    print(f"  Pending Tasks ({len(pending)}):")
    for i, task in enumerate(pending[:20], 1):
        due = f" (Due: {task.get('due')})" if task.get('due') else ""
        print(f"    {i}. {task.get('title')}{due}")
    if len(pending) > 20:
        print(f"    ... and {len(pending) - 20} more")
        
    print(f"\n  Completed Tasks ({len(completed)}):")
    for i, task in enumerate(completed[:5], 1):
        print(f"    {i}. {task.get('title')}")
    if len(completed) > 5:
        print(f"    ... and {len(completed) - 5} more")
