# Flask API Endpoints for GTasks Unified Dashboard
# This file contains all the API routes that serve data to the frontend

@app.route('/api/dashboard')
def get_dashboard_data():
    """Get comprehensive dashboard data"""
    try:
        # Compile all tasks from all accounts
        all_tasks = []
        for account_id, tasks in UNIFIED_DASHBOARD_DATA['tasks'].items():
            all_tasks.extend(tasks)
        
        # Apply filters based on current settings
        show_deleted = UNIFIED_DASHBOARD_DATA['settings'].get('show_deleted_tasks', False)
        if not show_deleted:
            all_tasks = [task for task in all_tasks if not task.get('is_deleted', False)]
        
        dashboard_data = {
            'accounts': UNIFIED_DASHBOARD_DATA['accounts'],
            'current_account': UNIFIED_DASHBOARD_DATA['current_account'],
            'account_types': UNIFIED_DASHBOARD_DATA['account_types'],
            'available_tags': UNIFIED_DASHBOARD_DATA['available_tags'],
            'priority_stats': UNIFIED_DASHBOARD_DATA['priority_stats'],
            'stats': UNIFIED_DASHBOARD_DATA['stats'],
            'hierarchy_data': UNIFIED_DASHBOARD_DATA['hierarchy_data'],
            'allTasks': all_tasks,
            'last_updated': datetime.datetime.now().isoformat()
        }
        
        return jsonify({'success': True, 'data': dashboard_data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/tasks')
def get_tasks():
    """Get filtered tasks"""
    try:
        account_id = request.args.get('account', UNIFIED_DASHBOARD_DATA['current_account'])
        status = request.args.get('status', '')
        priority = request.args.get('priority', '')
        project = request.args.get('project', '')
        search = request.args.get('search', '')
        include_deleted = request.args.get('include_deleted', 'false').lower() == 'true'
        
        tasks = UNIFIED_DASHBOARD_DATA['tasks'].get(account_id, [])
        
        # Apply filters
        if status:
            tasks = [t for t in tasks if t.get('status') == status]
        if priority:
            tasks = [t for t in tasks if t.get('calculated_priority') == priority or t.get('priority') == priority]
        if project:
            tasks = [t for t in tasks if t.get('project') == project]
        if search:
            search_lower = search.lower()
            tasks = [t for t in tasks if 
                    search_lower in t.get('title', '').lower() or
                    search_lower in t.get('description', '').lower()]
        if not include_deleted:
            tasks = [t for t in tasks if not t.get('is_deleted', False)]
        
        return jsonify({'success': True, 'data': tasks})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/tasks/due-today')
def get_tasks_due_today():
    """Get tasks due today"""
    try:
        today = datetime.date.today()
        today_str = today.isoformat()
        
        all_tasks = []
        for tasks in UNIFIED_DASHBOARD_DATA['tasks'].values():
            all_tasks.extend(tasks)
        
        # Filter for tasks due today (excluding deleted tasks)
        today_tasks = [task for task in all_tasks 
                      if task.get('due') == today_str and not task.get('is_deleted', False)]
        
        # Group by time slots
        time_groups = {
            'Morning (6-12)': [],
            'Afternoon (12-18)': [],
            'Evening (18-24)': [],
            'No Time': []
        }
        
        for task in today_tasks:
            # Simple time grouping logic (in real implementation, parse actual due times)
            if task.get('due_time'):
                # Parse time and categorize
                try:
                    due_time = datetime.datetime.fromisoformat(task['due_time'])
                    hour = due_time.hour
                    if 6 <= hour < 12:
                        time_groups['Morning (6-12)'].append(task)
                    elif 12 <= hour < 18:
                        time_groups['Afternoon (12-18)'].append(task)
                    else:
                        time_groups['Evening (18-24)'].append(task)
                except:
                    time_groups['No Time'].append(task)
            else:
                time_groups['No Time'].append(task)
        
        return jsonify({
            'success': True, 
            'data': {
                'today': today_str,
                'time_groups': time_groups,
                'total_count': len(today_tasks)
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/hierarchy')
def get_hierarchy_data():
    """Get hierarchical visualization data"""
    try:
        return jsonify({
            'success': True, 
            'data': UNIFIED_DASHBOARD_DATA['hierarchy_data']
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/priority-stats')
def get_priority_stats():
    """Get priority statistics"""
    try:
        return jsonify({
            'success': True, 
            'data': UNIFIED_DASHBOARD_DATA['priority_stats']
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/accounts')
def get_accounts():
    """Get all accounts"""
    try:
        return jsonify({
            'success': True, 
            'data': UNIFIED_DASHBOARD_DATA['accounts']
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/account-types')
def get_account_types():
    """Get account types"""
    try:
        return jsonify({
            'success': True, 
            'data': UNIFIED_DASHBOARD_DATA['account_types']
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/tags')
def get_tags():
    """Get all available tags with statistics"""
    try:
        return jsonify({
            'success': True, 
            'data': UNIFIED_DASHBOARD_DATA['available_tags']
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/settings', methods=['GET', 'POST'])
def handle_settings():
    """Get or update dashboard settings"""
    try:
        if request.method == 'GET':
            return jsonify({
                'success': True, 
                'data': UNIFIED_DASHBOARD_DATA['settings']
            })
        else:
            data = request.get_json()
            if data:
                # Update settings
                for key, value in data.items():
                    if key in UNIFIED_DASHBOARD_DATA['settings']:
                        UNIFIED_DASHBOARD_DATA['settings'][key] = value
                
                # Save to file
                save_settings()
                
                # If priority system setting changed, recalculate
                if 'priority_system_enabled' in data:
                    if data['priority_system_enabled']:
                        dashboard.calculate_priorities()
                        dashboard.calculate_priority_statistics()
                    else:
                        # Reset calculated priorities
                        for tasks in UNIFIED_DASHBOARD_DATA['tasks'].values():
                            for task in tasks:
                                task.pop('calculated_priority', None)
                                task.pop('asterisk_patterns', None)
                
                # If show_deleted_tasks setting changed, update stats
                if 'show_deleted_tasks' in data:
                    all_tasks = []
                    for tasks in UNIFIED_DASHBOARD_DATA['tasks'].values():
                        all_tasks.extend(tasks)
                    UNIFIED_DASHBOARD_DATA['stats'] = dashboard.calculate_stats(all_tasks)
                
                return jsonify({
                    'success': True, 
                    'data': UNIFIED_DASHBOARD_DATA['settings']
                })
            else:
                return jsonify({'success': False, 'error': 'No data provided'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/tasks', methods=['POST'])
def create_task():
    """Create a new task"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Generate task ID
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        
        # Extract tags using hybrid extraction
        title = data.get('title', '')
        description = data.get('description', '')
        tags_input = data.get('tags', '')
        
        # Parse asterisk priority from tags
        asterisk_patterns = re.findall(r'\*+', tags_input)
        calculated_priority = 'low'
        if len(asterisk_patterns) > 0:
            priority_count = sum(len(pattern) for pattern in asterisk_patterns)
            if priority_count >= 6:
                calculated_priority = 'critical'
            elif priority_count >= 4:
                calculated_priority = 'high'
            elif priority_count >= 3:
                calculated_priority = 'medium'
            else:
                calculated_priority = 'low'
        
        # Create task object
        new_task = {
            'id': task_id,
            'title': title,
            'description': description,
            'due': data.get('due'),
            'priority': data.get('priority', calculated_priority),
            'calculated_priority': calculated_priority,
            'priority_source': 'calculated' if asterisk_patterns else 'manual',
            'asterisk_patterns': asterisk_patterns,
            'status': 'pending',
            'project': data.get('project', ''),
            'tags': [],
            'notes': '',
            'created_at': datetime.datetime.now().isoformat(),
            'account': UNIFIED_DASHBOARD_DATA['current_account'],
            'is_deleted': False,
            'deleted_at': None,
            'deleted_by': None
        }
        
        # Extract hybrid tags
        text_content = f"{title} {description} {tags_input}"
        hybrid_tags = dashboard.extract_hybrid_tags(text_content)
        new_task['hybrid_tags'] = hybrid_tags
        new_task['categorized_tags'] = {}
        
        # Categorize all tags
        all_tags = (hybrid_tags['bracket'] + hybrid_tags['hash'] + hybrid_tags['user'])
        for tag in all_tags:
            category = dashboard.categorize_tag(tag)
            if category not in new_task['categorized_tags']:
                new_task['categorized_tags'][category] = []
            new_task['categorized_tags'][category].append(tag)
        
        # Add to account tasks
        current_account = UNIFIED_DASHBOARD_DATA['current_account']
        if current_account not in UNIFIED_DASHBOARD_DATA['tasks']:
            UNIFIED_DASHBOARD_DATA['tasks'][current_account] = []
        
        UNIFIED_DASHBOARD_DATA['tasks'][current_account].append(new_task)
        
        return jsonify({
            'success': True, 
            'data': new_task,
            'message': 'Task created successfully'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/tasks/<task_id>', methods=['PUT'])
def update_task(task_id):
    """Update a task"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Find and update task
        for account_id, tasks in UNIFIED_DASHBOARD_DATA['tasks'].items():
            for task in tasks:
                if task['id'] == task_id:
                    # Update allowed fields
                    allowed_fields = ['title', 'description', 'due', 'priority', 'status', 'project', 'notes']
                    for field in allowed_fields:
                        if field in data:
                            task[field] = data[field]
                    
                    # Recalculate priority if tags changed
                    if 'title' in data or 'description' in data or 'tags' in data:
                        text_content = f"{task.get('title', '')} {task.get('description', '')} {data.get('tags', '')}"
                        hybrid_tags = dashboard.extract_hybrid_tags(text_content)
                        task['hybrid_tags'] = hybrid_tags
                        
                        # Recalculate asterisk-based priority
                        asterisk_patterns = re.findall(r'\*+', str(hybrid_tags))
                        priority_count = sum(len(pattern) for pattern in asterisk_patterns)
                        
                        if priority_count >= 6:
                            task['calculated_priority'] = 'critical'
                        elif priority_count >= 4:
                            task['calculated_priority'] = 'high'
                        elif priority_count >= 3:
                            task['calculated_priority'] = 'medium'
                        else:
                            task['calculated_priority'] = 'low'
                        
                        task['asterisk_patterns'] = asterisk_patterns
                    
                    return jsonify({
                        'success': True, 
                        'data': task,
                        'message': 'Task updated successfully'
                    })
        
        return jsonify({'success': False, 'error': 'Task not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/tasks/<task_id>/delete', methods=['POST'])
def soft_delete_task_endpoint(task_id):
    """Soft delete a task"""
    try:
        success = dashboard.soft_delete_task(task_id)
        if success:
            return jsonify({
                'success': True, 
                'message': 'Task soft deleted successfully'
            })
        else:
            return jsonify({'success': False, 'error': 'Task not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/tasks/<task_id>/restore', methods=['POST'])
def restore_task_endpoint(task_id):
    """Restore a deleted task"""
    try:
        success = dashboard.restore_task(task_id)
        if success:
            return jsonify({
                'success': True, 
                'message': 'Task restored successfully'
            })
        else:
            return jsonify({'success': False, 'error': 'Task not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/tasks/<task_id>', methods=['DELETE'])
def permanently_delete_task_endpoint(task_id):
    """Permanently delete a task"""
    try:
        success = dashboard.permanently_delete_task(task_id)
        if success:
            return jsonify({
                'success': True, 
                'message': 'Task permanently deleted'
            })
        else:
            return jsonify({'success': False, 'error': 'Task not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/tasks/deleted')
def get_deleted_tasks():
    """Get all deleted tasks"""
    try:
        deleted_tasks = []
        for tasks in UNIFIED_DASHBOARD_DATA['tasks'].values():
            deleted_tasks.extend([task for task in tasks if task.get('is_deleted', False)])
        
        return jsonify({
            'success': True, 
            'data': deleted_tasks
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/reports')
def get_reports():
    """Generate various reports"""
    try:
        report_type = request.args.get('type', 'summary')
        
        if report_type == 'summary':
            # Summary report
            all_tasks = []
            for tasks in UNIFIED_DASHBOARD_DATA['tasks'].values():
                all_tasks.extend(tasks)
            
            # Calculate metrics
            total_tasks = len(all_tasks)
            completed_tasks = len([t for t in all_tasks if t.get('status') == 'completed'])
            deleted_tasks = len([t for t in all_tasks if t.get('is_deleted', False)])
            pending_tasks = len([t for t in all_tasks if t.get('status') == 'pending'])
            
            # Priority breakdown
            priority_breakdown = {}
            for priority in ['critical', 'high', 'medium', 'low']:
                count = len([t for t in all_tasks if t.get('calculated_priority') == priority])
                priority_breakdown[priority] = count
            
            report_data = {
                'summary': {
                    'total_tasks': total_tasks,
                    'completed_tasks': completed_tasks,
                    'pending_tasks': pending_tasks,
                    'deleted_tasks': deleted_tasks,
                    'completion_rate': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
                },
                'priority_breakdown': priority_breakdown,
                'accounts': UNIFIED_DASHBOARD_DATA['accounts'],
                'generated_at': datetime.datetime.now().isoformat()
            }
            
        elif report_type == 'priority_analysis':
            # Priority-focused report
            report_data = UNIFIED_DASHBOARD_DATA['priority_stats']
        
        elif report_type == 'account_performance':
            # Account performance report
            account_data = []
            for account in UNIFIED_DASHBOARD_DATA['accounts']:
                account_tasks = UNIFIED_DASHBOARD_DATA['tasks'].get(account['id'], [])
                active_tasks = [t for t in account_tasks if not t.get('is_deleted', False)]
                completed_count = len([t for t in active_tasks if t.get('status') == 'completed'])
                
                account_data.append({
                    'account': account,
                    'total_tasks': len(active_tasks),
                    'completed_tasks': completed_count,
                    'completion_rate': (completed_count / len(active_tasks) * 100) if active_tasks else 0,
                    'high_priority_count': len([t for t in active_tasks if t.get('calculated_priority') in ['high', 'critical']])
                })
            
            report_data = {
                'account_performance': account_data,
                'generated_at': datetime.datetime.now().isoformat()
            }
        
        else:
            return jsonify({'success': False, 'error': 'Unknown report type'}), 400
        
        return jsonify({
            'success': True, 
            'data': report_data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/accounts/switch', methods=['POST'])
def switch_account():
    """Switch current account"""
    try:
        data = request.get_json()
        account_id = data.get('account_id')
        
        if account_id in [acc['id'] for acc in UNIFIED_DASHBOARD_DATA['accounts']]:
            UNIFIED_DASHBOARD_DATA['current_account'] = account_id
            return jsonify({
                'success': True, 
                'message': f'Switched to account {account_id}'
            })
        else:
            return jsonify({'success': False, 'error': 'Account not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/export')
def export_data():
    """Export dashboard data"""
    try:
        export_format = request.args.get('format', 'json')
        
        if export_format == 'json':
            # Export as JSON
            export_data = {
                'dashboard_data': UNIFIED_DASHBOARD_DATA,
                'exported_at': datetime.datetime.now().isoformat(),
                'total_tasks': sum(len(tasks) for tasks in UNIFIED_DASHBOARD_DATA['tasks'].values()),
                'accounts_count': len(UNIFIED_DASHBOARD_DATA['accounts'])
            }
            
            response = jsonify({'success': True, 'data': export_data})
            response.headers['Content-Disposition'] = f'attachment; filename=gtasks_dashboard_export_{datetime.date.today()}.json'
            return response
        
        else:
            return jsonify({'success': False, 'error': 'Unsupported export format'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'success': True,
        'status': 'healthy',
        'timestamp': datetime.datetime.now().isoformat(),
        'data_summary': {
            'accounts': len(UNIFIED_DASHBOARD_DATA['accounts']),
            'total_tasks': sum(len(tasks) for tasks in UNIFIED_DASHBOARD_DATA['tasks'].values()),
            'features_active': 9,
            'priority_system_enabled': UNIFIED_DASHBOARD_DATA['settings'].get('priority_system_enabled', True)
        }
    })

# Advanced tag filtering endpoint
@app.route('/api/tags/filter', methods=['POST'])
def advanced_tag_filter():
    """Apply advanced tag filtering"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No filter data provided'}), 400
        
        tag_query = data.get('query', '').strip()
        account_id = data.get('account', UNIFIED_DASHBOARD_DATA['current_account'])
        
        tasks = UNIFIED_DASHBOARD_DATA['tasks'].get(account_id, [])
        
        if not tag_query:
            # Return all active tasks
            filtered_tasks = [task for task in tasks if not task.get('is_deleted', False)]
        else:
            filtered_tasks = apply_advanced_tag_filter(tasks, tag_query)
        
        return jsonify({
            'success': True, 
            'data': {
                'filtered_tasks': filtered_tasks,
                'total_count': len(filtered_tasks),
                'filter_query': tag_query,
                'applied_filters': parse_tag_query(tag_query)
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def apply_advanced_tag_filter(tasks, tag_query):
    """Apply advanced tag filtering logic"""
    # Parse tag query for OR (|), AND (&), NOT (-) operations
    operations = parse_tag_query(tag_query)
    
    filtered_tasks = []
    for task in tasks:
        if task.get('is_deleted', False):
            continue
            
        # Get all tags from task
        task_tags = []
        if task.get('hybrid_tags'):
            task_tags.extend(task['hybrid_tags'].get('bracket', []))
            task_tags.extend(task['hybrid_tags'].get('hash', []))
            task_tags.extend(task['hybrid_tags'].get('user', []))
        
        task_tags.extend(task.get('tags', []))
        
        # Apply OR filter (must have at least one tag)
        if operations['or_tags']:
            if not any(tag.lower() in [t.lower() for t in task_tags] for tag in operations['or_tags']):
                continue
        
        # Apply AND filter (must have all tags)
        if operations['and_tags']:
            if not all(tag.lower() in [t.lower() for t in task_tags] for tag in operations['and_tags']):
                continue
        
        # Apply NOT filter (must not have any excluded tags)
        if operations['not_tags']:
            if any(tag.lower() in [t.lower() for t in task_tags] for tag in operations['not_tags']):
                continue
        
        filtered_tasks.append(task)
    
    return filtered_tasks

def parse_tag_query(query):
    """Parse tag query into OR, AND, NOT operations"""
    if not query.strip():
        return {'or_tags': [], 'and_tags': [], 'not_tags': []}
    
    # Split by spaces and process operators
    parts = query.split()
    or_tags = []
    and_tags = []
    not_tags = []
    
    for part in parts:
        if part.startswith('-'):
            # NOT tag
            not_tags.append(part[1:].strip())
        elif '&' in part:
            # AND tags
            and_tags.extend(tag.strip() for tag in part.split('&'))
        elif '|' in part:
            # OR tags
            or_tags.extend(tag.strip() for tag in part.split('|'))
        else:
            # Regular tag (treated as OR)
            or_tags.append(part.strip())
    
    return {
        'or_tags': or_tags,
        'and_tags': and_tags,
        'not_tags': not_tags
    }