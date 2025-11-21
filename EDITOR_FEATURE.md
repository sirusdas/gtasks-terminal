# Editor Feature for Task Updates

This document describes the new editor feature that allows users to edit tasks using their preferred external text editor in the interactive mode.

## Overview

The editor feature enhances the task updating experience by allowing users to edit task titles and descriptions in their preferred external text editor rather than using interactive prompts. This is particularly useful for editing tasks with longer descriptions or when users prefer a full-featured text editor.

## Usage

To use the editor feature, use the `update` command with the `--editor` or `-e` flag:

```
update <task_number> [--editor|-e]
```

### Examples

```bash
# Update task number 3 with interactive prompts (original behavior)
update 3

# Update task number 3 with external editor
update 3 --editor
update 3 -e
```

## Editor Configuration

The editor feature uses the standard `EDITOR` environment variable to determine which editor to use. If this variable is not set, it defaults to `vim`.

### Setting the Editor

You can set your preferred editor by exporting the `EDITOR` environment variable:

```bash
# For vim
export EDITOR=vim

# For nano
export EDITOR=nano

# For emacs
export EDITOR=emacs

# For VS Code
export EDITOR="code -w"

# Add to your shell profile (e.g., ~/.bashrc, ~/.zshrc) to make it permanent
echo 'export EDITOR=vim' >> ~/.zshrc
```

Note: For GUI editors like VS Code, make sure to include the wait flag (e.g., `code -w`) so the command waits for the editor to close before proceeding.

## Editor Workflow

When you use the editor feature:

1. A temporary file is created with the current task content
2. The file is opened in your configured editor
3. You can modify the title and description
4. Save and exit the editor to apply changes
5. Close the editor without saving to cancel the operation
6. The temporary file is automatically cleaned up

### File Format

The temporary file has the following format:

```markdown
# Editing Task: [Current Task Title]

## Instructions
# - Modify the title after the 'Title:' marker
# - Modify the description after the 'Description:' marker
# - Lines starting with '#' are comments and will be ignored
# - Save and exit the editor to apply changes
# - Close the editor without saving to cancel

Title: [Current Task Title]

Description:
[Current Task Description]
```

## Supported Editors

The feature works with any text editor that can be invoked from the command line, including:

- vim/neovim
- nano
- emacs
- VS Code (`code -w`)
- Sublime Text (`subl -w`)
- Atom (`atom -w`)

## Error Handling

The editor feature includes proper error handling:

- If the editor is not found, a helpful error message is displayed
- If the editor process exits with an error, the operation is cancelled
- If there are issues updating the task, appropriate error messages are shown
- Temporary files are always cleaned up, even in error conditions

## Best Practices

1. **Choose the right editor**: Use a terminal-based editor like vim or nano for the best experience within the CLI
2. **Configure your EDITOR variable**: Set the `EDITOR` environment variable in your shell profile for consistent behavior
3. **Use for complex edits**: Reserve the editor feature for tasks with longer descriptions or complex formatting
4. **Stick with prompts for simple edits**: Use the interactive prompts for quick title changes

## Examples

### Editing with Vim

```bash
# Set vim as your editor
export EDITOR=vim

# Update task 5 using vim
update 5 --editor
```

In vim, you would:
1. Navigate to the title line and make changes
2. Navigate to the description section and modify as needed
3. Press `Esc` and type `:wq` to save and quit
4. The task will be updated with your changes

### Editing with VS Code

```bash
# Set VS Code as your editor (note the -w flag)
export EDITOR="code -w"

# Update task 10 using VS Code
update 10 --editor
```

In VS Code, you would:
1. Make your changes in the editor
2. Save the file (Ctrl+S or Cmd+S)
3. Close the editor window
4. The task will be updated with your changes

## Technical Implementation

The editor feature is implemented in the `_edit_task_in_editor` function in [interactive.py](file:///Users/int/Documents/workspace/projects/gtasks_automation/gtasks_cli/src/gtasks_cli/commands/interactive.py), which:

1. Creates a temporary file with the task content
2. Invokes the configured editor with the temporary file
3. Parses the updated content when the editor is closed
4. Updates the task using the task manager
5. Cleans up the temporary file

The implementation handles edge cases like:
- Editor process failures
- File system errors
- Parsing errors in the updated content
- Proper cleanup of temporary resources