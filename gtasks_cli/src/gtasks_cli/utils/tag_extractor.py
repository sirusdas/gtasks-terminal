"""
Tag extraction utilities for extracting tags from task titles and descriptions.
"""

import re
from typing import List
from gtasks_cli.models.task import Task


def _is_valid_tag(tag: str) -> bool:
    """Validate if a string is a clean tag rather than JSON, code, or link."""
    if not tag or not isinstance(tag, str):
        return False
    t = tag.strip()
    if not (1 <= len(t) <= 40):
        return False
    if any(c in t for c in '{}"\':,\r\n\t'):
        return False
    return True


def extract_tags_from_text(text: str) -> List[str]:
    """
    Extract tags from text. Tags are identified as text within square brackets.
    
    Args:
        text: Text to extract tags from
        
    Returns:
        List of extracted tags
    """
    if not text:
        return []
    
    # Pattern to match text within square brackets (ignoring markdown links [text](...))
    pattern = r'\[([^\]\r\n]+)\](?!\()'
    matches = re.findall(pattern, text)
    return [m.strip() for m in matches if _is_valid_tag(m)]


def remove_tags_from_text(text: str) -> str:
    """
    Remove tags (text within square brackets) from text.
    
    Args:
        text: Text to remove tags from
        
    Returns:
        Text with tags removed
    """
    if not text:
        return ""
    
    # Only remove valid tags, not JSON arrays or markdown links
    pattern = r'\[([^\]\r\n]+)\](?!\()'
    return re.sub(pattern, lambda m: '' if _is_valid_tag(m.group(1)) else m.group(0), text).strip()


def extract_tags_from_task(task: Task) -> List[str]:
    """
    Extract all tags from a task (both title and description).
    
    Args:
        task: Task to extract tags from
        
    Returns:
        List of all extracted tags
    """
    tags = []
    
    # Extract tags from title
    if task.title:
        tags.extend(extract_tags_from_text(task.title))
    
    # Extract tags from description
    if task.description:
        tags.extend(extract_tags_from_text(task.description))
    
    # Extract tags from notes
    if task.notes:
        tags.extend(extract_tags_from_text(task.notes))
    
    # Add existing task tags
    if task.tags:
        tags.extend(task.tags)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_tags = []
    for tag in tags:
        if tag not in seen:
            seen.add(tag)
            unique_tags.append(tag)
    
    return unique_tags


def task_has_any_tag(task: Task, tags: List[str]) -> bool:
    """
    Check if a task has any of the specified tags.
    
    Args:
        task: Task to check
        tags: List of tags to look for
        
    Returns:
        True if task has any of the specified tags, False otherwise
    """
    task_tags = extract_tags_from_task(task)
    task_tag_set = set(tag.lower() for tag in task_tags)
    search_tag_set = set(tag.lower() for tag in tags)
    return bool(task_tag_set & search_tag_set)


def task_has_all_tags(task: Task, tags: List[str]) -> bool:
    """
    Check if a task has all of the specified tags.
    
    Args:
        task: Task to check
        tags: List of tags to look for
        
    Returns:
        True if task has all of the specified tags, False otherwise
    """
    task_tags = extract_tags_from_task(task)
    task_tag_set = set(tag.lower() for tag in task_tags)
    search_tag_set = set(tag.lower() for tag in tags)
    return search_tag_set.issubset(task_tag_set)