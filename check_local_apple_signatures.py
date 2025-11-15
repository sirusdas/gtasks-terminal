#!/usr/bin/env python3

import sys
import os
import sqlite3
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'gtasks_cli', 'src'))

from gtasks_cli.utils.task_deduplication import create_task_signature

def check_local_apple_signatures():
    """Check the signatures of local apple tasks."""
    # Connect to the local database
    db_path = "/Users/int/.gtasks/personal/tasks.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all apple tasks
    cursor.execute("SELECT * FROM tasks WHERE title = 'apple'")
    rows = cursor.fetchall()
    
    print(f"Found {len(rows)} local apple tasks")
    
    # Get column names
    column_names = [description[0] for description in cursor.description]
    print("Column names:", column_names)
    
    for i, row in enumerate(rows):
        print(f"\nLocal apple task {i+1}:")
        task_dict = dict(zip(column_names, row))
        for key, value in task_dict.items():
            print(f"  {key}: {value}")
        
        # Create signature
        signature = create_task_signature(
            title=task_dict['title'] or "",
            description=task_dict['description'] or "",
            due_date=task_dict['due'],
            status=task_dict['status']
        )
        print(f"  Signature: {signature}")
    
    conn.close()

if __name__ == "__main__":
    check_local_apple_signatures()