#!/usr/bin/env python3
"""
Test script to verify tag filtering functionality in reports.
"""

import sys
import os
import uuid
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'gtasks_cli/src'))

from gtasks_cli.models.task import Task, TaskStatus, Priority
from gtasks_cli.utils.tag_extractor import extract_tags_from_task, task_has_any_tag, task_has_all_tags


def test_tag_extraction():
    """Test tag extraction from tasks."""
    print("Testing tag extraction...")
    
    # Create test tasks with tags in different fields
    task1 = Task(
        id=str(uuid.uuid4()),
        title="Complete project [work] [urgent]",
        description="Finish the quarterly report [finance]",
        notes="Meeting with team [meeting]",
        tags=["existing_tag"],
        priority=Priority.MEDIUM,
        tasklist_id="default"
    )
    
    task2 = Task(
        id=str(uuid.uuid4()),
        title="Buy groceries [personal]",
        description="Milk, eggs, bread",
        notes="Don't forget the [shopping]",
        priority=Priority.MEDIUM,
        tasklist_id="default"
    )
    
    task3 = Task(
        id=str(uuid.uuid4()),
        title="Plan vacation",
        description="Research destinations [travel] [leisure]",
        notes="Budget planning [finance]",
        priority=Priority.MEDIUM,
        tasklist_id="default"
    )
    
    tasks = [task1, task2, task3]
    
    for i, task in enumerate(tasks, 1):
        print(f"\nTask {i}: {task.title}")
        print(f"  Description: {task.description}")
        print(f"  Notes: {task.notes}")
        print(f"  Existing tags: {task.tags}")
        
        extracted_tags = extract_tags_from_task(task)
        print(f"  Extracted tags: {extracted_tags}")
        
        # Test tag filtering
        print(f"  Has any of ['work', 'urgent']: {task_has_any_tag(task, ['work', 'urgent'])}")
        print(f"  Has all of ['work', 'urgent']: {task_has_all_tags(task, ['work', 'urgent'])}")
        print(f"  Has any of ['personal', 'shopping']: {task_has_any_tag(task, ['personal', 'shopping'])}")
        print(f"  Has all of ['personal', 'shopping']: {task_has_all_tags(task, ['personal', 'shopping'])}")


if __name__ == "__main__":
    test_tag_extraction()