#!/usr/bin/env python3
"""
Editor functionality for interactive mode
"""

import click
import tempfile
import os
import subprocess
from typing import Optional
from gtasks_cli.models.task import Task
from gtasks_cli.utils.logger import setup_logger

logger = setup_logger(__name__)


def edit_task_in_editor(task: Task, task_manager) -> Optional[Task]:
    """Edit a task in an external editor.
    
    Args:
        task: The task to edit
        task_manager: The task manager instance
        
    Returns:
        Updated task if successful, None if cancelled or failed
    """
    # Create a temporary file with task content
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as temp_file:
        # Write task content to the temporary file
        temp_file.write(f"# Editing Task: {task.title}\n\n")
        temp_file.write("## Instructions\n")
        temp_file.write("# - Modify the title after the 'Title:' marker\n")
        temp_file.write("# - Modify the description after the 'Description:' marker\n")
        temp_file.write("# - Lines starting with '#' are comments and will be ignored\n")
        temp_file.write("# - Save and exit the editor to apply changes\n")
        temp_file.write("# - Close the editor without saving to cancel\n\n")
        temp_file.write(f"Title: {task.title}\n\n")
        temp_file.write("Description:\n")
        
        # Combine description and notes for the editor content
        editor_content = ""
        if task.description:
            editor_content += task.description
        if task.notes:
            if editor_content:
                editor_content += "\n"
            editor_content += task.notes
            
        if editor_content:
            # Add the content with proper indentation
            for line in editor_content.split('\n'):
                temp_file.write(f"{line}\n")
        temp_file.flush()
        
        # Get editor from environment or use default
        editor = os.environ.get('EDITOR', 'vim')
        
        try:
            # Open the file in the editor
            result = subprocess.run([editor, temp_file.name])
            
            # If editor was closed successfully, read the updated content
            if result.returncode == 0:
                with open(temp_file.name, 'r') as updated_file:
                    content = updated_file.read()
                
                # Parse the updated content
                lines = content.split('\n')
                title = task.title  # Default to original title
                description_lines = []
                in_description = False
                
                for line in lines:
                    # Skip comment lines
                    if line.startswith('#'):
                        continue
                    
                    # Check for title line
                    if line.startswith('Title:'):
                        title = line[6:].strip()  # Remove 'Title:' prefix
                    # Check for description section
                    elif line == 'Description:':
                        in_description = True
                    elif in_description:
                        # Collect description lines
                        description_lines.append(line)
                
                # Clean up description (remove trailing empty lines)
                while description_lines and not description_lines[-1].strip():
                    description_lines.pop()
                
                description = '\n'.join(description_lines) if description_lines else None
                
                # Update the task
                update_result = task_manager.update_task(
                    task.id, 
                    title=title, 
                    description=description
                )
                
                if update_result:
                    # If update was successful, retrieve and return the updated task
                    updated_tasks = task_manager.list_tasks()
                    for updated_task in updated_tasks:
                        if updated_task.id == task.id:
                            return updated_task
                    # If we can't find the task, return None
                    return None
                else:
                    # Update failed
                    return None
            else:
                # Editor was not closed successfully (e.g., killed)
                return None
                
        except Exception as e:
            logger.error(f"Error editing task in editor: {e}")
            return None
        finally:
            # Clean up the temporary file
            try:
                os.unlink(temp_file.name)
            except Exception as e:
                logger.warning(f"Failed to clean up temporary file: {e}")