#!/usr/bin/env python3

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from gtasks_cli.integrations.google_tasks_client import GoogleTasksClient

def main():
    client = GoogleTasksClient()
    # Try to connect first
    if client.connect():
        tasklists = client.list_tasklists()
        print("Task Lists:")
        for tasklist in tasklists:
            print(f"  - {tasklist.get('title', 'Untitled')} (ID: {tasklist.get('id')})")
    else:
        print("Failed to connect to Google Tasks API")

if __name__ == "__main__":
    main()