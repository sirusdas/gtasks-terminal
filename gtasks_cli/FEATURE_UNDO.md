# Undo Feature Documentation

## Overview
The Undo feature allows you to revert the most recent changes made to tasks in the interactive mode. It tracks operations that modify tasks and provides a way to restore the previous state.

## Usage

To undo the last operation, simply type `undo` in the interactive prompt.

```bash
Enter command: undo
```

## Supported Commands

The following commands support undo:

| Command | What is Undone |
| :--- | :--- |
| `update` | Restores the original title and description of the task. |
| `update-tags` | Restores the original tags (notes) of the task(s). |
| `update-status` | Restores the original status, due date, and completion time for all affected tasks. |
| `delete` | Restores the deleted task (sets status back to previous state). |
| `done` | Restores the task status to pending (or previous state). |
| `add` | Deletes the newly created task. |

## How it Works

1.  **Undo Manager**: A dedicated `UndoManager` module tracks the history of operations.
2.  **State Capture**: Before performing any modification, the current state of the task(s) is captured.
3.  **Undo Operation**: An undo function is registered that knows how to restore the captured state.
4.  **Execution**: When you run `undo`, the most recent undo function is executed, reverting the changes in the database and updating the in-memory task list where possible.

## Limitations

-   Undo history is stored in memory and is lost when you exit the interactive mode.
-   Undo operations are sequential (LIFO - Last In, First Out).
-   For some operations like `delete` or `add`, you might need to refresh the task list (`list` command) to see the changes reflected correctly in the current view if the automatic update doesn't cover it.
