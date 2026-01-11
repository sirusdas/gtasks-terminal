"""
Priority System Module for GTasks Dashboard

This module handles priority calculation and management including:
- Asterisk-based priority calculation from tags
- Priority statistics and analytics
- Priority visualization data

Author: GTasks Dashboard Team
Date: January 11, 2026
"""

import re
from collections import defaultdict


class PrioritySystem:
    """Handles priority calculation and management"""
    
    def __init__(self):
        self.priority_colors = {
            'critical': '#ef4444',  # Red
            'high': '#f97316',      # Orange  
            'medium': '#eab308',    # Yellow
            'low': '#6b7280'      # Gray
        }
        
        self.priority_icons = {
            'critical': '🔥',
            'high': '⚠️',
            'medium': '📋',
            'low': '📝'
        }
    
    def calculate_priority_from_tags(self, task):
        """Calculate priority for a task based on asterisk patterns in tags"""
        # Extract all text content for analysis
        all_text = ' '.join([
            str(task.get('title', '') or ''),
            str(task.get('description', '') or ''),
            str(task.get('notes', '') or ''),
            ' '.join([str(tag) for tag in task.get('tags', [])])
        ])
        
        # Find asterisk patterns
        asterisk_patterns = re.findall(r'\*+', all_text)
        
        # Calculate priority based on asterisk count
        max_asterisks = max([len(pattern) for pattern in asterisk_patterns]) if asterisk_patterns else 0
        
        if max_asterisks >= 6:
            priority = 'critical'
        elif max_asterisks >= 4:
            priority = 'high'
        elif max_asterisks >= 3:
            priority = 'medium'
        else:
            priority = 'low'
        
        return {
            'calculated_priority': priority,
            'asterisk_patterns': asterisk_patterns,
            'max_asterisks': max_asterisks,
            'priority_source': 'calculated'
        }
    
    def calculate_priorities_for_tasks(self, tasks):
        """Calculate priorities for a list of tasks"""
        for task in tasks:
            priority_info = self.calculate_priority_from_tags(task)
            task.update(priority_info)
        return tasks
    
    def calculate_priority_statistics(self, tasks):
        """Calculate comprehensive priority statistics"""
        stats = {
            'total_tasks': len(tasks),
            'by_priority': defaultdict(int),
            'by_source': defaultdict(int),
            'asterisk_patterns': defaultdict(int),
            'priority_distribution': {}
        }
        
        for task in tasks:
            stats['total_tasks'] += 1
            
            # Count by calculated priority
            priority = task.get('calculated_priority', 'low')
            stats['by_priority'][priority] += 1
            
            # Count by source
            source = task.get('priority_source', 'calculated')
            stats['by_source'][source] += 1
            
            # Count asterisk patterns
            patterns = task.get('asterisk_patterns', [])
            if patterns:
                stats['asterisk_patterns']['with_patterns'] += 1
                for pattern in patterns:
                    stats['asterisk_patterns'][pattern] += 1
            else:
                stats['asterisk_patterns']['no_patterns'] += 1
        
        # Convert to regular dicts for JSON serialization
        return {
            'total_tasks': stats['total_tasks'],
            'by_priority': dict(stats['by_priority']),
            'by_source': dict(stats['by_source']),
            'asterisk_patterns': dict(stats['asterisk_patterns']),
            'priority_distribution': stats['by_priority']
        }
    
    def get_priority_rules_documentation(self):
        """Get priority calculation rules for display"""
        return {
            'rules': [
                {
                    'level': 'critical',
                    'name': 'Critical Priority',
                    'asterisks': '6+ asterisks',
                    'examples': ['[******]', '[*******urgent]', '[******production]'],
                    'color': self.priority_colors['critical'],
                    'icon': self.priority_icons['critical']
                },
                {
                    'level': 'high',
                    'name': 'High Priority',
                    'asterisks': '4-5 asterisks',
                    'examples': ['[****]', '[*****important]', '[****bug]'],
                    'color': self.priority_colors['high'],
                    'icon': self.priority_icons['high']
                },
                {
                    'level': 'medium',
                    'name': 'Medium Priority',
                    'asterisks': '3 asterisks',
                    'examples': ['[***]', '[***review]', '[***enhancement]'],
                    'color': self.priority_colors['medium'],
                    'icon': self.priority_icons['medium']
                },
                {
                    'level': 'low',
                    'name': 'Low Priority',
                    'asterisks': '1-2 asterisks or none',
                    'examples': ['[**]', '[*optional]', '[enhancement]', '#work', '@user'],
                    'color': self.priority_colors['low'],
                    'icon': self.priority_icons['low']
                }
            ]
        }
    
    def create_priority_monitor_data(self, priority_stats):
        """Create data for priority monitoring display"""
        monitor_data = []
        
        for priority, count in priority_stats.get('by_priority', {}).items():
            monitor_data.append({
                'priority': priority,
                'count': count,
                'percentage': round((count / priority_stats['total_tasks']) * 100, 1) if priority_stats['total_tasks'] > 0 else 0,
                'color': self.priority_colors.get(priority, '#6b7280'),
                'icon': self.priority_icons.get(priority, '📝')
            })
        
        # Sort by priority level
        priority_order = ['critical', 'high', 'medium', 'low']
        monitor_data.sort(key=lambda x: priority_order.index(x['priority']) if x['priority'] in priority_order else 999)
        
        return monitor_data