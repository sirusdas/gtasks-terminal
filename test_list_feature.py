#!/usr/bin/env python3
"""
Test script for the new list selection feature in interactive mode.
This script demonstrates how to use the new 'gtasks interactive --list --list-names' command.
"""

def main():
    print("Testing the new list selection feature")
    print("=====================================")
    print()
    print("To test the new feature, run the following command:")
    print()
    print("  gtasks interactive -- list --list-names")
    print()
    print("This will display all task lists in a numbered, multi-column format.")
    print("You can then select a list by entering its number.")
    print()
    print("After selecting a list, all pending tasks in that list will be displayed,")
    print("and you can use the standard interactive mode commands like:")
    print("  view <number>        - View task details")
    print("  done <number>        - Mark task as completed") 
    print("  delete <number>      - Delete a task")
    print("  update <number>      - Update a task")
    print("  add                  - Add a new task")
    print("  search <query>       - Search tasks")
    print("  back                 - Go back to list selection")
    print("  quit/exit            - Exit interactive mode")
    print()


if __name__ == "__main__":
    main()