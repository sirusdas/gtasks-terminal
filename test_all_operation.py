#!/usr/bin/env python3
"""
Test script for the ALL operation in update-status command
"""

import sys
import os

# Add the src directory to the path so we can import the modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'gtasks_cli/src'))

from gtasks_cli.commands.interactive_utils.bulk_update_commands import _parse_bulk_update_command


class MockTaskState:
    def __init__(self, num_tasks=5):
        self.tasks = [f"task_{i}" for i in range(1, num_tasks + 1)]


def test_parse_all_operations():
    """Test parsing of ALL operations"""
    print("Testing ALL operation parsing...")
    
    # Test ALL[C] - mark all as completed
    task_state = MockTaskState(3)
    command = "ALL[C]"
    try:
        result = _parse_bulk_update_command(command, task_state)
        print(f"✓ ALL[C] parsed successfully: {result}")
        assert result[0][0] == "completed"
        assert result[0][1]["task_numbers"] == [1, 2, 3]
    except Exception as e:
        print(f"✗ Failed to parse ALL[C]: {e}")
        
    # Test ALL[DEL] - mark all as deleted
    command = "ALL[DEL]"
    try:
        result = _parse_bulk_update_command(command, task_state)
        print(f"✓ ALL[DEL] parsed successfully: {result}")
        assert result[0][0] == "delete"
        assert result[0][1]["task_numbers"] == [1, 2, 3]
    except Exception as e:
        print(f"✗ Failed to parse ALL[DEL]: {e}")
        
    # Test ALL[DUE:TODAY] - set all due today
    command = "ALL[DUE:TODAY]"
    try:
        result = _parse_bulk_update_command(command, task_state)
        print(f"✓ ALL[DUE:TODAY] parsed successfully: {result}")
        assert result[0][0] == "due_today"
        assert result[0][1]["task_numbers"] == [1, 2, 3]
    except Exception as e:
        print(f"✗ Failed to parse ALL[DUE:TODAY]: {e}")
        
    # Test ALL[DUE:26-11] - set all due on Nov 26
    command = "ALL[DUE:26-11]"
    try:
        result = _parse_bulk_update_command(command, task_state)
        print(f"✓ ALL[DUE:26-11] parsed successfully: {result}")
        assert result[0][0] == "due_on_all"
        assert result[0][1]["task_numbers"] == [1, 2, 3]
        assert result[0][1]["date"] == "26-11"
    except Exception as e:
        print(f"✗ Failed to parse ALL[DUE:26-11]: {e}")
        
    # Test ALL[DT] - set all due today (alternative syntax)
    command = "ALL[DT]"
    try:
        result = _parse_bulk_update_command(command, task_state)
        print(f"✓ ALL[DT] parsed successfully: {result}")
        assert result[0][0] == "due_today"
        assert result[0][1]["task_numbers"] == [1, 2, 3]
    except Exception as e:
        print(f"✗ Failed to parse ALL[DT]: {e}")
        
    # Test ALL[DT|09:00 PM] - set all due today at 9 PM
    command = "ALL[DT|09:00 PM]"
    try:
        result = _parse_bulk_update_command(command, task_state)
        print(f"✓ ALL[DT|09:00 PM] parsed successfully: {result}")
        assert result[0][0] == "due_today"
        assert result[0][1]["task_numbers"] == [1, 2, 3]
        assert result[0][1]["time"] == "09:00 PM"
    except Exception as e:
        print(f"✗ Failed to parse ALL[DT|09:00 PM]: {e}")

    print("All tests completed!")


if __name__ == "__main__":
    test_parse_all_operations()