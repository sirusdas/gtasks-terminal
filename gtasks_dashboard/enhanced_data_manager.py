#!/usr/bin/env python3
"""
GTasks Dashboard - Enhanced Data Manager Module
Handles data loading, processing, hierarchy creation, and all 10 advanced features:
1. Reports System Integration
2. Hierarchical Visualization
3. Advanced Tag Filtering
4. Priority System Enhancement
5. Deleted Tasks Management
6. Multi-Select Account Type Filters
7. Enhanced Task Management
8. Settings System
9. Collapsible Menu
10. Tasks Due Today Dashboard
"""

import os
import json
import sqlite3
import datetime
import re
import uuid
from pathlib import Path
from collections import defaultdict, Counter
import threading
import time

# Enhanced category mapping configuration
CATEGORIES = {
    'Team': ['@john', '@alice', '@bob', '@mou', '@john', '@devteam'],
    'UAT': ['#UAT', '#Testing', '#QA', '#Test', '#Validation'],
    'Production': ['#Live', '#Hotfix', '#Production', '#Deploy', '#Release'],
    'Priority': ['#High', '#Critical', '[p1]', '[urgent]', '#P0', '#P1'],
    'Projects': ['#API', '#Frontend', '#Backend', '#Mobile', '#Web', '#Database'],
    'Status': ['#InProgress', '#Blocked', '#Done', '#Review', '#Testing'],
    'Environment': ['#Dev', '#Staging', '#Prod', '#Development', '#Production'],
    'Type': ['#Bug', '#Feature', '#Enhancement', '#Refactor', '#Documentation'],
    'Domain': ['#Work', '#Personal', '#Learning', '#Health', '#Finance']
}

# Account type categorization configuration
ACCOUNT_TYPE_PATTERNS = {
    'Work': ['work', 'office', 'business', 'company', 'job', 'professional', 'corp'],
    'Personal': ['personal', 'home', 'private', 'life', 'family', 'me'],
    'Learning': ['learning', 'study', 'education', 'course', 'training', 'book'],
    'Health': ['health', 'fitness', 'medical', 'doctor', 'gym', 'exercise'],
    'Finance': ['finance', 'money', 'bank', 'investment', 'budget', 'tax'],
    'Social': ['social', 'friends', 'family', 'event', 'party', 'meeting']
}

# Available report types with metadata
REPORT_TYPES = {
    'task_completion': {
        'name': 'Task Completion Report',
        'description': 'Summary of completed tasks over a specified period',
        'class': 'TaskCompletionReport',
        'icon': 'fa-check-circle',
        'category': 'Performance',
        'supports_date_range': True,
        'parameters': {
            'start_date': {'type': 'date', 'required': False, 'label': 'Start Date'},
            'end_date': {'type': 'date', 'required': False, 'label': 'End Date'},
            'period_days': {'type': 'number', 'required': False, 'label': 'Period Days', 'default': 30}
        }
    },
    'overdue_tasks': {
        'name': 'Overdue Tasks Report',
        'description': 'Detailed list of tasks that are past their due dates',
        'class': 'OverdueTasksReport',
        'icon': 'fa-exclamation-triangle',
        'category': 'Analysis',
        'supports_date_range': False,
        'parameters': {}
    },
    'task_distribution': {
        'name': 'Task Distribution Report',
        'description': 'Analysis of tasks by category, priority, or tags',
        'class': 'TaskDistributionReport',
        'icon': 'fa-chart-pie',
        'category': 'Analytics',
        'supports_date_range': False,
        'parameters': {
            'group_by': {'type': 'select', 'required': False, 'label': 'Group By', 'options': ['status', 'priority', 'tags', 'projects']}
        }
    },
    'timeline': {
        'name': 'Timeline Report',
        'description': 'Visual representation of tasks completed over a specified time period',
        'class': 'TimelineReport',
        'icon': 'fa-timeline',
        'category': 'Visualization',
        'supports_date_range': True,
        'parameters': {
            'start_date': {'type': 'date', 'required': False, 'label': 'Start Date'},
            'end_date': {'type': 'date', 'required': False, 'label': 'End Date'},
            'period_days': {'type': 'number', 'required': False, 'label': 'Period Days', 'default': 30}
        }
    },
    'pending_tasks': {
        'name': 'Pending Tasks Report',
        'description': 'List of all pending tasks with their due dates',
        'class': 'PendingTasksReport',
        'icon': 'fa-clock',
        'category': 'Status',
        'supports_date_range': False,
        'parameters': {}
    },
    'completion_rate': {
        'name': 'Task Completion Rate Report',
        'description': 'Percentage of tasks completed over a given period',
        'class': 'TaskCompletionRateReport',
        'icon': 'fa-percentage',
        'category': 'Performance',
        'supports_date_range': True,
        'parameters': {
            'start_date': {'type': 'date', 'required': False, 'label': 'Start Date'},
            'end_date': {'type': 'date', 'required': False, 'label': 'End Date'},
            'period_days': {'type': 'number', 'required': False, 'label': 'Period Days', 'default': 30}
        }
    },
    'task_creation': {
        'name': 'Task Creation Report',
        'description': 'Overview of tasks created within a certain timeframe',
        'class': 'TaskCreationReport',
        'icon': 'fa-plus-circle',
        'category': 'Analytics',
        'supports_date_range': True,
        'parameters': {
            'start_date': {'type': 'date', 'required': False, 'label': 'Start Date'},
            'end_date': {'type': 'date', 'required': False, 'label': 'End Date'},
            'period_days': {'type': 'number', 'required': False, 'label': 'Period Days', 'default': 30}
        }
    },
    'future_timeline': {
        'name': 'Future Timeline Report',
        'description': 'Tasks scheduled for future dates',
        'class': 'FutureTimelineReport',
        'icon': 'fa-calendar-alt',
        'category': 'Planning',
        'supports_date_range': False,
        'parameters': {
            'days_ahead': {'type': 'number', 'required': False, 'label': 'Days Ahead', 'default': 30}
        }
    },
    'organized_tasks': {
        'name': 'Organized Tasks Report',
        'description': 'Tasks organized according to priority and functional categories',
        'class': 'OrganizedTasksReport',
        'icon': 'fa-list-alt',
        'category': 'Organization',
        'supports_date_range': False,
        'parameters': {}
    },
    'custom_filtered': {
        'name': 'Custom Filtered Report',
        'description': 'Custom filter-based reports with advanced criteria',
        'class': 'CustomFilteredReport',
        'icon': 'fa-filter',
        'category': 'Custom',
        'supports_date_range': False,
        'parameters': {
            'filter_str': {'type': 'text', 'required': False, 'label': 'Date Filter String'},
            'tags_filter': {'type': 'text', 'required': False, 'label': 'Tags Filter'},
            'order_by': {'type': 'select', 'required': False, 'label': 'Order By', 'options': ['created_at', 'modified_at', 'due', 'priority']}
        }
    }
}

class GTasksEnhancedDataManager:
    def __init__(self):
        self.setup_paths()
        self.dashboard_data = {
            'tasks': {},
            'accounts': [],
            'stats': {},
            'hierarchy_data': {'nodes': [], 'links': []},
            'current_account': 'default',
            'account_types': [],
            'account_type_filters': [],
            'available_tags': {},
            'priority_stats': {},
            'settings': {
                'show_deleted_tasks': False,
                'theme': 'light',
                'notifications': True,
                'default_view': 'dashboard',
                'auto_refresh': True,
                'compact_view': False,
                'menu_visible': True,
                'menu_animation': True,
                'keyboard_shortcuts': True,
                'priority_system_enabled': True,
                'advanced_filters_enabled': True,
                'reports_enabled': True,
                'sidebar_visible': True,
                'default_account': 'default'
            },
            'reports': {
                'templates': {},
                'history': [],
                'scheduled': []
            },
            'realtime': {'connected': False, 'last_update': None}
        }
        self.load_settings()
        self.detect_accounts()
        self.load_all_data()
        self.calculate_priorities()
        self.build_available_tags()
        self.calculate_priority_statistics()
        self.create_priority_enhanced_hierarchy()
        self.setup_realtime_updates()
    
    def setup_paths(self):
        """Setup paths for GTasks integration"""
        self.gtasks_home = Path.home() / '.gtasks'
        self.project_gtasks_path = Path('./gtasks_cli')
        
        if self.gtasks_home.exists():
            self.gtasks_path = self.gtasks_home
        elif self.project_gtasks_path.exists():
            self.gtasks_path = self.project_gtasks_path
        else:
            print("⚠️  GTasks CLI not found. Using demo data.")
            self.gtasks_path = None
    
    def load_settings(self):
        """Load user settings from file"""
        settings_file = 'enhanced_dashboard_settings.json'
        try:
            if os.path.exists(settings_file):
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
                    self.dashboard_data['settings'].update(settings)
        except Exception as e:
            print(f"⚠️  Error loading settings: {e}")
    
    def save_settings(self):
        """Save user settings to file"""
        settings_file = 'enhanced_dashboard_settings.json'
        try:
            with open(settings_file, 'w') as f:
                json.dump(self.dashboard_data['settings'], f, indent=2)
        except Exception as e:
            print(f"❌ Error saving settings: {e}")
    
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
        """Categorize a tag based on the CATEGORIES mapping"""
        tag_lower = tag.lower()
        
        for category, tag_list in CATEGORIES.items():
            if tag_lower in [t.lower() for t in tag_list]:
                return category
        
        # Default categorization based on tag format
        if tag.startswith('@'):
            return 'Team'
        elif tag.startswith('#'):
            return 'Tags'
        else:
            return 'Legacy'
    
    def calculate_priorities(self):
        """Calculate priorities for all tasks using asterisk patterns"""
        if not self.dashboard_data['settings'].get('priority_system_enabled', True):
            return
            
        print("🔄 Calculating priorities from asterisk patterns...")
        
        for account_id, tasks in self.dashboard_data['tasks'].items():
            for task in tasks:
                # Extract all tags for priority calculation
                all_tags = []
                
                # Add existing task tags
                all_tags.extend(task.get('tags', []))
                
                # Add tags from title, description, notes
                text_content = f"{task.get('title', '')} {task.get('description', '')} {task.get('notes', '')}"
                extracted_tags = self.extract_hybrid_tags(text_content)
                all_tags.extend(extracted_tags['bracket'])
                all_tags.extend(extracted_tags['hash'])
                all_tags.extend(extracted_tags['user'])
                
                # Simple asterisk-based priority calculation
                asterisk_patterns = re.findall(r'\*+', str(all_tags))
                priority_count = 0
                
                for pattern in asterisk_patterns:
                    priority_count += len(pattern)
                
                # Determine priority based on asterisk count
                if priority_count >= 6:
                    task['calculated_priority'] = 'critical'
                elif priority_count >= 4:
                    task['calculated_priority'] = 'high'
                elif priority_count >= 3:
                    task['calculated_priority'] = 'medium'
                else:
                    task['calculated_priority'] = 'low'
                
                task['priority_source'] = 'calculated'
                task['asterisk_patterns'] = asterisk_patterns
                
                # Update task priority if no manual override
                task['priority'] = task.get('priority', 'medium')
        
        print("✅ Priority calculation completed")
    
    def calculate_priority_statistics(self):
        """Calculate comprehensive priority statistics"""
        priority_stats = {
            'total_tasks': 0,
            'by_priority': defaultdict(int),
            'by_source': defaultdict(int),
            'asterisk_patterns': defaultdict(int)
        }
        
        for tasks in self.dashboard_data['tasks'].values():
            for task in tasks:
                priority_stats['total_tasks'] += 1
                
                # Count by calculated priority
                priority = task.get('calculated_priority', 'low')
                priority_stats['by_priority'][priority] += 1
                
                # Count by source
                source = task.get('priority_source', 'calculated')
                priority_stats['by_source'][source] += 1
                
                # Count asterisk patterns
                patterns = task.get('asterisk_patterns', [])
                if patterns:
                    priority_stats['asterisk_patterns']['with_patterns'] += 1
                    for pattern in patterns:
                        priority_stats['asterisk_patterns'][pattern] += 1
                else:
                    priority_stats['asterisk_patterns']['no_patterns'] += 1
        
        # Convert defaultdicts to regular dicts for JSON serialization
        self.dashboard_data['priority_stats'] = {
            'total_tasks': priority_stats['total_tasks'],
            'by_priority': dict(priority_stats['by_priority']),
            'by_source': dict(priority_stats['by_source']),
            'asterisk_patterns': dict(priority_stats['asterisk_patterns'])
        }
        
        print(f"✅ Calculated priority statistics for {priority_stats['total_tasks']} tasks")
    
    def build_available_tags(self):
        """Build a comprehensive list of all available tags with usage statistics"""
        all_tags = defaultdict(lambda: {'count': 0, 'categories': set(), 'accounts': set()})
        
        # Collect tags from all tasks
        for account_id, tasks in self.dashboard_data['tasks'].items():
            for task in tasks:
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
        
        self.dashboard_data['available_tags'] = available_tags
        print(f"✅ Built tag database: {len(available_tags)} unique tags found")
    
    def detect_accounts(self):
        """Detect all configured accounts from directory structure"""
        accounts = []
        
        if self.gtasks_path and self.gtasks_path.exists():
            if self.gtasks_path.is_dir():
                for item in self.gtasks_path.iterdir():
                    if item.is_dir() and item.name != 'default':
                        account_info = self.get_account_info(item.name)
                        accounts.append(account_info)
            
            default_account = self.get_account_info('default')
            accounts.append(default_account)
        
        if not accounts:
            accounts.append({
                'id': 'demo',
                'name': 'Demo Account',
                'email': 'demo@example.com',
                'isActive': True,
                'taskCount': 0,
                'completedCount': 0,
                'stats': {}
            })
        
        self.dashboard_data['accounts'] = accounts
        
        # Generate account types from detected accounts
        self.generate_account_types()
        
        print(f"✅ Detected {len(accounts)} accounts")
        for account in accounts:
            print(f"  - {account['name']} ({account['id']}) [{account.get('type', 'Unknown')}]")
    
    def generate_account_types(self):
        """Generate unique account types from detected accounts"""
        account_types = set()
        for account in self.dashboard_data['accounts']:
            account_types.add(account.get('type', 'Other'))
        
        self.dashboard_data['account_types'] = sorted(list(account_types))
        print(f"✅ Detected account types: {', '.join(self.dashboard_data['account_types'])}")
    
    def get_account_info(self, account_name):
        """Get information about a specific account"""
        account_path = self.gtasks_path / account_name if self.gtasks_path else None
        
        db_files = []
        if account_path and account_path.exists():
            db_files = list(account_path.glob('*.db'))
        
        has_data = len(db_files) > 0 or (account_path and (account_path / 'tasks.db').exists())
        
        # Determine account type
        account_type = self.categorize_account_type(account_name)
        
        return {
            'id': account_name,
            'name': account_name.replace('_', ' ').title(),
            'email': f'{account_name}@example.com',
            'type': account_type,
            'isActive': has_data,
            'taskCount': 0,
            'completedCount': 0,
            'hasDatabase': len(db_files) > 0,
            'stats': {}
        }
    
    def categorize_account_type(self, account_name):
        """Categorize account based on name patterns"""
        account_lower = account_name.lower()
        
        for account_type, patterns in ACCOUNT_TYPE_PATTERNS.items():
            for pattern in patterns:
                if pattern in account_lower:
                    return account_type
        
        # Default categorization based on common patterns
        if account_lower in ['default', 'main', 'primary']:
            return 'General'
        elif any(word in account_lower for word in ['test', 'demo', 'sample']):
            return 'Testing'
        else:
            return 'Other'
    
    def parse_tag_filter(self, tag_string):
        """Parse tag filter string with support for OR, AND, NOT operations"""
        if not tag_string:
            return {'or_tags': [], 'and_tags': [], 'not_tags': []}
        
        # Clean and normalize the input
        tag_string = tag_string.strip()
        
        # Split by spaces first to handle different operations
        parts = tag_string.split()
        or_tags = []
        and_tags = []
        not_tags = []
        
        for part in parts:
            part = part.strip()
            if not part:
                continue
            
            # Handle NOT operation (tags starting with -)
            if part.startswith('-'):
                tag = part[1:].strip()
                if tag:
                    not_tags.append(tag.lower())
            
            # Handle AND operation (& symbol)
            elif '&' in part:
                and_tags.extend([t.strip().lower() for t in part.split('&') if t.strip()])
            
            # Handle OR operation (| symbol)
            elif '|' in part:
                or_tags.extend([t.strip().lower() for t in part.split('|') if t.strip()])
            
            # Regular tag (add to OR group)
            else:
                or_tags.append(part.lower())
        
        return {
            'or_tags': list(set(or_tags)),  # Remove duplicates
            'and_tags': list(set(and_tags)),
            'not_tags': list(set(not_tags))
        }
    
    def filter_tasks_by_tags(self, tasks, tag_filters):
        """Filter tasks based on parsed tag filters"""
        if not tag_filters or not any(tag_filters.values()):
            return tasks
        
        or_tags = tag_filters.get('or_tags', [])
        and_tags = tag_filters.get('and_tags', [])
        not_tags = tag_filters.get('not_tags', [])
        
        filtered_tasks = []
        
        for task in tasks:
            # Get all tags for this task
            task_tags = set()
            if task.get('hybrid_tags'):
                task_tags.update(task['hybrid_tags'].get('bracket', []))
                task_tags.update(task['hybrid_tags'].get('hash', []))
                task_tags.update(task['hybrid_tags'].get('user', []))
            
            # Also check title, description, and notes for tags
            text_content = f"{task.get('title', '')} {task.get('description', '')} {task.get('notes', '')}"
            extracted_tags = self.extract_hybrid_tags(text_content)
            for tag_list in extracted_tags.values():
                task_tags.update(tag_list)
            
            # Apply filters
            matches_or = True
            matches_and = True
            matches_not = True
            
            # OR filter: Task must have at least one of the OR tags
            if or_tags:
                matches_or = any(tag in task_tags for tag in or_tags)
            
            # AND filter: Task must have all AND tags
            if and_tags:
                matches_and = all(tag in task_tags for tag in and_tags)
            
            # NOT filter: Task must not have any NOT tags
            if not_tags:
                matches_not = not any(tag in task_tags for tag in not_tags)
            
            # Include task if it matches all filter criteria
            if matches_or and matches_and and matches_not:
                filtered_tasks.append(task)
        
        return filtered_tasks
    
    def load_all_data(self):
        """Load data for all detected accounts"""
        for account in self.dashboard_data['accounts']:
            account_id = account['id']
            tasks = self.load_tasks_for_account(account_id)
            
            # Enhance tasks with hybrid tag extraction and metadata
            for task in tasks:
                task['hybrid_tags'] = self.extract_hybrid_tags(
                    f"{task.get('title', '')} {task.get('description', '')} {task.get('notes', '')}"
                )
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
                
                # Add additional metadata for CLI parity
                task['account'] = account_id
                task['is_recurring'] = task.get('recurrence_rule') is not None
                task['has_dependencies'] = len(task.get('dependencies', [])) > 0
                task['estimated_duration'] = task.get('estimated_duration')
                task['completion_rate'] = 100 if task.get('status') == 'completed' else 0
                
                # Add deleted task management fields
                task['is_deleted'] = task.get('is_deleted', False)
                task['deleted_at'] = task.get('deleted_at')
                task['deleted_by'] = task.get('deleted_by')
            
            # Calculate account stats
            total_tasks = len(tasks)
            completed_tasks = len([t for t in tasks if t.get('status') == 'completed'])
            deleted_tasks = len([t for t in tasks if t.get('is_deleted', False)])
            
            account['taskCount'] = total_tasks
            account['completedCount'] = completed_tasks
            account['deletedCount'] = deleted_tasks
            account['completionRate'] = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            
            self.dashboard_data['tasks'][account_id] = tasks
        
        # Set current account
        active_accounts = [a for a in self.dashboard_data['accounts'] if a['isActive']]
        if active_accounts:
            self.dashboard_data['current_account'] = active_accounts[0]['id']
        
        # Calculate overall stats
        all_tasks = []
        for tasks in self.dashboard_data['tasks'].values():
            all_tasks.extend(tasks)
        self.dashboard_data['stats'] = self.calculate_stats(all_tasks)
        
        print(f"✅ Loaded and enhanced data for {len(self.dashboard_data['tasks'])} accounts")
    
    def load_tasks_for_account(self, account_name):
        """Load tasks for a specific account"""
        tasks = []
        
        if not self.gtasks_path:
            return self.get_demo_tasks_with_priorities()
        
        if account_name == 'default':
            db_paths = [
                self.gtasks_path / 'tasks.db',
                self.project_gtasks_path / 'tasks.db'
            ]
        else:
            account_path = self.gtasks_path / account_name
            db_paths = [
                account_path / 'tasks.db',
                self.gtasks_path / account_name / 'tasks.db'
            ]
        
        for db_path in db_paths:
            if db_path.exists():
                try:
                    tasks = self.load_from_sqlite(db_path, account_name)
                    if tasks:
                        break
                except Exception as e:
                    print(f"❌ Error loading from {db_path}: {e}")
                    continue
        
        if not tasks:
            if account_name == 'default':
                json_files = list(self.gtasks_path.glob('google_tasks_backup_*.json'))
            else:
                json_files = list((self.gtasks_path / account_name).glob('google_tasks_backup_*.json')) if (self.gtasks_path / account_name).exists() else []
            
            if json_files:
                try:
                    with open(json_files[0], 'r') as f:
                        data = json.load(f)
                        for task in data:
                            task['account'] = account_name
                            task['list_name'] = task.get('list_name', 'My Tasks')
                            tasks.append(task)
                except Exception as e:
                    print(f"❌ Error loading JSON backup for {account_name}: {e}")
        
        return tasks if tasks else self.get_demo_tasks_with_priorities()
    
    def load_from_sqlite(self, db_path, account_name):
        """Load tasks from SQLite database"""
        tasks = []
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT t.*, l.list_name 
                FROM tasks t 
                LEFT JOIN task_lists l ON t.id = l.task_id
            ''')
            
            rows = cursor.fetchall()
            for row in rows:
                task = {
                    'id': row[0],
                    'title': row[1],
                    'description': row[2],
                    'due': row[3],
                    'priority': row[4] or 'medium',
                    'status': row[5] or 'pending',
                    'project': row[6],
                    'tags': json.loads(row[7]) if row[7] else [],
                    'notes': row[8],
                    'created_at': row[11],
                    'list_name': row[-1] if row[-1] else 'My Tasks',
                    'account': account_name,
                    'recurrence_rule': row[9] if len(row) > 9 else None,
                    'dependencies': json.loads(row[10]) if len(row) > 10 and row[10] else [],
                    # Default values for deleted task management
                    'is_deleted': False,
                    'deleted_at': None,
                    'deleted_by': None
                }
                tasks.append(task)
            
            conn.close()
            print(f"✅ Loaded {len(tasks)} tasks from {db_path}")
            
        except Exception as e:
            print(f"❌ Error loading from SQLite {db_path}: {e}")
            
        return tasks
    
    def get_demo_tasks_with_priorities(self):
        """Generate comprehensive demo tasks with asterisk-based priorities"""
        demo_tasks = [
            {
                'id': f'demo_1', 
                'title': f'Implement #API endpoint for @john #UAT [******critical]', 
                'description': 'Create REST API with comprehensive testing',
                'due': '2024-01-15', 'priority': 'high', 'status': 'pending',
                'project': 'API', 'tags': ['api', 'development'], 
                'notes': 'Use #Docker for containerization @alice will review [urgent]',
                'list_name': 'Development',
                'account': 'demo', 'created_at': '2024-01-10T10:00:00Z',
                'recurrence_rule': None,
                'dependencies': [],
                'estimated_duration': 480,
                'is_deleted': False,
                'deleted_at': None,
                'deleted_by': None
            },
            {
                'id': f'demo_2', 
                'title': f'Fix critical #Bug in #Frontend @mou [****important]',
                'description': 'Memory leak affecting user experience',
                'due': '2024-01-12', 'priority': 'medium', 'status': 'in_progress',
                'project': 'Frontend', 'tags': ['bug', 'ui'], 
                'notes': '[P0] needs immediate attention',
                'list_name': 'Bugs',
                'account': 'demo', 'created_at': '2024-01-09T14:30:00Z',
                'recurrence_rule': None,
                'dependencies': [],
                'estimated_duration': 240,
                'is_deleted': False,
                'deleted_at': None,
                'deleted_by': None
            },
            {
                'id': f'demo_3', 
                'title': f'#Feature: Dark mode implementation @bob [***review]',
                'description': 'User requested dark theme for better accessibility',
                'due': '2024-01-20', 'priority': 'medium', 'status': 'pending',
                'project': 'UI', 'tags': ['feature', 'theme'], 
                'notes': 'Test on #Staging before #Production deployment',
                'list_name': 'Features',
                'account': 'demo', 'created_at': '2024-01-08T09:15:00Z',
                'recurrence_rule': None,
                'dependencies': [f'demo_2'],
                'estimated_duration': 360,
                'is_deleted': False,
                'deleted_at': None,
                'deleted_by': None
            },
            {
                'id': f'demo_4', 
                'title': f'Review @alice code #Backend #API [*******emergency]',
                'description': 'Code review for authentication module',
                'due': '2024-01-18', 'priority': 'high', 'status': 'pending',
                'project': 'Backend', 'tags': ['review', 'auth'], 
                'notes': 'Focus on #Security and #Performance',
                'list_name': 'Code Reviews',
                'account': 'demo', 'created_at': '2024-01-07T11:20:00Z',
                'recurrence_rule': None,
                'dependencies': [],
                'estimated_duration': 120,
                'is_deleted': False,
                'deleted_at': None,
                'deleted_by': None
            },
            {
                'id': f'demo_5', 
                'title': f'#Bug: Database connection timeout @john [******production]',
                'description': 'Connection pool exhaustion causing timeouts',
                'due': '2024-01-14', 'priority': 'critical', 'status': 'in_progress',
                'project': 'Database', 'tags': ['bug', 'database'], 
                'notes': '[P0] affects all users #Production',
                'list_name': 'Critical Issues',
                'account': 'demo', 'created_at': '2024-01-06T16:45:00Z',
                'recurrence_rule': None,
                'dependencies': [],
                'estimated_duration': 180,
                'is_deleted': False,
                'deleted_at': None,
                'deleted_by': None
            },
            {
                'id': f'demo_6', 
                'title': f'#Work on #Mobile app #Frontend [**optional]',
                'description': 'Implement responsive design improvements',
                'due': '2024-01-22', 'priority': 'medium', 'status': 'pending',
                'project': 'Mobile', 'tags': ['work', 'mobile', 'frontend'], 
                'notes': 'Use #React Native for development',
                'list_name': 'Development',
                'account': 'demo', 'created_at': '2024-01-05T08:30:00Z',
                'recurrence_rule': None,
                'dependencies': [],
                'estimated_duration': 300,
                'is_deleted': False,
                'deleted_at': None,
                'deleted_by': None
            },
            {
                'id': f'demo_7', 
                'title': f'#Enhancement: Add logging system [*basic]',
                'description': 'Improve application logging for debugging',
                'due': '2024-01-25', 'priority': 'low', 'status': 'pending',
                'project': 'Infrastructure', 'tags': ['enhancement', 'logging'], 
                'notes': 'Nice to have feature',
                'list_name': 'Enhancements',
                'account': 'demo', 'created_at': '2024-01-04T10:15:00Z',
                'recurrence_rule': None,
                'dependencies': [],
                'estimated_duration': 200,
                'is_deleted': False,
                'deleted_at': None,
                'deleted_by': None
            },
            {
                'id': f'demo_8', 
                'title': f'DELETED TASK: Old #Testing framework [urgent]',
                'description': 'This is a deleted task for testing purposes',
                'due': '2024-01-05', 'priority': 'low', 'status': 'pending',
                'project': 'Legacy', 'tags': ['testing', 'legacy'], 
                'notes': 'This task has been deleted',
                'list_name': 'Deleted Tasks',
                'account': 'demo', 'created_at': '2024-01-05T10:00:00Z',
                'recurrence_rule': None,
                'dependencies': [],
                'estimated_duration': 120,
                'is_deleted': True,
                'deleted_at': '2024-01-06T15:30:00Z',
                'deleted_by': 'system'
            }
        ]
        return demo_tasks
    
    def calculate_stats(self, tasks):
        """Calculate comprehensive dashboard statistics"""
        total = len(tasks)
        completed = len([t for t in tasks if t.get('status') == 'completed'])
        pending = len([t for t in tasks if t.get('status') == 'pending'])
        in_progress = len([t for t in tasks if t.get('status') == 'in_progress'])
        deleted = len([t for t in tasks if t.get('is_deleted', False)])
        
        # Overdue tasks
        today = datetime.datetime.now().date()
        overdue = len([t for t in tasks if t.get('due') and 
                     datetime.datetime.fromisoformat(t['due']).date() < today and 
                     t.get('status') != 'completed'])
        
        # High priority tasks (including calculated priorities)
        high_priority = len([t for t in tasks if t.get('calculated_priority') in ['high', 'critical']])
        
        # Recurring tasks
        recurring = len([t for t in tasks if t.get('is_recurring')])
        
        completion_rate = (completed / total * 100) if total > 0 else 0
        
        return {
            'totalTasks': total,
            'completedTasks': completed,
            'pendingTasks': pending,
            'inProgressTasks': in_progress,
            'deletedTasks': deleted,
            'overdueTasks': overdue,
            'highPriorityTasks': high_priority,
            'recurringTasks': recurring,
            'completionRate': completion_rate
        }
    
    def create_priority_enhanced_hierarchy(self):
        """Create hierarchical data with priority indicators"""
        print("🔄 Creating priority-enhanced hierarchy data...")
        
        nodes = []
        links = []
        
        # Get all tasks from all accounts (excluding deleted tasks for hierarchy)
        all_tasks = []
        for tasks in self.dashboard_data['tasks'].values():
            active_tasks = [t for t in tasks if not t.get('is_deleted', False)]
            all_tasks.extend(active_tasks)
        
        if not all_tasks:
            return {'nodes': [], 'links': []}
        
        # Count tag occurrences and priority distribution
        tag_counts = defaultdict(int)
        category_counts = defaultdict(int)
        task_tag_mapping = defaultdict(list)
        priority_counts = defaultdict(int)
        
        for task in all_tasks:
            # Count priorities
            priority = task.get('calculated_priority', 'low')
            priority_counts[priority] += 1
            
            # Process categorized tags
            for category, tags in task.get('categorized_tags', {}).items():
                category_counts[category] += 1
                
                for tag in tags:
                    tag_counts[tag] += 1
                    task_tag_mapping[category].append(tag)
        
        # Create priority nodes
        priority_colors = {
            'critical': '#ef4444',  # Red
            'high': '#f97316',      # Orange  
            'medium': '#eab308',    # Yellow
            'low': '#6b7280'        # Gray
        }
        
        priority_icons = {
            'critical': '🔥',
            'high': '⚠️',
            'medium': '📋',
            'low': '📝'
        }
        
        priority_nodes = []
        for priority, count in priority_counts.items():
            priority_nodes.append({
                'id': f'priority_{priority}',
                'name': f'{priority_icons.get(priority, "📝")} {priority.title()} ({count})',
                'group': 0,
                'val': count * 3,
                'level': 'priority',
                'type': 'priority',
                'color': priority_colors.get(priority, '#6b7280'),
                'priority': priority
            })
        
        # Create category nodes
        category_nodes = []
        for category, count in category_counts.items():
            node_id = f"category_{category.lower().replace(' ', '_')}"
            category_nodes.append({
                'id': node_id,
                'name': category,
                'group': 1,
                'val': count * 2,
                'level': 'category',
                'type': 'category'
            })
        
        # Create tag nodes
        tag_nodes = []
        for tag, count in tag_counts.items():
            node_id = f"tag_{tag.lower().replace('@', 'at_').replace('#', 'hash_')}"
            
            # Determine which category this tag belongs to
            category = None
            for cat, tags in task_tag_mapping.items():
                if tag in tags:
                    category = f"category_{cat.lower().replace(' ', '_')}"
                    break
            
            tag_nodes.append({
                'id': node_id,
                'name': tag,
                'group': 2,
                'val': count + 2,
                'level': 'tag',
                'type': 'tag',
                'category': category
            })
        
        # Create task nodes with priority indicators
        task_nodes = []
        for task in all_tasks[:100]:  # Limit for performance
            node_id = f"task_{task['id']}"
            priority = task.get('calculated_priority', 'low')
            
            # Find primary tag for this task
            primary_tag = None
            if task.get('hybrid_tags'):
                all_tags = (task['hybrid_tags']['bracket'] + 
                           task['hybrid_tags']['hash'] + 
                           task['hybrid_tags']['user'])
                if all_tags:
                    primary_tag = f"tag_{all_tags[0].lower().replace('@', 'at_').replace('#', 'hash_')}"
            
            task_nodes.append({
                'id': node_id,
                'name': task['title'][:25] + '...' if len(task['title']) > 25 else task['title'],
                'group': 3,
                'val': 6,
                'level': 'task',
                'type': 'task',
                'task_id': task['id'],
                'status': task.get('status', 'pending'),
                'priority': priority,
                'priority_color': priority_colors.get(priority, '#6b7280'),
                'priority_icon': priority_icons.get(priority, '📝'),
                'tag': primary_tag,
                'account': task.get('account', 'default'),
                'asterisk_patterns': task.get('asterisk_patterns', []),
                'priority_source': task.get('priority_source', 'calculated')
            })
        
        # Combine all nodes
        nodes = priority_nodes + category_nodes + tag_nodes + task_nodes
        
        # Create links
        # Priority -> Task links
        for task_node in task_nodes:
            priority_node = f"priority_{task_node['priority']}"
            links.append({
                'source': priority_node,
                'target': task_node['id'],
                'value': 3,
                'type': 'priority_task'
            })
        
        # Category -> Tag links
        for tag_node in tag_nodes:
            if tag_node.get('category'):
                links.append({
                    'source': tag_node['category'],
                    'target': tag_node['id'],
                    'value': 2,
                    'type': 'category_tag'
                })
        
        # Tag -> Task links
        for task_node in task_nodes:
            if task_node.get('tag'):
                links.append({
                    'source': task_node['tag'],
                    'target': task_node['id'],
                    'value': 1,
                    'type': 'tag_task'
                })
        
        hierarchy_data = {
            'nodes': nodes,
            'links': links,
            'priorities': list(priority_counts.keys()),
            'categories': list(category_counts.keys()),
            'stats': {
                'total_priorities': len(priority_counts),
                'total_categories': len(category_counts),
                'total_tags': len(tag_counts),
                'total_tasks': len(all_tasks),
                'priority_distribution': dict(priority_counts)
            }
        }
        
        self.dashboard_data['hierarchy_data'] = hierarchy_data
        print(f"✅ Created priority-enhanced hierarchy: {len(nodes)} nodes, {len(links)} links")
        
        return hierarchy_data
    
    def setup_realtime_updates(self):
        """Setup periodic data updates"""
        def update_loop():
            while True:
                time.sleep(60)
                print("🔄 Updating enhanced dashboard data...")
                try:
                    self.load_all_data()
                    if self.dashboard_data['settings'].get('priority_system_enabled', True):
                        self.calculate_priorities()
                        self.calculate_priority_statistics()
                    self.create_priority_enhanced_hierarchy()
                    self.build_available_tags()
                    self.save_settings()
                    print("✅ Enhanced dashboard data updated successfully")
                except Exception as e:
                    print(f"❌ Error during update: {e}")
        
        thread = threading.Thread(target=update_loop, daemon=True)
        thread.start()
        print("✅ Realtime updates started")
    
    # Deleted Tasks Management Methods
    def soft_delete_task(self, task_id, account_id=None):
        """Soft delete a task"""
        current_account = account_id or self.dashboard_data['current_account']
        
        if current_account in self.dashboard_data['tasks']:
            for task in self.dashboard_data['tasks'][current_account]:
                if task['id'] == task_id:
                    task['is_deleted'] = True
                    task['deleted_at'] = datetime.datetime.now().isoformat()
                    task['deleted_by'] = 'user'
                    task['status'] = 'deleted'
                    return True
        return False
    
    def restore_task(self, task_id, account_id=None):
        """Restore a deleted task"""
        current_account = account_id or self.dashboard_data['current_account']
        
        if current_account in self.dashboard_data['tasks']:
            for task in self.dashboard_data['tasks'][current_account]:
                if task['id'] == task_id:
                    task['is_deleted'] = False
                    task['deleted_at'] = None
                    task['deleted_by'] = None
                    task['status'] = 'pending'  # Reset to pending
                    return True
        return False
    
    def permanently_delete_task(self, task_id, account_id=None):
        """Permanently delete a task"""
        current_account = account_id or self.dashboard_data['current_account']
        
        if current_account in self.dashboard_data['tasks']:
            tasks = self.dashboard_data['tasks'][current_account]
            for i, task in enumerate(tasks):
                if task['id'] == task_id:
                    del tasks[i]
                    return True
        return False
    
    # Task Management Methods
    def create_task(self, task_data, account_id=None):
        """Create a new task"""
        current_account = account_id or self.dashboard_data['current_account']
        
        if current_account not in self.dashboard_data['tasks']:
            self.dashboard_data['tasks'][current_account] = []
        
        # Generate ID if not provided
        if 'id' not in task_data:
            task_data['id'] = f"{current_account}_{uuid.uuid4().hex[:8]}"
        
        # Set default values
        task_data.setdefault('status', 'pending')
        task_data.setdefault('priority', 'medium')
        task_data.setdefault('account', current_account)
        task_data.setdefault('created_at', datetime.datetime.now().isoformat())
        task_data.setdefault('is_deleted', False)
        task_data.setdefault('deleted_at', None)
        task_data.setdefault('deleted_by', None)
        
        # Extract hybrid tags
        task_data['hybrid_tags'] = self.extract_hybrid_tags(
            f"{task_data.get('title', '')} {task_data.get('description', '')} {task_data.get('notes', '')}"
        )
        
        # Categorize tags
        task_data['categorized_tags'] = {}
        all_tags = (task_data['hybrid_tags']['bracket'] + 
                   task_data['hybrid_tags']['hash'] + 
                   task_data['hybrid_tags']['user'])
        
        for tag in all_tags:
            category = self.categorize_tag(tag)
            if category not in task_data['categorized_tags']:
                task_data['categorized_tags'][category] = []
            task_data['categorized_tags'][category].append(tag)
        
        self.dashboard_data['tasks'][current_account].append(task_data)
        return task_data
    
    def update_task(self, task_id, task_data, account_id=None):
        """Update an existing task"""
        current_account = account_id or self.dashboard_data['current_account']
        
        if current_account in self.dashboard_data['tasks']:
            for i, task in enumerate(self.dashboard_data['tasks'][current_account]):
                if task['id'] == task_id:
                    # Update task fields
                    task.update(task_data)
                    
                    # Re-extract hybrid tags if content changed
                    if any(field in task_data for field in ['title', 'description', 'notes']):
                        task['hybrid_tags'] = self.extract_hybrid_tags(
                            f"{task.get('title', '')} {task.get('description', '')} {task.get('notes', '')}"
                        )
                        
                        # Re-categorize tags
                        task['categorized_tags'] = {}
                        all_tags = (task['hybrid_tags']['bracket'] + 
                                   task['hybrid_tags']['hash'] + 
                                   task['hybrid_tags']['user'])
                        
                        for tag in all_tags:
                            category = self.categorize_tag(tag)
                            if category not in task['categorized_tags']:
                                task['categorized_tags'][category] = []
                            task['categorized_tags'][category].append(tag)
                    
                    return task
        return None
    
    # Reports Methods
    def get_report_types(self):
        """Get all available report types"""
        return REPORT_TYPES
    
    def generate_report(self, report_type, tasks, **kwargs):
        """Generate a report using demo implementation"""
        try:
            if report_type == 'task_completion':
                return self.generate_demo_completion_report(tasks, **kwargs)
            elif report_type == 'overdue_tasks':
                return self.generate_demo_overdue_report(tasks)
            elif report_type == 'task_distribution':
                return self.generate_demo_distribution_report(tasks)
            elif report_type == 'timeline':
                return self.generate_demo_timeline_report(tasks, **kwargs)
            else:
                return self.generate_demo_generic_report(report_type, tasks, **kwargs)
        except Exception as e:
            print(f"Error generating report {report_type}: {e}")
            return self.generate_demo_generic_report(report_type, tasks, **kwargs)
    
    def generate_demo_completion_report(self, tasks, **kwargs):
        """Generate demo task completion report"""
        period_days = kwargs.get('period_days', 30)
        end_date = datetime.datetime.now()
        start_date = end_date - datetime.timedelta(days=period_days)
        
        completed_tasks = [t for t in tasks if t.get('status') == 'completed']
        
        # Group by date
        daily_completion = {}
        for task in completed_tasks:
            if task.get('created_at'):
                date_key = task['created_at'][:10]  # YYYY-MM-DD
                if date_key not in daily_completion:
                    daily_completion[date_key] = []
                daily_completion[date_key].append(task)
        
        return {
            'report_name': 'Task Completion Report',
            'report_description': 'Summary of completed tasks over a specified period',
            'period_start': start_date.isoformat(),
            'period_end': end_date.isoformat(),
            'period_days': period_days,
            'total_completed': len(completed_tasks),
            'daily_completion': daily_completion,
            'daily_counts': {date: len(tasks) for date, tasks in daily_completion.items()},
            'average_per_day': len(completed_tasks) / period_days if period_days > 0 else 0,
            'completion_rate': (len(completed_tasks) / len(tasks) * 100) if tasks else 0
        }
    
    def generate_demo_overdue_report(self, tasks):
        """Generate demo overdue tasks report"""
        today = datetime.datetime.now().date()
        overdue_tasks = []
        
        for task in tasks:
            if (task.get('status') != 'completed' and 
                task.get('due') and 
                datetime.datetime.fromisoformat(task['due']).date() < today):
                
                days_overdue = (today - datetime.datetime.fromisoformat(task['due']).date()).days
                task_copy = task.copy()
                task_copy['days_overdue'] = days_overdue
                overdue_tasks.append(task_copy)
        
        overdue_tasks.sort(key=lambda x: x['days_overdue'], reverse=True)
        
        very_overdue = [t for t in overdue_tasks if t['days_overdue'] >= 30]
        moderately_overdue = [t for t in overdue_tasks if 7 <= t['days_overdue'] < 30]
        recently_overdue = [t for t in overdue_tasks if t['days_overdue'] < 7]
        
        return {
            'report_name': 'Overdue Tasks Report',
            'report_description': 'Detailed list of tasks that are past their due dates',
            'total_overdue': len(overdue_tasks),
            'very_overdue': very_overdue,
            'moderately_overdue': moderately_overdue,
            'recently_overdue': recently_overdue,
            'generated_at': datetime.datetime.now().isoformat()
        }
    
    def generate_demo_distribution_report(self, tasks):
        """Generate demo task distribution report"""
        # Distribution by status
        status_counter = Counter(t.get('status', 'unknown') for t in tasks)
        
        # Distribution by priority
        priority_counter = Counter(t.get('priority', 'medium') for t in tasks)
        
        # Distribution by tags
        tag_counter = Counter()
        for task in tasks:
            for tag in task.get('tags', []):
                tag_counter[tag] += 1
        
        # Distribution by projects
        project_counter = Counter(t.get('project', 'No Project') for t in tasks)
        
        total_tasks = len(tasks)
        
        return {
            'report_name': 'Task Distribution Report',
            'report_description': 'Analysis of tasks by category, priority, or tags',
            'total_tasks': total_tasks,
            'status_distribution': dict(status_counter),
            'priority_distribution': dict(priority_counter),
            'tag_distribution': dict(tag_counter.most_common(10)),
            'project_distribution': dict(project_counter),
            'top_tags': tag_counter.most_common(10),
            'top_projects': project_counter.most_common(10),
            'generated_at': datetime.datetime.now().isoformat()
        }
    
    def generate_demo_timeline_report(self, tasks, **kwargs):
        """Generate demo timeline report"""
        period_days = kwargs.get('period_days', 30)
        end_date = datetime.datetime.now()
        start_date = end_date - datetime.timedelta(days=period_days)
        
        # Create timeline data
        timeline_data = []
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            daily_tasks = [t for t in tasks if t.get('created_at', '').startswith(date_str)]
            
            timeline_data.append({
                'date': date_str,
                'total_tasks': len(daily_tasks),
                'completed_tasks': len([t for t in daily_tasks if t.get('status') == 'completed']),
                'pending_tasks': len([t for t in daily_tasks if t.get('status') == 'pending'])
            })
            
            current_date += datetime.timedelta(days=1)
        
        return {
            'report_name': 'Timeline Report',
            'report_description': 'Visual representation of tasks over a specified time period',
            'period_start': start_date.isoformat(),
            'period_end': end_date.isoformat(),
            'timeline_data': timeline_data,
            'generated_at': datetime.datetime.now().isoformat()
        }
    
    def generate_demo_generic_report(self, report_type, tasks, **kwargs):
        """Generate a generic demo report"""
        report_info = REPORT_TYPES.get(report_type, {})
        
        return {
            'report_name': report_info.get('name', f'{report_type.title()} Report'),
            'report_description': report_info.get('description', 'Report generated from tasks data'),
            'total_tasks': len(tasks),
            'generated_at': datetime.datetime.now().isoformat(),
            'parameters': kwargs,
            'summary': {
                'total_tasks': len(tasks),
                'completed_tasks': len([t for t in tasks if t.get('status') == 'completed']),
                'pending_tasks': len([t for t in tasks if t.get('status') == 'pending']),
                'overdue_tasks': len([t for t in tasks if t.get('due') and 
                                     datetime.datetime.fromisoformat(t['due']).date() < datetime.datetime.now().date()])
            }
        }
    
    def get_tasks_due_today(self):
        """Get tasks due today"""
        today = datetime.datetime.now().date().strftime('%Y-%m-%d')
        all_tasks = []
        
        for tasks in self.dashboard_data['tasks'].values():
            all_tasks.extend(tasks)
        
        due_today_tasks = []
        for task in all_tasks:
            if task.get('due') == today and not task.get('is_deleted', False):
                due_today_tasks.append(task)
        
        return due_today_tasks
    
    # Public API methods
    def get_dashboard_data(self):
        """Get the current dashboard data"""
        return self.dashboard_data
    
    def refresh_data(self):
        """Refresh all dashboard data"""
        self.load_all_data()
        self.calculate_priorities()
        self.calculate_priority_statistics()
        self.create_priority_enhanced_hierarchy()
        self.build_available_tags()
        return self.dashboard_data
    
    def switch_account(self, account_id):
        """Switch current account"""
        if account_id in [a['id'] for a in self.dashboard_data['accounts']]:
            self.dashboard_data['current_account'] = account_id
            return True
        return False
    
    def update_settings(self, settings_dict):
        """Update dashboard settings"""
        self.dashboard_data['settings'].update(settings_dict)
        self.save_settings()
        return self.dashboard_data['settings']
    
    def get_filtered_tasks(self, filters):
        """Get tasks based on filters"""
        all_tasks = []
        for tasks in self.dashboard_data['tasks'].values():
            all_tasks.extend(tasks)
        
        filtered_tasks = all_tasks
        
        # Apply account type filters
        if filters.get('account_types'):
            account_types = filters['account_types']
            filtered_tasks = [t for t in filtered_tasks if t.get('account') in account_types]
        
        # Apply status filters
        if filters.get('status'):
            status_filter = filters['status']
            filtered_tasks = [t for t in filtered_tasks if t.get('status') in status_filter]
        
        # Apply priority filters
        if filters.get('priority'):
            priority_filter = filters['priority']
            filtered_tasks = [t for t in filtered_tasks if t.get('calculated_priority') in priority_filter]
        
        # Apply date range filters
        if filters.get('start_date'):
            start_date = datetime.datetime.fromisoformat(filters['start_date'])
            filtered_tasks = [t for t in filtered_tasks if t.get('created_at') and 
                           datetime.datetime.fromisoformat(t['created_at']) >= start_date]
        
        if filters.get('end_date'):
            end_date = datetime.datetime.fromisoformat(filters['end_date'])
            filtered_tasks = [t for t in filtered_tasks if t.get('created_at') and 
                           datetime.datetime.fromisoformat(t['created_at']) <= end_date]
        
        # Apply tag filters
        if filters.get('tag_filters'):
            tag_filters = self.parse_tag_filter(filters['tag_filters'])
            filtered_tasks = self.filter_tasks_by_tags(filtered_tasks, tag_filters)
        
        return filtered_tasks