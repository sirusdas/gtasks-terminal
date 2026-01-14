"""
Data Manager Service
Handles all data loading from database or demo data

Features:
- Basic task loading and processing
- Priority calculation from asterisks
- Hierarchical visualization data
- Advanced features (if enabled in config):
  - Settings persistence
  - Advanced tag filtering (OR/AND/NOT)
  - Account type categorization
  - Deleted tasks management
  - Tasks due today
  - Priority statistics
"""
import sqlite3
import json
import re
import os
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict

from models.task import Task, Account, DashboardStats, HybridTags

# Import feature flags and configuration
from config import FEATURE_FLAGS, CATEGORIES, ACCOUNT_TYPE_PATTERNS, PRIORITY_COLORS, PRIORITY_ICONS, REPORT_TYPES


# Category mapping for tag categorization
CATEGORIES = {
    'Team': ['@john', '@alice', '@bob', '@mou', '@devteam', '@team'],
    'UAT': ['#UAT', '#Testing', '#QA', '#Test', '#Validation'],
    'Production': ['#Live', '#Hotfix', '#Production', '#Deploy', '#Release', '#Prod'],
    'Priority': ['#High', '#Critical', '[p1]', '[urgent]', '#P0', '#P1'],
    'Projects': ['#API', '#Frontend', '#Backend', '#Mobile', '#Web', '#Database', '#Database'],
    'Status': ['#InProgress', '#Blocked', '#Done', '#Review', '#Testing'],
    'Environment': ['#Dev', '#Staging', '#Prod', '#Development', '#Production'],
    'Type': ['#Bug', '#Feature', '#Enhancement', '#Refactor', '#Documentation'],
}


class DataManager:
    """Manages data loading and task/account operations"""
    
    def __init__(self, gtasks_path: Optional[Path] = None):
        self.gtasks_path = gtasks_path or self._detect_gtasks_path()
    
    def _detect_gtasks_path(self) -> Optional[Path]:
        """Detect GTasks CLI path"""
        home_path = Path.home() / '.gtasks'
        project_path = Path('./gtasks_cli')
        
        if home_path.exists():
            return home_path
        elif project_path.exists():
            return project_path
        return None
    
    def _extract_tags(self, text: str) -> Dict[str, List[str]]:
        """Extract tags from text"""
        if not text:
            return {'bracket': [], 'hash': [], 'user': []}
        
        bracket_tags = re.findall(r'\[([^\]]+)\]', text, re.IGNORECASE)
        hash_tags = re.findall(r'#(\w+)', text, re.IGNORECASE)
        user_tags = re.findall(r'@(\w+)', text, re.IGNORECASE)
        
        return {
            'bracket': [tag.lower() for tag in bracket_tags],
            'hash': [tag.lower() for tag in hash_tags],
            'user': [tag.lower() for tag in user_tags]
        }
    
    def _calculate_priority(self, title: str) -> str:
        """Calculate priority from asterisks in title"""
        asterisk_count = len(re.findall(r'\*+', title))
        if asterisk_count >= 6:
            return 'critical'
        elif asterisk_count >= 4:
            return 'high'
        elif asterisk_count >= 3:
            return 'medium'
        return 'low'
    
    def _categorize_tag(self, tag: str) -> str:
        """Categorize a tag"""
        tag_lower = tag.lower()
        for category, tag_list in CATEGORIES.items():
            if tag_lower in [t.lower() for t in tag_list]:
                return category
        return 'Tags' if tag.startswith('#') else 'Team' if tag.startswith('@') else 'Legacy'
    
    def detect_accounts(self) -> List[Account]:
        """Detect all configured accounts"""
        accounts = []
        
        if self.gtasks_path and self.gtasks_path.exists():
            if self.gtasks_path.is_dir():
                for item in self.gtasks_path.iterdir():
                    if item.is_dir() and item.name != 'default':
                        accounts.append(Account(
                            id=item.name,
                            name=item.name.replace('_', ' ').title(),
                            email=f'{item.name}@example.com',
                            account_type='Other',
                            is_active=True
                        ))
            
            # Add default account
            accounts.append(Account(
                id='default',
                name='Default',
                email='default@example.com',
                account_type='General',
                is_active=True
            ))
        
        # If no accounts found, create demo account
        if not accounts:
            accounts.append(Account(
                id='demo',
                name='Demo Account',
                email='demo@example.com',
                account_type='Testing',
                is_active=True
            ))
        
        return accounts
    
    def load_tasks_for_account(self, account_id: str) -> List[Task]:
        """Load tasks for a specific account"""
        if not self.gtasks_path:
            return self._get_demo_tasks(account_id)
        
        db_path = self.gtasks_path / account_id / 'tasks.db'
        if not db_path.exists():
            db_path = self.gtasks_path / 'tasks.db'
        
        if db_path.exists():
            try:
                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, title, description, due, priority, status, tags, notes, 
                           created_at, modified_at, dependencies
                    FROM tasks
                """)
                rows = cursor.fetchall()
                conn.close()
                
                if rows:
                    return self._process_task_rows(rows, account_id)
            except Exception as e:
                print(f"⚠️  Error loading tasks for {account_id}: {e}")
        
        return self._get_demo_tasks(account_id)
    
    def _process_task_rows(self, rows: List[tuple], account_id: str) -> List[Task]:
        """Process database rows into Task objects"""
        tasks = []
        for row in rows:
            task_data = {
                'id': row[0],
                'title': row[1],
                'description': row[2] or '',
                'due': row[3],
                'priority': row[4] or 'medium',
                'status': row[5] or 'pending',
                'tags': json.loads(row[6]) if row[6] else [],
                'notes': row[7] or '',
                'account': account_id,
                'created_at': row[8],
                'modified_at': row[9],
                'dependencies': json.loads(row[10]) if len(row) > 10 and row[10] else []
            }
            
            # Extract hybrid tags
            task_data['hybrid_tags'] = self._extract_tags(
                f"{task_data['title']} {task_data['description']} {task_data['notes']}"
            )
            
            # Calculate priority from asterisks
            task_data['calculated_priority'] = self._calculate_priority(task_data['title'])
            
            tasks.append(Task.from_dict(task_data))
        
        return tasks
    
    def _get_demo_tasks(self, account_id: str = 'demo') -> List[Task]:
        """Generate demo tasks with dependencies"""
        base_time = datetime.now()
        
        demo_tasks = [
            {
                'id': f'{account_id}_1',
                'title': 'Review #API implementation @john [*****high]',
                'description': 'Code review for new API endpoints',
                'due': (base_time).strftime('%Y-%m-%d'),
                'priority': 'high',
                'status': 'pending',
                'tags': ['api', 'review'],
                'notes': 'Use #Docker for testing',
                'account': account_id,
                'dependencies': []
            },
            {
                'id': f'{account_id}_2',
                'title': 'Fix #Bug in #Frontend @mou [******critical]',
                'description': 'Memory leak in dashboard component',
                'due': (base_time).strftime('%Y-%m-%d'),
                'priority': 'critical',
                'status': 'in_progress',
                'tags': ['bug', 'frontend'],
                'notes': '[P0] production issue - depends on API being stable',
                'account': account_id,
                'dependencies': [f'{account_id}_1']
            },
            {
                'id': f'{account_id}_3',
                'title': '#Feature: Dark mode implementation @bob [***medium]',
                'description': 'User requested dark theme for accessibility',
                'due': (base_time).strftime('%Y-%m-%d'),
                'priority': 'medium',
                'status': 'pending',
                'tags': ['feature', 'theme'],
                'notes': 'Test on #Staging - waiting for bug fix',
                'account': account_id,
                'dependencies': [f'{account_id}_2']
            },
            {
                'id': f'{account_id}_4',
                'title': 'Database optimization @alice [****high]',
                'description': 'Optimize slow queries in dashboard',
                'due': (base_time).strftime('%Y-%m-%d'),
                'priority': 'high',
                'status': 'pending',
                'tags': ['database', 'optimization'],
                'notes': 'Focus on #Production',
                'account': account_id,
                'dependencies': [f'{account_id}_1']
            },
            {
                'id': f'{account_id}_5',
                'title': 'Setup CI/CD pipeline @devteam [****high]',
                'description': 'Automated testing and deployment',
                'due': (base_time).strftime('%Y-%m-%d'),
                'priority': 'high',
                'status': 'completed',
                'tags': ['devops', 'automation'],
                'notes': 'Complete setup',
                'account': account_id,
                'dependencies': []
            },
            {
                'id': f'{account_id}_6',
                'title': 'Write documentation for #API @tech-writer [**low]',
                'description': 'API documentation for endpoints',
                'due': (base_time).strftime('%Y-%m-%d'),
                'priority': 'low',
                'status': 'pending',
                'tags': ['documentation', 'api'],
                'notes': 'After CI/CD is ready',
                'account': account_id,
                'dependencies': [f'{account_id}_5']
            }
        ]
        
        tasks = []
        for task_data in demo_tasks:
            task_data['hybrid_tags'] = self._extract_tags(
                f"{task_data['title']} {task_data['description']} {task_data['notes']}"
            )
            task_data['calculated_priority'] = self._calculate_priority(task_data['title'])
            tasks.append(Task.from_dict(task_data))
        
        return tasks
    
    def calculate_stats_for_account(self, account_id: str, tasks: List[Task]) -> DashboardStats:
        """Calculate stats for a specific account"""
        return DashboardStats.from_tasks(tasks)
    
    def get_hierarchy_data(self, tasks: List[Task]) -> Dict[str, Any]:
        """Generate hierarchy visualization data from tasks"""
        nodes = []
        links = []
        node_ids = set()
        
        # Create meta nodes
        meta_nodes = [
            {'id': 'all_tasks', 'name': 'All Tasks', 'type': 'meta', 'val': len(tasks), 'level': 0},
        ]
        
        # Create priority nodes
        priorities = ['critical', 'high', 'medium', 'low']
        priority_counts = {}
        for p in priorities:
            count = len([t for t in tasks if t.calculated_priority == p])
            priority_counts[p] = count
        
        for i, priority in enumerate(priorities):
            if priority_counts[priority] > 0:
                node_id = f'priority_{priority}'
                nodes.append({
                    'id': node_id,
                    'name': f'{priority.title()} ({priority_counts[priority]})',
                    'type': 'priority',
                    'val': priority_counts[priority],
                    'level': 1,
                    'priority': priority
                })
                node_ids.add(node_id)
                
                # Link to meta
                links.append({'source': 'all_tasks', 'target': node_id, 'value': priority_counts[priority]})
        
        # Create category nodes based on tags
        category_keywords = {
            'development': ['api', 'frontend', 'backend', 'code', 'implementation', 'feature', 'bug'],
            'testing': ['test', 'qa', 'validation', 'verification'],
            'infrastructure': ['deploy', 'setup', 'config', 'infrastructure', 'environment', 'devops'],
            'documentation': ['doc', 'documentation', 'readme', 'guide'],
            'meeting': ['meeting', 'review', 'discussion'],
            'research': ['research', 'investigate', 'explore', 'analysis']
        }
        
        category_counts = {cat: 0 for cat in category_keywords}
        for task in tasks:
            task_text = f"{task.title} {task.description}".lower()
            for category, keywords in category_keywords.items():
                if any(kw in task_text for kw in keywords):
                    category_counts[category] += 1
        
        for i, (category, count) in enumerate(category_counts.items()):
            if count > 0:
                node_id = f'category_{category}'
                nodes.append({
                    'id': node_id,
                    'name': f'{category.title()} ({count})',
                    'type': 'category',
                    'val': count,
                    'level': 2
                })
                node_ids.add(node_id)
                
                # Find matching priority nodes
                for task in tasks:
                    if task.calculated_priority:
                        pri_node = f'priority_{task.calculated_priority}'
                        if pri_node in node_ids:
                            links.append({'source': pri_node, 'target': node_id, 'value': 1})
                        break
        
        # Create tag nodes (top 10 most frequent)
        tag_counts = {}
        for task in tasks:
            if task.hybrid_tags:
                all_tags = task.hybrid_tags.to_list()
                for tag in all_tags:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        top_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        for tag, count in top_tags:
            node_id = f'tag_{tag}'
            nodes.append({
                'id': node_id,
                'name': f'#{tag} ({count})',
                'type': 'tag',
                'val': count,
                'level': 3,
                'tag': tag
            })
            node_ids.add(node_id)
        
        # Create account node
        if tasks:
            account_id = tasks[0].account
            nodes.append({
                'id': f'account_{account_id}',
                'name': f'{account_id.title()}',
                'type': 'account',
                'val': len(tasks),
                'level': 4
            })
            node_ids.add(f'account_{account_id}')
            links.append({'source': 'all_tasks', 'target': f'account_{account_id}', 'value': len(tasks)})
        
        # Add meta nodes at the start
        nodes = meta_nodes + nodes
        
        return {'nodes': nodes, 'links': links}
    
    # ============================================
    # ENHANCED FEATURES (Controlled by Feature Flags)
    # ============================================
    
    def __init__(self, gtasks_path: Optional[Path] = None):
        """Enhanced initialization with settings and state management"""
        self.gtasks_path = gtasks_path or self._detect_gtasks_path()
        
        # Enhanced dashboard state
        self.dashboard_state = {
            'tasks': {},
            'accounts': [],
            'stats': {},
            'hierarchy_data': {'nodes': [], 'links': []},
            'current_account': 'default',
            'account_types': [],
            'available_tags': {},
            'priority_stats': {},
            'settings': self._get_default_settings(),
            'realtime': {'connected': False, 'last_update': None}
        }
        
        # Load settings if persistence enabled
        if FEATURE_FLAGS.get('ENABLE_SETTINGS_PERSISTENCE', False):
            self._load_settings()
        
        # Initialize enhanced features
        if FEATURE_FLAGS.get('ENABLE_ACCOUNT_TYPE_FILTERS', False):
            self._generate_account_types()
    
    def _get_default_settings(self) -> Dict[str, Any]:
        """Get default dashboard settings"""
        return {
            'show_deleted_tasks': False,
            'theme': 'light',
            'notifications': True,
            'default_view': 'dashboard',
            'auto_refresh': FEATURE_FLAGS.get('ENABLE_REALTIME_UPDATES', True),
            'compact_view': False,
            'menu_visible': True,
            'menu_animation': True,
            'keyboard_shortcuts': True,
            'priority_system_enabled': FEATURE_FLAGS.get('ENABLE_PRIORITY_SYSTEM', True),
            'advanced_filters_enabled': FEATURE_FLAGS.get('ENABLE_ADVANCED_FILTERS', True),
            'reports_enabled': FEATURE_FLAGS.get('ENABLE_REPORTS', True),
            'sidebar_visible': True,
            'default_account': 'default'
        }
    
    def _load_settings(self):
        """Load user settings from file"""
        settings_file = 'enhanced_dashboard_settings.json'
        try:
            if os.path.exists(settings_file):
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
                    self.dashboard_state['settings'].update(settings)
        except Exception as e:
            print(f"⚠️  Error loading settings: {e}")
    
    def _save_settings(self):
        """Save user settings to file"""
        if not FEATURE_FLAGS.get('ENABLE_SETTINGS_PERSISTENCE', False):
            return
            
        settings_file = 'enhanced_dashboard_settings.json'
        try:
            with open(settings_file, 'w') as f:
                json.dump(self.dashboard_state['settings'], f, indent=2)
        except Exception as e:
            print(f"❌ Error saving settings: {e}")
    
    def update_settings(self, settings_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Update dashboard settings"""
        self.dashboard_state['settings'].update(settings_dict)
        self._save_settings()
        return self.dashboard_state['settings']
    
    def _generate_account_types(self):
        """Generate unique account types from detected accounts"""
        if not FEATURE_FLAGS.get('ENABLE_ACCOUNT_TYPE_FILTERS', False):
            return
            
        account_types = set()
        for account in self.dashboard_state['accounts']:
            # Account is an object, access attribute directly
            account_types.add(getattr(account, 'account_type', 'Other'))
        
        self.dashboard_state['account_types'] = sorted(list(account_types))
    
    def _categorize_account_type(self, account_name: str) -> str:
        """Categorize account based on name patterns"""
        if not FEATURE_FLAGS.get('ENABLE_ACCOUNT_TYPE_FILTERS', False):
            return 'General'
            
        account_lower = account_name.lower()
        
        for account_type, patterns in ACCOUNT_TYPE_PATTERNS.items():
            for pattern in patterns:
                if pattern in account_lower:
                    return account_type
        
        # Default categorization
        if account_lower in ['default', 'main', 'primary']:
            return 'General'
        elif any(word in account_lower for word in ['test', 'demo', 'sample']):
            return 'Testing'
        else:
            return 'Other'
    
    def detect_accounts(self) -> List[Account]:
        """Enhanced account detection with type categorization"""
        accounts = []
        
        if self.gtasks_path and self.gtasks_path.exists():
            if self.gtasks_path.is_dir():
                for item in self.gtasks_path.iterdir():
                    if item.is_dir() and item.name != 'default':
                        account_type = self._categorize_account_type(item.name)
                        accounts.append(Account(
                            id=item.name,
                            name=item.name.replace('_', ' ').title(),
                            email=f'{item.name}@example.com',
                            account_type=account_type,
                            is_active=True
                        ))
            
            # Add default account
            default_type = self._categorize_account_type('default')
            accounts.append(Account(
                id='default',
                name='Default',
                email='default@example.com',
                account_type=default_type,
                is_active=True
            ))
        
        # If no accounts found, create demo account
        if not accounts:
            accounts.append(Account(
                id='demo',
                name='Demo Account',
                email='demo@example.com',
                account_type='Testing',
                is_active=True
            ))
        
        self.dashboard_state['accounts'] = accounts
        self._generate_account_types()
        
        return accounts
    
    # ============================================
    # ADVANCED TAG FILTERING
    # ============================================
    
    def parse_tag_filter(self, tag_string: str) -> Dict[str, List[str]]:
        """Parse tag filter string with support for OR, AND, NOT operations"""
        if not FEATURE_FLAGS.get('ENABLE_ADVANCED_FILTERS', False):
            return {'or_tags': [], 'and_tags': [], 'not_tags': []}
        
        if not tag_string:
            return {'or_tags': [], 'and_tags': [], 'not_tags': []}
        
        tag_string = tag_string.strip()
        parts = tag_string.split()
        or_tags = []
        and_tags = []
        not_tags = []
        
        for part in parts:
            part = part.strip()
            if not part:
                continue
            
            # Handle NOT operation
            if part.startswith('-'):
                tag = part[1:].strip()
                if tag:
                    not_tags.append(tag.lower())
            
            # Handle AND operation
            elif '&' in part:
                and_tags.extend([t.strip().lower() for t in part.split('&') if t.strip()])
            
            # Handle OR operation
            elif '|' in part:
                or_tags.extend([t.strip().lower() for t in part.split('|') if t.strip()])
            
            # Regular tag
            else:
                or_tags.append(part.lower())
        
        return {
            'or_tags': list(set(or_tags)),
            'and_tags': list(set(and_tags)),
            'not_tags': list(set(not_tags))
        }
    
    def filter_tasks_by_tags(self, tasks: List[Task], tag_filters: Dict[str, List[str]]) -> List[Task]:
        """Filter tasks based on parsed tag filters"""
        if not FEATURE_FLAGS.get('ENABLE_ADVANCED_FILTERS', False):
            return tasks
        
        if not tag_filters or not any(tag_filters.values()):
            return tasks
        
        or_tags = tag_filters.get('or_tags', [])
        and_tags = tag_filters.get('and_tags', [])
        not_tags = tag_filters.get('not_tags', [])
        
        filtered_tasks = []
        
        for task in tasks:
            # Get all tags for this task
            task_tags = set()
            if task.hybrid_tags:
                task_tags.update(task.hybrid_tags.to_list())
            
            # Apply filters
            matches_or = True
            matches_and = True
            matches_not = True
            
            # OR filter
            if or_tags:
                matches_or = any(tag in task_tags for tag in or_tags)
            
            # AND filter
            if and_tags:
                matches_and = all(tag in task_tags for tag in and_tags)
            
            # NOT filter
            if not_tags:
                matches_not = not any(tag in task_tags for tag in not_tags)
            
            # Include task if it matches all criteria
            if matches_or and matches_and and matches_not:
                filtered_tasks.append(task)
        
        return filtered_tasks
    
    # ============================================
    # DELETED TASKS MANAGEMENT
    # ============================================
    
    def soft_delete_task(self, task_id: str, account_id: Optional[str] = None) -> bool:
        """Soft delete a task"""
        if not FEATURE_FLAGS.get('ENABLE_DELETED_TASKS', False):
            return False
            
        current_account = account_id or self.dashboard_state['current_account']
        
        if current_account in self.dashboard_state['tasks']:
            for task in self.dashboard_state['tasks'][current_account]:
                if task.id == task_id:
                    task.is_deleted = True
                    task.deleted_at = datetime.now().isoformat()
                    task.deleted_by = 'user'
                    task.status = 'deleted'
                    return True
        return False
    
    def restore_task(self, task_id: str, account_id: Optional[str] = None) -> bool:
        """Restore a deleted task"""
        if not FEATURE_FLAGS.get('ENABLE_DELETED_TASKS', False):
            return False
            
        current_account = account_id or self.dashboard_state['current_account']
        
        if current_account in self.dashboard_state['tasks']:
            for task in self.dashboard_state['tasks'][current_account]:
                if task.id == task_id:
                    task.is_deleted = False
                    task.deleted_at = None
                    task.deleted_by = None
                    task.status = 'pending'
                    return True
        return False
    
    def permanently_delete_task(self, task_id: str, account_id: Optional[str] = None) -> bool:
        """Permanently delete a task"""
        if not FEATURE_FLAGS.get('ENABLE_DELETED_TASKS', False):
            return False
            
        current_account = account_id or self.dashboard_state['current_account']
        
        if current_account in self.dashboard_state['tasks']:
            tasks = self.dashboard_state['tasks'][current_account]
            for i, task in enumerate(tasks):
                if task.id == task_id:
                    del tasks[i]
                    return True
        return False
    
    # ============================================
    # PRIORITY SYSTEM ENHANCEMENTS
    # ============================================
    
    def calculate_priority_statistics(self) -> Dict[str, Any]:
        """Calculate comprehensive priority statistics"""
        if not FEATURE_FLAGS.get('ENABLE_PRIORITY_SYSTEM', False):
            return {}
            
        priority_stats = {
            'total_tasks': 0,
            'by_priority': defaultdict(int),
            'by_source': defaultdict(int),
        }
        
        for tasks in self.dashboard_state['tasks'].values():
            for task in tasks:
                priority_stats['total_tasks'] += 1
                
                # Count by calculated priority
                priority = getattr(task, 'calculated_priority', 'low')
                priority_stats['by_priority'][priority] += 1
        
        # Convert to regular dicts
        self.dashboard_state['priority_stats'] = {
            'total_tasks': priority_stats['total_tasks'],
            'by_priority': dict(priority_stats['by_priority']),
        }
        
        return self.dashboard_state['priority_stats']
    
    # ============================================
    # TASKS DUE TODAY
    # ============================================
    
    def get_tasks_due_today(self) -> List[Task]:
        """Get tasks due today"""
        if not FEATURE_FLAGS.get('ENABLE_TASKS_DUE_TODAY', False):
            return []
            
        today = datetime.now().strftime('%Y-%m-%d')
        all_tasks = []
        
        for tasks in self.dashboard_state['tasks'].values():
            all_tasks.extend(tasks)
        
        due_today_tasks = []
        for task in all_tasks:
            if task.due == today and not getattr(task, 'is_deleted', False):
                due_today_tasks.append(task)
        
        return due_today_tasks
    
    # ============================================
    # REPORT SYSTEM
    # ============================================
    
    def get_report_types(self) -> Dict[str, Dict[str, Any]]:
        """Get all available report types"""
        if not FEATURE_FLAGS.get('ENABLE_REPORTS', False):
            return {}
        return REPORT_TYPES
    
    def generate_report(self, report_type: str, tasks: List[Task], **kwargs) -> Dict[str, Any]:
        """Generate a report (demo implementation)"""
        if not FEATURE_FLAGS.get('ENABLE_REPORTS', False):
            return {}
            
        try:
            if report_type == 'task_completion':
                return self._generate_completion_report(tasks, **kwargs)
            elif report_type == 'overdue_tasks':
                return self._generate_overdue_report(tasks)
            elif report_type == 'task_distribution':
                return self._generate_distribution_report(tasks)
            elif report_type == 'timeline':
                return self._generate_timeline_report(tasks, **kwargs)
            else:
                return self._generate_generic_report(report_type, tasks, **kwargs)
        except Exception as e:
            print(f"Error generating report {report_type}: {e}")
            return self._generate_generic_report(report_type, tasks, **kwargs)
    
    def _generate_completion_report(self, tasks: List[Task], **kwargs) -> Dict[str, Any]:
        """Generate task completion report"""
        period_days = kwargs.get('period_days', 30)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)
        
        completed_tasks = [t for t in tasks if t.status == 'completed']
        
        return {
            'report_name': 'Task Completion Report',
            'period_start': start_date.isoformat(),
            'period_end': end_date.isoformat(),
            'total_completed': len(completed_tasks),
            'completion_rate': (len(completed_tasks) / len(tasks) * 100) if tasks else 0
        }
    
    def _generate_overdue_report(self, tasks: List[Task]) -> Dict[str, Any]:
        """Generate overdue tasks report"""
        today = datetime.now().date()
        overdue_tasks = []
        
        for task in tasks:
            if (task.status != 'completed' and task.due):
                due_date = datetime.fromisoformat(task.due).date()
                if due_date < today:
                    overdue_tasks.append({
                        'id': task.id,
                        'title': task.title,
                        'due': task.due,
                        'days_overdue': (today - due_date).days
                    })
        
        return {
            'report_name': 'Overdue Tasks Report',
            'total_overdue': len(overdue_tasks),
            'overdue_tasks': overdue_tasks
        }
    
    def _generate_distribution_report(self, tasks: List[Task]) -> Dict[str, Any]:
        """Generate task distribution report"""
        from collections import Counter
        
        status_counter = Counter(t.status for t in tasks)
        priority_counter = Counter(getattr(t, 'calculated_priority', 'medium') for t in tasks)
        
        return {
            'report_name': 'Task Distribution Report',
            'total_tasks': len(tasks),
            'status_distribution': dict(status_counter),
            'priority_distribution': dict(priority_counter)
        }
    
    def _generate_timeline_report(self, tasks: List[Task], **kwargs) -> Dict[str, Any]:
        """Generate timeline report"""
        period_days = kwargs.get('period_days', 30)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)
        
        return {
            'report_name': 'Timeline Report',
            'period_start': start_date.isoformat(),
            'period_end': end_date.isoformat(),
            'total_tasks': len(tasks)
        }
    
    def _generate_generic_report(self, report_type: str, tasks: List[Task], **kwargs) -> Dict[str, Any]:
        """Generate a generic report"""
        return {
            'report_name': f'{report_type.title()} Report',
            'total_tasks': len(tasks),
            'generated_at': datetime.now().isoformat()
        }
    
    # ============================================
    # FILTERED TASKS
    # ============================================
    
    def get_filtered_tasks(self, filters: Dict[str, Any]) -> List[Task]:
        """Get tasks based on filters"""
        all_tasks = []
        for tasks in self.dashboard_state['tasks'].values():
            all_tasks.extend(tasks)
        
        filtered_tasks = all_tasks
        
        # Apply account type filters
        if filters.get('account_types') and FEATURE_FLAGS.get('ENABLE_ACCOUNT_TYPE_FILTERS', False):
            account_types = filters['account_types']
            filtered_tasks = [t for t in filtered_tasks if getattr(t, 'account_type', 'General') in account_types]
        
        # Apply status filters
        if filters.get('status'):
            status_filter = filters['status']
            filtered_tasks = [t for t in filtered_tasks if t.status in status_filter]
        
        # Apply priority filters
        if filters.get('priority') and FEATURE_FLAGS.get('ENABLE_PRIORITY_SYSTEM', False):
            priority_filter = filters['priority']
            filtered_tasks = [t for t in filtered_tasks if getattr(t, 'calculated_priority', 'low') in priority_filter]
        
        # Apply tag filters
        if filters.get('tag_filters') and FEATURE_FLAGS.get('ENABLE_ADVANCED_FILTERS', False):
            tag_filters = self.parse_tag_filter(filters['tag_filters'])
            filtered_tasks = self.filter_tasks_by_tags(filtered_tasks, tag_filters)
        
        return filtered_tasks
    
    # ============================================
    # REALTIME UPDATES
    # ============================================
    
    def setup_realtime_updates(self):
        """Setup periodic data updates (if enabled)"""
        if not FEATURE_FLAGS.get('ENABLE_REALTIME_UPDATES', False):
            return
            
        def update_loop():
            while True:
                time.sleep(60)  # Update every minute
                print("🔄 Updating dashboard data...")
                try:
                    self.refresh_data()
                    print("✅ Dashboard data updated successfully")
                except Exception as e:
                    print(f"❌ Error during update: {e}")
        
        thread = threading.Thread(target=update_loop, daemon=True)
        thread.start()
        self.dashboard_state['realtime']['connected'] = True
        print("✅ Realtime updates started")
    
    def refresh_data(self):
        """Refresh all dashboard data"""
        self.detect_accounts()
        
        for account in self.dashboard_state['accounts']:
            tasks = self.load_tasks_for_account(account.id)
            self.dashboard_state['tasks'][account.id] = tasks
        
        # Calculate priority stats if enabled
        if FEATURE_FLAGS.get('ENABLE_PRIORITY_SYSTEM', False):
            self.calculate_priority_statistics()
        
        # Update hierarchy data
        all_tasks = []
        for tasks in self.dashboard_state['tasks'].values():
            all_tasks.extend(tasks)
        self.dashboard_state['hierarchy_data'] = self.get_hierarchy_data(all_tasks)
        
        self.dashboard_state['realtime']['last_update'] = datetime.now().isoformat()
        
        return self.dashboard_state
