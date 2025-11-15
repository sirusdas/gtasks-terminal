#!/usr/bin/env python3

import sys
import os
import sqlite3
import hashlib
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'gtasks_cli', 'src'))

from gtasks_cli.utils.task_deduplication import create_task_signature

def debug_existing_signatures():
    """Debug what's in the existing_signatures set."""
    # Create signatures from tasks in temporary database
    temp_db_path = "/var/folders/nl/hb47k0yj22l1k5nhzk942rww0000gn/T/gtasks_sync_temp.db"
    
    # First create a temporary database for testing
    conn = sqlite3.connect(temp_db_path)
    cursor = conn.cursor()
    
    # Create table for Google Tasks
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS temp_google_tasks (
            id TEXT PRIMARY KEY,
            title TEXT,
            description TEXT,
            due TEXT,
            priority TEXT,
            status TEXT,
            project TEXT,
            tags TEXT,
            notes TEXT,
            dependencies TEXT,
            recurrence_rule TEXT,
            created_at TEXT,
            modified_at TEXT,
            tasklist_id TEXT,
            signature TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    
    # Now load Google Tasks into this database like we do in the sync process
    from gtasks_cli.integrations.google_tasks_client import GoogleTasksClient
    from gtasks_cli.integrations.google_auth import GoogleAuthManager
    
    client = GoogleTasksClient()
    auth_manager = GoogleAuthManager()
    service = auth_manager.get_service()
    
    if not service:
        print("Failed to connect to Google Tasks")
        return
    
    client.service = service
    
    if not client.connect():
        print("Failed to connect to Google Tasks")
        return
    
    # Load all Google Tasks into temporary database
    tasklists = client.list_tasklists()
    task_count = 0
    
    conn = sqlite3.connect(temp_db_path)
    cursor = conn.cursor()
    
    # Load tasks from each tasklist
    for tasklist in tasklists:
        tasklist_id = tasklist['id']
        tasklist_title = tasklist['title']
        
        print(f"Loading tasks from tasklist: {tasklist_title}")
        
        # Get all tasks from this tasklist
        tasks = client.list_tasks(
            tasklist_id=tasklist_id,
            show_completed=True,
            show_hidden=True,
            show_deleted=False
        )
        
        if not tasks:
            print(f"No tasks found in tasklist: {tasklist_title}")
            continue
        
        # Insert tasks into temporary database
        for task in tasks:
            # Create task signature for duplicate detection
            signature = create_task_signature(
                title=task.title or "",
                description=task.description or "",
                due_date=task.due,
                status=task.status
            )
            
            # Convert task to dictionary for database insertion
            task_dict = {
                'id': task.id,
                'title': task.title,
                'description': task.description,
                'due': task.due.isoformat() if task.due else None,
                'priority': task.priority.value if hasattr(task.priority, 'value') else str(task.priority),
                'status': task.status.value if hasattr(task.status, 'value') else str(task.status),
                'project': task.project,
                'tags': str(task.tags) if task.tags else None,
                'notes': task.notes,
                'dependencies': str(task.dependencies) if task.dependencies else None,
                'recurrence_rule': task.recurrence_rule,
                'created_at': task.created_at.isoformat() if task.created_at else None,
                'modified_at': task.modified_at.isoformat() if task.modified_at else None,
                'tasklist_id': tasklist_id,
                'signature': signature
            }
            
            # Insert task into database
            cursor.execute('''
                INSERT OR REPLACE INTO temp_google_tasks 
                (id, title, description, due, priority, status, project, tags, notes, 
                 dependencies, recurrence_rule, created_at, modified_at, tasklist_id, signature)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                task_dict['id'], task_dict['title'], task_dict['description'], task_dict['due'],
                task_dict['priority'], task_dict['status'], task_dict['project'], task_dict['tags'],
                task_dict['notes'], task_dict['dependencies'], task_dict['recurrence_rule'],
                task_dict['created_at'], task_dict['modified_at'], task_dict['tasklist_id'], task_dict['signature']
            ))
        
        task_count += len(tasks)
        print(f"Loaded {len(tasks)} tasks from tasklist: {tasklist_title}")
    
    # Commit all changes
    conn.commit()
    conn.close()
    
    print(f"Loaded {task_count} Google Tasks into temporary database")
    
    # Now get existing task signatures like we do in the sync method
    try:
        # Create signatures from tasks in temporary database
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT title, description, due, status FROM temp_google_tasks
        ''')
        
        existing_signatures = set()
        rows = cursor.fetchall()
        for row in rows:
            title = row[0] or ""
            description = row[1] or ""
            due_date = row[2] or ""
            status = row[3] or ""
            signature = create_task_signature(title, description, due_date, status)
            existing_signatures.add(signature)
        
        conn.close()
        print(f"Retrieved {len(existing_signatures)} existing task signatures from temporary database")
        
        # Check if apple signature is in existing signatures
        apple_signature = create_task_signature("apple", "", "", "pending")
        print(f"Apple task signature: {apple_signature}")
        print(f"Is apple signature in existing signatures? {apple_signature in existing_signatures}")
        
        # Print first 10 signatures for debugging
        print("\nFirst 10 signatures:")
        for i, sig in enumerate(list(existing_signatures)[:10]):
            print(f"  {i+1}. {sig}")
            
    except Exception as e:
        print(f"Failed to retrieve existing task signatures from temporary database: {e}")
    
    # Clean up
    os.unlink(temp_db_path)

if __name__ == "__main__":
    debug_existing_signatures()