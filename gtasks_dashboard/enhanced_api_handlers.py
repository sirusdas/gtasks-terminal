#!/usr/bin/env python3
"""
GTasks Dashboard - Enhanced API Handlers Module
Handles all Flask API endpoints for the comprehensive dashboard with all 10 features:
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

from flask import Flask, jsonify, request
from enhanced_data_manager import GTasksEnhancedDataManager

class GTasksEnhancedAPIHandlers:
    def __init__(self, app: Flask, data_manager: GTasksEnhancedDataManager):
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
                'data': self.data_manager.dashboard_data
            })
        
        @self.app.route('/api/tasks', methods=['GET'])
        def api_get_tasks():
            """Get tasks with filtering options"""
            account = request.args.get('account', self.data_manager.dashboard_data['current_account'])
            status = request.args.get('status')
            priority = request.args.get('priority')
            search = request.args.get('search')
            tag_filters = request.args.get('tag_filters')
            include_deleted = request.args.get('include_deleted', 'false').lower() == 'true'
            
            tasks = self.data_manager.dashboard_data['tasks'].get(account, [])
            
            # Apply filters
            if status:
                tasks = [t for t in tasks if t.get('status') == status]
            if priority:
                tasks = [t for t in tasks if t.get('calculated_priority') == priority]
            if search:
                tasks = [t for t in tasks if search.lower() in t.get('title', '').lower() or 
                        search.lower() in t.get('description', '').lower()]
            if tag_filters:
                parsed_filters = self.data_manager.parse_tag_filter(tag_filters)
                tasks = self.data_manager.filter_tasks_by_tags(tasks, parsed_filters)
            if not include_deleted:
                tasks = [t for t in tasks if not t.get('is_deleted', False)]
            
            return jsonify({'success': True, 'data': tasks})
        
        @self.app.route('/api/tasks', methods=['POST'])
        def api_create_task():
            """Create a new task"""
            data = request.get_json()
            account_id = data.get('account_id', self.data_manager.dashboard_data['current_account'])
            
            try:
                task = self.data_manager.create_task(data, account_id)
                return jsonify({
                    'success': True, 
                    'data': task,
                    'message': 'Task created successfully'
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f'Error creating task: {str(e)}'
                }), 500
        
        @self.app.route('/api/tasks/<task_id>', methods=['PUT'])
        def api_update_task(task_id):
            """Update an existing task"""
            data = request.get_json()
            account_id = data.get('account_id', self.data_manager.dashboard_data['current_account'])
            
            try:
                task = self.data_manager.update_task(task_id, data, account_id)
                if task:
                    return jsonify({
                        'success': True, 
                        'data': task,
                        'message': 'Task updated successfully'
                    })
                else:
                    return jsonify({
                        'success': False,
                        'message': 'Task not found'
                    }), 404
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f'Error updating task: {str(e)}'
                }), 500
        
        @self.app.route('/api/tasks/<task_id>/delete', methods=['POST'])
        def api_delete_task(task_id):
            """Soft delete a task"""
            data = request.get_json() or {}
            account_id = data.get('account_id', self.data_manager.dashboard_data['current_account'])
            permanent = data.get('permanent', False)
            
            try:
                if permanent:
                    success = self.data_manager.permanently_delete_task(task_id, account_id)
                    action = 'permanently deleted'
                else:
                    success = self.data_manager.soft_delete_task(task_id, account_id)
                    action = 'deleted'
                
                if success:
                    return jsonify({
                        'success': True,
                        'message': f'Task {action} successfully'
                    })
                else:
                    return jsonify({
                        'success': False,
                        'message': 'Task not found'
                    }), 404
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f'Error deleting task: {str(e)}'
                }), 500
        
        @self.app.route('/api/tasks/<task_id>/restore', methods=['POST'])
        def api_restore_task(task_id):
            """Restore a deleted task"""
            data = request.get_json() or {}
            account_id = data.get('account_id', self.data_manager.dashboard_data['current_account'])
            
            try:
                success = self.data_manager.restore_task(task_id, account_id)
                if success:
                    return jsonify({
                        'success': True,
                        'message': 'Task restored successfully'
                    })
                else:
                    return jsonify({
                        'success': False,
                        'message': 'Task not found'
                    }), 404
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f'Error restoring task: {str(e)}'
                }), 500
        
        @self.app.route('/api/deleted-tasks', methods=['GET'])
        def api_get_deleted_tasks():
            """Get deleted tasks"""
            account_id = request.args.get('account', self.data_manager.dashboard_data['current_account'])
            
            all_tasks = self.data_manager.dashboard_data['tasks'].get(account_id, [])
            deleted_tasks = [t for t in all_tasks if t.get('is_deleted', False)]
            
            return jsonify({'success': True, 'data': deleted_tasks})
        
        @self.app.route('/api/switch_account', methods=['POST'])
        def api_switch_account():
            """Switch current account"""
            data = request.get_json()
            account = data.get('account')
            
            if self.data_manager.switch_account(account):
                return jsonify({
                    'success': True, 
                    'message': f'Switched to account: {account}'
                })
            
            return jsonify({
                'success': False, 
                'message': 'Account not found'
            }), 400
        
        @self.app.route('/api/refresh', methods=['POST'])
        def api_refresh():
            """Refresh dashboard data"""
            try:
                self.data_manager.refresh_data()
                return jsonify({
                    'success': True, 
                    'message': 'Data refreshed successfully'
                })
            except Exception as e:
                return jsonify({
                    'success': False, 
                    'message': f'Error refreshing data: {str(e)}'
                }), 500
        
        @self.app.route('/api/accounts', methods=['GET'])
        def api_get_accounts():
            """Get all accounts"""
            return jsonify({
                'success': True,
                'data': self.data_manager.dashboard_data['accounts']
            })
        
        @self.app.route('/api/account-types', methods=['GET'])
        def api_get_account_types():
            """Get all account types"""
            return jsonify({
                'success': True,
                'data': self.data_manager.dashboard_data['account_types']
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
        
        @self.app.route('/api/available-tags', methods=['GET'])
        def api_get_available_tags():
            """Get all available tags with statistics"""
            return jsonify({
                'success': True,
                'data': self.data_manager.dashboard_data['available_tags']
            })
        
        @self.app.route('/api/priority-stats', methods=['GET'])
        def api_get_priority_stats():
            """Get priority statistics"""
            return jsonify({
                'success': True,
                'data': self.data_manager.dashboard_data['priority_stats']
            })
        
        @self.app.route('/api/tags/parse-filter', methods=['POST'])
        def api_parse_tag_filter():
            """Parse tag filter string"""
            data = request.get_json()
            tag_string = data.get('tag_string', '')
            
            parsed = self.data_manager.parse_tag_filter(tag_string)
            return jsonify({
                'success': True,
                'data': parsed
            })
        
        @self.app.route('/api/tasks/due-today', methods=['GET'])
        def api_get_tasks_due_today():
            """Get tasks due today"""
            due_today_tasks = self.data_manager.get_tasks_due_today()
            return jsonify({
                'success': True,
                'data': due_today_tasks
            })
        
        @self.app.route('/api/settings', methods=['GET'])
        def api_get_settings():
            """Get dashboard settings"""
            return jsonify({
                'success': True,
                'data': self.data_manager.dashboard_data['settings']
            })
        
        @self.app.route('/api/settings', methods=['POST'])
        def api_update_settings():
            """Update dashboard settings"""
            data = request.get_json()
            try:
                updated_settings = self.data_manager.update_settings(data)
                return jsonify({
                    'success': True,
                    'data': updated_settings,
                    'message': 'Settings updated successfully'
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f'Error updating settings: {str(e)}'
                }), 500
        
        @self.app.route('/api/export', methods=['GET'])
        def api_export_tasks():
            """Export all tasks"""
            all_tasks = []
            for tasks in self.data_manager.dashboard_data['tasks'].values():
                all_tasks.extend(tasks)
            
            format_type = request.args.get('format', 'json')
            
            if format_type == 'csv':
                # Simple CSV export
                import csv
                import io
                output = io.StringIO()
                writer = csv.writer(output)
                
                # Write header
                if all_tasks:
                    writer.writerow(all_tasks[0].keys())
                    for task in all_tasks:
                        writer.writerow(task.values())
                
                csv_content = output.getvalue()
                return jsonify({
                    'success': True,
                    'data': csv_content,
                    'format': 'csv',
                    'filename': f'gtasks_export_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
                })
            else:
                return jsonify({
                    'success': True,
                    'data': all_tasks,
                    'export_count': len(all_tasks),
                    'format': 'json'
                })
        
        @self.app.route('/api/reports/types', methods=['GET'])
        def api_get_report_types():
            """Get available report types"""
            return jsonify({
                'success': True,
                'data': self.data_manager.get_report_types()
            })
        
        @self.app.route('/api/reports/generate', methods=['POST'])
        def api_generate_report():
            """Generate a report"""
            data = request.get_json()
            report_type = data.get('report_type')
            account_ids = data.get('account_ids', [])
            filters = data.get('filters', {})
            parameters = data.get('parameters', {})
            
            if not report_type:
                return jsonify({
                    'success': False,
                    'message': 'Report type is required'
                }), 400
            
            try:
                # Get tasks from specified accounts or all accounts
                tasks = []
                if account_ids:
                    for account_id in account_ids:
                        account_tasks = self.data_manager.dashboard_data['tasks'].get(account_id, [])
                        tasks.extend(account_tasks)
                else:
                    for tasks_list in self.data_manager.dashboard_data['tasks'].values():
                        tasks.extend(tasks_list)
                
                # Apply filters
                if filters:
                    tasks = self.data_manager.get_filtered_tasks(filters)
                
                # Generate report
                report_data = self.data_manager.generate_report(report_type, tasks, **parameters)
                
                return jsonify({
                    'success': True,
                    'data': report_data,
                    'message': f'Report {report_type} generated successfully'
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f'Error generating report: {str(e)}'
                }), 500
        
        @self.app.route('/api/filter-tasks', methods=['POST'])
        def api_filter_tasks():
            """Advanced task filtering"""
            data = request.get_json()
            filters = data.get('filters', {})
            
            try:
                filtered_tasks = self.data_manager.get_filtered_tasks(filters)
                return jsonify({
                    'success': True,
                    'data': filtered_tasks,
                    'count': len(filtered_tasks)
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f'Error filtering tasks: {str(e)}'
                }), 500
        
        @self.app.route('/api/priorities/recalculate', methods=['POST'])
        def api_recalculate_priorities():
            """Force recalculation of all priorities"""
            try:
                self.data_manager.calculate_priorities()
                self.data_manager.calculate_priority_statistics()
                self.data_manager.create_priority_enhanced_hierarchy()
                
                return jsonify({
                    'success': True,
                    'message': 'Priorities recalculated successfully'
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f'Error recalculating priorities: {str(e)}'
                }), 500
        
        @self.app.route('/api/health')
        def api_health():
            """Health check endpoint"""
            import datetime
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.datetime.now().isoformat(),
                'features_enabled': {
                    'reports': self.data_manager.dashboard_data['settings'].get('reports_enabled', True),
                    'priority_system': self.data_manager.dashboard_data['settings'].get('priority_system_enabled', True),
                    'advanced_filters': self.data_manager.dashboard_data['settings'].get('advanced_filters_enabled', True),
                    'deleted_tasks': True,
                    'hierarchical_viz': True,
                    'account_types': True,
                    'task_management': True,
                    'settings': True,
                    'collapsible_menu': True,
                    'due_today': True
                }
            })
        
        # Real-time updates endpoint
        @self.app.route('/api/updates/last', methods=['GET'])
        def api_get_last_update():
            """Get last update timestamp"""
            return jsonify({
                'success': True,
                'data': {
                    'last_update': self.data_manager.dashboard_data['realtime'].get('last_update'),
                    'connected': self.data_manager.dashboard_data['realtime'].get('connected', False)
                }
            })