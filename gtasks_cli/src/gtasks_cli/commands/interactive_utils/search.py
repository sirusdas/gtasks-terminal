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

def _task_matches_term(task: Task, term_lower: str, exact: bool = False) -> bool:
    """Helper to check if task fields or spaces match a search term."""
    title_lower = (task.title or "").lower()
    desc_lower = (task.description or "").lower()
    notes_lower = (task.notes or "").lower()

    from gtasks_cli.utils.space_extractor import extract_spaces_from_text
    spaces = task.spaces or extract_spaces_from_text(task.notes or task.description or "")
    space_terms = []
    for sp_name, sp_subs in spaces.items():
        space_terms.append(sp_name.lower())
        for sub in sp_subs:
            space_terms.append(sub.lower())
            space_terms.append(f"{sp_name.lower()}:{sub.lower()}")

    if exact:
        if exact and (term_lower == title_lower or term_lower == desc_lower or term_lower == notes_lower):
            return True
        if term_lower in space_terms:
            return True
        return False
    else:
        if term_lower in title_lower or term_lower in desc_lower or term_lower in notes_lower:
            return True
        if any(term_lower in st for st in space_terms):
            return True
        return False


def apply_search_filter(tasks: List[Task], search_filter: str) -> List[Task]:
    """Apply search filter with support for exclusion, exact matching, and spaces."""
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
                if exclude_term and _task_matches_term(task, exclude_term, exact=False):
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

                search_matches = bool(search_part and _task_matches_term(task, search_part.lower(), exact=False))
                exclude_matches = bool(exclude_part and _task_matches_term(task, exclude_part.lower(), exact=False))

                if search_matches and not exclude_matches:
                    include_task = True
                    break

            elif term.startswith('--em:'):
                # Exact match
                exact_term = term[5:].strip().lower()
                if exact_term and _task_matches_term(task, exact_term, exact=True):
                    include_task = True
                    break

            elif not term.startswith('--ex:'):
                # Regular substring search
                term_lower = term.lower()
                if _task_matches_term(task, term_lower, exact=False):
                    include_task = True
                    break

        if include_task:
            filtered_tasks.append(task)

    return filtered_tasks


def apply_space_filter(tasks: List[Task], space_filter: str, subspace_filter: str = None) -> List[Task]:
    """Apply space and optional subspace filter to tasks."""
    if not space_filter:
        return tasks

    from gtasks_cli.utils.space_extractor import extract_spaces_from_text

    target_space = space_filter.strip().lower()
    target_sub = subspace_filter.strip().lower() if subspace_filter else None

    matched = []
    for task in tasks:
        spaces = task.spaces or extract_spaces_from_text(task.notes or task.description or "")
        matching_key = next((k for k in spaces.keys() if k.lower() == target_space), None)
        if matching_key:
            if target_sub:
                subs = [s.lower() for s in spaces[matching_key]]
                if target_sub in subs:
                    matched.append(task)
            else:
                matched.append(task)
    return matched
