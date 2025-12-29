from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import re
from gtasks_cli.models.task import Task, TaskStatus
from gtasks_cli.reports.base_report import BaseReport
from gtasks_cli.utils.tag_extractor import extract_tags_from_task

class CustomFilteredReport(BaseReport):
    """
    Custom Filtered Report (rp10)
    Generates a report based on dynamic filters for dates, tags, and ordering.
    """

    def __init__(self):
        super().__init__(
            name="Custom Filtered Report",
            description="Generates a report with custom filters for dates, tags, and ordering."
        )

    def generate(self, tasks: List[Task], **kwargs) -> Dict[str, Any]:
        """
        Generate the report data.
        
        Args:
            tasks: List of tasks to filter
            **kwargs: 
                filter_str: Date filter string (e.g., "this_week:created_at")
                tags_filter: Tags filter string (e.g., "--em:***|--ex:cr")
                order_by: Field to order by with optional direction
                         (e.g., "modified_at:desc", "created_at:asc", "-modified_at")
                
        Returns:
            Dict containing report data
        """
        filter_str = kwargs.get('filter_str')
        tags_filter = kwargs.get('tags_filter')
        order_by = kwargs.get('order_by')
        output_tags = kwargs.get('output_tags')
        output_lists = kwargs.get('output_lists')
        output_tasks = kwargs.get('output_tasks')

        filtered_tasks = tasks
        
        # 1. Apply Date Filter
        if filter_str:
            filtered_tasks = self._apply_date_filter(filtered_tasks, filter_str)
            
        # 2. Apply Tags Filter
        if tags_filter:
            filtered_tasks = self._apply_tags_filter(filtered_tasks, tags_filter)
            
        # 3. Apply Ordering
        if order_by:
            filtered_tasks = self._apply_ordering(filtered_tasks, order_by)
            
        # 4. Generate Title
        title = self._generate_title(filter_str, tags_filter)
        
        # 5. Group Tasks
        # 5. Group Tasks
        grouped_tasks = self._group_tasks(filtered_tasks, output_tags, output_lists, output_tasks)
        
        return {
            'title': title,
            'generated_at': datetime.now().isoformat(),
            'total_tasks': len(filtered_tasks),
            'grouped_tasks': grouped_tasks,
            'tasks': [t.dict() for t in filtered_tasks] # For raw access if needed
        }

    def _apply_date_filter(self, tasks: List[Task], filter_str: str) -> List[Task]:
        """
        Apply date filtering logic.
        Format: period:field (e.g., "this_week:created_at", "past2weeks:modified_at")
        """
        try:
            period, field = filter_str.split(':')
        except ValueError:
            return tasks

        # Create timezone-aware datetime objects to match the task datetimes
        now = datetime.now().astimezone()
        start_date = None
        end_date = now

        if period == 'this_week':
            start_date = now - timedelta(days=now.weekday())
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period.startswith('past') and 'weeks' in period:
            # Extract number of weeks
            match = re.search(r'past(\d+)weeks', period)
            if match:
                weeks = int(match.group(1))
                start_date = now - timedelta(weeks=weeks)
            else:
                # Default to 2 weeks if parsing fails but matches pattern
                start_date = now - timedelta(weeks=2)
        
        if not start_date:
            return tasks

        filtered = []
        for task in tasks:
            task_date = getattr(task, field, None)
            if isinstance(task_date, str):
                try:
                    task_date = datetime.fromisoformat(task_date)
                except ValueError:
                    continue
            
            if task_date:
                # Ensure both dates use the same timezone awareness for comparison
                if task_date.tzinfo is None and start_date.tzinfo is not None:
                    # Make start/end dates naive to match task_date
                    start_date = start_date.replace(tzinfo=None)
                    end_date = end_date.replace(tzinfo=None)
                elif task_date.tzinfo is not None and start_date.tzinfo is None:
                    # Make start/end dates aware to match task_date
                    start_date = start_date.astimezone()
                    end_date = end_date.astimezone()
            
            if task_date and task_date >= start_date and task_date <= end_date:
                filtered.append(task)
                
        return filtered

    def _apply_tags_filter(self, tasks: List[Task], tags_filter: str) -> List[Task]:
        """
        Apply tag filtering logic.
        Flexible format supports:
        - "tag1" - include tasks with tag1
        - "tag1,tag2" - include tasks with tag1 OR tag2
        - "tag1|ex:tag2" - include tag1 but exclude tag2
        - "--em:tag1|--ex:tag2" - explicit include/exclude (legacy)
        """
        # Parse filter string
        include_tags = []
        exclude_tags = []
        
        # Remove quotes if present
        tags_filter = tags_filter.strip('"\'')
        
        parts = tags_filter.split('|')
        for part in parts:
            part = part.strip()
            
            # Check for explicit prefixes
            if part.startswith('--em:'):
                tags = part[5:].replace('[', '').replace(']', '').split(',')
                include_tags.extend([t.strip() for t in tags if t.strip()])
            elif part.startswith('em:'):
                tags = part[3:].replace('[', '').replace(']', '').split(',')
                include_tags.extend([t.strip() for t in tags if t.strip()])
            elif part.startswith('--ex:'):
                tags = part[5:].replace('[', '').replace(']', '').split(',')
                exclude_tags.extend([t.strip() for t in tags if t.strip()])
            elif part.startswith('ex:'):
                tags = part[3:].replace('[', '').replace(']', '').split(',')
                exclude_tags.extend([t.strip() for t in tags if t.strip()])
            else:
                # No prefix - treat as include tags
                tags = part.replace('[', '').replace(']', '').split(',')
                include_tags.extend([t.strip() for t in tags if t.strip()])

        filtered = []
        for task in tasks:
            task_tags = set(t.lower() for t in extract_tags_from_task(task))
            
            # Check exclusions first
            if any(tag.lower() in task_tags for tag in exclude_tags):
                continue
                
            # Check inclusions (if any specified)
            if include_tags:
                if not any(tag.lower() in task_tags for tag in include_tags):
                    continue
            
            filtered.append(task)
            
        return filtered

    def _apply_ordering(self, tasks: List[Task], order_by: str) -> List[Task]:
        """Order tasks by a field with optional direction.
        
        Supports:
        - '-field_name' for descending (e.g., '-modified_at')
        - 'field_name:desc' for descending (e.g., 'modified_at:desc')
        - 'field_name:asc' for ascending (e.g., 'modified_at:asc')
        - 'field_name' for ascending (default)
        """
        if not order_by:
            return tasks
            
        reverse = False
        
        # Check for :desc or :asc suffix
        if ':' in order_by:
            field, direction = order_by.rsplit(':', 1)
            direction = direction.lower().strip()
            if direction == 'desc':
                reverse = True
            elif direction == 'asc':
                reverse = False
            order_by = field.strip()
        # Check for - prefix (legacy support)
        elif order_by.startswith('-'):
            reverse = True
            order_by = order_by[1:]
            
        def get_sort_key(task):
            val = getattr(task, order_by, None)
            if val is None:
                return datetime.min if 'date' in order_by or 'at' in order_by else ""
            
            # Handle datetime string parsing for consistent timezone handling
            if isinstance(val, str) and ('date' in order_by or 'at' in order_by):
                try:
                    val = datetime.fromisoformat(val)
                except ValueError:
                    pass
            
            # Ensure consistent timezone handling for datetime comparisons
            if isinstance(val, datetime):
                # If datetime is naive, make it aware
                if val.tzinfo is None:
                    val = val.astimezone()
            
            return val
            
        return sorted(tasks, key=get_sort_key, reverse=reverse)

    def _generate_title(self, filter_str: str, tags_filter: str) -> str:
        """Generate a dynamic title based on filters."""
        title_parts = ["TASKS"]
        
        # Add tag info
        if tags_filter:
            include_tags = []
            exclude_tags = []
            tags_filter = tags_filter.strip('"\'')
            parts = tags_filter.split('|')
            for part in parts:
                if part.startswith('--em:'):
                    tags = part[5:].replace('[', '').replace(']', '').split(',')
                    include_tags.extend([t.strip() for t in tags if t.strip()])
                elif part.startswith('--ex:'):
                    tags = part[5:].replace('[', '').replace(']', '').split(',')
                    exclude_tags.extend([t.strip() for t in tags if t.strip()])
            
            if include_tags:
                title_parts.append(f"WITH TAGS {', '.join(include_tags)}")
            
            if exclude_tags:
                title_parts.append(f"EXCLUDING {', '.join(exclude_tags)}")

        # Add date info
        if filter_str:
            period, field = filter_str.split(':')
            field_readable = field.replace('_', ' ').upper()
            if period == 'this_week':
                title_parts.append(f"{field_readable} THIS WEEK")
            elif 'past' in period and 'weeks' in period:
                match = re.search(r'past(\d+)weeks', period)
                weeks = match.group(1) if match else "2"
                title_parts.append(f"{field_readable} IN LAST {weeks} WEEKS")

        return " ".join(title_parts).upper()

    def _group_tasks(self, tasks: List[Task], output_tags: str = None, output_lists: str = None, output_tasks: str = None) -> Dict[str, Any]:
        """Group tasks by List and then by Tags."""
        
        # Parse output tags filter
        include_tags = []
        exclude_tags = []

        group_tags = {} # Map group name to list of patterns
        tag_group_order = {} # Map group name to sort order (int)
        
        def parse_group_content(content, target_dict, order_dict):
            if '[' in content:
                # Matches patterns like: 1[p1,p2] or [p1,p2]
                # Regex to capture optional number and content inside brackets
                # We need to handle multiple groups separated by comma, e.g. 1[a,b],2[c]
                # But the split logic might be tricky if commas are inside brackets.
                # Let's use regex to find all occurrences of (optional digit) + [...]
                matches = re.findall(r'(\d*)\[(.*?)\]', content)
                for order_str, m in matches:
                    patterns = [p.strip().lower() for p in m.split(',') if p.strip()]
                    if patterns:
                        g_name = ", ".join(patterns)
                        target_dict[g_name] = patterns
                        if order_str:
                            order_dict[g_name] = int(order_str)
            else:
                groups = content.split(',')
                for g in groups:
                    g = g.strip().lower()
                    if g:
                        target_dict[g] = [g]

        if output_tags:
            output_tags = output_tags.strip('"\'')
            parts = output_tags.split('|')
            for part in parts:
                part = part.strip()
                if part.startswith('--em:'):
                    tags = part[5:].split(',')
                    include_tags.extend([t.strip().lower() for t in tags if t.strip()])
                elif part.startswith('em:'):
                    tags = part[3:].split(',')
                    include_tags.extend([t.strip().lower() for t in tags if t.strip()])
                elif part.startswith('--ex:'):
                    tags = part[5:].split(',')
                    exclude_tags.extend([t.strip().lower() for t in tags if t.strip()])
                elif part.startswith('ex:'):
                    tags = part[3:].split(',')
                    exclude_tags.extend([t.strip().lower() for t in tags if t.strip()])
                elif part.startswith('--group:'):
                    parse_group_content(part[8:], group_tags, tag_group_order)
                elif part.startswith('group:'):
                    parse_group_content(part[6:], group_tags, tag_group_order)
                else:
                    # No prefix - treat as include
                    tags = part.split(',')
                    include_tags.extend([t.strip().lower() for t in tags if t.strip()])

        # Parse output lists filter
        include_lists = []
        exclude_lists = []
        if output_lists:
            output_lists = output_lists.strip('"\'')
            parts = output_lists.split('|')
            for part in parts:
                part = part.strip()
                if part.startswith('--em:'):
                    lists = part[5:].split(',')
                    include_lists.extend([l.strip().lower() for l in lists if l.strip()])
                elif part.startswith('em:'):
                    lists = part[3:].split(',')
                    include_lists.extend([l.strip().lower() for l in lists if l.strip()])
                elif part.startswith('--ex:'):
                    lists = part[5:].split(',')
                    exclude_lists.extend([l.strip().lower() for l in lists if l.strip()])
                elif part.startswith('ex:'):
                    lists = part[3:].split(',')
                    exclude_lists.extend([l.strip().lower() for l in lists if l.strip()])
                else:
                    # No prefix - treat as include
                    lists = part.split(',')
                    include_lists.extend([l.strip().lower() for l in lists if l.strip()])

        # Parse output tasks filter
        include_tasks = []
        exclude_tasks = []
        group_tasks = {} # Map group name to list of patterns
        task_group_order = {} # Map group name to sort order
        
        if output_tasks:
            output_tasks = output_tasks.strip('"\'')
            parts = output_tasks.split('|')
            for part in parts:
                part = part.strip()
                if part.startswith('--em:'):
                    ts = part[5:].split(',')
                    include_tasks.extend([t.strip().lower() for t in ts if t.strip()])
                elif part.startswith('em:'):
                    ts = part[3:].split(',')
                    include_tasks.extend([t.strip().lower() for t in ts if t.strip()])
                elif part.startswith('--ex:'):
                    ts = part[5:].split(',')
                    exclude_tasks.extend([t.strip().lower() for t in ts if t.strip()])
                elif part.startswith('ex:'):
                    ts = part[3:].split(',')
                    exclude_tasks.extend([t.strip().lower() for t in ts if t.strip()])
                elif part.startswith('--group:'):
                    parse_group_content(part[8:], group_tasks, task_group_order)
                elif part.startswith('group:'):
                    parse_group_content(part[6:], group_tasks, task_group_order)
                else:
                    # No prefix - treat as include
                    ts = part.split(',')
                    include_tasks.extend([t.strip().lower() for t in ts if t.strip()])

        by_list = {}
        
        # Additional structure for task groups
        by_task_group = {}
        for g_name in group_tasks:
            by_task_group[g_name] = []

        for task in tasks:
            # Apply task filtering (substring match)
            task_title_lower = task.title.lower() if task.title else ""
            
            if exclude_tasks:
                if any(ex in task_title_lower for ex in exclude_tasks):
                    continue
            
            # Check for task grouping
            for g_name, patterns in group_tasks.items():
                for pattern in patterns:
                    if pattern in task_title_lower:
                        by_task_group[g_name].append(task)
                        break # Avoid adding same task multiple times to same group if it matches multiple patterns
            
            if include_tasks:
                if not any(inc in task_title_lower for inc in include_tasks):
                    # Check if it matched any group
                    matched_any_group = False
                    for g_name, patterns in group_tasks.items():
                        for pattern in patterns:
                            if pattern in task_title_lower:
                                matched_any_group = True
                                break
                        if matched_any_group: break
                    
                    if not matched_any_group:
                         continue

            list_name = task.list_title or "Unknown List"
            
            # Apply list filtering
            list_name_lower = list_name.lower()
            if exclude_lists and list_name_lower in exclude_lists:
                continue
            if include_lists and list_name_lower not in include_lists:
                continue
                
            if list_name not in by_list:
                by_list[list_name] = []
            by_list[list_name].append(task)
            
        result = {}
        for list_name, list_tasks in by_list.items():
            result[list_name] = {
                "tasks": [t.dict() for t in list_tasks],
                "by_tag": {}
            }
            
            for task in list_tasks:
                tags = extract_tags_from_task(task)
                
                if not tags:
                    # Only add "No Tag" if we are not strictly filtering for specific tags
                    if not include_tags and not group_tags:
                        tags = ["No Tag"]
                    else:
                        continue
                
                for tag in tags:
                    tag_lower = tag.lower()
                    
                    # Apply output tag filters
                    if exclude_tags and tag_lower in exclude_tags:
                        continue
                    
                    # Check for grouping first
                    matched_group = False
                    for g_name, patterns in group_tags.items():
                        for pattern in patterns:
                            if pattern in tag_lower:
                                if g_name not in result[list_name]["by_tag"]:
                                    result[list_name]["by_tag"][g_name] = []
                                result[list_name]["by_tag"][g_name].append(task.dict())
                                matched_group = True
                                break # Matched this group, move to next group check
                    
                    if matched_group:
                        pass
                    else:
                        if include_tags and tag_lower not in include_tags:
                            continue
                        
                        # If output_tags is NOT provided, we should probably stick to the old behavior (exclude "my").
                        if not output_tags and tag_lower == "my":
                            continue

                        if tag not in result[list_name]["by_tag"]:
                            result[list_name]["by_tag"][tag] = []
                        result[list_name]["by_tag"][tag].append(task.dict())
        
        # Add task groups to result
        result['__task_groups__'] = {g: [t.dict() for t in ts] for g, ts in by_task_group.items()}
        result['__tag_group_order__'] = tag_group_order
        result['__task_group_order__'] = task_group_order
                    
        return result

    def export(self, data: Dict[str, Any], format: str = 'txt', color: bool = False) -> str:
        """Export the report to text."""
        if format != 'txt':
            return "Only TXT export is supported for this report."
            
        # ANSI Color Codes
        HEADER = '\033[95m'
        BLUE = '\033[94m'
        CYAN = '\033[96m'
        GREEN = '\033[92m'
        WARNING = '\033[93m'
        FAIL = '\033[91m'
        ENDC = '\033[0m'
        BOLD = '\033[1m'
        DIM = '\033[2m'

        def c(text, code):
            return f"{code}{text}{ENDC}" if color else text

        lines = []
        lines.append(c("=" * 60, BOLD))
        lines.append(c(data['title'], HEADER + BOLD))
        lines.append(c("=" * 60, BOLD))
        lines.append(f"Generated at: {data['generated_at']}")
        lines.append(f"Total Tasks: {data['total_tasks']}")
        lines.append(c("-" * 60, DIM))
        lines.append("")
        
        grouped = data['grouped_tasks']
        
        # Section 1: Tasks by List
        lines.append(c("SECTION 1: TASKS BY LIST", CYAN + BOLD))
        lines.append(c("=" * 60, CYAN))
        
        for list_name, content in grouped.items():
            if list_name.startswith('__'): continue
            lines.append(c(f"LIST: {list_name}", BLUE + BOLD))
            lines.append(c("-" * len(f"LIST: {list_name}"), BLUE))
            
            for task in content['tasks']:
                is_completed = task['status'] == 'completed'
                status_mark = "x" if is_completed else " "
                status_color = GREEN if is_completed else WARNING
                
                lines.append(f"Task: [{c(status_mark, status_color)}] {c(task['title'], BOLD)}")
                
                # Add details
                details = []
                if task.get('description'):
                    details.append(c(f"  Details: {task['description']}", DIM))
                
                # Combine dates and notes on one line
                date_parts = []
                if task.get('created_at'):
                    try:
                        created_val = task['created_at']
                        if isinstance(created_val, str):
                            created_dt = datetime.fromisoformat(created_val.replace('+00:00', ''))
                        else:
                            created_dt = created_val
                        date_parts.append(f"C:{created_dt.strftime('%d-%m %H:%M')}")
                    except Exception as e:
                        pass
                if task.get('modified_at'):
                    try:
                        modified_val = task['modified_at']
                        if isinstance(modified_val, str):
                            modified_dt = datetime.fromisoformat(modified_val.replace('+00:00', ''))
                        else:
                            modified_dt = modified_val
                        date_parts.append(f"M:{modified_dt.strftime('%d-%m %H:%M')}")
                    except Exception as e:
                        pass
                if task.get('due'):
                    try:
                        due_date = datetime.fromisoformat(task['due']).strftime('%d-%m')
                        date_parts.append(f"D:{due_date}")
                    except:
                        pass
                
                # Combine dates with notes on same line
                if date_parts or task.get('notes'):
                    line_parts = []
                    if date_parts:
                        line_parts.append(f"📅 {', '.join(date_parts)}")
                    if task.get('notes'):
                        line_parts.append(task['notes'])
                    details.append(c(f"  {' | '.join(line_parts)}", DIM))
                
                if details:
                    lines.extend(details)
                lines.append("") # Empty line between tasks
            
            lines.append("")
            
        # Helper for sorting with custom order
        def get_sort_key(name, order_map):
            # Returns tuple (order_priority, name)
            # If in order_map: (order, name)
            # If not: (infinity, name) to put at end
            if name in order_map:
                return (order_map[name], name)
            return (float('inf'), name)

        # Section 2: Tasks by Tag (Aggregated)
        lines.append(c("SECTION 2: TASKS BY TAG", CYAN + BOLD))
        lines.append(c("=" * 60, CYAN))
        
        tag_order = grouped.get('__tag_group_order__', {})
        
        # Aggregate tags across all lists
        all_tags_map = {}
        for list_name, content in grouped.items():
            if list_name.startswith('__'): continue # Skip special keys
            by_tag = content['by_tag']
            for tag, tasks in by_tag.items():
                if tag not in all_tags_map:
                    all_tags_map[tag] = []
                all_tags_map[tag].extend(tasks)
        
        # Sort tags using custom order
        sorted_tags = sorted(all_tags_map.keys(), key=lambda t: get_sort_key(t, tag_order))
        
        if not sorted_tags:
            lines.append(c("(No tags found matching criteria)", DIM))
        
        for tag in sorted_tags:
            tasks = all_tags_map[tag]
            
            # Deduplicate tasks by ID
            seen_ids = set()
            unique_tasks = []
            for t in tasks:
                if t['id'] not in seen_ids:
                    seen_ids.add(t['id'])
                    unique_tasks.append(t)
            
            lines.append(c(f"TAG: {tag}", BLUE + BOLD))
            lines.append(c("-" * len(f"TAG: {tag}"), BLUE))
            
            for task in unique_tasks:
                is_completed = task['status'] == 'completed'
                status_mark = "x" if is_completed else " "
                status_color = GREEN if is_completed else WARNING
                
                lines.append(f"Task: [{c(status_mark, status_color)}] {c(task['title'], BOLD)}")
                
                # Add details
                details = []
                if task.get('description'):
                    details.append(c(f"  Details: {task['description']}", DIM))
                
                # Combine dates and notes on one line
                date_parts = []
                if task.get('created_at'):
                    try:
                        created_val = task['created_at']
                        if isinstance(created_val, str):
                            created_dt = datetime.fromisoformat(created_val.replace('+00:00', ''))
                        else:
                            created_dt = created_val
                        date_parts.append(f"C:{created_dt.strftime('%d-%m %H:%M')}")
                    except Exception as e:
                        pass
                if task.get('modified_at'):
                    try:
                        modified_val = task['modified_at']
                        if isinstance(modified_val, str):
                            modified_dt = datetime.fromisoformat(modified_val.replace('+00:00', ''))
                        else:
                            modified_dt = modified_val
                        date_parts.append(f"M:{modified_dt.strftime('%d-%m %H:%M')}")
                    except Exception as e:
                        pass
                if task.get('due'):
                    try:
                        due_date = datetime.fromisoformat(task['due']).strftime('%d-%m')
                        date_parts.append(f"D:{due_date}")
                    except:
                        pass
                
                # Combine dates with notes on same line
                if date_parts or task.get('notes'):
                    line_parts = []
                    if date_parts:
                        line_parts.append(f"📅 {', '.join(date_parts)}")
                    if task.get('notes'):
                        line_parts.append(task['notes'])
                    details.append(c(f"  {' | '.join(line_parts)}", DIM))
                
                if details:
                    lines.extend(details)
                lines.append("")
            
            lines.append("")

        # Section 3: Tasks by Title Group (if any)
        task_groups = grouped.get('__task_groups__', {})
        task_group_order = grouped.get('__task_group_order__', {})
        
        if task_groups:
            lines.append(c("SECTION 3: TASKS BY TITLE GROUP", CYAN + BOLD))
            lines.append(c("=" * 60, CYAN))
            
            sorted_groups = sorted(task_groups.keys(), key=lambda g: get_sort_key(g, task_group_order))
            for group_name in sorted_groups:
                tasks = task_groups[group_name]
                if not tasks: continue
                
                lines.append(c(f"GROUP: {group_name}", BLUE + BOLD))
                lines.append(c("-" * len(f"GROUP: {group_name}"), BLUE))
                
                for task in tasks:
                    is_completed = task['status'] == 'completed'
                    status_mark = "x" if is_completed else " "
                    status_color = GREEN if is_completed else WARNING
                    
                    lines.append(f"Task: [{c(status_mark, status_color)}] {c(task['title'], BOLD)}")
                    
                    # Add details
                    details = []
                    if task.get('description'):
                        details.append(c(f"  Details: {task['description']}", DIM))
                    
                    # Combine dates and notes on one line
                    date_parts = []
                    if task.get('created_at'):
                        try:
                            created_val = task['created_at']
                            if isinstance(created_val, str):
                                created_dt = datetime.fromisoformat(created_val.replace('+00:00', ''))
                            else:
                                created_dt = created_val
                            date_parts.append(f"C:{created_dt.strftime('%d-%m %H:%M')}")
                        except Exception as e:
                            pass
                    if task.get('modified_at'):
                        try:
                            modified_val = task['modified_at']
                            if isinstance(modified_val, str):
                                modified_dt = datetime.fromisoformat(modified_val.replace('+00:00', ''))
                            else:
                                modified_dt = modified_val
                            date_parts.append(f"M:{modified_dt.strftime('%d-%m %H:%M')}")
                        except Exception as e:
                            pass
                    if task.get('due'):
                        try:
                            due_date = datetime.fromisoformat(task['due']).strftime('%d-%m')
                            date_parts.append(f"D:{due_date}")
                        except:
                            pass
                    
                    # Combine dates with notes on same line
                    if date_parts or task.get('notes'):
                        line_parts = []
                        if date_parts:
                            line_parts.append(f"📅 {', '.join(date_parts)}")
                        if task.get('notes'):
                            line_parts.append(task['notes'])
                        details.append(c(f"  {' | '.join(line_parts)}", DIM))
                    
                    if details:
                        lines.extend(details)
                    lines.append("")
                lines.append("")
            
        return "\n".join(lines)
