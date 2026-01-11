"""
Account Management Module for GTasks Dashboard

This module handles all account-related functionality including:
- Account detection and categorization
- Account type filtering
- Multi-account data loading

Author: GTasks Dashboard Team
Date: January 11, 2026
"""

import os
import sqlite3
import json
from pathlib import Path
from collections import defaultdict


class AccountManager:
    """Manages account detection, categorization, and data loading"""
    
    def __init__(self, gtasks_path=None):
        self.gtasks_home = Path.home() / '.gtasks'
        self.project_gtasks_path = Path('./gtasks_cli')
        
        if gtasks_path:
            self.gtasks_path = Path(gtasks_path)
        elif self.gtasks_home.exists():
            self.gtasks_path = self.gtasks_home
        elif self.project_gtasks_path.exists():
            self.gtasks_path = self.project_gtasks_path
        else:
            self.gtasks_path = None
            print("⚠️  GTasks CLI not found. Using demo data.")
        
        # Account type categorization patterns
        self.account_type_patterns = {
            'Work': ['work', 'office', 'business', 'company', 'job', 'professional', 'corp'],
            'Personal': ['personal', 'home', 'private', 'life', 'family', 'me'],
            'Learning': ['learning', 'study', 'education', 'course', 'training', 'book'],
            'Health': ['health', 'fitness', 'medical', 'doctor', 'gym', 'exercise'],
            'Finance': ['finance', 'money', 'bank', 'investment', 'budget', 'tax'],
            'Social': ['social', 'friends', 'family', 'event', 'party', 'meeting']
        }
    
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
            accounts.append(self._create_demo_account())
        
        return accounts
    
    def _create_demo_account(self):
        """Create a demo account when no real accounts are found"""
        return {
            'id': 'demo',
            'name': 'Demo Account',
            'email': 'demo@example.com',
            'type': 'General',
            'isActive': True,
            'taskCount': 0,
            'completedCount': 0,
            'hasDatabase': False,
            'stats': {}
        }
    
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
        
        for account_type, patterns in self.account_type_patterns.items():
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
    
    def generate_account_types(self, accounts):
        """Generate unique account types from detected accounts"""
        account_types = set()
        for account in accounts:
            account_types.add(account.get('type', 'Other'))
        
        return sorted(list(account_types))
    
    def load_tasks_for_account(self, account_name):
        """Load tasks for a specific account"""
        tasks = []
        
        if not self.gtasks_path:
            return self._get_demo_tasks()
        
        if account_name == 'demo':
            return self._get_demo_tasks()
        
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
                    tasks = self._load_from_sqlite(db_path, account_name)
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
        
        return tasks if tasks else self._get_demo_tasks()
    
    def _load_from_sqlite(self, db_path, account_name):
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
    
    def _get_demo_tasks(self):
        """Generate demo tasks for testing"""
        return [
            {
                'id': 'demo_1', 
                'title': 'Implement API endpoint for user authentication',
                'description': 'Create REST API with comprehensive testing',
                'due': '2024-01-15', 'priority': 'high', 'status': 'pending',
                'project': 'API', 'tags': ['api', 'development'], 
                'notes': 'Use Docker for containerization and testing',
                'list_name': 'Development',
                'account': 'demo', 'created_at': '2024-01-10T10:00:00Z',
                'recurrence_rule': None,
                'dependencies': [],
                'estimated_duration': 480,
                'is_deleted': False,
                'deleted_at': None,
                'deleted_by': None
            }
        ]