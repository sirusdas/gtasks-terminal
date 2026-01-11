#!/usr/bin/env python3
"""
GTasks Dashboard - API Handlers Module
Handles all Flask API endpoints for the dashboard
"""

from flask import Flask, jsonify, request
from data_manager import GTasksDataManager

class GTasksAPIHandlers:
    def __init__(self, app: Flask, data_manager: GTasksDataManager):
        self.app = app
        self.data_manager = data_manager
        self.setup_routes()
    
    def setup_routes(self):
        """Setup all API routes"""
        
        @self.app.route('/api/dashboard')
        def api_dashboard():
            """API endpoint for dashboard data"""
            return jsonify({
                'success': True,
                'data': {
                    'stats': self.data_manager.dashboard_data['stats'],
                    'tasks': self.data_manager.dashboard_data['tasks'],
                    'accounts': self.data_manager.dashboard_data['accounts'],
                    'current_account': self.data_manager.dashboard_data['current_account'],
                    'hierarchy_data': self.data_manager.dashboard_data['hierarchy_data']
                }
            })
        
        @self.app.route('/api/tasks', methods=['GET'])
        def api_get_tasks():
            """Get tasks with filtering options"""
            account = request.args.get('account', self.data_manager.dashboard_data['current_account'])
            status = request.args.get('status')
            priority = request.args.get('priority')
            search = request.args.get('search')
            
            tasks = self.data_manager.dashboard_data['tasks'].get(account, [])
            
            # Apply filters
            if status:
                tasks = [t for t in tasks if t.get('status') == status]
            if priority:
                tasks = [t for t in tasks if t.get('priority') == priority]
            if search:
                tasks = [t for t in tasks if search.lower() in t.get('title', '').lower() or 
                        search.lower() in t.get('description', '').lower()]
            
            return jsonify({'success': True, 'data': tasks})
        
        @self.app.route('/api/tasks', methods=['POST'])
        def api_create_task():
            """Create a new task"""
            data = request.get_json()
            
            # Here you would implement task creation logic
            # For now, just return success
            return jsonify({'success': True, 'message': 'Task created successfully'})
        
        @self.app.route('/api/tasks/<task_id>', methods=['PUT'])
        def api_update_task(task_id):
            """Update an existing task"""
            data = request.get_json()
            
            # Here you would implement task update logic
            return jsonify({'success': True, 'message': 'Task updated successfully'})
        
        @self.app.route('/api/tasks/<task_id>', methods=['DELETE'])
        def api_delete_task(task_id):
            """Delete a task"""
            # Here you would implement task deletion logic
            return jsonify({'success': True, 'message': 'Task deleted successfully'})
        
        @self.app.route('/api/switch_account', methods=['POST'])
        def api_switch_account():
            """Switch current account"""
            data = request.get_json()
            account = data.get('account')
            
            if self.data_manager.switch_account(account):
                return jsonify({'success': True, 'message': f'Switched to account: {account}'})
            
            return jsonify({'success': False, 'message': 'Account not found'}), 400
        
        @self.app.route('/api/refresh', methods=['POST'])
        def api_refresh():
            """Refresh dashboard data"""
            try:
                self.data_manager.refresh_data()
                return jsonify({'success': True, 'message': 'Data refreshed successfully'})
            except Exception as e:
                return jsonify({'success': False, 'message': f'Error refreshing data: {str(e)}'}), 500
        
        @self.app.route('/api/accounts', methods=['GET'])
        def api_get_accounts():
            """Get all accounts"""
            return jsonify({
                'success': True,
                'data': self.data_manager.dashboard_data['accounts']
            })
        
        @self.app.route('/api/stats', methods=['GET'])
        def api_get_stats():
            """Get dashboard statistics"""
            return jsonify({
                'success': True,
                'data': self.data_manager.dashboard_data['stats']
            })
        
        @self.app.route('/api/hierarchy', methods=['GET'])
        def api_get_hierarchy():
            """Get hierarchy data"""
            return jsonify({
                'success': True,
                'data': self.data_manager.dashboard_data['hierarchy_data']
            })
        
        @self.app.route('/api/settings', methods=['GET'])
        def api_get_settings():
            """Get dashboard settings"""
            # Return default settings for now
            return jsonify({
                'success': True,
                'data': {
                    'show_deleted_tasks': False,
                    'default_account': self.data_manager.dashboard_data['current_account'],
                    'refresh_interval': 60,
                    'theme': 'light'
                }
            })
        
        @self.app.route('/api/settings', methods=['POST'])
        def api_update_settings():
            """Update dashboard settings"""
            data = request.get_json()
            # Here you would save settings to a file or database
            return jsonify({'success': True, 'message': 'Settings updated successfully'})
        
        @self.app.route('/api/export', methods=['GET'])
        def api_export_tasks():
            """Export all tasks"""
            all_tasks = []
            for tasks in self.data_manager.dashboard_data['tasks'].values():
                all_tasks.extend(tasks)
            
            return jsonify({
                'success': True,
                'data': all_tasks,
                'export_count': len(all_tasks)
            })