from typing import List
from gtasks_cli.models.task import Task
from gtasks_cli.utils.tag_extractor import extract_tags_from_task

def apply_tag_filter(tasks: List[Task], tag_filter: str) -> List[Task]:
    """Apply tag filter with support for exclusion and exact matching."""
    if not tag_filter:
        return tasks

    # Split filter by '|' for OR logic
    filter_terms = [term.strip() for term in tag_filter.split('|')]

    # Check if we have any positive terms (not starting with --ex:)
    has_positive_terms = any(not term.startswith('--ex:') for term in filter_terms)

    filtered_tasks = []

    for task in tasks:
        task_tags = extract_tags_from_task(task)
        # Normalize task tags to lower case for comparison
        task_tags_lower = [t.lower() for t in task_tags]

        # If we only have exclusion terms, we include by default (unless excluded)
        # If we have positive terms, we exclude by default (must match a positive term)
        include_task = not has_positive_terms
        should_exclude = False

        # Check for exclusion terms
        for term in filter_terms:
            if term.startswith('--ex:'):
                exclude_term = term[5:].strip().lower()
                if exclude_term:
                    # Check if any task tag matches the exclude term (partial match)
                    if any(exclude_term in t for t in task_tags_lower):
                        should_exclude = True
                        break

        if should_exclude:
            continue

        # Check for inclusion terms
        for term in filter_terms:
            if '--ex:' in term and not term.startswith('--ex:'):
                # Embedded search-exclude
                parts = term.split('--ex:')
                search_part = parts[0].strip()
                exclude_part = parts[1].strip() if len(parts) > 1 else ""

                # Check search part
                search_matches = False
                if search_part:
                    search_part_lower = search_part.lower()
                    if any(search_part_lower in t for t in task_tags_lower):
                        search_matches = True

                # Check exclude part
                exclude_matches = False
                if exclude_part:
                    exclude_part_lower = exclude_part.lower()
                    if any(exclude_part_lower in t for t in task_tags_lower):
                        exclude_matches = True

                if search_matches and not exclude_matches:
                    include_task = True
                    break

            elif term.startswith('--em:'):
                # Exact match
                exact_term = term[5:].strip().lower()
                if exact_term:
                    if exact_term in task_tags_lower:
                        include_task = True
                        break

            elif not term.startswith('--ex:'):
                # Regular substring search
                term_lower = term.lower()
                if any(term_lower in t for t in task_tags_lower):
                    include_task = True
                    break

        if include_task:
            filtered_tasks.append(task)

    return filtered_tasks

def apply_search_filter(tasks: List[Task], search_filter: str) -> List[Task]:
    """Apply search filter with support for exclusion and exact matching."""
    if not search_filter:
        return tasks

    # Split search filter by '|' for OR logic
    search_terms = [term.strip() for term in search_filter.split('|')]

    # Check if we have any positive search terms (not starting with --ex:)
    has_positive_terms = any(not term.startswith('--ex:') for term in search_terms)

    filtered_tasks = []

    for task in tasks:
        # If we only have exclusion terms, we include by default (unless excluded)
        # If we have positive terms, we exclude by default (must match a positive term)
        include_task = not has_positive_terms
        should_exclude = False

        # Check for exclusion terms
        for term in search_terms:
            if term.startswith('--ex:'):
                exclude_term = term[5:].strip().lower()
                if exclude_term:
                    if (exclude_term in task.title.lower() or
                        (task.description and exclude_term in task.description.lower()) or
                        (task.notes and exclude_term in task.notes.lower())):
                        should_exclude = True
                        break

        if should_exclude:
            continue

        # Check for inclusion terms
        for term in search_terms:
            if '--ex:' in term and not term.startswith('--ex:'):
                # Embedded search-exclude
                parts = term.split('--ex:')
                search_part = parts[0].strip()
                exclude_part = parts[1].strip() if len(parts) > 1 else ""

                # Check search part
                search_matches = False
                if search_part:
                    search_part_lower = search_part.lower()
                    if (search_part_lower in task.title.lower() or
                        (task.description and search_part_lower in task.description.lower()) or
                        (task.notes and search_part_lower in task.notes.lower())):
                        search_matches = True

                # Check exclude part
                exclude_matches = False
                if exclude_part:
                    exclude_part_lower = exclude_part.lower()
                    if (exclude_part_lower in task.title.lower() or
                        (task.description and exclude_part_lower in task.description.lower()) or
                        (task.notes and exclude_part_lower in task.notes.lower())):
                        exclude_matches = True

                if search_matches and not exclude_matches:
                    include_task = True
                    break

            elif term.startswith('--em:'):
                # Exact match
                exact_term = term[5:].strip().lower()
                if exact_term:
                    if (exact_term == task.title.lower() or
                        (task.description and exact_term == task.description.lower()) or
                        (task.notes and exact_term == task.notes.lower())):
                        include_task = True
                        break

            elif not term.startswith('--ex:'):
                # Regular substring search
                term_lower = term.lower()
                if (term_lower in task.title.lower() or
                    (task.description and term_lower in task.description.lower()) or
                    (task.notes and term_lower in task.notes.lower())):
                    include_task = True
                    break

        if include_task:
            filtered_tasks.append(task)

    return filtered_tasks
