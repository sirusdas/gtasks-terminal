#!/usr/bin/env python3
"""
Organized Tasks Report - rp9
Organizes tasks according to priority and functional categories, with tags removed for email delivery.
"""

from typing import List, Dict, Any
from datetime import datetime
import sys
from gtasks_cli.reports.base_report import BaseReport
from gtasks_cli.models.task import Task
from gtasks_cli.utils.tag_extractor import extract_tags_from_task, remove_tags_from_text


class OrganizedTasksReport(BaseReport):
    """Report that organizes tasks according to priority and functional categories."""
    
    def __init__(self):
        """Initialize the report."""
        super().__init__(
            name="Organized Tasks Report",
            description="Organizes tasks according to priority and functional categories with tags removed"
        )
        
        # Define the categories with their tags and sort order based on the requirements
        # Grouped by category types as specified in the requirements
        self.category_groups = [
            {
                "name": "Tasks with Priority Tags sort it with resepct to date",
                "categories": [
                    {"number": 4, "name": "Tasks with \"*****\" tag ---> Highest Priority", "tags": ["*****"], "sort_key": 4},
                    {"number": 7, "name": "Tasks with \"p1\" tag ---> Highest Priority", "tags": ["p1"], "sort_key": 7},
                    {"number": 5, "name": "Tasks with \"***\" tag ---> Medium Priority", "tags": ["***"], "sort_key": 5},
                    {"number": 8, "name": "Tasks with \"p2\" tag ---> Medium Priority", "tags": ["p2"], "sort_key": 8},
                    {"number": 9, "name": "Tasks with \"defects\" or \"bugs\" tag", "tags": ["defects", "bugs"], "sort_key": 9},
                    {"number": 17, "name": "Tasks with \"inTesting\" tag", "tags": ["inTesting"], "sort_key": 17},
                ]
            },
            {
                "name": "Tasks with Functional Tags sort it with resepct to date",
                "categories": [
                    {"number": 6, "name": "Tasks with \"FE\" tag ---> Frontend Tasks", "tags": ["FE"], "sort_key": 6},
                    {"number": 6, "name": "Tasks with \"BE\" tag ---> Backend Tasks", "tags": ["BE"], "sort_key": 6},
                    {"number": 2, "name": "Tasks with \"DEP\" tag ---> Dependency", "tags": ["DEP"], "sort_key": 2},
                    {"number": 18, "name": "Tasks with \"in-uat\" tag. ---> Tasks in UAT Phase", "tags": ["in-uat"], "sort_key": 18},
                ]
            },
            {
                "name": "Tasks with Pending Tags sort it with resepct to date",
                "categories": [
                    {"number": 6, "name": "Tasks with \"PET\" tag ---> Pending Testing", "tags": ["PET"], "sort_key": 6},
                    {"number": 6, "name": "Tasks with \"PDEP\" tag ---> Pending Development", "tags": ["PDEP"], "sort_key": 6},
                    {"number": 6, "name": "Tasks with \"PE\" tag ---> Pending Estimation", "tags": ["PE"], "sort_key": 6},
                    {"number": 10, "name": "Tasks with \"pending\" tag", "tags": ["pending"], "sort_key": 10},
                    {"number": 11, "name": "Tasks with \"pending-prod\" tag", "tags": ["pending-prod"], "sort_key": 11},
                ]
            },
            {
                "name": "Tasks with Time-Based Tags sort it with resepct to date",
                "categories": [
                    {"number": 21, "name": "Tasks with \"today\" tag or has today's date as due date", "tags": ["today"], "sort_key": 21},
                    {"number": 26, "name": "Tasks with \"daily\" tag", "tags": ["daily"], "sort_key": 26},
                    {"number": 22, "name": "Tasks with \"todo\" tag", "tags": ["todo"], "sort_key": 22},
                    {"number": 13, "name": "Tasks with \"this-week\" tag", "tags": ["this-week"], "sort_key": 13},
                    {"number": 16, "name": "Tasks with \"DEL-T\" tag ---> Delivery Today Tasks", "tags": ["DEL-T"], "sort_key": 16},
                    {"number": 19, "name": "Tasks with \"meeting\" or \"meetings\" tag", "tags": ["meeting", "meetings"], "sort_key": 19},
                    {"number": 24, "name": "Tasks with \"vapt\" or 'waf\" tag --> Security Related Tasks", "tags": ["vapt", "waf"], "sort_key": 24},
                ]
            },
            {
                "name": "PM related Tasks sort it with resepct to date",
                "categories": [
                    {"number": 14, "name": "Tasks with \"events\" tag", "tags": ["events"], "sort_key": 14},
                    {"number": 27, "name": "Tasks with \"go-live:\" tag", "tags": ["go-live:"], "sort_key": 27},
                    {"number": 15, "name": "Tasks with \"pm\" tag ---> Project Management Tasks", "tags": ["pm"], "sort_key": 15},
                    {"number": 25, "name": "Tasks with \"estimation\" tag", "tags": ["estimation"], "sort_key": 25},
                    {"number": 23, "name": "Tasks with \"upcoming-cr\" tag", "tags": ["upcoming-cr"], "sort_key": 23},
                    {"number": 3, "name": "Tasks with \"cr\" tag ---> Change Request", "tags": ["cr"], "sort_key": 3},
                ]
            },
            {
                "name": "Other Tasks",
                "categories": [
                    {"number": 1, "name": "Tasks with \"HOLD\" tag", "tags": ["HOLD"], "sort_key": 1},
                    {"number": 20, "name": "Tasks with \"long-term\" tag", "tags": ["long-term"], "sort_key": 20},
                    {"number": 12, "name": "Tasks with \"study\" tag", "tags": ["study"], "sort_key": 12},
                ]
            }
        ]
    
    def _has_any_tag(self, task: Task, tags: List[str]) -> bool:
        """Check if a task has any of the specified tags in title, description, or notes."""
        # Check in title
        if task.title:
            title_lower = " " + task.title.lower() + " "
            for tag in tags:
                # For single character or specific tags, use word boundary checking
                if tag.lower() in ["p1", "p2", "fe", "be", "cr", "pm", "de", "dep", "hold"]:
                    # Use word boundaries for these specific tags
                    if " " + tag.lower() + " " in title_lower:
                        return True
                    # Also check at the beginning or end of the title
                    if task.title.lower().startswith(tag.lower() + " ") or task.title.lower().endswith(" " + tag.lower()):
                        return True
                else:
                    # For longer tags, simple containment check
                    if tag.lower() in task.title.lower():
                        return True
        
        # Check in description
        if task.description:
            desc_lower = " " + task.description.lower() + " "
            for tag in tags:
                # For single character or specific tags, use word boundary checking
                if tag.lower() in ["p1", "p2", "fe", "be", "cr", "pm", "de", "dep", "hold"]:
                    # Use word boundaries for these specific tags
                    if " " + tag.lower() + " " in desc_lower:
                        return True
                    # Also check at the beginning or end of the description
                    if task.description.lower().startswith(tag.lower() + " ") or task.description.lower().endswith(" " + tag.lower()):
                        return True
                else:
                    # For longer tags, simple containment check
                    if tag.lower() in task.description.lower():
                        return True
                    
        # Check in notes
        if task.notes:
            notes_lower = " " + task.notes.lower() + " "
            for tag in tags:
                # For single character or specific tags, use word boundary checking
                if tag.lower() in ["p1", "p2", "fe", "be", "cr", "pm", "de", "dep", "hold"]:
                    # Use word boundaries for these specific tags
                    if " " + tag.lower() + " " in notes_lower:
                        return True
                    # Also check at the beginning or end of the notes
                    if task.notes.lower().startswith(tag.lower() + " ") or task.notes.lower().endswith(" " + tag.lower()):
                        return True
                else:
                    # For longer tags, simple containment check
                    if tag.lower() in task.notes.lower():
                        return True
        
        # Check in extracted tags
        task_tags = extract_tags_from_task(task)
        task_tag_set = set(tag.lower() for tag in task_tags)
        search_tag_set = set(tag.lower() for tag in tags)
        if task_tag_set & search_tag_set:
            return True
            
        return False
    
    def _normalize_datetime(self, dt):
        """Normalize datetime to handle timezone-aware and naive datetimes."""
        if dt is None:
            return None
        if isinstance(dt, str):
            try:
                dt = datetime.fromisoformat(dt)
            except:
                return None
        # If datetime is timezone-aware, convert to naive
        if dt.tzinfo is not None:
            return dt.replace(tzinfo=None)
        return dt
    
    def _sort_tasks_by_date(self, tasks: List[Task]) -> List[Task]:
        """Sort tasks by due date, with tasks without due dates at the end."""
        def get_sort_key(task):
            if task.due:
                # Normalize datetime for sorting
                normalized_due = self._normalize_datetime(task.due)
                if normalized_due:
                    return normalized_due
            return datetime.max.replace(tzinfo=None)
        
        return sorted(tasks, key=get_sort_key)
    
    def _remove_tags_from_task_fields(self, task: Task) -> Task:
        """Create a copy of the task with tags removed from title and description."""
        # Create a shallow copy of the task
        import copy
        clean_task = copy.copy(task)
        
        # Remove tags from title
        if clean_task.title:
            clean_task.title = remove_tags_from_text(clean_task.title)
        
        # Remove tags from description
        if clean_task.description:
            clean_task.description = remove_tags_from_text(clean_task.description)
            
        # Remove tags from notes
        if clean_task.notes:
            clean_task.notes = remove_tags_from_text(clean_task.notes)
            
        return clean_task
    
    def generate(self, tasks: List[Task], **kwargs) -> Dict[str, Any]:
        """
        Generate the organized tasks report.
        
        Args:
            tasks: List of tasks to generate report from
            **kwargs: Additional parameters (not used)
            
        Returns:
            Dict containing report data
        """
        # Extract options
        only_pending = kwargs.get("only_pending", False)
        
        # Categorize tasks
        categorized_tasks = {}
        uncategorized_tasks = []
        
        # Process each task to remove tags
        clean_tasks = [self._remove_tags_from_task_fields(task) for task in tasks]
        
        # Categorize tasks according to the exact group structure
        # For each task, we check all categories and place it in every matching category
        for original_task, clean_task in zip(tasks, clean_tasks):
            # Skip non-pending tasks if only_pending is True
            if only_pending and original_task.status != "pending":
                continue
                
            categorized = False
            # Iterate through all category groups and their categories
            # Check all categories to place task in every matching category
            for group in self.category_groups:
                for category in group["categories"]:
                    if self._has_any_tag(original_task, category["tags"]):
                        category_key = f"{category['number']}. {category['name']}"
                        if category_key not in categorized_tasks:
                            categorized_tasks[category_key] = {
                                "tasks": [],
                                "sort_key": category["sort_key"],
                                "number": category["number"],
                                "group": group["name"]
                            }
                        categorized_tasks[category_key]["tasks"].append(clean_task)
                        categorized = True
                        # Do NOT break here - continue checking all categories
            
            if not categorized:
                uncategorized_tasks.append(clean_task)
        
        # Sort tasks within each category by date
        for category_data in categorized_tasks.values():
            category_data["tasks"] = self._sort_tasks_by_date(category_data["tasks"])
        
        # Sort categories by the exact sequence (sort_key)
        sorted_categories = sorted(
            categorized_tasks.items(), 
            key=lambda x: x[1]["sort_key"]
        )
        
        return {
            "categories": sorted_categories,
            "uncategorized": self._sort_tasks_by_date(uncategorized_tasks),
            "total_tasks": len(clean_tasks),
            "only_title": kwargs.get("only_title", False),
            "no_other_tasks": kwargs.get("no_other_tasks", False),
            "only_pending": only_pending
        }
    
    def export(self, data: Dict[str, Any], format: str = 'txt') -> str:
        """
        Export the report in the specified format.
        
        Args:
            data: Report data generated by generate() method
            format: Export format (txt, csv, pdf)
            
        Returns:
            String representation of the exported report
        """
        if not data:
            return "No data available for report."
            
        if format == 'csv':
            return self._export_csv(data)
        elif format == 'txt':
            return self._export_txt(data)
        else:
            # Default to text format
            return self._export_txt(data)
    
    def _export_txt(self, data: Dict[str, Any]) -> str:
        """Export report in text format with enhanced formatting."""
        if not data:
            return "No data available for report."
            
        # Check if we should use colors (only when output is going to a terminal)
        use_colors = sys.stdout.isatty()
        
        # Try to import Rich for colored output if we're using colors
        if use_colors:
            try:
                from rich.console import Console
                from rich.panel import Panel
                from rich.text import Text
                from rich import print as rich_print
            except ImportError:
                use_colors = False
        
        # Extract options
        only_title = data.get("only_title", False)
        no_other_tasks = data.get("no_other_tasks", False)
        only_pending = data.get("only_pending", False)
        
        output = []
        output.append("=" * 60)
        output.append("                    ORGANIZED TASKS REPORT")
        output.append("=" * 60)
        output.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        output.append(f"Total tasks: {data['total_tasks']}")
        if only_pending:
            output.append("Filter: Only pending tasks")
        output.append("")
        
        # Create a mapping of group names to their categories for ordered display
        group_categories = {}
        for item in data.get("categories", []):
            if isinstance(item, tuple) and len(item) == 2:
                category_key, category_data = item
                group_name = category_data.get("group")
                if group_name:
                    if group_name not in group_categories:
                        group_categories[group_name] = []
                    group_categories[group_name].append((category_key, category_data))
        
        # Display groups in the correct order as defined in category_groups
        displayed_groups = set()
        for group in self.category_groups:
            group_name = group["name"]
            if group_name in group_categories and group_name not in displayed_groups:
                displayed_groups.add(group_name)
                output.append("")
                if use_colors:
                    # Add colored group header
                    output.append(f"[bold blue]# {group_name}[/bold blue]")
                else:
                    output.append(f"# {group_name}")
                    output.append("=" * len(f"# {group_name}"))
                output.append("")
                
                # Display categories within this group in their defined order
                for category in group["categories"]:
                    category_key = f"{category['number']}. {category['name']}"
                    # Find the matching category data
                    category_data = None
                    for cat_key, cat_data in group_categories[group_name]:
                        if cat_key == category_key:
                            category_data = cat_data
                            break
                    
                    if category_data:
                        tasks = category_data.get("tasks", [])
                        if tasks:
                            if use_colors:
                                # Add colored category header
                                output.append(f"[bold yellow]{category_key}[/bold yellow]")
                                output.append("[dim]" + "-" * 50 + "[/dim]")
                            else:
                                output.append(category_key)
                                output.append("-" * 50)
                            
                            for i, task in enumerate(tasks, 1):
                                # Format task display
                                if use_colors:
                                    task_line = f"[bold green]{i:2d}.[/bold green] {task.title}"
                                else:
                                    task_line = f"{i:2d}. {task.title}"
                                
                                # Add due date if available
                                if task.due:
                                    normalized_due = self._normalize_datetime(task.due)
                                    if normalized_due:
                                        due_str = normalized_due.strftime('%Y-%m-%d')
                                        if use_colors:
                                            task_line += f" [cyan](Due: {due_str})[/cyan]"
                                        else:
                                            task_line += f" (Due: {due_str})"
                                    elif isinstance(task.due, str):
                                        if use_colors:
                                            task_line += f" [cyan](Due: {task.due})[/cyan]"
                                        else:
                                            task_line += f" (Due: {task.due})"
                                
                                output.append(task_line)
                                
                                # Add description if available and not in only_title mode
                                if task.description and not only_title:
                                    # Indent description lines
                                    desc_lines = task.description.split('\n')
                                    for line in desc_lines:
                                        if line.strip():
                                            if use_colors:
                                                output.append(f"     [dim]{line}[/dim]")
                                            else:
                                                output.append(f"     └─ {line}")
                                
                                # Add notes if available and not in only_title mode
                                if task.notes and not only_title:
                                    notes_stripped = task.notes.strip()
                                    if notes_stripped:
                                        note_lines = notes_stripped.split('\n')
                                        for line in note_lines:
                                            if line.strip():
                                                if use_colors:
                                                    output.append(f"     [magenta]📓 {line}[/magenta]")
                                                else:
                                                    output.append(f"     📓 {line}")
                            
                            output.append("")
        
        # Display uncategorized tasks if not in no_other_tasks mode
        if not no_other_tasks:
            uncategorized = data.get("uncategorized", [])
            if uncategorized:
                output.append("")
                if use_colors:
                    output.append("[bold red]# Uncategorized Tasks[/bold red]")
                else:
                    output.append("# Uncategorized Tasks")
                    output.append("=" * 23)
                output.append("")
                
                if use_colors:
                    output.append("[bold red]Other Tasks (not matching any category)[/bold red]")
                    output.append("[dim]" + "-" * 50 + "[/dim]")
                else:
                    output.append("Other Tasks (not matching any category)")
                    output.append("-" * 50)
                
                for i, task in enumerate(uncategorized, 1):
                    if use_colors:
                        task_line = f"[bold green]{i:2d}.[/bold green] {task.title}"
                    else:
                        task_line = f"{i:2d}. {task.title}"
                    
                    # Add due date if available
                    if task.due:
                        normalized_due = self._normalize_datetime(task.due)
                        if normalized_due:
                            due_str = normalized_due.strftime('%Y-%m-%d')
                            if use_colors:
                                task_line += f" [cyan](Due: {due_str})[/cyan]"
                            else:
                                task_line += f" (Due: {due_str})"
                        elif isinstance(task.due, str):
                            if use_colors:
                                task_line += f" [cyan](Due: {task.due})[/cyan]"
                            else:
                                task_line += f" (Due: {task.due})"
                    
                    output.append(task_line)
                    
                    # Add description if available and not in only_title mode
                    if task.description and not only_title:
                        # Indent description lines
                        desc_lines = task.description.split('\n')
                        for line in desc_lines:
                            if line.strip():
                                if use_colors:
                                    output.append(f"     [dim]{line}[/dim]")
                                else:
                                    output.append(f"     └─ {line}")
                    
                    # Add notes if available and not in only_title mode
                    if task.notes and not only_title:
                        notes_stripped = task.notes.strip()
                        if notes_stripped:
                            note_lines = notes_stripped.split('\n')
                            for line in note_lines:
                                if line.strip():
                                    if use_colors:
                                        output.append(f"     [magenta]📓 {line}[/magenta]")
                                    else:
                                        output.append(f"     📓 {line}")
                
                output.append("")
        
        # Add footer
        output.append("=" * 60)
        output.append("              END OF ORGANIZED TASKS REPORT")
        output.append("=" * 60)
        
        result = "\n".join(output)
        
        # If we're using colors, we need to process the Rich markup
        if use_colors:
            try:
                from rich.console import Console
                from io import StringIO
                
                # Create a console that outputs to a string
                console_str = StringIO()
                console = Console(file=console_str, force_terminal=True)
                console.print(result)
                return console_str.getvalue()
            except ImportError:
                # Fallback to plain text if Rich is not available
                pass
        
        return result
    
    def _export_csv(self, data: Dict[str, Any]) -> str:
        """Export report in CSV format."""
        import csv
        import io
        
        if not data:
            return "No data available for report."
            
        # Extract options
        only_title = data.get("only_title", False)
        no_other_tasks = data.get("no_other_tasks", False)
        only_pending = data.get("only_pending", False)
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        if only_title:
            writer.writerow(["Category Group", "Category Number", "Category Name", "Task Number", "Title", "Due Date"])
        else:
            writer.writerow(["Category Group", "Category Number", "Category Name", "Task Number", "Title", "Due Date", "Description", "Notes"])
        
        # Add a row indicating the filter if only_pending is True
        if only_pending:
            writer.writerow(["FILTER", "Only pending tasks", "", "", "", "", "", ""])
        
        # Write categorized tasks
        for item in data.get("categories", []):
            if isinstance(item, tuple) and len(item) == 2:
                category_key, category_data = item
            else:
                continue
                
            # Extract number and name from category key
            parts = category_key.split(". ", 1)
            category_number = parts[0] if len(parts) > 1 else ""
            category_name = parts[1] if len(parts) > 1 else category_key
            
            group_name = category_data.get("group", "")
            
            tasks = category_data.get("tasks", [])
            for i, task in enumerate(tasks, 1):
                due_date_str = ""
                if task.due:
                    normalized_due = self._normalize_datetime(task.due)
                    if normalized_due:
                        due_date_str = normalized_due.strftime('%Y-%m-%d')
                    elif isinstance(task.due, str):
                        due_date_str = task.due
                
                if only_title:
                    writer.writerow([
                        group_name,
                        category_number,
                        category_name,
                        i,
                        task.title,
                        due_date_str
                    ])
                else:
                    writer.writerow([
                        group_name,
                        category_number,
                        category_name,
                        i,
                        task.title,
                        due_date_str,
                        task.description or "",
                        task.notes or ""
                    ])
        
        # Write uncategorized tasks if not in no_other_tasks mode
        if not no_other_tasks:
            uncategorized = data.get("uncategorized", [])
            for i, task in enumerate(uncategorized, 1):
                due_date_str = ""
                if task.due:
                    normalized_due = self._normalize_datetime(task.due)
                    if normalized_due:
                        due_date_str = normalized_due.strftime('%Y-%m-%d')
                    elif isinstance(task.due, str):
                        due_date_str = task.due
                
                if only_title:
                    writer.writerow([
                        "Uncategorized",
                        "",
                        "Other Tasks (not matching any category)",
                        i,
                        task.title,
                        due_date_str
                    ])
                else:
                    writer.writerow([
                        "Uncategorized",
                        "",
                        "Other Tasks (not matching any category)",
                        i,
                        task.title,
                        due_date_str,
                        task.description or "",
                        task.notes or ""
                    ])
        
        return output.getvalue()