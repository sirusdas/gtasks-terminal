#!/usr/bin/env python3

from gtasks_cli.core.task_manager import TaskManager

def test_recurring_task():
    task_manager = TaskManager()
    task = task_manager.create_task(
        title="Daily Exercise",
        description="Do 30 minutes of exercise",
        recurrence_rule="daily"
    )
    print(f"Created task: {task.title} with ID: {task.id}")

if __name__ == "__main__":
    test_recurring_task()