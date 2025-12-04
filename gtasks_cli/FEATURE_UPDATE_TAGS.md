# Update-Tags Feature Documentation

## Overview
The `update-tags` command allows you to bulk add or remove tags from tasks in interactive mode. Tags are stored in the notes section of tasks within square brackets, e.g., `[work]`, `[urgent]`, `[personal]`.

## Syntax

```bash
update-tags ADD[task_ids|tag1,tag2,...] DEL[task_ids|tag1,tag2,...]
update-tags ALL[ADD:tag1,tag2] ALL[DEL:tag1,tag2]
update-tags ADD[tag1,tag2] --all  # Legacy syntax
```

## Examples

### 1. Add a single tag to multiple tasks
```bash
update-tags ADD[1,2,3|work]
```
Adds `[work]` tag to tasks 1, 2, and 3.

### 2. Add multiple tags to multiple tasks
```bash
update-tags ADD[1,2|work,urgent]
```
Adds both `[work]` and `[urgent]` tags to tasks 1 and 2.

### 3. Remove multiple tags from a task
```bash
update-tags DEL[3|personal,old]
```
Removes `[personal]` and `[old]` tags from task 3.

### 4. Combined add and remove operations
```bash
update-tags ADD[1,2|work,sirus],DEL[3|personal,sirus]
```
- Adds `[work]` and `[sirus]` to tasks 1 and 2
- Removes `[personal]` and `[sirus]` from task 3

### 5. Add tags to all tasks (new ALL syntax)
```bash
update-tags ALL[ADD:urgent,sirus]
```
Adds `[urgent]` and `[sirus]` tags to all tasks in the current filtered list.

### 6. Remove tags from all tasks
```bash
update-tags ALL[DEL:old,done]
```
Removes `[old]` and `[done]` tags from all tasks.

### 7. Combined ALL operations
```bash
update-tags ALL[ADD:new,active],ALL[DEL:old,archived]
```
- Adds `[new]` and `[active]` to all tasks
- Removes `[old]` and `[archived]` from all tasks

### 8. Legacy --all flag (still supported)
```bash
update-tags ADD[urgent] --all
```
Adds `[urgent]` tag to all tasks in the current filtered list.

### 9. Mix regular and ALL operations
```bash
update-tags ADD[1,2|priority],ALL[ADD:reviewed]
```
- Adds `[priority]` to tasks 1 and 2
- Adds `[reviewed]` to all tasks

## Features

- ✅ **Multiple tags per operation** - Separate tags with commas
- ✅ **Multiple tasks per operation** - Separate task IDs with commas  
- ✅ **Multiple operations** - Combine ADD and DEL operations with commas
- ✅ **ALL syntax** - Use `ALL[ADD:tags]` or `ALL[DEL:tags]` for cleaner all-task operations
- ✅ **Typo tolerance** - Accepts dots instead of commas in task IDs (e.g., `1.2.3`)
- ✅ **Progress bar** - Visual feedback when updating multiple tasks
- ✅ **Smart spacing** - Automatically cleans up extra spaces when removing tags
- ✅ **Duplicate prevention** - Won't add a tag if it already exists

## Syntax Comparison

| Old Syntax | New ALL Syntax |
|------------|----------------|
| `update-tags ADD[work] --all` | `update-tags ALL[ADD:work]` |
| `update-tags ADD[work,urgent] --all` | `update-tags ALL[ADD:work,urgent]` |
| N/A | `update-tags ALL[DEL:old,done]` |
| N/A | `update-tags ALL[ADD:new],ALL[DEL:old]` |

## Notes

- Tags are stored in the `notes` field of tasks
- Tags must be enclosed in square brackets: `[tagname]`
- The command works in both main interactive mode and tag-filtered mode
- After updating tags, the task list is automatically refreshed
- The `--all` flag is still supported for backward compatibility
