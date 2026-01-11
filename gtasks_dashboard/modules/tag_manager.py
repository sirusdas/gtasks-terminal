"""
Tag Management Module for GTasks Dashboard

This module handles tag extraction, categorization, and filtering including:
- Hybrid tag extraction (brackets, hashtags, user mentions)
- Tag categorization and organization
- Advanced tag filtering with pipe-separated operations

Author: GTasks Dashboard Team
Date: January 11, 2026
"""

import re
from collections import defaultdict


class TagManager:
    """Handles tag extraction, categorization, and filtering"""
    
    def __init__(self):
        # Category mapping for tag organization
        self.categories = {
            'Team': ['@john', '@alice', '@bob', '@mou', '@devteam'],
            'UAT': ['#UAT', '#Testing', '#QA', '#Test', '#Validation'],
            'Production': ['#Live', '#Hotfix', '#Production', '#Deploy', '#Release'],
            'Priority': ['#High', '#Critical', '[p1]', '[urgent]', '#P0', '#P1'],
            'Projects': ['#API', '#Frontend', '#Backend', '#Mobile', '#Web', '#Database'],
            'Status': ['#InProgress', '#Blocked', '#Done', '#Review', '#Testing'],
            'Environment': ['#Dev', '#Staging', '#Prod', '#Development', '#Production'],
            'Type': ['#Bug', '#Feature', '#Enhancement', '#Refactor', '#Documentation'],
            'Domain': ['#Work', '#Personal', '#Learning', '#Health', '#Finance']
        }
    
    def extract_hybrid_tags(self, text):
        """Extract tags using both [] and #/@ style"""
        if not text:
            return {'bracket': [], 'hash': [], 'user': []}
        
        # Extract bracket tags: [tag]
        bracket_tags = re.findall(r'\[([^\]]+)\]', text, re.IGNORECASE)
        
        # Extract hash tags: #tag
        hash_tags = re.findall(r'#(\w+)', text, re.IGNORECASE)
        
        # Extract user tags: @user
        user_tags = re.findall(r'@(\w+)', text, re.IGNORECASE)
        
        return {
            'bracket': [tag.lower() for tag in bracket_tags],
            'hash': [tag.lower() for tag in hash_tags],
            'user': [tag.lower() for tag in user_tags]
        }
    
    def categorize_tag(self, tag):
        """Categorize a tag based on the categories mapping"""
        tag_lower = tag.lower()
        
        for category, tag_list in self.categories.items():
            if tag_lower in [t.lower() for t in tag_list]:
                return category
        
        # Default categorization based on tag format
        if tag.startswith('@'):
            return 'Team'
        elif tag.startswith('#'):
            return 'Tags'
        else:
            return 'Legacy'
    
    def build_available_tags(self, tasks):
        """Build a comprehensive list of all available tags with usage statistics"""
        all_tags = defaultdict(lambda: {'count': 0, 'categories': set(), 'accounts': set()})
        
        # Collect tags from all tasks
        for task in tasks:
            account_id = task.get('account', 'default')
            
            # Get tags from hybrid_tags
            if task.get('hybrid_tags'):
                all_task_tags = (
                    task['hybrid_tags'].get('bracket', []) +
                    task['hybrid_tags'].get('hash', []) +
                    task['hybrid_tags'].get('user', [])
                )
                
                for tag in all_task_tags:
                    all_tags[tag]['count'] += 1
                    all_tags[tag]['categories'].add(self.categorize_tag(tag))
                    all_tags[tag]['accounts'].add(account_id)
        
        # Convert to the format needed by the API
        available_tags = {}
        for tag, data in all_tags.items():
            available_tags[tag] = {
                'count': data['count'],
                'categories': list(data['categories']),
                'accounts': list(data['accounts']),
                'popularity': 'high' if data['count'] > 5 else 'medium' if data['count'] > 2 else 'low'
            }
        
        return available_tags
    
    def parse_tag_filter(self, tag_string):
        """Parse tag filter string with OR, AND, NOT operations"""
        if not tag_string:
            return []
        
        tags = tag_string.split('|')
        return [tag.strip() for tag in tags if tag.strip()]
    
    def filter_tasks_by_tags(self, tasks, tag_filters):
        """Filter tasks based on tag filters with OR/AND/NOT operations"""
        if not tag_filters:
            return tasks
        
        filtered_tasks = []
        
        for task in tasks:
            # Get all tags for this task
            task_tags = []
            if task.get('hybrid_tags'):
                task_tags = (
                    task['hybrid_tags'].get('bracket', []) +
                    task['hybrid_tags'].get('hash', []) +
                    task['hybrid_tags'].get('user', [])
                )
            
            # Apply tag filters
            should_include = False
            for filter_pattern in tag_filters:
                # Handle NOT operations
                if filter_pattern.startswith('-'):
                    tag_to_exclude = filter_pattern[1:]
                    if tag_to_exclude in task_tags:
                        should_include = False
                        break
                    else:
                        continue
                
                # Handle OR operations (any matching tag)
                if filter_pattern in task_tags:
                    should_include = True
                    break
            
            if should_include:
                filtered_tasks.append(task)
        
        return filtered_tasks
    
    def enhance_task_with_tags(self, task):
        """Enhance a task with tag extraction and categorization"""
        # Extract hybrid tags
        text_content = f"{task.get('title', '')} {task.get('description', '')} {task.get('notes', '')}"
        task['hybrid_tags'] = self.extract_hybrid_tags(text_content)
        task['categorized_tags'] = {}
        
        # Categorize all tags
        all_tags = (task['hybrid_tags']['bracket'] + 
                   task['hybrid_tags']['hash'] + 
                   task['hybrid_tags']['user'])
        
        for tag in all_tags:
            category = self.categorize_tag(tag)
            if category not in task['categorized_tags']:
                task['categorized_tags'][category] = []
            task['categorized_tags'][category].append(tag)
        
        return task
    
    def get_tag_suggestions(self, available_tags, query="", limit=10):
        """Get tag suggestions based on search query"""
        if not query:
            # Return most popular tags
            sorted_tags = sorted(available_tags.items(), key=lambda x: x[1]['count'], reverse=True)
            return {tag: data for tag, data in sorted_tags[:limit]}
        
        # Filter tags by query
        filtered_tags = {}
        query_lower = query.lower()
        
        for tag, data in available_tags.items():
            if query_lower in tag.lower():
                filtered_tags[tag] = data
        
        # Sort by popularity and return
        sorted_tags = sorted(filtered_tags.items(), key=lambda x: x[1]['count'], reverse=True)
        return {tag: data for tag, data in sorted_tags[:limit]}