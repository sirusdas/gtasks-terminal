#!/usr/bin/env python3
"""
GTasks Dashboard - Data Manager Module
Handles data loading, processing, and hierarchy creation
"""

import os
import json
import sqlite3
import datetime
import re
from pathlib import Path
from collections import defaultdict

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

class GTasksDataManager:
    def __init__(self):
        self.setup_paths()
        self.dashboard_data = {
            'tasks': {},
            'accounts': [],
            'stats': {},
            'hierarchy_data': {'nodes': [], 'links': []},
            'current_account': 'default',
            'tag_categories': {},
            'realtime': {'connected': False, 'last_update': None}
        }
    
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
        print(f"✅ Detected {len(accounts)} accounts")
        for account in accounts:
            print(f"  - {account['name']} ({account['id']})")
        
        return accounts
    
    def get_account_info(self, account_name):
        """Get information about a specific account"""
        account_path = self.gtasks_path / account_name if self.gtasks_path else None
        
        db_files = []
        if account_path and account_path.exists():
            db_files = list(account_path.glob('*.db'))
        
        has_data = len(db_files) > 0 or (account_path and (account_path / 'tasks.db').exists())
        
        return {
            'id': account_name,
            'name': account_name.replace('_', ' ').title(),
            'email': f'{account_name}@example.com',
            'isActive': has_data,
            'taskCount': 0,
            'completedCount': 0,
            'hasDatabase': len(db_files) > 0,
            'stats': {}
        }
    
    def load_tasks_for_account(self, account_name):
        """Load tasks for a specific account"""
        tasks = []
        
        if not self.gtasks_path:
            return self.get_demo_tasks()
        
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
        
        return tasks if tasks else self.get_demo_tasks_for_account(account_name)
    
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
                    'dependencies': json.loads(row[10]) if len(row) > 10 and row[10] else []
                }
                tasks.append(task)
            
            conn.close()
            print(f"✅ Loaded {len(tasks)} tasks from {db_path}")
            
        except Exception as e:
            print(f"❌ Error loading from SQLite {db_path}: {e}")
            
        return tasks
    
    def get_demo_tasks_for_account(self, account_name):
        """Generate comprehensive demo tasks with all CLI features"""
        demo_tasks = [
            {
                'id': f'{account_name}_1', 
                'title': f'Implement #API endpoint for @john #UAT', 
                'description': 'Create REST API with comprehensive testing',
                'due': '2024-01-15', 'priority': 'high', 'status': 'pending',
                'project': 'API', 'tags': ['api', 'development'], 
                'notes': 'Use #Docker for containerization @alice will review [urgent]',
                'list_name': 'Development',
                'account': account_name, 'created_at': '2024-01-10T10:00:00Z',
                'recurrence_rule': None,
                'dependencies': [],
                'estimated_duration': 480
            },
            {
                'id': f'{account_name}_2', 
                'title': f'Fix critical #Bug in #Frontend @mou',
                'description': 'Memory leak affecting user experience',
                'due': '2024-01-12', 'priority': 'critical', 'status': 'in_progress',
                'project': 'Frontend', 'tags': ['bug', 'ui'], 
                'notes': '[P0] needs immediate attention',
                'list_name': 'Bugs',
                'account': account_name, 'created_at': '2024-01-09T14:30:00Z',
                'recurrence_rule': None,
                'dependencies': [],
                'estimated_duration': 240
            },
            {
                'id': f'{account_name}_3', 
                'title': f'#Feature: Dark mode implementation @bob',
                'description': 'User requested dark theme for better accessibility',
                'due': '2024-01-20', 'priority': 'medium', 'status': 'pending',
                'project': 'UI', 'tags': ['feature', 'theme'], 
                'notes': 'Test on #Staging before #Production deployment',
                'list_name': 'Features',
                'account': account_name, 'created_at': '2024-01-08T09:15:00Z',
                'recurrence_rule': None,
                'dependencies': [f'{account_name}_2'],
                'estimated_duration': 360
            }
        ]
        return demo_tasks
    
    def get_demo_tasks(self):
        """Generate demo tasks for when no real data is available"""
        return self.get_demo_tasks_for_account('default')
    
    def load_all_data(self):
        """Load data for all detected accounts"""
        accounts = self.detect_accounts()
        
        for account in accounts:
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
            
            # Calculate account stats
            total_tasks = len(tasks)
            completed_tasks = len([t for t in tasks if t.get('status') == 'completed'])
            
            account['taskCount'] = total_tasks
            account['completedCount'] = completed_tasks
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
    
    def calculate_stats(self, tasks):
        """Calculate comprehensive dashboard statistics"""
        total = len(tasks)
        completed = len([t for t in tasks if t.get('status') == 'completed'])
        pending = len([t for t in tasks if t.get('status') == 'pending'])
        in_progress = len([t for t in tasks if t.get('status') == 'in_progress'])
        
        # Overdue tasks
        today = datetime.datetime.now().date()
        overdue = len([t for t in tasks if t.get('due') and 
                     datetime.datetime.fromisoformat(t['due']).date() < today and 
                     t.get('status') != 'completed'])
        
        # High priority tasks
        high_priority = len([t for t in tasks if t.get('priority') in ['high', 'critical']])
        
        # Recurring tasks
        recurring = len([t for t in tasks if t.get('is_recurring')])
        
        completion_rate = (completed / total * 100) if total > 0 else 0
        
        return {
            'totalTasks': total,
            'completedTasks': completed,
            'pendingTasks': pending,
            'inProgressTasks': in_progress,
            'overdueTasks': overdue,
            'highPriorityTasks': high_priority,
            'recurringTasks': recurring,
            'completionRate': completion_rate
        }
    
    def create_hierarchy_data(self):
        """Create hierarchical data for D3.js Force Graph"""
        nodes = []
        links = []
        
        # Get all tasks from all accounts
        all_tasks = []
        for tasks in self.dashboard_data['tasks'].values():
            all_tasks.extend(tasks)
        
        if not all_tasks:
            return {'nodes': [], 'links': []}
        
        # Count tag occurrences
        tag_counts = defaultdict(int)
        category_counts = defaultdict(int)
        task_tag_mapping = defaultdict(list)
        
        for task in all_tasks:
            task_id = task['id']
            
            # Process categorized tags
            for category, tags in task.get('categorized_tags', {}).items():
                category_counts[category] += 1
                
                for tag in tags:
                    tag_counts[tag] += 1
                    task_tag_mapping[category].append(tag)
        
        # Create category nodes
        category_nodes = []
        for category, count in category_counts.items():
            node_id = f"category_{category.lower().replace(' ', '_')}"
            category_nodes.append({
                'id': node_id,
                'name': category,
                'group': 1,
                'val': count * 3,
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
                'val': count + 5,
                'level': 'tag',
                'type': 'tag',
                'category': category
            })
        
        # Create task nodes (sample for performance)
        task_nodes = []
        for task in all_tasks[:100]:  # Limit to first 100 tasks for performance
            node_id = f"task_{task['id']}"
            
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
                'val': 8,
                'level': 'task',
                'type': 'task',
                'task_id': task['id'],
                'status': task.get('status', 'pending'),
                'priority': task.get('priority', 'medium'),
                'tag': primary_tag,
                'account': task.get('account', 'default')
            })
        
        # Combine all nodes
        nodes = category_nodes + tag_nodes + task_nodes
        
        # Create links
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
            'categories': list(category_counts.keys()),
            'stats': {
                'total_categories': len(category_counts),
                'total_tags': len(tag_counts),
                'total_tasks': len(all_tasks),
                'tag_distribution': dict(tag_counts)
            }
        }
        
        self.dashboard_data['hierarchy_data'] = hierarchy_data
        print(f"✅ Created hierarchy data: {len(nodes)} nodes, {len(links)} links")
        
        return hierarchy_data
    
    def get_dashboard_data(self):
        """Get the current dashboard data"""
        return self.dashboard_data
    
    def refresh_data(self):
        """Refresh all dashboard data"""
        self.load_all_data()
        self.create_hierarchy_data()
        return self.dashboard_data
    
    def switch_account(self, account_id):
        """Switch current account"""
        if account_id in [a['id'] for a in self.dashboard_data['accounts']]:
            self.dashboard_data['current_account'] = account_id
            return True
        return False