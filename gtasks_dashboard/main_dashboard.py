#!/usr/bin/env python3
"""
GTasks Dashboard - Main Entry Point

A clean, centralized dashboard that consolidates all features:
- Multi-Account Management
- Advanced Tags Filtering
- Priority System
- Task Management
- API Endpoints

Author: GTasks Dashboard Team
Date: January 11, 2026
"""

import os
import sys
import json
import datetime
import sqlite3
import re
from pathlib import Path
from flask import Flask, jsonify, request, render_template_string

# Configuration
app = Flask(__name__)

# Global dashboard state
DASHBOARD_STATE = {
    'tasks': {},
    'accounts': [],
    'current_account': 'default',
    'settings': {},
    'stats': {}
}

# Category mapping for tags
CATEGORIES = {
    'Team': ['@john', '@alice', '@bob', '@mou', '@devteam'],
    'UAT': ['#UAT', '#Testing', '#QA', '#Test', '#Validation'],
    'Production': ['#Live', '#Hotfix', '#Production', '#Deploy', '#Release'],
    'Priority': ['#High', '#Critical', '[p1]', '[urgent]', '#P0', '#P1'],
    'Projects': ['#API', '#Frontend', '#Backend', '#Mobile', '#Web', '#Database'],
    'Status': ['#InProgress', '#Blocked', '#Done', '#Review', '#Testing'],
    'Environment': ['#Dev', '#Staging', '#Prod', '#Development', '#Production'],
    'Type': ['#Bug', '#Feature', '#Enhancement', '#Refactor', '#Documentation'],
}


class GTasksDashboard:
    """Main dashboard class managing all features"""
    
    def __init__(self):
        self.gtasks_path = self._detect_gtasks_path()
        self.load_data()
    
    def _detect_gtasks_path(self):
        """Detect GTasks CLI path"""
        home_path = Path.home() / '.gtasks'
        project_path = Path('./gtasks_cli')
        
        if home_path.exists():
            return home_path
        elif project_path.exists():
            return project_path
        return None
    
    def _extract_tags(self, text):
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
    
    def _categorize_tag(self, tag):
        """Categorize a tag"""
        tag_lower = tag.lower()
        for category, tag_list in CATEGORIES.items():
            if tag_lower in [t.lower() for t in tag_list]:
                return category
        return 'Tags' if tag.startswith('#') else 'Team' if tag.startswith('@') else 'Legacy'
    
    def detect_accounts(self):
        """Detect all configured accounts"""
        accounts = []
        
        if self.gtasks_path and self.gtasks_path.exists():
            if self.gtasks_path.is_dir():
                for item in self.gtasks_path.iterdir():
                    if item.is_dir() and item.name != 'default':
                        accounts.append({
                            'id': item.name,
                            'name': item.name.replace('_', ' ').title(),
                            'email': f'{item.name}@example.com',
                            'type': 'Other',
                            'isActive': True,
                            'taskCount': 0,
                            'completedCount': 0
                        })
            
            accounts.append({
                'id': 'default',
                'name': 'Default',
                'email': 'default@example.com',
                'type': 'General',
                'isActive': True,
                'taskCount': 0,
                'completedCount': 0
            })
        
        if not accounts:
            accounts.append({
                'id': 'demo',
                'name': 'Demo Account',
                'email': 'demo@example.com',
                'type': 'Testing',
                'isActive': True,
                'taskCount': 0,
                'completedCount': 0
            })
        
        return accounts
    
    def _calculate_priority(self, title):
        """Calculate priority from asterisks in title"""
        asterisk_count = len(re.findall(r'\*+', title))
        if asterisk_count >= 6:
            return 'critical'
        elif asterisk_count >= 4:
            return 'high'
        elif asterisk_count >= 3:
            return 'medium'
        return 'low'
    
    def load_data(self):
        """Load all dashboard data"""
        self.accounts = self.detect_accounts()
        DASHBOARD_STATE['accounts'] = self.accounts
        
        # Load tasks for each account
        for account in self.accounts:
            tasks = self._load_tasks(account['id'])
            DASHBOARD_STATE['tasks'][account['id']] = tasks
        
        self._calculate_stats()
        print(f"✅ Dashboard loaded: {len(self.accounts)} accounts")
    
    def _load_tasks(self, account_id):
        """Load tasks from database or return demo tasks"""
        tasks = []
        if not self.gtasks_path:
            return self._get_demo_tasks()
        
        db_path = self.gtasks_path / account_id / 'tasks.db'
        if not db_path.exists():
            db_path = self.gtasks_path / 'tasks.db'
        
        if db_path.exists():
            try:
                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()
                cursor.execute("SELECT id, title, description, due, priority, status, tags, notes FROM tasks")
                rows = cursor.fetchall()
                
                for row in rows:
                    task = {
                        'id': row[0],
                        'title': row[1],
                        'description': row[2] or '',
                        'due': row[3],
                        'priority': row[4] or 'medium',
                        'status': row[5] or 'pending',
                        'tags': json.loads(row[6]) if row[6] else [],
                        'notes': row[7] or '',
                        'account': account_id
                    }
                    # Extract hybrid tags
                    task['hybrid_tags'] = self._extract_tags(
                        f"{task['title']} {task['description']} {task['notes']}"
                    )
                    # Calculate priority from asterisks
                    task['calculated_priority'] = self._calculate_priority(task['title'])
                    tasks.append(task)
                
                conn.close()
            except Exception as e:
                print(f"⚠️  Error loading tasks for {account_id}: {e}")
        
        return tasks if tasks else self._get_demo_tasks()
    
    def _get_demo_tasks(self):
        """Generate demo tasks"""
        return [
            {
                'id': 'demo_1',
                'title': 'Review #API implementation @john [*****high]',
                'description': 'Code review for new API endpoints',
                'due': '2024-01-15',
                'priority': 'high',
                'status': 'pending',
                'tags': ['api', 'review'],
                'notes': 'Use #Docker for testing',
                'account': 'demo',
                'hybrid_tags': {'bracket': ['high'], 'hash': ['api', 'docker'], 'user': ['john']},
                'calculated_priority': 'high'
            },
            {
                'id': 'demo_2',
                'title': 'Fix #Bug in #Frontend @mou [******critical]',
                'description': 'Memory leak in dashboard',
                'due': '2024-01-12',
                'priority': 'critical',
                'status': 'in_progress',
                'tags': ['bug', 'frontend'],
                'notes': '[P0] production issue',
                'account': 'demo',
                'hybrid_tags': {'bracket': ['critical'], 'hash': ['bug', 'frontend'], 'user': ['mou']},
                'calculated_priority': 'critical'
            },
            {
                'id': 'demo_3',
                'title': '#Feature: Dark mode implementation @bob [***medium]',
                'description': 'User requested dark theme for accessibility',
                'due': '2024-01-20',
                'priority': 'medium',
                'status': 'pending',
                'tags': ['feature', 'theme'],
                'notes': 'Test on #Staging',
                'account': 'demo',
                'hybrid_tags': {'bracket': ['medium'], 'hash': ['feature', 'theme', 'staging'], 'user': ['bob']},
                'calculated_priority': 'medium'
            },
            {
                'id': 'demo_4',
                'title': 'Database optimization @alice [****high]',
                'description': 'Optimize slow queries',
                'due': '2024-01-18',
                'priority': 'high',
                'status': 'pending',
                'tags': ['database', 'optimization'],
                'notes': 'Focus on #Production',
                'account': 'demo',
                'hybrid_tags': {'bracket': ['high'], 'hash': ['production'], 'user': ['alice']},
                'calculated_priority': 'high'
            }
        ]
    
    def _calculate_stats(self):
        """Calculate dashboard statistics"""
        all_tasks = []
        for tasks in DASHBOARD_STATE['tasks'].values():
            all_tasks.extend(tasks)
        
        DASHBOARD_STATE['stats'] = {
            'total': len(all_tasks),
            'completed': len([t for t in all_tasks if t.get('status') == 'completed']),
            'pending': len([t for t in all_tasks if t.get('status') == 'pending']),
            'in_progress': len([t for t in all_tasks if t.get('status') == 'in_progress']),
            'critical': len([t for t in all_tasks if t.get('calculated_priority') == 'critical']),
            'high': len([t for t in all_tasks if t.get('calculated_priority') == 'high'])
        }
    
    def get_tasks(self, account_id=None, filters=None):
        """Get tasks with optional filters"""
        account_id = account_id or DASHBOARD_STATE['current_account']
        tasks = DASHBOARD_STATE['tasks'].get(account_id, [])
        
        if filters:
            if filters.get('status'):
                tasks = [t for t in tasks if t.get('status') == filters['status']]
            if filters.get('priority'):
                tasks = [t for t in tasks if t.get('calculated_priority') == filters['priority']]
            if filters.get('search'):
                search = filters['search'].lower()
                tasks = [t for t in tasks if search in t.get('title', '').lower()]
        
        return tasks
    
    def get_accounts(self):
        """Get all accounts"""
        return DASHBOARD_STATE['accounts']
    
    def get_stats(self):
        """Get dashboard statistics"""
        return DASHBOARD_STATE['stats']


# Initialize dashboard
dashboard = GTasksDashboard()


# ========== FLASK ROUTES ==========

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GTasks Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        .priority-critical { background-color: #fef2f2; color: #dc2626; }
        .priority-high { background-color: #fff7ed; color: #ea580c; }
        .priority-medium { background-color: #fefce8; color: #ca8a04; }
        .priority-low { background-color: #f8fafc; color: #64748b; }
    </style>
</head>
<body class="bg-gray-100 min-h-screen">
    <header class="bg-gradient-to-r from-purple-600 to-blue-600 text-white py-4">
        <div class="container mx-auto px-4">
            <h1 class="text-2xl font-bold">
                <i class="fas fa-tasks mr-2"></i>GTasks Dashboard
            </h1>
        </div>
    </header>
    
    <div class="container mx-auto px-4 py-8">
        <!-- Stats Cards -->
        <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4 mb-8">
            <div class="bg-white rounded-lg shadow p-4 text-center">
                <div class="text-2xl font-bold text-blue-600" id="totalTasks">-</div>
                <div class="text-gray-600 text-sm">Total</div>
            </div>
            <div class="bg-white rounded-lg shadow p-4 text-center">
                <div class="text-2xl font-bold text-green-600" id="completedTasks">-</div>
                <div class="text-gray-600 text-sm">Completed</div>
            </div>
            <div class="bg-white rounded-lg shadow p-4 text-center">
                <div class="text-2xl font-bold text-yellow-600" id="pendingTasks">-</div>
                <div class="text-gray-600 text-sm">Pending</div>
            </div>
            <div class="bg-white rounded-lg shadow p-4 text-center">
                <div class="text-2xl font-bold text-blue-500" id="inProgressTasks">-</div>
                <div class="text-gray-600 text-sm">In Progress</div>
            </div>
            <div class="bg-white rounded-lg shadow p-4 text-center">
                <div class="text-2xl font-bold text-red-600" id="criticalTasks">-</div>
                <div class="text-gray-600 text-sm">Critical</div>
            </div>
            <div class="bg-white rounded-lg shadow p-4 text-center">
                <div class="text-2xl font-bold text-purple-600" id="accountsCount">-</div>
                <div class="text-gray-600 text-sm">Accounts</div>
            </div>
        </div>
        
        <!-- Filters -->
        <div class="bg-white rounded-lg shadow p-4 mb-6">
            <div class="flex flex-wrap gap-4">
                <input type="text" id="searchInput" placeholder="Search tasks..." 
                       class="border rounded px-3 py-2 flex-1 min-w-48"
                       onkeyup="filterTasks()">
                <select id="statusFilter" onchange="filterTasks()" class="border rounded px-3 py-2">
                    <option value="">All Status</option>
                    <option value="pending">Pending</option>
                    <option value="completed">Completed</option>
                    <option value="in_progress">In Progress</option>
                </select>
                <select id="priorityFilter" onchange="filterTasks()" class="border rounded px-3 py-2">
                    <option value="">All Priorities</option>
                    <option value="critical">Critical</option>
                    <option value="high">High</option>
                    <option value="medium">Medium</option>
                    <option value="low">Low</option>
                </select>
                <select id="accountFilter" onchange="filterTasks()" class="border rounded px-3 py-2">
                    <option value="">All Accounts</option>
                </select>
            </div>
        </div>
        
        <!-- Tasks Table -->
        <div class="bg-white rounded-lg shadow p-6">
            <h2 class="text-xl font-bold mb-4">Tasks</h2>
            <div class="overflow-x-auto">
                <table class="w-full">
                    <thead>
                        <tr class="bg-gray-100">
                            <th class="px-4 py-2 text-left">Title</th>
                            <th class="px-4 py-2 text-left">Status</th>
                            <th class="px-4 py-2 text-left">Priority</th>
                            <th class="px-4 py-2 text-left">Due</th>
                            <th class="px-4 py-2 text-left">Tags</th>
                        </tr>
                    </thead>
                    <tbody id="tasksTable">
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    
    <script>
        let allTasks = [];
        
        async function loadDashboard() {
            const response = await fetch('/api/data');
            const data = await response.json();
            
            document.getElementById('totalTasks').textContent = data.stats.total;
            document.getElementById('completedTasks').textContent = data.stats.completed;
            document.getElementById('pendingTasks').textContent = data.stats.pending;
            document.getElementById('inProgressTasks').textContent = data.stats.in_progress;
            document.getElementById('criticalTasks').textContent = data.stats.critical;
            document.getElementById('accountsCount').textContent = data.accounts.length;
            
            // Populate account filter
            const accountSelect = document.getElementById('accountFilter');
            data.accounts.forEach(acc => {
                const option = document.createElement('option');
                option.value = acc.id;
                option.textContent = acc.name;
                accountSelect.appendChild(option);
            });
            
            allTasks = data.tasks;
            renderTasks(allTasks);
        }
        
        function renderTasks(tasks) {
            const table = document.getElementById('tasksTable');
            table.innerHTML = '';
            
            tasks.forEach(task => {
                const row = document.createElement('tr');
                row.className = 'border-b hover:bg-gray-50';
                
                const priorityClass = `priority-${task.calculated_priority || 'low'}`;
                const statusClass = task.status === 'completed' ? 'bg-green-100 text-green-800' :
                                   task.status === 'in_progress' ? 'bg-blue-100 text-blue-800' :
                                   'bg-yellow-100 text-yellow-800';
                
                // Extract tags from hybrid_tags
                const tags = task.hybrid_tags ? 
                    [...task.hybrid_tags.bracket, ...task.hybrid_tags.hash, ...task.hybrid_tags.user] : 
                    (task.tags || []);
                
                row.innerHTML = `
                    <td class="px-4 py-2">
                        <div class="font-medium">${task.title}</div>
                        <div class="text-sm text-gray-500">${task.description || ''}</div>
                    </td>
                    <td class="px-4 py-2">
                        <span class="px-2 py-1 rounded text-xs ${statusClass}">${task.status}</span>
                    </td>
                    <td class="px-4 py-2">
                        <span class="px-2 py-1 rounded text-xs ${priorityClass}">${task.calculated_priority || task.priority}</span>
                    </td>
                    <td class="px-4 py-2 text-sm">${task.due || '-'}</td>
                    <td class="px-4 py-2">
                        <div class="flex flex-wrap gap-1">
                            ${tags.slice(0, 3).map(t => `<span class="text-xs bg-gray-200 px-1 rounded">${t}</span>`).join('')}
                            ${tags.length > 3 ? `<span class="text-xs">+${tags.length - 3}</span>` : ''}
                        </div>
                    </td>
                `;
                table.appendChild(row);
            });
        }
        
        function filterTasks() {
            const search = document.getElementById('searchInput').value.toLowerCase();
            const status = document.getElementById('statusFilter').value;
            const priority = document.getElementById('priorityFilter').value;
            const account = document.getElementById('accountFilter').value;
            
            let filtered = allTasks;
            
            if (search) {
                filtered = filtered.filter(t => 
                    t.title.toLowerCase().includes(search) || 
                    (t.description && t.description.toLowerCase().includes(search))
                );
            }
            if (status) {
                filtered = filtered.filter(t => t.status === status);
            }
            if (priority) {
                filtered = filtered.filter(t => (t.calculated_priority || t.priority) === priority);
            }
            if (account) {
                filtered = filtered.filter(t => t.account === account);
            }
            
            renderTasks(filtered);
        }
        
        loadDashboard();
    </script>
</body>
</html>
    ''')


@app.route('/api/data')
def api_data():
    """API endpoint for dashboard data"""
    return jsonify({
        'tasks': dashboard.get_tasks(),
        'accounts': dashboard.get_accounts(),
        'stats': dashboard.get_stats()
    })


@app.route('/api/tasks', methods=['GET'])
def api_tasks():
    """API endpoint for tasks with filters"""
    filters = {}
    if request.args.get('status'):
        filters['status'] = request.args.get('status')
    if request.args.get('priority'):
        filters['priority'] = request.args.get('priority')
    if request.args.get('search'):
        filters['search'] = request.args.get('search')
    
    return jsonify({
        'tasks': dashboard.get_tasks(filters=filters),
        'total': len(dashboard.get_tasks())
    })


@app.route('/api/accounts', methods=['GET'])
def api_accounts():
    """API endpoint for accounts"""
    return jsonify({
        'accounts': dashboard.get_accounts()
    })


@app.route('/api/stats', methods=['GET'])
def api_stats():
    """API endpoint for statistics"""
    return jsonify({
        'stats': dashboard.get_stats()
    })


@app.route('/api/health')
def api_health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.datetime.now().isoformat()
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("🚀 Starting GTasks Dashboard...")
    print(f"📊 Dashboard available at http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=True)
